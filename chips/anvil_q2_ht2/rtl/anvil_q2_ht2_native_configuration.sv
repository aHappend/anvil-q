module anvil_q2_ht2_native_configuration #(
  parameter NUM_LAYERS=28, HIDDEN_SIZE=1536, INTERMEDIATE_SIZE=8960,
  parameter NUM_Q_HEADS=12, NUM_KV_HEADS=2, HEAD_DIM=128,
  parameter GROUP_SIZE=128, VOCAB_SIZE=151936, MAX_SEQ_LEN=32768,
  parameter CACHE_BLOCK=16
) (
  input wire clk, rst_n, annul, invalidate,
  input wire [5:0] ht2_mode,
  input wire operation_busy, quiescent, ddr_ready, sticky_fault,
  input wire cfg_valid, cfg_write,
  input wire [15:0] cfg_addr,
  input wire [31:0] cfg_wdata,
  output wire cfg_ready, cfg_rsp_valid,
  input wire cfg_rsp_ready,
  output wire [31:0] cfg_rdata,
  output wire cfg_error,
  output wire validating, model_loaded, configuration_changed,
  output wire [32:0] kv_base, kv_length,
  input wire desc_req_valid,
  output wire desc_req_ready,
  input wire [8:0] desc_req_index,
  output wire desc_rsp_valid,
  input wire desc_rsp_ready,
  output wire [511:0] desc_rsp_data,
  output wire desc_rsp_error
);
  localparam SAFE_GROUP=GROUP_SIZE>=1 ? GROUP_SIZE : 1;
  localparam SAFE_BLOCK=CACHE_BLOCK>=1 ? CACHE_BLOCK : 1;
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
    GROUP_SIZE>=1 && GROUP_SIZE<=128 &&
    (GROUP_SIZE & (GROUP_SIZE-1))==0 &&
    (HIDDEN_SIZE & (SAFE_GROUP-1))==0 &&
    (INTERMEDIATE_SIZE & (SAFE_GROUP-1))==0 &&
    CACHE_BLOCK>=1 && CACHE_BLOCK<=128 &&
    (CACHE_BLOCK & (CACHE_BLOCK-1))==0 && (HEAD_DIM & (SAFE_BLOCK-1))==0 &&
    VOCAB_SIZE>=1 && VOCAB_SIZE<=151936 &&
    MAX_SEQ_LEN>=1 && MAX_SEQ_LEN<=32768;
  generate if (!LEGAL) begin: invalid_parameters
    initial $fatal(1,"ANVIL_Q2_HT2 PARAMETER ERROR: native configuration geometry");
    assign cfg_ready=0; assign cfg_rsp_valid=0; assign cfg_rdata=0;
    assign cfg_error=0; assign validating=0; assign model_loaded=0;
    assign configuration_changed=0; assign kv_base=0; assign kv_length=0;
    assign desc_req_ready=0; assign desc_rsp_valid=0;
    assign desc_rsp_data=0; assign desc_rsp_error=0;
  end else begin: implementation
    localparam ENTRIES=16+16*NUM_LAYERS;
    localparam AW=$clog2(2*ENTRIES);
    localparam RANGES=1+3*ENTRIES;
    localparam RW=$clog2(RANGES+1);
    localparam BLOCK_SHIFT=$clog2(CACHE_BLOCK);
    localparam [63:0] RECORDS=64'(NUM_LAYERS*2*NUM_KV_HEADS)*
      (HEAD_DIM >> BLOCK_SHIFT)*(MAX_SEQ_LEN+4);
    localparam [63:0] BF16_EXTENT=(RECORDS*(2*CACHE_BLOCK)+63) & ~64'd63;
    localparam [63:0] INT8_EXTENT=(RECORDS*(CACHE_BLOCK+2)+63) & ~64'd63;
    localparam [3:0] IDLE=0, START=1, LOAD=2, CHECK_SEND=3, CHECK_WAIT=4,
      REGION=5, SCAN=6, APPEND=7, NEXT=8, COPY=9;
    reg [3:0] state;
    reg loaded, active_bank, changed, response_valid, response_error;
    reg [31:0] response_data;
    reg [32:0] shadow_base, shadow_length, committed_base, committed_length;
    reg shadow_weight;
    reg [1:0] shadow_cache;
    reg [5:0] validated_mode, committed_mode;
    (* ramstyle = "M20K", nomem2reg *) reg [511:0] shadow [0:ENTRIES-1];
    (* ramstyle = "M20K", nomem2reg *) reg [511:0] committed [0:2*ENTRIES-1];
    reg [15:0] initialized [0:ENTRIES-1];
    reg [511:0] descriptor, embedding_descriptor, descriptor_data;
    reg descriptor_valid, descriptor_error;
    reg [8:0] index;
    reg [1:0] part, region_count;
    reg [98:0] regions_base;
    reg [101:0] regions_end;
    reg [RW-1:0] range_count, scan_index;
    (* ramstyle = "M20K", nomem2reg *) reg [32:0] range_base [0:RANGES-1];
    (* ramstyle = "M20K", nomem2reg *) reg [33:0] range_end [0:RANGES-1];
    (* ramstyle = "M20K", nomem2reg *) reg [10:0] range_owner [0:RANGES-1];
    reg [32:0] candidate_base, prior_base;
    reg [33:0] candidate_end, prior_end;
    reg [10:0] prior_owner;
    reg scan_loaded;
    integer i;

    function automatic [511:0] visible_descriptor(
      input [511:0] value, input [15:0] mask);
      integer word_index;
      begin
        for (word_index=0;word_index<16;word_index=word_index+1)
          visible_descriptor[32*word_index+:32]=
            mask[word_index] ? value[32*word_index+:32] : 32'd0;
      end
    endfunction

    wire native_mode=(ht2_mode[1:0]==1 || ht2_mode[1:0]==2) &&
      ht2_mode[3:2]!=3;
    wire busy=state!=IDLE;
    wire available=rst_n && !annul && !invalidate;
    wire can_write=!operation_busy && quiescent;
    wire cfg_transfer=cfg_valid && cfg_ready;
    wire descriptor_transfer=desc_req_valid && desc_req_ready;
    wire [8:0] cfg_index=9'((cfg_addr-16'h1000) >> 6);
    wire descriptor_address=cfg_addr>=16'h1000 &&
      {1'b0,cfg_addr}<17'(16'h1000+64*ENTRIES);
    wire [63:0] configured_extent=ht2_mode[5] ? INT8_EXTENT : BF16_EXTENT;
    wire [33:0] configured_end={1'b0,shadow_base}+{1'b0,shadow_length};
    wire [AW-1:0] read_address=AW'((active_bank ? ENTRIES : 0)+desc_req_index);
    wire [AW-1:0] write_address=AW'((active_bank ? 0 : ENTRIES)+index);
    wire check_ready, check_valid, check_error;
    wire [1:0] check_regions;
    wire [98:0] check_bases;
    wire [101:0] check_ends;
    wire overlap=candidate_base<prior_end && prior_base<candidate_end;
    wire embedding_alias=index==1 && part==0 && prior_owner==0 &&
      descriptor==embedding_descriptor;
    wire validation_abort=annul || invalidate || validated_mode!=ht2_mode;

    anvil_q2_ht2_descriptor_check #(
      .NUM_LAYERS(NUM_LAYERS),.HIDDEN_SIZE(HIDDEN_SIZE),
      .INTERMEDIATE_SIZE(INTERMEDIATE_SIZE),.NUM_Q_HEADS(NUM_Q_HEADS),
      .NUM_KV_HEADS(NUM_KV_HEADS),.HEAD_DIM(HEAD_DIM),.GROUP_SIZE(GROUP_SIZE),
      .VOCAB_SIZE(VOCAB_SIZE),.MAX_SEQ_LEN(MAX_SEQ_LEN)
    ) descriptor_check (
      .clk(clk),.rst_n(rst_n),.annul(validation_abort),
      .s_valid(available && state==CHECK_SEND),.s_ready(check_ready),
      .s_descriptor(descriptor),.s_index(index),.s_mode(validated_mode),
      .m_valid(check_valid),.m_ready(available && state==CHECK_WAIT),
      .m_error(check_error),.m_regions(check_regions),
      .m_region_base(check_bases),.m_region_end(check_ends)
    );

    assign cfg_ready=available && !busy && !response_valid;
    assign cfg_rsp_valid=rst_n && response_valid;
    assign cfg_rdata=cfg_rsp_valid ? response_data : 32'd0;
    assign cfg_error=cfg_rsp_valid && response_error;
    assign validating=rst_n && busy;
    assign model_loaded=available && loaded && committed_mode==ht2_mode;
    assign configuration_changed=available && changed;
    assign kv_base=model_loaded ? committed_base : 33'd0;
    assign kv_length=model_loaded ? committed_length : 33'd0;
    assign desc_req_ready=available && model_loaded && !busy &&
      (!descriptor_valid || desc_rsp_ready);
    assign desc_rsp_valid=available && descriptor_valid;
    assign desc_rsp_data=desc_rsp_valid && !descriptor_error ? descriptor_data : 512'd0;
    assign desc_rsp_error=desc_rsp_valid && descriptor_error;

    always @(posedge clk) begin
      if (cfg_transfer && cfg_write && can_write && cfg_addr[1:0]==0 &&
          descriptor_address)
        shadow[cfg_index][cfg_addr[5:2]*32+:32]<=cfg_wdata;
      if (available && state==LOAD)
        descriptor<=visible_descriptor(shadow[index],initialized[index]);
      if (available && state==COPY && !validation_abort)
        committed[write_address]<=visible_descriptor(shadow[index],initialized[index]);
      if (descriptor_transfer && desc_req_index<ENTRIES)
        descriptor_data<=committed[read_address];
      if (available && state==START) begin
        range_base[0]<=shadow_base; range_end[0]<=configured_end;
        range_owner[0]<=11'h7ff;
      end
      if (available && state==SCAN && !scan_loaded && scan_index<range_count) begin
        prior_base<=range_base[scan_index]; prior_end<=range_end[scan_index];
        prior_owner<=range_owner[scan_index];
      end
      if (available && state==APPEND) begin
        range_base[range_count]<=candidate_base; range_end[range_count]<=candidate_end;
        range_owner[range_count]<={index,part};
      end
    end

    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        state<=IDLE; loaded<=0; active_bank<=0; changed<=0;
        response_valid<=0; response_error<=0; response_data<=0;
        shadow_base<=0; shadow_length<=0; committed_base<=0; committed_length<=0;
        shadow_weight<=0; shadow_cache<=0; validated_mode<=0; committed_mode<=0;
        embedding_descriptor<=0; descriptor_valid<=0; descriptor_error<=0;
        index<=0; part<=0; region_count<=0; regions_base<=0; regions_end<=0;
        range_count<=0; scan_index<=0; candidate_base<=0; candidate_end<=0;
        scan_loaded<=0;
        for (i=0;i<ENTRIES;i=i+1) initialized[i]<=0;
      end else begin
        changed<=0;
        if (response_valid && cfg_rsp_ready) response_valid<=0;
        if (descriptor_valid && desc_rsp_ready) descriptor_valid<=0;
        if (descriptor_transfer) begin
          descriptor_valid<=1; descriptor_error<=desc_req_index>=ENTRIES;
        end
        if (invalidate || (loaded && committed_mode!=ht2_mode)) begin
          loaded<=0; descriptor_valid<=0; changed<=1;
        end
        if (annul) descriptor_valid<=0;
        if (busy && validation_abort) begin
          state<=IDLE; response_valid<=1;
          response_error<=1; response_data<=0;
        end else if (!annul) case (state)
          IDLE: if (cfg_transfer) begin
            response_valid<=1; response_error<=0; response_data<=0;
            if (cfg_addr[1:0]!=0) response_error<=1;
            else if (cfg_write) begin
              if (!can_write || !native_mode) response_error<=1;
              else if (descriptor_address)
                initialized[cfg_index][cfg_addr[5:2]]<=1;
              else case (cfg_addr)
                16'h0008: case (cfg_wdata)
                  0: begin end
                  1: begin
                    state<=START; index<=0; response_valid<=0;
                    validated_mode<=ht2_mode;
                  end
                  2: begin loaded<=0; changed<=1; descriptor_valid<=0; end
                  default: response_error<=1;
                endcase
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
            end else if (descriptor_address)
              response_data<=initialized[cfg_index][cfg_addr[5:2]] ?
                shadow[cfg_index][cfg_addr[5:2]*32+:32] : 32'd0;
            else case (cfg_addr)
              16'h0000: response_data<=32'h41513248;
              16'h0004: response_data<=32'h02050002;
              16'h0008: response_data<=0;
              16'h000c: response_data<={28'd0,ddr_ready,sticky_fault,operation_busy,
                model_loaded};
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
            if (!native_mode || shadow_base[5:0]!=0 ||
                {31'd0,shadow_length}<configured_extent ||
                configured_end>34'h200000000) begin
              state<=IDLE; response_valid<=1; response_error<=1; response_data<=0;
            end else begin range_count<=1; state<=LOAD; end
          end
          LOAD: state<=CHECK_SEND;
          CHECK_SEND: if (check_ready) state<=CHECK_WAIT;
          CHECK_WAIT: if (check_valid) begin
            if (check_error) begin
              state<=IDLE; response_valid<=1; response_error<=1; response_data<=0;
            end else begin
              if (index==0) embedding_descriptor<=descriptor;
              regions_base<=check_bases; regions_end<=check_ends;
              region_count<=check_regions; part<=0;
              if (check_regions==0) state<=NEXT;
              else state<=REGION;
            end
          end
          REGION: begin
            candidate_base<=regions_base[33*part+:33];
            candidate_end<=regions_end[34*part+:34];
            scan_index<=0; scan_loaded<=0; state<=SCAN;
          end
          SCAN: begin
            if (scan_index==range_count) state<=APPEND;
            else if (!scan_loaded) scan_loaded<=1;
            else if (overlap && !embedding_alias) begin
              state<=IDLE; response_valid<=1; response_error<=1; response_data<=0;
            end else begin scan_index<=scan_index+1'b1; scan_loaded<=0; end
          end
          APPEND: begin
            range_count<=range_count+1'b1;
            if (part+2'd1<region_count) begin part<=part+2'd1; state<=REGION; end
            else state<=NEXT;
          end
          NEXT: begin
            if (index+9'd1<ENTRIES) begin index<=index+9'd1; state<=LOAD; end
            else begin index<=0; state<=COPY; end
          end
          COPY: begin
            if (index+9'd1<ENTRIES) index<=index+9'd1;
            else begin
              state<=IDLE; response_valid<=1; response_error<=0; response_data<=0;
              loaded<=1; active_bank<=!active_bank; changed<=1; descriptor_valid<=0;
              committed_base<=shadow_base; committed_length<=shadow_length;
              committed_mode<=validated_mode;
            end
          end
          default: begin
            state<=IDLE; response_valid<=1; response_error<=1; response_data<=0;
          end
        endcase
      end
    end
  end endgenerate
endmodule
