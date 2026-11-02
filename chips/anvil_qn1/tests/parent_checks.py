"""Executed unchanged-parent reference, not an inherited passing baseline.

The bounded legacy fixture has nonuniform nonzero FP16 embeddings and unit norm
weights, with zero-dequantized affine matrices and zero legacy QKV bias. Hence
both residuals retain the embedding and all causal K/V and contexts are zero.
An integer/rational model independently checks every scratch/KV write and logit.
This intentionally differs from native BF16 nonzero-affine fixtures; its cycles
are a labeled legacy reference, not a speedup or QK-fusion-overhead denominator.
"""

from fractions import Fraction
import hashlib
import json
import math
import re
import struct

from execution import ROOT, relative


PARENT_DRIVER = r"""
#include "Vanvil_q3_top.h"
#include "verilated.h"
#include <algorithm>
#include <array>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

static void check(bool condition,const char* message) {
  if (!condition) throw std::runtime_error(message);
}
static std::vector<uint32_t> image(const std::string& path,size_t count) {
  std::ifstream input(path);
  check(bool(input),"PARENT_IMAGE_OPEN");
  std::vector<uint32_t> result;
  uint32_t value;
  while (input>>std::hex>>value) result.push_back(value);
  check(input.eof() && result.size()==count,"PARENT_IMAGE_SHAPE");
  return result;
}
struct Response { uint64_t tag; uint32_t data; };
int main(int argc,char** argv) {
  try {
    check(argc==2,"PARENT_ARGUMENTS");
    const std::string prefix=argv[1];
    const auto embedding=image(prefix+"/embedding.hex",4*16);
    const auto inputs=image(prefix+"/inputs.hex",6);
    const auto initial=image(prefix+"/initial.hex",6*16);
    const auto normalized=image(prefix+"/normalized.hex",6*16);
    const auto logits=image(prefix+"/logits.hex",6*4);
    Vanvil_q3_top dut;
    dut.clk=0;dut.rst_n=0;dut.cancel=0;dut.token_valid=0;dut.token_id=0;
    dut.token_pos=0;dut.new_sequence=0;dut.token_phase=0;dut.logit_ready=0;
    dut.mem_req_ready=0;dut.mem_rsp_valid=0;dut.mem_rsp_error=0;
    dut.mem_rsp_rdata=0;dut.mem_rsp_tag=0;dut.eval();
    check(!dut.token_ready && !dut.logit_valid && !dut.done && !dut.error,
          "PARENT_RESET");
    for (unsigned i=0;i<3;i++) {
      dut.clk=1;dut.eval();dut.clk=0;dut.eval();
    }
    dut.rst_n=1;dut.eval();
    std::array<uint32_t,15*16> scratch{};
    std::array<bool,15*16> valid{};
    std::array<std::array<uint32_t,16*8>,2> kv{};
    std::array<std::array<bool,16*8>,2> kv_valid{};
    std::vector<Response> queue;
    uint64_t cycle=0,requests=0,writes=0,logit_words=0,active_cycles=0;
    uint64_t bias_reads=0,kv_reads=0,kv_writes=0,projection_mask=0;
    uint64_t request_stalls=0,output_stalls=0,last_logit_cycle=0;
    bool held_req=false,held_logit=false;
    std::array<uint64_t,8> saved_req{};
    uint32_t saved_index=0,saved_logit=0;
    unsigned transaction=0,frame_words=0;
    bool owned=false,submit=false,finished=false;
    while (!finished && cycle<5000000) {
      cycle++;
      dut.clk=0;
      dut.mem_req_ready=(cycle%7)!=3;
      dut.logit_ready=(cycle%9)>=4;
      dut.mem_rsp_valid=!queue.empty();
      dut.mem_rsp_tag=queue.empty() ? 0:queue.front().tag;
      dut.mem_rsp_rdata=queue.empty() ? 0:queue.front().data;
      dut.token_valid=submit;
      dut.token_id=inputs[transaction];dut.token_pos=transaction;
      dut.new_sequence=transaction==0;dut.token_phase=transaction!=0;
      dut.eval();
      if (!owned && !submit && dut.token_ready) {
        submit=true;dut.token_valid=1;dut.eval();
      }
      check(!dut.error && !dut.cancel_done,"PARENT_UNEXPECTED_ERROR");
      const std::array<uint64_t,8> request={dut.mem_req_write,dut.mem_req_kind,
        dut.mem_req_layer,dut.mem_req_proj,dut.mem_req_row,dut.mem_req_col,
        dut.mem_req_wdata,dut.mem_req_tag};
      if (held_req) check(dut.mem_req_valid && request==saved_req,"PARENT_REQUEST_STALL");
      if (held_logit) check(dut.logit_valid && dut.logit_index==saved_index &&
                           dut.logit_data==saved_logit,"PARENT_LOGIT_STALL");
      held_req=dut.mem_req_valid && !dut.mem_req_ready;saved_req=request;
      held_logit=dut.logit_valid && !dut.logit_ready;
      saved_index=dut.logit_index;saved_logit=dut.logit_data;
      request_stalls+=held_req;output_stalls+=held_logit;
      const bool accepted=dut.token_valid && dut.token_ready;
      const bool completed=dut.done;
      if (owned) active_cycles++;
      if (accepted) {
        check(!owned && frame_words==0,"PARENT_DOUBLE_TOKEN");
        owned=true;valid.fill(false);
      }
      if (dut.mem_rsp_valid && dut.mem_rsp_ready) {
        check(!queue.empty(),"PARENT_UNOWNED_RESPONSE");queue.erase(queue.begin());
      }
      if (dut.mem_req_valid && dut.mem_req_ready) {
        check(owned && dut.mem_req_layer==0 && dut.mem_req_col<16,
              "PARENT_REQUEST_BOUNDS");
        uint32_t data=0;
        const uint32_t kind=dut.mem_req_kind,row=dut.mem_req_row,col=dut.mem_req_col;
        if (dut.mem_req_write) {
          writes++;
          if (kind==8) {
            check(row<15,"PARENT_SCRATCH_EXTENT");
            const uint32_t expected=(row==0 || row==7) ? initial[transaction*16+col] :
              (row==1 || row==8 || row==14) ? normalized[transaction*16+col] : 0;
            check(dut.mem_req_wdata==expected,"PARENT_SCRATCH_COMPARE");
            scratch[row*16+col]=dut.mem_req_wdata;valid[row*16+col]=true;
          } else {
            check((kind==9 || kind==10) && row==transaction && col<8,
                  "PARENT_KV_WRITE_ADDRESS");
            check(dut.mem_req_wdata==0 && !kv_valid[kind-9][row*8+col],
                  "PARENT_KV_WRITE_COMPARE");
            kv[kind-9][row*8+col]=dut.mem_req_wdata;
            kv_valid[kind-9][row*8+col]=true;kv_writes++;
          }
        } else {
          switch (kind) {
            case 0:
              check(row<4,"PARENT_EMBEDDING_EXTENT");data=embedding[row*16+col];break;
            case 1:case 2:
              check(dut.mem_req_proj<7 && col<2,"PARENT_PACKED_EXTENT");
              data=0x88888888;projection_mask|=1u<<dut.mem_req_proj;break;
            case 3: data=0x3c00;break;
            case 4: data=0;bias_reads++;break;
            case 5:case 6:case 7:
              check(row==0,"PARENT_GAMMA_ROW");data=0x3c00;break;
            case 8:
              check(row<15 && valid[row*16+col],"PARENT_UNINITIALIZED_SCRATCH");
              data=scratch[row*16+col];break;
            case 9:case 10:
              check(row<=transaction && col<8 && kv_valid[kind-9][row*8+col],
                    "PARENT_CAUSAL_CACHE");
              data=kv[kind-9][row*8+col];kv_reads++;break;
            case 11:
              check(row==transaction && col<8,"PARENT_ROPE_ADDRESS");
              // Zero Q/K makes the legacy Q30 coefficient immaterial, but valid.
              data=(col%2)==0 ? (1u<<30):0;break;
            default: throw std::runtime_error("PARENT_UNSUPPORTED_KIND");
          }
        }
        check(std::none_of(queue.begin(),queue.end(),[&](const Response& response) {
          return response.tag==dut.mem_req_tag;
        }),"PARENT_DUPLICATE_TAG");
        queue.push_back({dut.mem_req_tag,data});requests++;
      }
      if (dut.logit_valid && dut.logit_ready) {
        check(owned && frame_words<4 && dut.logit_index==frame_words &&
          dut.logit_data==logits[transaction*4+frame_words],"PARENT_LOGIT_COMPARE");
        frame_words++;logit_words++;last_logit_cycle=cycle;
      }
      if (completed) {
        check(owned && frame_words==4 && queue.empty() && cycle>last_logit_cycle,
              "PARENT_COMPLETION_ORDER");
        owned=false;frame_words=0;transaction++;
        if (transaction==6) finished=true;
      }
      dut.clk=1;dut.eval();
      if (accepted) submit=false;
    }
    check(finished && projection_mask==127 && bias_reads>0 && kv_reads>0 &&
      kv_writes==6*8*2 && logit_words==24 && request_stalls>0 && output_stalls>0,
      "PARENT_COVERAGE");
    dut.final();
    std::cout << "PARENT_SUMMARY transactions=" << transaction << " logits=" << logit_words
      << " busy_cycles=" << active_cycles << " total_cycles=" << cycle
      << " requests=" << requests << " writes=" << writes << " bias_reads=" << bias_reads
      << " kv_reads=" << kv_reads << " kv_writes=" << kv_writes
      << " projections=" << projection_mask << "\n";
    return 0;
  } catch (const std::exception& error) {
    std::cerr << "FAIL " << error.what() << "\n";return 1;
  }
}
"""


