module anvil_q2_ht2_row_accumulator (
  input wire clk, rst_n, annul, s_valid, m_ready,
  input wire s_first, s_last, s_error,
  input wire [31:0] s_row, s_column_tile,
  input wire [3:0] s_token_mask,
  input wire [127:0] s_sum,
  input wire [63:0] s_tag,
  output wire s_ready, m_valid, m_error,
  output wire [31:0] m_row,
  output wire [3:0] m_token_mask,
  output wire [127:0] m_sum,
  output wire [63:0] m_tag
);
  reg active, in_flight;
  reg [31:0] row, next_tile;
  reg [3:0] token_mask;
  reg [63:0] row_tag;
  reg [127:0] accumulator;
  reg [3:0] valid, first, last, errors;
  reg [127:0] initial_sum [0:3];
  reg [31:0] rows [0:3], tiles [0:3];
  reg [3:0] masks [0:3];
  reg [63:0] tags [0:3];
  wire [127:0] added;
  wire [3:0] add_error;
  wire bad_order=s_first ?
    (active || s_column_tile!=0) :
    (!active || s_row!=row || s_column_tile!=next_tile ||
      s_token_mask!=token_mask || s_tag!=row_tag);
  wire bad_terminal=!s_last && s_column_tile==32'hffffffff;
  wire arithmetic_error=|(add_error & masks[3]);
  wire result_error=errors[3] || arithmetic_error;
  wire terminal=last[3] || result_error;
  wire retire=valid[3] && (!terminal || m_ready);
  wire advance=!valid[3] || !terminal || m_ready;
  integer i;
  genvar t;

  generate for (t=0;t<4;t=t+1) begin: token
    anvil_q2_ht2_fp32_add_pipe addition (
      .clk(clk),.rst_n(rst_n),.advance(advance && !annul),
      .a(s_token_mask[t] && !s_first ? accumulator[32*t+:32] : 32'd0),
      .b(s_token_mask[t] ? s_sum[32*t+:32] : 32'd0),
      .sum(added[32*t+:32]),.error(add_error[t]));
  end endgenerate

  assign s_ready=rst_n && !annul && !in_flight;
  assign m_valid=rst_n && !annul && valid[3] && terminal;
  assign m_error=m_valid && result_error;
  assign m_sum=m_valid && !result_error ?
    (first[3] ? initial_sum[3] : added) : 128'd0;
  assign m_row=m_valid ? rows[3] : 32'd0;
  assign m_token_mask=m_valid ? masks[3] : 4'd0;
  assign m_tag=m_valid ? tags[3] : 64'd0;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      active<=0; in_flight<=0; row<=0; next_tile<=0;
      token_mask<=0; row_tag<=0; accumulator<=0;
      valid<=0; first<=0; last<=0; errors<=0;
      for (i=0;i<4;i=i+1) begin
        initial_sum[i]<=0; rows[i]<=0; tiles[i]<=0; masks[i]<=0; tags[i]<=0;
      end
    end else if (annul) begin
      active<=0; in_flight<=0; valid<=0;
    end else begin
      if (advance) begin
        valid<={valid[2:0],s_valid && s_ready};
        first<={first[2:0],s_first};
        last<={last[2:0],s_last};
        errors<={errors[2:0],s_error || bad_order || bad_terminal};
        rows[0]<=s_row; tiles[0]<=s_column_tile;
        masks[0]<=s_token_mask; tags[0]<=s_tag;
        for (i=0;i<4;i=i+1)
          initial_sum[0][32*i+:32]<=s_token_mask[i] ? s_sum[32*i+:32] : 32'd0;
        for (i=1;i<4;i=i+1) begin
          initial_sum[i]<=initial_sum[i-1]; rows[i]<=rows[i-1];
          tiles[i]<=tiles[i-1]; masks[i]<=masks[i-1]; tags[i]<=tags[i-1];
        end
      end
      if (s_valid && s_ready) in_flight<=1;
      if (retire) begin
        in_flight<=0;
        if (terminal) active<=0;
        else begin
          active<=1;
          accumulator<=first[3] ? initial_sum[3] : added;
          row<=rows[3]; token_mask<=masks[3]; row_tag<=tags[3];
          next_tile<=tiles[3]+32'd1;
        end
      end
    end
  end
endmodule
