module anvil_q2_fp_exp(
  input wire clk, rst_n,
  input wire in_valid, output wire in_ready,
  input wire [31:0] in_x,
  output wire out_valid, input wire out_ready,
  output wire [31:0] out_data,
  output wire out_error
);
  import anvil_q2_fp_pkg::*;
  localparam IDLE=0, RANGE_MUL=1, RANGE_WAIT=2, INTEGER_CONVERT=3,
    LN_MUL=4, LN_WAIT=5, REDUCE_ADD=6, REDUCE_WAIT=7,
    HORNER_MUL=8, HORNER_MUL_WAIT=9, HORNER_ADD=10, HORNER_ADD_WAIT=11,
    SCALE=12, SCALE_WAIT=13, OUTPUT=14;
  reg [3:0] state;
  reg [31:0] x, reduced, partial, result;
  reg signed [31:0] n;
  reg [2:0] coefficient;
  reg failed;
  reg alu_valid;
  wire alu_ready, alu_out_valid, alu_error;
  wire [31:0] alu_result;
  reg [2:0] alu_op;
  reg [31:0] alu_a, alu_b;

  function automatic [31:0] taylor_coefficient(input [2:0] k);
    begin
      case (k)
        0,1: taylor_coefficient=32'h3f800000;
        2: taylor_coefficient=32'h3f000000;
        3: taylor_coefficient=32'h3e2aaaab;
        4: taylor_coefficient=32'h3d2aaaab;
        5: taylor_coefficient=32'h3c088889;
        6: taylor_coefficient=32'h3ab60b61;
        default: taylor_coefficient=32'h39500d01;
      endcase
    end
  endfunction

  assign in_ready=rst_n && state==IDLE;
  assign out_valid=rst_n && state==OUTPUT;
  assign out_data=rst_n ? result : 32'd0;
  assign out_error=out_valid && failed;
  anvil_q2_fp_scalar arithmetic(
    .clk(clk),.rst_n(rst_n),.in_valid(alu_valid),.in_ready(alu_ready),
    .in_op(alu_op),.in_a(alu_a),.in_b(alu_b),
    .out_valid(alu_out_valid),.out_ready(1'b1),
    .out_data(alu_result),.out_error(alu_error));

  always @* begin
    alu_valid=0; alu_op=0; alu_a=0; alu_b=0;
    if (rst_n) case (state)
      RANGE_MUL: begin alu_valid=1; alu_op=1; alu_a=x; alu_b=32'h3fb8aa3b; end
      LN_MUL: begin alu_valid=1; alu_op=1; alu_a=fp_from_int(n); alu_b=32'h3f317218; end
      REDUCE_ADD: begin alu_valid=1; alu_a=x; alu_b={~partial[31],partial[30:0]}; end
      HORNER_MUL: begin alu_valid=1; alu_op=1; alu_a=partial; alu_b=reduced; end
      HORNER_ADD: begin alu_valid=1; alu_a=partial; alu_b=taylor_coefficient(coefficient); end
      SCALE: begin alu_valid=1; alu_op=4; alu_a=partial; alu_b=n; end
      default: begin end
    endcase
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; x<=0; reduced<=0; partial<=0; result<=0;
      n<=0; coefficient<=0; failed<=0;
    end else if (alu_out_valid && alu_error) begin
      failed<=1; result<=alu_result; state<=OUTPUT;
    end else case (state)
      IDLE: if (in_valid) begin
        failed<=0; x<=in_x;
        if (!fp_is_finite(in_x) || (!in_x[31] && !fp_is_zero(in_x))) begin
          failed<=1; result<=FP_NAN; state<=OUTPUT;
        end else if (fp_is_zero(in_x)) begin result<=FP_ONE; state<=OUTPUT; end
        else if (in_x[30:0]>31'h42a00000) begin result<=FP_ZERO; state<=OUTPUT; end
        else state<=RANGE_MUL;
      end
      RANGE_MUL: if (alu_ready) state<=RANGE_WAIT;
      RANGE_WAIT: if (alu_out_valid) begin partial<=alu_result; state<=INTEGER_CONVERT; end
      INTEGER_CONVERT: begin n<=fp_to_int_rne(partial); state<=LN_MUL; end
      LN_MUL: if (alu_ready) state<=LN_WAIT;
      LN_WAIT: if (alu_out_valid) begin partial<=alu_result; state<=REDUCE_ADD; end
      REDUCE_ADD: if (alu_ready) state<=REDUCE_WAIT;
      REDUCE_WAIT: if (alu_out_valid) begin
        reduced<=alu_result; partial<=taylor_coefficient(7);
        coefficient<=6; state<=HORNER_MUL;
      end
      HORNER_MUL: if (alu_ready) state<=HORNER_MUL_WAIT;
      HORNER_MUL_WAIT: if (alu_out_valid) begin partial<=alu_result; state<=HORNER_ADD; end
      HORNER_ADD: if (alu_ready) state<=HORNER_ADD_WAIT;
      HORNER_ADD_WAIT: if (alu_out_valid) begin
        partial<=alu_result;
        if (coefficient==0) state<=SCALE;
        else begin coefficient<=coefficient-1'b1; state<=HORNER_MUL; end
      end
      SCALE: if (alu_ready) state<=SCALE_WAIT;
      SCALE_WAIT: if (alu_out_valid) begin result<=alu_result; state<=OUTPUT; end
      OUTPUT: if (out_ready) state<=IDLE;
      default: begin failed<=1; result<=FP_NAN; state<=OUTPUT; end
    endcase
  end
endmodule
