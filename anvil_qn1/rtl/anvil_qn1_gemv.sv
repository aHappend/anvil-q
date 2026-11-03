module anvil_qn1_gemv #(
  parameter GROUP_SIZE=128, MAX_INPUT=9728, MAX_OUTPUT=151936
) (
  input wire clk, rst_n, flush, start_valid,
  output wire start_ready,
  input wire start_w4,
  input wire [31:0] start_input_extent, start_output_extent, start_layer, start_source_slot,
  input wire [2:0] start_proj,
  output wire out_valid,
  input wire out_ready,
  output wire [31:0] out_index, out_fp32,
  output wire [15:0] out_bf16,
  output wire done, error,
  output wire req_valid,
  input wire req_ready,
  output wire [3:0] req_kind,
  output wire [31:0] req_layer, req_row, req_col, req_tag,
  output wire [2:0] req_proj,
  input wire rsp_valid,
  output wire rsp_ready,
  input wire [31:0] rsp_data, rsp_tag,
  input wire rsp_error,
  output wire tensor_valid,
  input wire tensor_ready,
  output wire tensor_w4,
  output wire [1023:0] tensor_q, tensor_z,
  output wire [4095:0] tensor_scale, tensor_activation, tensor_weight,
  output wire [255:0] tensor_mask,
  output wire [31:0] tensor_tag,
  input wire tensor_rsp_valid,
  output wire tensor_rsp_ready,
  input wire [31:0] tensor_sum, tensor_rsp_tag,
  input wire tensor_error
);
  import anvil_qn1_pkg::*;
  generate if (GROUP_SIZE>=8 && GROUP_SIZE<=128 &&
      (GROUP_SIZE & (GROUP_SIZE-1))==0 && MAX_INPUT>=1 && MAX_INPUT<=9728 &&
      MAX_OUTPUT>=1 && MAX_OUTPUT<=151936) begin: legal
    localparam GS=$clog2(GROUP_SIZE);
    localparam GROUPS=256 >> GS;
    localparam IDLE=0, INITIALIZE=1, GROUP_LOAD=2, DATA_LOAD=3;
    localparam TENSOR_REQ=4, TENSOR_WAIT=5, ACCUMULATE=6, ROUND=7;
    localparam OUTPUT=8, FINISH=9, FAULT=10;
    reg [3:0] state;
    reg w4, waiting, done_reg, error_reg;
    reg [31:0] input_extent, output_extent, layer, source_slot, output_row, base;
    reg [2:0] projection;
    reg [9:0] issued, received;
    reg [1279:0] seen;
    reg [1023:0] quantized;
    reg [4095:0] activations, weights;
    reg [31:0] zeros [0:GROUPS-1];
    reg [15:0] scales [0:GROUPS-1];
    reg [31:0] accumulator, partial, result;
    reg [15:0] rounded_result;
    wire [31:0] remaining=input_extent-base;
    wire [8:0] active_lanes=remaining>=256 ? 9'd256 : remaining[8:0];
    wire [5:0] active_groups=6'(active_lanes >> GS);
    wire [9:0] request_count=state==GROUP_LOAD ?
      {3'd0,active_groups,1'b0} : {active_lanes,1'b0};
    wire load_state=state==GROUP_LOAD || state==DATA_LOAD;
    wire [7:0] request_index=issued[8:1];
    wire [2:0] request_type=state==GROUP_LOAD ?
      (issued[0] ? 3'd3 : 3'd2) : (issued[0] ? (w4 ? 3'd1 : 3'd4) : 3'd0);
    wire [7:0] response_index=rsp_tag[7:0];
    wire [2:0] response_type=rsp_tag[10:8];
    wire [10:0] seen_address=rsp_tag[10:0];
    wire expected_type=state==GROUP_LOAD ? (response_type==2 || response_type==3) :
      (response_type==0 || response_type==(w4 ? 3'd1 : 3'd4));
    wire [9:0] response_ordinal={1'b0,response_index,
      state==GROUP_LOAD ? response_type==3 : response_type!=0};
    wire response_in_range=state==GROUP_LOAD ? response_index<active_groups :
      {1'b0,response_index}<active_lanes;
    wire reserved_bad=(response_type==0 || response_type==3 || response_type==4) &&
      (rsp_data[31:16]!=0 || bf16_invalid(rsp_data[15:0]));
    wire scale_bad=response_type==3 && bf16_scale_invalid(rsp_data[15:0]);
    wire response_bad=rsp_valid && (!load_state || rsp_error || rsp_tag[31:11]!=0 ||
      !expected_type || !response_in_range || response_ordinal>=issued ||
      seen_address>=1280 || seen[seen_address] || reserved_bad || scale_bad);
    wire tensor_bad=tensor_rsp_valid && (state!=TENSOR_WAIT ||
      tensor_error || tensor_rsp_tag!=output_row || fp32_invalid(tensor_sum));
    wire [16:0] rounded=round_bf16(accumulator);
    wire alu_ready, alu_valid, alu_error;
    wire [31:0] alu_data;
    anvil_qn1_scalar accumulator_add (
      .clk(clk),.rst_n(rst_n),.flush(flush || state==FAULT),
      .in_valid(state==ACCUMULATE && !waiting),.in_ready(alu_ready),
      .in_op(3'd0),.in_a(accumulator),.in_b(partial),.in_error(1'b0),
      .out_valid(alu_valid),.out_ready(waiting),.out_data(alu_data),.out_error(alu_error)
    );
    assign start_ready=rst_n && !flush && state==IDLE && !done_reg && !error_reg;
    assign out_valid=rst_n && !flush && !response_bad && !tensor_bad && state==OUTPUT;
    assign out_index=out_valid ? output_row : 32'd0;
    assign out_fp32=out_valid ? result : 32'd0;
    assign out_bf16=out_valid ? rounded_result : 16'd0;
    assign done=rst_n && !flush && done_reg;
    assign error=rst_n && !flush && (state==FAULT || error_reg);
    assign req_valid=rst_n && !flush && load_state && issued<request_count &&
      !response_bad && !tensor_bad;
    assign req_kind=!req_valid ? 4'd0 : request_type==0 ? 4'd8 :
      request_type==1 ? 4'd1 : request_type==2 ? 4'd2 : request_type==3 ? 4'd3 : 4'd0;
    assign req_layer=req_valid && request_type!=0 && request_type!=4 ? layer : 32'd0;
    assign req_proj=req_valid && request_type!=0 && request_type!=4 ? projection : 3'd0;
    assign req_row=!req_valid ? 32'd0 : request_type==0 ? source_slot :
      request_type==1 ? base+{24'd0,request_index} :
      request_type==4 ? output_row : (base >> GS)+{24'd0,request_index};
    assign req_col=!req_valid ? 32'd0 :
      (request_type==0 || request_type==4) ? base+{24'd0,request_index} :
      request_type==3 ? output_row : output_row >> 3;
    assign req_tag=req_valid ? {21'd0,request_type,request_index} : 32'd0;
    assign rsp_ready=rst_n && !flush;
    assign tensor_valid=rst_n && !flush && !response_bad && !tensor_bad && state==TENSOR_REQ;
    assign tensor_w4=tensor_valid && w4;
    assign tensor_q=tensor_valid ? quantized : 1024'd0;
    assign tensor_activation=tensor_valid ? activations : 4096'd0;
    assign tensor_weight=tensor_valid ? weights : 4096'd0;
    assign tensor_tag=tensor_valid ? output_row : 32'd0;
    assign tensor_rsp_ready=rst_n && !flush && state==TENSOR_WAIT;
    genvar lane;
    for (lane=0;lane<256;lane=lane+1) begin: lanes
      wire [31:0] zero_word=zeros[lane >> GS];
      wire [4:0] shift=awq_lane_shift(output_row[2:0]);
      assign tensor_z[lane*4+:4]=tensor_valid && w4 ? 4'(zero_word >> shift) : 4'd0;
      assign tensor_scale[lane*16+:16]=tensor_valid && w4 ? scales[lane >> GS] : 16'd0;
      assign tensor_mask[lane]=tensor_valid && lane<active_lanes;
    end
    integer group_index;
    wire [4:0] nibble_shift=awq_lane_shift(output_row[2:0]);
    wire [3:0] returned_nibble=4'(rsp_data >> nibble_shift);
    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        state<=IDLE; w4<=0; waiting<=0; done_reg<=0; error_reg<=0;
        input_extent<=0; output_extent<=0; layer<=0; source_slot<=0;
        output_row<=0; base<=0; projection<=0; issued<=0; received<=0;
        seen<=0; quantized<=0; activations<=0; weights<=0;
        accumulator<=0; partial<=0; result<=0; rounded_result<=0;
        for (group_index=0;group_index<GROUPS;group_index=group_index+1) begin
          zeros[group_index]<=0; scales[group_index]<=0;
        end
      end else if (flush) begin
        state<=IDLE; waiting<=0; done_reg<=0; error_reg<=0;
      end else begin
        done_reg<=0; error_reg<=0;
        if (response_bad || tensor_bad) state<=FAULT;
        else begin
          if (req_valid && req_ready) issued<=issued+1'b1;
          if (rsp_valid && load_state) begin
            seen[seen_address]<=1; received<=received+1'b1;
            case (response_type)
              0: activations[response_index*16+:16]<=rsp_data[15:0];
              1: quantized[response_index*4+:4]<=returned_nibble;
              2: zeros[response_index]<=rsp_data;
              3: scales[response_index]<=rsp_data[15:0];
              4: weights[response_index*16+:16]<=rsp_data[15:0];
              default: begin end
            endcase
          end
          if (state==ACCUMULATE && !waiting && alu_ready) waiting<=1;
          case (state)
            IDLE: if (start_valid && start_ready) begin
              input_extent<=start_input_extent; output_extent<=start_output_extent;
              layer<=start_layer; source_slot<=start_source_slot; projection<=start_proj;
              w4<=start_w4; output_row<=0; base<=0; accumulator<=0; waiting<=0;
              if (start_input_extent<1 || start_input_extent>MAX_INPUT ||
                  start_output_extent<1 || start_output_extent>MAX_OUTPUT ||
                  (start_w4 && ((start_input_extent & (GROUP_SIZE-1))!=0 || start_proj>6)))
                state<=FAULT;
              else state<=INITIALIZE;
            end
            INITIALIZE: begin
              quantized<=0; activations<=0; weights<=0;
              issued<=0; received<=0; seen<=0;
              if (w4) state<=GROUP_LOAD;
              else state<=DATA_LOAD;
            end
            GROUP_LOAD: if (received==request_count && issued==request_count) begin
              issued<=0; received<=0; seen<=0; state<=DATA_LOAD;
            end
            DATA_LOAD: if (received==request_count && issued==request_count) state<=TENSOR_REQ;
            TENSOR_REQ: if (tensor_valid && tensor_ready) state<=TENSOR_WAIT;
            TENSOR_WAIT: if (tensor_rsp_valid && tensor_rsp_ready) begin
              partial<=tensor_sum; state<=ACCUMULATE;
            end
            ACCUMULATE: if (alu_valid && waiting) begin
              waiting<=0;
              if (alu_error) state<=FAULT;
              else begin
                accumulator<=alu_data;
                if (base+{23'd0,active_lanes}==input_extent) state<=ROUND;
                else begin base<=base+256; state<=INITIALIZE; end
              end
            end
            ROUND: begin
              result<=accumulator;
              // Vocabulary logits remain binary32; their BF16 conversion is not an operation.
              if (w4 && rounded[16]) state<=FAULT;
              else begin rounded_result<=w4 ? rounded[15:0] : 16'd0; state<=OUTPUT; end
            end
            OUTPUT: if (out_valid && out_ready) begin
              if (output_row==output_extent-1) state<=FINISH;
              else begin
                output_row<=output_row+1'b1; base<=0; accumulator<=0; state<=INITIALIZE;
              end
            end
            FINISH: begin done_reg<=1; state<=IDLE; end
            FAULT: begin error_reg<=1; waiting<=0; state<=IDLE; end
            default: state<=FAULT;
          endcase
        end
      end
    end
  end else begin: invalid
    initial $fatal(1,"ANVIL_QN1 PARAMETER ERROR: GEMV geometry");
    assign start_ready=0; assign out_valid=0; assign out_index=0; assign out_fp32=0;
    assign out_bf16=0; assign done=0; assign error=0; assign req_valid=0;
    assign req_kind=0; assign req_layer=0; assign req_row=0; assign req_col=0;
    assign req_tag=0; assign req_proj=0; assign rsp_ready=0; assign tensor_valid=0;
    assign tensor_w4=0; assign tensor_q=0; assign tensor_z=0; assign tensor_scale=0;
    assign tensor_activation=0; assign tensor_weight=0; assign tensor_mask=0;
    assign tensor_tag=0; assign tensor_rsp_ready=0;
  end endgenerate
endmodule
