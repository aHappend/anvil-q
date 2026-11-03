"""Actual marker IDs at the public top, including deferred-token reobservation.

These are protocol fixtures, not pretrained inference: zero-dequantized linear
weights and three nonzero tied embedding rows make every vocabulary logit
independently predictable. All 151936 logits still traverse the real decoder.
"""

from fractions import Fraction
import hashlib
import json
import re

from execution import ROOT, relative
from model import rmsnorm
import reference as fp


OPEN, CLOSE, VOCABULARY = 151667, 151668, 151936


def marker_reference(path, opening):
    path.mkdir(exist_ok=False)
    target = OPEN if opening else CLOSE
    inputs = [3 if opening else OPEN, target]
    vectors = {}
    for token, multiplier in ((3, 1), (OPEN, 4 if opening else 1),
                               (CLOSE, 0 if opening else 4)):
        vectors[token] = [fp.encode(Fraction(multiplier * (i + 1), 128), 16)
                          for i in range(8)]
    tables = {"embeddings": [], "scratch": [], "logits": []}
    for token in (3, OPEN, CLOSE):
        tables["embeddings"].extend(vectors[token])
    for token in inputs:
        initial = vectors[token]
        normalized = rmsnorm(initial, [0x3F80] * 8)
        stages = {0: initial, 1: normalized, 7: initial, 8: normalized, 14: normalized}
        flat = [0] * (15 * 16)
        for slot, data in stages.items():
            flat[slot * 16:slot * 16 + 8] = data
        tables["scratch"].extend(flat)
        logits = []
        for row in (3, OPEN, CLOSE):
            products = [fp.multiply(a << 16, b << 16)
                        for a, b in zip(normalized, vectors[row])]
            logits.append(fp.add(0, fp.balanced_sum(products + [0] * 248)))
        if (3, OPEN, CLOSE)[max(range(3), key=lambda i: (fp.decode(logits[i]), -i))] != target:
            raise AssertionError("marker fixture does not predict its real target marker")
        tables["logits"].extend(logits)
    hashes = {}
    for name, data in tables.items():
        file = path / f"{name}.hex"
        file.write_text("".join(f"{value:08x}\n" for value in data))
        hashes[name] = hashlib.sha256(file.read_bytes()).hexdigest()
    return {"opening": opening, "target": target, "inputs": inputs,
            "image_sha256": hashes, "vocabulary": VOCABULARY,
            "expected_frames": 2, "expected_logit_words": 2 * VOCABULARY}


