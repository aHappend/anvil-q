module anvil_qn1_exp (
  input wire clk, rst_n, flush, in_valid,
  output wire in_ready,
  input wire [31:0] in_data,
  output wire out_valid,
  input wire out_ready,
  output wire [31:0] out_data,
  output wire out_error
);
  import anvil_qn1_pkg::*;
  localparam IDLE=0, REDUCE=1, MULTIPLE=2, RESIDUAL=3, TERM_MUL=4;
  localparam TERM_DIV=5, SUM=6, SCALE=7, HOLD=8;
  reg [3:0] state;
  reg waiting, failed;
  reg [31:0] x, r, term, sum, temporary, result;
  reg [28:0] remainder;
  reg [4:0] exponent;
  reg [2:0] order;
  reg [2:0] op;
  reg [31:0] a, b;
  wire arithmetic_state=state>=MULTIPLE && state<=SUM;
  wire alu_valid=rst_n && !flush && arithmetic_state && !waiting;
  wire alu_ready, alu_out_valid, alu_error;
  wire [31:0] alu_data;
  wire [31:0] exponent32=unsigned32_to_fp32({27'd0,exponent});
  wire [31:0] order32=unsigned32_to_fp32({29'd0,order});
  wire [31:0] clamped=sum[31] ? 32'd0 :
    fp32_greater(sum,32'h3f800000) ? 32'h3f800000 : sum;
  wire [32:0] scaled=scale32(clamped,-$signed({7'd0,exponent}));
  always @* begin
    op=0; a=0; b=0;
    case (state)
      MULTIPLE: begin op=2; a=exponent32; b=32'h3f317218; end
      RESIDUAL: begin op=0; a=x; b=temporary; end
      TERM_MUL: begin op=2; a=term; b=r; end
      TERM_DIV: begin op=3; a=temporary; b=order32; end
      SUM: begin op=0; a=sum; b=term; end
      default: begin op=0; a=0; b=0; end
    endcase
  end
  anvil_qn1_scalar arithmetic (
    .clk(clk),.rst_n(rst_n),.flush(flush),.in_valid(alu_valid),
    .in_ready(alu_ready),.in_op(op),.in_a(a),.in_b(b),.in_error(1'b0),
    .out_valid(alu_out_valid),.out_ready(waiting),.out_data(alu_data),
    .out_error(alu_error)
  );
  assign in_ready=rst_n && !flush && state==IDLE;
  assign out_valid=rst_n && !flush && state==HOLD;
  assign out_data=out_valid ? result : 32'd0;
  assign out_error=out_valid && failed;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; waiting<=0; failed<=0; x<=0; r<=0; term<=0;
      sum<=0; temporary<=0; result<=0; remainder<=0; exponent<=0; order<=0;
    end else if (flush) begin
      state<=IDLE; waiting<=0; failed<=0; result<=0;
    end else begin
      if (alu_valid && alu_ready) waiting<=1;
      if (alu_out_valid && waiting) begin
        waiting<=0;
        if (alu_error) begin failed<=1; result<=0; state<=HOLD; end
        else case (state)
          MULTIPLE: begin temporary<=alu_data; state<=RESIDUAL; end
          RESIDUAL: begin
            r<=alu_data; term<=32'h3f800000; sum<=32'h3f800000;
            order<=1; state<=TERM_MUL;
          end
          TERM_MUL: begin temporary<=alu_data; state<=TERM_DIV; end
          TERM_DIV: begin term<=alu_data; state<=SUM; end
          SUM: begin
            sum<=alu_data;
            if (order==6) state<=SCALE;
            else begin order<=order+1'b1; state<=TERM_MUL; end
          end
          default: begin failed<=1; result<=0; state<=HOLD; end
        endcase
      end else case (state)
        IDLE: if (in_valid && in_ready) begin
          x<=in_data; exponent<=0; failed<=0; waiting<=0;
          if (fp32_invalid(in_data) || (!in_data[31] && in_data[30:0]!=0)) begin
            failed<=1; result<=0; state<=HOLD;
          end else if (in_data[30:0]==0) begin result<=32'h3f800000; state<=HOLD; end
          else if (in_data[30:0]>31'h41800000) begin result<=0; state<=HOLD; end
          else begin
            remainder<=in_data[30:0]<31'h3f317218 ? 29'd0 :
              {5'd0,1'b1,in_data[22:0]} << (in_data[30:23]-8'd126);
            state<=REDUCE;
          end
        end
        REDUCE: begin
          // Exact represented-value range reduction; no rounded quotient.
          if (remainder>=29'h0b17218) begin
            remainder<=remainder-29'h0b17218; exponent<=exponent+1'b1;
          end else state<=MULTIPLE;
        end
        SCALE: begin
          result<=scaled[32] ? 32'd0 : scaled[31:0];
          failed<=scaled[32]; state<=HOLD;
        end
        HOLD: if (out_ready) state<=IDLE;
        default: begin end
      endcase
    end
  end
endmodule
