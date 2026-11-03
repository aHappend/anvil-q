module anvil_d1_absorption #(
  parameter integer NUM_LAYERS=27, HIDDEN_SIZE=2048, NUM_Q_HEADS=16,
  parameter integer KV_LORA_RANK=512, QK_NOPE_HEAD_DIM=128, V_HEAD_DIM=128,
  localparam integer NL=(NUM_LAYERS>=1 && NUM_LAYERS<=36) ? NUM_LAYERS : 1
) (
  input wire clk, rst_n, flush, cmd_valid,
  output wire cmd_ready,
  input wire [31:0] cmd_epoch, cmd_layer,
  output wire done, error,
  output wire [63:0] raw_read_bytes, absorbed_write_bytes,
  output wire c_req_valid,
  input wire c_req_ready,
  output wire c_req_write,
  output wire [3:0] c_req_kind,
  output wire [31:0] c_req_layer,
  output wire [2:0] c_req_proj,
  output wire [31:0] c_req_row, c_req_col, c_req_wdata,
  input wire c_rsp_valid,
  output wire c_rsp_ready,
  input wire [31:0] c_rsp_rdata,
  input wire c_rsp_error
);
  localparam IDLE=0, CHECK_EPOCH=1, LEFT_READ=2, LEFT_RESPONSE=3;
  localparam RIGHT_READ=4, RIGHT_RESPONSE=5, MULTIPLY=6, MULTIPLY_WAIT=7;
  localparam ACCUMULATE=8, ACCUMULATE_WAIT=9, WRITE=10, WRITE_RESPONSE=11;
  localparam COMPLETE=12, FAULTED=13, REJECT=14;
  reg [3:0] state;
  reg armed, failed, matrix_b;
  reg [NL-1:0] epoch_valid;
  reg [31:0] epochs [0:NL-1];
  reg [31:0] layer, epoch, output_index, input_index, reduction, head_value_base;
  reg [31:0] absorbed_col;
  reg [3:0] head;
  reg [1:0] word_number;
  reg signed [31:0] left_weight, right_weight;
  reg signed [63:0] product;
  reg signed [95:0] coefficient;
  wire port_idle, memory_complete, memory_fault;
  wire [31:0] rdata;
  wire issue=port_idle && (state==LEFT_READ || state==RIGHT_READ || state==WRITE);
  wire left_request=state==LEFT_READ;
  wire [31:0] raw_row=matrix_b ?
    (left_request ? {4'd6,4'd0,output_index[23:0]} : {4'd5,head,reduction[23:0]}) :
    (left_request ? {4'd4,head,reduction[23:0]} : {4'd2,head,reduction[23:0]});
  wire [31:0] raw_col=matrix_b ?
    (left_request ? head_value_base+reduction : input_index) :
    (left_request ? output_index : input_index);
  wire [31:0] write_col=absorbed_col+{30'd0,word_number};
  wire multiply_ready, multiply_valid;
  wire signed [63:0] multiply_result;
  wire acc_ready, acc_valid, acc_error;
  wire signed [127:0] accumulated;
  wire accepting=cmd_valid && cmd_ready;
  wire read_transfer=c_req_valid && c_req_ready && !c_req_write;
  wire write_transfer=c_req_valid && c_req_ready && c_req_write;
  wire [63:0] unused_read_snapshot, unused_write_snapshot;
  wire read_overflow, write_overflow;
  integer l;
  generate if (NUM_LAYERS<1 || NUM_LAYERS>36 || HIDDEN_SIZE<8 || HIDDEN_SIZE>2048 ||
      (HIDDEN_SIZE & 7)!=0 || NUM_Q_HEADS<1 || NUM_Q_HEADS>16 ||
      KV_LORA_RANK<1 || KV_LORA_RANK>512 || QK_NOPE_HEAD_DIM<1 ||
      QK_NOPE_HEAD_DIM>128 || V_HEAD_DIM<1 || V_HEAD_DIM>128) begin: invalid_parameters
    initial $fatal(1,"ANVIL_D1 PARAMETER ERROR: absorption geometry");
  end endgenerate
  assign cmd_ready=rst_n && armed && !flush && state==IDLE;
  assign done=rst_n && !flush && state==COMPLETE;
  assign error=done && failed;
  anvil_d1_mem_port memory_port (
    .clk(clk),.rst_n(rst_n),.flush(flush),.issue(issue),
    .idle(port_idle),.complete(memory_complete),.fault(memory_fault),
    .write(state==WRITE),.kind(4'd15),.layer(layer),
    .proj(state==WRITE ? (matrix_b ? 3'd2 : 3'd1) : 3'd0),
    .row(state==WRITE ? {head,output_index[27:0]} : raw_row),
    .col(state==WRITE ? write_col : raw_col),
    .wdata(state==WRITE ? coefficient[word_number*32+:32] : 32'd0),.rdata(rdata),
    .c_req_valid(c_req_valid),.c_req_ready(c_req_ready),
    .c_req_write(c_req_write),.c_req_kind(c_req_kind),.c_req_layer(c_req_layer),
    .c_req_proj(c_req_proj),.c_req_row(c_req_row),.c_req_col(c_req_col),.c_req_wdata(c_req_wdata),
    .c_rsp_valid(c_rsp_valid),.c_rsp_ready(c_rsp_ready),
    .c_rsp_rdata(c_rsp_rdata),.c_rsp_error(c_rsp_error)
  );
  anvil_d1_mul32 multiplier (
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .in_valid(state==MULTIPLY),.in_ready(multiply_ready),
    .in_a(left_weight),.in_b(right_weight),
    .out_valid(multiply_valid),.out_ready(1'b1),.out_product(multiply_result)
  );
  anvil_d1_accumulator accumulator (
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .in_valid(state==ACCUMULATE),.in_ready(acc_ready),
    .in_first(reduction==0),.in_value({{64{product[63]}},product}),
    .out_valid(acc_valid),.out_ready(1'b1),.out_error(acc_error),.out_sum(accumulated)
  );
  anvil_d1_counter64 raw_counter (
    .clk(clk),.rst_n(rst_n),.clear(accepting),.snapshot(1'b0),
    .increment(read_transfer ? 36'd4 : 36'd0),
    .live_value(raw_read_bytes),.snapshot_value(unused_read_snapshot),.overflow(read_overflow)
  );
  anvil_d1_counter64 absorbed_counter (
    .clk(clk),.rst_n(rst_n),.clear(accepting),.snapshot(1'b0),
    .increment(write_transfer ? 36'd4 : 36'd0),
    .live_value(absorbed_write_bytes),.snapshot_value(unused_write_snapshot),.overflow(write_overflow)
  );
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; armed<=0; failed<=0; matrix_b<=0; epoch_valid<=0;
      layer<=0; epoch<=0; output_index<=0; input_index<=0; reduction<=0; head_value_base<=0;
      absorbed_col<=0; head<=0; word_number<=0; left_weight<=0; right_weight<=0;
      product<=0; coefficient<=0;
      for (l=0;l<NL;l=l+1) epochs[l]<=0;
    end else begin
      armed<=1;
      if (flush) begin state<=IDLE; failed<=0; epoch_valid<=0; end
      else if (!failed && (memory_fault || (acc_valid && acc_error) ||
          read_overflow || write_overflow)) begin
        failed<=1; epoch_valid<=0; state<=COMPLETE;
      end else case (state)
        IDLE: if (accepting) begin
          layer<=cmd_layer; epoch<=cmd_epoch; failed<=0; matrix_b<=0;
          head<=0; head_value_base<=0; output_index<=0; input_index<=0;
          absorbed_col<=0; reduction<=0; word_number<=0;
          if (cmd_layer>=NUM_LAYERS) begin failed<=1; state<=REJECT; end
          else state<=CHECK_EPOCH;
        end
        CHECK_EPOCH: begin
          if (epoch_valid[layer] && epochs[layer]==epoch) state<=COMPLETE;
          else begin epoch_valid[layer]<=0; state<=LEFT_READ; end
        end
        LEFT_READ: if (issue) state<=LEFT_RESPONSE;
        LEFT_RESPONSE: if (memory_complete) begin left_weight<=rdata; state<=RIGHT_READ; end
        RIGHT_READ: if (issue) state<=RIGHT_RESPONSE;
        RIGHT_RESPONSE: if (memory_complete) begin right_weight<=rdata; state<=MULTIPLY; end
        MULTIPLY: if (multiply_ready) state<=MULTIPLY_WAIT;
        MULTIPLY_WAIT: if (multiply_valid) begin product<=multiply_result; state<=ACCUMULATE; end
        ACCUMULATE: if (acc_ready) state<=ACCUMULATE_WAIT;
        ACCUMULATE_WAIT: if (acc_valid) begin
          if (reduction==(matrix_b ? V_HEAD_DIM-1 : QK_NOPE_HEAD_DIM-1)) begin
            if (accumulated[127:96]!={32{accumulated[95]}}) begin
              failed<=1; epoch_valid<=0; state<=COMPLETE;
            end else begin coefficient<=accumulated[95:0]; word_number<=0; state<=WRITE; end
          end else begin reduction<=reduction+1'b1; state<=LEFT_READ; end
        end
        WRITE: if (issue) state<=WRITE_RESPONSE;
        WRITE_RESPONSE: if (memory_complete) begin
          if (word_number!=2) begin word_number<=word_number+1'b1; state<=WRITE; end
          else begin
            reduction<=0; word_number<=0;
            if (input_index!=(matrix_b ? KV_LORA_RANK-1 : HIDDEN_SIZE-1)) begin
              input_index<=input_index+1'b1; absorbed_col<=absorbed_col+32'd3; state<=LEFT_READ;
            end else begin
              input_index<=0; absorbed_col<=0;
              if (output_index!=(matrix_b ? HIDDEN_SIZE-1 : KV_LORA_RANK-1)) begin
                output_index<=output_index+1'b1; state<=LEFT_READ;
              end else begin
                output_index<=0;
                if (head!=NUM_Q_HEADS-1) begin
                  head<=head+1'b1; head_value_base<=head_value_base+32'(V_HEAD_DIM);
                  state<=LEFT_READ;
                end else if (!matrix_b) begin
                  matrix_b<=1; head<=0; head_value_base<=0; state<=LEFT_READ;
                end else begin
                  epoch_valid[layer]<=1; epochs[layer]<=epoch; state<=COMPLETE;
                end
              end
            end
          end
        end
        REJECT: state<=COMPLETE;
        COMPLETE: begin
          if (failed) state<=FAULTED;
          else state<=IDLE;
        end
        FAULTED: state<=FAULTED;
        default: begin failed<=1; epoch_valid<=0; state<=COMPLETE; end
      endcase
    end
  end
endmodule
