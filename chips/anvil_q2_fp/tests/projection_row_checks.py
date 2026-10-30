"""Real native-geometry GEMV first-row-group tests, not full-projection timing.

For Q and down projections, check all native input columns for the first eight
output rows of each bank. Stop each public bank client after its eighth write
acknowledgement, then explicitly reset the still-active full projection. No
legal dimension is clamped and no complete native-token throughput is claimed.
"""

import argparse
import hashlib
import json
import sys
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from codec_checks import SHIFTS
from fp_reference import add, convert, multiply, rounded
from retained import ROOT, Run, require_time_zero, with_time_zero_check
from simulation import compile_model, startup_check, stream_model


BENCH = r"""
module tb;
  parameter BANKS=4,FORMAT=0,WEIGHTS=0,PROJECTION=0,INPUTS=1536,GROUPS=12;
  reg clk=0,rst_n,cmd_valid=0;
  string fixture_dir;
  always #5 clk=~clk;
  wire ready,done,error;
  wire mv,mw,mrr;
  wire [3:0] mk;
  wire [2:0] mp;
  wire [31:0] ml,mrow,mcol,md;
  wire [BANKS-1:0] qv,qw,sr;
  reg [BANKS-1:0] qr=0,sv=0;
  wire [BANKS*4-1:0] qk;
  wire [BANKS*3-1:0] qp;
  wire [BANKS*32-1:0] ql,qrow,qcol,qd;
  reg [BANKS*32-1:0] sd=0;
  reg [31:0] activations[0:INPUTS-1];
  reg [15:0] weights[0:INPUTS*BANKS*8-1];
  reg [31:0] packed_weights[0:INPUTS*BANKS-1],zeros[0:GROUPS*BANKS-1];
  reg [15:0] scales[0:GROUPS*BANKS*8-1],biases[0:BANKS*8-1];
  reg [31:0] expected[0:BANKS*8-1];
  integer rows[0:BANKS-1],due[0:BANKS-1],stalls[0:BANKS-1];
  integer writes_acked[0:BANKS-1];
  reg pending[0:BANKS-1],pending_write[0:BANKS-1],held[0:BANKS-1];
  reg [31:0] response[0:BANKS-1];
  reg [135:0] payload[0:BANKS-1];
  reg [BANKS*8-1:0] seen=0;
  integer b,i,kind,row,col,proj,cycle=0,command_cycle=0,reads=0,acks=0,compared=0;
  integer total_acked=0,source_slot,target_slot;
  reg [31:0] data;
  anvil_q2_fp_gemv #(.BANKS(BANKS),.EXTERNAL_CLIENTS(1),
    .FP_FORMAT(FORMAT),.WEIGHT_MODE(WEIGHTS)) dut(
    clk,rst_n,cmd_valid,ready,32'd0,32'd0,3'(PROJECTION),done,error,
    mv,1'b0,mw,mk,ml,mp,mrow,mcol,md,1'b0,mrr,32'd0,1'b0,
    qv,qr,qw,qk,ql,qp,qrow,qcol,qd,sv,sr,sd,{BANKS{1'b0}});
  initial begin
    rst_n=0;
    if(!$value$plusargs("FIXTURES=%s",fixture_dir)) $fatal(1,"MISSING_FIXTURES");
    $readmemh({fixture_dir,"/activations.hex"},activations);
    $readmemh({fixture_dir,"/weights.hex"},weights);
    $readmemh({fixture_dir,"/packed.hex"},packed_weights);
    $readmemh({fixture_dir,"/zeros.hex"},zeros);
    $readmemh({fixture_dir,"/scales.hex"},scales);
    $readmemh({fixture_dir,"/biases.hex"},biases);
    $readmemh({fixture_dir,"/expected.hex"},expected);
    source_slot=PROJECTION==0 ? 1 : 11;
    target_slot=PROJECTION==0 ? 2 : 12;
    for(i=0;i<BANKS;i=i+1) begin
      rows[i]=0; due[i]=0; stalls[i]=0; writes_acked[i]=0;
      pending[i]=0; pending_write[i]=0; held[i]=0; response[i]=0; payload[i]=0;
    end
    #1;
    if({ready,done,error,mv,mw,mk,ml,mp,mrow,mcol,md,mrr,
        qv,qw,qk,ql,qp,qrow,qcol,qd,sr} !== 0) $fatal(1,"RESET_NONZERO_X");
    repeat(2) @(negedge clk); rst_n=1;
    @(negedge clk); cmd_valid=1;
    do @(posedge clk); while(!ready);
    command_cycle=cycle;
    @(negedge clk); cmd_valid=0;
    do @(negedge clk); while(total_acked<BANKS*8);
    if(compared!=BANKS*8 || seen !== {BANKS*8{1'b1}} || reads<INPUTS*BANKS*2)
      $fatal(1,"FULL_ROW_COMPARISON_COVERAGE");
    if(done || ready || error) $fatal(1,"PARTIAL_PROJECTION_MISLABELLED_COMPLETE");
    for(i=0;i<BANKS;i=i+1)
      if(pending[i] || sv[i] || writes_acked[i]!=8 || stalls[i]==0)
        $fatal(1,"FIRST_ROW_GROUP_NOT_ACKNOWLEDGED");
    $display("NATIVE_ROW_GROUP_COMPARED %0d %0d %0d %0d %0d %0d",
      INPUTS,BANKS*8,reads,acks,cycle-command_cycle,compared);
    // Discard only unaccepted subsequent-row requests with a real reset.
    #1; rst_n=0;
    #1;
    if({ready,done,error,mv,mw,mk,ml,mp,mrow,mcol,md,mrr,
        qv,qw,qk,ql,qp,qrow,qcol,qd,sr} !== 0) $fatal(1,"ROW_GROUP_RESET_X");
    repeat(2) @(negedge clk);
    $finish;
  end
  always @(negedge clk) if(rst_n) begin
    for(integer k=0;k<BANKS;k=k+1) begin
      qr[k]=writes_acked[k]<8 && !pending[k] && (cycle+k)%7>1;
      if(pending[k] && !sv[k] && cycle>=due[k]) begin
        sv[k]=1; sd[k*32+:32]=response[k];
      end
    end
  end
  always @(posedge clk or negedge clk)
    if(!rst_n && $time>0 &&
       {ready,done,error,mv,mw,mk,ml,mp,mrow,mcol,md,mrr,
        qv,qw,qk,ql,qp,qrow,qcol,qd,sr} !== 0) $fatal(1,"RESET_EDGE_NONZERO_X");
  always @(posedge clk) begin
    cycle<=cycle+1;
    if(rst_n) begin
      if((^{ready,done,error,qv,sr}) === 1'bx) $fatal(1,"PROJECTION_CONTROL_X");
      if(error || done || mv) $fatal(1,"UNEXPECTED_FULL_PROJECTION_COMPLETION");
      for(b=0;b<BANKS;b=b+1) begin
        if(held[b] && (qv[b] !== 1'b1 ||
           {qw[b],qk[b*4+:4],ql[b*32+:32],qp[b*3+:3],qrow[b*32+:32],
            qcol[b*32+:32],qd[b*32+:32]} !== payload[b]))
          $fatal(1,"ROW_GROUP_REQUEST_INSTABILITY");
        held[b]=qv[b] && !qr[b];
        payload[b]={qw[b],qk[b*4+:4],ql[b*32+:32],qp[b*3+:3],qrow[b*32+:32],
                    qcol[b*32+:32],qd[b*32+:32]};
        if(qv[b] && !qr[b]) stalls[b]=stalls[b]+1;
        if(sv[b] && sr[b]) begin
          sv[b]<=0; pending[b]=0; acks=acks+1;
          if(pending_write[b]) begin
            writes_acked[b]=writes_acked[b]+1; total_acked=total_acked+1;
          end
        end
        if(qv[b] && qr[b]) begin
          if((^{qw[b],qk[b*4+:4],ql[b*32+:32],qp[b*3+:3],qrow[b*32+:32],
                qcol[b*32+:32],qd[b*32+:32]}) === 1'bx) $fatal(1,"NATIVE_ROW_REQUEST_X");
          kind=qk[b*4+:4]; row=qrow[b*32+:32]; col=qcol[b*32+:32]; proj=qp[b*3+:3];
          if(ql[b*32+:32]!=0 || (kind!=8 && proj!=PROJECTION) || (kind==8 && proj!=0))
            $fatal(1,"NATIVE_ROW_LAYER_PROJECTION");
          data=0;
          if(qw[b]) begin
            if(kind!=8 || row!=target_slot || col<8*b || col>=8*b+8 || seen[col])
              $fatal(1,"NATIVE_ROW_WRITE_ASSOCIATION");
            if(qd[b*32+:32] !== expected[col])
              $fatal(1,"NATIVE_PROJECTION_ROW_MISMATCH row=%0d got=%08h expected=%08h",
                col,qd[b*32+:32],expected[col]);
            seen[col]=1; compared=compared+1; rows[b]=rows[b]+1;
          end else case(kind)
            8: begin
              if(row!=source_slot || col>=INPUTS) $fatal(1,"NATIVE_ACTIVATION_ADDRESS");
              data=activations[col];
            end
            1: begin
              if(row>=INPUTS) $fatal(1,"NATIVE_WEIGHT_INPUT_ADDRESS");
              if(WEIGHTS==0) begin
                if(col<8*b || col>=8*b+8) $fatal(1,"NATIVE_WEIGHT_ROW_ADDRESS");
                data={16'd0,weights[row*BANKS*8+col]};
              end else begin
                if(col!=b) $fatal(1,"AWQ_PACKED_ROW_ADDRESS");
                data=packed_weights[row*BANKS+col];
              end
            end
            2: begin
              if(!WEIGHTS || row>=GROUPS || col!=b) $fatal(1,"AWQ_ZERO_ADDRESS");
              data=zeros[row*BANKS+col];
            end
            3: begin
              if(!WEIGHTS || row>=GROUPS || col<8*b || col>=8*b+8)
                $fatal(1,"AWQ_SCALE_ADDRESS");
              data={16'd0,scales[row*BANKS*8+col]};
            end
            4: begin
              if(PROJECTION!=0 || row!=0 || col<8*b || col>=8*b+8)
                $fatal(1,"NATIVE_BIAS_ADDRESS");
              data={16'd0,biases[col]};
            end
            default: $fatal(1,"NATIVE_ROW_BAD_MEMORY_KIND");
          endcase
          if(!qw[b]) reads=reads+1;
          response[b]=data; pending[b]=1; pending_write[b]=qw[b]; due[b]=cycle+3+b;
          $fdisplay(32'h80000001,"ROW_TRANSACTION %0d %0d %0d %0d %0d %0d %08h",
            cycle,b,qw[b],kind,row,col,qw[b] ? qd[b*32+:32] : data);
        end
      end
    end
  end
endmodule
"""


