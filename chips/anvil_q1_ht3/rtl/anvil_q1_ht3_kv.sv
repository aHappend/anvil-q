module anvil_q1_ht3_kv #(
  parameter NUM_LAYERS = 24, NUM_KV_HEADS = 2,
  parameter HEAD_DIM = 64, MAX_SEQ_LEN = 32768
) (
  input wire clk, rst_n, flush, abort_error, cmd_valid,
  output wire cmd_ready,
  input wire cmd_begin,
  input wire [3:0] cmd_slots,
  output wire cmd_error,
  input wire store_valid,
  output wire store_ready,
  input wire [1:0] store_node,
  input wire [31:0] store_layer, store_column,
  input wire store_first, store_last,
  input wire [15:0] store_key, store_value,
  output wire store_error,
  input wire read_valid,
  output wire read_ready,
  input wire read_provisional, read_fp16,
  input wire [1:0] read_node,
  input wire [31:0] read_layer, read_head, read_column,
  input wire [31:0] read_position, read_prefix_length,
  input wire [32:0] read_key_base, read_value_base,
  input wire [31:0] read_key_length, read_value_length,
  output wire read_rsp_valid,
  input wire read_rsp_ready,
  output wire [15:0] read_rsp_key, read_rsp_value,
  output wire read_rsp_error,
  input wire copy_valid,
  output wire copy_ready,
  input wire copy_fp16,
  input wire [1:0] copy_node,
  input wire [31:0] copy_layer, copy_position, copy_prefix_length,
  input wire [32:0] copy_key_base, copy_value_base,
  input wire [31:0] copy_key_length, copy_value_length,
  output wire copy_rsp_valid,
  input wire copy_rsp_ready,
  output wire copy_rsp_error,
  output wire read_dma_valid,
  input wire read_dma_ready,
  output wire [32:0] read_dma_address,
  output wire [7:0] read_dma_burstcount,
  input wire read_dma_data_valid,
  output wire read_dma_data_ready,
  input wire [511:0] read_dma_data,
  input wire read_dma_error,
  output wire write_dma_valid,
  input wire write_dma_ready,
  output wire [32:0] write_dma_address,
  output wire [511:0] write_dma_data,
  output wire [63:0] write_dma_byteenable,
  input wire write_dma_rsp_valid,
  output wire write_dma_rsp_ready,
  input wire write_dma_error,
  input wire [1:0] cmd_kv_format, store_format, read_kv_format, copy_kv_format,
  input wire [31:0] cmd_image, store_image, read_image, copy_image,
  input wire store_fault,
  input wire [31:0] read_key_scale, read_value_scale,
  output wire [31:0] read_rsp_key_scale, read_rsp_value_scale
);
  import anvil_q1_ht3_fp_pkg::*;
  localparam LEGAL = NUM_LAYERS >= 1 && NUM_LAYERS <= 24 &&
    NUM_KV_HEADS >= 1 && NUM_KV_HEADS <= 2 &&
    HEAD_DIM >= 2 && HEAD_DIM <= 64 && (HEAD_DIM & 1) == 0 &&
    ((NUM_KV_HEADS*HEAD_DIM) & 7) == 0 &&
    MAX_SEQ_LEN >= 1 && MAX_SEQ_LEN <= 32768;
  initial if (!LEGAL) $fatal(1, "PARAMETER ERROR: HT3 KV controller geometry");
  generate if (!LEGAL) begin: g_invalid
    assign cmd_ready = 0;
    assign cmd_error = 0;
    assign store_ready = 0;
    assign store_error = 0;
    assign read_ready = 0;
    assign read_rsp_valid = 0;
    assign read_rsp_key = 0;
    assign read_rsp_value = 0;
    assign read_rsp_error = 0;
    assign read_rsp_key_scale = 0;
    assign read_rsp_value_scale = 0;
    assign copy_ready = 0;
    assign copy_rsp_valid = 0;
    assign copy_rsp_error = 0;
    assign read_dma_valid = 0;
    assign read_dma_address = 0;
    assign read_dma_burstcount = 0;
    assign read_dma_data_ready = 0;
    assign write_dma_valid = 0;
    assign write_dma_address = 0;
    assign write_dma_data = 0;
    assign write_dma_byteenable = 0;
    assign write_dma_rsp_ready = 0;
  end else begin: g_legal
    localparam C = NUM_KV_HEADS*HEAD_DIM;
    localparam R_IDLE = 3'd0, R_PROV_SEND = 3'd1, R_PROV_WAIT = 3'd2,
      R_DDR_SEND = 3'd3, R_DDR_WAIT = 3'd4, R_RESPONSE = 3'd5, R_DRAIN = 3'd6;
    localparam C_IDLE = 4'd0, C_COMMAND = 4'd1, C_INPUT_READY = 4'd2,
      C_FETCH_SEND = 4'd3, C_FETCH_WAIT = 4'd4, C_STREAM = 4'd5,
      C_WAIT = 4'd6, C_RESPONSE = 4'd7, C_DRAIN = 4'd8;
    wire run_n;
    wire cancel = flush || abort_error;
    reg [2:0] read_state;
    reg [3:0] copy_state;
    reg [1:0] format_q, reading_format, copying_format;
    reg [31:0] image_q, reading_image, copying_image;
    reg [3:0] slots_q;
    reg [1:0] reading_node, copying_node;
    reg [31:0] reading_layer, reading_head, reading_column;
    reg [31:0] reading_position, reading_prefix_length;
    reg [31:0] reading_key_scale, reading_value_scale;
    reg [32:0] reading_key_base, reading_value_base;
    reg [31:0] reading_key_length, reading_value_length;
    reg [31:0] copying_layer, copying_position, copying_prefix_length;
    reg [32:0] copying_key_base, copying_value_base;
    reg [31:0] copying_key_length, copying_value_length;
    reg [7:0] copy_column;
    reg [15:0] reading_key, reading_value, copying_key, copying_value;
    reg reading_failed, copying_failed, copy_cancel;
    reg reader_owned, writer_owned, provisional_owned;
    wire idle = read_state == R_IDLE && copy_state == C_IDLE &&
      !reader_owned && !writer_owned && !provisional_owned;
    wire pv_cmd_ready, pv_cmd_error, pv_store_ready, pv_store_error;
    wire pv_read_ready, pv_rsp_valid, pv_rsp_error;
    wire [15:0] pv_key, pv_value;
    wire [1:0] pv_format;
    wire [31:0] pv_image;
    wire pv_read_valid = run_n && !cancel &&
      (read_state == R_PROV_SEND || copy_state == C_FETCH_SEND);
    wire pv_rsp_ready = run_n &&
      (read_state == R_PROV_WAIT || copy_state == C_FETCH_WAIT ||
       read_state == R_DRAIN || copy_state == C_DRAIN);
    wire pv_request = pv_read_valid && pv_read_ready;
    wire pv_response = pv_rsp_valid && pv_rsp_ready;
    wire copying_fetch = copy_state == C_FETCH_SEND;
    wire [1:0] pv_node = copying_fetch ? copying_node : reading_node;
    wire [31:0] pv_layer = copying_fetch ? copying_layer : reading_layer;
    wire [31:0] read_flat_column = reading_column +
      (reading_head == 0 ? 32'd0 : 32'(HEAD_DIM));
    wire [31:0] pv_column = copying_fetch ? {24'b0, copy_column} : read_flat_column;
    wire [1:0] pv_request_format = copying_fetch ? copying_format : reading_format;
    wire [31:0] pv_request_image = copying_fetch ? copying_image : reading_image;
    wire reader_ready, reader_valid, reader_error;
    wire [15:0] reader_key, reader_value;
    wire [31:0] reader_key_scale, reader_value_scale;
    wire reader_request = run_n && !cancel && read_state == R_DDR_SEND;
    wire reader_rsp_ready = run_n && (read_state == R_DDR_WAIT || read_state == R_DRAIN);
    wire reader_response = reader_valid && reader_rsp_ready;
    wire writer_ready, writer_in_ready, writer_valid, writer_error;
    wire writer_request = run_n && !cancel && copy_state == C_COMMAND;
    wire writer_input = run_n && !cancel && copy_state == C_STREAM;
    wire writer_rsp_ready = run_n && (copy_state == C_INPUT_READY ||
      copy_state == C_WAIT || copy_state == C_DRAIN);
    wire writer_response = writer_valid && writer_rsp_ready;
    wire scale_error = read_kv_format[1] &&
      (read_key_scale[31] || read_value_scale[31] ||
       read_key_scale[30:0] == 0 || read_value_scale[30:0] == 0 ||
       fp32_nonfinite(read_key_scale) || fp32_nonfinite(read_value_scale));
    wire command_legal = cmd_begin ? cmd_slots != 0 :
      (cmd_kv_format == format_q && cmd_image == image_q &&
       (cmd_slots & ~slots_q) == 0);

    anvil_q1_ht3_reset_sync u_reset(clk, rst_n, run_n);
    anvil_q1_ht3_provisional_kv #(
      .NUM_LAYERS(NUM_LAYERS), .NUM_KV_HEADS(NUM_KV_HEADS), .HEAD_DIM(HEAD_DIM)
    ) u_provisional (
      .clk(clk), .rst_n(rst_n), .flush(cancel),
      .cmd_valid(cmd_valid && cmd_ready), .cmd_ready(pv_cmd_ready),
      .cmd_begin(cmd_begin), .cmd_slots(cmd_slots), .cmd_error(pv_cmd_error),
      .cmd_format(cmd_kv_format), .cmd_image(cmd_image),
      .write_valid(store_valid && store_ready), .write_ready(pv_store_ready),
      .write_node(store_node), .write_layer(store_layer), .write_column(store_column),
      .write_first(store_first), .write_last(store_last),
      .write_key(store_key), .write_value(store_value), .write_error(pv_store_error),
      .write_format(store_format), .write_image(store_image), .write_fault(store_fault),
      .read_valid(pv_read_valid), .read_ready(pv_read_ready),
      .read_node(pv_node), .read_layer(pv_layer), .read_column(pv_column),
      .read_format(pv_request_format), .read_image(pv_request_image),
      .rsp_valid(pv_rsp_valid), .rsp_ready(pv_rsp_ready),
      .rsp_key(pv_key), .rsp_value(pv_value), .rsp_error(pv_rsp_error),
      .rsp_format(pv_format), .rsp_image(pv_image)
    );
    anvil_q1_ht3_kv_reader #(
      .NUM_KV_HEADS(NUM_KV_HEADS), .HEAD_DIM(HEAD_DIM), .MAX_SEQ_LEN(MAX_SEQ_LEN)
    ) u_committed_reader (
      .clk(clk), .rst_n(rst_n), .abort_error(cancel),
      .invalidate_cache(cancel || copy_state != C_IDLE || (store_valid && store_ready) ||
        (cmd_valid && cmd_ready)),
      .req_valid(reader_request), .req_ready(reader_ready),
      .req_fp16(reading_format == 1), .req_kv_format(reading_format),
      .req_key_scale(reading_key_scale), .req_value_scale(reading_value_scale),
      .req_prefix_length(reading_prefix_length), .req_position(reading_position),
      .req_head(reading_head), .req_column(reading_column),
      .req_key_base(reading_key_base), .req_value_base(reading_value_base),
      .req_key_length(reading_key_length), .req_value_length(reading_value_length),
      .rsp_valid(reader_valid), .rsp_ready(reader_rsp_ready),
      .rsp_key(reader_key), .rsp_value(reader_value), .rsp_error(reader_error),
      .rsp_key_scale(reader_key_scale), .rsp_value_scale(reader_value_scale),
      .dma_valid(read_dma_valid), .dma_ready(read_dma_ready),
      .dma_address(read_dma_address), .dma_burstcount(read_dma_burstcount),
      .dma_data_valid(read_dma_data_valid), .dma_data_ready(read_dma_data_ready),
      .dma_data(read_dma_data), .dma_error(read_dma_error)
    );
    anvil_q1_ht3_kv_writer #(
      .NUM_KV_HEADS(NUM_KV_HEADS), .HEAD_DIM(HEAD_DIM), .MAX_SEQ_LEN(MAX_SEQ_LEN)
    ) u_committed_writer (
      .clk(clk), .rst_n(rst_n), .abort_error(cancel || copy_cancel),
      .cmd_valid(writer_request), .cmd_ready(writer_ready),
      .cmd_fp16(copying_format == 1), .cmd_kv_format(copying_format),
      .cmd_prefix_length(copying_prefix_length), .cmd_position(copying_position),
      .cmd_key_base(copying_key_base), .cmd_value_base(copying_value_base),
      .cmd_key_length(copying_key_length), .cmd_value_length(copying_value_length),
      .in_valid(writer_input), .in_ready(writer_in_ready),
      .in_key(copying_key), .in_value(copying_value),
      .in_first(copy_column == 0), .in_last(copy_column + 1'b1 == C),
      .rsp_valid(writer_valid), .rsp_ready(writer_rsp_ready), .rsp_error(writer_error),
      .dma_valid(write_dma_valid), .dma_ready(write_dma_ready),
      .dma_address(write_dma_address), .dma_data(write_dma_data),
      .dma_byteenable(write_dma_byteenable), .dma_rsp_valid(write_dma_rsp_valid),
      .dma_rsp_ready(write_dma_rsp_ready), .dma_error(write_dma_error)
    );
    assign cmd_ready = run_n && !cancel && idle && !store_valid && pv_cmd_ready;
    assign cmd_error = run_n && pv_cmd_error;
    assign store_ready = run_n && !cancel && copy_state == C_IDLE &&
      !cmd_valid && pv_store_ready;
    assign store_error = run_n && pv_store_error;
    assign copy_ready = run_n && !cancel && idle && !cmd_valid && !store_valid;
    assign read_ready = run_n && !cancel && idle && !cmd_valid && !copy_valid;
    assign read_rsp_valid = run_n && read_state == R_RESPONSE;
    assign read_rsp_key = read_rsp_valid ? reading_key : 16'b0;
    assign read_rsp_value = read_rsp_valid ? reading_value : 16'b0;
    assign read_rsp_error = read_rsp_valid && reading_failed;
    assign read_rsp_key_scale = read_rsp_valid ? reading_key_scale : 32'b0;
    assign read_rsp_value_scale = read_rsp_valid ? reading_value_scale : 32'b0;
    assign copy_rsp_valid = run_n && copy_state == C_RESPONSE;
    assign copy_rsp_error = copy_rsp_valid && copying_failed;

    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        format_q <= 0;
        image_q <= 0;
        slots_q <= 0;
        provisional_owned <= 0;
      end else if (run_n) begin
        if (pv_request) provisional_owned <= 1;
        if (pv_response) provisional_owned <= 0;
        if (cancel) slots_q <= 0;
        else if (cmd_valid && cmd_ready && command_legal) begin
          format_q <= cmd_kv_format;
          image_q <= cmd_image;
          slots_q <= cmd_slots;
        end
      end
    end
    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        read_state <= R_IDLE;
        reading_format <= 0;
        reading_image <= 0;
        reading_node <= 0;
        reading_layer <= 0;
        reading_head <= 0;
        reading_column <= 0;
        reading_position <= 0;
        reading_prefix_length <= 0;
        reading_key_scale <= 0;
        reading_value_scale <= 0;
        reading_key_base <= 0;
        reading_value_base <= 0;
        reading_key_length <= 0;
        reading_value_length <= 0;
        reading_key <= 0;
        reading_value <= 0;
        reading_failed <= 0;
        reader_owned <= 0;
      end else if (run_n) begin
        if (reader_request && reader_ready) reader_owned <= 1;
        if (reader_response) reader_owned <= 0;
        if (cancel && read_state != R_IDLE && read_state != R_RESPONSE &&
            read_state != R_DRAIN) begin
          reading_failed <= 1;
          read_state <= R_DRAIN;
        end else case (read_state)
          R_IDLE: if (read_valid && read_ready) begin
            reading_format <= read_kv_format;
            reading_image <= read_image;
            reading_node <= read_node;
            reading_layer <= read_layer;
            reading_head <= read_head;
            reading_column <= read_column;
            reading_position <= read_position;
            reading_prefix_length <= read_prefix_length;
            reading_key_base <= read_key_base;
            reading_value_base <= read_value_base;
            reading_key_length <= read_key_length;
            reading_value_length <= read_value_length;
            reading_key_scale <= read_key_scale;
            reading_value_scale <= read_value_scale;
            reading_key <= 0;
            reading_value <= 0;
            reading_failed <= 0;
            if (read_layer >= NUM_LAYERS || read_head >= NUM_KV_HEADS ||
                read_column >= HEAD_DIM || read_kv_format != format_q ||
                read_image != image_q || scale_error ||
                read_prefix_length > MAX_SEQ_LEN ||
                (!read_provisional && read_position >= read_prefix_length)) begin
              reading_failed <= 1;
              read_state <= R_RESPONSE;
            end else if (read_provisional) read_state <= R_PROV_SEND;
            else read_state <= R_DDR_SEND;
          end
          R_PROV_SEND: if (pv_request) read_state <= R_PROV_WAIT;
          R_PROV_WAIT: if (pv_response) begin
            reading_key <= pv_key;
            reading_value <= pv_value;
            reading_failed <= pv_rsp_error || pv_format != reading_format ||
              pv_image != reading_image;
            read_state <= R_RESPONSE;
          end
          R_DDR_SEND: if (reader_request && reader_ready) read_state <= R_DDR_WAIT;
          R_DDR_WAIT: if (reader_response) begin
            reading_key <= reader_key;
            reading_value <= reader_value;
            reading_key_scale <= reader_key_scale;
            reading_value_scale <= reader_value_scale;
            reading_failed <= reader_error;
            read_state <= R_RESPONSE;
          end
          R_DRAIN: if ((!reader_owned || reader_response) &&
              (!provisional_owned || pv_response)) read_state <= R_RESPONSE;
          R_RESPONSE: if (read_rsp_ready) read_state <= R_IDLE;
          default: begin reading_failed <= 1; read_state <= R_DRAIN; end
        endcase
      end
    end
    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        copy_state <= C_IDLE;
        copying_format <= 0;
        copying_image <= 0;
        copying_node <= 0;
        copying_layer <= 0;
        copying_position <= 0;
        copying_prefix_length <= 0;
        copying_key_base <= 0;
        copying_value_base <= 0;
        copying_key_length <= 0;
        copying_value_length <= 0;
        copy_column <= 0;
        copying_key <= 0;
        copying_value <= 0;
        copying_failed <= 0;
        copy_cancel <= 0;
        writer_owned <= 0;
      end else if (run_n) begin
        if (writer_request && writer_ready) writer_owned <= 1;
        if (writer_response) writer_owned <= 0;
        if (cancel && copy_state != C_IDLE && copy_state != C_RESPONSE &&
            copy_state != C_DRAIN) begin
          copying_failed <= 1;
          copy_cancel <= 1;
          copy_state <= C_DRAIN;
        end else case (copy_state)
          C_IDLE: begin
            copy_cancel <= 0;
            if (copy_valid && copy_ready) begin
              copying_format <= copy_kv_format;
              copying_image <= copy_image;
              copying_node <= copy_node;
              copying_layer <= copy_layer;
              copying_position <= copy_position;
              copying_prefix_length <= copy_prefix_length;
              copying_key_base <= copy_key_base;
              copying_value_base <= copy_value_base;
              copying_key_length <= copy_key_length;
              copying_value_length <= copy_value_length;
              copy_column <= 0;
              copying_failed <= 0;
              if (copy_layer >= NUM_LAYERS || !slots_q[copy_node] ||
                  copy_kv_format != format_q || copy_image != image_q) begin
                copying_failed <= 1;
                copy_state <= C_RESPONSE;
              end else copy_state <= C_COMMAND;
            end
          end
          C_COMMAND: if (writer_request && writer_ready) copy_state <= C_INPUT_READY;
          C_INPUT_READY: begin
            if (writer_response) begin copying_failed <= 1; copy_state <= C_RESPONSE; end
            else if (writer_in_ready) copy_state <= C_FETCH_SEND;
          end
          C_FETCH_SEND: if (pv_request) copy_state <= C_FETCH_WAIT;
          C_FETCH_WAIT: if (pv_response) begin
            if (pv_rsp_error || pv_format != copying_format || pv_image != copying_image) begin
              copying_failed <= 1;
              copy_cancel <= 1;
              copy_state <= C_WAIT;
            end else begin
              copying_key <= pv_key;
              copying_value <= pv_value;
              copy_state <= C_STREAM;
            end
          end
          C_STREAM: if (writer_input && writer_in_ready) begin
            if (copy_column + 1'b1 == C) copy_state <= C_WAIT;
            else begin copy_column <= copy_column + 1'b1; copy_state <= C_FETCH_SEND; end
          end
          C_WAIT: if (writer_response) begin
            copying_failed <= copying_failed || writer_error;
            copy_state <= C_RESPONSE;
          end
          C_DRAIN: if ((!writer_owned || writer_response) &&
              (!provisional_owned || pv_response)) copy_state <= C_RESPONSE;
          C_RESPONSE: if (copy_rsp_ready) copy_state <= C_IDLE;
          default: begin copying_failed <= 1; copy_cancel <= 1; copy_state <= C_DRAIN; end
        endcase
      end
    end
  end endgenerate
endmodule
