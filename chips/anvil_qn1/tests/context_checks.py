"""D128 causal attention over an independently initialized external 40K cache.

Keys are nonzero and coordinate-dependent but invariant across positions, so all
scores for one head are equal. The softmax is exactly uniform. Position-varying
dyadic values permit an independent exact-rational sum while every physical
read, score, output coordinate, and completion is still checked.
"""

from fractions import Fraction
import hashlib
import json
import re

from execution import ROOT, relative
import reference as fp


CONTEXT_BENCH = r"""
module context_tb;
  parameter QH=32,KH=8,D=128,M=40960;
  reg clk=0,rst_n,flush=0,start_valid=0;
  always #5 clk=~clk;
  wire start_ready,out_valid,done,error,score_valid,req_valid,rsp_ready;
  wire [31:0] out_index,score_fp32,req_layer,req_row,req_col,req_tag;
  wire [15:0] out_data;
  wire [3:0] req_kind;
  reg out_ready=0,req_ready=0,rsp_valid=0;
  reg [31:0] rsp_data=0,rsp_tag=0,start_pos=0;
  reg [5:0] start_head=0;
  reg [D*16-1:0] start_query=0;
  reg [31:0] expected_score=0,query_image[0:D-1],key_image[0:D-1];
  reg [31:0] value_image[0:257*D-1],expected_context[0:D-1];
  reg [4095:0] prefix;
  reg [8191:0] filename;
  reg queued=0,held_req=0,held_out=0,finished=0;
  reg [131:0] saved_req;
  reg [47:0] saved_out;
  integer cycle=0,reads=0,scores=0,outputs=0,stalls=0,request_stalls=0;
  integer n=0,expected_row=0,expected_column=0,expected_kind=0;
  integer head_value=0,position_value=0,guard=0,queue_due=0,i,j;
  integer expected_reads=0,kv_base=0,last_output_cycle=-1;
  anvil_qn1_attention #(.HEAD_DIM(D),.NUM_Q_HEADS(QH),
    .NUM_KV_HEADS(KH),.MAX_SEQ_LEN(M)) dut(
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .start_valid(start_valid),.start_ready(start_ready),
    .start_layer(32'd2),.start_pos(start_pos),.start_head(start_head),
    .start_query(start_query),.out_valid(out_valid),.out_ready(out_ready),
    .out_index(out_index),.out_data(out_data),.done(done),.error(error),
    .score_valid(score_valid),.score_fp32(score_fp32),
    .req_valid(req_valid),.req_ready(req_ready),.req_kind(req_kind),
    .req_layer(req_layer),.req_row(req_row),.req_col(req_col),.req_tag(req_tag),
    .rsp_valid(rsp_valid),.rsp_ready(rsp_ready),.rsp_data(rsp_data),
    .rsp_tag(rsp_tag),.rsp_error(1'b0));
  task reset_outputs;
    begin
      if ({start_ready,out_valid,out_index,out_data,done,error,score_valid,score_fp32,
           req_valid,req_kind,req_layer,req_row,req_col,req_tag,rsp_ready}!==0)
        $fatal(1,"CONTEXT_RESET_XZ");
    end
  endtask
  always @(posedge clk or negedge clk) if (!rst_n) reset_outputs();
  always @(negedge clk) begin
    if (rst_n) begin
      req_ready=!queued && cycle%7!=2;
      out_ready=cycle%9>=4;
      rsp_valid=queued && cycle>=queue_due;
    end
  end
  always @(posedge clk) if (rst_n) begin
    cycle=cycle+1;
    if ((^{start_ready,out_valid,done,error,score_valid,req_valid,rsp_ready})===1'bx)
      $fatal(1,"CONTEXT_ACTIVE_XZ");
    if (error!==0) $fatal(1,"CONTEXT_UNEXPECTED_ERROR");
    if (held_req && (req_valid!==1 ||
        {req_kind,req_layer,req_row,req_col,req_tag}!==saved_req))
      $fatal(1,"CONTEXT_REQUEST_STABILITY");
    if (held_out && (out_valid!==1 || {out_index,out_data}!==saved_out))
      $fatal(1,"CONTEXT_OUTPUT_STABILITY");
    held_req=req_valid && !req_ready;
    saved_req={req_kind,req_layer,req_row,req_col,req_tag};
    held_out=out_valid && !out_ready;saved_out={out_index,out_data};
    if (held_req) request_stalls=request_stalls+1;
    if (held_out) stalls=stalls+1;
    if (rsp_valid && rsp_ready) begin
      if (!queued) $fatal(1,"CONTEXT_UNOWNED_RESPONSE");
      queued=0;
    end
    if (req_valid && req_ready) begin
      if (queued || reads>=expected_reads) $fatal(1,"CONTEXT_EXTRA_READ");
      // The public algorithm requires a maximum-score pass, then ordered K,V.
      if (reads<(start_pos+1)*D) begin
        expected_kind=9;expected_row=reads/D;expected_column=reads%D;
      end else begin
        n=reads-(start_pos+1)*D;expected_row=n/(2*D);
        expected_kind=n%(2*D)<D ? 9:10;expected_column=n%D;
      end
      if (req_kind!==expected_kind[3:0] || req_layer!==32'd2 ||
          req_row!==expected_row || req_col!==kv_base+expected_column ||
          req_tag!==((expected_kind==10 ? 256:0)+expected_column))
        $fatal(1,"CONTEXT_CACHE_ADDRESS read=%0d kind=%0d row=%0d col=%0d tag=%h expected_row=%0d expected_col=%0d",
          reads,req_kind,req_row,req_col,req_tag,expected_row,kv_base+expected_column);
      rsp_data=expected_kind==9 ? key_image[expected_column] :
        value_image[(expected_row%257)*D+expected_column];
      rsp_tag=req_tag;queued=1;queue_due=cycle+2+(reads%3);reads=reads+1;
    end
    if (score_valid) begin
      if (scores>=2*(start_pos+1) || score_fp32!==expected_score)
        $fatal(1,"CONTEXT_SCORE_COMPARE index=%0d got=%h expected=%h",
          scores,score_fp32,expected_score);
      scores=scores+1;
    end
    if (out_valid && out_ready) begin
      if (outputs>=D || reads!=expected_reads || queued ||
          out_index!==start_head*D+outputs ||
          out_data!==expected_context[outputs][15:0])
        $fatal(1,"CONTEXT_NUMERICAL_COMPARE coordinate=%0d got=%h expected=%h",
          outputs,out_data,expected_context[outputs]);
      outputs=outputs+1;last_output_cycle=cycle;
    end
    if (done) begin
      if (finished || outputs!=D || scores!=2*(start_pos+1) ||
          reads!=expected_reads || queued || cycle<=last_output_cycle || start_ready!==0)
        $fatal(1,"CONTEXT_DONE_ORDER");
      finished=1;
    end
  end
  initial begin
    rst_n=0;#1;reset_outputs();
    if (!$value$plusargs("images=%s",prefix) ||
        !$value$plusargs("position=%d",position_value) ||
        !$value$plusargs("head=%d",head_value) ||
        !$value$plusargs("score=%h",expected_score) ||
        position_value<0 || position_value>=M || head_value<0 || head_value>=QH)
      $fatal(1,"CONTEXT_ARGUMENTS");
    filename={prefix,"/query.hex"};$readmemh(filename,query_image);
    filename={prefix,"/key.hex"};$readmemh(filename,key_image);
    filename={prefix,"/value.hex"};$readmemh(filename,value_image);
    filename={prefix,"/context.hex"};$readmemh(filename,expected_context);
    for (i=0;i<D;i=i+1) start_query[i*16+:16]=query_image[i][15:0];
    start_pos=position_value;start_head=head_value;kv_base=(head_value/(QH/KH))*D;
    expected_reads=3*(position_value+1)*D;
    repeat (2) @(negedge clk);
    rst_n=1;#1;if (start_ready!==1) $fatal(1,"CONTEXT_START_READY");
    start_valid=1;@(posedge clk);#1;
    if (start_ready!==0 || out_valid!==0 || done!==0) $fatal(1,"CONTEXT_ACCEPT_ORDER");
    @(negedge clk);#1;start_valid=0;
    wait(finished);
    repeat (4) @(negedge clk);
    if (start_ready!==1 || stalls==0 || request_stalls==0 || done!==0)
      $fatal(1,"CONTEXT_RECOVERY_OR_STALL_COVERAGE");
    $display("CONTEXT_SUMMARY positions=%0d head=%0d reads=%0d scores=%0d outputs=%0d cycles=%0d output_stalls=%0d request_stalls=%0d",
      position_value+1,head_value,reads,scores,outputs,cycle,stalls,request_stalls);
    $finish;
  end
  initial begin repeat (400000000) @(posedge clk);$fatal(1,"CONTEXT_CYCLE_BOUND");end
endmodule
"""


