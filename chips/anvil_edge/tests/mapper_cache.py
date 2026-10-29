"""Public-port descriptor-cache regression and retained-source A/B measurement.

Only immutable metadata may be cached. Tensor replies always come from the DDR
transaction model. The same alternating workload and assertions run against the
retained uncached mapper and the delivered mapper.
"""

import copy
import difflib
import hashlib
import json
import re
import shutil
import struct
from pathlib import Path

from storage import synthetic_image


BASELINE_RECEIPT = (
    "evidence/preparation/official-qwen-shell-general-"
    "79870737978648f58850a61e30a567f0/receipt.json"
)
BASELINE_MAPPER_SHA256 = "5a9f273d97a00524d6ce00043c367bb16e78613a79b343ec5d70f79d9d864558"
SOURCES = [
    "rtl/anvil_edge_parameters.sv", "rtl/anvil_edge_signed_multiplier.sv",
    "rtl/anvil_edge_tensor_mapper.sv",
]


BENCH = r"""
module bench;
  reg clk=0;
  always #5 clk=~clk;
  reg rst_n;
  reg config_valid=1;
  reg [63:0] cfg_directory_base=@DIRECTORY@,cfg_immutable_base=@IMMUTABLE@;
  reg [63:0] cfg_writable_base=@WRITABLE@;
  reg [31:0] cfg_directory_count=32;
  reg [63:0] cfg_immutable_bytes=@IMMUTABLE_BYTES@,cfg_writable_bytes=@WRITABLE_BYTES@;
  reg mem_req_valid=0,mem_req_write=0,mem_rsp_ready=0;
  reg [3:0] mem_req_kind=0;
  reg [31:0] mem_req_layer=0,mem_req_row=0,mem_req_col=0,mem_req_wdata=0;
  reg [2:0] mem_req_proj=0;
  wire mem_req_ready,mem_rsp_valid,mem_rsp_error,idle;
  wire [31:0] mem_rsp_rdata;
  wire ddr_req_valid,ddr_req_write,ddr_rsp_ready;
  wire [63:0] ddr_req_addr;
  wire [31:0] ddr_req_wdata;
  wire [3:0] ddr_req_wstrb;
  reg ddr_req_ready=0,ddr_rsp_valid=0,ddr_rsp_error=0;
  reg [31:0] ddr_rsp_rdata=0;
  anvil_edge_tensor_mapper #(
    .NUM_LAYERS(1),.HIDDEN_SIZE(8),.INTERMEDIATE_SIZE(8),
    .NUM_Q_HEADS(1),.NUM_KV_HEADS(1),.HEAD_DIM(8),.GROUP_SIZE(8),
    .VOCAB_SIZE(257),.MAX_SEQ_LEN(4),.DDR_BYTES(65536)
  ) dut(.*);
  reg [31:0] directory[0:391];
  reg [31:0] rng=@SEED@;
  integer cycle=0,comparisons=0,dir_requests=0,data_requests=0,responses=0;
  integer delay_count=0,request_stalls=0,response_stalls=0,epoch_changes=0;
  reg outstanding=0,pending_error=0,ddr_held=0,response_held=0;
  reg [100:0] held_ddr;
  reg [32:0] held_response;
  reg [63:0] pending_address=0,expected_address=0;
  reg [63:0] inject_directory_address=64'hffffffffffffffff;
  reg inject_data_error=0,expected_error=0,expected_write=0;
  reg withdraw_on_request=0;
  function automatic bit in_directory(input [63:0] address);
    return address>=cfg_directory_base && address<cfg_directory_base+1568;
  endfunction
  function automatic [31:0] value_at(input [63:0] address);
    if (in_directory(address)) return directory[(address-cfg_directory_base)>>2];
    return 32'(address*32'h9e3779b9)^32'ha5c31927;
  endfunction
  task automatic reset_check;
    if ({mem_req_ready,mem_rsp_valid,mem_rsp_error,mem_rsp_rdata,idle,
         ddr_req_valid,ddr_req_write,ddr_req_addr,ddr_req_wdata,ddr_req_wstrb,
         ddr_rsp_ready}!==139'd0) $fatal(1,"CACHE_RESET");
  endtask
  always @(posedge clk or negedge clk) if (!rst_n) reset_check();
  always @(negedge clk) if (rst_n) begin
    rng=rng ^ (rng<<13); rng=rng ^ (rng>>17); rng=rng ^ (rng<<5);
    ddr_req_ready=rng[0] && cycle%5!=0;
    if (outstanding && !ddr_rsp_valid) begin
      if (delay_count==0) begin
        ddr_rsp_valid<=1;
        ddr_rsp_rdata=value_at(pending_address);
        ddr_rsp_error=pending_error;
      end else delay_count=delay_count-1;
    end
  end
  always @(posedge clk) begin
    cycle=cycle+1;
    if (rst_n) begin
      if ((^{mem_req_ready,mem_rsp_valid,mem_rsp_error,mem_rsp_rdata,idle,
             ddr_req_valid,ddr_req_write,ddr_req_addr,ddr_req_wdata,
             ddr_req_wstrb,ddr_rsp_ready})===1'bx) $fatal(1,"CACHE_XZ");
      if (ddr_held && (!ddr_req_valid ||
          {ddr_req_write,ddr_req_addr,ddr_req_wdata,ddr_req_wstrb}!==held_ddr))
        $fatal(1,"CACHE_DDR_STABILITY");
      ddr_held=ddr_req_valid && !ddr_req_ready;
      held_ddr={ddr_req_write,ddr_req_addr,ddr_req_wdata,ddr_req_wstrb};
      if (ddr_held) request_stalls=request_stalls+1;
      if (response_held && (!mem_rsp_valid ||
          {mem_rsp_error,mem_rsp_rdata}!==held_response))
        $fatal(1,"CACHE_RESPONSE_STABILITY");
      response_held=mem_rsp_valid && !mem_rsp_ready;
      held_response={mem_rsp_error,mem_rsp_rdata};
      if (response_held) response_stalls=response_stalls+1;
      if (ddr_rsp_valid && ddr_rsp_ready) begin
        if (!outstanding) $fatal(1,"CACHE_ORPHAN_RESPONSE");
        outstanding=0; ddr_rsp_valid<=0; responses=responses+1;
      end
      if (ddr_req_valid && ddr_req_ready) begin
        if (outstanding || ddr_req_addr[1:0]!=0 || ddr_req_addr>=65536)
          $fatal(1,"CACHE_DDR_BOUNDS");
        if (in_directory(ddr_req_addr)) begin
          if (ddr_req_write || ddr_req_wstrb!==0)
            $fatal(1,"CACHE_DIRECTORY_WRITE");
          dir_requests=dir_requests+1;
          pending_error=ddr_req_addr==inject_directory_address;
        end else begin
          if (ddr_req_addr!==expected_address || ddr_req_write!==expected_write ||
              ddr_req_wstrb!==(expected_write ? 4'hf : 4'h0) ||
              (expected_write && ddr_req_wdata!==32'h81478521))
            $fatal(1,"CACHE_DATA_TUPLE expected=%h observed=%h",expected_address,ddr_req_addr);
          data_requests=data_requests+1; pending_error=inject_data_error;
        end
        outstanding=1; pending_address=ddr_req_addr; delay_count=1+rng[4:2];
      end
    end
  end
  task automatic tick; begin @(posedge clk); #1; end endtask
  task automatic epoch;
    begin
      if (!idle || outstanding || mem_rsp_valid) $fatal(1,"CACHE_RELOAD_NOT_IDLE");
      @(negedge clk); #1; config_valid=0;
      repeat (3) begin tick(); if (mem_req_ready) $fatal(1,"CACHE_WITHDRAWN_READY"); end
      @(negedge clk); #1; config_valid=1; epoch_changes=epoch_changes+1;
    end
  endtask
  task automatic transaction(input string label,input bit wr,input integer kind,
      input integer layer,input integer projection,input integer row,input integer col,
      input [63:0] address,input bit bad,input integer expected_data_requests);
    integer start_cycle,start_dirs,start_data;
    begin
      @(negedge clk); #1;
      start_cycle=cycle; start_dirs=dir_requests; start_data=data_requests;
      expected_address=address; expected_error=bad; expected_write=wr;
      mem_req_valid=1; mem_req_write=wr; mem_req_kind=kind; mem_req_layer=layer;
      mem_req_proj=projection; mem_req_row=row; mem_req_col=col;
      mem_req_wdata=32'h81478521;
      do begin @(posedge clk); end while (!mem_req_ready);
      if (mem_rsp_valid) $fatal(1,"CACHE_SAME_EDGE_REPLY");
      #1; @(negedge clk); #1; mem_req_valid=0;
      if (withdraw_on_request) begin config_valid=0; epoch_changes=epoch_changes+1; end
      while (!mem_rsp_valid) tick();
      repeat (7) begin
        if (mem_rsp_valid!==1 || mem_rsp_error!==bad ||
            mem_rsp_rdata!==(bad ? 32'd0 : value_at(address)) || mem_req_ready!==0)
          $fatal(1,"CACHE_RESPONSE label=%s expected_error=%b observed_error=%b data=%h",
                 label,bad,mem_rsp_error,mem_rsp_rdata);
        tick();
      end
      if (outstanding || data_requests-start_data!=expected_data_requests)
        $fatal(1,"CACHE_TRANSACTION_COUNTS label=%s",label);
      @(negedge clk); #1; mem_rsp_ready=1; tick();
      @(negedge clk); #1; mem_rsp_ready=0;
      if (mem_rsp_valid || !idle) $fatal(1,"CACHE_RETIREMENT");
      $display("CACHE_MEASURE %s %0d %0d %0d",
               label,cycle-start_cycle,dir_requests-start_dirs,data_requests-start_data);
      comparisons=comparisons+1;
    end
  endtask
  initial begin
    rst_n=0; #0; reset_check();
    $readmemh("@DIRECTORY_FILE@",directory);
    repeat (2) tick(); @(negedge clk); #1; rst_n=1;
    @TRANSACTIONS@
    if (comparisons!=@COMPARISONS@ || request_stalls==0 || response_stalls==0 ||
        outstanding || responses!=dir_requests+data_requests)
      $fatal(1,"CACHE_FINAL_COUNTS");
    $display("CACHE_TOTAL cycles=%0d directory=%0d data=%0d epochs=%0d",
             cycle,dir_requests,data_requests,epoch_changes);
    $display("COMPARED %0d",comparisons); $finish;
  end
  initial begin repeat (400000) @(posedge clk); $fatal(1,"CACHE_CYCLE_BOUND"); end
endmodule
"""


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def fixture_bench(evidence, seed, lifecycle):
    fixture = synthetic_image(257)
    records = {record[:3]: (index, record)
               for index, record in enumerate(fixture["regions"])}
    commands, labels = [], []

    def request(label, key, *, row=0, column=0, write=False, bad=False,
                data_requests=None, offset=None, layer=None):
        _, record = records[key]
        _, _, _, storage, displacement, _, columns, _, _, _ = record
        address = fixture["destinations"][storage] + (
            displacement if offset is None else offset) + 4 * (row * columns + column)
        fields = [int(write), *key, row, column, address, int(bad),
                  int(not bad) if data_requests is None else data_requests]
        if layer is not None:
            fields[2] = layer
        arguments = [f"{64 if index == 6 else 32}'d{value}"
                     for index, value in enumerate(fields)]
        commands.append(f'transaction("{label}",' + ",".join(arguments) + ");")
        labels.append(label)

    activation, embedding, gamma = (8, 0, 0), (0, 0, 0), (7, 0, 0)
    for iteration in range(16):
        request(f"alternate-a{iteration}", activation, row=14, column=iteration % 8)
        request(f"alternate-e{iteration}", embedding, row=iteration, column=iteration % 8)
    if lifecycle:
        # Two warmed keys remain legal only for each new request's own coordinates.
        request("hit-bad-row", activation, row=13, bad=True)
        request("hit-bad-column", activation, row=3, column=8, bad=True)
        request("hit-bad-layer", embedding, layer=1, bad=True)
        request("hit-readonly-write", embedding, write=True, bad=True)
        request("hit-overflow-row", embedding, row=0xffffffff, bad=True)
        request("hit-good-write", activation, row=14, write=True)
        commands.append("inject_data_error=1;")
        request("hit-data-read-error", embedding, bad=True, data_requests=1)
        request("hit-data-write-error", activation, write=True, bad=True, data_requests=1)
        commands.append("inject_data_error=0;")
        request("hit-after-data-error", embedding)
        request("evict-gamma", gamma)
        request("evict-activation", activation)
        request("evict-embedding", embedding)

        # A failed descriptor validation must never leave a hit, even if repaired
        # without an epoch change. Only unsuccessful records are edited in-place.
        index, record = records[gamma]
        for field, corrupt in ((3, 0x103), (6, 2), (8, 3), (9, 3),
                               (10, record[-1] + 4), (5, 0xffffffff)):
            word_index = 8 + index * 12 + field
            original = struct.unpack_from("<I", fixture["segments"][0x101], 4 * word_index)[0]
            commands.extend(["epoch();", f"directory[{word_index}]=32'd{corrupt};"])
            request(f"failed-fill-{field}", gamma, bad=True)
            commands.append(f"directory[{word_index}]=32'd{original};")
            request(f"repair-fill-{field}", gamma)
            request(f"repair-hit-{field}", gamma, column=7)
        for field in (0, 11):
            address = fixture["destinations"][0x101] + 32 + index * 48 + 4 * field
            commands.extend(["epoch();", f"inject_directory_address=64'd{address};"])
            request(f"directory-error-{field}", gamma, bad=True)
            commands.append("inject_directory_address=64'hffffffffffffffff;")
            request(f"directory-repair-{field}", gamma)
            request(f"directory-hit-{field}", gamma)

        # Swap equally sized immutable records while configuration is withdrawn;
        # every base and extent stays unchanged in the new committed epoch.
        other_index, other_record = records[(5, 0, 0)]
        commands.append("epoch();")
        request("reload-warm", gamma)
        commands.append("epoch();")
        commands.extend([
            f"directory[{8+index*12+4}]=32'd{other_record[4]};",
            f"directory[{8+other_index*12+4}]=32'd{record[4]};",
        ])
        request("same-address-reload", gamma, offset=other_record[4])
        request("same-address-hit", gamma, column=7, offset=other_record[4])
        commands.append("cfg_directory_count=31;")
        request("hit-invalid-config", gamma, bad=True)
        commands.append("cfg_directory_count=32;")
        request("context-refill", gamma, offset=other_record[4])
        request("hit-restored-context", gamma, offset=other_record[4])
        # Withdrawal during a miss must suppress its later fill. Its already
        # accepted DDR operation must nevertheless complete, without rerouting.
        commands.extend(["epoch();", "withdraw_on_request=1;"])
        request("withdraw-inflight", embedding)
        commands.extend(["withdraw_on_request=0;", "config_valid=1;"])
        request("withdraw-refill", embedding)
        request("withdraw-hit", embedding)
        # Reset discards a warm epoch; four-state startup is also checked above.
        commands.extend([
            "@(negedge clk); #1; rst_n=0;",
            "repeat (2) tick(); @(negedge clk); #1; rst_n=1;",
        ])
        request("reset-refill", embedding)
        request("reset-hit", embedding)
    data = fixture["segments"][0x101]
    directory = evidence.path / f"cache-directory-s{seed}.hex"
    directory.write_text("".join(f"{word[0]:08x}\n" for word in struct.iter_unpack("<I", data)),
                         encoding="ascii")
    values = {
        "SEED": seed, "DIRECTORY": fixture["destinations"][0x101],
        "IMMUTABLE": fixture["destinations"][0x102],
        "WRITABLE": fixture["destinations"][0x103],
        "IMMUTABLE_BYTES": len(fixture["segments"][0x102]),
        "WRITABLE_BYTES": len(fixture["segments"][0x103]),
        "DIRECTORY_FILE": evidence.relative(directory),
        "TRANSACTIONS": "\n".join(commands), "COMPARISONS": len(labels),
    }
    bench = BENCH
    for key, value in values.items():
        bench = bench.replace(f"@{key}@", str(value))
    require(not re.search(r"@[A-Z_]+@", bench), "Unexpanded mapper-cache fixture")
    return bench, labels


