"""Independent native-operation and FP64 references for public vector operators."""

from fractions import Fraction
import math
import random

from evidence import relative, write_json
import ieee_reference as ref
from leaf_checks import SEEDS, emit_rows, packed, simulate


def norm_reference(values, gamma, fp16):
    fmt = ref.FP16 if fp16 else ref.BF16
    norm = 0
    for x in values:
        norm = ref.add(norm, ref.multiply(x, x))
    mean = ref.divide(norm, ref.rounded(len(values)))
    root = ref.sqrt(ref.add(mean, ref.rounded(Fraction(1, 1000000))))
    inverse = ref.divide(ref.rounded(1), root)
    return [ref.multiply(ref.multiply(x, inverse), ref.convert(g, fmt, ref.FP32))
            for x, g in zip(values, gamma)]


def norm_fp64(values, gamma, fp16):
    fmt = ref.FP16 if fp16 else ref.BF16
    xs = [float(ref.value(x)) for x in values]
    inv = 1 / math.sqrt(math.fsum(x * x for x in xs) / len(xs) + 1e-6)
    return [x * inv * float(ref.value(g, fmt)) for x, g in zip(xs, gamma)]


def swiglu_reference(gate, up, fp16):
    fmt = ref.FP16 if fp16 else ref.BF16
    one = ref.rounded(1)
    positive = not (gate & ref.FP32.sign) or ref.kind(gate) == "zero"
    e = ref.exp32(gate ^ ref.FP32.sign if positive else gate)
    sigmoid = ref.divide(one if positive else e, ref.add(one, e))
    result = ref.multiply(ref.multiply(gate, sigmoid), up)
    encoded = ref.convert(result, ref.FP32, fmt)
    return result, encoded, bool(result & 0x7FFFFFFF)


def swiglu_fp64(gate, up):
    g, u = float(ref.value(gate)), float(ref.value(up))
    if g >= 0:
        sigmoid = 1 / (1 + math.exp(-g))
    else:
        e = math.exp(g)
        sigmoid = e / (1 + e)
    return g * sigmoid * u


def operator_fixture(kind, words):
    records, fidelity_records = [], []
    for seed in SEEDS:
        rng = random.Random(seed)
        for fp16 in (0, 1):
            fmt = ref.FP16 if fp16 else ref.BF16
            for slots in (15, 5):
                values = [[ref.rounded(Fraction(rng.randrange(-128, 129), 32))
                           for _ in range(words)] for _ in range(4)]
                other = [[ref.rounded(Fraction(rng.randrange(-128, 129), 64))
                          for _ in range(words)] for _ in range(4)]
                # Exercise signed zero and strongly negative/positive sigmoid.
                for slot in range(4):
                    values[slot][0] = ref.rounded(0, negative_zero=bool(slot & 1))
                if kind == "swiglu":
                    values[0][1] = ref.rounded(-104)
                    values[1][1] = ref.rounded(89)
                gamma = [ref.rounded(Fraction(rng.randrange(32, 97), 64), fmt)
                         for _ in range(words)]
                expected = [[0] * words for _ in range(4)]
                exact = [[0.0] * words for _ in range(4)]
                encoded = [[0] * words for _ in range(4)]
                original_nonzero = [[False] * words for _ in range(4)]
                for slot in range(4):
                    if not slots >> slot & 1:
                        continue
                    if kind == "rmsnorm":
                        expected[slot] = norm_reference(values[slot], gamma, fp16)
                        exact[slot] = norm_fp64(values[slot], gamma, fp16)
                    else:
                        for i in range(words):
                            result, activation, nz = swiglu_reference(values[slot][i], other[slot][i], fp16)
                            expected[slot][i] = result
                            encoded[slot][i] = activation
                            original_nonzero[slot][i] = nz
                            exact[slot][i] = swiglu_fp64(values[slot][i], other[slot][i])
                    metrics = ref.fidelity([ref.as_float(x) for x in expected[slot]], exact[slot])
                    if metrics["nrmse"] > .02 or metrics["cosine"] < .999:
                        raise AssertionError(f"operator operational reference fidelity {kind}: {metrics}")
                    fidelity_records.append({"operator": kind, "seed": seed, "fp16": bool(fp16),
                                             "slot": slot, "words": words, **metrics})
                for i in range(words):
                    records.append((fp16, slots, packed([v[i] for v in values], 32),
                                    gamma[i] if kind == "rmsnorm" else packed([v[i] for v in other], 32),
                                    packed([v[i] for v in expected], 32),
                                    packed([v[i] for v in encoded], 16),
                                    packed([v[i] for v in original_nonzero], 1)))
    return records, fidelity_records


