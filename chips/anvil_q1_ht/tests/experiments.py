"""Embedded, public-pin experiments and independent expected-vector generation."""

import hashlib
import json
import math
import random
import re
import shutil

from reference import (AWQ_SHIFTS, EngineeringModel, MATRIX, bf16, fp_q16, norm, silu,
                       round_div, round_shift, sat32, signed, trunc_div)


def hx(value, bits):
    return f"{bits}'h{value & ((1 << bits) - 1):0{(bits + 3) // 4}x}"


def packed(values, bits):
    return sum((value & ((1 << bits) - 1)) << (bits * index)
               for index, value in enumerate(values))


def fixture_integrity(evidence):
    from fixtures import hashes
    root = evidence.folder.parents[2] / "fixtures/qwen2.5-0.5b"
    evidence.command(["python3", "tests/fixtures.py"], "real-fixture-validation")
    original = json.loads((root / "manifest.json").read_text())
    for rewrite_manifest in (False, True):
        folder = evidence.folder / ("fixture-tampered" if rewrite_manifest else "fixture-corrupt")
        (folder / "awq").mkdir(parents=True)
        config = folder / "awq/config.json"
        shutil.copyfile(root / "awq/config.json", config)
        config.write_bytes(config.read_bytes() + b"\n")
        manifest = json.loads(json.dumps(original))
        if rewrite_manifest:
            manifest["models"]["AWQ"]["files"]["config.json"] = hashes(config)
        (folder / "manifest.json").write_text(json.dumps(manifest))
        text = evidence.command(
            ["python3", "tests/fixtures.py", "--root", evidence.relative(folder)],
            folder.name, expected_codes=(1,))
        expected = ("checkpoint manifest SHA-256 differs from pinned input"
                    if rewrite_manifest else "checkpoint input mismatch")
        if expected not in text:
            raise AssertionError(f"fixture integrity rejected for the wrong reason: {text}")
        evidence.record["observations"].append({
            "scope": "real_checkpoint_input_integrity_not_RTL_acceptance",
            "case": folder.name, "data_corruption": True,
            "manifest_rewritten": rewrite_manifest, "expected_rejection": expected,
        })
        evidence.flush()


CLOCK = r"""
`timescale 1ns/1ps
`ifdef VERILATOR
`define RESET_DELTA
`else
`define RESET_DELTA #0;
`endif
module tb;
reg clk = 0;
always #5 clk = !clk;
reg rst_n;
task edge_tick;
  begin @(posedge clk); #0.001; end
endtask
"""


def tensor(evidence, seed):
    rng = random.Random(seed)
    dots = []
    for activation, weight in ((1, 32768), (-1, 32768), (1, 32767), (-1, 32767),
                               (1, 32769), (-1, 32769), (-(1 << 31), -(1 << 36)),
                               ((1 << 31) - 1, (1 << 36) - 1)):
        dots.append(([(activation, [weight] * 64)], (1 << 64) - 1))
    dots.append(([(-(1 << 31), [(1 << 36) - 1] * 64),
                 (-(1 << 31), [-((1 << 36) - 1)] * 64)], (1 << 64) - 1))
    for index in range(70):
        mask = (1 << (index % 64 + 1)) - 1 if index < 64 else rng.getrandbits(64)
        beats = [(rng.randrange(-200000, 200001),
                  [rng.randrange(-1000000, 1000001) for _ in range(64)])
                 for _ in range(rng.choice((1, 2, 4, 9, 17)))]
        dots.append((beats, mask))
    calls = []
    for beats, mask in dots:
        sums = [sum(a * weights[lane] for a, weights in beats) for lane in range(64)]
        expected = [sat32(round_shift(total, 16)) if mask >> lane & 1 else 0
                    for lane, total in enumerate(sums)]
        for index, (activation, weights) in enumerate(beats):
            calls.append(f"feed({int(index == 0)}, {int(index == len(beats)-1)}, "
                         f"{hx(activation,32)}, {hx(packed(weights,37),2368)}, {hx(mask,64)});")
        calls.append(f"result({hx(packed(expected,32),2048)}, {hx(mask,64)});")
    extra_dots = []
    full_mask = (1 << 64) - 1
    for sign in (-1, 1):
        extra_dots.append(([(sign * ((1 << 31) - 1), [(1 << 36) - 1] * 64)] * 16,
                           full_mask, "wide_sum"))
        for residual in (32767, 32768, 32769, 65535, 65536, 65537):
            weights = [(1 << 36) - 1 - lane for lane in range(64)]
            beats = [((1 << 31) - 1, weights)] * 17
            beats += [(-((1 << 31) - 1), weights)] * 17
            beats += [(sign, [residual + lane * 65536 for lane in range(64)])]
            extra_dots.append((beats, full_mask, "wide_cancel"))
    for bit in (15, 16, 17, 18, 19, 30, 31):
        for sign in (-1, 1):
            activation = sign * ((1 << bit) - 1)
            for weight_bit in (17, 18, 19, 31, 32, 35, 36):
                weights = [((1 << weight_bit) - 1 - lane) * (-1 if lane & 1 else 1)
                           for lane in range(64)]
                extra_dots.append(([(activation, weights), (-activation, weights),
                                    (1, [32768 + lane * 65536 for lane in range(64)])],
                                   full_mask, "limb_boundary"))
    extra_dots.append(([(1, [65536] * 64)] * 4, 0, "zero_mask"))
    extra_path = evidence.folder / "tensor-boundary-vectors.hex"
    records = []
    bins = {name: 0 for name in ("wide_sum", "wide_cancel", "limb_boundary", "zero_mask")}
    for dot_index, (beats, mask, category) in enumerate(extra_dots):
        sums = [sum(a * weights[lane] for a, weights in beats) for lane in range(64)]
        expected = [sat32(round_shift(total, 16)) if mask >> lane & 1 else 0
                    for lane, total in enumerate(sums)]
        if category == "wide_sum" and not all(abs(total) >= 1 << 69 for total in sums):
            raise AssertionError("tensor wide-sum stimulus did not exceed product width")
        for index, (activation, weights) in enumerate(beats):
            gap = (0, 1, 2, 5, 11)[(dot_index + index) % 5]
            first, last = int(index == 0), int(index == len(beats) - 1)
            value = gap
            for field, width in ((first, 1), (last, 1), (activation & 0xffffffff, 32),
                                 (packed(weights, 37), 2368), (mask, 64),
                                 (packed(expected, 32) if last else 0, 2048)):
                value = (value << width) | field
            records.append(f"{value:01131x}\n")
        bins[category] += 1
    extra_path.write_text("".join(records))
    evidence.record.setdefault("runtime_input_sha256", {})[evidence.relative(extra_path)] = (
        hashlib.sha256(extra_path.read_bytes()).hexdigest())
    evidence.flush()
    bench = CLOCK + r"""
reg in_valid=0, in_first=0, in_last=0, out_ready=0;
reg signed [31:0] in_activation=0;
reg [2367:0] in_weight_q16=0;
reg [63:0] in_mask=0;
wire in_ready, out_valid, protocol_error;
wire [2047:0] out_data;
wire [63:0] out_mask;
integer compared=0, vectors=0, n, protocol_rejections=0, recovery_dots=0;
integer reset_aborts=0;
integer extra_index,extra_compared=0,bubble_edges=0,blocked_offers=0;
reg [4521:0] boundary_vectors [0:BOUNDARY_VECTOR_COUNT-1];
anvil_q1_ht_tensor_array product(
  .clk(clk),.rst_n(rst_n),.in_valid(in_valid),.in_ready(in_ready),
  .in_first(in_first),.in_last(in_last),.in_activation(in_activation),
  .in_weight_q16(in_weight_q16),.in_mask(in_mask),.out_valid(out_valid),
  .out_ready(out_ready),.out_data(out_data),.out_mask(out_mask),.protocol_error(protocol_error));
task reset_check;
  begin
    if ({in_ready,out_valid,out_data,out_mask,protocol_error} !== 2115'b0)
      $fatal(1,"TENSOR_RESET_XZ_OR_NONZERO time=%0t",$time);
  end
endtask
always @(posedge clk or negedge clk) if (!rst_n) reset_check();
task feed(input first_bit, last_bit, input [31:0] activation,
          input [2367:0] weights, input [63:0] mask);
  begin
    @(negedge clk);
    in_valid=1; in_first=first_bit; in_last=last_bit;
    in_activation=activation; in_weight_q16=weights; in_mask=mask;
    #0.001;
    if (in_ready !== 1) $fatal(1,"TENSOR_INPUT_II_OR_READINESS");
    edge_tick();
    if (out_valid !== 0 || protocol_error !== 0) $fatal(1,"TENSOR_EARLY_RESULT_OR_ERROR");
    vectors=vectors+1;
  end
endtask
task result(input [2047:0] expected, input [63:0] mask);
  integer latency, stall;
  begin
    @(negedge clk); in_valid=0;
    for (latency=1;latency<=10;latency=latency+1) begin
      edge_tick();
      if (in_ready !== 0) $fatal(1,"TENSOR_ACCEPTS_FOLLOWING_DOT");
      if (out_valid !== (latency==10)) $fatal(1,"TENSOR_LATENCY observed=%0d",latency);
    end
    if (out_data !== expected || out_mask !== mask || protocol_error !== 0)
      $fatal(1,"TENSOR_MISMATCH dot=%0d actual=%h expected=%h mask=%h",
             compared,out_data,expected,out_mask);
    for (stall=0;stall<7;stall=stall+1) begin
      @(negedge clk);
      in_valid=1; in_first=1; in_last=1;
      in_activation=32'h80000000; in_weight_q16={64{37'h1000000000}};
      in_mask=~mask;
      edge_tick();
      if (in_ready !== 0 || protocol_error !== 0 ||
          out_valid !== 1 || out_data !== expected || out_mask !== mask)
        $fatal(1,"TENSOR_STALL_CHANGED");
      blocked_offers=blocked_offers+1;
    end
    @(negedge clk); in_valid=0; out_ready=1;
    edge_tick();
    if (out_valid !== 0) $fatal(1,"TENSOR_RESULT_NOT_RETIRED");
    @(negedge clk); out_ready=0;
    compared=compared+1;
  end
endtask
task bubble(input integer count);
  integer gap;
  begin
    for(gap=0;gap<count;gap=gap+1) begin
      @(negedge clk); in_valid=0;
      in_first=1; in_last=1; in_activation=32'h7fffffff;
      in_weight_q16={64{37'h0fffffffff}}; in_mask=~in_mask;
      edge_tick();
      if(in_ready!==1 || out_valid!==0 || protocol_error!==0)
        $fatal(1,"TENSOR_INPUT_BUBBLE_CHANGED_PROTOCOL");
      bubble_edges=bubble_edges+1;
    end
  end
endtask
task rejected_dot(input integer violation);
  integer wait_edge;
  begin
    @(negedge clk); rst_n=0; in_valid=0; out_ready=0;
    edge_tick();
    @(negedge clk); rst_n=1;
    feed(1,0,32'd1,2368'd1,64'd3);
    @(negedge clk);
    in_valid=1; in_first=(violation!=0); in_last=(violation!=1);
    in_mask=(violation==0 ? 64'd1 : 64'd3);
    #0.001;
    if(in_ready !== 1) $fatal(1,"TENSOR_PROTOCOL_STIMULUS_NOT_ACCEPTED");
    edge_tick();
    if(protocol_error !== 1 || out_valid !== 0 || in_ready !== 0)
      $fatal(1,"TENSOR_PROTOCOL_VIOLATION_NOT_REJECTED case=%0d",violation);
    @(negedge clk); in_valid=0; out_ready=1;
    for(wait_edge=0;wait_edge<15;wait_edge=wait_edge+1) begin
      edge_tick();
      if(protocol_error !== 1 || out_valid !== 0 || in_ready !== 0)
        $fatal(1,"TENSOR_PROTOCOL_FAILURE_NOT_STICKY case=%0d",violation);
    end
    protocol_rejections=protocol_rejections+1;
    @(negedge clk); rst_n=0; out_ready=0;
    edge_tick();
    @(negedge clk); rst_n=1;
    feed(1,1,32'd65536,{64{37'd65536}},64'hffffffffffffffff);
    result({64{32'd65536}},64'hffffffffffffffff);
    recovery_dots=recovery_dots+1;
  end
endtask
task reset_abort(input integer phase);
  integer wait_edge;
  begin
    feed(1,phase!=0,32'd65536,{64{37'd65536}},64'hffffffffffffffff);
    @(negedge clk); in_valid=0;
    if(phase==0) begin
      if(in_ready !== 1 || out_valid !== 0 || protocol_error !== 0)
        $fatal(1,"TENSOR_OPEN_RESET_PRECONDITION");
    end else begin
      for(wait_edge=1;wait_edge<=(phase==1 ? 2 : 10);wait_edge=wait_edge+1) begin
        edge_tick();
        if(in_ready !== 0 || protocol_error !== 0 ||
           out_valid !== (wait_edge==10))
          $fatal(1,"TENSOR_RESET_PIPELINE_PRECONDITION phase=%0d",phase);
      end
      if(phase==2 && (out_data !== {64{32'd65536}} ||
                     out_mask !== 64'hffffffffffffffff || out_ready !== 0))
        $fatal(1,"TENSOR_STALLED_RESET_PRECONDITION");
    end
    @(negedge clk); #1; rst_n=0;
    #0.001; reset_check();
    repeat(3) edge_tick();
    @(negedge clk); rst_n=1;
    for(wait_edge=0;wait_edge<15;wait_edge=wait_edge+1) begin
      edge_tick();
      if(in_ready !== 1 || out_valid !== 0 || out_data !== 2048'b0 ||
         out_mask !== 64'b0 || protocol_error !== 0)
        $fatal(1,"TENSOR_RESET_GHOST_RESULT phase=%0d",phase);
    end
    feed(1,1,-32'sd65536,{64{37'd65536}},64'hffffffffffffffff);
    result({64{32'hffff0000}},64'hffffffffffffffff);
    reset_aborts=reset_aborts+1;
    recovery_dots=recovery_dots+1;
  end
endtask
initial begin
  rst_n=0; `RESET_DELTA reset_check();
  repeat (3) edge_tick();
  @(negedge clk); rst_n=1;
""" + "\n".join(calls) + r"""
  $readmemh("BOUNDARY_VECTOR_PATH",boundary_vectors);
  for(extra_index=0;extra_index<BOUNDARY_VECTOR_COUNT;extra_index=extra_index+1) begin
    bubble(boundary_vectors[extra_index][4521:4514]);
    feed(boundary_vectors[extra_index][4513],boundary_vectors[extra_index][4512],
         boundary_vectors[extra_index][4511:4480],boundary_vectors[extra_index][4479:2112],
         boundary_vectors[extra_index][2111:2048]);
    if(boundary_vectors[extra_index][4512]) begin
      result(boundary_vectors[extra_index][2047:0],boundary_vectors[extra_index][2111:2048]);
      extra_compared=extra_compared+1;
    end
  end
  if(extra_compared!=BOUNDARY_DOT_COUNT || bubble_edges==0 ||
     blocked_offers!=compared*7)
    $fatal(1,"TENSOR_BOUNDARY_COVERAGE_MISSING");
  @(negedge clk);
  in_valid=1;in_first=0;in_last=1;in_activation=1;in_weight_q16=1;in_mask=64'hffffffffffffffff;
  if (in_ready !== 1) $fatal(1,"TENSOR_ORDERING_STIMULUS_NOT_ACCEPTED");
  edge_tick();
  if (protocol_error !== 1 || out_valid !== 0 || in_ready !== 0)
    $fatal(1,"TENSOR_ORDERING_ERROR_NOT_STICKY");
  @(negedge clk); in_valid=0;
  repeat (15) begin
    edge_tick();
    if (protocol_error !== 1 || out_valid !== 0 || in_ready !== 0)
      $fatal(1,"TENSOR_ILLEGAL_SUCCESS");
  end
  protocol_rejections=protocol_rejections+1;
  rejected_dot(0);
  rejected_dot(1);
  rejected_dot(2);
  if(protocol_rejections!=4 || recovery_dots!=3)
    $fatal(1,"TENSOR_PROTOCOL_COVERAGE_MISSING");
  reset_abort(0);
  reset_abort(1);
  reset_abort(2);
  if(reset_aborts!=3 || recovery_dots!=6)
    $fatal(1,"TENSOR_RESET_ABORT_COVERAGE_MISSING");
  $display("CHECKS_PASSED tensor dots=%0d lane_comparisons=%0d vectors=%0d latency=10 stall_edges=7 protocol_rejections=%0d recovery_dots=%0d reset_aborts=%0d boundary_dots=%0d bubble_edges=%0d blocked_offers=%0d",
           compared,compared*64,vectors,protocol_rejections,recovery_dots,reset_aborts,
           extra_compared,bubble_edges,blocked_offers);
  $finish;
end
endmodule
"""
    bench = (bench.replace("BOUNDARY_VECTOR_COUNT", str(len(records)))
             .replace("BOUNDARY_DOT_COUNT", str(len(extra_dots)))
             .replace("BOUNDARY_VECTOR_PATH", evidence.relative(extra_path)))
    output = evidence.simulate("tensor", bench,
                              ["anvil_q1_ht_mac_lane.sv", "anvil_q1_ht_tensor_array.sv"])
    match = re.search(r"boundary_dots=(\d+) bubble_edges=(\d+) blocked_offers=(\d+)", output)
    if not match or int(match[1]) != len(extra_dots) or min(map(int, match.groups()[1:])) <= 0:
        raise AssertionError("tensor boundary comparisons or handshake observations missing")
    evidence.record["observations"].append({
        "scope": "public_tensor_primitive_not_decoder_bias_or_full_model_acceptance",
        "seed": seed, "original_dots": len(dots), "compared_boundary_dots": int(match[1]),
        "compared_boundary_categories": bins, "observed_input_bubble_edges": int(match[2]),
        "observed_blocked_following_dot_offers": int(match[3]),
    })
    evidence.flush()


