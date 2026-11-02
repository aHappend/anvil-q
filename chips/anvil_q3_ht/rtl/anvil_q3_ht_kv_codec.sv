module anvil_q3_ht_kv_codec #(
  parameter CACHE_MODE=0,
  localparam CAP=CACHE_MODE==2 ? 64 : CACHE_MODE==1 ? 32 : 16
) (
  input wire clk, rst_n, flush,
  input wire in_valid,
  output wire in_ready,
  input wire decode,
  input wire [6:0] count,
  input wire [CAP*32-1:0] values_in,
  input wire [511:0] record_in,
  output wire out_valid,
  input wire out_ready,
  output wire out_error,
  output wire [CAP*32-1:0] values_out,
  output wire [511:0] record_out
);
  localparam LEGAL=CACHE_MODE==0 || CACHE_MODE==1 || CACHE_MODE==2;
  localparam LIMIT=CACHE_MODE==2 ? 7 : 127;
  localparam MAX_EXP=CACHE_MODE==2 ? 29 : 25;
  localparam BITS=CACHE_MODE==0 ? 32 : CACHE_MODE==1 ? 8 : 4;
  localparam IDLE=3'd0, SCAN=3'd1, SELECT_EXP=3'd2, ENCODE=3'd3;
  localparam DECODE=3'd4, CHECK_ZERO=3'd5, COMPLETE=3'd6;
  reg [2:0] state;
  reg failed, any_nonzero;
  reg [6:0] length, index;
  reg [5:0] exponent;
  reg [32:0] maximum;
  reg [CAP*32-1:0] source_values, result_values;
  reg [511:0] source_record, result_record;
  wire signed [31:0] sample=source_values[index*32+:32];
  wire [32:0] magnitude=sample[31] ? -{sample[31],sample} : {1'b0,sample};
  wire [63:0] threshold=64'(LIMIT)<<exponent;
  wire [33:0] rounded_magnitude=exponent==0 ? {1'b0,magnitude} :
    ({1'b0,magnitude}+(34'd1<<(exponent-1'b1)))>>exponent;
  wire [7:0] clamped_magnitude=rounded_magnitude>LIMIT ?
    8'(LIMIT) : rounded_magnitude[7:0];
  wire signed [8:0] encoded_code=sample[31] ?
    -$signed({1'b0,clamped_magnitude}) : $signed({1'b0,clamped_magnitude});
  wire [31:0] payload_lane=source_record[index*BITS+:BITS];
  wire signed [8:0] code=CACHE_MODE==2 ?
    $signed({{5{payload_lane[3]}},payload_lane[3:0]}) :
    $signed({payload_lane[7],payload_lane[7:0]});
  wire signed [63:0] reconstruction=
    $signed({{55{code[8]}},code})<<<exponent;
  wire signed [31:0] saturated=reconstruction>64'sd2147483647 ?
    32'sh7fffffff : reconstruction< -64'sd2147483648 ?
    32'sh80000000 : reconstruction[31:0];
  wire reserved_code=CACHE_MODE==1 ? code== -9'sd128 : code== -9'sd8;
  wire invalid_header=CACHE_MODE!=0 &&
    (record_in[511:288]!=0 || record_in[287:264]!=0 ||
     record_in[263:256]>MAX_EXP);

  generate if (!LEGAL) begin: invalid_parameters
    initial $fatal(1,"ANVIL_Q3_HT PARAMETER ERROR: KV codec mode");
  end endgenerate
  assign in_ready=rst_n && LEGAL && !flush && state==IDLE;
  assign out_valid=rst_n && !flush && state==COMPLETE;
  assign out_error=out_valid && failed;
  assign values_out=out_valid && !failed ? result_values : {CAP*32{1'b0}};
  assign record_out=out_valid && !failed ? result_record : 512'd0;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; failed<=0; any_nonzero<=0;
      length<=0; index<=0; exponent<=0; maximum<=0;
      source_values<=0; source_record<=0; result_values<=0; result_record<=0;
    end else if (flush) begin
      state<=IDLE; failed<=0; any_nonzero<=0;
    end else case (state)
      IDLE: if (in_valid && in_ready) begin
        failed<=0; any_nonzero<=0; length<=count; index<=0;
        exponent<=0; maximum<=0;
        source_values<=values_in; source_record<=record_in;
        result_values<=0; result_record<=0;
        if (count==0 || count>CAP || (decode && invalid_header)) begin
          failed<=1;
          state<=COMPLETE;
        end else if (decode) begin
          if (CACHE_MODE!=0) exponent<=record_in[261:256];
          result_record<=record_in;
          state<=DECODE;
        end else if (CACHE_MODE==0) state<=ENCODE;
        else state<=SCAN;
      end
      SCAN: begin
        if (magnitude>maximum) maximum<=magnitude;
        if (index+1==length) begin index<=0; state<=SELECT_EXP; end
        else index<=index+1'b1;
      end
      SELECT_EXP: begin
        if ({31'd0,maximum}<=threshold) begin
          result_record[287:256]<={26'd0,exponent};
          state<=ENCODE;
        end else if (exponent==MAX_EXP) begin failed<=1; state<=COMPLETE; end
        else exponent<=exponent+1'b1;
      end
      ENCODE: begin
        if (CACHE_MODE==0) result_record[index*32+:32]<=sample;
        else if (CACHE_MODE==1) result_record[index*8+:8]<=encoded_code[7:0];
        else result_record[index*4+:4]<=encoded_code[3:0];
        if (index+1==length) state<=COMPLETE;
        else index<=index+1'b1;
      end
      DECODE: begin
        if (index<length) begin
          if (CACHE_MODE==0) result_values[index*32+:32]<=payload_lane;
          else begin
            result_values[index*32+:32]<=saturated;
            if (reserved_code) failed<=1;
            if (code!=0) any_nonzero<=1;
          end
        end else if (payload_lane!=0) failed<=1;
        if (index==CAP-1) state<=CHECK_ZERO;
        else index<=index+1'b1;
      end
      CHECK_ZERO: begin
        if (CACHE_MODE!=0 && !any_nonzero && exponent!=0) failed<=1;
        state<=COMPLETE;
      end
      COMPLETE: if (out_ready) state<=IDLE;
      default: begin failed<=1; state<=COMPLETE; end
    endcase
  end
endmodule
