module anvil_q1_ht3_fp32_exp (
  input wire clk, rst_n, enable, in_valid,
  input wire [31:0] in_data,
  output wire out_valid,
  output wire [31:0] out_data
);
  import anvil_q1_ht3_fp_pkg::*;
  wire run_n;
  reg [31:0] valid_pipe, special_pipe;
  reg [31:0] special_data [0:31];
  reg signed [9:0] n_pipe [2:22];
  reg signed [57:0] x48 [0:3];
  reg signed [33:0] x24;
  reg signed [67:0] quotient_product;
  reg signed [59:0] n_ln2;
  reg signed [43:0] remainder_pipe [4:21];
  reg signed [43:0] polynomial [0:8];
  reg signed [87:0] product [0:7];
  reg [31:0] result_pipe [22:31];
  wire input_special = fp32_nonfinite(in_data) ||
    (in_data[31] ? in_data[30:0] >= 31'h42d00000 :
                   in_data[30:0] >= 31'h42b20000);
  wire [31:0] input_special_data = fp32_nan(in_data) ? FP32_QNAN :
    (in_data[31] ? 32'b0 : 32'h7f800000);
  wire [63:0] magnitude48 = shift_rne64(
    {40'b0, (|in_data[30:23]), in_data[22:0]},
    (in_data[30:23] == 0 ? -149 :
      int'({1'b0, in_data[30:23]})-150) * (-1) - 48);
  wire [63:0] magnitude24 = shift_rne64(
    {40'b0, (|in_data[30:23]), in_data[22:0]},
    (in_data[30:23] == 0 ? -149 :
      int'({1'b0, in_data[30:23]})-150) * (-1) - 24);
  wire signed [67:0] rounded_quotient =
    (quotient_product + 68'sh00080000000000000) >>> 56;
  wire signed [59:0] reduced48 =
    $signed({{2{x48[3][57]}}, x48[3]}) - n_ln2;
  wire [63:0] final_significand = {20'b0, polynomial[8]};
  wire [31:0] scaled_polynomial = pack32(1'b0, final_significand,
    int'(n_pipe[21])-40);

  function automatic signed [43:0] coefficient(input integer degree);
    begin
      case (degree)
        0, 1: coefficient = 44'h10000000000;
        2: coefficient = 44'h08000000000;
        3: coefficient = 44'h02aaaaaaaab;
        4: coefficient = 44'h00aaaaaaaab;
        5: coefficient = 44'h00222222222;
        6: coefficient = 44'h0005b05b05b;
        7: coefficient = 44'h0000d00d00d;
        8: coefficient = 44'h00001a01a02;
        default: coefficient = 0;
      endcase
    end
  endfunction

  anvil_q1_ht3_reset_sync u_reset(clk, rst_n, run_n);
  assign out_valid = run_n && valid_pipe[31];
  assign out_data = out_valid ? result_pipe[31] : 32'b0;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      valid_pipe <= 0;
      special_pipe <= 0;
      x48[0] <= 0;
      x24 <= 0;
      quotient_product <= 0;
      n_ln2 <= 0;
      polynomial[0] <= 0;
    end else if (run_n && enable) begin
      valid_pipe <= {valid_pipe[30:0], in_valid};
      special_pipe <= {special_pipe[30:0], input_special};
      if (input_special) begin
        x48[0] <= 0;
        x24 <= 0;
      end else begin
        x48[0] <= in_data[31] ? -$signed(magnitude48[57:0]) :
                                               $signed(magnitude48[57:0]);
        x24 <= in_data[31] ? -$signed(magnitude24[33:0]) :
                                               $signed(magnitude24[33:0]);
      end
      quotient_product <= x24 * 34'sh171547653;
      n_ln2 <= n_pipe[2] * 50'sh0b17217f7d1cf;
      polynomial[0] <= coefficient(8);
    end
  end

  genvar stage;
  generate
    for (stage = 0; stage < 32; stage = stage + 1) begin: g_special
      always @(posedge clk or negedge rst_n) begin
        if (!rst_n) special_data[stage] <= 0;
        else if (run_n && enable) begin
          if (stage == 0) special_data[stage] <= input_special_data;
          else special_data[stage] <= special_data[stage-1];
        end
      end
    end
    for (stage = 1; stage < 4; stage = stage + 1) begin: g_x
      always @(posedge clk or negedge rst_n) begin
        if (!rst_n) x48[stage] <= 0;
        else if (run_n && enable) x48[stage] <= x48[stage-1];
      end
    end
    for (stage = 2; stage < 23; stage = stage + 1) begin: g_n
      always @(posedge clk or negedge rst_n) begin
        if (!rst_n) n_pipe[stage] <= 0;
        else if (run_n && enable) begin
          if (stage == 2) n_pipe[stage] <= rounded_quotient[9:0];
          else n_pipe[stage] <= n_pipe[stage-1];
        end
      end
    end
    for (stage = 4; stage < 22; stage = stage + 1) begin: g_remainder
      always @(posedge clk or negedge rst_n) begin
        if (!rst_n) remainder_pipe[stage] <= 0;
        else if (run_n && enable) begin
          if (stage == 4) remainder_pipe[stage] <= reduced48 >>> 8;
          else remainder_pipe[stage] <= remainder_pipe[stage-1];
        end
      end
    end
    for (stage = 0; stage < 8; stage = stage + 1) begin: g_horner
      wire signed [87:0] rounded_product =
        (product[stage] + 88'sh0000000000008000000000) >>> 40;
      always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
          product[stage] <= 0;
          polynomial[stage+1] <= 0;
        end else if (run_n && enable) begin
          product[stage] <= polynomial[stage] * remainder_pipe[5+2*stage];
          polynomial[stage+1] <= rounded_product[43:0] + coefficient(7-stage);
        end
      end
    end
    for (stage = 22; stage < 32; stage = stage + 1) begin: g_result
      always @(posedge clk or negedge rst_n) begin
        if (!rst_n) result_pipe[stage] <= 0;
        else if (run_n && enable) begin
          if (stage == 22)
            result_pipe[stage] <= special_pipe[21] ?
              special_data[21] : scaled_polynomial;
          else result_pipe[stage] <= result_pipe[stage-1];
        end
      end
    end
  endgenerate
endmodule
