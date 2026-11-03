"""Nonzero seven-projection Qwen graph oracle, independent of RTL state/control."""

import argparse
from fractions import Fraction
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fp2_probe import Probe, ROOT
from fp2_reference import add, exact, mx_decode, mx_encode_group, rms, rope, rope_coefficients
from fp2_reference import rounded, swiglu, tensor
from fp2_attention_probe import attention_reference
from fp2_top_probe import TOP_TB, embedding, run as run_top


GRAPH_FUNCTIONS = r"""
  reg [31:0] graph_coefficients[0:23],graph_scan;
  string graph_path;
  function automatic [15:0] graph_weight(
    input [2:0] projection, input integer row,column
  );
    begin
      graph_weight=0;
      case(projection)
        0,1,3: if(row==column) graph_weight=16'h3d80;
        2: if(row==column) graph_weight=16'h3e00;
        4: if(row%48==column) graph_weight=16'h3d80;
        5: if(row%48==column) graph_weight=16'h3e00;
        6: begin
          if(row==column) graph_weight=16'h3e00;
          else if(row+48==column) graph_weight=16'h3d80;
        end
      endcase
    end
  endfunction
  function automatic [7:0] graph_scale(
    input [2:0] projection, input integer row,group_index
  );
    reg [15:0] maximum,weight;
    integer k;
    begin
      maximum=0;
      for(k=0;k<32;k=k+1) begin
        weight=graph_weight(projection,row,group_index*32+k);
        if(group_index*32+k>=((projection==6) ? 64 : 48)) weight=0;
        if(weight>maximum) maximum=weight;
      end
      graph_scale=(maximum==0) ? 127 : ((maximum==16'h3e00) ? 116 : 115);
    end
  endfunction
  function automatic [7:0] graph_payload(
    input [2:0] projection, input integer row,column
  );
    reg [15:0] weight;
    reg [7:0] scale;
    begin
      weight=graph_weight(projection,row,column);
      scale=graph_scale(projection,row,column/32);
      graph_payload=(weight==0) ? 0 :
        ((weight==16'h3d80 && scale==116) ? 8'h70 : 8'h78);
    end
  endfunction
  function automatic [15:0] graph_bias(input integer column);
    reg [15:0] value;
    begin
      case(column%4)
        0: value=16'h3b80;
        1: value=16'h3c00;
        2: value=16'h3c40;
        3: value=16'h3c80;
      endcase
      graph_bias=column[0] ? value|16'h8000 : value;
    end
  endfunction
"""


def graph_tb():
    text = TOP_TB.replace("  function automatic [511:0] read_beat(", GRAPH_FUNCTIONS +
                          "\n  function automatic [511:0] read_beat(")
    text = text.replace("        1,4: data=0;\n        3: data={64{8'h7f}};", r"""
        1: begin
          if(format==2) begin
            for(element=0;element<64;element=element+1)
              if(column+element<((ddr_req_proj==6) ? 64 : 48))
                data[8*element+:8]=graph_payload(ddr_req_proj,row,column+element);
          end else begin
            for(element=0;element<32;element=element+1)
              if(column+element<((ddr_req_proj==6) ? 64 : 48))
                data[16*element+:16]=graph_weight(ddr_req_proj,row,column+element);
          end
        end
        3: for(element=0;element<64;element=element+1)
          if(column+element<2)
            data[8*element+:8]=graph_scale(ddr_req_proj,row,column+element);
        4: for(element=0;element<32;element=element+1)
          if(column+element<((ddr_req_proj==0) ? 48 : 8))
            data[16*element+:16]=graph_bias(column+element);
""")
    text = text.replace(
        "data[32*element+:32]=((column+element)&1) ? 32'd0 : 32'h3f800000;",
        "if(row<3 && column+element<8)\n"
        "            data[32*element+:32]=graph_coefficients[row*8+column+element];")
    anchor = "    $fclose(fd);\n    if(!$value$plusargs(\"COMMANDS=%s\",command_path))"
    replacement = r"""
    $fclose(fd);
    if(!$value$plusargs("GRAPH_COEFFICIENTS=%s",graph_path)) $fatal(1,"missing GRAPH_COEFFICIENTS");
    fd=$fopen(graph_path,"r"); if(!fd) $fatal(1,"graph coefficients open");
    for(i=0;i<24;i=i+1) begin
      n=$fscanf(fd,"%h\n",graph_scan); if(n!=1) $fatal(1,"graph coefficient length");
      graph_coefficients[i]=graph_scan;
    end
    $fclose(fd);
    if(!$value$plusargs("COMMANDS=%s",command_path))"""
    if text.count(anchor) != 1:
        raise ValueError("top transactor fixture anchor changed")
    return text.replace(anchor, replacement)


def projection_weight(projection, row, column):
    if projection in (0, 1, 3):
        value = Fraction(1, 16) if row == column else 0
    elif projection == 2:
        value = Fraction(1, 8) if row == column else 0
    elif projection in (4, 5):
        value = Fraction(1, 16 if projection == 4 else 8) if row % 48 == column else 0
    elif projection == 6:
        value = Fraction(1, 8) if row == column else (Fraction(1, 16) if row + 48 == column else 0)
    else:
        raise ValueError("unknown logical projection")
    return rounded(value, fraction_bits=7)


