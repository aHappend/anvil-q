module anvil_q1_w4a16_gemv #(
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
  input wire [31:0] mem_rsp_rdata, input wire mem_rsp_error
);
  localparam SAFE_GROUP = GROUP_SIZE > 0 ? GROUP_SIZE : 1;
  reg [4:0] state;
  reg failed;
  reg [31:0] layer, pos, k, c, inputs, outputs, source_slot, target_slot;
  reg [2:0] projection;
  reg [31:0] qw, qz;
  reg [15:0] scales [0:7];
  reg [2:0] lane;
  reg signed [31:0] activation;
  wire signed [36:0] weight [0:7];
  wire [7:0] invalid;
  wire signed [68:0] product [0:7];
  reg signed [127:0] accumulators [0:7];
  integer i;
  genvar arithmetic_lane;
  wire complete, fault, request_transfer;
  wire [31:0] rd;
  wire [15:0] bias_f16;
  wire signed [31:0] bias_value;
  wire signed [31:0] output_value;
  assign bias_f16 = (complete && state==12) ? rd[15:0] : 16'd0;
  assign bias_value = anvil_q1_pkg::f16_q16(bias_f16);
  assign output_value = (rst_n && state==13) ? anvil_q1_pkg::sat32(
    anvil_q1_pkg::round_shift(accumulators[lane],16)) : 32'sd0;
  anvil_q1_parameters #(
    NUM_LAYERS,HIDDEN_SIZE,INTERMEDIATE_SIZE,NUM_Q_HEADS,NUM_KV_HEADS,
    HEAD_DIM,GROUP_SIZE,AWQ_BITS,1,MAX_SEQ_LEN) parameters_ok();
  reg request_valid, wr;
  reg [3:0] kind;
  reg [31:0] row, col, wd, ml;
  reg [2:0] mp;
  generate
    for(arithmetic_lane=0;arithmetic_lane<8;arithmetic_lane=arithmetic_lane+1) begin: lanes
      localparam [2:0] LOGICAL_LANE = arithmetic_lane;
      wire signed [68:0] activation_operand, weight_operand;
      anvil_q1_awq_dequant dequant(
        .qweight_word(qw),.qzero_word(qz),.scale_f16(scales[arithmetic_lane]),
        .lane(LOGICAL_LANE),.weight_q16_16(weight[arithmetic_lane]),
        .invalid(invalid[arithmetic_lane]));
      assign activation_operand = (rst_n && state==9) ?
        $signed({{37{activation[31]}},activation}) : 69'sd0;
      assign weight_operand = (rst_n && state==9) ?
        $signed({{32{weight[arithmetic_lane][36]}},weight[arithmetic_lane]}) : 69'sd0;
      assign product[arithmetic_lane] = activation_operand * weight_operand;
    end
  endgenerate
  assign cmd_ready = rst_n && state == 0;
  assign done = rst_n && state == 20;
  assign error = done && failed;
  assign mem_req_valid = request_valid;
  assign mem_req_write = wr;
  assign mem_req_kind = kind;
  assign mem_req_layer = ml;
  assign mem_req_proj = mp;
  assign mem_req_row = row;
  assign mem_req_col = col;
  assign mem_req_wdata = wd;
  assign mem_rsp_ready = rst_n &&
    (state==2 || state==4 || state==6 || state==8 || state==12 || state==14);
  assign request_transfer = mem_req_valid && mem_req_ready;
  assign complete = mem_rsp_ready && mem_rsp_valid;
  assign fault = complete && mem_rsp_error;
  assign rd = complete ? mem_rsp_rdata : 32'd0;
  always @* begin
    request_valid=0; wr=0; kind=0; row=0; col=0; wd=0; ml=0; mp=0;
    if (rst_n) case(state)
      1: begin request_valid=1; kind=8; row=source_slot; col=k; end
      3: begin request_valid=1; kind=1; ml=layer; mp=projection; row=k; col=c/8; end
      5: begin request_valid=1; kind=2; ml=layer; mp=projection; row=k/SAFE_GROUP; col=c/8; end
      7: begin request_valid=1; kind=3; ml=layer; mp=projection; row=k/SAFE_GROUP; col=c+{29'd0,lane}; end
      11: begin request_valid=1; kind=4; ml=layer; mp=projection; col=c+{29'd0,lane}; end
      13: begin
        request_valid=1; wr=1; kind=8; row=target_slot; col=c+{29'd0,lane};
        wd=output_value;
      end
      default: begin end
    endcase
  end
  always @(posedge clk) begin
    if (!rst_n) begin
      state<=0; failed<=0; layer<=0; pos<=0; k<=0; c<=0;
      inputs<=0; outputs<=0; source_slot<=0; target_slot<=0;
      projection<=0; qw<=0; qz<=0; lane<=0; activation<=0;
      for(i=0;i<8;i=i+1) begin scales[i]<=0; accumulators[i]<=0; end
    end else if(fault) begin failed<=1; state<=20; end
    else case(state)
      0: if(cmd_valid) begin
        failed<=0; layer<=cmd_layer; pos<=cmd_pos; projection<=cmd_proj;
        k<=0; c<=0; lane<=0;
        if(cmd_layer>=NUM_LAYERS || cmd_pos>=MAX_SEQ_LEN || cmd_proj>6)
          begin failed<=1; state<=19; end
        else begin
          inputs<=cmd_proj==6 ? INTERMEDIATE_SIZE : HIDDEN_SIZE;
          case(cmd_proj)
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
      1: if(request_transfer) state<=2;
      2: if(complete) begin activation<=rd; state<=3; end
      3: if(request_transfer) state<=4;
      4: if(complete) begin qw<=rd; lane<=0; state<=9; end
      5: if(request_transfer) state<=6;
      6: if(complete) begin qz<=rd; lane<=0; state<=7; end
      7: if(request_transfer) state<=8;
      8: if(complete) begin
        if(anvil_q1_pkg::f16_invalid(rd[15:0]) ||
           (rd[15] && rd[14:0]!=0)) begin failed<=1; state<=20; end
        else begin
          scales[lane]<=rd[15:0];
          if(lane==7) begin lane<=0; state<=1; end
          else begin lane<=lane+1; state<=7; end
        end
      end
      9: if(|invalid) begin failed<=1; state<=20; end
         else begin
           for(i=0;i<8;i=i+1)
             accumulators[i]<=accumulators[i]+{{59{product[i][68]}},product[i]};
           lane<=0;
           if(k+1<inputs) begin
             k<=k+1;
             if((k+1)/SAFE_GROUP!=k/SAFE_GROUP) state<=5;
             else state<=1;
           end
           else if(projection<3) state<=11;
           else state<=13;
         end
      11: if(request_transfer) state<=12;
      12: if(complete) begin
        if(anvil_q1_pkg::f16_invalid(rd[15:0])) begin failed<=1; state<=20; end
        else begin
          accumulators[lane]<=accumulators[lane];
          if(lane==7) begin lane<=0; state<=13; end
          else begin lane<=lane+1; state<=11; end
        end
      end
      13: if(request_transfer) state<=14;
      14: if(complete) begin
        if(lane<7) begin
          lane<=lane+1;
          state<=13;
        end
        else if(c+8<outputs) begin c<=c+8; k<=0; lane<=0; state<=16; end
        else state<=20;
      end
      16: begin
        qw<=0; qz<=0; activation<=0; lane<=0;
        for(i=0;i<8;i=i+1) begin scales[i]<=0; accumulators[i]<=0; end
        state<=5;
      end
      19: state<=20;
      20: begin
        qw<=0; qz<=0; activation<=0; lane<=0;
        for(i=0;i<8;i=i+1) begin scales[i]<=0; accumulators[i]<=0; end
        state<=0;
      end
      default: state<=0;
    endcase
  end
endmodule
