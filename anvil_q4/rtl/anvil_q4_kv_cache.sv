module anvil_q4_kv_cache (
  input wire clk, rst_n, flush, cmd_valid,
  output wire cmd_ready,
  input wire cmd_write, cmd_value, cmd_allow_current,
  input wire [31:0] cmd_layer, cmd_pos, cmd_head, cmd_dimension, cmd_epoch,
  input wire [31:0] committed_tokens, context_capacity,
  input wire [31:0] protected_epoch, protected_tokens,
  input wire [31:0] kv_heads, head_dim, hidden, intermediate,
  input wire cache_int8,
  input wire [31:0] page_tokens, physical_pages,
  output wire out_valid,
  input wire out_ready,
  output wire [31:0] result,
  output wire error,
  output wire mem_req_valid,
  input wire mem_req_ready,
  output wire mem_req_write,
  output wire [3:0] mem_req_kind,
  output wire [31:0] mem_req_layer,
  output wire [2:0] mem_req_proj,
  output wire [31:0] mem_req_row, mem_req_col, mem_req_wdata, mem_req_stride,
  input wire mem_rsp_valid,
  output wire mem_rsp_ready,
  input wire [31:0] mem_rsp_rdata,
  input wire mem_rsp_error
);
  import anvil_q4_fp_pkg::*;
  localparam [5:0] IDLE=0, GEOMETRY=1, PAGE_READ=2, PAGE_WAIT=3,
    ALIAS_NEXT=4, ALIAS_READ=5, ALIAS_WAIT=6, BEGIN_ACCESS=7,
    READ_SCALE=8, READ_SCALE_WAIT=9, READ_PAYLOAD=10, READ_PAYLOAD_WAIT=11,
    CONVERT_ISSUE=12, CONVERT_WAIT=13, DECODE_ISSUE=14, DECODE_WAIT=15,
    SOURCE_READ=16, SOURCE_WAIT=17, SCALE_ISSUE=18, SCALE_WAIT=19,
    WRITE_SCALE=20, WRITE_SCALE_WAIT=21, RATIO_ISSUE=22, RATIO_WAIT=23,
    ENCODE=24, WRITE_PAYLOAD=25, WRITE_PAYLOAD_WAIT=26,
    NEXT_SCALAR=27, NEXT_HEAD=28, RESPONSE=29,
    PROTECTED_NEXT=30, PROTECTED_READ=31, PROTECTED_WAIT=32,
    PREPARE_PAYLOAD=33, READ_ESCAPE=34, READ_ESCAPE_WAIT=35;
  reg [5:0] state;
  reg writing, value_select, allow_current, int8_mode, failed, scanning;
  reg escaping, payload_escape;
  reg [31:0] layer, position, epoch, count, capacity, heads, dimension;
  reg [31:0] stride, pages, page_size, logical_page, physical_page, physical_row;
  reg [31:0] page_count, alias_index, requested_head, requested_dimension;
  reg [31:0] retained_epoch, retained_pages;
  reg [4:0] page_shift;
  reg [31:0] head, scalar, global_index, head_base, kd, packed_stride;
  reg [31:0] scale_register, maximum, operand, result_register;
  reg [31:0] packed_word, write_word, payload_col;
  wire [16:0] configured_kd=kv_heads[7:0]*head_dim[8:0];
  reg [4:0] configured_shift;
  reg valid_page_size;
  always @* begin
    valid_page_size=1;
    case (page_tokens)
      1: configured_shift=0;
      2: configured_shift=1;
      4: configured_shift=2;
      8: configured_shift=3;
      16: configured_shift=4;
      32: configured_shift=5;
      default: begin configured_shift=0; valid_page_size=0; end
    endcase
  end
  wire port_idle, complete, fault;
  wire [31:0] rdata;
  wire page_read=state==PAGE_READ || state==ALIAS_READ || state==PROTECTED_READ;
  wire scale_read=state==READ_SCALE;
  wire source_read=state==SOURCE_READ;
  wire payload_read=state==READ_PAYLOAD || state==READ_ESCAPE;
  wire scale_write=state==WRITE_SCALE;
  wire payload_write=state==WRITE_PAYLOAD;
  wire escape_access=state==READ_ESCAPE || (payload_write && payload_escape);
  wire memory_write=scale_write || payload_write;
  wire issue=(page_read || scale_read || source_read || payload_read || memory_write) && port_idle;
  wire [3:0] payload_kind=int8_mode ?
    (value_select ? 4'd13 : 4'd12) : (value_select ? 4'd10 : 4'd9);
  wire [3:0] request_kind=page_read ? 4'd15 : source_read ? 4'd8 :
    scale_read || scale_write ? 4'd14 : payload_kind;
  wire [31:0] request_col=page_read ? 32'd0 : scale_read || scale_write ? head :
    source_read ? global_index : payload_col;
  wire [31:0] request_stride=page_read ? 32'd1 : source_read ? stride :
    scale_read || scale_write ? heads :
    int8_mode && !escape_access ? packed_stride : kd;
  wire [31:0] request_row=page_read ?
    (state==ALIAS_READ || state==PROTECTED_READ ? alias_index : logical_page) :
    source_read ? (value_select ? 32'd4 : 32'd3) : physical_row;
  anvil_q4_mem_port memory_port (
    .clk(clk),.rst_n(rst_n),.flush(flush),.issue(issue),
    .idle(port_idle),.complete(complete),.fault(fault),
    .write(memory_write),.kind(request_kind),
    .layer(page_read ? (state==PROTECTED_READ ? retained_epoch : epoch) :
      source_read ? 32'd0 : layer),
    .proj(((scale_read || scale_write) && value_select) || escape_access ? 3'd1 : 3'd0),
    .row(request_row),.col(request_col),
    .wdata(scale_write ? scale_register : payload_write ? write_word : 32'd0),
    .stride(request_stride),.rdata(rdata),
    .mem_req_valid(mem_req_valid),.mem_req_ready(mem_req_ready),
    .mem_req_write(mem_req_write),.mem_req_kind(mem_req_kind),
    .mem_req_layer(mem_req_layer),.mem_req_proj(mem_req_proj),
    .mem_req_row(mem_req_row),.mem_req_col(mem_req_col),.mem_req_wdata(mem_req_wdata),
    .mem_req_stride(mem_req_stride),.mem_rsp_valid(mem_rsp_valid),
    .mem_rsp_ready(mem_rsp_ready),.mem_rsp_rdata(mem_rsp_rdata),.mem_rsp_error(mem_rsp_error)
  );
  wire fp_ready, fp_valid;
  wire [31:0] fp_result;
  wire [4:0] fp_flags;
  wire [3:0] conversion_op=writing ? 4'd7 : int8_mode ? 4'd9 : 4'd5;
  anvil_q4_fp32 arithmetic (
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .in_valid(state==CONVERT_ISSUE || state==DECODE_ISSUE ||
      (state==SCALE_ISSUE && !escaping && !is_zero(maximum)) || state==RATIO_ISSUE),
    .in_ready(fp_ready),
    .op(state==CONVERT_ISSUE ? conversion_op : state==DECODE_ISSUE ? 4'd2 : 4'd3),
    .a(state==SCALE_ISSUE ? maximum : operand),
    .b(state==SCALE_ISSUE ? 32'h42fe0000 : scale_register),
    .out_valid(fp_valid),.out_ready(state==CONVERT_WAIT || state==DECODE_WAIT ||
      state==SCALE_WAIT || state==RATIO_WAIT),.result(fp_result),.flags(fp_flags)
  );
  wire [31:0] selected_byte=rdata >> {global_index[1:0],3'd0};
  wire [31:0] signed_byte={{24{selected_byte[7]}},selected_byte[7:0]};
  wire [31:0] bounded_ratio=ordered_less(32'h42fe0000,operand) ? 32'h42fe0000 :
    ordered_less(operand,32'hc2fe0000) ? 32'hc2fe0000 : operand;
  wire [31:0] encoded=bounded_int_rne(bounded_ratio);
  wire [31:0] byte_mask=32'hff << {global_index[1:0],3'd0};
  wire [31:0] assembled=(packed_word & ~byte_mask) |
    ({24'd0,(escaping ? 8'd0 : encoded[7:0])} << {global_index[1:0],3'd0});
  wire [31:0] padding_mask=kd[1:0]==0 ? 32'd0 :
    32'hffffffff << {kd[1:0],3'd0};
  assign cmd_ready=rst_n && !flush && state==IDLE;
  assign out_valid=rst_n && !flush && state==RESPONSE;
  assign result=rst_n && !flush ? result_register : 32'd0;
  assign error=out_valid && failed;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; writing<=0; value_select<=0; allow_current<=0; int8_mode<=0;
      escaping<=0; payload_escape<=0;
      failed<=0; scanning<=0; layer<=0; position<=0; epoch<=0; count<=0;
      capacity<=0; heads<=0; dimension<=0; stride<=0; pages<=0;
      page_size<=0; logical_page<=0; physical_page<=0; physical_row<=0;
      page_count<=0; alias_index<=0; requested_head<=0; requested_dimension<=0;
      retained_epoch<=0; retained_pages<=0;
      page_shift<=0; head<=0; scalar<=0; global_index<=0; head_base<=0;
      kd<=0; packed_stride<=0; scale_register<=0; maximum<=0; operand<=0;
      result_register<=0; packed_word<=0; write_word<=0; payload_col<=0;
    end else if (flush) begin state<=IDLE; failed<=0; result_register<=0; end
    else if (fault) begin failed<=1; state<=RESPONSE; end
    else case (state)
      IDLE: if (cmd_valid) begin
        writing<=cmd_write; value_select<=cmd_write ? 1'b0 : cmd_value;
        allow_current<=cmd_allow_current; int8_mode<=cache_int8;
        layer<=cmd_layer; position<=cmd_pos; epoch<=cmd_epoch;
        count<=committed_tokens; capacity<=context_capacity;
        heads<=kv_heads; dimension<=head_dim; kd<={15'd0,configured_kd};
        stride<=hidden>intermediate ? hidden : intermediate;
        pages<=physical_pages; page_size<=page_tokens; page_shift<=configured_shift;
        requested_head<=cmd_head; requested_dimension<=cmd_dimension;
        retained_epoch<=protected_epoch;
        retained_pages<=(protected_tokens+page_tokens-1)>>configured_shift;
        failed<=0; result_register<=0;
        if (!valid_page_size || physical_pages==0 || physical_pages>131072 ||
            context_capacity==0 || context_capacity>131072 ||
            committed_tokens>context_capacity || cmd_pos>=context_capacity ||
            kv_heads==0 || kv_heads>128 || head_dim<2 || head_dim>256 ||
            head_dim[0] || configured_kd>32768 ||
            (cmd_write && cmd_pos!=committed_tokens) ||
            (!cmd_write && (cmd_head>=kv_heads || cmd_dimension>=head_dim ||
              (cmd_pos>=committed_tokens &&
                !(cmd_allow_current && cmd_pos==committed_tokens))))) begin
          failed<=1; state<=RESPONSE;
        end else state<=GEOMETRY;
      end
      GEOMETRY: begin
        logical_page<=position >> page_shift;
        page_count<=(count+((writing || allow_current) ? 32'd1 : 32'd0)+page_size-1) >> page_shift;
        packed_stride<=(kd+3)>>2;
        state<=PAGE_READ;
      end
      PAGE_READ: if (issue) state<=PAGE_WAIT;
      PAGE_WAIT: if (complete) begin
        if (!rdata[31] || {1'b0,rdata[30:0]}>=pages) begin failed<=1; state<=RESPONSE; end
        else begin
          physical_page<={1'b0,rdata[30:0]};
          physical_row<=({1'b0,rdata[30:0]} << page_shift) | (position & (page_size-1));
          alias_index<=0; state<=ALIAS_NEXT;
        end
      end
      ALIAS_NEXT: begin
        if (alias_index>=page_count) begin alias_index<=0; state<=PROTECTED_NEXT; end
        else if (alias_index==logical_page) alias_index<=alias_index+1'b1;
        else state<=ALIAS_READ;
      end
      ALIAS_READ: if (issue) state<=ALIAS_WAIT;
      ALIAS_WAIT: if (complete) begin
        if (!rdata[31] || {1'b0,rdata[30:0]}>=pages ||
            {1'b0,rdata[30:0]}==physical_page) begin failed<=1; state<=RESPONSE; end
        else begin alias_index<=alias_index+1'b1; state<=ALIAS_NEXT; end
      end
      PROTECTED_NEXT: begin
        if (alias_index>=retained_pages || retained_epoch==epoch) state<=BEGIN_ACCESS;
        else state<=PROTECTED_READ;
      end
      PROTECTED_READ: if (issue) state<=PROTECTED_WAIT;
      PROTECTED_WAIT: if (complete) begin
        if (!rdata[31] || {1'b0,rdata[30:0]}>=pages ||
            {1'b0,rdata[30:0]}==physical_page) begin failed<=1; state<=RESPONSE; end
        else begin alias_index<=alias_index+1'b1; state<=PROTECTED_NEXT; end
      end
      BEGIN_ACCESS: begin
        packed_word<=0; maximum<=0; escaping<=0; payload_escape<=0;
        if (writing) begin
          head<=0; scalar<=0; global_index<=0; head_base<=0;
          scanning<=int8_mode; state<=SOURCE_READ;
        end else begin
          head<=requested_head; scalar<=requested_dimension;
          global_index<=32'(requested_head[7:0]*dimension[8:0])+requested_dimension;
          payload_col<=int8_mode ?
            (32'(requested_head[7:0]*dimension[8:0])+requested_dimension)>>2 :
            32'(requested_head[7:0]*dimension[8:0])+requested_dimension;
          if (int8_mode) state<=READ_SCALE;
          else state<=READ_PAYLOAD;
        end
      end
      READ_SCALE: if (issue) state<=READ_SCALE_WAIT;
      READ_SCALE_WAIT: if (complete) begin
        if (rdata==32'h7fc00000) begin
          escaping<=1; state<=READ_PAYLOAD;
        end else if (rdata[31] || is_zero(rdata) || rdata[30:23]==8'hff) begin
          failed<=1; state<=RESPONSE;
        end else begin scale_register<=rdata; state<=READ_PAYLOAD; end
      end
      READ_PAYLOAD: if (issue) state<=READ_PAYLOAD_WAIT;
      READ_PAYLOAD_WAIT: if (complete) begin
        if ((int8_mode && ((escaping ? selected_byte[7:0]!=0 : selected_byte[7:0]==8'h80) ||
            (payload_col+1==packed_stride && |(rdata & padding_mask)))) ||
            (!int8_mode && rdata[31:16]!=0)) begin
          failed<=1; state<=RESPONSE;
        end else if (escaping) begin
          payload_col<=global_index; state<=READ_ESCAPE;
        end else begin
          operand<=int8_mode ? signed_byte : rdata; state<=CONVERT_ISSUE;
        end
      end
      READ_ESCAPE: if (issue) state<=READ_ESCAPE_WAIT;
      READ_ESCAPE_WAIT: if (complete) begin
        if (is_nan(rdata) && rdata!=32'h7fc00000) begin
          failed<=1; state<=RESPONSE;
        end else begin result_register<=rdata; state<=RESPONSE; end
      end
      CONVERT_ISSUE: if (fp_ready) state<=CONVERT_WAIT;
      CONVERT_WAIT: if (fp_valid) begin
        if (writing) begin
          write_word<=fp_result; payload_col<=global_index;
          payload_escape<=0; state<=WRITE_PAYLOAD;
        end else if (int8_mode) begin operand<=fp_result; state<=DECODE_ISSUE; end
        else begin result_register<=fp_result; state<=RESPONSE; end
      end
      DECODE_ISSUE: if (fp_ready) state<=DECODE_WAIT;
      DECODE_WAIT: if (fp_valid) begin result_register<=fp_result; state<=RESPONSE; end
      SOURCE_READ: if (issue) state<=SOURCE_WAIT;
      SOURCE_WAIT: if (complete) begin
        operand<=rdata;
        if (!int8_mode) state<=CONVERT_ISSUE;
        else if (scanning) begin
          if (is_nan(rdata) || is_infinity(rdata) || rdata==32'h80000000)
            escaping<=1;
          else if (ordered_less(maximum,{1'b0,rdata[30:0]}))
            maximum<={1'b0,rdata[30:0]};
          if (scalar+1<dimension) begin
            scalar<=scalar+1'b1; global_index<=global_index+1'b1; state<=SOURCE_READ;
          end else state<=SCALE_ISSUE;
        end else if (escaping) begin
          write_word<=is_nan(rdata) ? 32'h7fc00000 : rdata;
          payload_col<=global_index; payload_escape<=1; state<=WRITE_PAYLOAD;
        end else state<=RATIO_ISSUE;
      end
      SCALE_ISSUE: begin
        if (escaping) begin scale_register<=32'h7fc00000; state<=PREPARE_PAYLOAD; end
        else if (is_zero(maximum)) begin scale_register<=32'h3f800000; state<=PREPARE_PAYLOAD; end
        else if (fp_ready) state<=SCALE_WAIT;
      end
      SCALE_WAIT: if (fp_valid) begin
        if (is_zero(fp_result)) begin
          escaping<=1; scale_register<=32'h7fc00000; state<=PREPARE_PAYLOAD;
        end else if (fp_result[31] || fp_result[30:23]==8'hff) begin
          failed<=1; state<=RESPONSE;
        end else begin scale_register<=fp_result; state<=PREPARE_PAYLOAD; end
      end
      PREPARE_PAYLOAD: begin
        scalar<=0; global_index<=head_base; scanning<=0; state<=SOURCE_READ;
      end
      WRITE_SCALE: if (issue) state<=WRITE_SCALE_WAIT;
      WRITE_SCALE_WAIT: if (complete) state<=NEXT_HEAD;
      RATIO_ISSUE: if (fp_ready) state<=RATIO_WAIT;
      RATIO_WAIT: if (fp_valid) begin operand<=fp_result; state<=ENCODE; end
      ENCODE: begin
        packed_word<=assembled;
        if (global_index[1:0]==3 || scalar+1==dimension) begin
          write_word<=assembled; payload_col<=global_index>>2;
          payload_escape<=0; state<=WRITE_PAYLOAD;
        end else state<=NEXT_SCALAR;
      end
      WRITE_PAYLOAD: if (issue) state<=WRITE_PAYLOAD_WAIT;
      WRITE_PAYLOAD_WAIT: if (complete) begin
        if (payload_escape) state<=ENCODE;
        else begin
          if (int8_mode && (global_index[1:0]==3 || global_index+1==kd))
            packed_word<=0;
          state<=NEXT_SCALAR;
        end
      end
      NEXT_SCALAR: begin
        if (scalar+1<dimension) begin
          scalar<=scalar+1'b1; global_index<=global_index+1'b1; state<=SOURCE_READ;
        end else if (int8_mode) state<=WRITE_SCALE;
        else state<=NEXT_HEAD;
      end
      NEXT_HEAD: begin
        maximum<=0; scalar<=0; scanning<=int8_mode; escaping<=0; payload_escape<=0;
        if (head+1<heads) begin
          head<=head+1'b1; head_base<=head_base+dimension;
          global_index<=head_base+dimension; state<=SOURCE_READ;
        end else if (!value_select) begin
          value_select<=1; head<=0; head_base<=0; global_index<=0; packed_word<=0;
          state<=SOURCE_READ;
        end else state<=RESPONSE;
      end
      RESPONSE: if (out_ready) state<=IDLE;
      default: begin failed<=1; state<=RESPONSE; end
    endcase
  end
endmodule
