module anvil_q2_fp2_flash_attn #(
  parameter HEAD_DIM=128, TILE_TOKENS=16, MAX_SEQ_LEN=32768,
  parameter G=(HEAD_DIM>0) ? ((HEAD_DIM+31) >> 5) : 1,
  parameter D=(HEAD_DIM>0 && HEAD_DIM<=128) ? HEAD_DIM : 1
) (
  input wire clk, rst_n, flush,
  input wire cmd_valid,
  input wire [31:0] cmd_layer, cmd_kv_head, cmd_pos, cmd_len, cmd_tag,
  input wire [6*D*16-1:0] cmd_query,
  output wire cmd_ready,
  input wire kv_valid,
  input wire [D*16-1:0] kv_key, kv_value,
  input wire [G*8-1:0] kv_scale_key, kv_scale_value,
  input wire kv_format,
  input wire [31:0] kv_index,
  input wire kv_last, kv_error,
  output wire kv_ready,
  output wire out_valid,
  output wire [6*D*32-1:0] out_data,
  output wire [31:0] out_tag,
  output wire out_error,
  input wire out_ready
);
  generate if (HEAD_DIM<2 || HEAD_DIM>128 || (HEAD_DIM & 1)!=0 ||
               TILE_TOKENS<1 || TILE_TOKENS>32 ||
               MAX_SEQ_LEN<1 || MAX_SEQ_LEN>32768 ||
               G!=((HEAD_DIM+31) >> 5) || D!=HEAD_DIM) begin: invalid_parameters
    initial $fatal(1,"ANVIL_Q2_FP2 PARAMETER ERROR: FlashAttention geometry");
    assign cmd_ready=0;
    assign kv_ready=0;
    assign out_valid=0;
    assign out_data=0;
    assign out_tag=0;
    assign out_error=0;
  end else begin: datapath
    localparam IDLE=0, WAIT_KV=1, SCORES=2, HEAD_START=3, EXP_WAIT=4,
      UPDATE_SEND=5, UPDATE_DRAIN=6, HEAD_NEXT=7,
      NORM_BEGIN=8, NORM_WAIT=9, NORM_SEND=10, NORM_DRAIN=11, RESULT=12;
    reg [3:0] state;
    reg failed, last_key;
    reg [31:0] tag, position, expected_kv;
    reg [6*D*16-1:0] queries;
    reg [D*16-1:0] key, value;
    reg [2:0] issue_head, received_heads, head;
    reg [7:0] component;
    reg [31:0] scores [0:5], maxima [0:5], denominators [0:5];
    (* ramstyle = "logic", nomem2reg *) reg [31:0] accumulator [0:6*D-1];
    reg [31:0] alpha, beta, inverse;
    reg [6*D*32-1:0] result;
    wire clear=flush || state==IDLE;
    assign cmd_ready=rst_n && !flush && state==IDLE;
    assign kv_ready=rst_n && !flush && state==WAIT_KV;
    assign out_valid=rst_n && !flush && state==RESULT;
    assign out_data=rst_n ? result : {6*D*32{1'b0}};
    assign out_tag=rst_n ? tag : 32'd0;
    assign out_error=out_valid && failed;
    wire [D*16-1:0] decoded_key, decoded_value;
    wire [D-1:0] decode_error, finite_error;
    wire [6*D-1:0] query_error;
    genvar element;
    for (element=0;element<D;element=element+1) begin: decode_elements
      wire [15:0] mx_key, mx_value;
      wire key_error, value_error;
      anvil_q2_fp2_mx_decode key_decoder(
        kv_key[8*element+:8],kv_scale_key[8*(element >> 5)+:8],mx_key,key_error);
      anvil_q2_fp2_mx_decode value_decoder(
        kv_value[8*element+:8],kv_scale_value[8*(element >> 5)+:8],mx_value,value_error);
      assign decoded_key[16*element+:16]=kv_format ? mx_key : kv_key[16*element+:16];
      assign decoded_value[16*element+:16]=kv_format ? mx_value : kv_value[16*element+:16];
      assign decode_error[element]=kv_format && (key_error || value_error);
      assign finite_error[element]=(&decoded_key[16*element+7+:8]) ||
        (&decoded_value[16*element+7+:8]);
    end
    for (element=0;element<6*D;element=element+1) begin: query_classification
      assign query_error[element]=&cmd_query[16*element+7+:8];
    end

    wire score_issue=state==SCORES && issue_head<6;
    wire [4095:0] dot_data [0:7];
    wire [127:0] dot_valid [0:7], dot_error [0:7];
    genvar lane, level, node;
    for (lane=0;lane<128;lane=lane+1) begin: dot_lanes
      wire [31:0] a, b;
      if (lane<D) begin: active
        assign a={queries[(issue_head*D+lane)*16+:16],16'd0};
        assign b={key[16*lane+:16],16'd0};
      end else begin: padding
        assign a=0;
        assign b=0;
      end
      anvil_q2_fp2_mul3 multiply(
        clk,rst_n,clear,1'b1,score_issue,1'b0,a,b,
        dot_valid[0][lane],dot_data[0][32*lane+:32],dot_error[0][lane]);
    end
    for (level=1;level<=7;level=level+1) begin: dot_reduction
      for (node=0;node<128;node=node+1) begin: nodes
        if (node<(128 >> level)) begin: active
          anvil_q2_fp2_add4 addition(
            clk,rst_n,clear,1'b1,dot_valid[level-1][2*node],
            (dot_error[level-1][2*node] || dot_error[level-1][2*node+1]),
            dot_data[level-1][64*node+:32],dot_data[level-1][64*node+32+:32],
            dot_valid[level][node],dot_data[level][32*node+:32],dot_error[level][node]);
        end else begin: padding
          assign dot_valid[level][node]=0;
          assign dot_data[level][32*node+:32]=0;
          assign dot_error[level][node]=0;
        end
      end
    end
    wire [31:0] head_scale;
    localparam [7:0] SCALE_ADDRESS=D;
    anvil_q2_fp2_head_scale_rom scale_lut(SCALE_ADDRESS,head_scale);
    wire score_valid, score_error;
    wire [31:0] score_data;
    anvil_q2_fp2_mul3 score_scale(
      clk,rst_n,clear,1'b1,dot_valid[7][0],dot_error[7][0],
      dot_data[7][31:0],head_scale,score_valid,score_data,score_error);
    reg [2:0] score_head [0:33];

    function automatic less_than(input [31:0] a,b);
      begin
        if (!(|a[30:0]) && !(|b[30:0])) less_than=0;
        else if (a[31]!=b[31]) less_than=a[31];
        else less_than=a[31] ? (a[30:0]>b[30:0]) : (a[30:0]<b[30:0]);
      end
    endfunction
    wire [31:0] new_maximum=less_than(maxima[head],scores[head]) ?
      scores[head] : maxima[head];
    wire old_delta_valid, new_delta_valid, old_delta_error, new_delta_error;
    wire [31:0] old_delta, new_delta;
    wire delta_issue=state==HEAD_START && expected_kv!=0;
    anvil_q2_fp2_add4 old_difference(
      clk,rst_n,clear,1'b1,delta_issue,1'b0,
      maxima[head],{!new_maximum[31],new_maximum[30:0]},
      old_delta_valid,old_delta,old_delta_error);
    anvil_q2_fp2_add4 new_difference(
      clk,rst_n,clear,1'b1,delta_issue,1'b0,
      scores[head],{!new_maximum[31],new_maximum[30:0]},
      new_delta_valid,new_delta,new_delta_error);
    wire alpha_valid, beta_valid, alpha_error, beta_error;
    wire [31:0] alpha_data, beta_data;
    anvil_q2_fp2_exp9 old_rescale(
      clk,rst_n,clear,1'b1,old_delta_valid,old_delta_error,old_delta,
      alpha_valid,alpha_data,alpha_error);
    anvil_q2_fp2_exp9 new_rescale(
      clk,rst_n,clear,1'b1,new_delta_valid,new_delta_error,new_delta,
      beta_valid,beta_data,beta_error);

    wire update_issue=state==UPDATE_SEND;
    wire [31:0] old_element=(component==D) ?
      denominators[head] : accumulator[head*D+component];
    wire [31:0] new_element=(component==D) ?
      32'h3f800000 : {value[16*component+:16],16'd0};
    wire old_product_valid, new_product_valid, old_product_error, new_product_error;
    wire [31:0] old_product, new_product;
    anvil_q2_fp2_mul3 update_old(
      clk,rst_n,clear,1'b1,update_issue,1'b0,alpha,old_element,
      old_product_valid,old_product,old_product_error);
    anvil_q2_fp2_mul3 update_new(
      clk,rst_n,clear,1'b1,update_issue,1'b0,beta,new_element,
      new_product_valid,new_product,new_product_error);
    wire update_valid, update_error;
    wire [31:0] update_data;
    anvil_q2_fp2_add4 update_sum(
      clk,rst_n,clear,1'b1,(old_product_valid && new_product_valid),
      (old_product_error || new_product_error),old_product,new_product,
      update_valid,update_data,update_error);
    reg [7:0] update_component [0:6];

    wire reciprocal_valid, reciprocal_error;
    wire [31:0] reciprocal_data;
    anvil_q2_fp2_reciprocal2 normalization_reciprocal(
      clk,rst_n,clear,1'b1,(state==NORM_BEGIN),1'b0,denominators[head],
      reciprocal_valid,reciprocal_data,reciprocal_error);
    wire norm_valid, norm_error;
    wire [31:0] norm_data;
    anvil_q2_fp2_mul3 normalization_multiply(
      clk,rst_n,clear,1'b1,(state==NORM_SEND),1'b0,
      accumulator[head*D+component],inverse,norm_valid,norm_data,norm_error);
    reg [7:0] norm_component [0:2];
    integer i;
    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        state<=IDLE; failed<=0; last_key<=0; tag<=0; position<=0; expected_kv<=0;
        queries<=0; key<=0; value<=0; issue_head<=0; received_heads<=0; head<=0;
        component<=0; alpha<=0; beta<=0; inverse<=0; result<=0;
        for (i=0;i<34;i=i+1) score_head[i]<=0;
        for (i=0;i<7;i=i+1) update_component[i]<=0;
        for (i=0;i<3;i=i+1) norm_component[i]<=0;
        for (i=0;i<6;i=i+1) begin
          scores[i]<=0; maxima[i]<=0; denominators[i]<=0;
        end
      end else if (flush) begin
        state<=IDLE; failed<=0; result<=0;
      end else begin
        score_head[0]<=issue_head;
        for (i=1;i<34;i=i+1) score_head[i]<=score_head[i-1];
        update_component[0]<=component;
        for (i=1;i<7;i=i+1) update_component[i]<=update_component[i-1];
        norm_component[0]<=component;
        for (i=1;i<3;i=i+1) norm_component[i]<=norm_component[i-1];
        if (update_valid && (state==UPDATE_SEND || state==UPDATE_DRAIN)) begin
          if (update_error) failed<=1;
          if (update_component[6]==D) begin
            denominators[head]<=update_data;
            state<=HEAD_NEXT;
          end else accumulator[head*D+update_component[6]]<=update_data;
        end
        if (norm_valid && (state==NORM_SEND || state==NORM_DRAIN)) begin
          result[(head*D+norm_component[2])*32+:32]<=norm_data;
          if (norm_error) failed<=1;
          if (norm_component[2]==D-1) begin
            if (head==5) state<=RESULT;
            else begin head<=head+1'b1; state<=NORM_BEGIN; end
          end
        end
        case (state)
          IDLE: if (cmd_valid && cmd_ready) begin
            tag<=cmd_tag; position<=cmd_pos; expected_kv<=0; queries<=cmd_query;
            result<=0; failed<=0;
            if (cmd_len==0 || cmd_pos>=MAX_SEQ_LEN ||
                cmd_len!=cmd_pos+32'd1 || (|query_error)) begin
              failed<=1; state<=RESULT;
            end else state<=WAIT_KV;
          end
          WAIT_KV: if (kv_valid && kv_ready) begin
            if (kv_error || (|decode_error) || (|finite_error) ||
                kv_index!=expected_kv || kv_last!=(expected_kv==position)) begin
              failed<=1; state<=RESULT;
            end else begin
              key<=decoded_key; value<=decoded_value; last_key<=kv_last;
              issue_head<=0; received_heads<=0; state<=SCORES;
            end
          end
          SCORES: begin
            if (score_issue) issue_head<=issue_head+1'b1;
            if (score_valid) begin
              scores[score_head[33]]<=score_data;
              if (score_error || score_head[33]>=6) begin
                failed<=1; state<=RESULT;
              end else if (received_heads==5) begin head<=0; state<=HEAD_START; end
              else received_heads<=received_heads+1'b1;
            end
          end
          HEAD_START: begin
            if (expected_kv==0) begin
              maxima[head]<=scores[head];
              denominators[head]<=32'h3f800000;
              for (i=0;i<D;i=i+1) accumulator[head*D+i]<={value[16*i+:16],16'd0};
              state<=HEAD_NEXT;
            end else begin
              maxima[head]<=new_maximum;
              state<=EXP_WAIT;
            end
          end
          EXP_WAIT: if (alpha_valid && beta_valid) begin
            if (alpha_error || beta_error) failed<=1;
            alpha<=alpha_data; beta<=beta_data; component<=0; state<=UPDATE_SEND;
          end
          UPDATE_SEND: begin
            if (component==D) state<=UPDATE_DRAIN;
            else component<=component+1'b1;
          end
          HEAD_NEXT: begin
            if (head==5) begin
              if (last_key) begin head<=0; state<=NORM_BEGIN; end
              else begin expected_kv<=expected_kv+1'b1; state<=WAIT_KV; end
            end else begin head<=head+1'b1; state<=HEAD_START; end
          end
          NORM_BEGIN: state<=NORM_WAIT;
          NORM_WAIT: if (reciprocal_valid) begin
            inverse<=reciprocal_data; component<=0; state<=NORM_SEND;
            if (reciprocal_error) failed<=1;
          end
          NORM_SEND: begin
            if (component==D-1) state<=NORM_DRAIN;
            else component<=component+1'b1;
          end
          RESULT: if (out_ready) state<=IDLE;
          default: begin end
        endcase
      end
    end
  end endgenerate
endmodule
