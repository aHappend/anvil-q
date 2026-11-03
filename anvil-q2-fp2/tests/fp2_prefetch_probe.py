"""Ping-pong ownership, simultaneous transfer, malformed beats and flush oracle."""

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fp2_probe import Probe, ROOT, simulate
from fp2_reference import mx_decode
from fp2_tensor_probe import packed


PREFETCH_TB = r"""
module tb;
  reg clk=0; always #5 clk=~clk;
  reg rst_n,flush=0,w_valid=0,w_format=0,w_first=0,w_last=0,w_error=0,tile_ready=0;
  reg [511:0] w_data=0,read_data;
  reg [15:0] w_scale=0;
  reg [31:0] w_tag=0;
  wire w_ready,tile_valid,tile_first,tile_last,tile_error;
  wire [2047:0] tile_data;
  wire [31:0] tile_tag;
  anvil_q2_fp2_ping_pong_prefetch prefetch(clk,rst_n,flush,w_valid,w_ready,w_data,
    w_scale,w_format,w_first,w_last,w_tag,w_error,tile_valid,tile_ready,tile_data,
    tile_first,tile_last,tile_tag,tile_error);
  integer fd,n,cycle=0,rf,rv,rformat,rfirst,rlast,rtag,re,rr,rs;
  integer writes=0,tiles=0,overlap=0,both_full=0,flushes=0;
  reg held=0; reg [2082:0] held_payload;
  wire [2082:0] payload={tile_data,tile_tag,tile_first,tile_last,tile_error};
  wire reset_ok=({w_ready,tile_valid,payload}===0);
  string input_path;
  always @(posedge clk) if(!rst_n && reset_ok !== 1'b1) $fatal(1,"RESET posedge");
  always @(negedge clk) if(!rst_n && reset_ok !== 1'b1) $fatal(1,"RESET negedge");
  initial begin
    rst_n=0; #1; if(reset_ok !== 1'b1) $fatal(1,"RESET time0");
    repeat(2) @(negedge clk); rst_n=1;
    if(!$value$plusargs("INPUT=%s",input_path)) $fatal(1,"missing INPUT");
    fd=$fopen(input_path,"r"); if(!fd) $fatal(1,"open INPUT");
    while(!$feof(fd)) begin
      n=$fscanf(fd,"%d %d %h %d %d %d %d %d %d %d\n",rf,rv,read_data,
        rs,rformat,rfirst,rlast,rtag,re,rr);
      if(n!=10) begin if(!$feof(fd)) $fatal(1,"malformed INPUT"); end
      else begin
        flush=rf; w_valid=rv; w_data=read_data; w_scale=rs; w_format=rformat;
        w_first=rfirst; w_last=rlast; w_tag=rtag; w_error=re; tile_ready=rr;
        @(posedge clk);
        if((^{w_ready,tile_valid,tile_error}) === 1'bx) $fatal(1,"PREFETCH_ACTIVE_X");
        if(!flush && held && (tile_valid !== 1'b1 || payload !== held_payload))
          $fatal(1,"PREFETCH_STALLED_PAYLOAD");
        if(!flush && tile_valid && !w_ready) both_full=both_full+1;
        if(w_valid && w_ready && tile_valid && tile_ready) overlap=overlap+1;
        if(tile_valid && tile_ready) begin
          if((^payload) === 1'bx) $fatal(1,"PREFETCH_PAYLOAD_X");
          $display("TILE %0d %h %0d %0d %0d %0d",cycle,tile_data,tile_tag,
            tile_first,tile_last,tile_error); tiles=tiles+1;
        end
        if(w_valid) begin
          if(!flush && w_ready !== 1'b1) $fatal(1,"DIRECTED_BEAT_NOT_READY");
          if(w_ready) begin $display("BEAT %0d",cycle); writes=writes+1; end
        end
        if(flush) begin $display("FLUSH %0d",cycle); flushes=flushes+1; end
        held=tile_valid && !tile_ready && !flush;
        if(held) held_payload=payload;
        @(negedge clk); cycle=cycle+1;
      end
    end
    if(tile_valid || writes==0 || tiles==0 || overlap==0 || both_full==0 || flushes==0)
      $fatal(1,"PREFETCH_REQUIRED_COVERAGE");
    $display("SUMMARY %0d %0d %0d %0d %0d",writes,tiles,overlap,both_full,flushes);
    $finish;
  end
endmodule
"""


