module anvil_q2_ht2_kv_map #(
  parameter NUM_LAYERS=28,
  parameter MAX_SEQ_LEN=32768,
  parameter VOCAB_SIZE=151936
) (
  input wire clk, rst_n, annul,
  input wire s_begin_valid,
  output wire s_begin_ready,
  input wire [2:0] s_count,
  input wire [127:0] s_ids,
  input wire [7:0] s_parent,
  input wire [31:0] s_position,
  input wire s_new_sequence,
  output wire active, input_error, allocator_error,
  output wire [127:0] provisional_pages,
  output wire [7:0] node_depth,
  input wire r_valid,
  output wire r_ready,
  input wire [1:0] r_slot,
  input wire [31:0] r_position,
  output wire r_rsp_valid, r_rsp_error,
  input wire r_rsp_ready,
  output wire [31:0] r_page,
  input wire s_finish_valid,
  output wire s_finish_ready,
  input wire [127:0] s_target_ids,
  input wire [111:0] s_kv_complete,
  input wire [3:0] s_kv_error,
  output wire m_valid, m_error,
  input wire m_ready,
  output wire [2:0] m_accepted,
  output wire [3:0] m_mask,
  output wire [31:0] m_next_token, m_position, committed_position,
  output wire commit_valid
);
  localparam LEGAL=NUM_LAYERS>=1 && NUM_LAYERS<=28 &&
    MAX_SEQ_LEN>=1 && MAX_SEQ_LEN<=32768 &&
    VOCAB_SIZE>=1 && VOCAB_SIZE<=151936;
  generate if (!LEGAL) begin: invalid_parameters
    initial $fatal(1,"ANVIL_Q2_HT2 PARAMETER ERROR: native KV mapping geometry");
    assign s_begin_ready=0; assign active=0; assign input_error=0;
    assign allocator_error=0; assign provisional_pages=0; assign node_depth=0;
    assign r_ready=0; assign r_rsp_valid=0; assign r_rsp_error=0; assign r_page=0;
    assign s_finish_ready=0; assign m_valid=0; assign m_error=0;
    assign m_accepted=0; assign m_mask=0; assign m_next_token=0;
    assign m_position=0; assign committed_position=0; assign commit_valid=0;
  end else begin: implementation
    localparam MAP_ROWS=(MAX_SEQ_LEN+3) >> 2;
    localparam AW=MAP_ROWS<=1 ? 1 : $clog2(MAP_ROWS);
    reg batch_active, batch_bad, finish_sent, new_sequence;
    reg committed_valid, allocation_failed;
    reg [2:0] count;
    reg [127:0] ids;
    reg [7:0] parents, depths;
    reg [15:0] ancestors;
    reg [31:0] position, origin;
    reg [31:0] scratch [0:3], excluded [0:3];
    reg [31:0] cursor;
    reg [3:0] replace_pending;
    reg [1:0] query_state, query_bank;
    reg query_error, query_committed;
    reg [31:0] query_direct, query_result;
    reg [7:0] begin_depth;
    reg [15:0] begin_ancestors;
    reg begin_bad;
    reg query_bad, query_is_committed;
    reg [31:0] query_page;
    reg [2:0] replace_slot;
    reg excluded_candidate, target_bad;
    wire tree_ready, tree_valid, tree_error;
    wire [2:0] tree_accepted;
    wire [3:0] tree_mask;
    wire [31:0] tree_next, tree_position, pointer;
    wire publish=rst_n && !annul && tree_valid && m_ready && !tree_error;
    wire finish_transfer=s_finish_valid && s_finish_ready;
    wire begin_transfer=s_begin_valid && s_begin_ready;
    wire read_transfer=r_valid && r_ready;
    wire [127:0] bank_data;
    wire [3:0] rank0=0;
    wire [3:0] rank1={3'd0,tree_mask[0]};
    wire [3:0] rank2=rank1+{3'd0,tree_mask[1]};
    wire [3:0] rank3=rank2+{3'd0,tree_mask[2]};
    wire [15:0] ranks={rank3,rank2,rank1,rank0};
    wire [31:0] query_limit=position+{30'd0,depths[2*r_slot+:2]};
    integer depth_i, depth_j, query_i, alloc_i, seq_i;
    genvar bank;

    always @* begin
      begin_bad=(s_count!=1 && s_count!=2 && s_count!=4) ||
        s_parent[1:0]!=0 || s_position>=MAX_SEQ_LEN ||
        (!s_new_sequence && s_position!=pointer);
      begin_depth=0;
      begin_ancestors=16'h0001;
      for (depth_i=0;depth_i<4;depth_i=depth_i+1) begin
        if (depth_i<s_count && s_ids[32*depth_i+:32]>=VOCAB_SIZE) begin_bad=1;
        if (depth_i!=0) begin
          begin_ancestors[4*depth_i+:4]=4'b0001 << depth_i;
          if (depth_i<s_count && {30'd0,s_parent[2*depth_i+:2]}>=depth_i) begin_bad=1;
          for (depth_j=0;depth_j<depth_i;depth_j=depth_j+1)
            if (s_parent[2*depth_i+:2]==depth_j) begin
              begin_depth[2*depth_i+:2]=begin_depth[2*depth_j+:2]+2'd1;
              begin_ancestors[4*depth_i+:4]=
                begin_ancestors[4*depth_j+:4] | (4'b0001 << depth_i);
            end
        end
      end
    end

    always @* begin
      query_bad=batch_bad || {1'b0,r_slot}>=count;
      query_is_committed=0;
      query_page=0;
      if (r_position<position) begin
        query_is_committed=1;
        if (new_sequence || !committed_valid ||
            r_position<origin || r_position>=pointer) query_bad=1;
      end else begin
        if (r_position>query_limit) query_bad=1;
        for (query_i=0;query_i<4;query_i=query_i+1)
          if (ancestors[4*r_slot+query_i] && query_i<count &&
              r_position==position+{30'd0,depths[2*query_i+:2]})
            query_page=scratch[query_i];
      end
    end

    always @* begin
      replace_slot=0;
      excluded_candidate=0;
      target_bad=0;
      for (alloc_i=0;alloc_i<4;alloc_i=alloc_i+1) begin
        if (!replace_slot[2] && replace_pending[alloc_i]) replace_slot={1'b1,2'(alloc_i)};
        if (cursor==excluded[alloc_i]) excluded_candidate=1;
        if (alloc_i<count && s_target_ids[32*alloc_i+:32]>=VOCAB_SIZE) target_bad=1;
      end
    end

    for (bank=0;bank<4;bank=bank+1) begin: map_bank
      (* ramstyle = "M20K", nomem2reg *) reg [31:0] memory [0:MAP_ROWS-1];
      reg [31:0] data;
      reg write_enable;
      reg [AW-1:0] write_address;
      reg [31:0] write_data, logical_position;
      integer k;
      assign bank_data[32*bank+:32]=data;
      always @* begin
        write_enable=0; write_address=0; write_data=0; logical_position=0;
        for (k=0;k<4;k=k+1) begin
          logical_position=position+{28'd0,ranks[4*k+:4]};
          if (publish && tree_mask[k] && logical_position[1:0]==bank) begin
            write_enable=1;
            write_address=AW'(logical_position >> 2);
            write_data=scratch[k];
          end
        end
      end
      always @(posedge clk) begin
        if (write_enable) memory[write_address]<=write_data;
        if (read_transfer && query_is_committed && !query_bad)
          data<=memory[AW'(r_position >> 2)];
      end
    end

    anvil_q2_ht2_spec_verifier #(
      .NUM_LAYERS(NUM_LAYERS),.MAX_SEQ_LEN(MAX_SEQ_LEN)
    ) verifier (
      .clk(clk),.rst_n(rst_n),.annul(annul),
      .s_valid(finish_transfer),.s_ready(tree_ready),
      .s_new_sequence(new_sequence),.s_count(count),
      .s_ids(ids),.s_parent(parents),.s_target_ids(s_target_ids),
      .s_position(position),.s_kv_complete(s_kv_complete),
      .s_kv_error(s_kv_error | {4{batch_bad || target_bad}}),
      .m_ready(m_ready),.m_valid(tree_valid),.m_error(tree_error),
      .m_accepted(tree_accepted),.m_mask(tree_mask),
      .m_next_token(tree_next),.m_position(tree_position),
      .committed_position(pointer),.commit_valid(commit_valid));

    assign active=rst_n && !annul && batch_active;
    assign input_error=active && batch_bad;
    assign allocator_error=rst_n && allocation_failed;
    assign provisional_pages=active ? {scratch[3],scratch[2],scratch[1],scratch[0]} :
      128'd0;
    assign node_depth=active ? depths : 8'd0;
    assign s_begin_ready=rst_n && !annul && !batch_active &&
      replace_pending==0 && !allocation_failed && query_state==0 && tree_ready;
    assign r_ready=active && !finish_sent && query_state==0 && !s_finish_valid;
    assign r_rsp_valid=rst_n && !annul && query_state==2;
    assign r_rsp_error=r_rsp_valid && query_error;
    assign r_page=r_rsp_valid && !query_error ? query_result : 32'd0;
    assign s_finish_ready=active && !finish_sent && query_state==0 && tree_ready;
    assign m_valid=tree_valid;
    assign m_error=tree_error;
    assign m_accepted=tree_accepted;
    assign m_mask=tree_mask;
    assign m_next_token=tree_next;
    assign m_position=tree_position;
    assign committed_position=pointer;

    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        batch_active<=0; batch_bad<=0; finish_sent<=0; new_sequence<=0;
        committed_valid<=0; allocation_failed<=0; count<=0;
        ids<=0; parents<=0; depths<=0; ancestors<=0; position<=0; origin<=0;
        cursor<=4; replace_pending<=0;
        query_state<=0; query_bank<=0; query_error<=0; query_committed<=0;
        query_direct<=0; query_result<=0;
        for (seq_i=0;seq_i<4;seq_i=seq_i+1) begin
          scratch[seq_i]<=32'(seq_i); excluded[seq_i]<=32'(seq_i);
        end
      end else if (annul) begin
        batch_active<=0; batch_bad<=0; finish_sent<=0; query_state<=0;
      end else begin
        if (begin_transfer) begin
          batch_active<=1; finish_sent<=0; batch_bad<=begin_bad;
          new_sequence<=s_new_sequence; count<=s_count; ids<=s_ids;
          parents<=s_parent; position<=s_position;
          depths<=begin_depth; ancestors<=begin_ancestors;
        end
        if (finish_transfer) finish_sent<=1;
        if (tree_valid && m_ready) begin
          batch_active<=0;
          finish_sent<=0;
          if (!tree_error) begin
            committed_valid<=1;
            replace_pending<=tree_mask;
            if (new_sequence) begin
              origin<=position;
              cursor<=0;
              for (seq_i=0;seq_i<4;seq_i=seq_i+1) excluded[seq_i]<=scratch[seq_i];
            end else if (!committed_valid) origin<=0;
          end
        end
        if (replace_pending!=0 && !allocation_failed) begin
          if (cursor>=MAX_SEQ_LEN+4) allocation_failed<=1;
          else begin
            cursor<=cursor+32'd1;
            if (!excluded_candidate) begin
              scratch[replace_slot[1:0]]<=cursor;
              replace_pending[replace_slot[1:0]]<=0;
            end
          end
        end
        case (query_state)
          0: if (read_transfer) begin
            query_error<=query_bad;
            query_committed<=query_is_committed;
            query_direct<=query_page;
            query_bank<=r_position[1:0];
            query_state<=1;
          end
          1: begin
            query_result<=query_committed ? bank_data[32*query_bank+:32] : query_direct;
            query_state<=2;
          end
          2: if (r_rsp_ready) query_state<=0;
          default: begin query_error<=1; query_result<=0; query_state<=2; end
        endcase
      end
    end
  end endgenerate
endmodule
