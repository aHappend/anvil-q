module anvil_q3_ht_scratch_backing #(
  parameter WORDS=54016, LOCAL_WORDS=54016,
  localparam SPILL_WORDS=WORDS>LOCAL_WORDS ? WORDS-LOCAL_WORDS : 0,
  localparam PAGES=(64'(SPILL_WORDS)+511)>>9
) (
  input wire clk, rst_n, flush, memory_enable,
  input wire req_valid, req_write,
  output wire req_ready,
  input wire [31:0] req_index, req_wdata,
  output wire rsp_valid, rsp_error,
  input wire rsp_ready,
  output wire [31:0] rsp_rdata,
  output wire idle, drain_done, fault,
  output wire memory_req_valid, memory_req_write,
  input wire memory_req_ready,
  output wire [32:0] memory_req_address,
  output wire [511:0] memory_req_wdata,
  output wire [63:0] memory_req_byteenable,
  input wire memory_rsp_valid, memory_rsp_error,
  input wire [511:0] memory_rsp_rdata
);
  localparam INIT=0, INIT_WAIT=1, IDLE=2, BITMAP_REQUEST=3, BITMAP_RESPONSE=4;
  localparam CHECK=5, DATA_REQUEST=6, DATA_RESPONSE=7, MARK_REQUEST=8;
  localparam MARK_RESPONSE=9, RESPONSE=10, ABORT=11, FAULTED=12;
  localparam LEGAL=WORDS>=LOCAL_WORDS && LOCAL_WORDS>=1 &&
    64'(WORDS)*4<=64'h3e000000 && PAGES*64<=64'h02000000;
  reg [3:0] state;
  reg failed, write_command, response_error;
  reg [31:0] clear_page, physical, write_data, response_data;
  reg [32:0] bitmap_address, data_address;
  reg [8:0] bit_index;
  reg [511:0] bitmap;
  wire running=rst_n && LEGAL && !flush;
  wire transport_ready, transport_valid, transport_error, transport_fault, transport_drained;
  wire [511:0] transport_data;
  wire transport_request=running && memory_enable &&
    ((state==INIT && PAGES!=0) || state==BITMAP_REQUEST ||
     state==DATA_REQUEST || state==MARK_REQUEST);
  wire transport_write=state==INIT || state==MARK_REQUEST ||
    (state==DATA_REQUEST && write_command);
  wire [63:0] init_address=64'hfe000000+(64'(clear_page)<<6);
  wire [32:0] transport_address=state==INIT ? init_address[32:0] :
    state==DATA_REQUEST ? data_address : bitmap_address;
  wire [511:0] transport_wdata=state==INIT ? 512'd0 : state==MARK_REQUEST ? bitmap :
    ({480'd0,write_data}<<{physical[3:0],5'd0});
  wire [63:0] transport_byteenable=state==DATA_REQUEST && write_command ?
    64'hf<<{physical[3:0],2'd0} : 64'hffffffffffffffff;
  wire [511:0] selected_data=transport_data>>{physical[3:0],5'd0};
  wire [63:0] requested_data=64'hc0000000+(64'(req_index)<<2);
  wire [63:0] requested_bitmap=64'hfe000000+
    ((64'(req_index)-64'(LOCAL_WORDS))>>9)*64;
  generate if (!LEGAL) begin: invalid_parameters
    initial $fatal(1,"ANVIL_Q3_HT PARAMETER ERROR: scratch backing reservation extent");
  end endgenerate
  assign req_ready=running && state==IDLE && transport_ready;
  assign rsp_valid=running && state==RESPONSE;
  assign rsp_error=rsp_valid && response_error;
  assign rsp_rdata=rsp_valid && !response_error && !write_command ? response_data : 32'd0;
  assign idle=running && state==IDLE && transport_ready;
  assign drain_done=transport_drained;
  assign fault=rst_n && (failed || transport_fault);
  anvil_q3_ht_ddr_record_port record_port (
    .clk(clk),.rst_n(rst_n),.flush(flush || state==ABORT),
    .in_valid(transport_request),.in_ready(transport_ready),
    .in_write(transport_write),.in_address(transport_address),
    .in_wdata(transport_wdata),.in_byteenable(transport_byteenable),
    .out_valid(transport_valid),.out_ready(1'b1),
    .out_error(transport_error),.out_rdata(transport_data),
    .idle(),.drain_done(transport_drained),.fault(transport_fault),
    .memory_req_valid(memory_req_valid),.memory_req_ready(memory_req_ready),
    .memory_req_write(memory_req_write),.memory_req_address(memory_req_address),
    .memory_req_wdata(memory_req_wdata),.memory_req_byteenable(memory_req_byteenable),
    .memory_rsp_valid(memory_rsp_valid),.memory_rsp_error(memory_rsp_error),
    .memory_rsp_rdata(memory_rsp_rdata)
  );
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=INIT; failed<=0; write_command<=0; response_error<=0;
      clear_page<=0; physical<=0; write_data<=0; response_data<=0;
      bitmap_address<=0; data_address<=0; bit_index<=0; bitmap<=0;
    end else if (flush) begin
      state<=ABORT; failed<=0; response_error<=0; response_data<=0; clear_page<=0;
    end else if (state!=ABORT && !failed && transport_fault) begin
      failed<=1; state<=FAULTED;
    end else case (state)
      INIT: if (PAGES==0) state<=IDLE;
        else if (transport_request && transport_ready) state<=INIT_WAIT;
      INIT_WAIT: if (transport_valid) begin
        if (transport_error) begin failed<=1; state<=FAULTED; end
        else if (64'(clear_page)+1==PAGES) state<=IDLE;
        else begin clear_page<=clear_page+1'b1; state<=INIT; end
      end
      IDLE: if (req_valid && req_ready) begin
        physical<=req_index; write_command<=req_write; write_data<=req_wdata;
        bit_index<=9'(req_index-LOCAL_WORDS);
        bitmap_address<=requested_bitmap[32:0];
        data_address<={requested_data[32:6],6'd0};
        response_data<=0; response_error<=0;
        if (req_index<LOCAL_WORDS || req_index>=WORDS ||
            requested_data+4>64'hfe000000 || requested_bitmap+64>64'h100000000) begin
          response_error<=1; state<=RESPONSE;
        end else state<=BITMAP_REQUEST;
      end
      BITMAP_REQUEST: if (transport_request && transport_ready) state<=BITMAP_RESPONSE;
      BITMAP_RESPONSE: if (transport_valid) begin
        if (transport_error) begin response_error<=1; state<=RESPONSE; end
        else begin bitmap<=transport_data; state<=CHECK; end
      end
      CHECK: if (!write_command && !bitmap[bit_index]) begin
        response_error<=1; state<=RESPONSE;
      end else state<=DATA_REQUEST;
      DATA_REQUEST: if (transport_request && transport_ready) state<=DATA_RESPONSE;
      DATA_RESPONSE: if (transport_valid) begin
        if (transport_error) begin response_error<=1; state<=RESPONSE; end
        else if (write_command) begin bitmap[bit_index]<=1; state<=MARK_REQUEST; end
        else begin response_data<=selected_data[31:0]; state<=RESPONSE; end
      end
      MARK_REQUEST: if (transport_request && transport_ready) state<=MARK_RESPONSE;
      MARK_RESPONSE: if (transport_valid) begin response_error<=transport_error; state<=RESPONSE; end
      RESPONSE: if (rsp_ready) begin response_error<=0; response_data<=0; state<=IDLE; end
      ABORT: if (transport_drained && !transport_fault) begin clear_page<=0; state<=INIT; end
      FAULTED: begin end
      default: begin failed<=1; state<=FAULTED; end
    endcase
  end
endmodule
