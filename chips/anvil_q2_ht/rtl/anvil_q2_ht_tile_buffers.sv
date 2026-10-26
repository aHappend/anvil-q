module anvil_q2_ht_tile_buffers #(
  parameter TILE_SLOTS=4
) (
  input wire clk, rst_n, flush, drain_complete,
  input wire alloc_valid,
  output wire alloc_ready,
  input wire [2:0] alloc_slot,
  input wire [31:0] alloc_generation,
  input wire alloc_mode,
  input wire operand_valid,
  output wire operand_ready,
  input wire [2:0] operand_slot,
  input wire [31:0] operand_generation,
  input wire [4095:0] operand_activation,
  input wire [127:0] operand_keep,
  input wire meta_valid,
  output wire meta_ready,
  input wire [2:0] meta_slot,
  input wire [31:0] meta_generation,
  input wire [3:0] meta_row,
  input wire [511:0] meta_zero,
  input wire [2047:0] meta_scale,
  input wire fill_valid,
  input wire [2:0] fill_slot,
  input wire [31:0] fill_generation,
  input wire [5:0] fill_beat,
  input wire [511:0] fill_data,
  input wire fill_last, fill_error,
  input wire execute_valid,
  output wire execute_ready,
  input wire [2:0] execute_slot,
  input wire [31:0] execute_generation,
  input wire issue_valid,
  output wire issue_ready,
  input wire [2:0] issue_slot,
  input wire [31:0] issue_generation,
  input wire [3:0] issue_row,
  input wire [63:0] issue_tag,
  input wire release_valid,
  output wire release_ready,
  input wire [2:0] release_slot,
  input wire [31:0] release_generation,
  output wire m_valid,
  input wire m_ready,
  output wire m_mode,
  output wire [127:0] m_keep,
  output wire [4095:0] m_act,
  output wire [511:0] m_w4, m_zero,
  output wire [2047:0] m_scale, m_bf16,
  output wire [63:0] m_tag,
  output wire fault
);
  generate if (TILE_SLOTS<2 || TILE_SLOTS>8) begin: invalid_parameters
    initial $fatal(1,"ANVIL_Q2_HT PARAMETER ERROR: tile slots");
    assign alloc_ready = 0; assign operand_ready = 0; assign meta_ready = 0;
    assign execute_ready = 0; assign issue_ready = 0; assign release_ready = 0;
    assign m_valid = 0; assign m_mode = 0; assign m_keep = 0; assign m_act = 0;
    assign m_w4 = 0; assign m_zero = 0; assign m_scale = 0; assign m_bf16 = 0;
    assign m_tag = 0; assign fault = 0;
  end else begin: implementation
    localparam [2:0] FREE=0, FILLING=1, READY=2, EXECUTING=3, DRAINING=4;
    reg [2:0] state [0:TILE_SLOTS-1];
    reg [31:0] generation [0:TILE_SLOTS-1];
    reg generation_used [0:TILE_SLOTS-1];
    reg mode [0:TILE_SLOTS-1];
    reg [6:0] received [0:TILE_SLOTS-1];
    reg weights_complete [0:TILE_SLOTS-1];
    reg operands_complete [0:TILE_SLOTS-1];
    reg [15:0] metadata_complete [0:TILE_SLOTS-1];
    reg [127:0] keep_mask [0:TILE_SLOTS-1];
    reg failed [0:TILE_SLOTS-1];
    reg data_valid, data_mode;
    reg [2:0] data_slot;
    reg [63:0] data_tag;
    reg [127:0] data_keep;
    reg fault_pulse, draining;
    integer i;
    genvar bank_index, bank_lane;

    wire alloc_in_range = alloc_slot<TILE_SLOTS;
    wire operand_in_range = operand_slot<TILE_SLOTS;
    wire meta_in_range = meta_slot<TILE_SLOTS;
    wire fill_in_range = fill_slot<TILE_SLOTS;
    wire execute_in_range = execute_slot<TILE_SLOTS;
    wire issue_in_range = issue_slot<TILE_SLOTS;
    wire release_in_range = release_slot<TILE_SLOTS;
    wire available = rst_n && !flush && !draining;
    wire allocation = alloc_valid && alloc_ready;
    wire allocation_ok = allocation && alloc_in_range &&
      (!generation_used[alloc_slot] || alloc_generation!=generation[alloc_slot]);
    wire operand_write = operand_valid && operand_ready;
    wire operand_ok = operand_write && operand_in_range &&
      state[operand_slot]==FILLING && generation[operand_slot]==operand_generation &&
      !operands_complete[operand_slot];
    wire metadata_write = meta_valid && meta_ready;
    wire metadata_ok = metadata_write && meta_in_range &&
      state[meta_slot]==FILLING && generation[meta_slot]==meta_generation &&
      !mode[meta_slot] && !metadata_complete[meta_slot][meta_row];
    wire fill_ok = available && fill_valid && fill_in_range &&
      state[fill_slot]==FILLING && generation[fill_slot]==fill_generation &&
      !weights_complete[fill_slot] && received[fill_slot]=={1'b0,fill_beat} &&
      (mode[fill_slot] || fill_beat<16) &&
      (fill_last == (mode[fill_slot] ? fill_beat==63 : fill_beat==15));
    wire execution = execute_valid && execute_ready;
    wire execution_ok = execution && execute_in_range &&
      state[execute_slot]==READY && generation[execute_slot]==execute_generation;
    wire issue = issue_valid && issue_ready;
    wire issue_ok = issue && issue_in_range && state[issue_slot]==EXECUTING &&
      generation[issue_slot]==issue_generation;
    wire release_transfer = release_valid && release_ready;
    wire release_ok = release_transfer && release_in_range &&
      state[release_slot]==EXECUTING && generation[release_slot]==release_generation;
    wire read_advance = available && (!data_valid || m_ready);
    wire [6:0] write_address = mode[fill_slot] ?
      {fill_slot,fill_beat[5:2]} : {fill_slot,fill_beat[3:0]};
    wire [6:0] meta_address = {meta_slot,meta_row};
    wire [6:0] read_address = {issue_slot,issue_row};

    assign alloc_ready = available && (!alloc_in_range || state[alloc_slot]==FREE);
    assign operand_ready = available;
    assign meta_ready = available;
    assign execute_ready = available && (!execute_in_range ||
      state[execute_slot]!=FILLING);
    assign issue_ready = read_advance;
    assign release_ready = available && !(data_valid && !m_ready &&
      data_slot==release_slot) && !(issue_valid && issue_slot==release_slot);
    assign m_valid = available && data_valid;
    assign m_mode = m_valid && data_mode;
    assign m_keep = m_valid ? data_keep : 128'd0;
    assign m_tag = m_valid ? data_tag : 64'd0;
    assign fault = rst_n && fault_pulse;

    for (bank_index=0; bank_index<16; bank_index=bank_index+1) begin: banks
      for (bank_lane=0; bank_lane<8; bank_lane=bank_lane+1) begin: slices
        localparam J = bank_index+16*bank_lane;
        localparam QUARTER = J >> 5;
        localparam WORD = J & 31;
        (* ramstyle = "M20K, no_rw_check" *)
        reg [15:0] weight_ram [0:TILE_SLOTS*16-1];
        (* ramstyle = "M20K, no_rw_check" *)
        reg [19:0] metadata_ram [0:TILE_SLOTS*16-1];
        (* ramstyle = "M20K, no_rw_check" *)
        reg [31:0] activation_ram [0:TILE_SLOTS-1];
        reg [15:0] weight_read;
        reg [19:0] metadata_read;
        reg [31:0] activation_read;

        // RAM contents and read registers need no reset; validity gates all outputs.
        always @(posedge clk) begin
          if (fill_ok) begin
            if (!mode[fill_slot]) weight_ram[write_address] <= {12'd0,fill_data[J*4+:4]};
            else if (fill_beat[1:0]==QUARTER)
              weight_ram[write_address] <= fill_data[WORD*16+:16];
          end
          if (metadata_ok)
            metadata_ram[meta_address] <= {meta_scale[J*16+:16],meta_zero[J*4+:4]};
          if (operand_ok)
            activation_ram[operand_slot] <= operand_activation[J*32+:32];
          if (issue_ok) begin
            weight_read <= weight_ram[read_address];
            metadata_read <= metadata_ram[read_address];
            activation_read <= activation_ram[issue_slot];
          end
        end
        assign m_act[J*32+:32] = m_valid ? activation_read : 32'd0;
        assign m_w4[J*4+:4] = m_valid && !data_mode ? weight_read[3:0] : 4'd0;
        assign m_bf16[J*16+:16] = m_valid && data_mode ? weight_read : 16'd0;
        assign m_zero[J*4+:4] = m_valid && !data_mode ? metadata_read[3:0] : 4'd0;
        assign m_scale[J*16+:16] = m_valid && !data_mode ? metadata_read[19:4] : 16'd0;
      end
    end

    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        data_valid <= 0; data_mode <= 0; data_slot <= 0; data_tag <= 0;
        data_keep <= 0; fault_pulse <= 0; draining <= 0;
        for (i=0; i<TILE_SLOTS; i=i+1) begin
          state[i] <= FREE; generation[i] <= 0; generation_used[i] <= 0;
          mode[i] <= 0; received[i] <= 0; weights_complete[i] <= 0;
          operands_complete[i] <= 0; metadata_complete[i] <= 0;
          keep_mask[i] <= 0; failed[i] <= 0;
        end
      end else begin
        fault_pulse <= 0;
        if (flush || draining) begin
          data_valid <= 0;
          if (drain_complete && !flush) begin
            draining <= 0;
            for (i=0; i<TILE_SLOTS; i=i+1) state[i] <= FREE;
          end else begin
            draining <= 1;
            for (i=0; i<TILE_SLOTS; i=i+1)
              if (state[i]!=FREE) state[i] <= DRAINING;
          end
        end else begin
          if (read_advance) begin
            data_valid <= issue_ok;
            if (issue_ok) begin
              data_slot <= issue_slot;
              data_tag <= issue_tag;
              data_mode <= mode[issue_slot];
              data_keep <= keep_mask[issue_slot];
            end
          end
          for (i=0; i<TILE_SLOTS; i=i+1)
            if (state[i]==FILLING && weights_complete[i] && operands_complete[i] &&
                (mode[i] || (&metadata_complete[i])) && !failed[i])
              state[i] <= READY;
          if (allocation) begin
            if (!allocation_ok) fault_pulse <= 1;
            else begin
              state[alloc_slot] <= FILLING;
              generation[alloc_slot] <= alloc_generation;
              generation_used[alloc_slot] <= 1;
              mode[alloc_slot] <= alloc_mode;
              received[alloc_slot] <= 0;
              weights_complete[alloc_slot] <= 0;
              operands_complete[alloc_slot] <= 0;
              metadata_complete[alloc_slot] <= 0;
              keep_mask[alloc_slot] <= 0;
              failed[alloc_slot] <= 0;
            end
          end
          if (operand_write) begin
            if (!operand_ok) fault_pulse <= 1;
            else begin
              operands_complete[operand_slot] <= 1;
              keep_mask[operand_slot] <= operand_keep;
            end
          end
          if (metadata_write) begin
            if (!metadata_ok) fault_pulse <= 1;
            else metadata_complete[meta_slot][meta_row] <= 1;
          end
          if (fill_valid) begin
            if (!fill_ok) fault_pulse <= 1;
            else begin
              received[fill_slot] <= received[fill_slot]+7'd1;
              if (fill_last) weights_complete[fill_slot] <= 1;
              if (fill_error) begin
                failed[fill_slot] <= 1;
                fault_pulse <= 1;
              end
            end
          end
          if (execution) begin
            if (!execution_ok) fault_pulse <= 1;
            else state[execute_slot] <= EXECUTING;
          end
          if (issue && !issue_ok) fault_pulse <= 1;
          if (release_transfer) begin
            if (!release_ok) fault_pulse <= 1;
            else state[release_slot] <= FREE;
          end
        end
      end
    end
  end endgenerate
endmodule
