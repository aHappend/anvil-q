"""Sparse byte-memory upload/readback oracle for the real DMA and tile SRAMs.

Changed payload bytes distinguish preservation from merely replaying an image.
Only public load, Avalon and tile pins are observed. This compact experiment
does not qualify image commit, full-model inference, physical DDR or throughput.

python3 -B tests/verify.py --probe dma-upload-sensitivity --seed 17
executes both simulators and two separately compiled, disposable RTL defects.
"""

import random

from experiments import hx, measurement_records


ADDRESSES = (0xFC0, 0x100000FC0, 0x1FFFFFFC0)


def instrument_upload(bench, seed):
    rng = random.Random(seed)
    expected = [0, 0, 0]
    vectors = []
    initial = []
    for slot, address in enumerate(ADDRESSES):
        value = rng.getrandbits(512)
        expected[slot] = value
        initial.append(f" upload_memory[{slot}]={hx(value, 512)};")
        initial.append(f" upload_expected[{slot}]={hx(value, 512)};")
    masks = [(1 << 64) - 1, 0]
    masks += [1 << lane for lane in range(64)]
    masks += [((1 << 64) - 1) ^ (1 << lane) for lane in range(64)]
    for index, mask in enumerate(masks):
        slot = index % len(ADDRESSES)
        # Every incoming byte differs, including each byte that must be preserved.
        data = expected[slot] ^ sum(rng.randrange(1, 256) << (8 * lane)
                                    for lane in range(64))
        for lane in range(64):
            if mask & (1 << lane):
                byte_mask = 255 << (8 * lane)
                expected[slot] = (expected[slot] & ~byte_mask) | (data & byte_mask)
        vectors.append(
            (ADDRESSES[slot] << 1099) | (data << 587) | (mask << 523) |
            (int(index % 2 == 0) << 522) | ((0, 1, 7, 31)[index % 4] << 517) |
            ((0, 3, 11)[index % 3] << 513) | (1 << 512) | expected[slot])
    # One upload stays open across three independently addressed, reordered beats.
    for index, slot in enumerate((2, 0, 1)):
        data = expected[slot] ^ sum(rng.randrange(1, 256) << (8 * lane)
                                    for lane in range(64))
        expected[slot] = data
        vectors.append(
            (ADDRESSES[slot] << 1099) | (data << 587) | (((1 << 64) - 1) << 523) |
            (7 << 517) | (3 << 513) | (int(index == 2) << 512) | data)
    initial += [f" upload_vectors[{index}]={hx(vector, 1132)};"
                for index, vector in enumerate(vectors)]

    declarations = r"""
reg load_enable=1,load_clear=0,load_valid=0,load_last=0;
reg [32:0] load_address=0;
reg [511:0] load_data=0;
reg [63:0] load_byteenable=0;
wire load_ready,load_done,load_error,load_idle;
reg [511:0] upload_memory[0:2],upload_expected[0:2];
reg [1131:0] upload_vectors[0:132];
integer upload_index=0;
reg upload_immediate=0,upload_pending=0;
integer upload_delay=0,upload_service_delay=0,upload_wait=0,upload_wait_left=0;
integer upload_accepted=0,upload_issued=0,upload_responses=0,upload_completions=0;
integer upload_same_edge=0,upload_delayed=0,upload_preserved=0,upload_changed=0;
integer upload_onehot=0,upload_inverse=0,upload_zero=0,upload_full=0;
integer upload_stalls1=0,upload_stalls7=0,upload_stalls31=0,upload_held_edges=0;
integer upload_low=0,upload_high=0,upload_top=0,upload_partial_last=0;
reg upload_holding=0,upload_command_seen=0;
reg [616:0] upload_held_payload;
wire [616:0] upload_command_payload=
 {avm_address,avm_burstcount,avm_writedata,avm_byteenable};
wire upload_response=rst_n &&
 ((upload_immediate && avm_write && !avm_waitrequest) ||
  (upload_pending && upload_delay==0));
function automatic integer upload_slot(input [32:0] address);
 begin
  case(address)
   33'h000000fc0:upload_slot=0;
   33'h100000fc0:upload_slot=1;
   33'h1ffffffc0:upload_slot=2;
   default:upload_slot=-1;
  endcase
 end
endfunction
function automatic [511:0] upload_service_word(input [32:0] address);
 integer slot;
 begin
  slot=upload_slot(address);
  upload_service_word=slot<0 ? 512'bx : upload_memory[slot];
 end
endfunction
function automatic [511:0] upload_reference_word(input [32:0] address);
 integer slot;
 begin
  slot=upload_slot(address);
  upload_reference_word=slot<0 ? 512'bx : upload_expected[slot];
 end
endfunction
always @(negedge ddr_clk) begin
 if(!rst_n || !avm_write) begin upload_command_seen=0;upload_wait_left=0;end
 else if(!upload_command_seen) begin
  upload_command_seen=1;upload_wait_left=upload_wait;
 end else if(upload_wait_left>0) upload_wait_left=upload_wait_left-1;
end
always @(posedge ddr_clk) begin : upload_service
 integer slot,b;
 if(!rst_n) begin
  upload_pending<=0;upload_delay<=0;upload_holding<=0;
 end else begin
  if(upload_holding && (avm_write!==1 || upload_command_payload!==upload_held_payload))
   $fatal(1,"UPLOAD_HELD_COMMAND_CHANGED");
  upload_holding<=avm_write && avm_waitrequest;
  if(avm_write && avm_waitrequest) begin
   upload_held_payload<=upload_command_payload;upload_held_edges=upload_held_edges+1;
  end
  if(avm_write && !avm_waitrequest) begin
   slot=upload_slot(avm_address);
   if(slot<0 || avm_burstcount!==1 || avm_read!==0 || upload_pending ||
      avm_address!==load_address || avm_writedata!==load_data ||
      avm_byteenable!==load_byteenable)
    $fatal(1,"UPLOAD_AVALON_COMMAND_MISMATCH");
   for(b=0;b<64;b=b+1)
    if(avm_byteenable[b]) upload_memory[slot][8*b+:8]=avm_writedata[8*b+:8];
   upload_issued=upload_issued+1;
   if(upload_immediate) begin
    if(upload_response!==1) $fatal(1,"UPLOAD_IMMEDIATE_NOT_COINCIDENT");
   end else begin
    upload_pending<=1;upload_delay<=upload_service_delay;
   end
  end
  if(upload_pending && upload_delay>0) upload_delay<=upload_delay-1;
  if(upload_response) begin
   upload_responses=upload_responses+1;upload_pending<=0;
   if(upload_immediate) upload_same_edge=upload_same_edge+1;
   else upload_delayed=upload_delayed+1;
  end
 end
end
task upload_word(input [32:0] address,input [511:0] data,input [63:0] mask,
                 input integer instant,stalls,delay,input last);
 integer n,b,old_issued,old_responses,old_held,old_reads;
 reg [511:0] before_word;
 begin
  old_issued=upload_issued;old_responses=upload_responses;
  old_held=upload_held_edges;old_reads=reads;
  before_word=upload_reference_word(address);
  @(negedge ddr_clk);
  upload_immediate=instant;upload_wait=stalls;upload_service_delay=delay;
  load_address=address;load_data=data;load_byteenable=mask;load_last=last;load_valid=1;
  #0.001;
  if(load_ready!==1) $fatal(1,"UPLOAD_INPUT_NOT_READY");
  @(posedge ddr_clk);#0.001;upload_accepted=upload_accepted+1;
  if(load_ready!==0 || load_done!==0 || load_error!==0)
   $fatal(1,"UPLOAD_ACCEPT_EDGE_OR_PREMATURE_COMPLETION");
  @(negedge ddr_clk);load_valid=0;
  n=0;
  while(upload_responses==old_responses && n<10000) begin
   @(posedge ddr_clk);#0.001;n=n+1;
   if(upload_responses==old_responses && (load_ready!==0 || load_done!==0))
    $fatal(1,"UPLOAD_ACKNOWLEDGED_BEFORE_RESPONSE");
  end
  if(upload_issued!==old_issued+1 || upload_responses!==old_responses+1 ||
     upload_held_edges-old_held!==stalls || load_error!==0 ||
     load_done!==last || load_idle!==last || reads!==old_reads ||
     upload_pending!==0 || avm_write!==0)
   $fatal(1,"UPLOAD_WRITE_CONSERVATION_OR_LAST");
  if(last) upload_completions=upload_completions+1;
  else upload_partial_last=upload_partial_last+1;
  case(stalls)
   1:upload_stalls1=upload_stalls1+1;
   7:upload_stalls7=upload_stalls7+1;
   31:upload_stalls31=upload_stalls31+1;
  endcase
  if(mask==0) upload_zero=upload_zero+1;
  else if(mask==64'hffffffffffffffff) upload_full=upload_full+1;
  else if((mask & (mask-1))==0) upload_onehot=upload_onehot+1;
  else if(((~mask) & ((~mask)-1))==0) upload_inverse=upload_inverse+1;
  case(upload_slot(address))
   0:upload_low=upload_low+1;1:upload_high=upload_high+1;2:upload_top=upload_top+1;
  endcase
  for(b=0;b<64;b=b+1) begin
   if(!mask[b] && before_word[8*b+:8]!==data[8*b+:8])
    upload_preserved=upload_preserved+1;
   if(mask[b] && before_word[8*b+:8]!==data[8*b+:8])
    upload_changed=upload_changed+1;
  end
  @(posedge ddr_clk);#0.001;
  if(load_done!==0 || load_error!==0) $fatal(1,"UPLOAD_DONE_NOT_ONE_CYCLE");
 end
endtask
"""
    replacements = {
        "if({request_ready,completion_valid,completion_error,completion_tiles,":
            "if({load_ready,load_done,load_error,load_idle,"
            "request_ready,completion_valid,completion_error,completion_tiles,",
        "wire avm_waitrequest=stall_remaining>0;":
            "wire avm_waitrequest=avm_write ? upload_wait_left>0 : stall_remaining>0;",
        "wire [511:0] avm_readdata=pattern(response_remaining>0 ? service_address : avm_address);":
            "wire [511:0] avm_readdata=upload_service_word("
            "response_remaining>0 ? service_address : avm_address);",
        ".load_enable(1'b0),.load_clear(1'b0),.load_valid(1'b0),.load_ready(),":
            ".load_enable(load_enable),.load_clear(load_clear),.load_valid(load_valid),"
            ".load_ready(load_ready),",
        ".load_address(33'b0),.load_data(512'b0),.load_byteenable(64'b0),.load_last(1'b0),":
            ".load_address(load_address),.load_data(load_data),"
            ".load_byteenable(load_byteenable),.load_last(load_last),",
        ".load_done(),.load_error(),.load_idle(),":
            ".load_done(load_done),.load_error(load_error),.load_idle(load_idle),",
        ".avm_readdatavalid(avm_readdatavalid),.avm_response(2'b00),.avm_writeresponsevalid(1'b0),":
            ".avm_readdatavalid(avm_readdatavalid),.avm_response(2'b00),"
            ".avm_writeresponsevalid(upload_response),",
        "expected=pattern(base+offset*64+n*64);":
            "expected=upload_reference_word(base+offset*64+n*64);",
    }
    for before, after in replacements.items():
        if bench.count(before) != 1:
            raise AssertionError("upload instrument lost unique public driver: " + before)
        bench = bench.replace(before, after, 1)
    # Keep all run_transfer assertions, but not a line per one-beat readback.
    start = bench.index('  $display("MEASURED_DMA ')
    stop = bench.index("  transfer_index=transfer_index+1;", start)
    bench = bench[:start] + bench[stop:]
    marker = "initial begin\n rst_n=0;`RESET_DELTA check_reset();"
    if bench.count(marker) != 1:
        raise AssertionError("upload instrument lost unique DMA startup")
    bench = bench[:bench.index(marker)] + declarations + r"""
initial begin
 rst_n=0;`RESET_DELTA check_reset();
 if({load_ready,load_done,load_error,load_idle}!==4'b0)
  $fatal(1,"UPLOAD_RESET_XZ_OR_NONZERO");
""" + "\n".join(initial) + r"""
 repeat(6) edge_tick();
 @(negedge clk);rst_n=1;
 repeat(6) edge_tick();
 for(upload_index=0;upload_index<133;upload_index=upload_index+1) begin
  upload_word(upload_vectors[upload_index][1099+:33],
              upload_vectors[upload_index][587+:512],
              upload_vectors[upload_index][523+:64],
              int'(upload_vectors[upload_index][522]),
              int'(upload_vectors[upload_index][517+:5]),
              int'(upload_vectors[upload_index][513+:4]),
              upload_vectors[upload_index][512]);
  upload_expected[upload_slot(upload_vectors[upload_index][1099+:33])]=
   upload_vectors[upload_index][0+:512];
  if(upload_vectors[upload_index][512]) begin
   run_transfer(33'h000000fc0,1,64,upload_index<130,0,0);
   run_transfer(33'h100000fc0,1,64,upload_index<130,0,0);
   run_transfer(33'h1ffffffc0,1,64,upload_index<130,0,0);
  end
 end
 if(upload_accepted!==133 || upload_issued!==133 || upload_responses!==133 ||
    upload_completions!==131 || upload_partial_last!==2 || comparisons!==393 ||
    upload_onehot!==64 || upload_inverse!==64 || upload_zero!==1 || upload_full!==4 ||
    upload_same_edge!==65 || upload_delayed!==68 ||
    upload_preserved!==4160 || upload_changed!==4352 ||
    upload_stalls1!==33 || upload_stalls7!==35 || upload_stalls31!==32 ||
    upload_low!==45 || upload_high!==44 || upload_top!==44 ||
    protocol_error!==0 || compute_error!==0)
  $fatal(1,"UPLOAD_MISSING_OBSERVED_COVERAGE preserved=%0d changed=%0d",
          upload_preserved,upload_changed);
 $display("CHECKS_PASSED dma_upload accepted=%0d issued=%0d responses=%0d completions=%0d open_beats=%0d readback_beats=%0d onehot=%0d inverse=%0d zero=%0d full=%0d immediate=%0d delayed=%0d preserved_bytes=%0d changed_bytes=%0d stall1=%0d stall7=%0d stall31=%0d low=%0d high=%0d top=%0d",
          upload_accepted,upload_issued,upload_responses,upload_completions,
          upload_partial_last,comparisons,upload_onehot,upload_inverse,upload_zero,upload_full,
          upload_same_edge,upload_delayed,upload_preserved,upload_changed,
          upload_stalls1,upload_stalls7,upload_stalls31,upload_low,upload_high,upload_top);
 $finish;
end
endmodule
"""
    return bench


