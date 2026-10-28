"""Functional mutations in isolated copies; compiler failures/timeouts never kill."""

from dataclasses import replace
import shutil

from decoder_checks import decoder_case
from execution import ROOT, Run, sha256, write_json
from leaf_checks import codec_case, dot8_case
from parameters import A, B, legal
from scheduler_checks import scheduler_case
from prefetch_checks import prefetch_case
from tensor_checks import activation_case


MUTATIONS = (
    ("awq-nibble-permutation", "anvil_q3_00_pkg.sv",
     "3'd1: awq_lane_shift = 5'd16", "3'd1: awq_lane_shift = 5'd4", "decoder", A),
    ("zero-subtraction", "anvil_q3_awq_dot8.sv",
     "$signed({1'b0,q0[i]})-$signed({1'b0,z0[i]})",
     "$signed({1'b0,q0[i]})+$signed({1'b0,z0[i]})", "dot8", A),
    ("pipeline-valid-shift", "anvil_q3_awq_dot8.sv",
     "{valid_pipe[6:0],in_valid}", "{valid_pipe[5:0],in_valid,1'b0}", "dot8", A),
    ("reduction-lane", "anvil_q3_awq_dot8.sv",
     "$signed({product4[2*i+1][68],product4[2*i+1]})",
     "$signed({product4[2*i][68],product4[2*i]})", "dot8", A),
    ("ping-pong-premature-swap", "anvil_q3_weight_prefetcher.sv",
     "if (tile_state[head]==READY)", "if (tile_state[head]==FILLING)", "prefetch", A),
    ("reordered-response-association", "anvil_q3_bank_scheduler.sv",
     "rdata[response_slot[i]]<=mem_rsp_rdata[i*32+:32]",
     "rdata[response_slot[i]]<=mem_rsp_rdata[0+:32]", "scheduler", A),
    ("mode0-bit-corruption", "anvil_q3_cache_codec.sv",
     "if (decode) result_values<=payload_in", "if (decode) result_values<=payload_in ^ 1",
     "codec", A),
    ("int8-exponent", "anvil_q3_cache_codec.sv",
     "result_metadata<={24'd0,2'd0,exponent}",
     "result_metadata<={24'd0,2'd0,(exponent ^ 6'd1)}",
     "codec", replace(A, CACHE_MODE=1)),
    ("int4-signedness", "anvil_q3_cache_codec.sv",
     "$signed({{5{payload_lane[3]}},payload_lane[3:0]})",
     "$signed({5'b0,payload_lane[3:0]})", "codec", replace(A, CACHE_MODE=2)),
    ("int4-zero-code", "anvil_q3_cache_codec.sv",
     "encoded_round+{{30{zero_code[3]}},zero_code}", "encoded_round",
     "codec", replace(A, CACHE_MODE=2, INT4_ASYM=1)),
    ("gqa-head-mapping", "anvil_q3_gqa_attention.sv",
     "kv_head<=kv_head+1'b1", "kv_head<=0", "decoder",
     replace(A, HIDDEN_SIZE=32, NUM_Q_HEADS=16, NUM_KV_HEADS=2)),
    ("causal-position", "anvil_q3_gqa_attention.sv",
     "if (time_index<position) begin time_index<=time_index+1'b1; dimension<=0",
     "if (time_index<0) begin time_index<=time_index+1'b1; dimension<=0", "decoder", A),
    ("rope-theta-pair", "anvil_q3_rope.sv",
     "((pair_index<<1)+(state==SIN_READ ? 32'd1 : 32'd0))",
     "(state==SIN_READ ? 32'd1 : 32'd0)", "decoder", B),
    ("rms-epsilon", "anvil_q3_rmsnorm.sv",
     "128'sd18446744073710", "128'sd0", "decoder", A),
    ("omitted-residual", "anvil_q3_elementwise.sv",
     ".in_a({{96{a[31]}},a})", ".in_a(128'sd0)", "decoder", A),
    ("cancel-epoch", "anvil_q3_top.sv",
     "failed<=1; sequence_valid<=0; cancelled_active<=active_token",
     "failed<=1; sequence_valid<=1; cancelled_active<=active_token", "cancel", A),
    ("delayed-logit-completion", "anvil_q3_top.sv",
     "PROJECT_WAIT: if (last_logit)", "PROJECT_WAIT: if (io_done)", "completion", A),
    ("activation-write-lane", "anvil_q3_tensor_array.sv",
     "load_index[2:0]==a", "load_index[2:0]==((a+1)&7)",
     "activation", replace(A, BANKS=4, INTERMEDIATE_SIZE=120)),
    ("activation-read-word", "anvil_q3_tensor_array.sv",
     "activation_read_address=beat_input[g*32+:32]>>3",
     "activation_read_address=(beat_input[g*32+:32]>>3)^1",
     "activation", replace(A, BANKS=4, INTERMEDIATE_SIZE=120)),
    ("activation-stall-enable", "anvil_q3_tensor_array.sv",
     "if (activation_read && beat_mask[g*8+a])",
     "if (beat_valid[g] && beat_mask[g*8+a])",
     "activation", replace(A, BANKS=4, INTERMEDIATE_SIZE=120)),
)


