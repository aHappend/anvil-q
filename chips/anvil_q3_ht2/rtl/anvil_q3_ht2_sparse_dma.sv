module anvil_q3_ht2_sparse_dma #(
  parameter MAX_COLUMNS = 11008
) (
  input wire clk, rst_n, flush,
  input wire cmd_valid,
  output wire cmd_ready,
  input wire [31:0] cmd_epoch, cmd_layer,
  input wire [2:0] cmd_proj,
  input wire [32:0] cmd_qweight_base,
  input wire [31:0] cmd_output_count, cmd_row_base, cmd_columns,
  input wire [3:0] cmd_token_mask,
  input wire cmd_sparse_enable,
  input wire [15:0] cmd_threshold_f16,
  input wire act_valid,
  output wire act_ready,
  input wire [31:0] act_column,
  input wire [63:0] act_f16,
  output wire tile_valid,
  input wire tile_ready,
  output wire [31:0] tile_columns,
  output wire [127:0] tile_row_mask,
  output wire memory_req_valid,
  input wire memory_req_ready,
  output wire [32:0] memory_req_address,
  output wire [7:0] memory_req_burstcount,
  input wire memory_rsp_valid, memory_rsp_error,
  input wire [511:0] memory_rsp_rdata,
  output wire weight_valid,
  input wire weight_ready,
  output wire [31:0] weight_column,
  output wire [511:0] weight_data,
  output wire [63:0] weight_activation_f16,
  output wire [3:0] weight_keep_mask,
  output wire weight_last,
  output wire done, error, idle, drain_done, fault,
  output wire [31:0] scanned_columns, skipped_columns, issued_weight_beats
);
  localparam LEGAL = MAX_COLUMNS > 0 && 64'(MAX_COLUMNS) <= 64'hffffffff;
  generate if (!LEGAL) begin: invalid_parameters
    initial $fatal(1, "ANVIL_Q3_HT2 PARAMETER ERROR: MAX_COLUMNS");
    assign cmd_ready = 1'b0;
    assign act_ready = 1'b0;
    assign tile_valid = 1'b0;
    assign tile_columns = 32'd0;
    assign tile_row_mask = 128'd0;
    assign memory_req_valid = 1'b0;
    assign memory_req_address = 33'd0;
    assign memory_req_burstcount = 8'd0;
    assign weight_valid = 1'b0;
    assign weight_column = 32'd0;
    assign weight_data = 512'd0;
    assign weight_activation_f16 = 64'd0;
    assign weight_keep_mask = 4'd0;
    assign weight_last = 1'b0;
    assign done = 1'b0;
    assign error = 1'b0;
    assign idle = 1'b0;
    assign drain_done = 1'b0;
    assign fault = 1'b0;
    assign scanned_columns = 32'd0;
    assign skipped_columns = 32'd0;
    assign issued_weight_beats = 32'd0;
  end else begin: datapath
    localparam IDLE=0, EXTENT_ROUND=1, EXTENT_END=2, COMMAND_CHECK=3,
      SCAN=4, DESCRIPTOR=5, SELECT=6, SELECT_CHECK=7, ADDRESS_PRODUCT=8,
      ADDRESS_PACKED=9, ADDRESS_LINES=10, REQUEST=11, WAIT_RETURN=12,
      NORMALIZE=13, OPERAND=14, FINISH=15, COMPLETE=16, DRAIN=17,
      DRAIN_FINISH=18, FAULTED=19;
    reg [4:0] state;
    reg failed, cancelled, outstanding;
    reg [31:0] epoch, layer, columns, output_count, row_base;
    reg [2:0] projection;
    reg [3:0] token_mask;
    reg sparse;
    reg [14:0] threshold;
    reg [32:0] matrix_base;
    reg [63:0] matrix_bytes, matrix_allocation, matrix_end, packed_base;
    reg [31:0] stride, rows, span_words;
    reg [127:0] row_mask;
    reg command_bad;
    reg [31:0] ingest_index, scan_count, skip_count, physical_count, retained;
    reg capture_valid, predicate_valid, capture_bad, predicate_bad;
    reg [31:0] capture_column, predicate_column;
    reg [63:0] capture_activation, predicate_activation;
    reg [3:0] predicate_keep;
    reg [31:0] cursor, selected_column, emitted;
    reg [63:0] stride_product, packed_start;
    reg [63:0] selected_activation;
    reg [3:0] selected_keep;
    reg [32:0] line_address;
    reg two_lines, line_number;
    reg [511:0] operand_data;
    reg [63:0] operand_activation;
    reg [3:0] operand_keep;
    reg [31:0] operand_column;
    reg operand_last;
    (* ramstyle = "M20K", nomem2reg *) reg [3:0] keep_ram [0:MAX_COLUMNS-1];
    reg [3:0] keep_q;
    wire [63:0] activation_q;
    wire enabled = rst_n && !flush;
    wire command_fire = cmd_valid && cmd_ready;
    wire activation_fire = act_valid && act_ready;
    wire request_fire = memory_req_valid && memory_req_ready;
    wire response_known = outstanding || request_fire;
    wire response_fire = enabled && memory_rsp_valid && response_known;
    wire response_fault = memory_rsp_valid &&
      (!response_known || memory_rsp_error);
    wire pipeline_fault = state == SCAN &&
      ((capture_valid && capture_bad) || (predicate_valid && predicate_bad));
    wire fault_now = response_fault || pipeline_fault;
    wire ram_write = enabled && state == SCAN && predicate_valid &&
      !predicate_bad && !fault_now;
    wire ram_read = enabled && state == SELECT && !fault_now;
    wire [63:0] command_remaining = {32'd0,cmd_output_count} -
      {32'd0,cmd_row_base};
    wire [31:0] command_rows = command_remaining > 128 ?
      32'd128 : command_remaining[31:0];
    wire [63:0] command_last_row = {32'd0,cmd_row_base} +
      {32'd0,command_rows} - 64'd1;
    wire [63:0] rounded_bytes = (matrix_bytes + 64'd63) &
      64'hffffffffffffffc0;
    wire [63:0] first_line = packed_start & 64'hffffffffffffffc0;
    wire [7:0] span_bytes = {1'b0,span_words[4:0],2'b00};
    wire crossing = {2'b0,packed_start[5:0]} + span_bytes > 8'd64;
    wire [63:0] line_end = first_line + (crossing ? 64'd128 : 64'd64);
    wire line_bad = packed_start < {31'd0,matrix_base} ||
      first_line < {31'd0,matrix_base} || line_end > matrix_end ||
      line_end > 64'h60000000 || span_words == 0 || span_words > 17;
    reg [3:0] calculated_keep;
    reg calculated_bad;
    reg [63:0] active_capture;
    wire [511:0] normalized_data;
    integer token, mask_row;

    function automatic [2:0] awq_position(input [2:0] row);
      begin
        case (row)
          0: awq_position=0;
          1: awq_position=4;
          2: awq_position=1;
          3: awq_position=5;
          4: awq_position=2;
          5: awq_position=6;
          6: awq_position=3;
          default: awq_position=7;
        endcase
      end
    endfunction

    always @* begin
      active_capture = 0;
      calculated_keep = 0;
      calculated_bad = 0;
      for (token=0; token<4; token=token+1) begin
        if (token_mask[token]) begin
          active_capture[token*16+:16] = act_f16[token*16+:16];
          if (capture_activation[token*16+10+:5] == 5'b11111)
            calculated_bad = 1;
          if (!sparse || projection != 6 ||
              capture_activation[token*16+:15] > threshold)
            calculated_keep[token] = 1;
`ifndef SYNTHESIS
          if ((^capture_activation[token*16+:16]) === 1'bx)
            calculated_bad = 1;
`endif
        end
      end
    end

    genvar bank;
    for (bank=0; bank<4; bank=bank+1) begin: activation_banks
      (* ramstyle = "M20K", nomem2reg *) reg [15:0] data [0:MAX_COLUMNS-1];
      reg [15:0] data_q;
      always @(posedge clk) begin
        if (ram_write)
          data[predicate_column] <= predicate_activation[bank*16+:16];
        if (ram_read)
          data_q <= data[cursor];
      end
      assign activation_q[bank*16+:16] = data_q;
    end
    always @(posedge clk) begin
      if (ram_write) keep_ram[predicate_column] <= predicate_keep;
      if (ram_read) keep_q <= keep_ram[cursor];
    end

    wire [31:0] source_word [0:16];
    genvar word_bank;
    for (word_bank=0; word_bank<17; word_bank=word_bank+1) begin: source_banks
      reg [31:0] data;
      reg owner_line;
      reg [3:0] owner_word;
      wire [5:0] descriptor_word = {2'b0,packed_start[5:2]} + 6'(word_bank);
      always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
          owner_line <= 0;
          owner_word <= 0;
        end else if (flush) begin
          owner_line <= 0;
          owner_word <= 0;
        end else if (state == ADDRESS_LINES && !fault_now) begin
          owner_line <= descriptor_word[4];
          owner_word <= descriptor_word[3:0];
        end
      end
      always @(posedge clk) begin
        if (response_fire && !memory_rsp_error && !fault_now &&
            (state == REQUEST || state == WAIT_RETURN) &&
            owner_line == line_number && word_bank < span_words)
          data <= memory_rsp_rdata[{owner_word,5'd0}+:32];
      end
      assign source_word[word_bank] = data;
    end
    genvar local_row;
    for (local_row=0; local_row<128; local_row=local_row+1) begin: local_rows
      wire [3:0] offset = {1'b0,row_base[2:0]} + 4'(local_row & 7);
      wire [31:0] word_data = offset[3] ?
        source_word[(local_row >> 3)+1] : source_word[local_row >> 3];
      wire [2:0] nibble = awq_position(offset[2:0]);
      localparam LOCAL_BIT = (local_row >> 3)*32 +
        ((local_row & 7)==0 ? 0 : (local_row & 7)==1 ? 16 :
         (local_row & 7)==2 ? 4 : (local_row & 7)==3 ? 20 :
         (local_row & 7)==4 ? 8 : (local_row & 7)==5 ? 24 :
         (local_row & 7)==6 ? 12 : 28);
      assign normalized_data[LOCAL_BIT+:4] = local_row < rows ?
        word_data[{nibble,2'b00}+:4] : 4'd0;
    end

    assign cmd_ready = enabled && state == IDLE && !failed &&
      !memory_rsp_valid;
    assign act_ready = enabled && state == SCAN && ingest_index < columns &&
      !failed && !fault_now;
    assign tile_valid = enabled && state == DESCRIPTOR && !failed &&
      !fault_now;
    assign tile_columns = tile_valid ? retained : 32'd0;
    assign tile_row_mask = tile_valid ? row_mask : 128'd0;
    assign memory_req_valid = enabled && state == REQUEST && !failed;
    assign memory_req_address = memory_req_valid ? line_address : 33'd0;
    assign memory_req_burstcount = memory_req_valid ? 8'd1 : 8'd0;
    assign weight_valid = enabled && state == OPERAND && !failed &&
      !fault_now;
    assign weight_column = weight_valid ? operand_column : 32'd0;
    assign weight_data = weight_valid ? operand_data : 512'd0;
    assign weight_activation_f16 = weight_valid ? operand_activation : 64'd0;
    assign weight_keep_mask = weight_valid ? operand_keep : 4'd0;
    assign weight_last = weight_valid && operand_last;
    assign done = enabled && state == COMPLETE && !cancelled;
    assign error = done && failed;
    assign idle = enabled && state == IDLE && !failed && !outstanding;
    assign drain_done = enabled && state == DRAIN_FINISH && cancelled;
    assign fault = enabled && failed;
    assign scanned_columns = enabled ? scan_count : 32'd0;
    assign skipped_columns = enabled ? skip_count : 32'd0;
    assign issued_weight_beats = enabled ? physical_count : 32'd0;

    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        state <= IDLE;
        failed <= 0; cancelled <= 0; outstanding <= 0;
        epoch <= 0; layer <= 0; projection <= 0; columns <= 0;
        output_count <= 0; row_base <= 0; token_mask <= 0;
        sparse <= 0; threshold <= 0; matrix_base <= 0;
        matrix_bytes <= 0; matrix_allocation <= 0; matrix_end <= 0; packed_base <= 0;
        stride <= 0; rows <= 0; span_words <= 0; row_mask <= 0;
        command_bad <= 0; ingest_index <= 0; scan_count <= 0;
        skip_count <= 0; physical_count <= 0; retained <= 0;
        capture_valid <= 0; predicate_valid <= 0;
        capture_bad <= 0; predicate_bad <= 0;
        capture_column <= 0; predicate_column <= 0;
        capture_activation <= 0; predicate_activation <= 0; predicate_keep <= 0;
        cursor <= 0; selected_column <= 0; emitted <= 0;
        stride_product <= 0; packed_start <= 0; selected_activation <= 0;
        selected_keep <= 0; line_address <= 0; two_lines <= 0; line_number <= 0;
        operand_data <= 0; operand_activation <= 0; operand_keep <= 0;
        operand_column <= 0; operand_last <= 0;
      end else begin
        // Read ownership survives flush; only an actual return releases it.
        if (request_fire && !memory_rsp_valid) outstanding <= 1;
        if (memory_rsp_valid && response_known) outstanding <= 0;
        if (flush) begin
          state <= DRAIN;
          failed <= 0;
          cancelled <= 1;
          capture_valid <= 0; predicate_valid <= 0;
          capture_bad <= 0; predicate_bad <= 0;
          capture_column <= 0; predicate_column <= 0;
          capture_activation <= 0; predicate_activation <= 0; predicate_keep <= 0;
          epoch <= 0; layer <= 0; projection <= 0; columns <= 0;
          output_count <= 0; row_base <= 0; token_mask <= 0;
          sparse <= 0; threshold <= 0; matrix_base <= 0;
          matrix_bytes <= 0; matrix_allocation <= 0; matrix_end <= 0; packed_base <= 0;
          stride <= 0; rows <= 0; span_words <= 0; row_mask <= 0;
          command_bad <= 0; ingest_index <= 0; scan_count <= 0;
          skip_count <= 0; physical_count <= 0; retained <= 0;
          cursor <= 0; selected_column <= 0; emitted <= 0;
          stride_product <= 0; packed_start <= 0; selected_activation <= 0;
          selected_keep <= 0; line_address <= 0; two_lines <= 0; line_number <= 0;
          operand_data <= 0; operand_activation <= 0; operand_keep <= 0;
          operand_column <= 0; operand_last <= 0;
        end else begin
          if (request_fire) physical_count <= physical_count + 1'b1;
          if (fault_now) begin
            failed <= 1;
            cancelled <= 0;
            state <= DRAIN;
            capture_valid <= 0;
            predicate_valid <= 0;
          end else begin
            capture_valid <= activation_fire;
            predicate_valid <= capture_valid;
            if (activation_fire) begin
              capture_column <= act_column;
              capture_activation <= active_capture;
              capture_bad <= act_column != ingest_index;
              ingest_index <= ingest_index + 1'b1;
`ifndef SYNTHESIS
              if ((^act_column) === 1'bx) capture_bad <= 1;
`endif
            end
            if (capture_valid) begin
              predicate_column <= capture_column;
              predicate_activation <= capture_activation;
              predicate_keep <= calculated_keep;
              predicate_bad <= capture_bad || calculated_bad;
            end
            case (state)
              IDLE: if (command_fire) begin
                cancelled <= 0;
                epoch <= cmd_epoch; layer <= cmd_layer; projection <= cmd_proj;
                columns <= cmd_columns; output_count <= cmd_output_count;
                row_base <= cmd_row_base; token_mask <= cmd_token_mask;
                sparse <= cmd_sparse_enable; threshold <= cmd_threshold_f16[14:0];
                matrix_base <= cmd_qweight_base;
                stride <= cmd_output_count >> 1;
                matrix_bytes <= {32'd0,cmd_columns} *
                  {32'd0,(cmd_output_count >> 1)};
                rows <= command_rows;
                span_words <= (command_last_row >> 3) -
                  ({32'd0,cmd_row_base} >> 3) + 64'd1;
                for (mask_row=0; mask_row<128; mask_row=mask_row+1)
                  row_mask[mask_row] <= mask_row < command_rows;
                command_bad <= cmd_columns == 0 || cmd_columns > MAX_COLUMNS ||
                  cmd_output_count == 0 || cmd_output_count[2:0] != 0 ||
                  cmd_row_base >= cmd_output_count || cmd_token_mask == 0 ||
                  cmd_proj > 6 || cmd_qweight_base[5:0] != 0 ||
                  cmd_threshold_f16[14:10] == 5'b11111 ||
                  (cmd_threshold_f16[15] && cmd_threshold_f16[14:0] != 0);
`ifndef SYNTHESIS
                if ((^{cmd_epoch,cmd_layer,cmd_proj,cmd_qweight_base,
                        cmd_output_count,cmd_row_base,cmd_columns,cmd_token_mask,
                        cmd_sparse_enable,cmd_threshold_f16}) === 1'bx)
                  command_bad <= 1;
`endif
                ingest_index <= 0; scan_count <= 0; skip_count <= 0;
                physical_count <= 0; retained <= 0; emitted <= 0; cursor <= 0;
                state <= EXTENT_ROUND;
              end
              EXTENT_ROUND: begin
                matrix_allocation <= rounded_bytes;
                state <= EXTENT_END;
              end
              EXTENT_END: begin
                matrix_end <= {31'd0,matrix_base} + matrix_allocation;
                packed_base <= {31'd0,matrix_base} +
                  ({32'd0,(row_base >> 3)} << 2);
                state <= COMMAND_CHECK;
              end
              COMMAND_CHECK: begin
                if (command_bad || matrix_end > 64'h60000000 ||
                    matrix_end <= {31'd0,matrix_base}) begin
                  failed <= 1;
                  state <= DRAIN;
                end else state <= SCAN;
              end
              SCAN: if (predicate_valid) begin
                scan_count <= scan_count + 1'b1;
                if (predicate_keep == 0) skip_count <= skip_count + 1'b1;
                else retained <= retained + 1'b1;
                if (scan_count + 1'b1 == columns) state <= DESCRIPTOR;
              end
              DESCRIPTOR: if (tile_valid && tile_ready) begin
                if (retained == 0) state <= FINISH;
                else state <= SELECT;
              end
              SELECT: begin
                selected_column <= cursor;
                state <= SELECT_CHECK;
              end
              SELECT_CHECK: begin
                if (keep_q == 0) begin
                  if (cursor + 1'b1 >= columns) begin
                    failed <= 1;
                    state <= DRAIN;
                  end else begin
                    cursor <= cursor + 1'b1;
                    state <= SELECT;
                  end
                end else begin
                  selected_activation <= activation_q;
                  selected_keep <= keep_q;
                  state <= ADDRESS_PRODUCT;
                end
              end
              ADDRESS_PRODUCT: begin
                stride_product <= {32'd0,selected_column} * {32'd0,stride};
                state <= ADDRESS_PACKED;
              end
              ADDRESS_PACKED: begin
                packed_start <= packed_base + stride_product;
                state <= ADDRESS_LINES;
              end
              ADDRESS_LINES: begin
                if (line_bad) begin
                  failed <= 1;
                  state <= DRAIN;
                end else begin
                  line_address <= first_line[32:0];
                  two_lines <= crossing;
                  line_number <= 0;
                  state <= REQUEST;
                end
              end
              REQUEST: if (request_fire) begin
                if (response_fire) begin
                  if (two_lines && !line_number) begin
                    line_address <= line_address + 33'd64;
                    line_number <= 1;
                  end else state <= NORMALIZE;
                end else state <= WAIT_RETURN;
              end
              WAIT_RETURN: if (response_fire) begin
                if (two_lines && !line_number) begin
                  line_address <= line_address + 33'd64;
                  line_number <= 1;
                  state <= REQUEST;
                end else state <= NORMALIZE;
              end
              NORMALIZE: begin
                operand_data <= normalized_data;
                operand_activation <= selected_activation;
                operand_keep <= selected_keep;
                operand_column <= selected_column;
                operand_last <= emitted + 1'b1 == retained;
                state <= OPERAND;
              end
              OPERAND: if (weight_valid && weight_ready) begin
                emitted <= emitted + 1'b1;
                if (operand_last) state <= FINISH;
                else begin
                  cursor <= selected_column + 1'b1;
                  state <= SELECT;
                end
              end
              FINISH: state <= COMPLETE;
              COMPLETE: begin
                if (failed) state <= FAULTED;
                else state <= IDLE;
              end
              DRAIN: if (!outstanding) state <= DRAIN_FINISH;
              DRAIN_FINISH: begin
                if (cancelled) state <= IDLE;
                else state <= COMPLETE;
              end
              FAULTED: state <= FAULTED;
              default: begin
                failed <= 1;
                state <= DRAIN;
              end
            endcase
          end
        end
      end
    end
  end endgenerate
endmodule
