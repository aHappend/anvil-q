module anvil_q2_ht_configuration #(
  parameter NUM_LAYERS=28,
  parameter HIDDEN_SIZE=1536,
  parameter INTERMEDIATE_SIZE=8960,
  parameter NUM_Q_HEADS=12,
  parameter NUM_KV_HEADS=2,
  parameter HEAD_DIM=128,
  parameter GROUP_SIZE=128,
  parameter VOCAB_SIZE=151936,
  parameter MAX_SEQ_LEN=32768,
  parameter CACHE_BLOCK=16
) (
  input wire clk, rst_n, annul,
  input wire operation_busy, quiescent, ddr_ready, sticky_fault,
  input wire cfg_valid, cfg_write,
  input wire [15:0] cfg_addr,
  input wire [31:0] cfg_wdata,
  output wire cfg_ready, cfg_rsp_valid,
  input wire cfg_rsp_ready,
  output wire [31:0] cfg_rdata,
  output wire cfg_error,
  output wire validating, model_loaded, configuration_changed,
  output wire weight_mode,
  output wire [1:0] cache_mode,
  output wire [32:0] kv_base, kv_length,
  input wire desc_req_valid,
  output wire desc_req_ready,
  input wire [8:0] desc_req_index,
  output wire desc_rsp_valid,
  input wire desc_rsp_ready,
  output wire [511:0] desc_rsp_data,
  output wire desc_rsp_error
);
  localparam SAFE_GROUP = GROUP_SIZE>=1 ? GROUP_SIZE : 1;
  localparam SAFE_BLOCK = CACHE_BLOCK>=1 ? CACHE_BLOCK : 1;
  localparam LEGAL = NUM_LAYERS>=1 && NUM_LAYERS<=28 &&
    HIDDEN_SIZE>=8 && HIDDEN_SIZE<=1536 &&
    INTERMEDIATE_SIZE>=8 && INTERMEDIATE_SIZE<=8960 &&
    NUM_Q_HEADS>=1 && NUM_Q_HEADS<=16 &&
    NUM_KV_HEADS>=1 && NUM_KV_HEADS<=2 &&
    HEAD_DIM>=2 && HEAD_DIM<=128 && (HEAD_DIM & 1)==0 &&
    HIDDEN_SIZE==NUM_Q_HEADS*HEAD_DIM &&
    (NUM_KV_HEADS==1 || (NUM_KV_HEADS==2 && (NUM_Q_HEADS & 1)==0)) &&
    (HIDDEN_SIZE & 7)==0 && (INTERMEDIATE_SIZE & 7)==0 &&
    ((NUM_KV_HEADS*HEAD_DIM) & 7)==0 &&
    GROUP_SIZE>=1 && GROUP_SIZE<=128 &&
    (GROUP_SIZE & (GROUP_SIZE-1))==0 &&
    (HIDDEN_SIZE & (SAFE_GROUP-1))==0 &&
    (INTERMEDIATE_SIZE & (SAFE_GROUP-1))==0 &&
    CACHE_BLOCK>=1 && CACHE_BLOCK<=128 &&
    (CACHE_BLOCK & (CACHE_BLOCK-1))==0 &&
    (HEAD_DIM & (SAFE_BLOCK-1))==0 &&
    VOCAB_SIZE>=1 && VOCAB_SIZE<=151936 &&
    MAX_SEQ_LEN>=1 && MAX_SEQ_LEN<=32768;
  generate if (!LEGAL) begin: invalid_parameters
    initial $fatal(1,"ANVIL_Q2_HT PARAMETER ERROR: configuration geometry");
    assign cfg_ready=0; assign cfg_rsp_valid=0; assign cfg_rdata=0;
    assign cfg_error=0; assign validating=0; assign model_loaded=0;
    assign configuration_changed=0; assign weight_mode=0; assign cache_mode=0;
    assign kv_base=0; assign kv_length=0; assign desc_req_ready=0;
    assign desc_rsp_valid=0; assign desc_rsp_data=0; assign desc_rsp_error=0;
  end else begin: implementation
    localparam ENTRIES=16+16*NUM_LAYERS;
    localparam RANGES=1+3*ENTRIES;
    localparam RW=$clog2(RANGES+1);
    localparam GROUP_SHIFT=$clog2(GROUP_SIZE);
    localparam BLOCK_SHIFT=$clog2(CACHE_BLOCK);
    localparam [63:0] Q16_STRIDE=
      ((NUM_KV_HEADS*HEAD_DIM*4+63) >> 6) << 6;
    localparam [63:0] FP16_STRIDE=
      ((NUM_KV_HEADS*HEAD_DIM*2+63) >> 6) << 6;
    localparam [63:0] INT8_STRIDE=
      ((NUM_KV_HEADS*(HEAD_DIM >> BLOCK_SHIFT)*(CACHE_BLOCK+1)+63) >> 6) << 6;
    localparam [63:0] Q16_EXTENT=64'(NUM_LAYERS*2*MAX_SEQ_LEN)*Q16_STRIDE;
    localparam [63:0] FP16_EXTENT=64'(NUM_LAYERS*2*MAX_SEQ_LEN)*FP16_STRIDE;
    localparam [63:0] INT8_EXTENT=64'(NUM_LAYERS*2*MAX_SEQ_LEN)*INT8_STRIDE;
    localparam [3:0] IDLE=0, START=1, LOAD=2, SHAPE=3, TILE_COUNT=4,
      MULTIPLY=5, LENGTHS=6, LENGTH_CHECK=7, REGION=8, SCAN=9, APPEND=10,
      NEXT=11, COPY=12;
    reg [3:0] state;
    reg shadow_weight;
    reg [1:0] shadow_cache;
    reg [32:0] shadow_base, shadow_length;
    reg loaded, committed_weight, changed, active_bank;
    reg [1:0] committed_cache;
    reg [32:0] committed_base, committed_length;
    reg response_valid, response_error;
    reg [31:0] response_data;
    (* ramstyle = "M20K, no_rw_check" , nomem2reg *) reg [511:0] shadow [0:ENTRIES-1];
    reg [15:0] initialized [0:ENTRIES-1];
    (* ramstyle = "M20K, no_rw_check" , nomem2reg *) reg [511:0] committed [0:2*ENTRIES-1];
    reg [511:0] descriptor, embedding_descriptor;
    reg descriptor_valid, descriptor_error;
    reg [511:0] descriptor_data;
    reg [8:0] index;
    reg [1:0] part;
    reg [RW-1:0] range_count, scan_index;
    (* ramstyle = "M20K, no_rw_check" , nomem2reg *) reg [32:0] range_base [0:RANGES-1];
    (* ramstyle = "M20K, no_rw_check" , nomem2reg *) reg [33:0] range_end [0:RANGES-1];
    (* nomem2reg *) reg [8:0] range_entry [0:RANGES-1];
    (* nomem2reg *) reg [1:0] range_part [0:RANGES-1];
    reg [32:0] candidate_base, prior_base;
    reg [33:0] candidate_end, prior_end;
    reg [8:0] prior_entry;
    reg [1:0] prior_part;
    reg scan_loaded;
    reg tiled, auxiliary;
    reg [31:0] main_row_bytes, zero_row_bytes, scale_row_bytes;
    reg [31:0] tile_count;
    reg [63:0] main_product, zero_product, scale_product;
    reg [63:0] main_minimum, zero_length, scale_length;
    reg [31:0] expected_rows, expected_cols;
    reg [1:0] expected_format;
    reg expected_reserved, expected_tiled;
    integer i;

    function automatic [511:0] visible_descriptor(
      input [511:0] value, input [15:0] mask);
      integer word_index;
      begin
        for (word_index=0; word_index<16; word_index=word_index+1)
          visible_descriptor[word_index*32+:32]=
            mask[word_index] ? value[word_index*32+:32] : 32'd0;
      end
    endfunction

    wire [63:0] d_base=descriptor[0+:64];
    wire [63:0] d_length=descriptor[64+:64];
    wire [63:0] d_zero=descriptor[128+:64];
    wire [63:0] d_scale=descriptor[192+:64];
    wire [31:0] d_rows=descriptor[256+:32];
    wire [31:0] d_cols=descriptor[288+:32];
    wire [31:0] d_stride=descriptor[320+:32];
    wire [31:0] d_zero_stride=descriptor[352+:32];
    wire [31:0] d_scale_stride=descriptor[384+:32];
    wire [31:0] d_flags=descriptor[416+:32];
    wire [63:0] configured_extent=shadow_cache==0 ? Q16_EXTENT :
      (shadow_cache==1 ? FP16_EXTENT : INT8_EXTENT);
    wire [33:0] configured_end={1'b0,shadow_base}+{1'b0,shadow_length};
    wire [8:0] cfg_index=9'((cfg_addr-16'h1000) >> 6);
    wire descriptor_address=cfg_addr>=16'h1000 &&
      {1'b0,cfg_addr}<17'(16'h1000+64*ENTRIES);
    wire [31:0] groups=d_cols >> GROUP_SHIFT;
    wire [31:0] tile_rows=(d_rows+32'd15) >> 4;
    wire [31:0] tile_cols=(d_cols+32'd127) >> 7;
    wire [63:0] selected_base=part==0 ? d_base : (part==1 ? d_zero : d_scale);
    wire [63:0] selected_length=part==0 ? d_length :
      (part==1 ? zero_length : scale_length);
    wire [64:0] selected_end={1'b0,selected_base}+{1'b0,selected_length};
    wire overlap=candidate_base<prior_end &&
      prior_base<candidate_end;
    wire identical_embedding_alias=index==1 && part==0 &&
      prior_entry==0 && prior_part==0 && descriptor==embedding_descriptor;
    wire cfg_transfer=cfg_valid && cfg_ready;
    wire can_write=!operation_busy && quiescent;
    wire busy=state!=IDLE;

    always @* begin
      expected_rows=1;
      expected_cols=HIDDEN_SIZE;
      expected_format=shadow_weight ? 2'd2 : 2'd1;
      expected_reserved=0;
      expected_tiled=0;
      if (index==0 || index==1) expected_rows=VOCAB_SIZE;
      else if (index==3) begin
        expected_rows=MAX_SEQ_LEN;
        expected_cols=HEAD_DIM;
        expected_format=3;
      end else if (index>=4 && index<16) expected_reserved=1;
      else if (index>=16) begin
        case (index[3:0])
          0,3: begin
            expected_rows=HIDDEN_SIZE; expected_cols=HIDDEN_SIZE;
            expected_tiled=1; expected_format=shadow_weight ? 2'd2 : 2'd0;
          end
          1,2: begin
            expected_rows=NUM_KV_HEADS*HEAD_DIM; expected_cols=HIDDEN_SIZE;
            expected_tiled=1; expected_format=shadow_weight ? 2'd2 : 2'd0;
          end
          4,5: begin
            expected_rows=INTERMEDIATE_SIZE; expected_cols=HIDDEN_SIZE;
            expected_tiled=1; expected_format=shadow_weight ? 2'd2 : 2'd0;
          end
          6: begin
            expected_rows=HIDDEN_SIZE; expected_cols=INTERMEDIATE_SIZE;
            expected_tiled=1; expected_format=shadow_weight ? 2'd2 : 2'd0;
          end
          7,8,9: begin end
          10,11: expected_cols=NUM_KV_HEADS*HEAD_DIM;
          default: expected_reserved=1;
        endcase
      end
    end

    assign cfg_ready=rst_n && !annul && !response_valid && !busy;
    assign cfg_rsp_valid=rst_n && response_valid;
    assign cfg_rdata=cfg_rsp_valid ? response_data : 32'd0;
    assign cfg_error=cfg_rsp_valid && response_error;
    assign validating=rst_n && busy;
    assign model_loaded=rst_n && loaded;
    assign configuration_changed=rst_n && changed;
    assign weight_mode=rst_n && committed_weight;
    assign cache_mode=rst_n ? committed_cache : 2'd0;
    assign kv_base=rst_n ? committed_base : 33'd0;
    assign kv_length=rst_n ? committed_length : 33'd0;
    assign desc_req_ready=rst_n && !annul && !busy && loaded &&
      (!descriptor_valid || desc_rsp_ready);
    assign desc_rsp_valid=rst_n && descriptor_valid;
    assign desc_rsp_data=desc_rsp_valid ? descriptor_data : 512'd0;
    assign desc_rsp_error=desc_rsp_valid && descriptor_error;

    always @(posedge clk) begin
      if (cfg_transfer && cfg_write && can_write && cfg_addr[1:0]==0 &&
          descriptor_address) begin
        shadow[cfg_index][cfg_addr[5:2]*32+:32]<=cfg_wdata;
      end
      if (state==LOAD && !annul)
        descriptor<=visible_descriptor(shadow[index],initialized[index]);
      if (state==COPY && !annul)
        committed[(active_bank ? 0 : ENTRIES)+index]<=
          visible_descriptor(shadow[index],initialized[index]);
      if (desc_req_valid && desc_req_ready) begin
        if (desc_req_index<ENTRIES)
          descriptor_data<=committed[(active_bank ? ENTRIES : 0)+desc_req_index];
        else descriptor_data<=0;
      end
      if (state==SCAN && !scan_loaded && scan_index<range_count) begin
        prior_base<=range_base[scan_index];
        prior_end<=range_end[scan_index];
        prior_entry<=range_entry[scan_index];
        prior_part<=range_part[scan_index];
      end
      if (state==START && !annul) begin
        range_base[0]<=shadow_base;
        range_end[0]<=configured_end;
        range_entry[0]<=9'h1ff;
        range_part[0]<=0;
      end
      if (state==APPEND && !annul) begin
        range_base[range_count]<=candidate_base;
        range_end[range_count]<=candidate_end;
        range_entry[range_count]<=index;
        range_part[range_count]<=part;
      end
    end

    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        state<=IDLE; shadow_weight<=0; shadow_cache<=0;
        shadow_base<=0; shadow_length<=0; loaded<=0;
        committed_weight<=0; committed_cache<=0; committed_base<=0;
        committed_length<=0; changed<=0; active_bank<=0;
        response_valid<=0; response_error<=0; response_data<=0;
        descriptor_valid<=0; descriptor_error<=0; index<=0; part<=0;
        range_count<=0; scan_index<=0; candidate_base<=0; candidate_end<=0;
        scan_loaded<=0; tiled<=0; auxiliary<=0; main_row_bytes<=0;
        zero_row_bytes<=0; scale_row_bytes<=0; tile_count<=0;
        main_product<=0; zero_product<=0; scale_product<=0;
        main_minimum<=0; zero_length<=0; scale_length<=0;
        embedding_descriptor<=0;
        for (i=0; i<ENTRIES; i=i+1) initialized[i]<=0;
      end else begin
        changed<=0;
        if (response_valid && cfg_rsp_ready) response_valid<=0;
        if (descriptor_valid && desc_rsp_ready) descriptor_valid<=0;
        if (desc_req_valid && desc_req_ready) begin
          descriptor_valid<=1;
          descriptor_error<=desc_req_index>=ENTRIES;
        end
        if (annul) begin descriptor_valid<=0; descriptor_error<=0; end
        if (annul && busy) begin
          state<=IDLE;
          response_valid<=1; response_error<=1; response_data<=0;
        end else case (state)
          IDLE: if (cfg_transfer) begin
            response_valid<=1; response_error<=0; response_data<=0;
            if (cfg_addr[1:0]!=0) response_error<=1;
            else if (cfg_write) begin
              if (!can_write) response_error<=1;
              else if (descriptor_address) begin
                initialized[cfg_index][cfg_addr[5:2]]<=1;
              end else case (cfg_addr)
                16'h0008: begin
                  if (cfg_wdata==1) begin
                    state<=START; response_valid<=0; index<=0;
                  end else if (cfg_wdata==2) begin
                    loaded<=0; changed<=1; descriptor_valid<=0;
                  end else if (cfg_wdata!=0) response_error<=1;
                end
                16'h0010: if (cfg_wdata>1) response_error<=1;
                  else shadow_weight<=cfg_wdata[0];
                16'h0014: if (cfg_wdata>2) response_error<=1;
                  else shadow_cache<=cfg_wdata[1:0];
                16'h0018: shadow_base[31:0]<=cfg_wdata;
                16'h001c: if (cfg_wdata>1) response_error<=1;
                  else shadow_base[32]<=cfg_wdata[0];
                16'h0020: shadow_length[31:0]<=cfg_wdata;
                16'h0024: if (cfg_wdata>1) response_error<=1;
                  else shadow_length[32]<=cfg_wdata[0];
                default: response_error<=1;
              endcase
            end else if (descriptor_address) begin
              response_data<=initialized[cfg_index][cfg_addr[5:2]] ?
                shadow[cfg_index][cfg_addr[5:2]*32+:32] : 32'd0;
            end else case (cfg_addr)
              16'h0000: response_data<=32'h41513248;
              16'h0004: response_data<=32'h02000000;
              16'h0008: response_data<=0;
              16'h000c: response_data<={28'd0,ddr_ready,sticky_fault,
                operation_busy,loaded};
              16'h0010: response_data<={31'd0,shadow_weight};
              16'h0014: response_data<={30'd0,shadow_cache};
              16'h0018: response_data<=shadow_base[31:0];
              16'h001c: response_data<={31'd0,shadow_base[32]};
              16'h0020: response_data<=shadow_length[31:0];
              16'h0024: response_data<={31'd0,shadow_length[32]};
              default: response_error<=1;
            endcase
          end
          START: begin
            if (shadow_cache>2 || (|shadow_base[5:0]) ||
                {31'd0,shadow_length}<configured_extent ||
                configured_end>34'd8589934592) begin
              state<=IDLE; response_valid<=1; response_error<=1;
            end else begin range_count<=1; state<=LOAD; end
          end
          LOAD: state<=SHAPE;
          SHAPE: begin
            if (expected_reserved) begin
              if (descriptor!=0) begin
                state<=IDLE; response_valid<=1; response_error<=1;
              end else state<=NEXT;
            end else if (d_rows!=expected_rows || d_cols!=expected_cols ||
                d_flags!={23'd0,1'b1,6'd0,expected_format} ||
                descriptor[448+:64]!=0 || (|d_base[63:33]) ||
                (expected_tiled && ((|d_base[5:0]) || (|d_stride[5:0]))) ||
                (!expected_tiled && (|d_base[0+:1])) ||
                (!expected_tiled && expected_format==3 && (|d_base[1:0])) ||
                (expected_format!=0 && (d_zero!=0 || d_scale!=0 ||
                  d_zero_stride!=0 || d_scale_stride!=0)) ||
                (expected_format==0 && ((|d_zero[63:33]) ||
                  (|d_scale[63:33]) || d_scale[0] || d_scale_stride[0])) ||
                (!expected_tiled && d_stride[0]) ||
                (!expected_tiled && expected_format==3 && (|d_stride[1:0]))) begin
              state<=IDLE; response_valid<=1; response_error<=1;
            end else begin
              tiled<=expected_tiled; auxiliary<=expected_format==0;
              main_row_bytes<=expected_tiled ?
                (shadow_weight ? 32'd4096 : 32'd1024) :
                (d_cols << (expected_format==3 ? 2 : 1));
              zero_row_bytes<=(groups+32'd1) >> 1;
              scale_row_bytes<=groups << 1;
              if (index==0) embedding_descriptor<=descriptor;
              state<=TILE_COUNT;
            end
          end
          TILE_COUNT: begin
            tile_count<=tile_rows*tile_cols;
            zero_product<={32'd0,d_rows-32'd1}*{32'd0,d_zero_stride};
            scale_product<={32'd0,d_rows-32'd1}*{32'd0,d_scale_stride};
            state<=MULTIPLY;
          end
          MULTIPLY: begin
            main_product<=tiled ?
              {32'd0,tile_count-32'd1}*{32'd0,d_stride} :
              {32'd0,d_rows-32'd1}*{32'd0,d_stride};
            state<=LENGTHS;
          end
          LENGTHS: begin
            main_minimum<=main_product+{32'd0,main_row_bytes};
            zero_length<=zero_product+{32'd0,zero_row_bytes};
            scale_length<=scale_product+{32'd0,scale_row_bytes};
            state<=LENGTH_CHECK;
          end
          LENGTH_CHECK: begin
            if (d_stride<main_row_bytes || d_length<main_minimum ||
                (auxiliary && (d_zero_stride<zero_row_bytes ||
                  d_scale_stride<scale_row_bytes))) begin
              state<=IDLE; response_valid<=1; response_error<=1;
            end else begin part<=0; state<=REGION; end
          end
          REGION: begin
            if ((|selected_base[63:33]) || selected_length==0 ||
                selected_end>65'd8589934592) begin
              state<=IDLE; response_valid<=1; response_error<=1;
            end else begin
              candidate_base<=selected_base[32:0];
              candidate_end<=selected_end[33:0];
              scan_index<=0; scan_loaded<=0; state<=SCAN;
            end
          end
          SCAN: begin
            if (scan_index==range_count) state<=APPEND;
            else if (!scan_loaded) scan_loaded<=1;
            else if (overlap && !identical_embedding_alias) begin
              state<=IDLE; response_valid<=1; response_error<=1;
            end else begin scan_index<=scan_index+1'b1; scan_loaded<=0; end
          end
          APPEND: begin
            range_count<=range_count+1'b1;
            if (auxiliary && part<2) begin part<=part+2'd1; state<=REGION; end
            else state<=NEXT;
          end
          NEXT: begin
            if (index+9'd1<ENTRIES) begin index<=index+9'd1; state<=LOAD; end
            else begin index<=0; state<=COPY; end
          end
          COPY: begin
            if (index+9'd1<ENTRIES) index<=index+9'd1;
            else begin
              state<=IDLE; response_valid<=1; response_error<=0;
              loaded<=1; active_bank<=!active_bank; changed<=1;
              descriptor_valid<=0;
              committed_weight<=shadow_weight; committed_cache<=shadow_cache;
              committed_base<=shadow_base; committed_length<=shadow_length;
            end
          end
          default: begin state<=IDLE; response_valid<=1; response_error<=1; end
        endcase
      end
    end
  end endgenerate
endmodule