def mutation_case(run, spec, simulator="verilator"):
    name, filename, before, after, kind, g = spec
    if not legal(g):
        raise AssertionError("illegal mutation geometry " + name)
    copied = run.path / (name + "-rtl")
    copied.mkdir()
    binding = {}
    for original in sorted((ROOT / "rtl").glob("*.sv")):
        target = copied / original.name
        shutil.copyfile(original, target)
        binding[original.name] = {"original_sha256": sha256(original)}
    target = copied / filename
    text = target.read_text()
    if text.count(before) != 1:
        raise AssertionError("mutation target is not unique/current: " + name)
    target.write_text(text.replace(before, after, 1))
    for source in copied.glob("*.sv"):
        binding[source.name]["copied_sha256"] = sha256(source)
    manifest = {"name": name, "file": filename, "before": before, "after": after,
                "sources": binding,
                "rope_mutation": "All pairs use pair-0 frequency, equivalent to theta=1" if
                name == "rope-theta-pair" else None}
    write_json(run.path / (name + "-mutation.json"), manifest)
    child = Run(run.rel(run.path / name), "isolated-functional-mutation:" + name)
    try:
        rtl = [run.rel(p) for p in sorted(copied.glob("*.sv"))]
        if kind == "dot8":
            selected = [p for p in rtl if p.endswith(("anvil_q3_00_pkg.sv", "anvil_q3_awq_dot8.sv"))]
            result = dot8_case(child, simulator, rtl=selected, must_fail=True)
        elif kind == "scheduler":
            selected = [p for p in rtl if p.endswith("anvil_q3_bank_scheduler.sv")]
            result = scheduler_case(child, simulator=simulator, rtl=selected, must_fail=True)
        elif kind == "prefetch":
            selected = [p for p in rtl if p.endswith(("anvil_q3_00_pkg.sv",
                                                     "anvil_q3_weight_prefetcher.sv"))]
            result = prefetch_case(child, simulator=simulator, rtl=selected, must_fail=True)
        elif kind == "codec":
            selected = [p for p in rtl if p.endswith("anvil_q3_cache_codec.sv")]
            result = codec_case(child, simulator, g.CACHE_MODE, g.INT4_ASYM,
                                rtl=selected, must_fail=True)
        elif kind == "activation":
            result = activation_case(child, g.BANKS, simulator,
                                     capacity=g.INTERMEDIATE_SIZE, rtl=rtl, must_fail=True)
        else:
            result = decoder_case(child, g, tokens=[1, 4], rtl=rtl, prelude=5 if kind == "cancel" else 0,
                                  simulator=simulator,
                                  mutation_assertions=(
                                      ("COMPLETION must follow final logit on the same edge",)
                                      if kind == "completion" else
                                      ("PROTOCOL", "TOKEN error", "XZ", "STABILITY",
                                       "COORDINATE", "UNINITIALIZED")))
        if result.get("functional_mutation_killed") is not True:
            raise AssertionError("no functional mutation kill")
    except Exception as exc:
        child.finish("failed", diagnosis=str(exc), mutation=manifest)
        raise
    child.finish("passed", result=result, mutation=manifest)
    return {"name": name, "killed": True, "receipt": child.rel(child.path / "receipt.json"),
            "result": result}


def mutations(run):
    run.versions([("verilator", "--version")])
    # Every distinct unmodified geometry/stimulus must pass before measuring sensitivity.
    baseline = []
    seen = set()
    for spec in MUTATIONS:
        g, kind = spec[-1], spec[-2]
        key = g, kind == "cancel"
        if kind in ("dot8", "scheduler", "prefetch", "activation") or key in seen:
            continue
        seen.add(key)
        baseline.append(decoder_case(run, g, tokens=[1, 4], prelude=5 if key[1] else 0,
                                     simulator="verilator",
                                     label="mutation-baseline-" + str(len(baseline))))
    baseline.append(dot8_case(run, "verilator"))
    baseline.append(scheduler_case(run, simulator="verilator"))
    baseline.append(prefetch_case(run, simulator="verilator"))
    for mode, asym in ((0, 0), (1, 0), (2, 0), (2, 1)):
        baseline.append(codec_case(run, "verilator", mode, asym))
    baseline.append(activation_case(run, banks=4, capacity=120, simulator="verilator"))
    write_json(run.path / "unmodified-baselines.json", baseline)
    results = []
    write_json(run.path / "required-mutations.json", [spec[0] for spec in MUTATIONS])
    failures = []
    for spec in MUTATIONS:
        try:
            results.append(mutation_case(run, spec))
        except Exception as exc:
            failures.append({"name": spec[0], "diagnosis": str(exc)})
        write_json(run.path / "mutation-results.json", {"kills": results, "failures": failures})
    if failures or {r["name"] for r in results} != {spec[0] for spec in MUTATIONS}:
        raise AssertionError("not every required mutation was killed by a functional assertion")
    return results
