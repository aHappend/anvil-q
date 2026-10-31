module anvil_q2_ht2_weight_path #(
  parameter GROUP_SIZE=128
) (
  input wire clk, rst_n, annul, s_valid,
  output wire s_ready,
  input wire [511:0] s_descriptor,
  input wire [31:0] s_row, s_col,
  input wire s_sparse,
  input wire [3:0] s_token_mask,
  input wire [8191:0] s_act,
  input wire [511:0] s_keep,
  input wire [63:0] s_tag,
  output wire m_valid,
  input wire m_ready,
  output wire m_error, m_skipped,
  output wire [1:0] m_format,
  output wire [3:0] m_token_mask,
  output wire [8191:0] m_act,
  output wire [2047:0] m_weight,
  output wire [511:0] m_keep,
  output wire [63:0] m_tag,
  output wire idle, fault,
  output wire mem_valid,
  input wire mem_ready,
  output wire [32:0] mem_address,
  output wire [6:0] mem_beats,
  input wire fill_valid, fill_error, fill_last,
  input wire [511:0] fill_data,
  output wire fill_ready
);
  localparam [2:0] IDLE=0, META_SEND=1, META_WAIT=2,
    DMA_SEND=3, DMA_WAIT=4, ERROR_RESPONSE=5;
  reg [2:0] state;
  reg [511:0] descriptor;
  reg [31:0] row, col;
  reg sparse;
  reg [3:0] tokens;
  reg [8191:0] activations;
  reg [511:0] keep, zeros, effective_keep;
  reg [2047:0] scales;
  reg [63:0] tag;
  reg [32:0] address;
  reg [1:0] format;
  reg memory_owned, memory_dma, memory_discard, protocol_fault, transaction_error;
  reg [6:0] remaining;
  wire available=rst_n && !annul;
  wire meta_ready, meta_valid, meta_error, meta_skip, meta_idle;
  wire [1:0] meta_format;
  wire [32:0] meta_address;
  wire [511:0] meta_zero, meta_keep;
  wire [2047:0] meta_scale;
  wire [63:0] meta_tag;
  wire meta_mem_valid, meta_mem_rsp_ready;
  wire [32:0] meta_mem_address;
  wire dma_ready, dma_valid, dma_error, dma_skip;
  wire [2047:0] dma_weight;
  wire [511:0] dma_keep;
  wire [63:0] dma_tag;
  wire dma_mem_valid, dma_fill_ready;
  wire [32:0] dma_mem_address;
  wire [6:0] dma_mem_beats;
  wire selecting_dma=state==DMA_SEND || state==DMA_WAIT;
  wire memory_transfer=mem_valid && mem_ready;
  wire fill_transfer=fill_valid && fill_ready;
  wire bad_last=fill_last!=(remaining==1);
  wire response_memory_error=fill_error || bad_last;

  anvil_q2_ht2_metadata_tile #(.GROUP_SIZE(GROUP_SIZE)) metadata (
    .clk(clk),.rst_n(rst_n),.annul(annul),
    .s_valid(available && state==META_SEND),.s_ready(meta_ready),
    .s_descriptor(descriptor),.s_row(row),.s_col(col),.s_sparse(sparse),
    .s_token_mask(tokens),.s_act(activations),.s_keep(keep),.s_tag(tag),
    .m_valid(meta_valid),.m_ready(available && state==META_WAIT),
    .m_error(meta_error),.m_skipped(meta_skip),.m_format(meta_format),
    .m_address(meta_address),.m_zero(meta_zero),.m_keep(meta_keep),
    .m_scale(meta_scale),.m_tag(meta_tag),.idle(meta_idle),
    .mem_valid(meta_mem_valid),.mem_ready(!memory_owned && !selecting_dma && mem_ready),
    .mem_address(meta_mem_address),
    .mem_rsp_valid(memory_owned && !memory_dma && fill_valid),
    .mem_rsp_error(response_memory_error),.mem_rsp_ready(meta_mem_rsp_ready),
    .mem_rsp_data(fill_data)
  );
  anvil_q2_ht2_sparse_w2w4_dma dma (
    .clk(clk),.rst_n(rst_n),.annul(annul),
    .s_valid(available && state==DMA_SEND),.s_ready(dma_ready),
    .s_format(format),.s_sparse(1'b0),.s_token_mask(tokens),
    .s_act(activations),.s_keep(effective_keep),.s_address(address),
    .s_zero(zeros),.s_scale(scales),.s_tag(tag),
    .m_ready(available && state==DMA_WAIT && m_ready && !memory_owned),
    .m_valid(dma_valid),.m_error(dma_error),
    .m_weight(dma_weight),.m_keep(dma_keep),.m_tag(dma_tag),.m_skipped(dma_skip),
    .mem_valid(dma_mem_valid),.mem_ready(!memory_owned && selecting_dma && mem_ready),
    .mem_address(dma_mem_address),.mem_beats(dma_mem_beats),
    .fill_valid(memory_owned && memory_dma && fill_valid),
    .fill_error(response_memory_error),.fill_last(fill_last),
    .fill_data(fill_data),.fill_ready(dma_fill_ready)
  );

  assign s_ready=available && state==IDLE && !memory_owned && meta_ready && dma_ready;
  assign m_valid=available && !memory_owned &&
    ((state==DMA_WAIT && dma_valid) || state==ERROR_RESPONSE);
  assign m_error=m_valid && (state==ERROR_RESPONSE || dma_error || transaction_error ||
    (dma_valid && dma_tag!=tag));
  assign m_skipped=m_valid && !m_error && dma_skip;
  assign m_format=m_valid ? format : 2'd0;
  assign m_token_mask=m_valid ? tokens : 4'd0;
  assign m_act=m_valid && !m_error ? activations : 8192'd0;
  assign m_weight=m_valid && !m_error ? dma_weight : 2048'd0;
  assign m_keep=m_valid && !m_error ? dma_keep : 512'd0;
  assign m_tag=m_valid ? tag : 64'd0;
  assign idle=rst_n && state==IDLE && !memory_owned && meta_idle && dma_ready;
  assign fault=rst_n && protocol_fault;
  assign mem_valid=available && !memory_owned &&
    (selecting_dma ? dma_mem_valid : meta_mem_valid);
  assign mem_address=mem_valid ?
    (selecting_dma ? dma_mem_address : meta_mem_address) : 33'd0;
  assign mem_beats=mem_valid ? (selecting_dma ? dma_mem_beats : 7'd1) : 7'd0;
  assign fill_ready=rst_n && memory_owned &&
    (annul || memory_discard || state==IDLE ||
      (memory_dma ? dma_fill_ready : meta_mem_rsp_ready));

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; descriptor<=0; row<=0; col<=0; sparse<=0;
      tokens<=0; activations<=0; keep<=0; zeros<=0; effective_keep<=0;
      scales<=0; tag<=0; address<=0; format<=0;
      memory_owned<=0; memory_dma<=0; memory_discard<=0;
      protocol_fault<=0; transaction_error<=0; remaining<=0;
    end else begin
      protocol_fault<=0;
      if (fill_valid && !memory_owned) protocol_fault<=1;
      if (memory_transfer) begin
        memory_owned<=1; memory_dma<=selecting_dma; remaining<=mem_beats;
        memory_discard<=0;
      end
      if (fill_transfer) begin
        if (bad_last || fill_error) begin
          protocol_fault<=1; transaction_error<=1;
        end
        if (bad_last) memory_discard<=1;
        if (fill_last) begin memory_owned<=0; remaining<=0; end
        else if (remaining!=0) remaining<=remaining-7'd1;
      end
      if (annul) begin
        state<=IDLE;
      end else case (state)
        IDLE: if (s_valid && s_ready) begin
          descriptor<=s_descriptor; row<=s_row; col<=s_col;
          sparse<=s_sparse; tokens<=s_token_mask; activations<=s_act;
          keep<=s_keep; tag<=s_tag; transaction_error<=0; state<=META_SEND;
        end
        META_SEND: if (meta_ready) state<=META_WAIT;
        META_WAIT: if (meta_valid) begin
          format<=meta_format;
          if (meta_error || meta_tag!=tag) state<=ERROR_RESPONSE;
          else begin
            address<=meta_address; zeros<=meta_zero; scales<=meta_scale;
            effective_keep<=meta_keep; state<=DMA_SEND;
          end
        end
        DMA_SEND: if (dma_ready) state<=DMA_WAIT;
        DMA_WAIT: if (m_valid && m_ready) state<=IDLE;
        ERROR_RESPONSE: if (m_valid && m_ready) state<=IDLE;
        default: begin state<=ERROR_RESPONSE; protocol_fault<=1; end
      endcase
    end
  end
endmodule
