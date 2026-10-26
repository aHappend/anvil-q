module anvil_q2_ht_kv_cache #(
  parameter NUM_LAYERS=28,
  parameter NUM_KV_HEADS=2,
  parameter HEAD_DIM=128,
  parameter MAX_SEQ_LEN=32768,
  parameter CACHE_BLOCK=16,
  parameter HOT_BLOCKS=64,
  parameter WORDS=(CACHE_BLOCK>=1 && CACHE_BLOCK<=128) ? CACHE_BLOCK : 1
) (
  input wire clk, rst_n, invalidate,
  input wire [1:0] cfg_mode,
  input wire [32:0] cfg_base, cfg_length,
  input wire cmd_valid,
  output wire cmd_ready,
  input wire cmd_write, cmd_value,
  input wire [31:0] cmd_layer, cmd_pos, cmd_head, cmd_block,
  input wire [WORDS*32-1:0] cmd_data,
  output wire rsp_valid,
  input wire rsp_ready,
  output wire [WORDS*32-1:0] rsp_data,
  output wire rsp_error,
  input wire commit_valid,
  output wire commit_ready,
  input wire [31:0] commit_layer, commit_pos,
  output wire idle,
  output wire mem_req_valid,
  input wire mem_req_ready,
  output wire mem_req_write,
  output wire [32:0] mem_req_addr,
  output wire [511:0] mem_req_wdata,
  output wire [63:0] mem_req_be,
  input wire mem_rsp_valid,
  output wire mem_rsp_ready,
  input wire [511:0] mem_rsp_rdata,
  input wire mem_rsp_error
);
  localparam LEGAL = NUM_LAYERS>=1 && NUM_LAYERS<=28 &&
    NUM_KV_HEADS>=1 && NUM_KV_HEADS<=2 &&
    HEAD_DIM>=2 && HEAD_DIM<=128 && (HEAD_DIM & 1)==0 &&
    MAX_SEQ_LEN>=1 && MAX_SEQ_LEN<=32768 &&
    CACHE_BLOCK>=1 && CACHE_BLOCK<=128 &&
    (CACHE_BLOCK & (CACHE_BLOCK-1))==0 &&
    WORDS==CACHE_BLOCK && (HEAD_DIM & (WORDS-1))==0 &&
    HOT_BLOCKS>=1 && HOT_BLOCKS<=64;
  generate if (!LEGAL) begin: invalid_parameters
    initial $fatal(1,"ANVIL_Q2_HT PARAMETER ERROR: KV geometry");
    assign cmd_ready = 0; assign commit_ready = 0; assign rsp_valid = 0;
    assign rsp_data = 0; assign rsp_error = 0; assign idle = 0;
    assign mem_req_valid = 0; assign mem_req_write = 0; assign mem_req_addr = 0;
    assign mem_req_wdata = 0; assign mem_req_be = 0; assign mem_rsp_ready = 0;
  end else begin: implementation
    localparam BLOCK_SHIFT = $clog2(CACHE_BLOCK);
    localparam BLOCKS = HEAD_DIM >> BLOCK_SHIFT;
    localparam PARTS = 2*NUM_KV_HEADS*BLOCKS;
    localparam Q16_STRIDE = ((NUM_KV_HEADS*HEAD_DIM*4+63) >> 6) << 6;
    localparam FP16_STRIDE = ((NUM_KV_HEADS*HEAD_DIM*2+63) >> 6) << 6;
    localparam INT8_STRIDE =
      ((NUM_KV_HEADS*BLOCKS*(CACHE_BLOCK+1)+63) >> 6) << 6;
    localparam [32:0] Q16_EXTENT = 33'(NUM_LAYERS*2*MAX_SEQ_LEN)*Q16_STRIDE;
    localparam [32:0] FP16_EXTENT = 33'(NUM_LAYERS*2*MAX_SEQ_LEN)*FP16_STRIDE;
    localparam [32:0] INT8_EXTENT = 33'(NUM_LAYERS*2*MAX_SEQ_LEN)*INT8_STRIDE;
    localparam [4:0] IDLE=0, ENCODE_START=1, ENCODE_WAIT=2,
      ADDRESS1=3, ADDRESS2=4, ADDRESS3=5, PACK=6,
      MEMORY_REQUEST=7, MEMORY_RESPONSE=8, UNPACK=9,
      DECODE_START=10, DECODE_WAIT=11, INSTALL=12, RESPONSE=13,
      HOT_READ=14, HOT_LATCH=15;
    reg [4:0] state;
    reg canceled, failed, operation_write, operation_value;
    reg [1:0] mode;
    reg [31:0] layer, position, head, block_index;
    reg [32:0] base, allocation_length;
    reg [WORDS*32-1:0] source_data, record, block_result, result;
    reg [10:0] token_stride;
    reg [9:0] record_length, record_pointer;
    reg [8:0] part_index;
    reg [20:0] token_region_index;
    reg [10:0] block_offset;
    reg [32:0] relative_address, memory_address;
    reg [5:0] beat_byte;
    reg [511:0] write_buffer, read_buffer;
    reg [63:0] write_mask;
    reg [31:0] committed [0:NUM_LAYERS-1];
    reg [PARTS-1:0] written [0:NUM_LAYERS-1];
    reg [HOT_BLOCKS-1:0] hot_valid;
    reg [31:0] hot_layer [0:HOT_BLOCKS-1];
    reg [31:0] hot_position [0:HOT_BLOCKS-1];
    reg [31:0] hot_head [0:HOT_BLOCKS-1];
    reg [31:0] hot_block [0:HOT_BLOCKS-1];
    reg hot_value [0:HOT_BLOCKS-1];
    reg [1:0] hot_mode [0:HOT_BLOCKS-1];
    reg [5:0] target, replacement;
    reg target_hit;
    reg [63:0] hit_bitmap;
    (* ramstyle = "M20K, no_rw_check" , nomem2reg *) reg [WORDS*32-1:0] hot_ram [0:HOT_BLOCKS-1];
    reg [WORDS*32-1:0] hot_read_data;
    integer i, match_index;

    function automatic [5:0] first_match64(input [63:0] mask);
      reg [63:0] work;
      reg [5:0] answer;
      begin
        work = mask;
        answer = 0;
        if (!(|work[31:0])) begin answer = answer+32; work = work >> 32; end
        if (!(|work[15:0])) begin answer = answer+16; work = work >> 16; end
        if (!(|work[7:0])) begin answer = answer+8; work = work >> 8; end
        if (!(|work[3:0])) begin answer = answer+4; work = work >> 4; end
        if (!(|work[1:0])) begin answer = answer+2; work = work >> 2; end
        if (!work[0]) answer = answer+1;
        first_match64 = answer;
      end
    endfunction

    always @* begin
      hit_bitmap = 0;
      for (match_index=0; match_index<HOT_BLOCKS; match_index=match_index+1)
        hit_bitmap[match_index] = hot_valid[match_index] &&
          hot_layer[match_index]==cmd_layer && hot_position[match_index]==cmd_pos &&
          hot_head[match_index]==cmd_head && hot_block[match_index]==cmd_block &&
          hot_value[match_index]==cmd_value && hot_mode[match_index]==cfg_mode;
    end

    wire hit = |hit_bitmap;
    wire [5:0] hit_index = first_match64(hit_bitmap);
    wire [10:0] configured_stride = cfg_mode==0 ? 11'(Q16_STRIDE) :
      (cfg_mode==1 ? 11'(FP16_STRIDE) : 11'(INT8_STRIDE));
    wire [32:0] configured_extent = cfg_mode==0 ? Q16_EXTENT :
      (cfg_mode==1 ? FP16_EXTENT : INT8_EXTENT);
    wire [33:0] configured_end = {1'b0,cfg_base}+{1'b0,cfg_length};
    wire invalid_configuration = cfg_mode>2 || (|cfg_base[5:0]) ||
      cfg_length<configured_extent || configured_end>34'd8589934592;
    wire invalid_command = invalid_configuration || cmd_layer>=NUM_LAYERS ||
      cmd_pos>=MAX_SEQ_LEN || cmd_head>=NUM_KV_HEADS || cmd_block>=BLOCKS;
    wire [33:0] absolute_address = {1'b0,base}+{1'b0,relative_address};
    wire [33:0] relative_end = {1'b0,relative_address}+{24'd0,record_length};
    wire codec_s_ready, codec_m_valid, codec_m_error;
    wire [WORDS*32-1:0] codec_data, codec_record;
    wire [9:0] codec_length;
    wire codec_start = rst_n && !invalidate && !canceled &&
      (state==ENCODE_START || state==DECODE_START);
    wire codec_receive = rst_n && !invalidate && !canceled &&
      (state==ENCODE_WAIT || state==DECODE_WAIT);
    wire codec_failure = codec_receive && codec_m_valid && codec_m_error;
    wire memory_failure = state==MEMORY_RESPONSE && mem_rsp_valid && mem_rsp_error;
    wire can_operate = rst_n && !invalidate && !canceled;

    anvil_q2_ht_kv_codec #(.CACHE_BLOCK(CACHE_BLOCK),.WORDS(WORDS)) codec (
      .clk(clk),.rst_n(rst_n),.annul(invalidate || canceled),
      .s_valid(codec_start),.s_ready(codec_s_ready),.s_encode(state==ENCODE_START),
      .s_mode(mode),.s_data(source_data),.s_record(record),
      .m_valid(codec_m_valid),.m_ready(codec_receive),
      .m_data(codec_data),.m_record(codec_record),
      .m_byte_length(codec_length),.m_error(codec_m_error));

    assign cmd_ready = can_operate && state==IDLE && !commit_valid;
    assign commit_ready = can_operate && state==IDLE;
    assign rsp_valid = can_operate && state==RESPONSE;
    assign rsp_data = rsp_valid ? result : {WORDS*32{1'b0}};
    assign rsp_error = rsp_valid && failed;
    assign idle = can_operate && state==IDLE;
    // Invalidation never withdraws an already presented backing request.
    assign mem_req_valid = rst_n && state==MEMORY_REQUEST;
    assign mem_req_write = mem_req_valid && operation_write;
    assign mem_req_addr = mem_req_valid ? memory_address : 33'd0;
    assign mem_req_wdata = mem_req_write ? write_buffer : 512'd0;
    assign mem_req_be = mem_req_valid ?
      (operation_write ? write_mask : {64{1'b1}}) : 64'd0;
    assign mem_rsp_ready = rst_n && state==MEMORY_RESPONSE;

    always @(posedge clk) begin
      if (can_operate && state==HOT_READ) hot_read_data <= hot_ram[target];
      if (can_operate && state==INSTALL) hot_ram[target] <= block_result;
    end

    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        state <= IDLE; canceled <= 0; failed <= 0; operation_write <= 0;
        operation_value <= 0; mode <= 0; layer <= 0; position <= 0; head <= 0;
        block_index <= 0; base <= 0; allocation_length <= 0;
        source_data <= 0; record <= 0; block_result <= 0; result <= 0;
        token_stride <= 0; record_length <= 0; record_pointer <= 0; part_index <= 0;
        token_region_index <= 0; block_offset <= 0; relative_address <= 0;
        memory_address <= 0; beat_byte <= 0; write_buffer <= 0; read_buffer <= 0;
        write_mask <= 0; hot_valid <= 0; target <= 0; replacement <= 0; target_hit <= 0;
        for (i=0; i<NUM_LAYERS; i=i+1) begin committed[i] <= 0; written[i] <= 0; end
        for (i=0; i<HOT_BLOCKS; i=i+1) begin
          hot_layer[i] <= 0; hot_position[i] <= 0; hot_head[i] <= 0;
          hot_block[i] <= 0; hot_value[i] <= 0; hot_mode[i] <= 0;
        end
      end else if (invalidate || canceled) begin
        if (invalidate) begin
          hot_valid <= 0;
          for (i=0; i<NUM_LAYERS; i=i+1) begin committed[i] <= 0; written[i] <= 0; end
        end
        if (state==MEMORY_REQUEST) begin
          canceled <= 1;
          if (mem_req_ready) state <= MEMORY_RESPONSE;
        end else if (state==MEMORY_RESPONSE) begin
          if (mem_rsp_valid) begin state <= IDLE; canceled <= 0; end
          else canceled <= 1;
        end else begin
          state <= IDLE;
          canceled <= 0;
        end
      end else if (codec_failure || memory_failure) begin
        state <= RESPONSE; failed <= 1; result <= 0;
        hot_valid <= 0;
        for (i=0; i<NUM_LAYERS; i=i+1) begin committed[i] <= 0; written[i] <= 0; end
      end else case (state)
        IDLE: begin
          if (commit_valid && commit_ready) begin
            result <= 0;
            failed <= 0;
            state <= RESPONSE;
            if (invalid_configuration || commit_layer>=NUM_LAYERS ||
                commit_pos>=MAX_SEQ_LEN) failed <= 1;
            else if (commit_pos!=committed[commit_layer] ||
                     !(&written[commit_layer])) failed <= 1;
            else begin
              committed[commit_layer] <= committed[commit_layer]+32'd1;
              written[commit_layer] <= 0;
            end
          end else if (cmd_valid && cmd_ready) begin
            failed <= 0; result <= 0;
            operation_write <= cmd_write; operation_value <= cmd_value;
            mode <= cfg_mode; layer <= cmd_layer; position <= cmd_pos;
            head <= cmd_head; block_index <= cmd_block;
            base <= cfg_base; allocation_length <= cfg_length;
            source_data <= cmd_data; record <= 0; block_result <= 0;
            token_stride <= configured_stride;
            part_index <= 9'((cmd_value*NUM_KV_HEADS+cmd_head)*BLOCKS+cmd_block);
            if (cfg_mode==0) record_length <= CACHE_BLOCK*4;
            else if (cfg_mode==1) record_length <= CACHE_BLOCK*2;
            else record_length <= CACHE_BLOCK+1;
            target <= hit ? hit_index : replacement;
            target_hit <= hit;
            if (invalid_command) begin failed <= 1; state <= RESPONSE; end
            else if ((cmd_write && cmd_pos!=committed[cmd_layer]) ||
                     (!cmd_write && cmd_pos>=committed[cmd_layer])) begin
              failed <= 1; state <= RESPONSE;
            end else if (cmd_write) state <= ENCODE_START;
            else if (hit) state <= HOT_READ;
            else state <= ADDRESS1;
          end
        end
        ENCODE_START: if (codec_s_ready) state <= ENCODE_WAIT;
        ENCODE_WAIT: if (codec_m_valid) begin
          record <= codec_record;
          block_result <= codec_data;
          record_length <= codec_length;
          state <= ADDRESS1;
        end
        ADDRESS1: begin
          token_region_index <= 21'(((layer << 1)+{31'd0,operation_value})*
            MAX_SEQ_LEN+position);
          block_offset <= 11'((head*BLOCKS+block_index)*record_length);
          state <= ADDRESS2;
        end
        ADDRESS2: begin
          relative_address <= {12'd0,token_region_index}*{22'd0,token_stride}+
            {22'd0,block_offset};
          state <= ADDRESS3;
        end
        ADDRESS3: begin
          if (absolute_address[33] || relative_end>{1'b0,allocation_length} ||
              absolute_address+{24'd0,record_length}>34'd8589934592) begin
            failed <= 1; state <= RESPONSE;
          end else begin
            memory_address <= {absolute_address[32:6],6'd0};
            beat_byte <= absolute_address[5:0];
            record_pointer <= 0;
            write_buffer <= 0; write_mask <= 0;
            if (operation_write) state <= PACK;
            else state <= MEMORY_REQUEST;
          end
        end
        PACK: begin
          write_buffer[beat_byte*8+:8] <= record[record_pointer*8+:8];
          write_mask[beat_byte] <= 1;
          record_pointer <= record_pointer+10'd1;
          if (beat_byte==63 || record_pointer+10'd1==record_length) begin
            beat_byte <= 0;
            state <= MEMORY_REQUEST;
          end else beat_byte <= beat_byte+6'd1;
        end
        MEMORY_REQUEST: if (mem_req_ready) state <= MEMORY_RESPONSE;
        MEMORY_RESPONSE: if (mem_rsp_valid) begin
          if (operation_write) begin
            if (record_pointer==record_length) state <= INSTALL;
            else begin
              memory_address <= memory_address+33'd64;
              write_buffer <= 0; write_mask <= 0;
              state <= PACK;
            end
          end else begin
            read_buffer <= mem_rsp_rdata;
            state <= UNPACK;
          end
        end
        UNPACK: begin
          record[record_pointer*8+:8] <= read_buffer[beat_byte*8+:8];
          record_pointer <= record_pointer+10'd1;
          if (record_pointer+10'd1==record_length) state <= DECODE_START;
          else if (beat_byte==63) begin
            beat_byte <= 0;
            memory_address <= memory_address+33'd64;
            state <= MEMORY_REQUEST;
          end else beat_byte <= beat_byte+6'd1;
        end
        DECODE_START: if (codec_s_ready) state <= DECODE_WAIT;
        DECODE_WAIT: if (codec_m_valid) begin
          block_result <= codec_data;
          state <= INSTALL;
        end
        INSTALL: begin
          hot_valid[target] <= 1;
          hot_layer[target] <= layer; hot_position[target] <= position;
          hot_head[target] <= head; hot_block[target] <= block_index;
          hot_value[target] <= operation_value; hot_mode[target] <= mode;
          if (!target_hit) begin
            if (replacement==HOT_BLOCKS-1) replacement <= 0;
            else replacement <= replacement+6'd1;
          end
          if (operation_write) written[layer][part_index] <= 1;
          result <= block_result;
          state <= RESPONSE;
        end
        HOT_READ: state <= HOT_LATCH;
        HOT_LATCH: begin result <= hot_read_data; state <= RESPONSE; end
        RESPONSE: if (rsp_ready) state <= IDLE;
        default: begin failed <= 1; result <= 0; state <= RESPONSE; end
      endcase
    end
  end endgenerate
endmodule
