module anvil_q2_ht2_vector_unit #(
  parameter MAX_WORDS=32768
) (
  input wire clk, rst_n, annul,
  input wire s_valid,
  output wire s_ready,
  input wire [2:0] s_operation,
  input wire [31:0] s_count,
  input wire s_fp16,
  input wire [63:0] s_tag,
  input wire d_valid, d_last,
  output wire d_ready,
  input wire [31:0] d_data, d_aux,
  output wire m_valid,
  input wire m_ready,
  output wire m_error, m_last,
  output wire [31:0] m_index, m_fp32,
  output wire [15:0] m_data,
  output wire [63:0] m_tag
);
  localparam LEGAL=MAX_WORDS>=1 && MAX_WORDS<=32768;
  generate if (!LEGAL) begin: invalid_parameters
    initial $fatal(1,"ANVIL_Q2_HT2 PARAMETER ERROR: native vector capacity");
    assign s_ready=0; assign d_ready=0; assign m_valid=0;
    assign m_error=0; assign m_last=0; assign m_index=0;
    assign m_fp32=0; assign m_data=0; assign m_tag=0;
  end else begin: implementation
    import anvil_q2_ht2_fp_pkg::*;
    localparam [2:0] RMSNORM=0, RESIDUAL=1, SWIGLU=2, SOFTMAX=3, PRODUCT=4;
    localparam [5:0] IDLE=0, VALIDATE=1, LOAD=2,
      SCALAR_WAIT=6, FOLD=13, FOLD_SUM=14, COUNT_INVERSE=15,
      RMS_MEAN=16, RMS_EPSILON=17, RMS_INVERSE=18, SAVE_NORMALIZER=19,
      SOFTMAX_INVERSE=20, RESPONSE=31, FAILURE=32,
      STREAM=33, STATISTICS=34;
    reg [5:0] state, return_state;
    reg [2:0] operation;
    reg [31:0] count, index;
    reg fp16, response_error;
    reg [63:0] tag;
    reg [31:0] maximum, temporary, total, normalizer;
    reg [15:0] partial_valid, rounded;
    reg [4:0] level;
    (* ramstyle="M20K", nomem2reg *) reg [31:0] operands [0:MAX_WORDS-1];
    (* ramstyle="M20K", nomem2reg *) reg [31:0] auxiliaries [0:MAX_WORDS-1];
    (* ramstyle="M20K", nomem2reg *) reg [31:0] exponentials [0:MAX_WORDS-1];
    (* nomem2reg *) reg [31:0] partial [0:15];
    reg [31:0] operand_q, auxiliary_q, exponential_q;
    reg launch_scalar;
    reg [2:0] scalar_operation;
    reg [31:0] scalar_a, scalar_b;
    reg [5:0] scalar_return;
    wire scalar_ready, scalar_valid, scalar_error;
    wire [31:0] scalar_data;
    wire [63:0] scalar_tag;
    reg stream_pending;
    reg [31:0] stream_issued, stream_index;
    wire result_ready, result_valid, result_error, result_last;
    wire [31:0] result_index, result_fp32;
    wire [15:0] result_data;
    wire [63:0] result_tag;
    wire ordinary_ready, ordinary_valid, ordinary_error, ordinary_last;
    wire [31:0] ordinary_index, ordinary_fp32;
    wire [15:0] ordinary_data;
    wire [63:0] ordinary_tag;
    wire swi_ready, swi_valid, swi_error, swi_last;
    wire [31:0] swi_index, swi_fp32;
    wire [15:0] swi_data;
    wire [63:0] swi_tag;
    wire stream_active=rst_n && !annul && state==STREAM;
    wire stream_advance=!stream_pending || result_ready;
    wire stream_read=stream_active && stream_advance && stream_issued<count;
    wire result_transfer=stream_active && result_valid && m_ready;
    wire result_annul=annul || state!=STREAM;
    wire [5:0] count_leading=leading32(count);
    wire [31:0] normalized_count=count << count_leading;
    wire [8:0] count_exponent=9'd158-{3'd0,count_leading};
    wire [31:0] count_fp32={1'b0,count_exponent[7:0],normalized_count[30:8]};
    wire last_index=index==count-32'd1;
    wire loading=rst_n && !annul && state==LOAD;
    wire statistics_clear=annul || state==IDLE || state==FAILURE || state==RESPONSE;
    wire statistics_active=rst_n && !statistics_clear;
    wire square_input=loading && d_valid && operation==RMSNORM;
    wire [31:0] square_data, softmax_difference, softmax_exponential;
    wire square_error, difference_error, exponential_error;
    reg [6:0] square_valid, square_last;
    reg [163:0] exponential_valid, exponential_last;
    wire [31:0] exponential_index;
    wire delayed_difference_error;
    reg [31:0] statistics_issued, statistics_index;
    reg statistics_pending;
    wire statistics_read=statistics_active && state==STATISTICS &&
      operation==SOFTMAX && statistics_issued<count;
    wire reduction_ready, reduction_valid, reduction_error;
    wire [15:0] reduction_mask;
    wire [511:0] reduction_partials;
    wire reduction_input=statistics_active && (operation==RMSNORM ?
      square_valid[6] : exponential_valid[163]);
    wire statistics_capture=statistics_active && state==STATISTICS &&
      reduction_valid;
    wire work_write=statistics_active && operation==SOFTMAX && exponential_valid[163];
    integer partial_index;
    wire input_nonfinite=d_data[30:23]==8'hff ||
      (operation!=SOFTMAX && d_aux[30:23]==8'hff);
    wire magnitudes_zero=d_data[30:0]==0 && maximum[30:0]==0;
    wire input_larger=!magnitudes_zero && (d_data[31]!=maximum[31] ?
      !d_data[31] : (d_data[31] ? d_data[30:0]<maximum[30:0] :
        d_data[30:0]>maximum[30:0]));

    always @(posedge clk) begin
      if (loading && d_valid) begin
        operands[index]<=d_data;
        auxiliaries[index]<=d_aux;
      end
      if (stream_read) begin
        operand_q<=operands[stream_issued];
        auxiliary_q<=auxiliaries[stream_issued];
        exponential_q<=exponentials[stream_issued];
      end
      if (statistics_read) operand_q<=operands[statistics_issued];
      if (work_write) exponentials[exponential_index]<=softmax_exponential;
      if (statistics_capture)
        for (partial_index=0;partial_index<16;partial_index=partial_index+1)
          partial[partial_index]<=reduction_partials[32*partial_index+:32];
    end

    anvil_q2_ht2_fp32_mul_pipe square_pipeline (
      .clk(clk),.rst_n(rst_n),.advance(statistics_active),
      .a(square_input ? d_data : 32'd0),.b(square_input ? d_data : 32'd0),
      .product(square_data),.error(square_error)
    );
    anvil_q2_ht2_fp32_add_pipe maximum_subtraction (
      .clk(clk),.rst_n(rst_n),.advance(statistics_active),
      .a(statistics_pending ? operand_q : 32'd0),
      .b(statistics_pending ? {~maximum[31],maximum[30:0]} : 32'd0),
      .sum(softmax_difference),.error(difference_error)
    );
    anvil_q2_ht2_exp_datapath exponential_pipeline (
      .clk(clk),.rst_n(rst_n),.advance(statistics_active),
      .s_data(softmax_difference),.m_data(softmax_exponential),
      .m_error(exponential_error)
    );
    anvil_q2_ht2_delay #(.WIDTH(32),.STAGES(164)) statistics_index_delay (
      .clk(clk),.rst_n(rst_n),.advance(statistics_active),
      .s_data(statistics_index),.m_data(exponential_index)
    );
    anvil_q2_ht2_delay #(.WIDTH(1),.STAGES(160)) subtraction_error_delay (
      .clk(clk),.rst_n(rst_n),.advance(statistics_active),
      .s_data(difference_error),.m_data(delayed_difference_error)
    );
    anvil_q2_ht2_stream_reduction reduction (
      .clk(clk),.rst_n(rst_n),.annul(statistics_clear),
      .s_valid(reduction_input),.s_ready(reduction_ready),
      .s_last(operation==RMSNORM ? square_last[6] : exponential_last[163]),
      .s_error(operation==RMSNORM ? square_error :
        (exponential_error || delayed_difference_error)),
      .s_data(operation==RMSNORM ? square_data : softmax_exponential),
      .m_valid(reduction_valid),.m_ready(statistics_capture),
      .m_error(reduction_error),.m_mask(reduction_mask),
      .m_partials(reduction_partials)
    );
    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        square_valid<=0; square_last<=0; exponential_valid<=0; exponential_last<=0;
        statistics_issued<=0; statistics_index<=0; statistics_pending<=0;
      end else if (statistics_clear) begin
        square_valid<=0; square_last<=0; exponential_valid<=0; exponential_last<=0;
        statistics_issued<=0; statistics_index<=0; statistics_pending<=0;
      end else begin
        square_valid<={square_valid[5:0],square_input};
        square_last<={square_last[5:0],square_input && last_index};
        exponential_valid<={exponential_valid[162:0],statistics_pending};
        exponential_last<={exponential_last[162:0],
          statistics_pending && statistics_index+32'd1==count};
        statistics_pending<=statistics_read;
        if (statistics_read) begin
          statistics_index<=statistics_issued;
          statistics_issued<=statistics_issued+32'd1;
        end
      end
    end

    always @* begin
      launch_scalar=0; scalar_operation=0; scalar_a=0; scalar_b=0;
      scalar_return=FAILURE;
      if (rst_n && !annul) begin
        case (state)
          FOLD: if (level<16 && partial_valid[level]) begin
            launch_scalar=1; scalar_a=total; scalar_b=partial[level];
            scalar_return=FOLD_SUM;
          end
          COUNT_INVERSE: begin
            launch_scalar=1; scalar_operation=2;
            scalar_a=count_fp32; scalar_return=RMS_MEAN;
          end
          RMS_MEAN: begin
            launch_scalar=1; scalar_operation=1;
            scalar_a=total; scalar_b=temporary; scalar_return=RMS_EPSILON;
          end
          RMS_EPSILON: begin
            launch_scalar=1; scalar_a=temporary; scalar_b=32'h358637bd;
            scalar_return=RMS_INVERSE;
          end
          RMS_INVERSE: begin
            launch_scalar=1; scalar_operation=3;
            scalar_a=temporary; scalar_return=SAVE_NORMALIZER;
          end
          SOFTMAX_INVERSE: begin
            launch_scalar=1; scalar_operation=2;
            scalar_a=total; scalar_return=SAVE_NORMALIZER;
          end
          default: begin end
        endcase
      end
    end

    anvil_q2_ht2_scalar scalar (
      .clk(clk),.rst_n(rst_n),.annul(annul),
      .s_valid(launch_scalar),.s_ready(scalar_ready),
      .s_operation(scalar_operation),.s_a(scalar_a),.s_b(scalar_b),.s_tag(tag),
      .m_ready(rst_n && !annul && state==SCALAR_WAIT),
      .m_valid(scalar_valid),.m_error(scalar_error),
      .m_data(scalar_data),.m_tag(scalar_tag)
    );
    anvil_q2_ht2_vector_result_pipe output_pipeline (
      .clk(clk),.rst_n(rst_n),.annul(result_annul),
      .s_valid(stream_active && stream_pending && operation!=SWIGLU),.s_ready(ordinary_ready),
      .s_operation(operation),.s_fp16(fp16),
      .s_last(stream_index+32'd1==count),
      .s_data(operand_q),.s_aux(auxiliary_q),.s_exponential(exponential_q),
      .s_normalizer(normalizer),.s_index(stream_index),.s_tag(tag),
      .m_valid(ordinary_valid),.m_ready(stream_active && operation!=SWIGLU && m_ready),
      .m_error(ordinary_error),.m_last(ordinary_last),.m_index(ordinary_index),
      .m_fp32(ordinary_fp32),.m_data(ordinary_data),.m_tag(ordinary_tag)
    );
    anvil_q2_ht2_swiglu_pipe swiglu_pipeline (
      .clk(clk),.rst_n(rst_n),.annul(result_annul),
      .s_valid(stream_active && stream_pending && operation==SWIGLU),.s_ready(swi_ready),
      .s_fp16(fp16),.s_last(stream_index+32'd1==count),
      .s_gate(operand_q),.s_up(auxiliary_q),.s_index(stream_index),.s_tag(tag),
      .m_valid(swi_valid),.m_ready(stream_active && operation==SWIGLU && m_ready),
      .m_error(swi_error),.m_last(swi_last),.m_index(swi_index),
      .m_fp32(swi_fp32),.m_data(swi_data),.m_tag(swi_tag)
    );
    assign result_ready=operation==SWIGLU ? swi_ready : ordinary_ready;
    assign result_valid=operation==SWIGLU ? swi_valid : ordinary_valid;
    assign result_error=operation==SWIGLU ? swi_error : ordinary_error;
    assign result_last=operation==SWIGLU ? swi_last : ordinary_last;
    assign result_index=operation==SWIGLU ? swi_index : ordinary_index;
    assign result_fp32=operation==SWIGLU ? swi_fp32 : ordinary_fp32;
    assign result_data=operation==SWIGLU ? swi_data : ordinary_data;
    assign result_tag=operation==SWIGLU ? swi_tag : ordinary_tag;

    assign s_ready=rst_n && !annul && state==IDLE;
    assign d_ready=loading;
    assign m_valid=rst_n && !annul &&
      (state==RESPONSE || (state==STREAM && result_valid));
    assign m_error=m_valid && (state==STREAM ? result_error : response_error);
    assign m_last=m_valid && (state==STREAM ?
      (result_error || result_last) : (response_error || last_index));
    assign m_index=m_valid ? (state==STREAM ? result_index : index) : 32'd0;
    assign m_fp32=m_valid && !m_error ? (state==STREAM ? result_fp32 : temporary) : 32'd0;
    assign m_data=m_valid && !m_error ? (state==STREAM ? result_data : rounded) : 16'd0;
    assign m_tag=m_valid ? (state==STREAM ? result_tag : tag) : 64'd0;

    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        stream_pending<=0; stream_issued<=0; stream_index<=0;
      end else if (annul || state!=STREAM) begin
        stream_pending<=0; stream_issued<=0; stream_index<=0;
      end else if (stream_advance) begin
        stream_pending<=stream_read;
        if (stream_read) begin
          stream_index<=stream_issued; stream_issued<=stream_issued+32'd1;
        end
      end
    end

    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        state<=IDLE; return_state<=0; operation<=0;
        count<=0; index<=0; fp16<=0; response_error<=0;
        tag<=0; maximum<=0; temporary<=0; total<=0;
        normalizer<=0; partial_valid<=0; rounded<=0; level<=0;
      end else if (annul) begin
        state<=IDLE; partial_valid<=0; response_error<=0; rounded<=0;
      end else if (reduction_input && !reduction_ready) state<=FAILURE;
      else if (state==SCALAR_WAIT) begin
        if (scalar_valid) begin
          if (scalar_error || scalar_tag!=tag) state<=FAILURE;
          else begin temporary<=scalar_data; state<=return_state; end
        end
      end else if (launch_scalar) begin
        if (scalar_ready) begin
          return_state<=scalar_return; state<=SCALAR_WAIT;
        end
      end else case (state)
        IDLE: if (s_valid) begin
          operation<=s_operation; count<=s_count; fp16<=s_fp16; tag<=s_tag;
          index<=0; maximum<=0; total<=0; partial_valid<=0;
          response_error<=0; rounded<=0; state<=VALIDATE;
        end
        VALIDATE: begin
          if (count==0 || count>MAX_WORDS || operation>PRODUCT) state<=FAILURE;
          else state<=LOAD;
        end
        LOAD: if (d_valid) begin
          if (d_last!=last_index || input_nonfinite) state<=FAILURE;
          else begin
            if (index==0 || input_larger) maximum<=d_data;
            if (last_index) begin
              index<=0;
              if (operation==RESIDUAL || operation==PRODUCT || operation==SWIGLU)
                state<=STREAM;
              else state<=STATISTICS;
            end else index<=index+32'd1;
          end
        end
        FOLD: begin
          if (level==16) begin
            if (operation==RMSNORM) state<=COUNT_INVERSE;
            else state<=SOFTMAX_INVERSE;
          end else level<=level+5'd1;
        end
        FOLD_SUM: begin total<=temporary; level<=level+5'd1; state<=FOLD; end
        SAVE_NORMALIZER: begin
          normalizer<=temporary; index<=0; state<=STREAM;
        end
        STATISTICS: if (statistics_capture) begin
          if (reduction_error) state<=FAILURE;
          else begin
            partial_valid<=reduction_mask; level<=0; total<=0; state<=FOLD;
          end
        end
        STREAM: if (result_transfer && (result_error || result_last)) state<=IDLE;
        RESPONSE: if (m_ready) state<=IDLE;
        FAILURE: begin
          response_error<=1; rounded<=0; temporary<=0; state<=RESPONSE;
        end
        default: state<=FAILURE;
      endcase
    end
  end endgenerate
endmodule