def stimulus():
    rows = []

    def idle(ready=0, flush=0):
        rows.append((flush, 0, 0, 0, 0, 0, 0, 0, 0, ready))

    def beat(format_, tag, number, ready=0, bad=False, memory_error=False):
        if format_:
            codes = [(16 + lane + number * 64) % 120 for lane in range(64)]
            data = sum(value << (8 * lane) for lane, value in enumerate(codes))
            scale = 0x7F80
        else:
            values = [0x3F00 + ((tag * 17 + number * 32 + lane) % 127) for lane in range(32)]
            data = int(packed(values), 16)
            scale = 0
        rows.append((0, 1, data, scale, format_, 1, 1,
                     tag + int(bad), int(memory_error), ready))

    for number in range(4):
        beat(0, 10, number)
    for number in range(2):
        beat(1, 20, number)
    for _ in range(4):
        idle()
    idle(ready=1)
    # Slot zero is free and slot one still owns its tile at this next edge.
    beat(0, 30, 0, ready=1)
    for number in range(1, 4):
        beat(0, 30, number)
    idle(ready=1)
    for number in range(4):
        beat(0, 40, number, bad=number == 1)
    idle(ready=1)
    for number in range(2):
        beat(1, 50, number, memory_error=number == 0)
    idle(ready=1)
    for number in range(2):
        beat(0, 60, number)
    idle(flush=1)
    idle()
    for number in range(2):
        beat(1, 70, number)
    for _ in range(3):
        idle()
    idle(ready=1)
    idle()
    return rows


def run(probe, simulator="iverilog", override=None):
    rows = stimulus()
    source = probe.directory / "tb.sv"
    source.write_text(PREFETCH_TB)
    inputs = probe.directory / "inputs.txt"
    inputs.write_text("".join(
        f"{flush} {valid} {data:0128x} {scale} {format_} {first} {last} {tag} {error} {ready}\n"
        for flush, valid, data, scale, format_, first, last, tag, error, ready in rows))
    output = simulate(probe, source, [ROOT / "rtl/anvil_q2_fp2_mx_decode.sv",
                                     override or ROOT / "rtl/anvil_q2_fp2_ping_pong_prefetch.sv"],
                      simulator, [f"+INPUT={inputs.relative_to(ROOT)}"])
    queue, assembling = [], []
    metadata = None
    failed = False
    observed_beats, observed_tiles, summary = 0, 0, None
    for line in output.read_text().splitlines():
        words = line.split()
        if words[:1] == ["TILE"]:
            if not queue:
                raise AssertionError("output without a complete accepted weight tile")
            expected = queue.pop(0)
            cycle, data, tag, first, last, error = (int(words[1]), int(words[2], 16),
                                                   *map(int, words[3:]))
            probe.compare("prefetch-data", f"{expected[0]:0512x}", f"{data:0512x}", {"cycle": cycle})
            probe.compare("prefetch-metadata", expected[1:], (tag, first, last, error), {"cycle": cycle})
            observed_tiles += 1
        elif words[:1] == ["BEAT"]:
            row = rows[int(words[1])]
            _, _, data, scale, format_, first, last, tag, error, _ = row
            observed_beats += 1
            if metadata is None:
                metadata = (format_, tag, first, last)
                failed = bool(error)
            else:
                failed |= bool(error) or metadata != (format_, tag, first, last)
            if metadata[0]:
                decoded = []
                for lane in range(64):
                    value, invalid = mx_decode((data >> (8 * lane)) & 255,
                                               (scale >> (8 * (lane // 32))) & 255)
                    decoded.append(value)
                    failed |= invalid
                assembling.extend(decoded)
            else:
                assembling.extend((data >> (16 * lane)) & 65535 for lane in range(32))
            if len(assembling) == 128:
                queue.append((int(packed(assembling), 16), metadata[1], metadata[2],
                              metadata[3], int(failed)))
                metadata, assembling = None, []
        elif words[:1] == ["FLUSH"]:
            queue, assembling, metadata = [], [], None
        elif words[:1] == ["SUMMARY"]:
            summary = tuple(map(int, words[1:]))
    probe.compare("prefetch-observed-beats", sum(row[1] for row in rows), observed_beats, {})
    probe.compare("prefetch-observed-tiles", 6, observed_tiles, {})
    probe.compare("prefetch-undrained", 0, len(queue) + len(assembling), {})
    if summary is None:
        raise AssertionError("missing prefetch summary")
    for label, index in (("simultaneous-fill-and-consume", 2), ("both-owned-buffers", 3),
                         ("cancelled-partial-tile", 4)):
        probe.compare(label, True, summary[index] > 0, {})
    probe.summary["public_transaction_accounting"] = summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--simulator", choices=("iverilog", "verilator"), default="iverilog")
    args = parser.parse_args()
    probe = Probe("prefetch")
    try:
        run(probe, args.simulator)
        return probe.settle()
    except Exception as error:
        return probe.settle(f"{type(error).__name__}: {error}")


if __name__ == "__main__":
    raise SystemExit(main())
