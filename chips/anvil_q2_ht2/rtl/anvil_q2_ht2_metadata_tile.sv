module anvil_q2_ht2_metadata_tile #(
  parameter GROUP_SIZE=128
) (
  input wire clk, rst_n, annul, s_valid,
  output wire s_ready,
  input wire [511:0] s_descriptor,
  input wire [31:0] s_row, s_col,
  input wire s_sparse,
  input wire [3:0] s_token_mask,
  input wire [8191:0] s_act,
  input wire [511:0] s_keep,
  input wire [63:0] s_tag,
  output wire m_valid,
  input wire m_ready,
  output wire m_error, m_skipped,
  output wire [1:0] m_format,
  output wire [32:0] m_address,
  output wire [511:0] m_zero, m_keep,
  output wire [2047:0] m_scale,
  output wire [63:0] m_tag,
  output wire idle,
  output wire mem_valid,
  input wire mem_ready,
  output wire [32:0] mem_address,
  input wire mem_rsp_valid, mem_rsp_error,
  output wire mem_rsp_ready,
  input wire [511:0] mem_rsp_data
);
  localparam LEGAL=GROUP_SIZE>=1 && GROUP_SIZE<=128 &&
    (GROUP_SIZE & (GROUP_SIZE-1))==0;
  generate if (!LEGAL) begin: invalid_parameters
    initial $fatal(1,"ANVIL_Q2_HT2 PARAMETER ERROR: metadata group size");
    assign s_ready=0; assign m_valid=0; assign m_error=0; assign m_skipped=0;
    assign m_format=0; assign m_address=0; assign m_zero=0; assign m_keep=0;
    assign m_scale=0; assign m_tag=0; assign idle=0; assign mem_valid=0;
    assign mem_address=0; assign mem_rsp_ready=0;
  end else begin: implementation
    localparam GROUP_SHIFT=$clog2(GROUP_SIZE);
    localparam GROUPS=128 >> GROUP_SHIFT;
    localparam [4:0] IDLE=0, UNION=1, PRODUCTS=2, ADDRESS=3, BOUNDS=4,
      GROUP_SELECT=5, GROUP_ADDRESS=6, ZERO_LOOKUP=7, ZERO_EXTRACT=8,
      SCALE_LOOKUP=9, SCALE_EXTRACT=10, EXPAND=11,
      REQUEST=12, WAIT_MEMORY=13, RESPONSE=14, DRAIN=15, COLUMN=16;
    reg [4:0] state, continuation;
    reg [511:0] descriptor;
    reg [31:0] row, col;
    reg [1:0] format;
    reg sparse, failed, skipped;
    reg [3:0] tokens;
    reg [8191:0] activations;
    reg [511:0] keep, effective_keep, zeros;
    reg [127:0] required;
    reg [2047:0] scales;
    reg [63:0] tag;
    reg [7:0] group_index;
    reg [31:0] absolute_group;
    reg [63:0] row_offset, zero_offset, scale_offset;
    reg [63:0] payload_address, zero_row, scale_row, payload_end;
    reg [64:0] extent_end;
    reg [63:0] zero_address, scale_address;
    reg [3:0] zero_code;
    reg [15:0] scale_word;
    reg cache_target;
    reg [32:0] request_address;
    reg [1:0] cached;
    reg [26:0] cache_line [0:1];
    reg [511:0] cache_data [0:1];
    reg [511:0] union_keep;
    reg [127:0] union_lanes;
    reg illegal_keep, group_required;
    integer t, j, group_j, lane;
    wire available=rst_n && !annul;
    wire [31:0] rows=descriptor[256+:32];
    wire [31:0] cols=descriptor[288+:32];
    wire [31:0] stride=descriptor[320+:32];
    wire [31:0] zero_stride=descriptor[352+:32];
    wire [31:0] scale_stride=descriptor[384+:32];
    wire [31:0] flags=descriptor[416+:32];
    wire [31:0] groups=cols >> GROUP_SHIFT;
    wire [31:0] remaining=cols-col;
    wire [31:0] tile_columns=remaining<128 ? remaining : 32'd128;
    wire [31:0] column_offset=format<2 ? col << 1 :
      (format==2 ? col >> 1 : col >> 2);
    wire [31:0] tile_bytes=format<2 ? tile_columns << 1 :
      (format==2 ? (tile_columns+1) >> 1 : (tile_columns+3) >> 2);
    wire [31:0] zero_row_bytes=format==2 ? (groups+1) >> 1 : (groups+3) >> 2;
    wire [31:0] payload_row_bytes=format<2 ? cols << 1 :
      (format==2 ? (cols+1) >> 1 : (cols+3) >> 2);
    wire [4:0] zero_bit=format==2 ? {1'b0,absolute_group[0],2'd0} :
      {1'b0,absolute_group[1:0],1'b0};
    wire [7:0] zero_byte=cache_data[0][zero_address[5:0]*8+:8];
    wire [7:0] shifted_zero=zero_byte >> zero_bit;
    wire last_zero_byte=format==2 ? (absolute_group >> 1)==((groups-1) >> 1) :
      (absolute_group >> 2)==((groups-1) >> 2);
    wire [3:0] padding_start=format==2 ? {groups[0],2'd0} :
      {groups[1:0],1'b0};
    wire bad_zero_padding=last_zero_byte && padding_start!=0 &&
      (zero_byte >> padding_start)!=0;
    wire [15:0] selected_scale=cache_data[1][scale_address[5:0]*8+:16];
    wire [64:0] zero_address_end={1'b0,zero_address}+65'd1;
    wire [64:0] scale_address_end={1'b0,scale_address}+65'd2;
    wire metadata_address_bad=zero_address_end>65'h200000000 ||
      scale_address_end>65'h200000000;
    wire fill_transfer=mem_rsp_valid && mem_rsp_ready;

    always @* begin
      union_keep=0; union_lanes=0; illegal_keep=0;
      for (t=0;t<4;t=t+1)
        for (j=0;j<128;j=j+1) begin
          if (tokens[t] && keep[128*t+j]) begin
            if ({1'b0,col}+33'(j)>={1'b0,cols}) illegal_keep=1;
            else begin
              union_keep[128*t+j]=!sparse ||
                (|activations[(128*t+j)*16+:15]);
              union_lanes[j]=union_lanes[j] || union_keep[128*t+j];
            end
          end
        end
    end
    always @* begin
      group_required=0;
      for (group_j=0;group_j<128;group_j=group_j+1)
        if ((group_j >> GROUP_SHIFT)==group_index && required[group_j])
          group_required=1;
    end

    assign s_ready=available && state==IDLE;
    assign m_valid=available && state==RESPONSE;
    assign m_error=m_valid && failed;
    assign m_skipped=m_valid && !failed && skipped;
    assign m_format=m_valid ? format : 2'd0;
    assign m_address=m_valid && !failed ? payload_address[32:0] : 33'd0;
    assign m_zero=m_valid && !failed ? zeros : 512'd0;
    assign m_keep=m_valid && !failed ? effective_keep : 512'd0;
    assign m_scale=m_valid && !failed ? scales : 2048'd0;
    assign m_tag=m_valid ? tag : 64'd0;
    assign idle=rst_n && state==IDLE;
    assign mem_valid=available && state==REQUEST;
    assign mem_address=mem_valid ? request_address : 33'd0;
    assign mem_rsp_ready=rst_n && (state==WAIT_MEMORY || state==DRAIN);

    always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
        state<=IDLE; continuation<=IDLE; descriptor<=0; row<=0; col<=0;
        format<=0; sparse<=0; failed<=0; skipped<=0; tokens<=0;
        activations<=0; keep<=0; effective_keep<=0; zeros<=0; required<=0;
        scales<=0; tag<=0; group_index<=0; absolute_group<=0;
        row_offset<=0; zero_offset<=0; scale_offset<=0;
        payload_address<=0; zero_row<=0; scale_row<=0; payload_end<=0; extent_end<=0;
        zero_address<=0; scale_address<=0; zero_code<=0; scale_word<=0;
        cache_target<=0; request_address<=0; cached<=0;
        cache_line[0]<=0; cache_line[1]<=0; cache_data[0]<=0; cache_data[1]<=0;
      end else if (annul) begin
        cached<=0;
        if ((state==WAIT_MEMORY || state==DRAIN) && !fill_transfer) state<=DRAIN;
        else state<=IDLE;
      end else case (state)
        IDLE: if (s_valid && s_ready) begin
          descriptor<=s_descriptor; row<=s_row; col<=s_col;
          case (s_descriptor[416+:2])
            1: format<=0;
            2: format<=1;
            0: format<=2;
            default: format<=3;
          endcase
          sparse<=s_sparse; tokens<=s_token_mask; activations<=s_act;
          keep<=s_keep; tag<=s_tag; failed<=0; skipped<=0;
          zeros<=0; scales<=0; group_index<=0; state<=UNION;
        end
        UNION: begin
          effective_keep<=union_keep; required<=union_lanes;
          skipped<=union_lanes==0;
          if (illegal_keep || rows==0 || rows>151936 || row>=rows ||
              cols==0 || cols>8960 || col>=cols || col[6:0]!=0 ||
              (cols & (GROUP_SIZE-1))!=0 ||
              flags!={23'd0,1'b1,6'd0,flags[1:0]} ||
              descriptor[448+:64]!=0) begin
            failed<=1; state<=RESPONSE;
          end else state<=PRODUCTS;
        end
        PRODUCTS: begin
          row_offset<={32'd0,row}*{32'd0,stride};
          zero_offset<={32'd0,row}*{32'd0,zero_stride};
          scale_offset<={32'd0,row}*{32'd0,scale_stride};
          state<=ADDRESS;
        end
        ADDRESS: begin
          payload_address<=descriptor[0+:64]+row_offset;
          zero_row<=descriptor[128+:64]+zero_offset;
          scale_row<=descriptor[192+:64]+scale_offset;
          payload_end<=row_offset+{32'd0,column_offset};
          extent_end<={1'b0,descriptor[0+:64]}+{1'b0,descriptor[64+:64]};
          state<=COLUMN;
        end
        COLUMN: begin
          payload_address<=payload_address+{32'd0,column_offset};
          payload_end<=payload_end+{32'd0,tile_bytes};
          state<=BOUNDS;
        end
        BOUNDS: begin
          if (stride<payload_row_bytes || payload_end>descriptor[64+:64] ||
              descriptor[64+:64]==0 || extent_end>64'h200000000 ||
              descriptor[0+:64]>64'h1ffffffff ||
              payload_address>64'h1ffffffff ||
              (format<2 && (descriptor[0] || stride[0])) ||
              (format>=2 && (zero_stride<zero_row_bytes ||
                scale_stride<(groups << 1) || descriptor[192] ||
                (|descriptor[161+:31]) || (|descriptor[225+:31]) ||
                scale_stride[0] || zero_row>64'h1ffffffff ||
                scale_row>64'h1ffffffff))) begin
            failed<=1; state<=RESPONSE;
          end else if (skipped || format<2) state<=RESPONSE;
          else state<=GROUP_SELECT;
        end
        GROUP_SELECT: begin
          if (group_required) begin
            absolute_group<=(col >> GROUP_SHIFT)+{24'd0,group_index};
            state<=GROUP_ADDRESS;
          end else if (group_index+8'd1<GROUPS) group_index<=group_index+8'd1;
          else state<=RESPONSE;
        end
        GROUP_ADDRESS: begin
          zero_address<=zero_row+{32'd0,(format==2 ?
            absolute_group >> 1 : absolute_group >> 2)};
          scale_address<=scale_row+{32'd0,(absolute_group << 1)};
          state<=ZERO_LOOKUP;
        end
        ZERO_LOOKUP: begin
          if (metadata_address_bad) begin failed<=1; state<=RESPONSE; end
          else if (cached[0] && cache_line[0]==zero_address[32:6])
            state<=ZERO_EXTRACT;
          else begin
            request_address<={zero_address[32:6],6'd0}; cache_target<=0;
            continuation<=ZERO_EXTRACT; state<=REQUEST;
          end
        end
        ZERO_EXTRACT: begin
          if (bad_zero_padding) begin failed<=1; state<=RESPONSE; end
          else begin
            zero_code<=format==2 ? shifted_zero[3:0] : {2'd0,shifted_zero[1:0]};
            state<=SCALE_LOOKUP;
          end
        end
        SCALE_LOOKUP: begin
          if (cached[1] && cache_line[1]==scale_address[32:6])
            state<=SCALE_EXTRACT;
          else begin
            request_address<={scale_address[32:6],6'd0}; cache_target<=1;
            continuation<=SCALE_EXTRACT; state<=REQUEST;
          end
        end
        SCALE_EXTRACT: begin
          if (selected_scale[14:7]==8'hff) begin failed<=1; state<=RESPONSE; end
          else begin scale_word<=selected_scale; state<=EXPAND; end
        end
        EXPAND: begin
          for (lane=0;lane<128;lane=lane+1)
            if ((lane >> GROUP_SHIFT)==group_index && required[lane]) begin
              zeros[lane*4+:4]<=zero_code; scales[lane*16+:16]<=scale_word;
            end
          if (group_index+8'd1<GROUPS) begin
            group_index<=group_index+8'd1; state<=GROUP_SELECT;
          end else state<=RESPONSE;
        end
        REQUEST: if (mem_ready) state<=WAIT_MEMORY;
        WAIT_MEMORY: if (fill_transfer) begin
          if (mem_rsp_error) begin failed<=1; cached<=0; state<=RESPONSE; end
          else begin
            cache_data[cache_target]<=mem_rsp_data;
            cache_line[cache_target]<=request_address[32:6];
            cached[cache_target]<=1; state<=continuation;
          end
        end
        RESPONSE: if (m_ready) state<=IDLE;
        DRAIN: if (fill_transfer) state<=IDLE;
        default: begin failed<=1; cached<=0; state<=RESPONSE; end
      endcase
    end
  end endgenerate
endmodule
