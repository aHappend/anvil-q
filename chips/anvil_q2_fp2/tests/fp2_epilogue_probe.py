"""Public-pin fused epilogue numerical/latency preparation."""

import argparse
from fractions import Fraction
from pathlib import Path
import random
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fp2_probe import Probe, ROOT, simulate
from fp2_reference import exact, finite, rms, rope, rope_coefficients, rounded, swiglu


EPILOGUE_TB = r"""
module tb;
  reg clk=0;
  always #5 clk=~clk;
  reg rst_n, flush=0, in_valid=0, out_ready=0;
  reg [2:0] in_mode=0;
  reg [31:0] in_a=0,in_b=0,in_gamma=0,in_cos=0,in_sin=0;
  reg [31:0] in_length=0,in_index=0,in_tag=0;
  reg in_first=0,in_last=0;
  wire in_ready,out_valid,out_first,out_last,out_error;
  wire [31:0] out_data,out_pair,out_index,out_tag;
  anvil_q2_fp2_epilogue_fusion epilogue(
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .in_valid(in_valid),.in_ready(in_ready),.in_mode(in_mode),.in_a(in_a),.in_b(in_b),
    .in_gamma(in_gamma),.in_cos(in_cos),.in_sin(in_sin),.in_length(in_length),
    .in_index(in_index),.in_tag(in_tag),.in_first(in_first),.in_last(in_last),
    .out_valid(out_valid),.out_ready(out_ready),.out_data(out_data),.out_pair(out_pair),
    .out_index(out_index),.out_tag(out_tag),.out_first(out_first),.out_last(out_last),
    .out_error(out_error)
  );
  integer fd,n,id,mode,length,index,age,latency,outputs,held,count=0,wait_cycles;
  reg [31:0] a,b,gamma,cosine,sine;
  reg [130:0] held_payload;
  time previous_accept;
  string input_path;
  wire [130:0] payload={out_data,out_pair,out_index,out_tag,out_first,out_last,out_error};
  wire reset_ok=({in_ready,out_valid,payload} === 0);
  always @(posedge clk) if(!rst_n && reset_ok !== 1'b1) $fatal(1,"RESET posedge");
  always @(negedge clk) if(!rst_n && reset_ok !== 1'b1) $fatal(1,"RESET negedge");
  initial begin
    rst_n=0;
    #1; if(reset_ok !== 1'b1) $fatal(1,"RESET time0");
    repeat(2) @(negedge clk);
    rst_n=1;
    if(!$value$plusargs("INPUT=%s",input_path)) $fatal(1,"missing INPUT");
    fd=$fopen(input_path,"r");
    if(fd==0) $fatal(1,"input open");
    while(!$feof(fd)) begin
      n=$fscanf(fd,"%d %d %d\n",id,mode,length);
      if(n!=3) begin
        if(!$feof(fd)) $fatal(1,"malformed header");
      end else begin
        previous_accept=0;
        for(index=0;index<length;index=index+1) begin
          n=$fscanf(fd,"%h %h %h %h %h\n",a,b,gamma,cosine,sine);
          if(n!=5) $fatal(1,"malformed element");
          in_mode=mode; in_length=length; in_index=index; in_tag=id;
          in_a=a; in_b=b; in_gamma=gamma; in_cos=cosine; in_sin=sine;
          in_first=index==0; in_last=index==length-1; in_valid=1; wait_cycles=0;
          @(posedge clk);
          while(in_ready !== 1'b1) begin
            wait_cycles=wait_cycles+1;
            if(wait_cycles>64) $fatal(1,"EPILOGUE_INPUT_LIVENESS");
            @(posedge clk);
          end
          if(mode==0 && index>0 && $time-previous_accept!=40)
            $fatal(1,"RMS_SPACING");
          previous_accept=$time;
          #1;
          if(index<length-1 && out_valid !== 1'b0) $fatal(1,"EARLY_RMS_RESULT");
          if(index<length-1) begin @(negedge clk); in_valid=0; end
        end
        case(mode)
          0: latency=21;
          1: latency=6;
          2: latency=23;
          3: latency=3;
          default: latency=0;
        endcase
        for(age=0;age<=latency;age=age+1) begin
          if(out_valid !== (age==latency))
            $fatal(1,"EPILOGUE_LATENCY id=%0d mode=%0d age=%0d",id,mode,age);
          if(age!=latency) begin
            @(negedge clk); in_valid=0;
            @(posedge clk); #1;
          end
        end
        held_payload=payload;
        for(held=0;held<3;held=held+1) begin
          @(negedge clk); in_valid=0;
          @(posedge clk); #1;
          if(out_valid !== 1'b1 || payload !== held_payload) $fatal(1,"STALLED_EPILOGUE");
        end
        @(negedge clk); out_ready=1;
        for(outputs=0;outputs<length;outputs=outputs+1) begin
          @(posedge clk);
          if(out_valid !== 1'b1 || out_tag !== id || out_index !== outputs ||
             out_first !== (outputs==0) || out_last !== (outputs==length-1) ||
             (^payload) === 1'bx) $fatal(1,"EPILOGUE_OUTPUT_METADATA");
          $display("RESULT %0d %0d %08h %08h %0d",id,outputs,out_data,out_pair,out_error);
          #1;
        end
        if(out_valid !== 1'b0) $fatal(1,"DUPLICATE_EPILOGUE_OUTPUT");
        @(negedge clk); out_ready=0;
        count=count+1;
      end
    end
    $display("SUMMARY %0d",count);
    $finish;
  end
endmodule
"""


