module anvil_q3_cache_codec #(
  parameter PROFILE=3, CACHE_MODE=0, INT4_ASYM=0, CACHE_BLOCK=1,
  localparam CAP=CACHE_MODE==0 ? 1 :
    PROFILE==3 ? (CACHE_MODE==2 ? 64 : 32) : (CACHE_BLOCK>0 ? CACHE_BLOCK : 1)
) (
  input wire clk, rst_n, flush, start,
  output wire ready, done, error,
  input wire decode,
  input wire [31:0] count,
  input wire [CAP*32-1:0] values_in, payload_in,
  input wire [31:0] metadata_in,
  output wire [CAP*32-1:0] values_out, payload_out,
  output wire [31:0] metadata_out
);
  localparam BITS=CACHE_MODE==2 ? 4 : CACHE_MODE==1 ? 8 : 32;
  localparam MAX_EXP=CACHE_MODE==2 ? (INT4_ASYM ? 32 : 29) : 25;
  localparam LIMIT=CACHE_MODE==2 ? 7 : 127;
  localparam IDLE=0, SCAN=1, SELECT_EXP=2, ROUND_EXTREMA=3, CHOOSE_ZERO=4;
  localparam ENCODE=5, DECODE=6, CHECK_ZERO=7, COMPLETE=8;
  localparam EXPECT_CAP=CACHE_MODE==0 ? 1 :
    PROFILE==3 ? (CACHE_MODE==2 ? 64 : 32) : CACHE_BLOCK;
  localparam LEGAL=(PROFILE==1 || PROFILE==2 || PROFILE==3) &&
    (CACHE_MODE==0 || CACHE_MODE==1 || (PROFILE==3 && CACHE_MODE==2)) &&
    !(PROFILE==1 && CACHE_MODE!=0) &&
    (INT4_ASYM==0 || INT4_ASYM==1) && CAP>0 && CAP==EXPECT_CAP &&
    (PROFILE==3 || (CACHE_BLOCK>0 && (CACHE_BLOCK&(CACHE_BLOCK-1))==0));
  generate if (!LEGAL) begin: invalid_parameters
    initial $fatal(1,"ANVIL_Q3 PARAMETER ERROR: cache codec geometry");
  end endgenerate

  reg [3:0] state;
  reg failed, decode_op;
  reg [31:0] length, index;
  reg [5:0] exponent;
  reg signed [3:0] zero_code;
  reg [CAP*32-1:0] source_values, source_payload, result_values, result_payload;
  reg [31:0] result_metadata;
  reg [32:0] maximum;
  reg signed [31:0] minimum_value, maximum_value;
  reg signed [33:0] rounded_minimum, rounded_maximum;
  reg signed [33:0] decoded_minimum, decoded_maximum;
  reg any_nonzero;
  wire signed [31:0] sample=source_values[index*32+:32];
  wire [32:0] magnitude=sample[31] ? -{sample[31],sample} : {1'b0,sample};
  wire [63:0] threshold={32'd0,32'(LIMIT)}<<exponent;
  wire signed [33:0] encoded_round=round32(sample,exponent);
  wire signed [33:0] encoded_affine=encoded_round+{{30{zero_code[3]}},zero_code};
  wire [31:0] payload_lane=source_payload[index*BITS+:BITS];
  wire signed [8:0] signed_code=CACHE_MODE==2 ?
    $signed({{5{payload_lane[3]}},payload_lane[3:0]}) :
    $signed({payload_lane[7],payload_lane[7:0]});
  wire signed [33:0] centered_code=
    $signed({{25{signed_code[8]}},signed_code})-
    $signed({{30{zero_code[3]}},zero_code});
  wire signed [65:0] reconstruction=
    $signed({{32{centered_code[33]}},centered_code})<<<exponent;
  wire signed [33:0] range_minimum=decode_op ? decoded_minimum : rounded_minimum;
  wire signed [33:0] range_maximum=decode_op ? decoded_maximum : rounded_maximum;
  wire signed [33:0] lower_candidate=-34'sd8-range_minimum;
  wire signed [33:0] upper_candidate=34'sd7-range_maximum;
  wire signed [33:0] lower=lower_candidate> -34'sd8 ? lower_candidate : -34'sd8;
  wire signed [33:0] upper=upper_candidate<34'sd7 ? upper_candidate : 34'sd7;
  wire signed [33:0] canonical_zero=lower>0 ? lower : upper<0 ? upper : 34'sd0;
  wire invalid_header=CACHE_MODE!=0 &&
    (metadata_in[7:0]>MAX_EXP ||
     (PROFILE==3 ? metadata_in[31:12]!=0 : metadata_in[31:8]!=0) ||
     (!(CACHE_MODE==2 && INT4_ASYM) && metadata_in[11:8]!=0));
  wire invalid_code=(CACHE_MODE==1 && signed_code== -9'sd128) ||
    (CACHE_MODE==2 && !INT4_ASYM && signed_code== -9'sd8);

  function automatic signed [33:0] round32(
    input reg signed [31:0] value,
    input reg [5:0] shift
  );
    reg [32:0] absolute_value;
    reg [33:0] rounded;
    begin
      absolute_value=value[31] ? -{value[31],value} : {1'b0,value};
      rounded={1'b0,absolute_value};
      if (shift!=0) rounded=(rounded+(34'd1<<(shift-1'b1)))>>shift;
      round32=value[31] ? -$signed(rounded) : $signed(rounded);
    end
  endfunction

  function automatic signed [31:0] saturate66(input reg signed [65:0] value);
    begin
      if (value>66'sd2147483647) saturate66=32'sh7fffffff;
      else if (value< -66'sd2147483648) saturate66=32'sh80000000;
      else saturate66=value[31:0];
    end
  endfunction

  assign ready=rst_n && !flush && state==IDLE;
  assign done=rst_n && !flush && state==COMPLETE;
  assign error=done && failed;
  assign values_out=done && !failed ? result_values : {CAP*32{1'b0}};
  assign payload_out=done && !failed ? result_payload : {CAP*32{1'b0}};
  assign metadata_out=done && !failed ? result_metadata : 32'd0;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; failed<=0; decode_op<=0; length<=0; index<=0;
      exponent<=0; zero_code<=0; source_values<=0; source_payload<=0;
      result_values<=0; result_payload<=0; result_metadata<=0;
      maximum<=0; minimum_value<=0; maximum_value<=0;
      rounded_minimum<=0; rounded_maximum<=0;
      decoded_minimum<=0; decoded_maximum<=0; any_nonzero<=0;
    end else if (flush) begin
      state<=IDLE; failed<=0;
    end else case (state)
      IDLE: if (start) begin
        failed<=0; decode_op<=decode; length<=count; index<=0;
        exponent<=0; zero_code<=0; maximum<=0;
        source_values<=values_in; source_payload<=payload_in;
        result_values<=0; result_payload<=0; result_metadata<=0;
        minimum_value<=32'sh7fffffff; maximum_value<=32'sh80000000;
        decoded_minimum<=34'sd2147483647;
        decoded_maximum<= -34'sd2147483648;
        any_nonzero<=0;
        if (count==0 || count>CAP || (decode && invalid_header) ||
            (decode && CACHE_MODE==0 && metadata_in!=0) ||
            (decode && (payload_in>>(CAP*BITS))!=0)) begin
          failed<=1;
          state<=COMPLETE;
        end else if (CACHE_MODE==0) begin
          if (decode) result_values<=payload_in;
          else result_payload<=values_in;
          state<=COMPLETE;
        end else if (decode) begin
          exponent<=metadata_in[5:0];
          zero_code<=metadata_in[11:8];
          result_metadata<=metadata_in;
          state<=DECODE;
        end else state<=SCAN;
      end
      SCAN: begin
        if (magnitude>maximum) maximum<=magnitude;
        if (sample<minimum_value) minimum_value<=sample;
        if (sample>maximum_value) maximum_value<=sample;
        if (index+1==length) begin
          index<=0;
          if (CACHE_MODE==2 && INT4_ASYM) state<=ROUND_EXTREMA;
          else state<=SELECT_EXP;
        end else index<=index+1'b1;
      end
      SELECT_EXP: begin
        if ({31'd0,maximum}<=threshold) begin
          result_metadata<={24'd0,2'd0,exponent};
          state<=ENCODE;
        end else if (exponent==MAX_EXP) begin
          failed<=1;
          state<=COMPLETE;
        end else exponent<=exponent+1'b1;
      end
      ROUND_EXTREMA: begin
        rounded_minimum<=round32(minimum_value,exponent);
        rounded_maximum<=round32(maximum_value,exponent);
        state<=CHOOSE_ZERO;
      end
      CHOOSE_ZERO: begin
        if (lower<=upper) begin
          zero_code<=canonical_zero[3:0];
          result_metadata<={20'd0,canonical_zero[3:0],2'd0,exponent};
          state<=ENCODE;
        end else if (exponent==MAX_EXP) begin
          failed<=1;
          state<=COMPLETE;
        end else begin
          exponent<=exponent+1'b1;
          state<=ROUND_EXTREMA;
        end
      end
      ENCODE: begin
        if (CACHE_MODE==2) begin
          if (encoded_affine>7) result_payload[index*4+:4]<=4'h7;
          else if (encoded_affine<(INT4_ASYM ? -34'sd8 : -34'sd7))
            result_payload[index*4+:4]<=INT4_ASYM ? 4'h8 : 4'h9;
          else result_payload[index*4+:4]<=encoded_affine[3:0];
        end else begin
          if (encoded_round>127) result_payload[index*8+:8]<=8'h7f;
          else if (encoded_round< -127) result_payload[index*8+:8]<=8'h81;
          else result_payload[index*8+:8]<=encoded_round[7:0];
        end
        if (index+1==length) state<=COMPLETE;
        else index<=index+1'b1;
      end
      DECODE: begin
        if (index<length) begin
          if (invalid_code) failed<=1;
          result_values[index*32+:32]<=saturate66(reconstruction);
          if (centered_code<decoded_minimum) decoded_minimum<=centered_code;
          if (centered_code>decoded_maximum) decoded_maximum<=centered_code;
          if (centered_code!=0) any_nonzero<=1;
        end else if (payload_lane!=0) failed<=1;
        if (index==CAP-1) state<=CHECK_ZERO;
        else index<=index+1'b1;
      end
      CHECK_ZERO: begin
        if (!any_nonzero && (exponent!=0 || zero_code!=0)) failed<=1;
        if (CACHE_MODE==2 && INT4_ASYM &&
            (lower>upper || canonical_zero!=$signed({{30{zero_code[3]}},zero_code})))
          failed<=1;
        state<=COMPLETE;
      end
      COMPLETE: state<=IDLE;
      default: begin failed<=1; state<=COMPLETE; end
    endcase
  end
endmodule
