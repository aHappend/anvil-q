"""Functional mutations in isolated copies; compiler failures/timeouts never kill."""

from dataclasses import replace
import shutil

from decoder_checks import decoder_case
from execution import ROOT, Run, sha256, write_json
from leaf_checks import codec_case, dot8_case
from parameters import A, legal
from scheduler_checks import scheduler_case
from prefetch_checks import prefetch_case
from tensor_checks import activation_case


MUTATIONS = (
    ("awq-nibble-permutation", "anvil_q3_00_pkg.sv",
     "3'd1: awq_lane_shift = 5'd16;", "3'd1: awq_lane_shift = 5'd4;",
     "prefetch", A),
    ("zero-subtraction", "anvil_q3_awq_dot8.sv",
     "$signed({1'b0,q0[i]})-$signed({1'b0,z0[i]})",
     "$signed({1'b0,q0[i]})+$signed({1'b0,z0[i]})", "dot8", A),
    ("pipeline-valid-shift", "anvil_q3_awq_dot8.sv",
     "{valid_pipe[6:0],in_valid}", "{valid_pipe[5:0],in_valid,1'b0}", "dot8", A),
    ("reduction-lane", "anvil_q3_awq_dot8.sv",
     "product4[2*i+1][68],product4[2*i+1]", "product4[2*i][68],product4[2*i]",
     "dot8", A),
    ("ping-pong-premature-swap", "anvil_q3_weight_prefetcher.sv",
     "if (tile_state[head]==READY)", "if (tile_state[head]==FILLING)", "prefetch", A),
    ("reordered-response-association", "anvil_q3_bank_scheduler.sv",
     "rdata[s]<=mem_rsp_rdata[BANK*32+:32]",
     "rdata[s]<=mem_rsp_rdata[0+:32]", "scheduler", A),
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
     "zero_code<=metadata_in[11:8];", "zero_code<=0;",
     "codec", replace(A, CACHE_MODE=2, INT4_ASYM=1)),
    ("gqa-head-mapping", "anvil_q3_gqa_attention.sv",
     "kv_head<=kv_head+1'b1;", "kv_head<=0;",
     "decoder", replace(A, HIDDEN_SIZE=64, NUM_Q_HEADS=16, NUM_KV_HEADS=2, HEAD_DIM=4)),
    ("causal-position", "anvil_q3_gqa_attention.sv",
     "if (time_index<position) begin time_index<=time_index+1'b1; dimension<=0; state<=Q_READ; end",
     "if (time_index+1<position) begin time_index<=time_index+1'b1; dimension<=0; state<=Q_READ; end",
     "decoder", A),
    ("rope-theta-pair", "anvil_q3_rope.sv",
     "((pair_index<<1)+(state==SIN_READ ? 32'd1 : 32'd0))",
     "((32'd0)+(state==SIN_READ ? 32'd1 : 32'd0))",
     "decoder", replace(A, HIDDEN_SIZE=32, HEAD_DIM=4)),
    ("rms-epsilon", "anvil_q3_rmsnorm.sv",
     ".in_b(128'sd18446744073710)", ".in_b(128'sd184467440737100000)",
     "decoder", A),
    ("omitted-ffn", "anvil_q3_elementwise.sv",
     "arithmetic_result<={{64{product[63]}},product};",
     "arithmetic_result<=0;", "decoder", A),
    ("omitted-residual", "anvil_q3_elementwise.sv",
     ".in_a({{96{a[31]}},a})", ".in_a(128'sd0)", "decoder", A),
    ("cancel-epoch-handling", "anvil_q3_bank_scheduler.sv",
     "else if (stage[s]==SENT || issuing[s]) stage[s]<=SENT;",
     "else if (!flush && (stage[s]==SENT || issuing[s])) stage[s]<=SENT;",
     "scheduler", A),
)

# Requirement categories are deliberately independent of the executable inventory.
REQUIRED_CATEGORIES = {
    "AWQ nibble permutation": {"awq-nibble-permutation"},
    "zero subtraction": {"zero-subtraction"},
    "pipeline register/valid shift": {"pipeline-valid-shift"},
    "reduction lane": {"reduction-lane"},
    "ping-pong premature swap": {"ping-pong-premature-swap"},
    "stale/reordered response association": {"reordered-response-association"},
    "Mode0 bit corruption": {"mode0-bit-corruption"},
    "INT8 exponent": {"int8-exponent"},
    "INT4 signedness/zero-code": {"int4-signedness", "int4-zero-code"},
    "GQA head mapping": {"gqa-head-mapping"},
    "causal masking/position": {"causal-position"},
    "RoPE theta": {"rope-theta-pair"},
    "RMS epsilon": {"rms-epsilon"},
    "omitted FFN or residual": {"omitted-ffn", "omitted-residual"},
    "cancel epoch handling": {"cancel-epoch-handling"},
}
FAILED_RECEIPT = "evidence/check-mutations/20261031T230012Z-cb40820a0ba9/receipt.json"


def assert_required_coverage(names):
    observed = set(names)
    missing = {category: sorted(required - observed)
               for category, required in REQUIRED_CATEGORIES.items()
               if not required <= observed}
    if missing:
        raise AssertionError("missing mandatory functional mutation categories: " + str(missing))


def control_case(run, spec, simulator="verilator"):
    kind, g = spec[-2:]
    if kind == "dot8":
        return dot8_case(run, simulator)
    if kind == "scheduler":
        return scheduler_case(run, simulator=simulator)
    if kind == "prefetch":
        return prefetch_case(run, simulator=simulator)
    if kind == "codec":
        return codec_case(run, simulator, g.CACHE_MODE, g.INT4_ASYM)
    if kind == "activation":
        return activation_case(run, g.BANKS, simulator, capacity=g.INTERMEDIATE_SIZE)
    return decoder_case(run, g, tokens=[1, 4], simulator=simulator,
                        prelude=5 if kind == "cancel" else 0)


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
    child = Run(run.rel(run.path / name), "isolated-functional-mutation:" + name,
                repair_of=FAILED_RECEIPT)
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
    assert_required_coverage([spec[0] for spec in MUTATIONS])
    if len({spec[0] for spec in MUTATIONS}) != len(MUTATIONS):
        raise AssertionError("duplicate mutation names")
    run.versions([("verilator", "--version")])
    # Every distinct unmodified geometry/stimulus must pass before measuring sensitivity.
    baseline = []
    seen = set()
    for spec in MUTATIONS:
        g, kind = spec[-1], spec[-2]
        key = kind, g
        if key in seen:
            continue
        seen.add(key)
        baseline.append(control_case(run, spec))
    write_json(run.path / "unmodified-baselines.json", baseline)
    results = []
    write_json(run.path / "required-mutations.json",
               {category: sorted(names) for category, names in REQUIRED_CATEGORIES.items()})
    failures = []
    for spec in MUTATIONS:
        try:
            results.append(mutation_case(run, spec))
        except Exception as exc:
            failures.append({"name": spec[0], "diagnosis": str(exc)})
        write_json(run.path / "mutation-results.json", {"kills": results, "failures": failures})
    if failures or {r["name"] for r in results} != {spec[0] for spec in MUTATIONS}:
        raise AssertionError("not every required mutation was killed by a functional assertion")
    assert_required_coverage([r["name"] for r in results])
    return results