def execute(fmt, weights, banks, projection, seed):
    run = Run(f"verifier-native-row-{fmt}-w{weights}-b{banks}-p{projection}-s{seed}")
    try:
        run.command(["iverilog", "-V"], "iverilog-version")
        run.command(["vvp", "-V"], "vvp-version")
        inputs, outputs = (1536 if projection == 0 else 8960), banks * 8
        groups = inputs // 128
        activations = [rounded(Fraction((seed + 11 * col) % 41 - 20, 37)) for col in range(inputs)]
        native, packed, zeros, scales = [], [], [], []
        sums = [0] * outputs
        biases = [rounded(Fraction((seed + row) % 9 - 4, 256), fmt) for row in range(outputs)]
        for group in range(groups):
            for bank in range(banks):
                zeros.append(sum((3 + (seed + 3 * group + 5 * (8 * bank + j)) % 9) << SHIFTS[j]
                                 for j in range(8)))
            scales.extend(rounded(Fraction(1, 128 << ((seed + group + row) % 2)), fmt)
                          for row in range(outputs))
        for col, activation in enumerate(activations):
            qwords = [0] * banks
            a = convert(convert(activation, "fp32", fmt), fmt)
            group = col // 128
            for row in range(outputs):
                delta = (seed + 13 * col + 17 * row) % 7 - 3
                effective = rounded(Fraction(delta, 128 << ((seed + group + row) % 2)), fmt)
                native.append(effective)
                zero = 3 + (seed + 3 * group + 5 * row) % 9
                qwords[row // 8] |= (zero + delta) << SHIFTS[row % 8]
                sums[row] = add(sums[row], multiply(a, convert(effective, fmt)))
            packed.extend(qwords)
        if projection == 0:
            sums = [add(total, convert(bias, fmt)) for total, bias in zip(sums, biases)]
        artifacts = {}
        for label, values, width in (
            ("ACTIVATIONS", activations, 8), ("WEIGHTS", native, 4), ("PACKED", packed, 8),
            ("ZEROS", zeros, 8), ("SCALES", scales, 4), ("BIASES", biases, 4),
            ("EXPECTED", sums, 8),
        ):
            path = run.path / f"{label.lower()}.hex"
            path.write_text("".join(f"{v:0{width}x}\n" for v in values))
            artifacts[label] = path
        manifest = run.path / "manifest.json"
        manifest.write_text(json.dumps({
            "format": fmt, "weights": weights, "banks": banks, "projection": projection, "seed": seed,
            "geometry": "unmodified native Qwen parameters", "inputs": inputs,
            "compared_rows": list(range(outputs)), "operation_order": "ascending input column",
            "scope": "First eight rows per bank, then explicit reset of the unfinished projection.",
            "native_full_projection_or_token_throughput": False,
        }, indent=2) + "\n")
        bench = run.path / "bench.sv"
        bench.write_text(with_time_zero_check(BENCH))
        run.receipt["generated_sha256"] = {
            run.relative(p): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in [*artifacts.values(), manifest, bench]}
        parameters = dict(BANKS=banks, FORMAT=int(fmt == "fp16"), WEIGHTS=weights,
                          PROJECTION=projection, INPUTS=inputs, GROUPS=groups)
        binary = compile_model(run, bench, sorted((ROOT / "rtl").glob("*.sv")), parameters)
        arguments = [f"+FIXTURES={run.relative(run.path)}"]
        startup_check(run, binary, arguments)
        def compare_rows(lines):
            summaries, seen = [], set()
            reads = 0
            for line in lines:
                parts = line.split()
                if parts and parts[0] == "ROW_TRANSACTION":
                    _, cycle, bank, write, kind, row, col, data = parts
                    cycle, bank, write, kind, row, col = map(
                        int, (cycle, bank, write, kind, row, col))
                    data = int(data, 16)
                    assert 0 <= bank < banks and cycle > 0 and write in (0, 1)
                    if write:
                        assert kind == 8 and row == (2 if projection == 0 else 12)
                        assert 8 * bank <= col < 8 * bank + 8 and col not in seen
                        assert data == sums[col], (
                            f"NATIVE_PROJECTION_ROW_MISMATCH row={col} "
                            f"got={data:08x} expected={sums[col]:08x}")
                        seen.add(col)
                    else:
                        if kind == 8:
                            assert row == (1 if projection == 0 else 11) and 0 <= col < inputs
                            expected = activations[col]
                        elif kind == 1:
                            assert 0 <= row < inputs
                            if weights:
                                assert col == bank
                                expected = packed[row * banks + col]
                            else:
                                assert 8 * bank <= col < 8 * bank + 8
                                expected = native[row * outputs + col]
                        elif kind == 2:
                            assert weights and 0 <= row < groups and col == bank
                            expected = zeros[row * banks + col]
                        elif kind == 3:
                            assert weights and 0 <= row < groups and 8 * bank <= col < 8 * bank + 8
                            expected = scales[row * outputs + col]
                        else:
                            assert kind == 4 and projection == 0 and row == 0
                            assert 8 * bank <= col < 8 * bank + 8
                            expected = biases[col]
                        assert data == expected, (
                            f"NATIVE_ROW_READ_MISMATCH kind={kind} row={row} col={col} "
                            f"got={data:08x} expected={expected:08x}")
                        reads += 1
                elif parts and parts[0] == "NATIVE_ROW_GROUP_COMPARED":
                    summaries.append(parts[1:])
            assert seen == set(range(outputs)), "missing independent row comparisons"
            assert len(summaries) == 1 and int(summaries[0][2]) == reads
            return summaries
        summaries = stream_model(
            run, [run.relative(binary), *arguments], compare_rows,
            ("ROW_TRANSACTION ",), ("ROW_TRANSACTION ", "NATIVE_ROW_GROUP_COMPARED "))
        assert len(summaries) == 1
        metrics = dict(zip(("input_columns", "output_rows", "reads", "acknowledgements",
                            "partial_projection_cycles", "rows_compared"), map(int, summaries[0])))
        assert metrics["input_columns"] == inputs and metrics["rows_compared"] == outputs
        assert metrics["acknowledgements"] == metrics["reads"] + outputs
        run.finish("passed-focused-only", metrics=metrics,
                   limitations="Measured first row group only; full native hardware benchmark remains required.")
        return 0
    except (AssertionError, ArithmeticError, RuntimeError, OSError, ValueError) as exc:
        run.finish("failed", failure=f"{type(exc).__name__}: {exc}")
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("bf16", "fp16"), default="bf16")
    parser.add_argument("--weights", type=int, choices=(0, 1), default=0)
    parser.add_argument("--banks", type=int, choices=(1, 2, 4), default=4)
    parser.add_argument("--projection", type=int, choices=(0, 6), default=0)
    parser.add_argument("--seed", type=int, choices=(17, 43, 89), default=17)
    args = parser.parse_args()
    raise SystemExit(execute(args.format, args.weights, args.banks, args.projection, args.seed))
