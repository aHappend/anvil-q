module anvil_q4_tensor_array #(
  parameter integer LANES=16, TILE_K=128,
  localparam integer SL=(LANES>=1 && LANES<=16) ? LANES : 1,
  localparam integer SK=(TILE_K>=1 && TILE_K<=128) ? TILE_K : 1
) (
  input wire clk, rst_n, flush, cmd_valid,
  output wire cmd_ready,
  input wire [31:0] cmd_length,
  input wire [SL-1:0] cmd_mask,
  input wire [SL*32-1:0] cmd_accumulators,
  input wire cmd_a8, cmd_activation_format, cmd_asymmetric,
  input wire [1:0] cmd_weight_format,
  input wire activation_valid,
  output wire activation_ready,
  input wire [31:0] activation_data,
  input wire weights_valid,
  output wire weights_ready,
  input wire [SL*32-1:0] weight_payload, weight_zero, weight_scale,
  input wire [SL*3-1:0] weight_lane,
  output wire out_valid,
  input wire out_ready,
  output wire [SL*32-1:0] result,
  output wire [4:0] flags,
  output wire error
);
  import anvil_q4_fp_pkg::*;
  generate if (LANES!=SL || TILE_K!=SK) begin : invalid_parameters
    initial $fatal(1,"PARAMETER ERROR: anvil_q4_tensor_array geometry");
    assign cmd_ready=0; assign activation_ready=0; assign weights_ready=0;
    assign out_valid=0; assign result=0; assign flags=0; assign error=0;
  end else begin : legal
    localparam [4:0] IDLE=0, LOAD=1, SCALE_ISSUE=2, SCALE_WAIT=3,
      READ=4, READ_WAIT=5, QUANT_ISSUE=6, QUANT_WAIT=7, WEIGHTS=8,
      DEQUANT_ISSUE=9, DEQUANT_WAIT=10, MUL_ISSUE=11, MUL_WAIT=12,
      ADD_ISSUE=13, ADD_WAIT=14, RESPONSE=15;
    localparam integer IW=SK>1 ? $clog2(SK) : 1;
    reg [4:0] state;
    reg [31:0] length, index, maximum, tensor_scale, activation, tile_q;
    reg [SL-1:0] mask;
    reg a8, activation_format, asymmetric, failed, saw_nan;
    reg [1:0] format;
    reg [SL*32-1:0] accumulators, payloads, zeros, scales, weights, products;
    reg [SL*3-1:0] lanes;
    reg [4:0] flag_register;
    (* ramstyle="M20K", nomem2reg *) reg [31:0] tile [0:SK-1];
    wire [IW-1:0] tile_index=index[IW-1:0];
    always @(posedge clk) begin
      if (rst_n && !flush && state==LOAD && activation_valid)
        tile[tile_index]<=activation_data;
      if (rst_n && !flush && state==READ) tile_q<=tile[tile_index];
    end
    wire scale_ready, scale_valid;
    wire [31:0] scale_result;
    wire [4:0] scale_flags;
    wire quant_ready, quant_valid, quant_error;
    wire [31:0] quant_result;
    wire [4:0] quant_flags;
    wire [SL-1:0] dq_ready, dq_valid, dq_error, fp_ready, fp_valid;
    wire [SL*32-1:0] dq_result, fp_result;
    wire [SL*5-1:0] dq_flags, fp_flags;
    wire all_dq_ready=&(dq_ready | ~mask);
    wire all_dq_valid=&(dq_valid | ~mask);
    wire all_fp_ready=&(fp_ready | ~mask);
    wire all_fp_valid=&(fp_valid | ~mask);
    reg [4:0] combined_dq_flags, combined_fp_flags;
    integer f;
    always @* begin
      combined_dq_flags=0; combined_fp_flags=0;
      for (f=0;f<SL;f=f+1) if (mask[f]) begin
        combined_dq_flags=combined_dq_flags | dq_flags[f*5+:5];
        combined_fp_flags=combined_fp_flags | fp_flags[f*5+:5];
      end
    end
    anvil_q4_fp32 scale_arithmetic (
      .clk(clk),.rst_n(rst_n),.flush(flush),
      .in_valid(state==SCALE_ISSUE && a8 && !saw_nan && !is_zero(maximum)),
      .in_ready(scale_ready),
      .op(4'd3),.a(maximum),.b(32'h42fe0000),
      .out_valid(scale_valid),.out_ready(state==SCALE_WAIT),
      .result(scale_result),.flags(scale_flags)
    );
    anvil_q4_activation_quantizer activation_quantizer (
      .clk(clk),.rst_n(rst_n),.flush(flush),
      .in_valid(state==QUANT_ISSUE),.in_ready(quant_ready),
      .x(activation),.scale(tensor_scale),
      .out_valid(quant_valid),.out_ready(state==QUANT_WAIT),
      .result(quant_result),.flags(quant_flags),.error(quant_error)
    );
    for (genvar n=0;n<SL;n=n+1) begin : tensor_lanes
      anvil_q4_dequant dequant (
        .clk(clk),.rst_n(rst_n),.flush(flush),
        .in_valid(state==DEQUANT_ISSUE && all_dq_ready && mask[n]),
        .in_ready(dq_ready[n]),.lane_active(mask[n]),
        .weight_format(format),.activation_format(activation_format),
        .asymmetric(asymmetric),.lane(lanes[n*3+:3]),
        .payload(payloads[n*32+:32]),.zero_point(zeros[n*32+:32]),
        .scale(scales[n*32+:32]),.out_valid(dq_valid[n]),
        .out_ready(state==DEQUANT_WAIT && all_dq_valid),
        .result(dq_result[n*32+:32]),.flags(dq_flags[n*5+:5]),.error(dq_error[n])
      );
      anvil_q4_fp32 arithmetic (
        .clk(clk),.rst_n(rst_n),.flush(flush),
        .in_valid((state==MUL_ISSUE || state==ADD_ISSUE) && all_fp_ready && mask[n]),
        .in_ready(fp_ready[n]),.op(state==MUL_ISSUE ? 4'd2 : 4'd0),
        .a(state==MUL_ISSUE ? activation : accumulators[n*32+:32]),
        .b(state==MUL_ISSUE ? weights[n*32+:32] : products[n*32+:32]),
        .out_valid(fp_valid[n]),
        .out_ready((state==MUL_WAIT || state==ADD_WAIT) && all_fp_valid),
        .result(fp_result[n*32+:32]),.flags(fp_flags[n*5+:5])
      );
    end
    assign cmd_ready=rst_n && !flush && state==IDLE;
    assign activation_ready=rst_n && !flush && state==LOAD;
    assign weights_ready=rst_n && !flush && state==WEIGHTS;
    assign out_valid=rst_n && !flush && state==RESPONSE;
    assign result=rst_n && !flush ? accumulators : {SL*32{1'b0}};
    assign flags=rst_n && !flush ? flag_register : 5'd0;
    assign error=out_valid && failed;
    integer j;
    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        state<=IDLE; length<=0; index<=0; maximum<=0; tensor_scale<=0;
        activation<=0; mask<=0; a8<=0; activation_format<=0;
        asymmetric<=0; failed<=0; saw_nan<=0; format<=0;
        accumulators<=0; payloads<=0; zeros<=0; scales<=0;
        weights<=0; products<=0; lanes<=0; flag_register<=0;
      end else if (flush) begin state<=IDLE; failed<=0; accumulators<=0; flag_register<=0; end
      else case (state)
        IDLE: if (cmd_valid) begin
          length<=cmd_length; index<=0; mask<=cmd_mask;
          accumulators<=cmd_accumulators; a8<=cmd_a8;
          activation_format<=cmd_activation_format; asymmetric<=cmd_asymmetric;
          format<=cmd_weight_format; maximum<=0; failed<=0; saw_nan<=0;
          flag_register<=0; tensor_scale<=32'h3f800000;
          if (cmd_length==0 || cmd_length>TILE_K || cmd_weight_format>2 ||
              (cmd_a8 && cmd_weight_format==0) || cmd_mask==0) begin
            failed<=1; state<=RESPONSE;
          end else state<=LOAD;
        end
        LOAD: if (activation_valid) begin
          if (is_nan(activation_data)) saw_nan<=1;
          else if (ordered_less(maximum,{1'b0,activation_data[30:0]}))
            maximum<={1'b0,activation_data[30:0]};
          if (index+1<length) index<=index+1'b1;
          else begin index<=0; state<=SCALE_ISSUE; end
        end
        SCALE_ISSUE: begin
          if (!a8 || saw_nan || is_zero(maximum)) begin
            tensor_scale<=saw_nan ? 32'h7fc00000 : 32'h3f800000; state<=READ;
          end else if (scale_ready) state<=SCALE_WAIT;
        end
        SCALE_WAIT: if (scale_valid) begin
          tensor_scale<=scale_result; flag_register<=flag_register | scale_flags; state<=READ;
        end
        READ: state<=READ_WAIT;
        READ_WAIT: begin
          activation<=tile_q;
          if (a8) state<=QUANT_ISSUE;
          else state<=WEIGHTS;
        end
        QUANT_ISSUE: if (quant_ready) state<=QUANT_WAIT;
        QUANT_WAIT: if (quant_valid) begin
          activation<=quant_result; flag_register<=flag_register | quant_flags;
          if (quant_error) begin failed<=1; state<=RESPONSE; end
          else state<=WEIGHTS;
        end
        WEIGHTS: if (weights_valid) begin
          payloads<=weight_payload; zeros<=weight_zero;
          scales<=weight_scale; lanes<=weight_lane; state<=DEQUANT_ISSUE;
        end
        DEQUANT_ISSUE: if (all_dq_ready) state<=DEQUANT_WAIT;
        DEQUANT_WAIT: if (all_dq_valid) begin
          weights<=dq_result; flag_register<=flag_register | combined_dq_flags;
          if (|(dq_error & mask)) begin failed<=1; state<=RESPONSE; end
          else state<=MUL_ISSUE;
        end
        MUL_ISSUE: if (all_fp_ready) state<=MUL_WAIT;
        MUL_WAIT: if (all_fp_valid) begin
          products<=fp_result; flag_register<=flag_register | combined_fp_flags; state<=ADD_ISSUE;
        end
        ADD_ISSUE: if (all_fp_ready) state<=ADD_WAIT;
        ADD_WAIT: if (all_fp_valid) begin
          for (j=0;j<SL;j=j+1) if (mask[j])
            accumulators[j*32+:32]<=fp_result[j*32+:32];
          flag_register<=flag_register | combined_fp_flags;
          if (index+1<length) begin index<=index+1'b1; state<=READ; end
          else state<=RESPONSE;
        end
        RESPONSE: if (out_ready) state<=IDLE;
        default: begin failed<=1; state<=RESPONSE; end
      endcase
    end
  end endgenerate
endmodule
