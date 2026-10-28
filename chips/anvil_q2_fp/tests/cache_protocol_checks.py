"""Independent cache transaction, commit, corruption and invalidation campaign.

Only public cache pins are observed. Expected packed words and decoded values
come from exact rational IEEE/quantization models, never DUT hierarchy.
"""

import argparse
import hashlib
import json
import sys
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from codec_checks import codec_reference
from fp_reference import convert, rounded
from retained import ROOT, Run, require_time_zero, with_time_zero_check


BENCH = r"""
module tb;
  parameter FORMAT=0,MODE=0,BLOCK=2,COMMANDS=1,TRANSACTIONS=1;
  reg clk=0,rst_n,invalidate=0,cmd_valid=0;
  always #5 clk=~clk;
  reg [1:0] op=0;
  reg [31:0] layer=0,pos=0,head=0,dim=0;
  reg phase=0;
  wire ready,done,error;
  wire [31:0] result;
  wire mv,mw,mrr;
  reg mr=0,mrv=0,mre=0;
  wire [3:0] mk;
  wire [2:0] mp;
  wire [31:0] ml,mrow,mcol,md;
  reg [31:0] mrd=0;
  reg [199:0] commands[0:COMMANDS-1];
  reg [166:0] transactions[0:TRANSACTIONS-1];
  reg [199:0] command;
  reg [166:0] transaction;
  integer c,t=0,cycle=0,accepted=0,compared=0,acks=0,errors=0,aborts=0;
  integer first_t,expected_count,due=0,stall_count=0,ack_stalls=0;
  reg pending=0,abort_pending=0,held=0;
  reg [135:0] payload=0;
  anvil_q2_fp_kv_cache #(
    .NUM_LAYERS(2),.NUM_KV_HEADS(2),.HEAD_DIM(16),.MAX_SEQ_LEN(3),
    .CACHE_MODE(MODE),.CACHE_BLOCK(BLOCK),.FP_FORMAT(FORMAT)
  ) dut(clk,rst_n,invalidate,cmd_valid,ready,op,layer,pos,head,dim,phase,
    done,error,result,mv,mr,mw,mk,ml,mp,mrow,mcol,md,mrv,mrr,mrd,mre);
  initial begin
    rst_n=0;
    $readmemh("__COMMANDS__",commands);
    $readmemh("__TRANSACTIONS__",transactions);
    #1;
    if({ready,done,error,result,mv,mw,mk,ml,mp,mrow,mcol,md,mrr} !== 0)
      $fatal(1,"RESET_NONZERO_X");
    repeat(2) @(negedge clk); rst_n=1;
    for(c=0;c<COMMANDS;c=c+1) begin
      command=commands[c];
      if(command[199]) begin
        @(negedge clk); invalidate=1;
        repeat(2) @(negedge clk);
        invalidate=0;
        do @(posedge clk); while(!ready);
        if(pending || mrv) $fatal(1,"INVALIDATION_NOT_DRAINED");
        $display("INVALIDATE %0d",c);
      end else begin
        first_t=t;
        expected_count=command[196:181];
        @(negedge clk);
        {op,layer,pos,head,dim,phase}=command[130:0];
        cmd_valid=1;
        do @(posedge clk); while(!ready);
        accepted=accepted+1;
        $display("COMMAND %0d %0d",c,cycle);
        @(negedge clk); cmd_valid=0;
        if(command[198]) begin
          do @(negedge clk); while(!abort_pending);
          invalidate=1;
          @(negedge clk); invalidate=0; abort_pending=0;
          do @(posedge clk); while(!ready);
          if(done || pending || mrv) $fatal(1,"ABORT_NOT_DRAINED");
          aborts=aborts+1;
        end else begin
          do @(posedge clk); while(!done);
          if(error !== command[197] ||
             (!command[197] && result !== command[180:149] && op!=0))
            $fatal(1,"CACHE_RESULT_MISMATCH case=%0d op=%0d got=%08h error=%b expected=%08h error=%b",
              c,op,result,error,command[180:149],command[197]);
          if(pending || mrv) $fatal(1,"PREMATURE_CACHE_COMMIT");
          if(error) errors=errors+1;
          compared=compared+1;
          $display("COMPARED %0d %0d %08h %0d",c,cycle,result,error);
        end
        if(t-first_t!=expected_count)
          $fatal(1,"MISSING_CACHE_TRANSACTIONS case=%0d got=%0d expected=%0d",
                 c,t-first_t,expected_count);
        @(negedge clk);
      end
    end
    if(t!=TRANSACTIONS || pending || mrv || accepted!=compared+aborts ||
       errors==0 || aborts==0 || stall_count==0 || ack_stalls==0)
      $fatal(1,"CACHE_ACCOUNTING_OR_COVERAGE");
    $display("CACHE_PROTOCOL_COMPARED %0d %0d %0d %0d %0d %0d %0d",
             accepted,compared,aborts,t,acks,stall_count,ack_stalls);
    $finish;
  end
  always @(negedge clk) if(rst_n) begin
    mr=!pending && cycle%7>1;
    if(pending && cycle>=due && !mrv) mrv=1;
  end
  always @(posedge clk or negedge clk)
    if(!rst_n && $time>0 && {ready,done,error,result,mv,mw,mk,ml,mp,mrow,mcol,md,mrr} !== 0)
      $fatal(1,"RESET_EDGE_NONZERO_X");
  always @(posedge clk) begin
    cycle<=cycle+1;
    if(rst_n) begin
      if((^{ready,done,error,mv,mrr}) === 1'bx) $fatal(1,"CACHE_CONTROL_X");
      if(pending && ready) $fatal(1,"CACHE_READY_BEFORE_ACK");
      if(held && (mv !== 1'b1 || {mw,mk,ml,mp,mrow,mcol,md} !== payload))
        $fatal(1,"CACHE_REQUEST_INSTABILITY");
      held<=mv && !mr;
      payload<={mw,mk,ml,mp,mrow,mcol,md};
      if(mv && !mr) stall_count=stall_count+1;
      if(pending && !mrv) ack_stalls=ack_stalls+1;
      if(mrv && mrr) begin mrv<=0; pending=0; acks=acks+1; end
      if(mv && mr) begin
        if(t>=TRANSACTIONS) $fatal(1,"EXTRA_CACHE_REQUEST");
        transaction=transactions[t];
        if({mw,mk,ml,mp,mrow,mcol} !== transaction[166:63] ||
           (mw && md !== transaction[62:31]))
          $fatal(1,"CACHE_TRANSACTION_MISMATCH case=%0d transaction=%0d got=%b/%0d/%0d/%0d/%0d/%0d/%08h expected=%042h",
            c,t,mw,mk,ml,mp,mrow,mcol,md,transaction);
        mrd=transaction[62:31]; mre=transaction[30];
        pending=1; due=cycle+7;
        if(command[198] && t-first_t+1==command[196:181]) abort_pending=1;
        $display("TRANSACTION %0d %0d %b %0d %0d %0d %0d %08h %b",
          c,t,mw,mk,ml,mrow,mcol,md,mre);
        t=t+1;
      end
    end
  end
endmodule
"""


