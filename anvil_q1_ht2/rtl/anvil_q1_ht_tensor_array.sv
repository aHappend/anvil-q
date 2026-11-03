module anvil_q1_ht_tensor_array (
  input wire clk,
  input wire rst_n,
  input wire in_valid,
  output wire in_ready,
  input wire in_first,
  input wire in_last,
  input wire signed [31:0] in_activation,
  input wire [2367:0] in_weight_q16,
  input wire [63:0] in_mask,
  output wire out_valid,
  input wire out_ready,
  output wire [2047:0] out_data,
  output wire [63:0] out_mask,
  output wire protocol_error
);
  reg dot_open, pending, result_valid, failed;
  reg [63:0] dot_mask;
  reg [9:0] last_pipe;
  wire accepted = in_valid && in_ready;
  wire legal = dot_open ? (!in_first && in_mask == dot_mask) : in_first;
  wire arithmetic_valid = accepted && legal;

  assign in_ready = rst_n && !failed && !pending;
  assign protocol_error = rst_n && failed;
  assign out_valid = rst_n && !failed && result_valid;
  assign out_mask = rst_n && !failed && result_valid ? dot_mask : 64'b0;

  genvar bank, lane;
  generate
    for (bank = 0; bank < 8; bank = bank + 1) begin : g_bank
      for (lane = 0; lane < 8; lane = lane + 1) begin : g_lane
        localparam INDEX = bank * 8 + lane;
        wire signed [31:0] lane_result;
        anvil_q1_ht_mac_lane u_mac (
          .clk(clk),
          .rst_n(rst_n),
          .in_valid(arithmetic_valid),
          .in_first(in_first),
          .in_last(in_last),
          .in_enable(in_mask[INDEX]),
          .in_activation(in_activation),
          .in_weight_q16(in_weight_q16[37*INDEX+:37]),
          .out_data(lane_result)
        );
        assign out_data[32*INDEX+:32] =
          rst_n && !failed && result_valid && dot_mask[INDEX] ? lane_result : 32'b0;
      end
    end
  endgenerate

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      dot_open <= 0;
      pending <= 0;
      result_valid <= 0;
      failed <= 0;
      dot_mask <= 0;
      last_pipe <= 0;
    end else if (!failed) begin
      last_pipe <= {last_pipe[8:0], arithmetic_valid && in_last};
      if (last_pipe[9])
        result_valid <= 1;
      if (result_valid && out_ready) begin
        result_valid <= 0;
        pending <= 0;
      end
      if (accepted) begin
        if (!legal) begin
          failed <= 1;
          result_valid <= 0;
          last_pipe <= 0;
        end else begin
          if (!dot_open)
            dot_mask <= in_mask;
          dot_open <= !in_last;
          if (in_last)
            pending <= 1;
        end
      end
    end
  end
endmodule
