"""Public-pin 128-lane tensor test with an independent balanced IEEE tree.

The compact diagnostic executes 128 tiles. The unabridged generator declares
10,000 independent finite tiles plus directed exponent/cancellation cases.
"""

import argparse
from pathlib import Path
import random
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fp2_probe import Probe, ROOT, simulate
from fp2_reference import tensor


TENSOR_TB = r"""
module tb;
  reg clk=0;
  always #5 clk=~clk;
  reg rst_n, flush=0, w_valid=0, w_format=0, w_first=1, w_last=1, w_error=0;
  reg [511:0] w_data=0;
  reg [15:0] w_scale=16'h7f7f;
  reg [31:0] w_tag=0, in_tag=0;
  reg in_valid=0, in_first=1, in_last=1, out_ready=0;
  reg [2047:0] in_a=0;
  reg [127:0] in_mask=0;
  wire w_ready, in_ready, out_valid, out_first, out_last, out_error;
  wire [31:0] out_data, out_tag;
  anvil_q2_fp2_bfp_tensor_array array_dut(
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .w_valid(w_valid),.w_ready(w_ready),.w_data(w_data),.w_scale(w_scale),
    .w_format(w_format),.w_first(w_first),.w_last(w_last),.w_tag(w_tag),.w_error(w_error),
    .in_valid(in_valid),.in_ready(in_ready),.in_a(in_a),.in_mask(in_mask),
    .in_first(in_first),.in_last(in_last),.in_tag(in_tag),
    .out_valid(out_valid),.out_ready(out_ready),.out_data(out_data),
    .out_first(out_first),.out_last(out_last),.out_tag(out_tag),.out_error(out_error)
  );
  integer fd,n,id,beat,age,hold_cycle,count=0,wait_cycles;
  reg [2047:0] read_a,read_b,weights;
  reg [127:0] read_mask;
  reg [31:0] held_data;
  reg held_error;
  string input_path;
  wire reset_ok=({w_ready,in_ready,out_valid,out_data,out_first,out_last,out_tag,out_error} === 0);
  always @(posedge clk) if (!rst_n && reset_ok !== 1'b1) $fatal(1,"RESET posedge");
  always @(negedge clk) if (!rst_n && reset_ok !== 1'b1) $fatal(1,"RESET negedge");
  initial begin
    rst_n=0;
    #1; if(reset_ok !== 1'b1) $fatal(1,"RESET time0");
    repeat(2) @(negedge clk);
    rst_n=1;
    if(!$value$plusargs("INPUT=%s",input_path)) $fatal(1,"missing INPUT");
    fd=$fopen(input_path,"r");
    if(fd==0) $fatal(1,"input open");
    while(!$feof(fd)) begin
      n=$fscanf(fd,"%d %h %h %h\n",id,read_a,read_b,read_mask);
      if(n!=4) begin
        if(!$feof(fd)) $fatal(1,"malformed stimulus");
      end else begin
        weights=read_b;
        w_tag=id;
        for(beat=0;beat<4;beat=beat+1) begin
          w_data=weights[512*beat+:512];
          w_valid=1; wait_cycles=0;
          @(posedge clk);
          while(w_ready !== 1'b1) begin
            wait_cycles=wait_cycles+1;
            if(wait_cycles>128) $fatal(1,"WEIGHT_LIVENESS");
            @(posedge clk);
          end
          @(negedge clk); w_valid=0;
        end
        in_a=read_a; in_mask=read_mask; in_tag=id; in_valid=1;
        @(posedge clk);
        if(in_ready !== 1'b1) $fatal(1,"COMPLETED_TILE_NOT_READY");
        #1;
        for(age=0;age<38;age=age+1) begin
          if(out_valid !== (age==37)) $fatal(1,"TENSOR_LATENCY id=%0d age=%0d",id,age);
          if(age!=37) begin
            @(negedge clk); in_valid=0;
            @(posedge clk); #1;
          end
        end
        if(out_tag !== id || out_first !== 1'b1 || out_last !== 1'b1 ||
           (^{out_data,out_error}) === 1'bx) $fatal(1,"TENSOR_METADATA_OR_X");
        held_data=out_data;
        held_error=out_error;
        $display("RESULT %0d %08h %0d",id,out_data,out_error);
        for(hold_cycle=0;hold_cycle<3;hold_cycle=hold_cycle+1) begin
          @(posedge clk); #1;
          if(out_valid !== 1'b1 || out_data !== held_data || out_tag !== id ||
             out_first !== 1'b1 || out_last !== 1'b1 || out_error !== held_error)
            $fatal(1,"TENSOR_STALLED_PAYLOAD");
        end
        @(negedge clk); out_ready=1;
        @(posedge clk);
        @(negedge clk); out_ready=0;
        count=count+1;
      end
    end
    $display("SUMMARY %0d",count);
    $finish;
  end
endmodule
"""


