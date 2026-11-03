module anvil_q3_fp_rope #(
  parameter NUM_LAYERS=36, HIDDEN_SIZE=2048, NUM_Q_HEADS=16,
  parameter NUM_KV_HEADS=2, HEAD_DIM=128, MAX_SEQ_LEN=32768
) (
  input wire clk, rst_n, flush, cmd_valid, cmd_fp16,
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
  localparam X_WRITE=13, X_ACK=14, Y_WRITE=15, Y_ACK=16, COMPLETE=17, FAULTED=18;
  reg [4:0] state;
  reg failed, key_vector, fp16;
  reg [1:0] part;
  reg [31:0] position, head, head_base, pair_index, rotated_x, rotated_y;
  reg [31:0] x, y, cosine, sine, first_term, second_term;
  wire unit_flush=flush || failed;
  wire port_idle, memory_complete, memory_fault;
  wire [31:0] rdata;
  wire [31:0] widened_response=anvil_q3_fp_pkg::widen16(rdata[15:0],fp16);
  wire issue=port_idle && (state==X_READ || state==Y_READ ||
    state==COS_READ || state==SIN_READ || state==X_WRITE || state==Y_WRITE);
  wire coefficient=state==COS_READ || state==SIN_READ;
  wire second_component=state==Y_READ || state==Y_WRITE;
  wire multiply_ready, multiply_valid, add_ready, add_valid;
  wire [31:0] product, added;
  wire [20:0] narrowed_result=anvil_q3_fp_pkg::narrow16(added,fp16);
  wire malformed=memory_complete && (
    ((state==X_RESPONSE || state==Y_RESPONSE) && rdata[31:16]!=0) ||
    ((state==COS_RESPONSE || state==SIN_RESPONSE) &&
      (anvil_q3_fp_pkg::is_nan32(rdata) || rdata[30:0]>31'h3f800000)));
  generate if (NUM_LAYERS<=0 || HIDDEN_SIZE<=0 || NUM_Q_HEADS<=0 ||
      NUM_KV_HEADS<=0 || HEAD_DIM<=0 || HEAD_DIM%2!=0 ||
      MAX_SEQ_LEN<1 || MAX_SEQ_LEN>32768 ||
      128'(HIDDEN_SIZE)!=128'(NUM_Q_HEADS)*128'(HEAD_DIM) ||
      128'(NUM_Q_HEADS)!=8*128'(NUM_KV_HEADS) ||
      128'(HIDDEN_SIZE)>128'hffffffff ||
      128'(NUM_KV_HEADS)*128'(HEAD_DIM)>128'hffffffff ||
      128'(NUM_LAYERS)>128'hffffffff || 128'(HEAD_DIM)*2>128'hffffffff) begin: invalid_parameters
    initial $fatal(1,"ANVIL_Q3_FP PARAMETER ERROR: RoPE dimensions");
  end endgenerate
  assign cmd_ready=rst_n && !flush && state==IDLE;
  assign done=rst_n && !flush && state==COMPLETE;
  assign error=done && failed;
  anvil_q3_mem_port memory_port (
    .clk(clk),.rst_n(rst_n),.flush(unit_flush),.issue(issue),
    .idle(port_idle),.complete(memory_complete),.fault(memory_fault),
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
  anvil_q3_fp_mul multiplier (
    .clk(clk),.rst_n(rst_n),.flush(unit_flush),.in_valid(state==MULTIPLY),
    .in_a((part==0 || part==3) ? x : y),
    .in_b(part==1 || part==3 ? sine : cosine),.in_ready(multiply_ready),
    .out_valid(multiply_valid),.out_ready(1'b1),.out_data(product),.out_flags()
  );
  anvil_q3_fp_add rotation_adder (
    .clk(clk),.rst_n(rst_n),.flush(unit_flush),.in_valid(state==ADD),
    .in_ready(add_ready),.in_a(first_term),
    .in_b(part==1 ? {~second_term[31],second_term[30:0]} : second_term),
    .out_valid(add_valid),.out_ready(1'b1),.out_data(added),.out_flags()
  );
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; failed<=0; key_vector<=0; fp16<=0; part<=0;
      position<=0; head<=0; head_base<=0; pair_index<=0;
      rotated_x<=0; rotated_y<=0; x<=0; y<=0; cosine<=0; sine<=0;
      first_term<=0; second_term<=0;
    end else if (flush) begin state<=IDLE; failed<=0; end
    else if (!failed && (memory_fault || malformed)) begin failed<=1; state<=COMPLETE; end
    else case (state)
      IDLE: if (cmd_valid) begin
        failed<=0; fp16<=cmd_fp16; key_vector<=0;
        head<=0; head_base<=0; pair_index<=0; position<=cmd_pos;
        if (cmd_layer>=NUM_LAYERS || cmd_pos>=MAX_SEQ_LEN) begin
          failed<=1; state<=COMPLETE;
        end else state<=X_READ;
      end
      X_READ: if (issue) state<=X_RESPONSE;
      X_RESPONSE: if (memory_complete) begin x<=widened_response; state<=Y_READ; end
      Y_READ: if (issue) state<=Y_RESPONSE;
      Y_RESPONSE: if (memory_complete) begin y<=widened_response; state<=COS_READ; end
      COS_READ: if (issue) state<=COS_RESPONSE;
      COS_RESPONSE: if (memory_complete) begin cosine<=rdata; state<=SIN_READ; end
      SIN_READ: if (issue) state<=SIN_RESPONSE;
      SIN_RESPONSE: if (memory_complete) begin sine<=rdata; part<=0; state<=MULTIPLY; end
      MULTIPLY: if (multiply_ready) state<=MULTIPLY_WAIT;
      MULTIPLY_WAIT: if (multiply_valid) begin
        if (!part[0]) begin first_term<=product; part<=part+1'b1; state<=MULTIPLY; end
        else begin second_term<=product; state<=ADD; end
      end
      ADD: if (add_ready) state<=ADD_WAIT;
      ADD_WAIT: if (add_valid) begin
        if (part==1) begin
          rotated_x<={16'd0,narrowed_result[15:0]}; part<=2; state<=MULTIPLY;
        end else begin rotated_y<={16'd0,narrowed_result[15:0]}; state<=X_WRITE; end
      end
      X_WRITE: if (issue) state<=X_ACK;
      X_ACK: if (memory_complete) state<=Y_WRITE;
      Y_WRITE: if (issue) state<=Y_ACK;
      Y_ACK: if (memory_complete) begin
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
