"""Production-shaped layer transactions and measured normalization-only delta.

The measurement ends at the next layer's first scratch read, before that request
transfers. It includes the entire first layer and its acknowledged writes, but
neither a vocabulary projection nor deliberately added memory/backpressure time.
"""

from fractions import Fraction
import difflib
import hashlib
import json
import re

from execution import ROOT, relative
from model import Geometry, rmsnorm, residual
import reference as fp


PROFILES = {
    1: Geometry(hidden=1024, intermediate=3072, q_heads=16, kv_heads=8,
                head_dim=128, layers=28, vocabulary=151936,
                max_sequence=40960, group=128),
    2: Geometry(hidden=2048, intermediate=6144, q_heads=16, kv_heads=8,
                head_dim=128, layers=28, vocabulary=151936,
                max_sequence=40960, group=128),
    3: Geometry(hidden=2560, intermediate=9728, q_heads=32, kv_heads=8,
                head_dim=128, layers=36, vocabulary=151936,
                max_sequence=40960, group=128),
}


def gamma(kind, coordinate):
    return fp.encode(Fraction(96 + (kind * 3 + coordinate * 5) % 65, 128), 16)


def layer_reference(g, normalization=True):
    """Periodicity reduces oracle cost, never hardware work or reduction length."""
    cache = {}

    def product(a, b):
        key = (a, b)
        if key not in cache:
            cache[key] = fp.multiply(a, b)
        return cache[key]

    def linear(projection, activation):
        inputs, outputs = g.extents(projection)
        assert inputs == len(activation)
        rows = []
        for row in range(min(outputs, 21)):
            accumulator = 0
            for base in range(0, inputs, 256):
                products = []
                for coordinate in range(base, min(base + 256, inputs)):
                    delta = (coordinate * 3 + row * 5 + projection * 2) % 7 - 3
                    scale = fp.encode(Fraction(
                        1 + (coordinate // g.group + row + projection) % 3, 1024), 16)
                    weight = product(fp.encode(delta), scale << 16)
                    products.append(product(weight, activation[coordinate] << 16))
                products.extend([0] * (256 - len(products)))
                accumulator = fp.add(accumulator, fp.balanced_sum(products))
            rows.append(fp.bf16(accumulator))
        return [rows[row % 21] for row in range(outputs)]

    initial = [fp.encode(Fraction(1 + coordinate % 8, 128), 16)
               for coordinate in range(g.hidden)]
    scratch = {1: rmsnorm(initial, [gamma(5, i) for i in range(g.hidden)])}
    cosine, sine = fp.coefficients(g.head_dim, 0)
    for projection, slot, heads, kind in ((0, 2, g.q_heads, 12),
                                          (1, 3, g.kv_heads, 13)):
        raw = linear(projection, scratch[1])
        scratch[slot] = []
        for head in range(heads):
            data = raw[head * g.head_dim:(head + 1) * g.head_dim]
            if normalization:
                data = fp.qknorm(data, [gamma(kind, i) for i in range(g.head_dim)],
                                 cosine, sine, 0)
            else:
                data = rotate(data, cosine, sine)
            scratch[slot].extend(data)
    scratch[4] = linear(2, scratch[1])
    # At p=0 the exact softmax contains one weight of one for each GQA head.
    scratch[5] = [
        scratch[4][(head // (g.q_heads // g.kv_heads)) * g.head_dim + coordinate]
        for head in range(g.q_heads) for coordinate in range(g.head_dim)]
    scratch[6] = linear(3, scratch[5])
    scratch[7] = residual(initial, scratch[6])
    scratch[8] = rmsnorm(scratch[7], [gamma(6, i) for i in range(g.hidden)])
    scratch[9] = linear(4, scratch[8])
    scratch[10] = linear(5, scratch[8])
    silu = [fp.bf16(fp.silu32(value << 16)) for value in scratch[9]]
    scratch[11] = [fp.bf16(product(a << 16, b << 16))
                   for a, b in zip(silu, scratch[10])]
    scratch[12] = linear(6, scratch[11])
    scratch[0] = residual(scratch[7], scratch[12])
    if any(not values or all(value == 0 for value in values)
           for values in scratch.values()):
        raise AssertionError("production fixture lost a nontrivial layer stage")
    return initial, scratch


def rotate(data, cosine, sine):
    half = len(data) // 2
    result = [0] * len(data)
    for i, (c, s) in enumerate(zip(cosine, sine)):
        x, y = data[i] << 16, data[i + half] << 16
        result[i] = fp.bf16(fp.subtract(fp.multiply(x, c << 16),
                                       fp.multiply(y, s << 16)))
        result[i + half] = fp.bf16(fp.add(fp.multiply(x, s << 16),
                                         fp.multiply(y, c << 16)))
    return result


def rope_only_source():
    """Experimental clone: remove normalization, retain the real rotary pipeline."""
    original = (ROOT / "rtl/anvil_qn1_qknorm_rope.sv").read_text()
    header = original[:original.index("  import anvil_qn1_pkg::*;")]
    rotary = original[original.index("    for (pair_index=0;"):
                      original.rindex("  end endgenerate")]
    rotary = rotary.replace("normalized_head[", "captured[")
    rotary = rotary.replace(
        "normalized_failed[pair_index] || normalized_failed[pair_index+SH]",
        "head_failed")
    return header + r"""
  import anvil_qn1_pkg::*;
  reg owned, result_valid, result_failed, key_vector, head_failed;
  reg [7:0] age;
  reg [5:0] head;
  reg [31:0] layer, position;
  reg [SD*16-1:0] captured, result_data;
  reg [SH*16-1:0] cosine, sine;
  wire [SD-1:0] invalid_element;
  wire [SH-1:0] invalid_coefficient;
  wire [SD*16-1:0] rounded_output;
  wire [SD-1:0] rotated_failed;
  wire invalid_head=(|invalid_element) || (|invalid_coefficient) ||
    in_layer>=NUM_LAYERS || in_pos>=MAX_SEQ_LEN ||
    (in_is_key ? in_head>=NUM_KV_HEADS : in_head>=NUM_Q_HEADS);
  assign in_ready=rst_n && !flush && !owned;
  assign out_valid=rst_n && !flush && result_valid;
  assign out_error=out_valid && result_failed;
  assign out_is_key=out_valid && key_vector;
  assign out_head=out_valid ? head : 6'd0;
  assign out_layer=out_valid ? layer : 32'd0;
  assign out_pos=out_valid ? position : 32'd0;
  assign out_data=out_valid ? result_data : {SD*16{1'b0}};
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      owned<=0; result_valid<=0; result_failed<=0; key_vector<=0; head_failed<=0;
      age<=0; head<=0; layer<=0; position<=0; captured<=0;
      cosine<=0; sine<=0; result_data<=0;
    end else if (flush) begin
      owned<=0; result_valid<=0; result_failed<=0; head_failed<=0;
      age<=0; result_data<=0;
    end else begin
      if (in_valid && in_ready) begin
        owned<=1; age<=0; head_failed<=invalid_head; captured<=in_data;
        cosine<=in_pos==0 ? {SH{16'h3f80}} : in_cos;
        sine<=in_pos==0 ? {SH{16'h0000}} : in_sin;
        key_vector<=in_is_key; head<=in_head; layer<=in_layer; position<=in_pos;
      end
      if (owned && !result_valid) begin
        age<=age+1'b1;
        if (age==9) begin
          result_valid<=1;
          result_failed<=head_failed || (|rotated_failed);
          result_data<=head_failed || (|rotated_failed) ? {SD*16{1'b0}} : rounded_output;
        end
      end
      if (out_valid && out_ready) begin
        owned<=0; result_valid<=0; result_failed<=0; age<=0;
      end
    end
  end
  genvar i, pair_index;
  generate
    for (i=0;i<SD;i=i+1) begin: validate_input
      assign invalid_element[i]=bf16_invalid(in_data[i*16+:16]) ||
        bf16_invalid(in_gamma[i*16+:16]);
    end
""" + rotary + "  endgenerate\nendmodule\n"


LAYER_DRIVER = r"""
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
using U=uint32_t;
using L=uint64_t;
static void check(bool ok,const std::string& message) {
  if (!ok) throw std::runtime_error(message);
}
static std::vector<U> load(const std::string& path) {
  std::ifstream input(path);check(bool(input),"missing image "+path);
  std::vector<U> result;U value;
  while (input>>std::hex>>value) result.push_back(value);
  check(input.eof(),"invalid image "+path);return result;
}
struct Response { L tag; U data; };
int main(int argc,char** argv) {
  try {
    check(argc==9,"layer driver arguments");
    const std::string images=argv[1];
    const U H=std::stoul(argv[2]),I=std::stoul(argv[3]),QH=std::stoul(argv[4]);
    const U KH=std::stoul(argv[5]),D=std::stoul(argv[6]),G=std::stoul(argv[7]);
    const U threads=std::stoul(argv[8]);
    const U QD=QH*D,KD=KH*D,MAX=std::max(I,std::max(H,QD));
    const std::array<U,7> inputs={H,H,H,QD,H,H,I};
    const std::array<U,7> outputs={QD,KD,KD,H,I,I,H};
    auto expected=load(images+"/scratch.hex"),initial=load(images+"/initial.hex");
    auto gamma=load(images+"/gamma.hex");
    check(expected.size()==15*MAX && initial.size()==H &&
          gamma.size()==16*MAX,"reference image shapes");
    std::vector<U> scratch(15*MAX),keys(KD),values(KD),writes(15*MAX);
    std::vector<bool> valid(15*MAX),key_valid(KD),value_valid(KD);
    std::array<std::deque<Response>,8> pending;
    std::array<std::array<L,4>,7> projection_reads{};
    std::array<L,16> kind_reads{};
    L cycles=0,requests=0,compared=0,key_writes=0,value_writes=0;
    L accepted_cycle=0,last_write_response=0;
    const std::array<U,8> shifts={0,16,4,20,8,24,12,28};
    auto context=std::make_unique<VerilatedContext>();
    context->threads(threads);
    auto dut=std::make_unique<Vanvil_qn1_top>(context.get());
    dut->clk=0;dut->rst_n=0;dut->cancel=0;dut->token_valid=0;
    dut->new_sequence=0;dut->token_phase=0;dut->token_id=3;dut->token_pos=0;
    dut->logit_ready=1;dut->commit_ready=1;dut->draft_valid=0;
    dut->draft_count=0;dut->draft_parents=0;dut->draft_tokens=VlWide<4>{};
    dut->csr_valid=0;dut->csr_write=0;dut->csr_addr=0;dut->csr_wdata=0;
    dut->csr_wstrb=0;dut->csr_rsp_ready=1;
    dut->mem_req_ready=255;dut->mem_rsp_valid=0;dut->mem_rsp_error=0;
    for (unsigned b=0;b<8;++b) {
      dut->mem_rsp_rdata[b]=0;dut->mem_rsp_tag[2*b]=0;dut->mem_rsp_tag[2*b+1]=0;
    }
    dut->eval();
    check(!dut->token_ready && !dut->mem_req_valid && !dut->logit_valid &&
          !dut->done && !dut->error && !dut->commit_valid && !dut->think_active,
          "layer reset outputs");
    auto edge=[&] {
      dut->clk=1;dut->eval();context->timeInc(5);
      dut->clk=0;dut->eval();context->timeInc(5);
    };
    edge();edge();dut->rst_n=1;dut->eval();
    bool started=false,finished=false;
    auto last_progress=std::chrono::steady_clock::now();
    while (!finished) {
      dut->token_valid=!started;dut->new_sequence=!started;
      dut->mem_rsp_valid=0;
      for (unsigned b=0;b<8;++b) if (!pending[b].empty()) {
        dut->mem_rsp_valid|=1U<<b;
        dut->mem_rsp_rdata[b]=pending[b].front().data;
        dut->mem_rsp_tag[2*b]=U(pending[b].front().tag);
        dut->mem_rsp_tag[2*b+1]=U(pending[b].front().tag>>32);
      }
      dut->eval();
      check(!dut->error && !dut->cancel_done && !dut->done &&
            !dut->logit_valid && !dut->commit_valid && !dut->draft_ready,
            "unexpected layer status cycle="+std::to_string(cycles));
      if (dut->token_valid && dut->token_ready) {
        check(!started,"duplicate input acceptance");started=true;accepted_cycle=cycles;
      }
      for (unsigned b=0;b<8;++b) {
        if ((dut->mem_rsp_valid & dut->mem_rsp_ready) & (1U<<b)) {
          check(!pending[b].empty(),"unowned memory response");
          pending[b].pop_front();last_write_response=cycles;
        }
      }
      for (unsigned b=0;b<8;++b) if (dut->mem_req_valid & (1U<<b)) {
        U kind=(dut->mem_req_kind>>(4*b))&15,proj=(dut->mem_req_proj>>(3*b))&7;
        U layer=dut->mem_req_layer[b],row=dut->mem_req_row[b],col=dut->mem_req_col[b];
        U data=0;bool write=dut->mem_req_write & (1U<<b);
        if (!write && kind==8 && row==0 && col==0 && writes[H-1]==2) {
          for (const auto& queue:pending) check(queue.empty(),"unsettled layer boundary");
          check(cycles>last_write_response,"layer boundary preceded settlement");
          finished=true;break;
        }
        check(layer==0,"layer address before layer completion");
        check(col<MAX,"memory column bound");
        if (write) {
          U got=dut->mem_req_wdata[b];
          check((got>>16)==0,"write reserved payload");
          if (kind==8) {
            check(row<13 && col<(row==2 || row==5 ? QD:
                  row==3 || row==4 ? KD:row==9 || row==10 || row==11 ? I:H),
                  "scratch write extent");
            U a=row*MAX+col;
            U want=row==0 && writes[a]==0 ? initial[col]:expected[a];
            check(got==want,"LAYER_WRITE_COMPARE slot="+std::to_string(row)+
                  " coordinate="+std::to_string(col)+" got="+std::to_string(got)+
                  " expected="+std::to_string(want));
            check(writes[a]<(row==0 ? 2U:1U),"duplicate scratch write");
            scratch[a]=got;valid[a]=true;++writes[a];++compared;
          } else {
            check((kind==9 || kind==10) && row==0 && col<KD,"KV write address");
            auto& seen=kind==9 ? key_valid:value_valid;
            auto& storage=kind==9 ? keys:values;
            check(!seen[col],"duplicate KV position");
            check(got==expected[(kind==9 ? 3:4)*MAX+col],"LAYER_KV_COMPARE");
            seen[col]=true;storage[col]=got;
            if (kind==9) ++key_writes;else ++value_writes;
            ++compared;
          }
        } else {
          ++kind_reads[kind];
          switch (kind) {
            case 0:
              check(row==3 && col<H,"input embedding address");data=initial[col];break;
            case 1:case 2:case 3: {
              check(proj<7,"projection ID");
              check(kind==1 ? row<inputs[proj]:row<inputs[proj]/G,
                    "projection input/group extent");
              check(kind==3 ? col<outputs[proj]:col<(outputs[proj]+7)/8,
                    "projection output extent");
              ++projection_reads[proj][kind];
              if (kind==3) {
                const std::array<U,3> scales={0x3a80,0x3b00,0x3b40};
                data=scales[(row+col+proj)%3];
              } else for (U lane=0;lane<8;++lane) {
                U output=col*8+lane;
                U q=kind==2 ? 8:8+(row*3+output*5+proj*2)%7-3;
                data|=q<<shifts[lane];
              }
              break;
            }
            case 5:case 6:case 12:case 13:
              check(row==0 && col<(kind>=12 ? D:H),"norm gamma address");
              data=gamma[kind*MAX+col];break;
            case 8: {
              check(row<13 && valid[row*MAX+col],"uninitialized scratch read");
              data=scratch[row*MAX+col];break;
            }
            case 9:case 10:
              check(row==0 && col<KD && (kind==9 ? key_valid[col]:value_valid[col]),
                    "uninitialized/uncaused KV read");
              data=kind==9 ? keys[col]:values[col];break;
            case 11:
              check(row==0 && col<D,"RoPE address");
              data=col%2 ? 0:0x3f80;break;
            default: throw std::runtime_error("forbidden layer memory kind");
          }
        }
        L tag=L(dut->mem_req_tag[2*b])|(L(dut->mem_req_tag[2*b+1])<<32);
        for (const auto& queue:pending) for (const auto& item:queue)
          check(item.tag!=tag,"duplicate outstanding bank tag");
        pending[b].push_back({tag,data});++requests;
      }
      if (finished) break;
      edge();++cycles;
      if ((cycles&4095)==0 && std::chrono::steady_clock::now()-last_progress>
          std::chrono::seconds(30)) {
        std::cout<<"LAYER_PROGRESS cycles="<<cycles<<" requests="<<requests
          <<" compared_writes="<<compared<<std::endl;
        last_progress=std::chrono::steady_clock::now();
      }
    }
    check(started && cycles>accepted_cycle && key_writes==KD && value_writes==KD,
          "layer input/KV coverage");
    for (U slot=0;slot<13;++slot) {
      U extent=slot==2 || slot==5 ? QD:slot==3 || slot==4 ? KD:
        slot==9 || slot==10 || slot==11 ? I:H;
      for (U col=0;col<extent;++col)
        check(writes[slot*MAX+col]==(slot==0 ? 2U:1U),"missing layer write");
    }
    for (U p=0;p<7;++p) {
      check(projection_reads[p][1]==L(inputs[p])*outputs[p] &&
            projection_reads[p][2]==L(inputs[p]/G)*outputs[p] &&
            projection_reads[p][3]==L(inputs[p]/G)*outputs[p],
            "incomplete projection extent p="+std::to_string(p));
    }
    check(kind_reads[5]==H && kind_reads[6]==H &&
          kind_reads[12]==D && kind_reads[13]==D && kind_reads[11]==D,
          "missing normalization/rotary reads");
    std::cout<<"LAYER_SUMMARY cycles="<<cycles-accepted_cycle
      <<" requests="<<requests<<" compared_writes="<<compared
      <<" key_writes="<<key_writes<<" value_writes="<<value_writes<<std::endl;
    dut->final();return 0;
  } catch (const std::exception& error) {
    std::cerr<<error.what()<<std::endl;return 1;
  }
}
"""


def run_layer(run, profile=1, normalization=True, compact=False, threads=1):
    g = (Geometry(layers=2, vocabulary=8) if compact else PROFILES[profile])
    initial, scratch = layer_reference(g, normalization)
    images = run.path / "checkpoint-images"
    images.mkdir(exist_ok=False)
    flat = [0] * (15 * g.maximum)
    for slot, data in scratch.items():
        flat[slot * g.maximum:slot * g.maximum + len(data)] = data
    tables = {"initial": initial, "scratch": flat,
              "gamma": [gamma(kind, col) if kind in (5, 6, 12, 13) else 0
                        for kind in range(16) for col in range(g.maximum)]}
    image_hashes = {}
    for name, values in tables.items():
        path = images / f"{name}.hex"
        path.write_text("".join(f"{value:08x}\n" for value in values))
        image_hashes[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    driver = run.path / "layer_driver.cpp"
    driver.write_text(LAYER_DRIVER)
    sources = [relative(p) for p in sorted((ROOT / "rtl").glob("anvil_qn1_*.sv"))]
    if not normalization:
        path = run.path / "anvil_qn1_qknorm_rope.sv"
        path.write_text(rope_only_source())
        original = ROOT / "rtl/anvil_qn1_qknorm_rope.sv"
        delta = "".join(difflib.unified_diff(
            original.read_text().splitlines(True), path.read_text().splitlines(True),
            fromfile="rtl/anvil_qn1_qknorm_rope.sv", tofile=relative(path)))
        (run.path / "normalization-only.delta").write_text(delta)
        sources[sources.index(relative(original))] = relative(path)
    parameters = {"PROFILE": profile, "COMPACT": int(compact), "BANKS": 8,
                  "NUM_LAYERS": g.layers, "HIDDEN_SIZE": g.hidden,
                  "INTERMEDIATE_SIZE": g.intermediate, "NUM_Q_HEADS": g.q_heads,
                  "NUM_KV_HEADS": g.kv_heads, "HEAD_DIM": g.head_dim,
                  "VOCAB_SIZE": g.vocabulary, "MAX_SEQ_LEN": g.max_sequence,
                  "GROUP_SIZE": g.group}
    objects = run.path / "obj-layer"
    run.execute(["verilator", "--cc", "--exe", "--build", "-Wno-fatal",
                 "-j", "2", "--threads", str(threads),
                 "-CFLAGS", "-O3", "--top-module", "anvil_qn1_top",
                 *[f"-G{k}={v}" for k, v in parameters.items()],
                 "--Mdir", relative(objects), "-o", "simulate", *sources,
                 "../layer_driver.cpp"], "layer-compile")
    output = run.execute([relative(objects / "simulate"), relative(images),
                          str(g.hidden), str(g.intermediate), str(g.q_heads),
                          str(g.kv_heads), str(g.head_dim), str(g.group), str(threads)],
                         "layer-simulation")
    records = re.findall(r"^LAYER_SUMMARY cycles=(\d+) requests=(\d+) "
                         r"compared_writes=(\d+) key_writes=(\d+) "
                         r"value_writes=(\d+)$", output, re.M)
    if len(records) != 1:
        raise AssertionError("missing/duplicate complete layer record")
    cycles, requests, compared, keys, values = map(int, records[0])
    expected_writes = (7 * g.hidden + 2 * g.q_dimension +
                       4 * g.kv_dimension + 3 * g.intermediate)
    if compared != expected_writes or keys != g.kv_dimension or values != g.kv_dimension:
        raise AssertionError(f"layer comparison coverage: {compared} != {expected_writes}")
    result = {"profile": profile, "geometry": vars(g), "normalization": normalization,
              "cycles": cycles, "requests": requests, "compared_writes": compared,
              "key_writes": keys, "value_writes": values, "image_sha256": image_hashes,
              "compact_diagnostic": compact, "parameters": parameters,
              "simulation_threads": threads,
              "scope": "one real decoder layer, all seven projections and two residuals",
              "measurement": "token acceptance to first unaccepted next-layer scratch read",
              "memory": "eager-ready, one-cycle external tagged responses, eight banks"}
    (run.path / "layer-reference.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def run_fusion_profile(run, profile=1, compact=False):
    fused = run.component(f"layer-fused-profile{profile}",
                          lambda child: run_layer(child, profile, compact=compact))
    baseline = run.component(f"layer-rope-only-profile{profile}",
                             lambda child: run_layer(child, profile, False, compact))
    if baseline["cycles"] <= 0 or fused["requests"] != baseline["requests"]:
        raise AssertionError("fusion comparison changed memory work")
    difference = fused["cycles"] - baseline["cycles"]
    if not compact and 100 * difference >= 2 * baseline["cycles"]:
        raise AssertionError(f"fusion overhead >=2%: fused={fused['cycles']}, "
                             f"without_norm={baseline['cycles']}")
    return {"profile": profile, "fused": fused, "without_norm": baseline,
            "extra_cycles": difference,
            "overhead_percent": 100 * difference / baseline["cycles"],
            "threshold_percent_strict": 2, "compact_diagnostic": compact}
