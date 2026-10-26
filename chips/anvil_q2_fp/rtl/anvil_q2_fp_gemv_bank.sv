module anvil_q2_fp_gemv_bank #(
  parameter NUM_LAYERS=28, HIDDEN_SIZE=1536, INTERMEDIATE_SIZE=8960,
  NUM_KV_HEADS=2, HEAD_DIM=128, GROUP_SIZE=128, MAX_SEQ_LEN=32768,
  BANK_ID=0, BANKS=4, FP_FORMAT=0, WEIGHT_MODE=0
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
  output wire lane_in_valid, input wire lane_in_ready,
  output wire [15:0] lane_in_a, output wire [127:0] lane_in_b,
  output wire lane_in_first, lane_in_last,
  input wire lane_out_valid, output wire lane_out_ready,
  input wire [255:0] lane_out_sum, input wire lane_out_last
);
  import anvil_q2_fp_pkg::*;
  localparam IDLE=0, GROUP_START=1, ZERO_REQ=2, ZERO_WAIT=3,
    SCALE_REQ=4, SCALE_WAIT=5, ACT_REQ=6, ACT_WAIT=7, ACT_CONVERT=8,
    WEIGHT_REQ=9, WEIGHT_WAIT=10, DEQUANT=11, DEQUANT_WAIT=12,
    FEED=13, SUM_WAIT=14, BIAS_REQ=15, BIAS_WAIT=16, BIAS_ADD=17,
    WRITE_REQ=18, WRITE_WAIT=19, OUTPUT=20, BAD_COMMAND=21;
  reg [4:0] state;
  reg failed;
  reg [31:0] layer, position, column, row_base, inputs, outputs;
  reg [31:0] source_slot, target_slot, group_index, group_offset;
  reg [2:0] projection, element;
  reg [31:0] qweight, qzero, activation32, bias32;
  reg [15:0] activation16, scales [0:7], weights [0:7];
  reg [31:0] sums [0:7];
  reg issue, write;
  reg [3:0] kind;
  reg [31:0] address_layer, address_row, address_col, write_data;
  reg [2:0] address_proj;
  wire idle, complete, fault;
  wire [31:0] read_data;
  wire [15:0] converted_activation=narrow16(activation32,FP_FORMAT);
  wire dequant_ready, dequant_valid, dequant_error;
  wire [15:0] dequant_weight;
  wire [31:0] bias_sum=fp_add(sums[element],bias32);
  reg bad_sum;
  integer i;
  always @* begin
    bad_sum=0;
    for (integer j=0;j<8;j=j+1)
      if (row_base+j<outputs && !fp_is_finite(lane_out_sum[j*32+:32])) bad_sum=1;
  end
  assign cmd_ready=rst_n && state==IDLE;
  assign done=rst_n && state==OUTPUT;
  assign error=done && failed;
  assign lane_in_valid=rst_n && state==FEED;
  assign lane_in_a=rst_n ? activation16 : 16'd0;
  assign lane_in_first=rst_n && column==0;
  assign lane_in_last=rst_n && column+1==inputs;
  assign lane_out_ready=rst_n && state==SUM_WAIT;
  genvar j;
  generate for (j=0;j<8;j=j+1) begin: weight_outputs
    assign lane_in_b[j*16+:16]=rst_n ? weights[j] : 16'd0;
  end endgenerate
  anvil_q2_fp_awq_dequant #(.FP_FORMAT(FP_FORMAT)) dequant(
    .clk(clk),.rst_n(rst_n),.in_valid(rst_n && state==DEQUANT),
    .in_ready(dequant_ready),.in_qweight(qweight),.in_qzero(qzero),
    .in_scale(scales[element]),.in_lane(element),.out_valid(dequant_valid),
    .out_ready(1'b1),.out_weight(dequant_weight),.out_error(dequant_error));
  anvil_q2_mem_port memory_port(
    .clk(clk),.rst_n(rst_n),.issue(issue),.write(write),.kind(kind),
    .layer(address_layer),.proj(address_proj),.row(address_row),.col(address_col),
    .wdata(write_data),.idle(idle),.complete(complete),.rdata(read_data),.fault(fault),
    .mem_req_valid(mem_req_valid),.mem_req_ready(mem_req_ready),
    .mem_req_write(mem_req_write),.mem_req_kind(mem_req_kind),
    .mem_req_layer(mem_req_layer),.mem_req_proj(mem_req_proj),
    .mem_req_row(mem_req_row),.mem_req_col(mem_req_col),.mem_req_wdata(mem_req_wdata),
    .mem_rsp_valid(mem_rsp_valid),.mem_rsp_ready(mem_rsp_ready),
    .mem_rsp_rdata(mem_rsp_rdata),.mem_rsp_error(mem_rsp_error));
  always @* begin
    issue=0; write=0; kind=0; address_layer=0; address_proj=0;
    address_row=0; address_col=0; write_data=0;
    if (rst_n && idle) case (state)
      ZERO_REQ: begin
        issue=1; kind=2; address_layer=layer; address_proj=projection;
        address_row=group_index; address_col=row_base >> 3;
      end
      SCALE_REQ: begin
        issue=1; kind=3; address_layer=layer; address_proj=projection;
        address_row=group_index; address_col=row_base+{29'd0,element};
      end
      ACT_REQ: begin issue=1; kind=8; address_row=source_slot; address_col=column; end
      WEIGHT_REQ: begin
        issue=1; kind=1; address_layer=layer; address_proj=projection;
        address_row=column;
        address_col=WEIGHT_MODE ? (row_base >> 3) : row_base+{29'd0,element};
      end
      BIAS_REQ: begin
        issue=1; kind=4; address_layer=layer; address_proj=projection;
        address_col=row_base+{29'd0,element};
      end
      WRITE_REQ: begin
        issue=1; write=1; kind=8; address_row=target_slot;
        address_col=row_base+{29'd0,element}; write_data=sums[element];
      end
      default: begin end
    endcase
  end
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; failed<=0; layer<=0; position<=0; column<=0; row_base<=0;
      inputs<=0; outputs<=0; source_slot<=0; target_slot<=0; group_index<=0;
      group_offset<=0; projection<=0; element<=0; qweight<=0; qzero<=0;
      activation32<=0; activation16<=0; bias32<=0;
      for (i=0;i<8;i=i+1) begin scales[i]<=0; weights[i]<=0; sums[i]<=0; end
    end else if (fault) begin failed<=1; state<=OUTPUT; end
    else case (state)
      IDLE: if (cmd_valid) begin
        failed<=0; layer<=cmd_layer; position<=cmd_pos; projection<=cmd_proj;
        row_base<=8*BANK_ID;
        if (cmd_layer>=NUM_LAYERS || cmd_pos>=MAX_SEQ_LEN || cmd_proj>6) begin
          failed<=1; state<=BAD_COMMAND;
        end else begin
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
          state<=GROUP_START;
        end
      end
      GROUP_START: begin
        column<=0; group_index<=0; group_offset<=0; element<=0;
        for (i=0;i<8;i=i+1) begin scales[i]<=0; weights[i]<=0; sums[i]<=0; end
        if (row_base>=outputs) state<=OUTPUT;
        else if (WEIGHT_MODE==1) state<=ZERO_REQ;
        else state<=ACT_REQ;
      end
      ZERO_REQ: if (issue) state<=ZERO_WAIT;
      ZERO_WAIT: if (complete) begin qzero<=read_data; element<=0; state<=SCALE_REQ; end
      SCALE_REQ: if (issue) state<=SCALE_WAIT;
      SCALE_WAIT: if (complete) begin
        if (read_data[31:16]!=0 ||
            !fp_is_finite(expand16(read_data[15:0],FP_FORMAT)) ||
            (read_data[15] && (|read_data[14:0]))) begin failed<=1; state<=OUTPUT; end
        else begin
          scales[element]<=read_data[15:0];
          if (element==7 || row_base+{29'd0,element}+1>=outputs) begin
            element<=0; state<=ACT_REQ;
          end else begin element<=element+1'b1; state<=SCALE_REQ; end
        end
      end
      ACT_REQ: if (issue) state<=ACT_WAIT;
      ACT_WAIT: if (complete) begin
        if (!fp_is_finite(read_data)) begin failed<=1; state<=OUTPUT; end
        else begin activation32<=read_data; state<=ACT_CONVERT; end
      end
      ACT_CONVERT: begin
        if (!fp_is_finite(expand16(converted_activation,FP_FORMAT))) begin
          failed<=1; state<=OUTPUT;
        end else begin activation16<=converted_activation; element<=0; state<=WEIGHT_REQ; end
      end
      WEIGHT_REQ: if (issue) state<=WEIGHT_WAIT;
      WEIGHT_WAIT: if (complete) begin
        if (WEIGHT_MODE==1) begin qweight<=read_data; element<=0; state<=DEQUANT; end
        else if (read_data[31:16]!=0 ||
                 !fp_is_finite(expand16(read_data[15:0],FP_FORMAT))) begin
          failed<=1; state<=OUTPUT;
        end else begin
          weights[element]<=read_data[15:0];
          if (element==7 || row_base+{29'd0,element}+1>=outputs) state<=FEED;
          else begin element<=element+1'b1; state<=WEIGHT_REQ; end
        end
      end
      DEQUANT: if (dequant_ready) state<=DEQUANT_WAIT;
      DEQUANT_WAIT: if (dequant_valid) begin
        if (dequant_error) begin failed<=1; state<=OUTPUT; end
        else begin
          weights[element]<=dequant_weight;
          if (element==7 || row_base+{29'd0,element}+1>=outputs) state<=FEED;
          else begin element<=element+1'b1; state<=DEQUANT; end
        end
      end
      FEED: if (lane_in_ready) state<=SUM_WAIT;
      SUM_WAIT: if (lane_out_valid) begin
        if (bad_sum || lane_out_last!=(column+1==inputs)) begin failed<=1; state<=OUTPUT; end
        else begin
          for (i=0;i<8;i=i+1) sums[i]<=lane_out_sum[i*32+:32];
          if (column+1<inputs) begin
            column<=column+1;
            if (group_offset==GROUP_SIZE-1) begin
              group_offset<=0; group_index<=group_index+1;
              if (WEIGHT_MODE==1) state<=ZERO_REQ;
              else state<=ACT_REQ;
            end else begin group_offset<=group_offset+1; state<=ACT_REQ; end
          end else begin
            element<=0;
            if (projection<3) state<=BIAS_REQ; else state<=WRITE_REQ;
          end
        end
      end
      BIAS_REQ: if (issue) state<=BIAS_WAIT;
      BIAS_WAIT: if (complete) begin
        if (read_data[31:16]!=0 ||
            !fp_is_finite(expand16(read_data[15:0],FP_FORMAT))) begin
          failed<=1; state<=OUTPUT;
        end else begin bias32<=expand16(read_data[15:0],FP_FORMAT); state<=BIAS_ADD; end
      end
      BIAS_ADD: begin
        if (!fp_is_finite(bias_sum)) begin failed<=1; state<=OUTPUT; end
        else begin
          sums[element]<=bias_sum;
          if (element==7 || row_base+{29'd0,element}+1>=outputs) begin
            element<=0; state<=WRITE_REQ;
          end else begin element<=element+1'b1; state<=BIAS_REQ; end
        end
      end
      WRITE_REQ: if (issue) state<=WRITE_WAIT;
      WRITE_WAIT: if (complete) begin
        if (element<7 && row_base+{29'd0,element}+1<outputs) begin
          element<=element+1'b1; state<=WRITE_REQ;
        end else if (row_base+8*BANKS<outputs) begin
          row_base<=row_base+8*BANKS; state<=GROUP_START;
        end else state<=OUTPUT;
      end
      BAD_COMMAND: state<=OUTPUT;
      OUTPUT: state<=IDLE;
      default: begin failed<=1; state<=OUTPUT; end
    endcase
  end
endmodule
