module anvil_q2_fp2_gemv_stream (
  input wire clk, rst_n, flush,
  input wire cmd_valid,
  output wire cmd_ready,
  input wire [31:0] cmd_layer, cmd_inputs, cmd_outputs,
  input wire [2:0] cmd_projection,
  input wire cmd_embedding, cmd_mx,
  output wire busy,
  output wire row_valid,
  input wire row_ready,
  output wire [31:0] row_data, row_index,
  output wire row_last, row_error,
  output wire event_weight_underflow, event_tensor_bubble,
  output wire act_read_valid,
  output wire [31:0] act_read_column,
  input wire act_data_valid,
  input wire [2047:0] act_data,
  output wire req_valid,
  input wire req_ready,
  output wire [3:0] req_kind,
  output wire [31:0] req_layer, req_row, req_col, req_tag,
  output wire [2:0] req_proj,
  output wire [1:0] req_format,
  input wire rsp_valid,
  output wire rsp_ready,
  input wire [511:0] rsp_data,
  input wire [31:0] rsp_tag,
  input wire rsp_error,
  output wire tensor_flush,
  output wire w_valid,
  input wire w_ready,
  output wire [511:0] w_data,
  output wire [15:0] w_scale,
  output wire w_format, w_first, w_last, w_error,
  output wire [31:0] w_tag,
  output wire in_valid,
  input wire in_ready,
  output wire [2047:0] in_a,
  output wire [127:0] in_mask,
  output wire in_first, in_last,
  output wire [31:0] in_tag,
  input wire out_valid,
  output wire out_ready,
  input wire [31:0] out_data, out_tag,
  input wire out_first, out_last, out_error
);
  localparam LOAD_SCALE=0, WAIT_SCALE=1, LOAD_PAYLOAD=2, LOAD_DONE=3;
  reg active, embedding, mx;
  reg [31:0] layer, inputs, outputs;
  reg [2:0] projection;
  reg [1:0] load_state;
  reg [31:0] load_row, load_column, load_tag, scale_base;
  reg [2:0] request_beat, response_beat;
  reg [511:0] scales;
  reg scale_bad;
  reg [31:0] activation_row, activation_column, activation_tag;
  reg activation_pending, activation_valid, activation_done;
  reg [2047:0] activation_tile;
  reg [31:0] published_tiles, consumed_tiles;
  reg [31:0] result_row, result_column, result_tag, accumulator;
  reg sum_pending, sum_last, sum_bad, accumulator_bad;
  reg result_valid, result_bad;
  reg [31:0] result_data;
  wire accepted_command=cmd_valid && cmd_ready;
  wire live=rst_n && !flush;
  assign cmd_ready=live && !active;
  assign busy=rst_n && active;
  assign tensor_flush=flush || accepted_command;
  wire [31:0] payload_column=load_column+
    (mx ? ({29'd0,request_beat} << 6) : ({29'd0,request_beat} << 5));
  wire [31:0] remaining=inputs-load_column;
  wire [2:0] real_beats=mx ?
    ((remaining>=128) ? 3'd2 : ((remaining>64) ? 3'd2 : 3'd1)) :
    ((remaining>=128) ? 3'd4 : ((remaining>96) ? 3'd4 :
     ((remaining>64) ? 3'd3 : ((remaining>32) ? 3'd2 : 3'd1))));
  wire [2:0] total_beats=mx ? 3'd2 : 3'd4;
  wire scale_request=load_state==LOAD_SCALE;
  assign req_valid=live && active && (scale_request ||
    (load_state==LOAD_PAYLOAD && request_beat<real_beats));
  assign req_kind=embedding ? 4'd0 : (scale_request ? 4'd3 : 4'd1);
  assign req_layer=embedding ? 32'd0 : layer;
  assign req_proj=embedding ? 3'd0 : projection;
  assign req_row=load_row;
  assign req_col=scale_request ? scale_base : payload_column;
  assign req_format=scale_request ? 2'd3 : (mx ? 2'd2 : 2'd1);
  assign req_tag={load_tag[28:0],(scale_request ? 3'd4 : request_beat)};
  wire real_response=response_beat<real_beats;
  assign w_valid=live && active && load_state==LOAD_PAYLOAD &&
    (real_response ? rsp_valid : 1'b1);
  assign rsp_ready=live && active && ((load_state==WAIT_SCALE) ||
    (load_state==LOAD_PAYLOAD && real_response && w_ready));
  wire [31:0] response_column=load_column+
    (mx ? ({29'd0,response_beat} << 6) : ({29'd0,response_beat} << 5));
  genvar element;
  generate for (element=0;element<64;element=element+1) begin: payload_mask
    assign w_data[8*element+:8]=(real_response &&
      (mx ? (response_column+element<inputs) :
       (response_column+(element >> 1)<inputs))) ? rsp_data[8*element+:8] : 8'd0;
  end endgenerate
  wire [5:0] scale_offset=load_column[10:5];
  wire [6:0] scale_byte={1'b0,scale_offset}+({4'd0,response_beat} << 1);
  assign w_scale[7:0]=(mx && response_column<inputs) ?
    scales[8*scale_byte+:8] : 8'd127;
  assign w_scale[15:8]=(mx && response_column+32<inputs) ?
    scales[8*scale_byte+8+:8] : 8'd127;
  assign w_format=mx;
  assign w_first=load_column==0;
  assign w_last=load_column+128>=inputs;
  assign w_tag=load_tag;
  assign w_error=scale_bad || (real_response &&
    (rsp_error || rsp_tag!={load_tag[28:0],response_beat}));
  assign act_read_valid=live && active && !activation_done &&
    !activation_pending && !activation_valid;
  assign act_read_column=activation_column;
  assign in_valid=live && active && activation_valid;
  assign in_a=activation_tile;
  generate for (element=0;element<128;element=element+1) begin: activation_mask
    assign in_mask[element]=activation_column+element<inputs;
  end endgenerate
  assign in_first=activation_column==0;
  assign in_last=activation_column+128>=inputs;
  assign in_tag=activation_tag;
  wire tensor_accept=in_valid && in_ready;
  assign event_weight_underflow=live && active && activation_valid &&
    published_tiles==consumed_tiles;
  assign event_tensor_bubble=live && active && !activation_done && !tensor_accept;
  assign out_ready=live && active && !sum_pending && !result_valid;
  wire result_accept=out_valid && out_ready;
  wire metadata_bad=out_tag!=result_tag || out_first!=(result_column==0) ||
    out_last!=(result_column+128>=inputs);
  wire sum_valid, sum_error;
  wire [31:0] sum_data;
  anvil_q2_fp2_add4 row_accumulation(
    .clk(clk),.rst_n(rst_n),.flush(tensor_flush),.enable(1'b1),
    .in_valid(result_accept && result_column!=0),
    .in_error(out_error || metadata_bad || accumulator_bad),
    .in_a(accumulator),.in_b(out_data),
    .out_valid(sum_valid),.out_data(sum_data),.out_error(sum_error));
  assign row_valid=live && active && result_valid;
  assign row_data=result_data;
  assign row_index=result_row;
  assign row_last=result_row+1>=outputs;
  assign row_error=row_valid && result_bad;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      active<=0; embedding<=0; mx<=0; layer<=0; inputs<=0; outputs<=0;
      projection<=0; load_state<=LOAD_DONE; load_row<=0; load_column<=0;
      load_tag<=0; scale_base<=0; request_beat<=0; response_beat<=0;
      scales<=0; scale_bad<=0; activation_row<=0; activation_column<=0;
      activation_tag<=0; activation_pending<=0; activation_valid<=0;
      activation_done<=0; activation_tile<=0; published_tiles<=0; consumed_tiles<=0;
      result_row<=0; result_column<=0; result_tag<=0; accumulator<=0;
      sum_pending<=0; sum_last<=0; sum_bad<=0; accumulator_bad<=0;
      result_valid<=0; result_bad<=0; result_data<=0;
    end else if (flush) begin
      active<=0; activation_pending<=0; activation_valid<=0;
      result_valid<=0; sum_pending<=0; load_state<=LOAD_DONE;
    end else if (accepted_command) begin
      active<=1; embedding<=cmd_embedding; mx<=cmd_mx;
      layer<=cmd_layer; inputs<=cmd_inputs; outputs<=cmd_outputs;
      projection<=cmd_projection; load_state<=cmd_mx ? LOAD_SCALE : LOAD_PAYLOAD;
      load_row<=0; load_column<=0; load_tag<=0; scale_base<=0;
      request_beat<=0; response_beat<=0; scale_bad<=0;
      activation_row<=0; activation_column<=0; activation_tag<=0;
      activation_pending<=0; activation_valid<=0; activation_done<=0;
      published_tiles<=0; consumed_tiles<=0;
      result_row<=0; result_column<=0; result_tag<=0; accumulator<=0;
      sum_pending<=0; accumulator_bad<=0; result_valid<=0; result_bad<=0;
    end else if (active) begin
      if (req_valid && req_ready) begin
        if (scale_request) load_state<=WAIT_SCALE;
        else request_beat<=request_beat+1'b1;
      end
      if (load_state==WAIT_SCALE && rsp_valid && rsp_ready) begin
        scales<=rsp_data;
        scale_bad<=rsp_error || rsp_tag!={load_tag[28:0],3'd4};
        load_state<=LOAD_PAYLOAD;
      end
      if (w_valid && w_ready) begin
        if (response_beat+1==total_beats) begin
          published_tiles<=published_tiles+1;
          request_beat<=0; response_beat<=0; load_tag<=load_tag+1;
          if (load_column+128<inputs) begin
            load_column<=load_column+128;
            if (mx && load_column[10:0]==11'd1920) begin
              scale_base<=scale_base+64; load_state<=LOAD_SCALE;
            end
          end else if (load_row+1<outputs) begin
            load_row<=load_row+1; load_column<=0; scale_base<=0;
            if (mx) load_state<=LOAD_SCALE;
          end else load_state<=LOAD_DONE;
        end else response_beat<=response_beat+1'b1;
      end
      if (act_read_valid) activation_pending<=1;
      if (act_data_valid && activation_pending) begin
        activation_tile<=act_data;
        activation_pending<=0; activation_valid<=1;
      end
      if (tensor_accept) begin
        activation_valid<=0; consumed_tiles<=consumed_tiles+1;
        activation_tag<=activation_tag+1;
        if (activation_column+128<inputs) activation_column<=activation_column+128;
        else if (activation_row+1<outputs) begin
          activation_column<=0; activation_row<=activation_row+1;
        end else activation_done<=1;
      end
      if (result_accept) begin
        result_tag<=result_tag+1;
        if (result_column==0) begin
          if (result_column+128>=inputs) begin
            result_data<=out_data; result_bad<=out_error || metadata_bad;
            result_valid<=1;
          end else begin
            accumulator<=out_data; accumulator_bad<=out_error || metadata_bad;
            result_column<=128;
          end
        end else begin
          sum_pending<=1; sum_last<=result_column+128>=inputs;
          sum_bad<=out_error || metadata_bad || accumulator_bad;
        end
      end
      if (sum_valid && sum_pending) begin
        sum_pending<=0;
        if (sum_last) begin
          result_data<=sum_data; result_bad<=sum_error || sum_bad;
          result_valid<=1;
        end else begin
          accumulator<=sum_data; accumulator_bad<=sum_error || sum_bad;
          result_column<=result_column+128;
        end
      end
      if (row_valid && row_ready) begin
        result_valid<=0; result_column<=0; accumulator_bad<=0;
        if (row_last) active<=0;
        else result_row<=result_row+1;
      end
    end
  end
endmodule
