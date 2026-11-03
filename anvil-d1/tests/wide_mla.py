"""Compiled streaming MLA checks without production checkpoint/register dumps.

Two complementary legal geometries execute actual hardware absorption:
16 heads / 512 latent / 64 rotary / 128 noPE/value with H=8; and full
H=2048 contraction rows with one head/rank. Neither is a full production
token inference or a timing claim. Raw DDR weights are generated from a frozen
integer function. Absorbed/cache/scratch read responses come exclusively from
actual checked DUT writes. Same-edge request/response service is exercised.
"""

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from diagnostic import hexfile, simulate
from evidence import Evidence, rel
from reference import Q16, round_sat, rotate


def raw(matrix, head, row, col):
    return ((matrix*13+head*7+row*3+col*5) % 17-8)*1024


def wide_bench(evidence, full_hidden=False):
    h, nh, rk, rp, np, vh = (2048, 1, 1, 2, 128, 128) if full_hidden else (8, 16, 512, 64, 128, 128)
    x = [(j % 9-4)*8192 for j in range(h)]
    c = [round_sat(sum(raw(0, 0, r, j)*x[j] for j in range(h)), 16) for r in range(rk)]
    kr0 = [round_sat(sum(raw(1, 0, r, j)*x[j] for j in range(h)), 16) for r in range(rp)]
    table = [v for _ in range(rp//2) for v in (Q16, 8192)]
    kr = rotate(kr0, table)
    a, b, qa, qr0, qr = [], [], [], [], []
    for head in range(nh):
        ah = [[sum(raw(4, head, d, r)*raw(2, head, d, j) for d in range(np))
               for j in range(h)] for r in range(rk)]
        bh = [[sum(raw(6, 0, i, head*vh+v)*raw(5, head, v, r) for v in range(vh))
               for r in range(rk)] for i in range(h)]
        a.extend(v for row in ah for v in row)
        b.extend(v for row in bh for v in row)
        q = [round_sat(sum(v*w for v, w in zip(row, x, strict=True)), 32) for row in ah]
        qa.extend(q)
        qr_initial = [round_sat(sum(raw(3, head, r, j)*x[j] for j in range(h)), 16)
                      for r in range(rp)]
        qr0.extend(qr_initial)
        qr.extend(rotate(qr_initial, table))
    output = [round_sat(sum(b[(head*h+i)*rk+r]*c[r] for head in range(nh) for r in range(rk)), 32)
              for i in range(h)]
    # Full-width unabsorbed contractions, with no conventional intermediate
    # rounding, independently check every query/output boundary.
    for head in range(nh):
        qn_exact = [sum(raw(2, head, d, j)*x[j] for j in range(h)) for d in range(np)]
        unabsorbed = [round_sat(sum(raw(4, head, d, r)*qn_exact[d] for d in range(np)), 32)
                      for r in range(rk)]
        if unabsorbed != qa[head*rk:(head+1)*rk]:
            raise AssertionError("wide unabsorbed query contraction disagreement")
    uv_exact = [[sum(raw(5, head, v, r)*c[r] for r in range(rk)) for v in range(vh)]
                for head in range(nh)]
    expanded_output = [round_sat(sum(raw(6, 0, i, head*vh+v)*uv_exact[head][v]
                                     for head in range(nh) for v in range(vh)), 32) for i in range(h)]
    if expanded_output != output:
        raise AssertionError("wide unabsorbed output contraction disagreement")
    image = evidence.path / "checkpoint-images"
    image.mkdir()
    for name, values, digits in (
            ("a", a, 24), ("b", b, 24), ("x", x, 8), ("c", c, 8),
            ("kr0", kr0, 8), ("kr", kr, 8), ("qa", qa, 8),
            ("qr0", qr0, 8), ("qr", qr, 8), ("output", output, 8)):
        mask = (1 << (digits*4))-1
        hexfile(image / (name+".hex"), [v & mask for v in values], digits)
    summary = dict(hidden=h, heads=nh, rank=rk, nope=np, rope=rp, value=vh,
                   absorption_comparisons=len(a)*3+len(b)*3,
                   query_comparisons=nh*rk, context_comparisons=nh*rk,
                   cache_read_bytes=(rk+rp)*8, cache_write_bytes=(rk+rp)*4,
                   dense_equiv_bytes=nh*(np+rp+vh)*12,
                   raw_weight_formula="((matrix*13+head*7+row*3+col*5)%17-8)*1024",
                   full_production_top_inference=False)
    (evidence.path / "wide-fixtures.json").write_text(json.dumps(summary, indent=2)+"\n")
    bench = BENCH
    for name, value in dict(H=h, NH=nh, RK=rk, RP=rp, NP=np, VH=vh).items():
        bench = bench.replace("@"+name+"@", str(value))
    (evidence.path / "wide.sv").write_text(bench)
    return summary


BENCH = r"""
module tb;
  localparam H=@H@,NH=@NH@,RK=@RK@,RP=@RP@,NP=@NP@,VH=@VH@;
  reg clk=0; always #5 clk=~clk;
  reg rst_n,flush=0,cmd_valid=0;
  wire cmd_ready,done,error;
  wire [63:0] kv_read_bytes,kv_write_bytes,kv_dense_equiv_bytes;
  wire c_req_valid,c_req_write,c_rsp_ready;
  wire [3:0] c_req_kind;
  wire [2:0] c_req_proj;
  wire [31:0] c_req_layer,c_req_row,c_req_col,c_req_wdata;
  reg c_req_ready=0;
  wire c_rsp_valid=c_req_valid && c_req_ready;
  reg [31:0] c_rsp_rdata;
  anvil_d1_mla_engine #(.NUM_LAYERS(1),.HIDDEN_SIZE(H),.NUM_Q_HEADS(NH),
    .KV_LORA_RANK(RK),.QK_NOPE_HEAD_DIM(NP),.QK_ROPE_HEAD_DIM(RP),.V_HEAD_DIM(VH),
    .MAX_SEQ_LEN(1)) device (
    .clk(clk),.rst_n(rst_n),.flush(flush),.cmd_valid(cmd_valid),.cmd_ready(cmd_ready),
    .cmd_epoch(32'd1),.cmd_layer(32'd0),.cmd_pos(32'd0),.cmd_phase(1'b1),
    .done(done),.error(error),.kv_read_bytes(kv_read_bytes),.kv_write_bytes(kv_write_bytes),
    .kv_dense_equiv_bytes(kv_dense_equiv_bytes),.c_req_valid(c_req_valid),
    .c_req_ready(c_req_ready),.c_req_write(c_req_write),.c_req_kind(c_req_kind),
    .c_req_layer(c_req_layer),.c_req_proj(c_req_proj),.c_req_row(c_req_row),
    .c_req_col(c_req_col),.c_req_wdata(c_req_wdata),.c_rsp_valid(c_rsp_valid),
    .c_rsp_ready(c_rsp_ready),.c_rsp_rdata(c_rsp_rdata),.c_rsp_error(1'b0)
  );
  reg [95:0] expected_a[0:NH*RK*H-1],expected_b[0:NH*H*RK-1];
  reg [31:0] actual_a[0:NH*RK*H*3-1],actual_b[0:NH*H*RK*3-1];
  reg valid_a[0:NH*RK*H*3-1],valid_b[0:NH*H*RK*3-1];
  reg [31:0] xs[0:H-1],expected_c[0:RK-1],expected_kr0[0:RP-1],expected_kr[0:RP-1];
  reg [31:0] expected_qa[0:NH*RK-1],expected_qr0[0:NH*RP-1],expected_qr[0:NH*RP-1];
  reg [31:0] expected_output[0:H-1];
  reg [31:0] cache[0:RK+RP-1],queries[0:NH*RK-1],rope_scratch[0:NH*RP-1],contexts[0:NH*RK-1];
  reg cache_valid[0:RK+RP-1],query_valid[0:NH*RK-1],context_valid[0:NH*RK-1];
  integer rope_writes[0:NH*RP-1],cache_reads[0:RK+RP-1];
  reg output_valid[0:H-1];
  integer cycles=0,absorption=0,reads=0,writes=0,query_writes=0,context_writes=0;
  integer cache_writes=0,output_writes=0,stalls=0,same_edge=0,reset_samples=0;
  integer head,row,component,index,matrix,word_number;
  reg [31:0] expected_word;
  reg [136:0] held=0;
  reg stalled=0,preedge_done=0;
  function automatic [31:0] raw_weight(input integer m,h,r,c);
    raw_weight=((m*13+h*7+r*3+c*5)%17-8)*1024;
  endfunction
  function automatic [31:0] memory_read;
    integer m,h,r,c,address;
    begin
      memory_read=0;
      m=c_req_row[31:28]; h=c_req_row[27:24]; r=c_req_row[23:0]; c=c_req_col;
      if (c_req_kind==8) begin
        if (c_req_layer!=0 || c_req_proj!=0 || c_req_row!=1 || c>=H)
          $fatal(1,"WIDE_BAD_INPUT_READ");
        memory_read=xs[c];
      end else if (c_req_kind!=15 || c_req_layer!=0) $fatal(1,"WIDE_BAD_NAMESPACE");
      else case (c_req_proj)
        0: begin
          if (m>6 || h>=NH || (m==0 && (h!=0 || r>=RK || c>=H)) ||
              (m==1 && (h!=0 || r>=RP || c>=H)) ||
              (m==2 && (r>=NP || c>=H)) || (m==3 && (r>=RP || c>=H)) ||
              (m==4 && (r>=NP || c>=RK)) || (m==5 && (r>=VH || c>=RK)) ||
              (m==6 && (h!=0 || r>=H || c>=NH*VH))) $fatal(1,"WIDE_RAW_INDEX");
          memory_read=raw_weight(m,h,r,c);
        end
        1,2: begin
          h=c_req_row[31:28]; r=c_req_row[27:0];
          if (h>=NH || r>=(c_req_proj==1 ? RK : H) || c>=(c_req_proj==1 ? H*3 : RK*3))
            $fatal(1,"WIDE_ABSORBED_INDEX");
          address=(h*(c_req_proj==1 ? RK : H)+r)*(c_req_proj==1 ? H*3 : RK*3)+c;
          if (c_req_proj==1) begin
            if (!valid_a[address]) $fatal(1,"WIDE_UNINITIALIZED_A");
            memory_read=actual_a[address];
          end else begin
            if (!valid_b[address]) $fatal(1,"WIDE_UNINITIALIZED_B");
            memory_read=actual_b[address];
          end
        end
        3: begin
          if (c_req_row!=0 || c>=RK+RP || !cache_valid[c]) $fatal(1,"WIDE_EXPANDED_OR_INVALID_CACHE");
          memory_read=cache[c];
        end
        6: begin
          if (c_req_row!=0 || c>=RP) $fatal(1,"WIDE_ROTARY_INDEX");
          memory_read=c[0] ? 8192 : 65536;
        end
        7: case (c_req_row)
          5: begin
            if (c>=NH*RK || !query_valid[c]) $fatal(1,"WIDE_QUERY_INDEX");
            memory_read=queries[c];
          end
          6: begin
            if (c>=NH*RP || rope_writes[c]==0) $fatal(1,"WIDE_ROPE_INDEX");
            memory_read=rope_scratch[c];
          end
          7: begin
            if (c>=NH*RK || !context_valid[c]) $fatal(1,"WIDE_CONTEXT_INDEX");
            memory_read=contexts[c];
          end
          default: $fatal(1,"WIDE_SCRATCH_READ");
        endcase
        default: $fatal(1,"WIDE_BAD_PROJECTION");
      endcase
    end
  endfunction
  always @* c_rsp_rdata=c_rsp_valid && !c_req_write ? memory_read() : 32'd0;
  task automatic reset_check;
    begin
      if ({cmd_ready,done,error,kv_read_bytes,kv_write_bytes,kv_dense_equiv_bytes,
           c_req_valid,c_req_write,c_req_kind,c_req_layer,c_req_proj,
           c_req_row,c_req_col,c_req_wdata,c_rsp_ready} !== 0) $fatal(1,"WIDE_RESET_XZ");
      reset_samples=reset_samples+1;
    end
  endtask
  always @(posedge clk or negedge clk) if (!rst_n) reset_check();
  always @(negedge clk) c_req_ready=rst_n && cycles%11!=0;
  initial begin
    rst_n=0;
    $readmemh("checkpoint-images/a.hex",expected_a);
    $readmemh("checkpoint-images/b.hex",expected_b);
    $readmemh("checkpoint-images/x.hex",xs);
    $readmemh("checkpoint-images/c.hex",expected_c);
    $readmemh("checkpoint-images/kr0.hex",expected_kr0);
    $readmemh("checkpoint-images/kr.hex",expected_kr);
    $readmemh("checkpoint-images/qa.hex",expected_qa);
    $readmemh("checkpoint-images/qr0.hex",expected_qr0);
    $readmemh("checkpoint-images/qr.hex",expected_qr);
    $readmemh("checkpoint-images/output.hex",expected_output);
    for (integer j=0;j<NH*RK*H*3;j=j+1) valid_a[j]=0;
    for (integer j=0;j<NH*H*RK*3;j=j+1) valid_b[j]=0;
    for (integer j=0;j<RK+RP;j=j+1) begin cache_valid[j]=0; cache_reads[j]=0; end
    for (integer j=0;j<NH*RK;j=j+1) begin query_valid[j]=0; context_valid[j]=0; end
    for (integer j=0;j<NH*RP;j=j+1) rope_writes[j]=0;
    for (integer j=0;j<H;j=j+1) output_valid[j]=0;
    #1; reset_check(); repeat(2) @(negedge clk); #1; rst_n=1;
    @(negedge clk); while (!cmd_ready) @(negedge clk); cmd_valid=1;
    @(posedge clk); #1;
    if (cmd_ready!==0 || done!==0 || c_req_valid!==0) $fatal(1,"WIDE_POST_ACCEPTANCE");
    @(negedge clk); cmd_valid=0;
    wait(done); @(negedge clk);
    if (error!==0 || absorption!=NH*RK*H*6 || query_writes!=NH*RK ||
        context_writes!=NH*RK || cache_writes!=RK+RP || output_writes!=H ||
        kv_read_bytes!==64'((RK+RP)*8) || kv_write_bytes!==64'((RK+RP)*4) ||
        kv_dense_equiv_bytes!==64'(NH*(NP+RP+VH)*12) || same_edge==0 || stalls==0)
      $fatal(1,"WIDE_MISSING_COMPARISONS_OR_TRAFFIC");
    for (integer j=0;j<NH*RK*H*3;j=j+1) if (!valid_a[j]) $fatal(1,"WIDE_MISSING_A");
    for (integer j=0;j<NH*H*RK*3;j=j+1) if (!valid_b[j]) $fatal(1,"WIDE_MISSING_B");
    for (integer j=0;j<RK+RP;j=j+1) if (cache_reads[j]!=2) $fatal(1,"WIDE_REPEATED_CACHE_READ");
    for (integer j=0;j<NH*RP;j=j+1)
      if (rope_writes[j]!=(j<RP ? 3 : 2)) $fatal(1,"WIDE_ROPE_WRITE_COUNT");
    if (NH==16 && RK==512 && RP==64 &&
        (kv_read_bytes+kv_write_bytes)*100 >= kv_dense_equiv_bytes*18)
      $fatal(1,"WIDE_CACHE_REDUCTION_NOT_GREATER_THAN_82_PERCENT");
    $display("SUMMARY wide_hidden=%0d heads=%0d rank=%0d rope=%0d absorption=%0d queries=%0d contexts=%0d writes=%0d reads=%0d same_edge=%0d cache_read_bytes=%0d cache_write_bytes=%0d cache_dense_equiv_bytes=%0d cycles=%0d",
      H,NH,RK,RP,absorption,query_writes,context_writes,writes,reads,same_edge,
      kv_read_bytes,kv_write_bytes,kv_dense_equiv_bytes,cycles);
    $finish;
  end
  always @(posedge clk) if (rst_n) begin
    preedge_done=done; cycles=cycles+1;
    if (cycles>1000000000) $fatal(1,"WIDE_OPERATIONAL_CYCLE_BOUND");
    if (cycles%100000000==0) $display("PROGRESS cycles=%0d absorption=%0d",cycles,absorption);
    if ((^{cmd_ready,done,error,c_req_valid,c_rsp_ready})===1'bx) $fatal(1,"WIDE_CONTROL_XZ");
    if (stalled && {c_req_valid,c_req_write,c_req_kind,c_req_layer,c_req_proj,c_req_row,c_req_col,c_req_wdata} !== held)
      $fatal(1,"WIDE_UNSTABLE_REQUEST");
    stalled=c_req_valid && !c_req_ready;
    held={c_req_valid,c_req_write,c_req_kind,c_req_layer,c_req_proj,c_req_row,c_req_col,c_req_wdata};
    if (stalled) stalls=stalls+1;
    if (c_req_valid && c_req_ready) begin
      if (c_rsp_valid!==1'b1 || c_rsp_ready!==1'b1) $fatal(1,"WIDE_SAME_EDGE_NOT_ACCEPTED");
      same_edge=same_edge+1;
      if (c_req_write) begin
        if (c_req_kind!=15 || c_req_layer!=0) $fatal(1,"WIDE_WRITE_NAMESPACE");
        writes=writes+1; head=c_req_row[31:28]; row=c_req_row[27:0];
        component=c_req_col/3; word_number=c_req_col%3;
        case (c_req_proj)
          1,2: begin
            if (head>=NH || row>=(c_req_proj==1 ? RK : H) ||
                c_req_col>=(c_req_proj==1 ? H*3 : RK*3)) $fatal(1,"WIDE_ABSORPTION_INDEX");
            index=(head*(c_req_proj==1 ? RK : H)+row)*(c_req_proj==1 ? H : RK)+component;
            expected_word=c_req_proj==1 ? expected_a[index][word_number*32+:32] :
              expected_b[index][word_number*32+:32];
            index=index*3+word_number;
            if (c_req_proj==1) begin
              if (valid_a[index]) $fatal(1,"WIDE_DUPLICATE_A");
              actual_a[index]=c_req_wdata; valid_a[index]=1;
            end else begin
              if (valid_b[index]) $fatal(1,"WIDE_DUPLICATE_B");
              actual_b[index]=c_req_wdata; valid_b[index]=1;
            end
            absorption=absorption+1;
          end
          3: begin
            if (c_req_row!=0 || c_req_col>=RK+RP || cache_valid[c_req_col]) $fatal(1,"WIDE_CACHE_WRITE_INDEX");
            expected_word=c_req_col<RK ? expected_c[c_req_col] : expected_kr[c_req_col-RK];
            cache[c_req_col]=c_req_wdata; cache_valid[c_req_col]=1; cache_writes=cache_writes+1;
          end
          7: case (c_req_row)
            5: begin
              if (c_req_col>=NH*RK || query_valid[c_req_col]) $fatal(1,"WIDE_QUERY_WRITE_INDEX");
              expected_word=expected_qa[c_req_col]; queries[c_req_col]=c_req_wdata;
              query_valid[c_req_col]=1; query_writes=query_writes+1;
            end
            6: begin
              if (c_req_col>=NH*RP) $fatal(1,"WIDE_ROPE_WRITE_INDEX");
              if (c_req_col<RP && rope_writes[c_req_col]==0) expected_word=expected_kr0[c_req_col];
              else if (rope_writes[c_req_col]==(c_req_col<RP ? 1 : 0)) expected_word=expected_qr0[c_req_col];
              else expected_word=expected_qr[c_req_col];
              rope_scratch[c_req_col]=c_req_wdata; rope_writes[c_req_col]=rope_writes[c_req_col]+1;
            end
            7: begin
              if (c_req_col>=NH*RK || context_valid[c_req_col]) $fatal(1,"WIDE_CONTEXT_WRITE_INDEX");
              expected_word=expected_c[c_req_col%RK]; contexts[c_req_col]=c_req_wdata;
              context_valid[c_req_col]=1; context_writes=context_writes+1;
            end
            3: begin
              if (c_req_col>=H || output_valid[c_req_col]) $fatal(1,"WIDE_OUTPUT_WRITE_INDEX");
              expected_word=expected_output[c_req_col]; output_valid[c_req_col]=1; output_writes=output_writes+1;
            end
            default: $fatal(1,"WIDE_UNKNOWN_SCRATCH_WRITE");
          endcase
          default: $fatal(1,"WIDE_UNKNOWN_WRITE");
        endcase
        if (c_req_wdata !== expected_word)
          $fatal(1,"WIDE_NUMERICAL_WRITE_MISMATCH proj=%0d row=%h col=%0d actual=%h expected=%h",
            c_req_proj,c_req_row,c_req_col,c_req_wdata,expected_word);
        if (c_req_proj==7 && c_req_row==3 && c_req_col==H-1) begin
          #1;
          if (done!==1 || error!==0 || cmd_ready!==0) $fatal(1,"WIDE_FINAL_ACK_LATENCY");
        end
      end else begin
        reads=reads+1;
        if (c_req_kind==15 && c_req_proj==3) cache_reads[c_req_col]=cache_reads[c_req_col]+1;
      end
    end
    if (preedge_done) begin
      #1;
      if (done!==0 || cmd_ready!==1) $fatal(1,"WIDE_DONE_RETIREMENT");
    end
  end
endmodule
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--full-hidden", action="store_true")
    parser.add_argument("--repair-of")
    args = parser.parse_args()
    evidence = Evidence("mla-full-hidden" if args.full_hidden else "mla-production-widths", args.repair_of)
    try:
        summary = wide_bench(evidence, args.full_hidden)
        summary["observations"] = simulate(evidence, "wide.sv", "verilator")
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
