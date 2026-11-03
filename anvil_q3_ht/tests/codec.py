"""KV record tests derived from the signed quantization ABI, not RTL state."""

import json
import random

from model import decode_kv, encode_kv
from leaf import packed


CODEC_TB = r"""
module verify_codec;
  localparam MODE=@MODE@, CAP=@CAP@, N=@N@;
  reg clk=0; always #5 clk=~clk;
  reg rst_n=0, flush=0, in_valid=0, decode=0, out_ready=0;
  reg [6:0] count=0;
  reg [CAP*32-1:0] values_in=0;
  reg [511:0] record_in=0;
  wire in_ready, out_valid, out_error;
  wire [CAP*32-1:0] values_out;
  wire [511:0] record_out;
  anvil_q3_ht_kv_codec #(.CACHE_MODE(MODE)) dut(.*);
  reg [CAP*32-1:0] source_values [0:N-1], expected_values [0:N-1];
  reg [511:0] source_record [0:N-1], expected_record [0:N-1];
  reg [8:0] control [0:N-1];
  integer i, cycle=0, compared=0, rejected=0, encoded=0, decoded=0, stalled=0;
  integer accepted_at, delay_count;
  reg [CAP*32+512:0] held_output;
  task reset_check;
    begin
      if ({in_ready,out_valid,out_error,values_out,record_out} !== (CAP*32+515)'(0))
        $fatal(1,"KV_CODEC_RESET_XZ");
    end
  endtask
  always @(posedge clk) begin
    cycle=cycle+1;
    if (!rst_n) reset_check();
    else if (!out_valid && {out_error,values_out,record_out} !== (CAP*32+513)'(0))
      $fatal(1,"KV_CODEC_INVALID_PAYLOAD");
  end
  always @(negedge clk) if (!rst_n) reset_check();
  initial begin
    $readmemh("@SOURCE_VALUES@",source_values);
    $readmemh("@SOURCE_RECORD@",source_record);
    $readmemh("@EXPECTED_VALUES@",expected_values);
    $readmemh("@EXPECTED_RECORD@",expected_record);
    $readmemh("@CONTROL@",control);
    #1; reset_check();
    repeat(3) @(negedge clk);
    rst_n=1;
    // Cancel a real accepted operation before it can complete.
    @(negedge clk); in_valid=1; count=CAP; values_in={CAP{32'h7fffffff}};
    @(posedge clk); if (in_ready !== 1) $fatal(1,"KV_CODEC_FLUSH_SETUP");
    @(negedge clk); in_valid=0; flush=1;
    @(posedge clk);
    @(negedge clk); flush=0;
    repeat(180) begin
      @(posedge clk);
      if (out_valid !== 0) $fatal(1,"KV_CODEC_STALE_FLUSH");
    end
    for (i=0;i<N;i=i+1) begin
      @(negedge clk);
      in_valid=1; decode=control[i][8]; count=control[i][6:0];
      values_in=source_values[i]; record_in=source_record[i];
      @(posedge clk); while (!in_ready) @(posedge clk);
      accepted_at=cycle;
      if (out_valid !== 0) $fatal(1,"KV_CODEC_SAME_EDGE_RESULT");
      @(negedge clk); in_valid=0;
      @(posedge clk);
      while (!out_valid) begin
        if (cycle-accepted_at>512) $fatal(1,"KV_CODEC_COMPLETION_BOUND");
        @(posedge clk);
      end
      if (out_error !== control[i][7] || record_out !== expected_record[i] ||
          values_out !== expected_values[i])
        $fatal(1,"KV_CODEC_NUMERICAL mode=%0d case=%0d decode=%b error=%b expected_error=%b actual_record=%h expected_record=%h actual_values=%h expected_values=%h",
               MODE,i,decode,out_error,control[i][7],record_out,expected_record[i],
               values_out,expected_values[i]);
      held_output={out_error,values_out,record_out};
      for (delay_count=0;delay_count<1+i%4;delay_count=delay_count+1) begin
        @(posedge clk);
        if (out_valid !== 1 || {out_error,values_out,record_out} !== held_output)
          $fatal(1,"KV_CODEC_RESULT_STABILITY");
        stalled=stalled+1;
      end
      @(negedge clk); out_ready=1;
      @(posedge clk);
      compared=compared+1;
      if (out_error) rejected=rejected+1;
      else if (decode) decoded=decoded+1;
      else encoded=encoded+1;
      @(negedge clk); out_ready=0;
    end
    if (compared!=N || rejected==0 || encoded==0 || decoded==0 || stalled==0)
      $fatal(1,"KV_CODEC_COVERAGE");
    $display("CODEC_PASS mode=%0d compared=%0d encoded=%0d decoded=%0d rejected=%0d stalled=%0d",
             MODE,compared,encoded,decoded,rejected,stalled);
    $finish;
  end
endmodule
"""