def context_vectors(positions, dimension=128):
    query = [fp.encode(Fraction((i % 7) - 3, 8), 16) for i in range(dimension)]
    key = [fp.encode(Fraction((i % 11) - 5, 16), 16) for i in range(dimension)]
    values = [[fp.encode(Fraction(((p * 19 + i * 7) % 257) - 128, 256), 16)
               for i in range(dimension)] for p in range(257)]
    score = fp.multiply(fp.balanced_sum(
        fp.multiply(a << 16, b << 16) for a, b in zip(query, key)),
        fp.divide(0x3F800000, fp.sqrt32(fp.encode(dimension))))
    context = []
    for coordinate in range(dimension):
        complete, tail = divmod(positions, 257)
        exact = complete * sum((fp.decode(row[coordinate], 16) for row in values),
                               Fraction(0))
        exact += sum((fp.decode(values[p][coordinate], 16) for p in range(tail)),
                     Fraction(0))
        # All intermediate sums are integer multiples of 2^-8, with magnitude
        # below 2^16. Thus ordered RN32 additions are exact, even with cancellation.
        numerator = fp.encode(exact)
        if fp.decode(numerator) != exact:
            raise AssertionError("long-context exact-accumulation premise failed")
        context.append(fp.bf16(fp.divide(numerator, fp.encode(positions))))
    return query, key, values, score, context


