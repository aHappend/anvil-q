module anvil_d1_csr_perf #(
  parameter integer VOCAB_SIZE=102400
) (
  input wire clk, rst_n,
  input wire csr_valid, csr_write,
  input wire [11:0] csr_addr,
  input wire [31:0] csr_wdata,
  input wire [3:0] csr_wstrb,
  input wire csr_rsp_ready,
  output wire csr_ready, csr_rsp_valid,
  output wire [31:0] csr_rdata,
  output wire csr_error,
  input wire token_accept, token_complete, token_error, reasoning_active,
  input wire shared_busy, prefetch_busy,
  input wire [2:0] domain_id,
  input wire [31:0] cache_read_bytes, cache_write_bytes, cache_dense_equiv_bytes,
  input wire [31:0] expert_read_bytes, expert_dense_equiv_bytes,
  input wire [31:0] other_read_bytes, other_write_bytes,
  output wire [2:0] domain_select,
  output wire [31:0] think_begin_token, think_end_token
);
  reg armed, response_valid, response_error, busy, snapshot_valid;
  reg [31:0] response_data, begin_token, end_token;
  reg [2:0] selected_domain;
  reg decode_error;
  reg [31:0] decode_data;
  integer global_index, domain_index, domain_counter;
  wire accepted=csr_valid && csr_ready;
  wire command=accepted && csr_write && !decode_error && csr_addr==12'h008;
  wire clear=command && csr_wdata[0];
  wire snapshot=command && csr_wdata[1] && !csr_wdata[0];
  wire configuring_busy=busy || token_accept;
  wire active_interval=busy || token_accept;
  wire [63:0] global_live [0:14], global_saved [0:14];
  wire [63:0] domain_live [0:29], domain_saved [0:29];
  wire [14:0] global_overflow;
  wire [29:0] domain_overflow;
  wire overflow_sticky=(|global_overflow) || (|domain_overflow);
  wire [35:0] global_increment [0:14];
  wire [35:0] read_increment={4'd0,cache_read_bytes}+{4'd0,expert_read_bytes}+
    {4'd0,other_read_bytes};
  wire [35:0] write_increment={4'd0,cache_write_bytes}+{4'd0,other_write_bytes};
  wire [35:0] domain_increment [0:5];

  assign csr_ready=rst_n && armed && !response_valid;
  assign csr_rsp_valid=rst_n && response_valid;
  assign csr_rdata=rst_n ? response_data : 32'd0;
  assign csr_error=csr_rsp_valid && response_error;
  assign domain_select=rst_n ? selected_domain : 3'd0;
  assign think_begin_token=rst_n ? begin_token : 32'd0;
  assign think_end_token=rst_n ? end_token : 32'd0;
  assign global_increment[0]=36'd1;
  assign global_increment[1]={35'd0,token_accept};
  assign global_increment[2]={35'd0,token_error};
  assign global_increment[3]={35'd0,(token_accept && reasoning_active)};
  assign global_increment[4]={35'd0,reasoning_active};
  assign global_increment[5]={4'd0,cache_read_bytes};
  assign global_increment[6]={4'd0,cache_write_bytes};
  assign global_increment[7]={4'd0,cache_dense_equiv_bytes};
  assign global_increment[8]={4'd0,expert_read_bytes};
  assign global_increment[9]={4'd0,expert_dense_equiv_bytes};
  assign global_increment[10]={4'd0,other_read_bytes};
  assign global_increment[11]={4'd0,other_write_bytes};
  assign global_increment[12]={35'd0,shared_busy};
  assign global_increment[13]={35'd0,prefetch_busy};
  assign global_increment[14]={35'd0,(shared_busy && prefetch_busy)};
  assign domain_increment[0]={35'd0,active_interval};
  assign domain_increment[1]={35'd0,token_accept};
  assign domain_increment[2]={35'd0,(token_accept && reasoning_active)};
  assign domain_increment[3]=read_increment;
  assign domain_increment[4]=write_increment;
  assign domain_increment[5]={4'd0,expert_read_bytes};

  genvar i, d, k;
  generate
    if (VOCAB_SIZE<4 || VOCAB_SIZE>151936) begin: invalid_parameters
      initial $fatal(1,"ANVIL_D1 PARAMETER ERROR: CSR vocabulary");
    end
    for (i=0;i<15;i=i+1) begin: global_counters
      anvil_d1_counter64 counter (
        .clk(clk),.rst_n(rst_n),.clear(clear),.snapshot(snapshot),
        .increment(armed ? global_increment[i] : 36'd0),
        .live_value(global_live[i]),.snapshot_value(global_saved[i]),
        .overflow(global_overflow[i])
      );
    end
    for (d=0;d<5;d=d+1) begin: domains
      for (k=0;k<6;k=k+1) begin: counters
        anvil_d1_counter64 counter (
          .clk(clk),.rst_n(rst_n),.clear(clear),.snapshot(snapshot),
          .increment(armed && domain_id==d ? domain_increment[k] : 36'd0),
          .live_value(domain_live[d*6+k]),.snapshot_value(domain_saved[d*6+k]),
          .overflow(domain_overflow[d*6+k])
        );
      end
    end
  endgenerate

  always @* begin
    decode_error=0; decode_data=0;
    global_index=0; domain_index=0; domain_counter=0;
    if (csr_addr[1:0]!=0) decode_error=1;
    else if (csr_write) begin
      if (csr_wstrb!=4'b1111) decode_error=1;
      else case (csr_addr)
        12'h008: if (csr_wdata[31:2]!=0) decode_error=1;
        12'h010: if (configuring_busy || csr_wdata>4) decode_error=1;
        12'h014,12'h018: if (configuring_busy || csr_wdata>=VOCAB_SIZE) decode_error=1;
        default: decode_error=1;
      endcase
    end else case (csr_addr)
      12'h000: decode_data=32'h41445631;
      12'h004: decode_data=32'h00010000;
      12'h008: decode_data=0;
      12'h00c: decode_data={29'd0,overflow_sticky,snapshot_valid,busy};
      12'h010: decode_data={29'd0,selected_domain};
      12'h014: decode_data=begin_token;
      12'h018: decode_data=end_token;
      default: begin
        if (csr_addr>=12'h040 && csr_addr<12'h0b8) begin
          global_index=(csr_addr-12'h040)>>3;
          if (snapshot_valid)
            decode_data=csr_addr[2] ? global_saved[global_index][63:32] :
              global_saved[global_index][31:0];
        end else if (csr_addr>=12'h100 && csr_addr<12'h240 && csr_addr[5:3]<6) begin
          domain_index=(csr_addr-12'h100)>>6;
          domain_counter=csr_addr[5:3];
          if (snapshot_valid)
            decode_data=csr_addr[2] ? domain_saved[domain_index*6+domain_counter][63:32] :
              domain_saved[domain_index*6+domain_counter][31:0];
        end else decode_error=1;
      end
    endcase
  end
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      armed<=0; response_valid<=0; response_error<=0; response_data<=0;
      busy<=0; snapshot_valid<=0; selected_domain<=0;
      begin_token<=VOCAB_SIZE-2; end_token<=VOCAB_SIZE-1;
    end else begin
      armed<=1;
      if (token_complete || token_error) busy<=0;
      else if (token_accept) busy<=1;
      if (clear) snapshot_valid<=0;
      else if (snapshot) snapshot_valid<=1;
      if (response_valid && csr_rsp_ready) response_valid<=0;
      if (accepted) begin
        response_valid<=1; response_error<=decode_error;
        response_data<=csr_write || decode_error ? 32'd0 : decode_data;
        if (csr_write && !decode_error) case (csr_addr)
          12'h010: selected_domain<=csr_wdata[2:0];
          12'h014: begin_token<=csr_wdata;
          12'h018: end_token<=csr_wdata;
          default: begin end
        endcase
      end
    end
  end
endmodule
