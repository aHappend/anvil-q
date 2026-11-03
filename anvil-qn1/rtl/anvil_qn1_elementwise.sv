module anvil_qn1_elementwise #(
  parameter HIDDEN_SIZE=2560
) (
  input wire clk, rst_n, flush, start_valid,
  output wire start_ready,
  input wire [31:0] start_a_slot, start_b_slot, start_target_slot,
  output wire done, error,
  output wire req_valid,
  input wire req_ready,
  output wire req_write,
  output wire [3:0] req_kind,
  output wire [31:0] req_row, req_col, req_wdata, req_tag,
  input wire rsp_valid,
  output wire rsp_ready,
  input wire [31:0] rsp_data, rsp_tag,
  input wire rsp_error
);
  import anvil_qn1_pkg::*;
  generate if (HIDDEN_SIZE>=8 && HIDDEN_SIZE<=2560 && (HIDDEN_SIZE & 7)==0) begin: legal
    localparam IDLE=0, READ_A=1, WAIT_A=2, READ_B=3, WAIT_B=4;
    localparam ADD=5, ROUND=6, WRITE=7, WAIT_WRITE=8, FINISH=9, FAULT=10;
    reg [3:0] state;
    reg [31:0] a_slot, b_slot, target_slot, cursor, expected_tag, sum;
    reg [15:0] a, b, result;
    reg waiting, done_reg, error_reg;
    wire response_expected=state==WAIT_A || state==WAIT_B || state==WAIT_WRITE;
    wire response_bad=rsp_valid && (!response_expected || rsp_error || rsp_tag!=expected_tag ||
      (state!=WAIT_WRITE && (rsp_data[31:16]!=0 || bf16_invalid(rsp_data[15:0]))));
    wire unit_flush=flush || state==FAULT;
    wire alu_ready, alu_valid, alu_error;
    wire [31:0] alu_data;
    anvil_qn1_scalar addition (
      .clk(clk),.rst_n(rst_n),.flush(unit_flush),
      .in_valid(state==ADD && !waiting),.in_ready(alu_ready),.in_op(3'd0),
      .in_a({a,16'd0}),.in_b({b,16'd0}),.in_error(1'b0),
      .out_valid(alu_valid),.out_ready(waiting),.out_data(alu_data),.out_error(alu_error)
    );
    wire [16:0] rounded=round_bf16(sum);
    assign start_ready=rst_n && !flush && state==IDLE && !done_reg && !error_reg;
    assign done=rst_n && !flush && done_reg;
    assign error=rst_n && !flush && (state==FAULT || error_reg);
    assign req_valid=rst_n && !unit_flush && !response_bad &&
      (state==READ_A || state==READ_B || state==WRITE);
    assign req_write=req_valid && state==WRITE;
    assign req_kind=req_valid ? 4'd8 : 4'd0;
    assign req_row=!req_valid ? 32'd0 : state==READ_A ? a_slot : state==READ_B ? b_slot : target_slot;
    assign req_col=req_valid ? cursor : 32'd0;
    assign req_wdata=req_write ? {16'd0,result} : 32'd0;
    assign req_tag=req_valid ? {cursor[29:0],state==WRITE,state==READ_B} : 32'd0;
    assign rsp_ready=rst_n && !flush;
    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        state<=IDLE; a_slot<=0; b_slot<=0; target_slot<=0; cursor<=0; expected_tag<=0;
        sum<=0; a<=0; b<=0; result<=0; waiting<=0; done_reg<=0; error_reg<=0;
      end else if (flush) begin
        state<=IDLE; waiting<=0; done_reg<=0; error_reg<=0;
      end else begin
        done_reg<=0; error_reg<=0;
        if (response_bad) state<=FAULT;
        else begin
          if (req_valid && req_ready) expected_tag<=req_tag;
          if (state==ADD && !waiting && alu_ready) waiting<=1;
          case (state)
            IDLE: if (start_valid && start_ready) begin
              a_slot<=start_a_slot; b_slot<=start_b_slot; target_slot<=start_target_slot;
              cursor<=0; waiting<=0; state<=READ_A;
            end
            READ_A: if (req_valid && req_ready) state<=WAIT_A;
            WAIT_A: if (rsp_valid) begin a<=rsp_data[15:0]; state<=READ_B; end
            READ_B: if (req_valid && req_ready) state<=WAIT_B;
            WAIT_B: if (rsp_valid) begin b<=rsp_data[15:0]; state<=ADD; end
            ADD: if (alu_valid && waiting) begin
              waiting<=0;
              if (alu_error) state<=FAULT;
              else begin sum<=alu_data; state<=ROUND; end
            end
            ROUND: begin
              if (rounded[16]) state<=FAULT;
              else begin result<=rounded[15:0]; state<=WRITE; end
            end
            WRITE: if (req_valid && req_ready) state<=WAIT_WRITE;
            WAIT_WRITE: if (rsp_valid) begin
              if (cursor==HIDDEN_SIZE-1) state<=FINISH;
              else begin cursor<=cursor+1'b1; state<=READ_A; end
            end
            FINISH: begin done_reg<=1; state<=IDLE; end
            FAULT: begin error_reg<=1; waiting<=0; state<=IDLE; end
            default: state<=FAULT;
          endcase
        end
      end
    end
  end else begin: invalid
    initial $fatal(1,"ANVIL_QN1 PARAMETER ERROR: residual geometry");
    assign start_ready=0; assign done=0; assign error=0; assign req_valid=0;
    assign req_write=0; assign req_kind=0; assign req_row=0; assign req_col=0;
    assign req_wdata=0; assign req_tag=0; assign rsp_ready=0;
  end endgenerate
endmodule
