module anvil_q2_ht2_spec_verifier #(
  parameter NUM_LAYERS=28,
  parameter MAX_SEQ_LEN=32768
) (
  input wire clk, rst_n, annul, s_valid, m_ready, s_new_sequence,
  input wire [2:0] s_count,
  input wire [127:0] s_ids,
  input wire [7:0] s_parent,
  input wire [127:0] s_target_ids,
  input wire [31:0] s_position,
  input wire [111:0] s_kv_complete,
  input wire [3:0] s_kv_error,
  output wire s_ready, m_valid, m_error,
  output wire [2:0] m_accepted,
  output wire [3:0] m_mask,
  output wire [31:0] m_next_token, m_position, committed_position,
  output wire commit_valid
);
  localparam LEGAL=NUM_LAYERS>=1 && NUM_LAYERS<=28 &&
    MAX_SEQ_LEN>=1 && MAX_SEQ_LEN<=32768;
  generate if (!LEGAL) begin: invalid_parameters
    initial $fatal(1,"ANVIL_Q2_HT2 PARAMETER ERROR: tree geometry");
    assign s_ready=0; assign m_valid=0; assign m_error=0;
    assign m_accepted=0; assign m_mask=0; assign m_next_token=0;
    assign m_position=0; assign committed_position=0; assign commit_valid=0;
  end else begin: implementation
    reg [2:0] stage, count, accepted, response_accepted;
    reg [127:0] ids, targets;
    reg [7:0] parents;
    reg [111:0] completions;
    reg [3:0] kv_errors, mask, response_mask;
    reg [31:0] position, pointer, response_position, response_next;
    reg new_sequence, failed, stopped, response_error, published;
    reg [1:0] selected;
    reg bad_input;
    reg [2:0] child;
    integer t,l,j;
    wire [32:0] next_position={1'b0,position}+{30'd0,accepted};

    always @* begin
      bad_input=(count!=1 && count!=2 && count!=4) ||
        parents[1:0]!=0 || (!new_sequence && position!=pointer) ||
        position>=MAX_SEQ_LEN;
      for (t=0;t<4;t=t+1) begin
        if (t<count) begin
          if (t!=0 && {30'd0,parents[t*2+:2]}>=t) bad_input=1;
          if (kv_errors[t]) bad_input=1;
          for (l=0;l<NUM_LAYERS;l=l+1)
            if (!completions[28*t+l]) bad_input=1;
        end
      end
    end

    always @* begin
      child=0;
      for (j=1;j<4;j=j+1)
        if (!child[2] && j<count && parents[j*2+:2]==selected &&
            ids[j*32+:32]==targets[selected*32+:32])
          child={1'b1,2'(j)};
    end

    assign s_ready=rst_n && !annul && stage==0;
    assign m_valid=rst_n && !annul && stage==6;
    assign m_error=m_valid && response_error;
    assign m_accepted=m_valid ? response_accepted : 3'd0;
    assign m_mask=m_valid ? response_mask : 4'd0;
    assign m_next_token=m_valid ? response_next : 32'd0;
    assign m_position=m_valid ? response_position : 32'd0;
    assign committed_position=rst_n ? pointer : 32'd0;
    assign commit_valid=rst_n && !annul && published;

    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        stage<=0; count<=0; accepted<=0; response_accepted<=0;
        ids<=0; targets<=0; parents<=0; completions<=0; kv_errors<=0;
        mask<=0; response_mask<=0; position<=0; pointer<=0;
        response_position<=0; response_next<=0; new_sequence<=0;
        failed<=0; stopped<=0; response_error<=0; published<=0; selected<=0;
      end else if (annul) begin
        stage<=0;
        published<=0;
      end else begin
        published<=0;
        case (stage)
          0: if (s_valid && s_ready) begin
            count<=s_count; ids<=s_ids; targets<=s_target_ids;
            parents<=s_parent; position<=s_position;
            completions<=s_kv_complete; kv_errors<=s_kv_error;
            new_sequence<=s_new_sequence;
            stage<=1;
          end
          1: begin
            failed<=bad_input;
            selected<=0; mask<=1; accepted<=1; stopped<=0;
            stage<=2;
          end
          2,3,4: begin
            if (!failed && !stopped && child[2]) begin
              selected<=child[1:0];
              mask<=mask | (4'b0001 << child[1:0]);
              accepted<=accepted+3'd1;
            end else stopped<=1;
            stage<=stage+3'd1;
          end
          5: begin
            response_error<=failed || next_position>MAX_SEQ_LEN;
            if (failed || next_position>MAX_SEQ_LEN) begin
              response_accepted<=0; response_mask<=0;
              response_position<=0; response_next<=0;
            end else begin
              response_accepted<=accepted; response_mask<=mask;
              response_position<=next_position[31:0];
              response_next<=targets[selected*32+:32];
            end
            stage<=6;
          end
          6: if (m_ready) begin
            if (!response_error) begin
              pointer<=response_position;
              published<=1;
            end
            stage<=0;
          end
          default: begin
            response_error<=1; response_accepted<=0; response_mask<=0;
            response_position<=0; response_next<=0; stage<=6;
          end
        endcase
      end
    end
  end endgenerate
endmodule
