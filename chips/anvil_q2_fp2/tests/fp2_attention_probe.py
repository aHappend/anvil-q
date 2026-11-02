"""Six-head attention public-pin comparison against stable high-precision softmax."""

import argparse
from decimal import Decimal, localcontext
from fractions import Fraction
from pathlib import Path
import random
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fp2_probe import Probe, ROOT, simulate
from fp2_reference import decimal_value, exact, finite, multiply, mx_decode, rounded, tensor, transcendental
from fp2_tensor_probe import packed


ATTENTION_TB = r"""
module tb;
  localparam D=@DIM@, TILE=@TILE@, G=(D+31)/32;
  reg clk=0;
  always #5 clk=~clk;
  reg rst_n,flush=0,cmd_valid=0,kv_valid=0,out_ready=0;
  reg [31:0] cmd_layer=0,cmd_kv_head=0,cmd_pos=0,cmd_len=0,cmd_tag=0,kv_index=0;
  reg [6*D*16-1:0] cmd_query=0;
  reg [D*16-1:0] kv_key=0,kv_value=0;
  reg [G*8-1:0] kv_scale_key=0,kv_scale_value=0;
  reg kv_format=0,kv_last=0,kv_error=0;
  wire cmd_ready,kv_ready,out_valid,out_error;
  wire [6*D*32-1:0] out_data;
  wire [31:0] out_tag;
  anvil_q2_fp2_flash_attn #(.HEAD_DIM(D),.TILE_TOKENS(TILE),.MAX_SEQ_LEN(32768)) attention(
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .cmd_valid(cmd_valid),.cmd_ready(cmd_ready),.cmd_layer(cmd_layer),
    .cmd_kv_head(cmd_kv_head),.cmd_pos(cmd_pos),.cmd_len(cmd_len),.cmd_tag(cmd_tag),
    .cmd_query(cmd_query),.kv_valid(kv_valid),.kv_ready(kv_ready),
    .kv_key(kv_key),.kv_value(kv_value),.kv_scale_key(kv_scale_key),
    .kv_scale_value(kv_scale_value),.kv_format(kv_format),.kv_index(kv_index),
    .kv_last(kv_last),.kv_error(kv_error),.out_valid(out_valid),.out_ready(out_ready),
    .out_data(out_data),.out_tag(out_tag),.out_error(out_error)
  );
  integer fd,n,id,length,index,format,count=0,accepted_kv=0,cycles,bound,held,read_head;
  reg [D*16-1:0] read_query;
  reg [D*16-1:0] read_key,read_value;
  reg [G*8-1:0] read_ks,read_vs;
  reg [6*D*32-1:0] held_data;
  reg held_error;
  time accepted_command;
  string input_path;
  wire reset_ok=({cmd_ready,kv_ready,out_valid,out_error,out_data,out_tag} === 0);
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
      n=$fscanf(fd,"%d %d\n",id,length);
      if(n!=2) begin
        if(!$feof(fd)) $fatal(1,"malformed header");
      end else begin
        for(read_head=0;read_head<6;read_head=read_head+1) begin
          n=$fscanf(fd,"%h\n",read_query);
          if(n!=1) $fatal(1,"malformed query");
          cmd_query[read_head*D*16+:D*16]=read_query;
        end
        cmd_len=length; cmd_pos=length-1; cmd_tag=id; cmd_valid=1;
        @(posedge clk);
        if(cmd_ready !== 1'b1 || out_valid !== 1'b0) $fatal(1,"COMMAND_NOT_IDLE");
        accepted_command=$time; bound=(512+64*D)*length+64*D;
        @(negedge clk); cmd_valid=0;
        for(index=0;index<length;index=index+1) begin
          n=$fscanf(fd,"%d %h %h %h %h\n",format,read_key,read_value,read_ks,read_vs);
          if(n!=5) $fatal(1,"malformed KV");
          kv_key=read_key; kv_value=read_value;
          kv_scale_key=read_ks; kv_scale_value=read_vs;
          kv_format=format; kv_index=index; kv_last=index==length-1; kv_valid=1;
          @(posedge clk);
          while(kv_ready !== 1'b1) begin
            if(out_valid !== 1'b0) $fatal(1,"EARLY_ATTENTION_RESULT");
            if($time-accepted_command>bound*10) $fatal(1,"ATTENTION_BOUND_WHILE_KV");
            @(posedge clk);
          end
          accepted_kv=accepted_kv+1;
          if(out_valid !== 1'b0) $fatal(1,"RESULT_PRECEDES_LAST_KV");
          @(negedge clk); kv_valid=0;
        end
        @(posedge clk); #1;
        while(out_valid !== 1'b1) begin
          if((^{cmd_ready,kv_ready,out_valid,out_error}) === 1'bx)
            $fatal(1,"ATTENTION_CONTROL_X");
          if($time-accepted_command>bound*10) $fatal(1,"ATTENTION_COMPLETION_BOUND");
          @(posedge clk); #1;
        end
        cycles=($time-accepted_command)/10;
        if(out_tag !== id || (^{out_data,out_error}) === 1'bx)
          $fatal(1,"ATTENTION_PAYLOAD_X_OR_TAG");
        held_data=out_data; held_error=out_error;
        for(held=0;held<3;held=held+1) begin
          @(posedge clk); #1;
          if(out_valid !== 1'b1 || out_tag !== id || out_data !== held_data ||
             out_error !== held_error) $fatal(1,"ATTENTION_STALLED_PAYLOAD");
        end
        @(negedge clk); out_ready=1;
        @(posedge clk);
        for(read_head=0;read_head<6;read_head=read_head+1)
          $display("RESULT %0d %0d %h %0d %0d",id,read_head,
            out_data[read_head*D*32+:D*32],out_error,cycles);
        #1; if(out_valid !== 1'b0) $fatal(1,"DUPLICATE_ATTENTION_RESULT");
        @(negedge clk); out_ready=0;
        count=count+1;
      end
    end
    $display("SUMMARY %0d %0d",count,accepted_kv);
    $finish;
  end
endmodule
"""


