module anvil_q2_ht2_payload_prefetch (
  input wire clk, rst_n, annul, s_valid,
  output wire s_ready,
  input wire [1:0] s_format,
  input wire [32:0] s_address,
  input wire [511:0] s_keep,
  input wire [3:0] s_token_mask,
  output wire m_valid,
  input wire m_ready,
  output wire m_error,
  output wire [2559:0] m_image,
  output wire idle,
  output wire mem_valid,
  input wire mem_ready,
  output wire [32:0] mem_address,
  output wire [6:0] mem_beats,
  input wire fill_valid, fill_error, fill_last,
  input wire [511:0] fill_data,
  output wire fill_ready
);
  localparam [2:0] IDLE=0, PLAN=1, SELECT=2, REQUEST=3,
    READ=4, RESPONSE=5, DRAIN=6;
  reg [2:0] state, first, length, received;
  reg [1:0] format;
  reg [32:0] address, cache_address;
  reg [511:0] keep, cache_data;
  reg [3:0] tokens;
  reg [2559:0] image;
  reg [4:0] pending, run;
  reg failed, cache_valid;
  reg [4:0] needed, selected;
  reg [2:0] selected_first, selected_length;
  reg found, ended;
  integer lane, slot, beat, offset;
  reg required;
  wire available=rst_n && !annul;
  wire fill_transfer=fill_valid && fill_ready;
  wire expected_last=received+3'd1==length;
  wire [3:0] image_beat={1'b0,first}+{1'b0,received};
  wire [4:0] remaining=pending & ~run;
  wire [32:0] aligned={address[32:6],6'd0};
  wire [2:0] extent=needed[4] ? 3'd5 : (needed[3] ? 3'd4 :
    (needed[2] ? 3'd3 : (needed[1] ? 3'd2 : (needed[0] ? 3'd1 : 3'd0))));
  wire [33:0] end_address={1'b0,aligned}+{25'd0,extent,6'd0};
  wire cache_hit=format==3 && needed==5'b00001 &&
    cache_valid && cache_address==aligned;

  always @* begin
    needed=0; required=0; offset=0;
    for (lane=0;lane<128;lane=lane+1) begin
      required=0;
      for (slot=0;slot<4;slot=slot+1)
        required=required || (tokens[slot] && keep[128*slot+lane]);
      case (format)
        0,1: offset=int'(address[5:0])+(lane << 1);
        2: offset=int'(address[5:0])+(lane >> 1);
        default: offset=int'(address[5:0])+(lane >> 2);
      endcase
      if (required) begin
        needed[offset >> 6]=1;
        if (format<2) needed[(offset+1) >> 6]=1;
      end
    end
  end
  always @* begin
    selected=0; selected_first=0; selected_length=0; found=0; ended=0;
    for (beat=0;beat<5;beat=beat+1) begin
      if (!found && pending[beat]) begin found=1; selected_first=3'(beat); end
      if (found && !ended) begin
        if (pending[beat]) begin
          selected[beat]=1; selected_length=selected_length+3'd1;
        end else ended=1;
      end
    end
  end
  assign s_ready=available && state==IDLE;
  assign idle=rst_n && state==IDLE;
  assign m_valid=available && state==RESPONSE;
  assign m_error=m_valid && failed;
  assign m_image=m_valid && !failed ? image : 2560'd0;
  assign mem_valid=available && state==REQUEST;
  assign mem_address=mem_valid ? aligned+{24'd0,first,6'd0} : 33'd0;
  assign mem_beats=mem_valid ? {4'd0,length} : 7'd0;
  assign fill_ready=rst_n && (state==READ || state==DRAIN);

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; first<=0; length<=0; received<=0; format<=0;
      address<=0; keep<=0; tokens<=0; image<=0; pending<=0; run<=0;
      failed<=0; cache_valid<=0; cache_address<=0; cache_data<=0;
    end else if (annul) begin
      cache_valid<=0;
      if ((state==READ || state==DRAIN) && !(fill_transfer && fill_last))
        state<=DRAIN;
      else state<=IDLE;
    end else case (state)
      IDLE: if (s_valid) begin
        address<=s_address; format<=s_format; keep<=s_keep;
        tokens<=s_token_mask; image<=0; failed<=0; state<=PLAN;
      end
      PLAN: begin
        if (end_address>34'h200000000) begin
          failed<=1; state<=RESPONSE;
        end else if (needed==0) state<=RESPONSE;
        else if (cache_hit) begin image[511:0]<=cache_data; state<=RESPONSE; end
        else begin pending<=needed; state<=SELECT; end
      end
      SELECT: begin
        first<=selected_first; length<=selected_length; run<=selected;
        received<=0; state<=REQUEST;
      end
      REQUEST: if (mem_ready) state<=READ;
      READ: if (fill_transfer) begin
        if (image_beat<5) image[512*image_beat+:512]<=fill_data;
        if (fill_error || fill_last!=expected_last) begin failed<=1; cache_valid<=0; end
        if (fill_last) begin
          if (failed || fill_error || !expected_last || remaining==0) state<=RESPONSE;
          else begin pending<=remaining; state<=SELECT; end
          if (format==3 && length==1 && !failed && !fill_error && expected_last) begin
            cache_valid<=1; cache_address<=aligned+{24'd0,first,6'd0};
            cache_data<=fill_data;
          end
        end else if (received<7) received<=received+3'd1;
      end
      RESPONSE: if (m_ready) state<=IDLE;
      DRAIN: if (fill_transfer && fill_last) state<=IDLE;
      default: begin failed<=1; cache_valid<=0; state<=RESPONSE; end
    endcase
  end
endmodule
