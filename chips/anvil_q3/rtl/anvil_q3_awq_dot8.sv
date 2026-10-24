module anvil_q3_awq_dot8 (
  input wire clk, rst_n, flush,
  input wire in_valid,
  output wire in_ready,
  input wire [31:0] q_nibbles, z_nibbles,
  input wire [127:0] scale_f16,
  input wire [255:0] activation_q16,
  input wire [7:0] lane_mask,
  output wire out_valid,
  input wire out_ready,
  output wire out_error,
  output wire signed [71:0] out_dot
);
  reg [7:0] valid_pipe, error_pipe;
  reg [3:0] q0 [0:7], z0 [0:7];
  reg sign0 [0:7];
  reg [4:0] exponent0 [0:7];
  reg [9:0] fraction0 [0:7];
  reg signed [31:0] activation0 [0:7], activation1 [0:7], activation2 [0:7];
  reg [7:0] mask0;
  reg signed [4:0] delta1 [0:7];
  reg [31:0] scale1 [0:7];
  reg signed [36:0] weight2 [0:7];
  reg signed [53:0] low3 [0:7];
  reg signed [52:0] high3 [0:7];
  reg signed [68:0] product4 [0:7];
  reg signed [69:0] pair5 [0:3];
  reg signed [70:0] pair6 [0:1];
  reg signed [71:0] sum7;
  wire [7:0] invalid0;
  wire enable = !valid_pipe[7] || out_ready;
  integer i;

  assign in_ready = rst_n && !flush && enable;
  assign out_valid = rst_n && !flush && valid_pipe[7];
  assign out_error = out_valid && error_pipe[7];
  assign out_dot = out_valid ? sum7 : 72'sd0;

  genvar g;
  generate for (g=0; g<8; g=g+1) begin: lane_errors
    assign invalid0[g] = mask0[g] &&
      anvil_q3_pkg::f16_scale_invalid({sign0[g],exponent0[g],fraction0[g]});
  end endgenerate

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      valid_pipe <= 0;
      error_pipe <= 0;
    end else if (flush) begin
      valid_pipe <= 0;
      error_pipe <= 0;
    end else if (enable) begin
      valid_pipe <= {valid_pipe[6:0],in_valid};
      error_pipe <= {error_pipe[6:1],(|invalid0),1'b0};
    end
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      mask0 <= 0;
    end else if (flush) begin
      mask0 <= 0;
    end else if (enable) begin
      mask0 <= lane_mask;
      for (i=0; i<8; i=i+1) begin
        q0[i] <= lane_mask[i] ? q_nibbles[i*4+:4] : 4'd0;
        z0[i] <= lane_mask[i] ? z_nibbles[i*4+:4] : 4'd0;
        sign0[i] <= lane_mask[i] && scale_f16[i*16+15];
        exponent0[i] <= lane_mask[i] ? scale_f16[i*16+10+:5] : 5'd0;
        fraction0[i] <= lane_mask[i] ? scale_f16[i*16+:10] : 10'd0;
        activation0[i] <= lane_mask[i] ? activation_q16[i*32+:32] : 32'd0;
        delta1[i] <= $signed({1'b0,q0[i]})-$signed({1'b0,z0[i]});
        scale1[i] <= anvil_q3_pkg::f16_scale(
          {sign0[i],exponent0[i],fraction0[i]});
        activation1[i] <= activation0[i];
        weight2[i] <= delta1[i]*$signed({1'b0,scale1[i]});
        activation2[i] <= activation1[i];
        low3[i] <= weight2[i]*$signed({1'b0,activation2[i][15:0]});
        high3[i] <= weight2[i]*$signed(activation2[i][31:16]);
        product4[i] <= $signed({{15{low3[i][53]}},low3[i]}) +
          ($signed({{16{high3[i][52]}},high3[i]}) <<< 16);
      end
      for (i=0; i<4; i=i+1)
        pair5[i] <= $signed({product4[2*i][68],product4[2*i]}) +
                    $signed({product4[2*i+1][68],product4[2*i+1]});
      for (i=0; i<2; i=i+1)
        pair6[i] <= $signed({pair5[2*i][69],pair5[2*i]}) +
                    $signed({pair5[2*i+1][69],pair5[2*i+1]});
      sum7 <= $signed({pair6[0][70],pair6[0]}) +
              $signed({pair6[1][70],pair6[1]});
    end
  end
endmodule
