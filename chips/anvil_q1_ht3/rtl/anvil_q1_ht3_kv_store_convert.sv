module anvil_q1_ht3_kv_store_convert (
  input wire clk, rst_n, abort_error,
  input wire in_valid,
  output wire in_ready,
  input wire [1:0] in_format, in_node,
  input wire [31:0] in_layer, in_column,
  input wire in_first, in_last,
  input wire [31:0] in_key, in_value,
  input wire [31:0] in_key_scale, in_value_scale,
  output wire out_valid,
  input wire out_ready,
  output wire [1:0] out_format, out_node,
  output wire [31:0] out_layer, out_column,
  output wire out_first, out_last,
  output wire [15:0] out_key, out_value,
  output wire out_error,
  output wire busy
);
  import anvil_q1_ht3_fp_pkg::*;
  localparam IDLE = 2'd0, NATIVE = 2'd1, QUANTIZED = 2'd2, RESPONSE = 2'd3;
  wire run_n;
  reg [1:0] state, format_q, node_q;
  reg [31:0] layer_q, column_q;
  reg first_q, last_q, canceled, native_error_q;
  reg [15:0] native_key_q, native_value_q, response_key, response_value;
  reg response_error;
  wire key_ready, value_ready, key_valid, value_valid;
  wire [15:0] key_code, value_code;
  wire key_error, value_error;
  wire quantized_request = in_valid && in_ready && in_format[1];
  wire join_responses = run_n && state == QUANTIZED && key_valid && value_valid;
  wire [15:0] narrowed_key = narrow32(in_key, in_format == 2'd1);
  wire [15:0] narrowed_value = narrow32(in_value, in_format == 2'd1);
  wire native_key_nonfinite = in_format == 2'd1 ?
    (&narrowed_key[14:10]) : (&narrowed_key[14:7]);
  wire native_value_nonfinite = in_format == 2'd1 ?
    (&narrowed_value[14:10]) : (&narrowed_value[14:7]);
  wire native_input_bad = fp32_nonfinite(in_key) || fp32_nonfinite(in_value) ||
    native_key_nonfinite || native_value_nonfinite;

  anvil_q1_ht3_reset_sync u_reset(clk, rst_n, run_n);
  anvil_q1_ht3_kv_quantize u_key_quantize (
    .clk(clk), .rst_n(rst_n),
    .in_valid(quantized_request), .in_ready(key_ready),
    .in_data(in_key), .in_scale(in_key_scale), .in_int8(in_format[0]),
    .out_valid(key_valid), .out_ready(join_responses),
    .out_code(key_code), .out_error(key_error)
  );
  anvil_q1_ht3_kv_quantize u_value_quantize (
    .clk(clk), .rst_n(rst_n),
    .in_valid(quantized_request), .in_ready(value_ready),
    .in_data(in_value), .in_scale(in_value_scale), .in_int8(in_format[0]),
    .out_valid(value_valid), .out_ready(join_responses),
    .out_code(value_code), .out_error(value_error)
  );

  assign in_ready = run_n && state == IDLE && !abort_error &&
    (!in_format[1] || (key_ready && value_ready));
  assign out_valid = run_n && state == RESPONSE;
  assign out_format = out_valid ? format_q : 2'b0;
  assign out_node = out_valid ? node_q : 2'b0;
  assign out_layer = out_valid ? layer_q : 32'b0;
  assign out_column = out_valid ? column_q : 32'b0;
  assign out_first = out_valid && first_q;
  assign out_last = out_valid && last_q;
  assign out_key = out_valid ? response_key : 16'b0;
  assign out_value = out_valid ? response_value : 16'b0;
  assign out_error = out_valid && response_error;
  assign busy = run_n && state != IDLE;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state <= IDLE;
      format_q <= 0;
      node_q <= 0;
      layer_q <= 0;
      column_q <= 0;
      first_q <= 0;
      last_q <= 0;
      canceled <= 0;
      native_error_q <= 0;
      native_key_q <= 0;
      native_value_q <= 0;
      response_key <= 0;
      response_value <= 0;
      response_error <= 0;
    end else if (run_n) begin
      if ((state == NATIVE || state == QUANTIZED) && abort_error)
        canceled <= 1;
      case (state)
        IDLE: if (in_valid && in_ready) begin
          format_q <= in_format;
          node_q <= in_node;
          layer_q <= in_layer;
          column_q <= in_column;
          first_q <= in_first;
          last_q <= in_last;
          canceled <= 0;
          if (in_format[1]) state <= QUANTIZED;
          else begin
            native_key_q <= narrowed_key;
            native_value_q <= narrowed_value;
            native_error_q <= native_input_bad;
            state <= NATIVE;
          end
        end
        NATIVE: begin
          response_key <= native_key_q;
          response_value <= native_value_q;
          response_error <= native_error_q || canceled || abort_error;
          state <= RESPONSE;
        end
        QUANTIZED: if (join_responses) begin
          response_key <= key_code;
          response_value <= value_code;
          response_error <= key_error || value_error || canceled || abort_error;
          state <= RESPONSE;
        end
        RESPONSE: if (out_valid && out_ready) state <= IDLE;
        default: begin
          response_key <= 0;
          response_value <= 0;
          response_error <= 1;
          state <= RESPONSE;
        end
      endcase
    end
  end
endmodule
