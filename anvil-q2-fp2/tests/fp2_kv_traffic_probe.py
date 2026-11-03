"""Executed nonbroadcast six-query DDR-beat reference for the zero-KV benchmark."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fp2_probe import ROOT, simulate
from fp2_attention_probe import ATTENTION_TB


BRIDGE = r"""
  reg reference_req_valid=0,reference_req_ready=0,reference_rsp_valid=0;
  reg [3:0] reference_req_kind=0;
  reg [31:0] reference_req_row=0,reference_req_col=0;
  reg [511:0] reference_rsp_data=0,reference_memory_data=0,reference_beat=0;
  reg [31:0] reference_random=17;
  integer reference_reads=0,reference_payload=0,reference_scales=0;
  integer reference_delay,reference_kind,reference_part,reference_element;
  reg reference_accepted;
  task automatic reference_read(input [3:0] kind,input [31:0] row,column,
                                input [511:0] memory_data,output [511:0] result);
    begin
      reference_req_valid=1; reference_req_kind=kind;
      reference_req_row=row; reference_req_col=column;
      reference_memory_data=memory_data; reference_accepted=0;
      while(!reference_accepted) begin
        reference_random=reference_random^(reference_random<<13);
        reference_random=reference_random^(reference_random>>17);
        reference_random=reference_random^(reference_random<<5);
        reference_req_ready=reference_random[2:0]!=0;
        @(posedge clk);
        reference_accepted=reference_req_valid && reference_req_ready;
        if(reference_accepted) begin
          reference_reads=reference_reads+1;
          if(reference_req_kind==14 || reference_req_kind==15)
            reference_scales=reference_scales+1;
          else reference_payload=reference_payload+1;
        end
        @(negedge clk);
      end
      reference_req_valid=0; reference_req_ready=0;
      reference_delay=2+reference_random[9:6];
      repeat(reference_delay) @(negedge clk);
      reference_rsp_valid=1; reference_rsp_data=reference_memory_data;
      @(posedge clk);
      if(reference_rsp_valid !== 1'b1 || (^reference_rsp_data) === 1'bx)
        $fatal(1,"REFERENCE_MEMORY_RESPONSE");
      result=reference_rsp_data;
      @(negedge clk); reference_rsp_valid=0;
    end
  endtask
