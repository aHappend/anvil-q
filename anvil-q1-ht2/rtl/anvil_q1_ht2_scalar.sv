module anvil_q1_ht2_scalar (
  input wire clk, rst_n, enable, req_valid,
  output wire req_ready,
  input wire [2:0] req_opcode,
  input wire [31:0] req_a, req_b,
  output wire rsp_valid,
  input wire rsp_ready,
  output wire [31:0] rsp_data, rsp_aux,
  output wire rsp_error
);
  import anvil_q1_ht2_fp_pkg::*;
  localparam IDLE = 2'd0, ISSUE = 2'd1, WAIT_RESULT = 2'd2, RESPONSE = 2'd3;
  wire run_n;
  reg [1:0] state;
  reg [2:0] opcode;
  reg [31:0] a, b, result, auxiliary;
  reg failed;
  wire add_valid, multiply_valid, divide_valid, exp_valid, trig_valid;
  wire divide_ready, exp_ready, trig_ready, trig_error;
  wire [31:0] add_data, multiply_data, divide_data, exp_data, trig_sin, trig_cos;
  wire issue = run_n && enable && state == ISSUE;
  wire consume = run_n && enable && state == WAIT_RESULT;
  wire selected_valid = opcode == 0 ? add_valid :
    opcode == 1 ? multiply_valid :
    (opcode == 2 || opcode == 3) ? divide_valid :
    opcode == 4 ? exp_valid : trig_valid;
  wire [31:0] selected_data = opcode == 0 ? add_data :
    opcode == 1 ? multiply_data :
    (opcode == 2 || opcode == 3) ? divide_data :
    opcode == 4 ? exp_data : trig_sin;

  anvil_q1_ht2_reset_sync u_reset(clk, rst_n, run_n);
  anvil_q1_ht2_fp32_add u_add (
    .clk(clk), .rst_n(run_n), .enable(enable), .in_valid(issue && opcode == 0),
    .in_a(a), .in_b(b), .out_valid(add_valid), .out_data(add_data)
  );
  anvil_q1_ht2_fp32_mul u_multiply (
    .clk(clk), .rst_n(run_n), .enable(enable), .in_valid(issue && opcode == 1),
    .in_a(a), .in_b(b), .out_valid(multiply_valid), .out_data(multiply_data)
  );
  anvil_q1_ht2_fp32_divsqrt u_divide (
    .clk(clk), .rst_n(run_n), .enable(enable),
    .req_valid(issue && (opcode == 2 || opcode == 3)), .req_ready(divide_ready),
    .req_sqrt(opcode == 3), .req_a(a), .req_b(b),
    .rsp_valid(divide_valid), .rsp_ready(consume && (opcode == 2 || opcode == 3)),
    .rsp_data(divide_data)
  );
  anvil_q1_ht2_fp32_exp u_exp (
    .clk(clk), .rst_n(run_n), .enable(enable),
    .req_valid(issue && opcode == 4), .req_ready(exp_ready), .req_data(a),
    .rsp_valid(exp_valid), .rsp_ready(consume && opcode == 4), .rsp_data(exp_data)
  );
  anvil_q1_ht2_fp32_sincos u_sincos (
    .clk(clk), .rst_n(run_n), .enable(enable),
    .req_valid(issue && opcode == 5), .req_ready(trig_ready), .req_data(a),
    .rsp_valid(trig_valid), .rsp_ready(consume && opcode == 5),
    .rsp_sin(trig_sin), .rsp_cos(trig_cos), .rsp_error(trig_error)
  );
  assign req_ready = run_n && enable && state == IDLE;
  assign rsp_valid = run_n && state == RESPONSE;
  assign rsp_data = rsp_valid ? result : 32'b0;
  assign rsp_aux = rsp_valid ? auxiliary : 32'b0;
  assign rsp_error = rsp_valid && failed;

  always @(posedge clk or negedge run_n) begin
    if (!run_n) begin
      state <= IDLE;
      opcode <= 0;
      a <= 0;
      b <= 0;
      result <= 0;
      auxiliary <= 0;
      failed <= 0;
    end else if (state == RESPONSE) begin
      if (rsp_valid && rsp_ready) state <= IDLE;
    end else if (enable) case (state)
      IDLE: if (req_valid && req_ready) begin
        opcode <= req_opcode;
        a <= req_a;
        b <= req_b;
        result <= 0;
        auxiliary <= 0;
        failed <= 0;
        if (req_opcode > 5 || fp32_nonfinite(req_a) ||
            (req_opcode <= 2 && fp32_nonfinite(req_b))) begin
          failed <= 1;
          result <= FP32_QNAN;
          state <= RESPONSE;
        end else state <= ISSUE;
      end
      ISSUE: if (opcode <= 1 || ((opcode == 2 || opcode == 3) && divide_ready) ||
                 (opcode == 4 && exp_ready) || (opcode == 5 && trig_ready))
        state <= WAIT_RESULT;
      WAIT_RESULT: if (selected_valid) begin
        result <= selected_data;
        auxiliary <= opcode == 5 ? trig_cos : 32'b0;
        failed <= fp32_nonfinite(selected_data) ||
          (opcode == 5 && (trig_error || fp32_nonfinite(trig_cos)));
        state <= RESPONSE;
      end
      default: begin failed <= 1; result <= FP32_QNAN; state <= RESPONSE; end
    endcase
  end
endmodule
