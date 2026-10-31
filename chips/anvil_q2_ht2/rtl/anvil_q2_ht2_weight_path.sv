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
  localparam DEPTH=8;
  reg [511:0] descriptors [0:DEPTH-1];
  reg [31:0] rows [0:DEPTH-1], columns [0:DEPTH-1];
  reg [7:0] sparsity;
  reg [3:0] tokens [0:DEPTH-1];
  reg [8191:0] activations [0:DEPTH-1];
  reg [511:0] keeps [0:DEPTH-1], zeros [0:DEPTH-1];
  reg [2047:0] scales [0:DEPTH-1];
  reg [63:0] tags [0:DEPTH-1];
  reg [32:0] addresses [0:DEPTH-1];
  reg [1:0] formats [0:DEPTH-1];
  reg [7:0] errors;
  reg [2:0] tail, meta_head, dma_head, output_head;
  reg [3:0] occupied, awaiting_metadata, awaiting_dma, decoding;
  reg meta_active, draining, protocol_fault, prefer_dma;
  reg [1:0] owner_head, owner_tail;
  reg [2:0] owners;
  reg [3:0] owner_dma, owner_discard;
  reg [6:0] owner_beats [0:3];
  reg offer_valid, offer_dma;
  reg [32:0] offer_address;
  reg [6:0] offer_beats;
  wire available=rst_n && !annul && !draining;
  wire meta_ready, meta_valid, meta_error, meta_idle;
  wire [1:0] meta_format;
  wire [32:0] meta_address;
  wire [511:0] meta_zero, meta_keep;
  wire [2047:0] meta_scale;
  wire [63:0] meta_tag;
  wire meta_mem_valid, meta_rsp_ready;
  wire [32:0] meta_mem_address;
  wire dma_ready, dma_valid, dma_error, dma_skip;
  wire [2047:0] dma_weight;
  wire [511:0] dma_keep;
  wire [63:0] dma_tag;
  wire dma_mem_valid, dma_fill_ready;
  wire [32:0] dma_mem_address;
  wire [6:0] dma_mem_beats;
  wire input_transfer=s_valid && s_ready;
  wire meta_start=available && awaiting_metadata!=0 && !meta_active && meta_ready;
  wire meta_complete=available && meta_active && meta_valid;
  wire dma_start=available && awaiting_dma!=0 && dma_ready;
  wire output_transfer=m_valid && m_ready;
  wire memory_transfer=mem_valid && mem_ready;
  wire fill_transfer=fill_valid && fill_ready;
  wire owner_complete=fill_transfer && fill_last;
  wire bad_last=owners!=0 && fill_last!=(owner_beats[owner_head]==1);
  wire response_memory_error=fill_error || bad_last || owner_discard[owner_head];
  wire to_dma=owners!=0 && owner_dma[owner_head];
  wire selected_dma=dma_mem_valid && (prefer_dma || !meta_mem_valid);
  wire select_request=available && !offer_valid && owners<4 &&
    (meta_mem_valid || dma_mem_valid);
  wire response_error=dma_error || errors[output_head] ||
    dma_tag!=tags[output_head];
  integer q;

  anvil_q2_ht2_metadata_tile #(.GROUP_SIZE(GROUP_SIZE)) metadata (
    .clk(clk),.rst_n(rst_n),.annul(annul),
    .s_valid(available && awaiting_metadata!=0 && !meta_active),.s_ready(meta_ready),
    .s_descriptor(descriptors[meta_head]),.s_row(rows[meta_head]),
    .s_col(columns[meta_head]),.s_sparse(sparsity[meta_head]),
    .s_token_mask(tokens[meta_head]),.s_act(activations[meta_head]),
    .s_keep(keeps[meta_head]),.s_tag(tags[meta_head]),
    .m_valid(meta_valid),.m_ready(available && meta_active),
    .m_error(meta_error),.m_skipped(),.m_format(meta_format),
    .m_address(meta_address),.m_zero(meta_zero),.m_keep(meta_keep),
    .m_scale(meta_scale),.m_tag(meta_tag),.idle(meta_idle),
    .mem_valid(meta_mem_valid),
    .mem_ready(memory_transfer && !offer_dma),
    .mem_address(meta_mem_address),
    .mem_rsp_valid(rst_n && owners!=0 && !to_dma && fill_valid),
    .mem_rsp_error(response_memory_error),.mem_rsp_ready(meta_rsp_ready),
    .mem_rsp_data(fill_data)
  );
  anvil_q2_ht2_sparse_w2w4_dma dma (
    .clk(clk),.rst_n(rst_n),.annul(annul),
    .s_valid(available && awaiting_dma!=0),.s_ready(dma_ready),
    .s_format(formats[dma_head]),.s_sparse(1'b0),
    .s_token_mask(errors[dma_head] ? 4'd0 : tokens[dma_head]),
    .s_act(activations[dma_head]),.s_keep(keeps[dma_head]),
    .s_address(addresses[dma_head]),.s_zero(zeros[dma_head]),
    .s_scale(scales[dma_head]),.s_tag(tags[dma_head]),
    .m_ready(available && decoding!=0 && m_ready),
    .m_valid(dma_valid),.m_error(dma_error),
    .m_weight(dma_weight),.m_keep(dma_keep),.m_tag(dma_tag),.m_skipped(dma_skip),
    .mem_valid(dma_mem_valid),.mem_ready(memory_transfer && offer_dma),
    .mem_address(dma_mem_address),.mem_beats(dma_mem_beats),
    .fill_valid(rst_n && to_dma && fill_valid),
    .fill_error(response_memory_error),.fill_last(fill_last),
    .fill_data(fill_data),.fill_ready(dma_fill_ready)
  );

  assign s_ready=available && occupied<DEPTH;
  assign m_valid=available && decoding!=0 && dma_valid;
  assign m_error=m_valid && response_error;
  assign m_skipped=m_valid && !response_error && dma_skip;
  assign m_format=m_valid ? formats[output_head] : 2'd0;
  assign m_token_mask=m_valid ? tokens[output_head] : 4'd0;
  assign m_act=m_valid && !response_error ? activations[output_head] : 8192'd0;
  assign m_weight=m_valid && !response_error ? dma_weight : 2048'd0;
  assign m_keep=m_valid && !response_error ? dma_keep : 512'd0;
  assign m_tag=m_valid ? tags[output_head] : 64'd0;
  assign idle=rst_n && !draining && occupied==0 && owners==0 &&
    !offer_valid && meta_idle && dma_ready;
  assign fault=rst_n && protocol_fault;
  assign mem_valid=available && offer_valid;
  assign mem_address=mem_valid ? offer_address : 33'd0;
  assign mem_beats=mem_valid ? offer_beats : 7'd0;
  assign fill_ready=rst_n && owners!=0 &&
    (annul || draining || owner_discard[owner_head] ||
      (to_dma ? dma_fill_ready : meta_rsp_ready));

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      tail<=0; meta_head<=0; dma_head<=0; output_head<=0;
      occupied<=0; awaiting_metadata<=0; awaiting_dma<=0; decoding<=0;
      meta_active<=0; draining<=0; protocol_fault<=0; prefer_dma<=0;
      owner_head<=0; owner_tail<=0; owners<=0; owner_dma<=0; owner_discard<=0;
      offer_valid<=0; offer_dma<=0; offer_address<=0; offer_beats<=0;
      sparsity<=0; errors<=0;
      for (q=0;q<DEPTH;q=q+1) begin
        descriptors[q]<=0; rows[q]<=0; columns[q]<=0; tokens[q]<=0;
        activations[q]<=0; keeps[q]<=0; zeros[q]<=0; scales[q]<=0;
        tags[q]<=0; addresses[q]<=0; formats[q]<=0;
      end
      for (q=0;q<4;q=q+1) owner_beats[q]<=0;
    end else begin
      protocol_fault<=0;
      if (fill_valid && owners==0) protocol_fault<=1;
      if (memory_transfer) begin
        owner_dma[owner_tail]<=offer_dma; owner_discard[owner_tail]<=0;
        owner_beats[owner_tail]<=offer_beats; owner_tail<=owner_tail+2'd1;
        offer_valid<=0; prefer_dma<=!offer_dma;
      end
      if (fill_transfer) begin
        if (bad_last || fill_error) protocol_fault<=1;
        if (bad_last) owner_discard[owner_head]<=1;
        if (fill_last) owner_head<=owner_head+2'd1;
        else if (owner_beats[owner_head]!=0)
          owner_beats[owner_head]<=owner_beats[owner_head]-7'd1;
      end
      case ({memory_transfer,owner_complete})
        2'b10: owners<=owners+3'd1;
        2'b01: owners<=owners-3'd1;
        default: begin end
      endcase
      if (annul) begin
        tail<=0; meta_head<=0; dma_head<=0; output_head<=0;
        occupied<=0; awaiting_metadata<=0; awaiting_dma<=0; decoding<=0;
        meta_active<=0; offer_valid<=0; draining<=1;
      end else if (draining) begin
        if (owners==0 && meta_idle && dma_ready) draining<=0;
      end else begin
        if (select_request) begin
          offer_valid<=1; offer_dma<=selected_dma;
          offer_address<=selected_dma ? dma_mem_address : meta_mem_address;
          offer_beats<=selected_dma ? dma_mem_beats : 7'd1;
        end
        if (input_transfer) begin
          descriptors[tail]<=s_descriptor; rows[tail]<=s_row; columns[tail]<=s_col;
          sparsity[tail]<=s_sparse; tokens[tail]<=s_token_mask;
          activations[tail]<=s_act; keeps[tail]<=s_keep; tags[tail]<=s_tag;
          errors[tail]<=0; tail<=tail+3'd1;
        end
        if (meta_start) meta_active<=1;
        if (meta_complete) begin
          addresses[meta_head]<=meta_address; formats[meta_head]<=meta_format;
          zeros[meta_head]<=meta_zero; scales[meta_head]<=meta_scale;
          keeps[meta_head]<=meta_keep;
          errors[meta_head]<=meta_error || meta_tag!=tags[meta_head];
          meta_head<=meta_head+3'd1; meta_active<=0;
        end
        if (dma_start) dma_head<=dma_head+3'd1;
        if (output_transfer) output_head<=output_head+3'd1;
        case ({input_transfer,output_transfer})
          2'b10: occupied<=occupied+4'd1;
          2'b01: occupied<=occupied-4'd1;
          default: begin end
        endcase
        case ({input_transfer,meta_complete})
          2'b10: awaiting_metadata<=awaiting_metadata+4'd1;
          2'b01: awaiting_metadata<=awaiting_metadata-4'd1;
          default: begin end
        endcase
        case ({meta_complete,dma_start})
          2'b10: awaiting_dma<=awaiting_dma+4'd1;
          2'b01: awaiting_dma<=awaiting_dma-4'd1;
          default: begin end
        endcase
        case ({dma_start,output_transfer})
          2'b10: decoding<=decoding+4'd1;
          2'b01: decoding<=decoding-4'd1;
          default: begin end
        endcase
      end
    end
  end
endmodule
