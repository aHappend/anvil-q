"""Bank-independent exact accumulation and metadata tests at the tensor pins."""

import random

from leaf import packed
from model import PRODUCTION, half_scale, mac


TENSOR_TB = r"""
module verify_tensor;
  localparam B=@BANKS@, ROWS=@ROWS@, N=@N@, RESULTS=@RESULTS@, PACKET_BITS=1072;
  reg clk=0; always #5 clk=~clk;
  reg rst_n=0, flush=0;
  reg [B-1:0] operand_valid=0, result_ready=0;
  wire [B-1:0] operand_ready, result_valid;
  reg [B*64-1:0] operand_q=0, operand_z=0;
  reg [B*256-1:0] operand_scale=0;
  reg [B*512-1:0] operand_activation=0;
  reg [B*16-1:0] operand_mask=0;
  reg [B*160-1:0] operand_meta=0;
  wire [B*128-1:0] result_sum;
  wire [B*160-1:0] result_meta;
  wire idle, fault;
  anvil_q3_ht_tensor_array #(.BANKS(B),.TILE_ROWS(ROWS)) dut(.*);
  reg [B*PACKET_BITS-1:0] vectors [0:N-1];
  reg [B*288-1:0] expected [0:RESULTS-1];
  integer input_index [0:B-1], output_index [0:B-1];
  reg [B-1:0] blocked=0, held_valid=0;
  reg [B*288-1:0] held_results=0;
  integer cycle=0, compared=0, input_stalls=0, output_stalls=0;
  integer bank, total, lane;
  reg [31:0] rng=@SEED@;
  function automatic [31:0] next_random(input [31:0] x);
    reg [31:0] y;
    begin y=x^(x<<13); y=y^(y>>17); next_random=y^(y<<5); end
  endfunction
  task reset_check;
    begin
      if ({operand_ready,result_valid,result_sum,result_meta,idle,fault}
          !== (B*290+2)'(0)) $fatal(1,"TENSOR_RESET_XZ");
    end
  endtask
  always @(posedge clk) begin
    cycle=cycle+1;
    if (!rst_n) reset_check();
    else if (!flush) begin
      if (cycle>1000000) $fatal(1,"TENSOR_PROGRESS");
      if (fault !== 0) $fatal(1,"TENSOR_UNEXPECTED_FAULT cycle=%0d",cycle);
      for (bank=0;bank<B;bank=bank+1) begin
        if (held_valid[bank] &&
            {result_valid[bank],result_meta[bank*160+:160],result_sum[bank*128+:128]}
            !== {1'b1,held_results[bank*288+:288]})
          $fatal(1,"TENSOR_RESULT_STABILITY bank=%0d",bank);
        held_valid[bank]=result_valid[bank] && !result_ready[bank];
        held_results[bank*288+:288]={result_meta[bank*160+:160],result_sum[bank*128+:128]};
        if (held_valid[bank]) output_stalls=output_stalls+1;
        if (result_valid[bank] && result_ready[bank]) begin
          if (output_index[bank]>=RESULTS ||
              {result_meta[bank*160+:160],result_sum[bank*128+:128]}
              !== expected[output_index[bank]][bank*288+:288])
            $fatal(1,"TENSOR_EXACT_ROW bank=%0d index=%0d meta=%h sum=%0d expected=%h",
                   bank,output_index[bank],result_meta[bank*160+:160],
                   $signed(result_sum[bank*128+:128]),
                   expected[output_index[bank]][bank*288+:288]);
          output_index[bank]=output_index[bank]+1; compared=compared+1;
        end
        if (!result_valid[bank] &&
            {result_meta[bank*160+:160],result_sum[bank*128+:128]} !== 288'd0)
          $fatal(1,"TENSOR_INVALID_PAYLOAD");
        blocked[bank]=operand_valid[bank] && !operand_ready[bank];
        if (blocked[bank]) input_stalls=input_stalls+1;
        if (operand_valid[bank] && operand_ready[bank])
          input_index[bank]=input_index[bank]+1;
      end
    end
  end
  always @(negedge clk) begin
    if (!rst_n) reset_check();
    else if (!flush) begin
      for (integer b=0;b<B;b=b+1) begin
        rng=next_random(rng);
        result_ready[b]=(rng[2:0]>=2);
        if (!blocked[b]) begin
          operand_valid[b]=input_index[b]<N && rng[5:3]!=0;
          if (input_index[b]<N) begin
            {operand_meta[b*160+:160],operand_mask[b*16+:16],
             operand_activation[b*512+:512],operand_scale[b*256+:256],
             operand_z[b*64+:64],operand_q[b*64+:64]}
              =vectors[input_index[b]][b*PACKET_BITS+:PACKET_BITS];
          end
        end
      end
    end
  end
  initial begin
    $readmemh("@VECTORS@",vectors);
    $readmemh("@EXPECTED@",expected);
    for (integer b=0;b<B;b=b+1) begin input_index[b]=0; output_index[b]=0; end
    #1; reset_check();
    repeat(3) @(negedge clk);
    rst_n=1;
    begin: completion
      forever begin
        @(posedge clk); #1;
        total=0;
        for (integer b=0;b<B;b=b+1) total=total+output_index[b];
        if (total==B*RESULTS) disable completion;
      end
    end
    if (!idle || compared!=B*RESULTS || input_stalls==0 || output_stalls==0)
      $fatal(1,"TENSOR_COVERAGE");
    for (integer b=0;b<B;b=b+1)
      if (input_index[b]!=N) $fatal(1,"TENSOR_INPUT_COUNT");
    $display("TENSOR_PASS banks=%0d rows=%0d seed=@SEED@ layers=36 projections=7 compared=%0d input_stalls=%0d output_stalls=%0d",
             B,ROWS,compared,input_stalls,output_stalls);
    $finish;
  end
endmodule
"""


