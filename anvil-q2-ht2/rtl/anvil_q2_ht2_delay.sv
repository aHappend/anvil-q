module anvil_q2_ht2_delay #(
  parameter WIDTH=1, STAGES=1
) (
  input wire clk, rst_n, advance,
  input wire [WIDTH-1:0] s_data,
  output wire [WIDTH-1:0] m_data
);
  generate if (WIDTH<1 || STAGES<1) begin: invalid_parameters
    initial $fatal(1,"ANVIL_Q2_HT2 PARAMETER ERROR: pipeline delay");
    assign m_data=0;
  end else begin: implementation
    reg [WIDTH-1:0] data [0:STAGES-1];
    integer i;
    assign m_data=rst_n ? data[STAGES-1] : {WIDTH{1'b0}};
    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        for (i=0;i<STAGES;i=i+1) data[i]<=0;
      end else if (advance) begin
        data[0]<=s_data;
        for (i=1;i<STAGES;i=i+1) data[i]<=data[i-1];
      end
    end
  end endgenerate
endmodule
