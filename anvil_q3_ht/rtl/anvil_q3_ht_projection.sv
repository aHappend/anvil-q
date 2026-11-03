module anvil_q3_ht_projection #(
  parameter BANKS=16, TILE_K=128, TILE_ROWS=8, TILE_SLOTS=4,
  parameter NUM_LAYERS=36, HIDDEN_SIZE=2048, INTERMEDIATE_SIZE=11008,
  parameter NUM_Q_HEADS=16, NUM_KV_HEADS=2, HEAD_DIM=128,
  parameter GROUP_SIZE=128, VOCAB_SIZE=151936, MAX_SEQ_LEN=32768,
  localparam SB=(BANKS==1 || BANKS==2 || BANKS==4 ||
    BANKS==8 || BANKS==16) ? BANKS : 1,
  localparam TK=(TILE_K==16 || TILE_K==32 || TILE_K==64 ||
    TILE_K==128) ? TILE_K : 16,
  localparam TR=TILE_ROWS>=1 && TILE_ROWS<=8 ? TILE_ROWS : 1,
  localparam TS=TILE_SLOTS>=2 && TILE_SLOTS<=4 ? TILE_SLOTS : 2,
  localparam GS=GROUP_SIZE>=8 && GROUP_SIZE<=128 &&
    (GROUP_SIZE&(GROUP_SIZE-1))==0 ? GROUP_SIZE : 8,
  localparam ACT_WORDS=TK>>4,
  localparam ACT_AW=ACT_WORDS>1 ? $clog2(ACT_WORDS) : 1
) (
  input wire clk, rst_n, flush, cmd_valid,
  output wire cmd_ready,
  input wire [31:0] cmd_epoch, cmd_layer, cmd_pos,
  input wire [2:0] cmd_proj,
  output wire done, error, idle,
  output wire mem_req_valid, mem_req_write,
  input wire mem_req_ready,
  output wire [3:0] mem_req_kind,
  output wire [31:0] mem_req_layer, mem_req_row, mem_req_col, mem_req_wdata,
  output wire [2:0] mem_req_proj,
  input wire mem_rsp_valid, mem_rsp_error,
  output wire mem_rsp_ready,
  input wire [31:0] mem_rsp_rdata,
  output wire prefetch_valid,
  input wire prefetch_ready,
  output wire [32:0] prefetch_address,
  output wire [31:0] prefetch_beats,
  output wire [159:0] prefetch_meta,
  input wire prefetch_data_valid,
  output wire prefetch_data_ready,
  input wire [511:0] prefetch_data,
  input wire [159:0] prefetch_data_meta,
  input wire prefetch_data_last, prefetch_data_error, prefetch_idle, prefetch_fault,
  output wire tile_alloc_valid,
  input wire tile_alloc_ready,
  input wire [1:0] tile_alloc_slot,
  output wire [31:0] tile_alloc_entries,
  output wire [159:0] tile_alloc_meta,
  output wire tile_write_valid,
  input wire tile_write_ready,
  output wire [1:0] tile_write_slot,
  output wire [3:0] tile_write_bank,
  output wire [31:0] tile_write_entry,
  output wire [159:0] tile_write_meta,
  output reg [63:0] tile_write_q, tile_write_z,
  output reg [255:0] tile_write_scale,
  output reg [15:0] tile_write_mask,
  output wire [511:0] tile_write_activation,
  output wire tile_seal_valid,
  input wire tile_seal_ready,
  output wire [1:0] tile_seal_slot,
  output wire [159:0] tile_seal_meta,
  output wire tile_activate_valid,
  input wire tile_activate_ready,
  output wire [1:0] tile_activate_slot,
  output wire [159:0] tile_activate_meta,
  input wire tile_operand_valid,
  output wire tile_operand_ready,
  input wire [SB*64-1:0] tile_operand_q, tile_operand_z,
  input wire [SB*256-1:0] tile_operand_scale,
  input wire [SB*16-1:0] tile_operand_mask,
  input wire [511:0] tile_operand_activation,
  input wire [159:0] tile_operand_meta,
  input wire [31:0] tile_operand_entry,
  input wire tile_operand_last,
  input wire [TS*2-1:0] tile_slot_states,
  input wire tile_idle, tile_fault,
  output wire [SB-1:0] operand_valid,
  input wire [SB-1:0] operand_ready,
  output wire [SB*64-1:0] operand_q, operand_z,
  output wire [SB*256-1:0] operand_scale,
  output wire [SB*512-1:0] operand_activation,
  output wire [SB*16-1:0] operand_mask,
  output wire [SB*160-1:0] operand_meta,
  input wire [SB-1:0] result_valid,
  output reg [SB-1:0] result_ready,
  input wire [SB*128-1:0] result_sum,
  input wire [SB*160-1:0] result_meta,
  input wire tensor_idle, tensor_fault
);
  localparam LEGAL=SB==BANKS && TK==TILE_K && TR==TILE_ROWS &&
    TS==TILE_SLOTS && GS==GROUP_SIZE && HIDDEN_SIZE>0 && INTERMEDIATE_SIZE>0;
  localparam PACKETS=TK>>4, PSHIFT=$clog2(PACKETS), GSHIFT=$clog2(GS);
  localparam GROUPS=TK<GS ? 1 : TK>>GSHIFT;
  localparam ENTRIES=TR*PACKETS;
  localparam IDLE=0, MAP_REQUEST=1, MAP_RESPONSE=2, LOAD_REQUEST=3;
  localparam LOAD_RESPONSE=4, RUN=5, COMPLETE=6, FAULTED=7;
  localparam P_ALLOC=0, P_GROUP_ADDRESS=1, P_SPAN_COMMAND=2, P_SPAN_DATA=3;
  localparam P_SPAN_SAVE=4, P_WEIGHT_ADDRESS=5, P_RAW_READ=6, P_RAW_WRITE=7;
  localparam P_SEAL=8, P_FINISHED=9, P_SCALE_ADDRESS=10;
  localparam P_ACT_REQUEST=11, P_ACT_RESPONSE=12;
  localparam ZERO_SPAN=0, SCALE_SPAN=1, WEIGHT_SPAN=2;
  localparam W_IDLE=0, W_BIAS_REQUEST=1, W_BIAS_RESPONSE=2, W_ADD=3;
  localparam W_ADD_WAIT=4, W_ROUND=5, W_WRITE_REQUEST=6, W_WRITE_RESPONSE=7;
  reg [2:0] state;
  reg [3:0] producer;
  reg [2:0] writer;
  reg failed;
  reg [31:0] epoch, layer, position, inputs, outputs, source_slot, target_slot;
  reg [2:0] projection;
  reg [32:0] qweight_base, qzeros_base, scales_base;
  reg [31:0] load_index, output_count;
  reg [31:0] fill_row, fill_input, group_index, group_first, group_last;
  reg [31:0] weight_index, write_entry;
  reg [3:0] write_bank;
  reg [1:0] fill_slot;
  reg [159:0] fill_meta;
  reg [1:0] span_kind;
  reg [63:0] span_start, span_end;
  reg [31:0] span_beats, span_index;
  reg [2559:0] span_buffer;
  reg [543:0] zero_group;
  (* nomem2reg *) reg [1:0] queue_slots [0:TS-1];
  (* nomem2reg *) reg [159:0] queue_meta [0:TS-1];
  reg [1:0] queue_head, queue_tail;
  reg [2:0] queue_count;
  reg consuming;
  reg [SB-1:0] sent;
  reg [3:0] result_pointer;
  reg [31:0] result_row, rounded;
  reg signed [127:0] row_sum;
  reg signed [31:0] bias;
  wire running=rst_n && LEGAL && !flush && !failed;
  wire map_ready, map_valid, map_error;
  wire [31:0] map_inputs, map_outputs;
  wire [32:0] map_qweight, map_qzeros, map_scales;
  wire [31:0] block_rows=outputs-fill_row<SB*TR ? outputs-fill_row : SB*TR;
  wire [31:0] packed_words=({29'd0,fill_row[2:0]}+block_rows+7)>>3;
  wire [31:0] packed_stride=(outputs+7)>>3;
  wire [31:0] actual_k=inputs-fill_input<TK ? inputs-fill_input : TK;
  wire [31:0] group_offset=group_index-group_first;
  wire [63:0] zero_address={31'd0,qzeros_base}+
    (64'(group_index)*64'(packed_stride)+64'(fill_row>>3))*4;
  wire [63:0] scale_address={31'd0,scales_base}+
    (64'(group_index)*64'(outputs)+64'(fill_row))*2;
  wire [63:0] weight_address={31'd0,qweight_base}+
    (64'(fill_input+weight_index)*64'(packed_stride)+64'(fill_row>>3))*4;
  wire [2559:0] normalized_span=span_buffer>>{span_start[5:0],3'd0};
  wire [63:0] aligned_end=(span_end+63)&64'hffffffffffffffc0;
  wire span_bad=span_end<=span_start || aligned_end>64'h60000000 &&
    span_kind==WEIGHT_SPAN || aligned_end>64'h64000000 && span_kind==ZERO_SPAN ||
    aligned_end>64'h6c000000 && span_kind==SCALE_SPAN || span_beats==0 ||
    span_beats>5 || span_start>=64'h200000000;
  wire [159:0] allocation_meta={24'd0,2'b00,3'd0,fill_input,fill_row,projection,layer,epoch};
  wire allocate=tile_alloc_valid && tile_alloc_ready;
  wire release_slot=tile_operand_valid && tile_operand_ready && tile_operand_last;
  wire [1:0] next_slot=queue_slots[queue_head];
  wire activate=tile_activate_valid && tile_activate_ready;
  wire [31:0] read_packet=tile_operand_entry&(PACKETS-1);
  wire [31:0] read_context=tile_operand_entry>>PSHIFT;
  wire [31:0] activation_base=tile_operand_meta[130:99]+(read_packet<<4);
  wire [31:0] raw_packet=write_entry&(PACKETS-1);
  wire [31:0] raw_context=write_entry>>PSHIFT;
  wire [31:0] raw_input=fill_input+(raw_packet<<4);
  wire [31:0] raw_group0=(raw_input>>GSHIFT)-group_first;
  wire [31:0] raw_group1=((raw_input+8)>>GSHIFT)-group_first;
  wire raw_read=running && state==RUN && producer==P_RAW_READ;
  wire save_weight=running && state==RUN && producer==P_SPAN_SAVE && span_kind==WEIGHT_SPAN;
  wire save_group=running && state==RUN && producer==P_SPAN_SAVE && span_kind==SCALE_SPAN;
  wire [31:0] materialized_row=fill_row+raw_context*SB+{28'd0,write_bank};
  wire [31:0] row_offset=raw_context*SB+{28'd0,write_bank};
  wire [31:0] packed_bit=((({29'd0,fill_row[2:0]}+row_offset)>>3)<<5)+
    {27'd0,anvil_q3_pkg::awq_lane_shift(materialized_row[2:0])};
  wire [2591:0] group_data0, group_data1;
  wire [543:0] raw_q [0:15];
  wire [31:0] act_q [0:15];
  wire [SB-1:0] finished_banks;
  reg scalar_pending, scalar_waiting, scalar_load;
  reg scalar_write;
  reg [3:0] scalar_kind;
  reg [31:0] scalar_layer, scalar_row, scalar_col, scalar_wdata;
  reg [2:0] scalar_proj;
  wire load_request=state==RUN && producer==P_ACT_REQUEST;
  wire write_request=state==RUN && (writer==W_BIAS_REQUEST || writer==W_WRITE_REQUEST);
  wire scalar_available=!scalar_pending && !scalar_waiting;
  wire load_issue=running && scalar_available && load_request && !write_request;
  wire write_issue=running && scalar_available && write_request;
  wire load_response=scalar_waiting && scalar_load && mem_rsp_valid;
  wire write_response=scalar_waiting && !scalar_load && mem_rsp_valid;
  wire scalar_fault=mem_rsp_valid && (!scalar_waiting || mem_rsp_error ||
    (write_response && writer==W_BIAS_RESPONSE &&
      (mem_rsp_rdata[31:16]!=0 || anvil_q3_pkg::f16_invalid(mem_rsp_rdata[15:0]))));
  wire add_ready, add_valid, add_error;
  wire signed [127:0] biased_sum;
  wire signed [31:0] converted_bias=anvil_q3_pkg::f16_q16(mem_rsp_rdata[15:0]);
  wire signed [31:0] rounded_sum=anvil_q3_pkg::round_q32_to_q16(row_sum);
  integer offset, candidate, selected, lane;
  reg [2591:0] selected_group;
  reg [543:0] shifted_q, shifted_z;
  reg [2047:0] shifted_scale;

  generate if (!LEGAL) begin: invalid_parameters
    initial $fatal(1,"ANVIL_Q3_HT PARAMETER ERROR: packed projection parameters");
  end endgenerate
  assign cmd_ready=running && state==IDLE;
  assign done=rst_n && !flush && state==COMPLETE;
  assign error=done && failed;
  assign idle=running && state==IDLE;
  assign mem_req_valid=running && scalar_pending;
  assign mem_req_write=mem_req_valid && scalar_write;
  assign mem_req_kind=mem_req_valid ? scalar_kind : 4'd0;
  assign mem_req_layer=mem_req_valid ? scalar_layer : 32'd0;
  assign mem_req_proj=mem_req_valid ? scalar_proj : 3'd0;
  assign mem_req_row=mem_req_valid ? scalar_row : 32'd0;
  assign mem_req_col=mem_req_valid ? scalar_col : 32'd0;
  assign mem_req_wdata=mem_req_write ? scalar_wdata : 32'd0;
  assign mem_rsp_ready=running && scalar_waiting;
  assign prefetch_valid=running && state==RUN && producer==P_SPAN_COMMAND && !span_bad;
  assign prefetch_address=prefetch_valid ? {span_start[32:6],6'd0} : 33'd0;
  assign prefetch_beats=prefetch_valid ? span_beats : 32'd0;
  assign prefetch_meta=prefetch_valid ? fill_meta : 160'd0;
  assign prefetch_data_ready=running && state==RUN && producer==P_SPAN_DATA;
  assign tile_alloc_valid=running && state==RUN && producer==P_ALLOC && queue_count<TS;
  assign tile_alloc_entries=tile_alloc_valid ? ENTRIES : 32'd0;
  assign tile_alloc_meta=tile_alloc_valid ? allocation_meta : 160'd0;
  assign tile_write_valid=running && state==RUN && producer==P_RAW_WRITE;
  assign tile_write_slot=tile_write_valid ? fill_slot : 2'd0;
  assign tile_write_bank=tile_write_valid ? write_bank : 4'd0;
  assign tile_write_entry=tile_write_valid ? write_entry : 32'd0;
  assign tile_write_meta=tile_write_valid ? fill_meta : 160'd0;
  assign tile_seal_valid=running && state==RUN && producer==P_SEAL;
  assign tile_seal_slot=tile_seal_valid ? fill_slot : 2'd0;
  assign tile_seal_meta=tile_seal_valid ? fill_meta : 160'd0;
  assign tile_activate_valid=running && state==RUN && !consuming && queue_count!=0 &&
    tile_slot_states[next_slot*2+:2]==2'd2;
  assign tile_activate_slot=tile_activate_valid ? next_slot : 2'd0;
  assign tile_activate_meta=tile_activate_valid ? queue_meta[queue_head] : 160'd0;
  assign tile_operand_ready=running && state==RUN && (&finished_banks);

  genvar a, b;
  generate for (a=0;a<16;a=a+1) begin: activation_lanes
    (* ramstyle="M20K", nomem2reg *) reg [31:0] memory [0:ACT_WORDS-1];
    reg [31:0] read_data;
    assign act_q[a]=read_data;
    always @(posedge clk) begin
      if (running && load_response && !mem_rsp_error &&
          load_index[3:0]==a) memory[ACT_AW'(load_index>>4)]<=mem_rsp_rdata;
      if (raw_read) read_data<=memory[ACT_AW'(raw_packet)];
    end
    assign tile_write_activation[a*32+:32]=tile_write_valid && raw_input+a<inputs ?
      act_q[a] : 32'd0;
  end
  for (a=0;a<16;a=a+1) begin: packed_lanes
    (* ramstyle="M20K", nomem2reg *) reg [543:0] memory [0:PACKETS-1];
    reg [543:0] read_data;
    assign raw_q[a]=read_data;
    always @(posedge clk) begin
      if (save_weight && weight_index[3:0]==a)
        memory[weight_index>>4]<=normalized_span[543:0];
      if (raw_read) read_data<=memory[raw_packet];
    end
  end
  for (a=0;a<2;a=a+1) begin: group_copies
    (* ramstyle="M20K", nomem2reg *) reg [2591:0] memory [0:GROUPS-1];
    reg [2591:0] read_data;
    if (a==0) assign group_data0=read_data;
    else assign group_data1=read_data;
    always @(posedge clk) begin
      if (save_group) memory[group_offset]<={normalized_span[2047:0],zero_group};
      if (raw_read) read_data<=memory[a==0 ? raw_group0 : raw_group1];
    end
  end
  for (b=0;b<SB;b=b+1) begin: tensor_banks
    wire [31:0] row=tile_operand_meta[98:67]+read_context*SB+b;
    wire active_row=row<outputs && activation_base<inputs;
    wire [159:0] metadata={24'd0,(activation_base+16>=inputs),
      (activation_base==0),3'(read_context),activation_base,row,
      tile_operand_meta[66:0]};
    assign operand_valid[b]=running && state==RUN && tile_operand_valid &&
      !sent[b] && active_row;
    assign finished_banks[b]=!active_row || sent[b] || operand_ready[b];
    assign operand_q[b*64+:64]=operand_valid[b] ? tile_operand_q[b*64+:64] : 64'd0;
    assign operand_z[b*64+:64]=operand_valid[b] ? tile_operand_z[b*64+:64] : 64'd0;
    assign operand_scale[b*256+:256]=operand_valid[b] ? tile_operand_scale[b*256+:256] : 256'd0;
    assign operand_mask[b*16+:16]=operand_valid[b] ? tile_operand_mask[b*16+:16] : 16'd0;
    assign operand_meta[b*160+:160]=operand_valid[b] ? metadata : 160'd0;
    for (a=0;a<16;a=a+1) begin: activation_broadcast
      assign operand_activation[b*512+a*32+:32]=operand_valid[b] &&
        activation_base+a<inputs ? tile_operand_activation[a*32+:32] : 32'd0;
    end
  end endgenerate

  always @* begin
    tile_write_q=0; tile_write_z=0; tile_write_scale=0; tile_write_mask=0;
    selected_group=0; shifted_q=0; shifted_z=0; shifted_scale=0;
    for (lane=0;lane<16;lane=lane+1) begin
      selected_group=lane<8 ? group_data0 : group_data1;
      shifted_q=raw_q[lane]>>packed_bit;
      shifted_z=selected_group[543:0]>>packed_bit;
      shifted_scale=selected_group[2591:544]>>(row_offset<<4);
      if (tile_write_valid && materialized_row<outputs && raw_input+lane<inputs) begin
        tile_write_q[lane*4+:4]=shifted_q[3:0];
        tile_write_z[lane*4+:4]=shifted_z[3:0];
        tile_write_scale[lane*16+:16]=shifted_scale[15:0];
        tile_write_mask[lane]=1;
      end
    end
  end
  always @* begin
    selected=-1; candidate=0; result_ready=0;
    for (offset=0;offset<SB;offset=offset+1) begin
      candidate=result_pointer+offset;
      if (candidate>=SB) candidate=candidate-SB;
      if (running && state==RUN && writer==W_IDLE &&
          selected<0 && result_valid[candidate]) selected=candidate;
    end
    if (selected>=0) result_ready[selected]=1;
  end

  anvil_q3_ht_image_map #(
    .NUM_LAYERS(NUM_LAYERS),.HIDDEN_SIZE(HIDDEN_SIZE),.INTERMEDIATE_SIZE(INTERMEDIATE_SIZE),
    .NUM_Q_HEADS(NUM_Q_HEADS),.NUM_KV_HEADS(NUM_KV_HEADS),.HEAD_DIM(HEAD_DIM),
    .GROUP_SIZE(GROUP_SIZE),.VOCAB_SIZE(VOCAB_SIZE),.MAX_SEQ_LEN(MAX_SEQ_LEN)
  ) image_map (
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .req_valid(running && state==MAP_REQUEST),.req_ready(map_ready),
    .req_write(1'b0),.req_kind(4'd1),.req_layer(layer),
    .req_row(32'd0),.req_col(32'd0),.req_proj(projection),
    .rsp_valid(map_valid),.rsp_ready(state==MAP_RESPONSE),.rsp_error(map_error),
    .rsp_scratch(),.rsp_address(),.rsp_bytes(),
    .rsp_inputs(map_inputs),.rsp_outputs(map_outputs),
    .rsp_qweight_base(map_qweight),.rsp_qzeros_base(map_qzeros),.rsp_scales_base(map_scales)
  );
  anvil_q3_add128 bias_accumulator (
    .clk(clk),.rst_n(rst_n),.flush(flush || failed),
    .in_valid(running && state==RUN && writer==W_ADD),.in_ready(add_ready),
    .in_a(row_sum),.in_b({{80{bias[31]}},bias,16'd0}),
    .out_valid(add_valid),.out_ready(1'b1),.out_error(add_error),.out_sum(biased_sum)
  );

  always @(posedge clk) begin
    if (allocate) begin
      queue_slots[queue_tail]<=tile_alloc_slot;
      queue_meta[queue_tail]<=allocation_meta;
    end
  end
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; producer<=P_ALLOC; writer<=W_IDLE; failed<=0;
      epoch<=0; layer<=0; position<=0; projection<=0; inputs<=0; outputs<=0;
      source_slot<=0; target_slot<=0; qweight_base<=0; qzeros_base<=0; scales_base<=0;
      load_index<=0; output_count<=0; fill_row<=0; fill_input<=0;
      group_index<=0; group_first<=0; group_last<=0; weight_index<=0;
      write_entry<=0; write_bank<=0; fill_slot<=0; fill_meta<=0;
      span_kind<=0; span_start<=0; span_end<=0; span_beats<=0; span_index<=0;
      span_buffer<=0; zero_group<=0; queue_head<=0; queue_tail<=0; queue_count<=0;
      consuming<=0; sent<=0; result_pointer<=0;
      result_row<=0; rounded<=0; row_sum<=0; bias<=0;
      scalar_pending<=0; scalar_waiting<=0; scalar_load<=0; scalar_write<=0;
      scalar_kind<=0; scalar_layer<=0; scalar_row<=0; scalar_col<=0;
      scalar_wdata<=0; scalar_proj<=0;
    end else if (flush) begin
      state<=IDLE; producer<=P_ALLOC; writer<=W_IDLE; failed<=0;
      queue_head<=0; queue_tail<=0; queue_count<=0; consuming<=0;
      sent<=0; scalar_pending<=0; scalar_waiting<=0;
    end else if (!failed && (scalar_fault || tensor_fault || tile_fault || prefetch_fault ||
        (add_valid && add_error) ||
        (state==RUN && producer==P_SPAN_COMMAND && span_bad) ||
        (prefetch_data_valid && prefetch_data_ready &&
          (prefetch_data_error || prefetch_data_meta!=fill_meta ||
           prefetch_data_last!=(span_index+1==span_beats))))) begin
      failed<=1; state<=COMPLETE;
    end else if (running || (rst_n && !flush && state==COMPLETE)) begin
      if (allocate) begin
        queue_tail<=queue_tail==TS-1 ? 0 : queue_tail+1'b1;
        fill_slot<=tile_alloc_slot; fill_meta<=allocation_meta;
      end
      if (release_slot) begin
        queue_head<=queue_head==TS-1 ? 0 : queue_head+1'b1;
        consuming<=0;
      end
      case ({allocate,release_slot})
        2'b10: queue_count<=queue_count+1'b1;
        2'b01: queue_count<=queue_count-1'b1;
        default: begin end
      endcase
      if (activate) consuming<=1;
      sent<=sent|(operand_valid&operand_ready);
      if (tile_operand_valid && tile_operand_ready) sent<=0;
      if (load_issue || write_issue) begin
        scalar_pending<=1;
        scalar_load<=load_issue;
        scalar_write<=write_issue && writer==W_WRITE_REQUEST;
        scalar_kind<=write_issue && writer==W_BIAS_REQUEST ? 4'd4 : 4'd8;
        scalar_layer<=write_issue && writer==W_BIAS_REQUEST ? layer : 32'd0;
        scalar_proj<=write_issue && writer==W_BIAS_REQUEST ? projection : 3'd0;
        scalar_row<=load_issue ? source_slot : writer==W_BIAS_REQUEST ? 32'd0 : target_slot;
        scalar_col<=load_issue ? fill_input+load_index : result_row;
        scalar_wdata<=write_issue && writer==W_WRITE_REQUEST ? rounded : 32'd0;
      end
      if (mem_req_valid && mem_req_ready) begin scalar_pending<=0; scalar_waiting<=1; end
      if (mem_rsp_valid && mem_rsp_ready) scalar_waiting<=0;
      case (state)
        IDLE: if (cmd_valid) begin
          epoch<=cmd_epoch; layer<=cmd_layer; position<=cmd_pos; projection<=cmd_proj;
          load_index<=0; output_count<=0; fill_row<=0; fill_input<=0;
          producer<=P_ALLOC; writer<=W_IDLE; result_pointer<=0;
          case (cmd_proj)
            0: begin source_slot<=1; target_slot<=2; end
            1: begin source_slot<=1; target_slot<=3; end
            2: begin source_slot<=1; target_slot<=4; end
            3: begin source_slot<=5; target_slot<=6; end
            4: begin source_slot<=8; target_slot<=9; end
            5: begin source_slot<=8; target_slot<=10; end
            default: begin source_slot<=11; target_slot<=12; end
          endcase
          if (cmd_layer>=NUM_LAYERS || cmd_pos>=MAX_SEQ_LEN || cmd_proj>6) begin
            failed<=1; state<=COMPLETE;
          end else state<=MAP_REQUEST;
        end
        MAP_REQUEST: if (map_ready) state<=MAP_RESPONSE;
        MAP_RESPONSE: if (map_valid) begin
          if (map_error) begin failed<=1; state<=COMPLETE; end
          else begin
            inputs<=map_inputs; outputs<=map_outputs;
            qweight_base<=map_qweight; qzeros_base<=map_qzeros; scales_base<=map_scales;
            state<=RUN;
          end
        end
        RUN: begin
          case (producer)
            P_ALLOC: if (allocate) begin
              group_first<=fill_input>>GSHIFT;
              group_index<=fill_input>>GSHIFT;
              group_last<=(fill_input+actual_k-1)>>GSHIFT;
              load_index<=0; producer<=P_ACT_REQUEST;
            end
            P_ACT_REQUEST: if (load_issue) producer<=P_ACT_RESPONSE;
            P_ACT_RESPONSE: if (load_response) begin
              if (load_index+1==actual_k) producer<=P_GROUP_ADDRESS;
              else begin load_index<=load_index+1'b1; producer<=P_ACT_REQUEST; end
            end
            P_GROUP_ADDRESS: begin
              span_kind<=ZERO_SPAN; span_start<=zero_address;
              span_end<=zero_address+64'(packed_words)*4;
              span_beats<=32'((({58'd0,zero_address[5:0]}+64'(packed_words)*4)+63)>>6);
              producer<=P_SPAN_COMMAND;
            end
            P_SCALE_ADDRESS: begin
              span_kind<=SCALE_SPAN; span_start<=scale_address;
              span_end<=scale_address+64'(block_rows)*2;
              span_beats<=32'((({58'd0,scale_address[5:0]}+64'(block_rows)*2)+63)>>6);
              producer<=P_SPAN_COMMAND;
            end
            P_WEIGHT_ADDRESS: begin
              if (weight_index>=actual_k) begin
                write_entry<=0; write_bank<=0; producer<=P_RAW_READ;
              end else begin
                span_kind<=WEIGHT_SPAN; span_start<=weight_address;
                span_end<=weight_address+64'(packed_words)*4;
                span_beats<=32'((({58'd0,weight_address[5:0]}+64'(packed_words)*4)+63)>>6);
                producer<=P_SPAN_COMMAND;
              end
            end
            P_SPAN_COMMAND: if (prefetch_ready) begin
              span_buffer<=0; span_index<=0; producer<=P_SPAN_DATA;
            end
            P_SPAN_DATA: if (prefetch_data_valid) begin
              span_buffer[span_index*512+:512]<=prefetch_data;
              if (prefetch_data_last) producer<=P_SPAN_SAVE;
              else span_index<=span_index+1'b1;
            end
            P_SPAN_SAVE: case (span_kind)
              ZERO_SPAN: begin zero_group<=normalized_span[543:0]; producer<=P_SCALE_ADDRESS; end
              SCALE_SPAN: if (group_index==group_last) begin
                weight_index<=0; producer<=P_WEIGHT_ADDRESS;
              end else begin group_index<=group_index+1'b1; producer<=P_GROUP_ADDRESS; end
              default: begin weight_index<=weight_index+1'b1; producer<=P_WEIGHT_ADDRESS; end
            endcase
            P_RAW_READ: producer<=P_RAW_WRITE;
            P_RAW_WRITE: if (tile_write_ready) begin
              if (write_bank==SB-1) begin
                write_bank<=0;
                if (write_entry+1==ENTRIES) producer<=P_SEAL;
                else begin write_entry<=write_entry+1'b1; producer<=P_RAW_READ; end
              end else write_bank<=write_bank+1'b1;
            end
            P_SEAL: if (tile_seal_ready) begin
              if (fill_input+TK<inputs) begin fill_input<=fill_input+TK; producer<=P_ALLOC; end
              else begin
                fill_input<=0;
                if (fill_row+SB*TR<outputs) begin fill_row<=fill_row+SB*TR; producer<=P_ALLOC; end
                else producer<=P_FINISHED;
              end
            end
            P_FINISHED: begin end
            default: begin failed<=1; state<=COMPLETE; end
          endcase
          case (writer)
            W_IDLE: if (selected>=0) begin
              row_sum<=result_sum[selected*128+:128];
              result_row<=result_meta[selected*160+67+:32];
              result_pointer<=selected==SB-1 ? 0 : 4'(selected+1);
              if (result_meta[selected*160+:32]!=epoch ||
                  result_meta[selected*160+32+:32]!=layer ||
                  result_meta[selected*160+64+:3]!=projection ||
                  result_meta[selected*160+67+:32]>=outputs ||
                  !result_meta[selected*160+135]) begin
                failed<=1; state<=COMPLETE;
              end else if (projection<3) writer<=W_BIAS_REQUEST;
              else writer<=W_ROUND;
            end
            W_BIAS_REQUEST: if (write_issue) writer<=W_BIAS_RESPONSE;
            W_BIAS_RESPONSE: if (write_response) begin bias<=converted_bias; writer<=W_ADD; end
            W_ADD: if (add_ready) writer<=W_ADD_WAIT;
            W_ADD_WAIT: if (add_valid) begin row_sum<=biased_sum; writer<=W_ROUND; end
            W_ROUND: begin rounded<=rounded_sum; writer<=W_WRITE_REQUEST; end
            W_WRITE_REQUEST: if (write_issue) writer<=W_WRITE_RESPONSE;
            W_WRITE_RESPONSE: if (write_response) begin
              output_count<=output_count+1'b1; writer<=W_IDLE;
            end
            default: begin failed<=1; state<=COMPLETE; end
          endcase
          if (producer==P_FINISHED && queue_count==0 && !consuming &&
              writer==W_IDLE && output_count==outputs &&
              tensor_idle && tile_idle && prefetch_idle) state<=COMPLETE;
        end
        COMPLETE: if (failed) state<=FAULTED; else state<=IDLE;
        FAULTED: begin end
        default: begin failed<=1; state<=COMPLETE; end
      endcase
    end
  end
endmodule
