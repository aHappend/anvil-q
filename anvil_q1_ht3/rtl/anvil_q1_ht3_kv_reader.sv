module anvil_q1_ht3_kv_reader #(
  parameter NUM_KV_HEADS = 2, HEAD_DIM = 64, MAX_SEQ_LEN = 32768
) (
  input wire clk, rst_n, abort_error, invalidate_cache,
  input wire req_valid,
  output wire req_ready,
  input wire req_fp16,
  input wire [31:0] req_prefix_length, req_position, req_head, req_column,
  input wire [32:0] req_key_base, req_value_base,
  input wire [31:0] req_key_length, req_value_length,
  output wire rsp_valid,
  input wire rsp_ready,
  output wire [15:0] rsp_key, rsp_value,
  output wire rsp_error,
  output wire dma_valid,
  input wire dma_ready,
  output wire [32:0] dma_address,
  output wire [7:0] dma_burstcount,
  input wire dma_data_valid,
  output wire dma_data_ready,
  input wire [511:0] dma_data,
  input wire dma_error,
  input wire [1:0] req_kv_format,
  input wire [31:0] req_key_scale, req_value_scale,
  output wire [31:0] rsp_key_scale, rsp_value_scale
);
  import anvil_q1_ht3_fp_pkg::*;
  localparam LEGAL = NUM_KV_HEADS >= 1 && NUM_KV_HEADS <= 2 &&
    HEAD_DIM >= 2 && HEAD_DIM <= 64 && (HEAD_DIM & 1) == 0 &&
    ((NUM_KV_HEADS*HEAD_DIM) & 7) == 0 &&
    MAX_SEQ_LEN >= 1 && MAX_SEQ_LEN <= 32768;
  initial begin
    if (!LEGAL) $fatal(1, "PARAMETER ERROR: HT3 committed KV reader geometry");
  end
  generate if (!LEGAL) begin: g_invalid
    assign req_ready = 0;
    assign rsp_valid = 0;
    assign rsp_key = 0;
    assign rsp_value = 0;
    assign rsp_error = 0;
    assign dma_valid = 0;
    assign dma_address = 0;
    assign dma_burstcount = 0;
    assign dma_data_ready = 0;
    assign rsp_key_scale = 0;
    assign rsp_value_scale = 0;
  end else begin: g_legal
    localparam C = NUM_KV_HEADS*HEAD_DIM;
    localparam NATIVE_STRIDE = ((16*C+511) >> 9) << 6;
    localparam INT4_STRIDE = ((4*C+511) >> 9) << 6;
    localparam INT8_STRIDE = ((8*C+511) >> 9) << 6;
    localparam IDLE = 4'd0, OFFSET = 4'd1, ADDRESS = 4'd2, CHECK = 4'd3,
      LOOKUP = 4'd4, KEY_SEND = 4'd5, KEY_WAIT = 4'd6,
      VALUE_SEND = 4'd7, VALUE_WAIT = 4'd8, SELECT = 4'd9, RESPONSE = 4'd10;
    wire run_n;
    reg [3:0] state;
    reg [1:0] format_q, cache_format;
    reg [31:0] key_scale_q, value_scale_q;
    reg [32:0] key_base_q, value_base_q;
    reg [33:0] key_address_q, value_address_q;
    reg [31:0] position_q;
    reg [8:0] stride_q;
    reg [7:0] coordinate_q;
    reg [10:0] bit_offset;
    reg [31:0] row_offset;
    reg [32:0] cache_key_address, cache_value_address;
    reg [511:0] cache_key, cache_value;
    reg [15:0] key_q, value_q;
    reg cache_valid, command_bad, failed, canceled;
    wire [31:0] requested_stride = req_kv_format == 2 ? INT4_STRIDE :
      req_kv_format == 3 ? INT8_STRIDE : NATIVE_STRIDE;
    wire [31:0] requested_length = MAX_SEQ_LEN*requested_stride;
    wire [33:0] key_end = {1'b0, req_key_base} + {2'b0, req_key_length};
    wire [33:0] value_end = {1'b0, req_value_base} + {2'b0, req_value_length};
    wire overlap = {1'b0, req_key_base} < value_end &&
      {1'b0, req_value_base} < key_end;
    wire scales_bad = req_kv_format[1] &&
      (req_key_scale[31] || req_value_scale[31] ||
       req_key_scale[30:0] == 0 || req_value_scale[30:0] == 0 ||
       fp32_nonfinite(req_key_scale) || fp32_nonfinite(req_value_scale));
    wire request_transfer = dma_valid && dma_ready;
    wire response_transfer = dma_data_valid && dma_data_ready;
    reg [15:0] selected_key, selected_value;
    wire selected_bad = !format_q[1] &&
      (fp32_nonfinite(expand16(selected_key, format_q == 1)) ||
       fp32_nonfinite(expand16(selected_value, format_q == 1)));
    wire cache_hit = cache_valid && cache_format == format_q &&
      cache_key_address == key_address_q[32:0] &&
      cache_value_address == value_address_q[32:0];

    anvil_q1_ht3_reset_sync u_reset(clk, rst_n, run_n);
    assign req_ready = run_n && state == IDLE && !abort_error && !invalidate_cache;
    assign rsp_valid = run_n && state == RESPONSE;
    assign rsp_key = rsp_valid && !failed ? key_q : 16'b0;
    assign rsp_value = rsp_valid && !failed ? value_q : 16'b0;
    assign rsp_key_scale = rsp_valid ? key_scale_q : 32'b0;
    assign rsp_value_scale = rsp_valid ? value_scale_q : 32'b0;
    assign rsp_error = rsp_valid && failed;
    assign dma_valid = run_n && (state == KEY_SEND || state == VALUE_SEND);
    assign dma_address = dma_valid ?
      (state == KEY_SEND ? key_address_q[32:0] : value_address_q[32:0]) : 33'b0;
    assign dma_burstcount = dma_valid ? 8'd1 : 8'b0;
    assign dma_data_ready = run_n &&
      (state == KEY_WAIT || state == VALUE_WAIT || (dma_valid && dma_ready));

    always @* begin
      selected_key = 0;
      selected_value = 0;
      case (format_q)
        2: begin
          selected_key[3:0] = cache_key[bit_offset[8:0]+:4];
          selected_value[3:0] = cache_value[bit_offset[8:0]+:4];
        end
        3: begin
          selected_key[7:0] = cache_key[bit_offset[8:0]+:8];
          selected_value[7:0] = cache_value[bit_offset[8:0]+:8];
        end
        default: begin
          selected_key = cache_key[bit_offset[8:0]+:16];
          selected_value = cache_value[bit_offset[8:0]+:16];
        end
      endcase
    end

    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        state <= IDLE;
        format_q <= 0;
        cache_format <= 0;
        key_scale_q <= 0;
        value_scale_q <= 0;
        key_base_q <= 0;
        value_base_q <= 0;
        key_address_q <= 0;
        value_address_q <= 0;
        position_q <= 0;
        stride_q <= 0;
        coordinate_q <= 0;
        bit_offset <= 0;
        row_offset <= 0;
        cache_key_address <= 0;
        cache_value_address <= 0;
        cache_key <= 0;
        cache_value <= 0;
        key_q <= 0;
        value_q <= 0;
        cache_valid <= 0;
        command_bad <= 0;
        failed <= 0;
        canceled <= 0;
      end else if (run_n) begin
        if (abort_error || invalidate_cache) begin
          cache_valid <= 0;
          if (state != IDLE && state != RESPONSE) begin
            canceled <= 1;
            failed <= 1;
            if (state != KEY_SEND && state != KEY_WAIT &&
                state != VALUE_SEND && state != VALUE_WAIT) state <= RESPONSE;
          end
        end
        if (!(abort_error || invalidate_cache) || state == KEY_SEND ||
            state == KEY_WAIT || state == VALUE_SEND || state == VALUE_WAIT ||
            state == RESPONSE) begin
          case (state)
            IDLE: if (req_valid && req_ready) begin
              format_q <= req_kv_format;
              key_scale_q <= req_kv_format[1] ? req_key_scale : 32'b0;
              value_scale_q <= req_kv_format[1] ? req_value_scale : 32'b0;
              key_base_q <= req_key_base;
              value_base_q <= req_value_base;
              position_q <= req_position;
              stride_q <= requested_stride[8:0];
              coordinate_q <= 8'(req_head*HEAD_DIM + req_column);
              failed <= 0;
              canceled <= 0;
              command_bad <= req_prefix_length > MAX_SEQ_LEN ||
                req_position >= req_prefix_length || req_position >= MAX_SEQ_LEN ||
                req_head >= NUM_KV_HEADS || req_column >= HEAD_DIM ||
                req_key_length != requested_length || req_value_length != requested_length ||
                (|req_key_base[5:0]) || (|req_value_base[5:0]) || overlap || scales_bad ||
                key_end > 34'h200000000 || value_end > 34'h200000000;
              state <= OFFSET;
            end
            OFFSET: begin
              row_offset <= position_q*stride_q;
              case (format_q)
                2: bit_offset <= {1'b0, coordinate_q, 2'b0};
                3: bit_offset <= {coordinate_q, 3'b0};
                default: bit_offset <= {coordinate_q[6:0], 4'b0};
              endcase
              state <= ADDRESS;
            end
            ADDRESS: begin
              key_address_q <= {1'b0, key_base_q} + {2'b0, row_offset} +
                {26'b0, bit_offset[10:9], 6'b0};
              value_address_q <= {1'b0, value_base_q} + {2'b0, row_offset} +
                {26'b0, bit_offset[10:9], 6'b0};
              state <= CHECK;
            end
            CHECK: begin
              if (command_bad || key_address_q + 34'd64 > 34'h200000000 ||
                  value_address_q + 34'd64 > 34'h200000000) begin
                failed <= 1;
                state <= RESPONSE;
              end else state <= LOOKUP;
            end
            LOOKUP: begin
              if (cache_hit) state <= SELECT;
              else begin cache_valid <= 0; state <= KEY_SEND; end
            end
            KEY_SEND, KEY_WAIT: begin
              if (request_transfer && !response_transfer) state <= KEY_WAIT;
              if (response_transfer) begin
                if (dma_error || canceled || abort_error || invalidate_cache) begin
                  failed <= 1;
                  state <= RESPONSE;
                end else begin cache_key <= dma_data; state <= VALUE_SEND; end
              end
            end
            VALUE_SEND, VALUE_WAIT: begin
              if (request_transfer && !response_transfer) state <= VALUE_WAIT;
              if (response_transfer) begin
                if (dma_error || canceled || abort_error || invalidate_cache) begin
                  failed <= 1;
                  state <= RESPONSE;
                end else begin
                  cache_value <= dma_data;
                  cache_key_address <= key_address_q[32:0];
                  cache_value_address <= value_address_q[32:0];
                  cache_format <= format_q;
                  cache_valid <= 1;
                  state <= SELECT;
                end
              end
            end
            SELECT: begin
              if (selected_bad) begin failed <= 1; cache_valid <= 0; end
              else begin key_q <= selected_key; value_q <= selected_value; end
              state <= RESPONSE;
            end
            RESPONSE: if (rsp_ready) state <= IDLE;
            default: begin failed <= 1; cache_valid <= 0; state <= RESPONSE; end
          endcase
        end
      end
    end
  end endgenerate
endmodule