"""


def testbench():
    text = ATTENTION_TB.replace("@DIM@", "8").replace("@TILE@", "3")
    text = text.replace("module tb;", "module tb;" + BRIDGE, 1)
    text = text.replace("    rst_n=0;", """
    if(!$value$plusargs("SEED=%d",reference_random)) $fatal(1,"missing SEED");
    rst_n=0;""", 1)
    needle = """          kv_key=read_key; kv_value=read_value;
          kv_scale_key=read_ks; kv_scale_value=read_vs;"""
    if text.count(needle) != 1:
        raise ValueError("reference KV transactor anchor changed")
    replacement = r"""
          kv_key=0; kv_value=0; kv_scale_key=0; kv_scale_value=0;
          for(reference_kind=0;reference_kind<(format ? 4 : 2);reference_kind=reference_kind+1) begin
            reference_memory_data=0;
            if(reference_kind<2) begin
              if(format)
                reference_memory_data[D*8-1:0]=reference_kind==0 ? read_key[D*8-1:0] : read_value[D*8-1:0];
              else
                reference_memory_data[D*16-1:0]=reference_kind==0 ? read_key : read_value;
            end else
              reference_memory_data[G*8-1:0]=reference_kind==2 ? read_ks : read_vs;
            reference_read(format ? 12+reference_kind : 9+reference_kind,
                           index,0,reference_memory_data,reference_beat);
            case(reference_kind)
              0: kv_key=reference_beat[D*16-1:0];
              1: kv_value=reference_beat[D*16-1:0];
              2: kv_scale_key=reference_beat[G*8-1:0];
              3: kv_scale_value=reference_beat[G*8-1:0];
            endcase
          end"""
    text = text.replace(needle, replacement, 1)
    text = text.replace('    $display("SUMMARY %0d %0d",count,accepted_kv);', """
    $display("SUMMARY %0d %0d",count,accepted_kv);
    $display("REFERENCE_READS %0d %0d %0d",reference_reads,reference_payload,reference_scales);""", 1)
    return text


def run(probe, commands, mode, seed=17):
    source = probe.directory / "tb.sv"
    source.write_text(testbench())
    images = probe.directory / "checkpoint-images"
    images.mkdir()
    inputs = images / "six-query-reference.txt"
    with inputs.open("w") as stream:
        tag = 0
        for command in commands:
            for query in range(6):
                length = command[1] + 1
                stream.write(f"{tag} {length}\n" + "0\n" * 6)
                for position in range(length):
                    stream.write(f"{int(mode == 2)} 0 0 7f 7f\n")
                tag += 1
    sources = [ROOT / "rtl" / name for name in (
        "anvil_q2_fp2_arithmetic.sv", "anvil_q2_fp2_nonlinear.sv",
        "anvil_q2_fp2_coefficients.sv", "anvil_q2_fp2_mx_decode.sv",
        "anvil_q2_fp2_flash_attn.sv")]
    output = simulate(probe, source, sources, "verilator",
                      [f"+INPUT={inputs.relative_to(ROOT)}", f"+SEED={seed}"])
    results, summaries, accounting = set(), [], []
    for line in output.read_text().splitlines():
        words = line.split()
        if words[:1] == ["RESULT"]:
            tag, head, data, error = int(words[1]), int(words[2]), int(words[3], 16), int(words[4])
            if (tag, head) in results or not 0 <= tag < 6 * len(commands) or not 0 <= head < 6:
                raise AssertionError("duplicate/unexpected nonbroadcast result")
            results.add((tag, head))
            # Exactly zero V makes the independent weighted sum zero for any
            # finite normalized causal probability distribution.
            probe.compare("nonbroadcast-reference-zero-v", 0, data, {"tag": tag, "head": head})
            probe.compare("nonbroadcast-reference-error", 0, error, {"tag": tag, "head": head})
        elif words[:1] == ["SUMMARY"]:
            summaries.append(tuple(map(int, words[1:])))
        elif words[:1] == ["REFERENCE_READS"]:
            accounting.append(tuple(map(int, words[1:])))
    probe.compare("nonbroadcast-result-count", 36 * len(commands), len(results), {})
    probe.compare("nonbroadcast-command-and-kv-count",
                  [(6 * len(commands), 6 * sum(command[1] + 1 for command in commands))],
                  summaries, {})
    if len(accounting) != 1:
        raise AssertionError("missing executed nonbroadcast memory accounting")
    reads, payload, scales = accounting[0]
    probe.compare("reference-memory-conservation", reads, payload + scales, {})
    probe.compare("reference-real-reads", True, reads > 0, {})
    probe.compare("reference-scale-transfers", mode == 2, scales > 0, {})
    probe.summary["nonbroadcast_external_accounting"] = {
        "accepted_64byte_reads": reads, "kv_read_bytes": reads * 64,
        "payload_beats": payload, "scale_beats": scales,
        "query_replays": 6 * len(commands), "accepted_causal_kv": summaries[0][1],
        "fixture": "identical zero BF16/MX KV cache used by the matched compact benchmark",
        "memory_master": "deliberately nonbroadcast public beat-handshake reference bridge",
    }


def main():
    import argparse
    from fp2_probe import Probe, SuiteDeadline
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", type=int, choices=(0, 2), default=0)
    args = parser.parse_args()
    probe = Probe("six-query-read-reference")
    try:
        with SuiteDeadline():
            run(probe, ((3, 0, 1, 0),), args.mode)
        return probe.settle()
    except Exception as error:
        return probe.settle(f"{type(error).__name__}: {error}")


if __name__ == "__main__":
    raise SystemExit(main())
