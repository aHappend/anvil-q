module anvil_q2_ht_ddr_prefetcher #(
  parameter TILE_SLOTS=4,
  parameter READ_OUTSTANDING=8,
  parameter QUEUE_DEPTH=3
) (
  input wire clk, rst_n, flush,
  input wire ddr_ready, ddr_fault,
  input wire [32:0] region_base,
  input wire [33:0] region_end,
  input wire cmd_valid,
  output wire cmd_ready,
  input wire [32:0] cmd_address,
  input wire [6:0] cmd_beats,
  input wire [2:0] cmd_slot,
  input wire [31:0] cmd_generation,
  output wire fill_valid,
  output wire [2:0] fill_slot,
  output wire [31:0] fill_generation,
  output wire [5:0] fill_beat,
  output wire [511:0] fill_data,
  output wire fill_last, fill_error,
  output wire reject_valid,
  output wire [2:0] reject_slot,
  output wire [31:0] reject_generation,
  output wire fault, idle, drained,
  output wire [32:0] avm_address,
  output wire avm_read,
  output wire [4:0] avm_burstcount,
  input wire avm_waitrequest,
  input wire [511:0] avm_readdata,
  input wire avm_readdatavalid,
  input wire [1:0] avm_response
);
  localparam LEGAL = TILE_SLOTS>=2 && TILE_SLOTS<=8 &&
    READ_OUTSTANDING>=1 && READ_OUTSTANDING<=16 &&
    QUEUE_DEPTH>=1 && QUEUE_DEPTH<=16;
  generate if (!LEGAL) begin: invalid_parameters
    initial $fatal(1,"ANVIL_Q2_HT PARAMETER ERROR: prefetch depths");
    assign cmd_ready = 0;
    assign fill_valid = 0; assign fill_slot = 0; assign fill_generation = 0;
    assign fill_beat = 0; assign fill_data = 0; assign fill_last = 0;
    assign fill_error = 0; assign reject_valid = 0;
    assign reject_slot = 0; assign reject_generation = 0;
    assign fault = 0; assign idle = 0; assign drained = 0;
    assign avm_address = 0; assign avm_read = 0; assign avm_burstcount = 0;
  end else begin: implementation
    localparam QW = QUEUE_DEPTH<=1 ? 1 : $clog2(QUEUE_DEPTH);
    localparam RW = READ_OUTSTANDING<=1 ? 1 : $clog2(READ_OUTSTANDING);
    reg [32:0] queue_address [0:QUEUE_DEPTH-1];
    reg [6:0] queue_beats [0:QUEUE_DEPTH-1];
    reg [2:0] queue_slot [0:QUEUE_DEPTH-1];
    reg [31:0] queue_generation [0:QUEUE_DEPTH-1];
    reg [QW-1:0] queue_head, queue_tail;
    reg [4:0] queue_count;
    reg current_valid;
    reg [32:0] current_address;
    reg [6:0] current_remaining;
    reg [5:0] current_offset;
    reg [2:0] current_slot;
    reg [31:0] current_generation;

    reg command_held;
    reg [32:0] held_address;
    reg [4:0] held_count;
    reg [5:0] held_offset;
    reg [2:0] held_slot;
    reg [31:0] held_generation;
    reg held_last;
    reg [2:0] response_slot [0:READ_OUTSTANDING-1];
    reg [31:0] response_generation [0:READ_OUTSTANDING-1];
    reg [5:0] response_offset [0:READ_OUTSTANDING-1];
    reg [4:0] response_count [0:READ_OUTSTANDING-1];
    reg response_last [0:READ_OUTSTANDING-1];
    reg [RW-1:0] response_head, response_tail;
    reg [4:0] outstanding;
    reg [4:0] response_beat;
    reg draining;
    reg fault_pulse, rejected;
    reg [2:0] rejected_slot;
    reg [31:0] rejected_generation;
    integer i;

    wire [33:0] request_end =
      {1'b0,cmd_address}+({27'd0,cmd_beats} << 6);
    wire bad_request = (|cmd_address[5:0]) || cmd_beats==0 || cmd_beats>64 ||
      cmd_slot>=TILE_SLOTS || cmd_address<region_base ||
      request_end>region_end || region_end>34'd8589934592 ||
      region_end<={1'b0,region_base};
    wire accepting = cmd_valid && cmd_ready;
    wire enqueue = accepting && !bad_request;
    wire dequeue = !flush && !draining && !ddr_fault &&
      !current_valid && queue_count!=0;
    wire command_accept = avm_read && !avm_waitrequest;
    wire response_accept = rst_n && avm_readdatavalid && outstanding!=0;
    wire response_finish = response_accept &&
      response_beat+5'd1==response_count[response_head];
    wire [6:0] page_beats = 7'd64-{1'b0,current_address[11:6]};
    wire [6:0] capped_beats = current_remaining>16 ? 7'd16 : current_remaining;
    wire [6:0] next_beats = capped_beats<page_beats ? capped_beats : page_beats;
    wire no_transactions = !command_held && outstanding==0;

    assign cmd_ready = rst_n && !flush && !draining && !ddr_fault &&
      ddr_ready && queue_count<QUEUE_DEPTH;
    assign avm_read = rst_n && command_held;
    assign avm_address = avm_read ? held_address : 33'd0;
    assign avm_burstcount = avm_read ? held_count : 5'd0;
    assign fill_valid = response_accept && !flush && !draining && !ddr_fault;
    assign fill_slot = fill_valid ? response_slot[response_head] : 3'd0;
    assign fill_generation = fill_valid ? response_generation[response_head] : 32'd0;
    assign fill_beat = fill_valid ?
      response_offset[response_head]+{1'b0,response_beat} : 6'd0;
    assign fill_data = fill_valid ? avm_readdata : 512'd0;
    assign fill_last = fill_valid && response_finish && response_last[response_head];
    assign fill_error = fill_valid && avm_response!=0;
    assign reject_valid = rst_n && rejected;
    assign reject_slot = reject_valid ? rejected_slot : 3'd0;
    assign reject_generation = reject_valid ? rejected_generation : 32'd0;
    assign fault = rst_n && fault_pulse;
    assign idle = rst_n && !draining && !flush && queue_count==0 &&
      !current_valid && no_transactions;
    assign drained = rst_n && (flush || draining) && no_transactions;

    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        queue_head <= 0; queue_tail <= 0; queue_count <= 0;
        current_valid <= 0; current_address <= 0; current_remaining <= 0;
        current_offset <= 0; current_slot <= 0; current_generation <= 0;
        command_held <= 0; held_address <= 0; held_count <= 0;
        held_offset <= 0; held_slot <= 0; held_generation <= 0; held_last <= 0;
        response_head <= 0; response_tail <= 0; outstanding <= 0; response_beat <= 0;
        draining <= 0; fault_pulse <= 0; rejected <= 0;
        rejected_slot <= 0; rejected_generation <= 0;
        for (i=0; i<QUEUE_DEPTH; i=i+1) begin
          queue_address[i] <= 0; queue_beats[i] <= 0;
          queue_slot[i] <= 0; queue_generation[i] <= 0;
        end
        for (i=0; i<READ_OUTSTANDING; i=i+1) begin
          response_slot[i] <= 0; response_generation[i] <= 0;
          response_offset[i] <= 0; response_count[i] <= 0; response_last[i] <= 0;
        end
      end else begin
        fault_pulse <= ddr_fault ||
          (avm_readdatavalid && (outstanding==0 || avm_response!=0));
        rejected <= accepting && bad_request;
        if (accepting && bad_request) begin
          rejected_slot <= cmd_slot;
          rejected_generation <= cmd_generation;
          fault_pulse <= 1;
        end

        if (flush || ddr_fault) begin
          draining <= 1;
          queue_head <= 0; queue_tail <= 0; queue_count <= 0;
          current_valid <= 0;
        end else if (draining) begin
          if (no_transactions) draining <= 0;
        end else begin
          case ({enqueue,dequeue})
            2'b10: queue_count <= queue_count+5'd1;
            2'b01: queue_count <= queue_count-5'd1;
            default: begin end
          endcase
          if (enqueue) begin
            queue_address[queue_tail] <= cmd_address;
            queue_beats[queue_tail] <= cmd_beats;
            queue_slot[queue_tail] <= cmd_slot;
            queue_generation[queue_tail] <= cmd_generation;
            if (queue_tail==QUEUE_DEPTH-1) queue_tail <= 0;
            else queue_tail <= queue_tail+1'b1;
          end
          if (dequeue) begin
            current_valid <= 1;
            current_address <= queue_address[queue_head];
            current_remaining <= queue_beats[queue_head];
            current_slot <= queue_slot[queue_head];
            current_generation <= queue_generation[queue_head];
            current_offset <= 0;
            if (queue_head==QUEUE_DEPTH-1) queue_head <= 0;
            else queue_head <= queue_head+1'b1;
          end
          if (!command_held && current_valid &&
              outstanding<READ_OUTSTANDING && ddr_ready) begin
            command_held <= 1;
            held_address <= current_address;
            held_count <= next_beats[4:0];
            held_offset <= current_offset;
            held_slot <= current_slot;
            held_generation <= current_generation;
            held_last <= next_beats==current_remaining;
          end
          if (command_accept) begin
            current_address <= current_address+({28'd0,held_count} << 6);
            current_remaining <= current_remaining-{2'd0,held_count};
            current_offset <= current_offset+{1'b0,held_count};
            if (held_last) current_valid <= 0;
          end
        end

        // Already presented commands remain live even while draining.
        if (command_accept) begin
          command_held <= 0;
          response_slot[response_tail] <= held_slot;
          response_generation[response_tail] <= held_generation;
          response_offset[response_tail] <= held_offset;
          response_count[response_tail] <= held_count;
          response_last[response_tail] <= held_last;
          if (response_tail==READ_OUTSTANDING-1) response_tail <= 0;
          else response_tail <= response_tail+1'b1;
        end
        case ({command_accept,response_finish})
          2'b10: outstanding <= outstanding+5'd1;
          2'b01: outstanding <= outstanding-5'd1;
          default: begin end
        endcase
        if (response_accept) begin
          if (response_finish) begin
            response_beat <= 0;
            if (response_head==READ_OUTSTANDING-1) response_head <= 0;
            else response_head <= response_head+1'b1;
          end else response_beat <= response_beat+5'd1;
        end
      end
    end
  end endgenerate
endmodule