def projection_bias(row):
    return rounded(Fraction((row % 4 + 1) * (-1 if row & 1 else 1), 256), fraction_bits=7)


def bf16(value):
    return rounded(exact(value), fraction_bits=7, negative_zero=bool(value >> 31))


def gemv(projection, activation):
    outputs = (48, 8, 8, 48, 64, 64, 48)[projection]
    result = []
    for row in range(outputs):
        weights = [projection_weight(projection, row, column) for column in range(len(activation))]
        value, failed = tensor(activation + [0] * (128 - len(activation)),
                               weights + [0] * (128 - len(weights)),
                               (1 << len(activation)) - 1)
        if failed:
            raise ArithmeticError("finite graph fixture produced a nonfinite GEMV")
        if projection < 3:
            value = add(value, projection_bias(row) << 16)
        result.append(value)
    return result


def normalized(x):
    return [bf16(value) for value in rms(x, [0x3F800000] * len(x))]


def rotate(values, position):
    result = []
    for first in range(0, len(values), 8):
        head = [0] * 8
        for pair in range(4):
            cosine, sine = rope_coefficients(position, pair, 8)
            x, y = rope(values[first + pair], values[first + pair + 4], cosine, sine)
            head[pair], head[pair + 4] = bf16(x), bf16(y)
        result.extend(head)
    return result


def cache_codec(values, mode):
    if mode == 0:
        return values
    encoded, scale = mx_encode_group(values + [0] * (32 - len(values)),
                                     (1 << len(values)) - 1)
    result = []
    for code in encoded[:len(values)]:
        value, failed = mx_decode(code, scale)
        if failed:
            raise ArithmeticError("finite graph cache reconstruction overflow")
        result.append(value)
    return result


def graph_reference(commands, cache_mode):
    keys, values = [], []
    logits = []
    for token, position, new_sequence, phase in commands:
        if new_sequence:
            keys, values = [], []
        x = [embedding(token, column) << 16 for column in range(48)]
        hidden = normalized(x)
        queries = rotate(gemv(0, hidden), position)
        key = cache_codec(rotate(gemv(1, hidden), position), cache_mode)
        value = cache_codec([bf16(element) for element in gemv(2, hidden)], cache_mode)
        if position != len(keys):
            raise ValueError("graph fixture requires contiguous causal cache")
        keys.append(key)
        values.append(value)
        attention = [bf16(element) for element in attention_reference(queries, keys, values, 8)]
        x = [add(residual, output) for residual, output in zip(x, gemv(3, attention), strict=True)]
        hidden = normalized(x)
        gate, up = gemv(4, hidden), gemv(5, hidden)
        intermediate = [bf16(swiglu(a, b)) for a, b in zip(gate, up, strict=True)]
        x = [add(residual, output) for residual, output in zip(x, gemv(6, intermediate), strict=True)]
        hidden = normalized(x)
        token_logits = []
        for row in range(16):
            value, failed = tensor(hidden + [0] * 80,
                                   [embedding(row, column) for column in range(48)] + [0] * 80,
                                   (1 << 48) - 1)
            if failed:
                raise ArithmeticError("finite graph fixture produced nonfinite logits")
            token_logits.append(value)
        logits.append(token_logits)
    return logits


def run(probe, commands=None, seed=17, weight_mode=0, cache_mode=0):
    commands = commands or [(3, 0, 1, 0), (5, 1, 0, 0), (7, 2, 0, 1),
                            (4, 0, 1, 0), (8, 1, 0, 1)]
    coefficients = probe.directory / "rope.hex"
    coefficients.write_text("".join(f"{value:08x}\n"
                                   for position in range(3) for pair in range(4)
                                   for value in rope_coefficients(position, pair, 8)))
    reference = graph_reference(commands, cache_mode)
    run_top(probe, "verilator", commands, seed, weight_mode, cache_mode,
            tb_template=graph_tb(), expected_results=reference,
            extra_arguments=[f"+GRAPH_COEFFICIENTS={coefficients.relative_to(ROOT)}"])
    probe.summary["fixture"] = {
        "geometry": [1, 48, 64, 6, 1, 8, 16, 3],
        "nonzero_projections": list(range(7)), "nonzero_qkv_biases": True,
        "rope_theta": 1000000, "official_checkpoint_data": False,
        "weight_quantization": "all nonzero fixture weights exactly MX-representable",
        "oracle": "independent FP32 graph ordering and high-precision stable causal softmax",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, choices=(17, 89, 203), default=17)
    parser.add_argument("--weight-mode", type=int, choices=(0, 2), default=0)
    parser.add_argument("--cache-mode", type=int, choices=(0, 2), default=0)
    args = parser.parse_args()
    probe = Probe("graph")
    try:
        run(probe, seed=args.seed, weight_mode=args.weight_mode, cache_mode=args.cache_mode)
        return probe.settle()
    except Exception as error:
        return probe.settle(f"{type(error).__name__}: {error}")


if __name__ == "__main__":
    raise SystemExit(main())
