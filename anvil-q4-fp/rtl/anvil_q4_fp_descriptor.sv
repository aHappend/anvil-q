module anvil_q4_fp_descriptor #(
  parameter integer BANKS=16
) (
  input wire clk, rst_n, cancel, quiescent, cfg_valid, cfg_commit,
  input wire [5:0] cfg_index,
  input wire [31:0] cfg_wdata,
  output wire cfg_ready, cfg_done, cfg_error, cfg_busy,
  output wire [1023:0] active_words
);
  localparam integer LEGAL_BANKS=
    BANKS==1 || BANKS==2 || BANKS==4 || BANKS==8 || BANKS==16;

  function automatic [1023:0] reset_image;
    reg [1023:0] image;
    begin
      image=0;
      image[0*32+:32]=2; image[1*32+:32]=5;
      image[6*32+:32]=BANKS; image[7*32+:32]=28;
      image[8*32+:32]=3584; image[9*32+:32]=18944;
      image[10*32+:32]=28; image[11*32+:32]=4;
      image[12*32+:32]=128; image[13*32+:32]=152064;
      image[14*32+:32]=32768; image[15*32+:32]=1;
      image[16*32+:32]=1; image[17*32+:32]=32'h49742400;
      image[18*32+:32]=32'h358637bd; image[19*32+:32]=32;
      image[20*32+:32]=1024; image[22*32+:32]=7;
      image[23*32+:32]=1;
      reset_image=image;
    end
  endfunction

  function automatic positive_finite(input [31:0] value);
    positive_finite=!value[31] && value[30:23]!=8'hff && value[30:0]!=0;
  endfunction

  function automatic power_of_two(input [31:0] value);
    power_of_two=value!=0 && (value & (value-32'd1))==0;
  endfunction

  generate if (!LEGAL_BANKS) begin : invalid_parameters
    initial $fatal(1,"PARAMETER ERROR: anvil_q4_fp_descriptor BANKS");
    assign cfg_ready=0; assign cfg_done=0; assign cfg_error=0;
    assign cfg_busy=0; assign active_words=0;
  end else begin : legal
    localparam [2:0] IDLE=0, DERIVE=1, REMAINDER_INIT=2,
      REMAINDER_STEP=3, EVALUATE=4, COMMIT_RESPONSE=5, SETTLE=6;
    localparam [1023:0] RESET_IMAGE=reset_image();
    reg [1023:0] shadow, active;
    reg [2:0] state;
    reg write_fault, shadow_valid, commit_valid, scalar_valid;
    reg done_register, error_register;
    reg [31:0] successful_commits;
    reg [63:0] computed_hidden, computed_queries, computed_kv_width, computed_capacity;
    reg [15:0] hidden_numerator, intermediate_numerator;
    reg [8:0] hidden_remainder, intermediate_remainder;
    reg [4:0] remainder_bit;

    wire [31:0] version=shadow[0*32+:32], mode=shadow[1*32+:32];
    wire [31:0] activation_format=shadow[2*32+:32], weight_format=shadow[3*32+:32];
    wire [31:0] quantization=shadow[4*32+:32], cache_encoding=shadow[5*32+:32];
    wire [31:0] banks=shadow[6*32+:32], layers=shadow[7*32+:32];
    wire [31:0] hidden=shadow[8*32+:32], intermediate=shadow[9*32+:32];
    wire [31:0] query_heads=shadow[10*32+:32], kv_heads=shadow[11*32+:32];
    wire [31:0] head_dim=shadow[12*32+:32], vocabulary=shadow[13*32+:32];
    wire [31:0] context_capacity=shadow[14*32+:32], group_size=shadow[15*32+:32];
    wire [31:0] bias_enable=shadow[16*32+:32], theta=shadow[17*32+:32];
    wire [31:0] epsilon=shadow[18*32+:32], page_tokens=shadow[19*32+:32];
    wire [31:0] physical_pages=shadow[20*32+:32], zero_convention=shadow[21*32+:32];
    wire [31:0] ratio=shadow[22*32+:32], cache_block=shadow[24*32+:32];
    wire native_mode=version==2 && mode==5;

    wire dimensions_valid=
      power_of_two(banks) && banks<=BANKS &&
      layers>=1 && layers<=64 && hidden>=2 && hidden<=8192 &&
      intermediate>=1 && intermediate<=32768 &&
      query_heads>=1 && query_heads<=128 && kv_heads>=1 && kv_heads<=128 &&
      head_dim>=2 && head_dim<=256 && !head_dim[0] &&
      vocabulary>=1 && vocabulary<=262144 &&
      context_capacity>=1 && context_capacity<=131072 &&
      positive_finite(theta) && positive_finite(epsilon);
    wire pages_valid=power_of_two(page_tokens) && page_tokens<=32 &&
      physical_pages>=1 && physical_pages<=131072;
    wire native_valid=native_mode && dimensions_valid && pages_valid &&
      activation_format<=1 && weight_format==0 && quantization==0 &&
      cache_encoding<=2 && group_size==1 && bias_enable<=1 &&
      zero_convention==0 && ratio>=1 && ratio<=8 &&
      shadow[23*32+:32]==1 && shadow[24*32+:256]==0;

    wire parent_common_valid=version==1 && mode>=1 && mode<=4 && dimensions_valid &&
      group_size>=1 && group_size<=128 &&
      (ratio==1 || ratio==3 || ratio==6 || ratio==7 || ratio==8) &&
      shadow[25*32+:224]==0;
    wire parent_q4_valid=
      activation_format<=1 && weight_format<=2 && quantization<=1 &&
      !(quantization==1 && weight_format==0) &&
      cache_encoding<=1 && bias_enable<=1 && zero_convention<=1 &&
      cache_block==0 && pages_valid;
    wire parent_block_valid=
      (cache_encoding==0 && cache_block==1) ||
      (mode==2 && cache_encoding==1 && power_of_two(cache_block) &&
        cache_block<=head_dim && (head_dim & (cache_block-32'd1))==0) ||
      (mode==3 && cache_encoding==1 && cache_block==32) ||
      (mode==3 && (cache_encoding==2 || cache_encoding==3) && cache_block==64);
    wire parent_legacy_valid=
      activation_format==1 && weight_format==1 && quantization==0 &&
      bias_enable==1 && zero_convention==1 && banks<=8 &&
      hidden[2:0]==0 && intermediate[2:0]==0 && context_capacity<=32768 &&
      page_tokens==1 && physical_pages==context_capacity &&
      epsilon==32'h358637bd && (mode!=3 || ratio==8) && parent_block_valid;

    wire [8:0] shifted_hidden={hidden_remainder[7:0],hidden_numerator[15]};
    wire [8:0] shifted_intermediate=
      {intermediate_remainder[7:0],intermediate_numerator[15]};
    wire [8:0] divisor={1'b0,group_size[7:0]};
    wire [8:0] next_hidden=shifted_hidden>=divisor ? shifted_hidden-divisor : shifted_hidden;
    wire [8:0] next_intermediate=shifted_intermediate>=divisor ?
      shifted_intermediate-divisor : shifted_intermediate;
    wire [63:0] hidden_product={32'd0,query_heads}*{32'd0,head_dim};
    wire [63:0] query_product={32'd0,kv_heads}*{32'd0,ratio};
    wire [63:0] kv_product={32'd0,kv_heads}*{32'd0,head_dim};
    wire [63:0] capacity_product={32'd0,physical_pages}*{32'd0,page_tokens};

    assign cfg_ready=rst_n && !cancel && quiescent && state==IDLE;
    assign cfg_busy=rst_n && state!=IDLE;
    assign cfg_done=rst_n && done_register;
    assign cfg_error=cfg_done && error_register;
    assign active_words=rst_n ? active : 1024'd0;

    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        shadow<=RESET_IMAGE; active<=RESET_IMAGE; state<=IDLE;
        write_fault<=0; shadow_valid<=1; commit_valid<=0; scalar_valid<=0;
        done_register<=0; error_register<=0; successful_commits<=0;
        computed_hidden<=0; computed_queries<=0; computed_kv_width<=0; computed_capacity<=0;
        hidden_numerator<=0; intermediate_numerator<=0;
        hidden_remainder<=0; intermediate_remainder<=0; remainder_bit<=0;
      end else begin
        done_register<=0; error_register<=0;
        case (state)
          IDLE: if (cfg_valid && cfg_ready) begin
            if (cfg_commit) begin
              commit_valid<=shadow_valid && !write_fault && successful_commits!=32'hffffffff;
              state<=COMMIT_RESPONSE;
            end else if (cfg_index>=32) write_fault<=1;
            else begin shadow[cfg_index*32+:32]<=cfg_wdata; state<=DERIVE; end
          end
          DERIVE: begin
            scalar_valid<=native_valid ||
              (parent_common_valid && (mode==4 ? parent_q4_valid : parent_legacy_valid));
            computed_hidden<=hidden_product; computed_queries<=query_product;
            computed_kv_width<=kv_product; computed_capacity<=capacity_product;
            state<=REMAINDER_INIT;
          end
          REMAINDER_INIT: begin
            hidden_numerator<=hidden[15:0]; intermediate_numerator<=intermediate[15:0];
            hidden_remainder<=0; intermediate_remainder<=0; remainder_bit<=15;
            state<=REMAINDER_STEP;
          end
          REMAINDER_STEP: begin
            hidden_numerator<={hidden_numerator[14:0],1'b0};
            intermediate_numerator<={intermediate_numerator[14:0],1'b0};
            hidden_remainder<=next_hidden; intermediate_remainder<=next_intermediate;
            if (remainder_bit==0) state<=EVALUATE;
            else remainder_bit<=remainder_bit-1'b1;
          end
          EVALUATE: begin
            shadow_valid<=scalar_valid && {32'd0,hidden}==computed_hidden &&
              {32'd0,query_heads}==computed_queries &&
              (native_mode || mode==4 ? computed_capacity>={32'd0,context_capacity} :
                (hidden_remainder==0 && intermediate_remainder==0 &&
                  (mode==3 || computed_kv_width[2:0]==0)));
            state<=IDLE;
          end
          COMMIT_RESPONSE: begin
            if (!cancel) begin
              done_register<=1; error_register<=!commit_valid;
              if (commit_valid) begin
                active<=shadow; successful_commits<=successful_commits+1'b1;
              end else write_fault<=0;
            end
            state<=SETTLE;
          end
          SETTLE: state<=IDLE;
          default: begin shadow_valid<=0; state<=IDLE; end
        endcase
      end
    end
  end endgenerate
endmodule