def tensor_bench(directory, relative, seed, banks=16, rows=8):
    directory = directory / "checkpoint-images"
    directory.mkdir(exist_ok=True)
    rng = random.Random(seed)
    vector_path = directory / f"tensor-b{banks}-r{rows}-s{seed}-vectors.hex"
    expected_path = directory / f"tensor-b{banks}-r{rows}-s{seed}-expected.hex"
    # Two distinct K packets per context require exact, unrounded accumulation.
    with vector_path.open("w") as vectors, expected_path.open("w") as expected:
        for layer in range(36):
            for projection in range(7):
                sums = [[0] * banks for _ in range(rows)]
                metas = [[0] * banks for _ in range(rows)]
                for tile in range(2):
                    for row in range(rows):
                        packets = []
                        for bank in range(banks):
                            q = [rng.randrange(16) for _ in range(16)]
                            z = [rng.randrange(16) for _ in range(16)]
                            scales = [rng.choice((0, 1, 0x80, 0x81, 0x3C00, 0x7BFF))
                                      for _ in range(16)]
                            activations = [rng.randrange(-(1 << 31), 1 << 31)
                                           for _ in range(16)]
                            mask = 0xFFFF if tile == 0 else (1 << (1 + layer % 16)) - 1
                            meta = (seed | (layer << 32) | (projection << 64)
                                    | ((row * banks + bank) << 67) | ((tile * 16) << 99)
                                    | (row << 131) | (int(tile == 0) << 134)
                                    | (int(tile == 1) << 135))
                            sums[row][bank] += mac(q, z, scales, activations, mask)
                            metas[row][bank] = meta
                            fields = ((packed(q, 4), 64), (packed(z, 4), 64),
                                      (packed(scales, 16), 256), (packed(activations, 32), 512),
                                      (mask, 16), (meta, 160))
                            value, offset = 0, 0
                            for field, bits in fields:
                                value |= field << offset
                                offset += bits
                            packets.append(value)
                        vectors.write(f"{packed(packets, 1072):0{banks * 1072 // 4}x}\n")
                for row in range(rows):
                    results = [((sums[row][bank] & ((1 << 128) - 1))
                                | (metas[row][bank] << 128)) for bank in range(banks)]
                    expected.write(f"{packed(results, 288):0{banks * 288 // 4}x}\n")
    bench = TENSOR_TB
    replacements = dict(BANKS=banks, ROWS=rows, SEED=seed, N=36 * 7 * rows * 2,
                        RESULTS=36 * 7 * rows, VECTORS=relative(vector_path),
                        EXPECTED=relative(expected_path))
    for key, value in replacements.items():
        bench = bench.replace(f"@{key}@", str(value))
    return bench