def validate_upload(evidence, transcript, seed):
    rows = measurement_records(transcript, "CHECKS_PASSED dma_upload")
    expected = {
        "accepted": 133, "issued": 133, "responses": 133, "completions": 131,
        "open_beats": 2, "readback_beats": 393, "onehot": 64, "inverse": 64,
        "zero": 1, "full": 4, "immediate": 65, "delayed": 68,
        "preserved_bytes": 4160, "changed_bytes": 4352,
        "stall1": 33, "stall7": 35, "stall31": 32, "low": 45, "high": 44, "top": 44,
    }
    if len(rows) != 1 or rows[0] != expected:
        raise AssertionError("missing exact upload/readback comparison ledger")
    evidence.record["observations"].append({
        "scope": "public_DMA_upload_byte_masks_and_tile_readback_not_image_commit",
        "seed": seed, "observed": rows[0],
        "oracle": "Python byte-mask updates on three distinct sparse 33-bit addresses; "
                  "read back all three through actual DMA/tile SRAM after every completed upload",
    })
    evidence.flush()


def upload_checks(evidence, seed):
    from experiments import dma_probe

    transcripts = []
    previous = getattr(evidence, "default_simulator", None)
    try:
        for simulator in ("iverilog", "verilator"):
            evidence.default_simulator = simulator
            transcripts.append(dma_probe(evidence, 3, seed, upload_validation=True))
    finally:
        if previous is None:
            del evidence.default_simulator
        else:
            evidence.default_simulator = previous
    if transcripts[0] != transcripts[1]:
        raise AssertionError("Icarus/Verilator upload comparison ledgers disagree")