def run_context(run, positions=40960, q_heads=32, kv_heads=8, head=31, compiled=None):
    if not 1 <= positions <= 40960:
        raise ValueError("invalid bounded attention context")
    vectors = context_vectors(positions)
    query, key, values, score, context = vectors
    images = run.path / "checkpoint-images"
    images.mkdir(exist_ok=False)
    for name, items in (("query", query), ("key", key),
                        ("value", [value for row in values for value in row]),
                        ("context", context)):
        with (images / f"{name}.hex").open("x") as output:
            output.writelines(f"{value:08x}\n" for value in items)
    bench = run.path / "context_tb.sv"
    bench.write_text(CONTEXT_BENCH)
    parameters = {"QH": q_heads, "KH": kv_heads, "D": 128, "M": 40960}
    binding = {"bench_sha256": hashlib.sha256(CONTEXT_BENCH.encode()).hexdigest(),
               "parameters": parameters, "source_sha256": run.hashes,
               "tool_versions": run.tool_versions}
    if compiled is not None and compiled["binding"] != binding:
        raise AssertionError("incompatible attention build reuse")
    if compiled is None:
        objects = run.path / "obj-context"
        sources = [relative(p) for p in sorted((ROOT / "rtl").glob("anvil_qn1_*.sv"))]
        run.execute(["verilator", "--binary", "--timing", "-Wno-fatal", "-j", "2",
                     "-CFLAGS", "-O3",
                     "--top-module", "context_tb", *[f"-G{k}={v}" for k, v in parameters.items()],
                     "--Mdir", relative(objects), "-o", "simulate", *sources, relative(bench)],
                    "context-compile")
        compiled = {"binary": relative(objects / "simulate"), "binding": binding}
    output = run.execute([compiled["binary"], f"+images={relative(images)}",
                          f"+position={positions-1}", f"+head={head}",
                          f"+score={score:08x}"], "context-simulation")
    matches = re.findall(
        r"CONTEXT_SUMMARY positions=(\d+) head=(\d+) reads=(\d+) scores=(\d+) "
        r"outputs=(\d+) cycles=(\d+) output_stalls=(\d+) request_stalls=(\d+)", output)
    if len(matches) != 1:
        raise AssertionError("missing full causal-cache comparison record")
    counts = list(map(int, matches[0]))
    if counts[:5] != [positions, head, 3 * positions * 128, 2 * positions, 128]:
        raise AssertionError("missing or duplicate long-context comparisons")
    result = {"positions": positions, "head": head, "q_heads": q_heads,
              "kv_heads": kv_heads, "head_dimension": 128, "score": score,
              "context": context, "counts": counts, "compiled": compiled,
              "oracle": "exact rational, uniform softmax, ordered exact dyadic accumulation",
              "scope": "attention leaf with independently initialized cache, not top-prefill"}
    (run.path / "context-reference.json").write_text(json.dumps(result, indent=2) + "\n")
    return result
