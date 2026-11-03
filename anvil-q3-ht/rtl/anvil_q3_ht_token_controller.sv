module anvil_q3_ht_token_controller #(
  parameter NUM_LAYERS=36, VOCAB_SIZE=151936, MAX_SEQ_LEN=32768
) (
  input wire clk, rst_n, cancel, run_enable,
  input wire token_valid,
  output wire token_ready,
  input wire [31:0] token_id, token_pos,
  input wire new_sequence, token_phase,
  output wire done, error, cancel_done, inference_idle,
  input wire memory_idle, memory_drained, memory_fault,
  output wire core_flush, memory_flush,
  output wire decoder_valid,
  input wire decoder_ready, decoder_done, decoder_error,
  output wire norm_valid,
  input wire norm_ready, norm_done, norm_error,
  output wire io_valid, io_project,
  input wire io_ready, io_done, io_error,
  input wire last_logit_transfer,
  output wire logits_enabled,
  output wire [31:0] epoch, active_token_id, active_position, active_layer,
  output wire active_phase
);
  localparam LEGAL=NUM_LAYERS>0 && VOCAB_SIZE>0 &&
    MAX_SEQ_LEN>=1 && MAX_SEQ_LEN<=32768;
  localparam IDLE=0, SEQUENCE_FLUSH=1, SEQUENCE_DRAIN=2, EMBED=3, EMBED_WAIT=4;
  localparam DECODER=5, DECODER_WAIT=6, FINAL_NORM=7, FINAL_NORM_WAIT=8;
  localparam PROJECT=9, PROJECT_WAIT=10, COMPLETE=11;
  localparam ABORT_FLUSH=12, ABORT_DRAIN=13, CANCEL_COMPLETE=14;
  reg [3:0] state;
  reg failed, sequence_valid, active_token, cancelled_active, cancel_pending;
  reg phase, decoding;
  reg [31:0] token, position, next_position, layer, sequence_epoch;
  reg [31:0] prefill_count, frozen_prefill_count;
  wire operation_fault=memory_fault || (decoder_done && decoder_error) ||
    (norm_done && norm_error) || (io_done && io_error);
  wire accepting_token=token_valid && token_ready;

  generate if (!LEGAL) begin: invalid_parameters
    initial $fatal(1,"ANVIL_Q3_HT PARAMETER ERROR: token controller dimensions");
  end endgenerate
  assign token_ready=rst_n && LEGAL && !cancel && run_enable &&
    !memory_fault && state==IDLE && memory_idle;
  assign inference_idle=rst_n && !cancel && state==IDLE && !active_token;
  assign memory_flush=rst_n && (cancel || state==SEQUENCE_FLUSH || state==ABORT_FLUSH);
  assign core_flush=rst_n && (cancel || state==SEQUENCE_FLUSH || state==SEQUENCE_DRAIN ||
    state==ABORT_FLUSH || state==ABORT_DRAIN || state==CANCEL_COMPLETE ||
    (state==COMPLETE && failed));
  assign done=rst_n && !cancel && (state==COMPLETE ||
    (state==CANCEL_COMPLETE && cancelled_active));
  assign error=done && failed;
  assign cancel_done=rst_n && !cancel && state==CANCEL_COMPLETE;
  assign decoder_valid=rst_n && !core_flush && state==DECODER;
  assign norm_valid=rst_n && !core_flush && state==FINAL_NORM;
  assign io_valid=rst_n && !core_flush && (state==EMBED || state==PROJECT);
  assign io_project=io_valid && state==PROJECT;
  assign logits_enabled=rst_n && !core_flush && state==PROJECT_WAIT;
  assign epoch=rst_n ? sequence_epoch : 32'd0;
  assign active_token_id=rst_n ? token : 32'd0;
  assign active_position=rst_n ? position : 32'd0;
  assign active_layer=rst_n ? layer : 32'd0;
  assign active_phase=rst_n && phase;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; failed<=0; sequence_valid<=0; active_token<=0;
      cancelled_active<=0; cancel_pending<=0; phase<=0; decoding<=0;
      token<=0; position<=0; next_position<=0; layer<=0; sequence_epoch<=0;
      prefill_count<=0; frozen_prefill_count<=0;
    end else if (cancel) begin
      failed<=1; sequence_valid<=0; cancelled_active<=active_token; cancel_pending<=1;
      decoding<=0; prefill_count<=0; frozen_prefill_count<=0; state<=ABORT_DRAIN;
    end else if (operation_fault && state!=ABORT_FLUSH && state!=ABORT_DRAIN &&
        state!=CANCEL_COMPLETE && !(state==COMPLETE && failed)) begin
      failed<=1; sequence_valid<=0; cancelled_active<=0; cancel_pending<=0;
      decoding<=0; prefill_count<=0; frozen_prefill_count<=0; state<=ABORT_FLUSH;
    end else case (state)
      IDLE: if (accepting_token) begin
        failed<=0; active_token<=1; cancelled_active<=0; cancel_pending<=0;
        if (token_id>=VOCAB_SIZE || token_pos>=MAX_SEQ_LEN ||
            (new_sequence && token_pos!=0) ||
            (!new_sequence && (!sequence_valid || token_pos!=next_position ||
              (decoding && !token_phase) ||
              (decoding && token_pos<frozen_prefill_count)))) begin
          failed<=1; sequence_valid<=0; decoding<=0; prefill_count<=0;
          frozen_prefill_count<=0; state<=ABORT_FLUSH;
        end else begin
          token<=token_id; position<=token_pos; phase<=token_phase; layer<=0;
          if (new_sequence) begin
            sequence_valid<=1; next_position<=0; prefill_count<=0; frozen_prefill_count<=0;
            decoding<=token_phase; sequence_epoch<=sequence_epoch+1'b1; state<=SEQUENCE_FLUSH;
          end else begin
            if (token_phase && !decoding) begin
              decoding<=1; frozen_prefill_count<=prefill_count;
            end
            state<=EMBED;
          end
        end
      end
      SEQUENCE_FLUSH: state<=SEQUENCE_DRAIN;
      SEQUENCE_DRAIN: if (memory_drained) state<=EMBED;
      EMBED: if (io_ready) state<=EMBED_WAIT;
      EMBED_WAIT: if (io_done) state<=DECODER;
      DECODER: if (decoder_ready) state<=DECODER_WAIT;
      DECODER_WAIT: if (decoder_done) begin
        if (layer+1<NUM_LAYERS) begin layer<=layer+1'b1; state<=DECODER; end
        else state<=FINAL_NORM;
      end
      FINAL_NORM: if (norm_ready) state<=FINAL_NORM_WAIT;
      FINAL_NORM_WAIT: if (norm_done) state<=PROJECT;
      PROJECT: if (io_ready) state<=PROJECT_WAIT;
      PROJECT_WAIT: if (last_logit_transfer) begin
        failed<=0; active_token<=0; next_position<=position+1'b1; sequence_valid<=1;
        if (!phase) prefill_count<=position+1'b1;
        state<=COMPLETE;
      end
      COMPLETE: begin active_token<=0; state<=IDLE; end
      ABORT_FLUSH: state<=ABORT_DRAIN;
      ABORT_DRAIN: if (memory_drained) begin
        active_token<=0;
        if (cancel_pending) state<=CANCEL_COMPLETE; else state<=COMPLETE;
      end
      CANCEL_COMPLETE: begin cancelled_active<=0; state<=IDLE; end
      default: begin
        failed<=1; sequence_valid<=0; cancel_pending<=0; state<=ABORT_FLUSH;
      end
    endcase
  end
endmodule
