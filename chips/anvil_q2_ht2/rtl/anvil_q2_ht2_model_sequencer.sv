module anvil_q2_ht2_model_sequencer #(
  parameter NUM_LAYERS=28, HIDDEN_SIZE=1536, INTERMEDIATE_SIZE=8960,
  parameter NUM_Q_HEADS=12, NUM_KV_HEADS=2, HEAD_DIM=128,
  parameter GROUP_SIZE=128, VOCAB_SIZE=151936, MAX_SEQ_LEN=32768,
  parameter CACHE_BLOCK=16,
  parameter WORDS=(CACHE_BLOCK>=1 && CACHE_BLOCK<=128) ? CACHE_BLOCK : 1
) (
  input wire clk, rst_n, annul, invalidate,
  input wire s_valid,
  output wire s_ready,
  input wire [2:0] s_count,
  input wire [2:0] s_k,
  input wire [127:0] s_ids,
  input wire [7:0] s_parent,
  input wire [31:0] s_position,
  input wire s_new_sequence,
  input wire [5:0] s_mode,
  input wire [32:0] s_kv_base, s_kv_length,
  output wire busy, idle, fault, cache_valid,
  output wire logit_valid,
  input wire logit_ready,
  output wire [1:0] logit_slot,
  output wire [31:0] logit_index, logit_fp32,
  output wire signed [31:0] logit_data,
  output wire m_valid, m_error,
  input wire m_ready,
  output wire [2:0] m_accepted,
  output wire [3:0] m_mask,
  output wire [31:0] m_next_token, m_position, committed_position,
  output wire commit_valid,
  output wire desc_req_valid,
  input wire desc_req_ready,
  output wire [8:0] desc_req_index,
  input wire desc_rsp_valid, desc_rsp_error,
  output wire desc_rsp_ready,
  input wire [511:0] desc_rsp_data,
  output wire weight_valid,
  input wire weight_ready,
  output wire [32:0] weight_address,
  output wire [6:0] weight_beats,
  input wire fill_valid, fill_error, fill_last,
  output wire fill_ready,
  input wire [511:0] fill_data,
  output wire scalar_mem_valid,
  input wire scalar_mem_ready,
  output wire [32:0] scalar_mem_address,
  input wire scalar_mem_rsp_valid, scalar_mem_rsp_error,
  output wire scalar_mem_rsp_ready,
  input wire [511:0] scalar_mem_rsp_data,
  output wire kv_mem_valid, kv_mem_write,
  input wire kv_mem_ready,
  output wire [32:0] kv_mem_address,
  output wire [511:0] kv_mem_wdata,
  output wire [63:0] kv_mem_be,
  input wire kv_mem_rsp_valid, kv_mem_rsp_error,
  output wire kv_mem_rsp_ready,
  input wire [511:0] kv_mem_rsp_data
);
  localparam SG=GROUP_SIZE>=1 ? GROUP_SIZE : 1;
  localparam CB=CACHE_BLOCK>=1 ? CACHE_BLOCK : 1;
  localparam LEGAL=NUM_LAYERS>=1 && NUM_LAYERS<=28 &&
    HIDDEN_SIZE>=8 && HIDDEN_SIZE<=1536 &&
    INTERMEDIATE_SIZE>=8 && INTERMEDIATE_SIZE<=8960 &&
    NUM_Q_HEADS>=1 && NUM_Q_HEADS<=16 &&
    NUM_KV_HEADS>=1 && NUM_KV_HEADS<=2 &&
    HEAD_DIM>=2 && HEAD_DIM<=128 && (HEAD_DIM & 1)==0 &&
    HIDDEN_SIZE==NUM_Q_HEADS*HEAD_DIM &&
    (NUM_KV_HEADS==1 || (NUM_KV_HEADS==2 && (NUM_Q_HEADS & 1)==0)) &&
    (HIDDEN_SIZE & 7)==0 && (INTERMEDIATE_SIZE & 7)==0 &&
    ((NUM_KV_HEADS*HEAD_DIM) & 7)==0 &&
    GROUP_SIZE>=1 && GROUP_SIZE<=128 && (GROUP_SIZE & (GROUP_SIZE-1))==0 &&
    (HIDDEN_SIZE & (SG-1))==0 && (INTERMEDIATE_SIZE & (SG-1))==0 &&
    CACHE_BLOCK>=1 && CACHE_BLOCK<=128 && WORDS==CACHE_BLOCK &&
    (CACHE_BLOCK & (CACHE_BLOCK-1))==0 && (HEAD_DIM & (CB-1))==0 &&
    VOCAB_SIZE>=1 && VOCAB_SIZE<=151936 &&
    MAX_SEQ_LEN>=1 && MAX_SEQ_LEN<=32768;
  generate if (!LEGAL) begin: invalid_parameters
    initial $fatal(1,"ANVIL_Q2_HT2 PARAMETER ERROR: native model geometry");
    assign s_ready=0; assign busy=0; assign idle=0; assign fault=0;
    assign cache_valid=0; assign logit_valid=0; assign logit_slot=0;
    assign logit_index=0; assign logit_fp32=0; assign logit_data=0;
    assign m_valid=0; assign m_error=0; assign m_accepted=0; assign m_mask=0;
    assign m_next_token=0; assign m_position=0; assign committed_position=0;
    assign commit_valid=0; assign desc_req_valid=0; assign desc_req_index=0;
    assign desc_rsp_ready=0; assign weight_valid=0; assign weight_address=0;
    assign weight_beats=0; assign fill_ready=0; assign scalar_mem_valid=0;
    assign scalar_mem_address=0; assign scalar_mem_rsp_ready=0;
    assign kv_mem_valid=0; assign kv_mem_write=0; assign kv_mem_address=0;
    assign kv_mem_wdata=0; assign kv_mem_be=0; assign kv_mem_rsp_ready=0;
  end else begin: implementation
    localparam MAX_WORDS=HIDDEN_SIZE>INTERMEDIATE_SIZE ? HIDDEN_SIZE : INTERMEDIATE_SIZE;
    localparam VECTOR_COUNT=10, VECTOR_TILES=(MAX_WORDS+127) >> 7;
    localparam DEPTH=VECTOR_COUNT*VECTOR_TILES;
    localparam AW=DEPTH<=1 ? 1 : $clog2(DEPTH);
    localparam BLOCKS=HEAD_DIM >> $clog2(CACHE_BLOCK);
    localparam [3:0] HIDDEN=0, NORMAL=1, QUERY=2, KEY=3, VALUE=4,
      CONTEXT=5, PROJECTED=6, GATE=7, UP=8, ACTIVATED=9;
    localparam [2:0] EMBEDDING=0, VECTOR=1, PROJECTION=2,
      ROTARY=3, CACHE_WRITE=4, ATTENTION=5, VOCABULARY=6;
    localparam [7:0] IDLE=0, VALIDATE=1, BEGIN_CACHE=2, CHECK_CACHE=3,
      SCHEDULE=4, DESCRIPTOR_SEND=5, DESCRIPTOR_WAIT=6, DISPATCH=7,
      ELEMENT_READ=8, ELEMENT_CAPTURE=9, ELEMENT_WRITE=10,
      READER_SEND=11, READER_WAIT=12, CONVERT_SEND=13, CONVERT_WAIT=14,
      EMBED_SEND=15, EMBED_SAVE=16, ELEMENT_NEXT=17, PHASE_DONE=18,
      VECTOR_SEND=19, VECTOR_RESULT=25,
      TILE_START=27, TILE_READ=28, TILE_SAVE=29,
      TILE_SEND=30, TILE_ACK=31, PROJECTION_SEND=32, PROJECTION_ROW=33,
      PROJECTION_BIAS=34,
      LOGIT_SEND=41, ROTARY_START=42, ROTARY_FIRST=43, ROTARY_EXPAND1=44,
      ROTARY_SECOND=45, ROTARY_EXPAND2=46, ROTARY_COS=47, ROTARY_SIN=48,
      ROTARY_SEND=49, ROTARY_WAIT=50, ROTARY_SAVE1=51, ROTARY_SAVE2=52,
      ROTARY_NEXT=53, CACHE_START=54, CACHE_ELEMENT=55, CACHE_EXPAND=56,
      CACHE_BF16=57, CACHE_SAVE=58, CACHE_SEND=59, CACHE_ACK=60,
      ATTENTION_START=61, ATTENTION_ELEMENT=62, ATTENTION_SAVE=63,
      ATTENTION_SEND=64, ATTENTION_WAIT=65, ATTENTION_OUTPUT=66,
      ATTENTION_NEXT=67, FINISH=68, BATCH_RESPONSE=69, FAILURE=70,
      FAILURE_DRAIN=71, ERROR_RESPONSE=72,
      PROJECTION_PIPE=73, PROJECTION_DRAIN=74,
      VECTOR_TILE_A_READ=75, VECTOR_TILE_A_SAVE=76,
      VECTOR_TILE_B_READ=77, VECTOR_TILE_B_SAVE=78,
      VECTOR_STREAM_SEND=79, VECTOR_STREAM_WAIT=80,
      COEFFICIENT_TILE_SEND=81, COEFFICIENT_TILE_WAIT=82;
    reg [7:0] state, memory_return, reader_return, convert_return;
    reg [4:0] phase, layer;
    reg [2:0] operation, count, width, vector_operation;
    reg [5:0] mode;
    reg [127:0] ids, targets, maxima;
    reg [3:0] tokens, maxima_valid;
    reg [7:0] parents;
    reg [31:0] position, origin, committed_origin, index, length;
    reg [32:0] kv_base, kv_length;
    reg new_sequence, sticky_fault, published, tensor_fault_seen;
    reg [63:0] generation, tag;
    reg [1:0] slot;
    reg [3:0] source_vector, auxiliary_vector, destination_vector, head;
    reg [31:0] source_count, destination_count;
    reg need_auxiliary, descriptor_auxiliary, bias_required;
    reg [8:0] descriptor_index, auxiliary_index;
    reg [511:0] descriptor, auxiliary_descriptor;
    reg [31:0] memory_index;
    reg [3:0] memory_vector;
    reg [1:0] memory_slot;
    reg [15:0] memory_value, memory_write_data;
    reg [3:0] memory_write_vector;
    reg [1:0] memory_write_slot;
    reg [31:0] memory_write_index;
    reg [39:0] vector_valid;
    wire [63:0] memory_data;
    wire [8191:0] tile_memory_data;
    reg [511:0] reader_descriptor;
    reg [31:0] reader_row, reader_column, read_fp32;
    reg [15:0] read_native;
    reg convert_expand, convert_half;
    reg [31:0] convert_source, converted_value;
    reg [31:0] bias;
    reg [127:0] row_sums;
    reg [31:0] row_index;
    reg row_last;
    reg [2047:0] tile;
    reg [2047:0] vector_a_tile, vector_b_tile;
    reg [127:0] tile_keep;
    reg [31:0] tile_index;
    reg [7:0] dimension;
    reg [6:0] pair_index, block_index, block_word;
    reg cache_value, cache_head;
    reg [WORDS*16-1:0] cache_data;
    reg [HEAD_DIM*16-1:0] query_data, attention_data;
    reg [63:0] rotary_source, rotary_coefficients;
    reg [31:0] rotary_data;
    wire fp16=mode[1:0]==2;
    wire child_annul=annul || state==FAILURE;
    wire enabled=rst_n && !child_annul && !invalidate;
    wire kv_rst_n=rst_n && !invalidate;
    wire [7:0] depths;
    wire [31:0] node_position=position+{30'd0,depths[2*slot+:2]};
    wire [31:0] head_base={28'd0,head}*HEAD_DIM;
    wire [31:0] pair_first=head_base+{25'd0,pair_index};
    wire [31:0] pair_second=pair_first+(HEAD_DIM >> 1);
    wire final_slot={1'b0,slot}+3'd1==count;
    wire final_element=index+32'd1==length;
    wire final_tile=(({1'b0,tile_index}+33'd1) << 7)>={1'b0,source_count};
    reg [127:0] staging_keep;
    wire final_dimension=dimension==HEAD_DIM-1;
    wire final_pair=pair_index==(HEAD_DIM >> 1)-1;
    wire final_block=block_index==BLOCKS-1;
    wire final_block_word=block_word==CACHE_BLOCK-1;
    wire [31:0] block_column=head_base+
      ({25'd0,block_index} << $clog2(CACHE_BLOCK))+{25'd0,block_word};
    wire [31:0] current_sum=row_sums[32*slot+:32];
    wire [31:0] previous_max=maxima[32*slot+:32];
    wire both_zero=current_sum[30:0]==0 && previous_max[30:0]==0;
    wire greater_sum=!both_zero && (current_sum[31]!=previous_max[31] ?
      !current_sum[31] : (current_sum[31] ?
        current_sum[30:0]<previous_max[30:0] :
        current_sum[30:0]>previous_max[30:0]));
    wire reader_ready, reader_valid, reader_error, reader_idle;
    wire [15:0] reader_native;
    wire [31:0] reader_fp32;
    wire [63:0] reader_tag;
    wire coefficient_tile_ready, coefficient_tile_valid, coefficient_tile_error;
    wire coefficient_tile_fp16, coefficient_tile_idle;
    wire [2047:0] coefficient_tile_data;
    wire [63:0] coefficient_tile_tag;
    reg vector_b_fp16;
    wire scalar_reader_mem_valid, scalar_reader_mem_ready, scalar_reader_rsp_ready;
    wire [32:0] scalar_reader_mem_address;
    wire tile_reader_mem_valid, tile_reader_mem_ready, tile_reader_rsp_ready;
    wire [32:0] tile_reader_mem_address;
    reg scalar_owner_valid, scalar_owner_tile;
    reg scalar_offer_valid, scalar_offer_tile;
    reg [32:0] scalar_offer_address;
    wire scalar_request_transfer=scalar_mem_valid && scalar_mem_ready;
    wire scalar_response_transfer=scalar_mem_rsp_valid && scalar_mem_rsp_ready;
    wire conversion_ready, conversion_valid, conversion_error;
    wire [31:0] conversion_data;
    wire [63:0] conversion_tag;
    wire vector_ready, vector_data_ready, vector_result_valid, vector_error, vector_last;
    wire [31:0] vector_index;
    wire [15:0] vector_data;
    wire [63:0] vector_tag;
    wire vector_result_fault=vector_error || vector_tag!=tag ||
      vector_index!=index || vector_last!=final_element;
    wire vector_store_write=enabled && state==VECTOR_RESULT &&
      vector_result_valid && !vector_result_fault;
    wire vector_input_ready, vector_input_valid, vector_input_error;
    wire vector_input_last, vector_input_idle;
    wire [31:0] vector_input_a, vector_input_b;
    wire [63:0] vector_input_tag;
    wire [31:0] vector_remaining=length-(tile_index << 7);
    wire [7:0] vector_tile_count=vector_remaining>=128 ?
      8'd128 : vector_remaining[7:0];
    wire vector_tile_last=(({1'b0,tile_index}+33'd1) << 7)>={1'b0,length};
    wire vector_input_fault=vector_input_valid &&
      (vector_input_error || vector_input_tag!=tag);
    wire vector_input_transfer=enabled && state==VECTOR_STREAM_WAIT &&
      vector_input_valid && vector_data_ready && !vector_input_fault;
    wire tensor_ready, tensor_write_ready, tensor_write_valid, tensor_write_error;
    wire tensor_valid, tensor_error, tensor_last, tensor_idle, tensor_fault;
    wire [31:0] tensor_row;
    wire [127:0] tensor_sums;
    wire [3:0] tensor_tokens;
    wire [63:0] tensor_tag;
    wire row_store_ready, row_store_valid, row_store_error, row_store_last, row_store_idle;
    wire [63:0] row_store_data, row_store_tag;
    wire [31:0] row_store_row;
    wire [3:0] row_store_tokens;
    reg [31:0] stored_rows;
    wire row_store_fault=row_store_valid && (row_store_error ||
      row_store_tag!=tag || row_store_tokens!=tokens || row_store_row!=stored_rows ||
      row_store_last!=(stored_rows+32'd1==destination_count));
    wire row_write=enabled && row_store_valid && !row_store_fault;
    reg projection_inflight;
    reg [2:0] projection_head, projection_tail;
    reg [3:0] projection_queued;
    reg [127:0] projection_sums [0:7];
    reg [31:0] projection_rows [0:7];
    reg [3:0] projection_tokens [0:7];
    reg [63:0] projection_tags [0:7];
    reg [7:0] projection_errors, projection_lasts;
    wire projection_pop=enabled && state==PROJECTION_ROW && projection_queued!=0;
    wire tensor_output_ready=enabled && projection_inflight &&
      (projection_queued<8 || projection_pop);
    wire projection_push=tensor_valid && tensor_output_ready;
    wire rotary_ready, rotary_valid, rotary_error;
    wire [31:0] rotary_result;
    wire [63:0] rotary_tag;
    wire attention_ready, attention_valid, attention_error;
    wire [HEAD_DIM*16-1:0] attention_result;
    wire [63:0] attention_tag;
    wire cache_begin_ready, cache_active, cache_input_error, cache_allocator_error;
    wire cache_idle, cache_write_ready, cache_write_valid, cache_write_error;
    wire cache_read_valid, cache_read_ready, cache_read_value, cache_read_head;
    wire [1:0] cache_read_slot;
    wire [31:0] cache_read_position;
    wire [4:0] cache_read_layer;
    wire [6:0] cache_read_block;
    wire cache_read_rsp_valid, cache_read_rsp_error, cache_read_rsp_ready;
    wire [WORDS*16-1:0] cache_read_data;
    wire cache_finish_ready, cache_response_valid, cache_response_error;
    wire [2:0] cache_accepted;
    wire [3:0] cache_mask;
    wire [31:0] cache_next, cache_position;
    wire all_idle=reader_idle && tensor_idle && cache_idle && !cache_active &&
      row_store_idle && vector_input_idle && coefficient_tile_idle &&
      !scalar_owner_valid && !scalar_offer_valid;
    wire memory_read=enabled && state==ELEMENT_READ;
    wire memory_write=enabled && state==ELEMENT_WRITE;
    wire memory_read_bad=memory_index>=MAX_WORDS || memory_vector>=VECTOR_COUNT ||
      !vector_valid[10*memory_slot+memory_vector];
    wire tile_read=enabled && (state==TILE_READ ||
      state==VECTOR_TILE_A_READ || state==VECTOR_TILE_B_READ);
    wire [3:0] tile_read_vector=state==VECTOR_TILE_B_READ ? auxiliary_vector : source_vector;
    wire tile_read_bad=tile_read_vector>=VECTOR_COUNT || tile_index>=VECTOR_TILES ||
      !vector_valid[10*slot+tile_read_vector];
    genvar bank, word_lane;
    integer staging_lane, staging_write_lane;

    always @* begin
      staging_keep=0;
      for (staging_lane=0;staging_lane<128;staging_lane=staging_lane+1)
        staging_keep[staging_lane]=
          ({1'b0,tile_index,7'd0}+40'(staging_lane))<{8'd0,source_count};
    end

    function automatic [31:0] legacy_fixed(input [31:0] value);
      reg [55:0] magnitude;
      reg [8:0] distance;
      begin
        magnitude={32'd0,(|value[30:23]),value[22:0]};
        distance=0;
        if (value[30:23]>=134) begin
          distance={1'b0,value[30:23]}-9'd134;
          if (distance>31) magnitude=56'hffffffffffffff;
          else magnitude=magnitude << distance;
        end else begin
          distance=9'd134-{1'b0,value[30:23]};
          if (distance>=56) magnitude=0;
          else magnitude=magnitude >> distance;
        end
        if (value[31]) begin
          if (magnitude>=56'h00000080000000) legacy_fixed=32'h80000000;
          else legacy_fixed=~magnitude[31:0]+32'd1;
        end else begin
          if (magnitude>56'h0000007fffffff) legacy_fixed=32'h7fffffff;
          else legacy_fixed=magnitude[31:0];
        end
      end
    endfunction

    for (bank=0;bank<4;bank=bank+1) begin: token_storage
      wire [2047:0] read_data;
      wire [31:0] read_address=tile_read ?
        tile_read_vector*VECTOR_TILES+tile_index :
        memory_vector*VECTOR_TILES+(memory_index >> 7);
      wire [31:0] write_address=memory_write_vector*VECTOR_TILES+(memory_write_index >> 7);
      assign memory_data[16*bank+:16]=read_data[16*memory_index[6:0]+:16];
      assign tile_memory_data[2048*bank+:2048]=read_data;
      for (word_lane=0;word_lane<128;word_lane=word_lane+1) begin: column_bank
        (* ramstyle="M20K", nomem2reg *) reg [15:0] words [0:DEPTH-1];
        reg [15:0] data_q;
        assign read_data[16*word_lane+:16]=data_q;
        always @(posedge clk) begin
          if (row_write && row_store_tokens[bank] && row_store_row[6:0]==word_lane)
            words[AW'(destination_vector*VECTOR_TILES+(row_store_row >> 7))]<=
              row_store_data[16*bank+:16];
          else if (vector_store_write && slot==bank && index[6:0]==word_lane)
            words[AW'(destination_vector*VECTOR_TILES+(index >> 7))]<=vector_data;
          else if (memory_write && memory_write_slot==bank &&
              memory_write_index[6:0]==word_lane &&
              memory_write_index<MAX_WORDS && memory_write_vector<VECTOR_COUNT)
            words[AW'(write_address)]<=memory_write_data;
          if ((tile_read && slot==bank && !tile_read_bad) ||
              (memory_read && memory_slot==bank && !memory_read_bad &&
                memory_index[6:0]==word_lane))
            data_q<=words[AW'(read_address)];
        end

      end
    end

    anvil_q2_ht2_projection_store_pipe projection_storage (
      .clk(clk),.rst_n(rst_n),.annul(child_annul || invalidate),
      .s_valid(enabled && state==PROJECTION_PIPE),.s_ready(row_store_ready),
      .s_fp16(fp16),.s_bias_valid(bias_required),.s_last(row_last),
      .s_sum(row_sums),.s_bias(bias),.s_row(row_index),.s_token_mask(tokens),.s_tag(tag),
      .m_valid(row_store_valid),.m_ready(enabled),.m_error(row_store_error),
      .m_last(row_store_last),.m_data(row_store_data),.m_tag(row_store_tag),
      .m_row(row_store_row),.m_token_mask(row_store_tokens),.idle(row_store_idle)
    );
    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) stored_rows<=0;
      else if (child_annul || invalidate) stored_rows<=0;
      else if (enabled && state==PROJECTION_SEND && tensor_ready) stored_rows<=0;
      else if (row_write) stored_rows<=stored_rows+32'd1;
    end

    anvil_q2_ht2_scalar_reader coefficients (
      .clk(clk),.rst_n(rst_n),.annul(child_annul || invalidate),
      .s_valid(enabled && state==READER_SEND),.s_ready(reader_ready),
      .s_descriptor(reader_descriptor),.s_row(reader_row),
      .s_column(reader_column),.s_tag(tag),
      .m_valid(reader_valid),.m_ready(enabled && state==READER_WAIT),
      .m_error(reader_error),.m_fp16(),.m_native(reader_native),
      .m_fp32(reader_fp32),.m_tag(reader_tag),.idle(reader_idle),
      .mem_valid(scalar_reader_mem_valid),.mem_ready(scalar_reader_mem_ready),
      .mem_address(scalar_reader_mem_address),
      .mem_rsp_valid(scalar_mem_rsp_valid && scalar_owner_valid && !scalar_owner_tile),
      .mem_rsp_error(scalar_mem_rsp_error),
      .mem_rsp_ready(scalar_reader_rsp_ready),.mem_rsp_data(scalar_mem_rsp_data)
    );
    anvil_q2_ht2_native_tile_reader coefficient_tiles (
      .clk(clk),.rst_n(rst_n),.annul(child_annul || invalidate),
      .s_valid(enabled && state==COEFFICIENT_TILE_SEND),.s_ready(coefficient_tile_ready),
      .s_descriptor(descriptor),.s_row(32'd0),.s_column(tile_index << 7),
      .s_count(vector_tile_count),.s_tag(tag),
      .m_valid(coefficient_tile_valid),.m_ready(enabled && state==COEFFICIENT_TILE_WAIT),
      .m_error(coefficient_tile_error),.m_fp16(coefficient_tile_fp16),
      .m_data(coefficient_tile_data),.m_tag(coefficient_tile_tag),
      .idle(coefficient_tile_idle),
      .mem_valid(tile_reader_mem_valid),.mem_ready(tile_reader_mem_ready),
      .mem_address(tile_reader_mem_address),
      .mem_rsp_valid(scalar_mem_rsp_valid && scalar_owner_valid && scalar_owner_tile),
      .mem_rsp_error(scalar_mem_rsp_error),.mem_rsp_ready(tile_reader_rsp_ready),
      .mem_rsp_data(scalar_mem_rsp_data)
    );
    assign scalar_mem_valid=rst_n && !child_annul && !invalidate && scalar_offer_valid;
    assign scalar_mem_address=scalar_mem_valid ? scalar_offer_address : 33'd0;
    assign scalar_reader_mem_ready=scalar_request_transfer && !scalar_offer_tile;
    assign tile_reader_mem_ready=scalar_request_transfer && scalar_offer_tile;
    assign scalar_mem_rsp_ready=rst_n && scalar_owner_valid &&
      (scalar_owner_tile ? tile_reader_rsp_ready : scalar_reader_rsp_ready);
    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        scalar_owner_valid<=0; scalar_owner_tile<=0;
        scalar_offer_valid<=0; scalar_offer_tile<=0; scalar_offer_address<=0;
      end else begin
        if (scalar_response_transfer) scalar_owner_valid<=0;
        if (scalar_request_transfer) begin
          scalar_offer_valid<=0; scalar_owner_valid<=1;
          scalar_owner_tile<=scalar_offer_tile;
        end
        if (child_annul || invalidate) scalar_offer_valid<=0;
        else if (!scalar_owner_valid && !scalar_offer_valid &&
            (scalar_reader_mem_valid || tile_reader_mem_valid)) begin
          scalar_offer_valid<=1; scalar_offer_tile<=tile_reader_mem_valid;
          scalar_offer_address<=tile_reader_mem_valid ?
            tile_reader_mem_address : scalar_reader_mem_address;
        end
      end
    end
    anvil_q2_ht2_convert_pipe conversion (
      .clk(clk),.rst_n(rst_n),.annul(child_annul),
      .s_valid(enabled && state==CONVERT_SEND),.s_ready(conversion_ready),
      .s_to_fp32(convert_expand),.s_fp16(convert_half),
      .s_data(convert_source),.s_tag(tag),
      .m_valid(conversion_valid),.m_ready(enabled && state==CONVERT_WAIT),
      .m_error(conversion_error),.m_data(conversion_data),.m_tag(conversion_tag)
    );
    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) tensor_fault_seen<=0;
      else if (tensor_fault) tensor_fault_seen<=1;
    end
    integer projection_entry;
    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        projection_inflight<=0; projection_head<=0; projection_tail<=0;
        projection_queued<=0; projection_errors<=0; projection_lasts<=0;
        for (projection_entry=0;projection_entry<8;projection_entry=projection_entry+1) begin
          projection_sums[projection_entry]<=0; projection_rows[projection_entry]<=0;
          projection_tokens[projection_entry]<=0; projection_tags[projection_entry]<=0;
        end
      end else if (child_annul || invalidate) begin
        projection_inflight<=0; projection_head<=0; projection_tail<=0;
        projection_queued<=0; projection_errors<=0; projection_lasts<=0;
      end else begin
        if (enabled && state==PROJECTION_SEND && tensor_ready)
          projection_inflight<=1;
        if (projection_push) begin
          projection_sums[projection_tail]<=tensor_sums;
          projection_rows[projection_tail]<=tensor_row;
          projection_tokens[projection_tail]<=tensor_tokens;
          projection_tags[projection_tail]<=tensor_tag;
          projection_errors[projection_tail]<=tensor_error;
          projection_lasts[projection_tail]<=tensor_last;
          projection_tail<=projection_tail+3'd1;
          if (tensor_last) projection_inflight<=0;
        end
        if (projection_pop) projection_head<=projection_head+3'd1;
        case ({projection_push,projection_pop})
          2'b10: projection_queued<=projection_queued+4'd1;
          2'b01: projection_queued<=projection_queued-4'd1;
          default: begin end
        endcase
      end
    end
    anvil_q2_ht2_vector_input_pipe vector_input (
      .clk(clk),.rst_n(rst_n),.annul(child_annul || invalidate),
      .s_valid(enabled && state==VECTOR_STREAM_SEND),.s_ready(vector_input_ready),
      .s_count(vector_tile_count),.s_fp16(fp16),.s_b_fp16(vector_b_fp16),
      .s_a(vector_a_tile),.s_b(vector_b_tile),.s_tag(tag),
      .m_valid(vector_input_valid),
      .m_ready(enabled && state==VECTOR_STREAM_WAIT && vector_data_ready),
      .m_error(vector_input_error),.m_last(vector_input_last),
      .m_a(vector_input_a),.m_b(vector_input_b),.m_tag(vector_input_tag),
      .idle(vector_input_idle)
    );
    anvil_q2_ht2_vector_unit #(.MAX_WORDS(MAX_WORDS)) vector_execution (
      .clk(clk),.rst_n(rst_n),.annul(child_annul),
      .s_valid(enabled && state==VECTOR_SEND),.s_ready(vector_ready),
      .s_operation(vector_operation),.s_count(length),.s_fp16(fp16),.s_tag(tag),
      .d_valid(enabled && state==VECTOR_STREAM_WAIT &&
        vector_input_valid && !vector_input_fault),
      .d_ready(vector_data_ready),
      .d_last(vector_tile_last && vector_input_last),
      .d_data(vector_input_a),.d_aux(vector_input_b),
      .m_valid(vector_result_valid),.m_ready(enabled && state==VECTOR_RESULT),
      .m_error(vector_error),.m_last(vector_last),.m_index(vector_index),
      .m_fp32(),.m_data(vector_data),.m_tag(vector_tag)
    );
    anvil_q2_ht2_tensor_engine #(
      .MAX_WORDS(MAX_WORDS),.VECTOR_COUNT(1),.GROUP_SIZE(GROUP_SIZE)
    ) tensor_execution (
      .clk(clk),.rst_n(rst_n),.annul(child_annul || invalidate),
      .s_valid(enabled && state==PROJECTION_SEND),.s_ready(tensor_ready),
      .s_descriptor(descriptor),.s_vector(32'd0),.s_first_row(32'd0),
      .s_row_count(destination_count),.s_token_mask(tokens),.s_fp16(fp16),
      .s_sparse(mode[4]),.s_weight_mode(mode[3:2]),.s_tag(tag),
      .w_valid(enabled && state==TILE_SEND),.w_ready(tensor_write_ready),
      .w_slot(slot),.w_vector(32'd0),.w_tile(tile_index),
      .w_data(tile),.w_keep(tile_keep),.w_rsp_valid(tensor_write_valid),
      .w_rsp_error(tensor_write_error),.w_rsp_ready(enabled && state==TILE_ACK),
      .r_valid(1'b0),.r_ready(),.r_vector(32'd0),.r_tile(32'd0),
      .r_token_mask(4'd0),.r_keep(512'd0),.r_tag(64'd0),
      .r_rsp_valid(),.r_rsp_error(),.r_rsp_ready(1'b0),
      .r_data(),.r_rsp_keep(),.r_rsp_tag(),
      .m_valid(tensor_valid),.m_ready(tensor_output_ready),
      .m_error(tensor_error),.m_last(tensor_last),.m_row(tensor_row),
      .m_token_mask(tensor_tokens),.m_sum(tensor_sums),.m_tag(tensor_tag),
      .idle(tensor_idle),.fault(tensor_fault),
      .mem_valid(weight_valid),.mem_ready(weight_ready),
      .mem_address(weight_address),.mem_beats(weight_beats),
      .fill_valid(fill_valid),.fill_error(fill_error),.fill_last(fill_last),
      .fill_ready(fill_ready),.fill_data(fill_data)
    );
    anvil_q2_ht2_rope_pair rotary (
      .clk(clk),.rst_n(rst_n),.annul(child_annul),
      .s_valid(enabled && state==ROTARY_SEND),.s_ready(rotary_ready),
      .s_fp16(fp16),.s_data(rotary_source),.s_coefficients(rotary_coefficients),
      .s_tag(tag),.m_valid(rotary_valid),.m_ready(enabled && state==ROTARY_WAIT),
      .m_error(rotary_error),.m_data(rotary_result),.m_fp32(),.m_tag(rotary_tag)
    );
    anvil_q2_ht2_attention #(
      .NUM_LAYERS(NUM_LAYERS),.NUM_Q_HEADS(NUM_Q_HEADS),
      .NUM_KV_HEADS(NUM_KV_HEADS),.HEAD_DIM(HEAD_DIM),
      .CACHE_BLOCK(CACHE_BLOCK),.MAX_SEQ_LEN(MAX_SEQ_LEN)
    ) attention (
      .clk(clk),.rst_n(rst_n),.annul(child_annul),.kv_idle(cache_idle),
      .s_valid(enabled && state==ATTENTION_SEND),.s_ready(attention_ready),
      .s_slot(slot),.s_layer(layer),.s_head(head),.s_origin(origin),
      .s_position(node_position),.s_fp16(fp16),.s_query(query_data),.s_tag(tag),
      .m_valid(attention_valid),.m_ready(enabled && state==ATTENTION_WAIT),
      .m_error(attention_error),.m_data(attention_result),.m_tag(attention_tag),
      .r_valid(cache_read_valid),.r_ready(cache_read_ready),
      .r_slot(cache_read_slot),.r_position(cache_read_position),
      .r_layer(cache_read_layer),.r_value(cache_read_value),
      .r_head(cache_read_head),.r_block(cache_read_block),
      .r_rsp_valid(cache_read_rsp_valid),.r_rsp_error(cache_read_rsp_error),
      .r_rsp_ready(cache_read_rsp_ready),.r_data(cache_read_data)
    );
    anvil_q2_ht2_native_kv_store #(
      .NUM_LAYERS(NUM_LAYERS),.NUM_KV_HEADS(NUM_KV_HEADS),
      .HEAD_DIM(HEAD_DIM),.CACHE_BLOCK(CACHE_BLOCK),
      .MAX_SEQ_LEN(MAX_SEQ_LEN),.VOCAB_SIZE(VOCAB_SIZE)
    ) transactional_cache (
      .clk(clk),.rst_n(kv_rst_n),.annul(child_annul),
      .s_begin_valid(enabled && state==BEGIN_CACHE),.s_begin_ready(cache_begin_ready),
      .s_count(count),.s_ids(ids),.s_parent(parents),.s_position(position),
      .s_new_sequence(new_sequence),.s_int8(mode[5]),.s_base(kv_base),
      .s_length(kv_length),.active(cache_active),.input_error(cache_input_error),
      .allocator_error(cache_allocator_error),.memory_idle(cache_idle),.node_depth(depths),
      .w_valid(enabled && state==CACHE_SEND),.w_ready(cache_write_ready),
      .w_slot(slot),.w_layer(layer),.w_value(cache_value),.w_head(cache_head),
      .w_block(block_index),.w_data(cache_data),
      .w_rsp_valid(cache_write_valid),.w_rsp_error(cache_write_error),
      .w_rsp_ready(enabled && state==CACHE_ACK),
      .r_valid(cache_read_valid),.r_ready(cache_read_ready),
      .r_slot(cache_read_slot),.r_position(cache_read_position),
      .r_layer(cache_read_layer),.r_value(cache_read_value),
      .r_head(cache_read_head),.r_block(cache_read_block),
      .r_rsp_valid(cache_read_rsp_valid),.r_rsp_error(cache_read_rsp_error),
      .r_rsp_ready(cache_read_rsp_ready),.r_data(cache_read_data),
      .s_finish_valid(enabled && state==FINISH),.s_finish_ready(cache_finish_ready),
      .s_target_ids(targets),.m_valid(cache_response_valid),.m_error(cache_response_error),
      .m_ready(enabled && state==BATCH_RESPONSE && m_ready),
      .m_accepted(cache_accepted),.m_mask(cache_mask),.m_next_token(cache_next),
      .m_position(cache_position),.committed_position(committed_position),
      .commit_valid(commit_valid),
      .mem_valid(kv_mem_valid),.mem_ready(kv_mem_ready),.mem_write(kv_mem_write),
      .mem_address(kv_mem_address),.mem_wdata(kv_mem_wdata),.mem_be(kv_mem_be),
      .mem_rsp_valid(kv_mem_rsp_valid),.mem_rsp_error(kv_mem_rsp_error),
      .mem_rsp_ready(kv_mem_rsp_ready),.mem_rsp_data(kv_mem_rsp_data)
    );

    assign s_ready=enabled && state==IDLE && all_idle && cache_begin_ready;
    assign busy=rst_n && state!=IDLE;
    assign idle=enabled && state==IDLE && all_idle;
    assign fault=rst_n && (sticky_fault || cache_allocator_error);
    assign cache_valid=rst_n && published;
    assign desc_req_valid=enabled && state==DESCRIPTOR_SEND;
    assign desc_req_index=desc_req_valid ?
      (descriptor_auxiliary ? auxiliary_index : descriptor_index) : 9'd0;
    assign desc_rsp_ready=rst_n &&
      ((enabled && state==DESCRIPTOR_WAIT) || state==FAILURE_DRAIN);
    assign logit_valid=enabled && state==LOGIT_SEND;
    assign logit_slot=logit_valid ? slot : 2'd0;
    assign logit_index=logit_valid ? row_index : 32'd0;
    assign logit_fp32=logit_valid ? current_sum : 32'd0;
    wire [31:0] legacy_logit=legacy_fixed(current_sum);
    assign logit_data=logit_valid ? $signed(legacy_logit) : 32'sd0;
    assign m_valid=enabled && ((state==BATCH_RESPONSE && cache_response_valid) ||
      state==ERROR_RESPONSE);
    assign m_error=m_valid && (state==ERROR_RESPONSE || cache_response_error);
    assign m_accepted=m_valid && !m_error ? cache_accepted : 3'd0;
    assign m_mask=m_valid && !m_error ? cache_mask : 4'd0;
    assign m_next_token=m_valid && !m_error ? cache_next : 32'd0;
    assign m_position=m_valid ? (m_error ? committed_position : cache_position) : 32'd0;

    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        state<=IDLE; memory_return<=0; reader_return<=0; convert_return<=0;
        phase<=0; layer<=0; operation<=0; count<=0; width<=0;
        vector_operation<=0; mode<=0; ids<=0; targets<=0; maxima<=0;
        tokens<=0; maxima_valid<=0; parents<=0; position<=0; origin<=0;
        committed_origin<=0; index<=0; length<=0; kv_base<=0; kv_length<=0;
        new_sequence<=0; sticky_fault<=0; published<=0; generation<=0; tag<=0;
        slot<=0; source_vector<=0; auxiliary_vector<=0; destination_vector<=0;
        head<=0; source_count<=0; destination_count<=0; need_auxiliary<=0;
        descriptor_auxiliary<=0; bias_required<=0; descriptor_index<=0;
        auxiliary_index<=0; descriptor<=0; auxiliary_descriptor<=0;
        memory_index<=0; memory_vector<=0; memory_slot<=0; memory_value<=0;
        memory_write_data<=0; memory_write_vector<=0; memory_write_slot<=0;
        memory_write_index<=0; vector_valid<=0; reader_descriptor<=0;
        reader_row<=0; reader_column<=0; read_fp32<=0; read_native<=0;
        convert_expand<=0; convert_half<=0; convert_source<=0; converted_value<=0;
        bias<=0; row_sums<=0;
        row_index<=0; row_last<=0; tile<=0; vector_a_tile<=0; vector_b_tile<=0;
        vector_b_fp16<=0;
        tile_keep<=0; tile_index<=0; dimension<=0;
        pair_index<=0; block_index<=0; block_word<=0; cache_value<=0;
        cache_head<=0; cache_data<=0; query_data<=0; attention_data<=0;
        rotary_source<=0; rotary_coefficients<=0; rotary_data<=0;
      end else if (annul || invalidate) begin
        state<=IDLE; vector_valid<=0; maxima_valid<=0;
        if (invalidate) begin published<=0; committed_origin<=0; sticky_fault<=0; end
      end else if (tensor_fault && !tensor_fault_seen && state!=IDLE && state!=FAILURE &&
          state!=FAILURE_DRAIN && state!=ERROR_RESPONSE) begin
        state<=FAILURE;
      end else if (enabled && row_store_fault) begin
        state<=FAILURE;
      end else if (enabled && vector_input_fault) begin
        state<=FAILURE;
      end else case (state)
        IDLE: if (s_valid && s_ready) begin
          count<=s_count; width<=s_k; ids<=s_ids; parents<=s_parent; position<=s_position;
          new_sequence<=s_new_sequence; mode<=s_mode;
          kv_base<=s_kv_base; kv_length<=s_kv_length;
          origin<=s_new_sequence ? s_position : committed_origin;
          tokens<=s_count==4 ? 4'b1111 : (s_count==2 ? 4'b0011 : 4'b0001);
          generation<=generation+64'd1; tag<=generation+64'd1;
          vector_valid<=0; maxima_valid<=0; targets<=0; maxima<=0;
          layer<=0; phase<=0; slot<=0; index<=0; state<=VALIDATE;
        end
        VALIDATE: begin
          if ((count!=1 && count!=2 && count!=4) ||
              (width!=1 && width!=2 && width!=4) || count>width ||
              (mode[1:0]!=1 && mode[1:0]!=2) || mode[3:2]==3 ||
              position>=MAX_SEQ_LEN || (!new_sequence && !published && position!=0))
            state<=FAILURE;
          else state<=BEGIN_CACHE;
        end
        BEGIN_CACHE: if (cache_begin_ready) state<=CHECK_CACHE;
        CHECK_CACHE: begin
          if (cache_input_error || cache_allocator_error) state<=FAILURE;
          else state<=SCHEDULE;
        end
        SCHEDULE: begin
          slot<=0; index<=0; head<=0; pair_index<=0;
          dimension<=0; block_index<=0; block_word<=0;
          source_count<=HIDDEN_SIZE; destination_count<=HIDDEN_SIZE;
          length<=HIDDEN_SIZE; need_auxiliary<=0; bias_required<=0;
          descriptor_auxiliary<=0; auxiliary_descriptor<=0;
          operation<=PROJECTION; source_vector<=NORMAL;
          destination_vector<=PROJECTED; descriptor_index<=9'(16+16*layer);
          state<=DESCRIPTOR_SEND;
          case (phase)
            0: begin operation<=EMBEDDING; descriptor_index<=0; destination_vector<=HIDDEN; end
            1: begin
              operation<=VECTOR; vector_operation<=0; source_vector<=HIDDEN;
              destination_vector<=NORMAL; descriptor_index<=9'(16+16*layer+7);
            end
            2,3,4: begin
              descriptor_index<=9'(16+16*layer+phase-2);
              auxiliary_index<=9'(16+16*layer+phase+7);
              need_auxiliary<=1; bias_required<=1;
              if (phase==2) destination_vector<=QUERY;
              else begin
                destination_count<=NUM_KV_HEADS*HEAD_DIM;
                if (phase==3) destination_vector<=KEY;
                else destination_vector<=VALUE;
              end
            end
            5,6: begin
              operation<=ROTARY; descriptor_index<=3;
              if (phase==5) begin source_vector<=QUERY; length<=NUM_Q_HEADS; end
              else begin source_vector<=KEY; length<=NUM_KV_HEADS; end
            end
            7: begin
              operation<=CACHE_WRITE; state<=DISPATCH;
              cache_value<=0; cache_head<=0; head<=0;
            end
            8: begin operation<=ATTENTION; state<=DISPATCH; end
            9: begin source_vector<=CONTEXT; descriptor_index<=9'(16+16*layer+3); end
            10: begin
              operation<=VECTOR; vector_operation<=1; source_vector<=HIDDEN;
              auxiliary_vector<=PROJECTED; destination_vector<=HIDDEN; state<=DISPATCH;
            end
            11: begin
              operation<=VECTOR; vector_operation<=0; source_vector<=HIDDEN;
              destination_vector<=NORMAL; descriptor_index<=9'(16+16*layer+8);
            end
            12,13: begin
              descriptor_index<=9'(16+16*layer+phase-8);
              destination_count<=INTERMEDIATE_SIZE;
              if (phase==12) destination_vector<=GATE;
              else destination_vector<=UP;
            end
            14: begin
              operation<=VECTOR; vector_operation<=2; source_vector<=GATE;
              auxiliary_vector<=UP; destination_vector<=ACTIVATED;
              length<=INTERMEDIATE_SIZE; state<=DISPATCH;
            end
            15: begin
              source_vector<=ACTIVATED; source_count<=INTERMEDIATE_SIZE;
              descriptor_index<=9'(16+16*layer+6);
            end
            16: begin
              operation<=VECTOR; vector_operation<=1; source_vector<=HIDDEN;
              auxiliary_vector<=PROJECTED; destination_vector<=HIDDEN; state<=DISPATCH;
            end
            17: begin
              if (layer==NUM_LAYERS-1) begin phase<=18; state<=SCHEDULE; end
              else begin layer<=layer+5'd1; phase<=1; state<=SCHEDULE; end
            end
            18: begin
              operation<=VECTOR; vector_operation<=0; source_vector<=HIDDEN;
              destination_vector<=NORMAL; descriptor_index<=2;
            end
            19: begin
              operation<=VOCABULARY; descriptor_index<=1;
              destination_count<=VOCAB_SIZE; maxima_valid<=0;
            end
            20: state<=FINISH;
            default: state<=FAILURE;
          endcase
        end
        DESCRIPTOR_SEND: if (desc_req_ready) state<=DESCRIPTOR_WAIT;
        DESCRIPTOR_WAIT: if (desc_rsp_valid) begin
          if (desc_rsp_error) state<=FAILURE;
          else if (descriptor_auxiliary) begin
            auxiliary_descriptor<=desc_rsp_data; state<=DISPATCH;
          end else begin
            descriptor<=desc_rsp_data;
            if (need_auxiliary) begin descriptor_auxiliary<=1; state<=DESCRIPTOR_SEND; end
            else state<=DISPATCH;
          end
        end
        DISPATCH: begin
          case (operation)
            EMBEDDING: state<=EMBED_SEND;
            VECTOR: state<=VECTOR_SEND;
            PROJECTION,VOCABULARY: begin tile_index<=0; state<=TILE_START; end
            ROTARY: state<=ROTARY_START;
            CACHE_WRITE: state<=CACHE_START;
            ATTENTION: state<=ATTENTION_START;
            default: state<=FAILURE;
          endcase
        end
        ELEMENT_READ: begin
          if (memory_read_bad) state<=FAILURE;
          else state<=ELEMENT_CAPTURE;
        end
        ELEMENT_CAPTURE: begin
          memory_value<=memory_data[16*memory_slot+:16]; state<=memory_return;
        end
        ELEMENT_WRITE: begin
          if (memory_write_index>=MAX_WORDS || memory_write_vector>=VECTOR_COUNT)
            state<=FAILURE;
          else state<=memory_return;
        end
        READER_SEND: if (reader_ready) state<=READER_WAIT;
        READER_WAIT: if (reader_valid) begin
          if (reader_error || reader_tag!=tag) state<=FAILURE;
          else begin read_fp32<=reader_fp32; read_native<=reader_native; state<=reader_return; end
        end
        CONVERT_SEND: if (conversion_ready) state<=CONVERT_WAIT;
        CONVERT_WAIT: if (conversion_valid) begin
          if (conversion_error || conversion_tag!=tag) state<=FAILURE;
          else begin converted_value<=conversion_data; state<=convert_return; end
        end
        EMBED_SEND: begin
          reader_descriptor<=descriptor; reader_row<=ids[32*slot+:32];
          reader_column<=index; reader_return<=EMBED_SAVE; state<=READER_SEND;
        end
        EMBED_SAVE: begin
          memory_write_slot<=slot; memory_write_vector<=HIDDEN;
          memory_write_index<=index; memory_write_data<=read_native;
          memory_return<=ELEMENT_NEXT; state<=ELEMENT_WRITE;
        end
        ELEMENT_NEXT: begin
          if (final_element) begin
            vector_valid[10*slot+destination_vector]<=1; index<=0;
            if (final_slot) state<=PHASE_DONE;
            else begin
              slot<=slot+2'd1;
              if (operation==EMBEDDING) state<=EMBED_SEND;
              else state<=VECTOR_SEND;
            end
          end else begin index<=index+32'd1; state<=EMBED_SEND; end
        end
        PHASE_DONE: begin phase<=phase+5'd1; state<=SCHEDULE; end
        VECTOR_SEND: if (vector_ready) begin
          index<=0; tile_index<=0;
          state<=VECTOR_TILE_A_READ;
        end
        VECTOR_TILE_A_READ: begin
          if (tile_read_bad) state<=FAILURE;
          else state<=VECTOR_TILE_A_SAVE;
        end
        VECTOR_TILE_A_SAVE: begin
          vector_a_tile<=tile_memory_data[2048*slot+:2048];
          if (vector_operation==0) state<=COEFFICIENT_TILE_SEND;
          else state<=VECTOR_TILE_B_READ;
        end
        VECTOR_TILE_B_READ: begin
          if (tile_read_bad) state<=FAILURE;
          else state<=VECTOR_TILE_B_SAVE;
        end
        VECTOR_TILE_B_SAVE: begin
          vector_b_tile<=tile_memory_data[2048*slot+:2048];
          vector_b_fp16<=fp16;
          state<=VECTOR_STREAM_SEND;
        end
        COEFFICIENT_TILE_SEND: if (coefficient_tile_ready) state<=COEFFICIENT_TILE_WAIT;
        COEFFICIENT_TILE_WAIT: if (coefficient_tile_valid) begin
          if (coefficient_tile_error || coefficient_tile_tag!=tag) state<=FAILURE;
          else begin
            vector_b_tile<=coefficient_tile_data; vector_b_fp16<=coefficient_tile_fp16;
            state<=VECTOR_STREAM_SEND;
          end
        end
        VECTOR_STREAM_SEND: if (vector_input_ready) state<=VECTOR_STREAM_WAIT;
        VECTOR_STREAM_WAIT: if (vector_input_transfer && vector_input_last) begin
          if (vector_tile_last) begin index<=0; state<=VECTOR_RESULT; end
          else begin tile_index<=tile_index+32'd1; state<=VECTOR_TILE_A_READ; end
        end
        VECTOR_RESULT: if (vector_result_valid) begin
          if (vector_result_fault) state<=FAILURE;
          else begin
            if (final_element) state<=ELEMENT_NEXT;
            else index<=index+32'd1;
          end
        end
        TILE_START: state<=TILE_READ;
        TILE_READ: begin
          if (tile_read_bad) state<=FAILURE;
          else state<=TILE_SAVE;
        end
        TILE_SAVE: begin
          for (staging_write_lane=0;staging_write_lane<128;staging_write_lane=staging_write_lane+1)
            tile[16*staging_write_lane+:16]<=staging_keep[staging_write_lane] ?
              tile_memory_data[2048*slot+16*staging_write_lane+:16] : 16'd0;
          tile_keep<=staging_keep; state<=TILE_SEND;
        end
        TILE_SEND: if (tensor_write_ready) state<=TILE_ACK;
        TILE_ACK: if (tensor_write_valid) begin
          if (tensor_write_error) state<=FAILURE;
          else if (!final_tile) begin tile_index<=tile_index+32'd1; state<=TILE_START; end
          else if (!final_slot) begin slot<=slot+2'd1; tile_index<=0; state<=TILE_START; end
          else begin slot<=0; row_index<=0; state<=PROJECTION_SEND; end
        end
        PROJECTION_SEND: if (tensor_ready) state<=PROJECTION_ROW;
        PROJECTION_ROW: if (projection_queued!=0) begin
          if (projection_errors[projection_head] || projection_tags[projection_head]!=tag ||
              projection_tokens[projection_head]!=tokens ||
              projection_rows[projection_head]!=row_index ||
              projection_lasts[projection_head]!=(row_index+32'd1==destination_count))
            state<=FAILURE;
          else begin
            row_sums<=projection_sums[projection_head];
            row_last<=projection_lasts[projection_head]; slot<=0;
            if (bias_required) begin
              reader_descriptor<=auxiliary_descriptor; reader_row<=0;
              reader_column<=row_index; reader_return<=PROJECTION_BIAS; state<=READER_SEND;
            end else if (operation==VOCABULARY) state<=LOGIT_SEND;
            else state<=PROJECTION_PIPE;
          end
        end
        PROJECTION_BIAS: begin bias<=read_fp32; state<=PROJECTION_PIPE; end
        PROJECTION_PIPE: if (row_store_ready) begin
          if (row_last) state<=PROJECTION_DRAIN;
          else begin row_index<=row_index+32'd1; state<=PROJECTION_ROW; end
        end
        PROJECTION_DRAIN: if (row_write && row_store_last) begin
          for (staging_write_lane=0;staging_write_lane<4;staging_write_lane=staging_write_lane+1)
            if (tokens[staging_write_lane])
              vector_valid[10*staging_write_lane+destination_vector]<=1;
          state<=PHASE_DONE;
        end
        LOGIT_SEND: if (logit_ready) begin
          if (!maxima_valid[slot] || greater_sum) begin
            maxima[32*slot+:32]<=current_sum; targets[32*slot+:32]<=row_index;
            maxima_valid[slot]<=1;
          end
          if (!final_slot) slot<=slot+2'd1;
          else if (row_last) state<=PHASE_DONE;
          else begin row_index<=row_index+32'd1; state<=PROJECTION_ROW; end
        end
        ROTARY_START: begin
          memory_slot<=slot; memory_vector<=source_vector; memory_index<=pair_first;
          memory_return<=ROTARY_FIRST; state<=ELEMENT_READ;
        end
        ROTARY_FIRST: begin
          convert_expand<=1; convert_half<=fp16; convert_source<={16'd0,memory_value};
          convert_return<=ROTARY_EXPAND1; state<=CONVERT_SEND;
        end
        ROTARY_EXPAND1: begin
          rotary_source[31:0]<=converted_value;
          memory_slot<=slot; memory_vector<=source_vector; memory_index<=pair_second;
          memory_return<=ROTARY_SECOND; state<=ELEMENT_READ;
        end
        ROTARY_SECOND: begin
          convert_expand<=1; convert_half<=fp16; convert_source<={16'd0,memory_value};
          convert_return<=ROTARY_EXPAND2; state<=CONVERT_SEND;
        end
        ROTARY_EXPAND2: begin
          rotary_source[63:32]<=converted_value;
          reader_descriptor<=descriptor; reader_row<=node_position;
          reader_column<={24'd0,pair_index,1'b0};
          reader_return<=ROTARY_COS; state<=READER_SEND;
        end
        ROTARY_COS: begin
          rotary_coefficients[31:0]<=read_fp32;
          reader_column<=reader_column+32'd1; reader_return<=ROTARY_SIN; state<=READER_SEND;
        end
        ROTARY_SIN: begin rotary_coefficients[63:32]<=read_fp32; state<=ROTARY_SEND; end
        ROTARY_SEND: if (rotary_ready) state<=ROTARY_WAIT;
        ROTARY_WAIT: if (rotary_valid) begin
          if (rotary_error || rotary_tag!=tag) state<=FAILURE;
          else begin rotary_data<=rotary_result; state<=ROTARY_SAVE1; end
        end
        ROTARY_SAVE1: begin
          memory_write_slot<=slot; memory_write_vector<=source_vector;
          memory_write_index<=pair_first; memory_write_data<=rotary_data[15:0];
          memory_return<=ROTARY_SAVE2; state<=ELEMENT_WRITE;
        end
        ROTARY_SAVE2: begin
          memory_write_slot<=slot; memory_write_vector<=source_vector;
          memory_write_index<=pair_second; memory_write_data<=rotary_data[31:16];
          memory_return<=ROTARY_NEXT; state<=ELEMENT_WRITE;
        end
        ROTARY_NEXT: begin
          if (!final_pair) begin pair_index<=pair_index+7'd1; state<=ROTARY_START; end
          else if ({28'd0,head}+32'd1<length) begin
            head<=head+4'd1; pair_index<=0; state<=ROTARY_START;
          end else if (!final_slot) begin
            slot<=slot+2'd1; head<=0; pair_index<=0; state<=ROTARY_START;
          end else state<=PHASE_DONE;
        end
        CACHE_START: begin
          head<={3'd0,cache_head}; cache_data<=0; block_word<=0; state<=CACHE_ELEMENT;
        end
        CACHE_ELEMENT: begin
          memory_slot<=slot; memory_vector<=cache_value ? VALUE : KEY;
          memory_index<=block_column; memory_return<=CACHE_EXPAND; state<=ELEMENT_READ;
        end
        CACHE_EXPAND: begin
          if (fp16) begin
            convert_expand<=1; convert_half<=1; convert_source<={16'd0,memory_value};
            convert_return<=CACHE_BF16; state<=CONVERT_SEND;
          end else begin converted_value<={16'd0,memory_value}; state<=CACHE_SAVE; end
        end
        CACHE_BF16: begin
          convert_expand<=0; convert_half<=0; convert_source<=converted_value;
          convert_return<=CACHE_SAVE; state<=CONVERT_SEND;
        end
        CACHE_SAVE: begin
          cache_data[16*block_word+:16]<=converted_value[15:0];
          if (final_block_word) state<=CACHE_SEND;
          else begin block_word<=block_word+7'd1; state<=CACHE_ELEMENT; end
        end
        CACHE_SEND: if (cache_write_ready) state<=CACHE_ACK;
        CACHE_ACK: if (cache_write_valid) begin
          if (cache_write_error) state<=FAILURE;
          else if (!final_block) begin block_index<=block_index+7'd1; state<=CACHE_START; end
          else begin
            block_index<=0;
            if (NUM_KV_HEADS==2 && !cache_head) begin cache_head<=1; state<=CACHE_START; end
            else begin
              cache_head<=0;
              if (!cache_value) begin cache_value<=1; state<=CACHE_START; end
              else if (!final_slot) begin slot<=slot+2'd1; cache_value<=0; state<=CACHE_START; end
              else state<=PHASE_DONE;
            end
          end
        end
        ATTENTION_START: begin dimension<=0; query_data<=0; state<=ATTENTION_ELEMENT; end
        ATTENTION_ELEMENT: begin
          memory_slot<=slot; memory_vector<=QUERY;
          memory_index<=head_base+{24'd0,dimension};
          memory_return<=ATTENTION_SAVE; state<=ELEMENT_READ;
        end
        ATTENTION_SAVE: begin
          query_data[16*dimension+:16]<=memory_value;
          if (final_dimension) state<=ATTENTION_SEND;
          else begin dimension<=dimension+8'd1; state<=ATTENTION_ELEMENT; end
        end
        ATTENTION_SEND: if (attention_ready) state<=ATTENTION_WAIT;
        ATTENTION_WAIT: if (attention_valid) begin
          if (attention_error || attention_tag!=tag) state<=FAILURE;
          else begin attention_data<=attention_result; dimension<=0; state<=ATTENTION_OUTPUT; end
        end
        ATTENTION_OUTPUT: begin
          memory_write_slot<=slot; memory_write_vector<=CONTEXT;
          memory_write_index<=head_base+{24'd0,dimension};
          memory_write_data<=attention_data[16*dimension+:16];
          memory_return<=ATTENTION_NEXT; state<=ELEMENT_WRITE;
        end
        ATTENTION_NEXT: begin
          if (!final_dimension) begin dimension<=dimension+8'd1; state<=ATTENTION_OUTPUT; end
          else if (head!=NUM_Q_HEADS-1) begin head<=head+4'd1; state<=ATTENTION_START; end
          else begin
            vector_valid[10*slot+CONTEXT]<=1;
            if (!final_slot) begin slot<=slot+2'd1; head<=0; state<=ATTENTION_START; end
            else state<=PHASE_DONE;
          end
        end
        FINISH: if (cache_finish_ready) state<=BATCH_RESPONSE;
        BATCH_RESPONSE: if (cache_response_valid && m_ready) begin
          if (!cache_response_error) begin
            published<=1;
            if (new_sequence) committed_origin<=position;
          end
          state<=IDLE;
        end
        FAILURE: begin sticky_fault<=1; vector_valid<=0; state<=FAILURE_DRAIN; end
        FAILURE_DRAIN: if (all_idle) state<=ERROR_RESPONSE;
        ERROR_RESPONSE: if (m_ready) state<=IDLE;
        default: state<=FAILURE;
      endcase
    end
  end endgenerate
endmodule
