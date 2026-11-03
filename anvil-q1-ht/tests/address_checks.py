"""Public logical-to-DDR translation checks using independent tensor coordinates."""

import hashlib
import random

from experiments import CLOCK, measurement_records


def address_case(evidence, mode, simulator, seed):
    hidden, intermediate, kv, vocab, sequence, group = 24, 80, 8, 67, 9, 8
    rng = random.Random(seed)
    cases = []
    bins = {}

    def add(kind, layer, proj, row, col, write=0, fault=None):
        outputs = kv if proj in (1, 2) else intermediate if proj in (4, 5) else hidden
        inputs = intermediate if proj == 6 else hidden
        width = 4 if kind >= 8 or kind == 2 or (kind == 1 and mode == "AWQ") else 2
        if kind == 0:
            rows, columns, logical_row, column = hidden, vocab, col, row
        elif kind in (1, 2, 3):
            rows = inputs if kind == 1 else inputs // group
            columns = outputs // 8 if width == 4 else outputs
            logical_row, column = row, col
        elif kind in (4, 5, 6, 7):
            rows, columns, logical_row, column = 1, outputs if kind == 4 else hidden, row, col
        else:
            rows = 15 if kind == 8 else sequence
            columns = max(hidden, intermediate) if kind == 8 else 8
            logical_row, column = row, col
        legal = (
            0 <= kind <= 11 and 0 <= layer < 2 and
            (not write or kind in (8, 9, 10)) and
            (kind not in (0, 7, 8, 11) or (layer == 0 and proj == 0)) and
            (kind not in (1, 2, 3) or proj < 7) and
            (kind != 4 or proj < 3) and
            (kind not in (5, 6, 9, 10) or proj == 0) and
            not (mode == "BF16" and kind in (2, 3)) and
            0 <= logical_row < rows and 0 <= column < columns)
        if kind >= 8:
            offset = (logical_row * columns + column) * width
        else:
            panel = 8 if width == 4 else 64
            start = column // panel * panel
            count = min(panel, columns - start)
            offset = (start * rows + logical_row * count + column - start) * width
        base = 0x100000000 + ((kind * 16 + layer * 8 + proj) * 4096)
        length = (rows * columns * width + 63) // 64 * 64
        lookup_error = int(fault == "lookup")
        ddr_error = int(fault == "ddr")
        if fault == "short":
            length = offset + width - 1
        elif fault == "exact":
            length = offset + width
        elif fault == "bank_end":
            base, length = (1 << 33) - 64, 64
        elif fault == "bank_boundary":
            base, length = (1 << 33) - 64, max(128, offset + width)
        address = base + offset
        expect_ddr = int(legal and not lookup_error and offset + width <= length
                         and address + width <= (1 << 33))
        error = int(not expect_ddr or ddr_error)
        data = rng.getrandbits(32)
        salt = len(cases) & 255
        beat = bytes((salt + j * 13) & 255 for j in range(64))
        expected = 0 if error or write else int.from_bytes(
            beat[address % 64:address % 64 + width], "little")
        byteenable = ((15 << (address % 64)) if write else (1 << 64) - 1)
        label = ("reject_" + fault if fault and error else
                 "accepted_" + fault if fault else
                 "kind_" + str(kind) + ("_write" if write else "_read")
                 + ("_rejected" if error else "_accepted"))
        bin_index = bins.setdefault(label, len(bins))
        fields = [
            write, kind, layer, proj, row, col, data, int(mode == "BF16"),
            base & 0xffffffff, base >> 32, length, lookup_error,
            error, int(legal), ((layer * 12) + kind) * 8 + proj, expect_ddr,
            (address & ~63) & 0xffffffff, (address & ~63) >> 32,
            expected, byteenable & 0xffffffff, byteenable >> 32,
            (address % 64) * 8, width, salt, ddr_error, bin_index,
        ]
        if any(not 0 <= value < (1 << 32) for value in fields):
            raise ValueError("address stimulus field exceeds uint32")
        cases.append(fields + [0] * (32 - len(fields)))

    identities = [(0, 0, 0), (7, 0, 0), (8, 0, 0), (11, 0, 0)]
    for layer in range(2):
        identities.extend((kind, layer, proj) for kind in (1, 2, 3) for proj in range(7))
        identities.extend((4, layer, proj) for proj in range(3))
        identities.extend((kind, layer, 0) for kind in (5, 6, 9, 10))
    for kind, layer, proj in identities:
        outputs = kv if proj in (1, 2) else intermediate if proj in (4, 5) else hidden
        inputs = intermediate if proj == 6 else hidden
        rows = (vocab if kind == 0 else inputs if kind == 1 else inputs // group
                if kind in (2, 3) else 15 if kind == 8 else sequence
                if kind >= 9 else 1)
        cols = (hidden if kind == 0 else outputs // 8
                if kind == 2 or (kind == 1 and mode == "AWQ") else outputs
                if kind in (1, 3, 4) else max(hidden, intermediate) if kind == 8
                else kv if kind in (9, 10) else 8 if kind == 11 else hidden)
        coordinates = {(r, c) for r in (0, rows - 1)
                       for c in (0, min(7, cols - 1), min(63, cols - 1),
                                 min(64, cols - 1), cols - 1)}
        if kind == 0:
            coordinates |= {(r, c) for r in (63, 64, 66) for c in (0, hidden - 1)}
        for row, col in sorted(coordinates):
            add(kind, layer, proj, row, col)
            if kind in (8, 9, 10):
                add(kind, layer, proj, row, col, write=1)
        add(kind, layer, proj, rows, 0, fault="row")
        add(kind, layer, proj, 0, cols, fault="column")
        add(kind, layer, proj, 0, 0, write=1, fault="write_permission")
    for kind in range(12):
        for fault in ("lookup", "ddr", "short", "exact", "bank_end"):
            add(kind, 0, 0, 0, 0, fault=fault)
        add(kind, 0, 0, 1, 0, fault="bank_boundary")
        add(kind, 2, 0, 0, 0, fault="layer")
        add(kind, 0, 7, 0, 0, fault="projection")
        add(kind, 0, 0, 0xffffffff, 0, fault="wide_row")
        add(kind, 0, 0, 0, 0xffffffff, fault="wide_column")
    for kind in range(12, 16):
        add(kind, 0, 0, 0, 0, fault="kind")
    # Exercise every physical byte lane for 16- and 32-bit entries.
    for col in range(hidden):
        add(7, 0, 0, 0, col)
    for col in range(80):
        add(3 if mode == "AWQ" else 1, 0, 4, 0, col)
        add(8, 0, 0, 0, col, write=col & 1)
    path = evidence.folder / f"address-{mode.lower()}-{simulator}.hex"
    path.write_text("".join(
        "".join(f"{word:08x}" for word in reversed(fields)) + "\n" for fields in cases))
    evidence.record.setdefault("runtime_input_sha256", {})[
        evidence.relative(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
    evidence.flush()
    bench = CLOCK + r"""
reg storage_bf16=0,req_valid=0,req_write=0,rsp_ready=0;
reg [3:0] req_kind=0;
reg [31:0] req_layer=0,req_row=0,req_col=0,req_wdata=0;
reg [2:0] req_proj=0;
wire req_ready,rsp_valid,rsp_error;
wire [31:0] rsp_data;
wire lookup_valid,lookup_rsp_ready;
wire [31:0] lookup_index;
reg lookup_ready=0,lookup_rsp_valid=0,lookup_error=0;
reg [32:0] lookup_base=0;
reg [31:0] lookup_length=0;
wire ddr_valid,ddr_write,ddr_rsp_ready;
wire [32:0] ddr_address;
wire [511:0] ddr_wdata;
wire [63:0] ddr_byteenable;
reg ddr_ready=0,ddr_rsp_valid=0,ddr_rsp_error=0;
reg [511:0] ddr_rsp_data=0;
reg [1023:0] vectors [0:CASE_LAST];
reg [1023:0] instruction;
integer observed [0:BIN_LAST];
integer comparisons=0,lookups=0,transfers=0,errors=0,immediate=0,delayed=0;
integer s,n,j,waits,lookup_count,ddr_count,lookup_age,ddr_age;
integer lookup_due,ddr_due,stall_edges,stalls=0;
reg [511:0] expected_write;
function automatic [31:0] f(input integer index);
 begin f=instruction[32*index+:32];end
endfunction
anvil_q1_ht_address #(
 .NUM_LAYERS(2),.HIDDEN_SIZE(24),.INTERMEDIATE_SIZE(80),.NUM_KV_HEADS(1),
 .HEAD_DIM(8),.GROUP_SIZE(8),.VOCAB_SIZE(67),.MAX_SEQ_LEN(9)
) product(.*);
task check_reset;
 begin
  if({req_ready,rsp_valid,rsp_data,rsp_error,lookup_valid,lookup_index,lookup_rsp_ready,
      ddr_valid,ddr_write,ddr_address,ddr_wdata,ddr_byteenable,ddr_rsp_ready} !== 781'b0)
   $fatal(1,"ADDRESS_RESET_XZ_OR_NONZERO");
 end
endtask
always @(posedge clk or negedge clk) if(!rst_n) check_reset();
initial begin
 rst_n=0;`RESET_DELTA check_reset();
 $readmemh("VECTOR_PATH",vectors);
 for(j=0;j<=BIN_LAST;j=j+1) observed[j]=0;
 repeat(3) edge_tick();
 @(negedge clk);rst_n=1;
 for(s=0;s<=CASE_LAST;s=s+1) begin
  instruction=vectors[s];
  @(negedge clk);
  storage_bf16=f(7);req_write=f(0);req_kind=f(1);req_layer=f(2);req_proj=f(3);
  req_row=f(4);req_col=f(5);req_wdata=f(6);req_valid=1;
  if(req_ready!==1) $fatal(1,"ADDRESS_REQUEST_NOT_READY");
  edge_tick();
  @(negedge clk);req_valid=0;
  // Inputs are no longer owned once accepted; in particular mode must be latched.
  storage_bf16=!f(7);req_row=32'hffffffff;req_col=32'hffffffff;
  lookup_count=0;ddr_count=0;lookup_age=0;ddr_age=0;lookup_due=-1;ddr_due=-1;
  stall_edges=s%3==0 ? 1 : s%3==1 ? 7 : 31;
  begin : await_result
  for(waits=0;waits<500;waits=waits+1) begin
   lookup_ready=0;lookup_rsp_valid=0;ddr_ready=0;ddr_rsp_valid=0;
   lookup_base={f(9)[0],f(8)};
   lookup_length=f(10);lookup_error=f(11);ddr_rsp_error=f(24);
   for(j=0;j<64;j=j+1) ddr_rsp_data[8*j+:8]=(f(23)+13*j)&255;
   if(lookup_valid===1) begin
    if(f(13)!==1 || lookup_count!=0 || lookup_index!==f(14))
     $fatal(1,"ADDRESS_LOOKUP_MISMATCH case=%0d",s);
    lookup_age=lookup_age+1;lookup_ready=lookup_age>stall_edges;
    if(lookup_ready) begin
     if(s%2==0) lookup_rsp_valid=1;else lookup_due=waits+3;
    end
   end
   if(lookup_due==waits) lookup_rsp_valid=1;
   if(ddr_valid===1) begin
    expected_write=0;
    if(f(0)) expected_write={{480{1'b0}},f(6)}<<f(21);
    if(f(15)!==1 || ddr_count!=0 || ddr_write!==f(0)[0] ||
       ddr_address!=={f(17)[0],f(16)} || ddr_wdata!==expected_write ||
       ddr_byteenable!=={f(20),f(19)})
     $fatal(1,"ADDRESS_DDR_MISMATCH case=%0d kind=%0d row=%0d col=%0d actual=%h expected=%h",
            s,f(1),f(4),f(5),ddr_address,{f(17)[0],f(16)});
    ddr_age=ddr_age+1;ddr_ready=ddr_age>stall_edges;
    if(ddr_ready) begin
     if(s%2==0) ddr_rsp_valid=1;else ddr_due=waits+5;
    end
   end
   if(ddr_due==waits) ddr_rsp_valid=1;
   #0.001;
   if(lookup_rsp_valid && lookup_rsp_ready!==1) $fatal(1,"ADDRESS_LOOKUP_RESPONSE_NOT_READY");
   if(ddr_rsp_valid && ddr_rsp_ready!==1) $fatal(1,"ADDRESS_DDR_RESPONSE_NOT_READY");
   if(lookup_valid && lookup_ready) begin lookup_count=lookup_count+1;lookups=lookups+1;end
   if(ddr_valid && ddr_ready) begin
    ddr_count=ddr_count+1;transfers=transfers+1;
    if(ddr_rsp_valid) immediate=immediate+1;else delayed=delayed+1;
   end
   edge_tick();
   if(rsp_valid===1) begin
    if(rsp_error!==f(12)[0] || rsp_data!==f(18) ||
       lookup_count!=f(13) || ddr_count!=f(15))
     $fatal(1,"ADDRESS_RESULT_MISMATCH case=%0d data=%h expected=%h error=%b expected_error=%0d",
            s,rsp_data,f(18),rsp_error,f(12));
    disable await_result;
   end
   end
   @(negedge clk);
  end
  if(rsp_valid!==1) $fatal(1,"ADDRESS_RESULT_MISSING case=%0d",s);
  @(negedge clk);
  lookup_ready=0;lookup_rsp_valid=0;ddr_ready=0;ddr_rsp_valid=0;
  repeat(7) begin
   edge_tick();
   if(rsp_valid!==1 || rsp_data!==f(18) || rsp_error!==f(12)[0] ||
      req_ready!==0 || lookup_valid!==0 || ddr_valid!==0)
    $fatal(1,"ADDRESS_STALLED_RESULT_CHANGED case=%0d",s);
   stalls=stalls+1;
  end
  @(negedge clk);rsp_ready=1;
  edge_tick();
  if(rsp_valid!==0 || req_ready!==1) $fatal(1,"ADDRESS_RESULT_NOT_RETIRED");
  @(negedge clk);rsp_ready=0;
  comparisons=comparisons+1;errors=errors+f(12);observed[f(25)]=observed[f(25)]+1;
 end
 for(j=0;j<=BIN_LAST;j=j+1) if(observed[j]==0) $fatal(1,"ADDRESS_MISSING_BIN");
 if(immediate==0 || delayed==0 || stalls==0) $fatal(1,"ADDRESS_MISSING_PROTOCOL_COVERAGE");
 $display("CHECKS_PASSED address comparisons=%0d lookups=%0d transfers=%0d errors=%0d immediate=%0d delayed=%0d stalls=%0d bins=BIN_COUNT",
          comparisons,lookups,transfers,errors,immediate,delayed,stalls);
 $finish;
end
endmodule
"""
    # Function-call bit selects are not portable to Icarus; narrow by casts.
    for index in (0, 9, 12, 17):
        bench = bench.replace(f"f({index})[0]", f"1'(f({index}))")
    bench = bench.replace("VECTOR_PATH", evidence.relative(path))
    bench = bench.replace("CASE_LAST", str(len(cases) - 1))
    bench = bench.replace("BIN_LAST", str(len(bins) - 1)).replace("BIN_COUNT", str(len(bins)))
    transcript = evidence.simulate(
        f"address-{mode.lower()}-{simulator}", bench,
        ["anvil_q1_ht_address.sv"], simulator=simulator)
    records = measurement_records(transcript, "CHECKS_PASSED address")
    expected = {"comparisons": len(cases), "lookups": sum(c[13] for c in cases),
                "transfers": sum(c[15] for c in cases), "errors": sum(c[12] for c in cases),
                "stalls": len(cases) * 7, "bins": len(bins)}
    if len(records) != 1 or any(records[0].get(k) != v for k, v in expected.items()):
        raise AssertionError("address comparisons or directed coverage are incomplete")
    evidence.record.setdefault("address_checks", []).append({
        "mode": mode, "simulator": simulator, "seed": seed, "observed": records[0],
        "bins": list(bins), "scope": "logical translator public ports, not decoder or physical DDR",
        "service": "1/7/31 command stalls; coincident or delayed lookup/DDR response; seven result stalls",
        "numerical_model": "little-endian coordinate-to-panel mapping, no DUT internal observations",
    })
    evidence.flush()
    return records[0]


def address_checks(evidence, seed):
    for mode in ("AWQ", "BF16"):
        observed = [address_case(evidence, mode, simulator, seed)
                    for simulator in ("iverilog", "verilator")]
        if observed[0] != observed[1]:
            raise AssertionError("address translator simulator counters differ")