def cases(compact, rotations=None):
    rng = random.Random(203)
    count = 32 if compact else 10000
    for index in range(count):
        x = rounded(Fraction(rng.randrange(-1024, 1025), 64))
        y = rounded(Fraction(rng.randrange(-1024, 1025), 64))
        position = 32767 if index % 17 == 0 else rng.randrange(1, 32768)
        dimension = (8, 32, 128)[index % 3]
        pair = index % (dimension // 2)
        cosine, sine = rope_coefficients(position, pair, dimension)
        if rotations is not None:
            rotations[index] = (position, pair, dimension)
        yield 1, [(x, y, 0x3F800000, cosine, sine)], [rope(x, y, cosine, sine)]
    for index in range(count):
        gate = rounded(Fraction(rng.randrange(-6400, 6401), 64))
        up = rounded(Fraction(rng.randrange(-1024, 1025), 64))
        yield 2, [(gate, up, 0, 0, 0)], [(swiglu(gate, up), 0)]
    lengths = [1, 2, 7, 48] if compact else [
        *([1, 2, 7, 48] * 249), 1536, 1536, 8960, 8960
    ]
    for length in lengths:
        values = [rounded(Fraction(rng.randrange(-256, 257), 64)) for _ in range(length)]
        gamma = [rounded(Fraction(rng.randrange(-128, 129), 64)) for _ in range(length)]
        expected = rms(values, gamma)
        yield 0, [(value, 0, weight, 0, 0) for value, weight in zip(values, gamma, strict=True)], [
            (value, 0) for value in expected
        ]
    for mode in (3, 4):
        for index in range(16):
            value = rounded(Fraction(index - 8, 8))
            other = rounded(Fraction(8 - index, 16))
            result = rounded(exact(value) + exact(other)) if mode == 3 else value
            yield mode, [(value, other, 0, 0, 0)], [(result, 0)]


def run(probe, compact, simulator, overrides=None):
    rotations = {}
    stimulus = list(cases(compact, rotations))
    source = probe.directory / "tb.sv"
    source.write_text(EPILOGUE_TB)
    inputs = probe.directory / "inputs.txt"
    expected = {}
    with inputs.open("w") as stream:
        for tag, (mode, elements, results) in enumerate(stimulus):
            stream.write(f"{tag} {mode} {len(elements)}\n")
            for index, (element, result) in enumerate(zip(elements, results, strict=True)):
                stream.write(" ".join(f"{word:08x}" for word in element) + "\n")
                expected[tag, index] = (mode, result)
    overrides = overrides or {}
    rtl = [overrides.get(name, ROOT / "rtl" / name) for name in (
        "anvil_q2_fp2_arithmetic.sv", "anvil_q2_fp2_nonlinear.sv",
        "anvil_q2_fp2_coefficients.sv", "anvil_q2_fp2_epilogue_fusion.sv",
    )]
    output = simulate(probe, source, rtl, simulator, [f"+INPUT={inputs.relative_to(ROOT)}"])
    seen = set()
    summary = None
    with output.open() as stream:
        for line in stream:
            words = line.split()
            if words[:1] == ["SUMMARY"]:
                summary = int(words[1])
            if words[:1] != ["RESULT"]:
                continue
            tag, index, data, pair, failed = (int(words[1]), int(words[2]), int(words[3], 16),
                                             int(words[4], 16), int(words[5]))
            if (tag, index) in seen or (tag, index) not in expected:
                raise AssertionError(f"duplicate/unexpected observation {tag} {index}")
            seen.add((tag, index))
            mode, (reference, reference_pair) = expected[tag, index]
            context = {"tag": tag, "index": index, "mode": mode}
            probe.compare("epilogue-error", 0, failed, context)
            probe.compare("epilogue-pair", f"{reference_pair:08x}", f"{pair:08x}", context)
            if mode in (0, 2):
                error = abs(exact(reference) - exact(data)) if finite(data) else None
                limit = Fraction(3, 1000000) * (1 + abs(exact(reference)))
                probe.compare(
                    "rms-bound" if mode == 0 else "swiglu-bound", True,
                    error is not None and error <= limit,
                    {**context, "reference": f"{reference:08x}", "observed": f"{data:08x}",
                     "absolute_error": float(error) if error is not None else None,
                     "threshold": float(limit)},
                )
            else:
                probe.compare("epilogue-exact", f"{reference:08x}", f"{data:08x}", context)
            if mode == 1:
                position, pair_index, dimension = rotations[tag]
                cosine, sine = rope_coefficients(position, pair_index, dimension, mathematical=True)
                x, y, _, supplied_cosine, supplied_sine = stimulus[tag][1][0]
                probe.compare("theta-coefficient-cosine", rounded(cosine), supplied_cosine, context)
                probe.compare("theta-coefficient-sine", rounded(sine), supplied_sine, context)
                analytic_first = exact(x) * cosine - exact(y) * sine
                analytic_second = exact(y) * cosine + exact(x) * sine
                limit = Fraction(3, 1000000) * (1 + max(abs(exact(x)), abs(exact(y))))
                probe.compare("analytic-rope-rotation-bound", True,
                              finite(data) and finite(pair) and
                              abs(exact(data) - analytic_first) <= limit and
                              abs(exact(pair) - analytic_second) <= limit,
                              {**context, "position": position, "dimension": dimension,
                               "threshold": float(limit)})
    probe.compare("summary-count", len(stimulus), summary, {})
    probe.compare("output-count", len(expected), len(seen), {})
    probe.summary["coverage"] = {
        "rms_vectors": sum(mode == 0 for mode, _, _ in stimulus),
        "rms_lengths": sorted({len(elements) for mode, elements, _ in stimulus if mode == 0}),
        "rope_pairs": sum(mode == 1 for mode, _, _ in stimulus),
        "swiglu_elements": sum(mode == 2 for mode, _, _ in stimulus),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compact", action="store_true")
    parser.add_argument("--simulator", choices=("iverilog", "verilator"), default="verilator")
    parser.add_argument("--repair-of")
    args = parser.parse_args()
    if args.simulator == "iverilog":
        args.compact = True
    probe = Probe("epilogue", args.repair_of)
    try:
        run(probe, args.compact, args.simulator)
        return probe.settle()
    except Exception as error:
        return probe.settle(f"{type(error).__name__}: {error}")


if __name__ == "__main__":
    raise SystemExit(main())
