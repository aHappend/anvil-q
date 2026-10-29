"""D2 matched eight/64-active-lane arithmetic, separate from parent service."""

import hashlib

from experiments import CLOCK, measurement_records
from reference import fp16, round_shift, sat32


def arithmetic_default(evidence, seed):
    shapes = [(896, width) for width in (896, 128, 128, 896, 4864, 4864)]
    shapes.append((4864, 896))
    cases = []
    expected_hashes = []
    for projection, (inputs, outputs) in enumerate(shapes):
        expected = []
        for col in range(outputs):
            total = sum(
                (((row * 997 + seed * 53) % 131071) - 65535) *
                (((row * 7 + col * 11 + (row >> 3) + seed) & 15) -
                 (((row // 128) * 3 + col * 5 + seed) & 15)) *
                fp16(0x2400 + 0x400 * (((row // 128) + col + seed) % 3))
                for row in range(inputs))
            expected.append(sat32(round_shift(total, 16)))
        path = evidence.folder / f"arithmetic-{projection}-expected.hex"
        path.write_text("".join(f"{value & 0xffffffff:08x}\n" for value in expected))
        expected_hashes.append(hashlib.sha256(path.read_bytes()).hexdigest())
        evidence.record.setdefault("runtime_input_sha256", {})[
            evidence.relative(path)] = expected_hashes[-1]
        cases.append(
            f'$readmemh("{evidence.relative(path)}", expected, 0, {outputs - 1});\n'
            f'run_case({projection}, {inputs}, {outputs}, 8);\n'
            f'run_case({projection}, {inputs}, {outputs}, 64);')
    evidence.flush()
    bench = CLOCK + r"""
reg in_valid=0,in_first=0,in_last=0,out_ready=0;
reg signed [31:0] in_activation=0;
reg [2367:0] in_weight_q16=0;
reg [63:0] in_mask=0;
wire in_ready,out_valid,protocol_error;
wire [2047:0] out_data;
wire [63:0] out_mask;
reg [31:0] expected [0:4863];
integer cycles=0,comparisons=0,vectors=0,dots=0;
anvil_q1_ht_tensor_array product(
 .clk(clk),.rst_n(rst_n),.in_valid(in_valid),.in_ready(in_ready),
 .in_first(in_first),.in_last(in_last),.in_activation(in_activation),
 .in_weight_q16(in_weight_q16),.in_mask(in_mask),
 .out_valid(out_valid),.out_ready(out_ready),.out_data(out_data),
 .out_mask(out_mask),.protocol_error(protocol_error));
always @(posedge clk) cycles<=cycles+1;
function automatic signed [36:0] weight(input integer row,col);
 integer group_index,q,z,scale;
 begin
  group_index=row/128;
  q=(row*7+col*11+(row>>3)+SEED_VALUE)&15;
  z=(group_index*3+col*5+SEED_VALUE)&15;
  case((group_index+col+SEED_VALUE)%3)
   0:scale=1024;
   1:scale=2048;
   2:scale=4096;
  endcase
  weight=(q-z)*scale;
 end
endfunction
task reset_check;
 begin
  if({in_ready,out_valid,out_data,out_mask,protocol_error} !== 2115'b0)
   $fatal(1,"ARITHMETIC_RESET_XZ_OR_NONZERO");
 end
endtask
always @(posedge clk or negedge clk) if(!rst_n) reset_check();
task run_case(input integer projection,inputs,outputs,active);
 integer panel,row,lane,latency,last_edge,first_edge,retired_edge;
 integer before_compares,before_vectors,before_dots;
 reg [63:0] mask;
 begin
  before_compares=comparisons;before_vectors=vectors;before_dots=dots;
  first_edge=-1;
  mask=active==64 ? 64'hffffffffffffffff : 64'hff;
  for(panel=0;panel<outputs;panel=panel+active) begin
   for(row=0;row<inputs;row=row+1) begin
    @(negedge clk);
    in_valid=1;in_first=row==0;in_last=row==inputs-1;
    in_activation=((row*997+SEED_VALUE*53)%131071)-65535;
    in_mask=mask;
    for(lane=0;lane<64;lane=lane+1)
     in_weight_q16[37*lane+:37]=lane<active ? weight(row,panel+lane) : 0;
    #0.001;
    if(in_ready!==1) $fatal(1,"ARITHMETIC_INPUT_II");
    edge_tick();
    if(first_edge<0) first_edge=cycles;
    if(out_valid!==0 || protocol_error!==0) $fatal(1,"ARITHMETIC_EARLY_RESULT");
    vectors=vectors+1;
   end
   last_edge=cycles;
   @(negedge clk);in_valid=0;in_first=0;in_last=0;
   for(latency=1;latency<=10;latency=latency+1) begin
    edge_tick();
    if(protocol_error!==0 || out_valid!==(latency==10))
     $fatal(1,"ARITHMETIC_LAST_TO_RESULT_LATENCY");
   end
   if(cycles-last_edge!=10 || out_mask!==mask || in_ready!==0)
    $fatal(1,"ARITHMETIC_MASK_OR_OVERLAP");
   for(lane=0;lane<64;lane=lane+1) begin
    if(lane<active) begin
     if(out_data[32*lane+:32]!==expected[panel+lane])
      $fatal(1,"ARITHMETIC_MISMATCH projection=%0d active=%0d col=%0d",
              projection,active,panel+lane);
     comparisons=comparisons+1;
    end else if(out_data[32*lane+:32]!==0)
     $fatal(1,"ARITHMETIC_MASKED_OUTPUT_NONZERO");
   end
   @(negedge clk);out_ready=1;
   edge_tick();retired_edge=cycles;
   if(out_valid!==0 || protocol_error!==0) $fatal(1,"ARITHMETIC_RETIREMENT");
   @(negedge clk);out_ready=0;
   dots=dots+1;
  end
  if(comparisons-before_compares!=outputs || vectors-before_vectors!=inputs*(outputs/active) ||
     dots-before_dots!=outputs/active)
   $fatal(1,"ARITHMETIC_MISSING_COMPARISONS");
  $display("MEASURED_ARITHMETIC projection=%0d inputs=%0d outputs=%0d active=%0d cycles=%0d compared=%0d vectors=%0d dots=%0d",
           projection,inputs,outputs,active,retired_edge-first_edge+1,
           comparisons-before_compares,vectors-before_vectors,dots-before_dots);
 end
endtask
initial begin
 rst_n=0;`RESET_DELTA reset_check();
 repeat(3) edge_tick();
 @(negedge clk);rst_n=1;
 repeat(3) edge_tick();
CASES_VALUE
 $display("CHECKS_PASSED arithmetic comparisons=%0d vectors=%0d dots=%0d",
          comparisons,vectors,dots);
 $finish;
end
endmodule
"""
    transcript = evidence.simulate(
        "arithmetic-default",
        bench.replace("SEED_VALUE", str(seed)).replace("CASES_VALUE", "\n".join(cases)),
        ["anvil_q1_ht_mac_lane.sv", "anvil_q1_ht_tensor_array.sv"],
        simulator="verilator", timeout=14400)
    rows = measurement_records(transcript, "MEASURED_ARITHMETIC")
    if len(rows) != 14:
        raise AssertionError("matched arithmetic benchmark lacks all projection/lane cases")
    results = []
    for projection, (inputs, outputs) in enumerate(shapes):
        pair = {}
        for row in rows:
            if row["projection"] != projection:
                continue
            active = row["active"]
            if (active not in (8, 64) or active in pair or row["inputs"] != inputs or
                    row["outputs"] != outputs or row["compared"] != outputs or
                    row["vectors"] != inputs * (outputs // active) or
                    row["dots"] != outputs // active or row["cycles"] <= 0):
                raise AssertionError("matched arithmetic shape/comparison coverage missing")
            pair[active] = row
        if set(pair) != {8, 64}:
            raise AssertionError("matched arithmetic lane pair missing")
        results.append({
            "projection": projection, "observed": list(pair.values()),
            "eight_to_64_active_lane_speedup": pair[8]["cycles"] / pair[64]["cycles"],
            "expected_sha256": expected_hashes[projection],
        })
    evidence.record["matched_arithmetic_benchmarks"] = {
        "scope": "D2_matched_packed_arithmetic_not_parent_service_or_physical_mapping",
        "seed": seed, "mode": "AWQ", "compute_period_ns": 10,
        "reference": "independent exact integer AWQ dot, final ties-away rounding and saturation",
        "baseline": "same product tensor pipeline, eight active low lanes per panel; "
                    "not an independently synthesized eight-lane engine or immutable parent",
        "parallel": "same pipeline, all 64 active lanes per panel",
        "input_policy": "identical predequantized packed weights and scalar activations; "
                        "one accepted vector each edge of each dot; no transport/dequantization stalls",
        "measurement": "first accepted vector through final output retirement inclusive; "
                       "includes ten-edge result latency, retirement and inter-dot setup gaps",
        "bias_policy": "unbiased exact dots only; biased projection correctness is checked "
                       "separately by the integrated parent/HT service benchmark",
        "warmup": "three reset and three idle compute edges, no warmup dot",
        "results": results,
    }
    evidence.record["observations"].append({
        "scope": "matched_arithmetic", "projection_pairs": len(results),
        "ordered_output_comparisons": sum(row["compared"] for row in rows),
    })
    evidence.flush()
