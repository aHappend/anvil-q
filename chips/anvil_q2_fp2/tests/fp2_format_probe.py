"""Independent BF16 storage and Group-32 MX encoding comparisons."""

import argparse
from fractions import Fraction
from pathlib import Path
import random
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fp2_probe import Probe, ROOT, simulate
from fp2_reference import exact, finite, mx_decode, mx_encode_group, rounded
from fp2_tensor_probe import packed


STORAGE_TB = r"""
module tb;
  reg [31:0] x;
  wire [15:0] y;
  wire failed;
  integer i;
  anvil_q2_fp2_bf16_round rounding(x,y,failed);
  initial begin
    for(i=0;i<65536;i=i+1) begin
      x={i[15:0],16'd0}; #1;
      $display("RESULT %0d %04h %0d",i,y,failed);
    end
    $display("SUMMARY 65536"); $finish;
  end
endmodule
"""


ENCODE_TB = r"""
module tb;
  reg clk=0;
  always #5 clk=~clk;
  reg rst_n, flush=0, in_valid=0, out_ready=0;
  reg [511:0] in_bf16=0, read_data;
  reg [31:0] in_mask=0,in_tag=0,read_mask;
  wire in_ready,out_valid,out_error;
  wire [255:0] out_payload;
  wire [7:0] out_scale;
  wire [31:0] out_tag;
  integer fd,n,id,age,held,count=0;
  reg [296:0] held_payload;
  string input_path;
  wire [296:0] payload={out_payload,out_scale,out_tag,out_error};
  wire reset_ok=({in_ready,out_valid,payload}===0);
  anvil_q2_fp2_mx_encode32 encoder(clk,rst_n,flush,in_valid,in_ready,
    in_bf16,in_mask,in_tag,out_valid,out_ready,out_payload,out_scale,out_tag,out_error);
  always @(posedge clk) if(!rst_n && reset_ok !== 1'b1) $fatal(1,"RESET posedge");
  always @(negedge clk) if(!rst_n && reset_ok !== 1'b1) $fatal(1,"RESET negedge");
  initial begin
    rst_n=0; #1;
    if(reset_ok !== 1'b1) $fatal(1,"RESET time0");
    repeat(2) @(negedge clk); rst_n=1;
    if(!$value$plusargs("INPUT=%s",input_path)) $fatal(1,"missing INPUT");
    fd=$fopen(input_path,"r"); if(!fd) $fatal(1,"open INPUT");
    while(!$feof(fd)) begin
      n=$fscanf(fd,"%d %h %h\n",id,read_data,read_mask);
      if(n!=3) begin if(!$feof(fd)) $fatal(1,"malformed INPUT"); end
      else begin
        in_bf16=read_data; in_mask=read_mask; in_tag=id; in_valid=1;
        @(posedge clk); if(in_ready !== 1'b1) $fatal(1,"INPUT_NOT_READY"); #1;
        for(age=0;age<3;age=age+1) begin
          if(out_valid !== (age==2)) $fatal(1,"ENCODE_LATENCY");
          if(age!=2) begin @(negedge clk); in_valid=0; @(posedge clk); #1; end
        end
        if(out_tag !== id || (^payload) === 1'bx) $fatal(1,"ENCODE_TAG_OR_X");
        held_payload=payload;
        for(held=0;held<3;held=held+1) begin
          @(posedge clk); #1;
          if(out_valid !== 1'b1 || payload !== held_payload) $fatal(1,"STALLED_ENCODER");
        end
        $display("RESULT %0d %h %0d %0d",id,out_payload,out_scale,out_error);
        @(negedge clk); out_ready=1; @(posedge clk);
        @(negedge clk); out_ready=0;
        count=count+1;
      end
    end
    $display("SUMMARY %0d",count); $finish;
  end
endmodule
"""


def run_storage(probe, simulator="iverilog"):
    source = probe.directory / "tb.sv"
    source.write_text(STORAGE_TB)
    output = simulate(probe, source, [ROOT / "rtl/anvil_q2_fp2_mx_encode.sv"], simulator)
    seen = set()
    summary = None
    for line in output.read_text().splitlines():
        words = line.split()
        if words[:1] == ["SUMMARY"]:
            summary = int(words[1])
        if words[:1] != ["RESULT"]:
            continue
        index, data, error = int(words[1]), int(words[2], 16), int(words[3])
        if index in seen or not 0 <= index < 65536:
            raise AssertionError("duplicate/out-of-range BF16 observation")
        seen.add(index)
        is_finite = finite(index, fraction_bits=7)
        expected = index if is_finite or index & 127 == 0 else 0x7FC0
        probe.compare("bf16-exact-storage", expected, data, {"bits": f"{index:04x}"})
        probe.compare("bf16-classification", int(not is_finite), error, {"bits": f"{index:04x}"})
    probe.compare("storage-summary", 65536, summary, {})
    probe.compare("storage-count", 65536, len(seen), {})


