module anvil_d1_expert #(
  parameter integer HIDDEN_SIZE=2048, INTERMEDIATE_SIZE=10944,
  parameter integer MOE_INTERMEDIATE_SIZE=1408, TILE_K=128, TILE_ROWS=8,
  localparam integer TK=(TILE_K>=8 && TILE_K<=128) ? TILE_K : 8,
  localparam integer TR=(TILE_ROWS>=1 && TILE_ROWS<=8) ? TILE_ROWS : 1,
  localparam integer TILE_WORDS=TK*TR
) (
  input wire clk, rst_n, flush, cmd_valid,
  output wire cmd_ready,
  input wire [31:0] cmd_layer,
  input wire [6:0] cmd_expert,
  input wire cmd_dense, cmd_prefetched,
  output wire done, error, arithmetic_busy,
  output wire tile_read_valid,
  input wire tile_read_ready,
  output wire [31:0] tile_read_index,
  input wire tile_rsp_valid,
  output wire tile_rsp_ready,
  input wire [31:0] tile_rsp_data,
  input wire tile_rsp_error,
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
  localparam IDLE=0, BIAS_READ=1, BIAS_RESPONSE=2, BIAS_ACC=3, BIAS_WAIT=4;
  localparam INPUT_READ=5, INPUT_RESPONSE=6, WEIGHT_READ=7, WEIGHT_RESPONSE=8;
  localparam TILE_READ=9, TILE_RESPONSE=10, MULTIPLY=11, MULTIPLY_WAIT=12;
  localparam ACC=13, ACC_WAIT=14, ROUND=15, ROUND_WAIT=16;
  localparam SILU=17, SILU_WAIT=18, GATE_UP=19, GATE_UP_WAIT=20;
  localparam PRODUCT_ROUND=21, PRODUCT_ROUND_WAIT=22, WRITE=23, WRITE_RESPONSE=24;
  localparam COMPLETE=25, FAULTED=26, REJECT=27;
  localparam FILL_READ=28, FILL_RESPONSE=29, COMPUTE_READ=30, COMPUTE_CAPTURE=31;
  reg [4:0] state;
  reg armed, failed, dense, prefetched;
  reg [6:0] expert;
  reg [1:0] projection;
  reg [31:0] layer, intermediate, output_index, input_index, tile_row_base;
  reg [31:0] output_tile_base, output_tile_offset, output_tile_word_base;
  reg [31:0] input_tile_base, input_tile_offset;
  reg [31:0] fill_row, fill_col, fill_index, fill_base, compute_address;
  reg victim, filling_bank;
  reg [1:0] compute_valid;
  reg [1:0] compute_projection [0:1];
  reg [31:0] compute_row_base [0:1], compute_col_base [0:1];
  (* ramstyle="M20K", nomem2reg *) reg [31:0] compute_tiles [0:2*TILE_WORDS-1];
  reg [31:0] compute_word;
  reg signed [31:0] activation, weight, bias_value, gate_value, up_value, result;
  reg signed [127:0] product, sum;
  wire port_idle, memory_complete, memory_fault;
  wire [31:0] rdata;
  wire issue=port_idle && (state==BIAS_READ || state==INPUT_READ ||
    state==FILL_READ || state==WRITE);
  wire tile_operand=prefetched && projection==0 && output_index<TILE_ROWS && input_index<TILE_K;
  wire hit0=compute_valid[0] && compute_projection[0]==projection &&
    compute_row_base[0]==output_tile_base && compute_col_base[0]==input_tile_base;
  wire hit1=compute_valid[1] && compute_projection[1]==projection &&
    compute_row_base[1]==output_tile_base && compute_col_base[1]==input_tile_base;
  wire [31:0] projection_rows=projection==2 ? 32'(HIDDEN_SIZE) : intermediate;
  wire [31:0] projection_cols=projection==2 ? intermediate : 32'(HIDDEN_SIZE);
  wire last_fill_col=fill_col==TK-1 || input_tile_base+fill_col==projection_cols-1'b1;
  wire last_fill_row=fill_row==TR-1 || output_tile_base+fill_row==projection_rows-1'b1;
  wire mul_ready, mul_valid;
  wire signed [63:0] multiplied;
  wire acc_ready, acc_valid, acc_error;
  wire signed [127:0] accumulated;
  wire round_ready, round_valid;
  wire signed [31:0] rounded;
  wire silu_ready, silu_valid, silu_error;
  wire signed [31:0] silu_value;
  assign cmd_ready=rst_n && armed && !flush && state==IDLE;
  assign done=rst_n && !flush && state==COMPLETE;
  assign error=done && failed;
  assign arithmetic_busy=rst_n && !flush && (
    state==BIAS_ACC || state==BIAS_WAIT || state==MULTIPLY || state==MULTIPLY_WAIT ||
    state==ACC || state==ACC_WAIT || state==ROUND || state==ROUND_WAIT ||
    state==SILU || state==SILU_WAIT || state==GATE_UP || state==GATE_UP_WAIT ||
    state==PRODUCT_ROUND || state==PRODUCT_ROUND_WAIT);
  assign tile_read_valid=rst_n && !flush && state==TILE_READ;
  assign tile_read_index=tile_read_valid ? tile_row_base+input_index : 32'd0;
  assign tile_rsp_ready=rst_n && !flush && state==TILE_RESPONSE;
  generate if (HIDDEN_SIZE<8 || HIDDEN_SIZE>2048 || (HIDDEN_SIZE & 7)!=0 ||
      INTERMEDIATE_SIZE<8 || INTERMEDIATE_SIZE>11008 || (INTERMEDIATE_SIZE & 7)!=0 ||
      MOE_INTERMEDIATE_SIZE<8 || MOE_INTERMEDIATE_SIZE>1408 || (MOE_INTERMEDIATE_SIZE & 7)!=0 ||
      TILE_K<8 || TILE_K>128 || (TILE_K & 7)!=0 || TILE_ROWS<1 || TILE_ROWS>8) begin: invalid_parameters
    initial $fatal(1,"ANVIL_D1 PARAMETER ERROR: expert geometry");
  end endgenerate
  anvil_d1_mem_port memory_port (
    .clk(clk),.rst_n(rst_n),.flush(flush),.issue(issue),
    .idle(port_idle),.complete(memory_complete),.fault(memory_fault),
    .write(state==WRITE),
    .kind(state==INPUT_READ && projection!=2 ? 4'd8 : 4'd15),
    .layer(state==INPUT_READ && projection!=2 ? 32'd0 : layer),
    .proj(state==INPUT_READ ? (projection==2 ? 3'd7 : 3'd0) :
      state==WRITE ? 3'd7 : 3'd5),
    .row(state==INPUT_READ ? 32'd8 : state==WRITE ? (projection==2 && dense ? 32'd4 : 32'd8) :
      state==FILL_READ ? {expert,projection,23'(output_tile_base+fill_row)} :
      {expert,2'd3,output_index[22:0]}),
    .col(state==BIAS_READ ? {30'd0,projection} : state==WRITE ?
      (projection==2 && !dense ? intermediate+output_index : output_index) :
      state==FILL_READ ? input_tile_base+fill_col : input_index),
    .wdata(state==WRITE ? result : 32'd0),.rdata(rdata),
    .c_req_valid(c_req_valid),.c_req_ready(c_req_ready),
    .c_req_write(c_req_write),.c_req_kind(c_req_kind),.c_req_layer(c_req_layer),
    .c_req_proj(c_req_proj),.c_req_row(c_req_row),.c_req_col(c_req_col),
    .c_req_wdata(c_req_wdata),.c_rsp_valid(c_rsp_valid),.c_rsp_ready(c_rsp_ready),
    .c_rsp_rdata(c_rsp_rdata),.c_rsp_error(c_rsp_error)
  );
  anvil_d1_mul32 multiplier (
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .in_valid(state==MULTIPLY || state==GATE_UP),.in_ready(mul_ready),
    .in_a(state==GATE_UP ? gate_value : activation),
    .in_b(state==GATE_UP ? up_value : weight),
    .out_valid(mul_valid),.out_ready(1'b1),.out_product(multiplied)
  );
  anvil_d1_accumulator accumulator (
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .in_valid(state==BIAS_ACC || state==ACC),.in_ready(acc_ready),
    .in_first(state==BIAS_ACC),
    .in_value(state==BIAS_ACC ? ($signed({{96{bias_value[31]}},bias_value})<<<16) : product),
    .out_valid(acc_valid),.out_ready(1'b1),.out_error(acc_error),.out_sum(accumulated)
  );
  anvil_d1_round_sat #(.SHIFT(16)) boundary (
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .in_valid(state==ROUND || state==PRODUCT_ROUND),.in_ready(round_ready),
    .in_value(state==PRODUCT_ROUND ? product : sum),
    .out_valid(round_valid),.out_ready(1'b1),.out_value(rounded)
  );
  anvil_d1_silu activation_function (
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .in_valid(state==SILU),.in_ready(silu_ready),.in_x(result),
    .out_valid(silu_valid),.out_ready(1'b1),.out_error(silu_error),.out_value(silu_value)
  );
  always @(posedge clk) begin
    compute_word<=compute_tiles[compute_address];
    if (rst_n && !flush && state==FILL_RESPONSE && memory_complete && !memory_fault)
      compute_tiles[fill_base+fill_index]<=rdata;
  end
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; armed<=0; failed<=0; dense<=0; prefetched<=0; expert<=0; projection<=0;
      layer<=0; intermediate<=0; output_index<=0; input_index<=0; tile_row_base<=0;
      output_tile_base<=0; output_tile_offset<=0; output_tile_word_base<=0;
      input_tile_base<=0; input_tile_offset<=0;
      fill_row<=0; fill_col<=0; fill_index<=0; fill_base<=0; compute_address<=0;
      victim<=0; filling_bank<=0; compute_valid<=0;
      compute_projection[0]<=0; compute_projection[1]<=0;
      compute_row_base[0]<=0; compute_row_base[1]<=0;
      compute_col_base[0]<=0; compute_col_base[1]<=0;
      activation<=0; weight<=0; bias_value<=0; gate_value<=0; up_value<=0;
      result<=0; product<=0; sum<=0;
    end else begin
      armed<=1;
      if (flush) begin state<=IDLE; failed<=0; compute_valid<=0; end
      else if (!failed && (memory_fault || (acc_valid && acc_error) ||
          (silu_valid && silu_error) ||
          (tile_rsp_valid && tile_rsp_ready && tile_rsp_error))) begin
        failed<=1; state<=COMPLETE;
      end else case (state)
        IDLE: if (cmd_valid && cmd_ready) begin
          layer<=cmd_layer; expert<=cmd_expert; dense<=cmd_dense; prefetched<=cmd_prefetched;
          intermediate<=cmd_dense ? 32'(INTERMEDIATE_SIZE) : 32'(MOE_INTERMEDIATE_SIZE);
          projection<=0; output_index<=0; input_index<=0; tile_row_base<=0; failed<=0;
          output_tile_base<=0; output_tile_offset<=0; output_tile_word_base<=0;
          input_tile_base<=0; input_tile_offset<=0; compute_valid<=0; victim<=0;
          if ((cmd_dense && (cmd_expert!=127 || cmd_prefetched)) ||
              (!cmd_dense && cmd_expert==127)) begin failed<=1; state<=REJECT; end
          else state<=BIAS_READ;
        end
        BIAS_READ: if (issue) state<=BIAS_RESPONSE;
        BIAS_RESPONSE: if (memory_complete) begin bias_value<=rdata; state<=BIAS_ACC; end
        BIAS_ACC: if (acc_ready) state<=BIAS_WAIT;
        BIAS_WAIT: if (acc_valid) begin
          input_index<=0; input_tile_base<=0; input_tile_offset<=0; state<=INPUT_READ;
        end
        INPUT_READ: if (issue) state<=INPUT_RESPONSE;
        INPUT_RESPONSE: if (memory_complete) begin
          activation<=rdata;
          if (tile_operand) state<=TILE_READ;
          else state<=WEIGHT_READ;
        end
        WEIGHT_READ: begin
          if (hit0 || hit1) begin
            compute_address<=(hit0 ? 32'd0 : 32'(TILE_WORDS))+
              output_tile_word_base+input_tile_offset;
            state<=COMPUTE_READ;
          end else begin
            filling_bank<=victim; fill_base<=victim ? 32'(TILE_WORDS) : 32'd0;
            compute_valid[victim]<=0; fill_row<=0; fill_col<=0; fill_index<=0;
            victim<=!victim; state<=FILL_READ;
          end
        end
        FILL_READ: if (issue) state<=FILL_RESPONSE;
        FILL_RESPONSE: if (memory_complete) begin
          if (last_fill_col) begin
            fill_col<=0;
            if (last_fill_row) begin
              compute_projection[filling_bank]<=projection;
              compute_row_base[filling_bank]<=output_tile_base;
              compute_col_base[filling_bank]<=input_tile_base;
              compute_valid[filling_bank]<=1; state<=WEIGHT_READ;
            end else begin
              fill_row<=fill_row+1'b1; fill_index<=fill_index+32'(TK)-fill_col;
              state<=FILL_READ;
            end
          end else begin
            fill_col<=fill_col+1'b1; fill_index<=fill_index+1'b1; state<=FILL_READ;
          end
        end
        COMPUTE_READ: state<=COMPUTE_CAPTURE;
        COMPUTE_CAPTURE: begin weight<=compute_word; state<=MULTIPLY; end
        TILE_READ: if (tile_read_ready) state<=TILE_RESPONSE;
        TILE_RESPONSE: if (tile_rsp_valid) begin weight<=tile_rsp_data; state<=MULTIPLY; end
        MULTIPLY: if (mul_ready) state<=MULTIPLY_WAIT;
        MULTIPLY_WAIT: if (mul_valid) begin
          product<={{64{multiplied[63]}},multiplied}; state<=ACC;
        end
        ACC: if (acc_ready) state<=ACC_WAIT;
        ACC_WAIT: if (acc_valid) begin
          if (input_index==(projection==2 ? intermediate-1'b1 : HIDDEN_SIZE-1)) begin
            sum<=accumulated; state<=ROUND;
          end else begin
            input_index<=input_index+1'b1;
            if (input_tile_offset==TK-1) begin
              input_tile_offset<=0; input_tile_base<=input_tile_base+32'(TK);
            end else input_tile_offset<=input_tile_offset+1'b1;
            state<=INPUT_READ;
          end
        end
        ROUND: if (round_ready) state<=ROUND_WAIT;
        ROUND_WAIT: if (round_valid) begin
          result<=rounded;
          if (projection==0) state<=SILU;
          else if (projection==1) begin up_value<=rounded; state<=GATE_UP; end
          else state<=WRITE;
        end
        SILU: if (silu_ready) state<=SILU_WAIT;
        SILU_WAIT: if (silu_valid) begin
          gate_value<=silu_value; projection<=1; state<=BIAS_READ;
        end
        GATE_UP: if (mul_ready) state<=GATE_UP_WAIT;
        GATE_UP_WAIT: if (mul_valid) begin
          product<={{64{multiplied[63]}},multiplied}; state<=PRODUCT_ROUND;
        end
        PRODUCT_ROUND: if (round_ready) state<=PRODUCT_ROUND_WAIT;
        PRODUCT_ROUND_WAIT: if (round_valid) begin result<=rounded; state<=WRITE; end
        WRITE: if (issue) state<=WRITE_RESPONSE;
        WRITE_RESPONSE: if (memory_complete) begin
          if (projection==2) begin
            if (output_index==HIDDEN_SIZE-1) state<=COMPLETE;
            else begin
              output_index<=output_index+1'b1;
              if (output_tile_offset==TR-1) begin
                output_tile_base<=output_tile_base+32'(TR); output_tile_offset<=0;
                output_tile_word_base<=0;
              end else begin
                output_tile_offset<=output_tile_offset+1'b1;
                output_tile_word_base<=output_tile_word_base+32'(TK);
              end
              state<=BIAS_READ;
            end
          end else if (output_index==intermediate-1'b1) begin
            projection<=2; output_index<=0; output_tile_base<=0;
            output_tile_offset<=0; output_tile_word_base<=0; state<=BIAS_READ;
          end else begin
            projection<=0; output_index<=output_index+1'b1;
            if (output_tile_offset==TR-1) begin
              output_tile_base<=output_tile_base+32'(TR); output_tile_offset<=0;
              output_tile_word_base<=0;
            end else begin
              output_tile_offset<=output_tile_offset+1'b1;
              output_tile_word_base<=output_tile_word_base+32'(TK);
            end
            tile_row_base<=tile_row_base+32'(TILE_K); state<=BIAS_READ;
          end
        end
        REJECT: state<=COMPLETE;
        COMPLETE: if (failed) state<=FAULTED; else state<=IDLE;
        FAULTED: state<=FAULTED;
        default: begin failed<=1; state<=COMPLETE; end
      endcase
    end
  end
endmodule
