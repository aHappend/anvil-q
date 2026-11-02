"""Complete-inference and dense differential benchmark recipes.

Frozen domain fixtures: math, coding, science, symbolic-logic, mixed-reasoning;
each uses seed 17+domain, H=16, vocabulary=8, two four-token sequences
[6,2,3,7], one prefill then three decode commands, identical finite bank
acceptance/response and logit stall schedules. Architectural differences are
reported explicitly: dense FP16/AWQ GQA versus native Q16 MLA plus MoE. Counts
include every accepted public transaction; no unrequested speedup or accuracy
threshold is imposed. These fixtures are frozen before any simulator launch.
"""

import json
from pathlib import Path
import re
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

from diagnostic import NATIVE_BENCH, hexfile, packed_key
from evidence import check_deadline
from legacy import LegacyFixture
from reference import Fixture, Shape


DOMAINS = ("math", "coding", "science", "symbolic-logic", "mixed-reasoning")
PORT_WIDTHS = dict(token_ready="1", logit_valid="1", logit_index="32",
                   logit_data="32", done="1", error="1", cancel_done="1",
                   mem_req_valid="B", mem_req_write="B", mem_req_kind="B*4",
                   mem_req_layer="B*32", mem_req_proj="B*3", mem_req_row="B*32",
                   mem_req_col="B*32", mem_req_wdata="B*32", mem_req_tag="B*64",
                   mem_rsp_ready="B")


def images(evidence, fixture, expected_logits):
    keys = sorted(set(fixture.initial) | set(fixture.writes))
    starts, counts, expected = [], [], []
    for key in keys:
        starts.append(len(expected))
        counts.append(len(fixture.writes[key]))
        expected.extend(fixture.writes[key])
    directory = evidence.path / "checkpoint-images"
    directory.mkdir()
    for name, values, digits in (
        ("keys", [packed_key(k) for k in keys], 26),
        ("memory", [fixture.initial.get(k, 0) & 0xffffffff for k in keys], 8),
        ("initialized", [int(k in fixture.initial) for k in keys], 1),
        ("starts", starts, 8), ("counts", counts, 8), ("expected-writes", expected, 8),
        ("logits", [v & 0xffffffff for seq in expected_logits for v in seq], 8)):
        hexfile(directory / (name+".hex"), values, digits)
    return len(keys), len(expected)


def mirror(bench, instance):
    declarations = "\n".join(f"wire [{width}-1:0] reference_{name};"
                             for name, width in PORT_WIDTHS.items())
    reference = instance.replace("anvil_d1_top", "anvil_q3_top").replace(" device (", " parent_device (")
    reference = reference.replace(".MODEL_MODE(1),", "")
    reference = re.sub(r",?\s*\.csr_\w+\([^)]*\)", "", reference)
    for name in PORT_WIDTHS:
        reference = reference.replace(f".{name}({name})", f".{name}(reference_{name})")
    pairs = ["{"+",".join(PORT_WIDTHS)+"}",
             "{"+",".join("reference_"+name for name in PORT_WIDTHS)+"}"]
    comparisons = f"""
  integer differential_edges=0;
  task automatic compare_parent;
    begin
      if ({pairs[0]} !== {pairs[1]})
        $fatal(1,"LEGACY_PUBLIC_PIN_MISMATCH t=%0t",$time);
      differential_edges=differential_edges+1;
    end
  endtask
  always @(posedge clk or negedge clk) begin
    compare_parent();
    #1; compare_parent();
  end
"""
    return bench.replace(instance, instance+"\n"+declarations+"\n"+reference+comparisons)