MARKER_DRIVER = r"""
#include "Vanvil_qn1_top.h"
#include "verilated.h"
#include <array>
#include <chrono>
#include <cstdint>
#include <deque>
#include <fstream>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
#include <vector>
using U=uint32_t;using L=uint64_t;
static void check(bool ok,const std::string& message) {
  if (!ok) throw std::runtime_error(message);
}
static std::vector<U> load(const std::string& path) {
  std::ifstream input(path);check(bool(input),"missing marker image");
  std::vector<U> values;U value;
  while (input>>std::hex>>value) values.push_back(value);
  check(input.eof(),"invalid marker image");return values;
}
struct Response { L tag;U data; };
int main(int argc,char** argv) {
  try {
    check(argc==4,"marker driver arguments");std::string prefix=argv[1];
    bool opening=std::stoul(argv[2]);const U target=opening ? 151667:151668;
    U threads=std::stoul(argv[3]);
    const U vocabulary=151936,MAX=16,KD=8;
    const std::array<U,2> host={opening ? 3U:151667U,target};
    auto embedding=load(prefix+"/embeddings.hex"),reference=load(prefix+"/scratch.hex");
    auto logits=load(prefix+"/logits.hex"),rope=load(prefix+"/rope.hex");
    check(embedding.size()==24 && reference.size()==480 && logits.size()==6,
          "marker reference extents");
    auto embed=[&](U row,U col)->U {
      return row==3 ? embedding[col]:row==151667 ? embedding[8+col]:
        row==151668 ? embedding[16+col]:0;
    };
    auto logit=[&](U tx,U row)->U {
      return row==3 ? logits[tx*3]:row==151667 ? logits[tx*3+1]:
        row==151668 ? logits[tx*3+2]:0;
    };
    auto context=std::make_unique<VerilatedContext>();
    context->threads(threads);
    auto dut=std::make_unique<Vanvil_qn1_top>(context.get());
    dut->clk=0;dut->rst_n=0;dut->cancel=0;dut->token_valid=0;
    dut->new_sequence=0;dut->token_phase=1;dut->token_id=0;dut->token_pos=0;
    dut->draft_valid=1;dut->draft_count=1;dut->draft_parents=4;
    for (U i=0;i<4;++i) dut->draft_tokens[i]=i==0 ? target:0;
    dut->commit_ready=0;dut->logit_ready=0;
    dut->csr_valid=0;dut->csr_write=0;dut->csr_addr=0;dut->csr_wdata=0;
    dut->csr_wstrb=15;dut->csr_rsp_ready=0;
    dut->mem_req_ready=255;dut->mem_rsp_valid=0;dut->mem_rsp_error=0;
    for (U b=0;b<8;++b) {
      dut->mem_rsp_rdata[b]=0;dut->mem_rsp_tag[2*b]=0;dut->mem_rsp_tag[2*b+1]=0;
    }
    L cycle=0,requests=0,words=0,commits=0,drafts=0,compared=0;
    std::array<std::deque<Response>,8> pending;
    std::vector<U> scratch(15*MAX),writes(15*MAX),keys(4*KD),values(4*KD);
    std::vector<bool> valid(15*MAX),key_valid(4*KD),value_valid(4*KD);
    std::array<U,7> in_extent={8,8,8,16,8,8,8},out_extent={16,8,8,8,8,8,8};
    auto last_progress=std::chrono::steady_clock::now();
    auto edge=[&] {
      dut->clk=1;dut->eval();context->timeInc(5);
      dut->clk=0;dut->eval();context->timeInc(5);++cycle;
      if ((cycle&4095)==0 && std::chrono::steady_clock::now()-last_progress>
          std::chrono::seconds(30)) {
        std::cout<<"MARKER_PROGRESS cycles="<<cycle<<" logits="<<words
          <<" requests="<<requests<<std::endl;
        last_progress=std::chrono::steady_clock::now();
      }
    };
    dut->eval();
    check(!dut->token_ready && !dut->logit_valid && !dut->commit_valid &&
          !dut->draft_ready && !dut->think_active && !dut->error &&
          !dut->done && !dut->mem_req_valid,"marker reset outputs");
    edge();edge();dut->rst_n=1;dut->eval();
    auto csr=[&](bool write,U address,U data,U expected) {
      dut->csr_write=write;dut->csr_addr=address;dut->csr_wdata=data;
      dut->csr_rsp_ready=0;dut->csr_valid=0;dut->eval();
      for (U i=0;!dut->csr_ready && i<100;++i) edge();
      check(dut->csr_ready,"marker CSR readiness");
      dut->csr_valid=1;dut->eval();edge();
      check(!dut->csr_rsp_valid,"marker CSR zero-latency response");
      dut->csr_valid=0;dut->eval();edge();
      check(dut->csr_rsp_valid && !dut->csr_error && dut->csr_rdata==expected,
            "MARKER_CSR_COMPARE address="+std::to_string(address)+
            " got="+std::to_string(dut->csr_rdata)+" expected="+std::to_string(expected));
      for (U i=0;i<3;++i) {
        edge();check(dut->csr_rsp_valid && !dut->csr_error &&
                     dut->csr_rdata==expected,"marker held CSR response");
      }
      dut->csr_rsp_ready=1;dut->eval();edge();
      check(!dut->csr_rsp_valid,"marker duplicate CSR response");
      dut->csr_valid=0;edge();
    };
    for (U tx=0;tx<2;++tx) {
      if (tx==1) {
        // Oppose the generated marker before its deferred resubmission.
        // Re-observing that old marker would select the wrong continuation mode.
        csr(true,8,opening ? 0:1,0);
        check(dut->think_active==!opening,"marker idle override");
      }
      std::fill(writes.begin(),writes.end(),0);
      std::fill(valid.begin(),valid.end(),false);
      U frame_words=0,draft_count=0,commit_count=0,frame_stalls=0,commit_stalls=0;
      L last_logit=0,last_commit=0;
      bool accepted=false,completed=false,held_logit=false,held_commit=false;
      U saved_index=0,saved_data=0,saved_pos=0;
      std::array<U,5> saved_tokens{};
      dut->token_valid=1;dut->new_sequence=tx==0;
      dut->token_id=host[tx];dut->token_pos=tx;dut->draft_valid=1;
      while (!completed) {
        dut->mem_rsp_valid=0;
        for (U b=0;b<8;++b) if (!pending[b].empty()) {
          dut->mem_rsp_valid|=1U<<b;dut->mem_rsp_rdata[b]=pending[b].front().data;
          dut->mem_rsp_tag[2*b]=U(pending[b].front().tag);
          dut->mem_rsp_tag[2*b+1]=U(pending[b].front().tag>>32);
        }
        dut->logit_ready=cycle%19!=2 && cycle%19!=3;
        dut->commit_ready=commit_stalls>=7;dut->eval();
        check(!dut->error && !dut->cancel_done,"marker transaction fault");
        if (accepted) check(!dut->token_ready,"overlapping marker transaction");
        if (!accepted && dut->token_valid && dut->token_ready) {
          check(!dut->draft_ready,"draft accepted with host token");accepted=true;
        }
        if (frame_words<vocabulary) {
          check(!dut->draft_ready,"marker draft before completed root frame");
          check(!dut->commit_valid,"marker commit before complete vocabulary");
        }
        if (held_logit)
          check(dut->logit_valid && dut->logit_index==saved_index &&
                dut->logit_data==saved_data,"marker stalled logit stability");
        held_logit=dut->logit_valid && !dut->logit_ready;
        saved_index=dut->logit_index;saved_data=dut->logit_data;
        if (held_logit) ++frame_stalls;
        if (held_commit) {
          check(dut->commit_valid && dut->commit_count==1 && dut->commit_pos==saved_pos,
                "marker stalled commit stability");
          for (U i=0;i<5;++i) check(dut->commit_tokens[i]==saved_tokens[i],
                                    "marker stalled token payload");
        }
        held_commit=dut->commit_valid && !dut->commit_ready;
        saved_pos=dut->commit_pos;
        for (U i=0;i<5;++i) saved_tokens[i]=dut->commit_tokens[i];
        if (held_commit) ++commit_stalls;
        if (dut->draft_valid && dut->draft_ready) {
          check(!opening && frame_words==vocabulary && draft_count==0 &&
                dut->think_active,"MARKER_DEFERRED_REOBSERVATION");
          ++draft_count;++drafts;
        }
        for (U b=0;b<8;++b) {
          if ((dut->mem_rsp_valid & dut->mem_rsp_ready)&(1U<<b)) {
            check(!pending[b].empty(),"marker unowned response");pending[b].pop_front();
          }
        }
        for (U b=0;b<8;++b) if (dut->mem_req_valid & (1U<<b)) {
          U kind=(dut->mem_req_kind>>(4*b))&15,proj=(dut->mem_req_proj>>(3*b))&7;
          U layer=dut->mem_req_layer[b],row=dut->mem_req_row[b],col=dut->mem_req_col[b];
          bool write=dut->mem_req_write & (1U<<b);U data=0;
          check(layer==0 && col<MAX,"marker memory bounds");
          if (write) {
            U got=dut->mem_req_wdata[b];check((got>>16)==0,"marker reserved bits");
            if (kind==8) {
              U extent=row==2 || row==5 ? 16:8;
              check(row<15 && row!=13 && col<extent,"marker scratch extent");
              U a=row*MAX+col;
              check(got==reference[tx*15*MAX+a],"MARKER_SCRATCH_COMPARE");
              check(writes[a]<(row==0 ? 2U:1U),"duplicate marker scratch write");
              ++writes[a];scratch[a]=got;valid[a]=true;++compared;
            } else {
              check((kind==9 || kind==10) && row==tx && col<KD,"marker KV position");
              U a=row*KD+col;auto& seen=kind==9 ? key_valid:value_valid;
              auto& storage=kind==9 ? keys:values;
              check(!seen[a] && got==0,"MARKER_KV_COMPARE");
              seen[a]=true;storage[a]=got;++compared;
            }
          } else switch (kind) {
            case 0:
              check(row<vocabulary && col<8,"marker embedding/LM extent");
              data=embed(row,col);break;
            case 1:case 2:case 3:
              check(proj<7 && (kind==1 ? row<in_extent[proj]:row<in_extent[proj]/8) &&
                    (kind==3 ? col<out_extent[proj]:col<(out_extent[proj]+7)/8),
                    "marker projection extents");
              data=kind==3 ? 0x3c00:0x88888888;break;
            case 5:case 6:case 7:case 12:case 13:
              check(row==0 && col<8,"marker gamma extent");data=0x3f80;break;
            case 8:
              check(row<15 && valid[row*MAX+col],"marker uninitialized scratch");
              data=scratch[row*MAX+col];break;
            case 9:case 10: {
              check(row<=tx && col<KD,"marker causal KV position");
              U a=row*KD+col;
              check(kind==9 ? key_valid[a]:value_valid[a],"marker uninitialized KV");
              data=kind==9 ? keys[a]:values[a];break;
            }
            case 11:
              check(row==tx && col<8,"marker coefficient address");
              data=rope[row*8+col];break;
            default: throw std::runtime_error("marker forbidden memory kind");
          }
          L tag=L(dut->mem_req_tag[2*b])|(L(dut->mem_req_tag[2*b+1])<<32);
          pending[b].push_back({tag,data});++requests;
        }
        if (dut->logit_valid && dut->logit_ready) {
          check(accepted && frame_words<vocabulary && dut->logit_index==frame_words &&
                dut->logit_data==logit(tx,frame_words),"MARKER_LOGIT_COMPARE");
          ++frame_words;++words;last_logit=cycle;
        }
        if (dut->commit_valid) {
          check(frame_words==vocabulary && dut->commit_count==1 &&
                dut->commit_pos==tx+1 && dut->commit_tokens[0]==target &&
                dut->think_active==!opening &&
                (opening ? draft_count==0:draft_count==1),
                "MARKER_CUTOFF_OR_MODE_COMPARE");
          for (U i=1;i<5;++i) check(dut->commit_tokens[i]==0,"marker extra token");
          for (const auto& queue:pending) check(queue.empty(),"marker unsettled publication");
        }
        bool transfer=dut->commit_valid && dut->commit_ready;
        if (transfer) {++commits;++commit_count;last_commit=cycle;}
        if (dut->done) {
          check(frame_words==vocabulary && commit_count==1 && cycle>last_logit &&
                cycle>last_commit && frame_stalls && commit_stalls>=7 &&
                !dut->token_ready,"marker completion ordering/coverage");
          completed=true;
        }
        edge();
        if (transfer) check(dut->think_active==opening,"marker commit mode transition");
        if (accepted) {dut->token_valid=0;dut->new_sequence=0;}
        if (draft_count) dut->draft_valid=0;
      }
      dut->mem_rsp_valid=0;dut->eval();edge();
      check(dut->think_active==opening && dut->token_ready,"marker idle continuation");
      for (U slot=0;slot<15;++slot) if (slot!=13) {
        U extent=slot==2 || slot==5 ? 16:8;
        for (U col=0;col<extent;++col)
          check(writes[slot*MAX+col]==(slot==0 ? 2U:1U),"marker stage write coverage");
      }
    }
    dut->draft_valid=0;
    csr(true,8,(opening ? 1:0)|2,0);
    csr(false,0x028,0,opening ? 0:2);csr(false,0x030,0,opening ? 2:0);
    csr(false,0x050,0,opening ? 0:2);csr(false,0x058,0,0);
    csr(false,0x060,0,opening ? 0:2);csr(false,0x068,0,0);
    check(words==2*vocabulary && commits==2 && drafts==(opening ? 0U:2U),
          "marker comparison denominator");
    std::cout<<"MARKER_SUMMARY opening="<<opening<<" frames=2 logits="<<words
      <<" commits="<<commits<<" drafts="<<drafts<<" compared_writes="<<compared
      <<" requests="<<requests<<" cycles="<<cycle<<std::endl;
    dut->final();return 0;
  } catch (const std::exception& error) {
    std::cerr<<error.what()<<std::endl;return 1;
  }
}
"""


