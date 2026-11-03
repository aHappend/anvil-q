module anvil_q1_ht2_provisional_kv #(
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
  output wire rsp_error
);
  localparam LEGAL = NUM_LAYERS >= 1 && NUM_LAYERS <= 24 &&
    NUM_KV_HEADS >= 1 && NUM_KV_HEADS <= 2 && HEAD_DIM >= 2 && HEAD_DIM <= 64 &&
    (HEAD_DIM & 1) == 0 && ((NUM_KV_HEADS*HEAD_DIM) & 7) == 0;
  localparam L = LEGAL ? NUM_LAYERS : 1;
  localparam C = LEGAL ? NUM_KV_HEADS*HEAD_DIM : 8;
  wire run_n;
  reg [3:0] slots;
  reg [L-1:0] complete0, complete1, complete2, complete3;
  reg writer_active;
  reg [1:0] writer_node;
  reg [4:0] writer_layer;
  reg [6:0] next_column;
  reg response_valid, response_error, command_error, writing_error;
  reg [31:0] memory_q;
  (* ramstyle = "M20K", ram_style = "block", nomem2reg *)
  reg [31:0] storage [0:4*L*C-1];
  wire command_transfer = cmd_valid && cmd_ready;
  wire writing = write_valid && write_ready;
  wire reading = read_valid && read_ready;
  wire [L-1:0] write_complete = write_node == 0 ? complete0 :
    write_node == 1 ? complete1 : write_node == 2 ? complete2 : complete3;
  wire [L-1:0] read_complete = read_node == 0 ? complete0 :
    read_node == 1 ? complete1 : read_node == 2 ? complete2 : complete3;
  wire write_range = write_layer < L && write_column < C;
  wire read_range = read_layer < L && read_column < C;
  wire write_owned = writer_active ?
    !write_first && write_node == writer_node && write_layer == {27'b0, writer_layer} &&
      write_column == {25'b0, next_column} :
    write_first && write_column == 0 && write_range && !write_complete[write_layer[4:0]];
  wire write_legal = LEGAL && slots[write_node] && write_range && write_owned &&
    write_last == (write_column + 1 == C);
  wire read_collision = (writer_active && read_node == writer_node &&
    read_layer == {27'b0, writer_layer}) ||
    (writing && write_legal && read_node == write_node && read_layer == write_layer);
  wire read_legal = LEGAL && slots[read_node] && read_range &&
    read_complete[read_layer[4:0]] && !read_collision;
  wire [6:0] write_node_layer = {5'b0, write_node} * 7'(L) + {2'b0, write_layer[4:0]};
  wire [6:0] read_node_layer = {5'b0, read_node} * 7'(L) + {2'b0, read_layer[4:0]};
  wire [13:0] write_address = {7'b0, write_node_layer} * 14'(C) +
                                                            {7'b0, write_column[6:0]};
  wire [13:0] read_address = {7'b0, read_node_layer} * 14'(C) +
                                                            {7'b0, read_column[6:0]};

  initial begin
    if (!LEGAL) $fatal(1, "PARAMETER ERROR: provisional KV geometry");
  end
  anvil_q1_ht2_reset_sync u_reset(clk, rst_n, run_n);
  assign cmd_ready = run_n && !flush && !writer_active && !response_valid;
  assign cmd_error = run_n && command_error;
  assign write_ready = run_n && !flush && !command_transfer;
  assign write_error = run_n && writing_error;
  assign read_ready = run_n && !flush && !command_transfer && (!response_valid || rsp_ready);
  assign rsp_valid = run_n && response_valid;
  assign rsp_key = rsp_valid && !response_error ? memory_q[15:0] : 16'b0;
  assign rsp_value = rsp_valid && !response_error ? memory_q[31:16] : 16'b0;
  assign rsp_error = rsp_valid && response_error;
  always @(posedge clk) begin
    if (run_n && !flush) begin
      if (writing && write_legal) storage[write_address] <= {write_value, write_key};
      if (reading && read_legal) memory_q <= storage[read_address];
    end
  end
  always @(posedge clk or negedge run_n) begin
    if (!run_n) begin
      slots <= 0;
      complete0 <= 0;
      complete1 <= 0;
      complete2 <= 0;
      complete3 <= 0;
      writer_active <= 0;
      writer_node <= 0;
      writer_layer <= 0;
      next_column <= 0;
      response_valid <= 0;
      response_error <= 0;
      command_error <= 0;
      writing_error <= 0;
    end else begin
      command_error <= 0;
      writing_error <= 0;
      if (flush) begin
        slots <= 0;
        complete0 <= 0;
        complete1 <= 0;
        complete2 <= 0;
        complete3 <= 0;
        writer_active <= 0;
        response_valid <= 0;
        response_error <= 0;
      end else begin
        if (rsp_valid && rsp_ready) response_valid <= 0;
        if (command_transfer) begin
          if ((cmd_begin && cmd_slots == 0) ||
              (!cmd_begin && ((cmd_slots & ~slots) != 0))) command_error <= 1;
          else begin
            slots <= cmd_slots;
            if (cmd_begin) begin
              complete0 <= 0;
              complete1 <= 0;
              complete2 <= 0;
              complete3 <= 0;
            end else begin
              if (!cmd_slots[0]) complete0 <= 0;
              if (!cmd_slots[1]) complete1 <= 0;
              if (!cmd_slots[2]) complete2 <= 0;
              if (!cmd_slots[3]) complete3 <= 0;
            end
          end
        end
        if (writing) begin
          if (!write_legal) begin
            writing_error <= 1;
            writer_active <= 0;
            if (writer_active) case (writer_node)
              0: complete0[writer_layer] <= 0;
              1: complete1[writer_layer] <= 0;
              2: complete2[writer_layer] <= 0;
              3: complete3[writer_layer] <= 0;
            endcase
          end else begin
            writer_node <= write_node;
            writer_layer <= write_layer[4:0];
            writer_active <= !write_last;
            if (!write_last) next_column <= write_column[6:0] + 1'b1;
            if (write_last) case (write_node)
              0: complete0[write_layer[4:0]] <= 1;
              1: complete1[write_layer[4:0]] <= 1;
              2: complete2[write_layer[4:0]] <= 1;
              3: complete3[write_layer[4:0]] <= 1;
            endcase
          end
        end
        if (reading) begin
          response_valid <= 1;
          response_error <= !read_legal;
        end
      end
    end
  end
endmodule
