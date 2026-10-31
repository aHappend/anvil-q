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
  input wire r_valid,
  output wire r_ready,
  input wire [31:0] r_vector, r_tile,
  input wire [3:0] r_token_mask,
  input wire [511:0] r_keep,
  input wire [63:0] r_tag,
  output wire r_rsp_valid, r_rsp_error,
  input wire r_rsp_ready,
  output wire [8191:0] r_data,
  output wire [511:0] r_rsp_keep,
  output wire [63:0] r_rsp_tag,
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
    assign r_ready=0; assign r_rsp_valid=0; assign r_rsp_error=0;
    assign r_data=0; assign r_rsp_keep=0; assign r_rsp_tag=0;
    assign w_rsp_error=0; assign m_valid=0; assign m_error=0;
    assign m_last=0; assign m_row=0; assign m_token_mask=0;
    assign m_sum=0; assign m_tag=0; assign idle=0; assign fault=0;
    assign mem_valid=0; assign mem_address=0; assign mem_beats=0;
    assign fill_ready=0;
  end else begin: implementation
    localparam [3:0] IDLE=0, VALIDATE=1, ACTIVATION_SEND=2, WAIT_COMPLETE=6,
      RESPONSE=8, FLUSH=9, FAULT_DRAIN=10;
    reg [3:0] state;
    reg [511:0] descriptor;
    reg [31:0] vector_id, row, rows_left, column, last_row;
    reg [3:0] tokens;
    reg fp16, sparse;
    reg [1:0] weight_mode;
    reg [63:0] tag;
    reg response_error, response_last, sticky_fault;
    reg external_read;
    reg [31:0] issued_row [0:63], issued_column [0:63];
    reg [5:0] issue_head, issue_tail;
    reg [6:0] issue_count;
    reg [31:0] prefetched_row [0:7], prefetched_column [0:7];
    reg [2:0] prefetch_head, prefetch_tail;
    reg [3:0] prefetch_count;
    reg [31:0] activation_row [0:3], activation_column [0:3];
    reg [1:0] activation_head, activation_tail;
    reg [2:0] activation_count;
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
    wire write_allowed=available && state==IDLE && weight_idle && !external_read;
    wire read_allowed=write_allowed && !w_valid &&
      (!store_w_valid || w_rsp_ready);
    wire external_read_transfer=r_valid && r_ready;
    wire command_transfer=s_valid && s_ready;
    wire executing=available && state!=IDLE && state!=VALIDATE &&
      state!=FLUSH && state!=FAULT_DRAIN && state!=RESPONSE;
    wire accumulate=executing && mac_valid && issue_count!=0 && accumulator_ready;
    wire issue_space=issue_count<64 || accumulate;
    wire issue=executing && weight_valid && prefetch_count!=0 &&
      !bad_weight && mac_ready && issue_space;
    wire prefetch_space=prefetch_count<8 || issue;
    wire bad_activation=store_m_error || store_tag!=tag;
    wire activation_request=available && state==ACTIVATION_SEND &&
      activation_count<4 && store_r_ready;
    wire submit=executing && store_m_valid && activation_count!=0 &&
      !bad_activation && weight_ready && prefetch_space;
    wire bad_accumulator=accumulator_error || accumulator_tokens!=tokens ||
      accumulator_tag!=tag;
    wire row_transfer=m_valid && m_ready && state!=RESPONSE;
    integer q;

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
      .r_valid((available && state==ACTIVATION_SEND && activation_count<4) ||
        (read_allowed && r_valid)),
      .r_ready(store_r_ready),
      .r_vector(state==IDLE ? r_vector : vector_id),
      .r_tile(state==IDLE ? r_tile : (column >> 7)),
      .r_token_mask(state==IDLE ? r_token_mask : tokens),
      .r_keep(state==IDLE ? r_keep : requested_keep),
      .r_tag(state==IDLE ? r_tag : tag),
      .m_ready(rst_n && !annul &&
        ((executing && activation_count!=0 &&
            (bad_activation || (weight_ready && prefetch_space))) ||
          (external_read && r_rsp_ready) || state==FAULT_DRAIN || state==FLUSH)),
      .m_valid(store_m_valid),.m_error(store_m_error),
      .m_data(store_data),.m_keep(store_keep),.m_tag(store_tag)
    );
    anvil_q2_ht2_weight_path #(.GROUP_SIZE(GROUP_SIZE)) weight_path (
      .clk(clk),.rst_n(rst_n),.annul(weight_annul),
      .s_valid(executing && store_m_valid && activation_count!=0 &&
        !bad_activation && prefetch_space),.s_ready(weight_ready),
      .s_descriptor(descriptor),.s_row(activation_row[activation_head]),
      .s_col(activation_column[activation_head]),
      .s_sparse(sparse),.s_token_mask(tokens),.s_act(store_data),
      .s_keep(store_keep),.s_tag(tag),
      .m_valid(weight_valid),
      .m_ready(executing && prefetch_count!=0 &&
        (bad_weight || (mac_ready && issue_space))),
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
      .s_valid(executing && weight_valid && prefetch_count!=0 &&
        !bad_weight && issue_space),
      .s_ready(mac_ready),.s_fp16(fp16),
      .s_weight_fp16(weight_format==2'd1),
      .s_token_mask(weight_tokens),.s_keep(weight_keep),
      .s_act(weight_activations),.s_weight(weights),
      .s_bias(128'd0),.s_tag(weight_tag),
      .m_valid(mac_valid),
      .m_ready(executing && issue_count!=0 && accumulator_ready),
      .m_error(mac_error),.m_sum(mac_sum),.m_tag(mac_tag),
      .m_token_mask(mac_tokens)
    );
    anvil_q2_ht2_row_accumulator row_accumulator (
      .clk(clk),.rst_n(rst_n),.annul(arithmetic_annul),
      .s_valid(executing && issue_count!=0 && mac_valid),
      .s_ready(accumulator_ready),.s_first(issued_column[issue_head]==0),
      .s_last({1'b0,issued_column[issue_head]}+33'd128>={1'b0,columns}),
      .s_error(mac_error || mac_tag!=tag || mac_tokens!=tokens),
      .s_row(issued_row[issue_head]),.s_column_tile(issued_column[issue_head] >> 7),
      .s_token_mask(tokens),.s_sum(mac_sum),.s_tag(tag),
      .m_valid(accumulator_valid),.m_ready(executing && !bad_accumulator && m_ready),
      .m_error(accumulator_error),.m_row(accumulator_row),
      .m_token_mask(accumulator_tokens),.m_sum(accumulator_sum),
      .m_tag(accumulator_tag)
    );

    assign s_ready=read_allowed && !r_valid && store_r_ready;
    assign w_ready=write_allowed && store_w_ready;
    assign w_rsp_valid=store_w_valid;
    assign w_rsp_error=store_w_error;
    assign r_ready=read_allowed && store_r_ready;
    assign r_rsp_valid=rst_n && !annul && external_read && store_m_valid;
    assign r_rsp_error=r_rsp_valid && store_m_error;
    assign r_data=r_rsp_valid ? store_data : 8192'd0;
    assign r_rsp_keep=r_rsp_valid ? store_keep : 512'd0;
    assign r_rsp_tag=r_rsp_valid ? store_tag : 64'd0;
    assign m_valid=available && (state==RESPONSE ||
      (executing && accumulator_valid && !bad_accumulator));
    assign m_error=m_valid && state==RESPONSE && response_error;
    assign m_last=m_valid && (state==RESPONSE ? response_last :
      accumulator_row==last_row);
    assign m_row=m_valid ? (state==RESPONSE ? row : accumulator_row) : 32'd0;
    assign m_token_mask=m_valid ? tokens : 4'd0;
    assign m_sum=m_valid && !m_error ? accumulator_sum : 128'd0;
    assign m_tag=m_valid ? tag : 64'd0;
    assign idle=available && state==IDLE && weight_idle &&
      !store_w_valid && !external_read;
    assign fault=rst_n && sticky_fault;

    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        state<=IDLE; descriptor<=0; vector_id<=0; row<=0; rows_left<=0;
        column<=0; last_row<=0; tokens<=0; fp16<=0; sparse<=0; weight_mode<=0;
        tag<=0;
        response_error<=0; response_last<=0; sticky_fault<=0;
        external_read<=0;
        issue_head<=0; issue_tail<=0; issue_count<=0;
        prefetch_head<=0; prefetch_tail<=0; prefetch_count<=0;
        activation_head<=0; activation_tail<=0; activation_count<=0;
        for (q=0;q<64;q=q+1) begin issued_row[q]<=0; issued_column[q]<=0; end
        for (q=0;q<8;q=q+1) begin prefetched_row[q]<=0; prefetched_column[q]<=0; end
        for (q=0;q<4;q=q+1) begin activation_row[q]<=0; activation_column[q]<=0; end
      end else if (annul) begin
        state<=IDLE; response_error<=0; response_last<=0;
        external_read<=0;
        issue_head<=0; issue_tail<=0; issue_count<=0;
        prefetch_head<=0; prefetch_tail<=0; prefetch_count<=0;
        activation_head<=0; activation_tail<=0; activation_count<=0;
      end else begin
        if (external_read_transfer) external_read<=1;
        if (r_rsp_valid && r_rsp_ready) external_read<=0;
        if (issue) begin
          issued_row[issue_tail]<=prefetched_row[prefetch_head];
          issued_column[issue_tail]<=prefetched_column[prefetch_head];
          issue_tail<=issue_tail+6'd1; prefetch_head<=prefetch_head+3'd1;
        end
        if (accumulate) issue_head<=issue_head+6'd1;
        case ({issue,accumulate})
          2'b10: issue_count<=issue_count+7'd1;
          2'b01: issue_count<=issue_count-7'd1;
          default: begin end
        endcase
        if (submit) begin
          prefetched_row[prefetch_tail]<=activation_row[activation_head];
          prefetched_column[prefetch_tail]<=activation_column[activation_head];
          prefetch_tail<=prefetch_tail+3'd1;
          activation_head<=activation_head+2'd1;
        end
        if (activation_request) begin
          activation_row[activation_tail]<=row;
          activation_column[activation_tail]<=column;
          activation_tail<=activation_tail+2'd1;
        end
        case ({activation_request,submit})
          2'b10: activation_count<=activation_count+3'd1;
          2'b01: activation_count<=activation_count-3'd1;
          default: begin end
        endcase
        case ({submit,issue})
          2'b10: prefetch_count<=prefetch_count+4'd1;
          2'b01: prefetch_count<=prefetch_count-4'd1;
          default: begin end
        endcase
        if (weight_fault) sticky_fault<=1;
        if (weight_fault && state!=IDLE && state!=FAULT_DRAIN) begin
          state<=FLUSH;
        end else if (executing && accumulator_valid && bad_accumulator) begin
          state<=FLUSH;
        end else if (executing && weight_valid && bad_weight) begin
          state<=FLUSH;
        end else if (executing && store_m_valid && activation_count!=0 &&
            bad_activation) begin
          state<=FLUSH;
        end else case (state)
          IDLE: if (command_transfer) begin
            descriptor<=s_descriptor; vector_id<=s_vector; row<=s_first_row;
            rows_left<=s_row_count; column<=0; tokens<=s_token_mask;
            last_row<=s_first_row+s_row_count-32'd1;
            fp16<=s_fp16; sparse<=s_sparse; weight_mode<=s_weight_mode;
            tag<=s_tag; response_error<=0; response_last<=0;
            state<=VALIDATE;
          end
          VALIDATE: begin
            if (command_bad) state<=FLUSH;
            else state<=ACTIVATION_SEND;
          end
          ACTIVATION_SEND: if (activation_request) begin
            if (!final_tile) begin
              column<=column+32'd128;
            end else if (rows_left!=1) begin
              row<=row+32'd1; rows_left<=rows_left-32'd1;
              column<=0;
            end else begin
              state<=WAIT_COMPLETE;
            end
          end
          WAIT_COMPLETE: if (row_transfer && m_last) state<=IDLE;
          FLUSH: begin
            response_error<=1; response_last<=1;
            sticky_fault<=1; issue_head<=0; issue_tail<=0; issue_count<=0;
            prefetch_head<=0; prefetch_tail<=0; prefetch_count<=0;
            activation_head<=0; activation_tail<=0; activation_count<=0;
            state<=FAULT_DRAIN;
          end
          FAULT_DRAIN: if (weight_idle) state<=RESPONSE;
          RESPONSE: if (m_ready) state<=IDLE;
          default: state<=FLUSH;
        endcase
      end
    end
  end endgenerate
endmodule
