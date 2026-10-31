module anvil_q2_ht2_sparse_w2w4_dma (
  input wire clk, rst_n, annul, s_valid, m_ready,
  input wire [1:0] s_format,
  input wire s_sparse,
  input wire [3:0] s_token_mask,
  input wire [8191:0] s_act,
  input wire [511:0] s_keep,
  input wire [32:0] s_address,
  input wire [511:0] s_zero,
  input wire [2047:0] s_scale,
  input wire [63:0] s_tag,
  input wire mem_ready, fill_valid,
  input wire [511:0] fill_data,
  input wire fill_last, fill_error,
  output wire s_ready, m_valid, m_error,
  output wire [2047:0] m_weight,
  output wire [511:0] m_keep,
  output wire [63:0] m_tag,
  output wire m_skipped, mem_valid,
  output wire [32:0] mem_address,
  output wire [6:0] mem_beats,
  output wire fill_ready
);
  localparam [2:0] IDLE=0, UNION=1, PLAN=2, OFFER=3, READ=4,
    WAIT_RESULT=5, DRAIN=6;
  reg [2:0] state;
  reg [1:0] format;
  reg sparse;
  reg [3:0] tokens;
  reg [8191:0] activations;
  reg [511:0] keep, zeros, request_keep;
  reg [2047:0] scales;
  reg [63:0] tag;
  reg [32:0] address;
  reg [127:0] lane_union;
  reg [4:0] pending, run_mask;
  reg [2:0] run_start, run_length, received;
  reg [2559:0] image;
  reg failed, skipped, planned;
  reg [9:0] response_valid, response_error;
  reg cache_valid;
  reg [32:0] cache_address;
  reg [511:0] cache_data;
  reg [511:0] union_keep;
  reg [127:0] union_lanes;
  reg [4:0] needed;
  reg [2:0] first_beat, length;
  reg [4:0] selected_run;
  reg found, ended;
  reg [2559:0] filled_image, cached_image;
  reg [8:0] byte_offset;
  integer t,j,k,b;

  wire advance=!response_valid[9] || m_ready;
  wire fill_transfer=fill_valid && fill_ready;
  wire [3:0] absolute_beat={1'b0,run_start}+{1'b0,received};
  wire expected_last=received+3'd1==run_length;
  wire bad_fill=failed || fill_error || !expected_last;
  wire [4:0] remaining=pending & ~run_mask;
  wire last_run=remaining==0;
  wire [4:0] candidates=planned ? pending : needed;
  wire [2:0] needed_extent=needed[4] ? 3'd5 : (needed[3] ? 3'd4 :
    (needed[2] ? 3'd3 : (needed[1] ? 3'd2 : (needed[0] ? 3'd1 : 3'd0))));
  wire [33:0] required_end={1'b0,address[32:6],6'd0}+
    {25'd0,needed_extent,6'd0};
  wire bad_address=required_end>34'h200000000;
  wire cached=format==3 && address[5:0]<=32 &&
    cache_valid && cache_address=={address[32:6],6'd0};
  wire all_skipped=lane_union==0;
  wire plan_inject=state==PLAN &&
    (bad_address || all_skipped || (!planned && cached));
  wire fill_inject=state==READ && fill_transfer && fill_last &&
    (last_run || bad_fill);
  wire inject=rst_n && !annul && (plan_inject || fill_inject);
  wire [2559:0] input_image=plan_inject ? cached_image : filled_image;
  wire [2047:0] payload=input_image >> {address[5:0],3'd0};
  wire [2047:0] decoded_weights;
  wire [127:0] decode_errors;
  genvar lane;

  always @* begin
    union_keep=0;
    union_lanes=0;
    for (t=0;t<4;t=t+1)
      for (j=0;j<128;j=j+1) begin
        union_keep[128*t+j]=tokens[t] && keep[128*t+j] &&
          (!sparse || (|activations[(128*t+j)*16+:15]));
        union_lanes[j]=union_lanes[j] || union_keep[128*t+j];
      end
  end

  always @* begin
    needed=0;
    byte_offset=0;
    for (k=0;k<128;k=k+1) begin
      case (format)
        0,1: byte_offset={3'd0,address[5:0]}+9'(k << 1);
        2: byte_offset={3'd0,address[5:0]}+9'(k >> 1);
        default: byte_offset={3'd0,address[5:0]}+9'(k >> 2);
      endcase
      if (lane_union[k]) begin
        case (format)
          0,1: begin
            needed[(int'(address[5:0])+(k << 1)) >> 6]=1;
            needed[(int'(address[5:0])+(k << 1)+1) >> 6]=1;
          end
          default: needed[byte_offset >> 6]=1;
        endcase
      end
    end
  end

  always @* begin
    first_beat=0;
    length=0;
    selected_run=0;
    found=0;
    ended=0;
    for (b=0;b<5;b=b+1) begin
      if (!found && candidates[b]) begin
        found=1;
        first_beat=3'(b);
      end
      if (found && !ended) begin
        if (candidates[b]) begin length=length+3'd1; selected_run[b]=1; end
        else ended=1;
      end
    end
  end

  always @* begin
    filled_image=image;
    if (absolute_beat<5)
      filled_image[absolute_beat*512+:512]=fill_data;
    cached_image=0;
    if (cached && !all_skipped) cached_image[511:0]=cache_data;
  end

  assign s_ready=rst_n && !annul && state==IDLE;
  assign m_valid=rst_n && !annul && response_valid[9];
  assign m_weight=m_valid ? decoded_weights : 2048'd0;
  assign m_keep=m_valid ? request_keep : 512'd0;
  assign m_tag=m_valid ? tag : 64'd0;
  assign m_skipped=m_valid && skipped;
  assign m_error=m_valid && (response_error[9] || (|decode_errors));
  assign mem_valid=rst_n && !annul && state==OFFER;
  assign mem_address=mem_valid ?
    ({address[32:6],6'd0}+{24'd0,run_start,6'd0}) : 33'd0;
  assign mem_beats=mem_valid ? {4'd0,run_length} : 7'd0;
  assign fill_ready=rst_n && (state==READ || state==DRAIN);

  generate for (lane=0;lane<128;lane=lane+1) begin: unpack
    wire [15:0] word_value=format<2 ? payload[lane*16+:16] :
      (format==2 ? {12'd0,payload[lane*4+:4]} :
        {14'd0,payload[lane*2+:2]});
    wire [3:0] zero_value=format==3 ? {2'd0,zeros[lane*4+:2]} :
      zeros[lane*4+:4];
    anvil_q2_ht2_unpack_lane converter (
      .clk(clk),.rst_n(rst_n),.advance(advance),
      .required(lane_union[lane] && !all_skipped),
      .format(format),.word_value(word_value),.zero(zero_value),
      .scale(scales[lane*16+:16]),.weight(decoded_weights[lane*16+:16]),
      .error(decode_errors[lane])
    );
  end endgenerate

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; format<=0; sparse<=0; tokens<=0; activations<=0;
      keep<=0; zeros<=0; request_keep<=0; scales<=0; tag<=0; address<=0;
      lane_union<=0; pending<=0; run_mask<=0; run_start<=0; run_length<=0;
      received<=0; image<=0; failed<=0; skipped<=0; planned<=0;
      response_valid<=0; response_error<=0;
      cache_valid<=0; cache_address<=0; cache_data<=0;
    end else if (annul) begin
      response_valid<=0;
      response_error<=0;
      cache_valid<=0;
      if (state==READ || state==DRAIN) begin
        if (fill_transfer && fill_last) state<=IDLE;
        else state<=DRAIN;
      end else state<=IDLE;
    end else begin
      if (advance) begin
        response_valid<={response_valid[8:0],inject};
        response_error<={response_error[8:0],
          ((fill_inject && bad_fill) || (plan_inject && bad_address))};
      end
      case (state)
        IDLE: if (s_valid && s_ready) begin
          format<=s_format; sparse<=s_sparse; tokens<=s_token_mask;
          activations<=s_act; keep<=s_keep; zeros<=s_zero; scales<=s_scale;
          address<=s_address; tag<=s_tag;
          image<=0; failed<=0; skipped<=0; pending<=0; planned<=0;
          state<=UNION;
        end
        UNION: begin
          request_keep<=union_keep;
          lane_union<=union_lanes;
          state<=PLAN;
        end
        PLAN: begin
          if (plan_inject) begin
            skipped<=all_skipped && !bad_address;
            state<=WAIT_RESULT;
          end else begin
            planned<=1;
            pending<=candidates;
            run_start<=first_beat;
            run_length<=length;
            run_mask<=selected_run;
            received<=0;
            state<=OFFER;
          end
        end
        OFFER: if (mem_ready) state<=READ;
        READ: if (fill_transfer) begin
          if (absolute_beat<5) image<=filled_image;
          if (fill_error || (fill_last!=expected_last)) begin
            failed<=1;
            cache_valid<=0;
          end
          if (fill_last) begin
            if (format==3 && !bad_fill && run_length==1) begin
              cache_valid<=1;
              cache_address<={address[32:6],6'd0}+{24'd0,run_start,6'd0};
              cache_data<=fill_data;
            end
            if (last_run || bad_fill) state<=WAIT_RESULT;
            else begin
              pending<=remaining;
              state<=PLAN;
            end
          end else if (received<7) received<=received+3'd1;
        end
        WAIT_RESULT: if (m_valid && m_ready) state<=IDLE;
        DRAIN: if (fill_transfer && fill_last) state<=IDLE;
        default: begin state<=IDLE; cache_valid<=0; end
      endcase
    end
  end
endmodule
