module anvil_q1_ht3_sincos_phase (
  input wire clk, rst_n, enable, in_valid,
  input wire [64:0] in_phase,
  input wire in_negative, in_zero, in_error,
  output wire out_valid,
  output wire [31:0] out_sin, out_cos,
  output wire out_error
);
  import anvil_q1_ht3_fp_pkg::*;
  wire run_n;
  reg [63:0] valid_pipe, error_pipe, negative_pipe, zero_pipe;
  reg signed [64:0] input48 [0:3];
  reg signed [41:0] input24;
  reg signed [74:0] quotient_product;
  reg signed [16:0] quadrant [2:53];
  reg signed [66:0] quadrant_pi;
  reg signed [50:0] x [0:48], y [0:48];
  reg signed [51:0] z [0:48];
  reg signed [50:0] mapped_sin, mapped_cos;
  reg [31:0] sin_pipe [54:63], cos_pipe [54:63];
  wire signed [74:0] rounded_quotient =
    (quotient_product + 75'sh0000080000000000000) >>> 56;
  wire signed [66:0] reduced_full =
    $signed({2'b0, input48[3]}) - quadrant_pi;
  wire [50:0] sin_magnitude = mapped_sin[50] ? -mapped_sin : mapped_sin;
  wire [50:0] cos_magnitude = mapped_cos[50] ? -mapped_cos : mapped_cos;
  wire [31:0] packed_sin = pack32(mapped_sin[50] ^ negative_pipe[53],
    {13'b0, sin_magnitude}, -48);
  wire [31:0] packed_cos = pack32(mapped_cos[50],
    {13'b0, cos_magnitude}, -48);

  function automatic signed [51:0] atan_constant(input integer index);
    begin
      case (index)
        0: atan_constant = 52'h0c90fdaa22169;
        1: atan_constant = 52'h076b19c1586ed;
        2: atan_constant = 52'h03eb6ebf25902;
        3: atan_constant = 52'h01fd5ba9aac2f;
        4: atan_constant = 52'h00ffaaddb967f;
        5: atan_constant = 52'h007ff556eea5e;
        6: atan_constant = 52'h003ffeaab776e;
        7: atan_constant = 52'h001fffd555bbc;
        8: atan_constant = 52'h000ffffaaaade;
        9: atan_constant = 52'h0007ffff55557;
        10: atan_constant = 52'h0003ffffeaaab;
        11: atan_constant = 52'h0001fffffd555;
        12: atan_constant = 52'h0000ffffffaab;
        13: atan_constant = 52'h00007ffffff55;
        14: atan_constant = 52'h00003ffffffeb;
        15: atan_constant = 52'h00001fffffffd;
        default: atan_constant = 52'sh1000000000000 >>> index;
      endcase
    end
  endfunction

  anvil_q1_ht3_reset_sync u_reset(clk, rst_n, run_n);
  assign out_valid = run_n && valid_pipe[63];
  assign out_error = out_valid && error_pipe[63];
  assign out_sin = out_valid ? sin_pipe[63] : 32'b0;
  assign out_cos = out_valid ? cos_pipe[63] : 32'b0;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      valid_pipe <= 0;
      error_pipe <= 0;
      negative_pipe <= 0;
      zero_pipe <= 0;
      input48[0] <= 0;
      input24 <= 0;
      quotient_product <= 0;
      quadrant_pi <= 0;
      x[0] <= 0;
      y[0] <= 0;
      z[0] <= 0;
      mapped_sin <= 0;
      mapped_cos <= 0;
    end else if (run_n && enable) begin
      valid_pipe <= {valid_pipe[62:0], in_valid};
      error_pipe <= {error_pipe[62:0], in_error};
      negative_pipe <= {negative_pipe[62:0], in_negative};
      zero_pipe <= {zero_pipe[62:0], in_zero};
      input48[0] <= in_error ? 65'b0 : in_phase;
      input24 <= in_error ? 42'b0 : $signed(in_phase[64:24]);
      quotient_product <= input24 * 33'sh0a2f9836e;
      quadrant_pi <= quadrant[2] * 50'sh1921fb54442d2;
      x[0] <= 51'sh09b74eda8435e;
      y[0] <= 0;
      z[0] <= reduced_full[51:0];
      case (quadrant[52][1:0])
        0: begin mapped_sin <= y[48]; mapped_cos <= x[48]; end
        1: begin mapped_sin <= x[48]; mapped_cos <= -y[48]; end
        2: begin mapped_sin <= -y[48]; mapped_cos <= -x[48]; end
        3: begin mapped_sin <= -x[48]; mapped_cos <= y[48]; end
      endcase
    end
  end

  genvar stage;
  generate
    for (stage = 1; stage < 4; stage = stage + 1) begin: g_input
      always @(posedge clk or negedge rst_n) begin
        if (!rst_n) input48[stage] <= 0;
        else if (run_n && enable) input48[stage] <= input48[stage-1];
      end
    end
    for (stage = 2; stage < 54; stage = stage + 1) begin: g_quadrant
      always @(posedge clk or negedge rst_n) begin
        if (!rst_n) quadrant[stage] <= 0;
        else if (run_n && enable) begin
          if (stage == 2) quadrant[stage] <= rounded_quotient[16:0];
          else quadrant[stage] <= quadrant[stage-1];
        end
      end
    end
    for (stage = 0; stage < 48; stage = stage + 1) begin: g_rotate
      always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
          x[stage+1] <= 0;
          y[stage+1] <= 0;
          z[stage+1] <= 0;
        end else if (run_n && enable) begin
          if (z[stage][51]) begin
            x[stage+1] <= x[stage] + (y[stage] >>> stage);
            y[stage+1] <= y[stage] - (x[stage] >>> stage);
            z[stage+1] <= z[stage] + atan_constant(stage);
          end else begin
            x[stage+1] <= x[stage] - (y[stage] >>> stage);
            y[stage+1] <= y[stage] + (x[stage] >>> stage);
            z[stage+1] <= z[stage] - atan_constant(stage);
          end
        end
      end
    end
    for (stage = 54; stage < 64; stage = stage + 1) begin: g_result
      always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
          sin_pipe[stage] <= 0;
          cos_pipe[stage] <= 0;
        end else if (run_n && enable) begin
          if (stage == 54) begin
            sin_pipe[stage] <= error_pipe[53] ? FP32_QNAN :
              (zero_pipe[53] ? {negative_pipe[53], 31'b0} : packed_sin);
            cos_pipe[stage] <= error_pipe[53] ? FP32_QNAN :
              (zero_pipe[53] ? 32'h3f800000 : packed_cos);
          end else begin
            sin_pipe[stage] <= sin_pipe[stage-1];
            cos_pipe[stage] <= cos_pipe[stage-1];
          end
        end
      end
    end
  endgenerate
endmodule

module anvil_q1_ht3_fp32_sincos (
  input wire clk, rst_n, enable, in_valid,
  input wire [31:0] in_data,
  output wire out_valid,
  output wire [31:0] out_sin, out_cos,
  output wire out_error
);
  import anvil_q1_ht3_fp_pkg::*;
  wire input_error = fp32_nonfinite(in_data) ||
    in_data[30:0] > 31'h47000000;
  wire [63:0] magnitude48 = shift_rne64(
    {40'b0, (|in_data[30:23]), in_data[22:0]},
    (in_data[30:23] == 0 ? 149 :
      150-int'({1'b0, in_data[30:23]})) - 48);
  anvil_q1_ht3_sincos_phase u_phase (
    .clk(clk), .rst_n(rst_n), .enable(enable), .in_valid(in_valid),
    .in_phase({1'b0, magnitude48}), .in_negative(in_data[31]),
    .in_zero(in_data[30:0] == 0), .in_error(input_error),
    .out_valid(out_valid), .out_sin(out_sin), .out_cos(out_cos),
    .out_error(out_error)
  );
endmodule