def measured(evidence, result, labels):
    root = Path(__file__).resolve().parent.parent
    output = (root / result["simulation_receipt"]["stdout"]).read_text()
    rows = [{"label": match[1], "cycles": int(match[2]),
             "directory_requests": int(match[3]), "data_requests": int(match[4])}
            for match in re.finditer(r"^CACHE_MEASURE (\S+) (\d+) (\d+) (\d+)$",
                                     output, re.MULTILINE)]
    require([row["label"] for row in rows] == labels, "Missing/reordered mapper measurements")
    return rows


def run_mapper_cache(evidence, comparison=False):
    """L1 is self-contained; optional preparation A/B uses a hashed old source."""
    root = Path(__file__).resolve().parent.parent
    metrics = []
    if comparison:
        prior = root / BASELINE_RECEIPT
        receipt = json.loads(prior.read_bytes())
        old = prior.parent / "sources/rtl/anvil_edge_tensor_mapper.sv"
        require(hashlib.sha256(old.read_bytes()).hexdigest() == BASELINE_MAPPER_SHA256 ==
                receipt["source_sha256"]["rtl/anvil_edge_tensor_mapper.sv"],
                "Retained uncached mapper provenance mismatch")
        retained = evidence.path / "uncached-mapper.sv"
        shutil.copyfile(old, retained)
        evidence.record["descriptor_cache_baseline"] = {
            "receipt": BASELINE_RECEIPT,
            "receipt_sha256": hashlib.sha256(prior.read_bytes()).hexdigest(),
            "mapper_sha256": BASELINE_MAPPER_SHA256,
            "disposable_copy": evidence.relative(retained),
            "scope": "Only the mapper differs; current parameters/multiplier and identical bench",
        }
        for seed in (1, 17, 89):
            bench, labels = fixture_bench(evidence, seed, False)
            before = copy.copy(evidence)
            before.source_overrides = {**evidence.source_overrides,
                                       "rtl/anvil_edge_tensor_mapper.sv": evidence.relative(retained)}
            old_result = before.simulate(f"cache-before-s{seed}", bench, SOURCES, len(labels))
            new_result = evidence.simulate(f"cache-after-s{seed}", bench, SOURCES, len(labels))
            require(old_result["bench_sha256"] == new_result["bench_sha256"],
                    "A/B benchmark stimulus or assertions changed")
            old_rows, new_rows = (measured(evidence, result, labels)
                                  for result in (old_result, new_result))
            old_cycles = sum(row["cycles"] for row in old_rows)
            new_cycles = sum(row["cycles"] for row in new_rows)
            old_dirs = sum(row["directory_requests"] for row in old_rows)
            new_dirs = sum(row["directory_requests"] for row in new_rows)
            require(all(row["data_requests"] == 1 for row in old_rows + new_rows),
                    "Caching bypassed actual tensor DDR access")
            require(new_cycles < old_cycles and new_dirs < old_dirs,
                    "Descriptor caching has not demonstrated useful reduction")
            metrics.append({
                "seed": seed, "operations": len(labels),
                "before": {"cycles": old_cycles, "directory_requests": old_dirs, "rows": old_rows},
                "after": {"cycles": new_cycles, "directory_requests": new_dirs, "rows": new_rows},
                "cycle_speedup": old_cycles / new_cycles,
                "directory_reduction": 1 - new_dirs / old_dirs,
                "before_receipt": old_result["simulation_receipt"],
                "after_receipt": new_result["simulation_receipt"],
            })
        evidence.record["descriptor_cache_comparison"] = metrics
        (evidence.path / "descriptor-cache-comparison.json").write_text(
            json.dumps(metrics, indent=2) + "\n", encoding="ascii")
    for seed in (1, 17, 89):
        bench, labels = fixture_bench(evidence, seed, True)
        results = [evidence.simulate(f"cache-lifecycle-s{seed}", bench, SOURCES, len(labels))]
        if seed == 17:
            results.append(evidence.simulate("cache-lifecycle-four-state-s17",
                                            bench, SOURCES, len(labels),
                                            simulator="iverilog"))
        for result in results:
            rows = measured(evidence, result, labels)
            for row in rows:
                label, count = row["label"], row["directory_requests"]
                hit = ((label.startswith("alternate-") and label not in
                        ("alternate-a0", "alternate-e0")) or
                       label.startswith(("hit-", "repair-hit-", "directory-hit-")) or
                       label in ("same-address-hit", "withdraw-hit", "reset-hit"))
                require(count == 0 if hit else count > 0,
                        f"Cache hit/miss lifecycle not observed: {label}: {count}")
            evidence.record.setdefault("descriptor_cache_lifecycle", []).append({
                "seed": seed, "compared": len(rows), "rows": rows,
                "simulator": result["simulator"], "receipt": result["simulation_receipt"],
                "scope": "Public request/address/error/data/stall observations, no DUT internals",
            })
    run_cache_mutations(evidence, bench, labels)


