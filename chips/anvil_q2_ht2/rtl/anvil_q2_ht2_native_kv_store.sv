module anvil_q2_ht2_native_kv_store #(
  parameter NUM_LAYERS=28, NUM_KV_HEADS=2, HEAD_DIM=128,
  parameter CACHE_BLOCK=16, MAX_SEQ_LEN=32768, VOCAB_SIZE=151936,
  parameter WORDS=(CACHE_BLOCK>=1 && CACHE_BLOCK<=128) ? CACHE_BLOCK : 1
) (
  input wire clk, rst_n, annul,
  input wire s_begin_valid,
  output wire s_begin_ready,
  input wire [2:0] s_count,
  input wire [127:0] s_ids,
  input wire [7:0] s_parent,
  input wire [31:0] s_position,
  input wire s_new_sequence, s_int8,
  input wire [32:0] s_base, s_length,
  output wire active, input_error, allocator_error, memory_idle,
  output wire [7:0] node_depth,
  input wire w_valid,
  output wire w_ready,
  input wire [1:0] w_slot,
  input wire [4:0] w_layer,
  input wire w_value, w_head,
  input wire [6:0] w_block,
  input wire [WORDS*16-1:0] w_data,
  output wire w_rsp_valid, w_rsp_error,
  input wire w_rsp_ready,
  input wire r_valid,
  output wire r_ready,
  input wire [1:0] r_slot,
  input wire [31:0] r_position,
  input wire [4:0] r_layer,
  input wire r_value, r_head,
  input wire [6:0] r_block,
  output wire r_rsp_valid, r_rsp_error,
  input wire r_rsp_ready,
  output wire [WORDS*16-1:0] r_data,
  input wire s_finish_valid,
  output wire s_finish_ready,
  input wire [127:0] s_target_ids,
  output wire m_valid, m_error,
  input wire m_ready,
  output wire [2:0] m_accepted,
  output wire [3:0] m_mask,
  output wire [31:0] m_next_token, m_position, committed_position,
  output wire commit_valid,
  output wire mem_valid,
  input wire mem_ready,
  output wire mem_write,
  output wire [32:0] mem_address,
  output wire [511:0] mem_wdata,
  output wire [63:0] mem_be,
  input wire mem_rsp_valid, mem_rsp_error,
  output wire mem_rsp_ready,
  input wire [511:0] mem_rsp_data
);
  localparam SAFE_BLOCK=(CACHE_BLOCK>=1 && CACHE_BLOCK<=128) ? CACHE_BLOCK : 1;
  localparam BLOCK_SHIFT=$clog2(SAFE_BLOCK);
  localparam LEGAL=NUM_LAYERS>=1 && NUM_LAYERS<=28 &&
    NUM_KV_HEADS>=1 && NUM_KV_HEADS<=2 &&
    HEAD_DIM>=2 && HEAD_DIM<=128 && (HEAD_DIM & 1)==0 &&
    ((NUM_KV_HEADS*HEAD_DIM) & 7)==0 &&
    CACHE_BLOCK>=1 && CACHE_BLOCK<=128 && WORDS==CACHE_BLOCK &&
    (CACHE_BLOCK & (CACHE_BLOCK-1))==0 && (HEAD_DIM & (SAFE_BLOCK-1))==0 &&
    MAX_SEQ_LEN>=1 && MAX_SEQ_LEN<=32768 && VOCAB_SIZE>=1 && VOCAB_SIZE<=151936;
  generate if (!LEGAL) begin: invalid_parameters
    initial $fatal(1,"ANVIL_Q2_HT2 PARAMETER ERROR: native KV storage geometry");
    assign s_begin_ready=0; assign active=0; assign input_error=0;
    assign allocator_error=0; assign memory_idle=0; assign node_depth=0;
    assign w_ready=0; assign w_rsp_valid=0; assign w_rsp_error=0;
    assign r_ready=0; assign r_rsp_valid=0; assign r_rsp_error=0; assign r_data=0;
    assign s_finish_ready=0; assign m_valid=0; assign m_error=0;
    assign m_accepted=0; assign m_mask=0; assign m_next_token=0; assign m_position=0;
    assign committed_position=0; assign commit_valid=0;
    assign mem_valid=0; assign mem_write=0; assign mem_address=0;
    assign mem_wdata=0; assign mem_be=0; assign mem_rsp_ready=0;
  end else begin: implementation
    localparam BLOCKS=HEAD_DIM >> BLOCK_SHIFT;
    localparam RECORDS_PER_LAYER=2*NUM_KV_HEADS*BLOCKS;
    localparam [63:0] BF16_PAGE_BYTES=64'(NUM_LAYERS*RECORDS_PER_LAYER)*(2*WORDS);
    localparam [63:0] INT8_PAGE_BYTES=64'(NUM_LAYERS*RECORDS_PER_LAYER)*(WORDS+2);
    localparam [63:0] BF16_EXTENT=BF16_PAGE_BYTES*(MAX_SEQ_LEN+4);
    localparam [63:0] INT8_EXTENT=INT8_PAGE_BYTES*(MAX_SEQ_LEN+4);
    localparam [4:0] IDLE=0, ENCODE_SEND=1, ENCODE_WAIT=2,
      MAP_SEND=3, MAP_WAIT=4, ADDRESS1=5, ADDRESS2=6, ADDRESS3=7, ADDRESS4=8,
      REQUEST=9, WAIT_MEMORY=10, DECODE_SEND=11, DECODE_WAIT=12, DRAIN=13;
    reg [4:0] state;
    reg sealed, int8_mode, writing, write_response, write_error;
    reg committed_format_valid, committed_int8;
    reg [32:0] committed_base, committed_length;
    reg read_response, read_error, configuration_bad;
    reg [2:0] count;
    reg [32:0] base, length, beat_address;
    reg [31:0] batch_position, page, request_position;
    reg [1:0] slot;
    reg [4:0] layer;
    reg [8:0] ordinal;
    reg [5:0] next_layer [0:3];
    reg [9:0] next_record [0:3];
    reg [111:0] completions;
    reg [3:0] kv_errors;
    reg [WORDS*16-1:0] source, decoded;
    reg [WORDS*16+15:0] encoded;
    reg [63:0] page_offset, local_record, record_offset, page_base, address;
    reg [5:0] offset;
    reg [2:0] beats_left, beat_index;
    reg [3071:0] window_data;
    reg [383:0] window_be;
    reg [383:0] prepared_be;
    reg provisional_read_good;
    wire map_active, map_bad, map_begin_ready, map_finish_ready;
    wire map_read_ready, map_response_valid, map_response_error;
    wire [31:0] map_page;
    wire [127:0] scratch;
    wire codec_ready, codec_valid, codec_error;
    wire [WORDS*16-1:0] codec_data;
    wire [WORDS*16+15:0] codec_record;
    wire [9:0] codec_length;
    wire [9:0] record_bytes=int8_mode ? 10'(WORDS+2) : 10'(2*WORDS);
    wire [8:0] w_ordinal=9'(w_value*(NUM_KV_HEADS*BLOCKS)+w_head*BLOCKS+w_block);
    wire [8:0] r_ordinal=9'(r_value*(NUM_KV_HEADS*BLOCKS)+r_head*BLOCKS+r_block);
    wire engine_available=state==IDLE && !write_response && !read_response;
    wire begin_transfer=s_begin_valid && s_begin_ready;
    wire write_transfer=w_valid && w_ready;
    wire read_transfer=r_valid && r_ready;
    wire finish_transfer=s_finish_valid && s_finish_ready;
    wire bad_write=map_bad || configuration_bad || {1'b0,w_slot}>=count ||
      w_layer>=NUM_LAYERS || w_head>=NUM_KV_HEADS || w_block>=BLOCKS ||
      {1'b0,w_layer}!=next_layer[w_slot] ||
      {1'b0,w_ordinal}!=next_record[w_slot];
    wire bad_read=map_bad || configuration_bad || {1'b0,r_slot}>=count ||
      r_layer>=NUM_LAYERS || r_head>=NUM_KV_HEADS || r_block>=BLOCKS;
    wire [63:0] unaligned_extent=s_int8 ? INT8_EXTENT : BF16_EXTENT;
    wire [63:0] required_extent=((unaligned_extent+64'd63) >> 6) << 6;
    wire [33:0] configured_end={1'b0,s_base}+{1'b0,s_length};
    wire bad_configuration=s_base[5:0]!=0 || {31'd0,s_length}<required_extent ||
      configured_end>34'h200000000 ||
      (committed_format_valid &&
        (s_int8!=committed_int8 || s_base!=committed_base || s_length!=committed_length));
    wire [63:0] region_end={31'd0,base}+{31'd0,length};
    wire [63:0] record_end=address+{54'd0,record_bytes};
    wire [10:0] covered_bytes={5'd0,address[5:0]}+{1'b0,record_bytes}+11'd63;
    wire [3071:0] read_window=window_data >> {offset,3'd0};
    wire [3071:0] encoded_window=
      {{(3072-WORDS*16-16){1'b0}},encoded} << {address[5:0],3'd0};
    integer prepare_i, progress_i;

    always @* begin
      prepared_be=0;
      for (prepare_i=0;prepare_i<384;prepare_i=prepare_i+1)
        if (prepare_i>=address[5:0] &&
            prepare_i<({26'd0,address[5:0]}+{22'd0,record_bytes}))
          prepared_be[prepare_i]=1;
      provisional_read_good=request_position<batch_position;
      for (prepare_i=0;prepare_i<4;prepare_i=prepare_i+1)
        if (request_position>=batch_position && page==scratch[32*prepare_i+:32] &&
            (layer<next_layer[prepare_i] ||
              (layer==next_layer[prepare_i] && {1'b0,ordinal}<next_record[prepare_i])))
          provisional_read_good=1;
    end

    anvil_q2_ht2_kv_map #(
      .NUM_LAYERS(NUM_LAYERS),.MAX_SEQ_LEN(MAX_SEQ_LEN),.VOCAB_SIZE(VOCAB_SIZE)
    ) mapping (
      .clk(clk),.rst_n(rst_n),.annul(annul),
      .s_begin_valid(s_begin_valid && engine_available),
      .s_begin_ready(map_begin_ready),.s_count(s_count),.s_ids(s_ids),
      .s_parent(s_parent),.s_position(s_position),.s_new_sequence(s_new_sequence),
      .active(map_active),.input_error(map_bad),.allocator_error(allocator_error),
      .provisional_pages(scratch),.node_depth(node_depth),
      .r_valid(state==MAP_SEND),.r_ready(map_read_ready),
      .r_slot(slot),.r_position(request_position),
      .r_rsp_valid(map_response_valid),.r_rsp_error(map_response_error),
      .r_rsp_ready(state==MAP_WAIT),.r_page(map_page),
      .s_finish_valid(s_finish_valid && engine_available && !w_valid && !r_valid),
      .s_finish_ready(map_finish_ready),.s_target_ids(s_target_ids),
      .s_kv_complete(completions),.s_kv_error(kv_errors),
      .m_valid(m_valid),.m_error(m_error),.m_ready(m_ready),
      .m_accepted(m_accepted),.m_mask(m_mask),.m_next_token(m_next_token),
      .m_position(m_position),.committed_position(committed_position),
      .commit_valid(commit_valid));

    anvil_q2_ht2_native_kv_codec #(.CACHE_BLOCK(CACHE_BLOCK),.WORDS(WORDS)) codec (
      .clk(clk),.rst_n(rst_n),.annul(annul),
      .s_valid(state==ENCODE_SEND || state==DECODE_SEND),
      .s_encode(state==ENCODE_SEND),.s_int8(int8_mode),.s_data(source),
      .s_record(read_window[WORDS*16+15:0]),.s_ready(codec_ready),
      .m_valid(codec_valid),.m_error(codec_error),
      .m_ready(state==ENCODE_WAIT || state==DECODE_WAIT),
      .m_data(codec_data),.m_record(codec_record),.m_byte_length(codec_length));

    assign active=map_active;
    assign input_error=map_active && (map_bad || configuration_bad);
    assign memory_idle=rst_n && state==IDLE;
    assign s_begin_ready=map_begin_ready && engine_available;
    assign w_ready=rst_n && !annul && map_active && !sealed && engine_available;
    assign r_ready=rst_n && !annul && map_active && !sealed &&
      engine_available && !w_valid;
    assign w_rsp_valid=rst_n && !annul && write_response;
    assign w_rsp_error=w_rsp_valid && write_error;
    assign r_rsp_valid=rst_n && !annul && read_response;
    assign r_rsp_error=r_rsp_valid && read_error;
    assign r_data=r_rsp_valid && !read_error ? decoded : {WORDS*16{1'b0}};
    assign s_finish_ready=map_finish_ready && engine_available && !w_valid && !r_valid;
    assign mem_valid=rst_n && !annul && state==REQUEST;
    assign mem_write=mem_valid && writing;
    assign mem_address=mem_valid ? beat_address : 33'd0;
    assign mem_wdata=mem_valid && writing ? window_data[511:0] : 512'd0;
    assign mem_be=mem_valid ? (writing ? window_be[63:0] : 64'hffffffffffffffff) :
      64'd0;
    assign mem_rsp_ready=rst_n && (state==WAIT_MEMORY || state==DRAIN);

    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        state<=IDLE; sealed<=0; int8_mode<=0; writing<=0;
        committed_format_valid<=0; committed_int8<=0;
        committed_base<=0; committed_length<=0;
        write_response<=0; write_error<=0; read_response<=0; read_error<=0;
        configuration_bad<=0; count<=0; base<=0; length<=0; beat_address<=0;
        batch_position<=0; page<=0; request_position<=0; slot<=0; layer<=0;
        ordinal<=0; completions<=0; kv_errors<=0; source<=0; decoded<=0; encoded<=0;
        page_offset<=0; local_record<=0; record_offset<=0; page_base<=0; address<=0;
        offset<=0; beats_left<=0; beat_index<=0; window_data<=0; window_be<=0;
        for (progress_i=0;progress_i<4;progress_i=progress_i+1) begin
          next_layer[progress_i]<=0; next_record[progress_i]<=0;
        end
      end else if (annul) begin
        write_response<=0; read_response<=0; sealed<=0;
        if ((state==WAIT_MEMORY || state==DRAIN) && !mem_rsp_valid) state<=DRAIN;
        else state<=IDLE;
      end else begin
        if (write_response && w_rsp_ready) write_response<=0;
        if (read_response && r_rsp_ready) read_response<=0;
        if (begin_transfer) begin
          sealed<=0; int8_mode<=s_int8; base<=s_base; length<=s_length;
          count<=s_count; batch_position<=s_position;
          configuration_bad<=bad_configuration;
          completions<=0; kv_errors<=bad_configuration ? 4'hf : 4'd0;
          for (progress_i=0;progress_i<4;progress_i=progress_i+1) begin
            next_layer[progress_i]<=0; next_record[progress_i]<=0;
          end
        end
        if (finish_transfer) sealed<=1;
        if (m_valid && m_ready && !m_error) begin
          committed_format_valid<=1; committed_int8<=int8_mode;
          committed_base<=base; committed_length<=length;
        end
        case (state)
          IDLE: begin
            if (write_transfer) begin
              if (bad_write) begin
                write_response<=1; write_error<=1; kv_errors<=4'hf;
              end else begin
                slot<=w_slot; layer<=w_layer; ordinal<=w_ordinal;
                source<=w_data; page<=scratch[32*w_slot+:32];
                writing<=1; state<=ENCODE_SEND;
              end
            end else if (read_transfer) begin
              if (bad_read) begin
                read_response<=1; read_error<=1; kv_errors<=4'hf;
              end else begin
                slot<=r_slot; layer<=r_layer; ordinal<=r_ordinal;
                request_position<=r_position;
                writing<=0; state<=MAP_SEND;
              end
            end
          end
          ENCODE_SEND: if (codec_ready) state<=ENCODE_WAIT;
          ENCODE_WAIT: if (codec_valid) begin
            if (codec_error || codec_length!=record_bytes) begin
              write_response<=1; write_error<=1; kv_errors<=4'hf; state<=IDLE;
            end else begin encoded<=codec_record; state<=ADDRESS1; end
          end
          MAP_SEND: if (map_read_ready) state<=MAP_WAIT;
          MAP_WAIT: if (map_response_valid) begin
            if (map_response_error) begin
              read_response<=1; read_error<=1; kv_errors<=4'hf; state<=IDLE;
            end else begin page<=map_page; state<=ADDRESS1; end
          end
          ADDRESS1: begin
            page_offset<=int8_mode ? {32'd0,page}*INT8_PAGE_BYTES :
              {32'd0,page}*BF16_PAGE_BYTES;
            local_record<=64'(layer)*RECORDS_PER_LAYER+{55'd0,ordinal};
            state<=ADDRESS2;
          end
          ADDRESS2: begin
            page_base<={31'd0,base}+page_offset;
            record_offset<=int8_mode ? local_record*(WORDS+2) : local_record*(2*WORDS);
            state<=ADDRESS3;
          end
          ADDRESS3: begin address<=page_base+record_offset; state<=ADDRESS4; end
          ADDRESS4: begin
            if (address<{31'd0,base} || record_end>region_end ||
                record_end>64'h200000000 || (!writing && !provisional_read_good)) begin
              if (writing) begin write_response<=1; write_error<=1; end
              else begin read_response<=1; read_error<=1; end
              kv_errors<=4'hf; state<=IDLE;
            end else begin
              beat_address<={address[32:6],6'd0};
              offset<=address[5:0]; beats_left<=3'(covered_bytes >> 6); beat_index<=0;
              window_data<=writing ? encoded_window : 3072'd0;
              window_be<=writing ? prepared_be : 384'd0;
              state<=REQUEST;
            end
          end
          REQUEST: if (mem_ready) state<=WAIT_MEMORY;
          WAIT_MEMORY: if (mem_rsp_valid) begin
            if (mem_rsp_error) begin
              if (writing) begin write_response<=1; write_error<=1; end
              else begin read_response<=1; read_error<=1; end
              kv_errors<=4'hf; state<=IDLE;
            end else begin
              if (!writing) window_data[512*beat_index+:512]<=mem_rsp_data;
              if (beats_left==1) begin
                if (writing) begin
                  write_response<=1; write_error<=0; state<=IDLE;
                  if (ordinal==RECORDS_PER_LAYER-1) begin
                    completions[28*slot+layer]<=1;
                    next_layer[slot]<=next_layer[slot]+6'd1;
                    next_record[slot]<=0;
                  end else next_record[slot]<=next_record[slot]+10'd1;
                end else state<=DECODE_SEND;
              end else begin
                beats_left<=beats_left-3'd1; beat_index<=beat_index+3'd1;
                beat_address<=beat_address+33'd64;
                if (writing) begin
                  window_data<=window_data >> 512;
                  window_be<=window_be >> 64;
                end
                state<=REQUEST;
              end
            end
          end
          DECODE_SEND: if (codec_ready) state<=DECODE_WAIT;
          DECODE_WAIT: if (codec_valid) begin
            read_response<=1; read_error<=codec_error || codec_length!=record_bytes;
            decoded<=codec_data;
            if (codec_error || codec_length!=record_bytes) kv_errors<=4'hf;
            state<=IDLE;
          end
          DRAIN: if (mem_rsp_valid) state<=IDLE;
          default: begin
            if (writing) begin write_response<=1; write_error<=1; end
            else begin read_response<=1; read_error<=1; end
            kv_errors<=4'hf; state<=IDLE;
          end
        endcase
      end
    end
  end endgenerate
endmodule
