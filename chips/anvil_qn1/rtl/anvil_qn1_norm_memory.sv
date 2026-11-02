module anvil_qn1_norm_memory #(
  parameter HIDDEN_SIZE=2560
) (
  input wire clk, rst_n, flush, start_valid,
  output wire start_ready,
  input wire [31:0] start_layer, start_source_slot, start_target_slot,
  input wire [3:0] start_gamma_kind,
  output wire done, error,
  output wire req_valid,
  input wire req_ready,
  output wire req_write,
  output wire [3:0] req_kind,
  output wire [31:0] req_layer, req_row, req_col, req_wdata, req_tag,
  input wire rsp_valid,
  output wire rsp_ready,
  input wire [31:0] rsp_data, rsp_tag,
  input wire rsp_error
);
  import anvil_qn1_pkg::*;
  localparam IDLE=0, START=1, INPUT_READ=2, INPUT_WAIT=3, GAMMA_READ=4;
  localparam GAMMA_WAIT=5, INPUT_SEND=6, COMPUTE=7, OUTPUT_WRITE=8;
  localparam OUTPUT_WAIT=9, OUTPUT_RETIRE=10, FINISH=11, FAULT=12;
  reg [3:0] state;
  reg [31:0] layer, source_slot, target_slot, cursor, expected_tag, output_cursor;
  reg [3:0] gamma_kind;
  reg [15:0] captured_data, captured_gamma, output_data;
  reg done_reg, error_reg;
  wire response_expected=state==INPUT_WAIT || state==GAMMA_WAIT || state==OUTPUT_WAIT;
  wire response_bad=rsp_valid && (!response_expected || rsp_error || rsp_tag!=expected_tag ||
    (state!=OUTPUT_WAIT && (rsp_data[31:16]!=0 || bf16_invalid(rsp_data[15:0]))));
  wire unit_flush=flush || state==FAULT;
  wire norm_start_ready, norm_in_ready, norm_out_valid, norm_error, norm_done;
  wire [15:0] norm_data;
  wire [31:0] norm_index;
  wire retiring=state==OUTPUT_RETIRE;
  anvil_qn1_rmsnorm #(.EXTENT(HIDDEN_SIZE)) norm (
    .clk(clk),.rst_n(rst_n),.flush(unit_flush),.start_valid(state==START),
    .start_ready(norm_start_ready),.in_valid(state==INPUT_SEND),.in_ready(norm_in_ready),
    .in_data(captured_data),.in_gamma(captured_gamma),
    .out_valid(norm_out_valid),.out_ready(retiring),.out_index(norm_index),
    .out_data(norm_data),.out_error(norm_error),.done(norm_done)
  );
  assign start_ready=rst_n && !flush && state==IDLE && !done_reg && !error_reg;
  assign done=rst_n && !flush && done_reg;
  assign error=rst_n && !flush && (state==FAULT || error_reg);
  assign req_valid=rst_n && !unit_flush && !response_bad &&
    (state==INPUT_READ || state==GAMMA_READ || state==OUTPUT_WRITE);
  assign req_write=req_valid && state==OUTPUT_WRITE;
  assign req_kind=!req_valid ? 4'd0 : state==GAMMA_READ ? gamma_kind : 4'd8;
  assign req_layer=req_valid && state==GAMMA_READ && gamma_kind!=7 ? layer : 32'd0;
  assign req_row=!req_valid ? 32'd0 : state==GAMMA_READ ? 32'd0 :
    state==INPUT_READ ? source_slot : target_slot;
  assign req_col=!req_valid ? 32'd0 : state==OUTPUT_WRITE ? output_cursor : cursor;
  assign req_wdata=req_write ? {16'd0,output_data} : 32'd0;
  assign req_tag=!req_valid ? 32'd0 : state==OUTPUT_WRITE ?
    {output_cursor[29:0],2'd2} : {cursor[29:0],1'b0,state==GAMMA_READ};
  assign rsp_ready=rst_n && !flush;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; layer<=0; source_slot<=0; target_slot<=0; cursor<=0;
      expected_tag<=0; output_cursor<=0; gamma_kind<=0;
      captured_data<=0; captured_gamma<=0; output_data<=0; done_reg<=0; error_reg<=0;
    end else if (flush) begin
      state<=IDLE; done_reg<=0; error_reg<=0;
    end else begin
      done_reg<=0; error_reg<=0;
      if (response_bad || (norm_out_valid && norm_error)) state<=FAULT;
      else begin
        if (req_valid && req_ready) expected_tag<=req_tag;
        case (state)
          IDLE: if (start_valid && start_ready) begin
            layer<=start_layer; source_slot<=start_source_slot; target_slot<=start_target_slot;
            gamma_kind<=start_gamma_kind; cursor<=0;
            if (start_gamma_kind!=5 && start_gamma_kind!=6 && start_gamma_kind!=7) state<=FAULT;
            else state<=START;
          end
          START: if (norm_start_ready) state<=INPUT_READ;
          INPUT_READ: if (req_valid && req_ready) state<=INPUT_WAIT;
          INPUT_WAIT: if (rsp_valid) begin captured_data<=rsp_data[15:0]; state<=GAMMA_READ; end
          GAMMA_READ: if (req_valid && req_ready) state<=GAMMA_WAIT;
          GAMMA_WAIT: if (rsp_valid) begin captured_gamma<=rsp_data[15:0]; state<=INPUT_SEND; end
          INPUT_SEND: if (norm_in_ready) begin
            if (cursor==HIDDEN_SIZE-1) state<=COMPUTE;
            else begin cursor<=cursor+1'b1; state<=INPUT_READ; end
          end
          COMPUTE: begin
            if (norm_out_valid) begin
              output_cursor<=norm_index; output_data<=norm_data; state<=OUTPUT_WRITE;
            end else if (norm_done) state<=FINISH;
          end
          OUTPUT_WRITE: if (req_valid && req_ready) state<=OUTPUT_WAIT;
          OUTPUT_WAIT: if (rsp_valid) state<=OUTPUT_RETIRE;
          OUTPUT_RETIRE: begin
            if (!norm_out_valid || norm_index!=output_cursor || norm_data!=output_data)
              state<=FAULT;
            else state<=COMPUTE;
          end
          FINISH: begin done_reg<=1; state<=IDLE; end
          FAULT: begin error_reg<=1; state<=IDLE; end
          default: state<=FAULT;
        endcase
      end
    end
  end
endmodule
