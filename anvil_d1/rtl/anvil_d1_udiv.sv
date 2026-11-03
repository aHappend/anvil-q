module anvil_d1_udiv #(
  parameter integer NUM_W=128, DEN_W=64,
  localparam integer NW=(NUM_W>=1 && NUM_W<=128) ? NUM_W : 1,
  localparam integer DW=(DEN_W>=1 && DEN_W<=128) ? DEN_W : 1,
  localparam integer CW=$clog2(NW+1)
) (
  input wire clk, rst_n, flush, in_valid,
  output wire in_ready,
  input wire [NW-1:0] numerator,
  input wire [DW-1:0] denominator,
  output wire out_valid,
  input wire out_ready,
  output wire out_error,
  output wire [NW-1:0] quotient,
  output wire [DW-1:0] remainder
);
  localparam IDLE=0, ITERATE=1, REGISTER=2;
  reg [1:0] state;
  reg armed, valid, failed;
  reg [CW-1:0] count;
  reg [NW-1:0] input_shift, q, result_q;
  reg [DW-1:0] divisor, rem_work, result_r;
  wire [DW:0] shifted={rem_work,input_shift[NW-1]};
  wire [DW:0] difference;
  wire borrow;
  wire bit_result=!borrow;
  anvil_d1_sub_unsigned #(.WIDTH(DW+1)) subtract (
    .a(shifted),.b({1'b0,divisor}),.difference(difference),.borrow(borrow)
  );
  assign in_ready=rst_n && armed && !flush && state==IDLE && !valid;
  assign out_valid=rst_n && !flush && valid;
  assign out_error=out_valid && failed;
  assign quotient=rst_n && !flush ? result_q : {NW{1'b0}};
  assign remainder=rst_n && !flush ? result_r : {DW{1'b0}};
  generate if (NUM_W<1 || NUM_W>128 || DEN_W<1 || DEN_W>128) begin: invalid_parameters
    initial $fatal(1,"ANVIL_D1 PARAMETER ERROR: divider widths");
  end endgenerate
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; armed<=0; valid<=0; failed<=0; count<=0;
      input_shift<=0; q<=0; result_q<=0; divisor<=0; rem_work<=0; result_r<=0;
    end else begin
      armed<=1;
      if (flush) begin
        state<=IDLE; valid<=0; failed<=0; result_q<=0; result_r<=0;
      end else begin
        if (out_valid && out_ready) valid<=0;
        case (state)
          IDLE: if (in_valid && in_ready) begin
            input_shift<=numerator; divisor<=denominator;
            q<=0; rem_work<=0; count<=0; failed<=denominator==0; state<=ITERATE;
          end
          ITERATE: begin
            input_shift<=input_shift<<1;
            q<=(q<<1) | {{(NW-1){1'b0}},bit_result};
            rem_work<=borrow ? shifted[DW-1:0] : difference[DW-1:0];
            if (count==NW-1) state<=REGISTER;
            else count<=count+1'b1;
          end
          REGISTER: begin
            result_q<=q; result_r<=rem_work; valid<=1; state<=IDLE;
          end
          default: begin state<=IDLE; failed<=1; valid<=1; end
        endcase
      end
    end
  end
endmodule
