module anvil_qn1_scalar (
  input wire clk, rst_n, flush, in_valid,
  output wire in_ready,
  input wire [2:0] in_op,
  input wire [31:0] in_a, in_b,
  input wire in_error,
  output wire out_valid,
  input wire out_ready,
  output wire [31:0] out_data,
  output wire out_error
);
  localparam IDLE=0, LAUNCH=1, RUN=2, HOLD=3;
  reg [1:0] state;
  reg [2:0] operation;
  reg [5:0] elapsed;
  reg [31:0] a, b, data;
  reg failed, result_failed;
  wire [31:0] add_data, mul_data, div_data, sqrt_data;
  wire add_error, mul_error, div_error, sqrt_error, div_done, sqrt_done;
  wire launch=state==LAUNCH;
  wire [31:0] add_b=operation==1 ? {~b[31],b[30:0]} : b;
  anvil_qn1_fp32_add add (
    .clk(clk),.rst_n(rst_n),.flush(flush),.ce(1'b1),
    .a(a),.b(add_b),.in_error(failed),.result(add_data),.out_error(add_error)
  );
  anvil_qn1_fp32_mul multiply (
    .clk(clk),.rst_n(rst_n),.flush(flush),.ce(1'b1),
    .a(a),.b(b),.in_error(failed),.result(mul_data),.out_error(mul_error)
  );
  anvil_qn1_fp32_div divide (
    .clk(clk),.rst_n(rst_n),.flush(flush),.start(launch && operation==3),
    .numerator(a),.denominator(b),.in_error(failed),.ready(),
    .done(div_done),.result(div_data),.out_error(div_error)
  );
  anvil_qn1_fp32_sqrt square_root (
    .clk(clk),.rst_n(rst_n),.flush(flush),.start(launch && operation==4),
    .radicand(a),.in_error(failed),.ready(),.done(sqrt_done),
    .result(sqrt_data),.out_error(sqrt_error)
  );
  assign in_ready=rst_n && !flush && state==IDLE;
  assign out_valid=rst_n && !flush && state==HOLD;
  assign out_data=out_valid ? data : 32'd0;
  assign out_error=out_valid && result_failed;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; operation<=0; elapsed<=0; a<=0; b<=0;
      data<=0; failed<=0; result_failed<=0;
    end else if (flush) begin
      state<=IDLE; data<=0; result_failed<=0;
    end else case (state)
      IDLE: if (in_valid && in_ready) begin
        a<=in_a; b<=in_b; operation<=in_op;
        failed<=in_error || in_op>4; elapsed<=0; state<=LAUNCH;
      end
      LAUNCH: begin elapsed<=1; state<=RUN; end
      RUN: begin
        elapsed<=elapsed+1'b1;
        if ((operation<=1 && elapsed==5) || (operation==2 && elapsed==4) ||
            (operation==3 && div_done) || (operation==4 && sqrt_done) ||
            operation>4) begin
          case (operation)
            0,1: begin data<=add_data; result_failed<=add_error; end
            2: begin data<=mul_data; result_failed<=mul_error; end
            3: begin data<=div_data; result_failed<=div_error; end
            4: begin data<=sqrt_data; result_failed<=sqrt_error; end
            default: begin data<=0; result_failed<=1; end
          endcase
          state<=HOLD;
        end
      end
      HOLD: if (out_ready) state<=IDLE;
      default: state<=IDLE;
    endcase
  end
endmodule