def groups(compact):
    yield [0] * 32, 0xFFFFFFFF
    yield [0x8000] * 32, 0xFFFFFFFF
    yield [0x7F7F] * 32, 0
    # Subnormal, boundary maxima, signed zero and every finite exponent bin.
    for exponent in range(255):
        magnitude = (exponent << 7) | (exponent % 128)
        yield [magnitude, magnitude | 0x8000, 0x8000] + [1] * 29, 0xFFFFFFFF
    rng = random.Random(89)
    for index in range(32 if compact else 1000):
        exponent = rng.randrange(1, 254)
        values = [(rng.randrange(2) << 15) |
                  (max(0, exponent - rng.randrange(8)) << 7) | rng.randrange(128)
                  for _ in range(32)]
        yield values, 0xFFFFFFFF if index % 3 == 0 else rng.getrandbits(32)


def run_encode(probe, compact=False, simulator="verilator"):
    stimulus = list(groups(compact))
    expected = [mx_encode_group(values, mask) for values, mask in stimulus]
    source = probe.directory / "tb.sv"
    source.write_text(ENCODE_TB)
    images = probe.directory / "checkpoint-images"
    images.mkdir()
    inputs = images / "groups.txt"
    inputs.write_text("".join(f"{i} {packed(values)} {mask:08x}\n"
                             for i, (values, mask) in enumerate(stimulus)))
    output = simulate(probe, source, [ROOT / "rtl/anvil_q2_fp2_mx_encode.sv"],
                      simulator, [f"+INPUT={inputs.relative_to(ROOT)}"])
    seen = set()
    summary = None
    maximum_nrmse = 0.0
    for line in output.read_text().splitlines():
        words = line.split()
        if words[:1] == ["SUMMARY"]:
            summary = int(words[1])
        if words[:1] != ["RESULT"]:
            continue
        index, payload, scale, error = int(words[1]), int(words[2], 16), int(words[3]), int(words[4])
        if index in seen or not 0 <= index < len(stimulus):
            raise AssertionError("duplicate/out-of-range encoding observation")
        seen.add(index)
        codes, expected_scale = expected[index]
        expected_payload = sum(code << (8 * lane) for lane, code in enumerate(codes))
        probe.compare("group-scale", expected_scale, scale, {"index": index})
        probe.compare("group-payload", f"{expected_payload:064x}", f"{payload:064x}", {"index": index})
        probe.compare("group-finite", 0, error, {"index": index})
        values, mask = stimulus[index]
        active = [lane for lane in range(32) if mask >> lane & 1]
        maximum = max((abs(exact(values[lane], fraction_bits=7)) for lane in active), default=0)
        if maximum:
            squared = []
            for lane in active:
                decoded, failed = mx_decode((payload >> (8 * lane)) & 255, scale)
                if failed:
                    raise AssertionError("encoder emitted a nonfinite reconstruction")
                squared.append((exact(decoded, fraction_bits=7) -
                                exact(values[lane], fraction_bits=7)) ** 2)
            normalized_squared = sum(squared) / (len(active) * maximum ** 2)
            probe.compare("group-reconstruction-bound", True,
                          normalized_squared <= Fraction(65, 1000) ** 2,
                          {"index": index, "nrmse": float(normalized_squared) ** 0.5})
            maximum_nrmse = max(maximum_nrmse, float(normalized_squared) ** 0.5)
    probe.compare("encode-summary", len(stimulus), summary, {})
    probe.compare("encode-count", len(stimulus), len(seen), {})
    probe.summary["maximum_normalized_reconstruction_rms"] = maximum_nrmse
    inputs.unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kind", choices=("storage", "encode"), required=True)
    parser.add_argument("--compact", action="store_true")
    parser.add_argument("--simulator", choices=("iverilog", "verilator"), default="verilator")
    args = parser.parse_args()
    probe = Probe(args.kind)
    try:
        if args.kind == "storage":
            run_storage(probe, args.simulator)
        else:
            run_encode(probe, args.compact or args.simulator == "iverilog", args.simulator)
        return probe.settle()
    except Exception as error:
        return probe.settle(f"{type(error).__name__}: {error}")


if __name__ == "__main__":
    raise SystemExit(main())
