module anvil_q2_ht_projection #(
  parameter TILE_SLOTS=4,
  parameter GROUP_SIZE=128
) (
  input wire clk, rst_n, flush, resources_drained,
  input wire cmd_valid,
  output wire cmd_ready,
  input wire cmd_mode,
  input wire [511:0] cmd_descriptor,
  output wire idle, done, fault,
  output wire result_valid,
  input wire result_ready,
  output wire [31:0] result_row,
  output wire signed [127:0] result_sum,
  output wire [31:0] result_fp32,
  output wire result_last,
  output wire act_req_valid,
  input wire act_req_ready,
  output wire [31:0] act_req_col,
  input wire act_rsp_valid,
  output wire act_rsp_ready,
  input wire [4095:0] act_rsp_data,
  input wire act_rsp_error,
  output wire prefetch_valid,
  input wire prefetch_ready,
  output wire [32:0] prefetch_address,
  output wire [6:0] prefetch_beats,
  output wire [2:0] prefetch_slot,
  output wire [31:0] prefetch_generation,
  output wire alloc_valid,
  input wire alloc_ready,
  output wire [2:0] alloc_slot,
  output wire [31:0] alloc_generation,
  output wire alloc_mode,
  output wire operand_valid,
  input wire operand_ready,
  output wire [2:0] operand_slot,
  output wire [31:0] operand_generation,
  output wire [4095:0] operand_activation,
  output wire [127:0] operand_keep,
  output wire meta_valid,
  input wire meta_ready,
  output wire [2:0] meta_slot,
  output wire [31:0] meta_generation,
  output wire [3:0] meta_row,
  output wire [511:0] meta_zero,
  output wire [2047:0] meta_scale,
  output wire execute_valid,
  input wire execute_ready,
  output wire [2:0] execute_slot,
  output wire [31:0] execute_generation,
  output wire issue_valid,
  input wire issue_ready,
  output wire [2:0] issue_slot,
  output wire [31:0] issue_generation,
  output wire [3:0] issue_row,
  output wire [63:0] issue_tag,
  output wire release_valid,
  input wire release_ready,
  output wire [2:0] release_slot,
  output wire [31:0] release_generation,
  input wire array_valid, array_mode,
  output wire array_ready,
  input wire signed [127:0] array_sum,
  input wire [31:0] array_fp32,
  input wire [63:0] array_tag,
  input wire array_error,
  output wire mem_req_valid,
  input wire mem_req_ready,
  output wire [32:0] mem_req_addr,
  input wire mem_rsp_valid,
  output wire mem_rsp_ready,
  input wire [511:0] mem_rsp_rdata,
  input wire mem_rsp_error
);
  localparam LEGAL=TILE_SLOTS>=2 && TILE_SLOTS<=8 &&
    GROUP_SIZE>=1 && GROUP_SIZE<=128 && (GROUP_SIZE & (GROUP_SIZE-1))==0;
  generate if (!LEGAL) begin: invalid_parameters
    initial $fatal(1,"ANVIL_Q2_HT PARAMETER ERROR: projection geometry");
    assign cmd_ready=0; assign idle=0; assign done=0; assign fault=0;
    assign result_valid=0; assign result_row=0; assign result_sum=0;
    assign result_fp32=0; assign result_last=0;
    assign act_req_valid=0; assign act_req_col=0; assign act_rsp_ready=0;
    assign prefetch_valid=0; assign prefetch_address=0; assign prefetch_beats=0;
    assign prefetch_slot=0; assign prefetch_generation=0;
    assign alloc_valid=0; assign alloc_slot=0; assign alloc_generation=0;
    assign alloc_mode=0; assign operand_valid=0; assign operand_slot=0;
    assign operand_generation=0; assign operand_activation=0; assign operand_keep=0;
    assign meta_valid=0; assign meta_slot=0; assign meta_generation=0;
    assign meta_row=0; assign meta_zero=0; assign meta_scale=0;
    assign execute_valid=0; assign execute_slot=0; assign execute_generation=0;
    assign issue_valid=0; assign issue_slot=0; assign issue_generation=0;
    assign issue_row=0; assign issue_tag=0;
    assign release_valid=0; assign release_slot=0; assign release_generation=0;
    assign array_ready=0; assign mem_req_valid=0;
    assign mem_req_addr=0; assign mem_rsp_ready=0;
  end else begin: implementation
    localparam GROUP_SHIFT=$clog2(GROUP_SIZE);
    localparam GROUPS_PER_TILE=128 >> GROUP_SHIFT;
    localparam [3:0] M_IDLE=0, M_ROW=1, M_PRODUCT=2, M_ADDRESS=3,
      M_ZERO_REQUEST=4, M_ZERO_RESPONSE=5, M_SCALE_REQUEST=6,
      M_SCALE_RESPONSE=7, M_EXPAND=8, M_SEND=9;
    localparam [2:0] E_EXECUTE=0, E_ISSUE=1, E_RELEASE=2,
      E_GROUP_WAIT=3, E_EMIT=4;
    reg active, flushing, failed, completed, mode;
    reg [31:0] rows, cols, chunks;
    reg [31:0] zero_stride, scale_stride, tile_stride;
    reg [32:0] zero_base, scale_base, next_tile_address;
    reg [23:0] epoch;
    reg [31:0] generation_counter;
    reg [TILE_SLOTS-1:0] occupied, main_sent, operand_sent, metadata_sent;
    reg [31:0] slot_generation [0:TILE_SLOTS-1];
    reg [31:0] slot_col [0:TILE_SLOTS-1];
    reg [31:0] slot_row [0:TILE_SLOTS-1];
    reg [32:0] slot_address [0:TILE_SLOTS-1];
    reg [2:0] allocation_pointer, main_pointer, operand_pointer;
    reg [2:0] metadata_pointer, execution_pointer;
    reg [31:0] allocation_row, allocation_col;
    reg allocation_finished, activation_waiting;
    reg [127:0] activation_keep;
    reg [3:0] metadata_state, metadata_row;
    reg [7:0] metadata_group;
    reg [511:0] expanded_zero;
    reg [2047:0] expanded_scale;
    reg [63:0] zero_product, scale_product;
    reg [32:0] zero_address, scale_address;
    reg [3:0] zero_nibble;
    reg [15:0] scale_word;
    reg [2:0] execution_state;
    reg [3:0] row_issue, row_emit;
    reg [31:0] execution_row, execution_chunk;
    reg [31:0] group_completed;
    reg [15:0] context_valid, context_busy;
    reg signed [127:0] integer_context [0:15];
    reg [31:0] floating_context [0:15];
    reg [7:0] context_next_chunk [0:15];
    reg [3:0] accumulation_valid;
    reg [3:0] accumulation_row [0:3];
    reg [7:0] accumulation_chunk [0:3];
    reg [3:0] accumulation_mode;
    reg [3:0] accumulation_first;
    reg [31:0] accumulation_first_value [0:3];
    integer i, lane;
    genvar activation_lane;

    function automatic [2:0] next_slot(input [2:0] current);
      begin
        if (current==TILE_SLOTS-1) next_slot=0;
        else next_slot=current+3'd1;
      end
    endfunction

    wire running=rst_n && active && !flush && !flushing && !failed;
    wire [31:0] remaining_rows=rows-execution_row;
    wire [31:0] group_rows=remaining_rows>16 ? 32'd16 : remaining_rows;
    wire [31:0] expected_group_results=group_rows*chunks;
    wire [31:0] metadata_output_row=slot_row[metadata_pointer]+
      {28'd0,metadata_row};
    wire [31:0] metadata_input_group=(slot_col[metadata_pointer] >> GROUP_SHIFT)+
      {24'd0,metadata_group};
    wire [31:0] metadata_input_col=slot_col[metadata_pointer]+
      ({24'd0,metadata_group} << GROUP_SHIFT);
    wire reader_cmd_ready, reader_rsp_valid, reader_rsp_error, reader_idle;
    wire [31:0] reader_rsp_data;
    wire reader_cmd_valid=running &&
      (metadata_state==M_ZERO_REQUEST || metadata_state==M_SCALE_REQUEST);
    wire [32:0] reader_address=metadata_state==M_ZERO_REQUEST ?
      {zero_address[32:1],1'b0} : scale_address;
    wire reader_rsp_ready=running &&
      (metadata_state==M_ZERO_RESPONSE || metadata_state==M_SCALE_RESPONSE);
    wire allocation=alloc_valid && alloc_ready;
    wire operand_request=act_req_valid && act_req_ready;
    wire operand_response=operand_valid && operand_ready;
    wire [3:0] returning_row=array_tag[3:0];
    wire returning_tag_valid=array_tag[63:40]==epoch &&
      array_tag[31:4]==execution_row[31:4] &&
      array_tag[31:0]<rows && array_tag[39:32]<chunks &&
      array_tag[39:32]==context_next_chunk[returning_row];
    wire accumulation_accept=array_valid && array_ready;
    wire signed [127:0] integer_add_a=context_valid[returning_row] ?
      integer_context[returning_row] : 128'sd0;
    wire [31:0] floating_add_a=context_valid[returning_row] ?
      floating_context[returning_row] : 32'd0;
    wire signed [127:0] integer_add_result;
    wire [31:0] floating_add_result;
    wire floating_add_error;
    wire local_rst_n=rst_n && !flush && !flushing;
    wire new_command=cmd_valid && cmd_ready;
    wire finishing_group=result_valid && result_ready &&
      {28'd0,row_emit}+32'd1==group_rows;
    wire [63:0] command_base=cmd_descriptor[0+:64];
    wire [63:0] command_length=cmd_descriptor[64+:64];
    wire [63:0] command_zero=cmd_descriptor[128+:64];
    wire [63:0] command_scale=cmd_descriptor[192+:64];
    wire [31:0] command_rows=cmd_descriptor[256+:32];
    wire [31:0] command_cols=cmd_descriptor[288+:32];
    wire [31:0] command_stride=cmd_descriptor[320+:32];
    wire malformed_command=(|command_base[63:33]) || (|command_base[5:0]) ||
      command_rows==0 || command_rows>151936 ||
      command_cols==0 || command_cols>8960 ||
      (command_cols & (GROUP_SIZE-1))!=0 ||
      command_stride<(cmd_mode ? 4096 : 1024) || (|command_stride[5:0]) ||
      command_length==0 ||
      cmd_descriptor[416+:32]!=(cmd_mode ? 32'h102 : 32'h100) ||
      cmd_descriptor[448+:64]!=0 ||
      (!cmd_mode && ((|command_zero[63:33]) || (|command_scale[63:33]) ||
        command_scale[0] || cmd_descriptor[384] ||
        cmd_descriptor[352+:32]<(((command_cols >> GROUP_SHIFT)+1) >> 1) ||
        cmd_descriptor[384+:32]<(command_cols >> GROUP_SHIFT)*2));

    anvil_q2_ht_scalar_reader metadata_reader (
      .clk(clk),.rst_n(rst_n),.invalidate(flush || failed),
      .cmd_valid(reader_cmd_valid),.cmd_ready(reader_cmd_ready),
      .cmd_address(reader_address),.cmd_word32(1'b0),
      .rsp_valid(reader_rsp_valid),.rsp_ready(reader_rsp_ready),
      .rsp_data(reader_rsp_data),.rsp_error(reader_rsp_error),.idle(reader_idle),
      .mem_req_valid(mem_req_valid),.mem_req_ready(mem_req_ready),
      .mem_req_addr(mem_req_addr),.mem_rsp_valid(mem_rsp_valid),
      .mem_rsp_ready(mem_rsp_ready),.mem_rsp_rdata(mem_rsp_rdata),
      .mem_rsp_error(mem_rsp_error));
    anvil_q2_ht_add128_pipe chunk_integer_add (
      .clk(clk),.rst_n(local_rst_n),.advance(1'b1),
      .a(integer_add_a),.b(array_sum),.sum(integer_add_result));
    anvil_q2_ht_fp32_add_pipe chunk_floating_add (
      .clk(clk),.rst_n(local_rst_n),.advance(1'b1),
      .a(floating_add_a),.b(array_fp32),
      .sum(floating_add_result),.error(floating_add_error));

    always @* begin
      activation_keep=0;
      for (lane=0; lane<128; lane=lane+1)
        activation_keep[lane]=slot_col[operand_pointer]+32'(lane)<cols;
    end

    assign cmd_ready=rst_n && !flush && !active && !flushing && !failed &&
      reader_idle && occupied==0;
    assign idle=rst_n && !active && !flushing && !failed && reader_idle &&
      occupied==0;
    assign done=rst_n && completed;
    assign fault=rst_n && failed;
    assign alloc_valid=running && !allocation_finished &&
      !occupied[allocation_pointer];
    assign alloc_slot=alloc_valid ? allocation_pointer : 3'd0;
    assign alloc_generation=alloc_valid ? generation_counter+32'd1 : 32'd0;
    assign alloc_mode=alloc_valid && mode;
    assign prefetch_valid=running && occupied[main_pointer] && !main_sent[main_pointer];
    assign prefetch_slot=prefetch_valid ? main_pointer : 3'd0;
    assign prefetch_generation=prefetch_valid ? slot_generation[main_pointer] : 32'd0;
    assign prefetch_address=prefetch_valid ? slot_address[main_pointer] : 33'd0;
    assign prefetch_beats=prefetch_valid ? (mode ? 7'd64 : 7'd16) : 7'd0;
    assign act_req_valid=running && !activation_waiting &&
      occupied[operand_pointer] && !operand_sent[operand_pointer];
    assign act_req_col=act_req_valid ? slot_col[operand_pointer] : 32'd0;
    assign act_rsp_ready=running && activation_waiting && operand_ready;
    assign operand_valid=running && activation_waiting && act_rsp_valid &&
      !act_rsp_error;
    assign operand_slot=operand_valid ? operand_pointer : 3'd0;
    assign operand_generation=operand_valid ? slot_generation[operand_pointer] : 32'd0;
    for (activation_lane=0; activation_lane<128; activation_lane=activation_lane+1) begin: activation_mask
      assign operand_activation[activation_lane*32+:32]=
        operand_valid && activation_keep[activation_lane] ?
          act_rsp_data[activation_lane*32+:32] : 32'd0;
    end
    assign operand_keep=operand_valid ? activation_keep : 128'd0;
    assign meta_valid=running && metadata_state==M_SEND;
    assign meta_slot=meta_valid ? metadata_pointer : 3'd0;
    assign meta_generation=meta_valid ? slot_generation[metadata_pointer] : 32'd0;
    assign meta_row=meta_valid ? metadata_row : 4'd0;
    assign meta_zero=meta_valid ? expanded_zero : 512'd0;
    assign meta_scale=meta_valid ? expanded_scale : 2048'd0;
    assign execute_valid=running && execution_state==E_EXECUTE &&
      occupied[execution_pointer] && main_sent[execution_pointer] &&
      operand_sent[execution_pointer] && metadata_sent[execution_pointer];
    assign execute_slot=execute_valid ? execution_pointer : 3'd0;
    assign execute_generation=execute_valid ?
      slot_generation[execution_pointer] : 32'd0;
    assign issue_valid=running && execution_state==E_ISSUE;
    assign issue_slot=issue_valid ? execution_pointer : 3'd0;
    assign issue_generation=issue_valid ? slot_generation[execution_pointer] : 32'd0;
    assign issue_row=issue_valid ? row_issue : 4'd0;
    assign issue_tag=issue_valid ?
      {epoch,execution_chunk[7:0],(execution_row+{28'd0,row_issue})} : 64'd0;
    assign release_valid=running && execution_state==E_RELEASE;
    assign release_slot=release_valid ? execution_pointer : 3'd0;
    assign release_generation=release_valid ?
      slot_generation[execution_pointer] : 32'd0;
    assign array_ready=running && !context_busy[returning_row];
    assign result_valid=running && execution_state==E_EMIT;
    assign result_row=result_valid ? execution_row+{28'd0,row_emit} : 32'd0;
    assign result_sum=result_valid && !mode ? integer_context[row_emit] : 128'sd0;
    assign result_fp32=result_valid && mode ? floating_context[row_emit] : 32'd0;
    assign result_last=result_valid && result_row+32'd1==rows;

    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        active<=0; flushing<=0; failed<=0; completed<=0; mode<=0;
        rows<=0; cols<=0; chunks<=0; zero_stride<=0; scale_stride<=0;
        tile_stride<=0; zero_base<=0; scale_base<=0; next_tile_address<=0;
        epoch<=0; generation_counter<=0; occupied<=0; main_sent<=0;
        operand_sent<=0; metadata_sent<=0; allocation_pointer<=0;
        main_pointer<=0; operand_pointer<=0; metadata_pointer<=0;
        execution_pointer<=0; allocation_row<=0; allocation_col<=0;
        allocation_finished<=0; activation_waiting<=0;
        metadata_state<=M_IDLE; metadata_row<=0; metadata_group<=0;
        expanded_zero<=0; expanded_scale<=0; zero_product<=0; scale_product<=0;
        zero_address<=0; scale_address<=0; zero_nibble<=0; scale_word<=0;
        execution_state<=E_EXECUTE; row_issue<=0; row_emit<=0;
        execution_row<=0; execution_chunk<=0; group_completed<=0;
        context_valid<=0; context_busy<=0;
        accumulation_valid<=0; accumulation_mode<=0; accumulation_first<=0;
        for (i=0; i<TILE_SLOTS; i=i+1) begin
          slot_generation[i]<=0; slot_col[i]<=0; slot_row[i]<=0; slot_address[i]<=0;
        end
        for (i=0; i<16; i=i+1) begin
          integer_context[i]<=0; floating_context[i]<=0; context_next_chunk[i]<=0;
        end
        for (i=0; i<4; i=i+1) begin
          accumulation_row[i]<=0; accumulation_chunk[i]<=0;
          accumulation_first_value[i]<=0;
        end
      end else begin
        completed<=0;
        if (flush) begin
          active<=0; flushing<=1; failed<=0;
          occupied<=0; main_sent<=0; operand_sent<=0; metadata_sent<=0;
          activation_waiting<=0; metadata_state<=M_IDLE;
          accumulation_valid<=0; context_busy<=0; context_valid<=0;
        end else if (flushing) begin
          if (resources_drained && reader_idle) flushing<=0;
        end else if (new_command) begin
          if (malformed_command) failed<=1;
          else begin
            active<=1; mode<=cmd_mode; rows<=command_rows; cols<=command_cols;
            chunks<=(command_cols+32'd127) >> 7;
            zero_stride<=cmd_descriptor[352+:32];
            scale_stride<=cmd_descriptor[384+:32];
            tile_stride<=command_stride;
            zero_base<=command_zero[32:0]; scale_base<=command_scale[32:0];
            next_tile_address<=command_base[32:0];
            epoch<=epoch+24'd1;
            allocation_pointer<=0; main_pointer<=0; operand_pointer<=0;
            metadata_pointer<=0; execution_pointer<=0;
            allocation_row<=0; allocation_col<=0; allocation_finished<=0;
            execution_state<=E_EXECUTE; execution_row<=0; execution_chunk<=0;
            row_issue<=0; row_emit<=0; group_completed<=0;
            context_valid<=0; context_busy<=0; accumulation_valid<=0;
            metadata_state<=M_IDLE; activation_waiting<=0;
            for (i=0; i<16; i=i+1) context_next_chunk[i]<=0;
          end
        end else if (running) begin
          accumulation_valid<={accumulation_valid[2:0],accumulation_accept};
          accumulation_mode<={accumulation_mode[2:0],array_mode};
          accumulation_first<={accumulation_first[2:0],!context_valid[returning_row]};
          accumulation_row[0]<=returning_row;
          accumulation_chunk[0]<=array_tag[39:32];
          accumulation_first_value[0]<=array_fp32;
          for (i=1; i<4; i=i+1) begin
            accumulation_row[i]<=accumulation_row[i-1];
            accumulation_chunk[i]<=accumulation_chunk[i-1];
            accumulation_first_value[i]<=accumulation_first_value[i-1];
          end
          if (accumulation_accept) begin
            if (!returning_tag_valid || array_error || array_mode!=mode) failed<=1;
            context_busy[returning_row]<=1;
          end
          if (accumulation_valid[3]) begin
            context_busy[accumulation_row[3]]<=0;
            context_valid[accumulation_row[3]]<=1;
            integer_context[accumulation_row[3]]<=integer_add_result;
            floating_context[accumulation_row[3]]<=accumulation_first[3] ?
              accumulation_first_value[3] : floating_add_result;
            context_next_chunk[accumulation_row[3]]<=accumulation_chunk[3]+8'd1;
            group_completed<=group_completed+32'd1;
            if (accumulation_mode[3] && !accumulation_first[3] &&
                floating_add_error) failed<=1;
          end
          if (allocation) begin
            occupied[allocation_pointer]<=1;
            main_sent[allocation_pointer]<=0;
            operand_sent[allocation_pointer]<=0;
            metadata_sent[allocation_pointer]<=mode;
            slot_generation[allocation_pointer]<=generation_counter+32'd1;
            generation_counter<=generation_counter+32'd1;
            slot_row[allocation_pointer]<=allocation_row;
            slot_col[allocation_pointer]<=allocation_col;
            slot_address[allocation_pointer]<=next_tile_address;
            next_tile_address<=next_tile_address+{1'b0,tile_stride};
            allocation_pointer<=next_slot(allocation_pointer);
            if (allocation_col+32'd128<cols) allocation_col<=allocation_col+32'd128;
            else begin
              allocation_col<=0;
              if (allocation_row+32'd16<rows) allocation_row<=allocation_row+32'd16;
              else allocation_finished<=1;
            end
          end
          if (prefetch_valid && prefetch_ready) begin
            main_sent[main_pointer]<=1;
            main_pointer<=next_slot(main_pointer);
          end
          if (operand_request) activation_waiting<=1;
          if (act_rsp_valid && act_rsp_ready && act_rsp_error) failed<=1;
          if (operand_response) begin
            activation_waiting<=0;
            operand_sent[operand_pointer]<=1;
            operand_pointer<=next_slot(operand_pointer);
          end

          if (!mode) case (metadata_state)
            M_IDLE: if (occupied[metadata_pointer] && !metadata_sent[metadata_pointer])
              begin metadata_row<=0; metadata_state<=M_ROW; end
            M_ROW: begin
              expanded_zero<=0; expanded_scale<=0; metadata_group<=0;
              if (metadata_output_row>=rows) metadata_state<=M_SEND;
              else metadata_state<=M_PRODUCT;
            end
            M_PRODUCT: begin
              zero_product<={32'd0,metadata_output_row}*{32'd0,zero_stride};
              scale_product<={32'd0,metadata_output_row}*{32'd0,scale_stride};
              metadata_state<=M_ADDRESS;
            end
            M_ADDRESS: begin
              zero_address<=33'({31'd0,zero_base}+zero_product+
                {32'd0,(metadata_input_group >> 1)});
              scale_address<=33'({31'd0,scale_base}+scale_product+
                ({32'd0,metadata_input_group} << 1));
              metadata_state<=M_ZERO_REQUEST;
            end
            M_ZERO_REQUEST: if (reader_cmd_ready) metadata_state<=M_ZERO_RESPONSE;
            M_ZERO_RESPONSE: if (reader_rsp_valid) begin
              if (reader_rsp_error) failed<=1;
              else begin
                zero_nibble<=reader_rsp_data[
                  ({4'd0,zero_address[0]} << 3)+
                  ({4'd0,metadata_input_group[0]} << 2)+:4];
                metadata_state<=M_SCALE_REQUEST;
              end
            end
            M_SCALE_REQUEST: if (reader_cmd_ready) metadata_state<=M_SCALE_RESPONSE;
            M_SCALE_RESPONSE: if (reader_rsp_valid) begin
              if (reader_rsp_error) failed<=1;
              else begin
                scale_word<=reader_rsp_data[15:0];
                metadata_state<=M_EXPAND;
              end
            end
            M_EXPAND: begin
              for (i=0; i<128; i=i+1)
                if ((i >> GROUP_SHIFT)==metadata_group &&
                    slot_col[metadata_pointer]+32'(i)<cols) begin
                  expanded_zero[i*4+:4]<=zero_nibble;
                  expanded_scale[i*16+:16]<=scale_word;
                end
              if (metadata_group+8'd1<GROUPS_PER_TILE &&
                  metadata_input_col+GROUP_SIZE<cols) begin
                metadata_group<=metadata_group+8'd1;
                metadata_state<=M_PRODUCT;
              end else metadata_state<=M_SEND;
            end
            M_SEND: if (meta_valid && meta_ready) begin
              if (metadata_row==15) begin
                metadata_sent[metadata_pointer]<=1;
                metadata_pointer<=next_slot(metadata_pointer);
                metadata_state<=M_IDLE;
              end else begin metadata_row<=metadata_row+4'd1; metadata_state<=M_ROW; end
            end
            default: failed<=1;
          endcase

          case (execution_state)
            E_EXECUTE: if (execute_valid && execute_ready) begin
              if (slot_row[execution_pointer]!=execution_row ||
                  slot_col[execution_pointer]!=(execution_chunk << 7)) failed<=1;
              row_issue<=0; execution_state<=E_ISSUE;
            end
            E_ISSUE: if (issue_valid && issue_ready) begin
              if ({28'd0,row_issue}+32'd1==group_rows) execution_state<=E_RELEASE;
              else row_issue<=row_issue+4'd1;
            end
            E_RELEASE: if (release_valid && release_ready) begin
              occupied[execution_pointer]<=0;
              execution_pointer<=next_slot(execution_pointer);
              if (execution_chunk+32'd1<chunks) begin
                execution_chunk<=execution_chunk+32'd1;
                execution_state<=E_EXECUTE;
              end else execution_state<=E_GROUP_WAIT;
            end
            E_GROUP_WAIT: if (group_completed==expected_group_results) begin
              row_emit<=0; execution_state<=E_EMIT;
            end
            E_EMIT: if (result_valid && result_ready) begin
              if (finishing_group) begin
                if (execution_row+group_rows==rows) begin active<=0; completed<=1; end
                else begin
                  execution_row<=execution_row+32'd16;
                  execution_chunk<=0; group_completed<=0;
                  context_valid<=0; context_busy<=0;
                  for (i=0; i<16; i=i+1) context_next_chunk[i]<=0;
                  execution_state<=E_EXECUTE;
                end
              end else row_emit<=row_emit+4'd1;
            end
            default: failed<=1;
          endcase
        end
      end
    end
  end endgenerate
endmodule
