"""Full native RMSNorm leaf comparisons for the independently frozen equations.

All three native normalization modes are exercised through public memory pins.
Memory returns only generated input/gamma words, never expected output words.
Each expected scalar is compared at its architectural write, with finite stalls,
registered command completion, complete request payload stability and reset/X/Z
checks. Numerical intermediates are retained before any DUT execution.
"""

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from diagnostic import hexfile, simulate
from evidence import Evidence, rel
from numerical import rms_discriminators


def rms_bench(evidence):
    traces = rms_discriminators()
    image = evidence.path / "checkpoint-images"
    image.mkdir()
    for name, field in (("x", "x"), ("gamma", "gamma"), ("expected", "outputs")):
        hexfile(image / (name+".hex"),
                [v & 0xffffffff for trace in traces for v in trace[field]], 8)
    (evidence.path / "rms-fixtures.json").write_text(json.dumps(
        dict(geometry=dict(hidden=24, layers=2, maxseq=5),
             traces=traces, modes=[0, 1, 2],
             required_writes=len(traces)*3*24,
             required_reads=len(traces)*3*24*3), indent=2)+"\n")
    bench = BENCH.replace("@CASES@", str(len(traces)))
    (evidence.path / "rms.sv").write_text(bench)
    return dict(rms_vectors=len(traces), modes=3, expected_scalars=len(traces)*3*24,
                fixed_u=traces[0]["u"], fixed_output=traces[0]["outputs"])


