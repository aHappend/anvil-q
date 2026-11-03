module anvil_d2_csr #(
  parameter integer MODEL_MODE=0, VOCAB_SIZE=102400, MAX_SEQ_LEN=32768
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
  input wire work_busy, token_accept, token_complete, token_error, reasoning_active,
  input wire shared_busy, prefetch_busy,
  input wire [31:0] cache_read_bytes, cache_write_bytes, cache_dense_equiv_bytes,
  input wire [31:0] expert_read_bytes, expert_dense_equiv_bytes,
  input wire [31:0] other_read_bytes, other_write_bytes,
  input wire generation_active, generated_retire, accepted_retire, rejected_block,
  input wire [2:0] proposed_increment,
  input wire [31:0] cache_payload_read_bytes, cache_payload_write_bytes, cache_scale_bytes,
  input wire [31:0] expert_payload_read_bytes, expert_scale_bytes,
  input wire verification_active,
  output wire [2:0] domain_select,
  output wire [31:0] think_begin_token, think_end_token,
  output wire mtp_enable, fp8_enable, generation_enable,
  output wire [31:0] generation_limit, eos_token
);
  localparam NO_RESPONSE=0, PARENT_RESPONSE=1, D2_RESPONSE=2;
  reg [1:0] owner;
  reg armed, local_error, saved_valid, parent_status, parent_extension_overflow;
  reg [31:0] local_data;
  reg [1:0] features;
  reg policy;
  reg [31:0] limit, eos;
  reg decode_error;
  reg [31:0] decode_data;
  integer counter_index;
  wire parent_ready, parent_valid, parent_error;
  wire [31:0] parent_data;
  wire enabled=rst_n && armed;
  wire extension_address=(csr_addr>=12'h280 && csr_addr<12'h294) ||
    (csr_addr>=12'h300 && csr_addr<12'h358);
  wire accepted=csr_valid && csr_ready;
  wire configuring_busy=work_busy || token_accept;
  wire parent_request=enabled && owner==NO_RESPONSE && !extension_address && csr_valid;
  wire counter_command=accepted && csr_write && csr_addr==12'h008 &&
    csr_wstrb==4'hf && csr_wdata[31:2]==0;
  wire clear=counter_command && csr_wdata[0];
  wire snapshot=counter_command && csr_wdata[1] && !csr_wdata[0];
  wire [63:0] live_count [0:10], saved_count [0:10];
  wire [35:0] increment [0:10];
  wire [10:0] extension_overflow;
  wire [31:0] inherited_response=parent_data |
    ((parent_status && parent_extension_overflow) ? 32'd4 : 32'd0);

  assign csr_ready=enabled && owner==NO_RESPONSE && (extension_address || parent_ready);
  assign csr_rsp_valid=enabled &&
    (owner==D2_RESPONSE || (owner==PARENT_RESPONSE && parent_valid));
  assign csr_rdata=!enabled ? 32'd0 : owner==D2_RESPONSE ? local_data :
    owner==PARENT_RESPONSE ? inherited_response : 32'd0;
  assign csr_error=csr_rsp_valid &&
    (owner==D2_RESPONSE ? local_error : parent_error);
  assign mtp_enable=rst_n && features[0];
  assign fp8_enable=rst_n && features[1];
  assign generation_enable=rst_n && policy;
  assign generation_limit=rst_n ? limit : 32'd1;
  assign eos_token=rst_n ? eos : VOCAB_SIZE-1;

  assign increment[0]={35'd0,generation_active};
  assign increment[1]={35'd0,generated_retire};
  assign increment[2]={33'd0,proposed_increment};
  assign increment[3]={35'd0,accepted_retire};
  assign increment[4]={35'd0,rejected_block};
  assign increment[5]={4'd0,cache_payload_read_bytes};
  assign increment[6]={4'd0,cache_payload_write_bytes};
  assign increment[7]={4'd0,cache_scale_bytes};
  assign increment[8]={4'd0,expert_payload_read_bytes};
  assign increment[9]={4'd0,expert_scale_bytes};
  assign increment[10]={35'd0,verification_active};

  anvil_d1_csr_perf #(.VOCAB_SIZE(VOCAB_SIZE)) inherited (
    .clk(clk),.rst_n(rst_n),
    .csr_valid(parent_request),.csr_write(csr_write),.csr_addr(csr_addr),
    .csr_wdata(csr_wdata),.csr_wstrb(csr_wstrb),
    .csr_rsp_ready(owner==PARENT_RESPONSE && csr_rsp_ready),
    .csr_ready(parent_ready),.csr_rsp_valid(parent_valid),.csr_rdata(parent_data),
    .csr_error(parent_error),.token_accept(token_accept),.token_complete(token_complete),
    .token_error(token_error),.reasoning_active(reasoning_active),
    .shared_busy(shared_busy),.prefetch_busy(prefetch_busy),.domain_id(domain_select),
    .cache_read_bytes(cache_read_bytes),.cache_write_bytes(cache_write_bytes),
    .cache_dense_equiv_bytes(cache_dense_equiv_bytes),
    .expert_read_bytes(expert_read_bytes),.expert_dense_equiv_bytes(expert_dense_equiv_bytes),
    .other_read_bytes(other_read_bytes),.other_write_bytes(other_write_bytes),
    .domain_select(domain_select),.think_begin_token(think_begin_token),
    .think_end_token(think_end_token)
  );
  generate
    if (MODEL_MODE!=0 && MODEL_MODE!=1) begin: invalid_mode
      initial $fatal(1,"ANVIL_D2 PARAMETER ERROR: CSR MODEL_MODE");
    end
    for (genvar n=0;n<11;n=n+1) begin: extension_counters
      anvil_d1_counter64 counter (
        .clk(clk),.rst_n(rst_n),.clear(clear),.snapshot(snapshot),
        .increment(armed ? increment[n] : 36'd0),
        .live_value(live_count[n]),.snapshot_value(saved_count[n]),
        .overflow(extension_overflow[n])
      );
    end
  endgenerate

  always @* begin
    decode_error=0;
    decode_data=0;
    counter_index=0;
    if (csr_addr[1:0]!=0) decode_error=1;
    else if (csr_write) begin
      if (csr_wstrb!=4'hf || configuring_busy) decode_error=1;
      else case (csr_addr)
        12'h284: if (csr_wdata[31:2]!=0 || (MODEL_MODE==1 && csr_wdata[1:0]!=0))
          decode_error=1;
        12'h288: if (csr_wdata==0 || csr_wdata>MAX_SEQ_LEN) decode_error=1;
        12'h28c: if (csr_wdata>=VOCAB_SIZE) decode_error=1;
        12'h290: if (csr_wdata[31:1]!=0 || (MODEL_MODE==1 && csr_wdata[0]))
          decode_error=1;
        default: decode_error=1;
      endcase
    end else case (csr_addr)
      12'h280: decode_data=32'h00020000;
      12'h284: decode_data={30'd0,features};
      12'h288: decode_data=limit;
      12'h28c: decode_data=eos;
      12'h290: decode_data={31'd0,policy};
      default: begin
        if (csr_addr>=12'h300 && csr_addr<12'h358) begin
          counter_index=(csr_addr-12'h300)>>3;
          if (saved_valid) decode_data=csr_addr[2] ?
            saved_count[counter_index][63:32] : saved_count[counter_index][31:0];
        end else decode_error=1;
      end
    endcase
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      owner<=NO_RESPONSE; armed<=0; local_error<=0; local_data<=0;
      saved_valid<=0; parent_status<=0; parent_extension_overflow<=0;
      features<=0; policy<=0; limit<=1; eos<=VOCAB_SIZE-1;
    end else begin
      armed<=1;
      if (clear) saved_valid<=0;
      else if (snapshot) saved_valid<=1;
      if (csr_rsp_valid && csr_rsp_ready) owner<=NO_RESPONSE;
      if (accepted) begin
        if (extension_address) begin
          owner<=D2_RESPONSE;
          local_error<=decode_error;
          local_data<=csr_write || decode_error ? 32'd0 : decode_data;
          if (csr_write && !decode_error) case (csr_addr)
            12'h284: features<=csr_wdata[1:0];
            12'h288: limit<=csr_wdata;
            12'h28c: eos<=csr_wdata;
            12'h290: policy<=csr_wdata[0];
            default: begin end
          endcase
        end else begin
          owner<=PARENT_RESPONSE;
          parent_status<=!csr_write && csr_addr==12'h00c;
          parent_extension_overflow<=|extension_overflow;
        end
      end
    end
  end
endmodule
