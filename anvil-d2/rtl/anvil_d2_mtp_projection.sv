module anvil_d2_mtp_projection #(
  parameter integer NUM_LAYERS=27, HIDDEN_SIZE=2048,
  parameter integer VOCAB_SIZE=102400, MAX_SEQ_LEN=32768
) (
  input wire clk, rst_n, flush,
  input wire cmd_valid,
  output wire cmd_ready,
  input wire [2:0] cmd_head,
  input wire [31:0] cmd_token, cmd_pos,
  input wire in_valid,
  output wire in_ready,
  input wire signed [31:0] in_hidden,
  output wire out_valid,
  input wire out_ready,
  output wire signed [31:0] out_hidden,
  output wire [31:0] out_index,
  output wire out_last,
  output wire done, error,
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
  generate
    if (NUM_LAYERS<1 || NUM_LAYERS>36 || HIDDEN_SIZE<8 || HIDDEN_SIZE>2048 ||
        (HIDDEN_SIZE & 7)!=0 || VOCAB_SIZE<4 || VOCAB_SIZE>151936 ||
        MAX_SEQ_LEN<1 || MAX_SEQ_LEN>32768) begin: invalid_parameters
      initial $fatal(1,"ANVIL_D2 PARAMETER ERROR: MTP input projection geometry");
      assign cmd_ready=0;
      assign in_ready=0;
      assign out_valid=0;
      assign out_hidden=0;
      assign out_index=0;
      assign out_last=0;
      assign done=0;
      assign error=0;
      assign c_req_valid=0;
      assign c_req_write=0;
      assign c_req_kind=0;
      assign c_req_layer=0;
      assign c_req_proj=0;
      assign c_req_row=0;
      assign c_req_col=0;
      assign c_req_wdata=0;
      assign c_rsp_ready=0;
    end else begin: projection_datapath
      localparam integer HW=$clog2(HIDDEN_SIZE), CW=$clog2(2*HIDDEN_SIZE);
      localparam IDLE=0, FILL=1, HIDDEN_NORM=2, HIDDEN_WAIT=3;
      localparam EMBEDDING_NORM=4, EMBEDDING_WAIT=5, PROJECT=6, PROJECT_WAIT=7;
      localparam OUT_READ=8, OUT_PUBLISH=9, COMPLETE=10, FAULTED=11;
      reg [3:0] state;
      reg armed, failed, local_valid, local_write;
      reg [2:0] head;
      reg [31:0] token, position, component;
      (* ramstyle="M20K", nomem2reg *) reg signed [31:0] hidden [0:HIDDEN_SIZE-1];
      (* ramstyle="M20K", nomem2reg *) reg signed [31:0] normalized [0:2*HIDDEN_SIZE-1];
      (* ramstyle="M20K", nomem2reg *) reg signed [31:0] projected [0:HIDDEN_SIZE-1];
      reg [31:0] local_q;
      reg signed [31:0] projected_q;
      wire enabled=rst_n && armed && !flush;
      wire child_flush=flush || failed;
      wire embedding_stage=state==EMBEDDING_NORM || state==EMBEDDING_WAIT;
      wire projecting=state==PROJECT || state==PROJECT_WAIT;
      wire norm_ready, norm_done, norm_error, tensor_ready, tensor_done, tensor_error;
      wire [1:0] s_req_valid, s_req_ready, s_req_write, s_rsp_valid, s_rsp_ready, s_rsp_error;
      wire [7:0] s_req_kind;
      wire [5:0] s_req_proj;
      wire [63:0] s_req_layer, s_req_row, s_req_col, s_req_wdata, s_rsp_rdata;
      wire raw_valid, raw_ready, raw_write, raw_rsp_valid, raw_rsp_ready, raw_rsp_error;
      wire [3:0] raw_kind;
      wire [2:0] raw_proj;
      wire [31:0] raw_layer, raw_row, raw_col, raw_data, raw_rsp_data;
      wire internal_address=raw_kind==4'd8 && !(embedding_stage && !raw_write);
      wire embedding_address=embedding_stage && raw_kind==4'd8 && !raw_write;
      wire gain_address=!projecting && raw_kind==4'd5;
      wire local_transfer=raw_valid && raw_ready && internal_address;
      wire [31:0] concat_col=embedding_stage ? raw_col+HIDDEN_SIZE : raw_col;
      wire [31:0] local_result=local_write ? 32'd0 : local_q;
      wire child_fault=(norm_done && norm_error) || (tensor_done && tensor_error);

      assign cmd_ready=enabled && state==IDLE;
      assign in_ready=enabled && state==FILL;
      assign out_valid=enabled && state==OUT_PUBLISH;
      assign out_hidden=out_valid ? projected_q : 32'sd0;
      assign out_index=out_valid ? component : 32'd0;
      assign out_last=out_valid && component==HIDDEN_SIZE-1;
      assign done=enabled && state==COMPLETE;
      assign error=done && failed;
      assign raw_ready=enabled && !failed && !local_valid &&
        (internal_address || c_req_ready);
      assign raw_rsp_valid=enabled && !failed && (local_valid || c_rsp_valid);
      assign raw_rsp_data=!raw_rsp_valid ? 32'd0 : local_valid ? local_result : c_rsp_rdata;
      assign raw_rsp_error=raw_rsp_valid && !local_valid && c_rsp_error;
      assign c_req_valid=enabled && !failed && !local_valid && raw_valid && !internal_address;
      assign c_req_write=c_req_valid && raw_write;
      assign c_req_kind=!c_req_valid ? 4'd0 : gain_address ? 4'd12 :
        embedding_address ? 4'd0 : raw_kind;
      assign c_req_layer=!c_req_valid ? 32'd0 : gain_address ? NUM_LAYERS+{29'd0,head} :
        embedding_address ? 32'd0 : raw_layer;
      assign c_req_proj=!c_req_valid ? 3'd0 : gain_address ?
        (embedding_stage ? 3'd2 : 3'd1) : embedding_address ? 3'd0 : raw_proj;
      assign c_req_row=!c_req_valid ? 32'd0 : gain_address ? 32'd0 :
        embedding_address ? token : raw_row;
      assign c_req_col=c_req_valid ? raw_col : 32'd0;
      assign c_req_wdata=c_req_valid ? raw_data : 32'd0;
      assign c_rsp_ready=enabled && !failed && !local_valid && raw_rsp_ready;

      anvil_d1_rmsnorm #(
        .NUM_LAYERS(1),.HIDDEN_SIZE(HIDDEN_SIZE),.MAX_SEQ_LEN(MAX_SEQ_LEN)
      ) normalization (
        .clk(clk),.rst_n(rst_n),.flush(child_flush),
        .cmd_valid(enabled && (state==HIDDEN_NORM || state==EMBEDDING_NORM)),
        .cmd_ready(norm_ready),.cmd_layer(32'd0),.cmd_pos(position),.cmd_mode(2'd0),
        .done(norm_done),.error(norm_error),
        .mem_req_valid(s_req_valid[0]),.mem_req_ready(s_req_ready[0]),
        .mem_req_write(s_req_write[0]),.mem_req_kind(s_req_kind[0+:4]),
        .mem_req_layer(s_req_layer[0+:32]),.mem_req_proj(s_req_proj[0+:3]),
        .mem_req_row(s_req_row[0+:32]),.mem_req_col(s_req_col[0+:32]),
        .mem_req_wdata(s_req_wdata[0+:32]),
        .mem_rsp_valid(s_rsp_valid[0]),.mem_rsp_ready(s_rsp_ready[0]),
        .mem_rsp_rdata(s_rsp_rdata[0+:32]),.mem_rsp_error(s_rsp_error[0])
      );
      anvil_d1_tensor concatenation_projection (
        .clk(clk),.rst_n(rst_n),.flush(child_flush),
        .cmd_valid(enabled && state==PROJECT),.cmd_ready(tensor_ready),
        .cmd_layer(NUM_LAYERS+{29'd0,head}),.cmd_rows(32'(HIDDEN_SIZE)),
        .cmd_cols(32'(2*HIDDEN_SIZE)),.cmd_wide(1'b0),.cmd_bias(1'b0),
        .cmd_head_reduction(1'b0),.cmd_rank(32'd0),
        .cmd_weight_kind(4'd12),.cmd_input_kind(4'd8),.cmd_output_kind(4'd8),
        .cmd_weight_proj(3'd0),.cmd_input_proj(3'd0),.cmd_output_proj(3'd0),
        .cmd_weight_row(32'd0),.cmd_bias_row(32'd0),
        .cmd_input_layer(32'd0),.cmd_input_row(32'd0),.cmd_input_col(32'd0),
        .cmd_output_layer(32'd0),.cmd_output_row(32'd0),.cmd_output_col(32'd0),
        .done(tensor_done),.error(tensor_error),
        .c_req_valid(s_req_valid[1]),.c_req_ready(s_req_ready[1]),
        .c_req_write(s_req_write[1]),.c_req_kind(s_req_kind[4+:4]),
        .c_req_layer(s_req_layer[32+:32]),.c_req_proj(s_req_proj[3+:3]),
        .c_req_row(s_req_row[32+:32]),.c_req_col(s_req_col[32+:32]),
        .c_req_wdata(s_req_wdata[32+:32]),
        .c_rsp_valid(s_rsp_valid[1]),.c_rsp_ready(s_rsp_ready[1]),
        .c_rsp_rdata(s_rsp_rdata[32+:32]),.c_rsp_error(s_rsp_error[1])
      );
      anvil_d1_mem_mux #(.CLIENTS(2)) client_mux (
        .rst_n(rst_n),.flush(child_flush),.select_client(projecting),
        .s_req_valid(s_req_valid),.s_req_ready(s_req_ready),.s_req_write(s_req_write),
        .s_req_kind(s_req_kind),.s_req_layer(s_req_layer),.s_req_proj(s_req_proj),
        .s_req_row(s_req_row),.s_req_col(s_req_col),.s_req_wdata(s_req_wdata),
        .s_rsp_valid(s_rsp_valid),.s_rsp_ready(s_rsp_ready),
        .s_rsp_rdata(s_rsp_rdata),.s_rsp_error(s_rsp_error),
        .c_req_valid(raw_valid),.c_req_ready(raw_ready),.c_req_write(raw_write),
        .c_req_kind(raw_kind),.c_req_layer(raw_layer),.c_req_proj(raw_proj),
        .c_req_row(raw_row),.c_req_col(raw_col),.c_req_wdata(raw_data),
        .c_rsp_valid(raw_rsp_valid),.c_rsp_ready(raw_rsp_ready),
        .c_rsp_rdata(raw_rsp_data),.c_rsp_error(raw_rsp_error)
      );

      always @(posedge clk) begin
        if (enabled && !failed) begin
          if (in_valid && in_ready) hidden[component[HW-1:0]]<=in_hidden;
          if (local_transfer) begin
            if (raw_write) begin
              if (projecting) projected[raw_col[HW-1:0]]<=raw_data;
              else normalized[concat_col[CW-1:0]]<=raw_data;
            end else begin
              if (projecting) local_q<=normalized[raw_col[CW-1:0]];
              else local_q<=hidden[raw_col[HW-1:0]];
            end
          end
          if (state==OUT_READ) projected_q<=projected[component[HW-1:0]];
        end
      end

      always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
          state<=IDLE; armed<=0; failed<=0; local_valid<=0; local_write<=0;
          head<=0; token<=0; position<=0; component<=0;
        end else begin
          armed<=1;
          if (flush) begin
            state<=IDLE; failed<=0; local_valid<=0; local_write<=0; component<=0;
          end else if (!failed && child_fault) begin
            state<=COMPLETE; failed<=1; local_valid<=0;
          end else begin
            if (local_valid && raw_rsp_ready) local_valid<=0;
            if (local_transfer) begin local_valid<=1; local_write<=raw_write; end
            case (state)
              IDLE: if (cmd_valid && cmd_ready) begin
                head<=cmd_head; token<=cmd_token; position<=cmd_pos;
                component<=0; failed<=0;
                if (cmd_head>3 || cmd_token>=VOCAB_SIZE || cmd_pos>=MAX_SEQ_LEN) begin
                  failed<=1; state<=COMPLETE;
                end else state<=FILL;
              end
              FILL: if (in_valid && in_ready) begin
                if (component==HIDDEN_SIZE-1) begin component<=0; state<=HIDDEN_NORM; end
                else component<=component+1'b1;
              end
              HIDDEN_NORM: if (norm_ready) state<=HIDDEN_WAIT;
              HIDDEN_WAIT: if (norm_done) state<=EMBEDDING_NORM;
              EMBEDDING_NORM: if (norm_ready) state<=EMBEDDING_WAIT;
              EMBEDDING_WAIT: if (norm_done) state<=PROJECT;
              PROJECT: if (tensor_ready) state<=PROJECT_WAIT;
              PROJECT_WAIT: if (tensor_done) begin component<=0; state<=OUT_READ; end
              OUT_READ: state<=OUT_PUBLISH;
              OUT_PUBLISH: if (out_valid && out_ready) begin
                if (component==HIDDEN_SIZE-1) state<=COMPLETE;
                else begin component<=component+1'b1; state<=OUT_READ; end
              end
              COMPLETE: if (failed) state<=FAULTED; else state<=IDLE;
              FAULTED: state<=FAULTED;
              default: begin state<=COMPLETE; failed<=1; local_valid<=0; end
            endcase
          end
        end
      end
    end
  endgenerate
endmodule
