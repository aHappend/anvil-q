module anvil_q4_parent_legacy_gemv (
  input wire clk, rst_n, flush, cmd_valid,
  output wire cmd_ready,
  input wire [31:0] cmd_layer, hidden, intermediate, kv_heads, head_dim, group_size,
  input wire [2:0] cmd_proj,
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
  localparam [4:0] IDLE=0, ACT=1, ACT_WAIT=2, WEIGHT=3, WEIGHT_WAIT=4,
    ZERO=5, ZERO_WAIT=6, SCALE=7, SCALE_WAIT=8, DOT=9, DOT_WAIT=10,
    ADD=11, ADD_WAIT=12, BIAS=13, BIAS_WAIT=14, BIAS_ADD=15,
    BIAS_ADD_WAIT=16, ROUND=17, STORE=18, STORE_WAIT=19, COMPLETE=20;
  reg [4:0] state;
  reg failed;
  reg [2:0] projection;
  reg [31:0] layer, inputs, outputs, input_index, output_index, group_index, group_lane;
  reg [31:0] source_slot, target_slot, activation, result_register;
  reg [3:0] q, z;
  reg [15:0] scale;
  reg signed [31:0] bias;
  reg signed [127:0] sum, term;
  wire port_idle, complete, fault;
  wire [31:0] rdata;
  wire issue=port_idle && (state==ACT || state==WEIGHT || state==ZERO ||
    state==SCALE || state==BIAS || state==STORE);
  wire table_read=state==WEIGHT || state==ZERO || state==SCALE || state==BIAS;
  wire [31:0] shifted_lane=rdata >> anvil_q3_parent_pkg::awq_lane_shift(output_index[2:0]);
  wire [31:0] rounded_sum=anvil_q3_parent_pkg::round_q32_to_q16(sum);
  wire [31:0] converted_bias=anvil_q3_parent_pkg::f16_q16(rdata[15:0]);
  anvil_q3_parent_mem_port memory_port (
    .clk(clk),.rst_n(rst_n),.flush(flush),.issue(issue),
    .idle(port_idle),.complete(complete),.fault(fault),
    .write(state==STORE),.kind(state==WEIGHT ? 4'd1 : state==ZERO ? 4'd2 :
      state==SCALE ? 4'd3 : state==BIAS ? 4'd4 : 4'd8),
    .layer(table_read ? layer : 32'd0),.proj(table_read ? projection : 3'd0),
    .row(state==WEIGHT ? input_index : state==ZERO || state==SCALE ? group_index :
      state==BIAS ? 32'd0 : state==STORE ? target_slot : source_slot),
    .col(state==WEIGHT || state==ZERO ? output_index>>3 :
      state==ACT ? input_index : output_index),
    .wdata(state==STORE ? result_register : 32'd0),.rdata(rdata),
    .mem_req_valid(mem_req_valid),.mem_req_ready(mem_req_ready),.mem_req_write(mem_req_write),
    .mem_req_kind(mem_req_kind),.mem_req_layer(mem_req_layer),.mem_req_proj(mem_req_proj),
    .mem_req_row(mem_req_row),.mem_req_col(mem_req_col),.mem_req_wdata(mem_req_wdata),
    .mem_rsp_valid(mem_rsp_valid),.mem_rsp_ready(mem_rsp_ready),
    .mem_rsp_rdata(mem_rsp_rdata),.mem_rsp_error(mem_rsp_error)
  );
  wire dot_ready, dot_valid, dot_error;
  wire signed [71:0] dot_result;
  anvil_q3_parent_awq_dot8 dot8 (
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .in_valid(state==DOT),.in_ready(dot_ready),
    .q_nibbles({28'd0,q}),.z_nibbles({28'd0,z}),.scale_f16({112'd0,scale}),
    .activation_q16({224'd0,activation}),.lane_mask(8'd1),
    .out_valid(dot_valid),.out_ready(state==DOT_WAIT),.out_error(dot_error),.out_dot(dot_result)
  );
  wire add_ready, add_valid, add_error;
  wire signed [127:0] added;
  anvil_q3_parent_add128 accumulator (
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .in_valid(state==ADD || state==BIAS_ADD),.in_ready(add_ready),
    .in_a(sum),.in_b(state==BIAS_ADD ? $signed({{80{bias[31]}},bias,16'd0}) : term),
    .out_valid(add_valid),.out_ready(state==ADD_WAIT || state==BIAS_ADD_WAIT),
    .out_error(add_error),.out_sum(added)
  );
  assign cmd_ready=rst_n && !flush && state==IDLE;
  assign done=rst_n && !flush && state==COMPLETE;
  assign error=done && failed;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; failed<=0; projection<=0; layer<=0; inputs<=0; outputs<=0;
      input_index<=0; output_index<=0; group_index<=0; group_lane<=0;
      source_slot<=0; target_slot<=0; activation<=0; result_register<=0;
      q<=0; z<=0; scale<=0; bias<=0; sum<=0; term<=0;
    end else if (flush) begin state<=IDLE; failed<=0; end
    else if (fault || (dot_valid && dot_error) || (add_valid && add_error)) begin
      failed<=1; state<=COMPLETE;
    end else case (state)
      IDLE: if (cmd_valid) begin
        failed<=0; layer<=cmd_layer; projection<=cmd_proj;
        input_index<=0; output_index<=0; group_index<=0; group_lane<=0; sum<=0;
        inputs<=cmd_proj==6 ? intermediate : hidden;
        outputs<=cmd_proj==1 || cmd_proj==2 ? kv_heads*head_dim :
          cmd_proj==4 || cmd_proj==5 ? intermediate : hidden;
        case (cmd_proj)
          0: begin source_slot<=1; target_slot<=2; end
          1: begin source_slot<=1; target_slot<=3; end
          2: begin source_slot<=1; target_slot<=4; end
          3: begin source_slot<=5; target_slot<=6; end
          4: begin source_slot<=8; target_slot<=9; end
          5: begin source_slot<=8; target_slot<=10; end
          default: begin source_slot<=11; target_slot<=12; end
        endcase
        if (cmd_proj>6 || group_size==0) begin failed<=1; state<=COMPLETE; end
        else state<=ACT;
      end
      ACT: if (issue) state<=ACT_WAIT;
      ACT_WAIT: if (complete) begin activation<=rdata; state<=WEIGHT; end
      WEIGHT: if (issue) state<=WEIGHT_WAIT;
      WEIGHT_WAIT: if (complete) begin q<=shifted_lane[3:0]; state<=ZERO; end
      ZERO: if (issue) state<=ZERO_WAIT;
      ZERO_WAIT: if (complete) begin z<=shifted_lane[3:0]; state<=SCALE; end
      SCALE: if (issue) state<=SCALE_WAIT;
      SCALE_WAIT: if (complete) begin
        if (rdata[31:16]!=0 || anvil_q3_parent_pkg::f16_scale_invalid(rdata[15:0])) begin
          failed<=1; state<=COMPLETE;
        end else begin scale<=rdata[15:0]; state<=DOT; end
      end
      DOT: if (dot_ready) state<=DOT_WAIT;
      DOT_WAIT: if (dot_valid) begin term<={{56{dot_result[71]}},dot_result}; state<=ADD; end
      ADD: if (add_ready) state<=ADD_WAIT;
      ADD_WAIT: if (add_valid) begin
        sum<=added;
        if (input_index+1<inputs) begin
          input_index<=input_index+1'b1;
          if (group_lane+1<group_size) group_lane<=group_lane+1'b1;
          else begin group_lane<=0; group_index<=group_index+1'b1; end
          state<=ACT;
        end else if (projection<=2) state<=BIAS;
        else state<=ROUND;
      end
      BIAS: if (issue) state<=BIAS_WAIT;
      BIAS_WAIT: if (complete) begin
        if (rdata[31:16]!=0 || anvil_q3_parent_pkg::f16_invalid(rdata[15:0])) begin
          failed<=1; state<=COMPLETE;
        end else begin bias<=converted_bias; state<=BIAS_ADD; end
      end
      BIAS_ADD: if (add_ready) state<=BIAS_ADD_WAIT;
      BIAS_ADD_WAIT: if (add_valid) begin sum<=added; state<=ROUND; end
      ROUND: begin result_register<=rounded_sum; state<=STORE; end
      STORE: if (issue) state<=STORE_WAIT;
      STORE_WAIT: if (complete) begin
        if (output_index+1<outputs) begin
          output_index<=output_index+1'b1; input_index<=0; group_index<=0; group_lane<=0;
          sum<=0; state<=ACT;
        end else state<=COMPLETE;
      end
      COMPLETE: state<=IDLE;
      default: begin failed<=1; state<=COMPLETE; end
    endcase
  end
endmodule
