module anvil_q1_ht_isqrt (
  input wire clk,
  input wire rst_n,
  input wire in_valid,
  output wire in_ready,
  input wire [127:0] in_data,
  output wire out_valid,
  input wire out_ready,
  output wire [63:0] out_root
);
  localparam IDLE = 3'd0, SHIFT = 3'd1, SUBTRACT = 3'd2,
             COMMIT = 3'd3, RESULT = 3'd4;
  reg [2:0] state;
  reg [1:0] chunk;
  reg [6:0] pairs_remaining;
  reg [127:0] digits;
  reg [63:0] root;
  reg [95:0] remainder, trial_divisor, trial;
  reg borrow;
  wire [32:0] difference =
    {1'b0, remainder[32*chunk+:32]} -
    {1'b0, trial_divisor[32*chunk+:32]} - {32'b0, borrow};

  assign in_ready = rst_n && state == IDLE;
  assign out_valid = rst_n && state == RESULT;
  assign out_root = out_valid ? root : 64'b0;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state <= IDLE;
      chunk <= 0;
      pairs_remaining <= 0;
      digits <= 0;
      root <= 0;
      remainder <= 0;
      trial_divisor <= 0;
      trial <= 0;
      borrow <= 0;
    end else case (state)
      IDLE: if (in_valid) begin
        digits <= in_data;
        root <= 0;
        remainder <= 0;
        pairs_remaining <= 64;
        state <= SHIFT;
      end
      SHIFT: begin
        remainder <= (remainder << 2) | {94'b0, digits[127:126]};
        digits <= digits << 2;
        trial_divisor <= {30'b0, root, 2'b01};
        chunk <= 0;
        borrow <= 0;
        state <= SUBTRACT;
      end
      SUBTRACT: begin
        trial[32*chunk+:32] <= difference[31:0];
        borrow <= difference[32];
        if (chunk == 2)
          state <= COMMIT;
        else
          chunk <= chunk + 2'd1;
      end
      COMMIT: begin
        root <= {root[62:0], !borrow};
        if (!borrow)
          remainder <= trial;
        pairs_remaining <= pairs_remaining - 7'd1;
        if (pairs_remaining == 1)
          state <= RESULT;
        else
          state <= SHIFT;
      end
      RESULT: if (out_ready) state <= IDLE;
      default: state <= IDLE;
    endcase
  end
endmodule
