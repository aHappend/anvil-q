"""Public descriptor/CSR validation against independently sized tensor regions.

Compact manifests exercise the complete AWQ and BF16 descriptor sets and
low/high counter snapshots without claiming checkpoint, decoder, EMIF timing
or board verification. Counter inputs are driven only through public ports.
"""

import hashlib

from experiments import CLOCK, measurement_records
from reference import MATRIX


def manifest(shape, mode):
    """Lengths and identities follow tensor shapes, not DUT scan sequencing."""
    h, i, kv = shape.hidden, shape.intermediate, shape.kv
    entries = []

    def add(kind, layer, proj, size):
        length = (size + 63) // 64 * 64
        base = sum(entry[5] for entry in entries)
        entries.append((((layer * 12) + kind) * 8 + proj,
                        kind, layer, proj, base, length))

    add(0, 0, 0, shape.vocab * h * 2)
    for layer in range(shape.layers):
        for proj, columns, rows in (
                (0, h, h), (1, kv, h), (2, kv, h), (3, h, h),
                (4, i, h), (5, i, h), (6, h, i)):
            add(1, layer, proj, rows * columns * 2 if mode == "BF16"
                else rows * columns // 2)
            if mode == "AWQ":
                add(2, layer, proj, rows // shape.group * columns // 8 * 4)
                add(3, layer, proj, rows // shape.group * columns * 2)
            if proj < 3:
                add(4, layer, proj, columns * 2)
        add(5, layer, 0, h * 2)
        add(6, layer, 0, h * 2)
        add(9, layer, 0, shape.max_seq * kv * 4)
        add(10, layer, 0, shape.max_seq * kv * 4)
    add(7, 0, 0, h * 2)
    add(8, 0, 0, 15 * max(h, i) * 4)
    add(11, 0, 0, shape.max_seq * shape.head_dim * 4)
    return entries


def descriptor_case(evidence, mode, simulator):
    shape = MATRIX[1]
    entries = manifest(shape, mode)
    instructions = []
    bins = {}
    counter_comparisons = 0

    def emit(opcode, *arguments):
        words = (opcode, *arguments, *(0 for _ in range(5 - len(arguments))))
        if len(words) != 6 or any(not 0 <= word < (1 << 32) for word in words):
            raise ValueError("invalid descriptor stimulus instruction")
        instructions.append("".join(f"{word:08x}" for word in words))

    def csr(write, address, data=0, error=0, expected=0):
        nonlocal counter_comparisons
        emit(0, write, address, data, error, expected)
        if not write and address in (0x30, 0x34, 0x38, 0x3c):
            counter_comparisons += 1

    def counters(token, reads):
        emit(5, token >> 32, token & 0xffffffff, reads >> 32, reads & 0xffffffff)

    def lookup(index, base, length, error):
        emit(2, index, base & 0xffffffff, base >> 32, length, error)

    def image(expected, sticky=2):
        emit(3, expected, sticky)

    def set_signal(name, value):
        emit(4, ("engine_busy", "load_busy", "emif_initialized", "load_failed").index(name), value)

    def observed(name):
        index = bins.setdefault(name, len(bins))
        emit(1, index)

    def stage(entry):
        index, kind, layer, proj, base, length = entry
        for address, value in ((0x10, index), (0x14, kind), (0x18, layer),
                               (0x1c, proj), (0x20, base & 0xffffffff),
                               (0x24, base >> 32), (0x28, length)):
            csr(1, address, value)

    def install(entry, error=0):
        stage(entry)
        csr(1, 0x2c, 1, error)

    def compare(entry):
        index, kind, layer, proj, base, length = entry
        csr(1, 0x10, index)
        for address, value in ((0x14, kind), (0x18, layer), (0x1c, proj),
                               (0x20, base & 0xffffffff), (0x24, base >> 32),
                               (0x28, length)):
            csr(0, address, expected=value)
        lookup(index, base, length, 0)

    csr(0, 0, expected=0x02000001)
    csr(0, 0x14, error=1)
    lookup(0, 0, 0, 1)
    observed("unavailable_entry")
    for address in (1, 0x40, 0xfffc):
        csr(0, address, error=1)
        csr(1, address, 0xffffffff, error=1)
    observed("undefined_and_unaligned_CSR")
    counters(0x12345678ffffffff, 0x87654321ffffffff)
    csr(0, 0x34, expected=0x12345678)
    csr(0, 0x3c, expected=0x87654321)
    observed("counter_high_without_low")
    csr(0, 0x30, expected=0xffffffff)
    csr(0, 0x38, expected=0xffffffff)
    counters(0x1234567900000000, 0x8765432200000000)
    csr(0, 0x34, expected=0x12345678)
    csr(0, 0x3c, expected=0x87654321)
    observed("independent_counter_rollover_snapshots")
    csr(0, 0x34, expected=0x12345679)
    csr(0, 0x3c, expected=0x87654322)
    observed("counter_high_consumes_snapshot_once")
    csr(0, 0x30, expected=0)
    csr(0, 0x38, expected=0)
    counters(0xffffffffffffffff, 0)
    csr(0, 0x30, expected=0xffffffff)
    csr(0, 0x38, expected=0)
    counters(0, 0xabcdef0187654321)
    csr(0, 0x34, expected=0xffffffff)
    csr(0, 0x3c, expected=0)
    observed("repeated_counter_low_replaces_snapshot")
    csr(0, 0x30, expected=0)
    csr(0, 0x38, expected=0x87654321)
    for address in (0x30, 0x34, 0x38, 0x3c):
        csr(1, address, 0xffffffff, error=1)
    csr(0, 0x31, error=1)
    csr(0, 0x39, error=1)
    counters(0x1111111122222222, 0x3333333344444444)
    csr(0, 0x34, expected=0)
    csr(0, 0x3c, expected=0xabcdef01)
    observed("rejected_counter_access_preserves_snapshots")
    csr(1, 0x0c, int(mode == "BF16"))
    csr(1, 8, 2, error=1)
    image(0)
    observed("missing_complete_set")
    for entry in entries:
        install(entry)
        compare(entry)
    csr(1, 8, 6)
    image(1, 0)
    observed("complete_manifest_commit")
    embedding = entries[0]
    for address, data in ((0x0c, 2), (0x10, shape.layers * 96), (0x10, 0xffffffff),
                          (8, 8), (8, 3), (0x2c, 2), (0, 0), (0x30, 0)):
        csr(1, address, data, error=1)
        image(1)
    csr(0, 0x0c, expected=int(mode == "BF16"))
    compare(embedding)
    observed("invalid_CSR_write_atomicity")
    # Invalid staging writes must leave the preceding complete staging tuple intact.
    stage(embedding)
    for address, data in ((0x14, 12), (0x18, shape.layers), (0x1c, 8), (0x24, 2)):
        csr(1, address, data, error=1)
    csr(1, 0x2c, 1)
    compare(embedding)
    observed("invalid_staging_write_atomicity")
    for name, change in (
            ("wrong_padded_length", {5: embedding[5] - 64}),
            ("unaligned_base", {4: 1}),
            ("extended_bank_overflow", {4: (1 << 33) - 64}),
            ("index_layer_identity", {2: 1}), ("index_projection_identity", {3: 1})):
        candidate = list(embedding)
        for index, value in change.items():
            candidate[index] = value
        install(candidate, error=1)
        compare(embedding)
        observed(name)
    # Scratch/K/V are as disjoint from immutable weights as all other tensors.
    for kind in (8, 9, 10):
        entry = next(item for item in entries if item[1] == kind)
        candidate = (*entry[:4], embedding[4], entry[5])
        install(candidate, error=1)
        compare(entry)
        compare(embedding)
        observed(f"scratch_cache_overlap_kind_{kind}")
    high_embedding = (*embedding[:4], (1 << 33) - embedding[5], embedding[5])
    install(high_embedding)
    compare(high_embedding)
    csr(1, 8, 6)
    image(1)
    observed("exact_8GiB_endpoint")
    for signal in ("engine_busy", "load_busy"):
        set_signal(signal, 1)
        for address, value in ((8, 1), (8, 2), (0x0c, 1 - int(mode == "BF16")),
                               (0x10, 1), (0x2c, 1)):
            csr(1, address, value, error=1)
        csr(0, 0x0c, expected=int(mode == "BF16"))
        image(1)
        set_signal(signal, 0)
        observed(signal + "_mutation_rejected")
    for signal, value in (("emif_initialized", 0), ("load_failed", 1)):
        csr(1, 8, 1)
        set_signal(signal, value)
        csr(1, 8, 2, error=1)
        image(0)
        set_signal(signal, 1 - value)
        csr(1, 8, 6)
        image(1)
        observed(signal + "_commit_rejected")
    missing = entries[-1]
    install((*missing[:5], 0))
    csr(0, 0x14, error=1)
    lookup(missing[0], 0, 0, 1)
    csr(1, 8, 2, error=1)
    image(0)
    install(missing)
    csr(1, 8, 6)
    image(1, 0)
    observed("removed_required_tensor")
    lookup(shape.layers * 96, 0, 0, 1)
    lookup(0xffffffff, 0, 0, 1)
    observed("lookup_out_of_range")
    bench = CLOCK + r"""
reg csr_valid=0,csr_write=0,csr_rsp_ready=0;
reg [15:0] csr_address=0;
reg [31:0] csr_wdata=0;
wire csr_ready,csr_rsp_valid,csr_error;
wire [31:0] csr_rdata;
reg engine_busy=0,load_busy=0,load_failed=0,emif_initialized=1;
reg fault_event=0,image_modified=0,engine_ready=0;
reg [63:0] token_cycles=0,read_beats=0;
wire initialized,image_valid,storage_bf16,sticky_error,clear_load_error,configuration_busy;
reg lookup_valid=0,lookup_rsp_ready=0;
reg [31:0] lookup_index=0;
wire lookup_ready,lookup_rsp_valid,lookup_error;
wire [32:0] lookup_base;
wire [31:0] lookup_length;
integer comparisons=0,lookups=0,stalls=0,counter_reads=0,n,waiting;
integer observed_bins [0:BIN_LAST];
reg [191:0] instructions [0:INSTRUCTION_LAST];
reg [191:0] instruction;
integer step;
anvil_q1_ht_descriptors #(
 .NUM_LAYERS(2),.HIDDEN_SIZE(24),.INTERMEDIATE_SIZE(40),.NUM_KV_HEADS(1),
 .HEAD_DIM(8),.GROUP_SIZE(8),.VOCAB_SIZE(17),.MAX_SEQ_LEN(9)
) product(.*);
task check_reset;
 begin
  if({csr_ready,csr_rsp_valid,csr_rdata,csr_error,initialized,image_valid,
      storage_bf16,sticky_error,clear_load_error,configuration_busy,
      lookup_ready,lookup_rsp_valid,lookup_base,lookup_length,lookup_error} !== 109'b0)
   $fatal(1,"DESCRIPTOR_RESET_NONZERO_OR_XZ");
 end
endtask
always @(posedge clk or negedge clk) if(!rst_n) check_reset();
task csr(input wr,input [15:0] address,input [31:0] data,
         input expected_error,input [31:0] expected_data);
 integer delay_edges,k;
 reg [31:0] response;
 begin
  @(negedge clk);
  if(csr_ready!==1) $fatal(1,"DESCRIPTOR_CSR_NOT_READY");
  csr_valid=1;csr_write=wr;csr_address=address;csr_wdata=data;
  edge_tick();
  if(csr_rsp_valid!==0 || csr_ready!==0) $fatal(1,"DESCRIPTOR_CSR_ACCEPT_EDGE");
  @(negedge clk);csr_valid=0;
  delay_edges=0;
  while(csr_rsp_valid!==1 && delay_edges<10000) begin
   edge_tick();delay_edges=delay_edges+1;
   if((^{csr_rsp_valid,csr_ready,configuration_busy})===1'bx)
    $fatal(1,"DESCRIPTOR_CSR_ACTIVE_XZ");
  end
  if(csr_rsp_valid!==1 || csr_error!==expected_error ||
     (!wr && csr_rdata!==expected_data) || (^csr_rdata)===1'bx)
   $fatal(1,"DESCRIPTOR_CSR_MISMATCH addr=%h error=%b expected_error=%b data=%h expected=%h",
          address,csr_error,expected_error,csr_rdata,expected_data);
  if((!wr || address!=16'h002c && address!=16'h0008) && delay_edges!=1)
   $fatal(1,"DESCRIPTOR_ORDINARY_CSR_LATENCY");
  response=csr_rdata;
  for(k=0;k<7;k=k+1) begin
   @(negedge clk);
   // A second mutation while the response is reserved must not be accepted.
   csr_valid=1;csr_write=1;csr_address=16'h000c;csr_wdata=32'hffffffff;
   edge_tick();
   if(csr_rsp_valid!==1 || csr_error!==expected_error || csr_rdata!==response ||
      csr_ready!==0) $fatal(1,"DESCRIPTOR_CSR_STALL_OR_SECOND_ACCEPT");
   stalls=stalls+1;
  end
  @(negedge clk);csr_valid=0;csr_rsp_ready=1;
  edge_tick();
  if(csr_rsp_valid!==0) $fatal(1,"DESCRIPTOR_CSR_NOT_RETIRED");
  @(negedge clk);csr_rsp_ready=0;
  comparisons=comparisons+1;
  if(!wr && (address==16'h0030 || address==16'h0034 ||
             address==16'h0038 || address==16'h003c))
   counter_reads=counter_reads+1;
 end
endtask
task lookup(input [31:0] index,input [32:0] expected_base,
            input [31:0] expected_length,input expected_error);
 integer k;
 begin
  @(negedge clk);
  if(lookup_ready!==1) $fatal(1,"DESCRIPTOR_LOOKUP_NOT_READY");
  lookup_index=index;lookup_valid=1;
  edge_tick();
  if(lookup_rsp_valid!==1 || lookup_error!==expected_error ||
     lookup_base!==expected_base || lookup_length!==expected_length)
   $fatal(1,"DESCRIPTOR_LOOKUP_MISMATCH index=%0d base=%h length=%0d error=%b",
          index,lookup_base,lookup_length,lookup_error);
  @(negedge clk);lookup_valid=0;lookup_index=32'hffffffff;
  for(k=0;k<7;k=k+1) begin
   edge_tick();
   if(lookup_rsp_valid!==1 || lookup_ready!==0 || lookup_error!==expected_error ||
      lookup_base!==expected_base || lookup_length!==expected_length)
    $fatal(1,"DESCRIPTOR_LOOKUP_STALL_CHANGED");
  end
  @(negedge clk);lookup_rsp_ready=1;
  edge_tick();
  if(lookup_rsp_valid!==0) $fatal(1,"DESCRIPTOR_LOOKUP_NOT_RETIRED");
  @(negedge clk);lookup_rsp_ready=0;
  lookups=lookups+1;
 end
endtask
initial begin
 rst_n=0;
`ifndef VERILATOR
 #0;
`endif
 check_reset();
 for(n=0;n<=BIN_LAST;n=n+1) observed_bins[n]=0;
 repeat(6) edge_tick();
 @(negedge clk);rst_n=1;
 waiting=0;
 while(initialized!==1 && waiting<1000) begin edge_tick();waiting=waiting+1;end
 if(initialized!==1) $fatal(1,"DESCRIPTOR_INITIALIZATION_NOT_COMPLETE");
 $readmemh("INSTRUCTION_PATH",instructions);
 for(step=0;step<=INSTRUCTION_LAST;step=step+1) begin
  instruction=instructions[step];
  if((^instruction)===1'bx) $fatal(1,"DESCRIPTOR_STIMULUS_XZ");
  case(instruction[191:160])
   0: csr(instruction[128],instruction[111:96],instruction[95:64],
          instruction[32],instruction[31:0]);
   1: observed_bins[instruction[159:128]]=observed_bins[instruction[159:128]]+1;
   2: lookup(instruction[159:128],{instruction[64],instruction[127:96]},
             instruction[63:32],instruction[0]);
   3: if(image_valid!==instruction[128] ||
         (instruction[127:96]!=2 && sticky_error!==instruction[96]))
       $fatal(1,"DESCRIPTOR_IMAGE_STATE step=%0d valid=%b sticky=%b",
              step,image_valid,sticky_error);
   4: begin
       @(negedge clk);
       case(instruction[159:128])
        0: engine_busy=instruction[96];
        1: load_busy=instruction[96];
        2: emif_initialized=instruction[96];
        3: load_failed=instruction[96];
        default: $fatal(1,"DESCRIPTOR_INVALID_INPUT_INSTRUCTION");
       endcase
      end
   5: begin
       @(negedge clk);
       token_cycles=instruction[159:96];
       read_beats=instruction[95:32];
      end
   default: $fatal(1,"DESCRIPTOR_INVALID_INSTRUCTION");
  endcase
 end
 for(n=0;n<=BIN_LAST;n=n+1)
  if(observed_bins[n]<1) $fatal(1,"DESCRIPTOR_UNOBSERVED_BIN index=%0d",n);
 $display("CHECKS_PASSED descriptor_validation csr=%0d lookups=%0d stalls=%0d bins=%0d counter_reads=%0d",
          comparisons,lookups,stalls,BIN_LAST+1,counter_reads);
 $finish;
end
endmodule
"""
    vectors = evidence.folder / ("descriptor-instructions-" + mode.lower() + "-" + simulator + ".hex")
    vectors.write_text("\n".join(instructions) + "\n")
    relative = evidence.relative(vectors)
    evidence.record.setdefault("runtime_input_sha256", {})[relative] = hashlib.sha256(
        vectors.read_bytes()).hexdigest()
    evidence.flush()
    bench = (bench.replace("BIN_LAST", str(len(bins) - 1))
             .replace("INSTRUCTION_LAST", str(len(instructions) - 1))
             .replace("INSTRUCTION_PATH", relative))
    transcript = evidence.simulate(
        "descriptors-" + mode.lower() + "-" + simulator, bench,
        ["anvil_q1_ht_descriptors.sv"], simulator=simulator)
    counters = measurement_records(transcript, "CHECKS_PASSED descriptor_validation")
    if (len(counters) != 1 or counters[0]["bins"] != len(bins) or
            counters[0]["csr"] < len(entries) * 14 or
            counters[0]["lookups"] < len(entries) or
            counters[0]["counter_reads"] != counter_comparisons or
            counters[0]["stalls"] != counters[0]["csr"] * 7):
        raise AssertionError("descriptor validation lacks required observed comparisons")
    evidence.record["observations"].append({
        "scope": "public_descriptor_CSR_and_lookup_not_integrated_inference",
        "mode": mode, "simulator": simulator, "shape": vars(shape),
        "manifest": entries, "observed_bins": list(bins), "counters": counters[0],
        "oracle": "independent tensor-shape lengths, disjoint byte ranges and CSR contract",
    })
    evidence.flush()
    return counters[0]


def descriptor_checks(evidence, seed):
    del seed
    for mode in ("AWQ", "BF16"):
        observed = [descriptor_case(evidence, mode, simulator)
                    for simulator in ("iverilog", "verilator")]
        if observed[0] != observed[1]:
            raise AssertionError("descriptor dual-simulator counter disagreement")