def attention_reference(query, keys, values, dimension):
    head_scale = transcendental(rounded(dimension), "rsqrt")
    outputs = []
    with localcontext() as context:
        context.prec = 100
        for head in range(6):
            scores = []
            for key in keys:
                dot, failed = tensor(
                    query[head * dimension:(head + 1) * dimension] + [0] * (128 - dimension),
                    key + [0] * (128 - dimension), (1 << dimension) - 1
                )
                if failed:
                    raise ArithmeticError("finite fixture produced a nonfinite attention score")
                scores.append(decimal_value(multiply(dot, head_scale)))
            maximum = max(scores)
            probabilities = [(score - maximum).exp() for score in scores]
            denominator = sum(probabilities)
            for component in range(dimension):
                numerator = sum(
                    weight * decimal_value(value[component] << 16)
                    for weight, value in zip(probabilities, values, strict=True)
                )
                outputs.append(rounded(Fraction(numerator / denominator)))
    return outputs


def cases(compact, dimension):
    rng = random.Random(17)
    count = 6 if compact else 100
    groups = (dimension + 31) // 32
    for number in range(count):
        length = (1, 2, 3, 4, 7, 17)[number % 6]
        query = [rounded(Fraction((head + 1) * ((column * 7 + 3) % 13 - 6), 16),
                         fraction_bits=7)
                 for head in range(6) for column in range(dimension)]
        keys, values, bus = [], [], []
        for position in range(length):
            if number % 2:
                payload_k = [rng.randrange(256) for _ in range(dimension)]
                payload_v = [rng.randrange(256) for _ in range(dimension)]
                payload_k = [value if value & 127 != 127 else 0 for value in payload_k]
                payload_v = [value if value & 127 != 127 else 0 for value in payload_v]
                scales_k = [123 + group % 3 for group in range(groups)]
                scales_v = [124 + group % 3 for group in range(groups)]
                key = [mx_decode(value, scales_k[i // 32])[0] for i, value in enumerate(payload_k)]
                value = [mx_decode(value, scales_v[i // 32])[0] for i, value in enumerate(payload_v)]
                bus.append((
                    1, sum(v << (8 * i) for i, v in enumerate(payload_k)),
                    sum(v << (8 * i) for i, v in enumerate(payload_v)),
                    sum(v << (8 * i) for i, v in enumerate(scales_k)),
                    sum(v << (8 * i) for i, v in enumerate(scales_v)),
                ))
            else:
                key = [rounded(Fraction(rng.randrange(-64, 65), 32), fraction_bits=7)
                       for _ in range(dimension)]
                value = [rounded(Fraction(rng.randrange(-64, 65), 32), fraction_bits=7)
                         for _ in range(dimension)]
                bus.append((0, int(packed(key), 16), int(packed(value), 16), 0, 0))
            keys.append(key)
            values.append(value)
        yield query, bus, attention_reference(query, keys, values, dimension)


def run(probe, compact, simulator, dimension, tile):
    stimulus = list(cases(compact, dimension))
    source = probe.directory / "tb.sv"
    source.write_text(ATTENTION_TB.replace("@DIM@", str(dimension)).replace("@TILE@", str(tile)))
    images = probe.directory / "checkpoint-images"
    images.mkdir()
    inputs = images / "attention.txt"
    with inputs.open("w") as stream:
        for tag, (query, bus, _) in enumerate(stimulus):
            stream.write(f"{tag} {len(bus)}\n")
            for head in range(6):
                stream.write(packed(query[head * dimension:(head + 1) * dimension]) + "\n")
            for format_, key, value, ks, vs in bus:
                stream.write(f"{format_} {key:x} {value:x} {ks:x} {vs:x}\n")
    rtl = [ROOT / "rtl" / name for name in (
        "anvil_q2_fp2_arithmetic.sv", "anvil_q2_fp2_nonlinear.sv",
        "anvil_q2_fp2_coefficients.sv", "anvil_q2_fp2_mx_decode.sv",
        "anvil_q2_fp2_flash_attn.sv",
    )]
    output = simulate(probe, source, rtl, simulator, [f"+INPUT={inputs.relative_to(ROOT)}"])
    seen = set()
    summary = None
    with output.open() as stream:
        for line in stream:
            words = line.split()
            if words[:1] == ["SUMMARY"]:
                summary = tuple(map(int, words[1:]))
            if words[:1] != ["RESULT"]:
                continue
            tag, head, data, error, cycles = (int(words[1]), int(words[2]), int(words[3], 16),
                                             int(words[4]), int(words[5]))
            if (tag, head) in seen or not 0 <= tag < len(stimulus) or not 0 <= head < 6:
                raise AssertionError(f"duplicate/out-of-range attention observation {tag} {head}")
            seen.add((tag, head))
            probe.compare("attention-error", 0, error, {"tag": tag, "head": head})
            query, bus, expected = stimulus[tag]
            probe.compare("attention-cycle-bound", True,
                          cycles <= (512 + 64 * dimension) * len(bus) + 64 * dimension, {"tag": tag})
            for local_component, reference in enumerate(expected[head * dimension:(head + 1) * dimension]):
                component = head * dimension + local_component
                actual = (data >> (32 * local_component)) & 0xFFFFFFFF
                difference = abs(exact(reference) - exact(actual)) if finite(actual) else None
                limit = Fraction(1, 100000) + Fraction(1, 10000) * abs(exact(reference))
                probe.compare(
                    "stable-softmax-bound", True, difference is not None and difference <= limit,
                    {"tag": tag, "component": component, "reference": f"{reference:08x}",
                     "observed": f"{actual:08x}",
                     "absolute_error": float(difference) if difference is not None else None,
                     "threshold": float(limit)},
                )
    expected_kv = sum(len(bus) for _, bus, _ in stimulus)
    probe.compare("summary", (len(stimulus), expected_kv), summary, {})
    probe.compare("attention-head-result-count", 6 * len(stimulus), len(seen), {})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compact", action="store_true")
    parser.add_argument("--simulator", choices=("iverilog", "verilator"), default="verilator")
    parser.add_argument("--head-dim", type=int, choices=(8, 128), default=8)
    parser.add_argument("--tile", type=int, choices=(1, 3), default=3)
    parser.add_argument("--repair-of")
    args = parser.parse_args()
    if args.simulator == "iverilog":
        args.compact = True
        args.head_dim = 8
    probe = Probe("attention", args.repair_of)
    try:
        run(probe, args.compact, args.simulator, args.head_dim, args.tile)
        return probe.settle()
    except Exception as error:
        return probe.settle(f"{type(error).__name__}: {error}")


if __name__ == "__main__":
    raise SystemExit(main())
