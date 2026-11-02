module anvil_q3_cache_codec (
  input wire clk, rst_n, flush, start,
  input wire [31:0] PROFILE, CACHE_MODE, CACHE_BLOCK,
  input wire INT4_ASYM,
  output wire ready, done, error,
  input wire decode,
  input wire [31:0] count,
  input wire [8191:0] values_in, payload_in,
  input wire [31:0] metadata_in,
  output wire [8191:0] values_out, payload_out,
  output wire [31:0] metadata_out
);
  localparam CAP=256;
  wire [31:0] BITS=CACHE_MODE==2 ? 32'd4 : CACHE_MODE==1 ? 32'd8 : 32'd32;
  wire [5:0] MAX_EXP=CACHE_MODE==2 ? (INT4_ASYM ? 6'd32 : 6'd29) : 6'd25;
  wire [31:0] LIMIT=CACHE_MODE==2 ? 32'd7 : 32'd127;
  localparam IDLE=0, SCAN=1, SELECT_EXP=2, ROUND_EXTREMA=3, CHOOSE_ZERO=4;
  localparam ENCODE=5, DECODE=6, CHECK_ZERO=7, COMPLETE=8;
  wire [31:0] effective_cap=CACHE_MODE==0 ? 32'd1 : CACHE_BLOCK;

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
  wire [31:0] value_tree [1:511];
  wire [31:0] payload_tree [1:511];
  wire [31:0] payload_word_index=CACHE_MODE==2 ? index>>3 :
    CACHE_MODE==1 ? index>>2 : index;
  wire signed [31:0] sample=index<CAP ? value_tree[1] : 32'bx;
  wire [32:0] magnitude=sample[31] ? -{sample[31],sample} : {1'b0,sample};
  wire [63:0] threshold={32'd0,32'(LIMIT)}<<exponent;
  wire signed [33:0] encoded_round=round32(sample,exponent);
  wire signed [33:0] encoded_affine=encoded_round+{{30{zero_code[3]}},zero_code};
  wire [31:0] payload_word=payload_word_index<CAP ? payload_tree[1] : 32'bx;
  wire [31:0] shifted_word=payload_word >>
    (CACHE_MODE==2 ? {index[2:0],2'b00} :
     CACHE_MODE==1 ? {index[1:0],3'b000} : 5'd0);
  wire [31:0] payload_lane=CACHE_MODE==2 ? {28'd0,shifted_word[3:0]} :
    CACHE_MODE==1 ? {24'd0,shifted_word[7:0]} : shifted_word;
  wire [31:0] payload_bits=effective_cap*BITS;
  wire [CAP-1:0] padding_nonzero;
  wire [3:0] encoded_nibble=encoded_affine>7 ? 4'h7 :
    encoded_affine<(INT4_ASYM ? -34'sd8 : -34'sd7) ?
    (INT4_ASYM ? 4'h8 : 4'h9) : encoded_affine[3:0];
  wire [7:0] encoded_byte=encoded_round>127 ? 8'h7f :
    encoded_round< -127 ? 8'h81 : encoded_round[7:0];
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
  wire reject_start=effective_cap==0 || effective_cap>CAP ||
    count==0 || count>effective_cap || (decode && invalid_header) ||
    (decode && CACHE_MODE==0 && metadata_in!=0) ||
    (decode && (|padding_nonzero));

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
  wire [33:0] next_rounded_minimum=round32(minimum_value,exponent);
  wire [33:0] next_rounded_maximum=round32(maximum_value,exponent);
  wire [31:0] saturated_reconstruction=saturate66(reconstruction);

  // Constant word slices keep selection and write steering local to 32 bits.
  generate
    for (genvar w=0;w<CAP;w=w+1) begin: workspace_word
      assign value_tree[CAP+w]=source_values[w*32+:32];
      assign payload_tree[CAP+w]=source_payload[w*32+:32];
      assign padding_nonzero[w]=payload_bits<=w*32 ?
        |payload_in[w*32+:32] : payload_bits<w*32+32 ?
        |(payload_in[w*32+:32]>>payload_bits[4:0]) : 1'b0;
      wire [31:0] next_payload;
      for (genvar n=0;n<8;n=n+1) begin: nibble
        assign next_payload[n*4+:4]=CACHE_MODE==2 ?
          (index[2:0]==n ? encoded_nibble : result_payload[w*32+n*4+:4]) :
          (index[1:0]==(n>>1) ? encoded_byte[(n&1)*4+:4] :
           result_payload[w*32+n*4+:4]);
      end
      always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
          result_values[w*32+:32]<=0;
          result_payload[w*32+:32]<=0;
        end else if (!flush) begin
          if (state==IDLE && start) begin
            result_values[w*32+:32]<=!reject_start && CACHE_MODE==0 && decode ?
              payload_in[w*32+:32] : 32'd0;
            result_payload[w*32+:32]<=!reject_start && CACHE_MODE==0 && !decode ?
              values_in[w*32+:32] : 32'd0;
          end else begin
            if (state==DECODE && index<length && index==w)
              result_values[w*32+:32]<=saturated_reconstruction;
            if (state==ENCODE &&
                (CACHE_MODE==2 ? index>>3 : index>>2)==w)
              result_payload[w*32+:32]<=next_payload;
          end
        end
      end
    end
    for (genvar level=0;level<8;level=level+1) begin: select_level
      for (genvar node=(1<<level);node<(1<<(level+1));node=node+1) begin: select_node
        assign value_tree[node]=index[7-level] ?
          value_tree[node*2+1] : value_tree[node*2];
        assign payload_tree[node]=payload_word_index[7-level] ?
          payload_tree[node*2+1] : payload_tree[node*2];
      end
    end
  endgenerate

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; failed<=0; decode_op<=0; length<=0; index<=0;
      exponent<=0; zero_code<=0; source_values<=0; source_payload<=0;
      result_metadata<=0;
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
        result_metadata<=0;
        minimum_value<=32'sh7fffffff; maximum_value<=32'sh80000000;
        decoded_minimum<=34'sd2147483647;
        decoded_maximum<= -34'sd2147483648;
        any_nonzero<=0;
        if (reject_start) begin
          failed<=1;
          state<=COMPLETE;
        end else if (CACHE_MODE==0) begin
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
        rounded_minimum<=next_rounded_minimum;
        rounded_maximum<=next_rounded_maximum;
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
        if (index+1==length) state<=COMPLETE;
        else index<=index+1'b1;
      end
      DECODE: begin
        if (index<length) begin
          if (invalid_code) failed<=1;
          if (centered_code<decoded_minimum) decoded_minimum<=centered_code;
          if (centered_code>decoded_maximum) decoded_maximum<=centered_code;
          if (centered_code!=0) any_nonzero<=1;
        end else if (payload_lane!=0) failed<=1;
        if (index+1==effective_cap) state<=CHECK_ZERO;
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
