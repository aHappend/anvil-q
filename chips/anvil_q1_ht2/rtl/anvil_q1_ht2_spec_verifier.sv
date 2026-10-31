module anvil_q1_ht2_spec_verifier (
  input wire clk, rst_n, in_valid,
  output wire in_ready,
  input wire [2:0] in_count,
  input wire [127:0] in_draft_tokens, in_target_tokens,
  input wire [11:0] in_parents,
  input wire [31:0] in_prefix_target,
  output wire out_valid,
  input wire out_ready,
  output wire [2:0] out_count,
  output wire [127:0] out_tokens,
  output wire [3:0] out_commit_mask,
  output wire out_error
);
  localparam IDLE = 2'd0, WALK = 2'd1, RESPONSE = 2'd2;
  wire run_n;
  reg [1:0] state;
  reg [2:0] count;
  reg [127:0] drafts, targets;
  reg [11:0] parents;
  reg [31:0] prefix_target;
  reg [2:0] result_count, walk_count;
  reg [127:0] result_tokens, walk_tokens;
  reg [3:0] result_mask, walk_mask;
  reg result_error, walk_error;
  reg [2:0] current_parent, selected;
  reg [31:0] current_target;
  reg stopped, found;
  integer node, step, child;

  anvil_q1_ht2_reset_sync u_reset(clk, rst_n, run_n);
  always @* begin
    walk_count = 0;
    walk_tokens = 0;
    walk_mask = 0;
    walk_error = count == 0 || count > 4;
    for (node = 0; node < 4; node = node + 1) begin
      if (node < count && parents[3*node+:3] != 3'd4 &&
          {29'b0, parents[3*node+:3]} >= node) walk_error = 1'b1;
    end
    current_parent = 3'd4;
    current_target = prefix_target;
    stopped = walk_error;
    found = 0;
    selected = 0;
    for (step = 0; step < 4; step = step + 1) begin
      found = 0;
      selected = 0;
      for (child = 0; child < 4; child = child + 1) begin
        if (!found && child < count && parents[3*child+:3] == current_parent &&
            drafts[32*child+:32] == current_target) begin
          found = 1;
          selected = child[2:0];
        end
      end
      if (!stopped) begin
        walk_tokens[32*step+:32] = current_target;
        walk_count = walk_count + 1'b1;
        if (found) begin
          walk_mask[selected[1:0]] = 1'b1;
          current_parent = selected;
          current_target = targets[32*selected+:32];
        end else stopped = 1'b1;
      end
    end
  end

  assign in_ready = run_n && state == IDLE;
  assign out_valid = run_n && state == RESPONSE;
  assign out_count = out_valid ? result_count : 3'b0;
  assign out_tokens = out_valid ? result_tokens : 128'b0;
  assign out_commit_mask = out_valid ? result_mask : 4'b0;
  assign out_error = out_valid && result_error;

  always @(posedge clk or negedge run_n) begin
    if (!run_n) begin
      state <= IDLE;
      count <= 0;
      drafts <= 0;
      targets <= 0;
      parents <= 0;
      prefix_target <= 0;
      result_count <= 0;
      result_tokens <= 0;
      result_mask <= 0;
      result_error <= 0;
    end else case (state)
      IDLE: if (in_valid && in_ready) begin
        count <= in_count;
        drafts <= in_draft_tokens;
        targets <= in_target_tokens;
        parents <= in_parents;
        prefix_target <= in_prefix_target;
        state <= WALK;
      end
      WALK: begin
        result_count <= walk_count;
        result_tokens <= walk_tokens;
        result_mask <= walk_mask;
        result_error <= walk_error;
        state <= RESPONSE;
      end
      RESPONSE: if (out_valid && out_ready) state <= IDLE;
      default: begin
        result_count <= 0;
        result_tokens <= 0;
        result_mask <= 0;
        result_error <= 1;
        state <= RESPONSE;
      end
    endcase
  end
endmodule
