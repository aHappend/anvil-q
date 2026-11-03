module anvil_q4_token_io #(
  parameter integer TILE_K=128, TILE_ROWS=8
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
  output wire mem_req_valid,
  input wire mem_req_ready,
  output wire mem_req_write,
  output wire [3:0] mem_req_kind,
  output wire [31:0] mem_req_layer,
  output wire [2:0] mem_req_proj,
  output wire [31:0] mem_req_row, mem_req_col, mem_req_wdata, mem_req_stride,
  input wire mem_rsp_valid,
  output wire mem_rsp_ready,
  input wire [31:0] mem_rsp_rdata,
  input wire mem_rsp_error
);
  localparam [3:0] IDLE=0, EMBED_READ=1, EMBED_WAIT=2,
    WIDEN=3, WIDEN_WAIT=4, STORE=5, STORE_WAIT=6,
    LMHEAD=7, LMHEAD_WAIT=8, COMPLETE=9;
  reg [3:0] state;
  reg [31:0] token, index, count, stride, operand, embedding_value;
  reg native_fp16, failed;
  wire lm_owner=state==LMHEAD || state==LMHEAD_WAIT;
  wire embedding_owner=state==EMBED_READ || state==EMBED_WAIT ||
    state==WIDEN || state==WIDEN_WAIT || state==STORE || state==STORE_WAIT;
  wire [1:0] req_valid, req_ready, req_write, rsp_valid, rsp_ready;
  wire [7:0] req_kind;
  wire [5:0] req_proj;
  wire [63:0] req_layer, req_row, req_col, req_data, req_stride;
  wire port_idle, complete, fault;
  wire [31:0] rdata;
  wire issue=(state==EMBED_READ || state==STORE) && port_idle;
  anvil_q4_mem_port embedding_port (
    .clk(clk),.rst_n(rst_n),.flush(flush),.issue(issue),
    .idle(port_idle),.complete(complete),.fault(fault),
    .write(state==STORE),.kind(state==STORE ? 4'd8 : 4'd0),
    .layer(32'd0),.proj(3'd0),.row(state==STORE ? 32'd0 : token),
    .col(index),.wdata(state==STORE ? embedding_value : 32'd0),
    .stride(state==STORE ? stride : count),.rdata(rdata),
    .mem_req_valid(req_valid[0]),.mem_req_ready(req_ready[0]),
    .mem_req_write(req_write[0]),.mem_req_kind(req_kind[0+:4]),
    .mem_req_layer(req_layer[0+:32]),.mem_req_proj(req_proj[0+:3]),
    .mem_req_row(req_row[0+:32]),.mem_req_col(req_col[0+:32]),
    .mem_req_wdata(req_data[0+:32]),.mem_req_stride(req_stride[0+:32]),
    .mem_rsp_valid(rsp_valid[0]),.mem_rsp_ready(rsp_ready[0]),
    .mem_rsp_rdata(mem_rsp_rdata),.mem_rsp_error(mem_rsp_error)
  );
  wire gemv_ready, gemv_done, gemv_error;
  anvil_q4_gemv #(.TILE_K(TILE_K),.TILE_ROWS(TILE_ROWS)) lm_head (
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .cmd_valid(state==LMHEAD),.cmd_ready(gemv_ready),
    .cmd_layer(32'd0),.cmd_proj(3'd0),.cmd_lmhead(1'b1),
    .hidden(hidden),.intermediate(intermediate),.kv_heads(kv_heads),.head_dim(head_dim),
    .vocabulary(vocabulary),.group_size(group_size),.activation_format(activation_format),
    .activation_a8(1'b0),.weight_asymmetric(1'b0),.qkv_bias(1'b0),.weight_format(2'd0),
    .done(gemv_done),.error(gemv_error),.result_valid(logit_valid),
    .result_ready(logit_ready),.result_index(logit_index),.result_data(logit_data),
    .mem_req_valid(req_valid[1]),.mem_req_ready(req_ready[1]),
    .mem_req_write(req_write[1]),.mem_req_kind(req_kind[4+:4]),
    .mem_req_layer(req_layer[32+:32]),.mem_req_proj(req_proj[3+:3]),
    .mem_req_row(req_row[32+:32]),.mem_req_col(req_col[32+:32]),
    .mem_req_wdata(req_data[32+:32]),.mem_req_stride(req_stride[32+:32]),
    .mem_rsp_valid(rsp_valid[1]),.mem_rsp_ready(rsp_ready[1]),
    .mem_rsp_rdata(mem_rsp_rdata),.mem_rsp_error(mem_rsp_error)
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
  wire owner=lm_owner;
  wire enabled=rst_n && !flush && (embedding_owner || lm_owner);
  assign req_ready[0]=enabled && embedding_owner && mem_req_ready;
  assign req_ready[1]=enabled && lm_owner && mem_req_ready;
  assign rsp_valid[0]=enabled && embedding_owner && mem_rsp_valid;
  assign rsp_valid[1]=enabled && lm_owner && mem_rsp_valid;
  assign mem_req_valid=enabled && req_valid[owner];
  assign mem_req_write=mem_req_valid && req_write[owner];
  assign mem_req_kind=mem_req_valid ? req_kind[owner*4+:4] : 4'd0;
  assign mem_req_layer=mem_req_valid ? req_layer[owner*32+:32] : 32'd0;
  assign mem_req_proj=mem_req_valid ? req_proj[owner*3+:3] : 3'd0;
  assign mem_req_row=mem_req_valid ? req_row[owner*32+:32] : 32'd0;
  assign mem_req_col=mem_req_valid ? req_col[owner*32+:32] : 32'd0;
  assign mem_req_wdata=mem_req_valid ? req_data[owner*32+:32] : 32'd0;
  assign mem_req_stride=mem_req_valid ? req_stride[owner*32+:32] : 32'd0;
  assign mem_rsp_ready=enabled && rsp_ready[owner];
  assign cmd_ready=rst_n && !flush && state==IDLE;
  assign done=rst_n && !flush && state==COMPLETE;
  assign error=done && failed;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; token<=0; index<=0; count<=0; stride<=0;
      operand<=0; embedding_value<=0; native_fp16<=0; failed<=0;
    end else if (flush) begin state<=IDLE; failed<=0; end
    else if (fault) begin failed<=1; state<=COMPLETE; end
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
        if (rdata[31:16]!=0) begin failed<=1; state<=COMPLETE; end
        else begin operand<=rdata; state<=WIDEN; end
      end
      WIDEN: if (fp_ready) state<=WIDEN_WAIT;
      WIDEN_WAIT: if (fp_valid) begin embedding_value<=fp_result; state<=STORE; end
      STORE: if (issue) state<=STORE_WAIT;
      STORE_WAIT: if (complete) begin
        if (index+1<count) begin index<=index+1'b1; state<=EMBED_READ; end
        else state<=COMPLETE;
      end
      LMHEAD: if (gemv_ready) state<=LMHEAD_WAIT;
      LMHEAD_WAIT: if (gemv_done) begin failed<=gemv_error; state<=COMPLETE; end
      COMPLETE: state<=IDLE;
      default: begin failed<=1; state<=COMPLETE; end
    endcase
  end
endmodule
