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
  reg [7:0] sparsity, allocated, metadata_started, metadata_done;
  reg [7:0] payload_started, payload_done, dma_started, errors;
  reg [3:0] tokens [0:DEPTH-1];
  reg [8191:0] activations [0:DEPTH-1];
  reg [511:0] keeps [0:DEPTH-1], zeros [0:DEPTH-1];
  reg [2047:0] scales [0:DEPTH-1];
  reg [63:0] tags [0:DEPTH-1];
  reg [32:0] addresses [0:DEPTH-1];
  reg [1:0] formats [0:DEPTH-1];
  reg [2:0] tail, output_head, owner_head, owner_tail;
  reg [3:0] occupied, owners, round_robin;
  reg draining, protocol_fault;
  reg [3:0] owner_client [0:7];
  reg [7:0] owner_discard;
  reg [7:0] owner_cache;
  reg [32:0] owner_address [0:7];
  reg [6:0] owner_beats [0:7];
  reg [7:0] cached;
  reg [26:0] cache_line [0:7];
  reg [511:0] cache_data [0:7];
  reg [2:0] cache_replace;
  reg offer_valid;
  reg [3:0] offer_client;
  reg [32:0] offer_address;
  reg [6:0] offer_beats;
  wire available=rst_n && !annul && !draining;
  wire [7:0] meta_ready, meta_valid, meta_error, meta_idle;
  wire [7:0] payload_ready, payload_valid, payload_error, payload_idle;
  wire [7:0] dma_ready, dma_valid, dma_error, dma_skip, replay_busy;
  wire [16383:0] dma_weight;
  wire [4095:0] dma_keep;
  wire [511:0] dma_tag;
  wire [15:0] request_valid, response_ready;
  wire [32:0] request_address [0:15];
  wire [6:0] request_beats [0:15];
  wire input_transfer=s_valid && s_ready;
  wire output_transfer=m_valid && m_ready;
  wire memory_transfer=mem_valid && mem_ready;
  wire fill_transfer=fill_valid && fill_ready;
  wire owner_complete=fill_transfer && fill_last;
  wire bad_last=owners!=0 && fill_last!=(owner_beats[owner_head]==1);
  wire response_memory_error=fill_error || bad_last || owner_discard[owner_head];
  wire response_error=dma_error[output_head] || errors[output_head] ||
    dma_tag[64*output_head+:64]!=tags[output_head];
  wire offer_space=(owners<8 || owner_complete) &&
    !(owners==7 && memory_transfer && !owner_complete);
  reg selected;
  reg [3:0] selected_client, candidate;
  integer offset, q;
  genvar worker;

  always @* begin
    selected=0; selected_client=0; candidate=0;
    for (offset=0;offset<16;offset=offset+1) begin
      candidate=round_robin+4'(offset);
      if (!selected && request_valid[candidate] &&
          !(memory_transfer && candidate==offer_client)) begin
        selected=1; selected_client=candidate;
      end
    end
  end

  generate for (worker=0;worker<DEPTH;worker=worker+1) begin: tile_context
    wire [1:0] meta_format;
    wire [32:0] meta_address;
    wire [511:0] meta_zero, meta_keep;
    wire [2047:0] meta_scale;
    wire [63:0] meta_tag;
    wire meta_start=available && allocated[worker] && !metadata_started[worker];
    wire meta_complete=available && allocated[worker] &&
      metadata_started[worker] && !metadata_done[worker] && meta_valid[worker];
    wire payload_start=available && allocated[worker] &&
      metadata_done[worker] && !payload_started[worker];
    wire payload_complete=available && allocated[worker] &&
      payload_started[worker] && !payload_done[worker] && payload_valid[worker];
    wire dma_start=available && allocated[worker] &&
      payload_done[worker] && !dma_started[worker];
    wire [2559:0] payload_image;
    wire payload_request_valid, payload_response_ready;
    wire [32:0] payload_request_address;
    wire [6:0] payload_request_beats;
    reg cache_hit, cache_pending;
    reg [2:0] cache_index;
    reg cached_response;
    reg [511:0] cached_word;
    integer cache_entry;
    wire cache_eligible=formats[worker]==3 && payload_request_beats==1;
    wire cached_accept=available && payload_request_valid && cache_hit &&
      !cached_response && !(offer_valid && offer_client==2*worker+1);
    assign request_valid[2*worker+1]=payload_request_valid &&
      !(cache_eligible && (cache_hit || cache_pending));
    assign request_address[2*worker+1]=payload_request_address;
    assign request_beats[2*worker+1]=payload_request_beats;
    assign response_ready[2*worker+1]=payload_response_ready && !cached_response;
    always @* begin
      cache_hit=0; cache_index=0; cache_pending=0;
      for (cache_entry=0;cache_entry<8;cache_entry=cache_entry+1) begin
        if (cache_eligible && !cache_hit && cached[cache_entry] &&
            cache_line[cache_entry]==payload_request_address[32:6]) begin
          cache_hit=1; cache_index=3'(cache_entry);
        end
        if (cache_eligible && 4'(cache_entry)<owners &&
            owner_cache[3'(owner_head+3'(cache_entry))] &&
            owner_address[3'(owner_head+3'(cache_entry))]==payload_request_address)
          cache_pending=1;
      end
      if (cache_eligible && offer_valid && offer_client[0] &&
          formats[offer_client[3:1]]==3 && offer_beats==1 &&
          offer_address==payload_request_address)
        cache_pending=1;
    end
    reg [2559:0] image;
    reg replay_active, replay_error;
    reg [2:0] replay_beat;
    reg [6:0] replay_left;
    wire replay_request_valid, replay_response_ready;
    wire [32:0] replay_address;
    wire [6:0] replay_beats;
    wire [33:0] replay_offset={1'b0,replay_address}-
      {1'b0,addresses[worker][32:6],6'd0};
    wire [33:0] replay_end={27'd0,replay_beats}+(replay_offset >> 6);
    wire replay_request=available && replay_request_valid && !replay_active;
    wire replay_transfer=available && replay_active && replay_response_ready;
    wire meta_fill=rst_n && owners!=0 && owner_client[owner_head]==2*worker &&
      !owner_discard[owner_head] && fill_valid;
    wire payload_fill=rst_n && owners!=0 &&
      owner_client[owner_head]==2*worker+1 && fill_valid;
    assign replay_busy[worker]=replay_active;
    assign request_beats[2*worker]=7'd1;

    anvil_q2_ht2_metadata_tile #(.GROUP_SIZE(GROUP_SIZE)) metadata (
      .clk(clk),.rst_n(rst_n),.annul(annul),
      .s_valid(meta_start),.s_ready(meta_ready[worker]),
      .s_descriptor(descriptors[worker]),.s_row(rows[worker]),
      .s_col(columns[worker]),.s_sparse(sparsity[worker]),
      .s_token_mask(tokens[worker]),.s_act(activations[worker]),
      .s_keep(keeps[worker]),.s_tag(tags[worker]),
      .m_valid(meta_valid[worker]),.m_ready(available && allocated[worker] &&
        metadata_started[worker] && !metadata_done[worker]),
      .m_error(meta_error[worker]),.m_skipped(),.m_format(meta_format),
      .m_address(meta_address),.m_zero(meta_zero),.m_keep(meta_keep),
      .m_scale(meta_scale),.m_tag(meta_tag),.idle(meta_idle[worker]),
      .mem_valid(request_valid[2*worker]),
      .mem_ready(memory_transfer && offer_client==2*worker),
      .mem_address(request_address[2*worker]),
      .mem_rsp_valid(meta_fill),.mem_rsp_error(response_memory_error),
      .mem_rsp_ready(response_ready[2*worker]),.mem_rsp_data(fill_data)
    );
    anvil_q2_ht2_payload_prefetch read_ahead (
      .clk(clk),.rst_n(rst_n),.annul(annul),
      .s_valid(payload_start),.s_ready(payload_ready[worker]),
      .s_format(formats[worker]),.s_address(addresses[worker]),
      .s_keep(keeps[worker]),.s_token_mask(errors[worker] ? 4'd0 : tokens[worker]),
      .m_valid(payload_valid[worker]),.m_ready(available && allocated[worker] &&
        payload_started[worker] && !payload_done[worker]),
      .m_error(payload_error[worker]),.m_image(payload_image),
      .idle(payload_idle[worker]),
      .mem_valid(payload_request_valid),
      .mem_ready((memory_transfer && offer_client==2*worker+1) || cached_accept),
      .mem_address(payload_request_address),.mem_beats(payload_request_beats),
      .fill_valid(payload_fill || (rst_n && cached_response)),
      .fill_error(!cached_response && response_memory_error),
      .fill_last(cached_response || fill_last),
      .fill_data(cached_response ? cached_word : fill_data),
      .fill_ready(payload_response_ready)
    );
    anvil_q2_ht2_sparse_w2w4_dma dma (
      .clk(clk),.rst_n(rst_n),.annul(annul),
      .s_valid(dma_start),.s_ready(dma_ready[worker]),
      .s_format(formats[worker]),.s_sparse(1'b0),
      .s_token_mask(errors[worker] ? 4'd0 : tokens[worker]),
      .s_act(activations[worker]),.s_keep(keeps[worker]),
      .s_address(addresses[worker]),.s_zero(zeros[worker]),
      .s_scale(scales[worker]),.s_tag(tags[worker]),
      .m_ready(available && allocated[worker] && dma_started[worker] &&
        output_head==worker && m_ready),
      .m_valid(dma_valid[worker]),.m_error(dma_error[worker]),
      .m_weight(dma_weight[2048*worker+:2048]),
      .m_keep(dma_keep[512*worker+:512]),.m_tag(dma_tag[64*worker+:64]),
      .m_skipped(dma_skip[worker]),
      .mem_valid(replay_request_valid),.mem_ready(available && !replay_active),
      .mem_address(replay_address),.mem_beats(replay_beats),
      .fill_valid(rst_n && replay_active),.fill_error(replay_error),
      .fill_last(annul || replay_left==1),
      .fill_data(replay_error ? 512'd0 : image[512*replay_beat+:512]),
      .fill_ready(replay_response_ready)
    );
    always @(posedge clk) begin
      if (payload_complete) image<=payload_image;
    end
    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        allocated[worker]<=0; metadata_started[worker]<=0; metadata_done[worker]<=0;
        payload_started[worker]<=0; payload_done[worker]<=0; dma_started[worker]<=0;
        descriptors[worker]<=0; rows[worker]<=0; columns[worker]<=0;
        sparsity[worker]<=0; tokens[worker]<=0; activations[worker]<=0;
        keeps[worker]<=0; zeros[worker]<=0; scales[worker]<=0; tags[worker]<=0;
        addresses[worker]<=0; formats[worker]<=0; errors[worker]<=0;
        replay_active<=0; replay_error<=0; replay_beat<=0; replay_left<=0;
        cached_response<=0; cached_word<=0;
      end else if (annul) begin
        allocated[worker]<=0; metadata_started[worker]<=0; metadata_done[worker]<=0;
        payload_started[worker]<=0; payload_done[worker]<=0; dma_started[worker]<=0;
        replay_active<=0;
        cached_response<=0;
      end else if (!draining) begin
        if (cached_accept) begin
          cached_response<=1; cached_word<=cache_data[cache_index];
        end else if (cached_response && payload_response_ready) cached_response<=0;
        if (input_transfer && tail==worker) begin
          allocated[worker]<=1; metadata_started[worker]<=0; metadata_done[worker]<=0;
          payload_started[worker]<=0; payload_done[worker]<=0; dma_started[worker]<=0;
          descriptors[worker]<=s_descriptor; rows[worker]<=s_row; columns[worker]<=s_col;
          sparsity[worker]<=s_sparse; tokens[worker]<=s_token_mask;
          activations[worker]<=s_act; keeps[worker]<=s_keep; tags[worker]<=s_tag;
          errors[worker]<=0;
        end
        if (meta_start && meta_ready[worker]) metadata_started[worker]<=1;
        if (meta_complete) begin
          metadata_done[worker]<=1; addresses[worker]<=meta_address;
          formats[worker]<=meta_format; zeros[worker]<=meta_zero;
          scales[worker]<=meta_scale; keeps[worker]<=meta_keep;
          errors[worker]<=meta_error[worker] || meta_tag!=tags[worker];
        end
        if (payload_start && payload_ready[worker]) payload_started[worker]<=1;
        if (payload_complete) begin
          payload_done[worker]<=1;
          if (payload_error[worker]) errors[worker]<=1;
        end
        if (dma_start && dma_ready[worker]) dma_started[worker]<=1;
        if (output_transfer && output_head==worker) allocated[worker]<=0;
        if (replay_request) begin
          replay_active<=1; replay_beat<=replay_offset[8:6];
          replay_left<=replay_beats==0 ? 7'd1 : replay_beats;
          replay_error<=replay_beats==0 || replay_offset[5:0]!=0 ||
            replay_offset[33] || replay_end>5;
        end
        if (replay_transfer) begin
          if (replay_left==1) replay_active<=0;
          else begin replay_left<=replay_left-7'd1; replay_beat<=replay_beat+3'd1; end
        end
      end
    end
  end endgenerate

  assign s_ready=available && occupied<DEPTH;
  assign m_valid=available && occupied!=0 && allocated[output_head] &&
    dma_started[output_head] && dma_valid[output_head];
  assign m_error=m_valid && response_error;
  assign m_skipped=m_valid && !response_error && dma_skip[output_head];
  assign m_format=m_valid ? formats[output_head] : 2'd0;
  assign m_token_mask=m_valid ? tokens[output_head] : 4'd0;
  assign m_act=m_valid && !response_error ? activations[output_head] : 8192'd0;
  assign m_weight=m_valid && !response_error ? dma_weight[2048*output_head+:2048] : 2048'd0;
  assign m_keep=m_valid && !response_error ? dma_keep[512*output_head+:512] : 512'd0;
  assign m_tag=m_valid ? tags[output_head] : 64'd0;
  assign idle=rst_n && !draining && occupied==0 && owners==0 && !offer_valid &&
    (&meta_idle) && (&payload_idle) && (&dma_ready) && !(|replay_busy);
  assign fault=rst_n && protocol_fault;
  assign mem_valid=available && offer_valid;
  assign mem_address=mem_valid ? offer_address : 33'd0;
  assign mem_beats=mem_valid ? offer_beats : 7'd0;
  assign fill_ready=rst_n && owners!=0 &&
    (annul || draining || owner_discard[owner_head] ||
      response_ready[owner_client[owner_head]]);

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      tail<=0; output_head<=0; occupied<=0; draining<=0; protocol_fault<=0;
      owner_head<=0; owner_tail<=0; owners<=0; owner_discard<=0;
      owner_cache<=0; cached<=0; cache_replace<=0;
      offer_valid<=0; offer_client<=0; offer_address<=0; offer_beats<=0;
      round_robin<=0;
      for (q=0;q<8;q=q+1) begin
        owner_beats[q]<=0; owner_client[q]<=0; owner_address[q]<=0;
        cache_line[q]<=0; cache_data[q]<=0;
      end
    end else begin
      protocol_fault<=0;
      if (fill_valid && owners==0) protocol_fault<=1;
      if (memory_transfer) begin
        owner_client[owner_tail]<=offer_client; owner_discard[owner_tail]<=0;
        owner_address[owner_tail]<=offer_address;
        owner_cache[owner_tail]<=offer_client[0] &&
          formats[offer_client[3:1]]==3 && offer_beats==1;
        owner_beats[owner_tail]<=offer_beats; owner_tail<=owner_tail+3'd1;
        offer_valid<=0; round_robin<=offer_client+4'd1;
      end
      if (fill_transfer) begin
        if (bad_last || fill_error) protocol_fault<=1;
        if (bad_last) owner_discard[owner_head]<=1;
        if (fill_last) owner_head<=owner_head+3'd1;
        else if (owner_beats[owner_head]!=0)
          owner_beats[owner_head]<=owner_beats[owner_head]-7'd1;
        if (!annul && !draining && owner_cache[owner_head] && fill_last &&
            !response_memory_error) begin
          cached[cache_replace]<=1;
          cache_line[cache_replace]<=owner_address[owner_head][32:6];
          cache_data[cache_replace]<=fill_data; cache_replace<=cache_replace+3'd1;
        end
      end
      case ({memory_transfer,owner_complete})
        2'b10: owners<=owners+4'd1;
        2'b01: owners<=owners-4'd1;
        default: begin end
      endcase
      if (annul) begin
        tail<=0; output_head<=0; occupied<=0; offer_valid<=0; draining<=1;
        cached<=0;
      end else if (draining) begin
        if (owners==0 && (&meta_idle) && (&payload_idle) && (&dma_ready))
          draining<=0;
      end else begin
        if ((!offer_valid || memory_transfer) && offer_space && selected) begin
          offer_valid<=1; offer_client<=selected_client;
          offer_address<=request_address[selected_client];
          offer_beats<=request_beats[selected_client];
        end
        if (input_transfer) tail<=tail+3'd1;
        if (output_transfer) output_head<=output_head+3'd1;
        case ({input_transfer,output_transfer})
          2'b10: occupied<=occupied+4'd1;
          2'b01: occupied<=occupied-4'd1;
          default: begin end
        endcase
      end
    end
  end
endmodule
