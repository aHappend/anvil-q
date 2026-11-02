"""Compact integrated architectural diagnostic with a public DDR memory model.

The fixture has nonzero, head/row-distinct embeddings, unit norm weights and
zero projection weights/biases. Thus both residual branches are exactly zero;
the independently computed final normalized embedding determines every logit.
This fixture is not the full behavioral matrix or five-domain benchmark.
"""

import argparse
from fractions import Fraction
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fp2_probe import Probe, ROOT, simulate
from fp2_reference import add, exact, finite, multiply, rounded, tensor, transcendental


TOP_TB = r"""
module tb;
  reg clk=0;
  always #5 clk=~clk;
  reg rst_n, cancel=0, token_valid=0, logit_ready=0;
  reg [31:0] token_id=3, token_pos=0;
  wire token_ready, logit_valid, done, error, cancel_done;
  wire [31:0] logit_index, logit_data;
  wire [0:0] mem_req_valid, mem_req_write, mem_rsp_ready;
  wire [3:0] mem_req_kind;
  wire [31:0] mem_req_layer, mem_req_row, mem_req_col, mem_req_wdata;
  wire [2:0] mem_req_proj;
  wire [63:0] mem_req_tag;
  wire ddr_req_valid, ddr_req_write, ddr_rsp_ready;
  reg ddr_req_ready=0, ddr_rsp_valid=0, ddr_rsp_error=0;
  wire [3:0] ddr_req_kind;
  wire [31:0] ddr_req_layer, ddr_req_row, ddr_req_col;
  wire [2:0] ddr_req_proj;
  wire [1:0] ddr_req_format;
  wire [63:0] ddr_req_tag, ddr_req_wstrb;
  wire [511:0] ddr_req_wdata;
  reg [63:0] ddr_rsp_tag=0;
  reg [511:0] ddr_rsp_rdata=0;
  wire csr_req_ready, csr_rsp_valid, csr_rsp_error;
  wire [31:0] csr_rsp_rdata;
  anvil_q2_fp2_top #(
    .NUM_LAYERS(1),.HIDDEN_SIZE(48),.INTERMEDIATE_SIZE(64),
    .NUM_Q_HEADS(6),.NUM_KV_HEADS(1),.HEAD_DIM(8),.GROUP_SIZE(8),
    .VOCAB_SIZE(16),.MAX_SEQ_LEN(3),.BANKS(1),.CACHE_BLOCK(8),.QUEUE_DEPTH(3)
  ) accelerator (
    .clk(clk),.rst_n(rst_n),.cancel(cancel),
    .token_valid(token_valid),.token_ready(token_ready),
    .token_id(token_id),.token_pos(token_pos),.new_sequence(1'b1),.token_phase(1'b0),
    .logit_valid(logit_valid),.logit_ready(logit_ready),
    .logit_index(logit_index),.logit_data(logit_data),
    .done(done),.error(error),.cancel_done(cancel_done),
    .mem_req_valid(mem_req_valid),.mem_req_ready(1'b1),.mem_req_write(mem_req_write),
    .mem_req_kind(mem_req_kind),.mem_req_layer(mem_req_layer),.mem_req_proj(mem_req_proj),
    .mem_req_row(mem_req_row),.mem_req_col(mem_req_col),.mem_req_wdata(mem_req_wdata),
    .mem_req_tag(mem_req_tag),.mem_rsp_valid(1'b0),.mem_rsp_error(1'b0),
    .mem_rsp_ready(mem_rsp_ready),.mem_rsp_rdata(32'd0),.mem_rsp_tag(64'd0),
    .ddr_req_valid(ddr_req_valid),.ddr_req_ready(ddr_req_ready),
    .ddr_req_write(ddr_req_write),.ddr_req_kind(ddr_req_kind),
    .ddr_req_layer(ddr_req_layer),.ddr_req_proj(ddr_req_proj),
    .ddr_req_row(ddr_req_row),.ddr_req_col(ddr_req_col),
    .ddr_req_format(ddr_req_format),.ddr_req_tag(ddr_req_tag),
    .ddr_req_wdata(ddr_req_wdata),.ddr_req_wstrb(ddr_req_wstrb),
    .ddr_rsp_valid(ddr_rsp_valid),.ddr_rsp_error(ddr_rsp_error),
    .ddr_rsp_ready(ddr_rsp_ready),.ddr_rsp_tag(ddr_rsp_tag),.ddr_rsp_rdata(ddr_rsp_rdata),
    .csr_req_valid(1'b0),.csr_req_write(1'b0),.csr_req_addr(16'd0),
    .csr_req_wdata(32'd0),.csr_req_wstrb(4'd0),.csr_rsp_ready(1'b1),
    .csr_req_ready(csr_req_ready),.csr_rsp_valid(csr_rsp_valid),
    .csr_rsp_rdata(csr_rsp_rdata),.csr_rsp_error(csr_rsp_error)
  );
  // This is the external memory image, never an accelerator-internal mirror.
  reg [15:0] keys[0:23], values[0:23];
  reg pending[0:15];
  reg [63:0] tags[0:15];
  reg [511:0] responses[0:15];
  integer due[0:15];
  integer cycle=0, i, j, slot, chosen, active_response=-1, fd, n;
  integer outstanding=0, maximum_outstanding=0, reads=0, writes=0, logits=0;
  integer reordered=0, response_count=0, output_stalls=0, request_stalls=0;
  integer oldest, accepted_tokens=0;
  reg [31:0] random_state=17;
  reg held_request=0, held_logit=0, previous_logit_accept=0, response_accepted=0;
  reg [745:0] request_payload;
  reg [63:0] logit_payload;
  string image_path;
  reg [15:0] embedding[0:767];
  reg [15:0] scan_word;
  wire [745:0] current_request={ddr_req_write,ddr_req_kind,ddr_req_layer,ddr_req_proj,
    ddr_req_row,ddr_req_col,ddr_req_format,ddr_req_tag,ddr_req_wdata,ddr_req_wstrb};
  wire reset_outputs_zero=(
    {token_ready,logit_valid,logit_index,logit_data,done,error,cancel_done,
     mem_req_valid,mem_req_write,mem_req_kind,mem_req_layer,mem_req_proj,
     mem_req_row,mem_req_col,mem_req_wdata,mem_req_tag,mem_rsp_ready,
     ddr_req_valid,ddr_req_write,ddr_req_kind,ddr_req_layer,ddr_req_proj,
     ddr_req_row,ddr_req_col,ddr_req_format,ddr_req_tag,ddr_req_wdata,
     ddr_req_wstrb,ddr_rsp_ready,csr_req_ready,csr_rsp_valid,csr_rsp_rdata,csr_rsp_error}
     === 0);
  always @(posedge clk) if (!rst_n && reset_outputs_zero !== 1'b1)
    $fatal(1,"RESET_OUTPUT_X_OR_NONZERO posedge");
  always @(negedge clk) if (!rst_n && reset_outputs_zero !== 1'b1)
    $fatal(1,"RESET_OUTPUT_X_OR_NONZERO negedge");
  function automatic [511:0] read_beat(
    input [3:0] kind, input [31:0] row, column, input [1:0] format
  );
    reg [511:0] data;
    integer element;
    begin
      data=0;
      case (kind)
        0: for(element=0;element<32;element=element+1)
          if (column+element<48 && row<16)
            data[16*element+:16]=embedding[row*48+column+element];
        1,4: data=0;
        5,6,7: for(element=0;element<32;element=element+1)
          data[16*element+:16]=16'h3f80;
        9,10: for(element=0;element<32;element=element+1)
          if (column+element<8 && row<3) begin
            data[16*element+:16]=(kind==9) ?
              keys[row*8+column+element] : values[row*8+column+element];
          end
        11: for(element=0;element<16;element=element+1)
          data[32*element+:32]=((column+element)&1) ? 32'd0 : 32'h3f800000;
        default: $fatal(1,"UNEXPECTED_READ_KIND %0d",kind);
      endcase
      read_beat=data;
    end
  endfunction
  task automatic accept_write;
    integer byte_index, element, address;
    begin
      if (ddr_req_kind!=9 && ddr_req_kind!=10) $fatal(1,"UNEXPECTED_WRITE_KIND");
      for(byte_index=0;byte_index<64;byte_index=byte_index+1)
        if (ddr_req_wstrb[byte_index]) begin
          element=byte_index>>1;
          address=ddr_req_row*8+ddr_req_col+element;
          if (address>=24 || ddr_req_col+element>=8) $fatal(1,"CACHE_WRITE_RANGE");
          if (ddr_req_kind==9)
            keys[address][8*(byte_index&1)+:8]=ddr_req_wdata[8*byte_index+:8];
          else values[address][8*(byte_index&1)+:8]=ddr_req_wdata[8*byte_index+:8];
        end
    end
  endtask
  initial begin
    rst_n=0;
    #1;
    if (reset_outputs_zero !== 1'b1) $fatal(1,"RESET_OUTPUT_X_OR_NONZERO time0");
    for(i=0;i<16;i=i+1) pending[i]=0;
    for(i=0;i<24;i=i+1) begin keys[i]=0; values[i]=0; end
    if (!$value$plusargs("IMAGE=%s",image_path)) $fatal(1,"missing IMAGE");
    fd=$fopen(image_path,"r");
    if (fd==0) $fatal(1,"image open");
    for(i=0;i<768;i=i+1) begin
      n=$fscanf(fd,"%h\n",scan_word);
      if(n!=1) $fatal(1,"image length");
      embedding[i]=scan_word;
    end
    $fclose(fd);
    repeat(2) @(negedge clk);
    rst_n=1; token_valid=1;
    while (cycle<500000) begin
      random_state=random_state^(random_state<<13);
      random_state=random_state^(random_state>>17);
      random_state=random_state^(random_state<<5);
      ddr_req_ready=(random_state[2:0]!=0);
      logit_ready=(random_state[5:3]!=0) && (!logit_valid || output_stalls>=3);
      if (!ddr_rsp_valid) begin
        chosen=-1; oldest=-1;
        for(i=0;i<16;i=i+1) if(pending[i]) begin
          if(oldest==-1 || tags[i]<tags[oldest]) oldest=i;
          if(due[i]<=cycle && (chosen==-1 || tags[i]>tags[chosen])) chosen=i;
        end
        if(chosen!=-1) begin
          if(chosen!=oldest) reordered=reordered+1;
          active_response=chosen;
          ddr_rsp_valid=1;
          ddr_rsp_tag=tags[chosen]; ddr_rsp_rdata=responses[chosen];
        end
      end
      @(posedge clk);
      if ((^{token_ready,logit_valid,done,error,cancel_done,ddr_req_valid,
             ddr_rsp_ready,mem_req_valid,mem_req_write,mem_rsp_ready}) === 1'bx)
        $fatal(1,"ACTIVE_X_CONTROL token_ready=%b logit_valid=%b done=%b error=%b cancel_done=%b ddr_req_valid=%b ddr_rsp_ready=%b narrow=%b%b%b",
          token_ready,logit_valid,done,error,cancel_done,ddr_req_valid,ddr_rsp_ready,
          mem_req_valid,mem_req_write,mem_rsp_ready);
      if ({mem_req_valid,mem_req_write,mem_req_kind,mem_req_layer,mem_req_proj,
           mem_req_row,mem_req_col,mem_req_wdata,mem_req_tag,mem_rsp_ready} !== 0)
        $fatal(1,"INACTIVE_NARROW_INTERFACE");
      if (held_request && (!ddr_req_valid || current_request !== request_payload))
        $fatal(1,"DDR_REQUEST_CHANGED_DURING_STALL");
      if (held_logit && (!logit_valid || {logit_index,logit_data} !== logit_payload))
        $fatal(1,"LOGIT_CHANGED_DURING_STALL");
      held_request=ddr_req_valid && !ddr_req_ready;
      if(held_request) begin request_payload=current_request; request_stalls=request_stalls+1; end
      held_logit=logit_valid && !logit_ready;
      if(held_logit) begin logit_payload={logit_index,logit_data}; output_stalls=output_stalls+1; end
      if (token_valid && token_ready) accepted_tokens=accepted_tokens+1;
      response_accepted=ddr_rsp_valid && ddr_rsp_ready;
      if (ddr_rsp_valid && ddr_rsp_ready) begin
        if(active_response<0 || !pending[active_response]) $fatal(1,"UNMATCHED_RESPONSE");
        pending[active_response]=0; outstanding=outstanding-1;
        response_count=response_count+1;
      end
      if (ddr_req_valid && ddr_req_ready) begin
        if((^current_request) === 1'bx) $fatal(1,"ACTIVE_X_REQUEST");
        slot=-1;
        for(i=0;i<16;i=i+1) begin
          if(pending[i] && tags[i]==ddr_req_tag) $fatal(1,"REUSED_LIVE_TAG");
          if(!pending[i]) slot=i;
        end
        if(slot<0) $fatal(1,"OUTSTANDING_OVERFLOW");
        pending[slot]=1; tags[slot]=ddr_req_tag; due[slot]=cycle+2+(random_state[9:6]);
        if(ddr_req_write) begin
          writes=writes+1; accept_write(); responses[slot]=0;
        end else begin
          reads=reads+1;
          responses[slot]=read_beat(ddr_req_kind,ddr_req_row,ddr_req_col,ddr_req_format);
        end
        outstanding=outstanding+1;
        if(outstanding>maximum_outstanding) maximum_outstanding=outstanding;
      end
      if(logit_valid && logit_ready) begin
        if((^{logit_index,logit_data}) === 1'bx) $fatal(1,"ACTIVE_X_LOGIT");
        if(logit_index!=logits || (&logit_data[30:23])) $fatal(1,"LOGIT_ORDER_OR_NONFINITE");
        $display("LOGIT %0d %08h",logit_index,logit_data);
        logits=logits+1;
      end
      if(done) begin
        if(error || logits!=16 || accepted_tokens!=1 || outstanding!=0 ||
           !previous_logit_accept) $fatal(1,"INVALID_COMPLETION");
        $display("SUMMARY %0d %0d %0d %0d %0d %0d %0d %0d %0d",
          cycle,reads,writes,response_count,maximum_outstanding,reordered,
          output_stalls,request_stalls,logits);
        $finish;
      end
      previous_logit_accept=logit_valid && logit_ready && logit_index==15;
      @(negedge clk);
      if(accepted_tokens!=0) token_valid=0;
      if(response_accepted) begin
        ddr_rsp_valid=0; active_response=-1;
      end
      cycle=cycle+1;
    end
    $fatal(1,"CYCLE_BOUND 500000");
  end
endmodule
"""


