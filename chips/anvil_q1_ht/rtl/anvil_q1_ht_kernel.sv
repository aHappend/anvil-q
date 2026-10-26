module anvil_q1_ht_kernel #(
  parameter NUM_LAYERS = 24, HIDDEN_SIZE = 896, INTERMEDIATE_SIZE = 4864,
  parameter NUM_Q_HEADS = 14, NUM_KV_HEADS = 2, HEAD_DIM = 64,
  parameter MAX_SEQ_LEN = 32768, LEGACY_PARAMETERS = 0
) (
  input wire clk, rst_n, abort_error,
  input wire cmd_valid,
  output wire cmd_ready,
  input wire [2:0] cmd_op,
  input wire [31:0] cmd_layer, cmd_pos,
  output wire done, error,
  output wire mem_req_valid,
  input wire mem_req_ready,
  output wire mem_req_write,
  output wire [3:0] mem_req_kind,
  output wire [31:0] mem_req_layer,
  output wire [2:0] mem_req_proj,
  output wire [31:0] mem_req_row, mem_req_col, mem_req_wdata,
  input wire mem_rsp_valid,
  output wire mem_rsp_ready,
  input wire [31:0] mem_rsp_rdata,
  input wire mem_rsp_error
);
  import anvil_q1_ht_numeric_pkg::*;
  localparam SAFE_KV_HEADS = NUM_KV_HEADS > 0 ? NUM_KV_HEADS : 1;
  localparam HEAD_RATIO = NUM_Q_HEADS / SAFE_KV_HEADS;
  localparam KV_WIDTH = NUM_KV_HEADS*HEAD_DIM;
  localparam LEGAL = LEGACY_PARAMETERS || (NUM_LAYERS >= 1 && NUM_LAYERS <= 24 &&
      HIDDEN_SIZE >= 8 && HIDDEN_SIZE <= 896 && (HIDDEN_SIZE & 7) == 0 &&
      INTERMEDIATE_SIZE >= 8 && INTERMEDIATE_SIZE <= 4864 && (INTERMEDIATE_SIZE & 7) == 0 &&
      NUM_Q_HEADS >= 1 && NUM_Q_HEADS <= 14 && NUM_KV_HEADS >= 1 && NUM_KV_HEADS <= 2 &&
      HEAD_DIM >= 2 && HEAD_DIM <= 64 && (HEAD_DIM & 1) == 0 &&
      HIDDEN_SIZE == NUM_Q_HEADS*HEAD_DIM && (NUM_Q_HEADS % SAFE_KV_HEADS) == 0 &&
      (KV_WIDTH & 7) == 0 && MAX_SEQ_LEN >= 1 && MAX_SEQ_LEN <= 32768);
  generate if (LEGAL) begin : g_legal
    localparam IDLE = 8'd0, COMPLETE = 8'd1, INVALID = 8'd2,
      MEMORY_SEND = 8'd3, MEMORY_WAIT = 8'd4,
      MATH_SEND = 8'd5, MATH_WAIT = 8'd6,
      NONLINEAR_SEND = 8'd7, NONLINEAR_WAIT = 8'd8,
      NORM_READ = 8'd10, NORM_SQUARE = 8'd11, NORM_SUM = 8'd12,
      NORM_SUM_DONE = 8'd13, NORM_MEAN = 8'd14, NORM_EPSILON = 8'd15,
      NORM_ROOT = 8'd16, NORM_RECIPROCAL = 8'd17, NORM_RECIPROCAL_DONE = 8'd18,
      NORM_X = 8'd19, NORM_X_DONE = 8'd20, NORM_GAMMA_DONE = 8'd21,
      NORM_PRODUCT = 8'd22, NORM_SCALE = 8'd23, NORM_ROUND = 8'd24,
      NORM_WRITE = 8'd25, NORM_NEXT = 8'd26,
      ROPE_READ_X = 8'd30, ROPE_X_DONE = 8'd31, ROPE_Y_DONE = 8'd32,
      ROPE_COS_DONE = 8'd33, ROPE_SIN_DONE = 8'd34,
      ROPE_XCOS = 8'd35, ROPE_YSIN = 8'd36, ROPE_SUB = 8'd37,
      ROPE_XROUND = 8'd38, ROPE_XWRITE = 8'd39,
      ROPE_YCOS = 8'd40, ROPE_XSIN = 8'd41, ROPE_ADD = 8'd42,
      ROPE_YROUND = 8'd43, ROPE_YWRITE = 8'd44, ROPE_NEXT = 8'd45,
      ELEMENT_READ_A = 8'd50, ELEMENT_A_DONE = 8'd51,
      ELEMENT_B_DONE = 8'd52, ELEMENT_SILU_DONE = 8'd53,
      ELEMENT_PRODUCT_DONE = 8'd54, ELEMENT_WRITE = 8'd55, ELEMENT_NEXT = 8'd56,
      ATTN_CACHE_READ = 8'd60, ATTN_CACHE_DONE = 8'd61, ATTN_CACHE_NEXT = 8'd62,
      ATTN_ROOT = 8'd63, ATTN_ROOT_DONE = 8'd64,
      ATTN_Q = 8'd65, ATTN_Q_DONE = 8'd66, ATTN_K_DONE = 8'd67,
      ATTN_DOT_SUM = 8'd68, ATTN_DOT_DONE = 8'd69,
      ATTN_SCORE = 8'd70, ATTN_SCORE_DONE = 8'd71, ATTN_SCORE_USE = 8'd72,
      ATTN_DIFF = 8'd73, ATTN_DIFF_DONE = 8'd74, ATTN_EXP_DONE = 8'd75,
      ATTN_DENOM_DONE = 8'd76, ATTN_V_DONE = 8'd77,
      ATTN_WEIGHT_SUM = 8'd78, ATTN_WEIGHT_DONE = 8'd79,
      ATTN_DIVIDE_DONE = 8'd80, ATTN_WRITE_NEXT = 8'd81;
    reg [7:0] state, memory_return, math_return, nonlinear_return;
    reg [2:0] operation;
    reg failed, key_vector, value_cache, context_pass;
    reg [31:0] layer, position, index, source_slot, target_slot;
    reg [3:0] norm_kind;
    reg [31:0] head, head_base, kv_base, head_in_group, pair_index;
    reg [31:0] time_index, dimension, component;
    reg signed [31:0] x, y, cosine, sine;
    reg [95:0] sum;
    reg [63:0] reciprocal, sqrt_dimension, denominator;
    reg signed [95:0] dot, max_score, current_score, weighted;
    reg [31:0] exponential;
    reg [127:0] temporary;
    reg [31:0] read_data;
    reg memory_write;
    reg [3:0] memory_kind;
    reg [31:0] memory_layer, memory_row, memory_col, memory_wdata;
    reg [3:0] math_op;
    reg [127:0] math_a, math_b, math_value;
    reg [6:0] math_shift;
    reg nonlinear_silu;
    reg signed [63:0] nonlinear_argument;
    reg [31:0] nonlinear_value;
    wire math_ready, math_valid, math_error;
    wire [127:0] math_result;
    wire nonlinear_ready, nonlinear_valid, nonlinear_error;
    wire [31:0] nonlinear_result;
    wire memory_complete = mem_rsp_valid && mem_rsp_ready;
    wire signed [96:0] difference = $signed(math_value[96:0]);
    wire [31:0] rope_slot = key_vector ? 32'd3 : 32'd2;
    wire [31:0] rope_column = head_base + pair_index;
    wire [31:0] element_a_slot = operation == 4 ? 32'd0 :
                                           (operation == 5 ? 32'd7 : 32'd9);
    wire [31:0] element_b_slot = operation == 4 ? 32'd6 :
                                           (operation == 5 ? 32'd12 : 32'd10);
    wire [31:0] element_out_slot = operation == 4 ? 32'd7 :
                                             (operation == 5 ? 32'd0 : 32'd11);

    assign cmd_ready = rst_n && state == IDLE;
    assign done = rst_n && state == COMPLETE;
    assign error = done && failed;
    assign mem_req_valid = rst_n && state == MEMORY_SEND && !abort_error;
    assign mem_req_write = mem_req_valid && memory_write;
    assign mem_req_kind = mem_req_valid ? memory_kind : 4'b0;
    assign mem_req_layer = mem_req_valid ? memory_layer : 32'b0;
    assign mem_req_proj = 0;
    assign mem_req_row = mem_req_valid ? memory_row : 32'b0;
    assign mem_req_col = mem_req_valid ? memory_col : 32'b0;
    assign mem_req_wdata = mem_req_valid ? memory_wdata : 32'b0;
    assign mem_rsp_ready = rst_n && (state == MEMORY_WAIT ||
                                    (state == MEMORY_SEND && mem_req_ready));

    anvil_q1_ht_math u_math (
      .clk(clk), .rst_n(rst_n), .in_valid(state == MATH_SEND), .in_ready(math_ready),
      .in_op(math_op), .in_a(math_a), .in_b(math_b), .in_shift(math_shift),
      .out_valid(math_valid), .out_ready(state == MATH_WAIT),
      .out_data(math_result), .out_error(math_error)
    );
    anvil_q1_ht_nonlinear u_nonlinear (
      .clk(clk), .rst_n(rst_n), .in_valid(state == NONLINEAR_SEND),
      .in_ready(nonlinear_ready), .in_silu(nonlinear_silu), .in_data(nonlinear_argument),
      .out_valid(nonlinear_valid), .out_ready(state == NONLINEAR_WAIT),
      .out_data(nonlinear_result), .out_error(nonlinear_error)
    );

    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        state <= IDLE;
        memory_return <= 0;
        math_return <= 0;
        nonlinear_return <= 0;
        operation <= 0;
        failed <= 0;
        key_vector <= 0;
        value_cache <= 0;
        context_pass <= 0;
        layer <= 0;
        position <= 0;
        index <= 0;
        source_slot <= 0;
        target_slot <= 0;
        norm_kind <= 0;
        head <= 0;
        head_base <= 0;
        kv_base <= 0;
        head_in_group <= 0;
        pair_index <= 0;
        time_index <= 0;
        dimension <= 0;
        component <= 0;
        x <= 0;
        y <= 0;
        cosine <= 0;
        sine <= 0;
        sum <= 0;
        reciprocal <= 0;
        sqrt_dimension <= 0;
        denominator <= 0;
        dot <= 0;
        max_score <= 0;
        current_score <= 0;
        weighted <= 0;
        exponential <= 0;
        temporary <= 0;
        read_data <= 0;
        memory_write <= 0;
        memory_kind <= 0;
        memory_layer <= 0;
        memory_row <= 0;
        memory_col <= 0;
        memory_wdata <= 0;
        math_op <= 0;
        math_a <= 0;
        math_b <= 0;
        math_value <= 0;
        math_shift <= 0;
        nonlinear_silu <= 0;
        nonlinear_argument <= 0;
        nonlinear_value <= 0;
      end else if (memory_complete && mem_rsp_error) begin
        failed <= 1;
        state <= COMPLETE;
      end else if (state == MATH_WAIT && math_valid && math_error) begin
        failed <= 1;
        state <= COMPLETE;
      end else if (state == NONLINEAR_WAIT && nonlinear_valid && nonlinear_error) begin
        failed <= 1;
        state <= COMPLETE;
      end else case (state)
        IDLE: if (cmd_valid) begin
          operation <= cmd_op;
          layer <= cmd_layer;
          position <= cmd_pos;
          failed <= 0;
          index <= 0;
          head <= 0;
          head_base <= 0;
          kv_base <= 0;
          head_in_group <= 0;
          pair_index <= 0;
          key_vector <= 0;
          value_cache <= 0;
          context_pass <= 0;
          time_index <= 0;
          dimension <= 0;
          component <= 0;
          sum <= 0;
          dot <= 0;
          weighted <= 0;
          denominator <= 0;
          max_score <= {1'b1, 95'b0};
          memory_write <= 0;
          memory_layer <= 0;
          math_shift <= 0;
          if (cmd_layer >= NUM_LAYERS || cmd_pos >= MAX_SEQ_LEN) begin
            failed <= 1;
            state <= INVALID;
          end else case (cmd_op)
            0, 1, 2: begin
              source_slot <= cmd_op == 1 ? 32'd7 : 32'd0;
              target_slot <= cmd_op == 0 ? 32'd1 : (cmd_op == 1 ? 32'd8 : 32'd14);
              norm_kind <= cmd_op == 0 ? 4'd5 : (cmd_op == 1 ? 4'd6 : 4'd7);
              state <= NORM_READ;
            end
            3: state <= ROPE_READ_X;
            4, 5, 6: state <= ELEMENT_READ_A;
            7: state <= ATTN_CACHE_READ;
          endcase
        end
        MEMORY_SEND, MEMORY_WAIT: begin
          if (memory_complete) begin
            read_data <= mem_rsp_rdata;
            state <= memory_return;
          end else if (state == MEMORY_SEND && mem_req_ready) state <= MEMORY_WAIT;
        end
        MATH_SEND: if (math_ready) state <= MATH_WAIT;
        MATH_WAIT: if (math_valid) begin
          math_value <= math_result;
          state <= math_return;
        end
        NONLINEAR_SEND: if (nonlinear_ready) state <= NONLINEAR_WAIT;
        NONLINEAR_WAIT: if (nonlinear_valid) begin
          nonlinear_value <= nonlinear_result;
          state <= nonlinear_return;
        end
        NORM_READ: begin
          memory_write <= 0;
          memory_kind <= 8;
          memory_layer <= 0;
          memory_row <= source_slot;
          memory_col <= index;
          memory_return <= NORM_SQUARE;
          state <= MEMORY_SEND;
        end
        NORM_SQUARE: begin
          math_op <= MATH_MUL;
          math_a <= {{96{read_data[31]}}, read_data};
          math_b <= {{96{read_data[31]}}, read_data};
          math_return <= NORM_SUM;
          state <= MATH_SEND;
        end
        NORM_SUM: begin
          math_op <= MATH_ADD;
          math_a <= {32'b0, sum};
          math_b <= {64'b0, math_value[63:0]};
          math_return <= NORM_SUM_DONE;
          state <= MATH_SEND;
        end
        NORM_SUM_DONE: begin
          sum <= math_value[95:0];
          if (index + 1 < HIDDEN_SIZE) begin
            index <= index + 32'd1;
            state <= NORM_READ;
          end else state <= NORM_MEAN;
        end
        NORM_MEAN: begin
          math_op <= MATH_UDIV;
          math_a <= {sum, 32'b0};
          math_b <= 128'(HIDDEN_SIZE);
          math_return <= NORM_EPSILON;
          state <= MATH_SEND;
        end
        NORM_EPSILON: begin
          math_op <= MATH_ADD;
          math_a <= math_value;
          math_b <= 128'd18446744073710;
          math_return <= NORM_ROOT;
          state <= MATH_SEND;
        end
        NORM_ROOT: begin
          math_op <= MATH_ISQRT;
          math_a <= math_value;
          math_return <= NORM_RECIPROCAL;
          state <= MATH_SEND;
        end
        NORM_RECIPROCAL: begin
          math_op <= MATH_UDIV;
          math_a <= 128'd18446744073709551616;
          math_b <= {64'b0, math_value[63:0]};
          math_return <= NORM_RECIPROCAL_DONE;
          state <= MATH_SEND;
        end
        NORM_RECIPROCAL_DONE: begin
          reciprocal <= math_value[63:0];
          index <= 0;
          state <= NORM_X;
        end
        NORM_X: begin
          memory_write <= 0;
          memory_kind <= 8;
          memory_layer <= 0;
          memory_row <= source_slot;
          memory_col <= index;
          memory_return <= NORM_X_DONE;
          state <= MEMORY_SEND;
        end
        NORM_X_DONE: begin
          x <= read_data;
          memory_kind <= norm_kind;
          memory_layer <= norm_kind == 7 ? 32'd0 : layer;
          memory_row <= 0;
          memory_return <= NORM_GAMMA_DONE;
          state <= MEMORY_SEND;
        end
        NORM_GAMMA_DONE: begin
          if (fp16_invalid(read_data[15:0])) begin
            failed <= 1;
            state <= COMPLETE;
          end else begin
            y <= fp16_q16(read_data[15:0]);
            state <= NORM_PRODUCT;
          end
        end
        NORM_PRODUCT: begin
          math_op <= MATH_MUL;
          math_a <= {{96{x[31]}}, x};
          math_b <= {{96{y[31]}}, y};
          math_return <= NORM_SCALE;
          state <= MATH_SEND;
        end
        NORM_SCALE: begin
          math_op <= MATH_MUL;
          math_a <= {{64{math_value[63]}}, math_value[63:0]};
          math_b <= {64'b0, reciprocal};
          math_return <= NORM_ROUND;
          state <= MATH_SEND;
        end
        NORM_ROUND: begin
          math_op <= MATH_ROUND_SHIFT;
          math_a <= math_value;
          math_shift <= 48;
          math_return <= NORM_WRITE;
          state <= MATH_SEND;
        end
        NORM_WRITE: begin
          memory_write <= 1;
          memory_kind <= 8;
          memory_layer <= 0;
          memory_row <= target_slot;
          memory_col <= index;
          memory_wdata <= sat32($signed(math_value));
          memory_return <= NORM_NEXT;
          state <= MEMORY_SEND;
        end
        NORM_NEXT: begin
          if (index + 1 < HIDDEN_SIZE) begin
            index <= index + 32'd1;
            state <= NORM_X;
          end else state <= COMPLETE;
        end
        ROPE_READ_X: begin
          memory_write <= 0;
          memory_kind <= 8;
          memory_row <= rope_slot;
          memory_col <= rope_column;
          memory_return <= ROPE_X_DONE;
          state <= MEMORY_SEND;
        end
        ROPE_X_DONE: begin
          x <= read_data;
          memory_col <= rope_column + (HEAD_DIM >> 1);
          memory_return <= ROPE_Y_DONE;
          state <= MEMORY_SEND;
        end
        ROPE_Y_DONE: begin
          y <= read_data;
          memory_kind <= 11;
          memory_row <= position;
          memory_col <= pair_index << 1;
          memory_return <= ROPE_COS_DONE;
          state <= MEMORY_SEND;
        end
        ROPE_COS_DONE: begin
          cosine <= read_data;
          memory_col <= (pair_index << 1) + 32'd1;
          memory_return <= ROPE_SIN_DONE;
          state <= MEMORY_SEND;
        end
        ROPE_SIN_DONE: begin
          sine <= read_data;
          state <= ROPE_XCOS;
        end
        ROPE_XCOS: begin
          math_op <= MATH_MUL;
          math_a <= {{96{x[31]}}, x};
          math_b <= {{96{cosine[31]}}, cosine};
          math_return <= ROPE_YSIN;
          state <= MATH_SEND;
        end
        ROPE_YSIN: begin
          temporary <= {{64{math_value[63]}}, math_value[63:0]};
          math_a <= {{96{y[31]}}, y};
          math_b <= {{96{sine[31]}}, sine};
          math_return <= ROPE_SUB;
          state <= MATH_SEND;
        end
        ROPE_SUB: begin
          math_op <= MATH_SUB;
          math_a <= temporary;
          math_b <= {{64{math_value[63]}}, math_value[63:0]};
          math_return <= ROPE_XROUND;
          state <= MATH_SEND;
        end
        ROPE_XROUND: begin
          math_op <= MATH_ROUND_SHIFT;
          math_a <= {{63{math_value[64]}}, math_value[64:0]};
          math_shift <= 30;
          math_return <= ROPE_XWRITE;
          state <= MATH_SEND;
        end
        ROPE_XWRITE: begin
          memory_write <= 1;
          memory_kind <= 8;
          memory_row <= rope_slot;
          memory_col <= rope_column;
          memory_wdata <= sat32($signed(math_value));
          memory_return <= ROPE_YCOS;
          state <= MEMORY_SEND;
        end
        ROPE_YCOS: begin
          math_op <= MATH_MUL;
          math_a <= {{96{y[31]}}, y};
          math_b <= {{96{cosine[31]}}, cosine};
          math_return <= ROPE_XSIN;
          state <= MATH_SEND;
        end
        ROPE_XSIN: begin
          temporary <= {{64{math_value[63]}}, math_value[63:0]};
          math_a <= {{96{x[31]}}, x};
          math_b <= {{96{sine[31]}}, sine};
          math_return <= ROPE_ADD;
          state <= MATH_SEND;
        end
        ROPE_ADD: begin
          math_op <= MATH_ADD;
          math_a <= temporary;
          math_b <= {{64{math_value[63]}}, math_value[63:0]};
          math_return <= ROPE_YROUND;
          state <= MATH_SEND;
        end
        ROPE_YROUND: begin
          math_op <= MATH_ROUND_SHIFT;
          math_a <= {{63{math_value[64]}}, math_value[64:0]};
          math_shift <= 30;
          math_return <= ROPE_YWRITE;
          state <= MATH_SEND;
        end
        ROPE_YWRITE: begin
          memory_write <= 1;
          memory_kind <= 8;
          memory_row <= rope_slot;
          memory_col <= rope_column + (HEAD_DIM >> 1);
          memory_wdata <= sat32($signed(math_value));
          memory_return <= ROPE_NEXT;
          state <= MEMORY_SEND;
        end
        ROPE_NEXT: begin
          if (pair_index + 1 < (HEAD_DIM >> 1)) begin
            pair_index <= pair_index + 32'd1;
            state <= ROPE_READ_X;
          end else if (head + 1 < (key_vector ? NUM_KV_HEADS : NUM_Q_HEADS)) begin
            pair_index <= 0;
            head <= head + 32'd1;
            head_base <= head_base + 32'(HEAD_DIM);
            state <= ROPE_READ_X;
          end else if (!key_vector) begin
            key_vector <= 1;
            pair_index <= 0;
            head <= 0;
            head_base <= 0;
            state <= ROPE_READ_X;
          end else state <= COMPLETE;
        end
        ELEMENT_READ_A: begin
          memory_write <= 0;
          memory_kind <= 8;
          memory_row <= element_a_slot;
          memory_col <= index;
          memory_return <= ELEMENT_A_DONE;
          state <= MEMORY_SEND;
        end
        ELEMENT_A_DONE: begin
          x <= read_data;
          memory_row <= element_b_slot;
          memory_return <= ELEMENT_B_DONE;
          state <= MEMORY_SEND;
        end
        ELEMENT_B_DONE: begin
          y <= read_data;
          if (operation == 6) begin
            nonlinear_silu <= 1;
            nonlinear_argument <= {{32{x[31]}}, x};
            nonlinear_return <= ELEMENT_SILU_DONE;
            state <= NONLINEAR_SEND;
          end else begin
            math_op <= MATH_ADD;
            math_a <= {{96{x[31]}}, x};
            math_b <= {{96{read_data[31]}}, read_data};
            math_return <= ELEMENT_WRITE;
            state <= MATH_SEND;
          end
        end
        ELEMENT_SILU_DONE: begin
          math_op <= MATH_MUL;
          math_a <= {{96{nonlinear_value[31]}}, nonlinear_value};
          math_b <= {{96{y[31]}}, y};
          math_return <= ELEMENT_PRODUCT_DONE;
          state <= MATH_SEND;
        end
        ELEMENT_PRODUCT_DONE: begin
          math_op <= MATH_ROUND_SHIFT;
          math_a <= {{64{math_value[63]}}, math_value[63:0]};
          math_shift <= 16;
          math_return <= ELEMENT_WRITE;
          state <= MATH_SEND;
        end
        ELEMENT_WRITE: begin
          memory_write <= 1;
          memory_kind <= 8;
          memory_row <= element_out_slot;
          memory_col <= index;
          memory_wdata <= sat32($signed(math_value));
          memory_return <= ELEMENT_NEXT;
          state <= MEMORY_SEND;
        end
        ELEMENT_NEXT: begin
          if (index + 1 < (operation == 6 ? INTERMEDIATE_SIZE : HIDDEN_SIZE)) begin
            index <= index + 32'd1;
            state <= ELEMENT_READ_A;
          end else state <= COMPLETE;
        end
        ATTN_CACHE_READ: begin
          memory_write <= 0;
          memory_kind <= 8;
          memory_layer <= 0;
          memory_row <= value_cache ? 32'd4 : 32'd3;
          memory_col <= index;
          memory_return <= ATTN_CACHE_DONE;
          state <= MEMORY_SEND;
        end
        ATTN_CACHE_DONE: begin
          memory_write <= 1;
          memory_kind <= value_cache ? 4'd10 : 4'd9;
          memory_layer <= layer;
          memory_row <= position;
          memory_wdata <= read_data;
          memory_return <= ATTN_CACHE_NEXT;
          state <= MEMORY_SEND;
        end
        ATTN_CACHE_NEXT: begin
          if (index + 1 < KV_WIDTH) begin
            index <= index + 32'd1;
            state <= ATTN_CACHE_READ;
          end else if (!value_cache) begin
            value_cache <= 1;
            index <= 0;
            state <= ATTN_CACHE_READ;
          end else state <= ATTN_ROOT;
        end
        ATTN_ROOT: begin
          math_op <= MATH_ISQRT;
          math_a <= 128'(HEAD_DIM) << 32;
          math_return <= ATTN_ROOT_DONE;
          state <= MATH_SEND;
        end
        ATTN_ROOT_DONE: begin
          sqrt_dimension <= math_value[63:0];
          state <= ATTN_Q;
        end
        ATTN_Q: begin
          memory_write <= 0;
          memory_kind <= 8;
          memory_layer <= 0;
          memory_row <= 2;
          memory_col <= head_base + dimension;
          memory_return <= ATTN_Q_DONE;
          state <= MEMORY_SEND;
        end
        ATTN_Q_DONE: begin
          x <= read_data;
          memory_kind <= 9;
          memory_layer <= layer;
          memory_row <= time_index;
          memory_col <= kv_base + dimension;
          memory_return <= ATTN_K_DONE;
          state <= MEMORY_SEND;
        end
        ATTN_K_DONE: begin
          math_op <= MATH_MUL;
          math_a <= {{96{x[31]}}, x};
          math_b <= {{96{read_data[31]}}, read_data};
          math_return <= ATTN_DOT_SUM;
          state <= MATH_SEND;
        end
        ATTN_DOT_SUM: begin
          math_op <= MATH_ADD;
          math_a <= {{32{dot[95]}}, dot};
          math_b <= {{64{math_value[63]}}, math_value[63:0]};
          math_return <= ATTN_DOT_DONE;
          state <= MATH_SEND;
        end
        ATTN_DOT_DONE: begin
          dot <= math_value[95:0];
          if (dimension + 1 < HEAD_DIM) begin
            dimension <= dimension + 32'd1;
            state <= ATTN_Q;
          end else state <= ATTN_SCORE;
        end
        ATTN_SCORE: begin
          math_op <= MATH_ROUND_DIV;
          math_a <= {{32{dot[95]}}, dot};
          math_b <= {64'b0, sqrt_dimension};
          math_return <= ATTN_SCORE_DONE;
          state <= MATH_SEND;
        end
        ATTN_SCORE_DONE: begin
          current_score <= math_value[95:0];
          state <= ATTN_SCORE_USE;
        end
        ATTN_SCORE_USE: begin
          if (!context_pass) begin
            if (current_score > max_score) max_score <= current_score;
            if (time_index < position) time_index <= time_index + 32'd1;
            else begin
              time_index <= 0;
              context_pass <= 1;
            end
            dimension <= 0;
            dot <= 0;
            state <= ATTN_Q;
          end else state <= ATTN_DIFF;
        end
        ATTN_DIFF: begin
          math_op <= MATH_SUB;
          math_a <= {{32{current_score[95]}}, current_score};
          math_b <= {{32{max_score[95]}}, max_score};
          math_return <= ATTN_DIFF_DONE;
          state <= MATH_SEND;
        end
        ATTN_DIFF_DONE: begin
          nonlinear_silu <= 0;
          if (difference < -97'sd1048576) nonlinear_argument <= -64'sd1048577;
          else if (difference > 0) nonlinear_argument <= 0;
          else nonlinear_argument <= difference[63:0];
          nonlinear_return <= ATTN_EXP_DONE;
          state <= NONLINEAR_SEND;
        end
        ATTN_EXP_DONE: begin
          exponential <= nonlinear_value;
          math_op <= MATH_ADD;
          math_a <= {64'b0, denominator};
          math_b <= {96'b0, nonlinear_value};
          math_return <= ATTN_DENOM_DONE;
          state <= MATH_SEND;
        end
        ATTN_DENOM_DONE: begin
          denominator <= math_value[63:0];
          memory_write <= 0;
          memory_kind <= 10;
          memory_layer <= layer;
          memory_row <= time_index;
          memory_col <= kv_base + component;
          memory_return <= ATTN_V_DONE;
          state <= MEMORY_SEND;
        end
        ATTN_V_DONE: begin
          math_op <= MATH_MUL;
          math_a <= {{96{read_data[31]}}, read_data};
          math_b <= {96'b0, exponential};
          math_return <= ATTN_WEIGHT_SUM;
          state <= MATH_SEND;
        end
        ATTN_WEIGHT_SUM: begin
          math_op <= MATH_ADD;
          math_a <= {{32{weighted[95]}}, weighted};
          math_b <= {{63{math_value[64]}}, math_value[64:0]};
          math_return <= ATTN_WEIGHT_DONE;
          state <= MATH_SEND;
        end
        ATTN_WEIGHT_DONE: begin
          weighted <= math_value[95:0];
          if (time_index < position) begin
            time_index <= time_index + 32'd1;
            dimension <= 0;
            dot <= 0;
            state <= ATTN_Q;
          end else begin
            math_op <= MATH_ROUND_DIV;
            math_a <= {{32{math_value[95]}}, math_value[95:0]};
            math_b <= {64'b0, denominator};
            math_return <= ATTN_DIVIDE_DONE;
            state <= MATH_SEND;
          end
        end
        ATTN_DIVIDE_DONE: begin
          memory_write <= 1;
          memory_kind <= 8;
          memory_layer <= 0;
          memory_row <= 5;
          memory_col <= head_base + component;
          memory_wdata <= sat32($signed(math_value));
          memory_return <= ATTN_WRITE_NEXT;
          state <= MEMORY_SEND;
        end
        ATTN_WRITE_NEXT: begin
          time_index <= 0;
          dimension <= 0;
          dot <= 0;
          weighted <= 0;
          denominator <= 0;
          if (component + 1 < HEAD_DIM) begin
            component <= component + 32'd1;
            state <= ATTN_Q;
          end else if (head + 1 < NUM_Q_HEADS) begin
            head <= head + 32'd1;
            head_base <= head_base + 32'(HEAD_DIM);
            if (head_in_group == HEAD_RATIO-1) begin
              head_in_group <= 0;
              kv_base <= kv_base + 32'(HEAD_DIM);
            end else head_in_group <= head_in_group + 32'd1;
            component <= 0;
            context_pass <= 0;
            max_score <= {1'b1, 95'b0};
            state <= ATTN_Q;
          end else state <= COMPLETE;
        end
        INVALID: state <= COMPLETE;
        COMPLETE: state <= IDLE;
        default: begin
          failed <= 1;
          state <= COMPLETE;
        end
      endcase
      if (rst_n && abort_error && state != IDLE && state != COMPLETE) begin
        failed <= 1;
        if (state != MEMORY_WAIT || memory_complete) state <= COMPLETE;
      end
    end
  end else begin : g_illegal
    initial $fatal(1, "ANVIL_Q1_HT PARAMETER ERROR: kernel dimensions");
    assign cmd_ready = 0;
    assign done = 0;
    assign error = 0;
    assign mem_req_valid = 0;
    assign mem_req_write = 0;
    assign mem_req_kind = 0;
    assign mem_req_layer = 0;
    assign mem_req_proj = 0;
    assign mem_req_row = 0;
    assign mem_req_col = 0;
    assign mem_req_wdata = 0;
    assign mem_rsp_ready = 0;
  end endgenerate
endmodule
