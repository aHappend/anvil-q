"""Compact public-memory/logit oracle. No DUT-internal assertions."""

import json
import re

from execution import ROOT, compiled, icarus, relative, run_compiled
from model import Fixture, FP64Fixture
from metrics import compare


def key_bits(key):
    kind, layer, projection, row, column = key
    return (kind << 99) | (layer << 67) | (projection << 64) | (row << 32) | column


def smoke(evidence, seed=17, simulator="verilator", banks=1, fmt="bf16", awq=False, tokens=1,
          mode=0, fp8=0, affine=0, layers=1, heads=8, head_dim=2,
          intermediate=24, vocab=3, queue_depth=3, tile_k=8, tile_rows=3,
          max_seq_len=4, awq_transition=False):
    if simulator == "iverilog" and (tokens > 1 or heads * head_dim >= 64 or layers > 1):
        portability_smoke = smoke(evidence, seed, "iverilog", banks, fmt, awq, 1)
        substantive = smoke(evidence, seed, "verilator", banks, fmt, awq, tokens,
                            mode, fp8, affine, layers, heads, head_dim, intermediate,
                            vocab, queue_depth, tile_k, tile_rows, max_seq_len, awq_transition)
        return {"icarus_compact_smoke": portability_smoke, "requested_workload": substantive}
    config = dict(seed=seed, fmt=fmt, awq=awq, cache_mode=mode, fp8=fp8, affine=affine,
                  layers=layers, heads=heads, kv_heads=heads // 8, head_dim=head_dim,
                  hidden=heads * head_dim, intermediate=intermediate, vocab=vocab)
    if awq_transition and (awq or tokens < 2):
        raise ValueError("Native-to-AWQ transition requires an initially native multi-token run")
    fixture = Fixture(**config)
    fp64 = FP64Fixture(**config)
    initial = dict(fixture.memory)
    second_image = None
    awq_image = Fixture(**{**config, "awq": True}) if awq_transition else None
    for position in range(tokens):
        if awq_transition and position == 1:
            for model in (fixture, fp64):
                model.weights = awq_image.weights
                model.memory.update({key: value for key, value in awq_image.memory.items() if key[0] in (1, 2, 3)})
            second_image = dict(fixture.memory)
        fixture.token(token=position % fixture.vocab, position=position)
        fp64.token(token=position % fixture.vocab, position=position)
    initial.update({key: value for key, value in fixture.memory.items() if key[0] == 11})
    if second_image is not None:
        second_image = {key: value for key, value in second_image.items() if key[0] != 8 and key[0] not in (9, 10, 12, 13, 14, 15)}
        second_image.update({key: value for key, value in fixture.memory.items() if key[0] == 11})
    text = f"{int(fmt == 'fp16')} {int(awq)} {tokens} {int(awq_transition)}\n"
    text += "".join(f"0 {key_bits(key):026x} {value:08x}\n" for key, value in sorted(initial.items()))
    if second_image is not None:
        text += "".join(f"3 {key_bits(key):026x} {value:08x}\n" for key, value in sorted(second_image.items()))
    text += "".join(f"1 {key_bits(key):026x} {value:08x}\n" for key, value in fixture.writes)
    text += "".join(f"2 {index:026x} {value:08x}\n"
                    for index, value in enumerate(value for token in fixture.logits for value in token))
    rtl = [relative(path) for path in sorted((ROOT / "rtl").glob("*.sv"))]
    rtl += ["anvil_q3_reference/rtl/anvil_q3_bank_scheduler.sv",
            "anvil_q3_reference/rtl/anvil_q3_mem_port.sv"]
    parameters = dict(NUM_LAYERS=layers, HIDDEN_SIZE=fixture.h, INTERMEDIATE_SIZE=intermediate,
                      NUM_Q_HEADS=heads, NUM_KV_HEADS=heads // 8, HEAD_DIM=head_dim,
                      GROUP_SIZE=8, VOCAB_SIZE=vocab, MAX_SEQ_LEN=max_seq_len, BANKS="B",
                      CACHE_MODE=mode, MODE1_FP8=fp8, INT4_ASYM=affine,
                      QUEUE_DEPTH=queue_depth, TILE_K=tile_k, TILE_ROWS=tile_rows)
    tb = TOP_TB.replace("localparam B=1;", f"localparam B={banks}, VOCAB={vocab};")
    tb = tb.replace("localparam C_MODE=0,C_H=16,C_I=24,C_KV=2,C_D=2;",
                    f"localparam C_MODE={mode},C_H={fixture.h},C_I={intermediate},"
                    f"C_KV={heads // 8 * head_dim},C_D={head_dim};")
    tb = re.sub(r"anvil_q3_fp_top #\([\s\S]*?\) dut", "anvil_q3_fp_top #(" +
                ",".join(f".{key}({value})" for key, value in parameters.items()) + ") dut", tb)
    name = (f"top-b{banks}-m{mode}-f{fp8}-a{affine}-l{layers}-h{fixture.h}"
            f"-{fmt}-w{int(awq)}-s{seed}-n{tokens}-q{queue_depth}-k{tile_k}-r{tile_rows}-v{vocab}")
    if awq_transition:
        name += "-transition"
    image_count = len(initial) + (len(second_image) if second_image is not None else 0)
    memory_capacity = max(262144, image_count)
    write_capacity = max(262144, len(fixture.writes))
    tb = tb.replace("memory_key[0:262143],expected_key[0:262143]",
                    f"memory_key[0:{memory_capacity - 1}],expected_key[0:{write_capacity - 1}]")
    tb = tb.replace("memory_data[0:262143],expected_data[0:262143]",
                    f"memory_data[0:{memory_capacity - 1}],expected_data[0:{write_capacity - 1}]")
    tb = tb.replace("used[0:262143]", f"used[0:{write_capacity - 1}]")
    if simulator == "verilator":
        binary = compiled(evidence, name, tb, rtl)
        output = run_compiled(evidence, binary, name, {"vectors.txt": text})
    else:
        output = icarus(evidence, name, tb, rtl, {"vectors.txt": text})
    observed = [int(line.split()[1], 16)
                for line in (evidence.path / name / "logits.txt").read_text().splitlines()]
    metrics = [compare(observed[t * vocab:(t + 1) * vocab], fp64.logits[t], fmt)
               for t in range(tokens)]
    threshold = (0.999, 0.99, 0.95)[mode]
    for token_metrics in metrics:
        if token_metrics["cosine"] < threshold:
            raise AssertionError(f"FP64 cosine {token_metrics['cosine']} below {threshold}: {name}")
    observations, traffic = [], []
    for line in output.read_text().splitlines():
        if line.startswith("TOKEN "):
            observations.append(dict(zip(("position", "cycles", "requests", "writes", "stalls"),
                                         map(int, line.split()[1:]))))
        elif line.startswith("TRAFFIC "):
            kind, projection, row, first, last, reads, writes, stalls, padding_bits = map(int, line.split()[1:])
            traffic.append({"kind": kind, "projection": projection, "scratch_slot": row,
                            "first_accepted_request_cycle": first,
                            "last_response_cycle": last,
                            "accepted_reads": reads, "accepted_writes": writes,
                            "request_stalls": stalls, "padding_bytes": padding_bits / 8})
    if len(observations) != tokens:
        raise AssertionError(f"Missing measured token records in {relative(output)}")
    result = {"scratch_cache_writes": len(fixture.writes), "logits": len(observed),
              "stdout": relative(output), "parameters": {**parameters, "BANKS": banks}, "seed": seed,
              "activation": fmt, "awq": awq, "native_to_awq_transition": awq_transition, "metrics_vs_fp64": metrics,
              "minimum_cosine": threshold, "tokens": observations}
    result["public_transaction_traffic"] = traffic
    (evidence.path / name / "summary.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


TOP_TB = """
module tb;
  localparam B=1;
  localparam C_MODE=0,C_H=16,C_I=24,C_KV=2,C_D=2;
  reg clk=0;
  always #5 clk=~clk;
  reg rst_n,cancel=0,token_valid=0;
  reg [31:0] token_id=0,token_pos=0;
  reg new_sequence=1,token_phase=0,token_fp16=0,token_awq=0,logit_ready=0;
  wire token_ready,logit_valid,done,error,cancel_done;
  wire [31:0] logit_index,logit_data;
  wire [B-1:0] mem_req_valid,mem_req_write,mem_rsp_ready;
  reg [B-1:0] mem_req_ready=0,mem_rsp_valid=0,mem_rsp_error=0;
  wire [4*B-1:0] mem_req_kind;
  wire [3*B-1:0] mem_req_proj;
  wire [32*B-1:0] mem_req_layer,mem_req_row,mem_req_col,mem_req_wdata;
  wire [64*B-1:0] mem_req_tag;
  reg [32*B-1:0] mem_rsp_rdata=0;
  reg [64*B-1:0] mem_rsp_tag=0;
  anvil_q3_fp_top #(.NUM_LAYERS(1),.HIDDEN_SIZE(16),.INTERMEDIATE_SIZE(24),
    .NUM_Q_HEADS(8),.NUM_KV_HEADS(1),.HEAD_DIM(2),.GROUP_SIZE(8),
    .VOCAB_SIZE(3),.MAX_SEQ_LEN(4),.BANKS(B),.CACHE_MODE(0),
    .QUEUE_DEPTH(3),.TILE_K(8),.TILE_ROWS(3)) dut(.*);
  reg [102:0] memory_key[0:262143],expected_key[0:262143];
  reg [31:0] memory_data[0:262143],expected_data[0:262143],expected_logit[0:255];
  reg [102:0] mutable_key[0:65535];
  reg [31:0] mutable_data[0:65535];
  reg mutable_used[0:65535];
  reg used[0:262143];
  reg [102:0] key,load_key;
  reg [31:0] load_data;
  integer nmemory=0,ninitial=0,nexpected=0,nlogit=0,fd,outfile,rc,record_type,i,j,match_index,memory_index;
  integer dtype,awq,TOKENS,transition,image_split=-1,token_start=0,token_requests=0,token_writes=0,stalls=0,token_stalls=0;
  integer low,high,middle,first_expected=0,mutable_index,hash_steps;
  integer cycle=0,accepted_token=0,completed_token=0,compared_writes=0,compared_logits=0,requests=0;
  integer traffic_first[0:4095],traffic_last[0:4095],traffic_reads[0:4095];
  integer traffic_writes[0:4095],traffic_stalls[0:4095],traffic_index;
  integer traffic_padding[0:4095],padding_bits,group_size,code_width,block_count;
  integer valid_elements,first_element,packed_outputs,packed_column;
  integer queued_traffic[0:B-1][0:31];
  integer occupied[0:B-1],queue_head[0:B-1],queue_tail[0:B-1],due[0:B-1][0:31],bank;
  reg [31:0] queued_data[0:B-1][0:31];
  reg [63:0] queued_tag[0:B-1][0:31];
  reg [B-1:0] held_request=0;
  reg held_logit=0;
  reg accepted_awq=0;
  reg [199:0] request_payload[0:B-1];
  reg [63:0] logit_payload;
  task reset_check;
    begin
      if ({token_ready,logit_valid,done,error,cancel_done,logit_index,logit_data,
          mem_req_valid,mem_req_write,mem_rsp_ready,mem_req_kind,mem_req_proj,
          mem_req_layer,mem_req_row,mem_req_col,mem_req_wdata,mem_req_tag} !== 0)
        $fatal(1,"RESET nonzero/X public top outputs");
    end
  endtask
  initial begin
    rst_n=0;
    for (i=0;i<4096;i=i+1) begin
      traffic_first[i]=-1; traffic_last[i]=-1; traffic_reads[i]=0;
      traffic_writes[i]=0; traffic_stalls[i]=0;
      traffic_padding[i]=0;
    end
    for (i=0;i<65536;i=i+1) mutable_used[i]=0;
    for (bank=0;bank<B;bank=bank+1) begin occupied[bank]=0; queue_head[bank]=0; queue_tail[bank]=0; end
    #0; reset_check;
    #1; reset_check;
    fd=$fopen("vectors.txt","r");
    if (!fd) $fatal(1,"vector open");
    outfile=$fopen("logits.txt","w");
    if (!outfile) $fatal(1,"logit output open");
    rc=$fscanf(fd,"%d %d %d %d\\n",dtype,awq,TOKENS,transition);
    if (rc!=4 || TOKENS<1) $fatal(1,"fixture header");
    token_fp16=dtype; token_awq=awq;
    while (!$feof(fd)) begin
      rc=$fscanf(fd,"%d %h %h\\n",record_type,load_key,load_data);
      if (rc!=3) $fatal(1,"malformed integration vector");
      case (record_type)
        0: begin
          if (nmemory>=$size(memory_key)) $fatal(1,"fixture memory array capacity");
          memory_key[nmemory]=load_key; memory_data[nmemory]=load_data; nmemory=nmemory+1;
        end
        1: begin
          if (nexpected>=$size(expected_key)) $fatal(1,"fixture expected-write capacity");
          expected_key[nexpected]=load_key; expected_data[nexpected]=load_data;
          used[nexpected]=0; nexpected=nexpected+1;
        end
        2: begin
          if (load_key>=$size(expected_logit)) $fatal(1,"fixture logit capacity");
          expected_logit[load_key]=load_data; nlogit=nlogit+1;
        end
        3: begin
          if (nmemory>=$size(memory_key)) $fatal(1,"fixture transition-image capacity");
          if (image_split<0) image_split=nmemory;
          memory_key[nmemory]=load_key; memory_data[nmemory]=load_data; nmemory=nmemory+1;
        end
        default: $fatal(1,"bad fixture record");
      endcase
    end
    ninitial=nmemory;
    @(negedge clk); rst_n=1;
  end
  always @(posedge clk) begin
    if (!rst_n) reset_check;
    else begin
      if (held_logit && ({logit_index,logit_data}!==logit_payload || logit_valid!==1'b1))
        $fatal(1,"STALL logit changed");
      held_logit=logit_valid && !logit_ready;
      logit_payload={logit_index,logit_data};
      for (bank=0;bank<B;bank=bank+1) begin
        if (held_request[bank] && ({mem_req_write[bank],mem_req_kind[bank*4+:4],mem_req_layer[bank*32+:32],
            mem_req_proj[bank*3+:3],mem_req_row[bank*32+:32],mem_req_col[bank*32+:32],
            mem_req_wdata[bank*32+:32],mem_req_tag[bank*64+:64]}!==request_payload[bank] ||
            mem_req_valid[bank]!==1'b1)) $fatal(1,"STALL memory request changed bank=%0d",bank);
        held_request[bank]=mem_req_valid[bank] && !mem_req_ready[bank];
        traffic_index=(mem_req_kind[bank*4+:4]<<8)+(mem_req_proj[bank*3+:3]<<5)+
          (mem_req_kind[bank*4+:4]==8 ? mem_req_row[bank*32+:32] : 0);
        if (held_request[bank]) traffic_stalls[traffic_index]=traffic_stalls[traffic_index]+1;
        if (held_request[bank]) stalls=stalls+1;
        request_payload[bank]={mem_req_write[bank],mem_req_kind[bank*4+:4],mem_req_layer[bank*32+:32],
            mem_req_proj[bank*3+:3],mem_req_row[bank*32+:32],mem_req_col[bank*32+:32],
            mem_req_wdata[bank*32+:32],mem_req_tag[bank*64+:64]};
        if (mem_rsp_valid[bank] && mem_rsp_ready[bank]) begin
          traffic_last[queued_traffic[bank][queue_head[bank]]]=cycle;
          queue_head[bank]=(queue_head[bank]+1)&31; occupied[bank]=occupied[bank]-1;
        end
        if (mem_req_valid[bank] && mem_req_ready[bank]) begin
        if (occupied[bank]==32) $fatal(1,"scoreboard overflow");
        padding_bits=0;
        if (mem_req_kind[bank*4+:4]==0 || mem_req_kind[bank*4+:4]==3 ||
            (mem_req_kind[bank*4+:4]>=4 && mem_req_kind[bank*4+:4]<=8)) padding_bits=16;
        if (accepted_awq && (mem_req_kind[bank*4+:4]==1 || mem_req_kind[bank*4+:4]==2)) begin
          packed_outputs=(mem_req_proj[bank*3+:3]==1 || mem_req_proj[bank*3+:3]==2) ? C_KV :
            (mem_req_proj[bank*3+:3]==4 || mem_req_proj[bank*3+:3]==5) ? C_I : C_H;
          packed_column=mem_req_col[bank*32+:32]*8;
          valid_elements=packed_outputs-packed_column;
          if (valid_elements<8) padding_bits=(8-valid_elements)*4;
        end
        if (C_MODE!=0 && (mem_req_kind[bank*4+:4]==12 || mem_req_kind[bank*4+:4]==13)) begin
          group_size=C_MODE==1 ? 32 : 64; code_width=C_MODE==1 ? 8 : 4;
          block_count=(C_D+group_size-1)/group_size;
          valid_elements=C_D-((mem_req_col[bank*32+:32]>>3)%block_count)*group_size;
          if (valid_elements>group_size) valid_elements=group_size;
          first_element=(mem_req_col[bank*32+:32]&7)*(32/code_width);
          valid_elements=valid_elements-first_element;
          if (valid_elements<0) valid_elements=0;
          if (valid_elements>32/code_width) valid_elements=32/code_width;
          padding_bits=32-valid_elements*code_width;
        end
        if (padding_bits<0 || padding_bits>32) $fatal(1,"invalid transfer padding accounting");
        traffic_padding[traffic_index]=traffic_padding[traffic_index]+padding_bits;
        queued_traffic[bank][queue_tail[bank]]=traffic_index;
        if (traffic_first[traffic_index]<0) traffic_first[traffic_index]=cycle;
        if (mem_req_write[bank]) traffic_writes[traffic_index]=traffic_writes[traffic_index]+1;
        else traffic_reads[traffic_index]=traffic_reads[traffic_index]+1;
        key={mem_req_kind[bank*4+:4],mem_req_layer[bank*32+:32],mem_req_proj[bank*3+:3],
          mem_req_row[bank*32+:32],mem_req_col[bank*32+:32]};
        memory_index=-1;
        low=transition && accepted_token>1 ? image_split : 0;
        high=transition && accepted_token==1 ? image_split-1 : ninitial-1;
        while (low<=high) begin
          middle=(low+high)>>1;
          if (memory_key[middle]==key) begin memory_index=middle; low=high+1; end
          else if (memory_key[middle]<key) low=middle+1;
          else high=middle-1;
        end
        mutable_index=(key[31:0]*97+key[63:32]*193+key[98:67]*389+
          key[102:99]*769+key[66:64]*1543)&65535;
        hash_steps=0;
        while (mutable_used[mutable_index] && mutable_key[mutable_index]!=key && hash_steps<65536) begin
          mutable_index=(mutable_index+1)&65535; hash_steps=hash_steps+1;
        end
        if (hash_steps==65536) $fatal(1,"memory oracle hash capacity");
        if (mem_req_write[bank]) begin
          match_index=-1;
          j=first_expected;
          while (j<nexpected && match_index<0) begin
            if (!used[j] && expected_key[j]==key) match_index=j;
            j=j+1;
          end
          if (match_index<0) $fatal(1,"UNEXPECTED WRITE kind=%d row=%d col=%d",
            mem_req_kind,mem_req_row,mem_req_col);
          if (mem_req_wdata[bank*32+:32]!==expected_data[match_index])
            $fatal(1,"SCRATCH/CACHE index=%0d kind=%d layer=%d proj=%d row=%d col=%d expected=%h got=%h cycle=%0d",
              match_index,mem_req_kind,mem_req_layer,mem_req_proj,mem_req_row,mem_req_col,
              expected_data[match_index],mem_req_wdata,cycle);
          used[match_index]=1; compared_writes=compared_writes+1;
          while (first_expected<nexpected && used[first_expected]) first_expected=first_expected+1;
          mutable_key[mutable_index]=key; mutable_used[mutable_index]=1;
          mutable_data[mutable_index]=mem_req_wdata[bank*32+:32];
        end
        if (memory_index<0 && !mutable_used[mutable_index]) $fatal(1,"UNINITIALIZED READ kind=%d layer=%d proj=%d row=%d col=%d",
          mem_req_kind,mem_req_layer,mem_req_proj,mem_req_row,mem_req_col);
        queued_data[bank][queue_tail[bank]]=mem_req_write[bank] ? 32'd0 :
          mutable_used[mutable_index] ? mutable_data[mutable_index] : memory_data[memory_index];
        queued_tag[bank][queue_tail[bank]]=mem_req_tag[bank*64+:64];
        due[bank][queue_tail[bank]]=cycle+2+(requests%5);
        queue_tail[bank]=(queue_tail[bank]+1)&31; occupied[bank]=occupied[bank]+1; requests=requests+1;
        end
      end
      if (token_valid && token_ready) begin
        accepted_awq=token_awq;
        accepted_token=accepted_token+1; token_start=cycle;
        token_requests=requests; token_writes=compared_writes; token_stalls=stalls;
      end
      if (logit_valid && logit_ready) begin
        if (logit_index!==32'(compared_logits%VOCAB) || logit_data!==expected_logit[compared_logits])
          $fatal(1,"LOGIT index=%0d expected=%h got=%h",logit_index,expected_logit[compared_logits],logit_data);
        compared_logits=compared_logits+1;
        $fdisplay(outfile,"%h %h",logit_index,logit_data);
      end
      if (done) begin
        if (error!==1'b0) $fatal(1,"TOP error after requests=%0d writes=%0d cycle=%0d",requests,compared_writes,cycle);
        completed_token=completed_token+1;
        $display("TOKEN %0d %0d %0d %0d %0d",completed_token-1,cycle-token_start,
          requests-token_requests,compared_writes-token_writes,stalls-token_stalls);
        if (completed_token==TOKENS) begin
        if (accepted_token!=TOKENS || compared_logits!=nlogit || compared_writes!=nexpected)
          $fatal(1,"INCOMPLETE writes=%0d/%0d logits=%0d/%0d outstanding=%0d",
            compared_writes,nexpected,compared_logits,nlogit,occupied[0]);
        for (bank=0;bank<B;bank=bank+1) if (occupied[bank]!=0) $fatal(1,"outstanding memory at done");
        for (i=0;i<4096;i=i+1) if (traffic_first[i]>=0)
          $display("TRAFFIC %0d %0d %0d %0d %0d %0d %0d %0d %0d",
            i>>8,(i>>5)&7,i&31,traffic_first[i],traffic_last[i],
            traffic_reads[i],traffic_writes[i],traffic_stalls[i],traffic_padding[i]);
        $display("COMPARED top writes=%0d logits=%0d requests=%0d cycles=%0d",
          compared_writes,compared_logits,requests,cycle);
        $fclose(outfile);
        $finish;
        end
      end
      cycle=cycle+1;
      if (cycle>20000000) $fatal(1,"TOP progress bound writes=%0d requests=%0d",compared_writes,requests);
    end
  end
  always @(negedge clk) begin
    if (!rst_n) reset_check;
    else begin
      token_valid=accepted_token<TOKENS;
      token_id=accepted_token%VOCAB; token_pos=accepted_token;
      token_awq=awq || (transition && accepted_token>=1);
      new_sequence=accepted_token==0; token_phase=accepted_token>=2;
      logit_ready=cycle%13<9;
      for (bank=0;bank<B;bank=bank+1) begin
        mem_req_ready[bank]=(cycle+bank)%7<5;
        mem_rsp_valid[bank]=occupied[bank]!=0 && due[bank][queue_head[bank]]<=cycle;
        mem_rsp_rdata[bank*32+:32]=mem_rsp_valid[bank] ? queued_data[bank][queue_head[bank]] : 32'd0;
        mem_rsp_tag[bank*64+:64]=mem_rsp_valid[bank] ? queued_tag[bank][queue_head[bank]] : 64'd0;
      end
    end
  end
endmodule
"""
