module anvil_q1_fp2_gqa_group #(
  parameter GROUP_HEADS=7, HEAD_DIM=64, MAX_SEQ_LEN=32768
) (
  input wire clk, rst_n, cmd_valid,
  output wire cmd_ready,
  input wire [31:0] cmd_len,
  input wire query_valid,
  output wire query_ready,
  input wire [15:0] query_data,
  input wire query_last,
  input wire kv_valid,
  output wire kv_ready,
  input wire [15:0] k_data, v_data,
  input wire kv_last,
  output wire out_valid,
  input wire out_ready,
  output wire [31:0] out_data, out_head, out_component,
  output wire out_last,
  output wire [4:0] status,
  output wire done, error,
  output wire engines_rst_n,
  output wire [GROUP_HEADS-1:0] engine_cmd_valid,
  input wire [GROUP_HEADS-1:0] engine_cmd_ready,
  output wire [31:0] engine_cmd_len,
  output wire [GROUP_HEADS-1:0] engine_q_valid,
  input wire [GROUP_HEADS-1:0] engine_q_ready,
  output wire [15:0] engine_q_data,
  output wire engine_q_last,
  output wire [GROUP_HEADS-1:0] engine_kv_valid,
  input wire [GROUP_HEADS-1:0] engine_kv_ready,
  output wire [15:0] engine_k_data, engine_v_data,
  output wire engine_kv_last,
  input wire [GROUP_HEADS-1:0] engine_out_valid,
  output wire [GROUP_HEADS-1:0] engine_out_ready,
  input wire [32*GROUP_HEADS-1:0] engine_out_data,
  input wire [GROUP_HEADS-1:0] engine_out_last,
  input wire [5*GROUP_HEADS-1:0] engine_status,
  input wire [GROUP_HEADS-1:0] engine_done, engine_error
);
  localparam IDLE=0, START=1, QUERY=2, KV=3, WAIT_RESULTS=4;
  localparam READ_RESULT=5, LATCH_RESULT=6, OUTPUT=7, COMPLETE_WAIT=8;
  localparam ERROR_WAIT0=9, ERROR_WAIT1=10, FINISH=11;
  localparam ADDRESS_BITS=HEAD_DIM>1 ? $clog2(HEAD_DIM) : 1;
  reg [3:0] state;
  reg failed;
  reg [4:0] flags;
  reg [31:0] length, query_head, query_component, token, component;
  reg [31:0] output_head, output_component, payload;
  reg [GROUP_HEADS-1:0] started, sent, finished;
  reg held, held_last, final_pair;
  reg [15:0] held_k, held_v;
  reg [31:0] received [0:GROUP_HEADS-1];
  wire [31:0] result_q [0:GROUP_HEADS-1];
  wire [GROUP_HEADS-1:0] result_complete, framing_error, fatal_result;
  wire [GROUP_HEADS-1:0] status_bits [0:4];
  wire [4:0] current_status;
  wire query_frame_ok=query_last==(query_component+1==HEAD_DIM);
  wire kv_frame_ok=kv_last==(component+1==HEAD_DIM);
  wire all_sent=&(sent | engine_kv_ready);
  wire query_transfer=query_valid && query_ready;
  wire kv_transfer=kv_valid && kv_ready;
  wire collecting=state==KV || state==WAIT_RESULTS;
  wire engine_fault=(|(engine_done & engine_error)) ||
    (|framing_error) || (|fatal_result);
  assign cmd_ready=rst_n && state==IDLE;
  assign query_ready=rst_n && state==QUERY && engine_q_ready[query_head];
  assign kv_ready=rst_n && state==KV && !held && !final_pair;
  assign out_valid=rst_n && state==OUTPUT;
  assign out_data=out_valid ? payload : 32'd0;
  assign out_head=out_valid ? output_head : 32'd0;
  assign out_component=out_valid ? output_component : 32'd0;
  assign out_last=out_valid && output_head+1==GROUP_HEADS &&
    output_component+1==HEAD_DIM;
  assign done=rst_n && state==FINISH;
  assign error=done && failed;
  assign status=rst_n && (out_valid || done) ? flags : 5'd0;
  // A group fault aborts every sibling, including engines still filling a tile.
  assign engines_rst_n=rst_n && !failed;
  assign engine_cmd_len=rst_n && state!=IDLE ? length : 32'd0;
  assign engine_q_data=rst_n && state==QUERY ? query_data : 16'd0;
  assign engine_q_last=rst_n && state==QUERY && query_frame_ok && query_last;
  assign engine_k_data=rst_n && held ? held_k : 16'd0;
  assign engine_v_data=rst_n && held ? held_v : 16'd0;
  assign engine_kv_last=rst_n && held && held_last;
  genvar g, b;
  generate
    if (GROUP_HEADS<1 || HEAD_DIM<1 || MAX_SEQ_LEN<1 ||
        128'(GROUP_HEADS)*128'(HEAD_DIM)>32'hffffffff ||
        128'(MAX_SEQ_LEN)*128'(HEAD_DIM)>32'hffffffff) begin: invalid_parameters
      initial $fatal(1,"FP2 GQA GROUP PARAMETER ERROR");
    end
    for (g=0;g<GROUP_HEADS;g=g+1) begin: heads
      (* ramstyle = "M20K", nomem2reg *) reg [31:0] results [0:HEAD_DIM-1];
      reg [31:0] read_q;
      assign result_q[g]=read_q;
      assign engine_cmd_valid[g]=rst_n && state==START && !started[g];
      assign engine_q_valid[g]=rst_n && state==QUERY && query_head==g &&
        query_valid && query_frame_ok;
      assign engine_kv_valid[g]=rst_n && state==KV && held && !sent[g];
      assign engine_out_ready[g]=rst_n && collecting && received[g]<HEAD_DIM;
      assign result_complete[g]=received[g]==HEAD_DIM;
      assign framing_error[g]=collecting &&
        ((engine_out_valid[g] && engine_out_ready[g] &&
          engine_out_last[g]!=(received[g]+1==HEAD_DIM)) ||
         (engine_done[g] && !engine_error[g] && received[g]!=HEAD_DIM) ||
         (engine_out_valid[g] && received[g]==HEAD_DIM));
      assign fatal_result[g]=collecting && (engine_out_valid[g] || engine_done[g]) &&
        (|engine_status[5*g+2+:3]);
      always @(posedge clk) begin
        if (engine_out_valid[g] && engine_out_ready[g])
          results[received[g][ADDRESS_BITS-1:0]]<=engine_out_data[32*g+:32];
        read_q<=results[output_component[ADDRESS_BITS-1:0]];
      end
      for (b=0;b<5;b=b+1) begin: flag_bits
        assign status_bits[b][g]=(engine_out_valid[g] || engine_done[g]) &&
          engine_status[5*g+b];
      end
    end
    for (b=0;b<5;b=b+1) begin: reduce_flags
      assign current_status[b]=|status_bits[b];
    end
  endgenerate
  integer i;
  always @(posedge clk) begin
    if (!rst_n) begin
      state<=IDLE; failed<=0; flags<=0; length<=0;
      query_head<=0; query_component<=0; token<=0; component<=0;
      output_head<=0; output_component<=0; payload<=0;
      started<=0; sent<=0; finished<=0;
      held<=0; held_last<=0; held_k<=0; held_v<=0; final_pair<=0;
      for (i=0;i<GROUP_HEADS;i=i+1) received[i]<=0;
    end else if ((state==QUERY || collecting) && engine_fault) begin
      failed<=1; flags<=flags | current_status; held<=0; state<=ERROR_WAIT0;
    end else begin
      if (collecting) begin
        flags<=flags | current_status;
        finished<=finished | engine_done;
        for (i=0;i<GROUP_HEADS;i=i+1)
          if (engine_out_valid[i] && engine_out_ready[i])
            received[i]<=received[i]+1'b1;
      end
      case (state)
        IDLE: if (cmd_valid) begin
          length<=cmd_len; failed<=0; flags<=0;
          query_head<=0; query_component<=0; token<=0; component<=0;
          output_head<=0; output_component<=0; payload<=0;
          started<=0; sent<=0; finished<=0; held<=0; final_pair<=0;
          for (i=0;i<GROUP_HEADS;i=i+1) received[i]<=0;
          if (cmd_len==0 || cmd_len>MAX_SEQ_LEN) begin
            failed<=1; state<=ERROR_WAIT0;
          end else state<=START;
        end
        START: begin
          started<=started | engine_cmd_ready;
          if (&(started | engine_cmd_ready)) state<=QUERY;
        end
        QUERY: if (query_transfer) begin
          if (!query_frame_ok) begin failed<=1; state<=ERROR_WAIT0; end
          else if (query_last) begin
            query_component<=0;
            if (query_head+1==GROUP_HEADS) state<=KV;
            else query_head<=query_head+1'b1;
          end else query_component<=query_component+1'b1;
        end
        KV: begin
          if (kv_transfer) begin
            if (!kv_frame_ok) begin failed<=1; state<=ERROR_WAIT0; end
            else begin
              held<=1; held_k<=k_data; held_v<=v_data; held_last<=kv_last; sent<=0;
              if (kv_last) begin
                component<=0;
                if (token+1==length) final_pair<=1;
                else token<=token+1'b1;
              end else component<=component+1'b1;
            end
          end
          if (held) begin
            sent<=sent | engine_kv_ready;
            if (all_sent) begin
              held<=0; sent<=0;
              if (final_pair) state<=WAIT_RESULTS;
            end
          end
        end
        WAIT_RESULTS: if ((&result_complete) && (&(finished | engine_done))) begin
          output_head<=0; output_component<=0; state<=READ_RESULT;
        end
        READ_RESULT: state<=LATCH_RESULT;
        LATCH_RESULT: begin payload<=result_q[output_head]; state<=OUTPUT; end
        OUTPUT: if (out_ready) begin
          if (output_component+1==HEAD_DIM) begin
            output_component<=0;
            if (output_head+1==GROUP_HEADS) state<=COMPLETE_WAIT;
            else begin output_head<=output_head+1'b1; state<=READ_RESULT; end
          end else begin output_component<=output_component+1'b1; state<=READ_RESULT; end
        end
        COMPLETE_WAIT: state<=FINISH;
        ERROR_WAIT0: state<=ERROR_WAIT1;
        ERROR_WAIT1: state<=FINISH;
        FINISH: begin state<=IDLE; failed<=0; end
        default: begin failed<=1; state<=ERROR_WAIT0; end
      endcase
    end
  end
endmodule
