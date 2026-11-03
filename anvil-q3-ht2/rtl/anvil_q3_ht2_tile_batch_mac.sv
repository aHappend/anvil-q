module anvil_q3_ht2_tile_batch_mac #(
  parameter K=4,WEIGHT_LANES=128,
  parameter NUM_LAYERS=36,HIDDEN_SIZE=2048,INTERMEDIATE_SIZE=11008,
  parameter NUM_KV_HEADS=2,HEAD_DIM=128
) (
  input wire clk,rst_n,flush,
  input wire cmd_valid,
  output wire cmd_ready,
  input wire [31:0] cmd_epoch,cmd_layer,
  input wire [2:0] cmd_proj,
  input wire [31:0] cmd_row_base,cmd_columns,
  input wire [3:0] cmd_token_mask,
  input wire [127:0] cmd_row_mask,
  input wire in_valid,
  output wire in_ready,
  input wire [31:0] in_column,
  input wire [511:0] in_qweight,in_qzero,
  input wire [2047:0] in_scale_f16,
  input wire [63:0] in_activation_f16,
  input wire [3:0] in_keep_mask,
  input wire in_last,
  output wire out_valid,
  input wire out_ready,
  output wire out_error,
  output wire [31:0] out_epoch,out_layer,
  output wire [2:0] out_proj,
  output wire [31:0] out_row_base,
  output wire [3:0] out_token_mask,
  output wire [127:0] out_row_mask,
  output wire [16383:0] out_sum_f32,
  output wire idle,fault
);
  localparam LEGAL=K==4 &&
    (WEIGHT_LANES==8 || WEIGHT_LANES==16 || WEIGHT_LANES==32 ||
      WEIGHT_LANES==64 || WEIGHT_LANES==128) &&
    NUM_LAYERS>0 && HIDDEN_SIZE>0 && INTERMEDIATE_SIZE>0 &&
    NUM_KV_HEADS>0 && HEAD_DIM>0 && (HEAD_DIM & 1)==0 &&
    64'(HIDDEN_SIZE)==64'(NUM_KV_HEADS)*64'(HEAD_DIM)*64'd8 &&
    64'(HIDDEN_SIZE)<=64'hffffffff &&
    64'(INTERMEDIATE_SIZE)<=64'hffffffff &&
    (INTERMEDIATE_SIZE & 7)==0;
  generate if (!LEGAL) begin: invalid_parameters
    initial $fatal(1,"ANVIL_Q3_HT2 PARAMETER ERROR: tile MAC geometry");
    assign cmd_ready=0; assign in_ready=0; assign out_valid=0;
    assign out_error=0; assign out_epoch=0; assign out_layer=0;
    assign out_proj=0; assign out_row_base=0; assign out_token_mask=0;
    assign out_row_mask=0; assign out_sum_f32=0; assign idle=0; assign fault=0;
  end else begin: datapath
    import anvil_q3_ht2_fp_pkg::*;
    localparam IDLE=0,FEED=1,DRAIN=2,EMPTY=3,ERROR_PENDING=4,
      RESULT=5,FAULTED=6;
    reg [2:0] state;
    reg failed,result_valid,result_error;
    reg [31:0] epoch,layer,row_base,columns,received,previous_column;
    reg [2:0] projection;
    reg [3:0] token_mask;
    reg [127:0] row_mask;
    reg [16383:0] sums;
    reg [5:0] elapsed;
    reg [2:0] stripe_tag [0:8];
    reg [15:0] activation_capture [0:3];
    reg [31:0] activation [0:3][1:2];
    wire [127:0] expanded_activation;
    wire enabled=rst_n && !flush;
    wire pipeline_enable=state==FEED || state==DRAIN;
    wire command_fire=cmd_valid && cmd_ready;
    wire beat_fire=in_valid && in_ready;
    wire [31:0] command_inputs=cmd_proj==6 ? INTERMEDIATE_SIZE : HIDDEN_SIZE;
    wire [31:0] command_outputs=(cmd_proj==1 || cmd_proj==2) ?
      NUM_KV_HEADS*HEAD_DIM : ((cmd_proj==4 || cmd_proj==5) ?
        INTERMEDIATE_SIZE : HIDDEN_SIZE);
    wire [31:0] inputs=projection==6 ? INTERMEDIATE_SIZE : HIDDEN_SIZE;
    reg command_bad,beat_bad;
    reg [3:0] activation_bad;
    reg [WEIGHT_LANES-1:0] scale_bad;
    wire [WEIGHT_LANES-1:0] decoded_valid,decoded_error;
    wire [WEIGHT_LANES*32-1:0] decoded_weight;
    wire [K*WEIGHT_LANES-1:0] lane_error,lane_final_valid;
    wire [16383:0] final_sums;
    wire arithmetic_fault=(|decoded_error) || (|lane_error);
    wire fault_now=(beat_fire && beat_bad) || arithmetic_fault;
    wire local_flush=flush || command_fire || failed ||
      (beat_fire && beat_bad);
    reg reduction_valid;
    reg [1:0] reduction_level,reduction_index;
    integer t,r,p;

    assign cmd_ready=enabled && !failed && state==IDLE;
    assign in_ready=enabled && !failed && state==FEED && received<columns;
    assign idle=enabled && !failed && state==IDLE;
    assign fault=enabled && failed;
    assign out_valid=enabled && result_valid;
    assign out_error=out_valid && result_error;
    assign out_epoch=out_valid ? epoch : 0;
    assign out_layer=out_valid ? layer : 0;
    assign out_proj=out_valid ? projection : 0;
    assign out_row_base=out_valid ? row_base : 0;
    assign out_token_mask=out_valid ? token_mask : 0;
    assign out_row_mask=out_valid ? row_mask : 0;
    assign out_sum_f32=out_valid && !result_error ? sums : 0;

    always @* begin
      command_bad=cmd_layer>=NUM_LAYERS || cmd_proj>6 ||
        cmd_columns>command_inputs || cmd_token_mask==0 || cmd_row_mask==0 ||
        cmd_row_base>=command_outputs;
      for (r=0;r<128;r=r+1) begin
        if (cmd_row_mask[r] && (r>=WEIGHT_LANES ||
            {32'd0,cmd_row_base}+64'(r)>={32'd0,command_outputs}))
          command_bad=1;
      end
      activation_bad=0;
      scale_bad=0;
      for (t=0;t<4;t=t+1) begin
        if (token_mask[t]) begin
          activation_bad[t]=in_activation_f16[t*16+10+:5]==31;
`ifndef SYNTHESIS
          if ((^in_activation_f16[t*16+:16])===1'bx)
            activation_bad[t]=1;
`endif
        end
      end
      for (r=0;r<WEIGHT_LANES;r=r+1) begin
        if (row_mask[r]) begin
          scale_bad[r]=in_scale_f16[r*16+10+:5]==31 ||
            (in_scale_f16[r*16+15] && in_scale_f16[r*16+:15]!=0);
`ifndef SYNTHESIS
          if ((^in_scale_f16[r*16+:16])===1'bx ||
              (^in_qweight[(r>>3)*32+awq_position(3'(r))*4+:4])===1'bx ||
              (^in_qzero[(r>>3)*32+awq_position(3'(r))*4+:4])===1'bx)
            scale_bad[r]=1;
`endif
        end
      end
      beat_bad=in_column>=inputs || (received!=0 && in_column<=previous_column) ||
        in_keep_mask==0 || (in_keep_mask & ~token_mask)!=0 ||
        in_last!=(received==columns-1) || (|activation_bad) || (|scale_bad);
`ifndef SYNTHESIS
      if ((^{cmd_epoch,cmd_layer,cmd_proj,cmd_row_base,cmd_columns,
          cmd_token_mask,cmd_row_mask})===1'bx) command_bad=1;
      if ((^{in_column,in_keep_mask,in_last})===1'bx) beat_bad=1;
`endif
    end

    always @* begin
      reduction_valid=0;
      reduction_level=0;
      reduction_index=0;
      if (state==DRAIN) begin
        if (elapsed>=14 && elapsed<=17) begin
          reduction_valid=1; reduction_level=1;
          reduction_index=2'(elapsed-6'd14);
        end else if (elapsed==23 || elapsed==24) begin
          reduction_valid=1; reduction_level=2;
          reduction_index=2'(elapsed-6'd23);
        end else if (elapsed==30) begin
          reduction_valid=1; reduction_level=3;
        end
      end
    end

    genvar row,token;
    for (row=0;row<WEIGHT_LANES;row=row+1) begin: weight_broadcast
      localparam PACKED_BIT=(row>>3)*32+awq_position(3'(row))*4;
      anvil_q3_ht2_weight_decode decode (
        .clk(clk),.rst_n(rst_n),.flush(local_flush),.enable(pipeline_enable),
        .in_valid(beat_fire && row_mask[row] && !beat_bad),
        .in_q(in_qweight[PACKED_BIT+:4]),.in_zero(in_qzero[PACKED_BIT+:4]),
        .in_scale_f16(in_scale_f16[row*16+:16]),
        .out_valid(decoded_valid[row]),.out_error(decoded_error[row]),
        .out_weight_f32(decoded_weight[row*32+:32])
      );
    end
    for (token=0;token<4;token=token+1) begin: token_banks
      assign expanded_activation[token*32+:32]=expand_f16(activation_capture[token]);
      for (row=0;row<128;row=row+1) begin: rows
        if (row<WEIGHT_LANES) begin: physical_lane
          anvil_q3_ht2_mac_lane lane (
            .clk(clk),.rst_n(rst_n),.flush(local_flush),.enable(pipeline_enable),
            .product_in_valid(decoded_valid[row] && !decoded_error[row]),
            .weight_f32(decoded_weight[row*32+:32]),
            .activation_f32(activation[token][2]),
            .product_stripe(stripe_tag[8]),
            .reduction_valid(reduction_valid),
            .reduction_level(reduction_level),.reduction_index(reduction_index),
            .arithmetic_error(lane_error[token*WEIGHT_LANES+row]),
            .final_valid(lane_final_valid[token*WEIGHT_LANES+row]),
            .final_sum(final_sums[(token*128+row)*32+:32])
          );
        end else begin: unused_output
          assign final_sums[(token*128+row)*32+:32]=0;
        end
      end
    end

    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        state<=IDLE; failed<=0; result_valid<=0; result_error<=0;
        epoch<=0; layer<=0; projection<=0; row_base<=0; columns<=0;
        token_mask<=0; row_mask<=0; sums<=0;
        received<=0; previous_column<=0; elapsed<=0;
        for (p=0;p<9;p=p+1) stripe_tag[p]<=0;
        for (t=0;t<4;t=t+1) begin
          activation_capture[t]<=0;
          for (p=1;p<3;p=p+1) activation[t][p]<=0;
        end
      end else if (flush) begin
        state<=IDLE; failed<=0; result_valid<=0; result_error<=0;
        epoch<=0; layer<=0; projection<=0; row_base<=0; columns<=0;
        token_mask<=0; row_mask<=0; sums<=0;
        received<=0; previous_column<=0; elapsed<=0;
        for (p=0;p<9;p=p+1) stripe_tag[p]<=0;
        for (t=0;t<4;t=t+1) begin
          activation_capture[t]<=0;
          for (p=1;p<3;p=p+1) activation[t][p]<=0;
        end
      end else begin
        if (pipeline_enable && !failed) begin
          stripe_tag[0]<=beat_fire ? received[2:0] : 0;
          for (p=1;p<9;p=p+1) stripe_tag[p]<=stripe_tag[p-1];
          for (t=0;t<4;t=t+1) begin
            activation_capture[t]<=beat_fire && token_mask[t] && in_keep_mask[t] ?
              in_activation_f16[t*16+:16] : 0;
            activation[t][1]<=expanded_activation[t*32+:32];
            activation[t][2]<=activation[t][1];
          end
        end
        if (command_fire) begin
          epoch<=cmd_epoch; layer<=cmd_layer; projection<=cmd_proj;
          row_base<=cmd_row_base; columns<=cmd_columns;
          token_mask<=cmd_token_mask; row_mask<=cmd_row_mask;
          received<=0; previous_column<=0; elapsed<=0; sums<=0;
          result_valid<=0; result_error<=0;
          if (command_bad) begin failed<=1; state<=ERROR_PENDING; end
          else if (cmd_columns==0) state<=EMPTY;
          else state<=FEED;
        end else if (!failed && fault_now) begin
          failed<=1; state<=ERROR_PENDING; sums<=0;
          result_valid<=0; result_error<=0;
        end else begin
          case (state)
            FEED: if (beat_fire) begin
              received<=received+1;
              previous_column<=in_column;
              if (in_last) begin state<=DRAIN; elapsed<=0; end
            end
            DRAIN: begin
              elapsed<=elapsed+1;
              if (elapsed==35) begin
                if (&lane_final_valid) begin
                  sums<=final_sums; result_valid<=1;
                  result_error<=0; state<=RESULT;
                end else begin
                  failed<=1; state<=ERROR_PENDING; sums<=0;
                end
              end
            end
            EMPTY: begin
              sums<=0; result_valid<=1; result_error<=0; state<=RESULT;
            end
            ERROR_PENDING: begin
              sums<=0; result_valid<=1; result_error<=1; state<=RESULT;
            end
            RESULT: if (out_ready) begin
              result_valid<=0; result_error<=0; sums<=0;
              epoch<=0; layer<=0; projection<=0; row_base<=0;
              token_mask<=0; row_mask<=0;
              if (failed) state<=FAULTED;
              else state<=IDLE;
            end
            default: begin end
          endcase
        end
      end
    end
  end endgenerate
endmodule
