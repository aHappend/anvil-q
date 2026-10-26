module anvil_q1_ht_logical_memory #(
  parameter NUM_LAYERS = 24, HIDDEN_SIZE = 896, INTERMEDIATE_SIZE = 4864,
  parameter NUM_KV_HEADS = 2, HEAD_DIM = 64, MAX_SEQ_LEN = 32768
) (
  input wire clk, rst_n,
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

  output wire external_valid,
  input wire external_ready,
  output wire external_write,
  output wire [3:0] external_kind,
  output wire [31:0] external_layer,
  output wire [2:0] external_proj,
  output wire [31:0] external_row, external_col, external_wdata,
  input wire external_rsp_valid,
  output wire external_rsp_ready,
  input wire [31:0] external_rsp_data,
  input wire external_rsp_error,

  output wire kv_valid,
  input wire kv_ready,
  output wire kv_write, kv_value,
  output wire [31:0] kv_layer, kv_head, kv_pos, kv_dim,
  output wire signed [31:0] kv_wdata,
  input wire kv_rsp_valid,
  output wire kv_rsp_ready,
  input wire signed [31:0] kv_rsp_data,
  input wire kv_rsp_error
);
  localparam S = HIDDEN_SIZE > INTERMEDIATE_SIZE ? HIDDEN_SIZE : INTERMEDIATE_SIZE;
  localparam SAFE_S = S > 0 ? S : 1;
  localparam WORDS = 15*SAFE_S;
  localparam ADDR_BITS = WORDS > 1 ? $clog2(WORDS) : 1;
  localparam IDLE = 4'd0, ADDRESS = 4'd1, ACCESS = 4'd2, READ_RESULT = 4'd3,
    EXTERNAL = 4'd4, EXTERNAL_WAIT = 4'd5, KV = 4'd6, KV_WAIT = 4'd7, RESULT = 4'd8;
  (* ramstyle = "M20K", ram_style = "block" *) reg [31:0] scratch [0:WORDS-1];
  reg [3:0] state, kind;
  reg wr, failed;
  reg [2:0] projection;
  reg [31:0] layer, row, column, write_data, result_data, scratch_data;
  reg [ADDR_BITS-1:0] scratch_address;
  wire external_response = external_rsp_valid && external_rsp_ready;
  wire kv_response = kv_rsp_valid && kv_rsp_ready;
  assign req_ready = rst_n && state == IDLE;
  assign rsp_valid = rst_n && state == RESULT;
  assign rsp_error = rsp_valid && failed;
  assign rsp_data = rsp_valid && !failed ? result_data : 32'b0;
  assign external_valid = rst_n && state == EXTERNAL;
  assign external_write = external_valid && wr;
  assign external_kind = external_valid ? kind : 4'b0;
  assign external_layer = external_valid ? layer : 32'b0;
  assign external_proj = external_valid ? projection : 3'b0;
  assign external_row = external_valid ? row : 32'b0;
  assign external_col = external_valid ? column : 32'b0;
  assign external_wdata = external_write ? write_data : 32'b0;
  assign external_rsp_ready = rst_n && (state == EXTERNAL_WAIT ||
                                      (state == EXTERNAL && external_ready));
  assign kv_valid = rst_n && state == KV;
  assign kv_write = kv_valid && wr;
  assign kv_value = kv_valid && kind == 10;
  assign kv_layer = kv_valid ? layer : 32'b0;
  assign kv_pos = kv_valid ? row : 32'b0;
  assign kv_head = kv_valid && column >= HEAD_DIM ? 32'd1 : 32'b0;
  assign kv_dim = !kv_valid ? 32'b0 : column >= HEAD_DIM ? column - HEAD_DIM : column;
  assign kv_wdata = kv_write ? $signed(write_data) : 32'sd0;
  assign kv_rsp_ready = rst_n && (state == KV_WAIT || (state == KV && kv_ready));

  always @(posedge clk) begin
    if (rst_n && state == ACCESS) begin
      if (wr) scratch[scratch_address] <= write_data;
      else scratch_data <= scratch[scratch_address];
    end
  end
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state <= IDLE;
      kind <= 0;
      wr <= 0;
      failed <= 0;
      projection <= 0;
      layer <= 0;
      row <= 0;
      column <= 0;
      write_data <= 0;
      result_data <= 0;
      scratch_address <= 0;
    end else case (state)
      IDLE: if (req_valid) begin
        kind <= req_kind;
        wr <= req_write;
        projection <= req_proj;
        layer <= req_layer;
        row <= req_row;
        column <= req_col;
        write_data <= req_wdata;
        result_data <= 0;
        failed <= 0;
        if (req_kind == 8) begin
          if (req_layer != 0 || req_proj != 0 || req_row >= 15 || req_col >= S) begin
            failed <= 1;
            state <= RESULT;
          end else state <= ADDRESS;
        end else if (req_kind == 9 || req_kind == 10) begin
          if (req_layer >= NUM_LAYERS || req_proj != 0 || req_row >= MAX_SEQ_LEN ||
              req_col >= NUM_KV_HEADS*HEAD_DIM) begin
            failed <= 1;
            state <= RESULT;
          end else state <= KV;
        end else state <= EXTERNAL;
      end
      ADDRESS: begin
        scratch_address <= ADDR_BITS'(row*SAFE_S + column);
        state <= ACCESS;
      end
      ACCESS: begin
        if (wr) state <= RESULT;
        else state <= READ_RESULT;
      end
      READ_RESULT: begin result_data <= scratch_data; state <= RESULT; end
      EXTERNAL, EXTERNAL_WAIT: begin
        if (external_valid && external_ready) state <= EXTERNAL_WAIT;
        if (external_response) begin
          result_data <= external_rsp_data;
          failed <= external_rsp_error;
          state <= RESULT;
        end
      end
      KV, KV_WAIT: begin
        if (kv_valid && kv_ready) state <= KV_WAIT;
        if (kv_response) begin
          result_data <= kv_rsp_data;
          failed <= kv_rsp_error;
          state <= RESULT;
        end
      end
      RESULT: if (rsp_ready) state <= IDLE;
      default: begin failed <= 1; state <= RESULT; end
    endcase
  end
endmodule