def embedding(row, column):
    return rounded(Fraction((row * 13 + column * 7) % 17 - 8, 16), fraction_bits=7)


def expected_logits():
    vector = [embedding(3, column) << 16 for column in range(48)]
    total = 0
    for value in vector:
        total = add(total, multiply(value, value))
    mean = multiply(total, rounded(Fraction(1, 48)))
    inverse = transcendental(add(mean, 0x358637BD), "rsqrt")
    normalized = [rounded(exact(multiply(value, inverse)), fraction_bits=7) for value in vector]
    return [
        tensor(normalized + [0] * 80, [embedding(row, c) for c in range(48)] + [0] * 80,
               (1 << 48) - 1)[0]
        for row in range(16)
    ]


def run(probe, simulator):
    source = probe.directory / "tb.sv"
    source.write_text(TOP_TB)
    images = probe.directory / "checkpoint-images"
    images.mkdir()
    image = images / "embedding.hex"
    image.write_text("".join(f"{embedding(row, c):04x}\n" for row in range(16) for c in range(48)))
    rtl = sorted((ROOT / "anvil_q2_fp_reference/rtl").glob("*.sv"))
    rtl += sorted((ROOT / "rtl").glob("*.sv"))
    output = simulate(probe, source, rtl, simulator, [f"+IMAGE={image.relative_to(ROOT)}"])
    expected = expected_logits()
    seen = set()
    summary = None
    with output.open() as stream:
        for line in stream:
            words = line.split()
            if words[:1] == ["SUMMARY"]:
                summary = list(map(int, words[1:]))
            if words[:1] != ["LOGIT"]:
                continue
            index, actual = int(words[1]), int(words[2], 16)
            if index in seen or not 0 <= index < 16:
                raise AssertionError(f"duplicate/out-of-range logit {index}")
            seen.add(index)
            reference = expected[index]
            error = abs(exact(actual) - exact(reference)) if finite(actual) else None
            threshold = Fraction(5, 10000) * (1 + abs(exact(reference)))
            probe.compare(
                "architectural-logit", True, error is not None and error <= threshold,
                {"index": index, "reference": f"{reference:08x}", "observed": f"{actual:08x}",
                 "absolute_error": float(error) if error is not None else None,
                 "threshold": float(threshold)},
            )
    probe.compare("logit-count", 16, len(seen), {})
    if summary is None or len(summary) != 9:
        raise AssertionError("missing complete simulation accounting summary")
    names = ("cycles", "read_beats", "write_beats", "responses", "maximum_outstanding",
             "reordered_responses", "logit_stalls", "request_stalls", "logits")
    probe.summary["transactions"] = dict(zip(names, summary, strict=True))
    accounting = probe.summary["transactions"]
    probe.compare("response-conservation", summary[1] + summary[2], summary[3], {})
    probe.compare("real-cache-writes", 2, summary[2], {})
    for key in ("read_beats", "reordered_responses", "logit_stalls", "request_stalls"):
        probe.compare(key + "-observed", True, accounting[key] > 0, {})
    probe.compare("two-outstanding-observed", True, accounting["maximum_outstanding"] >= 2, {})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--simulator", choices=("iverilog", "verilator"), default="verilator")
    parser.add_argument("--repair-of")
    args = parser.parse_args()
    probe = Probe("top-smoke", args.repair_of)
    try:
        run(probe, args.simulator)
        return probe.settle()
    except Exception as error:
        return probe.settle(f"{type(error).__name__}: {error}")


if __name__ == "__main__":
    raise SystemExit(main())
