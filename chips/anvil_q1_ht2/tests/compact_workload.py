#!/usr/bin/env python3
"""Compiled public-pin bridge integration; never official-model measurements."""

import argparse
import copy
import json
from pathlib import Path
import shutil
import sys
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent))

from benchmark_manifest import CASES, DEFAULT_GEOMETRY, MANIFEST_SHA256, sha256
from decoder_reference import Decoder, Geometry, Image
from evidence import ROOT, digest, execute, relative, require_success, write_json
import hardware_workload as bridge
import ieee_reference as fp
from integration_checks import TOP_PINS, MEMORY, CSR_TASK
from leaf_checks import HEADER


GEOMETRY = Geometry(sequence=12, window=3)
DECODE_MIN = 4
DECODE_MAX = DECODE_MIN + 3
REPAIR = "evidence/benchmark-contract-20261031T185427Z-38b6d4bd/receipt.json"


def link(path):
    return {"path": relative(path), "sha256": digest(path)}


def build(directory, mode):
    from integration_checks import fixture
    image, _, _ = fixture(directory, GEOMETRY, mode, 17)
    parameters = ",\n".join(f".{k}({v})" for k, v in GEOMETRY.parameters().items())
    memory = MEMORY.replace("MEMORY_WORDS", str(len(image.memory) // 64)).replace(
        "MEMORY_PATH", relative(directory / "memory.hex"))
    # Classify accepted response beats, not requested bursts.
    memory = memory.replace("if (avm_readdatavalid) reads=reads+1;", r"""
    if (avm_readdatavalid) begin
      reads=reads+1;
      for (category=0;category<DESCRIPTOR_COUNT;category=category+1)
        if (response_address>=descriptor_base[category] &&
            response_address<descriptor_end[category]) begin
          if (descriptor_kind[category]==1 && descriptor_projection[category]==6)
            down_reads=down_reads+1;
          if (descriptor_kind[category]==2 || descriptor_kind[category]==3)
            metadata_reads=metadata_reads+1;
        end
    end
""").replace("avm_readdatavalid=1; avm_readdata=memory[read_index];",
             "avm_readdatavalid=1; avm_readdata=memory[read_index]; response_address=read_index*64;")
    setup = r"""
  integer descriptor_base[0:DESCRIPTOR_COUNT-1],descriptor_end[0:DESCRIPTOR_COUNT-1];
  integer descriptor_kind[0:DESCRIPTOR_COUNT-1],descriptor_projection[0:DESCRIPTOR_COUNT-1];
  integer category,response_address=0,down_reads=0,metadata_reads=0;
  integer descriptor_index,kind,layer,projection,base,length,di=0;
  integer input_file,output_file,position=0,produced=0,steps=0;
  integer initial_token,candidate,limit,slot,draft_token,matched_drafts;
  integer start_reads,start_down,start_metadata;
  integer before_tokens,before_steps,before_baseline,before_avoided;
  integer after_tokens,after_steps,after_baseline,after_avoided;
  integer next_token,last_token,received,waited,accepted_count;
  reg [31:0] best_bits;
  reg [127:0] held_commit;
  reg [2:0] held_count;
  string input_path,output_path;
  integer total_clocks=0;
  always @(posedge clk) begin
    total_clocks=total_clocks+1;
    if (total_clocks>500000) $fatal(1,"BENCH_TOTAL_CYCLE_BOUND");
  end
  task ordinary(input integer value,input integer pos);
    begin
      @(negedge clk); token_id=value; token_pos=pos; token_valid=1; logit_ready=0;
      begin : accept
        forever begin @(posedge clk); if (token_ready===1) begin #1; disable accept; end end
      end
      @(negedge clk); token_valid=0; received=0; waited=0; next_token=0; best_bits=0;
      while (done!==1) begin
        logit_ready=waited%5!=1;
        @(posedge clk);
        if (logit_valid===1 && logit_ready) begin
          if (logit_index!==32'(received)) $fatal(1,"BENCH_LOGIT_ORDER");
          $fdisplay(output_file,"LOGIT %0d %0d %h",pos,received,logit_data);
          if (received==0 || $bitstoshortreal(logit_data)>$bitstoshortreal(best_bits)) begin
            best_bits=logit_data; next_token=received;
          end
          received=received+1; checked=checked+1;
        end
        #1; waited=waited+1; cycles=cycles+1;
        if (cycles>500000) $fatal(1,"CYCLE_BOUND");
        @(negedge clk);
      end
      if (error!==0 || received!=VOCAB) $fatal(1,"BENCH_ORDINARY");
      logit_ready=0; tick(); tick();
      $fflush(output_file);
    end
  endtask
  initial begin
    #1; reset_check();
    if (!$value$plusargs("INPUT=%s",input_path) || !$value$plusargs("OUTPUT=%s",output_path))
      $fatal(1,"BENCH_ARGUMENTS");
    input_file=$fopen(input_path,"r"); output_file=$fopen(output_path,"w");
    if (!input_file || !output_file) $fatal(1,"BENCH_FILE");
    rc=$fscanf(input_file,"%d %d %d\n",initial_token,candidate,limit);
    if (rc!=3 || limit!=DECODE_MIN) $fatal(1,"BENCH_INPUT");
    $fclose(input_file);
    repeat(4) tick(); @(negedge clk); rst_n=1; repeat(500) tick();
    $fdisplay(output_file,"START load_cold %0t",$time);
    csr(1,16'h100,MODE | (candidate ? 12 : 0),0,0,0);
    csr(1,16'h104,0,0,0,0);
    fd=$fopen("DESCRIPTORS","r");
    while (!$feof(fd)) begin
      rc=$fscanf(fd,"%h %h %h %h %h %h\n",descriptor_index,kind,layer,projection,base,length);
      if (rc!=6 || di>=DESCRIPTOR_COUNT) $fatal(1,"BENCH_DESCRIPTOR");
      descriptor_base[di]=base; descriptor_end[di]=base+length;
      descriptor_kind[di]=kind; descriptor_projection[di]=projection; di=di+1;
      csr(1,16'h10,descriptor_index,0,0,0);
      csr(1,16'h14,kind,0,0,0); csr(1,16'h18,layer,0,0,0);
      csr(1,16'h1c,projection,0,0,0); csr(1,16'h20,base,0,0,0);
      csr(1,16'h24,0,0,0,0); csr(1,16'h28,length,0,0,0);
      csr(1,16'h2c,1,0,0,0);
    end
    $fclose(fd);
    if (di!=DESCRIPTOR_COUNT) $fatal(1,"BENCH_DESCRIPTOR_COUNT");
    csr(1,16'h8,6,0,0,0); repeat(100) tick(); csr(0,16'h108,0,0,1,3);
    $fdisplay(output_file,"END load_cold %0t",$time);
    $fflush(output_file);
    $fdisplay(output_file,"START load_warm %0t",$time);
    csr(1,16'h8,4,0,0,0); repeat(100) tick(); csr(0,16'h108,0,0,1,3);
    $fdisplay(output_file,"END load_warm %0t",$time);
    $fflush(output_file);
    $fdisplay(output_file,"START prefill %0t",$time);
    ordinary(initial_token,0); last_token=initial_token;
    $fdisplay(output_file,"END prefill %0t",$time);
    csr(0,16'h110,0,0,0,0); before_tokens=response; csr(0,16'h114,0,0,1,0);
    csr(0,16'h118,0,0,0,0); before_steps=response; csr(0,16'h11c,0,0,1,0);
    csr(0,16'h128,0,0,0,0); before_baseline=response; csr(0,16'h12c,0,0,1,0);
    csr(0,16'h130,0,0,0,0); before_avoided=response; csr(0,16'h134,0,0,1,0);
    start_reads=reads; start_down=down_reads; start_metadata=metadata_reads;
    $fdisplay(output_file,"START decode %0t",$time);
    while (produced<limit) begin
      if (!candidate) begin
        position=position+1;
        $fdisplay(output_file,"TOKEN %0d",next_token);
        last_token=next_token; ordinary(next_token,position);
        produced=produced+1; steps=steps+1;
      end else begin
        draft_token=last_token;
        @(negedge clk); batch_valid=1; batch_count=4;
        batch_parents={3'd2,3'd1,3'd0,3'd4}; batch_token_ids={4{32'(last_token)}};
        begin : accept_batch
          forever begin @(posedge clk); if (batch_ready===1) begin #1; disable accept_batch; end end
        end
        @(negedge clk); batch_valid=0; commit_ready=0; waited=0; accepted_count=0;
        while (done!==1) begin
          @(posedge clk);
          if (logit_valid!==0) $fatal(1,"BENCH_BRANCH_LOGITS");
          if (commit_valid===1) begin
            if (commit_error!==0 || commit_position!==32'(position+1) ||
                commit_count<1 || commit_count>4) $fatal(1,"BENCH_COMMIT");
            if (waited!=0 && {commit_count,commit_token_ids}!=={held_count,held_commit})
              $fatal(1,"BENCH_STALL");
            held_count=commit_count; held_commit=commit_token_ids; waited=waited+1;
            if (commit_ready) begin
              accepted_count=commit_count;
              matched_drafts=0;
              for (slot=0;slot<commit_count;slot=slot+1) begin
                $fdisplay(output_file,"TOKEN %0d",commit_token_ids[32*slot+:32]);
                if (matched_drafts==slot && commit_token_ids[32*slot+:32]==32'(draft_token))
                  matched_drafts=matched_drafts+1;
                last_token=commit_token_ids[32*slot+:32];
              end
              $fdisplay(output_file,"COMMIT %0d %0d",commit_count,matched_drafts);
              checked=checked+1;
            end
          end
          #1; cycles=cycles+1; if (cycles>500000) $fatal(1,"CYCLE_BOUND");
          @(negedge clk); if (waited>=3) commit_ready=1;
        end
        if (error!==0 || accepted_count==0) $fatal(1,"BENCH_BATCH");
        commit_ready=0; produced=produced+accepted_count; position=position+accepted_count;
        steps=steps+1; tick(); tick();
      end
    end
    $fdisplay(output_file,"END decode %0t",$time);
    csr(0,16'h110,0,0,0,0); after_tokens=response; csr(0,16'h114,0,0,1,0);
    csr(0,16'h118,0,0,0,0); after_steps=response; csr(0,16'h11c,0,0,1,0);
    csr(0,16'h128,0,0,0,0); after_baseline=response; csr(0,16'h12c,0,0,1,0);
    csr(0,16'h130,0,0,0,0); after_avoided=response; csr(0,16'h134,0,0,1,0);
    csr(0,16'h120,0,0,1,reads*64); csr(0,16'h124,0,0,1,0);
    if (after_tokens-before_tokens!=produced || produced<limit || produced>limit+3)
      $fatal(1,"BENCH_COUNTERS");
    $fdisplay(output_file,"COUNTERS %0d %0d %0d %0d %0d %0d %0d %0d %0d",
              produced,steps,(reads-start_reads)*64,(down_reads-start_down)*64,
              (metadata_reads-start_metadata)*64,after_baseline-before_baseline,
              after_avoided-before_avoided,after_steps-before_steps,position);
    $fclose(output_file);
    $display("CHECK compared=%0d",checked); $finish;
  end
"""
    # Compare IEEE finite values without simulator real/shortreal conversion.
    setup = setup.replace("$bitstoshortreal(logit_data)>$bitstoshortreal(best_bits)",
                          "((logit_data[31]!=best_bits[31]) ? !logit_data[31] : "
                          "(logit_data[31] ? logit_data<best_bits : logit_data>best_bits))")
    for key, value in {
        "DESCRIPTOR_COUNT": str(len(image.descriptors)), "VOCAB": str(GEOMETRY.vocabulary),
        "MODE": str(mode), "DESCRIPTORS": relative(directory / "descriptors.txt"),
        "DECODE_MIN": str(DECODE_MIN),
    }.items():
        setup = setup.replace(key, value)
        memory = memory.replace(key, value)
    body = TOP_PINS.replace("PARAMETERS", parameters) + memory + CSR_TASK + setup
    tb = directory / "benchmark_tb.sv"
    tb.write_text(HEADER + body + "\nendmodule\n")
    obj = directory / "compile-obj"
    binary = directory / "simulation"
    sources = sorted((ROOT / "rtl").glob("anvil_q1_ht2_*.sv"))
    try:
        run = require_success(execute(
            ["verilator", "--binary", "--timing", "-Wno-fatal", "--top-module", "tb",
             "--Mdir", relative(obj), "-j", "2", "-o", "simulation",
             *map(relative, sources), relative(tb)], directory, "compile",
            timeout=1200, inputs=[tb, directory / "memory.hex", directory / "descriptors.txt"]))
        shutil.copyfile(obj / "simulation", binary)
        binary.chmod(0o755)
    finally:
        if obj.exists():
            shutil.rmtree(obj)
    return image, binary, run / "receipt.json"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", required=True)
    parser.add_argument("--response", required=True)
    parser.add_argument("--build", required=True)
    args = parser.parse_args()
    req = bridge.load_json(bridge.project_path(args.request))
    build_dir = bridge.project_path(args.build)
    directory = bridge.project_path(args.response).parent
    if not req["integration_only"] or req["geometry"] != {
        **DEFAULT_GEOMETRY, **GEOMETRY.parameters()
    } or req["sparse_threshold"] != 0:
        raise ValueError("compact-only bridge fixture/threshold mismatch")
    initial = req["input_ids"][0]
    data = directory / "stimulus.txt"
    data.write_text(f"{initial} {int(req['job_type'] == 'ht2_speculative_sparse')} {DECODE_MIN}\n")
    raw = directory / "observations.txt"
    run = require_success(execute(
        [relative(build_dir / "simulation"), f"+INPUT={relative(data)}", f"+OUTPUT={relative(raw)}"],
        directory, "compiled-execution", timeout=600, inputs=[
            data, build_dir / "benchmark_tb.sv", build_dir / "memory.hex",
            build_dir / "descriptors.txt", build_dir / "simulation"]))
    timings, output, observed, counts, commits = {}, [], [], None, []
    for line in raw.read_text().splitlines():
        words = line.split()
        if words[0] in ("START", "END"):
            stage = timings.setdefault(words[1], {})
            # %t with 1ps precision; convert to integer simulated nanoseconds.
            stage["start_monotonic_ns" if words[0] == "START" else "end_monotonic_ns"] = int(words[2]) // 1000
        elif words[0] == "TOKEN":
            output.append(int(words[1]))
        elif words[0] == "LOGIT":
            observed.append([int(words[1]), int(words[2]), int(words[3], 16)])
        elif words[0] == "COMMIT":
            commits.append((int(words[1]), int(words[2])))
        elif words[0] == "COUNTERS":
            if counts is not None:
                raise ValueError("duplicate counter record")
            counts = list(map(int, words[1:]))
    for timing in timings.values():
        timing["elapsed_ns"] = timing["end_monotonic_ns"] - timing["start_monotonic_ns"]
    if counts is None or len(counts) != 9:
        raise ValueError("missing executed counter snapshot")
    tokens, steps, physical, down, metadata, baseline, avoided, batch_steps, position = counts
    per_traversal = GEOMETRY.layers * GEOMETRY.intermediate * (64 if req["mode"] == "w4" else 128)
    if baseline % per_traversal or batch_steps != len(commits):
        raise ValueError("nonintegral traversal/counter contradiction")
    response = {key: req[key] for key in bridge.IDENTITY_FIELDS}
    response.update(
        request_sha256=sha256(req), integration_only=True, execution_kind="compiled_rtl",
        status="completed", software_versions={"verilator": bridge.load_json(
            run / "receipt.json")["tool_version"], "timing": "RTL 10ns testbench clock, not physical STA"},
        provenance=[link(run / "receipt.json"), link(build_dir / "compile-receipt.json")],
        timings=timings, measured_clock_hz=100000000,
        output_token_ids=output, eos_reason="integration_boundary",
        counters=dict(cycles=timings["decode"]["elapsed_ns"] // 10,
                      committed_tokens=tokens, completed_steps=steps, physical_read_bytes=physical,
                      down_projection_baseline_bytes=baseline, down_projection_actual_bytes=down,
                      metadata_bytes=metadata, replay_bytes=0, replay_count=0, replay_cycles=0,
                      corrections=sum(n != matches for n, matches in commits),
                      rejections=sum(4 - matches for _, matches in commits),
                      avoided_down_projection_bytes=avoided,
                      charged_weight_traversals=baseline // per_traversal),
        raw_observations=link(raw), observed_logits=observed,
        raw_counter_snapshot=counts,
        integration_scope="seeded compact tensors, hash-mapped compact prompt IDs; exact-zero sparsity; "
                          "simulated time only; not official tokenizer/model/performance")
    bridge.validate_response(response, req, full=False)
    write_json(bridge.project_path(args.response), response)


def contract(directory, cases=CASES, modes=(("bf16", 0), ("w4", 2))):
    import checkpoint_images
    checks, rejected = [checkpoint_images.selfcheck(directory)], []
    write_json(directory / "repair.json", {"repair_of": REPAIR, "integration_only": True})
    for mode_name, mode in modes:
        build_dir = directory / f"build-{mode_name}-{uuid.uuid4().hex[:8]}"
        build_dir.mkdir()
        image, binary, receipt = build(build_dir, mode)
        # Preserve the compiler receipt's own relative raw-log references.
        compiler = bridge.load_json(receipt)
        compiler["stdout"] = str(receipt.parent.relative_to(build_dir) / compiler["stdout"])
        compiler["stderr"] = str(receipt.parent.relative_to(build_dir) / compiler["stderr"])
        write_json(build_dir / "compile-receipt.json", compiler)
        document = {
            "model": {"revision": "compact-seeded-17", "tensors": [link(build_dir / "memory.hex")],
                      "config": {"sha256": sha256(GEOMETRY.parameters())},
                      "tokenizer": {"kind": "integration-hash-mapping-not-official"}},
            "images": {mode_name: link(build_dir / "memory.hex")},
            "tokenized_cases": {
                case["id"]: {"ids": [int(sha256(case["prompt"])[:8], 16) % GEOMETRY.vocabulary],
                             "sha256": sha256([int(sha256(case["prompt"])[:8], 16) % GEOMETRY.vocabulary])}
                for case in CASES},
            "eos_token_ids": [GEOMETRY.vocabulary - 1],
        }
        for case in cases:
            pair = {}
            for job in ("dense_reference", "ht2_speculative_sparse"):
                work = directory / f"{mode_name}-{case['id']}-{job}-{uuid.uuid4().hex[:8]}"
                work.mkdir()
                req = bridge.request(document, case, mode_name, job, integration_only=True,
                                     geometry={**DEFAULT_GEOMETRY, **GEOMETRY.parameters()})
                req["sparse_threshold"] = 0
                req["integration_decode_min"] = DECODE_MIN
                req["decode_limit"] = DECODE_MAX
                # This compact fixture has no EOS. Stop only at an atomic commit boundary.
                req["eos_token_ids"] = []
                response, record = bridge.launch(
                    ["python3", "tests/compact_workload.py", "--build", relative(build_dir)],
                    req, work, full=False)
                verify_native(image, req, response)
                pair[job] = response
                checks.append({"name": f"{mode_name}/{case['id']}/{job}", **record,
                               "integration_only": True, "tokens": len(response["output_token_ids"])})
                if not rejected:
                    rejected = negative_cases(req, response)
            if pair["dense_reference"]["output_token_ids"] != pair["ht2_speculative_sparse"]["output_token_ids"][:DECODE_MIN]:
                raise AssertionError("compact dense/speculative sequence mismatch")
    write_json(directory / "contract.json", {
        "integration_only": True, "workload_manifest_sha256": MANIFEST_SHA256,
        "executions": checks, "negative_cases": rejected, "repair_of": REPAIR})
    return checks


def verify_native(image, req, response):
    native = Decoder(image)
    prefix, expected_logits, expected_tokens = [], {}, []
    token = req["input_ids"][0]
    for position in range(len(response["output_token_ids"]) + 1):
        logits, target, state = native.token(token, position, prefix)
        expected_logits[position] = logits
        prefix.append(state)
        if position:
            expected_tokens.append(token)
        token = target
    if response["output_token_ids"] != expected_tokens:
        raise AssertionError("executed compact greedy sequence differs from independent decoder")
    if not response["observed_logits"]:
        raise AssertionError("no public logit comparisons")
    for position, index, value in response["observed_logits"]:
        if value != expected_logits[position][index]:
            raise AssertionError(f"compact logit mismatch at {position}/{index}")


def negative_cases(req, response):
    defects = {
        "identity": lambda value: value.update(run_nonce="stale"),
        "request-hash": lambda value: value.update(request_sha256="0" * 64),
        "provenance": lambda value: value.update(provenance=[]),
        "provenance-hash": lambda value: value["provenance"][0].update(sha256="0" * 64),
        "truncation": lambda value: (
            value["output_token_ids"].pop(),
            value["counters"].update(committed_tokens=len(value["output_token_ids"]))),
        "contradictory-counters": lambda value: value["counters"].update(
            down_projection_actual_bytes=value["counters"]["physical_read_bytes"] + 64),
        "timing": lambda value: value["timings"]["decode"].update(elapsed_ns=1),
    }
    rejected = []
    for name, inject in defects.items():
        bad = copy.deepcopy(response)
        inject(bad)
        try:
            bridge.validate_response(bad, req, full=False)
        except ValueError as exc:
            rejected.append({"case": name, "diagnostic": str(exc)})
        else:
            raise AssertionError(f"adapter defect escaped: {name}")
    try:
        bridge.validate_response(response, req, full=True)
    except ValueError as exc:
        if "rejects simulated" not in str(exc):
            raise
        rejected.append({"case": "integration-as-full-model", "diagnostic": str(exc)})
    else:
        raise AssertionError("compact execution qualified as physical full-model evidence")
    return rejected


if __name__ == "__main__":
    main()
