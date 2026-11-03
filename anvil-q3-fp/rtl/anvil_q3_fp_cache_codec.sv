module anvil_q3_fp_cache_codec #(
  parameter CACHE_MODE=0, MODE1_FP8=0, INT4_ASYM=0
) (
  input wire clk, rst_n, flush, cmd_valid, cmd_decode, cmd_fp16,
  input wire [6:0] cmd_count,
  output wire cmd_ready, done, error,
  input wire in_valid, in_last,
  input wire [31:0] in_data,
  output wire in_ready,
  output wire out_valid, out_last,
  output wire [31:0] out_data,
  input wire out_ready
);
  import anvil_q3_fp_pkg::*;
  localparam GROUP=CACHE_MODE==1 ? 32 : 64;
  localparam IDLE=0, INPUTS=1, FIND_EXP=2, ENCODE_READ=3, ENCODE_PACK=4;
  localparam VALIDATE=5, OUTPUTS=6, COMPLETE=7;
  generate if (CACHE_MODE<0 || CACHE_MODE>2 ||
    (MODE1_FP8!=0 && MODE1_FP8!=1) || (INT4_ASYM!=0 && INT4_ASYM!=1))
    begin: invalid_parameters
      initial $fatal(1,"ANVIL_Q3_FP PARAMETER ERROR: cache codec format");
    end
  endgenerate
  reg [2:0] state;
  reg failed, decoding, fp16;
  reg [6:0] count, input_index, input_length, work_index, output_index, output_length;
  (* nomem2reg *) reg [15:0] values [0:63];
  (* nomem2reg *) reg [15:0] decoded [0:63];
  reg [31:0] payload [0:31];
  reg [31:0] metadata, maximum_abs, minimum_value, maximum_value;
  reg signed [15:0] shared_exp;
  reg signed [4:0] zero_point;
  reg [15:0] encode_value;
  wire input_transfer=in_valid && in_ready;
  wire [31:0] input_float=widen16(in_data[15:0],fp16);
  wire source_nonfinite=is_nan32(input_float) || is_inf32(input_float);
  wire last_input=input_index+1==input_length;
  wire input_fault=in_last!=last_input ||
    (!decoding && in_data[31:16]!=0) ||
    (!decoding && CACHE_MODE!=0 && source_nonfinite) ||
    (decoding && CACHE_MODE==0 && last_input && count[0] && in_data[31:16]!=0) ||
    (decoding && CACHE_MODE!=0 && input_index==0 && bad_metadata(in_data,fp16));
  wire [31:0] encode_float=widen16(encode_value,fp16);
  wire signed [31:0] rounded_code=round_integer(encode_float,shared_exp);
  wire signed [31:0] shifted_code=rounded_code+{{27{zero_point[4]}},zero_point};
  wire [7:0] fp8_code=encode_fp8(encode_float,shared_exp);
  wire [7:0] integer8=rounded_code < -127 ? 8'h81 :
    rounded_code>127 ? 8'h7f : rounded_code[7:0];
  wire [3:0] integer4=shifted_code < (INT4_ASYM ? -8 : -7) ?
    (INT4_ASYM ? 4'h8 : 4'h9) : shifted_code>7 ? 4'h7 : shifted_code[3:0];
  wire signed [31:0] rounded_min=round_integer(minimum_value,shared_exp);
  wire signed [31:0] rounded_max=round_integer(maximum_value,shared_exp);
  wire signed [31:0] affine_low=(-32'sd8-rounded_min)>-32'sd8 ?
    -32'sd8-rounded_min : -32'sd8;
  wire signed [31:0] affine_high=(32'sd7-rounded_max)<32'sd7 ?
    32'sd7-rounded_max : 32'sd7;
  wire exponent_fits=CACHE_MODE==2 && INT4_ASYM!=0 ?
    affine_low<=affine_high : covers_limit(maximum_abs,shared_exp);
  wire [7:0] validate_byte=8'(payload[work_index>>2]>>({work_index[1:0],3'b0}));
  wire [3:0] validate_nibble=4'(payload[work_index>>3]>>({work_index[2:0],2'b0}));
  wire [7:0] current_code=CACHE_MODE==1 ? validate_byte : {4'd0,validate_nibble};
  wire invalid_code=work_index>=count ? current_code!=0 :
    CACHE_MODE==1 ? (MODE1_FP8!=0 ? validate_byte[6:0]==7'h7f : validate_byte==8'h80) :
    (INT4_ASYM==0 && validate_nibble==4'h8);
  wire signed [31:0] integer_code=CACHE_MODE==1 ?
    {{24{validate_byte[7]}},validate_byte} :
    $signed({{28{validate_nibble[3]}},validate_nibble})-
      $signed({{27{zero_point[4]}},zero_point});
  wire [31:0] code_float=CACHE_MODE==1 && MODE1_FP8!=0 ?
    widen_fp8(validate_byte) : integer_float(integer_code);
  wire [36:0] scaled_code=scale32(code_float,$signed(shared_exp[12:0]));
  wire [20:0] narrowed_code=narrow16(scaled_code[31:0],fp16);
  integer i;

  function automatic less_float(input reg [31:0] a, b);
    if (a[30:0]==0 && b[30:0]==0) less_float=0;
    else if (a[31]!=b[31]) less_float=a[31];
    else less_float=a[31] ? a[30:0]>b[30:0] : a[30:0]<b[30:0];
  endfunction

  function automatic bad_metadata(input reg [31:0] word_value, input reg dtype);
    reg signed [15:0] e;
    begin
      e=$signed(word_value[15:0]);
      bad_metadata=word_value[31:24]!=0 || word_value[23:22]!=2'(CACHE_MODE) ||
        word_value[21]!=(CACHE_MODE==1 && MODE1_FP8!=0) ||
        word_value[20]!=dtype || e < -256 || e>256 ||
        (!(CACHE_MODE==2 && INT4_ASYM!=0) && word_value[19:16]!=0);
    end
  endfunction

  function automatic covers_limit(input reg [31:0] magnitude, input reg signed [15:0] e);
    reg [23:0] sig, limit_sig;
    reg [4:0] leading;
    reg signed [16:0] exponent, limit_exponent;
    begin
      sig={magnitude[30:23]!=0,magnitude[22:0]};
      leading=clz24(sig);
      sig=sig<<leading;
      exponent=$signed({9'd0,(magnitude[30:23]==0 ? 8'd1 : magnitude[30:23])})-
        17'sd127-$signed({12'd0,leading});
      if (CACHE_MODE==1 && MODE1_FP8!=0) begin
        limit_sig=24' (448<<15); limit_exponent=$signed(e)+17'sd8;
      end else if (CACHE_MODE==1) begin
        limit_sig=24' (127<<17); limit_exponent=$signed(e)+17'sd6;
      end else begin
        limit_sig=24' (7<<21); limit_exponent=$signed(e)+17'sd2;
      end
      covers_limit=magnitude[30:0]==0 || exponent<limit_exponent ||
        (exponent==limit_exponent && sig<=limit_sig);
    end
  endfunction

  // Exact dyadic rounding, with a sentinel outside any feasible code interval.
  function automatic signed [31:0] round_integer(
    input reg [31:0] value, input reg signed [15:0] e
  );
    reg [23:0] sig, fraction;
    reg [4:0] leading;
    reg signed [16:0] exponent, shift;
    reg [30:0] magnitude;
    reg [23:0] halfway;
    begin
      sig={value[30:23]!=0,value[22:0]};
      leading=clz24(sig);
      sig=sig<<leading;
      exponent=$signed({9'd0,(value[30:23]==0 ? 8'd1 : value[30:23])})-
        17'sd127-$signed({12'd0,leading});
      shift=17'sd23+$signed(e)-exponent;
      magnitude=0; fraction=0; halfway=0;
      if (value[30:0]!=0) begin
        if (shift < -6) magnitude=31'h40000000;
        else if (shift<=0) magnitude={7'd0,sig}<<(-shift);
        else if (shift<=24) begin
          magnitude={7'd0,sig}>>shift;
          fraction=sig & ((24'd1<<shift)-1'b1);
          halfway=24'd1<<(shift-1'b1);
          if (fraction>halfway || (fraction==halfway && magnitude[0]))
            magnitude=magnitude+1'b1;
        end
      end
      round_integer=value[31] ? -$signed({1'b0,magnitude}) : $signed({1'b0,magnitude});
    end
  endfunction

  function automatic [31:0] integer_float(input reg signed [31:0] value);
    reg [31:0] magnitude, normalized;
    reg [5:0] leading;
    reg [7:0] exponent;
    begin
      magnitude=value[31] ? -value : value;
      leading=clz32(magnitude);
      normalized=magnitude<<leading;
      exponent=8'd158-{2'd0,leading};
      integer_float=magnitude==0 ? 32'd0 : {value[31],exponent,normalized[30:8]};
    end
  endfunction

  function automatic [7:0] encode_fp8(
    input reg [31:0] value, input reg signed [15:0] e
  );
    reg [23:0] sig;
    reg [4:0] leading;
    reg signed [16:0] exponent, shift;
    reg [26:0] work;
    reg [4:0] rounded;
    reg [3:0] encoded_exponent;
    begin
      sig={value[30:23]!=0,value[22:0]};
      leading=clz24(sig); sig=sig<<leading;
      exponent=$signed({9'd0,(value[30:23]==0 ? 8'd1 : value[30:23])})-
        17'sd127-$signed({12'd0,leading})-$signed(e);
      shift=20;
      if (exponent < -6) begin shift=shift-17'sd6-exponent; exponent=-6; end
      work=shift_jam27({sig,3'd0},shift>1023 ? 10'd1023 : 10'(shift));
      rounded={1'b0,work[6:3]}+{4'd0,(work[2] && (work[1] || work[0] || work[3]))};
      if (rounded[4]) begin rounded=rounded>>1; exponent=exponent+1'b1; end
      encoded_exponent=rounded[3] ? 4'(exponent+17'sd7) : 4'd0;
      if (value[30:0]==0) encode_fp8={value[31],7'd0};
      else if (exponent>8 || (exponent==8 && rounded>=15))
        encode_fp8={value[31],7'h7e};
      else encode_fp8={value[31],encoded_exponent,rounded[2:0]};
    end
  endfunction

  function automatic [31:0] widen_fp8(input reg [7:0] value);
    reg [23:0] sig;
    reg [4:0] leading;
    reg [7:0] exponent;
    begin
      sig={1'b0,value[2:0],20'd0};
      leading=clz24(sig); sig=sig<<leading;
      exponent=8'd121-{3'd0,leading};
      if (value[6:0]==0) widen_fp8={value[7],31'd0};
      else if (value[6:3]==0) widen_fp8={value[7],exponent,sig[22:0]};
      else begin
        exponent={4'd0,value[6:3]}+8'd120;
        widen_fp8={value[7],exponent,value[2:0],20'd0};
      end
    end
  endfunction

  assign cmd_ready=rst_n && !flush && state==IDLE;
  assign done=rst_n && !flush && state==COMPLETE;
  assign error=done && failed;
  assign in_ready=rst_n && !flush && state==INPUTS;
  assign out_valid=rst_n && !flush && state==OUTPUTS && !failed;
  assign out_last=out_valid && output_index+1==output_length;
  assign out_data=!out_valid ? 32'd0 :
    decoding ? (CACHE_MODE==0 ?
      (output_index[0] ? {16'd0,payload[output_index>>1][31:16]} :
                        {16'd0,payload[output_index>>1][15:0]}) :
      {16'd0,decoded[output_index]}) :
    CACHE_MODE==0 ? payload[output_index] :
    output_index==0 ? metadata : payload[output_index-1'b1];

  always @(posedge clk) begin
    if (rst_n && !flush && state==INPUTS && input_transfer && !input_fault &&
        !decoding && CACHE_MODE!=0)
      values[input_index]<=in_data[15:0];
    if (rst_n && !flush && state==ENCODE_READ) encode_value<=values[work_index];
    if (rst_n && !flush && state==VALIDATE && !invalid_code && work_index<count)
      decoded[work_index]<=narrowed_code[15:0];
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; failed<=0; decoding<=0; fp16<=0; count<=0;
      input_index<=0; input_length<=0; work_index<=0; output_index<=0; output_length<=0;
      metadata<=0; maximum_abs<=0; minimum_value<=0; maximum_value<=0;
      shared_exp<=0; zero_point<=0;
    end else if (flush) begin state<=IDLE; failed<=0; end
    else case (state)
      IDLE: if (cmd_valid) begin
        failed<=0; decoding<=cmd_decode; fp16<=cmd_fp16; count<=cmd_count;
        input_index<=0; work_index<=0; output_index<=0;
        metadata<=0; maximum_abs<=0; minimum_value<=0; maximum_value<=0;
        shared_exp<=0; zero_point<=0;
        input_length<=cmd_decode ? (CACHE_MODE==0 ? ((cmd_count+7'd1)>>1) : 7'd9) : cmd_count;
        output_length<=cmd_decode ? cmd_count : CACHE_MODE==0 ? ((cmd_count+7'd1)>>1) : 7'd9;
        for (i=0;i<32;i=i+1) payload[i]<=0;
        if (cmd_count==0 || cmd_count>GROUP) begin failed<=1; state<=COMPLETE; end
        else state<=INPUTS;
      end
      INPUTS: if (input_transfer) begin
        if (input_fault) begin failed<=1; state<=COMPLETE; end
        else begin
          if (decoding) begin
            if (CACHE_MODE==0) payload[input_index]<=in_data;
            else if (input_index==0) begin
              metadata<=in_data; shared_exp<=$signed(in_data[15:0]);
              zero_point<={in_data[19],in_data[19:16]};
            end else payload[input_index-1'b1]<=in_data;
          end else if (CACHE_MODE==0)
            payload[input_index>>1][input_index[0]*16+:16]<=in_data[15:0];
          else begin
            if (input_float[30:0]>maximum_abs[30:0]) maximum_abs<={1'b0,input_float[30:0]};
            if (input_index==0 || less_float(input_float,minimum_value)) minimum_value<=input_float;
            if (input_index==0 || less_float(maximum_value,input_float)) maximum_value<=input_float;
          end
          if (last_input) begin
            if (CACHE_MODE==0) state<=OUTPUTS;
            else if (decoding) begin work_index<=0; state<=VALIDATE; end
            else begin shared_exp<=-16'sd256; state<=FIND_EXP; end
          end else input_index<=input_index+1'b1;
        end
      end
      FIND_EXP: begin
        if (maximum_abs[30:0]==0) begin
          shared_exp<=0; zero_point<=0;
          metadata<={8'd0,2'(CACHE_MODE),1'(CACHE_MODE==1 && MODE1_FP8!=0),fp16,4'd0,16'd0};
          work_index<=0; state<=ENCODE_READ;
        end else if (exponent_fits) begin
          if (CACHE_MODE==2 && INT4_ASYM!=0) begin
            if (affine_low>0) begin
              zero_point<=affine_low[4:0];
              metadata<={8'd0,2'(CACHE_MODE),1'b0,fp16,affine_low[3:0],shared_exp};
            end else if (affine_high<0) begin
              zero_point<=affine_high[4:0];
              metadata<={8'd0,2'(CACHE_MODE),1'b0,fp16,affine_high[3:0],shared_exp};
            end else begin
              zero_point<=0;
              metadata<={8'd0,2'(CACHE_MODE),1'b0,fp16,4'd0,shared_exp};
            end
          end else begin
            zero_point<=0;
            metadata<={8'd0,2'(CACHE_MODE),1'(CACHE_MODE==1 && MODE1_FP8!=0),fp16,4'd0,shared_exp};
          end
          work_index<=0; state<=ENCODE_READ;
        end else if (shared_exp==256) begin failed<=1; state<=COMPLETE; end
        else shared_exp<=shared_exp+1'b1;
      end
      ENCODE_READ: state<=ENCODE_PACK;
      ENCODE_PACK: begin
        if (CACHE_MODE==1) payload[work_index>>2][work_index[1:0]*8+:8]<=
          MODE1_FP8!=0 ? fp8_code : integer8;
        else payload[work_index>>3][work_index[2:0]*4+:4]<=integer4;
        if (work_index+1==count) state<=OUTPUTS;
        else begin work_index<=work_index+1'b1; state<=ENCODE_READ; end
      end
      VALIDATE: begin
        if (invalid_code) begin failed<=1; state<=COMPLETE; end
        else if (work_index+1==GROUP) state<=OUTPUTS;
        else work_index<=work_index+1'b1;
      end
      OUTPUTS: if (out_valid && out_ready) begin
        if (out_last) state<=COMPLETE;
        else output_index<=output_index+1'b1;
      end
      COMPLETE: state<=IDLE;
      default: begin failed<=1; state<=COMPLETE; end
    endcase
  end
endmodule
