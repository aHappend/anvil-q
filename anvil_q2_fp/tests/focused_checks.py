"""Public-pin reduced token regression; diagnostic, not full L1 acceptance.

Reproduce with: python3 tests/focused_checks.py --format bf16
One layer, GQA 6:1, H=48, I=48, D=8, one token and one vocabulary row.
An impulse embedding and zero decoder matrices leave the residual unchanged.
Unit norm weights make the final norm independently calculable. The tied
embedding/output row selects its first component after mandatory A16 rounding.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fp_reference import rounded, unit_impulse_norm, value
from retained import ROOT, Run, require_time_zero, with_time_zero_check


TOKEN_BENCH = r"""
module tb;
  parameter FORMAT=0;
  reg clk=0;
  reg rst_n;
  always #5 clk=~clk;
  reg token_valid=0;
  wire token_ready, logit_valid, done, error, cancel_done;
  wire [31:0] logit_index, logit_data;
  wire req_valid, req_write, rsp_ready;
  wire [3:0] req_kind;
  wire [2:0] req_proj;
  wire [31:0] req_layer, req_row, req_col, req_data;
  wire [63:0] req_tag;
  reg rsp_valid=0;
  reg [31:0] rsp_data=0;
  reg [63:0] rsp_tag=0;
  reg [31:0] scratch[0:719];
  reg scratch_valid[0:719];
  reg [31:0] cache[0:7];
  reg cache_valid[0:7];
  integer i, cycles=0, requests=0, responses=0, logits=0, accepts=0;
  reg previous_stall=0;
  reg [31:0] previous_logit;
  wire [15:0] one16=FORMAT==0 ? 16'h3f80 : 16'h3c00;
  anvil_q2_fp_top #(
    .NUM_LAYERS(1),.HIDDEN_SIZE(48),.INTERMEDIATE_SIZE(48),
    .NUM_Q_HEADS(6),.NUM_KV_HEADS(1),.HEAD_DIM(8),.GROUP_SIZE(8),
    .VOCAB_SIZE(1),.MAX_SEQ_LEN(1),.BANKS(1),.CACHE_BLOCK(8),
    .CACHE_MODE(0),.FP_FORMAT(FORMAT),.WEIGHT_MODE(0)
  ) dut (
    .clk(clk),.rst_n(rst_n),.cancel(1'b0),
    .token_valid(token_valid),.token_ready(token_ready),
    .token_id(32'd0),.token_pos(32'd0),.new_sequence(1'b1),.token_phase(1'b0),
    .logit_valid(logit_valid),.logit_ready(1'b1),
    .logit_index(logit_index),.logit_data(logit_data),
    .done(done),.error(error),.cancel_done(cancel_done),
    .mem_req_valid(req_valid),.mem_req_ready(!rsp_valid),
    .mem_req_write(req_write),.mem_req_kind(req_kind),.mem_req_layer(req_layer),
    .mem_req_proj(req_proj),.mem_req_row(req_row),.mem_req_col(req_col),
    .mem_req_wdata(req_data),.mem_req_tag(req_tag),
    .mem_rsp_valid(rsp_valid),.mem_rsp_error(1'b0),
    .mem_rsp_ready(rsp_ready),.mem_rsp_rdata(rsp_data),.mem_rsp_tag(rsp_tag)
  );
  initial begin
    rst_n=0;
    for(i=0;i<720;i=i+1) begin scratch[i]=0; scratch_valid[i]=0; end
    for(i=0;i<8;i=i+1) begin cache[i]=0; cache_valid[i]=0; end
    #1;
    if ({token_ready,logit_valid,logit_index,logit_data,done,error,cancel_done,
         req_valid,req_write,req_kind,req_layer,req_proj,req_row,req_col,
         req_data,req_tag,rsp_ready} !== 0) $fatal(1,"RESET_X_OR_NONZERO");
    repeat(2) @(negedge clk);
    rst_n=1;
    @(negedge clk);
    token_valid=1;
    do @(posedge clk); while (!token_ready);
    @(negedge clk);
    token_valid=0;
  end
  always @(posedge clk or negedge clk) begin
    if (!rst_n && $time>0 &&
        {token_ready,logit_valid,logit_index,logit_data,done,error,cancel_done,
         req_valid,req_write,req_kind,req_layer,req_proj,req_row,req_col,
         req_data,req_tag,rsp_ready} !== 0) $fatal(1,"RESET_EDGE_X_OR_NONZERO");
  end
  always @(posedge clk) begin
    cycles<=cycles+1;
    if (rst_n) begin
      if ((^{token_ready,logit_valid,done,error,cancel_done,req_valid,rsp_ready}) === 1'bx)
        $fatal(1,"ACTIVE_CONTROL_X");
      if (token_valid && token_ready) accepts<=accepts+1;
      if (rsp_valid && rsp_ready) begin
        $display("RSP %0d %016h",cycles,rsp_tag);
        rsp_valid<=0;
        responses<=responses+1;
      end
      if (req_valid && !rsp_valid) begin
        if ((^{req_write,req_kind,req_layer,req_proj,req_row,req_col,req_data,req_tag})
            === 1'bx) $fatal(1,"ACTIVE_REQUEST_X");
        $display("REQ %0d %0d %0d %0d %0d %0d %0d %08h %016h",
                 cycles,req_write,req_kind,req_layer,req_proj,req_row,req_col,
                 req_data,req_tag);
        requests<=requests+1;
        rsp_valid<=1;
        rsp_tag<=req_tag;
        rsp_data<=0;
        case(req_kind)
          0: begin
            if(req_write || req_layer!=0 || req_proj!=0 || req_row!=0 || req_col>=48)
              $fatal(1,"BAD_MODEL_COORDINATE");
            rsp_data<=req_col==0 ? {16'd0,one16} : 0;
          end
          1,4: begin
            if(req_write || req_layer!=0 || req_proj>6 || req_row>=48 || req_col>=48)
              $fatal(1,"BAD_PROJECTION_COORDINATE");
          end
          5,6,7: begin
            if(req_write || req_layer!=0 || req_proj!=0 || req_row!=0 || req_col>=48)
              $fatal(1,"BAD_NORM_COORDINATE");
            rsp_data<={16'd0,one16};
          end
          8: begin
            if(req_layer!=0 || req_proj!=0 || req_row>=15 || req_col>=48)
              $fatal(1,"BAD_SCRATCH_COORDINATE");
            if(req_write) begin
              scratch[req_row*48+req_col]<=req_data;
              scratch_valid[req_row*48+req_col]<=1;
            end else begin
              if(!scratch_valid[req_row*48+req_col]) $fatal(1,"STALE_SCRATCH_READ");
              rsp_data<=scratch[req_row*48+req_col];
            end
          end
          9,10: begin
            if(req_layer!=0 || req_proj!=0 || req_row!=0 || req_col>=4)
              $fatal(1,"BAD_CACHE_COORDINATE");
            if(req_write) begin
              cache[(req_kind-9)*4+req_col]<=req_data;
              cache_valid[(req_kind-9)*4+req_col]<=1;
            end else begin
              if(!cache_valid[(req_kind-9)*4+req_col]) $fatal(1,"STALE_CACHE_READ");
              rsp_data<=cache[(req_kind-9)*4+req_col];
            end
          end
          11: begin
            if(req_write || req_layer!=0 || req_proj!=0 || req_row!=0 || req_col>=8)
              $fatal(1,"BAD_ROPE_COORDINATE");
            rsp_data<=req_col[0] ? 0 : 32'h3f800000;
          end
          default: $fatal(1,"UNEXPECTED_MEMORY_KIND");
        endcase
      end
      if(logit_valid) begin
        if ((^{logit_index,logit_data}) === 1'bx) $fatal(1,"LOGIT_X");
        $display("LOGIT %0d %0d %08h",cycles,logit_index,logit_data);
        logits<=logits+1;
      end
      if(done) begin
        $display("DONE %0d %0d %0d %0d %0d %0d",
                 cycles,error,accepts,logits,requests,responses);
        if(error || accepts!=1 || logits!=1 || requests!=responses || rsp_valid)
          $fatal(1,"TOKEN_COMPLETION_ACCOUNTING");
        $finish;
      end
    end
  end
endmodule
"""


def check_trace(path, fmt):
    norm = unit_impulse_norm(48)
    expected = rounded(value(rounded(value(norm), fmt), fmt))
    requests, responses, logits, completion = [], [], [], []
    scratch_writes = 0
    for line in path.read_text().splitlines():
        parts = line.split()
        if not parts:
            continue
        if parts[0] == "REQ":
            _, cycle, wr, kind, layer, proj, row, col, data, tag = parts
            wr, kind, row, col = map(int, (wr, kind, row, col))
            requests.append(int(tag, 16))
            if wr and kind == 8:
                scratch_writes += 1
                want = norm if row in (1, 8, 14) and col == 0 else (
                    0x3F800000 if row in (0, 7) and col == 0 else 0)
                assert int(data, 16) == want, (
                    f"scratch slot={row} col={col}: {data} != {want:08x}")
        elif parts[0] == "RSP":
            responses.append(int(parts[2], 16))
        elif parts[0] == "LOGIT":
            logits.append((int(parts[2]), int(parts[3], 16)))
        elif parts[0] == "DONE":
            completion.append(parts[1:])
    assert len(requests) > 0 and scratch_writes > 0, "empty comparisons"
    assert len(set(requests)) == len(requests), "duplicate request tags"
    assert requests == sorted(requests), "nonmonotonic allocation"
    assert responses == requests, "missing/duplicate/reassociated responses"
    assert len(completion) == 1, "missing or duplicate completion"
    assert len(logits) == 1, f"expected one logit, got {logits}"
    assert logits == [(0, expected)], (
        f"OUTPUT_A16_BOUNDARY: observed={logits[0][1]:08x}, expected={expected:08x}, "
        f"unrounded_final_norm={norm:08x}, format={fmt}")
    return {"requests_compared": len(requests), "scratch_writes_compared": scratch_writes,
            "expected_logit": f"{expected:08x}", "final_norm": f"{norm:08x}"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("bf16", "fp16"), default="bf16")
    args = parser.parse_args()
    run = Run(f"verifier-output-a16-{args.format}")
    try:
        run.command(["iverilog", "-V"], "iverilog-version")
        run.command(["vvp", "-V"], "vvp-version")
        bench = run.path / "token.sv"
        bench.write_text(with_time_zero_check(TOKEN_BENCH))
        run.receipt["generated_sha256"] = {}
        import hashlib
        run.receipt["generated_sha256"][run.relative(bench)] = (
            hashlib.sha256(bench.read_bytes()).hexdigest())
        binary = run.path / "token.vvp"
        run.command(["iverilog", "-g2012", "-Wall", "-s", "tb",
                     f"-Ptb.FORMAT={int(args.format == 'fp16')}", "-o", run.relative(binary),
                     *[str(p.relative_to(ROOT)) for p in sorted((ROOT / "rtl").glob("*.sv"))],
                     run.relative(bench)], "compile")
        trace = run.command(["vvp", run.relative(binary)], "simulation")
        require_time_zero(trace)
        metrics = check_trace(trace, args.format)
        run.finish("passed-focused-only", metrics=metrics)
        return 0
    except (AssertionError, RuntimeError, OSError, ValueError) as exc:
        run.finish("failed", failure=f"{type(exc).__name__}: {exc}")
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