def run_markers(run, opening=True, threads=1, compiled=None, clock_optimized=False):
    images = run.path / "checkpoint-images"
    result = marker_reference(images, opening)
    rope = [value for position in range(2)
            for pair in zip(*fp.coefficients(8, position)) for value in pair]
    (images / "rope.hex").write_text("".join(f"{value:08x}\n" for value in rope))
    driver = run.path / "marker_driver.cpp"
    text = MARKER_DRIVER
    if clock_optimized:
        from speculation_checks import replace_once

        # Native RTL has no falling-clock event. Settle the low clock with the
        # next inputs, not again immediately after the rising-edge evaluation.
        for source in (ROOT / "rtl").glob("anvil_qn1_*.sv"):
            if re.search(r"\bnegedge\s+clk\b", source.read_text()):
                raise AssertionError("optimized transactor requires rising-edge-only RTL")
        text = replace_once(text, "auto edge=[&] {",
                            "auto edge=[&](bool low_settled=false) {\n"
                            "      if (!low_settled) dut->eval();")
        text = replace_once(
            text, "dut->clk=0;dut->eval();context->timeInc(5);++cycle;",
            "dut->clk=0;context->timeInc(5);++cycle;")
        text = replace_once(text, "        edge();\n        if (transfer)",
                            "        edge(true);\n        if (transfer)")
    driver.write_text(text)
    sources = [relative(p) for p in sorted((ROOT / "rtl").glob("anvil_qn1_*.sv"))]
    parameters = {"COMPACT": 1, "NUM_LAYERS": 1, "HIDDEN_SIZE": 8,
                  "INTERMEDIATE_SIZE": 8, "NUM_Q_HEADS": 2, "NUM_KV_HEADS": 1,
                  "HEAD_DIM": 8, "VOCAB_SIZE": VOCABULARY, "MAX_SEQ_LEN": 4,
                  "GROUP_SIZE": 8, "BANKS": 8, "QUEUE_DEPTH": 3}
    binding = {"driver_sha256": hashlib.sha256(driver.read_bytes()).hexdigest(),
               "parameters": parameters, "simulation_threads": threads,
               "rtl_sha256": {name: run.hashes[name] for name in sources},
               "tool_versions": {name: run.tool_versions[name]
                                 for name in ("verilator", "g++", "make")}}
    if compiled is not None:
        binary = ROOT / compiled["binary"]
        if (compiled.get("binding") != binding or not binary.is_file() or
                hashlib.sha256(binary.read_bytes()).hexdigest() != compiled["binary_sha256"] or
                compiled.get("optimization") != "OPT_FAST=-O3 OPT_SLOW=-O3 OPT_GLOBAL=-O3"):
            print("MARKER_BUILD_STALE: recompiling current source/driver/parameters", flush=True)
            compiled = None
    if compiled is None:
        from marker_builds import marker_build

        compiled = marker_build(run, text, binding)
    output = run.execute([compiled["binary"], relative(images),
                          str(int(opening)), str(threads)], "marker-simulation")
    records = re.findall(r"^MARKER_SUMMARY opening=(\d+) frames=2 logits=(\d+) "
                         r"commits=(\d+) drafts=(\d+) compared_writes=(\d+) "
                         r"requests=(\d+) cycles=(\d+)$", output, re.M)
    if len(records) != 1:
        raise AssertionError("missing/duplicate integrated marker comparisons")
    counts = list(map(int, records[0]))
    if counts[:5] != [int(opening), 2 * VOCABULARY, 2, 0 if opening else 2, 304]:
        raise AssertionError("integrated marker coverage incomplete")
    result.update({"counts": counts, "parameters": parameters, "compiled": compiled,
                   "simulation_threads": threads, "clock_optimized": clock_optimized,
                   "scope": "real marker commit, cutoff, deferred resubmission and CSR counts"})
    (run.path / "marker-reference.json").write_text(json.dumps(result, indent=2) + "\n")
    return result