PRODUCTION_PACKETS = r"""
  function automatic [1071:0] packet_at(input integer index, bank_id);
    integer layer_id, offset, projection, packet, inputs, outputs, row_id, source, l;
    reg [63:0] qword, zword;
    reg [255:0] scales;
    reg [511:0] activations;
    reg [159:0] meta;
    reg [31:0] activation;
    begin
      layer_id=index/1456; offset=index%1456;
      projection=offset<768 ? offset/128 : 6;
      packet=offset<768 ? offset%128 : offset-768;
      inputs=projection==6 ? 11008 : 2048;
      outputs=projection==1 || projection==2 ? 256 :
        projection==4 || projection==5 ? 11008 : 2048;
      row_id=bank_id==15 ? outputs-1 : bank_id;
      for (l=0;l<16;l=l+1) begin
        source=packet*16+l;
        qword[l*4+:4]=4'(source*3+row_id+layer_id+@SEED@);
        zword[l*4+:4]=4'((source/128)*5+row_id*7+layer_id);
        case ((source/128+row_id)%4)
          0: scales[l*16+:16]=16'd0;
          1: scales[l*16+:16]=16'h0080;
          2: scales[l*16+:16]=16'h1400;
          3: scales[l*16+:16]=16'h3c00;
        endcase
        activation=source==0 ? 32'h80000000 : source==1 ? 32'h7fffffff :
          32'(source+1)*32'd1664525+32'(@SEED@)*32'd1013904223;
        activations[l*32+:32]=activation;
      end
      meta=160'(@SEED@)|(160'(layer_id)<<32)|(160'(projection)<<64)|
        (160'(row_id)<<67)|(160'(packet*16)<<99)|(160'(packet==0)<<134)|
        (160'(packet*16+16==inputs)<<135);
      packet_at={meta,16'hffff,activations,scales,zword,qword};
    end
  endfunction
"""


def production_tensor_bench(directory, relative, seed):
    """Full K dots for all production shapes/layers and first/last output rows.

    Generate stimulus at the pins instead of retaining a multi-hundred-MB tensor
    dump. Only the independent exact expected sums are retained.
    """
    g = PRODUCTION
    activations = []
    for source in range(g.intermediate):
        raw = ((source + 1) * 1664525 + seed * 1013904223) & 0xFFFFFFFF
        value = raw - (1 << 32) if raw & (1 << 31) else raw
        activations.append(-(1 << 31) if source == 0 else
                           (1 << 31) - 1 if source == 1 else value)
    scales = [half_scale(bits) for bits in (0, 0x80, 0x1400, 0x3C00)]
    expected_path = directory / "checkpoint-images" / f"production-tensor-s{seed}-expected.hex"
    expected_path.parent.mkdir(exist_ok=True)
    comparisons = 0
    with expected_path.open("w") as stream:
        for layer in range(g.layers):
            for projection, (n, m) in enumerate(g.shapes):
                results = []
                for bank in range(16):
                    row = m - 1 if bank == 15 else bank
                    total = sum(
                        (((source * 3 + row + layer + seed) & 15)
                         - (((source // g.group) * 5 + row * 7 + layer) & 15))
                        * scales[(source // g.group + row) % 4] * activations[source]
                        for source in range(n))
                    meta = (seed | (layer << 32) | (projection << 64)
                            | (row << 67) | ((n - 16) << 99) | (1 << 135))
                    results.append((meta << 128) | (total & ((1 << 128) - 1)))
                    comparisons += 1
                stream.write(f"{packed(results, 288):01152x}\n")
    bench = TENSOR_TB.replace("  reg [B*PACKET_BITS-1:0] vectors [0:N-1];", PRODUCTION_PACKETS)
    bench = bench.replace('    $readmemh("@VECTORS@",vectors);\n', "")
    bench = bench.replace("vectors[input_index[b]][b*PACKET_BITS+:PACKET_BITS]",
                          "packet_at(input_index[b],b)")
    bench = bench.replace("cycle>1000000", "cycle>20000000")
    bench = bench.replace("TENSOR_PASS banks=", "PRODUCTION_TENSOR_PASS banks=")
    for key, value in dict(BANKS=16, ROWS=1, N=52416, RESULTS=252,
                           EXPECTED=relative(expected_path), SEED=seed).items():
        bench = bench.replace(f"@{key}@", str(value))
    if comparisons != 4032:
        raise AssertionError("all seven production shapes and 36 layers must be compared")
    return bench
