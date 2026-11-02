"""Parent differential execution; comparison uses transactions, never internal state."""

import random
import struct
import math

from architecture import bf16
from reference import bits32


def compiled_driver(bench, directory, geometry, seed, enable, tokens, precisions, commands):
    """Drive only public pins; keep clocks of the inactive comparator stopped."""
    layers, hidden, intermediate, queries, kvheads, dimension, group, vocab, sequence = geometry
    maximum = max(hidden, intermediate)
    text = bench.read_text()
    instances = text[text.index("  anvil_q1_fp_top #("):text.index("  reg [15:0] values")]
    instances = instances.replace(".clk(clk)", ".clk(clk && !model)", 1)
    start = instances.index("  anvil_q1_fp2_top #(")
    instances = instances[:start] + instances[start:].replace(
        ".clk(clk)", ".clk(clk && model)", 1)
    bench.write_text("""module tb(
  input clk,rst_n,model,new_sequence,logit_ready,
  input [1:0] valid,precision_mode,reqr,rspv,rspe,
  input [31:0] token_id,token_pos,
  input [63:0] rspdata,
  output [1:0] ready,lv,done,error,reqv,reqw,rspr,
  output [63:0] li,ld,reql,reqrow,reqcol,reqwd,
  output [7:0] reqk,
  output [5:0] reqp,
  output ddr_req_valid,ddr_req_write,ddr_req_id,ddr_req_scale,ddr_rsp_ready,
  output [3:0] ddr_req_kind,
  output [2:0] ddr_req_proj,
  output [31:0] ddr_req_layer,ddr_req_row,ddr_req_col,
  output [511:0] ddr_req_wdata,
  output [63:0] ddr_req_wstrb
);
""" + instances[:instances.index("  wire ddr_req_valid")] +
                     instances[instances.index("  anvil_q1_fp2_top #("):] + "\nendmodule\n")
    driver = directory / "driver.cpp"
    code = r"""
#include "Vtb.h"
#include "verilated.h"
#include <algorithm>
#include <array>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

static void require(bool condition, const std::string& message) {
    if (!condition) throw std::runtime_error("COMPATIBILITY " + message);
}
static uint32_t word(uint64_t packed, unsigned model) { return packed >> (32 * model); }
static bool bit(unsigned packed, unsigned model) { return (packed >> model) & 1; }
static void load(const std::string& path, std::vector<uint32_t>& values) {
    std::ifstream stream(path);
    require(bool(stream), "fixture open " + path);
    for (auto& value : values) require(bool(stream >> std::hex >> value), "fixture short " + path);
    std::string extra;
    require(!(stream >> extra), "fixture extra " + path);
}
int main(int argc, char** argv) {
  try {
    VerilatedContext context;
    context.commandArgs(argc, argv);
    Vtb dut(&context);
    std::string fixture;
    uint32_t seed = 0;
    for (int i=1; i<argc; ++i) {
        std::string arg(argv[i]);
        if (arg.rfind("+fixture=",0)==0) fixture=arg.substr(9);
        if (arg.rfind("+seed=",0)==0) seed=std::stoul(arg.substr(6));
    }
    require(!fixture.empty() && seed!=0, "missing fixture/seed arguments");
    constexpr unsigned L=@L@, H=@H@, I=@I@, KV=@KV@, D=@D@, V=@V@, S=@S@, M=@M@;
    constexpr unsigned COMMANDS=@COMMANDS@, TOKENS=@TOKENS@, ENABLE=@ENABLE@;
    const std::vector<unsigned> modes={@MODES@};
    std::vector<uint32_t> values(96), coefficients(2*S*D);
    load(fixture+"/checkpoint-images/values.hex", values);
    load(fixture+"/rope.hex", coefficients);
    std::vector<uint32_t> scratch(15*M), keys(L*S*KV*D), vals(keys.size());
    std::vector<uint32_t> parent_logits(COMMANDS*V);
    std::array<uint64_t,COMMANDS> parent_hash{};
    std::array<unsigned,COMMANDS> parent_counts{}, parent_outputs{};
    std::array<bool,COMMANDS> parent_errors{};
    unsigned model=0, command_index=0, cycle=0, received=0, requests=0, compared=0;
    unsigned command_accepts=0, completion_count=0, remaining=0;
    bool pending=false, held=false, pending_error=false, finished=false, fault=false;
    uint32_t pending_data=0, held_index=0, held_data=0, rng=seed;
    uint64_t hash=0xcbf29ce484222325ULL;
    dut.clk=0; dut.rst_n=0; dut.model=0; dut.valid=0; dut.reqr=0;
    dut.rspv=0; dut.rspe=0; dut.rspdata=0; dut.logit_ready=0;
    dut.new_sequence=0; dut.precision_mode=0; dut.token_id=0; dut.token_pos=0;
    auto read_word = [&](unsigned kind, uint32_t layer, unsigned projection,
                         uint32_t row, uint32_t col) -> uint32_t {
        unsigned address=((row*7+col*3+layer*11+projection*5)&31)+dut.precision_mode*32;
        if (kind==0 || kind==12 || kind==4) return values.at(address);
        if (kind==1) return 0x87654321;
        if (kind==2) return 0x88888888;
        if (kind==3) return 0x00001400;
        if (kind>=5 && kind<=7) return dut.precision_mode==1 ? 0x3f80 : 0x3c00;
        if (kind==8) {
            require(row<15 && col<M, "scratch indexing");
            return scratch.at(row*M+col);
        }
        if (kind==9 || kind==10) {
            require(layer<L && row<S && col<KV*D, "KV indexing");
            return (kind==9 ? keys : vals).at((layer*S+row)*KV*D+col);
        }
        if (kind==11) {
            require(row<S && col<D, "RoPE indexing");
            return coefficients.at((dut.precision_mode!=0 ? S*D : 0)+row*D+col);
        }
        throw std::runtime_error("COMPATIBILITY unknown memory kind");
    };
    auto tick = [&]() {
        require(++cycle<=15000000, "cycle watchdog");
        rng^=rng<<13; rng^=rng>>17; rng^=rng<<5;
        dut.reqr=(!pending && !bit(dut.rspv,model) && cycle%17>=3 && (rng&3)!=0)<<model;
        dut.logit_ready=cycle%19>=4 && ((rng>>1)&7)!=0;
        if (pending && remaining==0 && !bit(dut.rspv,model)) {
            dut.rspv|=1<<model; dut.rspdata=uint64_t(pending_data)<<(model*32);
            dut.rspe=pending_error<<model;
        }
        dut.eval();
        if (model==1) {
            bool unused=dut.ddr_req_valid || dut.ddr_req_write || dut.ddr_req_id ||
                dut.ddr_req_scale || dut.ddr_req_kind || dut.ddr_req_layer ||
                dut.ddr_req_proj || dut.ddr_req_row || dut.ddr_req_col ||
                dut.ddr_req_wstrb;
            for (unsigned i=0;i<16;++i) unused|=dut.ddr_req_wdata[i]!=0;
            require(!unused, "legacy execution used DDR");
        }
        bool ta=bit(dut.valid,model) && bit(dut.ready,model);
        bool ra=bit(dut.reqv,model) && bit(dut.reqr,model);
        bool sa=bit(dut.rspv,model) && bit(dut.rspr,model);
        bool oa=bit(dut.lv,model) && dut.logit_ready;
        uint32_t index=word(dut.li,model), data=word(dut.ld,model);
        require(!held || (bit(dut.lv,model) && index==held_index && data==held_data),
                "output stability");
        held=bit(dut.lv,model) && !dut.logit_ready;
        held_index=index; held_data=data;
        require(!bit(dut.lv,model) || (received<V && index==received), "logit indexing");
        if (oa) {
            if (model==0) parent_logits.at(command_index*V+received)=data;
            else {
                require(data==parent_logits.at(command_index*V+received), "bit-exact logit mismatch");
                ++compared;
            }
            ++received;
        }
        if (bit(dut.done,model)) {
            require(!pending && !bit(dut.rspv,model), "completion ownership");
            if (model==0) {
                parent_hash.at(command_index)=hash; parent_counts.at(command_index)=requests;
                parent_outputs.at(command_index)=received;
                parent_errors.at(command_index)=bit(dut.error,model);
            } else require(hash==parent_hash.at(command_index) &&
                requests==parent_counts.at(command_index) &&
                received==parent_outputs.at(command_index) &&
                bit(dut.error,model)==parent_errors.at(command_index),
                "memory/error/output semantics mismatch command="+std::to_string(command_index));
            ++completion_count; finished=true;
            std::cout<<"PROGRESS compatibility model="<<model<<" command="<<command_index
                <<" cycles="<<cycle<<" requests="<<requests<<" logits="<<received
                <<" error="<<bit(dut.error,model)<<std::endl;
        }
        if (ra) {
            unsigned kind=(dut.reqk>>(model*4))&15, projection=(dut.reqp>>(model*3))&7;
            uint32_t layer=word(dut.reql,model), row=word(dut.reqrow,model);
            uint32_t col=word(dut.reqcol,model), data=word(dut.reqwd,model);
            bool write=bit(dut.reqw,model);
            for (uint64_t field : {uint64_t(kind),uint64_t(layer),uint64_t(projection),
                                  uint64_t(row),uint64_t(col),uint64_t(write)})
                hash=(hash^field)*0x100000001b3ULL;
            if (write) {
                hash=(hash^data)*0x100000001b3ULL;
                if (kind==8 && row<15 && col<M) scratch.at(row*M+col)=data;
                else if ((kind==9 || kind==10) && layer<L && row<S && col<KV*D)
                    (kind==9 ? keys : vals).at((layer*S+row)*KV*D+col)=data;
                else throw std::runtime_error("COMPATIBILITY write indexing");
                pending_data=0;
            } else pending_data=read_word(kind,layer,projection,row,col);
            pending_error=fault && requests==17; ++requests;
        }
        dut.clk=1; context.timeInc(5); dut.eval();
        if (ta) ++command_accepts;
        if (sa) pending=false;
        if (ra) {pending=true; remaining=2+((rng>>4)&3);}
        if (ta) dut.valid&=~(1<<model);
        if (sa) dut.rspv&=~(1<<model);
        if (pending && remaining>0) --remaining;
        dut.eval();
        dut.clk=0; context.timeInc(5); dut.eval();
        if (cycle%1000000==0)
            std::cout<<"PROGRESS compatibility model="<<model<<" command="<<command_index
                <<" cycles="<<cycle<<" requests="<<requests<<" pending="<<pending<<std::endl;
    };
    auto command = [&](uint32_t id, uint32_t pos, bool fresh, unsigned precision) {
        dut.token_id=id; dut.token_pos=pos; dut.new_sequence=fresh; dut.precision_mode=precision;
        received=0; requests=0; hash=0xcbf29ce484222325ULL; finished=false;
        for (unsigned i=0;i<3;++i) tick();
        dut.valid|=1<<model;
        while (bit(dut.valid,model)) tick();
        while (!finished) tick();
        ++command_index; tick(); tick();
        require(bit(dut.ready,model), "did not return idle");
    };
    for (model=0;model<2;++model) {
        dut.rst_n=0; dut.valid=0; dut.rspv=0; dut.reqr=0; pending=false; held=false;
        dut.model=model; dut.eval();
        for (unsigned i=0;i<2;++i) {
            dut.clk=1; dut.eval(); context.timeInc(5);
            dut.clk=0; dut.eval(); context.timeInc(5);
        }
        std::fill(scratch.begin(),scratch.end(),0);
        std::fill(keys.begin(),keys.end(),0); std::fill(vals.begin(),vals.end(),0);
        command_index=0; cycle=0; rng=seed; dut.rst_n=1; dut.eval();
        for (unsigned mode : modes) {
            fault=false;
            for (unsigned pos=0;pos<TOKENS;++pos) command(pos%V,pos,pos==0,mode);
            command(0,0,true,mode);
            if (S>1) command(0,1,false,mode^1);
            fault=true; command(0,0,true,mode); fault=false;
            command(0,S,false,mode);
        }
        if (ENABLE==0) command(0,0,true,3);
        else command(V,0,true,0);
        require(command_index==COMMANDS, "command coverage");
    }
    require(completion_count==COMMANDS*2 && command_accepts==COMMANDS*2 && compared>0,
            "missing comparisons/completions");
    std::cout<<"SUMMARY compatibility: commands="<<completion_count<<" logits="<<compared
        <<" enable="<<ENABLE<<" geometry_h="<<H<<std::endl;
    dut.final();
    return 0;
  } catch (const std::exception& error) {
    std::cerr<<error.what()<<std::endl;
    return 1;
  }
}
"""
    replacements = dict(L=layers, H=hidden, I=intermediate, KV=kvheads, D=dimension,
                        V=vocab, S=sequence, M=maximum, COMMANDS=commands,
                        TOKENS=tokens, ENABLE=enable, MODES=",".join(map(str, precisions)))
    for key, value in replacements.items():
        code = code.replace(f"@{key}@", str(value))
    driver.write_text(code)
    return driver


