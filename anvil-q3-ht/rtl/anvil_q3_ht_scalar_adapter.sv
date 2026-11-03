module anvil_q3_ht_scalar_adapter #(
  parameter CLIENTS=8, NUM_LAYERS=36, HIDDEN_SIZE=2048, INTERMEDIATE_SIZE=11008,
  parameter NUM_Q_HEADS=16, NUM_KV_HEADS=2, HEAD_DIM=128,
  parameter GROUP_SIZE=128, VOCAB_SIZE=151936, MAX_SEQ_LEN=32768,
  localparam NC=CLIENTS>=1 && CLIENTS<=32 ? CLIENTS : 1,
  localparam CW=NC>1 ? $clog2(NC) : 1
) (
  input wire clk, rst_n, flush, invalidate,
  input wire [NC-1:0] c_req_valid, c_req_write,
  output wire [NC-1:0] c_req_ready,
  input wire [NC*4-1:0] c_req_kind,
  input wire [NC*32-1:0] c_req_layer, c_req_row, c_req_col, c_req_wdata,
  input wire [NC*3-1:0] c_req_proj,
  output wire [NC-1:0] c_rsp_valid, c_rsp_error,
  input wire [NC-1:0] c_rsp_ready,
  output wire [NC*32-1:0] c_rsp_rdata,
  output wire idle, drain_done, fault,
  output wire scratch_req_valid, scratch_req_write,
  input wire scratch_req_ready,
  output wire [31:0] scratch_req_slot, scratch_req_index, scratch_req_wdata,
  input wire scratch_rsp_valid, scratch_rsp_error,
  output wire scratch_rsp_ready,
  input wire [31:0] scratch_rsp_rdata,
  output wire memory_req_valid, memory_req_write,
  input wire memory_req_ready,
  output wire [32:0] memory_req_address,
  output wire [511:0] memory_req_wdata,
  output wire [63:0] memory_req_byteenable,
  input wire memory_rsp_valid, memory_rsp_error,
  input wire [511:0] memory_rsp_rdata
);
  localparam IDLE=0, MAP_REQUEST=1, MAP_RESPONSE=2, SCRATCH_REQUEST=3;
  localparam SCRATCH_RESPONSE=4, LINE_SELECT=5, DDR_REQUEST=6, DDR_RESPONSE=7;
  localparam EXTRACT=8, RESPONSE=9, ABORT=10;
  reg [3:0] state;
  reg failed, write_command, response_error;
  reg [CW-1:0] pointer, owner;
  reg [3:0] kind;
  reg [2:0] projection, element_bytes;
  reg [31:0] layer, row, column, write_data, response_data;
  reg [32:0] address, cached_address;
  reg cache_valid;
  reg [511:0] cached_line, selected_line;
  wire running=rst_n && CLIENTS==NC && !flush && !failed;
  wire map_ready, map_valid, map_error, map_scratch;
  wire [32:0] map_address;
  wire [2:0] map_bytes;
  wire record_ready, record_valid, record_error, record_fault, record_drained;
  wire [511:0] record_data;
  wire [511:0] shifted_line=selected_line>>{address[5:0],3'd0};
  wire [32:0] line_address={address[32:6],6'd0};
  integer offset, candidate, selected;

  generate if (CLIENTS!=NC) begin: invalid_parameters
    initial $fatal(1,"ANVIL_Q3_HT PARAMETER ERROR: scalar adapter clients");
  end endgenerate
  always @* begin
    selected=-1;
    candidate=0;
    for (offset=0;offset<NC;offset=offset+1) begin
      candidate=pointer+offset;
      if (candidate>=NC) candidate=candidate-NC;
      if (selected<0 && c_req_valid[candidate]) selected=candidate;
    end
  end
  genvar client;
  generate for (client=0;client<NC;client=client+1) begin: clients
    assign c_req_ready[client]=running && state==IDLE && record_ready && selected==client;
    assign c_rsp_valid[client]=running && state==RESPONSE && owner==client;
    assign c_rsp_error[client]=c_rsp_valid[client] && response_error;
    assign c_rsp_rdata[client*32+:32]=
      c_rsp_valid[client] && !response_error ? response_data : 32'd0;
  end endgenerate
  assign idle=running && state==IDLE && record_ready;
  assign drain_done=record_drained;
  assign fault=rst_n && (failed || record_fault);
  assign scratch_req_valid=running && state==SCRATCH_REQUEST;
  assign scratch_req_write=scratch_req_valid && write_command;
  assign scratch_req_slot=scratch_req_valid ? row : 32'd0;
  assign scratch_req_index=scratch_req_valid ? column : 32'd0;
  assign scratch_req_wdata=scratch_req_write ? write_data : 32'd0;
  assign scratch_rsp_ready=running && state==SCRATCH_RESPONSE;

  anvil_q3_ht_image_map #(
    .NUM_LAYERS(NUM_LAYERS),.HIDDEN_SIZE(HIDDEN_SIZE),.INTERMEDIATE_SIZE(INTERMEDIATE_SIZE),
    .NUM_Q_HEADS(NUM_Q_HEADS),.NUM_KV_HEADS(NUM_KV_HEADS),.HEAD_DIM(HEAD_DIM),
    .GROUP_SIZE(GROUP_SIZE),.VOCAB_SIZE(VOCAB_SIZE),.MAX_SEQ_LEN(MAX_SEQ_LEN)
  ) image_map (
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .req_valid(running && state==MAP_REQUEST),.req_ready(map_ready),
    .req_write(write_command),.req_kind(kind),.req_layer(layer),
    .req_row(row),.req_col(column),.req_proj(projection),
    .rsp_valid(map_valid),.rsp_ready(state==MAP_RESPONSE),
    .rsp_error(map_error),.rsp_scratch(map_scratch),
    .rsp_address(map_address),.rsp_bytes(map_bytes),
    .rsp_inputs(),.rsp_outputs(),.rsp_qweight_base(),.rsp_qzeros_base(),.rsp_scales_base()
  );
  anvil_q3_ht_ddr_record_port record_port (
    .clk(clk),.rst_n(rst_n),.flush(flush || state==ABORT),
    .in_valid(running && state==DDR_REQUEST),.in_ready(record_ready),
    .in_write(1'b0),.in_address(line_address),.in_wdata(512'd0),
    .in_byteenable(64'hffffffffffffffff),
    .out_valid(record_valid),.out_ready(1'b1),
    .out_error(record_error),.out_rdata(record_data),
    .idle(),.drain_done(record_drained),.fault(record_fault),
    .memory_req_valid(memory_req_valid),.memory_req_ready(memory_req_ready),
    .memory_req_write(memory_req_write),.memory_req_address(memory_req_address),
    .memory_req_wdata(memory_req_wdata),.memory_req_byteenable(memory_req_byteenable),
    .memory_rsp_valid(memory_rsp_valid),.memory_rsp_error(memory_rsp_error),
    .memory_rsp_rdata(memory_rsp_rdata)
  );

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; failed<=0; write_command<=0; response_error<=0;
      pointer<=0; owner<=0; kind<=0; projection<=0; element_bytes<=0;
      layer<=0; row<=0; column<=0; write_data<=0; response_data<=0;
      address<=0; cached_address<=0; cache_valid<=0; cached_line<=0; selected_line<=0;
    end else if (flush) begin
      state<=ABORT; failed<=0; response_error<=0; response_data<=0;
      cache_valid<=0; pointer<=0;
    end else begin
      if (invalidate) cache_valid<=0;
      if (record_fault && state!=ABORT) begin
        failed<=1; cache_valid<=0;
      end else case (state)
        IDLE: if (running && record_ready && selected>=0) begin
          owner<=CW'(selected);
          write_command<=c_req_write[selected];
          kind<=c_req_kind[selected*4+:4];
          projection<=c_req_proj[selected*3+:3];
          layer<=c_req_layer[selected*32+:32];
          row<=c_req_row[selected*32+:32];
          column<=c_req_col[selected*32+:32];
          write_data<=c_req_wdata[selected*32+:32];
          response_data<=0; response_error<=0;
          state<=MAP_REQUEST;
        end
        MAP_REQUEST: if (map_ready) state<=MAP_RESPONSE;
        MAP_RESPONSE: if (map_valid) begin
          if (map_error) begin response_error<=1; state<=RESPONSE; end
          else if (map_scratch) state<=SCRATCH_REQUEST;
          else begin address<=map_address; element_bytes<=map_bytes; state<=LINE_SELECT; end
        end
        SCRATCH_REQUEST: if (scratch_req_ready) state<=SCRATCH_RESPONSE;
        SCRATCH_RESPONSE: if (scratch_rsp_valid) begin
          response_data<=scratch_rsp_rdata;
          response_error<=scratch_rsp_error;
          state<=RESPONSE;
        end
        LINE_SELECT: begin
          if (!invalidate && cache_valid && cached_address==line_address) begin
            selected_line<=cached_line; state<=EXTRACT;
          end else state<=DDR_REQUEST;
        end
        DDR_REQUEST: if (record_ready) state<=DDR_RESPONSE;
        DDR_RESPONSE: if (record_valid) begin
          if (record_error) begin response_error<=1; state<=RESPONSE; end
          else begin
            cached_address<=line_address;
            cached_line<=record_data;
            cache_valid<=!invalidate;
            selected_line<=record_data;
            state<=EXTRACT;
          end
        end
        EXTRACT: begin
          response_data<=element_bytes==2 ? {16'd0,shifted_line[15:0]} : shifted_line[31:0];
          state<=RESPONSE;
        end
        RESPONSE: if (c_rsp_ready[owner]) begin
          pointer<=owner==NC-1 ? 0 : owner+1'b1;
          response_data<=0; response_error<=0; state<=IDLE;
        end
        ABORT: if (record_drained && !record_fault) state<=IDLE;
        default: begin failed<=1; cache_valid<=0; end
      endcase
    end
  end
endmodule
