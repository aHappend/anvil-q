module anvil_q1_ht3_tree_mask #(
  parameter MAX_SEQ_LEN = 32768
) (
  input wire clk, rst_n, req_valid,
  output wire req_ready,
  input wire req_prefix_valid,
  input wire [31:0] req_prefix_position,
  input wire [2:0] req_count,
  input wire [11:0] req_parents,
  output wire rsp_valid,
  input wire rsp_ready,
  output wire [127:0] rsp_positions,
  output wire [15:0] rsp_ancestors,
  output wire rsp_error
);
  localparam IDLE = 2'd0, CLASSIFY = 2'd1, RESPONSE = 2'd2;
  wire run_n;
  reg [1:0] state;
  reg prefix_valid, failed;
  reg [31:0] prefix_position;
  reg [2:0] count;
  reg [11:0] parents;
  reg [127:0] positions, next_positions;
  reg [15:0] ancestors, next_ancestors;
  reg [2:0] depths [0:3];
  reg next_error;
  reg [32:0] extended_position;
  reg [2:0] parent;
  integer node;
  initial if (MAX_SEQ_LEN < 1 || MAX_SEQ_LEN > 32768)
    $fatal(1, "PARAMETER ERROR: HT3 tree sequence length");
  anvil_q1_ht3_reset_sync u_reset(clk, rst_n, run_n);
  always @* begin
    next_positions = 0;
    next_ancestors = 0;
    next_error = !prefix_valid || prefix_position >= MAX_SEQ_LEN || count == 0 || count > 4;
    extended_position = 0;
    parent = 0;
    for (node = 0; node < 4; node = node + 1) depths[node] = 0;
    for (node = 0; node < 4; node = node + 1) begin
      if (node < count) begin
        parent = parents[3*node+:3];
        if (parent == 4) depths[node] = 1;
        else if (parent < node) begin
          depths[node] = depths[parent] + 1'b1;
          next_ancestors[4*node+:4] = next_ancestors[4*parent+:4];
        end else next_error = 1;
        next_ancestors[4*node+node] = 1;
        extended_position = {1'b0,prefix_position} + {30'b0,depths[node]};
        if (extended_position >= MAX_SEQ_LEN) next_error = 1;
        next_positions[32*node+:32] = extended_position[31:0];
      end
    end
  end
  assign req_ready = run_n && state == IDLE;
  assign rsp_valid = run_n && state == RESPONSE;
  assign rsp_positions = rsp_valid && !failed ? positions : 128'b0;
  assign rsp_ancestors = rsp_valid && !failed ? ancestors : 16'b0;
  assign rsp_error = rsp_valid && failed;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state <= IDLE;
      prefix_valid <= 0;
      prefix_position <= 0;
      failed <= 0;
      count <= 0;
      parents <= 0;
      positions <= 0;
      ancestors <= 0;
    end else if (run_n) case (state)
      IDLE: if (req_valid && req_ready) begin
        prefix_valid <= req_prefix_valid;
        prefix_position <= req_prefix_position;
        count <= req_count;
        parents <= req_parents;
        state <= CLASSIFY;
      end
      CLASSIFY: begin
        positions <= next_positions;
        ancestors <= next_ancestors;
        failed <= next_error;
        state <= RESPONSE;
      end
      RESPONSE: if (rsp_ready) state <= IDLE;
      default: begin failed <= 1; positions <= 0; ancestors <= 0; state <= RESPONSE; end
    endcase
  end
endmodule
