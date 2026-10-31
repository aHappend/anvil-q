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
    localparam [5:0] IDLE=0, VALIDATE=1, LOAD=2, READ_SEND=3,
      READ_CAPTURE=4, DISPATCH=5, SCALAR_WAIT=6, RMS_SQUARE=7,
      SOFTMAX_SUB=8, SOFTMAX_EXP=9, SUM_PREPARE=10, SUM_FIND=11,
      SUM_MERGED=12, FOLD=13, FOLD_SUM=14, COUNT_INVERSE=15,
      RMS_MEAN=16, RMS_EPSILON=17, RMS_INVERSE=18, SAVE_NORMALIZER=19,
      SOFTMAX_INVERSE=20, RMS_SCALE=21, RMS_GAMMA=22,
      SOFTMAX_SCALE=23, RESIDUAL_ADD=24, SWI_SIGMOID=25,
      SWI_GATE=26, SWI_PRODUCT=27, ELEMENT_PRODUCT=28,
      CONVERT_SEND=29, CONVERT_WAIT=30, RESPONSE=31, FAILURE=32;
    reg [5:0] state, return_state;
    reg [2:0] operation;
    reg [31:0] count, index;
    reg fp16, output_pass, response_error;
    reg [63:0] tag;
    reg [31:0] maximum, temporary, carry, total, normalizer;
    reg [15:0] partial_valid, rounded;
    reg [4:0] level;
    (* ramstyle="M20K", nomem2reg *) reg [31:0] operands [0:MAX_WORDS-1];
    (* ramstyle="M20K", nomem2reg *) reg [31:0] auxiliaries [0:MAX_WORDS-1];
    (* ramstyle="M20K", nomem2reg *) reg [31:0] exponentials [0:MAX_WORDS-1];
    reg [31:0] partial [0:15];
    reg [31:0] operand_q, auxiliary_q, exponential_q;
    reg launch_scalar;
    reg [2:0] scalar_operation;
    reg [31:0] scalar_a, scalar_b;
    reg [5:0] scalar_return;
    wire scalar_ready, scalar_valid, scalar_error;
    wire [31:0] scalar_data;
    wire [63:0] scalar_tag;
    wire convert_ready, convert_valid, convert_error;
    wire [31:0] converted;
    wire [63:0] convert_tag;
    wire [5:0] count_leading=leading32(count);
    wire [31:0] normalized_count=count << count_leading;
    wire [8:0] count_exponent=9'd158-{3'd0,count_leading};
    wire [31:0] count_fp32={1'b0,count_exponent[7:0],normalized_count[30:8]};
    wire last_index=index==count-32'd1;
    wire loading=rst_n && !annul && state==LOAD;
    wire reading=rst_n && !annul && state==READ_SEND;
    wire partial_write=rst_n && !annul && state==SUM_FIND &&
      level<16 && !partial_valid[level];
    wire work_write=rst_n && !annul && state==SUM_PREPARE && operation==SOFTMAX;
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
      if (reading) begin
        operand_q<=operands[index];
        auxiliary_q<=auxiliaries[index];
        exponential_q<=exponentials[index];
      end
      if (work_write) exponentials[index]<=temporary;
      if (partial_write) partial[level]<=carry;
    end

    always @* begin
      launch_scalar=0; scalar_operation=0; scalar_a=0; scalar_b=0;
      scalar_return=FAILURE;
      if (rst_n && !annul) begin
        case (state)
          RMS_SQUARE: begin
            launch_scalar=1; scalar_operation=1;
            scalar_a=operand_q; scalar_b=operand_q; scalar_return=SUM_PREPARE;
          end
          SOFTMAX_SUB: begin
            launch_scalar=1; scalar_a=operand_q;
            scalar_b={~maximum[31],maximum[30:0]}; scalar_return=SOFTMAX_EXP;
          end
          SOFTMAX_EXP: begin
            launch_scalar=1; scalar_operation=4;
            scalar_a=temporary; scalar_return=SUM_PREPARE;
          end
          SUM_FIND: if (level<16 && partial_valid[level]) begin
            launch_scalar=1; scalar_a=partial[level]; scalar_b=carry;
            scalar_return=SUM_MERGED;
          end
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
          RMS_SCALE: begin
            launch_scalar=1; scalar_operation=1;
            scalar_a=operand_q; scalar_b=normalizer; scalar_return=RMS_GAMMA;
          end
          RMS_GAMMA: begin
            launch_scalar=1; scalar_operation=1;
            scalar_a=temporary; scalar_b=auxiliary_q; scalar_return=CONVERT_SEND;
          end
          SOFTMAX_SCALE: begin
            launch_scalar=1; scalar_operation=1;
            scalar_a=exponential_q; scalar_b=normalizer; scalar_return=CONVERT_SEND;
          end
          RESIDUAL_ADD: begin
            launch_scalar=1; scalar_a=operand_q; scalar_b=auxiliary_q;
            scalar_return=CONVERT_SEND;
          end
          SWI_SIGMOID: begin
            launch_scalar=1; scalar_operation=5;
            scalar_a=operand_q; scalar_return=SWI_GATE;
          end
          SWI_GATE: begin
            launch_scalar=1; scalar_operation=1;
            scalar_a=operand_q; scalar_b=temporary; scalar_return=SWI_PRODUCT;
          end
          SWI_PRODUCT: begin
            launch_scalar=1; scalar_operation=1;
            scalar_a=temporary; scalar_b=auxiliary_q; scalar_return=CONVERT_SEND;
          end
          ELEMENT_PRODUCT: begin
            launch_scalar=1; scalar_operation=1;
            scalar_a=operand_q; scalar_b=auxiliary_q; scalar_return=CONVERT_SEND;
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
    anvil_q2_ht2_convert_pipe conversion (
      .clk(clk),.rst_n(rst_n),.annul(annul),
      .s_valid(rst_n && !annul && state==CONVERT_SEND),
      .s_ready(convert_ready),.s_to_fp32(1'b0),.s_fp16(fp16),
      .s_data(temporary),.s_tag(tag),
      .m_ready(rst_n && !annul && state==CONVERT_WAIT),
      .m_valid(convert_valid),.m_error(convert_error),
      .m_data(converted),.m_tag(convert_tag)
    );

    assign s_ready=rst_n && !annul && state==IDLE;
    assign d_ready=loading;
    assign m_valid=rst_n && !annul && state==RESPONSE;
    assign m_error=m_valid && response_error;
    assign m_last=m_valid && (response_error || last_index);
    assign m_index=m_valid ? index : 32'd0;
    assign m_fp32=m_valid && !response_error ? temporary : 32'd0;
    assign m_data=m_valid && !response_error ? rounded : 16'd0;
    assign m_tag=m_valid ? tag : 64'd0;

    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        state<=IDLE; return_state<=0; operation<=0;
        count<=0; index<=0; fp16<=0; output_pass<=0; response_error<=0;
        tag<=0; maximum<=0; temporary<=0; carry<=0; total<=0;
        normalizer<=0; partial_valid<=0; rounded<=0; level<=0;
      end else if (annul) begin
        state<=IDLE; partial_valid<=0; response_error<=0; rounded<=0;
      end else if (state==SCALAR_WAIT) begin
        if (scalar_valid) begin
          if (scalar_error || scalar_tag!=tag) state<=FAILURE;
          else begin temporary<=scalar_data; state<=return_state; end
        end
      end else if (launch_scalar) begin
        if (scalar_ready) begin
          return_state<=scalar_return; state<=SCALAR_WAIT;
          if (state==SUM_FIND) partial_valid[level]<=0;
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
              output_pass<=operation!=RMSNORM && operation!=SOFTMAX;
              state<=READ_SEND;
            end else index<=index+32'd1;
          end
        end
        READ_SEND: state<=READ_CAPTURE;
        READ_CAPTURE: state<=DISPATCH;
        DISPATCH: begin
          case (operation)
            RMSNORM: begin
              if (output_pass) state<=RMS_SCALE;
              else state<=RMS_SQUARE;
            end
            SOFTMAX: begin
              if (output_pass) state<=SOFTMAX_SCALE;
              else state<=SOFTMAX_SUB;
            end
            RESIDUAL: state<=RESIDUAL_ADD;
            SWIGLU: state<=SWI_SIGMOID;
            PRODUCT: state<=ELEMENT_PRODUCT;
            default: state<=FAILURE;
          endcase
        end
        SUM_PREPARE: begin carry<=temporary; level<=0; state<=SUM_FIND; end
        SUM_FIND: begin
          if (level>=16) state<=FAILURE;
          else begin
            partial_valid[level]<=1;
            if (last_index) begin level<=0; total<=0; state<=FOLD; end
            else begin index<=index+32'd1; state<=READ_SEND; end
          end
        end
        SUM_MERGED: begin
          carry<=temporary; level<=level+5'd1; state<=SUM_FIND;
        end
        FOLD: begin
          if (level==16) begin
            if (operation==RMSNORM) state<=COUNT_INVERSE;
            else state<=SOFTMAX_INVERSE;
          end else level<=level+5'd1;
        end
        FOLD_SUM: begin total<=temporary; level<=level+5'd1; state<=FOLD; end
        SAVE_NORMALIZER: begin
          normalizer<=temporary; output_pass<=1; index<=0; state<=READ_SEND;
        end
        CONVERT_SEND: if (convert_ready) state<=CONVERT_WAIT;
        CONVERT_WAIT: if (convert_valid) begin
          if (convert_error || convert_tag!=tag) state<=FAILURE;
          else begin rounded<=converted[15:0]; state<=RESPONSE; end
        end
        RESPONSE: if (m_ready) begin
          if (response_error || last_index) state<=IDLE;
          else begin index<=index+32'd1; state<=READ_SEND; end
        end
        FAILURE: begin
          response_error<=1; rounded<=0; temporary<=0; state<=RESPONSE;
        end
        default: state<=FAILURE;
      endcase
    end
  end endgenerate
endmodule