def simulate_compatibility(run, root, compile_and_run, geometry, seed, enable=0,
                           compact=False, precisions=None):
    requested_geometry = geometry
    if compact:
        geometry = (*geometry[:-2], min(3, geometry[-2]), geometry[-1])
    layers, hidden, intermediate, queries, kvheads, dimension, group, vocab, sequence = geometry
    precisions = tuple(precisions if precisions is not None else
                       (range(3) if enable == 0 else (0,)))
    if not precisions or any(mode not in (range(3) if enable == 0 else (0,))
                             for mode in precisions):
        raise ValueError("unsupported compatibility precision selection")
    stem = f"compatibility-h{hidden}-enable{enable}-{seed}"
    directory = run.path / stem
    directory.mkdir()
    images = directory / "checkpoint-images"
    images.mkdir()
    rng = random.Random(seed)
    words = []
    for precision in range(3):
        for _ in range(32):
            value = rng.choice((-7, -5, -3, -1, 1, 3, 5, 7)) / 64
            words.append(bf16(value) if precision == 1 else
                         int.from_bytes(struct.pack(">e", value), "big"))
    with (images / "values.hex").open("x") as output:
        output.write("".join(f"{word:04x}\n" for word in words))
    coefficients = []
    for native in (False, True):
        for position in range(sequence):
            for col in range(dimension):
                angle = position * 1000000 ** (-2 * (col // 2) / dimension)
                value = math.sin(angle) if col & 1 else math.cos(angle)
                coefficients.append(bits32(value) if native else round(value * 65536) & 0xFFFFFFFF)
    with (directory / "rope.hex").open("x") as output:
        output.write("".join(f"{word:08x}\n" for word in coefficients))
    maximum = max(hidden, intermediate)
    tokens = min(3, sequence) if compact else sequence
    commands = (tokens + 3 + int(sequence > 1)) * len(precisions) + 1
    precision_cases = " ".join(
        f"{index}: mode={precision};" for index, precision in enumerate(precisions))
    bench = directory / "tb.sv"
    bench.write_text(f"""`timescale 1ns/1ps
module tb;
  reg clk=0,rst_n=0,token_valid=0,new_sequence=0,logit_ready=0;
  always #5 clk=~clk;
  reg [31:0] token_id=0,token_pos=0;
  reg [1:0] precision_mode=0;
  reg [1:0] valid=0;
  wire [1:0] ready,lv,done,error,reqv,reqw,rspr;
  wire [63:0] li,ld,reql,reqrow,reqcol,reqwd;
  wire [7:0] reqk;
  wire [5:0] reqp;
  reg [1:0] reqr=0,rspv=0,rspe=0;
  reg [63:0] rspdata=0;
  anvil_q1_fp_top #(
    .NUM_LAYERS({layers}),.HIDDEN_SIZE({hidden}),.INTERMEDIATE_SIZE({intermediate}),
    .NUM_Q_HEADS({queries}),.NUM_KV_HEADS({kvheads}),.HEAD_DIM({dimension}),
    .GROUP_SIZE({group}),.VOCAB_SIZE({vocab}),.MAX_SEQ_LEN({sequence})) parent(
    .clk(clk),.rst_n(rst_n),.token_valid(valid[0]),.token_ready(ready[0]),
    .token_id(token_id),.token_pos(token_pos),.new_sequence(new_sequence),
    .logit_valid(lv[0]),.logit_ready(logit_ready),.logit_index(li[0+:32]),
    .logit_data(ld[0+:32]),.done(done[0]),.error(error[0]),
    .mem_req_valid(reqv[0]),.mem_req_ready(reqr[0]),.mem_req_write(reqw[0]),
    .mem_req_kind(reqk[0+:4]),.mem_req_layer(reql[0+:32]),.mem_req_proj(reqp[0+:3]),
    .mem_req_row(reqrow[0+:32]),.mem_req_col(reqcol[0+:32]),.mem_req_wdata(reqwd[0+:32]),
    .mem_rsp_valid(rspv[0]),.mem_rsp_ready(rspr[0]),.mem_rsp_rdata(rspdata[0+:32]),
    .mem_rsp_error(rspe[0]),.precision_mode(precision_mode));
  wire ddr_req_valid,ddr_req_write,ddr_req_id,ddr_req_scale,ddr_rsp_ready;
  wire [3:0] ddr_req_kind;
  wire [2:0] ddr_req_proj;
  wire [31:0] ddr_req_layer,ddr_req_row,ddr_req_col;
  wire [511:0] ddr_req_wdata;
  wire [63:0] ddr_req_wstrb;
  anvil_q1_fp2_top #(
    .NUM_LAYERS({layers}),.HIDDEN_SIZE({hidden}),.INTERMEDIATE_SIZE({intermediate}),
    .NUM_Q_HEADS({queries}),.NUM_KV_HEADS({kvheads}),.HEAD_DIM({dimension}),
    .GROUP_SIZE({group}),.VOCAB_SIZE({vocab}),.MAX_SEQ_LEN({sequence}),
    .ENABLE_FP2({enable})) fp2(
    .clk(clk),.rst_n(rst_n),.token_valid(valid[1]),.token_ready(ready[1]),
    .token_id(token_id),.token_pos(token_pos),.new_sequence(new_sequence),
    .logit_valid(lv[1]),.logit_ready(logit_ready),.logit_index(li[32+:32]),
    .logit_data(ld[32+:32]),.done(done[1]),.error(error[1]),
    .mem_req_valid(reqv[1]),.mem_req_ready(reqr[1]),.mem_req_write(reqw[1]),
    .mem_req_kind(reqk[4+:4]),.mem_req_layer(reql[32+:32]),.mem_req_proj(reqp[3+:3]),
    .mem_req_row(reqrow[32+:32]),.mem_req_col(reqcol[32+:32]),.mem_req_wdata(reqwd[32+:32]),
    .mem_rsp_valid(rspv[1]),.mem_rsp_ready(rspr[1]),.mem_rsp_rdata(rspdata[32+:32]),
    .mem_rsp_error(rspe[1]),.precision_mode(precision_mode),
    .ddr_req_valid(ddr_req_valid),.ddr_req_ready(1'b1),.ddr_req_write(ddr_req_write),
    .ddr_req_id(ddr_req_id),.ddr_req_scale(ddr_req_scale),.ddr_req_kind(ddr_req_kind),
    .ddr_req_layer(ddr_req_layer),.ddr_req_proj(ddr_req_proj),.ddr_req_row(ddr_req_row),
    .ddr_req_col(ddr_req_col),.ddr_req_wdata(ddr_req_wdata),.ddr_req_wstrb(ddr_req_wstrb),
    .ddr_rsp_valid(1'b0),.ddr_rsp_ready(ddr_rsp_ready),.ddr_rsp_id(1'b0),
    .ddr_rsp_error(1'b0),.ddr_rsp_rdata(512'd0),.csr_req_valid(1'b0),
    .csr_req_ready(),.csr_req_write(1'b0),.csr_req_addr(12'd0),.csr_req_wdata(32'd0),
    .csr_req_wstrb(4'd0),.csr_rsp_ready(1'b1),.csr_rsp_valid(),.csr_rsp_rdata(),
    .csr_rsp_error());
  reg [15:0] values[0:95];
  reg [31:0] coefficients[0:{2*sequence*dimension-1}];
  reg [31:0] scratch[0:{15*maximum-1}];
  reg [31:0] keys[0:{layers*sequence*kvheads*dimension-1}];
  reg [31:0] vals[0:{layers*sequence*kvheads*dimension-1}];
  reg [31:0] parent_logits[0:{commands*vocab-1}];
  reg [63:0] parent_hash[0:{commands-1}];
  integer parent_counts[0:{commands-1}],parent_outputs[0:{commands-1}];
  reg parent_errors[0:{commands-1}];
  integer model=0,command_index=0,cycle=0,received=0,requests=0,compared=0;
  integer command_accepts=0,completion_count=0,remaining=0,position,mode,mode_index,j;
  reg pending=0,held=0;
  reg [31:0] pending_data=0,held_index=0,held_data=0;
  reg pending_error=0,finished=0,fault=0;
  reg [63:0] hash=64'hcbf29ce484222325;
  reg [31:0] rng=0;
  integer seed_value;
  string fixture_root;
  reg ta,ra,sa,oa;
  reg [3:0] kind;
  reg [2:0] projection;
  reg [31:0] layer,row,col,word;
  function [31:0] read_word(input [3:0] kind,input [31:0] layer,
      input [2:0] projection,input [31:0] row,col);
    integer address;
    begin
      address=((row*7+col*3+layer*11+projection*5)&31)+precision_mode*32;
      if (kind==0 || kind==12) read_word={{16'd0,values[address]}};
      else if (kind==1) read_word=32'h87654321;
      else if (kind==2) read_word=32'h88888888;
      else if (kind==3) read_word=32'h00001400;
      else if (kind==4) read_word={{16'd0,values[address]}};
      else if (kind>=5 && kind<=7)
        read_word=precision_mode==1 ? 32'h00003f80 : 32'h00003c00;
      else if (kind==8) begin
        if (row>=15 || col>={maximum}) $fatal(1,"compatibility scratch indexing");
        read_word=scratch[row*{maximum}+col];
      end else if (kind==9 || kind==10) begin
        if (layer>={layers} || row>={sequence} || col>={kvheads*dimension})
          $fatal(1,"compatibility KV indexing");
        address=(layer*{sequence}+row)*{kvheads*dimension}+col;
        read_word=kind==9 ? keys[address] : vals[address];
      end else if (kind==11) begin
        if (row>={sequence} || col>={dimension}) $fatal(1,"compatibility RoPE indexing");
        read_word=coefficients[(precision_mode!=0 ? {sequence*dimension} : 0)+
                               row*{dimension}+col];
      end
      else $fatal(1,"compatibility unknown memory kind");
    end
  endfunction
  task tick;
    begin
      cycle=cycle+1;
      if (cycle>15000000) $fatal(1,"compatibility cycle watchdog");
      rng=rng^(rng<<13); rng=rng^(rng>>17); rng=rng^(rng<<5);
      reqr=0; reqr[model]=!pending && !rspv[model] && cycle%17>=3 && rng[1:0]!=0;
      logit_ready=cycle%19>=4 && rng[3:1]!=0;
      if (pending && remaining==0 && !rspv[model]) begin
        rspv[model]=1; rspdata[model*32+:32]=pending_data; rspe[model]=pending_error;
      end
      #1;
      if ((^{{ready[model],lv[model],done[model],error[model],
          reqv[model],rspr[model]}})===1'bx) $fatal(1,"compatibility active X/Z");
      if (model==1 && {{ddr_req_valid,ddr_req_write,ddr_req_id,ddr_req_scale,
          ddr_req_kind,ddr_req_layer,ddr_req_proj,ddr_req_row,ddr_req_col,
          ddr_req_wdata,ddr_req_wstrb}} !== 0)
        $fatal(1,"legacy execution used DDR");
      ta=valid[model] && ready[model]; ra=reqv[model] && reqr[model];
      sa=rspv[model] && rspr[model]; oa=lv[model] && logit_ready;
      if (held && {{lv[model],li[model*32+:32],ld[model*32+:32]}} !==
          {{1'b1,held_index,held_data}}) $fatal(1,"compatibility output stability");
      held=lv[model] && !logit_ready;
      held_index=li[model*32+:32]; held_data=ld[model*32+:32];
      if (lv[model] && ((^held_data)===1'bx || received>={vocab} ||
          held_index!==received)) $fatal(1,"compatibility logit indexing");
      if (oa) begin
        if (model==0) parent_logits[command_index*{vocab}+received]=held_data;
        else begin
          if (held_data!==parent_logits[command_index*{vocab}+received])
            $fatal(1,"COMPATIBILITY bit-exact logit mismatch");
          compared=compared+1;
        end
        received=received+1;
      end
      if (done[model]) begin
        if (pending || rspv[model]) $fatal(1,"compatibility completion ownership");
        if (model==0) begin
          parent_hash[command_index]=hash; parent_counts[command_index]=requests;
          parent_outputs[command_index]=received; parent_errors[command_index]=error[model];
        end else if (hash!==parent_hash[command_index] ||
            requests!=parent_counts[command_index] ||
            received!=parent_outputs[command_index] ||
            error[model]!==parent_errors[command_index])
          $fatal(1,"COMPATIBILITY memory/error/output semantics mismatch command=%0d",command_index);
        completion_count=completion_count+1; finished=1;
        $display("PROGRESS compatibility model=%0d command=%0d cycles=%0d requests=%0d logits=%0d error=%b",
          model,command_index,cycle,requests,received,error[model]);
      end
      if (ra) begin
        kind=reqk[model*4+:4]; layer=reql[model*32+:32];
        projection=reqp[model*3+:3]; row=reqrow[model*32+:32]; col=reqcol[model*32+:32];
        word=reqwd[model*32+:32];
        if ((^{{kind,layer,projection,row,col,word}})===1'bx)
          $fatal(1,"compatibility request X/Z");
        hash=(hash^{{28'd0,kind}})*64'h100000001b3;
        hash=(hash^layer)*64'h100000001b3;
        hash=(hash^projection)*64'h100000001b3;
        hash=(hash^row)*64'h100000001b3;
        hash=(hash^col)*64'h100000001b3;
        hash=(hash^reqw[model])*64'h100000001b3;
        if (reqw[model]) begin
          hash=(hash^word)*64'h100000001b3;
          if (kind==8 && row<15 && col<{maximum}) scratch[row*{maximum}+col]=word;
          else if ((kind==9 || kind==10) && layer<{layers} &&
              row<{sequence} && col<{kvheads*dimension}) begin
            if (kind==9) keys[(layer*{sequence}+row)*{kvheads*dimension}+col]=word;
            else vals[(layer*{sequence}+row)*{kvheads*dimension}+col]=word;
          end else $fatal(1,"compatibility write indexing");
          pending_data=0;
        end else pending_data=read_word(kind,layer,projection,row,col);
        pending_error=fault && requests==17;
        requests=requests+1;
      end
      @(posedge clk);
      if (ta) command_accepts=command_accepts+1;
      if (sa) pending=0;
      if (ra) begin pending=1; remaining=2+rng[5:4]; end
      #1;
      if (ta) valid[model]=0;
      if (sa) rspv[model]=0;
      if (pending && remaining>0) remaining=remaining-1;
      @(negedge clk);
    end
  endtask
  task command(input [31:0] id,pos,input fresh,input [1:0] precision);
    begin
      token_id=id; token_pos=pos; new_sequence=fresh; precision_mode=precision;
      received=0; requests=0; hash=64'hcbf29ce484222325; finished=0;
      repeat(3) tick();
      valid[model]=1;
      while (valid[model]) tick();
      while (!finished) tick();
      command_index=command_index+1;
      tick(); tick();
      if (!ready[model]) $fatal(1,"compatibility did not return idle");
    end
  endtask
  initial begin
    if (!$value$plusargs("fixture=%s",fixture_root) ||
        !$value$plusargs("seed=%d",seed_value)) $fatal(1,"compatibility missing arguments");
    $readmemh({{fixture_root,"/checkpoint-images/values.hex"}},values);
    $readmemh({{fixture_root,"/rope.hex"}},coefficients);
    for (model=0;model<2;model=model+1) begin
      rst_n=0; valid=0; rspv=0; reqr=0; pending=0; held=0;
      repeat(2) @(posedge clk); @(negedge clk);
      for (j=0;j<{15*maximum};j=j+1) scratch[j]=0;
      for (j=0;j<{layers*sequence*kvheads*dimension};j=j+1) begin keys[j]=0; vals[j]=0; end
      command_index=0; cycle=0; rng=seed_value; rst_n=1; #1;
      for (mode_index=0;mode_index<{len(precisions)};mode_index=mode_index+1) begin
        case (mode_index) {precision_cases} default: $fatal(1,"precision matrix"); endcase
        fault=0;
        for (position=0;position<{tokens};position=position+1)
          command(position%{vocab},position,position==0,mode[1:0]);
        command(0,0,1,mode[1:0]);
        {"command(0,1,0,mode[1:0]^2'd1);" if sequence > 1 else ""}
        fault=1; command(0,0,1,mode[1:0]); fault=0;
        command(0,{sequence},0,mode[1:0]);
      end
      {"command(0,0,1,2'd3);" if enable == 0 else f"command({vocab},0,1,2'd0);"}
      if (command_index!={commands}) $fatal(1,"compatibility command coverage");
    end
    if (completion_count!={commands*2} || command_accepts!={commands*2} || compared==0)
      $fatal(1,"compatibility missing comparisons/completions");
    $display("SUMMARY compatibility: commands=%0d logits=%0d enable={enable} geometry_h={hidden}",
      completion_count,compared);
    $finish;
  end
endmodule
""")
    sources = [str(path.relative_to(root)) for pattern in (
        "anvil_q1_fp_reference/rtl/*.sv", "rtl/*.sv") for path in sorted(root.glob(pattern))]
    driver = compiled_driver(bench, directory, geometry, seed, enable, tokens, precisions, commands)
    compile_and_run(run, directory, bench, sources, "verilator", stem,
                    arguments=[f"+fixture={run.relative / stem}", f"+seed={seed}"], cache=True,
                    driver=driver)
    run.receipt["comparisons"].append({
        "kind": "compatibility", "seed": seed, "geometry": requested_geometry,
        "executed_geometry": geometry, "enable_fp2": enable,
        "commands_per_implementation": commands, "successive_tokens": tokens,
        "precisions": list(precisions),
        "checks": ["bit-exact logits", "memory transaction hash/count", "error semantics",
                   "fresh sequences", "continuations", "fault termination", "invalid position",
                   "maximum legal compact position",
                   *(["precision change rejection"] if sequence > 1 else []),
                   "precision 3 rejection" if enable == 0 else "invalid token rejection",
                   "output stalls", "request/response stalls"],
        "result": "passed",
    })
