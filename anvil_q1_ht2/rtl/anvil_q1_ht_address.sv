module anvil_q1_ht_address #(
  parameter NUM_LAYERS = 24, HIDDEN_SIZE = 896, INTERMEDIATE_SIZE = 4864,
  parameter NUM_KV_HEADS = 2, HEAD_DIM = 64, GROUP_SIZE = 128,
  parameter VOCAB_SIZE = 151936, MAX_SEQ_LEN = 32768
) (
  input wire clk, rst_n, storage_bf16,
  input wire req_valid,
  output wire req_ready,
  input wire req_write,
  input wire [3:0] req_kind,
  input wire [31:0] req_layer,
  input wire [2:0] req_proj,
  input wire [31:0] req_row, req_col, req_wdata,
  output wire rsp_valid,
  input wire rsp_ready,
  output wire [31:0] rsp_data,
  output wire rsp_error,
  output wire lookup_valid,
  input wire lookup_ready,
  output wire [31:0] lookup_index,
  input wire lookup_rsp_valid,
  output wire lookup_rsp_ready,
  input wire [32:0] lookup_base,
  input wire [31:0] lookup_length,
  input wire lookup_error,
  output wire ddr_valid,
  input wire ddr_ready,
  output wire ddr_write,
  output wire [32:0] ddr_address,
  output wire [511:0] ddr_wdata,
  output wire [63:0] ddr_byteenable,
  input wire ddr_rsp_valid,
  output wire ddr_rsp_ready,
  input wire [511:0] ddr_rsp_data,
  input wire ddr_rsp_error
);
  localparam SAFE_GROUP = GROUP_SIZE > 0 ? GROUP_SIZE : 1;
  localparam GROUPS_H = HIDDEN_SIZE / SAFE_GROUP, GROUPS_I = INTERMEDIATE_SIZE / SAFE_GROUP;
  localparam KV_WIDTH = NUM_KV_HEADS*HEAD_DIM;
  localparam SCRATCH_WIDTH = HIDDEN_SIZE > INTERMEDIATE_SIZE ? HIDDEN_SIZE : INTERMEDIATE_SIZE;
  localparam IDLE = 4'd0, SHAPE = 4'd1, PANEL = 4'd2, PRODUCTS = 4'd3,
    OFFSET = 4'd4, LOOKUP = 4'd5, LOOKUP_WAIT = 4'd6, BOUNDS = 4'd7,
    ISSUE = 4'd8, RESPONSE = 4'd9, RESULT = 4'd10;
  reg [3:0] state, kind;
  reg [2:0] projection;
  reg failed, wr, bf16, packed_words;
  reg [31:0] layer, row, column, write_data, descriptor_index;
  reg [17:0] output_count, panel_base, logical_row;
  reg [12:0] row_count;
  reg [6:0] panel_width;
  reg [5:0] inner;
  reg [1:0] element_shift;
  reg [31:0] panel_product, row_product;
  reg [33:0] byte_offset, relative_end, physical;
  reg [32:0] base;
  reg [31:0] length, result_data;
  reg [8:0] bit_offset;
  wire [17:0] input_outputs = projection == 1 || projection == 2 ? KV_WIDTH :
                             projection == 4 || projection == 5 ? INTERMEDIATE_SIZE : HIDDEN_SIZE;
  wire [12:0] input_rows = projection == 6 ? INTERMEDIATE_SIZE : HIDDEN_SIZE;
  wire [33:0] complete_address = {1'b0, base} + byte_offset;
  wire [33:0] complete_end = {1'b0, base} + relative_end;
  wire memory_response = ddr_rsp_valid && ddr_rsp_ready;
  assign req_ready = rst_n && state == IDLE;
  assign rsp_valid = rst_n && state == RESULT;
  assign rsp_data = rsp_valid && !failed ? result_data : 32'b0;
  assign rsp_error = rsp_valid && failed;
  assign lookup_valid = rst_n && state == LOOKUP;
  assign lookup_index = lookup_valid ? descriptor_index : 32'b0;
  assign lookup_rsp_ready = rst_n && (state == LOOKUP_WAIT ||
                                    (state == LOOKUP && lookup_ready));
  assign ddr_valid = rst_n && state == ISSUE;
  assign ddr_write = ddr_valid && wr;
  assign ddr_address = ddr_valid ? {physical[32:6], 6'b0} : 33'b0;
  assign ddr_wdata = ddr_write ? ({{480{1'b0}}, write_data} << bit_offset) : 512'b0;
  assign ddr_byteenable = !ddr_valid ? 64'b0 : !wr ? 64'hffffffffffffffff :
                         (64'hf << physical[5:0]);
  assign ddr_rsp_ready = rst_n && (state == RESPONSE || (state == ISSUE && ddr_ready));

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state <= IDLE;
      kind <= 0;
      projection <= 0;
      failed <= 0;
      wr <= 0;
      bf16 <= 0;
      packed_words <= 0;
      layer <= 0;
      row <= 0;
      column <= 0;
      write_data <= 0;
      descriptor_index <= 0;
      output_count <= 0;
      panel_base <= 0;
      logical_row <= 0;
      row_count <= 0;
      panel_width <= 0;
      inner <= 0;
      element_shift <= 0;
      panel_product <= 0;
      row_product <= 0;
      byte_offset <= 0;
      relative_end <= 0;
      physical <= 0;
      base <= 0;
      length <= 0;
      result_data <= 0;
      bit_offset <= 0;
    end else case (state)
      IDLE: if (req_valid) begin
        failed <= 0;
        wr <= req_write;
        kind <= req_kind;
        projection <= req_proj;
        layer <= req_layer;
        row <= req_row;
        column <= req_col;
        write_data <= req_wdata;
        bf16 <= storage_bf16;
        packed_words <= 0;
        result_data <= 0;
        descriptor_index <= (req_layer << 6) + (req_layer << 5) +
                            {25'b0, req_kind, 3'b0} + {29'b0, req_proj};
        if (req_layer >= NUM_LAYERS || req_kind > 11 ||
            (req_write && req_kind != 8 && req_kind != 9 && req_kind != 10) ||
            ((req_kind == 0 || req_kind == 7 || req_kind == 8 || req_kind == 11) &&
              (req_layer != 0 || req_proj != 0)) ||
            ((req_kind == 1 || req_kind == 2 || req_kind == 3) && req_proj > 6) ||
            (req_kind == 4 && req_proj > 2) ||
            ((req_kind == 5 || req_kind == 6 || req_kind == 9 || req_kind == 10) &&
              req_proj != 0)) begin
          failed <= 1;
          state <= RESULT;
        end else state <= SHAPE;
      end
      SHAPE: begin
        state <= PANEL;
        logical_row <= row[17:0];
        panel_base <= 0;
        inner <= column[5:0];
        case (kind)
          0: begin
            output_count <= VOCAB_SIZE;
            row_count <= HIDDEN_SIZE;
            logical_row <= column[17:0];
            panel_base <= {row[17:6], 6'b0};
            inner <= row[5:0];
            element_shift <= 1;
            if (row >= VOCAB_SIZE || column >= HIDDEN_SIZE) begin failed <= 1; state <= RESULT; end
          end
          1, 2, 3: begin
            output_count <= input_outputs;
            row_count <= kind == 1 ? input_rows :
                         projection == 6 ? GROUPS_I : GROUPS_H;
            if ((kind == 1 && !bf16) || kind == 2) begin
              packed_words <= 1;
              element_shift <= 2;
              panel_base <= {column[14:3], 6'b0};
              inner <= {3'b0, column[2:0]};
              if (column >= ({14'b0, input_outputs} >> 3)) begin failed <= 1; state <= RESULT; end
            end else begin
              element_shift <= 1;
              panel_base <= {column[17:6], 6'b0};
              if (column >= {14'b0, input_outputs}) begin failed <= 1; state <= RESULT; end
            end
            if ((kind == 2 || kind == 3) && bf16) begin failed <= 1; state <= RESULT; end
            if (row >= (kind == 1 ? {19'b0, input_rows} :
                        projection == 6 ? GROUPS_I : GROUPS_H))
              begin failed <= 1; state <= RESULT; end
          end
          4, 5, 6, 7: begin
            output_count <= kind == 4 ? input_outputs : HIDDEN_SIZE;
            row_count <= 1;
            logical_row <= 0;
            panel_base <= {column[17:6], 6'b0};
            element_shift <= 1;
            if (row != 0 || column >= (kind == 4 ? {14'b0, input_outputs} : HIDDEN_SIZE))
              begin failed <= 1; state <= RESULT; end
          end
          8: begin
            output_count <= SCRATCH_WIDTH;
            row_count <= 15;
            element_shift <= 2;
            if (row >= 15 || column >= SCRATCH_WIDTH) begin failed <= 1; state <= RESULT; end
          end
          9, 10: begin
            output_count <= KV_WIDTH;
            row_count <= 0;
            element_shift <= 2;
            if (row >= MAX_SEQ_LEN || column >= KV_WIDTH) begin failed <= 1; state <= RESULT; end
          end
          11: begin
            output_count <= HEAD_DIM;
            row_count <= 0;
            element_shift <= 2;
            if (row >= MAX_SEQ_LEN || column >= HEAD_DIM) begin failed <= 1; state <= RESULT; end
          end
          default: begin failed <= 1; state <= RESULT; end
        endcase
      end
      PANEL: begin
        panel_width <= output_count - panel_base < 64 ?
                       7'(output_count - panel_base) : 7'd64;
        if (kind >= 8) inner <= 0;
        state <= PRODUCTS;
      end
      PRODUCTS: begin
        if (kind >= 8) begin
          panel_product <= 0;
          row_product <= logical_row * output_count;
        end else begin
          panel_product <= packed_words ? ((panel_base >> 3) * row_count) : panel_base * row_count;
          row_product <= packed_words ? logical_row * (panel_width >> 3) : logical_row * panel_width;
        end
        state <= OFFSET;
      end
      OFFSET: begin
        if (kind >= 8) begin
          byte_offset <= ({2'b0, row_product} + {2'b0, column}) << 2;
          relative_end <= (({2'b0, row_product} + {2'b0, column}) << 2) + 34'd4;
        end else begin
          byte_offset <= ({2'b0, panel_product} + {2'b0, row_product} + {28'b0, inner}) << element_shift;
          relative_end <= (({2'b0, panel_product} + {2'b0, row_product} +
                            {28'b0, inner}) << element_shift) + (34'd1 << element_shift);
        end
        state <= LOOKUP;
      end
      LOOKUP, LOOKUP_WAIT: begin
        if (lookup_valid && lookup_ready) state <= LOOKUP_WAIT;
        if (lookup_rsp_valid && lookup_rsp_ready) begin
          base <= lookup_base;
          length <= lookup_length;
          if (lookup_error) begin failed <= 1; state <= RESULT; end
          else state <= BOUNDS;
        end
      end
      BOUNDS: begin
        physical <= complete_address;
        bit_offset <= {complete_address[5:0], 3'b0};
        if (relative_end > {2'b0, length} || complete_end > 34'h200000000 ||
            complete_address[33]) begin failed <= 1; state <= RESULT; end
        else state <= ISSUE;
      end
      ISSUE, RESPONSE: begin
        if (ddr_valid && ddr_ready) state <= RESPONSE;
        if (memory_response) begin
          failed <= ddr_rsp_error;
          if (!wr) begin
            if (element_shift == 1) result_data <= {16'b0, 16'(ddr_rsp_data >> bit_offset)};
            else result_data <= 32'(ddr_rsp_data >> bit_offset);
          end
          state <= RESULT;
        end
      end
      RESULT: if (rsp_ready) state <= IDLE;
      default: begin failed <= 1; state <= RESULT; end
    endcase
  end
endmodule