def dequant(evidence, seed, rtl_root=None):
    """Exhaust encodings and compare every lane/nibble pair at three finite scales."""
    rng = random.Random(seed)
    path = evidence.folder / "dequant-vectors.hex"
    count = 0
    expected_errors = []
    directed_scales = (0x0001, 0x2400, 0x7bff)
    with path.open("w") as out:
        for mode in range(2):
            for bits in range(65536):
                lane = bits % 8
                qw, qz = rng.getrandbits(32), rng.getrandbits(32)
                try:
                    if mode:
                        expected = bf16(bits)
                    else:
                        scale = fp_q16(bits, 5, 10, True)
                        expected = ((qw >> AWQ_SHIFTS[lane] & 15) -
                                    (qz >> AWQ_SHIFTS[lane] & 15)) * scale
                    error = 0
                except ValueError:
                    expected, error = 0, 1
                out.write(f"{mode:x}{qw:08x}{qz:08x}{lane:x}{bits:04x}"
                          f"{expected & ((1 << 37)-1):010x}{error:x}\n")
                count += 1
                expected_errors.append(error)
        for lane, shift in enumerate(AWQ_SHIFTS):
            for q in range(16):
                for z in range(16):
                    for bits in directed_scales:
                        qw = (rng.getrandbits(32) & ~(15 << shift)) | (q << shift)
                        qz = (rng.getrandbits(32) & ~(15 << shift)) | (z << shift)
                        expected = (q - z) * fp_q16(bits, 5, 10, True)
                        out.write(f"0{qw:08x}{qz:08x}{lane:x}{bits:04x}"
                                  f"{expected & ((1 << 37)-1):010x}0\n")
                        count += 1
                        expected_errors.append(0)
    evidence.record.setdefault("runtime_input_sha256", {})[evidence.relative(path)] = (
        hashlib.sha256(path.read_bytes()).hexdigest())
    evidence.flush()
    bench = CLOCK + r"""
reg in_valid=0,in_bf16=0,out_ready=0;
reg [31:0] in_qweight=0,in_qzero=0;
reg [2:0] in_lane=0;
reg [15:0] in_value=0;
wire in_ready,out_valid,out_error;
wire signed [36:0] out_weight;
reg [131:0] vectors [0:VECTOR_COUNT-1];
reg [36:0] expected;
reg expected_error;
integer i,stall,errors=0,comparisons=0,cycle_count=0;
integer pair_bins=0,lane_bins=0,shift,q,z,scale_index,bin_index;
reg pair_seen [0:6143];
reg [7:0] lane_seen=0;
always @(posedge clk) cycle_count=cycle_count+1;
anvil_q1_ht_dequant product(
  .clk(clk),.rst_n(rst_n),.in_valid(in_valid),.in_ready(in_ready),
  .in_bf16(in_bf16),.in_qweight(in_qweight),.in_qzero(in_qzero),.in_lane(in_lane),
  .in_value(in_value),.out_valid(out_valid),.out_ready(out_ready),
  .out_weight(out_weight),.out_error(out_error));
task check_reset;
  begin
    if ({in_ready,out_valid,out_weight,out_error} !== 40'b0)
      $fatal(1,"DEQUANT_RESET_XZ_OR_NONZERO");
  end
endtask
always @(posedge clk or negedge clk) if (!rst_n) check_reset();
initial begin
  rst_n=0; `RESET_DELTA check_reset();
  for(i=0;i<6144;i=i+1) pair_seen[i]=0;
  $readmemh("VECTOR_PATH",vectors);
  repeat (3) edge_tick();
  @(negedge clk); rst_n=1;
  for (i=VECTOR_START;i<VECTOR_STOP;i=i+1) begin
    @(negedge clk);
    in_bf16=vectors[i][128];
    in_qweight=vectors[i][127:96];
    in_qzero=vectors[i][95:64];
    in_lane=vectors[i][62:60];
    in_value=vectors[i][59:44];
    expected=vectors[i][40:4];
    expected_error=vectors[i][0];
    in_valid=1;
    if (in_ready !== 1) $fatal(1,"DEQUANT_NOT_READY");
    edge_tick();
    if (out_valid !== 0) $fatal(1,"DEQUANT_EARLY_OUTPUT");
    @(negedge clk); in_valid=0;
    edge_tick();
    if (out_valid !== 1 || out_weight !== expected || out_error !== expected_error)
      $fatal(1,"DEQUANT_MISMATCH vector=%0d bits=%h mode=%0d got=%h error=%b expected=%h error=%b",
             i,in_value,in_bf16,out_weight,out_error,expected,expected_error);
    if (expected_error) errors=errors+1;
    for (stall=0;stall<(i%31==0 ? 7 : 0);stall=stall+1) begin
      edge_tick();
      if (out_valid !== 1 || out_weight !== expected || out_error !== expected_error)
        $fatal(1,"DEQUANT_STALLED_RESULT_CHANGED");
    end
    @(negedge clk); out_ready=1;
    edge_tick();
    if (out_valid !== 0) $fatal(1,"DEQUANT_RETIRE");
    @(negedge clk); out_ready=0;
    comparisons=comparisons+1;
    if(i>=131072) begin
      case(in_lane)
       0:shift=0; 1:shift=16; 2:shift=4; 3:shift=20;
       4:shift=8; 5:shift=24; 6:shift=12; 7:shift=28;
       default:$fatal(1,"DEQUANT_DIRECTED_LANE_XZ");
      endcase
      case(in_value)
       16'h0001:scale_index=0;
       16'h2400:scale_index=1;
       16'h7bff:scale_index=2;
       default:$fatal(1,"DEQUANT_DIRECTED_SCALE");
      endcase
      if(in_bf16!==0 || expected_error!==0)
       $fatal(1,"DEQUANT_DIRECTED_MODE_OR_ERROR");
      q=(in_qweight>>shift)&15;
      z=(in_qzero>>shift)&15;
      bin_index=((in_lane*16+q)*16+z)*3+scale_index;
      if(!pair_seen[bin_index]) begin
       pair_seen[bin_index]=1;pair_bins=pair_bins+1;
      end
      if(!lane_seen[in_lane]) begin
       lane_seen[in_lane]=1;lane_bins=lane_bins+1;
      end
    end
  end
  if(errors!=EXPECTED_ERRORS || pair_bins!=EXPECTED_PAIRS ||
     lane_bins!=EXPECTED_LANES)
   $fatal(1,"DEQUANT_ENCODING_OR_NIBBLE_COVERAGE errors=%0d pairs=%0d lanes=%0d",
          errors,pair_bins,lane_bins);
  $display("CHECKS_PASSED dequant encodings=%0d expected_errors=%0d cycles=%0d directed_pairs=%0d physical_lanes=%0d",
           comparisons,errors,cycle_count,pair_bins,lane_bins);
  $finish;
end
endmodule
"""
    sources = ["anvil_q1_ht_dequant.sv"]
    if rtl_root is None:
        sources.insert(0, "anvil_q1_ht_00_numeric_pkg.sv")
    interpreted = getattr(evidence, "default_simulator", "iverilog") == "iverilog"
    # Keep the AWQ-to-BF16 transition inside one batch, not across a reset.
    batches = ((0, 65537), (65537, 131072), (131072, count)) if interpreted else ((0, count),)
    compared = pair_bins = 0
    for index, (start, stop) in enumerate(batches):
        pairs = max(0, stop - max(start, 131072))
        errors = sum(expected_errors[start:stop])
        program = bench.replace("VECTOR_PATH", evidence.relative(path)).replace(
            "VECTOR_START", str(start)).replace("VECTOR_STOP", str(stop)).replace(
            "VECTOR_COUNT", str(count)).replace("EXPECTED_ERRORS", str(errors)).replace(
            "EXPECTED_PAIRS", str(pairs)).replace("EXPECTED_LANES", "8" if pairs else "0")
        evidence.simulate(f"dequant-{index}", program, sources, rtl_root=rtl_root)
        counters = evidence.record["observations"][-1]["observed_counters"]
        if (len(counters) != 1 or counters[0].get("encodings") != stop - start or
                counters[0].get("expected_errors") != errors or
                counters[0].get("directed_pairs") != pairs or
                counters[0].get("physical_lanes") != (8 if pairs else 0) or
                counters[0].get("cycles", 0) <= 0):
            raise AssertionError("dequant batch lacks complete observed encoding/cycle counts")
        if interpreted and counters[0]["cycles"] > 500000:
            raise AssertionError("Icarus harness tier exceeded 500000 cycles; use compiled simulation")
        compared += counters[0]["encodings"]
        pair_bins += counters[0]["directed_pairs"]
    if compared != count or pair_bins != 8 * 16 * 16 * len(directed_scales):
        raise AssertionError("exhaustive dequant coverage is incomplete")
    evidence.record["dequant_encoding_count"] = compared
    evidence.record["dequant_coverage"] = {
        "exhaustive_FP16_AWQ_and_BF16_encodings": 131072,
        "directed_compared_lane_qweight_qzero_scale_bins": pair_bins,
        "physical_lanes": 8, "qweight_values": 16, "qzero_values": 16,
        "directed_FP16_scale_bits": list(directed_scales),
        "bin_event": "accepted public input, bit-exact output and error comparison, "
                     "stall stability and response retirement",
        "scope": "dequant_primitive_not_full_tensor_or_decoder_coverage",
    }
    evidence.flush()