def run_cache_mutations(evidence, bench, labels):
    root = Path(__file__).resolve().parent.parent
    original = (root / SOURCES[-1]).read_text()
    for name, before, after, assertion in (
        ("offset", "cache_offset[cache_victim]<=region_offset;",
         "cache_offset[cache_victim]<=region_offset+64'd4;", "CACHE_DATA_TUPLE"),
        ("epoch", "if (!config_valid || !cache_context_matches) begin",
         "if (1'b0) begin", "CACHE_RESPONSE"),
    ):
        require(original.count(before) == 1, f"Ambiguous cache mutation: {name}")
        directory = evidence.path / f"cache-defect-{name}"
        directory.mkdir()
        source = directory / "mapper.sv"
        changed = original.replace(before, after)
        source.write_text(changed, encoding="ascii")
        diff = directory / "mutation.diff"
        diff.write_text("".join(difflib.unified_diff(
            original.splitlines(True), changed.splitlines(True),
            fromfile=SOURCES[-1], tofile=f"mutant-{name}/mapper.sv")), encoding="ascii")
        mutant = copy.copy(evidence)
        mutant.source_overrides = {**evidence.source_overrides,
                                   SOURCES[-1]: evidence.relative(source)}
        first = len(evidence.record["coverage"])
        failure = None
        try:
            mutant.simulate(f"cache-mutant-{name}", bench, SOURCES, len(labels))
        except Exception as error:
            failure = error
        rows = evidence.record["coverage"][first:]
        require(len(rows) == 1 and failure is not None, f"Cache mutant {name} survived")
        row = rows[0]
        compile_receipt = row.get("compile_receipt", {})
        result = row.get("simulation_receipt", {})
        require(compile_receipt.get("exit_code") == 0 and result.get("exit_code") not in
                (None, 0) and not result.get("timed_out") and result.get("child_settled")
                and result.get("process_group_settled"),
                f"Cache mutant {name} lacks a compiled bounded functional kill")
        output = ((root / result["stdout"]).read_text() +
                  (root / result["stderr"]).read_text())
        require("%Error:" in output and assertion in output,
                f"Cache mutant {name} missed required original assertion {assertion}")
        row.update(status="expected-functional-rejection", mutation_assertion=assertion)
        evidence.record.setdefault("descriptor_cache_mutations", []).append({
            "name": name, "assertion": assertion, "diff": evidence.relative(diff),
            "simulation_receipt": result,
        })