def inference_bench(evidence, seed=17, tokens=4, sequences=1, shape=Shape(),
                    banks=2, queue=3, tile_rows=3, legacy=None, domain=None):
    check_deadline()
    fixture = Fixture(shape, seed) if legacy is None else LegacyFixture(
        seed=seed, profile=legacy[0], mode=legacy[1], asymmetric=legacy[2])
    ids = ([6, 2, 3, 7] if domain is not None else
           [(i+2) % (shape.vocab if legacy is None else fixture.vocab) for i in range(tokens)])
    expected_logits = []
    for sequence in range(sequences):
        if legacy is None:
            fixture.absorbed.clear()
        fixture.cache.clear()
        for pos, token in enumerate(ids):
            expected_logits.append(fixture.token(token, pos))
    slots, writes = images(evidence, fixture, expected_logits)
    count = tokens*sequences
    bench = NATIVE_BENCH.replace("@SLOTS@", str(slots)).replace("@WRITES@", str(writes))
    bench = bench.replace("@TOKENS@", str(count)).replace("@CYCLES@", "10000000")
    bench = bench.replace("localparam B=2,", f"localparam B={banks},")
    start, end = bench.index("  anvil_d1_top #("), bench.index("\n  reg [102:0] keys")
    instance = bench[start:end]
    parameters = (dict(NUM_LAYERS=shape.layers, HIDDEN_SIZE=shape.hidden,
                       INTERMEDIATE_SIZE=shape.intermediate, NUM_Q_HEADS=shape.heads,
                       KV_LORA_RANK=shape.rank, QK_NOPE_HEAD_DIM=shape.nope,
                       QK_ROPE_HEAD_DIM=shape.rope, V_HEAD_DIM=shape.value,
                       ROUTED_EXPERTS=shape.experts, TOP_K=shape.topk,
                       SHARED_EXPERTS=2, MOE_INTERMEDIATE_SIZE=shape.moe_intermediate,
                       FIRST_DENSE_LAYERS=shape.first_dense, VOCAB_SIZE=shape.vocab,
                       MAX_SEQ_LEN=shape.maxseq, BANKS="B", QUEUE_DEPTH=queue,
                       TILE_K=8, TILE_ROWS=tile_rows) if legacy is None else
                  dict(MODEL_MODE=1, PROFILE=fixture.profile, NUM_LAYERS=1,
                       HIDDEN_SIZE=16, INTERMEDIATE_SIZE=16, NUM_Q_HEADS=fixture.heads,
                       NUM_KV_HEADS=1, HEAD_DIM=fixture.dim, GROUP_SIZE=8,
                       AWQ_BITS=4, VOCAB_SIZE=8, MAX_SEQ_LEN=5,
                       CACHE_MODE=fixture.mode, CACHE_BLOCK=2,
                       INT4_ASYM=fixture.asymmetric, BANKS="B", QUEUE_DEPTH=queue,
                       TILE_K=8, TILE_ROWS=tile_rows))
    bindings = instance[instance.index("  ) device (")+len("  )"):]
    instance = "  anvil_d1_top #("+",".join(f".{k}({v})" for k, v in parameters.items())+"\n  )"+bindings
    bench = bench[:start]+instance+bench[end:]
    if legacy is not None:
        bench = mirror(bench, instance)
    vocab = shape.vocab if legacy is None else fixture.vocab
    for old, new in (("TOKENS*8", f"TOKENS*{vocab}"), ("(completed+1)*8", f"(completed+1)*{vocab}"),
                     ("compared_logits%8", f"compared_logits%{vocab}"),
                     ("logit_index==7", f"logit_index=={vocab-1}")):
        bench = bench.replace(old, new)
    # Use a case statement instead of simulator-specific unpacked array literals.
    token_selection = "case(position%"+str(tokens)+")\n"+ "\n".join(
        f"{pos}: token_id={token};" for pos, token in enumerate(ids))+"\nendcase"
    bench = bench.replace("token_id=(position+2)%8; token_pos=position;",
                          token_selection+f"; token_pos=position%{tokens};")
    bench = bench.replace("new_sequence=position==0; token_phase=position!=0;",
                          f"new_sequence=position%{tokens}==0; token_phase=position%{tokens}!=0;")
    bench = bench.replace("  integer logit_delay=0;", (
        "  integer logit_delay=0;\n"
        "  reg [63:0] read_bytes=0,write_bytes=0,expert_bytes_observed=0;\n"))
    bench = bench.replace("writes=writes+1;", "writes=writes+1; write_bytes=write_bytes+4;")
    bench = bench.replace("reads=reads+1;", """reads=reads+1; read_bytes=read_bytes+4;
            if (mem_req_kind[b*4+:4]==15 && mem_req_proj[b*3+:3]==5)
              expert_bytes_observed=expert_bytes_observed+4;""")
    if domain is not None:
        bench = benchmark_csr(bench, domain, count)
    bench = bench.replace('    $finish;', """    $display("METRICS read_bytes=%0d write_bytes=%0d expert_bytes=%0d",
      read_bytes,write_bytes,expert_bytes_observed);
    $finish;""")
    (evidence.path / "native.sv").write_text(bench)
    frozen = dict(seed=seed, parameters=parameters, tokens=ids, sequences=sequences,
                  expected_logits=expected_logits, expected_write_comparisons=writes,
                  domain=None if domain is None else DOMAINS[domain],
                  architecture="native fixed-point MLA/MoE" if legacy is None else "dense FP16/AWQ GQA",
                  numerical_model="reference.py" if legacy is None else "legacy.py",
                  service_schedule="bank ready (cycles+bank)%7!=0; response (cycles+bank*3)%5; four logit stall cycles")
    (evidence.path / "fixture.json").write_text(json.dumps(frozen, indent=2)+"\n")
    return frozen


