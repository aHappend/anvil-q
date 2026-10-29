"""D1/D2 public-pin DMA-to-tensor measurements, not physical EMIF evidence.

The bounded projection-bandwidth probe keeps the original unstalled parent
comparison and independently checks every accepted lane operand and result.
Additional 1/7/31-cycle burst-command stalls are diagnostic measurements, not a
replacement for the frozen unstalled >=8x service-inclusive acceptance.
The same integrated comparisons must reject separately compiled lane-sign and
DMA-address defects in disposable RTL copies.
"""

import hashlib
import re

from reference import bf16, fp16


def replace_once(text, old, new):
    if text.count(old) != 1:
        raise AssertionError(f"projection instrumentation anchor is not unique: {old!r}")
    return text.replace(old, new, 1)


def instrument(evidence, bench, mode, projection, inputs, outputs, seed, stall,
               activation, qweight, qzero, scale, bias, dense_bits, expected):
    if (projection, inputs, outputs) != (1, 896, 128) or stall not in (0, 1, 7, 31):
        raise ValueError("bandwidth probe is bounded to default K projection and admitted stalls")
    vectors = []
    for panel in range(0, outputs, 64):
        for row in range(inputs + 1):
            is_bias = row == inputs
            weights = [
                fp16(bias(col)) if is_bias else
                (qweight(row, col) - qzero(row // 128, col)) * fp16(scale(row // 128, col))
                if mode == "AWQ" else bf16(dense_bits(row, col))
                for col in range(panel, panel + 64)
            ]
            word = sum((weight & ((1 << 37) - 1)) << (37 * lane)
                       for lane, weight in enumerate(weights))
            word |= ((65536 if is_bias else activation(row)) & 0xffffffff) << 2368
            word |= int(row == 0) << 2400
            word |= int(is_bias) << 2401
            vectors.append(word)
    vector_path = evidence.folder / f"bandwidth-{mode.lower()}-vectors.hex"
    vector_path.write_text("".join(f"{word:0601x}\n" for word in vectors))
    evidence.record.setdefault("projection_bandwidth_inputs", []).append({
        "mode": mode, "projection": projection, "seed": seed,
        "burst_command_stall_edges": stall,
        "operand_file": evidence.relative(vector_path),
        "operand_sha256": hashlib.sha256(vector_path.read_bytes()).hexdigest(),
        "expected_vectors": len(vectors), "expected_lane_operands": len(vectors) * 64,
        "expected_results": len(expected),
    })
    evidence.flush()
    declarations = r"""
reg [2401:0] expected_vector [0:VECTOR_LAST];
integer operand_checks=0,result_checks=0,weight_bytes=0,bias_vectors=0;
integer first_ddr=-1,last_ddr=-1,first_compute=-1,last_compute=-1;
integer tile_acquires=0,tile_releases=0,fill_during_dot=0;
integer stalled_ddr_edges=0,stall_left=0,current_stall=0,max_stall=0;
integer live_dot=0;
reg next_bank=0,stall_seen=0,bandwidth_held=0;
reg [106:0] bandwidth_payload;
wire bandwidth_waitrequest=stall_left>0;
always @(negedge ddr_clk) begin
 if(!rst_n || !avm_read) begin stall_seen=0;stall_left=0;end
 else if(!stall_seen) begin stall_seen=1;stall_left=STALL_EDGES;end
 else if(stall_left>0) stall_left=stall_left-1;
end
always @(posedge ddr_clk) if(rst_n) begin
 if(avm_read && bandwidth_waitrequest) begin
  stalled_ddr_edges=stalled_ddr_edges+1;
  current_stall=current_stall+1;
  if(current_stall>max_stall) max_stall=current_stall;
 end else current_stall=0;
 if(bandwidth_held &&
    {avm_address,avm_burstcount,avm_read,avm_write,avm_byteenable}!==bandwidth_payload)
  $fatal(1,"BANDWIDTH_STALLED_COMMAND_CHANGED");
 bandwidth_held=avm_read && bandwidth_waitrequest;
 if(bandwidth_held)
  bandwidth_payload={avm_address,avm_burstcount,avm_read,avm_write,avm_byteenable};
 if(avm_read && !bandwidth_waitrequest && first_ddr<0) first_ddr=ddr_cycles;
 if(avm_readdatavalid) last_ddr=ddr_cycles;
 if(fill_data_valid && fill_data_ready && live_dot) fill_during_dot=fill_during_dot+1;
end
integer checked_lane;
always @(posedge clk) if(rst_n) begin
 if(tile_valid && tile_ready) begin
  if(tile_bank!==next_bank) $fatal(1,"BANDWIDTH_BANK_ORDER");
  next_bank=!next_bank;tile_acquires=tile_acquires+1;
 end
 if(release_valid && release_ready) tile_releases=tile_releases+1;
 if(tensor_in_valid && tensor_in_ready) begin
  if(operand_checks>=VECTOR_COUNT || tensor_in_mask!==64'hffffffffffffffff ||
     {tensor_in_last,tensor_in_first,tensor_in_activation,tensor_in_weights}
       !==expected_vector[operand_checks])
   $fatal(1,"BANDWIDTH_TENSOR_OPERAND_MISMATCH vector=%0d",operand_checks);
  if(first_compute<0) first_compute=core_cycles;
  last_compute=core_cycles;
  if(tensor_in_first) begin
   if(live_dot) $fatal(1,"BANDWIDTH_OVERLAPPING_DOTS");
   live_dot=1;
  end
  if(tensor_in_last) bias_vectors=bias_vectors+1;
  else weight_bytes=weight_bytes+WEIGHT_BYTES_PER_VECTOR;
  operand_checks=operand_checks+1;
 end
 if(tensor_out_valid && tensor_out_ready) begin
  if(!live_dot || tensor_out_mask!==64'hffffffffffffffff)
   $fatal(1,"BANDWIDTH_TENSOR_RESULT_PROTOCOL");
  for(checked_lane=0;checked_lane<64;checked_lane=checked_lane+1) begin
   if(result_checks>=128 || tensor_out_data[32*checked_lane+:32]!==expected[result_checks])
    $fatal(1,"BANDWIDTH_TENSOR_RESULT_MISMATCH lane=%0d",checked_lane);
   result_checks=result_checks+1;
  end
  live_dot=0;
 end
end
"""
    substitutions = {
        "VECTOR_LAST": len(vectors) - 1, "VECTOR_COUNT": len(vectors),
        "STALL_EDGES": stall, "WEIGHT_BYTES_PER_VECTOR": 32 if mode == "AWQ" else 128,
    }
    for key, value in substitutions.items():
        declarations = declarations.replace(key, str(value))
    bench = replace_once(bench, "integer port_index;", declarations + "\ninteger port_index;")
    bench = replace_once(bench, "if(avm_read) begin",
                         "if(avm_read && !bandwidth_waitrequest) begin")
    bench = replace_once(bench, ".avm_waitrequest(1'b0)",
                         ".avm_waitrequest(bandwidth_waitrequest)")
    image_load = next(line for line in bench.splitlines() if
                      '$readmemh("' in line and ",memory);" in line)
    bench = replace_once(
        bench, image_load,
        f' $readmemh("{evidence.relative(vector_path)}",expected_vector);\n' + image_load)
    final = r"""
 if(operand_checks!=VECTOR_COUNT || result_checks!=128 || bias_vectors!=2 ||
    weight_bytes!=EXPECTED_WEIGHT_BYTES || first_ddr<0 || last_ddr<first_ddr ||
    first_compute<0 || last_compute<first_compute || tile_acquires!=tile_releases ||
    tile_acquires<4 || live_dot || max_stall!=STALL_EDGES ||
    stalled_ddr_edges!=bursts*STALL_EDGES)
  $fatal(1,"BANDWIDTH_MISSING_CONSERVED_ACTIVITY");
 if(BF16_FLAG && fill_during_dot==0) $fatal(1,"BANDWIDTH_MISSING_FILL_COMPUTE_OVERLAP");
 $display("BANDWIDTH operands=%0d lane_operands=%0d results=%0d weight_bytes=%0d ddr_bytes=%0d ddr_edges=%0d compute_edges=%0d inference_edges=%0d tiles=%0d fill_during_dot=%0d stalled_ddr_edges=%0d max_stall=%0d",
          operand_checks,operand_checks*64,result_checks,weight_bytes,read_beats*64,
          last_ddr-first_ddr+1,last_compute-first_compute+1,ht_cycles,
          tile_acquires,fill_during_dot,stalled_ddr_edges,max_stall);
"""
    for key, value in {
        "VECTOR_COUNT": len(vectors), "EXPECTED_WEIGHT_BYTES": inputs * outputs *
        (1 if mode == "AWQ" else 4) // 2, "STALL_EDGES": stall,
        "BF16_FLAG": int(mode == "BF16"),
    }.items():
        final = final.replace(key, str(value))
    return replace_once(bench, ' $display("MEASURED ', final + '\n $display("MEASURED ')


def retain_measurement(evidence, transcript, mode, inputs, outputs, stall):
    rows = [line for line in transcript.splitlines() if line.startswith("BANDWIDTH ")]
    if len(rows) != 1 or not re.fullmatch(r"BANDWIDTH(?: [a-z_]+=[0-9]+)+", rows[0]):
        raise AssertionError("missing unique integrated bandwidth counters")
    observed = {key: int(value) for key, value in
                (field.split("=") for field in rows[0].split()[1:])}
    expected_bytes = inputs * outputs * (1 if mode == "AWQ" else 4) // 2
    if observed["weight_bytes"] != expected_bytes or observed["results"] != outputs:
        raise AssertionError("integrated bandwidth byte/result conservation failure")
    if min(observed[name] for name in ("ddr_edges", "compute_edges", "inference_edges")) <= 0:
        raise AssertionError("integrated bandwidth measurement interval is empty")
    evidence.record.setdefault("projection_bandwidth", []).append({
        "scope": "simulated_default_K_projection_public_pin_comparison",
        "mode": mode, "command_stall_edges": stall, "observed": observed,
        "compute_frequency_hz": 100_000_000, "ddr_frequency_hz": 1e9 / 3.75,
        "raw_DDR_peak_bytes_per_second": 64e9 / 3.75,
        "DDR_service_bytes_per_second": observed["ddr_bytes"] * 1e9 /
                                        (3.75 * observed["ddr_edges"]),
        "tensor_consumed_weight_bytes_per_second": expected_bytes * 1e8 /
                                                   observed["compute_edges"],
        "service_inclusive_weight_bytes_per_second": expected_bytes * 1e8 /
                                                     observed["inference_edges"],
        "boundaries": {
            "DDR": "first accepted Avalon read command through final accepted response, inclusive",
            "tensor": "first through final accepted tensor vector, inclusive; includes all feed gaps",
            "service_inclusive": "original accepted projection command through sampled done",
            "weight_bytes": "packed AWQ or BF16 matrix bytes only; excludes scales, zero points and bias",
            "overlap": "DDR fill beat accepted while a real tensor dot awaits its result",
        },
        "limitations": [
            "synthetic tensors, not checkpoint or physical DDR measurements",
            "K projection only; not full L1 closure or all-projection speedup acceptance",
            "logical activation/scratch service, not complete decoder service",
        ],
    })
    evidence.flush()


def sensitivity_trial(evidence, seed):
    from benchmarks import projection_case
    projection_case(evidence, seed, 1, "verilator", mode="AWQ", bandwidth_stall=7)


def run(evidence, seed):
    from benchmarks import projection_case
    for stall in (0, 1, 7, 31):
        for mode in ("AWQ", "BF16"):
            from verify import Evidence
            child = Evidence(f"projection-bandwidth-{mode.lower()}-{stall}",
                             source_root=evidence.folder / "sources")
            try:
                record = projection_case(child, seed, 1, "verilator", mode=mode,
                                         bandwidth_stall=stall)
                if stall == 0 and mode == "AWQ" and not record["threshold_met"]:
                    raise AssertionError("unchanged nominal AWQ speedup is below 8x")
                child.finish("probe_passed", "Bounded integrated operand/result and bandwidth measurement.")
                evidence.record.setdefault("projection_bandwidth_children", []).append({
                    "receipt": evidence.relative(child.folder / "receipt.json"),
                    "measurement": child.record["projection_bandwidth"],
                })
                evidence.flush()
            except Exception as exc:
                child.finish("failed", f"{type(exc).__name__}: {exc}")
                raise
    from sensitivity import run_sensitivity
    run_sensitivity(evidence, seed, only=(
        "projection_bandwidth_lane_sign", "projection_bandwidth_dma_cursor"))
