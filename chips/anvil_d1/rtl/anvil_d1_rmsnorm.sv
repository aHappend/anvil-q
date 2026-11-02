module anvil_d1_rmsnorm #(
  parameter integer NUM_LAYERS=27, HIDDEN_SIZE=2048, MAX_SEQ_LEN=32768
) (
  input wire clk, rst_n, flush, cmd_valid,
  output wire cmd_ready,
  input wire [31:0] cmd_layer, cmd_pos,
  input wire [1:0] cmd_mode,
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
  localparam IDLE=0, SUM_READ=1, SUM_RESPONSE=2, SQUARE=3, SQUARE_WAIT=4;
  localparam ACCUMULATE=5, ACCUMULATE_WAIT=6, MEAN=7, MEAN_WAIT=8;
  localparam EPSILON=9, EPSILON_WAIT=10, ROOT=11, ROOT_WAIT=12;
  localparam RECIPROCAL=13, RECIPROCAL_WAIT=14, X_READ=15, X_RESPONSE=16;
  localparam GAMMA_READ=17, GAMMA_RESPONSE=18, GAMMA_PRODUCT=19, GAMMA_WAIT=20;
  localparam LOW_PRODUCT=21, LOW_WAIT=22, LOW_CORRECT=23, LOW_CORRECT_WAIT=24;
  localparam HIGH_PRODUCT=25, HIGH_WAIT=26, COMBINE=27, COMBINE_WAIT=28;
  localparam ROUND=29, ROUND_WAIT=30, WRITE=31, WRITE_RESPONSE=32;
  localparam COMPLETE=33, FAULTED=34, REJECT=35;
  reg [5:0] state;
  reg armed, failed;
  reg [31:0] layer, index, source_slot, target_slot, result;
  reg [3:0] gamma_kind;
  reg signed [31:0] x, gamma;
  reg [63:0] square, denominator, reciprocal;
  reg signed [63:0] gamma_product;
  reg [127:0] sum, mean;
  reg signed [127:0] low_product, corrected_low, high_product, combined_product;
  wire port_idle, memory_complete, memory_fault;
  wire [31:0] rdata;
  wire issue=port_idle && (state==SUM_READ || state==X_READ ||
    state==GAMMA_READ || state==WRITE);
  wire mul_ready, mul_valid;
  wire signed [63:0] product32;
  wire acc_ready, acc_valid, acc_error;
  wire signed [127:0] accumulated;
  wire div_ready, div_valid, div_error;
  wire [127:0] quotient;
  wire [63:0] div_remainder;
  wire add_ready, add_valid, add_error;
  wire signed [127:0] added;
  wire root_ready, root_valid;
  wire [63:0] root;
  wire [64:0] root_remainder;
  wire wide_ready, wide_valid;
  wire signed [127:0] product96;
  wire round_ready, round_valid;
  wire signed [31:0] rounded;
  wire signed [127:0] extended_gamma_product={{64{gamma_product[63]}},gamma_product};
  wire signed [127:0] add_a=state==EPSILON ? $signed(mean) :
    state==LOW_CORRECT ? low_product : corrected_low;
  wire signed [127:0] add_b=state==EPSILON ? (128'sd1<<48) :
    state==LOW_CORRECT ? (reciprocal[31] ? (extended_gamma_product<<32) : 128'sd0) :
    (high_product<<32);
  wire arithmetic_fault=(acc_valid && acc_error) || (add_valid && add_error) ||
    (div_valid && div_error);
  assign cmd_ready=rst_n && armed && !flush && state==IDLE;
  assign done=rst_n && !flush && state==COMPLETE;
  assign error=done && failed;
  generate if (NUM_LAYERS<1 || NUM_LAYERS>36 || HIDDEN_SIZE<8 ||
      HIDDEN_SIZE>2048 || (HIDDEN_SIZE & 7)!=0 ||
      MAX_SEQ_LEN<1 || MAX_SEQ_LEN>32768) begin: invalid_parameters
    initial $fatal(1,"ANVIL_D1 PARAMETER ERROR: native RMSNorm geometry");
  end endgenerate
  anvil_d1_mem_port memory_port (
    .clk(clk),.rst_n(rst_n),.flush(flush),.issue(issue),
    .idle(port_idle),.complete(memory_complete),.fault(memory_fault),
    .write(state==WRITE),.kind(state==GAMMA_READ ? gamma_kind : 4'd8),
    .layer(state==GAMMA_READ && gamma_kind!=7 ? layer : 32'd0),.proj(3'd0),
    .row(state==GAMMA_READ ? 32'd0 : state==WRITE ? target_slot : source_slot),
    .col(index),.wdata(state==WRITE ? result : 32'd0),.rdata(rdata),
    .c_req_valid(mem_req_valid),.c_req_ready(mem_req_ready),
    .c_req_write(mem_req_write),.c_req_kind(mem_req_kind),.c_req_layer(mem_req_layer),
    .c_req_proj(mem_req_proj),.c_req_row(mem_req_row),.c_req_col(mem_req_col),
    .c_req_wdata(mem_req_wdata),.c_rsp_valid(mem_rsp_valid),.c_rsp_ready(mem_rsp_ready),
    .c_rsp_rdata(mem_rsp_rdata),.c_rsp_error(mem_rsp_error)
  );
  anvil_d1_mul32 multiplier (
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .in_valid(state==SQUARE || state==GAMMA_PRODUCT),.in_ready(mul_ready),
    .in_a(x),.in_b(state==SQUARE ? x : gamma),
    .out_valid(mul_valid),.out_ready(1'b1),.out_product(product32)
  );
  anvil_d1_accumulator accumulator (
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .in_valid(state==ACCUMULATE),.in_ready(acc_ready),
    .in_first(index==0),.in_value($signed({64'd0,square})),
    .out_valid(acc_valid),.out_ready(1'b1),.out_error(acc_error),.out_sum(accumulated)
  );
  anvil_d1_udiv #(.NUM_W(128),.DEN_W(64)) divider (
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .in_valid(state==MEAN || state==RECIPROCAL),.in_ready(div_ready),
    .numerator(state==MEAN ? (sum<<32) : (128'd1<<64)),
    .denominator(state==MEAN ? 64'(HIDDEN_SIZE) : denominator),
    .out_valid(div_valid),.out_ready(1'b1),.out_error(div_error),
    .quotient(quotient),.remainder(div_remainder)
  );
  anvil_d1_add128 adder (
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .in_valid(state==EPSILON || state==LOW_CORRECT || state==COMBINE),
    .in_ready(add_ready),.in_a(add_a),.in_b(add_b),
    .out_valid(add_valid),.out_ready(1'b1),.out_error(add_error),.out_sum(added)
  );
  anvil_d1_isqrt square_root (
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .in_valid(state==ROOT),.in_ready(root_ready),.radicand(mean),
    .out_valid(root_valid),.out_ready(1'b1),.root(root),.remainder(root_remainder)
  );
  anvil_d1_mul96x32 wide_multiplier (
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .in_valid(state==LOW_PRODUCT || state==HIGH_PRODUCT),.in_ready(wide_ready),
    .in_a({{32{gamma_product[63]}},gamma_product}),
    .in_b(state==LOW_PRODUCT ? $signed(reciprocal[31:0]) : $signed(reciprocal[63:32])),
    .out_valid(wide_valid),.out_ready(1'b1),.out_product(product96)
  );
  anvil_d1_round_sat #(.SHIFT(48)) boundary (
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .in_valid(state==ROUND),.in_ready(round_ready),.in_value(combined_product),
    .out_valid(round_valid),.out_ready(1'b1),.out_value(rounded)
  );
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; armed<=0; failed<=0; layer<=0; index<=0;
      source_slot<=0; target_slot<=0; result<=0; gamma_kind<=0;
      x<=0; gamma<=0; square<=0; denominator<=0; reciprocal<=0; gamma_product<=0;
      sum<=0; mean<=0; low_product<=0; corrected_low<=0; high_product<=0; combined_product<=0;
    end else begin
      armed<=1;
      if (flush) begin state<=IDLE; failed<=0; end
      else if (!failed && (memory_fault || arithmetic_fault)) begin
        failed<=1; state<=COMPLETE;
      end else case (state)
        IDLE: if (cmd_valid && cmd_ready) begin
          layer<=cmd_layer; index<=0; sum<=0; failed<=0;
          source_slot<=cmd_mode==1 ? 32'd7 : 32'd0;
          target_slot<=cmd_mode==0 ? 32'd1 : cmd_mode==1 ? 32'd8 : 32'd14;
          gamma_kind<=cmd_mode==0 ? 4'd5 : cmd_mode==1 ? 4'd6 : 4'd7;
          if (cmd_mode>2 || cmd_layer>=NUM_LAYERS || cmd_pos>=MAX_SEQ_LEN) begin
            failed<=1; state<=REJECT;
          end else state<=SUM_READ;
        end
        SUM_READ: if (issue) state<=SUM_RESPONSE;
        SUM_RESPONSE: if (memory_complete) begin x<=rdata; state<=SQUARE; end
        SQUARE: if (mul_ready) state<=SQUARE_WAIT;
        SQUARE_WAIT: if (mul_valid) begin square<=product32; state<=ACCUMULATE; end
        ACCUMULATE: if (acc_ready) state<=ACCUMULATE_WAIT;
        ACCUMULATE_WAIT: if (acc_valid) begin
          sum<=accumulated;
          if (index==HIDDEN_SIZE-1) state<=MEAN;
          else begin index<=index+1'b1; state<=SUM_READ; end
        end
        MEAN: if (div_ready) state<=MEAN_WAIT;
        MEAN_WAIT: if (div_valid) begin mean<=quotient; state<=EPSILON; end
        EPSILON: if (add_ready) state<=EPSILON_WAIT;
        EPSILON_WAIT: if (add_valid) begin mean<=added; state<=ROOT; end
        ROOT: if (root_ready) state<=ROOT_WAIT;
        ROOT_WAIT: if (root_valid) begin
          if (root==0) begin failed<=1; state<=COMPLETE; end
          else begin denominator<=root; state<=RECIPROCAL; end
        end
        RECIPROCAL: if (div_ready) state<=RECIPROCAL_WAIT;
        RECIPROCAL_WAIT: if (div_valid) begin
          if (quotient>(128'd1<<40)) begin failed<=1; state<=COMPLETE; end
          else begin reciprocal<=quotient[63:0]; index<=0; state<=X_READ; end
        end
        X_READ: if (issue) state<=X_RESPONSE;
        X_RESPONSE: if (memory_complete) begin x<=rdata; state<=GAMMA_READ; end
        GAMMA_READ: if (issue) state<=GAMMA_RESPONSE;
        GAMMA_RESPONSE: if (memory_complete) begin gamma<=rdata; state<=GAMMA_PRODUCT; end
        GAMMA_PRODUCT: if (mul_ready) state<=GAMMA_WAIT;
        GAMMA_WAIT: if (mul_valid) begin gamma_product<=product32; state<=LOW_PRODUCT; end
        LOW_PRODUCT: if (wide_ready) state<=LOW_WAIT;
        LOW_WAIT: if (wide_valid) begin low_product<=product96; state<=LOW_CORRECT; end
        LOW_CORRECT: if (add_ready) state<=LOW_CORRECT_WAIT;
        LOW_CORRECT_WAIT: if (add_valid) begin corrected_low<=added; state<=HIGH_PRODUCT; end
        HIGH_PRODUCT: if (wide_ready) state<=HIGH_WAIT;
        HIGH_WAIT: if (wide_valid) begin high_product<=product96; state<=COMBINE; end
        COMBINE: if (add_ready) state<=COMBINE_WAIT;
        COMBINE_WAIT: if (add_valid) begin combined_product<=added; state<=ROUND; end
        ROUND: if (round_ready) state<=ROUND_WAIT;
        ROUND_WAIT: if (round_valid) begin result<=rounded; state<=WRITE; end
        WRITE: if (issue) state<=WRITE_RESPONSE;
        WRITE_RESPONSE: if (memory_complete) begin
          if (index==HIDDEN_SIZE-1) state<=COMPLETE;
          else begin index<=index+1'b1; state<=X_READ; end
        end
        COMPLETE: begin
          if (failed) state<=FAULTED;
          else state<=IDLE;
        end
        FAULTED: state<=FAULTED;
        REJECT: state<=COMPLETE;
        default: begin failed<=1; state<=COMPLETE; end
      endcase
    end
  end
endmodule