class Campaign:
    def __init__(self, fmt, mode, block, seed):
        self.fmt, self.mode, self.block, self.seed = fmt, mode, block, seed
        self.commands, self.transactions, self.labels = [], [], []
        self.memory, self.decoded = {}, {}

    def transaction(self, write, kind, layer, row, col, data, error=0):
        # write/kind/layer/proj/row/col, response-or-write data, response error.
        address = (kind << 99) | (layer << 67) | (row << 32) | col
        self.transactions.append((int(write) << 166) | (address << 63) |
                                 (data << 31) | (error << 30))

    def command(self, label, op=0, layer=0, pos=0, head=0, dim=0, phase=0,
                error=0, result=0, start=None, abort=False, invalidate=False):
        count = len(self.transactions) - start if start is not None else 0
        # Input fields and expected output deliberately occupy disjoint bits.
        inputs = (op << 129) | (layer << 97) | (pos << 65) | (head << 33) | (dim << 1) | phase
        self.commands.append((int(invalidate) << 199) | (int(abort) << 198) |
                             (error << 197) | (count << 181) | (result << 149) | inputs)
        self.labels.append(label)

    def invalidate(self):
        self.command("repeated sequence invalidation", invalidate=True)
        self.memory.clear()
        self.decoded.clear()

    def commit(self, layer=0, pos=0, phase=0, fault_at=None, abort_at=None):
        start = len(self.transactions)
        writes = []
        for is_value in (0, 1):
            selected = []
            scratch = []
            for i in range(32):
                # Zero, alternating sign, outlier and non-power-of-two rationals.
                x = (Fraction(7, 4) if i == 15 else
                     Fraction(((i * 13 + self.seed + pos * 3 + layer) % 33) - 16, 97))
                if (i + pos) % 11 == 0:
                    x = Fraction(0)
                x += Fraction(is_value, 128)
                scratch.append(rounded(x))
                selected.append(convert(scratch[-1], "fp32", self.fmt))
            rebuilt = []
            step = 2 if self.mode == 0 else self.block
            for i in range(0, 32, step):
                for j in range(step):
                    self.transaction(False, 8, 0, 3 + is_value, i + j, scratch[i + j])
                if self.mode == 0:
                    data = selected[i] | (selected[i + 1] << 16)
                    writes.append((9 + is_value, layer, pos, i // 2, data))
                    self.transaction(True, *writes[-1])
                    rebuilt.extend(selected[i:i + 2])
                else:
                    r, q, exponent, failed = codec_reference(
                        selected[i:i + step], [0] * step, 0, False, self.fmt)
                    assert not failed
                    words = (step + 3) // 4
                    for word in range(words):
                        data = sum(b << (8 * j) for j, b in enumerate(q[4 * word:4 * word + 4]))
                        writes.append((12 + is_value, layer, pos, i // step * words + word, data))
                        self.transaction(True, *writes[-1])
                    writes.append((14 + is_value, layer, pos, i // step, exponent & 0xFFFFFFFF))
                    self.transaction(True, *writes[-1])
                    rebuilt.extend(r)
            self.decoded[layer, pos, is_value] = rebuilt
        if fault_at is not None or abort_at is not None:
            count = len(self.transactions) - start
            index = count - 1 if (fault_at if fault_at is not None else abort_at) == -1 else (
                fault_at if fault_at is not None else abort_at)
            self.transactions = self.transactions[:start + index + 1]
            if fault_at is not None:
                self.transactions[-1] |= 1 << 30
            self.memory.clear()
            self.decoded.clear()
        else:
            for kind, l, p, col, data in writes:
                self.memory[kind, l, p, col] = data
        self.command("commit" if fault_at is None and abort_at is None else
                     "failed/aborted partial commit", layer=layer, pos=pos, phase=phase,
                     error=int(fault_at is not None), abort=abort_at is not None, start=start)

    def read(self, layer=0, pos=0, head=0, dim=0, is_value=0, error=False,
             corruption=None):
        start = len(self.transactions)
        result = 0
        if not error:
            index = head * 16 + dim
            if self.mode == 0:
                kind, col = 9 + is_value, index // 2
                data = self.memory[kind, layer, pos, col]
                if corruption is not None:
                    data = corruption
                    error = True
                self.transaction(False, kind, layer, pos, col, data)
            else:
                block_index = index // self.block
                exponent = self.memory[14 + is_value, layer, pos, block_index]
                if corruption == "metadata":
                    exponent = 0x0000FFFF
                    error = True
                self.transaction(False, 14 + is_value, layer, pos, block_index, exponent)
                if corruption != "metadata":
                    words = (self.block + 3) // 4
                    for word in range(words):
                        col = block_index * words + word
                        data = self.memory[12 + is_value, layer, pos, col]
                        if corruption == "reserved" and word == 0:
                            data = (data & ~255) | 128
                            error = True
                        elif corruption == "padding" and word == 0:
                            data |= 1 << 24
                            error = True
                        self.transaction(False, 12 + is_value, layer, pos, col, data)
                        if corruption == "padding":
                            break
            if not error:
                result = convert(self.decoded[layer, pos, is_value][index], self.fmt)
        self.command("read corruption" if corruption is not None else
                     "read causal/geometry rejection" if error else "read exact reconstruction",
                     1 + is_value, layer, pos, head, dim, error=int(error),
                     result=result, start=start)

    def generate(self):
        self.read(error=True)
        self.command("nonsequential commit rejected", pos=1, error=1)
        self.commit()
        for v in (0, 1):
            for h in (0, 1):
                for d in range(16):
                    self.read(head=h, dim=d, is_value=v)
        self.read(pos=1, error=True)
        self.read(head=2, error=True)
        self.read(dim=16, error=True)
        self.read(layer=2, error=True)
        if self.mode:
            for corruption in ("metadata", "reserved"):
                self.read(corruption=corruption)
            if self.block < 4:
                self.read(corruption="padding")
        else:
            self.read(corruption=0x7F807F80 if self.fmt == "bf16" else 0x7C007C00)
        self.commit(layer=1)
        self.read(layer=1, head=1, dim=15, is_value=1)
        self.commit(pos=1, phase=1)
        self.read(pos=1, head=1, dim=15, is_value=1)
        self.command("prefill after decode rejected", pos=2, phase=0, error=1)
        self.read(error=True)
        self.read(layer=1, head=1, dim=15, is_value=1)
        for fault in (0, 3, -1):
            self.invalidate()
            self.commit()
            self.commit(pos=1, fault_at=fault)
            self.read(error=True)
            self.read(pos=1, error=True)
        for abort in (0, 3, -1):
            self.invalidate()
            self.commit(abort_at=abort)
            self.read(error=True)
            self.commit()
            self.read(head=1, dim=15, is_value=1)
        self.invalidate()
        self.invalidate()
        self.read(error=True)
        self.commit()
        self.read(head=1, dim=15, is_value=1)
        return self


def execute(fmt, mode, block, seed=17):
    run = Run(f"verifier-cache-protocol-{fmt}-c{mode}-block{block}-s{seed}")
    try:
        run.command(["iverilog", "-V"], "iverilog-version")
        run.command(["vvp", "-V"], "vvp-version")
        campaign = Campaign(fmt, mode, block, seed).generate()
        commands, transactions = run.path / "commands.hex", run.path / "transactions.hex"
        commands.write_text("".join(f"{v:050x}\n" for v in campaign.commands))
        transactions.write_text("".join(f"{v:042x}\n" for v in campaign.transactions))
        manifest = run.path / "manifest.json"
        manifest.write_text(json.dumps({
            "format": fmt, "cache_mode": mode, "block": block, "seed": seed,
            "geometry": {"layers": 2, "kv_heads": 2, "head_dim": 16, "positions": 3},
            "scenarios": campaign.labels,
            "expected_transactions": len(campaign.transactions),
        }, indent=2) + "\n")
        bench = run.path / "bench.sv"
        text = BENCH.replace("__COMMANDS__", run.relative(commands)).replace(
            "__TRANSACTIONS__", run.relative(transactions))
        bench.write_text(with_time_zero_check(text))
        run.receipt["generated_sha256"] = {
            run.relative(p): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (commands, transactions, manifest, bench)}
        binary = run.path / "bench.vvp"
        parameters = dict(FORMAT=int(fmt == "fp16"), MODE=mode, BLOCK=block,
                          COMMANDS=len(campaign.commands), TRANSACTIONS=len(campaign.transactions))
        run.command(["iverilog", "-g2012", "-Wall", "-s", "tb",
                     *[f"-Ptb.{k}={v}" for k, v in parameters.items()], "-o", run.relative(binary),
                     *[str(p.relative_to(ROOT)) for p in sorted((ROOT / "rtl").glob("*.sv"))],
                     run.relative(bench)], "compile")
        trace = run.command(["vvp", run.relative(binary)], "simulation")
        require_time_zero(trace)
        summaries = [line.split()[1:] for line in trace.read_text().splitlines()
                     if line.startswith("CACHE_PROTOCOL_COMPARED ")]
        assert len(summaries) == 1, "cache campaign did not reach checked completion"
        metrics = dict(zip(("commands", "results", "aborts", "transactions", "acknowledgements",
                            "request_stalls", "acknowledgement_delay_cycles"),
                           map(int, summaries[0])))
        assert metrics["transactions"] == metrics["acknowledgements"] == len(campaign.transactions)
        assert metrics["commands"] == metrics["results"] + metrics["aborts"]
        run.finish("passed-focused-only", metrics=metrics)
        return 0
    except (AssertionError, ArithmeticError, RuntimeError, OSError, ValueError) as exc:
        run.finish("failed", failure=f"{type(exc).__name__}: {exc}")
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("bf16", "fp16"), default="bf16")
    parser.add_argument("--cache", type=int, choices=(0, 1), default=1)
    parser.add_argument("--block", type=int, choices=(1, 2, 16), default=2)
    parser.add_argument("--seed", type=int, choices=(17, 43, 89), default=17)
    args = parser.parse_args()
    raise SystemExit(execute(args.format, args.cache, args.block, args.seed))
