module anvil_q1_fp_gemv #(
  parameter NUM_LAYERS=24, HIDDEN_SIZE=896, INTERMEDIATE_SIZE=4864,
  NUM_Q_HEADS=14, NUM_KV_HEADS=2, HEAD_DIM=64, GROUP_SIZE=128,
  AWQ_BITS=4, MAX_SEQ_LEN=32768
)(
  input wire clk, rst_n, cmd_valid, output wire cmd_ready,
  input wire [31:0] cmd_layer, cmd_pos, input wire [2:0] cmd_proj,
  output wire done, error,
  output wire mem_req_valid, input wire mem_req_ready,
  output wire mem_req_write, output wire [3:0] mem_req_kind,
  output wire [31:0] mem_req_layer, output wire [2:0] mem_req_proj,
  output wire [31:0] mem_req_row, mem_req_col, mem_req_wdata,
  input wire mem_rsp_valid, output wire mem_rsp_ready,
  input wire [31:0] mem_rsp_rdata, input wire mem_rsp_error,
  input wire [1:0] cmd_precision
);
  reg [5:0] state;
  reg failed;
  reg [1:0] precision;
  reg [31:0] layer, pos, k, c, inputs, outputs, source_slot, target_slot;
  reg [31:0] group_index, group_offset;
  reg [2:0] projection, lane;
  reg [31:0] qw, qz;
  reg [15:0] scales [0:7];
  reg signed [31:0] activation;
  wire signed [36:0] weight [0:7];
  wire [7:0] invalid;
  reg signed [36:0] weight_pipe [0:7];
  wire signed [68:0] product [0:7];
  reg signed [68:0] product_pipe [0:7];
  reg signed [127:0] accumulators [0:7];
  reg [15:0] native_weights [0:7];
  reg [31:0] native_accumulators [0:7];
  wire [7:0] native_valid;
  wire [31:0] native_result [0:7];
  wire [4:0] native_status [0:7];
  wire [7:0] native_fatal;
  reg [31:0] native_bias;
  wire bias_valid;
  wire [31:0] bias_result;
  wire [4:0] bias_status;
  wire complete, fault, request_transfer;
  wire [31:0] rd, native_read;
  wire [15:0] bias_f16;
  wire signed [31:0] bias_value, output_value;
  reg request_valid, wr;
  reg [3:0] kind;
  reg [31:0] row, col, wd, ml;
  reg [2:0] mp;
  integer i;
  genvar g;

  assign bias_f16=(complete && state==12) ? rd[15:0] : 16'd0;
  assign bias_value=anvil_q1_fp_compat_pkg::f16_q16(bias_f16);
  assign native_read=anvil_q1_fp_pkg::widen16(rd[15:0],precision);
  assign output_value=(rst_n && state==13) ? anvil_q1_fp_compat_pkg::sat32(
    anvil_q1_fp_compat_pkg::round_shift(accumulators[lane],16)) : 32'sd0;
  anvil_q1_parameters #(
    NUM_LAYERS,HIDDEN_SIZE,INTERMEDIATE_SIZE,NUM_Q_HEADS,NUM_KV_HEADS,
    HEAD_DIM,GROUP_SIZE,AWQ_BITS,1,MAX_SEQ_LEN) parameters_ok();
  generate for (g=0;g<8;g=g+1) begin: lanes
    localparam [2:0] LOGICAL_LANE=g;
    anvil_q1_fp_awq_dequant dequant(
      .qweight_word(qw),.qzero_word(qz),.scale_f16(scales[g]),
      .lane(LOGICAL_LANE),.weight_q16_16(weight[g]),.invalid(invalid[g]));
    assign product[g]=$signed(activation)*$signed(weight_pipe[g]);
    anvil_q1_fp_dot8_mixed native_dot(
      .clk(clk),.rst_n(rst_n),.in_valid(rst_n && state==23),
      .in_precision(precision),.a({224'd0,activation}),.b({112'd0,native_weights[g]}),
      .lane_mask(8'b00000001),.acc_in(native_accumulators[g]),
      .out_valid(native_valid[g]),.result(native_result[g]),.status(native_status[g]));
    assign native_fatal[g]=|native_status[g][4:2];
  end endgenerate
  anvil_q1_fp_add bias_add(
    .clk(clk),.rst_n(rst_n),.in_valid(rst_n && state==25),
    .a(native_accumulators[lane]),.b(native_bias),
    .out_valid(bias_valid),.result(bias_result),.status(bias_status));

  assign cmd_ready=rst_n && state==0;
  assign done=rst_n && state==20;
  assign error=done && failed;
  assign mem_req_valid=request_valid;
  assign mem_req_write=wr;
  assign mem_req_kind=kind;
  assign mem_req_layer=ml;
  assign mem_req_proj=mp;
  assign mem_req_row=row;
  assign mem_req_col=col;
  assign mem_req_wdata=wd;
  assign mem_rsp_ready=rst_n &&
    (state==2 || state==4 || state==6 || state==8 || state==12 || state==14 || state==22);
  assign request_transfer=mem_req_valid && mem_req_ready;
  assign complete=mem_rsp_ready && mem_rsp_valid;
  assign fault=complete && mem_rsp_error;
  assign rd=complete ? mem_rsp_rdata : 32'd0;
  always @* begin
    request_valid=0; wr=0; kind=0; row=0; col=0; wd=0; ml=0; mp=0;
    if (rst_n) case (state)
      1: begin request_valid=1; kind=8; row=source_slot; col=k; end
      3: begin request_valid=1; kind=1; ml=layer; mp=projection; row=k; col=c>>3; end
      5: begin request_valid=1; kind=2; ml=layer; mp=projection; row=group_index; col=c>>3; end
      7: begin request_valid=1; kind=3; ml=layer; mp=projection; row=group_index; col=c+{29'd0,lane}; end
      11: begin request_valid=1; kind=4; ml=layer; mp=projection; col=c+{29'd0,lane}; end
      13: begin
        request_valid=1; wr=1; kind=8; row=target_slot; col=c+{29'd0,lane};
        wd=precision==0 ? output_value : native_accumulators[lane];
      end
      21: begin request_valid=1; kind=12; ml=layer; mp=projection; row=k; col=c+{29'd0,lane}; end
      default: begin end
    endcase
  end

  always @(posedge clk) begin
    if (!rst_n) begin
      state<=0; failed<=0; precision<=0; layer<=0; pos<=0; k<=0; c<=0;
      inputs<=0; outputs<=0; source_slot<=0; target_slot<=0;
      group_index<=0; group_offset<=0; projection<=0; qw<=0; qz<=0;
      lane<=0; activation<=0; native_bias<=0;
      for (i=0;i<8;i=i+1) begin
        scales[i]<=0; accumulators[i]<=0; weight_pipe[i]<=0; product_pipe[i]<=0;
        native_weights[i]<=0; native_accumulators[i]<=0;
      end
    end else if (fault) begin failed<=1; state<=20; end
    else case (state)
      0: if (cmd_valid) begin
        failed<=0; layer<=cmd_layer; pos<=cmd_pos; projection<=cmd_proj;
        precision<=cmd_precision; k<=0; c<=0; lane<=0;
        if (cmd_layer>=NUM_LAYERS || cmd_pos>=MAX_SEQ_LEN || cmd_proj>6 || cmd_precision==3)
          begin failed<=1; state<=19; end
        else begin
          inputs<=cmd_proj==6 ? INTERMEDIATE_SIZE : HIDDEN_SIZE;
          case (cmd_proj)
            0: begin outputs<=HIDDEN_SIZE; source_slot<=1; target_slot<=2; end
            1: begin outputs<=NUM_KV_HEADS*HEAD_DIM; source_slot<=1; target_slot<=3; end
            2: begin outputs<=NUM_KV_HEADS*HEAD_DIM; source_slot<=1; target_slot<=4; end
            3: begin outputs<=HIDDEN_SIZE; source_slot<=5; target_slot<=6; end
            4: begin outputs<=INTERMEDIATE_SIZE; source_slot<=8; target_slot<=9; end
            5: begin outputs<=INTERMEDIATE_SIZE; source_slot<=8; target_slot<=10; end
            default: begin outputs<=HIDDEN_SIZE; source_slot<=11; target_slot<=12; end
          endcase
          state<=16;
        end
      end
      1: if (request_transfer) state<=2;
      2: if (complete) begin
        if (precision!=0 && rd[30:23]==255) begin failed<=1; state<=20; end
        else begin
          activation<=rd; lane<=0;
          if (precision==0) state<=3; else state<=21;
        end
      end
      3: if (request_transfer) state<=4;
      4: if (complete) begin qw<=rd; lane<=0; state<=9; end
      5: if (request_transfer) state<=6;
      6: if (complete) begin qz<=rd; lane<=0; state<=7; end
      7: if (request_transfer) state<=8;
      8: if (complete) begin
        if (anvil_q1_fp_compat_pkg::f16_invalid(rd[15:0]) || (rd[15] && rd[14:0]!=0))
          begin failed<=1; state<=20; end
        else begin
          scales[lane]<=rd[15:0];
          if (lane==7) begin lane<=0; state<=1; end
          else begin lane<=lane+1; state<=7; end
        end
      end
      9: if (|invalid) begin failed<=1; state<=20; end
         else begin
           for (i=0;i<8;i=i+1) weight_pipe[i]<=weight[i];
           state<=17;
         end
      17: begin
        for (i=0;i<8;i=i+1) product_pipe[i]<=product[i];
        state<=18;
      end
      18: begin
        for (i=0;i<8;i=i+1)
          accumulators[i]<=accumulators[i]+{{59{product_pipe[i][68]}},product_pipe[i]};
        lane<=0;
        if (k+1<inputs) begin
          k<=k+1;
          if (group_offset+1==GROUP_SIZE) begin
            group_offset<=0; group_index<=group_index+1; state<=5;
          end else begin group_offset<=group_offset+1; state<=1; end
        end else if (projection<3) state<=11;
        else state<=13;
      end
      11: if (request_transfer) state<=12;
      12: if (complete) begin
        if (precision==0) begin
          if (anvil_q1_fp_compat_pkg::f16_invalid(rd[15:0])) begin failed<=1; state<=20; end
          else begin
            accumulators[lane]<=accumulators[lane]+
              ($signed({{96{bias_value[31]}},bias_value}) <<< 16);
            if (lane==7) begin lane<=0; state<=13; end
            else begin lane<=lane+1; state<=11; end
          end
        end else if (rd[31:16]!=0 || native_read[30:23]==255)
          begin failed<=1; state<=20; end
        else begin native_bias<=native_read; state<=25; end
      end
      13: if (request_transfer) state<=14;
      14: if (complete) begin
        if (lane<7) begin lane<=lane+1; state<=13; end
        else if (c+8<outputs) begin c<=c+8; k<=0; lane<=0; state<=16; end
        else state<=20;
      end
      16: begin
        qw<=0; qz<=0; activation<=0; lane<=0; group_index<=0; group_offset<=0;
        for (i=0;i<8;i=i+1) begin
          scales[i]<=0; accumulators[i]<=0; native_weights[i]<=0; native_accumulators[i]<=0;
        end
        if (precision==0) state<=5; else state<=1;
      end
      19: state<=20;
      20: begin
        qw<=0; qz<=0; activation<=0; lane<=0; native_bias<=0;
        for (i=0;i<8;i=i+1) begin
          scales[i]<=0; accumulators[i]<=0; weight_pipe[i]<=0; product_pipe[i]<=0;
          native_weights[i]<=0; native_accumulators[i]<=0;
        end
        state<=0;
      end
      21: if (request_transfer) state<=22;
      22: if (complete) begin
        if (rd[31:16]!=0 || native_read[30:23]==255) begin failed<=1; state<=20; end
        else begin
          native_weights[lane]<=rd[15:0];
          if (lane==7) begin lane<=0; state<=23; end
          else begin lane<=lane+1; state<=21; end
        end
      end
      23: state<=24;
      24: if (&native_valid) begin
        if (|native_fatal) begin failed<=1; state<=20; end
        else begin
          for (i=0;i<8;i=i+1) native_accumulators[i]<=native_result[i];
          lane<=0;
          if (k+1<inputs) begin k<=k+1; state<=1; end
          else if (projection<3) state<=11;
          else state<=13;
        end
      end
      25: state<=26;
      26: if (bias_valid) begin
        if (|bias_status[4:2]) begin failed<=1; state<=20; end
        else begin
          native_accumulators[lane]<=bias_result;
          if (lane==7) begin lane<=0; state<=13; end
          else begin lane<=lane+1; state<=11; end
        end
      end
      default: state<=0;
    endcase
  end
endmodule
