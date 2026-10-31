module anvil_q2_ht2_tensor_engine #(
  parameter MAX_WORDS=8960, VECTOR_COUNT=16, GROUP_SIZE=128
) (
  input wire clk, rst_n, annul,
  input wire s_valid,
  output wire s_ready,
  input wire [511:0] s_descriptor,
  input wire [31:0] s_vector, s_first_row, s_row_count,
  input wire [3:0] s_token_mask,
  input wire s_fp16, s_sparse,
  input wire [1:0] s_weight_mode,
  input wire [63:0] s_tag,
  input wire w_valid,
  output wire w_ready,
  input wire [1:0] w_slot,
  input wire [31:0] w_vector, w_tile,
  input wire [2047:0] w_data,
  input wire [127:0] w_keep,
  output wire w_rsp_valid, w_rsp_error,
  input wire w_rsp_ready,
  output wire m_valid,
  input wire m_ready,
  output wire m_error, m_last,
  output wire [31:0] m_row,
  output wire [3:0] m_token_mask,
  output wire [127:0] m_sum,
  output wire [63:0] m_tag,
  output wire idle, fault,
  output wire mem_valid,
  input wire mem_ready,
  output wire [32:0] mem_address,
  output wire [6:0] mem_beats,
  input wire fill_valid, fill_error, fill_last,
  input wire [511:0] fill_data,
  output wire fill_ready
);
  localparam LEGAL=MAX_WORDS>=8 && MAX_WORDS<=8960 && (MAX_WORDS & 7)==0 &&
    VECTOR_COUNT>=1 && VECTOR_COUNT<=32 &&
    GROUP_SIZE>=1 && GROUP_SIZE<=128 && (GROUP_SIZE & (GROUP_SIZE-1))==0 &&
    (MAX_WORDS & (GROUP_SIZE-1))==0;
  generate if (!LEGAL) begin: invalid_parameters
    initial $fatal(1,"ANVIL_Q2_HT2 PARAMETER ERROR: tensor engine geometry");
    assign s_ready=0; assign w_ready=0; assign w_rsp_valid=0;
    assign w_rsp_error=0; assign m_valid=0; assign m_error=0;
    assign m_last=0; assign m_row=0; assign m_token_mask=0;
    assign m_sum=0; assign m_tag=0; assign idle=0; assign fault=0;
    assign mem_valid=0; assign mem_address=0; assign mem_beats=0;
    assign fill_ready=0;
  end else begin: implementation
    localparam [3:0] IDLE=0, VALIDATE=1, ACTIVATION_SEND=2,
      ACTIVATION_WAIT=3, WEIGHT_SEND=4, WEIGHT_WAIT=5, MAC_WAIT=6,
      ROW_WAIT=7, RESPONSE=8, FLUSH=9, FAULT_DRAIN=10;
    reg [3:0] state;
    reg [511:0] descriptor;
    reg [31:0] vector_id, row, rows_left, column;
    reg [3:0] tokens;
    reg fp16, sparse;
    reg [1:0] weight_mode;
    reg [63:0] tag;
    reg [8191:0] activations;
    reg [511:0] activation_keep;
    reg response_error, response_last, sticky_fault;
    reg [127:0] response_sum;
    wire available;
    wire arithmetic_annul;
    wire weight_annul;
    wire [31:0] columns=descriptor[288+:32];
    wire [31:0] flags=descriptor[416+:32];
    wire [31:0] expected_flags=weight_mode==0 ?
      (fp16 ? 32'h102 : 32'h101) :
      (weight_mode==1 ? 32'h100 : 32'h103);
    wire [1:0] expected_format=weight_mode==0 ? (fp16 ? 2'd1 : 2'd0) :
      (weight_mode==1 ? 2'd2 : 2'd3);
    wire [32:0] row_end={1'b0,row}+{1'b0,rows_left};
    wire command_bad=vector_id>=VECTOR_COUNT || tokens==0 ||
      rows_left==0 || descriptor[256+:32]==0 || descriptor[256+:32]>151936 ||
      row_end>{1'b0,descriptor[256+:32]} ||
      columns<8 || columns>MAX_WORDS || (columns & 7)!=0 ||
      (columns & (GROUP_SIZE-1))!=0 || weight_mode==3 ||
      flags!=expected_flags;
    wire final_tile={1'b0,column}+33'd128>={1'b0,columns};
    reg [511:0] requested_keep;
    integer t, j;
    wire store_w_ready, store_w_valid, store_w_error;
    wire store_r_ready, store_m_valid, store_m_error;
    wire [8191:0] store_data;
    wire [511:0] store_keep;
    wire [63:0] store_tag;
    wire weight_ready, weight_valid, weight_error, weight_idle, weight_fault;
    assign available=rst_n && !annul && !weight_fault;
    assign arithmetic_annul=annul || state==FLUSH ||
      state==FAULT_DRAIN || weight_fault;
    assign weight_annul=annul || state==FLUSH || weight_fault;
    wire [1:0] weight_format;
    wire [3:0] weight_tokens;
    wire [8191:0] weight_activations;
    wire [2047:0] weights;
    wire [511:0] weight_keep;
    wire [63:0] weight_tag;
    wire bad_weight=weight_error || weight_format!=expected_format ||
      weight_tag!=tag || weight_tokens!=tokens;
    wire mac_ready, mac_valid, mac_error;
    wire [127:0] mac_sum;
    wire [63:0] mac_tag;
    wire [3:0] mac_tokens;
    wire accumulator_ready, accumulator_valid, accumulator_error;
    wire [31:0] accumulator_row;
    wire [3:0] accumulator_tokens;
    wire [127:0] accumulator_sum;
    wire [63:0] accumulator_tag;
    wire write_allowed=available && state==IDLE && weight_idle;
    wire command_transfer=s_valid && s_ready;

    always @* begin
      requested_keep=0;
      for (t=0;t<4;t=t+1)
        for (j=0;j<128;j=j+1)
          requested_keep[128*t+j]=tokens[t] &&
            ({1'b0,column}+33'(j)<{1'b0,columns});
    end

    anvil_q2_ht2_activation_store #(
      .MAX_WORDS(MAX_WORDS),.VECTOR_COUNT(VECTOR_COUNT)
    ) activation_storage (
      .clk(clk),.rst_n(rst_n),.annul(annul),
      .w_valid(w_valid && write_allowed),.w_ready(store_w_ready),
      .w_rsp_ready(w_rsp_ready),.w_slot(w_slot),.w_vector(w_vector),
      .w_tile(w_tile),.w_data(w_data),.w_keep(w_keep),
      .w_rsp_valid(store_w_valid),.w_rsp_error(store_w_error),
      .r_valid(available && state==ACTIVATION_SEND),.r_ready(store_r_ready),
      .r_vector(vector_id),.r_tile(column >> 7),.r_token_mask(tokens),
      .r_keep(requested_keep),.r_tag(tag),
      .m_ready(rst_n && !annul &&
        ((available && state==ACTIVATION_WAIT) || state==FAULT_DRAIN || state==FLUSH)),
      .m_valid(store_m_valid),.m_error(store_m_error),
      .m_data(store_data),.m_keep(store_keep),.m_tag(store_tag)
    );
    anvil_q2_ht2_weight_path #(.GROUP_SIZE(GROUP_SIZE)) weight_path (
      .clk(clk),.rst_n(rst_n),.annul(weight_annul),
      .s_valid(available && state==WEIGHT_SEND),.s_ready(weight_ready),
      .s_descriptor(descriptor),.s_row(row),.s_col(column),
      .s_sparse(sparse),.s_token_mask(tokens),.s_act(activations),
      .s_keep(activation_keep),.s_tag(tag),
      .m_valid(weight_valid),
      .m_ready(available && state==WEIGHT_WAIT && (bad_weight || mac_ready)),
      .m_error(weight_error),.m_skipped(),.m_format(weight_format),
      .m_token_mask(weight_tokens),.m_act(weight_activations),
      .m_weight(weights),.m_keep(weight_keep),.m_tag(weight_tag),
      .idle(weight_idle),.fault(weight_fault),
      .mem_valid(mem_valid),.mem_ready(mem_ready),
      .mem_address(mem_address),.mem_beats(mem_beats),
      .fill_valid(fill_valid),.fill_error(fill_error),.fill_last(fill_last),
      .fill_data(fill_data),.fill_ready(fill_ready)
    );
    anvil_q2_ht2_tile_batch_mac array (
      .clk(clk),.rst_n(rst_n),.annul(arithmetic_annul),
      .s_valid(available && state==WEIGHT_WAIT && weight_valid && !bad_weight),
      .s_ready(mac_ready),.s_fp16(fp16),
      .s_weight_fp16(weight_format==2'd1),
      .s_token_mask(weight_tokens),.s_keep(weight_keep),
      .s_act(weight_activations),.s_weight(weights),
      .s_bias(128'd0),.s_tag(weight_tag),
      .m_valid(mac_valid),
      .m_ready(available && state==MAC_WAIT && accumulator_ready),
      .m_error(mac_error),.m_sum(mac_sum),.m_tag(mac_tag),
      .m_token_mask(mac_tokens)
    );
    anvil_q2_ht2_row_accumulator row_accumulator (
      .clk(clk),.rst_n(rst_n),.annul(arithmetic_annul),
      .s_valid(available && state==MAC_WAIT && mac_valid),
      .s_ready(accumulator_ready),.s_first(column==0),.s_last(final_tile),
      .s_error(mac_error || mac_tag!=tag || mac_tokens!=tokens),
      .s_row(row),.s_column_tile(column >> 7),
      .s_token_mask(tokens),.s_sum(mac_sum),.s_tag(tag),
      .m_valid(accumulator_valid),.m_ready(available && state==ROW_WAIT),
      .m_error(accumulator_error),.m_row(accumulator_row),
      .m_token_mask(accumulator_tokens),.m_sum(accumulator_sum),
      .m_tag(accumulator_tag)
    );

    assign s_ready=available && state==IDLE && weight_idle && !w_valid &&
      (!store_w_valid || w_rsp_ready);
    assign w_ready=write_allowed && store_w_ready;
    assign w_rsp_valid=store_w_valid;
    assign w_rsp_error=store_w_error;
    assign m_valid=available && state==RESPONSE;
    assign m_error=m_valid && response_error;
    assign m_last=m_valid && response_last;
    assign m_row=m_valid ? row : 32'd0;
    assign m_token_mask=m_valid ? tokens : 4'd0;
    assign m_sum=m_valid && !response_error ? response_sum : 128'd0;
    assign m_tag=m_valid ? tag : 64'd0;
    assign idle=available && state==IDLE && weight_idle && !store_w_valid;
    assign fault=rst_n && sticky_fault;

    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        state<=IDLE; descriptor<=0; vector_id<=0; row<=0; rows_left<=0;
        column<=0; tokens<=0; fp16<=0; sparse<=0; weight_mode<=0;
        tag<=0; activations<=0; activation_keep<=0;
        response_error<=0; response_last<=0; response_sum<=0; sticky_fault<=0;
      end else if (annul) begin
        state<=IDLE; response_error<=0; response_last<=0; response_sum<=0;
      end else begin
        if (weight_fault) sticky_fault<=1;
        if (weight_fault && state!=IDLE && state!=FAULT_DRAIN) begin
          state<=FAULT_DRAIN;
        end else case (state)
          IDLE: if (command_transfer) begin
            descriptor<=s_descriptor; vector_id<=s_vector; row<=s_first_row;
            rows_left<=s_row_count; column<=0; tokens<=s_token_mask;
            fp16<=s_fp16; sparse<=s_sparse; weight_mode<=s_weight_mode;
            tag<=s_tag; response_error<=0; response_last<=0;
            response_sum<=0; state<=VALIDATE;
          end
          VALIDATE: begin
            if (command_bad) state<=FLUSH;
            else state<=ACTIVATION_SEND;
          end
          ACTIVATION_SEND: if (store_r_ready) state<=ACTIVATION_WAIT;
          ACTIVATION_WAIT: if (store_m_valid) begin
            if (store_m_error || store_tag!=tag) state<=FLUSH;
            else begin
              activations<=store_data; activation_keep<=store_keep;
              state<=WEIGHT_SEND;
            end
          end
          WEIGHT_SEND: if (weight_ready) state<=WEIGHT_WAIT;
          WEIGHT_WAIT: if (weight_valid && (bad_weight || mac_ready)) begin
            if (bad_weight) state<=FLUSH;
            else state<=MAC_WAIT;
          end
          MAC_WAIT: if (mac_valid && accumulator_ready) state<=ROW_WAIT;
          ROW_WAIT: begin
            if (accumulator_valid) begin
              if (accumulator_error || accumulator_row!=row ||
                  accumulator_tokens!=tokens || accumulator_tag!=tag)
                state<=FLUSH;
              else begin
                response_sum<=accumulator_sum; response_error<=0;
                response_last<=rows_left==1; state<=RESPONSE;
              end
            end else if (!final_tile && accumulator_ready) begin
              column<=column+32'd128; state<=ACTIVATION_SEND;
            end
          end
          FLUSH: begin
            response_error<=1; response_last<=1; response_sum<=0;
            sticky_fault<=1; state<=RESPONSE;
          end
          FAULT_DRAIN: if (weight_idle) state<=FLUSH;
          RESPONSE: if (m_ready) begin
            if (response_last) state<=IDLE;
            else begin
              row<=row+32'd1; rows_left<=rows_left-32'd1;
              column<=0; state<=ACTIVATION_SEND;
            end
          end
          default: state<=FLUSH;
        endcase
      end
    end
  end endgenerate
endmodule