def round_away(value):
    magnitude = abs(value)
    integral = (2 * magnitude.numerator + magnitude.denominator) // (2 * magnitude.denominator)
    return -integral if value < 0 else integral


def parent_vectors():
    embeddings = [[Fraction(((row + 1) * (coordinate + 3)) % 13 - 6, 8)
                   for coordinate in range(16)] for row in range(4)]
    quantized = [[int(value * 65536) for value in row] for row in embeddings]
    normalized = []
    for row in quantized:
        mean_square_q64 = (sum(value * value for value in row) << 32) // 16
        root_q32 = math.isqrt(mean_square_q64 + 18446744073710)
        reciprocal_q32 = (1 << 64) // root_q32
        normalized.append([round_away(Fraction(value * 65536 * reciprocal_q32, 1 << 48))
                           for value in row])
    logits = [[round_away(Fraction(sum(x * weight for x, weight in zip(row, weights)),
                                  65536))
               for weights in quantized] for row in normalized]
    inputs = [3]
    for _ in range(5):
        prediction = max(range(4), key=lambda token: (logits[inputs[-1]][token], -token))
        inputs.append(prediction)
    return embeddings, quantized, normalized, logits, inputs


def run_parent(run):
    references = sorted((ROOT / "anvil_q3_reference" / "rtl").glob("*.sv"))
    if len(references) != 26:
        raise AssertionError("parent inventory changed")
    for source in references:
        delivered = ROOT / "rtl" / source.name
        if source.read_bytes() != delivered.read_bytes():
            raise AssertionError(f"delivered legacy source differs: {source.name}")
    embeddings, quantized, normalized, logits, inputs = parent_vectors()
    images = run.path / "checkpoint-images"
    images.mkdir(exist_ok=False)
    tables = {"embedding": [int.from_bytes(struct.pack("<e", float(value)), "little")
                             for row in embeddings for value in row],
              "inputs": inputs,
              "initial": [value & 0xFFFFFFFF for token in inputs for value in quantized[token]],
              "normalized": [value & 0xFFFFFFFF for token in inputs for value in normalized[token]],
              "logits": [value & 0xFFFFFFFF for token in inputs for value in logits[token]]}
    for name, items in tables.items():
        with (images / f"{name}.hex").open("x") as output:
            output.writelines(f"{value:08x}\n" for value in items)
    driver = run.path / "parent_driver.cpp"
    driver.write_text(PARENT_DRIVER)
    objects = run.path / "obj-parent"
    parameters = {"PROFILE": 2, "NUM_LAYERS": 1, "HIDDEN_SIZE": 16,
                  "INTERMEDIATE_SIZE": 8, "NUM_Q_HEADS": 2, "NUM_KV_HEADS": 1,
                  "HEAD_DIM": 8, "GROUP_SIZE": 8, "VOCAB_SIZE": 4,
                  "MAX_SEQ_LEN": 16, "BANKS": 1, "QUEUE_DEPTH": 3,
                  "TILE_K": 8, "TILE_ROWS": 8, "CACHE_MODE": 0}
    sources = [relative(p) for p in references]
    run.execute(["verilator", "--cc", "--exe", "--build", "-Wno-fatal", "-j", "2",
                 "-CFLAGS", "-O3", "--top-module", "anvil_q3_top",
                 *[f"-G{k}={v}" for k, v in parameters.items()],
                 "--Mdir", relative(objects), "-o", "simulate", *sources,
                 "../parent_driver.cpp"], "parent-compile")
    output = run.execute([relative(objects / "simulate"), relative(images)], "parent-simulation")
    matches = re.findall(
        r"PARENT_SUMMARY transactions=(\d+) logits=(\d+) busy_cycles=(\d+) total_cycles=(\d+) "
        r"requests=(\d+) writes=(\d+) bias_reads=(\d+) kv_reads=(\d+) kv_writes=(\d+) "
        r"projections=(\d+)", output)
    if len(matches) != 1:
        raise AssertionError("missing executed parent comparison record")
    counts = list(map(int, matches[0]))
    if counts[:2] != [6, 24] or counts[2] == 0 or counts[-2:] != [96, 127]:
        raise AssertionError("parent execution coverage mismatch")
    result = {"parameters": parameters, "counts": counts, "inputs": inputs,
              "expected_logits_q16": [logits[token] for token in inputs],
              "arithmetic": "legacy FP16 input, Q16 activation, integer floor sqrt/division, half-away rounding",
              "image": "nonuniform nonzero embeddings, unit gamma, zero-dequantized affine, zero QKV bias",
              "token_counts": {"consumed_inputs": 6, "prefill_frames": 1, "decode_prediction_frames": 5,
                               "generated_commit_bus_transfers": 0},
              "reference_cycles": counts[2],
              "reference_committed_tokens": 6,
              "reference_token_meaning": "six successfully completed/cached input tokens, including prefill; not native generated commits",
              "clock_interpretation": "measured cycles only, not a proven physical 100MHz result",
              "source_sha256": {relative(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in references},
              "comparison_limit": "different native/legacy arithmetic, geometry and affine work; no speedup/parity claim"}
    (run.path / "parent-reference.json").write_text(json.dumps(result, indent=2) + "\n")
    return result
