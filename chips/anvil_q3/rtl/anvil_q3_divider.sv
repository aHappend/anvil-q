module anvil_q3_divider #(
  parameter integer NUM_W=129,
  parameter integer DEN_W=64,
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
  generate if (NUM_W<1 || NUM_W>256 || DEN_W<1 || DEN_W>256) begin: invalid_parameters
    assign ready = 0;
    assign done = 0;
    assign error = 0;
    assign quotient = 0;
    assign remainder = 0;
    initial $fatal(1,"ANVIL_Q3 PARAMETER ERROR: divider widths must be in 1..256");
  end else begin: implementation
    localparam integer CHUNKS=(DW+16)/16;
    localparam integer PAD=CHUNKS*16;
    localparam integer CW=CHUNKS>1 ? $clog2(CHUNKS) : 1;
    localparam integer RW=$clog2(NW+1);
    localparam [1:0] IDLE=0, PREPARE=1, SUBTRACT=2, COMMIT=3;
    reg [1:0] state;
    reg done_reg, error_reg, borrow;
    reg [CW-1:0] segment;
    reg [RW-1:0] remaining;
    reg [NW-1:0] dividend, quotient_reg;
    reg [DW-1:0] remainder_reg;
    reg [PAD-1:0] divisor, trial, difference;
    wire [16:0] segment_difference =
      {1'b0,trial[segment*16+:16]} -
      {1'b0,divisor[segment*16+:16]} - {16'd0,borrow};

    assign ready = rst_n && !flush && state==IDLE;
    assign done = rst_n && !flush && done_reg;
    assign error = done && error_reg;
    assign quotient = rst_n && !flush ? quotient_reg : {NW{1'b0}};
    assign remainder = rst_n && !flush ? remainder_reg : {DW{1'b0}};

    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        state <= IDLE;
        done_reg <= 0;
        error_reg <= 0;
        borrow <= 0;
        segment <= 0;
        remaining <= 0;
        dividend <= 0;
        quotient_reg <= 0;
        remainder_reg <= 0;
        divisor <= 0;
        trial <= 0;
        difference <= 0;
      end else if (flush) begin
        state <= IDLE;
        done_reg <= 0;
        error_reg <= 0;
        quotient_reg <= 0;
        remainder_reg <= 0;
      end else begin
        done_reg <= 0;
        error_reg <= 0;
        case (state)
          IDLE: if (start && ready) begin
            quotient_reg <= 0;
            remainder_reg <= 0;
            if (denominator == 0) begin
              done_reg <= 1;
              error_reg <= 1;
            end else begin
              dividend <= numerator;
              divisor <= {{(PAD-DW){1'b0}},denominator};
              remaining <= RW'(NW);
              state <= PREPARE;
            end
          end
          PREPARE: begin
            trial <= {{(PAD-DW-1){1'b0}},remainder_reg,dividend[NW-1]};
            dividend <= dividend << 1;
            difference <= 0;
            borrow <= 0;
            segment <= 0;
            state <= SUBTRACT;
          end
          SUBTRACT: begin
            difference[segment*16+:16] <= segment_difference[15:0];
            borrow <= segment_difference[16];
            if (segment == CW'(CHUNKS-1)) state <= COMMIT;
            else segment <= segment+1'b1;
          end
          COMMIT: begin
            if (borrow) remainder_reg <= trial[DW-1:0];
            else remainder_reg <= difference[DW-1:0];
            quotient_reg <= (quotient_reg << 1) | {{(NW-1){1'b0}},!borrow};
            remaining <= remaining-1'b1;
            if (remaining == 1) begin
              state <= IDLE;
              done_reg <= 1;
            end else state <= PREPARE;
          end
          default: begin
            state <= IDLE;
            done_reg <= 1;
            error_reg <= 1;
          end
        endcase
      end
    end
  end endgenerate
endmodule
