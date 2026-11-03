module anvil_q4_fp_token_io #(
  parameter integer TILE_K=128, TILE_ROWS=16
) (
  input wire clk, rst_n, flush, cmd_valid,
  output wire cmd_ready,
  input wire cmd_lmhead,
  input wire [31:0] cmd_token,
  input wire [31:0] hidden, intermediate, kv_heads, head_dim, vocabulary, group_size,
  input wire activation_format,
  output wire done, error,
  output wire logit_valid,
  input wire logit_ready,
  output wire [31:0] logit_index, logit_data,
  output wire [16:0] mem_req_valid,
  input wire [16:0] mem_req_ready,
  output wire [16:0] mem_req_write,
  output wire [67:0] mem_req_kind,
  output wire [543:0] mem_req_layer,
  output wire [50:0] mem_req_proj,
  output wire [543:0] mem_req_row, mem_req_col, mem_req_wdata, mem_req_stride,
  input wire [16:0] mem_rsp_valid,
  output wire [16:0] mem_rsp_ready,
  input wire [543:0] mem_rsp_rdata,
  input wire [16:0] mem_rsp_error
);
  localparam [3:0] IDLE=0, EMBED_READ=1, EMBED_WAIT=2,
    WIDEN=3, WIDEN_WAIT=4, STORE=5, STORE_WAIT=6,
    LMHEAD=7, LMHEAD_WAIT=8, COMPLETE=9, FENCE=10;
  reg [3:0] state;
  reg [31:0] token, index, count, stride, operand, embedding_value;
  reg native_fp16, failed;
  wire lm_owner=state==LMHEAD || state==LMHEAD_WAIT;
  wire embedding_owner=state==EMBED_READ || state==EMBED_WAIT ||
    state==WIDEN || state==WIDEN_WAIT || state==STORE || state==STORE_WAIT;
  wire [33:0] req_valid, req_ready, req_write, rsp_valid, rsp_ready, rsp_error;
  wire [135:0] req_kind;
  wire [101:0] req_proj;
  wire [1087:0] req_layer, req_row, req_col, req_data, req_stride, rsp_data;
  wire routing_idle;
  assign req_valid[0+:16]=0;
  assign req_write[0+:16]=0;
  assign req_kind[0+:64]=0;
  assign req_proj[0+:48]=0;
  assign req_layer[0+:512]=0;
  assign req_row[0+:512]=0;
  assign req_col[0+:512]=0;
  assign req_data[0+:512]=0;
  assign req_stride[0+:512]=0;
  assign rsp_ready[0+:16]=0;
  wire port_idle, complete, fault;
  wire [31:0] rdata;
  wire issue=(state==EMBED_READ || state==STORE) && port_idle;
  anvil_q4_fp_mem_port embedding_port (
    .clk(clk),.rst_n(rst_n),.flush(flush),.issue(issue),
    .idle(port_idle),.complete(complete),.fault(fault),
    .write(state==STORE),.kind(state==STORE ? 4'd8 : 4'd0),
    .layer(32'd0),.proj(3'd0),.row(state==STORE ? 32'd0 : token),
    .col(index),.wdata(state==STORE ? embedding_value : 32'd0),
    .stride(state==STORE ? stride : count),.rdata(rdata),
    .mem_req_valid(req_valid[16]),.mem_req_ready(req_ready[16]),
    .mem_req_write(req_write[16]),.mem_req_kind(req_kind[64+:4]),
    .mem_req_layer(req_layer[512+:32]),.mem_req_proj(req_proj[48+:3]),
    .mem_req_row(req_row[512+:32]),.mem_req_col(req_col[512+:32]),
    .mem_req_wdata(req_data[512+:32]),.mem_req_stride(req_stride[512+:32]),
    .mem_rsp_valid(rsp_valid[16]),.mem_rsp_ready(rsp_ready[16]),
    .mem_rsp_rdata(rsp_data[512+:32]),.mem_rsp_error(rsp_error[16])
  );
  wire gemv_ready, gemv_done, gemv_error;
  anvil_q4_fp_gemv #(.TILE_K(TILE_K),.TILE_ROWS(TILE_ROWS)) lm_head (
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .cmd_valid(state==LMHEAD),.cmd_ready(gemv_ready),
    .cmd_layer(32'd0),.cmd_proj(3'd0),.cmd_lmhead(1'b1),
    .hidden(hidden),.intermediate(intermediate),.kv_heads(kv_heads),.head_dim(head_dim),
    .vocabulary(vocabulary),.group_size(group_size),.activation_format(activation_format),
    .activation_a8(1'b0),.weight_asymmetric(1'b0),.qkv_bias(1'b0),.weight_format(2'd0),
    .done(gemv_done),.error(gemv_error),.result_valid(logit_valid),
    .result_ready(logit_ready),.result_index(logit_index),.result_data(logit_data),
    .mem_req_valid(req_valid[17+:17]),.mem_req_ready(req_ready[17+:17]),
    .mem_req_write(req_write[17+:17]),.mem_req_kind(req_kind[68+:68]),
    .mem_req_layer(req_layer[544+:544]),.mem_req_proj(req_proj[51+:51]),
    .mem_req_row(req_row[544+:544]),.mem_req_col(req_col[544+:544]),
    .mem_req_wdata(req_data[544+:544]),.mem_req_stride(req_stride[544+:544]),
    .mem_rsp_valid(rsp_valid[17+:17]),.mem_rsp_ready(rsp_ready[17+:17]),
    .mem_rsp_rdata(rsp_data[544+:544]),.mem_rsp_error(rsp_error[17+:17])
  );
  wire fp_ready, fp_valid;
  wire [31:0] fp_result;
  wire [4:0] fp_flags;
  anvil_q4_fp32 arithmetic (
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .in_valid(state==WIDEN),.in_ready(fp_ready),
    .op(native_fp16 ? 4'd6 : 4'd5),.a(operand),.b(32'd0),
    .out_valid(fp_valid),.out_ready(state==WIDEN_WAIT),
    .result(fp_result),.flags(fp_flags)
  );
  anvil_q4_fp_channel_mux #(.CLIENTS(2)) routing (
    .clk(clk),.rst_n(rst_n),.flush(flush),.idle(routing_idle),
    .c_req_valid(req_valid),.c_req_ready(req_ready),.c_req_write(req_write),
    .c_req_kind(req_kind),.c_req_layer(req_layer),.c_req_proj(req_proj),
    .c_req_row(req_row),.c_req_col(req_col),.c_req_wdata(req_data),.c_req_stride(req_stride),
    .c_rsp_valid(rsp_valid),.c_rsp_ready(rsp_ready),.c_rsp_rdata(rsp_data),.c_rsp_error(rsp_error),
    .mem_req_valid(mem_req_valid),.mem_req_ready(mem_req_ready),.mem_req_write(mem_req_write),
    .mem_req_kind(mem_req_kind),.mem_req_layer(mem_req_layer),.mem_req_proj(mem_req_proj),
    .mem_req_row(mem_req_row),.mem_req_col(mem_req_col),.mem_req_wdata(mem_req_wdata),
    .mem_req_stride(mem_req_stride),.mem_rsp_valid(mem_rsp_valid),
    .mem_rsp_ready(mem_rsp_ready),.mem_rsp_rdata(mem_rsp_rdata),.mem_rsp_error(mem_rsp_error)
  );
  assign cmd_ready=rst_n && !flush && state==IDLE;
  assign done=rst_n && !flush && state==COMPLETE;
  assign error=done && failed;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; token<=0; index<=0; count<=0; stride<=0;
      operand<=0; embedding_value<=0; native_fp16<=0; failed<=0;
    end else if (flush) begin state<=IDLE; failed<=0; end
    else if (fault) begin failed<=1; state<=FENCE; end
    else case (state)
      IDLE: if (cmd_valid) begin
        token<=cmd_token; index<=0; count<=hidden;
        stride<=hidden>intermediate ? hidden : intermediate;
        native_fp16<=activation_format; failed<=0;
        if (hidden<2 || hidden>8192 || intermediate<1 || intermediate>32768 ||
            vocabulary==0 || vocabulary>262144 || (!cmd_lmhead && cmd_token>=vocabulary)) begin
          failed<=1; state<=COMPLETE;
        end else if (cmd_lmhead) state<=LMHEAD;
        else state<=EMBED_READ;
      end
      EMBED_READ: if (issue) state<=EMBED_WAIT;
      EMBED_WAIT: if (complete) begin
        if (rdata[31:16]!=0) begin failed<=1; state<=FENCE; end
        else begin operand<=rdata; state<=WIDEN; end
      end
      WIDEN: if (fp_ready) state<=WIDEN_WAIT;
      WIDEN_WAIT: if (fp_valid) begin embedding_value<=fp_result; state<=STORE; end
      STORE: if (issue) state<=STORE_WAIT;
      STORE_WAIT: if (complete) begin
        if (index+1<count) begin index<=index+1'b1; state<=EMBED_READ; end
        else state<=FENCE;
      end
      LMHEAD: if (gemv_ready) state<=LMHEAD_WAIT;
      LMHEAD_WAIT: if (gemv_done) begin failed<=gemv_error; state<=FENCE; end
      FENCE: if (routing_idle) state<=COMPLETE;
      COMPLETE: state<=IDLE;
      default: begin failed<=1; state<=COMPLETE; end
    endcase
  end
endmodule
