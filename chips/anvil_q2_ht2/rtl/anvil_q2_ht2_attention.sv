module anvil_q2_ht2_attention #(
  parameter NUM_LAYERS=28, NUM_Q_HEADS=12, NUM_KV_HEADS=2,
  parameter HEAD_DIM=128, CACHE_BLOCK=16, MAX_SEQ_LEN=32768,
  parameter QWORDS=(HEAD_DIM>=2 && HEAD_DIM<=128) ? HEAD_DIM : 1,
  parameter WORDS=(CACHE_BLOCK>=1 && CACHE_BLOCK<=128) ? CACHE_BLOCK : 1
) (
  input wire clk, rst_n, annul, kv_idle,
  input wire s_valid,
  output wire s_ready,
  input wire [1:0] s_slot,
  input wire [4:0] s_layer,
  input wire [3:0] s_head,
  input wire [31:0] s_origin, s_position,
  input wire s_fp16,
  input wire [QWORDS*16-1:0] s_query,
  input wire [63:0] s_tag,
  output wire m_valid,
  input wire m_ready,
  output wire m_error,
  output wire [QWORDS*16-1:0] m_data,
  output wire [63:0] m_tag,
  output wire r_valid,
  input wire r_ready,
  output wire [1:0] r_slot,
  output wire [31:0] r_position,
  output wire [4:0] r_layer,
  output wire r_value, r_head,
  output wire [6:0] r_block,
  input wire r_rsp_valid, r_rsp_error,
  output wire r_rsp_ready,
  input wire [WORDS*16-1:0] r_data
);
  localparam SAFE_BLOCK=(CACHE_BLOCK>=1 && CACHE_BLOCK<=128) ? CACHE_BLOCK : 1;
  localparam LEGAL=NUM_LAYERS>=1 && NUM_LAYERS<=28 &&
    NUM_Q_HEADS>=1 && NUM_Q_HEADS<=16 &&
    NUM_KV_HEADS>=1 && NUM_KV_HEADS<=2 &&
    (NUM_KV_HEADS==1 || (NUM_KV_HEADS==2 && (NUM_Q_HEADS & 1)==0)) &&
    HEAD_DIM>=2 && HEAD_DIM<=128 && (HEAD_DIM & 1)==0 && QWORDS==HEAD_DIM &&
    NUM_Q_HEADS*HEAD_DIM>=8 && NUM_Q_HEADS*HEAD_DIM<=1536 &&
    ((NUM_Q_HEADS*HEAD_DIM) & 7)==0 && ((NUM_KV_HEADS*HEAD_DIM) & 7)==0 &&
    CACHE_BLOCK>=1 && CACHE_BLOCK<=128 && WORDS==CACHE_BLOCK &&
    (CACHE_BLOCK & (CACHE_BLOCK-1))==0 && (HEAD_DIM & (SAFE_BLOCK-1))==0 &&
    MAX_SEQ_LEN>=1 && MAX_SEQ_LEN<=32768;
  generate if (!LEGAL) begin: invalid_parameters
    initial $fatal(1,"ANVIL_Q2_HT2 PARAMETER ERROR: native attention geometry");
    assign s_ready=0; assign m_valid=0; assign m_error=0;
    assign m_data=0; assign m_tag=0; assign r_valid=0; assign r_slot=0;
    assign r_position=0; assign r_layer=0; assign r_value=0;
    assign r_head=0; assign r_block=0; assign r_rsp_ready=0;
  end else begin: implementation
    import anvil_q2_ht2_fp_pkg::*;
    localparam [5:0] IDLE=0, VALIDATE=1, SCALE=2, SCALAR_WAIT=3,
      SAVE_SCALE=4, QUERY_SEND=5, QUERY_WAIT=6, VECTOR_SEND=7,
      KV_SEND=8, KV_WAIT=9, QUERY_READ=10, KEY_MUL=11, KEY_ADD=12,
      KEY_NEXT=13, SCORE_SCALE=14, SCORE_SEND=15, PROBABILITY=16,
      VALUE_READ=17, VALUE_MUL=18, VALUE_ADD=19, VALUE_SAVE=20,
      OUTPUT_READ=21, OUTPUT_SEND=22, OUTPUT_WAIT=23, RESPONSE=24, FAILURE=25;
    reg [5:0] state, return_state;
    reg [1:0] slot;
    reg [4:0] layer;
    reg [3:0] head;
    reg fp16, value_phase, response_error;
    reg [31:0] origin, position, time_index, context_count;
    reg [7:0] dimension;
    reg [6:0] block_index, block_word;
    reg [QWORDS*16-1:0] query_source, response;
    reg [WORDS*16-1:0] cache_block;
    reg [63:0] tag;
    reg [31:0] scale, dot, probability, temporary;
    (* ramstyle="M20K", nomem2reg *) reg [31:0] query [0:HEAD_DIM-1];
    (* ramstyle="M20K", nomem2reg *) reg [31:0] context_data [0:HEAD_DIM-1];
    reg [31:0] query_q, context_q;
    reg launch_scalar;
    reg [2:0] scalar_operation;
    reg [31:0] scalar_a, scalar_b;
    reg [5:0] scalar_return;
    wire scalar_ready, scalar_valid, scalar_error;
    wire [31:0] scalar_data;
    wire [63:0] scalar_tag;
    wire convert_ready, convert_valid, convert_error;
    wire [31:0] converted;
    wire [63:0] converted_tag;
    wire vector_ready, vector_d_ready, vector_valid, vector_error, vector_last;
    wire [31:0] vector_index, vector_fp32;
    wire [63:0] vector_tag;
    wire child_annul=annul || state==FAILURE;
    wire enabled=rst_n && !child_annul;
    wire [5:0] head_leading=leading32(32'(HEAD_DIM));
    wire [31:0] normalized_head=32'(HEAD_DIM) << head_leading;
    wire [8:0] head_exponent=9'd158-{3'd0,head_leading};
    wire [31:0] head_fp32={1'b0,head_exponent[7:0],normalized_head[30:8]};
    wire last_time=time_index==context_count-32'd1;
    wire last_dimension=dimension==HEAD_DIM-1;
    wire last_word=block_word==CACHE_BLOCK-1;
    wire [31:0] cached_word={cache_block[16*block_word+:16],16'd0};
    wire [31:0] preceding_context=time_index==0 ? 32'd0 : context_q;
    wire query_write=enabled && state==QUERY_WAIT && convert_valid &&
      !convert_error && converted_tag==tag;
    wire context_write=enabled && state==VALUE_SAVE;

    always @(posedge clk) begin
      if (query_write) query[dimension]<=converted;
      if (enabled && state==QUERY_READ) query_q<=query[dimension];
      if (enabled && (state==VALUE_READ || state==OUTPUT_READ))
        context_q<=context_data[dimension];
      if (context_write) context_data[dimension]<=temporary;
    end

    always @* begin
      launch_scalar=0; scalar_operation=0; scalar_a=0; scalar_b=0;
      scalar_return=FAILURE;
      if (enabled) begin
        case (state)
          SCALE: begin
            launch_scalar=1; scalar_operation=3;
            scalar_a=head_fp32; scalar_return=SAVE_SCALE;
          end
          KEY_MUL: begin
            launch_scalar=1; scalar_operation=1;
            scalar_a=query_q; scalar_b=cached_word; scalar_return=KEY_ADD;
          end
          KEY_ADD: begin
            launch_scalar=1; scalar_a=dot; scalar_b=temporary;
            scalar_return=KEY_NEXT;
          end
          SCORE_SCALE: begin
            launch_scalar=1; scalar_operation=1;
            scalar_a=dot; scalar_b=scale; scalar_return=SCORE_SEND;
          end
          VALUE_MUL: begin
            launch_scalar=1; scalar_operation=1;
            scalar_a=probability; scalar_b=cached_word; scalar_return=VALUE_ADD;
          end
          VALUE_ADD: begin
            launch_scalar=1; scalar_a=preceding_context; scalar_b=temporary;
            scalar_return=VALUE_SAVE;
          end
          default: begin end
        endcase
      end
    end

    anvil_q2_ht2_scalar scalar (
      .clk(clk),.rst_n(rst_n),.annul(child_annul),
      .s_valid(launch_scalar),.s_ready(scalar_ready),
      .s_operation(scalar_operation),.s_a(scalar_a),.s_b(scalar_b),.s_tag(tag),
      .m_ready(enabled && state==SCALAR_WAIT),
      .m_valid(scalar_valid),.m_error(scalar_error),
      .m_data(scalar_data),.m_tag(scalar_tag)
    );
    anvil_q2_ht2_convert_pipe conversion (
      .clk(clk),.rst_n(rst_n),.annul(child_annul),
      .s_valid(enabled && (state==QUERY_SEND || state==OUTPUT_SEND)),
      .s_ready(convert_ready),.s_to_fp32(state==QUERY_SEND),.s_fp16(fp16),
      .s_data(state==QUERY_SEND ?
        {16'd0,query_source[16*dimension+:16]} : context_q),.s_tag(tag),
      .m_ready(enabled && (state==QUERY_WAIT || state==OUTPUT_WAIT)),
      .m_valid(convert_valid),.m_error(convert_error),
      .m_data(converted),.m_tag(converted_tag)
    );
    anvil_q2_ht2_vector_unit #(.MAX_WORDS(MAX_SEQ_LEN)) softmax (
      .clk(clk),.rst_n(rst_n),.annul(child_annul),
      .s_valid(enabled && state==VECTOR_SEND),.s_ready(vector_ready),
      .s_operation(3'd3),.s_count(context_count),.s_fp16(fp16),.s_tag(tag),
      .d_valid(enabled && state==SCORE_SEND),.d_ready(vector_d_ready),
      .d_last(last_time),.d_data(temporary),.d_aux(32'd0),
      .m_valid(vector_valid),.m_ready(enabled && state==PROBABILITY),
      .m_error(vector_error),.m_last(vector_last),.m_index(vector_index),
      .m_fp32(vector_fp32),.m_data(),.m_tag(vector_tag)
    );

    assign s_ready=rst_n && !annul && state==IDLE && kv_idle;
    assign m_valid=rst_n && !annul && state==RESPONSE;
    assign m_error=m_valid && response_error;
    assign m_data=m_valid && !response_error ? response : {QWORDS*16{1'b0}};
    assign m_tag=m_valid ? tag : 64'd0;
    assign r_valid=enabled && state==KV_SEND;
    assign r_slot=r_valid ? slot : 2'd0;
    assign r_position=r_valid ? origin+time_index : 32'd0;
    assign r_layer=r_valid ? layer : 5'd0;
    assign r_value=r_valid && value_phase;
    assign r_head=r_valid && NUM_KV_HEADS==2 && head>=(NUM_Q_HEADS >> 1);
    assign r_block=r_valid ? block_index : 7'd0;
    assign r_rsp_ready=enabled && state==KV_WAIT;

    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        state<=IDLE; return_state<=0; slot<=0; layer<=0; head<=0;
        fp16<=0; value_phase<=0; response_error<=0; origin<=0;
        position<=0; time_index<=0; context_count<=0; dimension<=0;
        block_index<=0; block_word<=0; query_source<=0; response<=0;
        cache_block<=0; tag<=0; scale<=0; dot<=0; probability<=0; temporary<=0;
      end else if (annul) begin
        state<=IDLE; response_error<=0; response<=0;
      end else if (state==SCALAR_WAIT) begin
        if (scalar_valid) begin
          if (scalar_error || scalar_tag!=tag) state<=FAILURE;
          else begin temporary<=scalar_data; state<=return_state; end
        end
      end else if (launch_scalar) begin
        if (scalar_ready) begin state<=SCALAR_WAIT; return_state<=scalar_return; end
      end else case (state)
        IDLE: if (s_valid && s_ready) begin
          slot<=s_slot; layer<=s_layer; head<=s_head; fp16<=s_fp16;
          origin<=s_origin; position<=s_position;
          context_count<=s_position-s_origin+32'd1;
          query_source<=s_query; tag<=s_tag; dimension<=0;
          time_index<=0; block_index<=0; block_word<=0; dot<=0;
          value_phase<=0; response_error<=0; response<=0; state<=VALIDATE;
        end
        VALIDATE: begin
          if (origin>position || position>=MAX_SEQ_LEN ||
              context_count==0 || context_count>MAX_SEQ_LEN ||
              layer>=NUM_LAYERS || head>=NUM_Q_HEADS) state<=FAILURE;
          else state<=SCALE;
        end
        SAVE_SCALE: begin scale<=temporary; state<=QUERY_SEND; end
        QUERY_SEND: if (convert_ready) state<=QUERY_WAIT;
        QUERY_WAIT: if (convert_valid) begin
          if (convert_error || converted_tag!=tag) state<=FAILURE;
          else if (last_dimension) begin dimension<=0; state<=VECTOR_SEND; end
          else begin dimension<=dimension+8'd1; state<=QUERY_SEND; end
        end
        VECTOR_SEND: if (vector_ready) state<=KV_SEND;
        KV_SEND: if (r_ready) state<=KV_WAIT;
        KV_WAIT: if (r_rsp_valid) begin
          if (r_rsp_error) state<=FAILURE;
          else begin
            cache_block<=r_data;
            if (value_phase) state<=VALUE_READ;
            else state<=QUERY_READ;
          end
        end
        QUERY_READ: state<=KEY_MUL;
        KEY_NEXT: begin
          dot<=temporary;
          if (last_dimension) state<=SCORE_SCALE;
          else begin
            dimension<=dimension+8'd1;
            if (last_word) begin
              block_word<=0; block_index<=block_index+7'd1; state<=KV_SEND;
            end else begin block_word<=block_word+7'd1; state<=QUERY_READ; end
          end
        end
        SCORE_SEND: if (vector_d_ready) begin
          dimension<=0; block_index<=0; block_word<=0; dot<=0;
          if (last_time) begin
            time_index<=0; value_phase<=1; state<=PROBABILITY;
          end else begin time_index<=time_index+32'd1; state<=KV_SEND; end
        end
        PROBABILITY: if (vector_valid) begin
          if (vector_error || vector_tag!=tag ||
              vector_index!=time_index || vector_last!=last_time) state<=FAILURE;
          else begin
            probability<=vector_fp32; dimension<=0;
            block_index<=0; block_word<=0; state<=KV_SEND;
          end
        end
        VALUE_READ: state<=VALUE_MUL;
        VALUE_SAVE: begin
          if (last_dimension) begin
            dimension<=0;
            if (last_time) state<=OUTPUT_READ;
            else begin time_index<=time_index+32'd1; state<=PROBABILITY; end
          end else begin
            dimension<=dimension+8'd1;
            if (last_word) begin
              block_word<=0; block_index<=block_index+7'd1; state<=KV_SEND;
            end else begin block_word<=block_word+7'd1; state<=VALUE_READ; end
          end
        end
        OUTPUT_READ: state<=OUTPUT_SEND;
        OUTPUT_SEND: if (convert_ready) state<=OUTPUT_WAIT;
        OUTPUT_WAIT: if (convert_valid) begin
          if (convert_error || converted_tag!=tag) state<=FAILURE;
          else begin
            response[16*dimension+:16]<=converted[15:0];
            if (last_dimension) state<=RESPONSE;
            else begin dimension<=dimension+8'd1; state<=OUTPUT_READ; end
          end
        end
        RESPONSE: if (m_ready) state<=IDLE;
        FAILURE: begin response_error<=1; response<=0; state<=RESPONSE; end
        default: state<=FAILURE;
      endcase
    end
  end endgenerate
endmodule