def benchmark_csr(bench, domain, count):
    for name, value in (("valid", "1'b0"), ("write", "1'b0"), ("addr", "12'd0"),
                        ("wdata", "32'd0"), ("wstrb", "4'd0"), ("rsp_ready", "1'b1")):
        bench = bench.replace(f".csr_{name}({value})", f".csr_{name}(test_csr_{name})")
    declarations = r"""
  reg test_csr_valid=0,test_csr_write=0,test_csr_rsp_ready=1;
  reg [11:0] test_csr_addr=0;
  reg [31:0] test_csr_wdata=0;
  reg [3:0] test_csr_wstrb=15;
  integer csr_comparisons=0;
  task automatic access_csr(input integer address,input bit write_access,
                            input [31:0] data,input [31:0] expected_data);
    begin
      @(negedge clk); while (!csr_ready) @(negedge clk);
      test_csr_valid=1; test_csr_write=write_access;
      test_csr_addr=address; test_csr_wdata=data;
      @(posedge clk); #1;
      if (csr_rsp_valid!==1 || csr_error!==0 ||
          csr_rdata!==(write_access ? 32'd0 : expected_data))
        $fatal(1,"INTEGRATED_CSR_MISMATCH addr=%h actual=%h expected=%h",
          address,csr_rdata,expected_data);
      csr_comparisons=csr_comparisons+1;
      @(negedge clk); test_csr_valid=0; @(posedge clk); #1;
    end
  endtask
"""
    bench = bench.replace("  reg [102:0] keys", declarations+"\n  reg [102:0] keys")
    bench = bench.replace("    for (position=0;", (
        f"    access_csr(16,1,{domain},0);\n"
        "    access_csr(8,1,1,0);\n"
        "    for (position=0;"), 1)
    final = f"""
    access_csr(8,1,2,0);
    access_csr('h48,0,0,{count}); access_csr('h4c,0,0,0);
    access_csr('h50,0,0,0);
    access_csr('h58,0,0,{count*3//4});
    access_csr('h80,0,0,expert_bytes_observed[31:0]);
    access_csr('h84,0,0,expert_bytes_observed[63:32]);
    access_csr('h{0x108+domain*0x40:x},0,0,{count});
    access_csr('h{0x110+domain*0x40:x},0,0,{count*3//4});
    access_csr('h{0x118+domain*0x40:x},0,0,read_bytes[31:0]);
    access_csr('h{0x120+domain*0x40:x},0,0,write_bytes[31:0]);
    access_csr('h{0x128+domain*0x40:x},0,0,expert_bytes_observed[31:0]);
    $display("CSR_METRICS domain={domain} tokens={count} reasoning_tokens={count*3//4} comparisons=%0d",csr_comparisons);
"""
    return bench.replace('    $display("SUMMARY ', final+'    $display("SUMMARY ', 1)


def main():
    import argparse
    from diagnostic import simulate
    from evidence import Evidence, rel
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", type=int, choices=(1, 2, 3))
    parser.add_argument("--cache-mode", type=int, default=0)
    parser.add_argument("--asymmetric", type=int, default=0)
    parser.add_argument("--tokens", type=int, default=1)
    parser.add_argument("--domain", type=int, choices=range(5))
    parser.add_argument("--repair-of")
    args = parser.parse_args()
    evidence = Evidence("inference-recipe", args.repair_of)
    try:
        frozen = inference_bench(evidence, tokens=4 if args.domain is not None else args.tokens,
                                 sequences=2 if args.domain is not None else 1,
                                 legacy=None if args.profile is None else
                                 (args.profile, args.cache_mode, args.asymmetric),
                                 domain=args.domain)
        observations = simulate(evidence, "native.sv", "verilator")
        evidence.finish("passed", fixture=frozen, observations=observations)
        print(observations.strip())
    except Exception as exc:
        evidence.finish("failed", error=str(exc))
        print(str(exc))
        print(rel(evidence.path/"receipt.json"))
        return 1
    print(rel(evidence.path/"receipt.json"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
