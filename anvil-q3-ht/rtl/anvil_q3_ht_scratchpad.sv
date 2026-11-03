module anvil_q3_ht_scratchpad #(
  parameter HIDDEN_SIZE=2048, INTERMEDIATE_SIZE=11008,
  parameter NUM_KV_HEADS=2, HEAD_DIM=128,
  localparam SH=HIDDEN_SIZE>0 ? HIDDEN_SIZE : 1,
  localparam SI=INTERMEDIATE_SIZE>0 ? INTERMEDIATE_SIZE : 1,
  localparam SK=NUM_KV_HEADS>0 && HEAD_DIM>0 &&
    64'(NUM_KV_HEADS)*64'(HEAD_DIM)<=64'hffffffff ?
    32'(64'(NUM_KV_HEADS)*64'(HEAD_DIM)) : 1,
  localparam LOGICAL_WORDS=10*64'(SH)+3*64'(SI)+2*64'(SK),
  localparam WORDS=LOGICAL_WORDS>=1 && LOGICAL_WORDS*4<=64'h3e000000 ?
    32'(LOGICAL_WORDS) : 1,
  localparam LOCAL_WORDS=WORDS<65536 ? WORDS : 65536,
  localparam AW=LOCAL_WORDS>1 ? $clog2(LOCAL_WORDS) : 1
) (
  input wire clk, rst_n, flush, memory_enable,
  input wire req_valid,
  output wire req_ready,
  input wire req_write,
  input wire [31:0] req_slot, req_index, req_wdata,
  output wire rsp_valid,
  input wire rsp_ready,
  output wire rsp_error,
  output wire [31:0] rsp_rdata,
  output wire idle, drain_done, fault,
  output wire memory_req_valid, memory_req_write,
  input wire memory_req_ready,
  output wire [32:0] memory_req_address,
  output wire [511:0] memory_req_wdata,
  output wire [63:0] memory_req_byteenable,
  input wire memory_rsp_valid, memory_rsp_error,
  input wire [511:0] memory_rsp_rdata
);
  localparam LEGAL=HIDDEN_SIZE>0 && INTERMEDIATE_SIZE>0 &&
    NUM_KV_HEADS>0 && HEAD_DIM>0 &&
    64'(WORDS)==10*64'(HIDDEN_SIZE)+3*64'(INTERMEDIATE_SIZE)+
      2*64'(NUM_KV_HEADS)*64'(HEAD_DIM) &&
    64'(WORDS)*4<=64'h3e000000;
  function automatic [31:0] slot_length(input reg [31:0] slot);
    slot_length=slot==3 || slot==4 ? SK :
      slot==9 || slot==10 || slot==11 ? SI : SH;
  endfunction
  function automatic [31:0] slot_base(input reg [31:0] slot);
    begin
      case (slot)
        0: slot_base=0;
        1: slot_base=SH;
        2: slot_base=2*SH;
        3: slot_base=3*SH;
        4: slot_base=3*SH+SK;
        5: slot_base=3*SH+2*SK;
        6: slot_base=4*SH+2*SK;
        7: slot_base=5*SH+2*SK;
        8: slot_base=6*SH+2*SK;
        9: slot_base=7*SH+2*SK;
        10: slot_base=7*SH+2*SK+SI;
        11: slot_base=7*SH+2*SK+2*SI;
        12: slot_base=7*SH+2*SK+3*SI;
        13: slot_base=8*SH+2*SK+3*SI;
        default: slot_base=9*SH+2*SK+3*SI;
      endcase
    end
  endfunction
  (* ramstyle="M20K", nomem2reg *) reg [31:0] memory [0:LOCAL_WORDS-1];
  (* ramstyle="M20K", nomem2reg *) reg initialized [0:LOCAL_WORDS-1];
  reg [31:0] read_data;
  reg read_initialized;
  reg valid, failed, response_write, clearing, spill_pending;
  reg [AW-1:0] clear_address;
  wire [31:0] safe_slot=req_slot<=14 ? req_slot : 32'd0;
  wire [31:0] length=slot_length(safe_slot);
  wire [31:0] physical=slot_base(safe_slot)+req_index;
  wire [AW-1:0] address=AW'(physical);
  wire malformed=req_slot>14 || req_index>=length;
  wire spilled=!malformed && physical>=LOCAL_WORDS;
  wire transfer=req_valid && req_ready;
  wire spill_ready, spill_valid, spill_error, spill_idle;
  wire [31:0] spill_data;
  wire local_response=rst_n && !flush && valid;
  wire local_error=failed || (!response_write && !read_initialized);

  generate if (!LEGAL) begin: invalid_parameters
    initial $fatal(1,"ANVIL_Q3_HT PARAMETER ERROR: scratchpad dimensions or capacity");
  end endgenerate
  assign req_ready=rst_n && LEGAL && !flush && !clearing && !spill_pending &&
    spill_idle && (!valid || rsp_ready);
  assign rsp_valid=local_response || (rst_n && !flush && spill_pending && spill_valid);
  assign rsp_error=local_response ? local_error : rsp_valid && spill_error;
  assign rsp_rdata=local_response ? (!local_error && !response_write ? read_data : 32'd0) :
    rsp_valid && !spill_error ? spill_data : 32'd0;
  assign idle=rst_n && !flush && !clearing && !valid && !spill_pending && spill_idle;
  anvil_q3_ht_scratch_backing #(.WORDS(WORDS),.LOCAL_WORDS(LOCAL_WORDS)) backing (
    .clk(clk),.rst_n(rst_n),.flush(flush),.memory_enable(memory_enable),
    .req_valid(transfer && spilled),.req_ready(spill_ready),.req_write(req_write),
    .req_index(physical),.req_wdata(req_wdata),
    .rsp_valid(spill_valid),.rsp_ready(spill_pending && rsp_ready),
    .rsp_error(spill_error),.rsp_rdata(spill_data),
    .idle(spill_idle),.drain_done(drain_done),.fault(fault),
    .memory_req_valid(memory_req_valid),.memory_req_ready(memory_req_ready),
    .memory_req_write(memory_req_write),.memory_req_address(memory_req_address),
    .memory_req_wdata(memory_req_wdata),.memory_req_byteenable(memory_req_byteenable),
    .memory_rsp_valid(memory_rsp_valid),.memory_rsp_error(memory_rsp_error),
    .memory_rsp_rdata(memory_rsp_rdata)
  );

  always @(posedge clk) begin
    if (rst_n && !flush && clearing) initialized[clear_address]<=0;
    if (transfer && !malformed && !spilled) begin
      if (req_write) begin
        memory[address]<=req_wdata;
        initialized[address]<=1;
      end else begin
        read_data<=memory[address];
        read_initialized<=initialized[address];
      end
    end
  end
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      valid<=0; failed<=0; response_write<=0;
      clearing<=1; clear_address<=0; spill_pending<=0;
    end else if (flush) begin
      valid<=0; failed<=0; response_write<=0;
      clearing<=1; clear_address<=0; spill_pending<=0;
    end else if (clearing) begin
      if (clear_address==LOCAL_WORDS-1) clearing<=0;
      else clear_address<=clear_address+1'b1;
    end else if (req_ready) begin
      valid<=req_valid && !spilled;
      if (transfer && spilled) spill_pending<=1;
      if (req_valid) begin
        failed<=malformed;
        response_write<=req_write;
      end
    end else if (spill_pending && spill_valid && rsp_ready) spill_pending<=0;
  end
endmodule
