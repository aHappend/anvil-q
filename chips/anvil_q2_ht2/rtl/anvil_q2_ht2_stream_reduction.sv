module anvil_q2_ht2_stream_reduction (
  input wire clk, rst_n, annul,
  input wire s_valid, s_last, s_error,
  output wire s_ready,
  input wire [31:0] s_data,
  output wire m_valid, m_error,
  input wire m_ready,
  output wire [15:0] m_mask,
  output wire [511:0] m_partials
);
  reg closing, response, failed;
  wire active=rst_n && !annul;
  wire clear=annul || (m_valid && m_ready);
  wire [15:0] held;
  wire [15:0] pending, result_error;
  wire [16:0] input_valid;
  wire [31:0] input_data [0:16];
  wire [511:0] partials;
  genvar level;

  assign s_ready=active && !closing && !response;
  assign input_valid[0]=s_valid && s_ready;
  assign input_data[0]=s_data;
  assign m_valid=active && response;
  assign m_error=m_valid && failed;
  assign m_mask=m_valid ? held : 16'd0;
  assign m_partials=m_valid && !failed ? partials : 512'd0;

  generate for (level=0;level<16;level=level+1) begin: tree
    reg occupied;
    reg [31:0] first;
    reg [3:0] valid;
    wire [31:0] sum;
    wire error;
    wire pair=input_valid[level] && occupied;
    assign held[level]=occupied;
    assign partials[32*level+:32]=occupied ? first : 32'd0;
    assign pending[level]=|valid;
    assign result_error[level]=valid[3] && error;
    assign input_valid[level+1]=active && !response && valid[3];
    assign input_data[level+1]=sum;
    anvil_q2_ht2_fp32_add_pipe addition (
      .clk(clk),.rst_n(rst_n),.advance(active),
      .a(pair ? first : 32'd0),.b(pair ? input_data[level] : 32'd0),
      .sum(sum),.error(error)
    );
    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin occupied<=0; first<=0; valid<=0; end
      else if (clear) begin occupied<=0; valid<=0; end
      else begin
        valid<={valid[2:0],pair};
        if (input_valid[level]) begin
          occupied<=!occupied;
          if (!occupied) first<=input_data[level];
        end
      end
    end
  end endgenerate

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin closing<=0; response<=0; failed<=0; end
    else if (clear) begin closing<=0; response<=0; failed<=0; end
    else begin
      if (input_valid[0]) begin
        if (s_error) failed<=1;
        if (s_last) closing<=1;
      end
      if ((|result_error) || input_valid[16]) failed<=1;
      if (closing && !(|pending)) response<=1;
    end
  end
endmodule