def vectors(directory, kind, simulator="verilator", words=8):
    vector_path = directory / (kind + "-vectors.txt")
    rows, reference_fidelity = operator_fixture(kind, words)
    count = emit_rows(vector_path, rows)
    write_json(directory / (kind + "-reference-fidelity.json"), reference_fidelity)
    cases = count // words
    body = r"""
  localparam WORDS=WORD_COUNT;
  reg abort_error=0,cv=0,iv=0,ready=0,fp16=0;
  reg [3:0] slots=0;
  reg [127:0] input_a=0,input_b=0;
  reg [15:0] gamma=0;
  wire cr,ir,ov,busy,done,error;
  wire [31:0] index;
  wire [127:0] data;
  wire [63:0] encoded;
  wire [3:0] nonzero,os;
  reg [127:0] values[0:WORDS-1],others[0:WORDS-1],expected[0:WORDS-1];
  reg [63:0] expected_encoded[0:WORDS-1];
  reg [3:0] expected_nonzero[0:WORDS-1];
  reg ffp;
  reg [3:0] fslots;
  reg [127:0] fa,fb,fe;
  reg [63:0] fact;
  reg [3:0] fnz;
  reg source_held=0;
  integer testcase,w,sent,received,age,complete,input_transfers=0,output_transfers=0,stalls=0;
  INSTANCE
  task reset_check;
    begin
      if ({cr,ir,ov,index,data,encoded,nonzero,os,busy,done,error} !== 238'b0)
        $fatal(1,"RESET_OUTPUT_XZ");
    end
  endtask
  always @(posedge clk or negedge clk) if (!rst_n) reset_check();
  initial begin
    INITIAL_CHECK
    repeat(3) tick(); @(negedge clk); rst_n=1; repeat(4) tick();
    fd=$fopen("VECTORS","r");
    if (!fd) $fatal(1,"FIXTURE_OPEN");
    for (testcase=0;testcase<CASE_COUNT;testcase=testcase+1) begin
      for (w=0;w<WORDS;w=w+1) begin
        rc=$fscanf(fd,"%h %h %h %h %h %h %h\n",ffp,fslots,fa,fb,fe,fact,fnz);
        if (rc!=7) $fatal(1,"FIXTURE_PARSE");
        values[w]=fa; others[w]=fb; expected[w]=fe;
        expected_encoded[w]=fact; expected_nonzero[w]=fnz;
      end
      @(negedge clk); fp16=ffp; slots=fslots; cv=1;
      if (cr!==1) $fatal(1,"COMMAND_READY testcase=%0d",testcase);
      tick();
      @(negedge clk); cv=0;
      sent=0; received=0; age=0; complete=0;
      source_held=0;
      while (!complete) begin
        if (!source_held) begin
          iv=(sent<WORDS) && ((age%5)!=1);
          if (sent<WORDS) begin
            input_a=values[sent]; input_b=others[sent]; gamma=others[sent][15:0];
          end
        end
        ready=((age%7)<4);
        @(posedge clk);
        source_held=iv && !ir;
        if (iv && ir) begin sent=sent+1; input_transfers=input_transfers+1; end
        if (ov===1) begin
          if (received>=WORDS || {index,data,encoded,nonzero,os} !==
              {32'(received),expected[received],expected_encoded[received],
               expected_nonzero[received],slots})
            $fatal(1,"OPERATOR_NUMERIC testcase=%0d word=%0d index=%0d got=%h/%h/%h expected=%h/%h/%h",
                   testcase,received,index,data,encoded,nonzero,
                   expected[received],expected_encoded[received],expected_nonzero[received]);
          checked=checked+4;
          if (ready) begin received=received+1; output_transfers=output_transfers+1; end
          else stalls=stalls+1;
        end else if (ov!==0) $fatal(1,"VALID_XZ");
        if (done===1) begin
          if (error!==0 || sent!=WORDS || received!=WORDS)
            $fatal(1,"OPERATOR_COMPLETION testcase=%0d sent=%0d received=%0d error=%b",
                   testcase,sent,received,error);
          complete=1;
        end
        #1; cycles=cycles+1; age=age+1;
        if (age>50000) $fatal(1,"FINITE_COMPLETION");
        @(negedge clk);
      end
      iv=0; ready=0; tick();
      @(negedge clk); tick();
    end
    if (input_transfers!=CASE_COUNT*WORDS || output_transfers!=CASE_COUNT*WORDS ||
        stalls==0) $fatal(1,"COVERAGE");
    $display("CHECK compared=%0d inputs=%0d outputs=%0d stalled_comparisons=%0d",
             checked,input_transfers,output_transfers,stalls);
    $finish;
  end
"""
    instances = {
        "rmsnorm": (
            "anvil_q1_ht2_rmsnorm #(.HIDDEN_SIZE(WORDS)) dut(clk,rst_n,abort_error,cv,cr,"
            "slots,fp16,iv,ir,input_a,gamma,ov,ready,index,data,os,busy,done,error);\n"
            "assign encoded=0; assign nonzero=0;"
        ),
        "swiglu": (
            "anvil_q1_ht2_swiglu #(.INTERMEDIATE_SIZE(WORDS)) dut(clk,rst_n,abort_error,cv,cr,"
            "slots,fp16,iv,ir,input_a,input_b,ov,ready,index,data,encoded,nonzero,os,busy,done,error);"
        ),
    }
    body = body.replace("INSTANCE", instances[kind]).replace("WORD_COUNT", str(words))
    body = body.replace("CASE_COUNT", str(cases)).replace("VECTORS", relative(vector_path))
    body = body.replace("INITIAL_CHECK", "#1; reset_check();" if simulator == "verilator"
                        else "#0; reset_check();")
    modules = [kind, "fp32_mul", "fp32_add", "fp32_divsqrt"]
    if kind == "swiglu":
        modules += ["swiglu_engine", "fp32_exp"]
    return simulate(directory, f"{kind}-{words}-{simulator}", body, modules, simulator)
