module anvil_q1_ht_divide #(
  parameter WIDTH = 128
) (
  input wire clk,
  input wire rst_n,
  input wire in_valid,
  output wire in_ready,
  input wire [(WIDTH > 0 ? WIDTH : 1)-1:0] numerator,
  input wire [(WIDTH > 0 ? WIDTH : 1)-1:0] denominator,
  output wire out_valid,
  input wire out_ready,
  output wire [(WIDTH > 0 ? WIDTH : 1)-1:0] quotient,
  output wire [(WIDTH > 0 ? WIDTH : 1)-1:0] remainder,
  output wire divide_by_zero
);
  generate
    if (WIDTH >= 1 && WIDTH <= 129) begin : g_legal
      localparam CHUNKS = (WIDTH + 32) >> 5;
      localparam PAD = CHUNKS << 5;
      localparam IDLE = 3'd0, SHIFT = 3'd1, SUBTRACT = 3'd2,
                 COMMIT = 3'd3, RESULT = 3'd4;
      reg [2:0] state;
      reg [2:0] chunk;
      reg [7:0] bits_remaining;
      reg [WIDTH-1:0] q;
      reg [PAD-1:0] divisor, shifted_remainder, trial;
      reg borrow, zero_error;
      wire [32:0] difference =
        {1'b0, shifted_remainder[32*chunk+:32]} -
        {1'b0, divisor[32*chunk+:32]} - {32'b0, borrow};

      assign in_ready = rst_n && state == IDLE;
      assign out_valid = rst_n && state == RESULT;
      assign quotient = out_valid && !zero_error ? q : {WIDTH{1'b0}};
      assign remainder =
        out_valid && !zero_error ? shifted_remainder[WIDTH-1:0] : {WIDTH{1'b0}};
      assign divide_by_zero = out_valid && zero_error;

      always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
          state <= IDLE;
          chunk <= 0;
          bits_remaining <= 0;
          q <= 0;
          divisor <= 0;
          shifted_remainder <= 0;
          trial <= 0;
          borrow <= 0;
          zero_error <= 0;
        end else case (state)
          IDLE: if (in_valid) begin
            q <= numerator;
            divisor <= {{(PAD-WIDTH){1'b0}}, denominator};
            shifted_remainder <= 0;
            bits_remaining <= WIDTH;
            zero_error <= denominator == 0;
            if (denominator == 0)
              state <= RESULT;
            else
              state <= SHIFT;
          end
          SHIFT: begin
            shifted_remainder <= (shifted_remainder << 1) |
                                 {{(PAD-1){1'b0}}, q[WIDTH-1]};
            q <= q << 1;
            chunk <= 0;
            borrow <= 0;
            state <= SUBTRACT;
          end
          SUBTRACT: begin
            trial[32*chunk+:32] <= difference[31:0];
            borrow <= difference[32];
            if (chunk == CHUNKS-1)
              state <= COMMIT;
            else
              chunk <= chunk + 3'd1;
          end
          COMMIT: begin
            if (!borrow) begin
              shifted_remainder <= trial;
              q[0] <= 1;
            end
            bits_remaining <= bits_remaining - 8'd1;
            if (bits_remaining == 1)
              state <= RESULT;
            else
              state <= SHIFT;
          end
          RESULT: if (out_ready) state <= IDLE;
          default: begin
            zero_error <= 1;
            state <= RESULT;
          end
        endcase
      end
    end else begin : g_illegal
      initial $fatal(1, "ANVIL_Q1_HT PARAMETER ERROR: divider WIDTH must be 1..129");
      assign in_ready = 0;
      assign out_valid = 0;
      assign quotient = 0;
      assign remainder = 0;
      assign divide_by_zero = 0;
    end
  endgenerate
endmodule
