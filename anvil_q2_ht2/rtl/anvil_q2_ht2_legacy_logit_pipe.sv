module anvil_q2_ht2_legacy_logit_pipe (
  input wire clk, rst_n, annul, s_valid, m_ready,
  output wire s_ready, m_valid, idle,
  input wire [31:0] s_index,
  input wire signed [31:0] s_data,
  output wire [31:0] m_index, m_fp32,
  output wire signed [31:0] m_data
);
  import anvil_q2_ht2_fp_pkg::*;
  reg [2:0] valid;
  reg [31:0] indices [0:2], data [0:2];
  reg [31:0] magnitude1, normalized2, result3;
  reg sign1, sign2;
  reg [7:0] exponent2;
  wire advance=!valid[2] || m_ready;
  wire [5:0] leading=leading32(magnitude1);
  wire [24:0] rounded={1'b0,normalized2[31:8]}+
    {24'd0,(normalized2[7] && ((|normalized2[6:0]) || normalized2[8]))};
  wire [7:0] exponent3=exponent2+{7'd0,rounded[24]};
  integer i;

  assign s_ready=rst_n && !annul && advance;
  assign m_valid=rst_n && !annul && valid[2];
  assign m_index=m_valid ? indices[2] : 32'd0;
  assign m_data=m_valid ? $signed(data[2]) : 32'sd0;
  assign m_fp32=m_valid ? result3 : 32'd0;
  assign idle=rst_n && valid==0;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      valid<=0; magnitude1<=0; normalized2<=0; result3<=0;
      sign1<=0; sign2<=0; exponent2<=0;
      for (i=0;i<3;i=i+1) begin indices[i]<=0; data[i]<=0; end
    end else if (annul) begin
      valid<=0;
    end else if (advance) begin
      valid<={valid[1:0],s_valid};
      indices[0]<=s_index; data[0]<=s_data;
      for (i=1;i<3;i=i+1) begin
        indices[i]<=indices[i-1]; data[i]<=data[i-1];
      end
      magnitude1<=s_data[31] ? (~s_data+32'd1) : s_data;
      sign1<=s_data[31];
      normalized2<=magnitude1 << leading;
      sign2<=sign1; exponent2<=8'd142-{2'd0,leading};
      if (normalized2==0) result3<=0;
      else result3<={sign2,exponent3,
        (rounded[24] ? rounded[23:1] : rounded[22:0])};
    end
  end
endmodule
