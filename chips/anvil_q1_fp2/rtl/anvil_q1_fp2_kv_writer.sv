module anvil_q1_fp2_kv_writer #(
  parameter MAX_VECTOR=128
) (
  input wire clk, rst_n, cmd_valid,
  output wire cmd_ready,
  input wire cmd_format_mx,
  input wire [3:0] cmd_kind,
  input wire [31:0] cmd_layer, cmd_row, cmd_len,
  input wire in_valid,
  output wire in_ready,
  input wire [31:0] in_data,
  input wire in_last,
  output wire done, error,
  output wire [4:0] status,
  output wire ulp_valid,
  output wire [31:0] ulp_distance,
  output wire fetch_valid,
  input wire fetch_ready,
  output wire fetch_scale,
  output wire [3:0] fetch_kind,
  output wire [31:0] fetch_layer, fetch_row, fetch_col, fetch_tag,
  output wire [511:0] fetch_data,
  output wire [63:0] fetch_strobes,
  input wire response_valid,
  output wire response_ready,
  input wire [31:0] response_tag,
  input wire response_write, response_error,
  output wire work_active, result_needed
);
  import anvil_q1_fp2_pkg::*;
  localparam IDLE=0, COLLECT=1, QUANTIZE=2, QUANT_WAIT=3;
  localparam WRITE0=4, ACK0=5, WRITE1=6, ACK1=7, SCALE=8, ACK_SCALE=9;
  localparam NEXT=10, COMPLETE_WAIT=11, ERROR_WAIT0=12, ERROR_WAIT1=13, FINISH=14;
  reg [3:0] state, kind;
  reg format_mx, failed;
  reg [31:0] layer, row, length, received, base, width;
  reg [1023:0] gathered;
  reg [511:0] packed_mx;
  reg [15:0] scales;
  reg [4:0] flags;
  wire [20:0] converted=fp32_to_bf16(in_data);
  wire quant_valid;
  wire [511:0] quant_data;
  wire [15:0] quant_scales;
  wire [4:0] quant_status;
  wire [6:0] quant_saturations;
  wire [63:0] mask=64'hffffffffffffffff >> (64-width);
  wire ack=response_valid && response_ready;
  wire [31:0] expected_tag=state==ACK_SCALE ?
    {5'd0,base[31:11],6'd0} : (state==ACK1 ? base+32 : base);
  wire [31:0] roundtrip={converted[15:0],16'd0};
  wire [31:0] ordered_input=in_data[31] ? ~in_data : in_data ^ 32'h80000000;
  wire [31:0] ordered_roundtrip=roundtrip[31] ? ~roundtrip : roundtrip ^ 32'h80000000;
  assign ulp_valid=rst_n && in_valid && in_ready;
  assign ulp_distance=(in_data[30:23]==255 || roundtrip[30:23]==255) ? 32'hffffffff :
    (ordered_input>ordered_roundtrip ? ordered_input-ordered_roundtrip :
     ordered_roundtrip-ordered_input);
  assign cmd_ready=rst_n && state==IDLE;
  assign in_ready=rst_n && state==COLLECT;
  assign done=rst_n && state==FINISH;
  assign error=done && failed;
  assign status=done ? flags : 5'd0;
  assign fetch_valid=rst_n && (state==WRITE0 || state==WRITE1 || state==SCALE);
  assign fetch_scale=fetch_valid && state==SCALE;
  assign fetch_kind=fetch_valid ? kind : 4'd0;
  assign fetch_layer=fetch_valid ? layer : 32'd0;
  assign fetch_row=fetch_valid ? row : 32'd0;
  assign fetch_col=fetch_valid ? (state==SCALE ? {5'd0,base[31:11],6'd0} :
    (state==WRITE1 ? base+32 : base)) : 32'd0;
  assign fetch_tag=fetch_col;
  assign fetch_data=!fetch_valid ? 512'd0 :
    (state==SCALE ? ({496'd0,scales} << (8*base[10:5])) :
     (format_mx ? packed_mx : (state==WRITE1 ? gathered[1023:512] : gathered[511:0])));
  assign fetch_strobes=!fetch_valid ? 64'd0 :
    (state==SCALE ? ((width>32 ? 64'd3 : 64'd1) << base[10:5]) :
     (format_mx ? mask :
      (state==WRITE1 ? (64'hffffffffffffffff >> (64-2*(width-32))) :
       (width>=32 ? 64'hffffffffffffffff : (64'hffffffffffffffff >> (64-2*width))))));
  assign response_ready=rst_n && (state==ACK0 || state==ACK1 || state==ACK_SCALE);
  assign work_active=rst_n && state>=WRITE0 && state<=ACK_SCALE;
  assign result_needed=response_ready;
  generate if (MAX_VECTOR<1) begin: invalid_parameters
    initial $fatal(1,"FP2 KV WRITER PARAMETER ERROR");
  end endgenerate
  anvil_q1_fp2_mx_quantize quantizer(
    .clk(clk),.rst_n(rst_n),.in_valid(state==QUANTIZE),.bf16_data(gathered),
    .lane_mask(mask),.out_valid(quant_valid),.mx_data(quant_data),
    .scales(quant_scales),.status(quant_status),.saturation_events(quant_saturations));
  always @(posedge clk) begin
    if (!rst_n) begin
      state<=IDLE; kind<=0; format_mx<=0; failed<=0; layer<=0; row<=0;
      length<=0; received<=0; base<=0; width<=0; gathered<=0;
      packed_mx<=0; scales<=0; flags<=0;
    end else if (ack && (response_error || !response_write || response_tag!=expected_tag)) begin
      failed<=1; state<=ERROR_WAIT0;
    end else case (state)
      IDLE: if (cmd_valid) begin
        kind<=cmd_kind; format_mx<=cmd_format_mx; layer<=cmd_layer; row<=cmd_row;
        length<=cmd_len; received<=0; base<=0; gathered<=0; flags<=0; failed<=0;
        width<=cmd_len<64 ? cmd_len : 32'd64;
        if (cmd_len==0 || cmd_len>MAX_VECTOR || (cmd_kind!=9 && cmd_kind!=10)) begin
          failed<=1; state<=ERROR_WAIT0;
        end else state<=COLLECT;
      end
      COLLECT: if (in_valid) begin
        gathered[16*received[5:0]+:16]<=converted[15:0];
        flags<=flags | converted[20:16];
        if (in_last!=(received+1==length) || (|converted[20:18]) ||
            in_data[30:23]==255) begin failed<=1; state<=ERROR_WAIT0; end
        else if (in_last || (&received[5:0])) begin
          if (format_mx) state<=QUANTIZE; else state<=WRITE0;
        end else received<=received+1'b1;
      end
      QUANTIZE: state<=QUANT_WAIT;
      QUANT_WAIT: if (quant_valid) begin
        packed_mx<=quant_data; scales<=quant_scales; flags<=flags | quant_status;
        if ((|quant_status[4:2]) || quant_saturations!=0) begin failed<=1; state<=ERROR_WAIT0; end
        else state<=WRITE0;
      end
      WRITE0: if (fetch_ready) state<=ACK0;
      ACK0: if (ack) begin
        if (format_mx) state<=SCALE;
        else if (width>32) state<=WRITE1;
        else state<=NEXT;
      end
      WRITE1: if (fetch_ready) state<=ACK1;
      ACK1: if (ack) state<=NEXT;
      SCALE: if (fetch_ready) state<=ACK_SCALE;
      ACK_SCALE: if (ack) state<=NEXT;
      NEXT: begin
        if (received+1==length) state<=COMPLETE_WAIT;
        else begin
          received<=received+1'b1; base<=base+width; gathered<=0;
          width<=length-base-width<64 ? length-base-width : 32'd64;
          state<=COLLECT;
        end
      end
      COMPLETE_WAIT: state<=FINISH;
      ERROR_WAIT0: state<=ERROR_WAIT1;
      ERROR_WAIT1: state<=FINISH;
      FINISH: state<=IDLE;
      default: begin failed<=1; state<=ERROR_WAIT0; end
    endcase
  end
endmodule
