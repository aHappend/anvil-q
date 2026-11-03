module anvil_q4_fp_tensor_array #(
  parameter integer LANES=16, TILE_K=128,
  localparam integer SL=(LANES>=1 && LANES<=16) ? LANES : 1,
  localparam integer SK=(TILE_K>=1 && TILE_K<=128) ? TILE_K : 1
) (
  input wire clk, rst_n, flush, cmd_valid,
  output wire cmd_ready,
  input wire [31:0] cmd_length,
  input wire [SL-1:0] cmd_mask,
  input wire [32*SL-1:0] cmd_accumulators,
  input wire cmd_activation_format,
  input wire activation_valid,
  output wire activation_ready,
  input wire [15:0] activation_data,
  input wire weights_valid,
  output wire weights_ready,
  input wire [16*SL-1:0] weight_payload,
  output wire out_valid,
  input wire out_ready,
  output wire [32*SL-1:0] result,
  output wire [4:0] flags,
  output wire error
);
  import anvil_q4_fp_pkg::*;

  // {sNaN,NaN,infinity,zero,sign,FP32 exponent,FP32 fraction}.
  function automatic [35:0] unpack_native(input [15:0] x, input format);
    reg nan_value, infinity_value, zero_value, signaling;
    reg [7:0] exponent;
    reg [22:0] fraction;
    reg [5:0] shift;
    reg [10:0] normalized;
    begin
      exponent=0; fraction=0; shift=0; normalized=0;
      if (!format) begin
        nan_value=x[14:7]==8'hff && x[6:0]!=0;
        infinity_value=x[14:7]==8'hff && x[6:0]==0;
        zero_value=x[14:0]==0;
        signaling=nan_value && !x[6];
        exponent=x[14:7]; fraction={x[6:0],16'd0};
      end else begin
        nan_value=x[14:10]==5'h1f && x[9:0]!=0;
        infinity_value=x[14:10]==5'h1f && x[9:0]==0;
        zero_value=x[14:0]==0;
        signaling=nan_value && !x[9];
        if (x[14:10]!=0) begin
          exponent={3'd0,x[14:10]}+8'd112;
          fraction={x[9:0],13'd0};
        end else if (x[9:0]!=0) begin
          shift=leading_zeros32({22'd0,x[9:0]})-6'd21;
          normalized={1'b0,x[9:0]} << shift;
          exponent=8'd113-{2'd0,shift};
          fraction={normalized[9:0],13'd0};
        end
      end
      unpack_native={signaling,nan_value,infinity_value,zero_value,
        x[15],exponent,fraction};
    end
  endfunction

  function automatic [36:0] pack_native(input [35:0] unpacked);
    reg [31:0] bits;
    begin
      if (unpacked[34]) bits=32'h7fc00000;
      else if (unpacked[33]) bits={unpacked[31],8'hff,23'd0};
      else if (unpacked[32]) bits={unpacked[31],31'd0};
      else bits=unpacked[31:0];
      pack_native={unpacked[35],4'd0,bits};
    end
  endfunction

  generate if (LANES!=SL || TILE_K!=SK) begin : invalid_parameters
    initial $fatal(1,"PARAMETER ERROR: anvil_q4_fp_tensor_array geometry");
    assign cmd_ready=0; assign activation_ready=0; assign weights_ready=0;
    assign out_valid=0; assign result=0; assign flags=0; assign error=0;
  end else begin : legal
    localparam [3:0] IDLE=0, LOAD=1, WEIGHTS=2, UNPACK=3, WIDEN=4,
      MUL_ISSUE=5, MUL_WAIT=6, ADD_ISSUE=7, ADD_WAIT=8,
      PUBLISH=9, RESPONSE=10;
    localparam integer IW=SK>1 ? $clog2(SK) : 1;
    reg [3:0] state;
    reg [31:0] length, index;
    reg [SL-1:0] mask;
    reg activation_format, failed;
    reg [16*SL-1:0] raw_weights;
    reg [15:0] activation_q;
    reg [35:0] activation_unpacked;
    reg [36*SL-1:0] weight_unpacked;
    reg [31:0] activation;
    reg [32*SL-1:0] accumulators, weights, products;
    reg [4:0] flag_register;
    (* ramstyle="M20K", nomem2reg *) reg [15:0] tile [0:SK-1];

    always @(posedge clk) begin
      if (activation_valid && activation_ready)
        tile[index[IW-1:0]]<=activation_data;
      if (weights_valid && weights_ready)
        activation_q<=tile[index[IW-1:0]];
    end

    wire [36:0] widened_activation=pack_native(activation_unpacked);
    wire [SL-1:0] fp_ready, fp_valid;
    wire [32*SL-1:0] fp_result;
    wire [5*SL-1:0] fp_flags;
    wire all_fp_ready=&(fp_ready | ~mask);
    wire all_fp_valid=&(fp_valid | ~mask);
    wire [5*SL-1:0] conversion_flags;
    reg [4:0] combined_fp_flags, combined_conversion_flags;
    integer f;
    always @* begin
      combined_fp_flags=0;
      combined_conversion_flags=widened_activation[36:32];
      for (f=0;f<SL;f=f+1) if (mask[f]) begin
        combined_fp_flags=combined_fp_flags | fp_flags[f*5+:5];
        combined_conversion_flags=combined_conversion_flags | conversion_flags[f*5+:5];
      end
    end

    for (genvar n=0;n<SL;n=n+1) begin : tensor_lanes
      wire [35:0] unpacked_weight=unpack_native(raw_weights[n*16+:16],activation_format);
      wire [36:0] widened_weight=pack_native(weight_unpacked[n*36+:36]);
      assign conversion_flags[n*5+:5]=widened_weight[36:32];
      always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
          weight_unpacked[n*36+:36]<=0;
          weights[n*32+:32]<=0;
        end else if (flush) begin
          weight_unpacked[n*36+:36]<=0;
          weights[n*32+:32]<=0;
        end else begin
          if (state==UNPACK && mask[n])
            weight_unpacked[n*36+:36]<=unpacked_weight;
          if (state==WIDEN && mask[n])
            weights[n*32+:32]<=widened_weight[31:0];
        end
      end
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
    wire [35:0] unpacked_activation=unpack_native(activation_q,activation_format);
    assign cmd_ready=rst_n && !flush && state==IDLE;
    assign activation_ready=rst_n && !flush && state==LOAD;
    assign weights_ready=rst_n && !flush && state==WEIGHTS;
    assign out_valid=rst_n && !flush && state==RESPONSE;
    assign result=out_valid ? accumulators : {32*SL{1'b0}};
    assign flags=out_valid ? flag_register : 5'd0;
    assign error=out_valid && failed;

    integer j;
    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        state<=IDLE; length<=0; index<=0; mask<=0; activation_format<=0;
        failed<=0; raw_weights<=0; activation_unpacked<=0; activation<=0;
        accumulators<=0; products<=0; flag_register<=0;
      end else if (flush) begin
        state<=IDLE; failed<=0; accumulators<=0; flag_register<=0;
        activation<=0; activation_unpacked<=0; raw_weights<=0;
      end else case (state)
        IDLE: if (cmd_valid) begin
          length<=cmd_length; index<=0; mask<=cmd_mask;
          activation_format<=cmd_activation_format; accumulators<=cmd_accumulators;
          flag_register<=0; failed<=0;
          if (cmd_length==0 || cmd_length>SK || cmd_mask==0) begin
            failed<=1; state<=RESPONSE;
          end else state<=LOAD;
        end
        LOAD: if (activation_valid) begin
          if (index+1<length) index<=index+1'b1;
          else begin index<=0; state<=WEIGHTS; end
        end
        WEIGHTS: if (weights_valid) begin raw_weights<=weight_payload; state<=UNPACK; end
        UNPACK: begin activation_unpacked<=unpacked_activation; state<=WIDEN; end
        WIDEN: begin
          activation<=widened_activation[31:0];
          flag_register<=flag_register | combined_conversion_flags;
          state<=MUL_ISSUE;
        end
        MUL_ISSUE: if (all_fp_ready) state<=MUL_WAIT;
        MUL_WAIT: if (all_fp_valid) begin
          products<=fp_result; flag_register<=flag_register | combined_fp_flags;
          state<=ADD_ISSUE;
        end
        ADD_ISSUE: if (all_fp_ready) state<=ADD_WAIT;
        ADD_WAIT: if (all_fp_valid) begin
          for (j=0;j<SL;j=j+1) if (mask[j])
            accumulators[j*32+:32]<=fp_result[j*32+:32];
          flag_register<=flag_register | combined_fp_flags;
          if (index+1<length) begin index<=index+1'b1; state<=WEIGHTS; end
          else state<=PUBLISH;
        end
        PUBLISH: state<=RESPONSE;
        RESPONSE: if (out_ready) state<=IDLE;
        default: begin failed<=1; state<=RESPONSE; end
      endcase
    end
  end endgenerate
endmodule
