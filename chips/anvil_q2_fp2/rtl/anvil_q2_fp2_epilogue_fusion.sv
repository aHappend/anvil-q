module anvil_q2_fp2_epilogue_fusion (
  input wire clk, rst_n, flush,
  input wire in_valid,
  input wire [2:0] in_mode,
  input wire [31:0] in_a, in_b, in_gamma, in_cos, in_sin,
  input wire [31:0] in_length, in_index, in_tag,
  input wire in_first, in_last,
  output wire in_ready,
  output wire out_valid,
  output wire [31:0] out_data, out_pair, out_index, out_tag,
  output wire out_first, out_last, out_error,
  input wire out_ready
);
  reg busy, collecting, rms_failed, replaying, clear_pending;
  reg [2:0] mode;
  reg [1:0] spacing;
  reg [13:0] length, expected_index, replay_index;
  reg [31:0] tag, element_index, gate, up, exp_saved, inverse_saved, reciprocal_length;
  reg first, last, pass_valid, pass_error;
  reg [31:0] pass_data;
  (* ramstyle = "M20K", nomem2reg *) reg [31:0] rms_x [0:8959];
  (* ramstyle = "M20K", nomem2reg *) reg [31:0] rms_gamma [0:8959];
  reg [31:0] rms_x_q, rms_gamma_q;
  wire selected_valid;
  wire [31:0] selected_data, selected_pair;
  wire selected_error;
  wire enable=!selected_valid || out_ready;
  wire retiring=out_valid && out_ready;
  wire finishing=retiring && (mode!=0 || out_last);
  wire clear_pipeline=flush || clear_pending;
  wire live=rst_n && !flush;
  assign in_ready=live && !clear_pending &&
    ((!busy) || (mode==0 && collecting && spacing==0));
  wire accepted=in_valid && in_ready;
  wire rms_input=accepted && in_mode==0;
  wire legal_length=in_length>=1 && in_length<=8960;
  wire rms_metadata=(!busy) ?
    (legal_length && in_index==0 && in_first && (in_last==(in_length==1))) :
    (in_mode==0 && in_length=={18'd0,length} && in_tag==tag &&
     in_index=={18'd0,expected_index} && !in_first &&
     (in_last==(expected_index==length-1'b1)));
  wire bad_metadata=accepted && ((in_mode>4) ||
    ((in_mode==0 || busy) && !rms_metadata));
  wire valid_rms=rms_input && rms_metadata;
  wire [31:0] length_reciprocal;
  anvil_q2_fp2_length_rom length_lut(in_length[13:0],length_reciprocal);
  reg [6:0] final_square;
  reg [31:0] sum_saved;
  wire square_valid, square_error, sum_valid, sum_error;
  wire [31:0] square_data, sum_data;
  wire [31:0] sum_feedback=sum_valid ? sum_data : sum_saved;
  anvil_q2_fp2_mul3 rms_square(
    .clk(clk),.rst_n(rst_n),.flush(clear_pipeline),.enable(enable),
    .in_valid(valid_rms),.in_error(1'b0),.in_a(in_a),.in_b(in_a),
    .out_valid(square_valid),.out_data(square_data),.out_error(square_error));
  anvil_q2_fp2_add4 rms_sum(
    .clk(clk),.rst_n(rst_n),.flush(clear_pipeline),.enable(enable),
    .in_valid(square_valid),.in_error(square_error),
    .in_a(square_data),.in_b(sum_feedback),
    .out_valid(sum_valid),.out_data(sum_data),.out_error(sum_error));
  wire mean_valid, mean_error, epsilon_valid, epsilon_error;
  wire [31:0] mean_data, epsilon_data;
  anvil_q2_fp2_mul3 rms_mean(
    .clk(clk),.rst_n(rst_n),.flush(clear_pipeline),.enable(enable),
    .in_valid(sum_valid && final_square[6]),.in_error(sum_error || rms_failed),
    .in_a(sum_data),.in_b(reciprocal_length),
    .out_valid(mean_valid),.out_data(mean_data),.out_error(mean_error));
  anvil_q2_fp2_add4 rms_epsilon(
    .clk(clk),.rst_n(rst_n),.flush(clear_pipeline),.enable(enable),
    .in_valid(mean_valid),.in_error(mean_error),.in_a(mean_data),.in_b(32'h358637bd),
    .out_valid(epsilon_valid),.out_data(epsilon_data),.out_error(epsilon_error));
  wire inverse_valid, inverse_ready, inverse_error;
  wire [31:0] inverse_data;
  anvil_q2_fp2_rsqrt2 inverse_sqrt(
    .clk(clk),.rst_n(rst_n && !clear_pipeline),
    .in_valid(epsilon_valid && enable),.in_ready(inverse_ready),.in_x(epsilon_data),
    .out_valid(inverse_valid),.out_ready(enable),
    .out_data(inverse_data),.out_error(inverse_error));
  wire norm_issue=busy && mode==0 && (inverse_valid || replaying);
  wire [13:0] rms_raddr=(norm_issue && enable) ? (replay_index+14'd1) : replay_index;
  wire [31:0] replay_inverse=inverse_valid ? inverse_data : inverse_saved;
  reg [31:0] gamma_delay [0:2];
  reg [13:0] index_delay [0:5];
  reg [5:0] replay_first, replay_last;
  wire normalized_valid, normalized_error, rms_valid, rms_error;
  wire [31:0] normalized_data, rms_data;
  anvil_q2_fp2_mul3 rms_normalize(
    .clk(clk),.rst_n(rst_n),.flush(clear_pipeline),.enable(enable),
    .in_valid(norm_issue),.in_error(rms_failed || inverse_error),
    .in_a(rms_x_q),.in_b(replay_inverse),
    .out_valid(normalized_valid),.out_data(normalized_data),
    .out_error(normalized_error));
  anvil_q2_fp2_mul3 rms_apply_gamma(
    .clk(clk),.rst_n(rst_n),.flush(clear_pipeline),.enable(enable),
    .in_valid(normalized_valid),.in_error(normalized_error),
    .in_a(normalized_data),.in_b(gamma_delay[2]),
    .out_valid(rms_valid),.out_data(rms_data),.out_error(rms_error));

  wire rope_input=accepted && !busy && in_mode==1;
  wire [3:0] rotation_valid, rotation_error;
  wire [31:0] xc, ys, yc, xs;
  anvil_q2_fp2_mul3 rope_xc(
    clk,rst_n,clear_pipeline,enable,rope_input,1'b0,in_a,in_cos,
    rotation_valid[0],xc,rotation_error[0]);
  anvil_q2_fp2_mul3 rope_ys(
    clk,rst_n,clear_pipeline,enable,rope_input,1'b0,in_b,in_sin,
    rotation_valid[1],ys,rotation_error[1]);
  anvil_q2_fp2_mul3 rope_yc(
    clk,rst_n,clear_pipeline,enable,rope_input,1'b0,in_b,in_cos,
    rotation_valid[2],yc,rotation_error[2]);
  anvil_q2_fp2_mul3 rope_xs(
    clk,rst_n,clear_pipeline,enable,rope_input,1'b0,in_a,in_sin,
    rotation_valid[3],xs,rotation_error[3]);
  wire rope_valid, rope_pair_valid, rope_error, rope_pair_error;
  wire [31:0] rope_data, rope_pair;
  anvil_q2_fp2_add4 rope_subtract(
    clk,rst_n,clear_pipeline,enable,rotation_valid[0],
    (|rotation_error),xc,{!ys[31],ys[30:0]},rope_valid,rope_data,rope_error);
  anvil_q2_fp2_add4 rope_add(
    clk,rst_n,clear_pipeline,enable,rotation_valid[2],
    (|rotation_error),yc,xs,rope_pair_valid,rope_pair,rope_pair_error);
  wire residual_valid, residual_error;
  wire [31:0] residual_data;
  anvil_q2_fp2_add4 residual_add(
    clk,rst_n,clear_pipeline,enable,(accepted && !busy && in_mode==3),
    1'b0,in_a,in_b,residual_valid,residual_data,residual_error);

  wire exp_valid, exp_error, denominator_valid, denominator_error;
  wire reciprocal_valid, reciprocal_error, sign_valid, sign_error;
  wire gate_valid, gate_error, swiglu_valid, swiglu_error;
  wire [31:0] exp_data, denominator_data, reciprocal_data, sign_data, gate_data, swiglu_data;
  anvil_q2_fp2_exp9 swiglu_exp(
    clk,rst_n,clear_pipeline,enable,(accepted && !busy && in_mode==2),
    ((&in_a[30:23]) || (&in_b[30:23])),{1'b1,in_a[30:0]},
    exp_valid,exp_data,exp_error);
  anvil_q2_fp2_add4 swiglu_denominator(
    clk,rst_n,clear_pipeline,enable,exp_valid,exp_error,32'h3f800000,exp_data,
    denominator_valid,denominator_data,denominator_error);
  anvil_q2_fp2_reciprocal2 swiglu_reciprocal(
    clk,rst_n,clear_pipeline,enable,denominator_valid,denominator_error,denominator_data,
    reciprocal_valid,reciprocal_data,reciprocal_error);
  anvil_q2_fp2_mul3 swiglu_sign(
    clk,rst_n,clear_pipeline,enable,reciprocal_valid,reciprocal_error,
    (gate[31] ? exp_saved : 32'h3f800000),reciprocal_data,
    sign_valid,sign_data,sign_error);
  anvil_q2_fp2_mul3 swiglu_gate(
    clk,rst_n,clear_pipeline,enable,sign_valid,sign_error,gate,sign_data,
    gate_valid,gate_data,gate_error);
  anvil_q2_fp2_mul3 swiglu_up(
    clk,rst_n,clear_pipeline,enable,gate_valid,gate_error,gate_data,up,
    swiglu_valid,swiglu_data,swiglu_error);

  assign selected_valid=busy && (
    (mode==0 && rms_valid) || (mode==1 && rope_valid && rope_pair_valid) ||
    (mode==2 && swiglu_valid) || (mode==3 && residual_valid) ||
    ((mode==4 || mode==7) && pass_valid));
  assign selected_data=(mode==0) ? rms_data : ((mode==1) ? rope_data :
    ((mode==2) ? swiglu_data : ((mode==3) ? residual_data : pass_data)));
  assign selected_pair=(mode==1) ? rope_pair : 32'd0;
  assign selected_error=(mode==0) ? (rms_error || rms_failed) :
    ((mode==1) ? (rope_error || rope_pair_error) :
    ((mode==2) ? swiglu_error : ((mode==3) ? residual_error : pass_error)));
  assign out_valid=live && selected_valid;
  assign out_data=rst_n ? selected_data : 32'd0;
  assign out_pair=rst_n ? selected_pair : 32'd0;
  assign out_index=rst_n ? ((mode==0) ? {18'd0,index_delay[5]} : element_index) : 32'd0;
  assign out_tag=rst_n ? tag : 32'd0;
  assign out_first=out_valid && ((mode==0) ? replay_first[5] : first);
  assign out_last=out_valid && ((mode==0) ? replay_last[5] : last);
  assign out_error=out_valid && selected_error;
  integer i;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      busy<=0; collecting<=0; rms_failed<=0; replaying<=0; clear_pending<=0;
      mode<=0; spacing<=0; length<=0; expected_index<=0; replay_index<=0;
      tag<=0; element_index<=0; gate<=0; up<=0; exp_saved<=0;
      inverse_saved<=0; reciprocal_length<=0; first<=0; last<=0;
      pass_valid<=0; pass_error<=0; pass_data<=0;
      final_square<=0; sum_saved<=0; replay_first<=0; replay_last<=0;
      for (i=0;i<3;i=i+1) gamma_delay[i]<=0;
      for (i=0;i<6;i=i+1) index_delay[i]<=0;
    end else begin
      clear_pending<=0;
      if (flush || finishing) begin
        clear_pending<=!flush;
        busy<=0; collecting<=0; rms_failed<=0; replaying<=0;
        pass_valid<=0; final_square<=0; sum_saved<=0; spacing<=0;
        replay_index<=0;
      end else if (enable) begin
        final_square<={final_square[5:0],(valid_rms && in_last)};
        replay_first<={replay_first[4:0],(norm_issue && replay_index==0)};
        replay_last<={replay_last[4:0],(norm_issue && replay_index==length-1'b1)};
        if (spacing!=0) spacing<=spacing-1'b1;
        if (sum_valid) begin
          sum_saved<=sum_data;
          if (sum_error) rms_failed<=1;
        end
        if (epsilon_valid && epsilon_error) rms_failed<=1;
        if (inverse_valid && inverse_error) rms_failed<=1;
        if (exp_valid) exp_saved<=exp_data;
        for (i=1;i<3;i=i+1) gamma_delay[i]<=gamma_delay[i-1];
        for (i=1;i<6;i=i+1) index_delay[i]<=index_delay[i-1];
        if (norm_issue) begin
          gamma_delay[0]<=rms_gamma_q;
          index_delay[0]<=replay_index;
          if (inverse_valid) inverse_saved<=inverse_data;
          if (replay_index==length-1'b1) replaying<=0;
          else begin
            replaying<=1;
            replay_index<=replay_index+1'b1;
          end
        end
        if (accepted) begin
          if (!busy) begin
            busy<=1; mode<=in_mode; tag<=in_tag; element_index<=in_index;
            first<=in_first; last<=in_last; gate<=in_a; up<=in_b;
            pass_valid<=in_mode==4;
            pass_data<=in_a;
            pass_error<=(&in_a[30:23]);
          end
          if (valid_rms) begin
            spacing<=3;
            expected_index<=in_index[13:0]+1'b1;
            collecting<=!in_last;
            if ((&in_a[30:23]) || (&in_gamma[30:23])) rms_failed<=1;
            if (!busy) begin
              length<=in_length[13:0];
              reciprocal_length<=length_reciprocal;
              replay_index<=0;
            end
          end
          if (bad_metadata) begin
            mode<=7; collecting<=0; replaying<=0;
            pass_valid<=1; pass_error<=1; pass_data<=32'h7fc00000;
            tag<=in_tag; element_index<=in_index; first<=in_first; last<=in_last;
          end
        end
      end
    end
  end
  always @(posedge clk) begin
    if (rst_n && !(flush || finishing) && enable && accepted && valid_rms) begin
      rms_x[in_index[13:0]]<=in_a;
      rms_gamma[in_index[13:0]]<=in_gamma;
    end
    rms_x_q<=rms_x[rms_raddr];
    rms_gamma_q<=rms_gamma[rms_raddr];
  end
endmodule
