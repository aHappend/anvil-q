module anvil_q1_ht3_scalar (
  input wire clk, rst_n, req_valid,
  output wire req_ready,
  input wire [2:0] req_opcode,
  input wire [31:0] req_a, req_b,
  output wire rsp_valid,
  input wire rsp_ready,
  output wire [31:0] rsp_data,
  output wire rsp_error
);
  import anvil_q1_ht3_fp_pkg::*;
  localparam IDLE = 2'd0, ISSUE = 2'd1, WAIT = 2'd2, RESPONSE = 2'd3;
  wire run_n;
  reg [1:0] state;
  reg [2:0] opcode;
  reg [31:0] a_q, b_q, result_q;
  reg error_q;
  wire add_valid, mul_valid, div_valid, div_ready, exp_valid;
  wire [31:0] add_data, mul_data, div_data, exp_data;
  reg complete;
  reg [31:0] result;
  wire operands_bad = fp32_nonfinite(req_a) ||
    (req_opcode <= 2 && fp32_nonfinite(req_b));
  wire issue = run_n && state == ISSUE &&
    ((opcode != 2 && opcode != 3) || div_ready);
  anvil_q1_ht3_reset_sync u_reset(clk, rst_n, run_n);
  anvil_q1_ht3_fp32_add u_add (
    .clk(clk), .rst_n(rst_n), .enable(1'b1),
    .in_valid(issue && opcode == 0), .in_a(a_q), .in_b(b_q),
    .out_valid(add_valid), .out_data(add_data)
  );
  anvil_q1_ht3_fp32_mul u_mul (
    .clk(clk), .rst_n(rst_n), .enable(1'b1),
    .in_valid(issue && opcode == 1), .in_a(a_q), .in_b(b_q),
    .out_valid(mul_valid), .out_data(mul_data)
  );
  anvil_q1_ht3_fp32_divsqrt u_divsqrt (
    .clk(clk), .rst_n(rst_n), .enable(1'b1),
    .req_valid(issue && (opcode == 2 || opcode == 3)),
    .req_ready(div_ready), .req_sqrt(opcode == 3), .req_a(a_q), .req_b(b_q),
    .rsp_valid(div_valid), .rsp_ready(state == WAIT), .rsp_data(div_data)
  );
  anvil_q1_ht3_fp32_exp u_exp (
    .clk(clk), .rst_n(rst_n), .enable(1'b1),
    .in_valid(issue && opcode == 4), .in_data(a_q),
    .out_valid(exp_valid), .out_data(exp_data)
  );
  assign req_ready = run_n && state == IDLE;
  assign rsp_valid = run_n && state == RESPONSE;
  assign rsp_data = rsp_valid ? result_q : 32'b0;
  assign rsp_error = rsp_valid && error_q;
  always @* begin
    complete = 0;
    result = FP32_QNAN;
    case (opcode)
      0: begin complete = add_valid; result = add_data; end
      1: begin complete = mul_valid; result = mul_data; end
      2, 3: begin complete = div_valid; result = div_data; end
      4: begin complete = exp_valid; result = exp_data; end
      default: begin end
    endcase
  end
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state <= IDLE;
      opcode <= 0;
      a_q <= 0;
      b_q <= 0;
      result_q <= 0;
      error_q <= 0;
    end else if (run_n) begin
      case (state)
        IDLE: if (req_valid && req_ready) begin
          opcode <= req_opcode;
          a_q <= req_a;
          b_q <= req_b;
          error_q <= operands_bad || req_opcode > 4;
          if (operands_bad || req_opcode > 4) begin
            result_q <= FP32_QNAN;
            state <= RESPONSE;
          end else state <= ISSUE;
        end
        ISSUE: if (issue) state <= WAIT;
        WAIT: if (complete) begin
          result_q <= result;
          error_q <= fp32_nonfinite(result);
          state <= RESPONSE;
        end
        RESPONSE: if (rsp_ready) state <= IDLE;
        default: begin
          result_q <= FP32_QNAN;
          error_q <= 1;
          state <= RESPONSE;
        end
      endcase
    end
  end
endmodule