BENCH = r"""
module tb;
  localparam H=24, CASES=@CASES@;
  reg clk=0; always #5 clk=~clk;
  reg rst_n,flush=0,cmd_valid=0;
  reg [31:0] cmd_layer=0,cmd_pos=0;
  reg [1:0] cmd_mode=0;
  wire cmd_ready,done,error;
  wire mem_req_valid,mem_req_write,mem_rsp_ready;
  reg mem_req_ready=0,mem_rsp_valid=0,mem_rsp_error=0;
  wire [3:0] mem_req_kind;
  wire [2:0] mem_req_proj;
  wire [31:0] mem_req_layer,mem_req_row,mem_req_col,mem_req_wdata;
  reg [31:0] mem_rsp_rdata=0;
  anvil_d1_rmsnorm #(.HIDDEN_SIZE(H),.NUM_LAYERS(2),.MAX_SEQ_LEN(5)) device (
    .clk(clk),.rst_n(rst_n),.flush(flush),.cmd_valid(cmd_valid),.cmd_ready(cmd_ready),
    .cmd_layer(cmd_layer),.cmd_pos(cmd_pos),.cmd_mode(cmd_mode),.done(done),.error(error),
    .mem_req_valid(mem_req_valid),.mem_req_ready(mem_req_ready),.mem_req_write(mem_req_write),
    .mem_req_kind(mem_req_kind),.mem_req_layer(mem_req_layer),.mem_req_proj(mem_req_proj),
    .mem_req_row(mem_req_row),.mem_req_col(mem_req_col),.mem_req_wdata(mem_req_wdata),
    .mem_rsp_valid(mem_rsp_valid),.mem_rsp_ready(mem_rsp_ready),
    .mem_rsp_rdata(mem_rsp_rdata),.mem_rsp_error(mem_rsp_error)
  );
  reg [31:0] xs[0:CASES*H-1],gamma[0:CASES*H-1],expected[0:CASES*H-1];
  reg [H-1:0] written=0;
  reg pending=0,pending_write=0;
  integer pending_col=0,response_delay=0;
  reg [31:0] response_data=0;
  integer current_case=0,mode=0,cycles=0,reads=0,writes=0,completions=0;
  integer stimulus_case=0,active_case=0,active_mode=0,active_layer=0;
  integer accepted=0,write_acks=0,last_ack_edge=-1,reset_samples=0,stalls=0;
  integer previous_reads=0,previous_writes=0,previous_acks=0;
  integer mode_completions[0:2];
  integer source_reads[0:H-1],gamma_reads[0:H-1];
  reg stalled=0;
  reg [136:0] held=0;

  task automatic check_reset;
    begin
      if ({cmd_ready,done,error,mem_req_valid,mem_req_write,mem_req_kind,
           mem_req_layer,mem_req_proj,mem_req_row,mem_req_col,mem_req_wdata,
           mem_rsp_ready} !== 0) $fatal(1,"RESET_XZ_OR_NONZERO t=%0t",$time);
      reset_samples=reset_samples+1;
    end
  endtask
  always @(posedge clk or negedge clk) if (!rst_n) check_reset();

  initial begin
    rst_n=0;
    $readmemh("checkpoint-images/x.hex",xs);
    $readmemh("checkpoint-images/gamma.hex",gamma);
    $readmemh("checkpoint-images/expected.hex",expected);
    for (integer j=0;j<3;j=j+1) mode_completions[j]=0;
`ifdef VERILATOR
    #1;
`else
    #0;
`endif
    check_reset(); repeat(2) @(negedge clk); #1; rst_n=1;
    for (current_case=0;current_case<CASES;current_case=current_case+1)
      for (mode=0;mode<3;mode=mode+1) begin
        @(negedge clk); while (cmd_ready!==1'b1) @(negedge clk);
        written=0; previous_reads=reads; previous_writes=writes; previous_acks=write_acks;
        for (integer j=0;j<H;j=j+1) begin source_reads[j]=0; gamma_reads[j]=0; end
        stimulus_case=current_case;
        cmd_layer=mode==2 ? 0 : 1; cmd_mode=mode; cmd_pos=4; cmd_valid=1;
        @(posedge clk);
        if (cmd_ready!==1'b1 || mem_req_valid!==1'b0) $fatal(1,"ACCEPTANCE_EDGE");
        #1;
        if (cmd_ready!==1'b0 || done!==1'b0 || mem_req_valid!==1'b0)
          $fatal(1,"POST_ACCEPTANCE_EDGE");
        @(negedge clk); cmd_valid=0;
        @(posedge clk); while (done!==1'b1) @(posedge clk);
        if (error!==1'b0 || written!=={H{1'b1}} || pending ||
            reads-previous_reads!=3*H || writes-previous_writes!=H ||
            write_acks-previous_acks!=H || last_ack_edge<0)
          $fatal(1,"RMS_COMPLETION_OR_COUNTS case=%0d mode=%0d reads=%0d writes=%0d acks=%0d last_ack=%0d edge=%0d",
            current_case,mode,reads-previous_reads,writes-previous_writes,
            write_acks-previous_acks,last_ack_edge,cycles);
        for (integer j=0;j<H;j=j+1)
          if (source_reads[j]!=2 || gamma_reads[j]!=1) $fatal(1,"RMS_READ_COVERAGE col=%0d",j);
        #1;
        if (done!==1'b0 || cmd_ready!==1'b1) $fatal(1,"COMPLETION_RETIREMENT");
      end
    if (completions!=CASES*3 || accepted!=CASES*3 || stalls==0 || reset_samples<5)
      $fatal(1,"MISSING_COMPARISONS");
    for (integer j=0;j<3;j=j+1)
      if (mode_completions[j]!=CASES) $fatal(1,"MISSING_MODE_COMPARISONS mode=%0d",j);
    $display("SUMMARY rms_vectors=%0d commands=%0d reads=%0d compared_writes=%0d stalls=%0d reset=%0d",
      CASES,completions,reads,writes,stalls,reset_samples);
    $finish;
  end

  always @(negedge clk) if (rst_n)
    mem_req_ready=!pending && cycles%7!=0;

  always @(posedge clk) if (rst_n) begin
    cycles=cycles+1;
    if (cycles>500000) $fatal(1,"RMS_CYCLE_BOUND");
    if ((^{cmd_ready,done,error,mem_req_valid,mem_rsp_ready})===1'bx)
      $fatal(1,"ACTIVE_CONTROL_XZ");
    if (cmd_valid && cmd_ready) begin
      accepted=accepted+1;
      active_case=stimulus_case; active_mode=cmd_mode; active_layer=cmd_layer;
    end
    if (done) begin
      if (written!=={H{1'b1}} || error!==1'b0 || active_mode>2)
        $fatal(1,"UNCHECKED_MODE_COMPLETION");
      completions=completions+1;
      mode_completions[active_mode]=mode_completions[active_mode]+1;
    end
    if (stalled && {mem_req_valid,mem_req_write,mem_req_kind,mem_req_layer,mem_req_proj,
                    mem_req_row,mem_req_col,mem_req_wdata} !== held)
      $fatal(1,"STALLED_REQUEST_CHANGED");
    stalled=mem_req_valid && !mem_req_ready;
    held={mem_req_valid,mem_req_write,mem_req_kind,mem_req_layer,mem_req_proj,
          mem_req_row,mem_req_col,mem_req_wdata};
    if (stalled) stalls=stalls+1;
    if (mem_rsp_valid && mem_rsp_ready) begin
      if (!pending) $fatal(1,"UNOWNED_RESPONSE");
      if (pending_write) begin
        write_acks=write_acks+1;
        if (pending_col==H-1) last_ack_edge=cycles;
      end
      pending<=0; mem_rsp_valid<=0;
    end
    if (pending && !mem_rsp_valid) begin
      if (response_delay==0) begin
        mem_rsp_valid<=1; mem_rsp_rdata<=response_data;
      end else response_delay=response_delay-1;
    end
    if (mem_req_valid && mem_req_ready) begin
      if (pending || (^{mem_req_write,mem_req_kind,mem_req_layer,mem_req_proj,
                        mem_req_row,mem_req_col,mem_req_wdata})===1'bx ||
          mem_req_col>=H || mem_req_proj!==0) $fatal(1,"INVALID_REQUEST");
      pending<=1; pending_write<=mem_req_write; pending_col=mem_req_col;
      response_delay=cycles%5;
      if (mem_req_write) begin
        if (mem_req_kind!==8 || mem_req_layer!==0 ||
            mem_req_row!==(active_mode==0 ? 1 : active_mode==1 ? 8 : 14) || written[mem_req_col])
          $fatal(1,"MISINDEXED_RMS_WRITE");
        if (mem_req_wdata !== expected[active_case*H+mem_req_col])
          $fatal(1,"RMS_NUMERICAL_MISMATCH case=%0d mode=%0d col=%0d actual=%h expected=%h",
            active_case,active_mode,mem_req_col,mem_req_wdata,expected[active_case*H+mem_req_col]);
        written[mem_req_col]=1; writes=writes+1; response_data<=0;
      end else begin
        reads=reads+1;
        if (mem_req_kind==8) begin
          if (mem_req_layer!==0 || mem_req_row!==(active_mode==1 ? 7 : 0))
            $fatal(1,"MISINDEXED_RMS_INPUT");
          response_data<=xs[active_case*H+mem_req_col];
          source_reads[mem_req_col]=source_reads[mem_req_col]+1;
        end else begin
          if (mem_req_kind!==(active_mode==0 ? 5 : active_mode==1 ? 6 : 7) ||
              mem_req_layer!==(active_mode==2 ? 0 : active_layer) || mem_req_row!==0)
            $fatal(1,"MISINDEXED_RMS_GAMMA case=%0d mode=%0d kind=%0d layer=%0d row=%0d col=%0d command_mode=%0d command_layer=%0d",
              active_case,active_mode,mem_req_kind,mem_req_layer,mem_req_row,mem_req_col,cmd_mode,cmd_layer);
          response_data<=gamma[active_case*H+mem_req_col];
          gamma_reads[mem_req_col]=gamma_reads[mem_req_col]+1;
        end
      end
      if (mem_rsp_valid && mem_rsp_ready && pending_write && pending_col==H-1) begin
        #1;
        if (done!==1'b1 || cmd_ready!==1'b0 || error!==1'b0)
          $fatal(1,"FINAL_WRITE_ACK_COMPLETION_LATENCY");
      end
    end
  end
endmodule
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sim", choices=("icarus", "verilator"), default="verilator")
    parser.add_argument("--repair-of")
    args = parser.parse_args()
    evidence = Evidence("rms-"+args.sim, args.repair_of)
    try:
        summary = rms_bench(evidence)
        summary["observations"] = simulate(evidence, "rms.sv", args.sim)
        evidence.finish("passed", **summary)
        print(summary["observations"].strip())
    except Exception as exc:
        evidence.finish("failed", error=str(exc))
        print(str(exc), file=sys.stderr)
        print(rel(evidence.path / "receipt.json"), file=sys.stderr)
        return 1
    print(rel(evidence.path / "receipt.json"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
