module anvil_q4_speculative (
  input wire clk, rst_n, flush, abort, enabled,
  input wire draft_valid,
  output wire draft_ready,
  input wire [31:0] draft_token0, draft_token1, draft_pos,
  input wire draft_new_sequence,
  input wire [31:0] vocabulary, context_capacity, committed_tokens,
  input wire sequence_valid,
  input wire prediction_valid,
  input wire [31:0] prediction,
  output wire target_valid,
  input wire target_ready,
  output wire [31:0] target_token, target_pos,
  output wire target_new_sequence,
  input wire target_done, target_error,
  input wire [31:0] target_argmax,
  output wire verify_valid,
  input wire verify_ready,
  output wire [1:0] verify_accepted,
  output wire verify_error,
  output wire commit_valid,
  output wire [1:0] commit_length,
  output wire [31:0] commit_prediction,
  output wire busy
);
  localparam [2:0] IDLE=0, TARGET0=1, WAIT0=2, TARGET1=3, WAIT1=4, RESPONSE=5;
  reg [2:0] state;
  reg [31:0] token0, token1, position, next_prediction;
  reg new_sequence, failed, faulted;
  reg [1:0] accepted;
  assign draft_ready=rst_n && !flush && enabled && state==IDLE;
  assign target_valid=rst_n && !flush && !abort &&
    (state==TARGET0 || state==TARGET1);
  assign target_token=target_valid ? (state==TARGET0 ? token0 : token1) : 32'd0;
  assign target_pos=target_valid ? position+(state==TARGET1 ? 32'd1 : 32'd0) : 32'd0;
  assign target_new_sequence=target_valid && state==TARGET0 && new_sequence;
  assign verify_valid=rst_n && !flush && state==RESPONSE;
  assign verify_accepted=verify_valid ? accepted : 2'd0;
  assign verify_error=verify_valid && failed;
  assign commit_valid=verify_valid && verify_ready && !failed && !faulted && !abort;
  assign commit_length=commit_valid ? accepted : 2'd0;
  assign commit_prediction=commit_valid ? next_prediction : 32'd0;
  assign busy=rst_n && state!=IDLE;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; token0<=0; token1<=0; position<=0; next_prediction<=0;
      new_sequence<=0; failed<=0; faulted<=0; accepted<=0;
    end else if (flush) begin state<=IDLE; failed<=0; faulted<=0; accepted<=0; end
    else if (abort && state!=IDLE) begin
      faulted<=1;
      if (state==RESPONSE) begin
        if (verify_ready) state<=IDLE;
      end else begin
        failed<=1; accepted<=0; state<=RESPONSE;
      end
    end
    else case (state)
      IDLE: if (draft_valid && draft_ready) begin
        token0<=draft_token0; token1<=draft_token1; position<=draft_pos;
        new_sequence<=draft_new_sequence; failed<=0; faulted<=0; accepted<=0;
        next_prediction<=prediction;
        if (draft_token0>=vocabulary || draft_token1>=vocabulary ||
            vocabulary==0 || context_capacity<2 ||
            draft_pos>=context_capacity-1 ||
            (!draft_new_sequence && !sequence_valid) ||
            (draft_new_sequence ? draft_pos!=0 : draft_pos!=committed_tokens)) begin
          failed<=1; state<=RESPONSE;
        end else if (!draft_new_sequence && prediction_valid && draft_token0!=prediction)
          state<=RESPONSE;
        else state<=TARGET0;
      end
      TARGET0: if (target_ready) state<=WAIT0;
      WAIT0: if (target_done) begin
        if (target_error || target_argmax>=vocabulary) begin
          failed<=1; accepted<=0; state<=RESPONSE;
        end else begin
          accepted<=1; next_prediction<=target_argmax;
          if (target_argmax==token1) state<=TARGET1;
          else state<=RESPONSE;
        end
      end
      TARGET1: if (target_ready) state<=WAIT1;
      WAIT1: if (target_done) begin
        if (target_error || target_argmax>=vocabulary) begin
          failed<=1; accepted<=0; state<=RESPONSE;
        end else begin
          accepted<=2; next_prediction<=target_argmax; state<=RESPONSE;
        end
      end
      RESPONSE: if (verify_ready) state<=IDLE;
      default: begin failed<=1; accepted<=0; state<=RESPONSE; end
    endcase
  end
endmodule
