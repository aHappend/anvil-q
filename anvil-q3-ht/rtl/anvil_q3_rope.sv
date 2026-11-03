module anvil_q3_rope #(
  parameter NUM_LAYERS=36, HIDDEN_SIZE=2048, NUM_Q_HEADS=16,
  parameter NUM_KV_HEADS=2, HEAD_DIM=128, MAX_SEQ_LEN=32768
) (
  input wire clk, rst_n, flush, cmd_valid,
  output wire cmd_ready,
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
  localparam HALF=HEAD_DIM>0 ? HEAD_DIM/2 : 1;
  localparam IDLE=0, X_READ=1, X_RESPONSE=2, Y_READ=3, Y_RESPONSE=4;
  localparam COS_READ=5, COS_RESPONSE=6, SIN_READ=7, SIN_RESPONSE=8;
  localparam MULTIPLY=9, MULTIPLY_WAIT=10, ADD=11, ADD_WAIT=12;
  localparam ROUND=13, X_WRITE=14, X_ACK=15, Y_WRITE=16, Y_ACK=17;
  localparam COMPLETE=18, FAULTED=19;
  reg [4:0] state;
  reg failed, key_vector;
  reg [1:0] part;
  reg [31:0] position, head, head_base, pair_index, rotated_x, rotated_y;
  reg signed [31:0] x, y, cosine, sine;
  reg signed [127:0] first_term, second_term, rotated;
  wire unit_flush=flush || failed;
  wire port_idle, complete, fault;
  wire [31:0] rdata;
  wire issue=port_idle && (state==X_READ || state==Y_READ ||
    state==COS_READ || state==SIN_READ || state==X_WRITE || state==Y_WRITE);
  wire coefficient=state==COS_READ || state==SIN_READ;
  wire second_component=state==Y_READ || state==Y_WRITE;
  wire multiply_ready, multiply_done, multiply_error;
  wire signed [63:0] product;
  wire signed [31:0] multiply_a=(part==0 || part==3) ? x : y;
  wire signed [31:0] multiply_b=part==1 ? -sine : part==3 ? sine : cosine;
  wire add_ready, add_valid, add_error;
  wire signed [127:0] added;
  wire malformed_coefficient=$signed(rdata)>32'sd1073741824 ||
    $signed(rdata)< -32'sd1073741824;

  generate if (NUM_LAYERS<=0 || HIDDEN_SIZE<=0 || NUM_Q_HEADS<=0 ||
      NUM_KV_HEADS<=0 || HEAD_DIM<=0 || HEAD_DIM%2!=0 ||
      MAX_SEQ_LEN<=0 || MAX_SEQ_LEN>32768 ||
      128'(HIDDEN_SIZE)!=128'(NUM_Q_HEADS)*128'(HEAD_DIM) ||
      128'(HIDDEN_SIZE)>128'hffffffff ||
      128'(NUM_KV_HEADS)*128'(HEAD_DIM)>128'hffffffff ||
      128'(NUM_LAYERS)>128'hffffffff || 128'(HEAD_DIM)*2>128'hffffffff) begin: invalid_parameters
    initial $fatal(1,"ANVIL_Q3 PARAMETER ERROR: RoPE dimensions");
  end endgenerate
  assign cmd_ready=rst_n && !flush && state==IDLE;
  assign done=rst_n && !flush && state==COMPLETE;
  assign error=done && failed;

  anvil_q3_mem_port memory_port (
    .clk(clk),.rst_n(rst_n),.flush(unit_flush),.issue(issue),
    .idle(port_idle),.complete(complete),.fault(fault),
    .write(state==X_WRITE || state==Y_WRITE),.kind(coefficient ? 4'd11 : 4'd8),
    .layer(32'd0),.proj(3'd0),
    .row(coefficient ? position : key_vector ? 32'd3 : 32'd2),
    .col(coefficient ? ((pair_index<<1)+(state==SIN_READ ? 32'd1 : 32'd0)) :
      head_base+pair_index+(second_component ? 32'(HALF) : 32'd0)),
    .wdata(state==X_WRITE ? rotated_x : state==Y_WRITE ? rotated_y : 32'd0),
    .rdata(rdata),.mem_req_valid(mem_req_valid),.mem_req_ready(mem_req_ready),
    .mem_req_write(mem_req_write),.mem_req_kind(mem_req_kind),
    .mem_req_layer(mem_req_layer),.mem_req_proj(mem_req_proj),
    .mem_req_row(mem_req_row),.mem_req_col(mem_req_col),.mem_req_wdata(mem_req_wdata),
    .mem_rsp_valid(mem_rsp_valid),.mem_rsp_ready(mem_rsp_ready),
    .mem_rsp_rdata(mem_rsp_rdata),.mem_rsp_error(mem_rsp_error)
  );
  anvil_q3_multiplier #(.A_W(32),.B_W(32)) multiplier (
    .clk(clk),.rst_n(rst_n),.flush(unit_flush),.start(state==MULTIPLY),
    .a(multiply_a),.b(multiply_b),.ready(multiply_ready),
    .done(multiply_done),.error(multiply_error),.product(product)
  );
  anvil_q3_add128 rotation_adder (
    .clk(clk),.rst_n(rst_n),.flush(unit_flush),.in_valid(state==ADD),
    .in_ready(add_ready),.in_a(first_term),.in_b(second_term),
    .out_valid(add_valid),.out_ready(1'b1),.out_error(add_error),.out_sum(added)
  );
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; failed<=0; key_vector<=0; part<=0;
      position<=0; head<=0; head_base<=0; pair_index<=0;
      rotated_x<=0; rotated_y<=0; x<=0; y<=0; cosine<=0; sine<=0;
      first_term<=0; second_term<=0; rotated<=0;
    end else if (flush) begin state<=IDLE; failed<=0; end
    else if (!failed && (fault || (multiply_done && multiply_error) ||
        (add_valid && add_error))) begin failed<=1; state<=COMPLETE; end
    else case (state)
      IDLE: if (cmd_valid) begin
        failed<=0; key_vector<=0; head<=0; head_base<=0; pair_index<=0; position<=cmd_pos;
        if (cmd_layer>=NUM_LAYERS || cmd_pos>=MAX_SEQ_LEN) begin
          failed<=1; state<=COMPLETE;
        end else state<=X_READ;
      end
      X_READ: if (issue) state<=X_RESPONSE;
      X_RESPONSE: if (complete) begin x<=rdata; state<=Y_READ; end
      Y_READ: if (issue) state<=Y_RESPONSE;
      Y_RESPONSE: if (complete) begin y<=rdata; state<=COS_READ; end
      COS_READ: if (issue) state<=COS_RESPONSE;
      COS_RESPONSE: if (complete) begin
        if (malformed_coefficient) begin failed<=1; state<=COMPLETE; end
        else begin cosine<=rdata; state<=SIN_READ; end
      end
      SIN_READ: if (issue) state<=SIN_RESPONSE;
      SIN_RESPONSE: if (complete) begin
        if (malformed_coefficient) begin failed<=1; state<=COMPLETE; end
        else begin sine<=rdata; part<=0; state<=MULTIPLY; end
      end
      MULTIPLY: if (multiply_ready) state<=MULTIPLY_WAIT;
      MULTIPLY_WAIT: if (multiply_done) begin
        if (!part[0]) begin
          first_term<={{64{product[63]}},product};
          part<=part+1'b1;
          state<=MULTIPLY;
        end else begin second_term<={{64{product[63]}},product}; state<=ADD; end
      end
      ADD: if (add_ready) state<=ADD_WAIT;
      ADD_WAIT: if (add_valid) begin rotated<=added; state<=ROUND; end
      ROUND: begin
        if (part==1) begin
          rotated_x<=anvil_q3_pkg::round_shift_sat32(rotated,30);
          part<=2; state<=MULTIPLY;
        end else begin
          rotated_y<=anvil_q3_pkg::round_shift_sat32(rotated,30);
          state<=X_WRITE;
        end
      end
      X_WRITE: if (issue) state<=X_ACK;
      X_ACK: if (complete) state<=Y_WRITE;
      Y_WRITE: if (issue) state<=Y_ACK;
      Y_ACK: if (complete) begin
        if (pair_index+1<HALF) begin pair_index<=pair_index+1'b1; state<=X_READ; end
        else if (head+1<(key_vector ? NUM_KV_HEADS : NUM_Q_HEADS)) begin
          pair_index<=0; head<=head+1'b1; head_base<=head_base+HEAD_DIM; state<=X_READ;
        end else if (!key_vector) begin
          key_vector<=1; head<=0; head_base<=0; pair_index<=0; state<=X_READ;
        end else state<=COMPLETE;
      end
      COMPLETE: if (failed) state<=FAULTED; else state<=IDLE;
      FAULTED: state<=FAULTED;
      default: begin failed<=1; state<=COMPLETE; end
    endcase
  end
endmodule
