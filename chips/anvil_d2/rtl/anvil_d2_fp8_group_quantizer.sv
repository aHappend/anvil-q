module anvil_d2_fp8_group_quantizer #(
  parameter integer GROUP_SIZE=128
) (
  input wire clk, rst_n, flush,
  input wire cmd_valid,
  output wire cmd_ready,
  input wire [8:0] cmd_count,
  input wire in_valid,
  output wire in_ready,
  input wire signed [31:0] in_q16,
  output wire out_valid,
  input wire out_ready,
  output wire [7:0] out_fp8,
  output wire [6:0] out_index,
  output wire out_last,
  output wire [31:0] out_scale,
  output wire done, error
);
  generate
    if (GROUP_SIZE!=128) begin: invalid_parameters
      initial $fatal(1,"ANVIL_D2 PARAMETER ERROR: GROUP_SIZE must be 128");
      assign cmd_ready=0;
      assign in_ready=0;
      assign out_valid=0;
      assign out_fp8=0;
      assign out_index=0;
      assign out_last=0;
      assign out_scale=0;
      assign done=0;
      assign error=0;
    end else begin: group_datapath
      localparam IDLE=0, FILL=1, SCALE=2, READ=3, ENCODE=4, PUBLISH=5, COMPLETE=6;
      reg [2:0] state;
      reg armed, failed;
      reg [7:0] count;
      reg [6:0] fill_index, replay_index;
      reg [31:0] max_magnitude, scale_bits;
      reg signed [9:0] scale_exponent;
      reg [7:0] encoded;
      (* ramstyle = "M20K", nomem2reg *) reg [31:0] source [0:127];
      reg [31:0] source_q;
      wire [31:0] input_magnitude=in_q16[31] ? (~in_q16)+32'd1 : in_q16;
      wire enabled=rst_n && armed && !flush;
      wire capture=in_valid && in_ready;

      function automatic [4:0] leading_bit32(input [31:0] magnitude);
        reg [31:0] value;
        reg [4:0] index;
        begin
          value=magnitude;
          index=0;
          if (|value[31:16]) begin value=value>>16; index=index+5'd16; end
          if (|value[15:8]) begin value=value>>8; index=index+5'd8; end
          if (|value[7:4]) begin value=value>>4; index=index+5'd4; end
          if (|value[3:2]) begin value=value>>2; index=index+5'd2; end
          if (value[1]) index=index+5'd1;
          leading_bit32=index;
        end
      endfunction

      function automatic signed [9:0] choose_scale(input [31:0] maximum);
        integer leading, exponent;
        reg [39:0] threshold, compare_value;
        begin
          leading={27'd0,leading_bit32(maximum)};
          exponent=0;
          threshold=0;
          compare_value={8'd0,maximum};
          if (maximum!=0) begin
            exponent=leading-24;
            if (leading>=8) threshold=40'd448<<(leading-8);
            else begin
              threshold=40'd448;
              compare_value=compare_value<<(8-leading);
            end
            if (compare_value>threshold) exponent=exponent+1;
          end
          choose_scale=exponent;
        end
      endfunction

      function automatic [31:0] scale_encoding(input signed [9:0] exponent);
        reg [7:0] encoded_exponent;
        begin
          encoded_exponent=$signed(exponent)+127;
          scale_encoding={1'b0,encoded_exponent,23'd0};
        end
      endfunction

      function automatic [32:0] round_shift(
        input [31:0] magnitude,
        input integer shift
      );
        reg [32:0] extended, rounded, remainder, half;
        begin
          extended={1'b0,magnitude};
          rounded=0;
          remainder=0;
          half=0;
          if (shift<=0) rounded=extended<<(-shift);
          else if (shift<=32) begin
            rounded=extended>>shift;
            remainder=extended&((33'd1<<shift)-1'b1);
            half=33'd1<<(shift-1);
            if (remainder>half || (remainder==half && rounded[0]))
              rounded=rounded+1'b1;
          end
          round_shift=rounded;
        end
      endfunction

      function automatic [7:0] quantize(
        input [31:0] q16,
        input signed [9:0] exponent
      );
        reg sign_bit;
        reg [31:0] magnitude;
        reg [32:0] significand;
        reg [3:0] encoded_exponent;
        reg [6:0] payload;
        integer leading, unbiased;
        begin
          sign_bit=q16[31];
          magnitude=sign_bit ? (~q16)+32'd1 : q16;
          leading={27'd0,leading_bit32(magnitude)};
          unbiased=leading-16-$signed(exponent);
          significand=0;
          encoded_exponent=0;
          payload=0;
          if (magnitude!=0) begin
            if (unbiased < -6) begin
              significand=round_shift(magnitude,$signed(exponent)+7);
              payload=significand[6:0];
            end else begin
              significand=round_shift(magnitude,leading-3);
              if (significand[4]) begin
                significand=significand>>1;
                unbiased=unbiased+1;
              end
              if (unbiased>8 || (unbiased==8 && significand>14))
                payload=7'h7e;
              else begin
                encoded_exponent=unbiased+7;
                payload={encoded_exponent,significand[2:0]};
              end
            end
          end
          quantize={sign_bit,payload};
        end
      endfunction

      wire signed [9:0] selected_exponent=choose_scale(max_magnitude);
      wire [31:0] selected_scale=scale_encoding(selected_exponent);
      wire [7:0] quantized=quantize(source_q,scale_exponent);
      assign cmd_ready=enabled && state==IDLE;
      assign in_ready=enabled && state==FILL;
      assign out_valid=enabled && state==PUBLISH;
      assign out_fp8=out_valid ? encoded : 8'd0;
      assign out_index=out_valid ? replay_index : 7'd0;
      assign out_last=out_valid && {1'b0,replay_index}==count-1'b1;
      assign out_scale=out_valid ? scale_bits : 32'd0;
      assign done=enabled && state==COMPLETE;
      assign error=done && failed;

      always @(posedge clk) begin
        if (capture) source[fill_index]<=in_q16;
        if (enabled && state==READ) source_q<=source[replay_index];
      end

      always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
          state<=IDLE; armed<=0; failed<=0; count<=0;
          fill_index<=0; replay_index<=0; max_magnitude<=0;
          scale_bits<=0; scale_exponent<=0; encoded<=0;
        end else begin
          armed<=1;
          if (flush) begin
            state<=IDLE; failed<=0; count<=0;
            fill_index<=0; replay_index<=0; max_magnitude<=0;
            scale_bits<=0; scale_exponent<=0; encoded<=0;
          end else case (state)
            IDLE: if (cmd_valid && cmd_ready) begin
              fill_index<=0; replay_index<=0; max_magnitude<=0; failed<=0;
              if (cmd_count==0 || cmd_count>128) begin
                failed<=1; state<=COMPLETE;
              end else begin count<=cmd_count[7:0]; state<=FILL; end
            end
            FILL: if (capture) begin
              if (input_magnitude>max_magnitude) max_magnitude<=input_magnitude;
              if ({1'b0,fill_index}==count-1'b1) state<=SCALE;
              else fill_index<=fill_index+1'b1;
            end
            SCALE: begin
              scale_exponent<=selected_exponent; scale_bits<=selected_scale; state<=READ;
            end
            READ: state<=ENCODE;
            ENCODE: begin encoded<=quantized; state<=PUBLISH; end
            PUBLISH: if (out_valid && out_ready) begin
              if ({1'b0,replay_index}==count-1'b1) state<=COMPLETE;
              else begin replay_index<=replay_index+1'b1; state<=READ; end
            end
            COMPLETE: state<=IDLE;
            default: begin failed<=1; state<=COMPLETE; end
          endcase
        end
      end
    end
  endgenerate
endmodule