def codec_vectors(mode, seeds=(17, 89, 101)):
    cap = (16, 32, 64)[mode]
    vectors = []

    def add(decode, values=(), record=bytes(64), count=None, seed=None, category=None):
        count = len(values) if count is None else count
        error = False
        try:
            if decode:
                reconstructed = decode_kv(record, count, mode)
                expected_record = record
            else:
                expected_record = encode_kv(values, mode)
                reconstructed = []
        except ValueError:
            reconstructed, expected_record, error = [], bytes(64), True
        vectors.append(dict(
            source_values=packed(values, 32), source_record=int.from_bytes(record, "little"),
            expected_values=packed(reconstructed, 32),
            expected_record=int.from_bytes(expected_record, "little"),
            control=(int(decode) << 8) | (int(error) << 7) | count,
            seed=seed, category=category))

    for seed in seeds:
        rng = random.Random(seed)
        if mode:
            limit, maximum = (127, 25) if mode == 1 else (7, 29)
            for exponent in range(1, maximum + 1):
                half_step = 1 << (exponent - 1)
                values = [min((1 << 31) - 1, limit << exponent), half_step, -half_step]
                record = encode_kv(values, mode)
                if int.from_bytes(record[32:36], "little") != exponent:
                    raise AssertionError("independent exponent boundary construction")
                reconstructed = decode_kv(record, len(values), mode)
                if reconstructed[1:] != [1 << exponent, -(1 << exponent)]:
                    raise AssertionError("independent signed half-tie construction")
                add(False, values, seed=seed, category="positive_negative_half_ties")
                add(True, record=record, count=len(values), seed=seed,
                    category="positive_negative_half_ties")
        for index in range(256):
            length = (1, cap - 1, cap)[index % 3]
            values = [rng.randrange(-(1 << 31), 1 << 31) for _ in range(length)]
            if index < 32:
                boundaries = (0, 1, -1, 127, -127, 128, -128, 7, -7, 8, -8,
                              32768, -32768, (1 << 31) - 1, -(1 << 31))
                values = [boundaries[(index + lane) % len(boundaries)]
                          for lane in range(length)]
            if index == 32:
                values = [0] * length
            record = encode_kv(values, mode)
            reconstructed = decode_kv(record, length, mode)
            if mode:
                exponent = int.from_bytes(record[32:36], "little")
                bound = 0 if exponent == 0 else 1 << (exponent - 1)
                if any(abs(a - b) > bound for a, b in zip(values, reconstructed)):
                    raise AssertionError("independent quantization error bound")
            elif values != reconstructed:
                raise AssertionError("independent lossless codec")
            add(False, values, seed=seed, category="encode")
            add(True, record=record, count=length, seed=seed, category="decode")
        add(True, count=0, seed=seed, category="zero_count")
        add(True, count=cap + 1, seed=seed, category="oversize_count")
        bad = bytearray(64)
        bad[(cap - 1) * (4 if mode == 0 else 1 if mode == 1 else 0)] = 1
        if mode == 2:
            bad = bytearray(64)
            bad[31] = 0x10
        add(True, record=bytes(bad), count=1, seed=seed, category="unused_lane")
        if mode:
            for byte, value, category in ((0, 128 if mode == 1 else 8, "reserved_code"),
                                          (32, 26 if mode == 1 else 30, "bad_exponent"),
                                          (33, 1, "header_upper_bits"),
                                          (63, 1, "padding"),
                                          (32, 1, "noncanonical_zero")):
                bad = bytearray(64)
                bad[byte] = value
                add(True, record=bytes(bad), count=cap, seed=seed, category=category)
    return vectors


def codec_bench(directory, relative, mode):
    cap = (16, 32, 64)[mode]
    vectors = codec_vectors(mode)
    (directory / f"codec-m{mode}-cases.json").write_text(json.dumps(
        [dict(index=index, seed=vector["seed"], category=vector["category"],
              expected_error=bool(vector["control"] & 128))
         for index, vector in enumerate(vectors)], indent=2) + "\n")
    bench = CODEC_TB.replace("@MODE@", str(mode)).replace("@CAP@", str(cap))
    bench = bench.replace("@N@", str(len(vectors)))
    widths = dict(source_values=cap * 32, expected_values=cap * 32,
                  source_record=512, expected_record=512, control=9)
    for name, width in widths.items():
        path = directory / f"codec-m{mode}-{name}.hex"
        path.write_text("".join(f"{v[name]:0{(width + 3) // 4}x}\n" for v in vectors))
        bench = bench.replace(f"@{name.upper()}@", relative(path))
    return bench
