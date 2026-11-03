module anvil_d2_fp8_mla_moe #(
  parameter integer GROUP_SIZE=128
) (
  input wire clk, rst_n, flush,
  input wire cmd_valid,
  output wire cmd_ready,
  input wire cmd_write, cmd_expert, cmd_prefetch,
  input wire [31:0] cmd_epoch, cmd_layer, cmd_row, cmd_base_col,
  input wire [8:0] cmd_count,
  input wire in_valid,
  output wire in_ready,
  input wire signed [31:0] in_q16,
  output wire out_valid,
  input wire out_ready,
  output wire signed [31:0] out_q16,
  output wire [31:0] out_fp32,
  output wire [15:0] out_bf16,
  output wire [6:0] out_index,
  output wire out_last,
  output wire done, error, fault, idle,
  output wire c_req_valid,
  input wire c_req_ready,
  output wire c_req_write,
  output wire [3:0] c_req_kind,
  output wire [31:0] c_req_layer,
  output wire [2:0] c_req_proj,
  output wire [31:0] c_req_row, c_req_col, c_req_wdata,
  input wire c_rsp_valid,
  output wire c_rsp_ready,
  input wire [31:0] c_rsp_rdata,
  input wire c_rsp_error
);
  localparam IDLE=0, READ_SCALE=1, SCALE_RESPONSE=2, READ_PAYLOAD=3;
  localparam PAYLOAD_RESPONSE=4, DECODE_READ=5, DECODE_ISSUE=6, DECODE_WAIT=7;
  localparam CONVERT=8, CONVERT_WAIT=9, STORE=10, OUT_READ=11, OUT_PUBLISH=12;
  localparam QUANTIZE=13, QUANTIZE_CAPTURE=14, QUANTIZE_PACK=15, QUANTIZE_DRAIN=16;
  localparam WRITE_READ=17, WRITE_PAYLOAD=18, WRITE_RESPONSE=19;
  localparam WRITE_SCALE=20, WRITE_SCALE_RESPONSE=21, COMPLETE=22, FAULTED=23;
  reg [4:0] state;
  reg armed, failed, expert, prefetch, epoch_valid;
  reg [31:0] current_epoch, layer, row, base_col, scale_bits;
  reg [7:0] count;
  reg [6:0] element_index, fill_index;
  reg [5:0] word_index, final_word;
  reg [31:0] pack_accumulator, decoded_fp32;
  reg [15:0] decoded_bf16;
  reg signed [31:0] decoded_q16;
  reg [1:0] resident_valid;
  reg [31:0] resident_epoch [0:1], resident_layer [0:1];
  reg [31:0] resident_row [0:1], resident_base_col [0:1];
  reg [7:0] resident_count [0:1];
  (* ramstyle="M20K", nomem2reg *) reg [31:0] payload [0:31];
  (* ramstyle="M20K", nomem2reg *) reg [79:0] numerical [0:255];
  reg [31:0] payload_q;
  reg [79:0] numerical_q;
  wire enabled=rst_n && armed && !flush;
  wire accepted=cmd_valid && cmd_ready;
  wire source_transfer=in_valid && in_ready;
  wire output_transfer=out_valid && out_ready;
  wire memory_transfer=c_req_valid && c_req_ready;
  wire memory_response=c_rsp_valid && c_rsp_ready;
  wire child_flush=flush || failed;
  wire read_hit=resident_valid[cmd_expert] &&
    resident_epoch[cmd_expert]==cmd_epoch &&
    resident_layer[cmd_expert]==cmd_layer && resident_row[cmd_expert]==cmd_row &&
    resident_base_col[cmd_expert]==cmd_base_col &&
    {1'b0,resident_count[cmd_expert]}==cmd_count;
  wire command_invalid=GROUP_SIZE!=128 || cmd_count==0 || cmd_count>128 ||
    cmd_base_col[6:0]!=0 || (cmd_write && (cmd_expert || cmd_prefetch));
  wire [8:0] last_component=cmd_count-9'd1;
  wire [7:0] numerical_address={expert,element_index};
  wire quant_ready, quant_input_ready, quant_valid, quant_last, quant_done, quant_error;
  wire [7:0] quant_fp8;
  wire [6:0] quant_index;
  wire [31:0] quant_scale;
  wire quant_output_ready=enabled && state==QUANTIZE_PACK;
  wire quant_transfer=quant_valid && quant_output_ready;
  wire packed_word_complete=quant_index[1:0]==2'd3 || quant_last;
  wire [31:0] packed_word=pack_accumulator |
    ({24'd0,quant_fp8} << {quant_index[1:0],3'b000});
  wire dequant_ready, dequant_valid, dequant_error;
  wire [31:0] dequant_fp32;
  wire [15:0] dequant_bf16;
  wire [7:0] selected_byte=payload_q >> {element_index[1:0],3'b000};
  wire convert_ready, convert_valid, convert_error;
  wire signed [31:0] converted_q16;
  wire numerical_fault=(state==DECODE_WAIT && dequant_valid && dequant_error) ||
    (state==CONVERT_WAIT && convert_valid && convert_error) ||
    (state==QUANTIZE_DRAIN && quant_done && quant_error);
  integer n;

  generate if (GROUP_SIZE!=128) begin: invalid_parameters
    initial $fatal(1,"ANVIL_D2 PARAMETER ERROR: FP8 service GROUP_SIZE must be 128");
  end endgenerate

  assign cmd_ready=enabled && state==IDLE;
  assign in_ready=enabled && state==QUANTIZE_CAPTURE && quant_input_ready;
  assign out_valid=enabled && state==OUT_PUBLISH;
  assign out_q16=out_valid ? numerical_q[31:0] : 32'sd0;
  assign out_bf16=out_valid ? numerical_q[47:32] : 16'd0;
  assign out_fp32=out_valid ? numerical_q[79:48] : 32'd0;
  assign out_index=out_valid ? element_index : 7'd0;
  assign out_last=out_valid && {1'b0,element_index}==count-1'b1;
  assign done=enabled && state==COMPLETE;
  assign error=done && failed;
  assign fault=enabled && failed;
  assign idle=cmd_ready;
  assign c_req_valid=enabled && !failed && (state==READ_SCALE ||
    state==READ_PAYLOAD || state==WRITE_PAYLOAD || state==WRITE_SCALE);
  assign c_req_write=c_req_valid && (state==WRITE_PAYLOAD || state==WRITE_SCALE);
  assign c_req_kind=!c_req_valid ? 4'd0 :
    state==READ_SCALE || state==WRITE_SCALE ? 4'd14 : 4'd13;
  assign c_req_layer=c_req_valid ? layer : 32'd0;
  assign c_req_proj=!c_req_valid ? 3'd0 : expert ? 3'd5 : 3'd3;
  assign c_req_row=c_req_valid ? row : 32'd0;
  assign c_req_col=!c_req_valid ? 32'd0 :
    state==READ_SCALE || state==WRITE_SCALE ? base_col>>7 :
    (base_col>>2)+{26'd0,word_index};
  assign c_req_wdata=!c_req_write ? 32'd0 :
    state==WRITE_SCALE ? scale_bits : payload_q;
  assign c_rsp_ready=enabled && !failed && (state==SCALE_RESPONSE ||
    state==PAYLOAD_RESPONSE || state==WRITE_RESPONSE || state==WRITE_SCALE_RESPONSE);

  anvil_d2_fp8_group_quantizer #(.GROUP_SIZE(GROUP_SIZE)) cache_quantizer (
    .clk(clk),.rst_n(rst_n),.flush(child_flush),
    .cmd_valid(enabled && state==QUANTIZE),.cmd_ready(quant_ready),
    .cmd_count({1'b0,count}),
    .in_valid(enabled && state==QUANTIZE_CAPTURE && in_valid),
    .in_ready(quant_input_ready),.in_q16(in_q16),
    .out_valid(quant_valid),.out_ready(quant_output_ready),
    .out_fp8(quant_fp8),.out_index(quant_index),.out_last(quant_last),
    .out_scale(quant_scale),.done(quant_done),.error(quant_error)
  );
  anvil_d2_fp8_dequant dequantizer (
    .clk(clk),.rst_n(rst_n),.flush(child_flush),
    .in_valid(enabled && state==DECODE_ISSUE),.in_ready(dequant_ready),
    .in_fp8(selected_byte),.in_scale(scale_bits),
    .out_valid(dequant_valid),.out_ready(enabled && state==DECODE_WAIT),
    .out_fp32(dequant_fp32),.out_bf16(dequant_bf16),.out_error(dequant_error)
  );
  anvil_d2_bf16_to_q16 consumer_boundary (
    .clk(clk),.rst_n(rst_n),.flush(child_flush),
    .in_valid(enabled && state==CONVERT),.in_ready(convert_ready),
    .in_bf16(decoded_bf16),.out_valid(convert_valid),
    .out_ready(enabled && state==CONVERT_WAIT),
    .out_q16(converted_q16),.out_error(convert_error)
  );

  always @(posedge clk) begin
    if (enabled && !failed) begin
      if (state==PAYLOAD_RESPONSE && memory_response && !c_rsp_error)
        payload[word_index[4:0]]<=c_rsp_rdata;
      if (quant_transfer && packed_word_complete)
        payload[quant_index[6:2]]<=packed_word;
      if (state==DECODE_READ) payload_q<=payload[element_index[6:2]];
      if (state==WRITE_READ) payload_q<=payload[word_index[4:0]];
      if (state==STORE)
        numerical[numerical_address]<={decoded_fp32,decoded_bf16,decoded_q16};
      if (state==OUT_READ) numerical_q<=numerical[numerical_address];
    end
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; armed<=0; failed<=0; expert<=0; prefetch<=0; epoch_valid<=0;
      current_epoch<=0; layer<=0; row<=0; base_col<=0; scale_bits<=0;
      count<=0; element_index<=0; fill_index<=0; word_index<=0; final_word<=0;
      pack_accumulator<=0; decoded_fp32<=0; decoded_bf16<=0; decoded_q16<=0;
      resident_valid<=0;
      for (n=0;n<2;n=n+1) begin
        resident_epoch[n]<=0; resident_layer[n]<=0; resident_row[n]<=0;
        resident_base_col[n]<=0; resident_count[n]<=0;
      end
    end else begin
      armed<=1;
      if (flush) begin
        state<=IDLE; failed<=0; resident_valid<=0; epoch_valid<=0;
        element_index<=0; fill_index<=0; word_index<=0; pack_accumulator<=0;
        scale_bits<=0; decoded_fp32<=0; decoded_bf16<=0; decoded_q16<=0;
      end else if (!failed && ((memory_response && c_rsp_error) || numerical_fault)) begin
        state<=COMPLETE; failed<=1; resident_valid<=0;
      end else case (state)
        IDLE: if (accepted) begin
          expert<=cmd_expert; prefetch<=cmd_prefetch;
          layer<=cmd_layer; row<=cmd_row; base_col<=cmd_base_col;
          current_epoch<=cmd_epoch; epoch_valid<=1;
          count<=cmd_count[7:0]; final_word<=last_component[7:2];
          element_index<=0; fill_index<=0; word_index<=0;
          pack_accumulator<=0; failed<=0;
          if (!epoch_valid || current_epoch!=cmd_epoch) resident_valid<=0;
          if (command_invalid) begin
            failed<=1; resident_valid<=0; state<=COMPLETE;
          end else if (cmd_write) begin
            resident_valid[cmd_expert]<=0;
            state<=QUANTIZE;
          end else if (read_hit) begin
            if (cmd_prefetch) state<=COMPLETE;
            else state<=OUT_READ;
          end else begin
            resident_valid[cmd_expert]<=0;
            state<=READ_SCALE;
          end
        end
        READ_SCALE: if (memory_transfer) state<=SCALE_RESPONSE;
        SCALE_RESPONSE: if (memory_response) begin
          scale_bits<=c_rsp_rdata; word_index<=0; state<=READ_PAYLOAD;
        end
        READ_PAYLOAD: if (memory_transfer) state<=PAYLOAD_RESPONSE;
        PAYLOAD_RESPONSE: if (memory_response) begin
          if (word_index==final_word) begin element_index<=0; state<=DECODE_READ; end
          else begin word_index<=word_index+1'b1; state<=READ_PAYLOAD; end
        end
        DECODE_READ: state<=DECODE_ISSUE;
        DECODE_ISSUE: if (dequant_ready) state<=DECODE_WAIT;
        DECODE_WAIT: if (dequant_valid) begin
          decoded_fp32<=dequant_fp32; decoded_bf16<=dequant_bf16; state<=CONVERT;
        end
        CONVERT: if (convert_ready) state<=CONVERT_WAIT;
        CONVERT_WAIT: if (convert_valid) begin decoded_q16<=converted_q16; state<=STORE; end
        STORE: begin
          if ({1'b0,element_index}==count-1'b1) begin
            resident_valid[expert]<=1;
            resident_epoch[expert]<=current_epoch;
            resident_layer[expert]<=layer; resident_row[expert]<=row;
            resident_base_col[expert]<=base_col; resident_count[expert]<=count;
            element_index<=0;
            if (prefetch) state<=COMPLETE;
            else state<=OUT_READ;
          end else begin element_index<=element_index+1'b1; state<=DECODE_READ; end
        end
        OUT_READ: state<=OUT_PUBLISH;
        OUT_PUBLISH: if (output_transfer) begin
          if ({1'b0,element_index}==count-1'b1) state<=COMPLETE;
          else begin element_index<=element_index+1'b1; state<=OUT_READ; end
        end
        QUANTIZE: if (quant_ready) state<=QUANTIZE_CAPTURE;
        QUANTIZE_CAPTURE: if (source_transfer) begin
          if ({1'b0,fill_index}==count-1'b1) state<=QUANTIZE_PACK;
          else fill_index<=fill_index+1'b1;
        end
        QUANTIZE_PACK: if (quant_transfer) begin
          if (packed_word_complete) pack_accumulator<=0;
          else pack_accumulator<=packed_word;
          if (quant_last) begin
            scale_bits<=quant_scale; word_index<=0; state<=QUANTIZE_DRAIN;
          end
        end
        QUANTIZE_DRAIN: if (quant_done) state<=WRITE_READ;
        WRITE_READ: state<=WRITE_PAYLOAD;
        WRITE_PAYLOAD: if (memory_transfer) state<=WRITE_RESPONSE;
        WRITE_RESPONSE: if (memory_response) begin
          if (word_index==final_word) state<=WRITE_SCALE;
          else begin word_index<=word_index+1'b1; state<=WRITE_READ; end
        end
        WRITE_SCALE: if (memory_transfer) state<=WRITE_SCALE_RESPONSE;
        WRITE_SCALE_RESPONSE: if (memory_response) state<=COMPLETE;
        COMPLETE: if (failed) state<=FAULTED; else state<=IDLE;
        FAULTED: state<=FAULTED;
        default: begin failed<=1; resident_valid<=0; state<=COMPLETE; end
      endcase
    end
  end
endmodule
