module anvil_qn1_mlp #(
  parameter HIDDEN_SIZE=2560, INTERMEDIATE_SIZE=9728
) (
  input wire clk, rst_n, flush, start_valid,
  output wire start_ready,
  input wire [31:0] start_layer,
  output wire done, error,
  output wire gemv_valid,
  input wire gemv_ready,
  output wire [2:0] gemv_proj,
  output wire [31:0] gemv_layer, gemv_input_extent, gemv_output_extent,
    gemv_source_slot, gemv_target_slot,
  input wire gemv_done, gemv_error,
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
  generate if (HIDDEN_SIZE>=8 && HIDDEN_SIZE<=2560 && (HIDDEN_SIZE & 7)==0 &&
      INTERMEDIATE_SIZE>=8 && INTERMEDIATE_SIZE<=9728 &&
      (INTERMEDIATE_SIZE & 7)==0) begin: legal
    localparam IDLE=0, GATE=1, GATE_WAIT=2, UP=3, UP_WAIT=4, GATE_READ=5;
    localparam GATE_RSP=6, UP_READ=7, UP_RSP=8, SILU_REQ=9, SILU_WAIT=10;
    localparam PRODUCT=11, ROUND=12, WRITE=13, WRITE_RSP=14;
    localparam DOWN=15, DOWN_WAIT=16, FINISH=17, FAULT=18;
    reg [4:0] state;
    reg waiting, done_reg, error_reg;
    reg [31:0] layer, cursor, expected_tag, product;
    reg [15:0] gate, up, activated, result;
    wire response_expected=state==GATE_RSP || state==UP_RSP || state==WRITE_RSP;
    wire response_bad=rsp_valid && (!response_expected || rsp_error || rsp_tag!=expected_tag ||
      (state!=WRITE_RSP && (rsp_data[31:16]!=0 || bf16_invalid(rsp_data[15:0]))));
    wire projection_wait=state==GATE_WAIT || state==UP_WAIT || state==DOWN_WAIT;
    wire unit_flush=flush || state==FAULT;
    wire silu_ready, silu_valid, silu_error;
    wire [15:0] silu_data;
    anvil_qn1_silu silu (
      .clk(clk),.rst_n(rst_n),.flush(unit_flush),.in_valid(state==SILU_REQ),
      .in_ready(silu_ready),.in_data(gate),.out_valid(silu_valid),
      .out_ready(state==SILU_WAIT),.out_data(silu_data),.out_error(silu_error)
    );
    wire alu_ready, alu_valid, alu_error;
    wire [31:0] alu_data;
    anvil_qn1_scalar multiply (
      .clk(clk),.rst_n(rst_n),.flush(unit_flush),
      .in_valid(state==PRODUCT && !waiting),.in_ready(alu_ready),
      .in_op(3'd2),.in_a({activated,16'd0}),.in_b({up,16'd0}),.in_error(1'b0),
      .out_valid(alu_valid),.out_ready(waiting),.out_data(alu_data),.out_error(alu_error)
    );
    wire [16:0] rounded=round_bf16(product);
    assign start_ready=rst_n && !flush && state==IDLE && !done_reg && !error_reg;
    assign done=rst_n && !flush && done_reg;
    assign error=rst_n && !flush && (state==FAULT || error_reg);
    assign gemv_valid=rst_n && !unit_flush && !response_bad &&
      (state==GATE || state==UP || state==DOWN);
    assign gemv_proj=!gemv_valid ? 3'd0 : state==GATE ? 3'd4 : state==UP ? 3'd5 : 3'd6;
    assign gemv_layer=gemv_valid ? layer : 32'd0;
    assign gemv_input_extent=!gemv_valid ? 32'd0 : state==DOWN ? INTERMEDIATE_SIZE : HIDDEN_SIZE;
    assign gemv_output_extent=!gemv_valid ? 32'd0 : state==DOWN ? HIDDEN_SIZE : INTERMEDIATE_SIZE;
    assign gemv_source_slot=!gemv_valid ? 32'd0 : state==DOWN ? 32'd11 : 32'd8;
    assign gemv_target_slot=!gemv_valid ? 32'd0 : state==GATE ? 32'd9 :
      state==UP ? 32'd10 : 32'd12;
    assign req_valid=rst_n && !unit_flush && !response_bad &&
      (state==GATE_READ || state==UP_READ || state==WRITE);
    assign req_write=req_valid && state==WRITE;
    assign req_kind=req_valid ? 4'd8 : 4'd0;
    assign req_row=!req_valid ? 32'd0 : state==GATE_READ ? 32'd9 :
      state==UP_READ ? 32'd10 : 32'd11;
    assign req_col=req_valid ? cursor : 32'd0;
    assign req_wdata=req_write ? {16'd0,result} : 32'd0;
    assign req_tag=req_valid ? {cursor[28:0],state==WRITE,state==UP_READ,1'b0} : 32'd0;
    assign rsp_ready=rst_n && !flush;
    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        state<=IDLE; waiting<=0; done_reg<=0; error_reg<=0; layer<=0; cursor<=0;
        expected_tag<=0; product<=0; gate<=0; up<=0; activated<=0; result<=0;
      end else if (flush) begin
        state<=IDLE; waiting<=0; done_reg<=0; error_reg<=0;
      end else begin
        done_reg<=0; error_reg<=0;
        if (response_bad || (gemv_done && !projection_wait) || gemv_error) state<=FAULT;
        else begin
          if (req_valid && req_ready) expected_tag<=req_tag;
          if (state==PRODUCT && !waiting && alu_ready) waiting<=1;
          case (state)
            IDLE: if (start_valid && start_ready) begin
              layer<=start_layer; cursor<=0; waiting<=0; state<=GATE;
            end
            GATE: if (gemv_valid && gemv_ready) state<=GATE_WAIT;
            GATE_WAIT: if (gemv_done) state<=UP;
            UP: if (gemv_valid && gemv_ready) state<=UP_WAIT;
            UP_WAIT: if (gemv_done) state<=GATE_READ;
            GATE_READ: if (req_valid && req_ready) state<=GATE_RSP;
            GATE_RSP: if (rsp_valid) begin gate<=rsp_data[15:0]; state<=UP_READ; end
            UP_READ: if (req_valid && req_ready) state<=UP_RSP;
            UP_RSP: if (rsp_valid) begin up<=rsp_data[15:0]; state<=SILU_REQ; end
            SILU_REQ: if (silu_ready) state<=SILU_WAIT;
            SILU_WAIT: if (silu_valid) begin
              if (silu_error) state<=FAULT;
              else begin activated<=silu_data; state<=PRODUCT; end
            end
            PRODUCT: if (alu_valid && waiting) begin
              waiting<=0;
              if (alu_error) state<=FAULT;
              else begin product<=alu_data; state<=ROUND; end
            end
            ROUND: begin
              if (rounded[16]) state<=FAULT;
              else begin result<=rounded[15:0]; state<=WRITE; end
            end
            WRITE: if (req_valid && req_ready) state<=WRITE_RSP;
            WRITE_RSP: if (rsp_valid) begin
              if (cursor==INTERMEDIATE_SIZE-1) state<=DOWN;
              else begin cursor<=cursor+1'b1; state<=GATE_READ; end
            end
            DOWN: if (gemv_valid && gemv_ready) state<=DOWN_WAIT;
            DOWN_WAIT: if (gemv_done) state<=FINISH;
            FINISH: begin done_reg<=1; state<=IDLE; end
            FAULT: begin error_reg<=1; waiting<=0; state<=IDLE; end
            default: state<=FAULT;
          endcase
        end
      end
    end
  end else begin: invalid
    initial $fatal(1,"ANVIL_QN1 PARAMETER ERROR: MLP geometry");
    assign start_ready=0; assign done=0; assign error=0; assign gemv_valid=0;
    assign gemv_proj=0; assign gemv_layer=0; assign gemv_input_extent=0;
    assign gemv_output_extent=0; assign gemv_source_slot=0; assign gemv_target_slot=0;
    assign req_valid=0; assign req_write=0; assign req_kind=0;
    assign req_row=0; assign req_col=0; assign req_wdata=0; assign req_tag=0; assign rsp_ready=0;
  end endgenerate
endmodule
