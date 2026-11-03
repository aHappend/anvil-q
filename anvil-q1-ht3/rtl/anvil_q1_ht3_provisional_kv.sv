module anvil_q1_ht3_provisional_kv #(
  parameter NUM_LAYERS = 24, NUM_KV_HEADS = 2, HEAD_DIM = 64
) (
  input wire clk, rst_n, flush,
  input wire cmd_valid,
  output wire cmd_ready,
  input wire cmd_begin,
  input wire [3:0] cmd_slots,
  output wire cmd_error,
  input wire write_valid,
  output wire write_ready,
  input wire [1:0] write_node,
  input wire [31:0] write_layer, write_column,
  input wire write_first, write_last,
  input wire [15:0] write_key, write_value,
  output wire write_error,
  input wire read_valid,
  output wire read_ready,
  input wire [1:0] read_node,
  input wire [31:0] read_layer, read_column,
  output wire rsp_valid,
  input wire rsp_ready,
  output wire [15:0] rsp_key, rsp_value,
  output wire rsp_error,
  input wire [1:0] cmd_format, write_format, read_format,
  input wire [31:0] cmd_image, write_image, read_image,
  input wire write_fault,
  output wire [1:0] rsp_format,
  output wire [31:0] rsp_image
);
  import anvil_q1_ht3_fp_pkg::*;
  localparam LEGAL = NUM_LAYERS >= 1 && NUM_LAYERS <= 24 &&
    NUM_KV_HEADS >= 1 && NUM_KV_HEADS <= 2 && HEAD_DIM >= 2 && HEAD_DIM <= 64 &&
    (HEAD_DIM & 1) == 0 && ((NUM_KV_HEADS*HEAD_DIM) & 7) == 0;
  initial begin
    if (!LEGAL) $fatal(1, "PARAMETER ERROR: HT3 provisional KV geometry");
  end
  generate if (!LEGAL) begin: g_invalid
    assign cmd_ready = 0;
    assign cmd_error = 0;
    assign write_ready = 0;
    assign write_error = 0;
    assign read_ready = 0;
    assign rsp_valid = 0;
    assign rsp_key = 0;
    assign rsp_value = 0;
    assign rsp_error = 0;
    assign rsp_format = 0;
    assign rsp_image = 0;
  end else begin: g_legal
    localparam C = NUM_KV_HEADS*HEAD_DIM;
    localparam ROWS = 4*NUM_LAYERS;
    wire run_n;
    reg [3:0] slots_q;
    reg [ROWS-1:0] complete, poisoned;
    reg [1:0] format_q, writer_node, response_format;
    reg [31:0] image_q, response_image;
    reg writer_active;
    reg [4:0] writer_layer;
    reg [7:0] next_column;
    reg response_valid, response_error, command_error, writing_error;
    reg [31:0] memory_q;
    (* ramstyle = "M20K", nomem2reg *) reg [31:0] storage [0:ROWS*C-1];
    wire command_transfer = cmd_valid && cmd_ready;
    wire writing = write_valid && write_ready;
    wire reading = read_valid && read_ready;
    wire write_range = write_layer < NUM_LAYERS && write_column < C;
    wire read_range = read_layer < NUM_LAYERS && read_column < C;
    wire [6:0] write_row = 7'(write_node*NUM_LAYERS) + {2'b0, write_layer[4:0]};
    wire [6:0] read_row = 7'(read_node*NUM_LAYERS) + {2'b0, read_layer[4:0]};
    wire [6:0] writer_row = 7'(writer_node*NUM_LAYERS) + {2'b0, writer_layer};
    wire write_complete = write_range ? complete[write_row] : 1'b0;
    wire write_poisoned = write_range ? poisoned[write_row] : 1'b0;
    wire read_complete = read_range ? complete[read_row] : 1'b0;
    wire read_poisoned = read_range ? poisoned[read_row] : 1'b0;
    wire write_owned = writer_active ?
      !write_first && write_node == writer_node &&
        write_layer == {27'b0, writer_layer} &&
        write_column == {24'b0, next_column} :
      write_first && write_column == 0 && !write_complete;
    wire write_bits_bad = format_q == 2 ?
      ((|write_key[15:4]) || (|write_value[15:4])) : format_q == 3 ?
      ((|write_key[15:8]) || (|write_value[15:8])) :
      (fp32_nonfinite(expand16(write_key, format_q == 1)) ||
       fp32_nonfinite(expand16(write_value, format_q == 1)));
    wire write_legal = slots_q[write_node] && write_range && write_owned &&
      !write_poisoned && write_format == format_q && write_image == image_q &&
      write_last == (write_column + 1'b1 == C) && !write_fault && !write_bits_bad;
    wire collision = (writer_active && read_node == writer_node &&
      read_layer == {27'b0, writer_layer}) ||
      (writing && read_node == write_node && read_layer == write_layer);
    wire read_legal = slots_q[read_node] && read_range && read_complete &&
      !read_poisoned && !collision && read_format == format_q && read_image == image_q;
    wire [13:0] write_address = 14'(write_row*C) + {7'b0, write_column[6:0]};
    wire [13:0] read_address = 14'(read_row*C) + {7'b0, read_column[6:0]};
    integer row;

    anvil_q1_ht3_reset_sync u_reset(clk, rst_n, run_n);
    assign cmd_ready = run_n && !flush && !writer_active && !response_valid;
    assign cmd_error = run_n && command_error;
    assign write_ready = run_n && !flush && !command_transfer;
    assign write_error = run_n && writing_error;
    assign read_ready = run_n && !flush && !command_transfer &&
      (!response_valid || rsp_ready);
    assign rsp_valid = run_n && response_valid;
    assign rsp_key = rsp_valid && !response_error ? memory_q[15:0] : 16'b0;
    assign rsp_value = rsp_valid && !response_error ? memory_q[31:16] : 16'b0;
    assign rsp_error = rsp_valid && response_error;
    assign rsp_format = rsp_valid ? response_format : 2'b0;
    assign rsp_image = rsp_valid ? response_image : 32'b0;

    always @(posedge clk) begin
      if (run_n && !flush) begin
        if (writing && write_legal) storage[write_address] <= {write_value, write_key};
        if (reading && read_legal) memory_q <= storage[read_address];
      end
    end
    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        slots_q <= 0;
        complete <= 0;
        poisoned <= 0;
        format_q <= 0;
        image_q <= 0;
        writer_active <= 0;
        writer_node <= 0;
        writer_layer <= 0;
        next_column <= 0;
        response_valid <= 0;
        response_error <= 0;
        response_format <= 0;
        response_image <= 0;
        command_error <= 0;
        writing_error <= 0;
      end else if (run_n) begin
        command_error <= 0;
        writing_error <= 0;
        if (rsp_valid && rsp_ready) response_valid <= 0;
        if (flush) begin
          slots_q <= 0;
          complete <= 0;
          poisoned <= 0;
          writer_active <= 0;
        end else begin
          if (command_transfer) begin
            if ((cmd_begin && cmd_slots == 0) ||
                (!cmd_begin && ((cmd_slots & ~slots_q) != 0 ||
                 cmd_format != format_q || cmd_image != image_q)))
              command_error <= 1;
            else begin
              slots_q <= cmd_slots;
              if (cmd_begin) begin
                format_q <= cmd_format;
                image_q <= cmd_image;
                complete <= 0;
                poisoned <= 0;
              end else begin
                for (row = 0; row < NUM_LAYERS; row = row + 1) begin
                  if (!cmd_slots[0]) begin complete[row] <= 0; poisoned[row] <= 0; end
                  if (!cmd_slots[1]) begin
                    complete[NUM_LAYERS+row] <= 0;
                    poisoned[NUM_LAYERS+row] <= 0;
                  end
                  if (!cmd_slots[2]) begin
                    complete[2*NUM_LAYERS+row] <= 0;
                    poisoned[2*NUM_LAYERS+row] <= 0;
                  end
                  if (!cmd_slots[3]) begin
                    complete[3*NUM_LAYERS+row] <= 0;
                    poisoned[3*NUM_LAYERS+row] <= 0;
                  end
                end
              end
            end
          end
          if (writing) begin
            if (!write_legal) begin
              writing_error <= 1;
              writer_active <= 0;
              if (writer_active) begin
                complete[writer_row] <= 0;
                poisoned[writer_row] <= 1;
              end
              if (write_range && slots_q[write_node]) begin
                complete[write_row] <= 0;
                poisoned[write_row] <= 1;
              end
            end else begin
              writer_node <= write_node;
              writer_layer <= write_layer[4:0];
              writer_active <= !write_last;
              if (!write_last) next_column <= write_column[7:0] + 1'b1;
              if (write_last) complete[write_row] <= 1;
            end
          end
          if (reading) begin
            response_valid <= 1;
            response_error <= !read_legal;
            response_format <= format_q;
            response_image <= image_q;
          end
        end
      end
    end
  end endgenerate
endmodule
