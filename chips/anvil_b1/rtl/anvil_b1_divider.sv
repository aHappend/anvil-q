module anvil_b1_divider #(
  parameter integer NUM_W=128, DEN_W=64,
  localparam integer NW=(NUM_W>=1 && NUM_W<=256) ? NUM_W : 1,
  localparam integer DW=(DEN_W>=1 && DEN_W<=256) ? DEN_W : 1
) (
  input wire clk, rst_n, flush, start,
  input wire [NW-1:0] numerator,
  input wire [DW-1:0] denominator,
  output wire ready, done, error,
  output wire [NW-1:0] quotient,
  output wire [DW-1:0] remainder
);
  localparam integer SEGMENTS=(DW+16)/16, PAD=SEGMENTS*16;
  localparam IDLE=0, PREPARE=1, SUBTRACT=2, COMMIT=3, BAD=4;
  reg [2:0] state;
  reg done_reg, error_reg, borrow;
  reg [4:0] segment;
  reg [8:0] remaining;
  reg [NW-1:0] source, quotient_reg;
  reg [DW-1:0] remainder_reg;
  reg [PAD-1:0] divisor, trial, difference;
  wire [16:0] delta={1'b0,trial[segment*16+:16]}-
    {1'b0,divisor[segment*16+:16]}-{16'd0,borrow};
  generate if (NUM_W<1 || NUM_W>256 || DEN_W<1 || DEN_W>256) begin: invalid_parameters
    initial $fatal(1,"B1 PARAMETER ERROR: divider widths");
  end endgenerate
  assign ready=rst_n && !flush && state==IDLE;
  assign done=rst_n && !flush && done_reg;
  assign error=done && error_reg;
  assign quotient=rst_n && !flush ? quotient_reg : {NW{1'b0}};
  assign remainder=rst_n && !flush ? remainder_reg : {DW{1'b0}};
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; done_reg<=0; error_reg<=0; borrow<=0;
      segment<=0; remaining<=0; source<=0; quotient_reg<=0;
      remainder_reg<=0; divisor<=0; trial<=0; difference<=0;
    end else if (flush) begin
      state<=IDLE; done_reg<=0; error_reg<=0; quotient_reg<=0; remainder_reg<=0;
    end else begin
      done_reg<=0; error_reg<=0;
      case (state)
        IDLE: if (start && ready) begin
          quotient_reg<=0; remainder_reg<=0;
          if (denominator==0) state<=BAD;
          else begin
            source<=numerator; divisor<={{(PAD-DW){1'b0}},denominator};
            remaining<=NW; state<=PREPARE;
          end
        end
        PREPARE: begin
          trial<={{(PAD-DW-1){1'b0}},remainder_reg,source[NW-1]};
          source<=source<<1; difference<=0; borrow<=0; segment<=0;
          state<=SUBTRACT;
        end
        SUBTRACT: begin
          difference[segment*16+:16]<=delta[15:0]; borrow<=delta[16];
          if (segment+1==SEGMENTS) state<=COMMIT;
          else segment<=segment+1'b1;
        end
        COMMIT: begin
          remainder_reg<=borrow ? trial[DW-1:0] : difference[DW-1:0];
          quotient_reg<=(quotient_reg<<1) | {{(NW-1){1'b0}},!borrow};
          remaining<=remaining-1'b1;
          if (remaining==1) begin state<=IDLE; done_reg<=1; end
          else state<=PREPARE;
        end
        BAD: begin state<=IDLE; done_reg<=1; error_reg<=1; end
        default: state<=BAD;
      endcase
    end
  end
endmodule
