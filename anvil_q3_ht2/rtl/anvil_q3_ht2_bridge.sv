module anvil_q3_ht2_bridge #(
  parameter NUM_LAYERS=36, HIDDEN_SIZE=2048, INTERMEDIATE_SIZE=11008,
  parameter NUM_Q_HEADS=16, NUM_KV_HEADS=2, HEAD_DIM=128,
  parameter GROUP_SIZE=128, VOCAB_SIZE=151936, MAX_SEQ_LEN=32768,
  parameter CACHE_MODE=1, BANKS=16, TILE_K=128, TILE_ROWS=8, TILE_SLOTS=4,
  parameter QUEUE_DEPTH=3, BURST_BEATS=16, KV_RESIDENT_GROUPS=64
) (
  input wire clk, rst_n, ddr_cal_ready,
  input wire [9:0] csr_address,
  input wire csr_read, csr_write,
  input wire [31:0] csr_writedata,
  input wire [3:0] csr_byteenable,
  output wire csr_waitrequest,
  output reg csr_readdatavalid,
  output reg [31:0] csr_readdata,
  output wire [32:0] avm_address,
  output wire avm_read, avm_write,
  output wire [511:0] avm_writedata,
  output wire [63:0] avm_byteenable,
  output wire [7:0] avm_burstcount,
  input wire avm_waitrequest,
  input wire [511:0] avm_readdata,
  input wire avm_readdatavalid,
  input wire [1:0] avm_response
);
  reg [31:0] controls, threshold, token_config, position_config;
  reg [31:0] spec_id_config, base_config, mask_config, parents_config;
  reg [127:0] drafts_config;
  reg [32:0] host_address_config;
  reg [63:0] host_byteenable_config;
  reg [511:0] host_data_config;
  reg token_pending, spec_pending, host_pending, host_inflight, host_write;
  reg busy, prefix_available, sticky_done, sticky_error, sticky_cancel, bridge_error;
  reg cancel_pulse, model_commit_pulse;
  reg token_new, token_phase, mode, sparse;
  reg [15:0] sparse_threshold;
  reg [31:0] token, position, spec_id, base;
  reg [3:0] draft_mask;
  reg [11:0] draft_parents;
  reg [127:0] draft_tokens;
  reg [32:0] host_address;
  reg [63:0] host_byteenable;
  reg [511:0] host_data;
  reg logit_held, response_held, host_held, response_error, host_error;
  reg [31:0] held_logit_index, held_logit_data, held_id, held_next, held_position;
  reg [3:0] held_mask;
  reg [2:0] held_count;
  reg [127:0] held_tokens;
  reg [511:0] held_host_data;
  wire token_ready, spec_ready, host_ready, model_ready;
  wire logit_valid, response_valid, response_fault, host_valid, host_fault;
  wire [31:0] logit_index, response_id, response_next, response_position;
  wire signed [31:0] logit_data;
  wire [3:0] response_mask;
  wire [2:0] response_count;
  wire [127:0] response_tokens;
  wire [511:0] host_rsp_data;
  wire done, error, cancel_done;
  wire csr_transfer=rst_n && !csr_waitrequest && (csr_read || csr_write);
  wire [31:0] write_mask={{8{csr_byteenable[3]}},{8{csr_byteenable[2]}},
    {8{csr_byteenable[1]}},{8{csr_byteenable[0]}}};
  wire [31:0] command=csr_writedata & write_mask;
  wire launch_available=!busy && !token_pending && !spec_pending &&
    !host_inflight && !response_held && !logit_held && !host_held;
  reg [31:0] selected_read;
  reg read_known, write_known;

  assign csr_waitrequest=!rst_n;
  always @* begin
    selected_read=0; read_known=1; write_known=1;
    case (csr_address)
      10'h000: selected_read=32'h48543225;
      10'h004: selected_read={18'd0,prefix_available,host_inflight,ddr_cal_ready,bridge_error,host_held,
        response_held,logit_held,sticky_cancel,sticky_error,sticky_done,
        host_pending,spec_pending|token_pending,busy,model_ready};
      10'h008: selected_read=controls;
      10'h00c: selected_read=threshold;
      10'h010: selected_read=token_config;
      10'h014: selected_read=position_config;
      10'h018: selected_read=0;
      10'h020: selected_read=spec_id_config;
      10'h024: selected_read=base_config;
      10'h028: selected_read=mask_config;
      10'h02c: selected_read=parents_config;
      10'h030,10'h034,10'h038,10'h03c:
        selected_read=drafts_config[csr_address[3:2]*32+:32];
      10'h040: selected_read={31'd0,logit_held};
      10'h044: selected_read=logit_held ? held_logit_index : 32'd0;
      10'h048: selected_read=logit_held ? held_logit_data : 32'd0;
      10'h04c: selected_read=0;
      10'h050: selected_read={30'd0,response_error && response_held,response_held};
      10'h054: selected_read=response_held ? held_id : 32'd0;
      10'h058: selected_read=response_held ? {25'd0,held_count,held_mask} : 32'd0;
      10'h05c: selected_read=response_held ? held_next : 32'd0;
      10'h060: selected_read=response_held ? held_position : 32'd0;
      10'h064,10'h068,10'h06c,10'h070:
        selected_read=response_held ? held_tokens[((csr_address-10'h064)>>2)*32+:32] : 32'd0;
      10'h074: selected_read=0;
      10'h100: selected_read=host_address_config[31:0];
      10'h104: selected_read={31'd0,host_address_config[32]};
      10'h108: selected_read={30'd0,host_write,host_pending};
      10'h110: selected_read=host_byteenable_config[31:0];
      10'h114: selected_read=host_byteenable_config[63:32];
      10'h160: selected_read={30'd0,host_error && host_held,host_held};
      10'h164: selected_read=0;
      default: begin
        if (csr_address>=10'h120 && csr_address<=10'h15c && csr_address[1:0]==0)
          selected_read=host_data_config[((csr_address-10'h120)>>2)*32+:32];
        else if (csr_address>=10'h180 && csr_address<=10'h1bc && csr_address[1:0]==0)
          selected_read=host_held ? held_host_data[csr_address[5:2]*32+:32] : 32'd0;
        else read_known=0;
      end
    endcase
    case (csr_address)
      10'h004,10'h008,10'h00c,10'h010,10'h014,10'h018,10'h020,
      10'h024,10'h028,10'h02c,10'h030,10'h034,10'h038,10'h03c,
      10'h04c,10'h074,10'h100,10'h104,10'h108,10'h110,10'h114,10'h164: begin end
      default: write_known=csr_address>=10'h120 && csr_address<=10'h15c &&
        csr_address[1:0]==0;
    endcase
  end

  anvil_q3_ht2_top #(
    .NUM_LAYERS(NUM_LAYERS),.HIDDEN_SIZE(HIDDEN_SIZE),.INTERMEDIATE_SIZE(INTERMEDIATE_SIZE),
    .NUM_Q_HEADS(NUM_Q_HEADS),.NUM_KV_HEADS(NUM_KV_HEADS),.HEAD_DIM(HEAD_DIM),
    .GROUP_SIZE(GROUP_SIZE),.VOCAB_SIZE(VOCAB_SIZE),.MAX_SEQ_LEN(MAX_SEQ_LEN),
    .CACHE_MODE(CACHE_MODE),.BANKS(BANKS),.TILE_K(TILE_K),.TILE_ROWS(TILE_ROWS),
    .TILE_SLOTS(TILE_SLOTS),.QUEUE_DEPTH(QUEUE_DEPTH),.BURST_BEATS(BURST_BEATS),
    .KV_RESIDENT_GROUPS(KV_RESIDENT_GROUPS)
  ) accelerator (
    .clk(clk),.rst_n(rst_n),.cancel(cancel_pulse),.token_valid(token_pending),
    .token_ready(token_ready),.token_id(token),.token_pos(position),
    .new_sequence(token_new),.token_phase(token_phase),.logit_ready(!logit_held),
    .ddr_cal_ready(ddr_cal_ready),.model_commit(model_commit_pulse),
    .logit_valid(logit_valid),.logit_index(logit_index),.logit_data(logit_data),
    .done(done),.error(error),.cancel_done(cancel_done),.model_ready(model_ready),
    .host_req_valid(host_pending),.host_req_write(host_write),
    .host_req_address(host_address),.host_req_wdata(host_data),
    .host_req_byteenable(host_byteenable),.host_rsp_ready(!host_held),
    .host_req_ready(host_ready),.host_rsp_valid(host_valid),.host_rsp_rdata(host_rsp_data),
    .host_rsp_error(host_fault),.ht2_enable(mode),.sparse_enable(sparse),
    .sparse_threshold_f16(sparse_threshold),
    .spec_req_valid(spec_pending),.spec_req_ready(spec_ready),.spec_req_id(spec_id),
    .spec_base_pos(base),.draft_mask(draft_mask),.draft_tokens(draft_tokens),
    .draft_parents(draft_parents),.spec_rsp_valid(response_valid),
    .spec_rsp_ready(!response_held),.spec_rsp_id(response_id),
    .spec_rsp_error(response_fault),.accepted_mask(response_mask),
    .accepted_count(response_count),.accepted_tokens(response_tokens),
    .next_token(response_next),.committed_pos(response_position),
    .avm_address(avm_address),.avm_read(avm_read),.avm_write(avm_write),
    .avm_writedata(avm_writedata),.avm_byteenable(avm_byteenable),
    .avm_burstcount(avm_burstcount),.avm_waitrequest(avm_waitrequest),
    .avm_readdata(avm_readdata),.avm_readdatavalid(avm_readdatavalid),.avm_response(avm_response)
  );
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      controls<=0; threshold<=32'h1400; token_config<=0; position_config<=0;
      spec_id_config<=0; base_config<=0; mask_config<=0; parents_config<=0;
      drafts_config<=0; host_address_config<=0; host_byteenable_config<=0; host_data_config<=0;
      token_pending<=0; spec_pending<=0; host_pending<=0; host_inflight<=0; host_write<=0;
      busy<=0; prefix_available<=0; sticky_done<=0; sticky_error<=0; sticky_cancel<=0; bridge_error<=0;
      cancel_pulse<=0; model_commit_pulse<=0; token_new<=0; token_phase<=0;
      mode<=0; sparse<=0; sparse_threshold<=0; token<=0; position<=0;
      spec_id<=0; base<=0; draft_mask<=0; draft_parents<=0; draft_tokens<=0;
      host_address<=0; host_byteenable<=0; host_data<=0;
      logit_held<=0; response_held<=0; host_held<=0; response_error<=0; host_error<=0;
      held_logit_index<=0; held_logit_data<=0; held_id<=0; held_next<=0;
      held_position<=0; held_mask<=0; held_count<=0; held_tokens<=0; held_host_data<=0;
      csr_readdatavalid<=0; csr_readdata<=0;
    end else begin
      cancel_pulse<=0; model_commit_pulse<=0; csr_readdatavalid<=0; csr_readdata<=0;
      if (token_pending && token_ready) token_pending<=0;
      if (spec_pending && spec_ready) spec_pending<=0;
      if (host_pending && host_ready) host_pending<=0;
      if (done) begin
        sticky_done<=1; busy<=0;
        if (!error && mode) prefix_available<=1;
      end
      if (error) sticky_error<=1;
      if (cancel_done) begin sticky_cancel<=1; busy<=0; end
      if (logit_valid && !logit_held) begin
        logit_held<=1; held_logit_index<=logit_index; held_logit_data<=logit_data;
      end
      if (response_valid && !response_held) begin
        response_held<=1; response_error<=response_fault;
        held_id<=response_id; held_mask<=response_mask; held_count<=response_count;
        held_tokens<=response_tokens; held_next<=response_next; held_position<=response_position;
        sticky_done<=1; sticky_error<=sticky_error || response_fault; busy<=0;
      end
      if (host_valid && !host_held) begin
        host_held<=1; host_inflight<=0; host_error<=host_fault; held_host_data<=host_rsp_data;
      end
      if (cancel_pulse) begin
        token_pending<=0; spec_pending<=0; logit_held<=0; response_held<=0;
        held_logit_index<=0; held_logit_data<=0; held_id<=0; held_mask<=0;
        held_count<=0; held_tokens<=0; held_next<=0; held_position<=0; response_error<=0;
      end
      if (csr_transfer) begin
        if (csr_address[1:0]!=0 || (csr_read && csr_write) ||
            (csr_read && !read_known) || (csr_write && !write_known)) begin
          bridge_error<=1;
          if (csr_read && !csr_write) csr_readdatavalid<=1;
        end
        else if (csr_read) begin csr_readdatavalid<=1; csr_readdata<=selected_read; end
        else if (csr_write) begin
          case (csr_address)
            10'h004: begin
              if (command[4]) sticky_done<=0;
              if (command[5]) sticky_error<=0;
              if (command[6]) sticky_cancel<=0;
              if (command[10]) bridge_error<=0;
            end
            10'h008: if ((command & ~32'h7)==0)
              controls<=(controls & ~write_mask)|command;
              else bridge_error<=1;
            10'h00c: if ((command & 32'hffff0000)==0)
              threshold<=(threshold & ~write_mask)|command;
              else bridge_error<=1;
            10'h010: token_config<=(token_config & ~write_mask)|command;
            10'h014: position_config<=(position_config & ~write_mask)|command;
            10'h020: spec_id_config<=(spec_id_config & ~write_mask)|command;
            10'h024: base_config<=(base_config & ~write_mask)|command;
            10'h028: if ((command & ~32'hf)==0)
              mask_config<=(mask_config & ~write_mask)|command;
              else bridge_error<=1;
            10'h02c: if ((command & ~32'hfff)==0)
              parents_config<=(parents_config & ~write_mask)|command;
              else bridge_error<=1;
            10'h030,10'h034,10'h038,10'h03c:
              drafts_config[csr_address[3:2]*32+:32]<=
                (drafts_config[csr_address[3:2]*32+:32] & ~write_mask)|command;
            10'h018: begin
              if (command[2] && (command & ~32'h4)==0) begin cancel_pulse<=1; end
              else if (command[3] && (command & ~32'h8)==0 && launch_available) begin
                model_commit_pulse<=1; prefix_available<=0;
              end else if (command[0] && (command & ~32'h3)==0 && launch_available &&
                  model_ready && ddr_cal_ready) begin
                token_pending<=1; busy<=1; token<=token_config; position<=position_config;
                token_new<=command[1]; token_phase<=controls[2]; mode<=controls[0];
                sparse<=controls[1]; sparse_threshold<=threshold[15:0];
                if (command[1] || !controls[0]) prefix_available<=0;
              end else if (command[4] && (command & ~32'h10)==0 && launch_available &&
                  model_ready && ddr_cal_ready && prefix_available && mode) begin
                spec_pending<=1; busy<=1; spec_id<=spec_id_config; base<=base_config;
                draft_mask<=mask_config[3:0]; draft_parents<=parents_config[11:0];
                draft_tokens<=drafts_config; sparse<=controls[1]; sparse_threshold<=threshold[15:0];
              end else bridge_error<=1;
            end
            10'h04c: begin
              if (command==1 && logit_held) begin
                logit_held<=0; held_logit_index<=0; held_logit_data<=0;
              end else bridge_error<=1;
            end
            10'h074: begin
              if (command==1 && response_held) begin
                response_held<=0; response_error<=0; held_id<=0; held_mask<=0;
                held_count<=0; held_tokens<=0; held_next<=0; held_position<=0;
              end else bridge_error<=1;
            end
            10'h100: host_address_config[31:0]<=
              (host_address_config[31:0] & ~write_mask)|command;
            10'h104: if ((command & ~32'h1)==0) begin
              if (csr_byteenable[0]) host_address_config[32]<=command[0];
            end else bridge_error<=1;
            10'h108: begin
              if (command[0] && (command & ~32'h3)==0 && launch_available) begin
                host_pending<=1; host_inflight<=1; host_write<=command[1]; host_address<=host_address_config;
                host_byteenable<=host_byteenable_config; host_data<=host_data_config;
                if (command[1]) prefix_available<=0;
              end else bridge_error<=1;
            end
            10'h110: host_byteenable_config[31:0]<=
              (host_byteenable_config[31:0] & ~write_mask)|command;
            10'h114: host_byteenable_config[63:32]<=
              (host_byteenable_config[63:32] & ~write_mask)|command;
            10'h164: begin
              if (command==1 && host_held) begin host_held<=0; host_error<=0; held_host_data<=0; end
              else bridge_error<=1;
            end
            default: host_data_config[((csr_address-10'h120)>>2)*32+:32]<=
              (host_data_config[((csr_address-10'h120)>>2)*32+:32] & ~write_mask)|command;
          endcase
        end
      end
      if (done || (response_valid && !response_held)) sticky_done<=1;
      if (error || (response_valid && !response_held && response_fault)) sticky_error<=1;
      if (cancel_done) sticky_cancel<=1;
    end
  end
endmodule