def math_probe(evidence, seed):
    rng = random.Random(seed)
    vectors = []
    classes = ("random", "shift_boundary", "signed_division", "unsigned_division",
               "carry_boundary", "square_boundary", "error")

    def append(op, a, b, shift, result, error=0, category=0):
        vectors.append((op, a, b, shift, result, error, category))

    for _ in range(50):
        a, b = rng.getrandbits(128), rng.getrandbits(128)
        for op in range(8):
            shift = rng.randrange(128)
            if op == 0:
                result = a + b
            elif op == 1:
                result = a - b
            elif op == 2:
                result = a * b
            elif op == 3:
                result = round_shift(signed(a, 128), shift)
            elif op == 4:
                result = round_div(signed(a, 128), b)
            elif op == 5:
                result = trunc_div(signed(a, 128), b)
            elif op == 6:
                result = a // b
            else:
                result = math.isqrt(a)
            append(op, a, b, shift, result)
    for op in (4, 5, 6):
        append(op, 123, 0, 0, 0, 1, 6)
    for op in range(8, 16):
        append(op, 123, 456, 0, 0, 1, 6)
    for a in (0, 1, -1, 32767, -32767, 32768, -32768, 32769, -32769,
              -(1 << 127), (1 << 127) - 1):
        for shift in (0, 1, 16, 48, 127):
            append(3, a, 1, shift, round_shift(a, shift), category=1)
    for shift in range(128):
        half = 1 << (shift - 1) if shift else 0
        values = {0, -(1 << 127), (1 << 127) - 1}
        for delta in (-1, 0, 1):
            values.update((half + delta, -half - delta))
        for a in sorted(values):
            append(3, a, 1, shift, round_shift(a, shift), category=1)
    denominators = {1, 2, 3}
    for bit in (16, 31, 32, 63, 64, 95, 96, 127, 128):
        denominators.add((1 << bit) - 1)
        if bit < 128:
            denominators.add(1 << bit)
    for b in sorted(denominators):
        magnitudes = {0, 1, b - 1, b, b + 1,
                      b // 2 - 1, b // 2, b // 2 + 1,
                      3 * b + b // 2 - 1, 3 * b + b // 2, 3 * b + b // 2 + 1}
        signed_values = {-(1 << 127), (1 << 127) - 1}
        for a in magnitudes:
            if 0 <= a < (1 << 127):
                signed_values.update((a, -a))
        for a in sorted(signed_values):
            append(4, a, b, 0, round_div(a, b), category=2)
            append(5, a, b, 0, trunc_div(a, b), category=2)
        for a in sorted(magnitudes | {(1 << 128) - 1}):
            if 0 <= a < (1 << 128):
                append(6, a, b, 0, a // b, category=3)
    mask = (1 << 128) - 1
    for bit in (16, 32, 48, 64, 80, 96, 112, 127):
        boundary = 1 << bit
        for a, b in ((boundary - 1, 1), (boundary, 1),
                     (mask, boundary - 1), (boundary - 1, boundary - 1)):
            append(0, a, b, 0, a + b, category=4)
            append(1, a, b, 0, a - b, category=4)
            append(2, a, b, 0, a * b, category=4)
    roots = {0, 1, 2, 3, (1 << 64) - 1}
    for bit in (8, 16, 31, 32, 47, 48, 63):
        roots.update(((1 << bit) - 1, 1 << bit, (1 << bit) + 1))
    for root in sorted(roots):
        for a in (root * root - 1, root * root, root * root + 1):
            if 0 <= a <= mask:
                append(7, a, 0, 0, math.isqrt(a), category=5)
    append(7, mask, 0, 0, math.isqrt(mask), category=5)
    vector_path = evidence.folder / "math-vectors.json"
    vector_path.write_text(json.dumps({
        "seed": seed, "classes": classes,
        "fields": ["op", "a", "b", "shift", "expected", "error", "category"],
        "vectors": vectors,
    }, indent=2) + "\n")
    evidence.record.setdefault("runtime_input_sha256", {})[
        evidence.relative(vector_path)] = hashlib.sha256(vector_path.read_bytes()).hexdigest()
    evidence.flush()
    bench = CLOCK + r"""
reg in_valid=0,out_ready=0;
reg [3:0] in_op=0;
reg [127:0] in_a=0,in_b=0;
reg [6:0] in_shift=0;
wire in_ready,out_valid,out_error;
wire [127:0] out_data;
integer comparisons=0, cycles_total=0, i;
integer class_counts[0:6];
reg [127:0] compared_shifts=0;
reg [398:0] vectors[0:VECTOR_COUNT-1];
reg [3:0] vector_op;
reg [127:0] vector_a,vector_b,vector_expected;
reg [6:0] vector_shift;
reg vector_error;
reg [2:0] vector_category;
anvil_q1_ht_math product(
 .clk(clk),.rst_n(rst_n),.in_valid(in_valid),.in_ready(in_ready),.in_op(in_op),
 .in_a(in_a),.in_b(in_b),.in_shift(in_shift),.out_valid(out_valid),
 .out_ready(out_ready),.out_data(out_data),.out_error(out_error));
task reset_check;
 begin
  if ({in_ready,out_valid,out_data,out_error} !== 131'b0) $fatal(1,"MATH_RESET_XZ_OR_NONZERO");
 end
endtask
always @(posedge clk or negedge clk) if (!rst_n) reset_check();
always @(posedge clk) cycles_total=cycles_total+1;
task check(input [3:0] op,input [127:0] a,b,input [6:0] shift,
           input [127:0] expected,input expected_error,input integer category);
 integer cycles,stall;
 begin
  @(negedge clk); in_op=op; in_a=a; in_b=b; in_shift=shift; in_valid=1;
  if (in_ready !== 1) $fatal(1,"MATH_NOT_READY");
  edge_tick();
  if(in_ready !== 0) $fatal(1,"MATH_BUSY_ACCEPTS_ANOTHER_REQUEST");
  @(negedge clk); in_valid=0;
  cycles=0;
  while (out_valid !== 1 && cycles<10000) begin
    edge_tick(); cycles=cycles+1;
    if(in_ready !== 0) $fatal(1,"MATH_BUSY_ACCEPTS_ANOTHER_REQUEST");
    if(out_valid !== 0 && out_valid !== 1) $fatal(1,"MATH_ACTIVE_VALID_XZ");
  end
  if (out_valid !== 1 || out_data !== expected || out_error !== expected_error)
    $fatal(1,"MATH_MISMATCH case=%0d op=%0d a=%h b=%h shift=%0d actual=%h expected=%h err=%b expected_err=%b",
           comparisons,op,a,b,shift,out_data,expected,out_error,expected_error);
  for (stall=0;stall<3;stall=stall+1) begin
    edge_tick();
    if (out_valid !== 1 || out_data !== expected || out_error !== expected_error ||
        in_ready !== 0)
      $fatal(1,"MATH_STALL_CHANGED");
  end
  @(negedge clk); out_ready=1;
  edge_tick();
  if (out_valid !== 0) $fatal(1,"MATH_RETIRE");
  @(negedge clk); out_ready=0;
  comparisons=comparisons+1;
  class_counts[category]=class_counts[category]+1;
  if(category==1) compared_shifts[shift]=1'b1;
 end
endtask
initial begin
 $readmemh("VECTOR_PATH",vectors);
 for(i=0;i<7;i=i+1) class_counts[i]=0;
 rst_n=0; `RESET_DELTA reset_check();
 repeat (3) edge_tick();
 @(negedge clk); rst_n=1;
 for(i=0;i<VECTOR_COUNT;i=i+1) begin
  {vector_op,vector_a,vector_b,vector_shift,vector_expected,vector_error,vector_category}
   = vectors[i];
  if((^vectors[i]) === 1'bx) $fatal(1,"MATH_MALFORMED_VECTOR");
  check(vector_op,vector_a,vector_b,vector_shift,vector_expected,vector_error,vector_category);
 end
 if(compared_shifts !== {128{1'b1}}) $fatal(1,"MATH_MISSING_SHIFT_BOUNDARY");
 for(i=0;i<7;i=i+1)
  if(class_counts[i]==0) $fatal(1,"MATH_MISSING_DIRECTED_CLASS");
 $display("CHECKS_PASSED math comparisons=%0d cycles=%0d random=%0d shift_boundary=%0d signed_division=%0d unsigned_division=%0d carry_boundary=%0d square_boundary=%0d error=%0d shifts=128",
 comparisons,cycles_total,class_counts[0],class_counts[1],class_counts[2],
 class_counts[3],class_counts[4],class_counts[5],class_counts[6]);
 $finish;
end
endmodule
"""
    compact = [row for index, row in enumerate(vectors)
               if index < 8 or row[6] in (1, 4, 5, 6) or
               (row[6] in (2, 3) and row[2] <= 3)]
    simulations = [("verilator", vectors)]
    if getattr(evidence, "default_simulator", "iverilog") == "iverilog":
        simulations.insert(0, ("iverilog", compact))
    for simulator, cases in simulations:
        path = evidence.folder / ("math-" + simulator + "-vectors.hex")
        words = []
        for row in cases:
            word = 0
            for value, bits in zip(row, (4, 128, 128, 7, 128, 1, 3)):
                word = (word << bits) | (value & ((1 << bits) - 1))
            words.append(f"{word:0100x}\n")
        path.write_text("".join(words))
        evidence.record["runtime_input_sha256"][evidence.relative(path)] = hashlib.sha256(
            path.read_bytes()).hexdigest()
        evidence.flush()
        program = bench.replace("VECTOR_COUNT", str(len(cases))).replace(
            "VECTOR_PATH", evidence.relative(path))
        transcript = evidence.simulate(
            "math-" + simulator, program,
            ["anvil_q1_ht_00_numeric_pkg.sv", "anvil_q1_ht_divide.sv",
             "anvil_q1_ht_isqrt.sv", "anvil_q1_ht_math.sv"], simulator=simulator)
        counters = measurement_records(transcript, "CHECKS_PASSED math")
        expected_counts = {name: sum(row[6] == index for row in cases)
                           for index, name in enumerate(classes)}
        if (len(counters) != 1 or counters[0].get("comparisons") != len(cases) or
                counters[0].get("shifts") != 128 or
                any(counters[0].get(name) != count for name, count in expected_counts.items())):
            raise AssertionError("math directed public result comparisons lack required coverage")
        if simulator == "iverilog" and counters[0]["cycles"] > 500000:
            raise AssertionError("math Icarus smoke exceeds the 500000-cycle tier")
        evidence.record.setdefault("math_coverage", []).append({
            "seed": seed, "simulator": simulator, "observed": counters[0],
            "bin_event": "accepted public input, exact result/error comparison, "
                         "busy exclusion, stalled result stability and retirement",
            "oracle": "Python arbitrary-precision integers and math.isqrt; "
                      "results compared modulo 2**128, not saturated",
            "scope": "scalar_math_primitive_not_complete_network_or_timing_acceptance",
        })
        evidence.flush()


def top_probe(evidence, mode, seed, upload_only=False, config=0,
              fault_read=-1, fault_write=-1, orphan_fault=False, abort_stage=None,
              diagnostic_first_token=False, simulator="verilator",
              cxx_optimization="-O3", flatten=False, reusable_build=True,
              numerical_fault=None, command_validation=False, pending_upload_validation=False,
              reset_validation=False, late_read_fault=False):
    shape = MATRIX[config]
    if late_read_fault:
        if (config != 0 or not reusable_build or upload_only or fault_read >= 0 or
                fault_write >= 0 or orphan_fault or abort_stage or diagnostic_first_token or
                numerical_fault is not None or command_validation or pending_upload_validation or
                reset_validation):
            raise ValueError("late read fault requires a separate compact two-panel case")
        from dataclasses import replace
        shape = replace(shape, vocab=67)
    model = EngineeringModel(shape, seed, mode)
    if reset_validation and (
            config != 0 or not reusable_build or upload_only or fault_read >= 0 or
            fault_write >= 0 or orphan_fault or abort_stage or diagnostic_first_token or
            numerical_fault is not None or command_validation or pending_upload_validation):
        raise ValueError("reset validation requires a separate compact integration case")
    if pending_upload_validation and (
            config != 0 or not reusable_build or upload_only or fault_read >= 0 or
            fault_write >= 0 or orphan_fault or abort_stage or diagnostic_first_token or
            numerical_fault is not None or command_validation):
        raise ValueError("pending upload validation requires a separate compact integration case")
    if command_validation and (
            config != 1 or not reusable_build or upload_only or fault_read >= 0 or
            fault_write >= 0 or orphan_fault or abort_stage or diagnostic_first_token or
            numerical_fault is not None):
        raise ValueError("command validation requires its separate two-layer integration case")
    if numerical_fault is not None and (
            upload_only or fault_read >= 0 or fault_write >= 0 or orphan_fault or
            abort_stage or diagnostic_first_token or not reusable_build or config != 0):
        raise ValueError("numerical faults require a separate compact public-interface case")
    tokens = []
    for position in range(min(shape.max_seq, shape.window + 2)):
        token_id = (seed + position * 3) % shape.vocab
        expected = model.token(token_id, position, position == 0)
        tokens.append((token_id, position, position == 0, expected))
    token_id = (seed + 1) % shape.vocab
    tokens.append((token_id, 0, True, model.token(token_id, 0, True)))
    poisoned = None
    if numerical_fault is not None:
        from numerical_faults import poison_image
        poisoned = poison_image(model, numerical_fault, tokens[0][0])
    if diagnostic_first_token:
        if upload_only or fault_read >= 0 or fault_write >= 0 or orphan_fault or abort_stage:
            raise ValueError("first-token diagnostic cannot replace protocol/fault tests")
        tokens = tokens[:1]
        evidence.record["diagnostic_scope"] = (
            "One independently compared first token only; not the mandatory matrix, "
            "sequence reuse, window rollover, or full-model acceptance.")
    runtime_cases = evidence.record.setdefault("runtime_cases", [])
    case_folder = evidence.folder / f"case-inputs-{len(runtime_cases):04d}"
    case_folder.mkdir(exist_ok=False)
    runtime_case = {"directory": evidence.relative(case_folder)}
    runtime_cases.append(runtime_case)
    image = case_folder / "image.hex"
    image.write_text("".join(f"{int.from_bytes(model.image[i:i+64], 'little'):0128x}\n"
                             for i in range(0, len(model.image), 64)))
    calls = [f"csr(1,16'h000c,32'd{int(mode == 'BF16')},0,0);"]
    for index, kind, layer, proj, base, length in model.descriptors:
        for address, value in ((0x10, index), (0x14, kind), (0x18, layer), (0x1c, proj),
                               (0x20, base & 0xffffffff), (0x24, base >> 32),
                               (0x28, length), (0x2c, 1)):
            calls.append(f"csr(1,16'h{address:04x},32'd{value},0,0);")
    bench = CLOCK + r"""
reg ddr_clk=0;
always #1.875 ddr_clk=!ddr_clk;
reg token_valid=0,new_sequence=0,logit_ready=0;
reg [31:0] token_id=0,token_pos=0;
wire token_ready,logit_valid,done,error;
wire [31:0] logit_index;
wire signed [31:0] logit_data;
reg csr_valid=0,csr_write=0,csr_rsp_ready=0;
reg [15:0] csr_address=0;
reg [31:0] csr_wdata=0;
wire csr_ready,csr_rsp_valid,csr_error;
wire [31:0] csr_rdata;
reg load_valid=0,load_last=0;
reg [32:0] load_address=0;
reg [511:0] load_data=0;
reg [63:0] load_byteenable=0;
wire load_ready,load_done,load_error;
wire [32:0] avm_address;
wire [7:0] avm_burstcount;
wire avm_read,avm_write;
wire [511:0] avm_writedata;
wire [63:0] avm_byteenable;
reg avm_waitrequest=0;
reg [511:0] avm_readdata=0;
reg avm_readdatavalid=0;
reg [1:0] avm_response=0;
reg avm_writeresponsevalid=0;
reg [511:0] memory [0:MEMORY_LAST];
reg [511:0] image [0:IMAGE_LAST];
integer reads=0,writes=0,load_accepts=0,csr_compares=0,logits=0;
integer reset_checks=0;
integer outstanding=0,cursor=0,i,j,timeout_cycles;
integer ddr_cycles=0;
reg held_command=0;
reg inject_orphan=0,orphan_sent=0;
reg inject_unowned_write=0,unowned_write_sent=0;
integer target_commands=0;
integer target_response_delay=0;
integer fault_with_pending_read=0;
integer command_stall_left=0;
reg command_stall_started=0;
reg [681:0] held_payload;
wire [681:0] command_payload =
 {avm_address,avm_burstcount,avm_read,avm_write,avm_writedata,avm_byteenable,63'b0};
anvil_q1_ht_top #(
 .NUM_LAYERS(LAYERS_VALUE),.HIDDEN_SIZE(HIDDEN_VALUE),.INTERMEDIATE_SIZE(INTERMEDIATE_VALUE),
 .NUM_Q_HEADS(QHEADS_VALUE),.NUM_KV_HEADS(KVHEADS_VALUE),.HEAD_DIM(HEAD_VALUE),.GROUP_SIZE(GROUP_VALUE),
 .VOCAB_SIZE(VOCAB_VALUE),.MAX_SEQ_LEN(SEQ_VALUE),.TILE_BEATS(TILE_VALUE),.KV_WINDOW(WINDOW_VALUE)) product(
 .clk(clk),.ddr_clk(ddr_clk),.rst_n(rst_n),
 .token_valid(token_valid),.token_ready(token_ready),.token_id(token_id),.token_pos(token_pos),
 .new_sequence(new_sequence),.logit_valid(logit_valid),.logit_ready(logit_ready),
 .logit_index(logit_index),.logit_data(logit_data),.done(done),.error(error),
 .csr_valid(csr_valid),.csr_write(csr_write),.csr_address(csr_address),.csr_wdata(csr_wdata),
 .csr_ready(csr_ready),.csr_rsp_valid(csr_rsp_valid),.csr_rsp_ready(csr_rsp_ready),
 .csr_rdata(csr_rdata),.csr_error(csr_error),
 .load_valid(load_valid),.load_ready(load_ready),.load_address(load_address),
 .load_data(load_data),.load_byteenable(load_byteenable),.load_last(load_last),
 .load_done(load_done),.load_error(load_error),.avm_address(avm_address),
 .avm_burstcount(avm_burstcount),.avm_read(avm_read),.avm_write(avm_write),
 .avm_writedata(avm_writedata),.avm_byteenable(avm_byteenable),
 .avm_waitrequest(avm_waitrequest),.avm_readdata(avm_readdata),
 .avm_readdatavalid(avm_readdatavalid),.avm_response(avm_response),
 .avm_writeresponsevalid(avm_writeresponsevalid));
task check_reset;
 begin
  reset_checks=reset_checks+1;
  if ({token_ready,logit_valid,logit_index,logit_data,done,error,csr_ready,csr_rsp_valid,
       csr_rdata,csr_error,load_ready,load_done,load_error,avm_address,avm_burstcount,
       avm_read,avm_write,avm_writedata,avm_byteenable} !== 724'b0)
    $fatal(1,"TOP_RESET_XZ_OR_NONZERO time=%0t",$time);
 end
endtask
always @(posedge clk or negedge clk) if (!rst_n) check_reset();
always @(posedge ddr_clk) begin
 if (rst_n) begin
  if (load_valid && load_ready) load_accepts=load_accepts+1;
  if (held_command && command_payload !== held_payload)
    $fatal(1,"AVALON_COMMAND_CHANGED_DURING_STALL");
  held_command=(avm_read || avm_write) && avm_waitrequest;
  if (held_command) held_payload=command_payload;
  if (avm_read && !avm_waitrequest) begin
    if (outstanding || avm_burstcount<1 || avm_burstcount>16 || avm_address[5:0]!==0 ||
        {1'b0,avm_address[11:0]}+avm_burstcount*64>4096 ||
        {1'b0,avm_address}+avm_burstcount*64>34'h200000000 ||
        avm_byteenable!==64'hffffffffffffffff)
      $fatal(1,"AVALON_READ_CONTRACT");
    outstanding=avm_burstcount;
    cursor=avm_address>>6;
    if(avm_address>=TARGET_BASE && avm_address<TARGET_END) begin
      target_commands=target_commands+1;
      if(ABORT_PENDING_READ) target_response_delay=31;
    end
  end
  if (avm_readdatavalid) reads=reads+1;
  if (avm_write && !avm_waitrequest) begin
    if (avm_read || avm_burstcount!==1 || avm_address[5:0]!==0)
      $fatal(1,"AVALON_WRITE_CONTRACT");
    for (j=0;j<64;j=j+1)
      if (avm_byteenable[j]) memory[avm_address>>6][j*8+:8]=avm_writedata[j*8+:8];
    writes=writes+1;
  end
 end
end
always @(negedge ddr_clk) begin
 if (!rst_n) begin
  avm_readdatavalid=0; avm_writeresponsevalid=0; outstanding=0;
  avm_readdata=0; avm_waitrequest=0; avm_response=0; ddr_cycles=0; held_command=0;
 end else begin
  avm_readdatavalid=0;
  avm_writeresponsevalid=0;
  avm_response=0;
  if(target_response_delay>0) target_response_delay=target_response_delay-1;
  else if (outstanding>0) begin
    avm_readdatavalid=1;
    avm_readdata=memory[cursor];
    if(reads==READ_FAULT_VALUE) avm_response=2'b10;
    cursor=cursor+1;
    outstanding=outstanding-1;
  end
  // A command accepted on the prior positive edge gets its write response next edge.
  if (writes>response_writes) begin
    avm_writeresponsevalid=1;
    if(response_writes==WRITE_FAULT_VALUE) avm_response=2'b10;
    response_writes=writes;
  end
  if(inject_orphan && !orphan_sent) begin
    if(outstanding!=0 || avm_read || avm_write || avm_readdatavalid)
      $fatal(1,"ORPHAN_STIMULUS_PRECONDITION_FAILED");
    avm_readdatavalid=1;
    avm_readdata=512'h12345678;
    orphan_sent=1;
  end
  if(inject_unowned_write && !unowned_write_sent) begin
    if(avm_write || avm_writeresponsevalid || writes!=response_writes)
      $fatal(1,"UNOWNED_WRITE_STIMULUS_PRECONDITION_FAILED");
    avm_writeresponsevalid=1;
    unowned_write_sent=1;
    if(outstanding>0) fault_with_pending_read=fault_with_pending_read+1;
  end
  if(ABORT_WAITREQUEST && !command_stall_started && avm_read) begin
    avm_waitrequest=1;
    command_stall_started=1;
    command_stall_left=31;
    inject_unowned_write=1;
  end else if(command_stall_left>0) begin
    command_stall_left=command_stall_left-1;
    if(command_stall_left==0) avm_waitrequest=0;
  end
  ddr_cycles=ddr_cycles+1;
 end
end
integer response_writes=0;
task run_token(input [31:0] id,position,input sequence_start,
               input [VOCAB_BITS_MINUS_ONE:0] expected);
 integer token_logits,cycles,final_stalls;
 reg pre_transfer,pre_valid;
 reg [31:0] pre_index,pre_data;
 begin
  @(negedge clk);
  token_id=id;token_pos=position;new_sequence=sequence_start;token_valid=1;
  if (token_ready !== 1) $fatal(1,"TOKEN_NOT_READY_ON_START position=%0d",position);
  edge_tick();
  if (token_ready !== 0 || logit_valid !== 0) $fatal(1,"TOKEN_ACCEPT_EDGE");
  @(negedge clk);token_valid=0;logit_ready=0;
  cycles=0;token_logits=0;final_stalls=0;
  while (token_logits<VOCAB_VALUE) begin
   @(negedge clk);
   logit_ready=(cycles%11>3);
   if (logit_valid===1 && logit_index==VOCAB_VALUE-1 && final_stalls<31) begin
    logit_ready=0;final_stalls=final_stalls+1;
   end
   #0.001;
   pre_valid=logit_valid;pre_index=logit_index;pre_data=logit_data;
   pre_transfer=logit_valid && logit_ready;
   if ((^{logit_valid,logit_index,logit_data,done,error,token_ready})===1'bx)
    $fatal(1,"TOP_ACTIVE_XZ");
   if (logit_valid===1 &&
       (logit_index!==token_logits || logit_data!==expected[32*token_logits+:32]))
    $fatal(1,"TOP_LOGIT_MISMATCH position=%0d index=%0d actual_index=%0d actual=%h expected=%h",
           position,token_logits,logit_index,logit_data,expected[32*token_logits+:32]);
   edge_tick();
   if (pre_valid && !pre_transfer &&
       (logit_valid!==1 || logit_index!==pre_index || logit_data!==pre_data))
    $fatal(1,"TOP_STALLED_LOGIT_CHANGED");
   if (pre_transfer) begin
    token_logits=token_logits+1;
    if (token_logits==VOCAB_VALUE && (done!==1 || error!==0))
     $fatal(1,"TOP_FINAL_LOGIT_COMPLETION");
   end
   if (token_logits<VOCAB_VALUE && done!==0)
    $fatal(1,"TOP_EARLY_OR_ERROR_COMPLETION position=%0d error=%b logits=%0d cycles=%0d",
           position,error,token_logits,cycles);
   cycles=cycles+1;
  end
  if (token_logits!==VOCAB_VALUE || reads==0 || final_stalls!==31)
   $fatal(1,"TOP_MISSING_LOGITS_DDR_OR_FINAL_STALL");
  edge_tick();
  if (done!==0 || error!==0 || load_accepts!==IMAGE_LAST+1)
   $fatal(1,"TOP_COMPLETION_OR_REUPLOAD");
  logits=logits+token_logits;
  $display("TOKEN_COMPARED mode=MODE position=%0d new_sequence=%b logits=%0d cycles=%0d reads=%0d",
           position,sequence_start,token_logits,cycles,reads);
  $fflush();
 end
endtask
task csr(input wr,input [15:0] address,input [31:0] data,
         input expected_error,input [31:0] expected_data);
 integer wait_cycles,stall;
 reg [31:0] held_data;
 begin
  @(negedge clk);
  csr_valid=1;csr_write=wr;csr_address=address;csr_wdata=data;
  wait_cycles=0;
  while (csr_ready !== 1 && wait_cycles<10000) begin edge_tick(); @(negedge clk);wait_cycles=wait_cycles+1;end
  if (csr_ready !== 1) $fatal(1,"CSR_ACCEPT_NOT_PROGRESSING address=%h",address);
  edge_tick();
  if (csr_rsp_valid !== 0) $fatal(1,"CSR_RESPONSE_TOO_EARLY");
  @(negedge clk);csr_valid=0;
  wait_cycles=0;
  while (csr_rsp_valid !== 1 && wait_cycles<10000) begin edge_tick();wait_cycles=wait_cycles+1;end
  if (csr_rsp_valid !== 1 || csr_error !== expected_error ||
      (!wr && csr_rdata !== expected_data) || (^csr_rdata===1'bx))
    $fatal(1,"CSR_MISMATCH address=%h actual=%h error=%b expected=%h error=%b",
            address,csr_rdata,csr_error,expected_data,expected_error);
  held_data=csr_rdata;
  for (stall=0;stall<3;stall=stall+1) begin
    edge_tick();
    if (csr_rsp_valid !== 1 || csr_rdata !== held_data || csr_error !== expected_error ||
        csr_ready !== 0) $fatal(1,"CSR_STALL_OR_OUTSTANDING");
  end
  @(negedge clk);csr_rsp_ready=1;
  edge_tick();
  if (csr_rsp_valid !== 0) $fatal(1,"CSR_RETIRE");
  @(negedge clk);csr_rsp_ready=0;
  csr_compares=csr_compares+1;
 end
endtask
task upload;
 integer beat,waiting;
 begin
  for (beat=0;beat<=(WRITE_FAULT_VALUE<0 ? IMAGE_LAST : WRITE_FAULT_VALUE);beat=beat+1) begin
    @(negedge ddr_clk);
    load_valid=1;load_last=(beat==IMAGE_LAST);load_address=beat*64;
    load_data=image[beat];load_byteenable=64'hffffffffffffffff;
    #0.001;
    waiting=0;
    while (load_ready !== 1 && waiting<10000) begin
      @(posedge ddr_clk);#0.001;@(negedge ddr_clk);#0.001;waiting=waiting+1;
    end
    if (load_ready !== 1) $fatal(1,"LOAD_NOT_PROGRESSING beat=%0d",beat);
    @(posedge ddr_clk);#0.001;
    if (load_error !== 0) $fatal(1,"LOAD_UNEXPECTED_ERROR");
    @(negedge ddr_clk);load_valid=0;
  end
  waiting=0;
  while (load_done !== 1 && waiting<10000) begin @(posedge ddr_clk);#0.001;waiting=waiting+1;end
  if (load_done !== 1 || load_error !== (WRITE_FAULT_VALUE>=0) ||
      writes!==(WRITE_FAULT_VALUE<0 ? IMAGE_LAST+1 : WRITE_FAULT_VALUE+1) ||
      load_accepts!==writes) $fatal(1,"LOAD_ACK_OR_CONSERVATION");
  for (beat=0;beat<=(WRITE_FAULT_VALUE<0 ? IMAGE_LAST : WRITE_FAULT_VALUE);beat=beat+1)
    if (memory[beat] !== image[beat]) $fatal(1,"PRELOAD_MEMORY_MISMATCH beat=%0d",beat);
  repeat (30) edge_tick();
 end
endtask
initial begin
 rst_n=0;
`ifndef VERILATOR
 #0;
`endif
 check_reset();
 for(i=0;i<=MEMORY_LAST;i=i+1) memory[i]=0;
 $readmemh("IMAGE_PATH",image);
 repeat (6) edge_tick();
 @(negedge clk);rst_n=1;
 repeat (150) edge_tick();
 if (token_ready !== 0) $fatal(1,"TOKEN_READY_WITHOUT_IMAGE");
`ifdef RESET_ONLY
 if(reset_checks<3) $fatal(1,"MISSING_FOUR_STATE_RESET_OBSERVATIONS");
 $display("CHECKS_PASSED integration_reset asserted_samples=%0d",reset_checks);
 $finish;
`endif
 csr(0,16'h0000,0,0,32'h02000001);
 csr(0,16'h0014,0,1,0);
 csr(0,16'h0040,0,1,0);
 csr(1,16'h0008,4,0,0);
 upload();
 AFTER_UPLOAD
 DESCRIPTOR_CALLS
 csr(1,16'h0008,2,0,0);
 repeat (30) edge_tick();
 if (token_ready !== 1) $fatal(1,"COMMITTED_IMAGE_NOT_READY");
 AFTER_COMMIT
end
endmodule
"""
    inference = "\n".join(f"run_token(32'd{id},32'd{position},1'b{int(new)},"
                          f"{hx(packed(expected,32),32*shape.vocab)});"
                          for id, position, new, expected in tokens) + r"""
 $display("CHECKS_PASSED top mode=MODE logits=%0d reads=%0d preload_beats=%0d csr_compares=%0d",
          logits,reads,load_accepts,csr_compares);
 $finish;
"""
    if upload_only:
        inference = r"""
 $display("CHECKS_PASSED csr_upload preload_beats=%0d acknowledged_writes=%0d csr_compares=%0d",
          load_accepts,writes,csr_compares);
 $finish;
"""
    if command_validation:
        from command_checks import instrument_commands
        bench, inference = instrument_commands(bench, model)
    if pending_upload_validation:
        from upload_conflicts import instrument_upload
        bench, inference = instrument_upload(bench)
    if reset_validation:
        from reset_integration import instrument_resets
        bench, inference = instrument_resets(bench, model)
    if late_read_fault:
        from late_faults import instrument_late_read
        bench, inference = instrument_late_read(bench, model)
    if poisoned is not None:
        bench = bench.replace("integer response_writes=0;", r"""
integer poison_address,poison_bits,original_bits,poison_seen=0,uploads_completed=0;
integer response_writes=0;
always @(posedge ddr_clk) if(rst_n && avm_readdatavalid &&
                            cursor-1 == (poison_address>>6)) begin
 if(avm_readdata[(poison_address&63)*8+:16] === poison_bits[15:0])
  poison_seen=poison_seen+1;
end
""")
        bench = bench.replace(
            "writes!==(WRITE_FAULT_VALUE<0 ? IMAGE_LAST+1 : WRITE_FAULT_VALUE+1)",
            "writes!==(uploads_completed*(IMAGE_LAST+1) + "
            "(WRITE_FAULT_VALUE<0 ? IMAGE_LAST+1 : WRITE_FAULT_VALUE+1))")
        bench = bench.replace(
            "  repeat (30) edge_tick();\n end\nendtask",
            "  uploads_completed=uploads_completed+1;\n"
            "  repeat (30) edge_tick();\n end\nendtask")
        bench = bench.replace("load_accepts!==IMAGE_LAST+1",
                              "load_accepts!==uploads_completed*(IMAGE_LAST+1)")
        bench = bench.replace(' $readmemh("IMAGE_PATH",image);', r"""
 if(!$value$plusargs("NUMERICAL_ADDRESS=%d",poison_address) ||
    !$value$plusargs("NUMERICAL_BITS=%d",poison_bits) ||
    !$value$plusargs("ORIGINAL_BITS=%d",original_bits))
  $fatal(1,"NUMERICAL_MISSING_FAULT_INPUTS");
 $readmemh("IMAGE_PATH",image);
""")
        inference = r"""
 @(negedge clk);
 token_id=token_words[0][31:0];token_pos=0;new_sequence=1;token_valid=1;logit_ready=1;
 if(token_ready!==1) $fatal(1,"NUMERICAL_TOKEN_NOT_READY");
 edge_tick();
 if(token_ready!==0 || done!==0 || logit_valid!==0)
  $fatal(1,"NUMERICAL_ACCEPT_EDGE");
 @(negedge clk);token_valid=0;
 timeout_cycles=0;
 while(done!==1 && timeout_cycles<10000000) begin
  edge_tick();
  if(logit_valid!==0) $fatal(1,"NUMERICAL_FAULT_PUBLISHED_LOGIT");
  if((^{done,error,logit_valid,token_ready})===1'bx)
   $fatal(1,"NUMERICAL_ACTIVE_XZ");
  timeout_cycles=timeout_cycles+1;
 end
 if(done!==1 || error!==1 || poison_seen<1 || outstanding!==0 ||
    response_writes!==writes || avm_read!==0 || avm_write!==0)
  $fatal(1,"NUMERICAL_NO_DRAINED_ERROR_COMPLETION seen=%0d done=%b error=%b pending=%0d",
         poison_seen,done,error,outstanding);
 repeat(30) begin
  edge_tick();
  if(done!==0 || error!==0 || logit_valid!==0 || token_ready!==0 ||
     outstanding!==0 || avm_read!==0 || avm_write!==0)
   $fatal(1,"NUMERICAL_FAULT_FALSE_SUCCESS_OR_UNSETTLED");
 end
 csr(0,16'h0004,0,0,32'h0000000c);
 csr(1,16'h0008,1,0,0);
 csr(1,16'h0008,4,0,0);
 image[poison_address>>6][(poison_address&63)*8+:16]=original_bits[15:0];
 upload();
 csr(1,16'h0008,2,0,0);
 repeat(30) edge_tick();
 if(token_ready!==1) $fatal(1,"NUMERICAL_REPAIRED_IMAGE_NOT_READY");
 run_token(token_words[0][31:0],0,1'b1,token_words[0][65+:VOCAB_VALUE*32]);
 $display("CHECKS_PASSED numerical_fault poison_seen=%0d error_completion=1 drained=1 recovery_logits=%0d",
          poison_seen,logits);
 $finish;
"""
    if fault_read >= 0:
        inference = r"""
 @(negedge clk);token_id=1;token_pos=0;new_sequence=1;token_valid=1;
 if(token_ready!==1) $fatal(1,"FAULT_TEST_TOKEN_NOT_READY");
 edge_tick();
 @(negedge clk);token_valid=0;
 timeout_cycles=0;
 while(done!==1 && timeout_cycles<10000000) begin
  edge_tick();
  if(logit_valid!==0) $fatal(1,"READ_FAULT_PUBLISHED_LOGIT");
  timeout_cycles=timeout_cycles+1;
 end
 if(done!==1 || error!==1 || reads<=READ_FAULT_VALUE || outstanding!==0)
  $fatal(1,"READ_FAULT_NO_DRAINED_ERROR_COMPLETION");
 edge_tick();
 if(done!==0 || error!==0 || logit_valid!==0) $fatal(1,"READ_FAULT_COMPLETION_NOT_ONE_CYCLE");
 csr(0,16'h0004,0,0,32'h0000000c);
 csr(1,16'h0008,4,0,0);
 repeat(30) edge_tick();
 RECOVERY_TOKEN
 $display("CHECKS_PASSED read_fault beat=%0d reads=%0d recovered_logits=%0d",
          READ_FAULT_VALUE,reads,logits);
 $finish;
"""
        id, position, new, expected = tokens[0]
        inference = inference.replace(
            "RECOVERY_TOKEN", (
                "run_token(token_words[0][31:0],token_words[0][63:32],1'b1,"
                "token_words[0][65+:VOCAB_VALUE*32]);" if reusable_build else
                f"run_token(32'd{id},32'd{position},1'b1,"
                f"{hx(packed(expected,32),32*shape.vocab)});"))
    if orphan_fault:
        inference = r"""
 @(negedge clk);token_id=1;token_pos=0;new_sequence=0;token_valid=1;
 if(token_ready!==1) $fatal(1,"ORPHAN_TOKEN_NOT_READY");
 edge_tick();
 inject_orphan=1;
 @(negedge clk);token_valid=0;
 timeout_cycles=0;
 while(done!==1 && timeout_cycles<10000) begin
  edge_tick();
  if(logit_valid!==0) $fatal(1,"ORPHAN_FAULT_PUBLISHED_LOGIT");
  timeout_cycles=timeout_cycles+1;
 end
 if(orphan_sent!==1) $fatal(1,"ORPHAN_RESPONSE_NOT_INJECTED");
 if(done!==1 || error!==1) begin
  csr(0,16'h0004,0,0,32'h0000000e);
  $fatal(1,"ORPHAN_FAULT_NO_ERROR_COMPLETION after_core_edges=%0d token_ready=%b done=%b error=%b reads=%0d outstanding=%0d avm_read=%b avm_write=%b; CSR confirmed BUSY|IMAGE_VALID|ERROR",
          timeout_cycles,token_ready,done,error,reads,outstanding,avm_read,avm_write);
 end
 if(outstanding!==0) $fatal(1,"ORPHAN_FAULT_COMPLETED_BEFORE_DRAIN");
 edge_tick();
 if(done!==0 || error!==0) $fatal(1,"ORPHAN_COMPLETION_NOT_ONE_CYCLE");
 $display("CHECKS_PASSED orphan_fault no_logits=1 drained=1 error_completion=1");
 $finish;
"""
    if abort_stage:
        stage_condition = {
            "embedding-pending": "target_commands>0",
            "kernel": "target_commands>0",
            "projection": "target_commands>0",
            "waitrequest": "command_stall_started",
            "stalled-logit": "logit_valid===1",
        }[abort_stage]
        wait_for_stage = {
            "embedding-pending": r"""
 @(negedge clk);inject_unowned_write=1;
""",
            "kernel": r"""
 @(negedge clk);inject_unowned_write=1;
""",
            "projection": r"""
 @(negedge clk);inject_unowned_write=1;
""",
            "waitrequest": r"""
""",
            "stalled-logit": r"""
 @(negedge clk);
 if(logit_index!==0 || logit_data!==FIRST_EXPECTED)
   $fatal(1,"ABORT_STALLED_LOGIT_NUMERICAL_PRECONDITION");
 repeat(7) begin
   edge_tick();
   timeout_cycles=timeout_cycles+1;
   if(logit_valid!==1 || logit_index!==0 || logit_data!==FIRST_EXPECTED || done!==0)
     $fatal(1,"ABORT_STALLED_LOGIT_PRECONDITION");
 end
 @(negedge clk);inject_unowned_write=1;
""",
        }[abort_stage]
        inference = r"""
 @(negedge clk);token_id=FIRST_TOKEN;token_pos=0;new_sequence=0;token_valid=1;
 if(token_ready!==1) $fatal(1,"ABORT_TOKEN_NOT_READY");
 edge_tick();
 @(negedge clk);token_valid=0;logit_ready=0;
 timeout_cycles=0;
 while(!(STAGE_CONDITION) && timeout_cycles<10000000) begin
   edge_tick();timeout_cycles=timeout_cycles+1;
 end
 if(!(STAGE_CONDITION)) $fatal(1,"ABORT_STAGE_NOT_OBSERVED stage=ABORT_STAGE");
 WAIT_FOR_STAGE
 while(!unowned_write_sent && timeout_cycles<10000000) begin
   edge_tick();timeout_cycles=timeout_cycles+1;
 end
 if(!unowned_write_sent) $fatal(1,"ABORT_FAULT_NOT_INJECTED stage=ABORT_STAGE");
 // The crossed fault may take several compute edges to reach the public output.
 timeout_cycles=0;
 while(done!==1 && timeout_cycles<10000) begin
   edge_tick();
   if((^{done,error,token_ready,logit_valid})===1'bx) $fatal(1,"ABORT_ACTIVE_XZ");
   if(error && !done) $fatal(1,"ABORT_ERROR_WITHOUT_COMPLETION");
   timeout_cycles=timeout_cycles+1;
 end
 if(done!==1 || error!==1 || logit_valid!==0 || outstanding!==0 ||
    avm_read!==0 || avm_write!==0 || held_command!==0)
   $fatal(1,"ABORT_NOT_DRAINED stage=ABORT_STAGE done=%b error=%b outstanding=%0d avm_read=%b avm_write=%b held=%b",
          done,error,outstanding,avm_read,avm_write,held_command);
 if(ABORT_PENDING_READ && fault_with_pending_read!==1)
   $fatal(1,"ABORT_PENDING_READ_NOT_OBSERVED");
 repeat(50) begin
   edge_tick();
   if(done!==0 || error!==0 || logit_valid!==0 || token_ready!==0 ||
      avm_read!==0 || avm_write!==0)
     $fatal(1,"ABORT_DUPLICATE_COMPLETION_OR_LATE_TRAFFIC stage=ABORT_STAGE");
 end
 csr(0,16'h0004,0,0,32'h0000000c);
 $display("CHECKS_PASSED abort_stage=ABORT_STAGE injected_unowned_write=1 drained=1 error_completion=1 target_commands=%0d waitrequest_seen=%0d pending_read_seen=%0d",
          target_commands,command_stall_started,fault_with_pending_read);
 $finish;
"""
        inference = inference.replace("STAGE_CONDITION", stage_condition).replace(
            "WAIT_FOR_STAGE", wait_for_stage).replace(
            "ABORT_STAGE", abort_stage).replace(
            "FIRST_TOKEN", "token_words[0][31:0]" if reusable_build else str(tokens[0][0])).replace(
            "FIRST_EXPECTED", "token_words[0][65+:32]" if reusable_build else hx(tokens[0][3][0], 32))
    after_upload = ""
    if fault_write >= 0:
        after_upload = r"""
 if(token_ready!==0 || load_ready!==0 || load_error!==1 || reads!==0)
  $fatal(1,"WRITE_FAULT_ENABLED_INFERENCE_OR_UPLOAD");
 csr(0,16'h0004,0,0,32'h00000008);
 repeat(30) begin
  edge_tick();
  if(done!==0 || logit_valid!==0 || token_ready!==0) $fatal(1,"WRITE_FAULT_FALSE_INFERENCE_SUCCESS");
 end
 $display("CHECKS_PASSED write_fault beat=%0d acknowledged_writes=%0d image_invalid=1",
          WRITE_FAULT_VALUE,writes);
 $finish;
"""
    target_kind = {"embedding-pending": 0, "kernel": 5, "projection": 1}.get(abort_stage, 0)
    target = next(descriptor for descriptor in model.descriptors
                  if descriptor[1:4] == (target_kind, 0, 0))
    runtime_args = ()
    reusable = reusable_build
    if reusable:
        from verify import file_sha256

        capacity = max(len(EngineeringModel(shape, 0, precision).image) // 64
                       for precision in ("AWQ", "BF16"))
        descriptor_words = []
        for index, kind, layer, proj, base, length in model.descriptors:
            descriptor_words.extend(
                (address << 32) | value for address, value in (
                    (0x10, index), (0x14, kind), (0x18, layer), (0x1c, proj),
                    (0x20, base & 0xffffffff), (0x24, base >> 32),
                    (0x28, length), (0x2c, 1)))
        runtime_files = {
            "case.hex": "".join(f"{word:08x}\n" for word in (
                int(mode == "BF16"), len(model.image) // 64,
                len(descriptor_words), len(tokens), fault_read & 0xffffffff,
                fault_write & 0xffffffff, target[4] & 0xffffffff, target[4] >> 32,
                (target[4] + target[5]) & 0xffffffff, (target[4] + target[5]) >> 32)),
            "descriptors.hex": "".join(f"{word:012x}\n" for word in descriptor_words),
            "tokens.hex": "".join(
                format((packed(expected,32) << 65) | (int(new) << 64) |
                       (position << 32) | id, f"0{(32 * shape.vocab + 68) // 4}x") + "\n"
                for id, position, new, expected in tokens),
        }
        for filename, text in runtime_files.items():
            (case_folder / filename).write_text(text)
        input_hashes = {
            evidence.relative(path): file_sha256(path)
            for path in [image, *(case_folder / name for name in runtime_files)]
        }
        evidence.record.setdefault("runtime_input_sha256", {}).update(input_hashes)
        runtime_case["input_sha256"] = input_hashes
        bench = bench.replace(
            "integer response_writes=0;", r"""
integer response_writes=0;
string case_directory,mode_name;
reg [31:0] case_header [0:9];
reg [47:0] descriptor_words [0:2047];
reg [VOCAB_BITS_MINUS_ONE+65:0] token_words [0:MAX_TOKENS_MINUS_ONE];
integer image_beats,descriptor_count,token_count,case_index;
integer read_fault_value,write_fault_value;
reg [32:0] target_base;
reg [33:0] target_end;
task read_case;
 begin
  if(!$value$plusargs("CASE_DIR=%s",case_directory)) $fatal(1,"MISSING_CASE_DIRECTORY");
  $readmemh({case_directory,"/case.hex"},case_header);
  image_beats=case_header[1];descriptor_count=case_header[2];token_count=case_header[3];
  read_fault_value=$signed(case_header[4]);write_fault_value=$signed(case_header[5]);
  target_base={case_header[7][0],case_header[6]};
  target_end={case_header[9][1:0],case_header[8]};
  if(case_header[0]>1 || image_beats<1 || image_beats>IMAGE_CAPACITY ||
     descriptor_count<1 || descriptor_count>2048 ||
     token_count<1 || token_count>MAX_TOKENS) $fatal(1,"INVALID_CASE_HEADER");
  mode_name=case_header[0] ? "BF16" : "AWQ";
  $readmemh({case_directory,"/image.hex"},image,0,image_beats-1);
  $readmemh({case_directory,"/descriptors.hex"},descriptor_words,0,descriptor_count-1);
  $readmemh({case_directory,"/tokens.hex"},token_words,0,token_count-1);
 end
endtask
""")
        bench = bench.replace('$readmemh("IMAGE_PATH",image);', "read_case();")
        runtime_inference = r"""
 for(case_index=0;case_index<token_count;case_index=case_index+1)
  run_token(token_words[case_index][31:0],token_words[case_index][63:32],
            token_words[case_index][64],token_words[case_index][65+:VOCAB_VALUE*32]);
 $display("CHECKS_PASSED top mode=%s logits=%0d reads=%0d preload_beats=%0d csr_compares=%0d",
          mode_name,logits,reads,load_accepts,csr_compares);
 $finish;
"""
        bench = bench.replace("DESCRIPTOR_CALLS", r"""
 csr(1,16'h000c,case_header[0],0,0);
 for(case_index=0;case_index<descriptor_count;case_index=case_index+1)
  csr(1,descriptor_words[case_index][47:32],descriptor_words[case_index][31:0],0,0);
""")
        if not (upload_only or fault_read >= 0 or fault_write >= 0 or orphan_fault or abort_stage
                or numerical_fault is not None or command_validation or pending_upload_validation
                or reset_validation or late_read_fault):
            bench = bench.replace("AFTER_COMMIT", runtime_inference)
        else:
            bench = bench.replace("AFTER_COMMIT", inference)
        bench = bench.replace("AFTER_UPLOAD", after_upload)
        bench = bench.replace(
            '$display("TOKEN_COMPARED mode=MODE position=',
            '$display("TOKEN_COMPARED mode=%s position=').replace(
                "position,sequence_start,token_logits,cycles,reads);",
                "mode_name,position,sequence_start,token_logits,cycles,reads);")
        # Array bounds are geometry-only; case-specific upload lengths stay runtime data.
        bench = bench.replace("[0:IMAGE_LAST]", "[0:IMAGE_CAPACITY_MINUS_ONE]")
        bench = bench.replace("IMAGE_LAST", "(image_beats-1)")
        for old, new in {
            "IMAGE_CAPACITY_MINUS_ONE": str(capacity - 1),
            "IMAGE_CAPACITY": str(capacity),
            "MEMORY_LAST": str(capacity + 63),
            "MAX_TOKENS_MINUS_ONE": str(min(shape.max_seq, shape.window + 2)),
            "MAX_TOKENS": str(min(shape.max_seq, shape.window + 2) + 1),
            "TARGET_BASE": "target_base", "TARGET_END": "target_end",
            "READ_FAULT_VALUE": "read_fault_value", "WRITE_FAULT_VALUE": "write_fault_value",
        }.items():
            bench = bench.replace(old, new)
        runtime_args = ("+CASE_DIR=" + evidence.relative(case_folder),)
        if poisoned is not None:
            runtime_args += (
                "+NUMERICAL_ADDRESS=" + str(poisoned["byte_address"]),
                "+NUMERICAL_BITS=" + str(poisoned["invalid_bits"]),
                "+ORIGINAL_BITS=" + str(poisoned["original_bits"]),
            )
    replacements = {
        "AFTER_COMMIT": inference.replace("MODE", mode),
        "AFTER_UPLOAD": after_upload,
        "IMAGE_LAST": str(len(model.image) // 64 - 1),
        "MEMORY_LAST": str(len(model.image) // 64 + 63),
        "IMAGE_PATH": evidence.relative(image),
        "DESCRIPTOR_CALLS": "\n".join(calls),
        "LAYERS_VALUE": str(shape.layers),
        "HIDDEN_VALUE": str(shape.hidden),
        "INTERMEDIATE_VALUE": str(shape.intermediate),
        "QHEADS_VALUE": str(shape.qheads),
        "KVHEADS_VALUE": str(shape.kvheads),
        "HEAD_VALUE": str(shape.head_dim),
        "GROUP_VALUE": str(shape.group),
        "VOCAB_VALUE": str(shape.vocab),
        "VOCAB_BITS_MINUS_ONE": str(shape.vocab * 32 - 1),
        "SEQ_VALUE": str(shape.max_seq),
        "TILE_VALUE": str(shape.tile),
        "WINDOW_VALUE": str(shape.window),
        "MODE": mode,
        "READ_FAULT_VALUE": str(fault_read),
        "WRITE_FAULT_VALUE": str(fault_write),
        "TARGET_BASE": hx(target[4], 33),
        "TARGET_END": hx(target[4] + target[5], 34),
        "ABORT_WAITREQUEST": str(int(abort_stage == "waitrequest")),
        "ABORT_PENDING_READ": str(int(abort_stage in ("embedding-pending", "kernel", "projection"))),
    }
    for old, new in replacements.items():
        bench = bench.replace(old, new)
    evidence.record["engineering_fixture"] = {
        "kind": "synthetic_parameter_test_not_checkpoint",
        "mode": mode, "seed": seed, "image_bytes": len(model.image),
        "shape": vars(shape),
        "tokens": tokens,
        "read_fault_beat": fault_read,
        "write_fault_beat": fault_write,
        "orphan_response_fault": orphan_fault,
        "abort_stage": abort_stage,
        "numerical_fault": poisoned,
        "command_validation": command_validation,
        "pending_upload_validation": pending_upload_validation,
        "reset_validation": reset_validation,
        "late_read_fault": late_read_fault,
        "descriptors": model.descriptors,
    }
    runtime_case["engineering_fixture"] = evidence.record["engineering_fixture"]
    evidence.flush()
    name = "top-" + mode.lower() + ("-" + abort_stage if abort_stage else "")
    if simulator == "verilator":
        evidence.simulate(name + "-four-state-reset", bench, defines=("RESET_ONLY",),
                          simulator="iverilog", runtime_args=runtime_args)
        evidence.record["integration_simulator"] = {
            "functional": "Verilator timing simulation with unchanged numerical/protocol assertions",
            "four_state": "Icarus full-hierarchy time-zero and both-clock-edge reset assertions",
            "limitation": "Verilator functional data is two-state; no full-campaign four-state proof claimed",
            "reset_delta": "Icarus #0 reset sample; Verilator same-time initial reset sample without #0",
        }
        evidence.flush()
    evidence.simulate(name, bench, simulator=simulator, timeout=43200,
                      cxx_optimization=cxx_optimization, flatten=flatten,
                      runtime_args=runtime_args,
                      build_pool=getattr(evidence, "simulation_build_pool", None))


def kernel_default(evidence, seed):
    """Full-width D4 kernels against equations, using only logical-memory pins."""
    rng = random.Random(seed)
    hidden, intermediate, kv, head_dim, positions = 896, 4864, 128, 64, 3
    scratch_words = 15 * intermediate
    cache_words = 2 * positions * kv
    gamma_base, rope_base = scratch_words + cache_words, scratch_words + cache_words + 3 * hidden
    words = rope_base + head_dim
    calls = []
    expectations = []

    def scratch(slot, column):
        return slot * intermediate + column

    def cache(value, position, column):
        return scratch_words + (value * positions + position) * kv + column

    def dump(name, values, bits=32):
        path = evidence.folder / name
        path.write_text("".join(f"{value & ((1 << bits)-1):0{(bits+3)//4}x}\n"
                                for value in values))
        return evidence.relative(path)

    for operation in range(8):
        memory = [0] * words
        for slot in range(15):
            for column in range(intermediate):
                memory[scratch(slot, column)] = rng.randrange(-524288, 524289)
        for column, value in enumerate((-(1 << 31), (1 << 31)-1, -32768, 32768)):
            for slot in (0, 6, 7, 12):
                memory[scratch(slot, column)] = value
        gammas = [rng.choice((0x0001, 0x8000, 0x3800, 0x3c00, 0xbc00))
                  for _ in range(3 * hidden)]
        memory[gamma_base:rope_base] = gammas
        rope = []
        for pair in range(head_dim // 2):
            angle = 2.0 / (10000.0 ** (2 * pair / head_dim))
            rope.extend((round(math.cos(angle) * (1 << 30)),
                         round(math.sin(angle) * (1 << 30))))
        memory[rope_base:] = rope
        for value in range(2):
            for position in range(positions):
                for column in range(kv):
                    memory[cache(value, position, column)] = rng.randrange(-65536, 65537)
        expected = {}

        def vector(slot, width):
            return memory[scratch(slot, 0):scratch(slot, 0) + width]

        def output(slot, values):
            expected.update((scratch(slot, column), value) for column, value in enumerate(values))

        if operation < 3:
            source, target = ((0, 1), (7, 8), (0, 14))[operation]
            output(target, norm(vector(source, hidden),
                                gammas[operation * hidden:(operation + 1) * hidden]))
        elif operation == 3:
            for slot, heads in ((2, 14), (3, 2)):
                values = vector(slot, heads * head_dim)
                result = values.copy()
                for head in range(heads):
                    for pair in range(head_dim // 2):
                        lo, hi = head * head_dim + pair, head * head_dim + pair + head_dim // 2
                        x, y = values[lo], values[hi]
                        cosine, sine = rope[2 * pair:2 * pair + 2]
                        result[lo] = sat32(round_shift(x * cosine - y * sine, 30))
                        result[hi] = sat32(round_shift(y * cosine + x * sine, 30))
                output(slot, result)
        elif operation in (4, 5):
            left, right, target = (0, 6, 7) if operation == 4 else (7, 12, 0)
            output(target, [sat32(a + b) for a, b in zip(vector(left, hidden),
                                                        vector(right, hidden))])
        elif operation == 6:
            output(11, [sat32(round_shift(silu(gate) * up, 16))
                        for gate, up in zip(vector(9, intermediate), vector(10, intermediate))])
        else:
            from reference import exp_q24
            for value, slot in ((0, 3), (1, 4)):
                for column, data in enumerate(vector(slot, kv)):
                    expected[cache(value, positions - 1, column)] = data
            history = dict(expected)
            context = []
            query = vector(2, hidden)
            for head in range(14):
                kvhead = head // 7
                scores = []
                for position in range(positions):
                    dot = sum(query[head * head_dim + dim] *
                              history.get(cache(0, position, kvhead * head_dim + dim),
                                          memory[cache(0, position, kvhead * head_dim + dim)])
                              for dim in range(head_dim))
                    scores.append(signed(round_div(signed(dot, 96),
                                                   math.isqrt(head_dim << 32)), 96))
                maximum = max(scores)
                exps = [exp_q24(score - maximum) for score in scores]
                for dim in range(head_dim):
                    weighted = sum(
                        history.get(cache(1, position, kvhead * head_dim + dim),
                                    memory[cache(1, position, kvhead * head_dim + dim)]) * exponential
                        for position, exponential in enumerate(exps))
                    context.append(sat32(round_div(signed(weighted, 96), sum(exps))))
            output(5, context)
        reference = [0] * words
        mask = [0] * words
        for address, value in expected.items():
            reference[address], mask[address] = value, 1
        image = dump(f"kernel-{operation}-input.hex", memory)
        result = dump(f"kernel-{operation}-expected.hex", reference)
        valid = dump(f"kernel-{operation}-mask.hex", mask, 1)
        calls.append(f'run({operation}, "{image}", "{result}", "{valid}", {len(expected)});')
        expectations.append({"operation": operation, "expected_write_comparisons": len(expected)})

    bench = CLOCK + r"""
localparam STRIDE=4864,HIDDEN=896,KV=128,POSITIONS=3;
localparam SCRATCH=15*STRIDE,GAMMA=SCRATCH+2*POSITIONS*KV,ROPE=GAMMA+3*HIDDEN,WORDS=ROPE+64;
reg cmd_valid=0,mem_req_ready=0,mem_rsp_valid=0;
reg [2:0] cmd_op=0;
wire cmd_ready,done,error,mem_req_valid,mem_req_write,mem_rsp_ready;
wire [3:0] mem_req_kind;
wire [31:0] mem_req_layer,mem_req_row,mem_req_col,mem_req_wdata;
wire [2:0] mem_req_proj;
reg [31:0] mem_rsp_rdata=0;
reg [31:0] memory[0:WORDS-1],expected[0:WORDS-1];
reg wanted[0:WORDS-1],seen[0:WORDS-1];
integer address,cycles=0,pending=0,compares=0,total=0,completed=0;
reg [31:0] response_data=0;
reg held=0;
reg [135:0] held_payload;
wire [135:0] payload={mem_req_write,mem_req_kind,mem_req_layer,mem_req_proj,
                     mem_req_row,mem_req_col,mem_req_wdata};
anvil_q1_ht_kernel product(
 .clk(clk),.rst_n(rst_n),.abort_error(1'b0),.cmd_valid(cmd_valid),.cmd_ready(cmd_ready),
 .cmd_op(cmd_op),.cmd_layer(32'd23),.cmd_pos(32'd2),.done(done),.error(error),
 .mem_req_valid(mem_req_valid),.mem_req_ready(mem_req_ready),.mem_req_write(mem_req_write),
 .mem_req_kind(mem_req_kind),.mem_req_layer(mem_req_layer),.mem_req_proj(mem_req_proj),
 .mem_req_row(mem_req_row),.mem_req_col(mem_req_col),.mem_req_wdata(mem_req_wdata),
 .mem_rsp_valid(mem_rsp_valid),.mem_rsp_ready(mem_rsp_ready),
 .mem_rsp_rdata(mem_rsp_rdata),.mem_rsp_error(1'b0));
task reset_check;
 begin
  if({cmd_ready,done,error,mem_req_valid,payload,mem_rsp_ready}!==141'b0)
   $fatal(1,"KERNEL_RESET_XZ_OR_NONZERO");
 end
endtask
always @(posedge clk or negedge clk) if(!rst_n) reset_check();
always @(posedge clk) if(rst_n) begin
 if((^{cmd_ready,done,error,mem_req_valid,mem_rsp_ready})===1'bx)
  $fatal(1,"KERNEL_ACTIVE_XZ");
 if(held && (mem_req_valid!==1 || payload!==held_payload))
  $fatal(1,"KERNEL_REQUEST_CHANGED_UNDER_STALL");
 held=mem_req_valid && !mem_req_ready;
 if(held) held_payload=payload;
 if(mem_rsp_valid && mem_rsp_ready) pending=0;
 if(mem_req_valid && mem_req_ready) begin
  if(pending || (^payload)===1'bx || mem_req_proj!==0)
   $fatal(1,"KERNEL_MEMORY_PROTOCOL");
  case(mem_req_kind)
   8: begin
    if(mem_req_layer!==0 || mem_req_row>=15 || mem_req_col>=STRIDE)
     $fatal(1,"KERNEL_SCRATCH_ADDRESS");
    address=mem_req_row*STRIDE+mem_req_col;
   end
   5,6,7: begin
    if(mem_req_write || mem_req_row!==0 || mem_req_col>=HIDDEN ||
       mem_req_layer!==(mem_req_kind==7 ? 0 : 23)) $fatal(1,"KERNEL_GAMMA_ADDRESS");
    address=GAMMA+(mem_req_kind-5)*HIDDEN+mem_req_col;
   end
   9,10: begin
    if(mem_req_layer!==23 || mem_req_row>=POSITIONS || mem_req_col>=KV)
     $fatal(1,"KERNEL_CACHE_ADDRESS");
    address=SCRATCH+((mem_req_kind-9)*POSITIONS+mem_req_row)*KV+mem_req_col;
   end
   11: begin
    if(mem_req_write || mem_req_layer!==0 || mem_req_row!==2 || mem_req_col>=64)
     $fatal(1,"KERNEL_ROPE_ADDRESS");
    address=ROPE+mem_req_col;
   end
   default: $fatal(1,"KERNEL_UNEXPECTED_MEMORY_KIND");
  endcase
  if(mem_req_write) begin
   if(wanted[address]!==1 || seen[address]!==0 || mem_req_wdata!==expected[address])
    $fatal(1,"KERNEL_NUMERICAL_MISMATCH op=%0d address=%0d actual=%h expected=%h wanted=%b seen=%b",
           cmd_op,address,mem_req_wdata,expected[address],wanted[address],seen[address]);
   memory[address]=mem_req_wdata;
   seen[address]=1;
   compares=compares+1;
  end
  response_data=mem_req_write ? 0 : memory[address];
  pending=1;
 end
end
always @(negedge clk) begin
 cycles=cycles+1;
 mem_req_ready=rst_n && !pending && cycles%11>3;
 mem_rsp_valid=rst_n && pending;
 mem_rsp_rdata=mem_rsp_valid ? response_data : 0;
end
task run(input [2:0] operation,input string image,reference,mask,input integer count);
 integer i,elapsed;
 begin
  $readmemh(image,memory);$readmemh(reference,expected);$readmemh(mask,wanted);
  for(i=0;i<WORDS;i=i+1) seen[i]=0;
  compares=0;
  @(negedge clk);cmd_op=operation;cmd_valid=1;
  if(cmd_ready!==1) $fatal(1,"KERNEL_COMMAND_NOT_READY");
  edge_tick();
  if(cmd_ready!==0 || done!==0) $fatal(1,"KERNEL_COMMAND_ACCEPT_EDGE");
  @(negedge clk);cmd_valid=0;
  elapsed=0;
  while(done!==1 && elapsed<100000000) begin edge_tick();elapsed=elapsed+1;end
  if(done!==1 || error!==0 || compares!==count || pending!==0)
   $fatal(1,"KERNEL_COMPLETION_OR_COVERAGE op=%0d compares=%0d expected=%0d",operation,compares,count);
  for(i=0;i<WORDS;i=i+1)
   if(wanted[i]!==seen[i]) $fatal(1,"KERNEL_MISSING_OUTPUT");
  $display("TOKEN_COMPARED kernel_op=%0d comparisons=%0d cycles=%0d",operation,compares,elapsed);
  total=total+compares;completed=completed+1;
  edge_tick();
  if(done!==0 || error!==0 || cmd_ready!==1) $fatal(1,"KERNEL_COMPLETION_PULSE");
 end
endtask
initial begin
 rst_n=0;`RESET_DELTA reset_check();
 repeat(3) edge_tick();
 @(negedge clk);rst_n=1;
""" + "\n".join(calls) + r"""
 if(completed!==8 || total==0) $fatal(1,"KERNEL_MISSING_OPERATIONS");
 $display("CHECKS_PASSED kernel_default operations=%0d comparisons=%0d",completed,total);
 $finish;
end
endmodule
"""
    evidence.record["kernel_reference"] = {
        "scope": "D4_default_width_kernels_not_full_decoder_layer_or_checkpoint",
        "dimensions": {"layers": 24, "hidden": hidden, "intermediate": intermediate,
                       "qheads": 14, "kvheads": 2, "head_dim": head_dim},
        "seed": seed, "layer": 23, "position": 2, "expectations": expectations,
        "memory_service": "one response edge after acceptance; periodic request stalls",
    }
    evidence.flush()
    evidence.simulate("kernel-default", bench, timeout=14400, simulator="verilator")


def yosys_sources(evidence):
    """Normalize package syntax only; never abstract product logic or arithmetic."""
    package_path = evidence.folder / "sources/rtl/anvil_q1_ht_00_numeric_pkg.sv"
    package = package_path.read_text()
    body = package.split(";", 1)[1].rsplit("endpackage", 1)[0]
    substitutions = {
        "int'({1'b0, value[14:10]})": "$signed({1'b0, value[14:10]})",
        "int'({1'b0, value[14:7]})": "$signed({1'b0, value[14:7]})",
    }
    for old, new in substitutions.items():
        if body.count(old) != 1:
            raise AssertionError(f"unexpected package syntax: {old}")
        body = body.replace(old, new)
    normalized = evidence.folder / "yosys-input"
    normalized.mkdir()
    for original in sorted((evidence.folder / "sources/rtl").glob("*.sv")):
        if original.name == package_path.name:
            continue
        text = original.read_text()
        import_line = "import anvil_q1_ht_numeric_pkg::*;"
        qualified = "anvil_q1_ht_numeric_pkg::"
        if import_line in text:
            text = text.replace(import_line, body)
        elif qualified in text:
            header, remainder = text.split(");", 1)
            text = header + ");\n" + body + remainder
        text = text.replace(qualified, "")
        if original.name == "anvil_q1_ht_decoder.sv":
            text = re.sub(
                r"(?m)^(\s*)(reg\s+(?:signed\s+)?\[[^\]]+\]\s+\w+\s*\[0:[^\]]+\]\s*;)",
                r"\1(* nomem2reg *) \2",
                text,
            )
        (normalized / original.name).write_text(text)
    evidence.record["yosys_frontend_adapter"] = {
        "operations": ["inline numerical package definitions in referencing modules",
                       "remove package qualification after local definition",
                       "replace the two zero-prefixed positive exponent int casts by signed casts"],
        "substitutions": substitutions,
        "behavior_check": "all 65536 FP16 scales and all 65536 BF16 encodings, independent oracle",
        "original_failure": evidence.record["repair_of"],
        "not_a_primitive_abstraction": True,
    }
    evidence.flush()
    dequant(evidence, 17, normalized)
    return " ".join(evidence.relative(path) for path in sorted(normalized.glob("*.sv")))


def synthesis_fault_control(evidence):
    sources = yosys_sources(evidence)
    parameters = {
        "NUM_LAYERS": 1, "HIDDEN_SIZE": 8, "INTERMEDIATE_SIZE": 8,
        "NUM_Q_HEADS": 1, "NUM_KV_HEADS": 1, "HEAD_DIM": 8, "MAX_SEQ_LEN": 1,
    }
    for top in ("anvil_q1_ht_kernel", "anvil_q1_ht_decoder"):
        if top.endswith("decoder"):
            parameters.update(GROUP_SIZE=1, VOCAB_SIZE=8)
        options = "".join(f" -chparam {key} {value}" for key, value in parameters.items())
        script = evidence.folder / (top + ".ys")
        script.write_text(
            f"read_verilog -sv -defer {sources}\n"
            f"hierarchy -check -top {top}{options}\n"
            "proc\nopt\ncheck -assert\n"
            "select -assert-none t:$dlatch t:$adlatch t:$div t:$mod t:$divfloor t:$modfloor\n")
        evidence.command(["yosys", "-l", evidence.relative(evidence.folder / (top + "-tool.log")),
                          "-s", evidence.relative(script)], top)
        evidence.record["observations"].append({
            "scope": "focused_fault_control_synthesis_not_full_product",
            "top": top, "parameters": dict(parameters),
            "process_synthesis_completed": True, "latches": 0, "runtime_div_mod": 0,
        })
        evidence.flush()


def synthesis_probe(evidence, shape=None):
    sources = yosys_sources(evidence)
    output = evidence.folder / "synthesis.json"
    script = evidence.folder / "synthesis.ys"
    parameters = ""
    if shape is not None:
        names = ("NUM_LAYERS", "HIDDEN_SIZE", "INTERMEDIATE_SIZE", "NUM_Q_HEADS",
                 "NUM_KV_HEADS", "HEAD_DIM", "GROUP_SIZE", "VOCAB_SIZE", "MAX_SEQ_LEN",
                 "TILE_BEATS", "KV_WINDOW")
        parameters = "".join(f" -chparam {name} {value}"
                             for name, value in zip(names, vars(shape).values()))
    script.write_text(
        f"read_verilog -sv -defer {sources}\n"
        f"hierarchy -check -top anvil_q1_ht_top{parameters}\n"
        "proc\nopt\nmemory_dff\nmemory_collect\nopt_clean\ncheck -assert\n"
        "select -assert-none t:$dlatch t:$adlatch t:$div t:$mod t:$divfloor t:$modfloor\n"
        f"write_json {evidence.relative(output)}\nstat\n")
    evidence.command(["yosys", "-s", evidence.relative(script)], "synthesis",
                     timeout=14400 if shape is None else 3600)
    design = json.loads(output.read_text())
    modules = design["modules"]
    top = modules["anvil_q1_ht_top"]
    expected = {
        "u_dma": "anvil_q1_ht_weight_dma",
        "u_tiles": "anvil_q1_ht_weight_tiles",
        "u_tensor": "anvil_q1_ht_tensor_array",
        "u_kv": "anvil_q1_ht_kv_window",
        "u_decoder": "anvil_q1_ht_decoder",
    }

    def identity(module):
        return module.get("attributes", {}).get("hdlname", "").split()[0].lstrip("\\")

    def child(module, instance):
        if instance not in module.get("cells", {}):
            raise AssertionError(f"missing real hierarchy instance: {instance}")
        result = modules[module["cells"][instance]["type"]]
        return result

    def integer(parameter):
        return int(parameter, 2) if isinstance(parameter, str) else parameter

    for instance, required in expected.items():
        if identity(child(top, instance)) != required:
            raise AssertionError(f"wrong module identity for {instance}")
    tensor_module = child(top, "u_tensor")
    multipliers = 0
    for bank in range(8):
        for lane in range(8):
            mac = child(tensor_module, f"g_bank[{bank}].g_lane[{lane}].u_mac")
            if identity(mac) != "anvil_q1_ht_mac_lane":
                raise AssertionError("missing substantive MAC lane")
            cells = mac.get("cells", {}).values()
            products = [cell for cell in cells if cell["type"] == "$mul"]
            state_bits = {bit for cell in cells
                          if cell["type"] in ("$dff", "$adff", "$dffe", "$adffe", "$sdff", "$sdffe")
                          for bit in cell["connections"]["Q"] if isinstance(bit, int)}
            if len(products) < 4:
                raise AssertionError(f"lane {bank*8+lane}: registered partial multipliers lost")
            for accumulator in ("accumulator_s", "accumulator_c"):
                bits = mac["netnames"][accumulator]["bits"]
                if len(bits) != 128 or sum(bit in state_bits for bit in bits if isinstance(bit, int)) < 120:
                    raise AssertionError(f"lane {bank*8+lane}: exact accumulator state lost")
            multipliers += len(products)
    tiles = child(top, "u_tiles")
    stores = []
    tile_depth = shape.tile if shape else 256
    for bank in range(2):
        storage = child(tiles, f"g_legal.g_bank[{bank}].u_storage")
        memories = [cell for cell in storage.get("cells", {}).values()
                    if cell["type"] == "$mem_v2"
                    and integer(cell["parameters"]["WIDTH"]) == 512
                    and integer(cell["parameters"]["SIZE"]) == tile_depth]
        if len(memories) != 1:
            raise AssertionError(f"substantive distinct tile bank {bank} not retained")
        stores.append(integer(memories[0]["parameters"]["SIZE"]) * 512)
    kv = child(top, "u_kv")
    kv_words = shape.layers * shape.window * shape.kv if shape else 24 * 128 * 128
    cache_stores = [cell for cell in kv.get("cells", {}).values() if cell["type"] == "$mem_v2"
                    and integer(cell["parameters"]["WIDTH"]) == 32
                    and integer(cell["parameters"]["SIZE"]) == kv_words]
    if len(cache_stores) != 2:
        raise AssertionError("default K and V SRAMs not retained")
    forbidden = {"$dlatch", "$adlatch", "$div", "$mod", "$divfloor", "$modfloor"}
    for module in modules.values():
        if any(cell["type"] in forbidden for cell in module.get("cells", {}).values()):
            raise AssertionError("latch or runtime division/modulo cell remains")
    evidence.record["observations"].append({
        "scope": ("generic_Yosys_reduced_hierarchy_not_default_acceptance"
                  if shape else "generic_Yosys_default_hierarchy_not_Quartus_mapping_or_STA"),
        "shape": vars(shape) if shape else "full_default",
        "mac_lanes": 64, "lane_partial_multipliers": multipliers, "weight_bank_bits": stores,
        "kv_data_bytes": kv_words * 2 * 4,
        "latches": 0, "runtime_div_mod": 0,
    })
    evidence.flush()


def invalid_parameters(evidence):
    base = dict(zip(("NUM_LAYERS", "HIDDEN_SIZE", "INTERMEDIATE_SIZE", "NUM_Q_HEADS",
                     "NUM_KV_HEADS", "HEAD_DIM", "GROUP_SIZE", "VOCAB_SIZE", "MAX_SEQ_LEN",
                     "TILE_BEATS", "KV_WINDOW"), vars(MATRIX[1]).values()))
    cases = [{name: 0} for name in base]
    cases += [{"NUM_Q_HEADS": 2}, {"NUM_KV_HEADS": 2}, {"LANES": 32}, {"BANKS": 4},
              {"LANES_PER_BANK": 4}, {"DDR_WIDTH": 256}, {"AWQ_BITS": 8},
              {"GROUP_SIZE": 7}, {"TILE_BEATS": 257}, {"KV_WINDOW": 129},
              {"KV_WINDOW": 10}, {"HEAD_DIM": 7}, {"NUM_LAYERS": 25},
              {"HIDDEN_SIZE": 904}, {"INTERMEDIATE_SIZE": 4872},
              {"NUM_Q_HEADS": 15}, {"NUM_KV_HEADS": 3}, {"HEAD_DIM": 66},
              {"VOCAB_SIZE": 151937}, {"MAX_SEQ_LEN": 32769}]
    for index, changes in enumerate(cases):
        parameters = dict(base, **changes)
        arguments = ",".join(f".{name}({value})" for name, value in parameters.items())
        directory = evidence.folder / f"parameters-{index}"
        directory.mkdir()
        tb = directory / "tb.sv"
        tb.write_text("module tb;\nanvil_q1_ht_top #(" + arguments +
                      ") product();\ninitial begin #100; $display(\"MISSING_DIAGNOSTIC\"); $finish; end\nendmodule\n")
        image = directory / "simulation.vvp"
        sources = [evidence.relative(path) for path in sorted((evidence.folder / "sources/rtl").glob("*.sv"))]
        evidence.command(["iverilog", "-g2012", "-Wall", "-s", "tb", "-o",
                          evidence.relative(image), *sources, evidence.relative(tb)],
                         f"parameters-{index}-compile")
        text = evidence.command(["vvp", evidence.relative(image)],
                                f"parameters-{index}-simulation", expected_codes=(1,))
        if "PARAMETER ERROR" not in text or "MISSING_DIAGNOSTIC" in text:
            raise AssertionError(f"invalid parameter case lacks explicit rejection: {changes}")
        evidence.record["observations"].append({"invalid_parameters": changes,
                                               "compile_exit": 0, "diagnostic_exit": 1,
                                               "explicit_parameter_error": True})
        evidence.flush()


def kv_probe(evidence, depth, max_sequence=None, *, layers=2, head_dim=8):
    """Compare public KV words and spill traffic; full geometry uses compiled simulation."""
    max_sequence = depth + 2 if max_sequence is None else max_sequence
    if layers not in (2, 24) or head_dim not in (8, 64):
        raise ValueError("unsupported KV verification geometry")
    kv_width = 2 * head_dim
    bench = CLOCK + r"""
localparam WINDOW=DEPTH_VALUE, SEQUENCE=DEPTH_VALUE+2, MAXIMUM_SEQUENCE=SEQUENCE_VALUE;
localparam LAYERS=LAYERS_VALUE,HEAD_DIM=HEAD_DIM_VALUE,WIDTH=2*HEAD_DIM;
reg new_sequence=0,req_valid=0,req_write=0,req_value=0,rsp_ready=0;
reg [31:0] req_layer=0,req_head=0,req_pos=0,req_dim=0;
reg signed [31:0] req_wdata=0;
wire initialized,req_ready,rsp_valid,rsp_error,rsp_hit,protocol_error;
wire signed [31:0] rsp_data;
wire spill_valid,spill_write,spill_value,spill_rsp_ready;
wire [31:0] spill_layer,spill_pos,spill_col;
wire signed [31:0] spill_wdata;
reg spill_ready=0,spill_rsp_valid=0,spill_rsp_error=0;
reg signed [31:0] spill_rsp_data=0;
reg [31:0] backing [0:LAYERS*2*SEQUENCE*WIDTH-1];
reg present [0:LAYERS*2*SEQUENCE*WIDTH-1];
integer spill_reads=0,spill_writes=0,comparisons=0,hot_reads=0,cold_reads=0;
integer layer,position,value_bit,column,i,cycles=0,pending=0,pending_address=0;
integer startup_edges=0,sequence_edges=0,reset_compares=0,stale_rejections=0;
integer reset_aborts=0,reset_recoveries=0;
reg hold_spill_response=0;
integer hot_cycles=0,cold_cycles=0,hot_min=1000000,hot_max=0,cold_min=1000000,cold_max=0;
reg pending_write=0;
integer held_address;
reg held_spill=0;
reg [129:0] held_payload;
wire [129:0] spill_payload={spill_write,spill_value,spill_layer,spill_pos,spill_col,spill_wdata};
wire [31:0] backing_address=(((spill_layer*2+spill_value)*SEQUENCE+spill_pos)*WIDTH)+spill_col;
function automatic [31:0] expected_word(input integer l,p,c,v);
 begin expected_word=(l+1)*1000000+p*1000+c*10+v; end
endfunction
anvil_q1_ht_kv_window #(.NUM_LAYERS(LAYERS),.NUM_KV_HEADS(2),.HEAD_DIM(HEAD_DIM),
 .MAX_SEQ_LEN(MAXIMUM_SEQUENCE),.KV_WINDOW(WINDOW)) product(
 .clk(clk),.rst_n(rst_n),.new_sequence(new_sequence),.initialized(initialized),
 .req_valid(req_valid),.req_ready(req_ready),.req_write(req_write),.req_value(req_value),
 .req_layer(req_layer),.req_head(req_head),.req_pos(req_pos),.req_dim(req_dim),
 .req_wdata(req_wdata),.rsp_valid(rsp_valid),.rsp_ready(rsp_ready),
 .rsp_data(rsp_data),.rsp_error(rsp_error),.rsp_hit(rsp_hit),.protocol_error(protocol_error),
 .spill_valid(spill_valid),.spill_ready(spill_ready),.spill_write(spill_write),
 .spill_value(spill_value),.spill_layer(spill_layer),.spill_pos(spill_pos),
 .spill_col(spill_col),.spill_wdata(spill_wdata),.spill_rsp_valid(spill_rsp_valid),
 .spill_rsp_ready(spill_rsp_ready),.spill_rsp_data(spill_rsp_data),.spill_rsp_error(spill_rsp_error));
task check_reset;
 begin
  if ({initialized,req_ready,rsp_valid,rsp_data,rsp_error,rsp_hit,protocol_error,
       spill_valid,spill_write,spill_value,spill_layer,spill_pos,spill_col,
       spill_wdata,spill_rsp_ready} !== 171'b0) $fatal(1,"KV_RESET_XZ_OR_NONZERO");
  reset_compares=reset_compares+1;
 end
endtask
always @(posedge clk or negedge clk) if(!rst_n) check_reset();
task await_initialization(output integer elapsed);
 begin
  elapsed=0;
  while(initialized!==1 && elapsed<100000) begin
   if({initialized,req_ready,rsp_valid,protocol_error,spill_valid}!==5'b0)
    $fatal(1,"KV_STARTUP_TRANSACTION_OR_XZ");
   edge_tick();elapsed=elapsed+1;
  end
  if(initialized!==1 || req_ready!==1 || rsp_valid!==0 || protocol_error!==0)
   $fatal(1,"KV_INITIALIZATION_NOT_COMPLETED");
 end
endtask
always @(posedge clk) if(rst_n) begin
 if(held_spill && spill_payload!==held_payload) $fatal(1,"KV_SPILL_STALL_CHANGED");
 held_spill=spill_valid && !spill_ready;
 if(held_spill) held_payload=spill_payload;
 if(spill_valid && spill_ready) begin
  if(pending || spill_layer>=LAYERS || spill_col>=WIDTH || spill_pos>=SEQUENCE)
   $fatal(1,"KV_SPILL_OUTSTANDING_OR_SHAPE");
  pending=1;pending_address=backing_address;pending_write=spill_write;
  if(spill_write) begin
   if(spill_wdata!==expected_word(spill_layer,spill_pos,spill_col,spill_value))
    $fatal(1,"KV_EVICT_CORRUPTION");
   backing[backing_address]=spill_wdata;present[backing_address]=1;
   spill_writes=spill_writes+1;
  end else begin
   if(present[backing_address]!==1) $fatal(1,"KV_READ_UNSPILLED_CONTEXT");
   spill_reads=spill_reads+1;
  end
 end
 if(spill_rsp_valid && spill_rsp_ready) pending=0;
end
always @(negedge clk) begin
 cycles=cycles+1;
 spill_ready=rst_n && cycles%7>2 && !pending;
 spill_rsp_valid=rst_n && pending && !hold_spill_response && cycles%5==0;
 spill_rsp_data=pending && !pending_write ? backing[pending_address] : 0;
end
task transaction(input wr,input integer l,p,c,v,input expected_hit);
 integer waiting,before_reads,latency;
 reg [31:0] saved_data;
 reg saved_hit;
 begin
  @(negedge clk);
  req_valid=1;req_write=wr;req_layer=l;req_pos=p;req_head=c/HEAD_DIM;req_dim=c%HEAD_DIM;
  req_value=v;req_wdata=expected_word(l,p,c,v);
  before_reads=spill_reads;
  if(req_ready!==1) $fatal(1,"KV_REQUEST_NOT_READY");
  edge_tick();
  if(rsp_valid!==0) $fatal(1,"KV_PREMATURE_RESPONSE");
  @(negedge clk);req_valid=0;
  waiting=0;
  while(rsp_valid!==1 && waiting<10000) begin edge_tick();waiting=waiting+1;end
  if(rsp_valid!==1 || rsp_error!==0 || protocol_error!==0)
   $fatal(1,"KV_BAD_RESPONSE depth=%0d wr=%b layer=%0d pos=%0d col=%0d error=%b",
           WINDOW,wr,l,p,c,rsp_error);
  if(!wr) begin
   if(rsp_data!==expected_word(l,p,c,v) || rsp_hit!==expected_hit)
    $fatal(1,"KV_DATA_OR_TAG_MISMATCH");
   if(expected_hit && (spill_reads!==before_reads || waiting!==2))
    $fatal(1,"KV_HIT_LATENCY_OR_DDR_TURNAROUND latency=%0d",waiting);
   if(!expected_hit && spill_reads!==before_reads+1) $fatal(1,"KV_COLD_READ_MISSING");
   if(expected_hit) begin
    hot_reads=hot_reads+1;hot_cycles=hot_cycles+waiting;
    if(waiting<hot_min) hot_min=waiting;
    if(waiting>hot_max) hot_max=waiting;
   end else begin
    cold_reads=cold_reads+1;cold_cycles=cold_cycles+waiting;
    if(waiting<cold_min) cold_min=waiting;
    if(waiting>cold_max) cold_max=waiting;
   end
  end
  saved_data=rsp_data;saved_hit=rsp_hit;
  repeat(3) begin
   edge_tick();
   if(rsp_valid!==1 || rsp_data!==saved_data || rsp_hit!==saved_hit || rsp_error!==0)
    $fatal(1,"KV_STALLED_RESPONSE_CHANGED");
  end
  @(negedge clk);rsp_ready=1;
  edge_tick();
  @(negedge clk);rsp_ready=0;
  comparisons=comparisons+1;
 end
endtask
task reset_abort_read(input integer p,phase);
 integer waiting,reinitialize_edges,before_reads,before_writes;
 begin
  @(negedge clk);
  hold_spill_response=(phase==1);
  req_valid=1;req_write=0;req_layer=0;req_head=0;req_pos=p;req_dim=0;req_value=0;
  if(req_ready!==1) $fatal(1,"KV_RESET_REQUEST_NOT_READY");
  edge_tick();
  if(rsp_valid!==0) $fatal(1,"KV_RESET_REQUEST_PREMATURE_RESPONSE");
  @(negedge clk);req_valid=0;
  if(phase==1) begin
   waiting=0;
   while(!(pending && spill_rsp_ready===1) && waiting<10000) begin
    edge_tick();waiting=waiting+1;
   end
   if(!pending || pending_write || spill_rsp_ready!==1 || rsp_valid!==0)
    $fatal(1,"KV_RESET_OUTSTANDING_SPILL_NOT_OBSERVED");
  end else if(phase==2) begin
   waiting=0;
   while(rsp_valid!==1 && waiting<10000) begin edge_tick();waiting=waiting+1;end
   repeat(3) begin
    if({rsp_valid,rsp_error,rsp_hit,protocol_error}!==4'b1010 ||
       rsp_data!==expected_word(0,p,0,0) || rsp_ready!==0)
     $fatal(1,"KV_RESET_STALLED_RESPONSE_NOT_OBSERVED");
    edge_tick();
   end
  end else if({rsp_valid,spill_valid,protocol_error}!==3'b0)
   $fatal(1,"KV_RESET_LOOKUP_PRECONDITION");
  #1;rst_n=0;
  // Reset also quiesces the external spill responder.
  pending=0;held_spill=0;spill_rsp_valid=0;spill_ready=0;
  #0.001;check_reset();
  repeat(3) edge_tick();
  @(negedge clk);hold_spill_response=0;rst_n=1;
  await_initialization(reinitialize_edges);
  before_reads=spill_reads;before_writes=spill_writes;
  repeat(15) begin
   edge_tick();
   if({req_ready,rsp_valid,protocol_error,spill_valid}!==4'b1000 ||
      spill_reads!==before_reads || spill_writes!==before_writes)
    $fatal(1,"KV_RESET_GHOST_TRANSACTION phase=%0d",phase);
  end
  transaction(1,0,0,0,0,0);
  transaction(1,0,0,1,0,0);
  transaction(0,0,0,0,0,1);
  transaction(0,0,0,1,0,1);
  reset_aborts=reset_aborts+1;reset_recoveries=reset_recoveries+1;
 end
endtask
initial begin
 rst_n=0;`RESET_DELTA check_reset();
 for(i=0;i<LAYERS*2*SEQUENCE*WIDTH;i=i+1) begin present[i]=0;backing[i]=0;end
 repeat(3) edge_tick();
 @(negedge clk);rst_n=1;
 edge_tick();
 if(initialized!==0 || req_ready!==0) $fatal(1,"KV_STARTUP_EARLY_READY");
 @(negedge clk);rst_n=0;
 #0.001;check_reset();
 repeat(2) edge_tick();
 @(negedge clk);rst_n=1;
 await_initialization(startup_edges);
 for(position=0;position<WINDOW+2;position=position+1) begin
  for(layer=0;layer<LAYERS;layer=layer+1) begin
   for(value_bit=0;value_bit<2;value_bit=value_bit+1)
    for(column=0;column<WIDTH;column=column+1)
     transaction(1,layer,position,column,value_bit,0);
   for(value_bit=0;value_bit<2;value_bit=value_bit+1)
    for(column=0;column<WIDTH;column=column+1)
     transaction(0,layer,position,column,value_bit,1);
  end
  if(LAYERS>2 && position==0)
   for(layer=0;layer<LAYERS;layer=layer+1)
    for(value_bit=0;value_bit<2;value_bit=value_bit+1)
     for(column=0;column<WIDTH;column=column+1)
      transaction(0,layer,position,column,value_bit,1);
 end
 if(LAYERS>2)
  for(layer=0;layer<LAYERS;layer=layer+1)
   for(value_bit=0;value_bit<2;value_bit=value_bit+1)
    for(column=0;column<WIDTH;column=column+1)
     transaction(0,layer,WINDOW+1,column,value_bit,1);
 for(layer=0;layer<LAYERS;layer=layer+1)
  for(value_bit=0;value_bit<2;value_bit=value_bit+1)
   for(column=0;column<WIDTH;column=column+1)
    transaction(0,layer,0,column,value_bit,0);
 if(spill_writes!==4*LAYERS*WIDTH || hot_reads==0 || cold_reads!==2*LAYERS*WIDTH)
  $fatal(1,"KV_MISSING_COVERAGE spills=%0d hot=%0d cold=%0d",spill_writes,hot_reads,cold_reads);
 $display("MEASURED_KV hot_reads=%0d hot_cycles=%0d hot_min=%0d hot_max=%0d cold_reads=%0d cold_cycles=%0d cold_min=%0d cold_max=%0d spill_reads=%0d spill_writes=%0d",
          hot_reads,hot_cycles,hot_min,hot_max,cold_reads,cold_cycles,cold_min,cold_max,
          spill_reads,spill_writes);
 reset_abort_read(0,1);
 reset_abort_read(0,0);
 reset_abort_read(0,2);
 if(reset_aborts!==3 || reset_recoveries!==3)
  $fatal(1,"KV_RESET_ABORT_COVERAGE_MISSING");
 @(negedge clk);new_sequence=1;
 edge_tick();
 if(initialized!==0) $fatal(1,"KV_NEW_SEQUENCE_NOT_INVALIDATED");
 @(negedge clk);new_sequence=0;
 await_initialization(sequence_edges);
 transaction(1,0,0,0,0,0);
 transaction(0,0,0,0,0,1);
 // Column one was valid in the preceding sequence but has not been rewritten.
 @(negedge clk);
 req_valid=1;req_write=0;req_layer=0;req_head=0;req_pos=0;req_dim=1;req_value=0;
 if(req_ready!==1) $fatal(1,"KV_STALE_TEST_NOT_READY");
 edge_tick();
 @(negedge clk);req_valid=0;
 repeat(2) edge_tick();
 if({rsp_valid,rsp_error,protocol_error,rsp_hit}!==4'b1110 || rsp_data!==0)
  $fatal(1,"KV_NEW_SEQUENCE_STALE_WORD_VISIBLE");
 stale_rejections=stale_rejections+1;
 if(reset_compares==0 || stale_rejections!==1 || startup_edges==0 || sequence_edges==0)
  $fatal(1,"KV_STARTUP_COVERAGE_MISSING");
 $display("CHECKS_PASSED kv window=%0d max_sequence=%0d compares=%0d hot=%0d cold=%0d spill_writes=%0d startup_edges=%0d sequence_edges=%0d reset_compares=%0d stale_rejections=%0d",
           WINDOW,MAXIMUM_SEQUENCE,comparisons,hot_reads,cold_reads,spill_writes,
           startup_edges,sequence_edges,reset_compares,stale_rejections);
 $display("CHECKS_PASSED kv_reset window=%0d max_sequence=%0d reset_aborts=%0d reset_recoveries=%0d",
          WINDOW,MAXIMUM_SEQUENCE,reset_aborts,reset_recoveries);
 $finish;
end
endmodule
"""
    name = f"kv-{depth}" + (f"-sequence-{max_sequence}" if max_sequence != depth + 2 else "")
    if (layers, head_dim) != (2, 8):
        name += f"-layers-{layers}-head-{head_dim}"
    transcript = evidence.simulate(name, bench.replace("DEPTH_VALUE", str(depth))
                                  .replace("SEQUENCE_VALUE", str(max_sequence))
                                  .replace("LAYERS_VALUE", str(layers))
                                  .replace("HEAD_DIM_VALUE", str(head_dim)),
                                  ["anvil_q1_ht_kv_window.sv"],
                                  simulator=("verilator" if head_dim >= 64 or layers > 2
                                             else getattr(evidence, "default_simulator", "iverilog")))
    measured = measurement_records(transcript, "MEASURED_KV")
    if len(measured) != 1:
        raise AssertionError("KV benchmark lacks a unique measured record")
    counters = measured[0]
    reset_records = measurement_records(transcript, "CHECKS_PASSED kv_reset")
    if (len(reset_records) != 1 or reset_records[0]["reset_aborts"] != 3 or
            reset_records[0]["reset_recoveries"] != 3):
        raise AssertionError("KV reset-abort/recovery coverage missing")
    evidence.record.setdefault("kv_reset_checks", []).append({
        "window": depth, "max_sequence": max_sequence,
        "observed": reset_records[0],
        "phases": ["accepted cold spill awaiting response", "accepted hit lookup",
                   "stalled hit response"],
        "reset_source_policy": "quiesce external spill source and cancel its outstanding response",
        "recovery": "no ghost transaction, then independently compare two fresh hit words",
    })
    expected_hot = (depth + 2 + 2 * int(layers > 2)) * layers * 2 * kv_width
    if (counters["hot_reads"] != expected_hot or counters["cold_reads"] != layers * 2 * kv_width or
            counters["spill_writes"] != 4 * layers * kv_width or
            counters["spill_reads"] != counters["cold_reads"] or
            counters["hot_cycles"] != 2 * counters["hot_reads"] or
            counters["hot_min"] != 2 or counters["hot_max"] != 2):
        raise AssertionError("KV benchmark lacks exact hot/cold comparison coverage")
    evidence.record.setdefault("kv_benchmarks", []).append({
        "scope": "D3_KV_primitive_not_complete_attention_or_physical_DDR",
        "window": depth, "max_sequence": max_sequence,
        "layers": layers, "kv_heads": 2, "head_dim": head_dim,
        "cross_layer_reread_sweeps": 2 if layers > 2 else 0,
        "cross_layer_reread_words": 4 * layers * kv_width if layers > 2 else 0,
        "compute_period_ns": 10,
        "measurement": "accepted public request edge to post-edge rsp_valid; "
                       "excludes three deliberate response-hold cycles, request retirement "
                       "and subsequent reset-abort/recovery trials",
        "service": "spill_ready when cycle modulo 7 exceeds 2 and no response outstanding; "
                   "spill response on cycle modulo 5 equal to zero; "
                   "clock counter includes startup and all transactions",
        "observed": counters,
        "hot_logical_spill_reads": 0,
        "hot_mean_latency_cycles": counters["hot_cycles"] / counters["hot_reads"],
        "cold_mean_latency_cycles": counters["cold_cycles"] / counters["cold_reads"],
        "limitations": ["cold backing store is a public logical spill-port model, not an EMIF",
                        "MAX_SEQ_LEN elaboration does not exercise every context position",
                        "no attention-kernel throughput or full-context benchmark claim"],
    })
    evidence.flush()


def measurement_records(transcript, prefix):
    records = []
    for line in transcript.splitlines():
        if line.startswith(prefix + " "):
            records.append({key: int(value) for key, value in
                            (field.split("=", 1) for field in line[len(prefix):].split())})
    return records


def dma_probe(evidence, depth, seed=17, *, ddr_period_ns=3.75, ddr_phase_ns=0,
              upload_validation=False):
    """Keep nominal D1 measurements separate from phase/rate CDC stress runs."""
    if ddr_period_ns <= 0 or not 0 <= ddr_phase_ns < ddr_period_ns:
        raise ValueError("DMA test clocks require a positive period and an in-period phase")
    bench = CLOCK + r"""
reg ddr_clk=0;
always #1.875 ddr_clk=!ddr_clk;
reg request_valid=0,completion_ready=0;
reg [32:0] request_address=0;
reg [31:0] request_bytes=0;
wire request_ready,completion_valid,completion_error;
wire [26:0] completion_tiles;
wire fill_valid,fill_ready,fill_bank,fill_data_valid,fill_data_ready,fill_last,fill_abort,fill_error;
wire [8:0] fill_beats,tile_beats;
wire [63:0] fill_tail,tile_tail;
wire [511:0] fill_data;
reg tile_ready=0,release_valid=0,read_valid=0,read_rsp_ready=0;
reg [7:0] read_address=0;
wire tile_valid,tile_bank,release_ready,read_ready,read_rsp_valid,compute_error;
wire [511:0] read_data;
wire [63:0] read_mask;
wire [32:0] avm_address;
wire [7:0] avm_burstcount;
wire avm_read,avm_write;
wire [511:0] avm_writedata;
wire [63:0] avm_byteenable;
wire [63:0] accepted_read_beats;
wire protocol_error;
integer ddr_cycles=0,response_remaining=0;
reg [32:0] service_address=0;
integer reads=0,bursts=0,overlap=0,comparisons=0,swaps=0,stall_remaining=0;
integer burst1=0,burst2=0,burst15=0,burst16=0;
integer core_cycles=0,first_issue=-1,last_response=-1,compared_last=-1;
integer stalled_edges=0,max_stall=0,current_stall=0,immediate_beats=0,gap_edges=0;
integer reset_compares=0,transfer_index=0,reset_wait=0,reset_fill=0,reset_stall=0,epoch=0;
integer invalid_rejections=0;
realtime previous_core_edge=-1,previous_ddr_edge=-1;
integer observed_core_edges=0,observed_ddr_edges=0;
always @(posedge clk) begin
 if(previous_core_edge>=0 && $realtime-previous_core_edge!=10.0)
  $fatal(1,"DMA_CORE_CLOCK_PERIOD");
 previous_core_edge=$realtime;observed_core_edges=observed_core_edges+1;
end
always @(posedge ddr_clk) begin
 if(previous_ddr_edge<0) begin
  if($realtime!=DDR_FIRST_EDGE_VALUE) $fatal(1,"DMA_DDR_CLOCK_PHASE");
 end else if($realtime-previous_ddr_edge!=DDR_PERIOD_VALUE)
  $fatal(1,"DMA_DDR_CLOCK_PERIOD");
 previous_ddr_edge=$realtime;observed_ddr_edges=observed_ddr_edges+1;
end
reg immediate=0,gapped=0,held=0;
reg randomized=0;
reg [31:0] random_state=SEED_VALUE;
reg [42:0] held_command;
reg [4:0] issue_stall=0;
wire avm_waitrequest=stall_remaining>0;
wire avm_readdatavalid=rst_n &&
 (response_remaining>0 ? (!gapped || (randomized ? random_state[2:0]!=0 : ddr_cycles%5!=0)) :
  (immediate && avm_read && !avm_waitrequest));
function automatic [511:0] pattern(input [32:0] address);
 integer w;
 begin
  for(w=0;w<16;w=w+1)
   pattern[32*w+:32]=32'(address) ^ (address[32] ? 32'ha5c3f197 : 0) ^
                       (32'h13579bdf*(w+1));
 end
endfunction
wire [511:0] avm_readdata=pattern(response_remaining>0 ? service_address : avm_address);
anvil_q1_ht_weight_dma #(.TILE_BEATS(DEPTH_VALUE)) dma(
 .clk(clk),.ddr_clk(ddr_clk),.rst_n(rst_n),
 .request_valid(request_valid),.request_ready(request_ready),.request_address(request_address),
 .request_bytes(request_bytes),.request_abort(1'b0),
 .completion_valid(completion_valid),.completion_ready(completion_ready),
 .completion_error(completion_error),.completion_tiles(completion_tiles),
 .load_enable(1'b0),.load_clear(1'b0),.load_valid(1'b0),.load_ready(),
 .load_address(33'b0),.load_data(512'b0),.load_byteenable(64'b0),.load_last(1'b0),
 .load_done(),.load_error(),.load_idle(),
 .fill_valid(fill_valid),.fill_ready(fill_ready),.fill_beats(fill_beats),.fill_tail(fill_tail),
 .fill_data_valid(fill_data_valid),.fill_data_ready(fill_data_ready),.fill_data(fill_data),
 .fill_last(fill_last),.fill_abort(fill_abort),.fill_error(fill_error),
 .avm_address(avm_address),.avm_burstcount(avm_burstcount),.avm_read(avm_read),
 .avm_write(avm_write),.avm_writedata(avm_writedata),.avm_byteenable(avm_byteenable),
 .avm_waitrequest(avm_waitrequest),.avm_readdata(avm_readdata),
 .avm_readdatavalid(avm_readdatavalid),.avm_response(2'b00),.avm_writeresponsevalid(1'b0),
 .accepted_read_beats(accepted_read_beats),.protocol_error(protocol_error));
anvil_q1_ht_weight_tiles #(.TILE_BEATS(DEPTH_VALUE)) tiles(
 .clk(clk),.ddr_clk(ddr_clk),.rst_n(rst_n),
 .fill_valid(fill_valid),.fill_ready(fill_ready),.fill_bank(fill_bank),
 .fill_beats(fill_beats),.fill_tail(fill_tail),.fill_data_valid(fill_data_valid),
 .fill_data_ready(fill_data_ready),.fill_data(fill_data),.fill_last(fill_last),
 .fill_abort(fill_abort),.fill_error(fill_error),
 .tile_valid(tile_valid),.tile_ready(tile_ready),.tile_bank(tile_bank),.tile_beats(tile_beats),
 .tile_tail(tile_tail),.release_valid(release_valid),.release_ready(release_ready),
 .read_valid(read_valid),.read_ready(read_ready),.read_address(read_address),
 .read_rsp_valid(read_rsp_valid),.read_rsp_ready(read_rsp_ready),
 .read_data(read_data),.read_mask(read_mask),.compute_error(compute_error));
task check_reset;
 begin
  if({request_ready,completion_valid,completion_error,completion_tiles,
      fill_valid,fill_ready,fill_bank,fill_beats,fill_tail,fill_data_valid,
      fill_data_ready,fill_data,fill_last,fill_abort,fill_error,
      tile_valid,tile_bank,tile_beats,tile_tail,release_ready,
      read_ready,read_rsp_valid,read_data,read_mask,compute_error,
      avm_address,avm_burstcount,avm_read,avm_write,avm_writedata,avm_byteenable,
      accepted_read_beats,protocol_error} !== '0)
   $fatal(1,"DMA_RESET_XZ_OR_NONZERO time=%0t",$time);
  reset_compares=reset_compares+1;
 end
endtask
always @(posedge clk or negedge clk or posedge ddr_clk or negedge ddr_clk)
 if(!rst_n) check_reset();
always @(posedge clk) if(rst_n) core_cycles<=core_cycles+1;
always @(posedge ddr_clk) begin
 if(!rst_n) begin
  response_remaining<=0;service_address<=0;ddr_cycles<=0;last_response<=-1;
 end else begin
  ddr_cycles<=ddr_cycles+1;
  if(first_issue<0 && avm_read) first_issue=ddr_cycles;
  if(avm_read && avm_waitrequest) begin
   stalled_edges=stalled_edges+1;current_stall=current_stall+1;
   if(current_stall>max_stall) max_stall=current_stall;
  end else current_stall=0;
  if(response_remaining>0 && !avm_readdatavalid) gap_edges=gap_edges+1;
  if(((fill_valid && fill_ready) || (fill_data_valid && fill_data_ready)) &&
     (read_ready || read_rsp_valid || release_ready)) overlap=overlap+1;
  if(held && {avm_address,avm_burstcount,avm_read,avm_write}!==held_command)
   $fatal(1,"DMA_COMMAND_CHANGED_WHILE_WAITREQUEST");
  held=(avm_read || avm_write) && avm_waitrequest;
  if(held) held_command={avm_address,avm_burstcount,avm_read,avm_write};
  if(avm_read && !avm_waitrequest) begin
   if(response_remaining!=0 || avm_burstcount<1 || avm_burstcount>16 ||
      avm_address[5:0]!==0 || avm_write!==0 || avm_byteenable!==64'hffffffffffffffff ||
      {1'b0,avm_address[11:0]}+avm_burstcount*64>4096 ||
      {1'b0,avm_address}+avm_burstcount*64>34'h200000000)
    $fatal(1,"DMA_AVALON_BOUNDS_OR_OUTSTANDING");
   response_remaining<=avm_burstcount-(avm_readdatavalid ? 1 : 0);
   service_address<=avm_address+(avm_readdatavalid ? 64 : 0);
   bursts=bursts+1;
   case(avm_burstcount)
    1:burst1=burst1+1;2:burst2=burst2+1;15:burst15=burst15+1;16:burst16=burst16+1;
   endcase
  end else if(avm_readdatavalid) begin
   response_remaining<=response_remaining-1;service_address<=service_address+64;
  end
  if(avm_readdatavalid) begin
   reads=reads+1;last_response<=ddr_cycles;
   if(avm_read && !avm_waitrequest && response_remaining==0)
    immediate_beats=immediate_beats+1;
  end
  if(protocol_error!==0 || fill_error!==0) $fatal(1,"DMA_OR_TILE_PROTOCOL_ERROR");
 end
end
reg stalling_this_command=0;
always @(negedge ddr_clk) begin
 if(!rst_n) begin stall_remaining=0;stalling_this_command=0;end
 else begin
  random_state={random_state[30:0],
                random_state[31]^random_state[21]^random_state[1]^random_state[0]};
  if(!avm_read) stalling_this_command=0;
  else if(!stalling_this_command) begin
   stalling_this_command=1;
   stall_remaining=randomized ? random_state[4:0] : issue_stall;
  end else if(stall_remaining>0) stall_remaining=stall_remaining-1;
 end
end
task run_transfer(input [32:0] base,input integer count,input integer tail,
                  input same_edge,gaps,input [4:0] stalls);
 integer waiting,tile_index,offset,n,total_tiles,beats,before_reads;
 integer started_core,before_compares,before_bursts,before_overlap,request_ddr;
 reg [63:0] expected_tail,mask;
 reg [511:0] expected;
 begin
  immediate=same_edge;gapped=gaps;issue_stall=stalls;
  first_issue=-1;compared_last=-1;
  stalled_edges=0;max_stall=0;current_stall=0;immediate_beats=0;gap_edges=0;
  before_reads=reads;total_tiles=(count+DEPTH_VALUE-1)/DEPTH_VALUE;
  before_compares=comparisons;before_bursts=bursts;before_overlap=overlap;
  expected_tail=tail==64 ? 64'hffffffffffffffff : (64'd1<<tail)-1;
  @(negedge clk);request_address=base;request_bytes=(count-1)*64+tail;request_valid=1;
  waiting=0;
  while(request_ready!==1 && waiting<10000) begin edge_tick();@(negedge clk);waiting=waiting+1;end
  if(request_ready!==1) $fatal(1,"DMA_REQUEST_NOT_READY");
  started_core=core_cycles;request_ddr=ddr_cycles;
  edge_tick();
  @(negedge clk);request_valid=0;
  offset=0;
  for(tile_index=0;tile_index<total_tiles;tile_index=tile_index+1) begin
   waiting=0;
   while(tile_valid!==1 && waiting<100000) begin edge_tick();waiting=waiting+1;end
   beats=count-offset>DEPTH_VALUE ? DEPTH_VALUE : count-offset;
   if(tile_valid!==1 || tile_beats!==beats || tile_bank!==(swaps%2) ||
      tile_tail!==(tile_index==total_tiles-1 ? expected_tail : 64'hffffffffffffffff))
    $fatal(1,"DMA_TILE_METADATA_OR_MISSING tile=%0d valid=%b beats=%0d expected=%0d",
            tile_index,tile_valid,tile_beats,beats);
   @(negedge clk);tile_ready=1;
   edge_tick();
   @(negedge clk);tile_ready=0;
   for(n=0;n<beats;n=n+1) begin
    read_valid=1;read_address=n;#0.001;
    if(read_ready!==1) $fatal(1,"DMA_TILE_READ_NOT_READY");
    edge_tick();
    if(read_rsp_valid!==0) $fatal(1,"DMA_TILE_READ_EARLY");
    @(negedge clk);read_valid=0;
    edge_tick();
    expected=pattern(base+offset*64+n*64);
    mask=(offset+n==count-1) ? expected_tail : 64'hffffffffffffffff;
    if(read_rsp_valid!==1 || read_data!==expected || read_mask!==mask || compute_error!==0)
     $fatal(1,"DMA_DATA_MISMATCH tile=%0d beat=%0d actual=%h expected=%h mask=%h expectedmask=%h",
             tile_index,n,read_data,expected,read_mask,mask);
    repeat(3) begin
     edge_tick();
     if(read_rsp_valid!==1 || read_data!==expected || read_mask!==mask)
      $fatal(1,"DMA_TILE_STALL_CHANGED");
    end
    @(negedge clk);read_rsp_ready=1;
    edge_tick();
    @(negedge clk);read_rsp_ready=0;
    comparisons=comparisons+1;
    compared_last=core_cycles;
   end
   if(release_ready!==1) $fatal(1,"DMA_TILE_NOT_RELEASABLE");
   release_valid=1;
   edge_tick();
   @(negedge clk);release_valid=0;
   offset=offset+beats;swaps=swaps+1;
  end
  waiting=0;
  while(completion_valid!==1 && waiting<10000) begin edge_tick();waiting=waiting+1;end
  if(completion_valid!==1 || completion_error!==0 || completion_tiles!==total_tiles ||
     reads-before_reads!==count || accepted_read_beats!==reads)
   $fatal(1,"DMA_COMPLETION_OR_CONSERVATION tiles=%0d expected=%0d reads=%0d expected=%0d",
           completion_tiles,total_tiles,reads-before_reads,count);
  if(comparisons-before_compares!==count || first_issue<request_ddr ||
     last_response<first_issue || compared_last<=started_core ||
     (!randomized && max_stall!=stalls) ||
     (same_edge && immediate_beats!=bursts-before_bursts) ||
     (!same_edge && immediate_beats!=0) || (gaps && count>16 && gap_edges==0))
   $fatal(1,"DMA_MISSING_MEASUREMENT_OR_STALL_COVERAGE comparisons=%0d expected=%0d first_issue=%0d request_ddr=%0d last_response=%0d compared_last=%0d started_core=%0d max_stall=%0d expected_stall=%0d immediate_beats=%0d bursts=%0d gaps=%0d same_edge=%0d gapped=%0d",
           comparisons-before_compares,count,first_issue,request_ddr,last_response,
           compared_last,started_core,max_stall,stalls,immediate_beats,
           bursts-before_bursts,gap_edges,same_edge,gaps);
  $display("MEASURED_DMA transfer=%0d epoch=%0d depth=DEPTH_VALUE base=%0d beats=%0d useful_bytes=%0d tiles=%0d bursts=%0d overlap=%0d same_edge=%0d gapped=%0d randomized=%0d requested_stall=%0d stalled_edges=%0d max_stall=%0d immediate_beats=%0d gap_edges=%0d ddr_request_cycles=%0d ddr_service_cycles=%0d core_consumption_cycles=%0d core_completion_cycles=%0d",
           transfer_index,epoch,base,count,(count-1)*64+tail,total_tiles,bursts-before_bursts,
           overlap-before_overlap,same_edge,gaps,randomized,stalls,stalled_edges,max_stall,
           immediate_beats,gap_edges,last_response-request_ddr+1,
           last_response-first_issue+1,compared_last-started_core,
           core_cycles-started_core);
  transfer_index=transfer_index+1;
  repeat(3) begin
   edge_tick();
   if(completion_valid!==1 || completion_error!==0 || completion_tiles!==total_tiles)
    $fatal(1,"DMA_COMPLETION_STALL_CHANGED");
  end
  @(negedge clk);completion_ready=1;
  edge_tick();
  @(negedge clk);completion_ready=0;
 end
endtask
task reset_traffic(input integer phase);
 integer waiting;
 begin
  immediate=0;gapped=1;issue_stall=phase==0 ? 31 : 0;
  @(negedge clk);
  request_address=33'd16384;request_bytes=DEPTH_VALUE*128;request_valid=1;
  if(request_ready!==1) $fatal(1,"DMA_RESET_REQUEST_NOT_READY");
  edge_tick();
  @(negedge clk);request_valid=0;
  waiting=0;
  if(phase==0) begin
   while(!(avm_read && avm_waitrequest) && waiting<100000) begin
    @(negedge ddr_clk);#0.001;waiting=waiting+1;
   end
   if(!(avm_read && avm_waitrequest)) $fatal(1,"DMA_RESET_NO_WAITREQUEST");
   reset_wait=reset_wait+1;
  end else if(phase==1) begin
   while(response_remaining==0 && waiting<100000) begin
    @(negedge ddr_clk);#0.001;waiting=waiting+1;
   end
   if(response_remaining==0) $fatal(1,"DMA_RESET_NO_OUTSTANDING_RESPONSE");
   reset_fill=reset_fill+1;
  end else begin
   while(tile_valid!==1 && waiting<100000) begin edge_tick();waiting=waiting+1;end
   if(tile_valid!==1) $fatal(1,"DMA_RESET_NO_COMPUTE_TILE");
   @(negedge clk);tile_ready=1;
   edge_tick();
   @(negedge clk);tile_ready=0;read_valid=1;read_address=0;
   if(read_ready!==1) $fatal(1,"DMA_RESET_READ_NOT_READY");
   edge_tick();
   @(negedge clk);read_valid=0;
   edge_tick();
   if(read_rsp_valid!==1 || read_rsp_ready!==0 ||
      read_data!==pattern(33'd16384) || read_mask!==64'hffffffffffffffff)
    $fatal(1,"DMA_RESET_NO_COMPARED_STALLED_RESPONSE");
   reset_stall=reset_stall+1;
  end
  // Reset quiesces the external responder and starts a fresh scoreboard epoch.
  rst_n=0;request_valid=0;tile_ready=0;read_valid=0;read_rsp_ready=0;
  release_valid=0;completion_ready=0;held=0;swaps=0;reads=0;epoch=epoch+1;
  #0.001;check_reset();
  repeat(6) edge_tick();
  @(negedge clk);rst_n=1;
  repeat(6) begin
   edge_tick();
   if(completion_valid!==0 || tile_valid!==0 || read_rsp_valid!==0 ||
      accepted_read_beats!==0 || protocol_error!==0 || compute_error!==0)
    $fatal(1,"DMA_RESET_OLD_EPOCH_LEAK");
  end
  if(request_ready!==1) $fatal(1,"DMA_RESET_RECOVERY_NOT_READY");
  run_transfer(33'd20480,DEPTH_VALUE+1,19,0,0,0);
 end
endtask
task invalid_transfer(input [32:0] base,input [31:0] length);
 integer waiting,before_reads,before_bursts;
 begin
  @(negedge clk);request_address=base;request_bytes=length;request_valid=1;
  if(request_ready!==1) $fatal(1,"DMA_INVALID_REQUEST_NOT_ACCEPTED");
  before_reads=reads;before_bursts=bursts;
  edge_tick();
  @(negedge clk);request_valid=0;
  waiting=0;
  while(completion_valid!==1 && waiting<10000) begin
   edge_tick();waiting=waiting+1;
  end
  if({completion_valid,completion_error}!==2'b11 || completion_tiles!==0 ||
     reads!==before_reads || bursts!==before_bursts || tile_valid!==0 ||
     protocol_error!==0 || compute_error!==0)
   $fatal(1,"DMA_INVALID_RANGE_NOT_REJECTED_WITHOUT_TRAFFIC");
  repeat(3) begin
   edge_tick();
   if({completion_valid,completion_error}!==2'b11 || completion_tiles!==0 ||
      reads!==before_reads || bursts!==before_bursts || tile_valid!==0)
    $fatal(1,"DMA_INVALID_COMPLETION_NOT_HELD");
  end
  @(negedge clk);completion_ready=1;
  edge_tick();
  @(negedge clk);completion_ready=0;
  invalid_rejections=invalid_rejections+1;
 end
endtask
task pipelined_transfer(input [32:0] base,input integer count,input integer tail);
 integer waiting,tile_index,offset,beats,n,sent,received,total_tiles,before_reads;
 integer simultaneous,consecutive,longest_run,request_run,queued,stall_edges,stall_run;
 integer stalls1,stalls7,stalls31,compared_stalls,stall_slot,phase;
 reg take_request,take_response,was_stalled;
 reg [511:0] expected,saved_data;
 reg [63:0] expected_mask,saved_mask,expected_tail;
 begin
  immediate=1;gapped=0;issue_stall=0;
  before_reads=reads;total_tiles=(count+DEPTH_VALUE-1)/DEPTH_VALUE;
  simultaneous=0;consecutive=0;longest_run=0;queued=0;stall_edges=0;
  stalls1=0;stalls7=0;stalls31=0;compared_stalls=0;
  expected_tail=(64'd1<<tail)-1;
  @(negedge clk);request_address=base;request_bytes=(count-1)*64+tail;request_valid=1;
  if(request_ready!==1) $fatal(1,"PIPELINED_DMA_REQUEST_NOT_READY");
  edge_tick();
  @(negedge clk);request_valid=0;
  offset=0;
  for(tile_index=0;tile_index<total_tiles;tile_index=tile_index+1) begin
   waiting=0;
   while(tile_valid!==1 && waiting<100000) begin edge_tick();waiting=waiting+1;end
   beats=count-offset>DEPTH_VALUE ? DEPTH_VALUE : count-offset;
   if(tile_valid!==1 || tile_beats!==beats || tile_bank!==(swaps%2) ||
      tile_tail!==(tile_index==total_tiles-1 ? expected_tail : 64'hffffffffffffffff))
    $fatal(1,"PIPELINED_DMA_TILE_METADATA");
   @(negedge clk);tile_ready=1;
   edge_tick();
   @(negedge clk);tile_ready=0;
   sent=0;received=0;n=0;request_run=0;stall_run=0;was_stalled=0;
   // Each of the first three tiles holds its first response for a distinct duration.
   stall_slot=tile_index<3 ? (tile_index==0 ? 1 : tile_index==1 ? 7 : 31) : 0;
   phase=0;
   while(received<beats && n<100000) begin
    read_valid=sent<beats;read_address=sent;
    if(stall_slot>0 && received==0) read_rsp_ready=0;
    else read_rsp_ready=(tile_index<3 || n<8 || n%11>3);
    #0.001;
    @(posedge clk);
    take_request=read_valid && read_ready;
    take_response=read_rsp_valid && read_rsp_ready;
    if((^{read_ready,read_rsp_valid,compute_error})===1'bx || compute_error!==0)
     $fatal(1,"PIPELINED_DMA_ACTIVE_XZ_OR_ERROR");
    if(was_stalled && (read_rsp_valid!==1 || read_data!==saved_data || read_mask!==saved_mask))
     $fatal(1,"PIPELINED_DMA_STALLED_PAYLOAD_CHANGED");
    if(read_rsp_valid===1) begin
     if(received>=sent) $fatal(1,"PIPELINED_DMA_UNREQUESTED_RESPONSE");
     expected=pattern(base+(offset+received)*64);
     expected_mask=offset+received==count-1 ? expected_tail : 64'hffffffffffffffff;
     if(read_data!==expected || read_mask!==expected_mask)
      $fatal(1,"PIPELINED_DMA_ORDER_DATA_MASK tile=%0d response=%0d",tile_index,received);
     if(!read_rsp_ready) begin
      stall_edges=stall_edges+1;stall_run=stall_run+1;compared_stalls=compared_stalls+1;
      if(stall_slot>0 && stall_run==stall_slot) begin
       case(stall_slot)
        1:stalls1=stalls1+1;7:stalls7=stalls7+1;31:stalls31=stalls31+1;
       endcase
       phase=1;
      end
     end
    end
    was_stalled=read_rsp_valid && !read_rsp_ready;
    if(was_stalled) begin saved_data=read_data;saved_mask=read_mask;end
    if(take_request && take_response) simultaneous=simultaneous+1;
    if(take_request) begin
     sent=sent+1;request_run=request_run+1;
     if(request_run>longest_run) longest_run=request_run;
     if(request_run>=3) consecutive=consecutive+1;
    end else request_run=0;
    if(take_response) begin received=received+1;comparisons=comparisons+1;end
    if(sent-received>1) queued=queued+1;
    #0.001;
    if(was_stalled && (read_rsp_valid!==1 || read_data!==saved_data || read_mask!==saved_mask))
     $fatal(1,"PIPELINED_DMA_POSTEDGE_STALLED_PAYLOAD_CHANGED");
    if(phase==1) begin stall_slot=0;phase=2;end
    @(negedge clk);n=n+1;
   end
   read_valid=0;read_rsp_ready=0;
   if(received!==beats || sent!==beats || read_rsp_valid!==0 || release_ready!==1)
    $fatal(1,"PIPELINED_DMA_CONSERVATION_OR_TIMEOUT");
   release_valid=1;
   edge_tick();
   @(negedge clk);release_valid=0;
   offset=offset+beats;swaps=swaps+1;
  end
  waiting=0;
  while(completion_valid!==1 && waiting<10000) begin edge_tick();waiting=waiting+1;end
  if(completion_valid!==1 || completion_error!==0 || completion_tiles!==total_tiles ||
     reads-before_reads!==count || accepted_read_beats!==reads ||
     stalls1!==1 || stalls7!==1 || stalls31!==1 || compared_stalls<39 ||
     (DEPTH_VALUE>=3 && (simultaneous==0 || queued==0 || consecutive==0)))
   $fatal(1,"PIPELINED_DMA_MISSING_COVERAGE_OR_COMPLETION");
  @(negedge clk);completion_ready=1;
  edge_tick();
  @(negedge clk);completion_ready=0;
  $display("CHECKS_PASSED pipelined_dma depth=DEPTH_VALUE beats=%0d tiles=%0d simultaneous=%0d queued=%0d consecutive=%0d longest_request_run=%0d stalled_edges=%0d compared_stalls=%0d stall1=%0d stall7=%0d stall31=%0d",
           count,total_tiles,simultaneous,queued,consecutive,longest_run,stall_edges,
           compared_stalls,stalls1,stalls7,stalls31);
 end
endtask
initial begin
 rst_n=0;`RESET_DELTA check_reset();
 repeat(6) edge_tick();
 @(negedge clk);rst_n=1;
 repeat(6) edge_tick();
 run_transfer(33'd4032,DEPTH_VALUE*5,51,1,0,1);
 run_transfer(33'd8128,DEPTH_VALUE*5,64,0,1,7);
 run_transfer(33'h100000fc0,DEPTH_VALUE*5,23,0,1,7);
 run_transfer(33'h1ffffffc0,1,64,1,0,31);
 if(DEPTH_VALUE==256) begin
  run_transfer(33'd0,2,64,0,0,0);
  run_transfer(33'd0,15,64,1,0,0);
  run_transfer(33'd0,16,64,0,0,0);
  if(burst1==0 || burst2==0 || burst15==0 || burst16==0) $fatal(1,"DMA_MISSING_BURST_BINS");
 end
 randomized=1;
 run_transfer(33'd12224,DEPTH_VALUE*5,37,0,1,0);
 randomized=0;
 if(overlap==0 || swaps<4 || comparisons==0) $fatal(1,"DMA_NO_FILL_COMPUTE_OVERLAP");
 reset_traffic(0);
 reset_traffic(1);
 reset_traffic(2);
 invalid_transfer(33'd1,32'd64);
 invalid_transfer(33'd0,32'd0);
 invalid_transfer(33'h1ffffffc0,32'd65);
 pipelined_transfer(33'd28672,DEPTH_VALUE*5,19);
 if(reset_wait!==1 || reset_fill!==1 || reset_stall!==1 || reset_compares==0)
  $fatal(1,"DMA_MISSING_RESET_COVERAGE");
 if(invalid_rejections!==3) $fatal(1,"DMA_MISSING_INVALID_RANGE_COVERAGE");
 $display("CHECKS_PASSED dma_reset depth=DEPTH_VALUE waitrequest=%0d filling=%0d stalled_read=%0d reset_samples=%0d recovery_epochs=%0d",
          reset_wait,reset_fill,reset_stall,reset_compares,epoch);
 $display("CHECKS_PASSED dma_invalid depth=DEPTH_VALUE unaligned=1 zero_length=1 bank_overflow=1 rejected=%0d",
          invalid_rejections);
 $display("CHECKS_PASSED dma depth=DEPTH_VALUE beats=%0d tiles=%0d overlap=%0d bursts=%0d burst1=%0d burst2=%0d burst15=%0d burst16=%0d",
          comparisons,swaps,overlap,bursts,burst1,burst2,burst15,burst16);
 if(observed_core_edges<2 || observed_ddr_edges<2)
  $fatal(1,"DMA_MISSING_CLOCK_OBSERVATIONS");
 $display("CHECKS_PASSED dma_clocks core_edges=%0d ddr_edges=%0d",
          observed_core_edges,observed_ddr_edges);
 $finish;
end
endmodule
"""
    if upload_validation:
        from dma_upload import instrument_upload
        bench = instrument_upload(bench, seed)
    clock_case = ("" if (ddr_period_ns, ddr_phase_ns) == (3.75, 0) else
                  f"-ddr-{ddr_period_ns:g}-phase-{ddr_phase_ns:g}")
    bench = bench.replace(
        "always #1.875 ddr_clk=!ddr_clk;",
        f"initial begin #{ddr_phase_ns:g}; "
        f"forever #{ddr_period_ns / 2:g} ddr_clk=!ddr_clk; end"
        if ddr_phase_ns else
        f"always #{ddr_period_ns / 2:g} ddr_clk=!ddr_clk;")
    simulation_name = f"dma-{depth}{clock_case}"
    if upload_validation:
        simulation_name += f"-upload-{getattr(evidence, 'default_simulator', 'iverilog')}"
    transcript = evidence.simulate(
        simulation_name,
        bench.replace("DEPTH_VALUE", str(depth))
        .replace("SEED_VALUE", str(seed or 1))
        .replace("DDR_PERIOD_VALUE", f"{ddr_period_ns:g}")
        .replace("DDR_FIRST_EDGE_VALUE", f"{ddr_phase_ns + ddr_period_ns / 2:g}"),
        ["anvil_q1_ht_reset_sync.sv", "anvil_q1_ht_cdc_mailbox.sv",
         "anvil_q1_ht_tile_bank.sv", "anvil_q1_ht_weight_tiles.sv",
         "anvil_q1_ht_weight_dma.sv"])
    if upload_validation:
        from dma_upload import validate_upload
        validate_upload(evidence, transcript, seed)
        return measurement_records(transcript, "CHECKS_PASSED dma_upload")
    measured = measurement_records(transcript, "MEASURED_DMA")
    pipeline = measurement_records(transcript, "CHECKS_PASSED pipelined_dma")
    clocks = measurement_records(transcript, "CHECKS_PASSED dma_clocks")
    if len(clocks) != 1 or any(clocks[0][name] < 2 for name in ("core_edges", "ddr_edges")):
        raise AssertionError("DMA clock period/phase comparisons are missing")
    if (len(pipeline) != 1 or pipeline[0]["beats"] != depth * 5 or
            pipeline[0]["tiles"] != 5 or pipeline[0]["compared_stalls"] < 39 or
            any(pipeline[0][name] != 1 for name in ("stall1", "stall7", "stall31")) or
            (depth >= 3 and any(pipeline[0][name] <= 0 for name in
                               ("simultaneous", "queued", "consecutive")))):
        raise AssertionError("DMA pipelined public-pin comparisons lack required coverage")
    evidence.record["observations"].append({
        "scope": "public_DMA_tiles_pipelined_read_order_and_backpressure",
        "seed": seed, "observed": pipeline[0],
        "compute_period_ns": 10, "ddr_period_ns": ddr_period_ns,
        "ddr_phase_ns": ddr_phase_ns,
        "compared_clock_edges": clocks[0],
        "oracle": "accepted read addresses in order against independent byte-address pattern "
                  "and final useful-byte mask; compares stalled payload before and after edges",
    })
    if len(measured) != (11 if depth == 256 else 8):
        raise AssertionError("DMA benchmark missing transfer measurements")
    upper = [row for row in measured if row["base"] == 0x100000fc0]
    if (len(upper) != 1 or upper[0]["beats"] != depth * 5 or
            upper[0]["useful_bytes"] != (depth * 5 - 1) * 64 + 23 or
            upper[0]["same_edge"] != 0 or upper[0]["gapped"] != 1):
        raise AssertionError("DMA upper-bank multibeat byte-address comparison missing")
    for counters in measured:
        beats = counters["beats"]
        if (beats <= 0 or counters["useful_bytes"] <= 0 or
                any(counters[name] <= 0 for name in
                    ("ddr_request_cycles", "ddr_service_cycles",
                     "core_consumption_cycles", "core_completion_cycles"))):
            raise AssertionError("DMA benchmark has empty activity or measurement windows")
        evidence.record.setdefault("dma_benchmarks", []).append({
            "scope": "D1_public_DMA_tiles_simulation_not_physical_EMIF",
            "seed": seed, "observed": counters,
            "random_lfsr_initial_state": (seed or 1) & 0xffffffff,
            "compute_period_ns": 10, "ddr_period_ns": ddr_period_ns,
            "ddr_phase_ns": ddr_phase_ns,
            "clock_scope": ("nominal_application_clocks" if not clock_case else
                            "functional_CDC_stress_not_board_frequency_or_timing_evidence"),
            "raw_DDR_interface_peak_GBps": 64 / ddr_period_ns,
            "single_beat_compute_peak_GBps": 64 / 10,
            "DDR_service_GBps": beats * 64 / (counters["ddr_service_cycles"] * ddr_period_ns),
            "DDR_request_inclusive_GBps": beats * 64 /
                                         (counters["ddr_request_cycles"] * ddr_period_ns),
            "compute_consumed_GBps": counters["useful_bytes"] /
                                    (counters["core_consumption_cycles"] * 10),
            "measurement": {
                "ddr_request_cycles": "core request acceptance to last DDR response, "
                                      "counted as DDR rising edges after acceptance "
                                      "through the response edge inclusive",
                "ddr_service_cycles": "first public Avalon read assertion through final "
                                      "response edge inclusive; includes waitrequest, burst gaps "
                                      "and consumer-induced tile ownership waits",
                "core_consumption_cycles": "core request acceptance through final compared "
                                           "tile-read response retirement",
                "core_completion_cycles": "core request acceptance through observation of "
                                          "completion after every tile has been released",
            },
            "sink": "one synchronous tile read at a time; each response deliberately held "
                    "three compute edges before retirement",
            "reset_policy": "each epoch resets and quiesces the external responder; "
                            "aborted requests are separate from measured completed transfers",
            "limitations": ["compute consumption is a checked tile sink, not the tensor engine",
                            "raw peak is a frequency calculation, not achieved throughput"],
        })
    evidence.flush()


def integration_matrix(evidence, configurations=range(3), seeds=(17, 89, 257),
                       modes=("AWQ", "BF16"), lifecycle=None):
    ledger = evidence.record.setdefault("integration_matrix", [])
    pool = getattr(evidence, "simulation_build_pool", None)
    if pool is None:
        pool = evidence.simulation_build_pool = {}
    for config in configurations:
        for seed in seeds:
            for mode in modes:
                row = {"configuration": config, "shape": vars(MATRIX[config]),
                       "seed": seed, "mode": mode, "outcome": "not_run"}
                ledger.append(row)
    evidence.flush()
    for row in ledger:
        row["outcome"] = "running"
        evidence.flush()
        if lifecycle is not None:
            lifecycle("before_child_creation", None)
        trial = evidence.__class__(
            f"matrix-{row['configuration']}-{row['seed']}-{row['mode'].lower()}",
            source_root=evidence.folder / "sources")
        row["receipt"] = evidence.relative(trial.folder / "receipt.json")
        trial.simulation_build_pool = pool
        trial.record["tool_version_receipt"] = evidence.relative(evidence.folder / "receipt.json")
        evidence.flush()
        if lifecycle is not None:
            lifecycle("after_child_creation", trial)
        try:
            top_probe(trial, row["mode"], row["seed"], config=row["configuration"])
            counters = trial.record["observations"][-1]["observed_counters"]
            shape = MATRIX[row["configuration"]]
            required_tokens = min(shape.max_seq, shape.window + 2) + 1
            tokens = [counter for counter in counters if "position" in counter]
            summaries = [counter for counter in counters if "preload_beats" in counter]
            if (len(tokens) != required_tokens or len(summaries) != 1 or
                    any(token["logits"] != shape.vocab for token in tokens) or
                    summaries[0]["logits"] != required_tokens * shape.vocab or
                    summaries[0]["reads"] <= 0 or summaries[0]["preload_beats"] <= 0):
                raise AssertionError("mandatory matrix case lacks complete observed token/logit/DDR coverage")
        except (OSError, RuntimeError, AssertionError, ValueError) as exc:
            row.update(outcome="failed", reason=str(exc))
            trial.finish("failed", str(exc))
            if lifecycle is not None:
                lifecycle("after_child_failed_finalization", trial)
            evidence.flush()
            raise
        row.update(outcome="compared", tokens=len(tokens),
                   ordered_logits=summaries[0]["logits"],
                   accepted_DDR_read_beats=summaries[0]["reads"],
                   initial_preload_beats=summaries[0]["preload_beats"])
        trial.finish("probe_passed", "Mandatory engineering parameter case; not full-model acceptance.")
        if lifecycle is not None:
            lifecycle("after_child_finalization", trial)
        evidence.flush()


def run_probe(evidence, name, seed, config=0):
    if name == "compatibility-matrix":
        from compatibility import compatibility_matrix
        compatibility_matrix(evidence)
    elif name == "compatibility":
        from compatibility import compatibility
        compatibility(evidence, seed, config)
    elif name == "tensor":
        tensor(evidence, seed)
    elif name == "tensor-sensitivity":
        from sensitivity import run_sensitivity
        evidence.default_simulator = "verilator"
        tensor(evidence, seed)
        run_sensitivity(evidence, seed, only=(
            "tensor_bubble_accumulation", "tensor_high_chunk_carry"))
    elif name == "fixture-integrity":
        fixture_integrity(evidence)
    elif name == "checkpoint-repack":
        from repack import repack
        repack(evidence)
    elif name == "checkpoint-prompts":
        from prompts import prepare
        prepare(evidence)
    elif name == "checkpoint-reference":
        from software_discrepancy import prepare_and_measure
        prepare_and_measure(evidence, seed=seed)
    elif name == "dequant":
        dequant(evidence, seed)
    elif name == "dequant-sensitivity":
        from sensitivity import run_sensitivity
        evidence.default_simulator = "verilator"
        dequant(evidence, seed)
        run_sensitivity(evidence, seed, only=("awq_permutation",))
    elif name == "math":
        math_probe(evidence, seed)
    elif name == "math-sensitivity":
        from sensitivity import run_sensitivity
        evidence.default_simulator = "verilator"
        math_probe(evidence, seed)
        run_sensitivity(evidence, seed, only=("math_negative_tie", "math_sqrt_boundary"))
    elif name == "command-checks":
        from command_checks import command_checks
        command_checks(evidence, seed)
    elif name == "descriptor-checks":
        from descriptor_checks import descriptor_checks
        descriptor_checks(evidence, seed)
    elif name == "address-checks":
        from address_checks import address_checks
        address_checks(evidence, seed)
    elif name == "scalar-checks":
        from scalar_checks import scalar_checks
        scalar_checks(evidence, seed)
    elif name == "upload-conflicts":
        from upload_conflicts import upload_conflicts
        upload_conflicts(evidence, seed)
    elif name == "reset-integration":
        from reset_integration import reset_integration
        reset_integration(evidence, seed)
    elif name in ("numerical-faults", "numerical-fault-smoke"):
        from numerical_faults import numerical_faults
        numerical_faults(evidence, seed, selected=(
            ("awq_embedding_inf", "bf16_weight_0_nonfinite")
            if name == "numerical-fault-smoke" else None))
    elif name == "kernel-default":
        kernel_default(evidence, seed)
    elif name == "attention-context":
        from attention_benchmark import attention_context
        for window, positions in ((1, 1), (3, 3), (3, 9), (128, 131)):
            attention_context(evidence, seed, window, positions)
    elif name == "attention-default":
        from attention_benchmark import attention_context
        for window, positions in ((128, 3), (3, 5)):
            attention_context(evidence, seed, window, positions, default_width=True)
    elif name in ("layer-awq", "layer-bf16"):
        from layer_benchmark import layer_default
        layer_default(evidence, seed, name[6:].upper())
    elif name == "projection-default":
        from benchmarks import projection_default
        projection_default(evidence, seed)
    elif name == "projection-k":
        from benchmarks import projection_default
        projection_default(evidence, seed, (1,), simulator="verilator")
    elif name == "arithmetic-default":
        from arithmetic_benchmark import arithmetic_default
        arithmetic_default(evidence, seed)
    elif name in ("bf16-default", "vocabulary-default"):
        from benchmarks import dense_default
        dense_default(evidence, seed, vocabulary=name == "vocabulary-default")
    elif name == "integration-matrix":
        integration_matrix(evidence)
    elif name == "matrix-config":
        integration_matrix(evidence, (config,))
    elif name == "csr-upload":
        top_probe(evidence, "AWQ", seed, True, config)
    elif name == "synthesis":
        synthesis_probe(evidence)
    elif name == "synthesis-small":
        synthesis_probe(evidence, MATRIX[1])
    elif name == "synthesis-control":
        synthesis_fault_control(evidence)
    elif name == "kv":
        for depth in (1, 3, 128):
            kv_probe(evidence, depth)
            kv_probe(evidence, depth, max_sequence=32768)
        from kv_faults import kv_faults
        kv_faults(evidence, seed)
    elif name in ("kv-default", "kv-default-sensitivity"):
        kv_probe(evidence, 128, max_sequence=32768, layers=24, head_dim=64)
        if name == "kv-default-sensitivity":
            from sensitivity import run_sensitivity
            run_sensitivity(evidence, seed, only=("kv_default_layer_alias",))
    elif name in ("kv-faults", "kv-fault-sensitivity"):
        from kv_faults import kv_faults
        if name == "kv-fault-sensitivity":
            from sensitivity import run_sensitivity
            evidence.default_simulator = "verilator"
        kv_faults(evidence, seed)
        if name == "kv-fault-sensitivity":
            run_sensitivity(evidence, seed, only=(
                "kv_eviction_error_ignored", "kv_cold_error_ignored"))
    elif name == "parameters":
        invalid_parameters(evidence)
    elif name in ("dma", "dma-compiled"):
        if name == "dma-compiled":
            evidence.default_simulator = "verilator"
        for depth in (1, 3, 256):
            dma_probe(evidence, depth, seed)
        for period, phase in ((3.75, 1.25), (20, 2.5)):
            dma_probe(evidence, 3, seed, ddr_period_ns=period, ddr_phase_ns=phase)
        from dma_upload import upload_checks
        upload_checks(evidence, seed)
    elif name in ("dma-upload", "dma-upload-sensitivity"):
        from dma_upload import upload_checks
        upload_checks(evidence, seed)
        if name == "dma-upload-sensitivity":
            from sensitivity import run_sensitivity
            run_sensitivity(evidence, seed, only=(
                "upload_byteenable_ignored", "upload_address_high_bit_lost"))
    elif name == "sensitivity":
        from sensitivity import run_sensitivity
        run_sensitivity(evidence, seed)
    elif name == "dma-pipeline-sensitivity":
        from sensitivity import run_sensitivity
        run_sensitivity(evidence, seed, only=("tile_read_backpressure",))
    elif name == "arithmetic-sensitivity":
        from sensitivity import run_sensitivity
        run_sensitivity(evidence, seed, only=("matched_arithmetic_lane_sign",))
    elif name == "layer-sensitivity":
        from sensitivity import run_sensitivity
        run_sensitivity(evidence, seed, only=("layer_lane_sign",))
    elif name == "attention-sensitivity":
        from sensitivity import run_sensitivity
        run_sensitivity(evidence, seed, only=("attention_cold_value", "attention_drop_cold_term"))
    elif name == "numerical-fault-sensitivity":
        from sensitivity import run_sensitivity
        run_sensitivity(evidence, seed, only=(
            "stored_fp16_nonfinite", "stored_bf16_nonfinite", "stored_negative_scale"))
    elif name == "command-sensitivity":
        from sensitivity import run_sensitivity
        run_sensitivity(evidence, seed, only=(
            "command_new_sequence_position", "command_busy_mode_mutation"))
    elif name == "upload-conflict-sensitivity":
        from sensitivity import run_sensitivity
        run_sensitivity(evidence, seed, only=("pending_upload_busy_ownership",))
    elif name == "reset-sensitivity":
        from sensitivity import run_sensitivity
        run_sensitivity(evidence, seed, only=("reset_descriptor_validity",))
    elif name == "descriptor-sensitivity":
        from descriptor_checks import descriptor_checks
        descriptor_checks(evidence, seed)
        from sensitivity import run_sensitivity
        run_sensitivity(evidence, seed, only=(
            "descriptor_region_overlap", "descriptor_extended_bank_end",
            "descriptor_token_snapshot_bypass", "descriptor_read_snapshot_bypass"))
    elif name == "address-sensitivity":
        from sensitivity import run_sensitivity
        run_sensitivity(evidence, seed, only=(
            "address_tail_stride", "address_byte_lane"))
    elif name == "scalar-sensitivity":
        from sensitivity import run_sensitivity
        run_sensitivity(evidence, seed, only=(
            "scalar_issue_response", "scalar_response_error"))
    elif name in ("late-read-faults", "late-read-sensitivity"):
        from late_faults import late_read_faults
        late_read_faults(evidence, seed)
        if name == "late-read-sensitivity":
            from sensitivity import run_sensitivity
            run_sensitivity(evidence, seed, only=(
                "late_read_error_ignored", "late_read_sequence_reuse"))
    elif name == "faults":
        model = EngineeringModel(MATRIX[0], seed, "AWQ")
        last_write = len(model.image) // 64 - 1
        for kind, beats in (("read", (0, 110, 220)),
                            ("write", (0, last_write // 2, last_write))):
            for beat in beats:
                trial = evidence.__class__(f"{kind}-fault-{beat}",
                                           source_root=evidence.folder / "sources")
                trial.simulation_build_pool = evidence.simulation_build_pool
                trial.record["tool_version_receipt"] = evidence.relative(evidence.folder / "receipt.json")
                try:
                    top_probe(trial, "AWQ", seed, **{"fault_" + kind: beat})
                except (RuntimeError, AssertionError, ValueError) as exc:
                    trial.finish("failed", str(exc))
                    raise
                trial.finish("probe_passed", f"Observed public {kind} fault at traffic beat {beat}.")
                evidence.record["observations"].append({
                    "fault": kind, "beat": beat,
                    "receipt": evidence.relative(trial.folder / "receipt.json")})
                evidence.flush()
        from late_faults import late_read_faults
        late_read_faults(evidence, seed)
    elif name == "orphan-fault":
        top_probe(evidence, "AWQ", seed, orphan_fault=True)
    elif name == "abort-states":
        for mode in ("AWQ", "BF16"):
            for stage in ("embedding-pending", "waitrequest", "kernel", "projection", "stalled-logit"):
                top_probe(evidence, mode, seed, config=config, abort_stage=stage)
    elif name.startswith("top-"):
        top_probe(evidence, name[4:].upper(), seed, config=config)
    else:
        raise ValueError(f"unknown probe: {name}")
