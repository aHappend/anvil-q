module anvil_q1_ht_mac_lane (
  input wire clk,
  input wire rst_n,
  input wire in_valid,
  input wire in_first,
  input wire in_last,
  input wire in_enable,
  input wire signed [31:0] in_activation,
  input wire signed [36:0] in_weight_q16,
  output wire signed [31:0] out_data
);
  reg [3:0] valid_pipe, first_pipe, last_pipe;
  reg signed [31:0] activation;
  reg signed [36:0] weight;
  (* multstyle = "dsp" *) reg signed [35:0] product_ll, product_lh;
  (* multstyle = "dsp" *) reg signed [34:0] product_hl, product_hh;

  wire signed [68:0] term_ll = {{33{product_ll[35]}}, product_ll};
  wire signed [68:0] term_hl = {{18{product_hl[34]}}, product_hl, 16'b0};
  wire signed [68:0] term_lh = {{15{product_lh[35]}}, product_lh, 18'b0};
  wire signed [68:0] term_hh = {product_hh, 34'b0};
  wire [68:0] partial_s = term_ll ^ term_hl ^ term_lh;
  wire [68:0] partial_c =
    ((term_ll & term_hl) | (term_ll & term_lh) | (term_hl & term_lh)) << 1;
  wire [68:0] product_s = partial_s ^ partial_c ^ term_hh;
  wire [68:0] product_c =
    ((partial_s & partial_c) | (partial_s & term_hh) | (partial_c & term_hh)) << 1;

  reg [35:0] product_low;
  reg [33:0] product_high_s, product_high_c;
  reg signed [68:0] product;
  reg [127:0] accumulator_s, accumulator_c;
  wire [127:0] operand = {{59{product[68]}}, product};
  wire [127:0] old_s = first_pipe[3] ? 128'b0 : accumulator_s;
  wire [127:0] old_c = first_pipe[3] ? 128'b0 : accumulator_c;
  wire [127:0] next_s = old_s ^ old_c ^ operand;
  wire [127:0] next_c =
    ((old_s & old_c) | (old_s & operand) | (old_c & operand)) << 1;

  reg [2:0] finish_step;
  reg carry;
  reg [127:0] resolved;
  reg signed [31:0] rounded, published;
  wire [32:0] chunk0 =
    {1'b0, accumulator_s[31:0]} + {1'b0, accumulator_c[31:0]};
  wire [32:0] chunk1 =
    {1'b0, accumulator_s[63:32]} + {1'b0, accumulator_c[63:32]} + {32'b0, carry};
  wire [32:0] chunk2 =
    {1'b0, accumulator_s[95:64]} + {1'b0, accumulator_c[95:64]} + {32'b0, carry};
  wire [32:0] chunk3 =
    {1'b0, accumulator_s[127:96]} + {1'b0, accumulator_c[127:96]} + {32'b0, carry};

  function automatic signed [31:0] round_sat16(input signed [127:0] value);
    reg signed [32:0] candidate;
    begin
      candidate = $signed({value[127], value[47:16]});
      if (!value[127]) begin
        if (value[127:47] != 81'b0)
          round_sat16 = 32'sh7fffffff;
        else begin
          candidate = candidate + (value[15] ? 33'sd1 : 33'sd0);
          if (candidate > 33'sd2147483647)
            round_sat16 = 32'sh7fffffff;
          else
            round_sat16 = candidate[31:0];
        end
      end else if (value[127:47] != {81{1'b1}})
        round_sat16 = 32'sh80000000;
      else begin
        // Arithmetic floor increments only above a half, not at a negative tie.
        candidate = candidate + (value[15:0] > 16'h8000 ? 33'sd1 : 33'sd0);
        round_sat16 = candidate[31:0];
      end
    end
  endfunction

  assign out_data = rst_n ? published : 32'sd0;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      valid_pipe <= 0;
      first_pipe <= 0;
      last_pipe <= 0;
      activation <= 0;
      weight <= 0;
      product_ll <= 0;
      product_lh <= 0;
      product_hl <= 0;
      product_hh <= 0;
      product_low <= 0;
      product_high_s <= 0;
      product_high_c <= 0;
      product <= 0;
      accumulator_s <= 0;
      accumulator_c <= 0;
      finish_step <= 0;
      carry <= 0;
      resolved <= 0;
      rounded <= 0;
      published <= 0;
    end else begin
      valid_pipe <= {valid_pipe[2:0], in_valid};
      first_pipe <= {first_pipe[2:0], in_valid && in_first};
      last_pipe <= {last_pipe[2:0], in_valid && in_last};
      if (in_valid) begin
        activation <= in_enable ? in_activation : 32'sd0;
        weight <= in_enable ? in_weight_q16 : 37'sd0;
      end
      if (valid_pipe[0]) begin
        product_ll <= $signed({1'b0, activation[15:0]}) *
                      $signed({1'b0, weight[17:0]});
        product_lh <= $signed({1'b0, activation[15:0]}) * $signed(weight[36:18]);
        product_hl <= $signed(activation[31:16]) * $signed({1'b0, weight[17:0]});
        product_hh <= $signed(activation[31:16]) * $signed(weight[36:18]);
      end
      if (valid_pipe[1]) begin
        product_low <= {1'b0, product_s[34:0]} + {1'b0, product_c[34:0]};
        product_high_s <= product_s[68:35];
        product_high_c <= product_c[68:35];
      end
      if (valid_pipe[2])
        product <= {product_high_s + product_high_c + {33'b0, product_low[35]},
                    product_low[34:0]};
      if (valid_pipe[3]) begin
        accumulator_s <= next_s;
        accumulator_c <= next_c;
        if (last_pipe[3])
          finish_step <= 1;
      end
      case (finish_step)
        1: begin
          resolved[31:0] <= chunk0[31:0];
          carry <= chunk0[32];
          finish_step <= 2;
        end
        2: begin
          resolved[63:32] <= chunk1[31:0];
          carry <= chunk1[32];
          finish_step <= 3;
        end
        3: begin
          resolved[95:64] <= chunk2[31:0];
          carry <= chunk2[32];
          finish_step <= 4;
        end
        4: begin
          resolved[127:96] <= chunk3[31:0];
          finish_step <= 5;
        end
        5: begin
          rounded <= round_sat16($signed(resolved));
          finish_step <= 6;
        end
        6: begin
          published <= rounded;
          finish_step <= 0;
        end
        default: begin end
      endcase
    end
  end
endmodule
