module anvil_q1_fp2_kv_reader #(
  parameter HEAD_DIM=64, MAX_SEQ_LEN=32768
) (
  input wire clk, rst_n, cmd_valid,
  output wire cmd_ready,
  input wire cmd_format_mx,
  input wire [31:0] cmd_layer, cmd_first, cmd_len,
  output wire kv_valid,
  input wire kv_ready,
  output wire [15:0] k_data, v_data,
  output wire kv_last,
  output wire [4:0] status,
  output wire done, error, work_active, result_needed,
  output wire fetch_valid,
  input wire fetch_ready,
  output wire fetch_scale,
  output wire [3:0] fetch_kind,
  output wire [31:0] fetch_layer,
  output wire [2:0] fetch_proj,
  output wire [31:0] fetch_row, fetch_col, fetch_tag,
  input wire response_valid,
  output wire response_ready,
  input wire [31:0] response_tag,
  input wire response_write, response_error,
  input wire [511:0] response_data
);
  localparam IDLE=0, START_K=1, LOAD_K=2, WAIT_K=3, START_V=4;
  localparam READ_KEY=5, PAIR=6, WAIT_V=7, COMPLETE_WAIT=8;
  localparam ERROR_WAIT0=9, ERROR_WAIT1=10, FINISH=11;
  localparam ADDRESS_BITS=HEAD_DIM>1 ? $clog2(HEAD_DIM) : 1;
  reg [3:0] state;
  reg format_mx, failed;
  reg [31:0] layer, first, length, token, component;
  reg [4:0] flags;
  (* ramstyle = "M20K", nomem2reg *) reg [15:0] key_vector [0:HEAD_DIM-1];
  reg [15:0] key_q;
  wire reader_ready, reader_valid, reader_last, reader_done, reader_error;
  wire [15:0] reader_data;
  wire [4:0] reader_status;
  wire reader_transfer=reader_valid && reader_out_ready;
  wire reader_out_ready=rst_n &&
    (state==LOAD_K || (state==PAIR && kv_ready));
  wire [32:0] command_end={1'b0,cmd_first}+33'(HEAD_DIM);
  generate if (HEAD_DIM<1 || MAX_SEQ_LEN<1 ||
      128'(HEAD_DIM)>32'hffffffff || 128'(MAX_SEQ_LEN)>32'hffffffff) begin: invalid_parameters
    initial $fatal(1,"FP2 KV READER PARAMETER ERROR");
  end endgenerate
  anvil_q1_fp2_ddr_read_stream vector_reader (
    .clk(clk),.rst_n(rst_n),
    .cmd_valid(rst_n && (state==START_K || state==START_V)),
    .cmd_ready(reader_ready),.cmd_format_mx(format_mx),
    .cmd_kind(state==START_K ? 4'd9 : 4'd10),
    .cmd_layer(layer),.cmd_proj(3'd0),.cmd_row(token),
    .cmd_first(first),.cmd_len(32'(HEAD_DIM)),
    .out_valid(reader_valid),.out_ready(reader_out_ready),
    .out_data(reader_data),.out_last(reader_last),.status(reader_status),
    .done(reader_done),.error(reader_error),
    .work_active(work_active),.result_needed(result_needed),
    .fetch_valid(fetch_valid),.fetch_ready(fetch_ready),.fetch_scale(fetch_scale),
    .fetch_kind(fetch_kind),.fetch_layer(fetch_layer),.fetch_proj(fetch_proj),
    .fetch_row(fetch_row),.fetch_col(fetch_col),.fetch_tag(fetch_tag),
    .response_valid(response_valid),.response_ready(response_ready),
    .response_tag(response_tag),.response_write(response_write),
    .response_error(response_error),.response_data(response_data));
  assign cmd_ready=rst_n && state==IDLE;
  assign kv_valid=rst_n && state==PAIR && reader_valid;
  assign k_data=kv_valid ? key_q : 16'd0;
  assign v_data=kv_valid ? reader_data : 16'd0;
  assign kv_last=kv_valid && component+1==HEAD_DIM;
  assign done=rst_n && state==FINISH;
  assign error=done && failed;
  assign status=rst_n && (kv_valid || done) ?
    (kv_valid ? flags | reader_status : flags) : 5'd0;
  always @(posedge clk) begin
    if (reader_transfer && state==LOAD_K)
      key_vector[component[ADDRESS_BITS-1:0]]<=reader_data;
    key_q<=key_vector[component[ADDRESS_BITS-1:0]];
  end
  always @(posedge clk) begin
    if (!rst_n) begin
      state<=IDLE; format_mx<=0; failed<=0; layer<=0; first<=0;
      length<=0; token<=0; component<=0; flags<=0;
    end else if (reader_done && reader_error) begin
      flags<=flags | reader_status; failed<=1; state<=ERROR_WAIT0;
    end else begin
      if (reader_transfer || reader_done) flags<=flags | reader_status;
      case (state)
        IDLE: if (cmd_valid) begin
          format_mx<=cmd_format_mx; layer<=cmd_layer; first<=cmd_first;
          length<=cmd_len; token<=0; component<=0; flags<=0; failed<=0;
          if (cmd_len==0 || cmd_len>MAX_SEQ_LEN ||
              command_end>33'h100000000) begin
            failed<=1; state<=ERROR_WAIT0;
          end else state<=START_K;
        end
        START_K: if (reader_ready) state<=LOAD_K;
        LOAD_K: if (reader_transfer) begin
          if (reader_last) begin component<=0; state<=WAIT_K; end
          else component<=component+1'b1;
        end
        WAIT_K: if (reader_done) state<=START_V;
        START_V: if (reader_ready) state<=READ_KEY;
        READ_KEY: state<=PAIR;
        PAIR: if (reader_transfer) begin
          if (reader_last) begin component<=0; state<=WAIT_V; end
          else begin component<=component+1'b1; state<=READ_KEY; end
        end
        WAIT_V: if (reader_done) begin
          if (token+1==length) state<=COMPLETE_WAIT;
          else begin token<=token+1'b1; state<=START_K; end
        end
        COMPLETE_WAIT: state<=FINISH;
        ERROR_WAIT0: state<=ERROR_WAIT1;
        ERROR_WAIT1: state<=FINISH;
        FINISH: state<=IDLE;
        default: begin failed<=1; state<=ERROR_WAIT0; end
      endcase
    end
  end
endmodule
