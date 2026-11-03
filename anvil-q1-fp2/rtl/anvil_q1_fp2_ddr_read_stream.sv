module anvil_q1_fp2_ddr_read_stream (
  input wire clk, rst_n, cmd_valid,
  output wire cmd_ready,
  input wire cmd_format_mx,
  input wire [3:0] cmd_kind,
  input wire [31:0] cmd_layer,
  input wire [2:0] cmd_proj,
  input wire [31:0] cmd_row, cmd_first, cmd_len,
  output wire out_valid,
  input wire out_ready,
  output wire [15:0] out_data,
  output wire out_last,
  output wire [4:0] status,
  output wire done, error, work_active, result_needed,
  output wire fetch_valid,
  input wire fetch_ready,
  output wire fetch_scale,
  output wire [3:0] fetch_kind,
  output wire [31:0] fetch_layer,
  output wire [2:0] fetch_proj,
  output wire [31:0] fetch_row, fetch_col, fetch_tag,
  input wire response_valid,
  output wire response_ready,
  input wire [31:0] response_tag,
  input wire response_write, response_error,
  input wire [511:0] response_data
);
  localparam IDLE=0, SCALE=1, WAIT_SCALE=2, DATA=3, DRAIN=4;
  localparam COMPLETE_WAIT=5, ERROR_WAIT0=6, ERROR_WAIT1=7, FINISH=8;
  reg [3:0] state;
  reg format_mx, failed, drain_request;
  reg [3:0] kind;
  reg [2:0] projection;
  reg [31:0] layer, row;
  reg [32:0] cursor, end_exclusive, next_column, segment_end;
  reg [32:0] issued, retired;
  reg [511:0] scale_plane;
  reg [4:0] flags;
  wire [32:0] command_end={1'b0,cmd_first}+{1'b0,cmd_len};
  wire [32:0] first_scale_end={1'b0,cmd_first[31:11],11'd0}+33'd2048;
  wire [32:0] following_scale_end={1'b0,cursor[31:11],11'd0}+33'd4096;
  wire [31:0] scale_column={5'd0,next_column[31:11],6'd0};
  wire [31:0] expected_column=format_mx ?
    {cursor[31:6],6'd0} : {cursor[31:5],5'd0};
  wire [15:0] bf16_element=response_data[16*cursor[4:0]+:16];
  wire [7:0] mx_element=response_data[8*cursor[5:0]+:8];
  wire [7:0] mx_scale=scale_plane[8*cursor[10:5]+:8];
  wire [4:0] bf16_flags={bf16_element[14:7]==255 &&
    bf16_element[6:0]!=0 && !bf16_element[6],4'd0};
  wire [20:0] decoded=format_mx ? anvil_q1_fp2_pkg::mx_to_bf16(mx_element,mx_scale) :
    {bf16_flags,bf16_element};
  wire vector_last=cursor+1'b1==end_exclusive;
  wire beat_last=vector_last || (format_mx ? (&cursor[5:0]) : (&cursor[4:0]));
  wire segment_last=cursor+1'b1==segment_end;
  wire response_fault=response_valid && (state==WAIT_SCALE || state==DATA) &&
    (response_write || response_error ||
     (state==WAIT_SCALE && response_tag!=scale_column) ||
     (state==DATA && (response_tag!=expected_column || (|decoded[20:18]))));
  wire push=fetch_valid && fetch_ready;
  wire pop=response_valid && response_ready;
  wire transfer=out_valid && out_ready;
  assign cmd_ready=rst_n && state==IDLE;
  assign out_valid=rst_n && state==DATA && response_valid && !response_fault;
  assign out_data=out_valid ? decoded[15:0] : 16'd0;
  assign out_last=out_valid && vector_last;
  assign status=rst_n && (out_valid || done) ?
    (out_valid ? flags | decoded[20:16] : flags) : 5'd0;
  assign done=rst_n && state==FINISH;
  assign error=done && failed;
  assign work_active=rst_n &&
    (state==SCALE || state==WAIT_SCALE || state==DATA || state==DRAIN);
  assign result_needed=rst_n &&
    (state==WAIT_SCALE || (state==DATA && out_ready && !response_valid));
  assign fetch_valid=rst_n &&
    (state==SCALE || (state==DATA && next_column<segment_end) ||
     (state==DRAIN && drain_request));
  assign fetch_scale=fetch_valid && state==SCALE;
  assign fetch_kind=fetch_valid ? kind : 4'd0;
  assign fetch_layer=fetch_valid ? layer : 32'd0;
  assign fetch_proj=fetch_valid ? projection : 3'd0;
  assign fetch_row=fetch_valid ? row : 32'd0;
  assign fetch_col=fetch_valid ?
    (state==SCALE ? scale_column : next_column[31:0]) : 32'd0;
  assign fetch_tag=fetch_col;
  assign response_ready=rst_n &&
    (state==WAIT_SCALE || state==DRAIN || response_fault ||
     (state==DATA && out_ready && beat_last));
  always @(posedge clk) begin
    if (!rst_n) begin
      state<=IDLE; format_mx<=0; failed<=0; drain_request<=0; kind<=0; projection<=0;
      layer<=0; row<=0; cursor<=0; end_exclusive<=0; next_column<=0;
      segment_end<=0; issued<=0; retired<=0; scale_plane<=0; flags<=0;
    end else begin
      if (push) issued<=issued+1'b1;
      if (pop) retired<=retired+1'b1;
      if (response_fault) begin
        failed<=1;
        drain_request<=fetch_valid && !fetch_ready;
        if (state==DATA && !response_error && !response_write &&
            response_tag==expected_column) flags<=flags | decoded[20:16];
        state<=DRAIN;
      end else case (state)
        IDLE: if (cmd_valid) begin
          format_mx<=cmd_format_mx; kind<=cmd_kind; layer<=cmd_layer;
          projection<=cmd_proj; row<=cmd_row; cursor<={1'b0,cmd_first};
          end_exclusive<=command_end; issued<=0; retired<=0; flags<=0;
          failed<=0; drain_request<=0; scale_plane<=0;
          if (cmd_format_mx) begin
            next_column<={1'b0,cmd_first[31:6],6'd0};
            segment_end<=command_end<first_scale_end ? command_end : first_scale_end;
          end else begin
            next_column<={1'b0,cmd_first[31:5],5'd0};
            segment_end<=command_end;
          end
          if (cmd_len==0 || command_end>33'h100000000) begin
            failed<=1; state<=ERROR_WAIT0;
          end else if (cmd_format_mx) state<=SCALE;
          else state<=DATA;
        end
        SCALE: if (push) state<=WAIT_SCALE;
        WAIT_SCALE: if (pop) begin scale_plane<=response_data; state<=DATA; end
        DATA: begin
          if (push) next_column<=next_column+(format_mx ? 33'd64 : 33'd32);
          if (transfer) begin
            flags<=flags | decoded[20:16];
            cursor<=cursor+1'b1;
            if (vector_last) state<=COMPLETE_WAIT;
            else if (segment_last) begin
              segment_end<=end_exclusive<following_scale_end ?
                end_exclusive : following_scale_end;
              state<=SCALE;
            end
          end
        end
        // A fault cannot release descriptor ownership or leave stale completions
        // for the next command. Already accepted requests still retire normally.
        DRAIN: begin
          if (push) drain_request<=0;
          if (!drain_request && issued==retired) state<=ERROR_WAIT0;
        end
        COMPLETE_WAIT: state<=FINISH;
        ERROR_WAIT0: state<=ERROR_WAIT1;
        ERROR_WAIT1: state<=FINISH;
        FINISH: state<=IDLE;
        default: begin failed<=1; state<=DRAIN; end
      endcase
    end
  end
endmodule
