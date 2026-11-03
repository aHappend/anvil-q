module anvil_q4_fp_kv_cache (
  input wire clk, rst_n, flush, cmd_valid,
  output wire cmd_ready,
  input wire cmd_write, cmd_value, cmd_allow_current,
  input wire [31:0] cmd_layer, cmd_pos, cmd_head, cmd_dimension, cmd_epoch,
  input wire [31:0] committed_tokens, context_capacity, protected_epoch, protected_tokens,
  input wire [31:0] kv_heads, head_dim, hidden, intermediate,
  input wire [1:0] cache_format,
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
  localparam [4:0] IDLE=0,GEOMETRY=1,PAGE_READ=2,PAGE_WAIT=3,
    ALIAS_NEXT=4,ALIAS_READ=5,ALIAS_WAIT=6,PROTECTED_NEXT=7,
    PROTECTED_READ=8,PROTECTED_WAIT=9,BEGIN_ACCESS=10,
    SOURCE_READ=11,SOURCE_WAIT=12,CONVERT=13,CONVERT_WAIT=14,
    PACK=15,WRITE_PAYLOAD=16,WRITE_WAIT=17,NEXT_SCALAR=18,
    READ_PAYLOAD=19,READ_WAIT=20,RESPONSE=21,PEER_NEXT=22,PEER_READ=23,PEER_WAIT=24;
  reg [4:0] state;
  reg writing,value_select,allow_current,failed;
  reg [1:0] format;
  reg [31:0] layer,position,epoch,count,capacity,pages,page_size;
  reg [31:0] logical_page,physical_page,physical_row,page_count,alias_index;
  reg [31:0] retained_epoch,retained_pages,stride,kd,packed_stride;
  reg [31:0] requested_head,requested_dimension,dimension,global_index;
  reg [31:0] packed_word,write_word,operand,converted,result_register;
  reg [31:0] peer_index,alias_candidate_page;
  reg pair_is_protected;
  reg [4:0] page_shift;
  wire [63:0] configured_kd={32'd0,kv_heads}*{32'd0,head_dim};
  wire [63:0] configured_index={32'd0,cmd_head}*{32'd0,head_dim}+{32'd0,cmd_dimension};
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
  wire port_idle,complete,fault;
  wire [31:0] rdata;
  wire page_read=state==PAGE_READ || state==ALIAS_READ || state==PROTECTED_READ ||
    state==PEER_READ;
  wire source_read=state==SOURCE_READ;
  wire payload_write=state==WRITE_PAYLOAD;
  wire issue=port_idle && (page_read || source_read || payload_write || state==READ_PAYLOAD);
  wire [31:0] payload_col=format==2 ? global_index>>2 : global_index>>1;
  wire [4:0] bit_offset=format==2 ? {global_index[1:0],3'd0} :
    {global_index[0],4'd0};
  wire [31:0] element_mask=format==2 ? 32'hff : 32'hffff;
  wire [31:0] assembled=(packed_word & ~(element_mask<<bit_offset)) |
    ((converted & element_mask)<<bit_offset);
  wire end_word=format==2 ? global_index[1:0]==3 : global_index[0];
  wire [31:0] selected_element=(rdata>>bit_offset) & element_mask;
  wire [36:0] fp8_encoded=narrow_fp8(operand);
  wire [36:0] fp8_decoded=widen_fp16({operand[7],operand[6:2],operand[1:0],8'd0});
  anvil_q4_fp_mem_port memory_port (
    .clk(clk),.rst_n(rst_n),.flush(flush),.issue(issue),
    .idle(port_idle),.complete(complete),.fault(fault),
    .write(payload_write),
    .kind(page_read ? 4'd15 : source_read ? 4'd8 :
      format==2 ? (value_select ? 4'd13 : 4'd12) : (value_select ? 4'd10 : 4'd9)),
    .layer(page_read ? (state==PROTECTED_READ || (state==PEER_READ && pair_is_protected) ?
      retained_epoch : epoch) :
      source_read ? 32'd0 : layer),.proj(3'd0),
    .row(page_read ? (state==PAGE_READ ? logical_page :
      state==PEER_READ ? peer_index : alias_index) :
      source_read ? (value_select ? 32'd4 : 32'd3) : physical_row),
    .col(page_read ? 32'd0 : source_read ? global_index : payload_col),
    .wdata(payload_write ? write_word : 32'd0),
    .stride(page_read ? 32'd1 : source_read ? stride : packed_stride),.rdata(rdata),
    .mem_req_valid(mem_req_valid),.mem_req_ready(mem_req_ready),
    .mem_req_write(mem_req_write),.mem_req_kind(mem_req_kind),
    .mem_req_layer(mem_req_layer),.mem_req_proj(mem_req_proj),
    .mem_req_row(mem_req_row),.mem_req_col(mem_req_col),.mem_req_wdata(mem_req_wdata),
    .mem_req_stride(mem_req_stride),.mem_rsp_valid(mem_rsp_valid),
    .mem_rsp_ready(mem_rsp_ready),.mem_rsp_rdata(mem_rsp_rdata),.mem_rsp_error(mem_rsp_error)
  );
  wire fp_ready,fp_valid;
  wire [31:0] fp_result;
  wire [4:0] fp_flags;
  anvil_q4_fp32 arithmetic (
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .in_valid(state==CONVERT && format!=2),.in_ready(fp_ready),
    .op(writing ? (format==1 ? 4'd8 : 4'd7) : (format==1 ? 4'd6 : 4'd5)),
    .a(operand),.b(32'd0),.out_valid(fp_valid),.out_ready(state==CONVERT_WAIT),
    .result(fp_result),.flags(fp_flags)
  );
  assign cmd_ready=rst_n && !flush && state==IDLE;
  assign out_valid=rst_n && !flush && state==RESPONSE;
  assign result=out_valid ? result_register : 32'd0;
  assign error=out_valid && failed;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state<=IDLE; writing<=0; value_select<=0; allow_current<=0; failed<=0; format<=0;
      layer<=0; position<=0; epoch<=0; count<=0; capacity<=0; pages<=0; page_size<=0;
      logical_page<=0; physical_page<=0; physical_row<=0; page_count<=0; alias_index<=0;
      retained_epoch<=0; retained_pages<=0; stride<=0; kd<=0; packed_stride<=0;
      requested_head<=0; requested_dimension<=0; dimension<=0; global_index<=0;
      packed_word<=0; write_word<=0; operand<=0; converted<=0; result_register<=0;
      peer_index<=0; alias_candidate_page<=0; pair_is_protected<=0;
      page_shift<=0;
    end else if (flush) begin state<=IDLE; failed<=0; result_register<=0; end
    else if (fault) begin failed<=1; result_register<=0; state<=RESPONSE; end
    else case (state)
      IDLE: if (cmd_valid) begin
        writing<=cmd_write; value_select<=cmd_write ? 1'b0 : cmd_value;
        allow_current<=cmd_allow_current; format<=cache_format;
        layer<=cmd_layer; position<=cmd_pos; epoch<=cmd_epoch; count<=committed_tokens;
        capacity<=context_capacity; pages<=physical_pages; page_size<=page_tokens;
        page_shift<=configured_shift; retained_epoch<=protected_epoch;
        retained_pages<=(protected_tokens+page_tokens-1)>>configured_shift;
        stride<=hidden>intermediate ? hidden : intermediate;
        kd<=configured_kd[31:0]; dimension<=head_dim;
        requested_head<=cmd_head; requested_dimension<=cmd_dimension;
        global_index<=configured_index[31:0]; failed<=0; result_register<=0;
        if (cache_format>2 || !valid_page_size || physical_pages==0 || physical_pages>131072 ||
            context_capacity==0 || context_capacity>131072 || committed_tokens>context_capacity ||
            protected_tokens>context_capacity || cmd_pos>=context_capacity ||
            kv_heads==0 || kv_heads>128 || head_dim<2 || head_dim>256 || head_dim[0] ||
            configured_kd>32768 || hidden<2 || hidden>8192 || intermediate==0 ||
            intermediate>32768 || (cmd_write && cmd_pos!=committed_tokens) ||
            (!cmd_write && (cmd_head>=kv_heads || cmd_dimension>=head_dim ||
              (cmd_pos>=committed_tokens && !(cmd_allow_current && cmd_pos==committed_tokens))))) begin
          failed<=1; state<=RESPONSE;
        end else state<=GEOMETRY;
      end
      GEOMETRY: begin
        logical_page<=position>>page_shift;
        page_count<=(count+((writing || allow_current) ? 32'd1 : 32'd0)+page_size-1)>>page_shift;
        packed_stride<=format==2 ? (kd+3)>>2 : (kd+1)>>1;
        state<=PAGE_READ;
      end
      PAGE_READ: if (issue) state<=PAGE_WAIT;
      PAGE_WAIT: if (complete) begin
        if (!rdata[31] || {1'b0,rdata[30:0]}>=pages) begin failed<=1; state<=RESPONSE; end
        else begin
          physical_page<={1'b0,rdata[30:0]};
          physical_row<=({1'b0,rdata[30:0]}<<page_shift) | (position & (page_size-1));
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
        else begin
          alias_candidate_page<={1'b0,rdata[30:0]}; peer_index<=0;
          pair_is_protected<=0; state<=PEER_NEXT;
        end
      end
      PROTECTED_NEXT: begin
        if (!writing || alias_index>=retained_pages || retained_epoch==epoch) state<=BEGIN_ACCESS;
        else state<=PROTECTED_READ;
      end
      PROTECTED_READ: if (issue) state<=PROTECTED_WAIT;
      PROTECTED_WAIT: if (complete) begin
        if (!rdata[31] || {1'b0,rdata[30:0]}>=pages ||
            {1'b0,rdata[30:0]}==physical_page) begin failed<=1; state<=RESPONSE; end
        else begin
          alias_candidate_page<={1'b0,rdata[30:0]}; peer_index<=0;
          pair_is_protected<=1; state<=PEER_NEXT;
        end
      end
      PEER_NEXT: begin
        if (peer_index>=alias_index) begin
          alias_index<=alias_index+1'b1;
          if (pair_is_protected) state<=PROTECTED_NEXT; else state<=ALIAS_NEXT;
        end else if (!pair_is_protected && peer_index==logical_page)
          peer_index<=peer_index+1'b1;
        else state<=PEER_READ;
      end
      PEER_READ: if (issue) state<=PEER_WAIT;
      PEER_WAIT: if (complete) begin
        if (!rdata[31] || {1'b0,rdata[30:0]}>=pages ||
            {1'b0,rdata[30:0]}==alias_candidate_page) begin failed<=1; state<=RESPONSE; end
        else begin peer_index<=peer_index+1'b1; state<=PEER_NEXT; end
      end
      BEGIN_ACCESS: begin
        packed_word<=0;
        if (writing) begin global_index<=0; state<=SOURCE_READ; end
        else state<=READ_PAYLOAD;
      end
      SOURCE_READ: if (issue) state<=SOURCE_WAIT;
      SOURCE_WAIT: if (complete) begin operand<=rdata; state<=CONVERT; end
      CONVERT: begin
        if (format==2) begin
          if (writing) begin converted<=fp8_encoded[31:0]; state<=PACK; end
          else begin result_register<=fp8_decoded[31:0]; state<=RESPONSE; end
        end else if (fp_ready) state<=CONVERT_WAIT;
      end
      CONVERT_WAIT: if (fp_valid) begin
        if (writing) begin converted<=fp_result; state<=PACK; end
        else begin result_register<=fp_result; state<=RESPONSE; end
      end
      PACK: begin
        packed_word<=assembled;
        if (end_word || global_index+1==kd) begin write_word<=assembled; state<=WRITE_PAYLOAD; end
        else state<=NEXT_SCALAR;
      end
      WRITE_PAYLOAD: if (issue) state<=WRITE_WAIT;
      WRITE_WAIT: if (complete) begin packed_word<=0; state<=NEXT_SCALAR; end
      NEXT_SCALAR: begin
        if (global_index+1<kd) begin global_index<=global_index+1'b1; state<=SOURCE_READ; end
        else if (!value_select) begin
          value_select<=1; global_index<=0; packed_word<=0; state<=SOURCE_READ;
        end else state<=RESPONSE;
      end
      READ_PAYLOAD: if (issue) state<=READ_WAIT;
      READ_WAIT: if (complete) begin operand<=selected_element; state<=CONVERT; end
      RESPONSE: if (out_ready) state<=IDLE;
      default: begin failed<=1; state<=RESPONSE; end
    endcase
  end
endmodule