def vectors(compact):
    randomizer = random.Random(89)
    count = 128 if compact else 10000
    for index in range(count):
        a = [(randomizer.randrange(2) << 15) | (randomizer.randrange(151) << 7) |
             randomizer.randrange(128) for _ in range(128)]
        b = [(randomizer.randrange(2) << 15) | (randomizer.randrange(151) << 7) |
             randomizer.randrange(128) for _ in range(128)]
        mask = randomizer.getrandbits(128)
        if index % 8 == 0:
            mask = (1 << 128) - 1
        elif index % 8 == 1:
            mask = 1 << (index % 128)
        elif index % 8 == 2:
            mask = (1 << (1 + index % 127)) - 1
        yield a, b, mask
    for lane in range(128):
        a, b = [0] * 128, [0x3F80] * 128
        a[lane] = 0x7F7F
        b[lane] = 1
        yield a, b, (1 << 128) - 1
    yield [0x8000] * 128, [0x3F80] * 128, 0
    yield [0x8000] * 128, [0x3F80] * 128, (1 << 128) - 1
    yield [0x3F80, 0xBF80] * 64, [0x3F80] * 128, (1 << 128) - 1


def packed(values):
    return "".join(f"{word:04x}" for word in reversed(values))


def run(probe, compact, simulator, overrides=None):
    cases = list(vectors(compact))
    expected = [tensor(a, b, mask) for a, b, mask in cases]
    source = probe.directory / "tb.sv"
    source.write_text(TENSOR_TB)
    images = probe.directory / "checkpoint-images"
    images.mkdir()
    inputs = images / "tiles.txt"
    with inputs.open("w") as stream:
        for index, (a, b, mask) in enumerate(cases):
            stream.write(f"{index} {packed(a)} {packed(b)} {mask:032x}\n")
    overrides = overrides or {}
    rtl = [overrides.get(name, ROOT / "rtl" / name) for name in (
        "anvil_q2_fp2_arithmetic.sv", "anvil_q2_fp2_mx_decode.sv",
        "anvil_q2_fp2_ping_pong_prefetch.sv", "anvil_q2_fp2_bfp_tensor_array.sv",
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
            index, data, error = int(words[1]), int(words[2], 16), int(words[3])
            if index in seen or not 0 <= index < len(expected):
                raise AssertionError(f"duplicate/out-of-range tile {index}")
            seen.add(index)
            value, failed = expected[index]
            probe.compare("balanced-tree-bits", f"{value:08x}", f"{data:08x}", {"index": index})
            probe.compare("tensor-error", int(failed), error, {"index": index})
    probe.compare("summary-count", len(cases), summary, {})
    probe.compare("observed-tile-count", len(cases), len(seen), {})
    probe.summary["coverage"] = {
        "independent_random_finite_tiles": 128 if compact else 10000,
        "directed_single_lane_extreme_exponents": 128,
        "physical_lanes": 128, "groups": 4,
        "stalled_outputs_per_tile": 3, "registered_stages": 38,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compact", action="store_true")
    parser.add_argument("--simulator", choices=("iverilog", "verilator"), default="verilator")
    parser.add_argument("--repair-of")
    args = parser.parse_args()
    if args.simulator == "iverilog":
        args.compact = True
    probe = Probe("tensor", args.repair_of)
    try:
        run(probe, args.compact, args.simulator)
        return probe.settle()
    except Exception as error:
        return probe.settle(f"{type(error).__name__}: {error}")


if __name__ == "__main__":
    raise SystemExit(main())
