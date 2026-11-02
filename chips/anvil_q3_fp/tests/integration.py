"""Compact public-memory/logit oracle. No DUT-internal assertions."""

from execution import ROOT, icarus, relative, verilator
from model import Fixture


def key_bits(key):
    kind, layer, projection, row, column = key
    return (kind << 99) | (layer << 67) | (projection << 64) | (row << 32) | column


def smoke(evidence, seed=17, simulator="verilator", banks=1, fmt="bf16", awq=False, tokens=1):
    fixture = Fixture(seed=seed, fmt=fmt, awq=awq)
    initial = dict(fixture.memory)
    for position in range(tokens):
        fixture.token(token=position % fixture.vocab, position=position)
    initial.update({key: value for key, value in fixture.memory.items() if key[0] == 11})
    text = "".join(f"0 {key_bits(key):026x} {value:08x}\n" for key, value in initial.items())
    text += "".join(f"1 {key_bits(key):026x} {value:08x}\n" for key, value in fixture.writes)
    text += "".join(f"2 {index:026x} {value:08x}\n"
                    for index, value in enumerate(value for token in fixture.logits for value in token))
    rtl = [relative(path) for path in sorted((ROOT / "rtl").glob("*.sv"))]
    rtl += ["anvil_q3_reference/rtl/anvil_q3_bank_scheduler.sv",
            "anvil_q3_reference/rtl/anvil_q3_mem_port.sv"]
    runner = verilator if simulator == "verilator" else icarus
    tb = TOP_TB.replace("localparam B=1;", f"localparam B={banks}, TOKENS={tokens};")
    tb = tb.replace("token_fp16=0,token_awq=0", f"token_fp16={int(fmt == 'fp16')},token_awq={int(awq)}")
    output = runner(evidence, "top-smoke", tb, rtl, {"vectors.txt": text})
    return {"scratch_cache_writes": len(fixture.writes), "logits": sum(map(len, fixture.logits)),
            "stdout": relative(output), "configuration": {"banks": banks, "cache_mode": 0,
            "hidden": fixture.h, "intermediate": fixture.i, "layers": 1, "tokens": tokens,
            "activation": fixture.fmt, "awq": awq, "seed": seed}}


TOP_TB = """
module tb;
  localparam B=1;
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
  reg [102:0] memory_key[0:8191],expected_key[0:4095];
  reg [31:0] memory_data[0:8191],expected_data[0:4095],expected_logit[0:15];
  reg used[0:4095];
  reg [102:0] key,load_key;
  reg [31:0] load_data;
  integer nmemory=0,nexpected=0,nlogit=0,fd,rc,record_type,i,j,match_index,memory_index;
  integer cycle=0,accepted_token=0,completed_token=0,compared_writes=0,compared_logits=0,requests=0;
  integer occupied[0:B-1],queue_head[0:B-1],queue_tail[0:B-1],due[0:B-1][0:31],bank;
  reg [31:0] queued_data[0:B-1][0:31];
  reg [63:0] queued_tag[0:B-1][0:31];
  reg [B-1:0] held_request=0;
  reg held_logit=0;
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
    for (bank=0;bank<B;bank=bank+1) begin occupied[bank]=0; queue_head[bank]=0; queue_tail[bank]=0; end
    #0; reset_check;
    #1; reset_check;
    fd=$fopen("vectors.txt","r");
    if (!fd) $fatal(1,"vector open");
    while (!$feof(fd)) begin
      rc=$fscanf(fd,"%d %h %h\\n",record_type,load_key,load_data);
      if (rc!=3) $fatal(1,"malformed integration vector");
      case (record_type)
        0: begin memory_key[nmemory]=load_key; memory_data[nmemory]=load_data; nmemory=nmemory+1; end
        1: begin
          expected_key[nexpected]=load_key; expected_data[nexpected]=load_data;
          used[nexpected]=0; nexpected=nexpected+1;
        end
        2: begin expected_logit[load_key]=load_data; nlogit=nlogit+1; end
        default: $fatal(1,"bad fixture record");
      endcase
    end
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
        request_payload[bank]={mem_req_write[bank],mem_req_kind[bank*4+:4],mem_req_layer[bank*32+:32],
            mem_req_proj[bank*3+:3],mem_req_row[bank*32+:32],mem_req_col[bank*32+:32],
            mem_req_wdata[bank*32+:32],mem_req_tag[bank*64+:64]};
        if (mem_rsp_valid[bank] && mem_rsp_ready[bank]) begin
          queue_head[bank]=(queue_head[bank]+1)&31; occupied[bank]=occupied[bank]-1;
        end
        if (mem_req_valid[bank] && mem_req_ready[bank]) begin
        if (occupied[bank]==32) $fatal(1,"scoreboard overflow");
        key={mem_req_kind[bank*4+:4],mem_req_layer[bank*32+:32],mem_req_proj[bank*3+:3],
          mem_req_row[bank*32+:32],mem_req_col[bank*32+:32]};
        memory_index=-1;
        for (i=0;i<nmemory;i=i+1) if (memory_key[i]==key) memory_index=i;
        if (mem_req_write[bank]) begin
          match_index=-1;
          for (j=0;j<nexpected;j=j+1)
            if (match_index<0 && !used[j] && expected_key[j]==key) match_index=j;
          if (match_index<0) $fatal(1,"UNEXPECTED WRITE kind=%d row=%d col=%d",
            mem_req_kind,mem_req_row,mem_req_col);
          if (mem_req_wdata[bank*32+:32]!==expected_data[match_index])
            $fatal(1,"SCRATCH/CACHE index=%0d kind=%d layer=%d proj=%d row=%d col=%d expected=%h got=%h cycle=%0d",
              match_index,mem_req_kind,mem_req_layer,mem_req_proj,mem_req_row,mem_req_col,
              expected_data[match_index],mem_req_wdata,cycle);
          used[match_index]=1; compared_writes=compared_writes+1;
          if (memory_index<0) begin
            memory_index=nmemory; memory_key[nmemory]=key; nmemory=nmemory+1;
          end
          memory_data[memory_index]=mem_req_wdata[bank*32+:32];
        end
        if (memory_index<0) $fatal(1,"UNINITIALIZED READ kind=%d layer=%d proj=%d row=%d col=%d",
          mem_req_kind,mem_req_layer,mem_req_proj,mem_req_row,mem_req_col);
        queued_data[bank][queue_tail[bank]]=mem_req_write[bank] ? 32'd0 : memory_data[memory_index];
        queued_tag[bank][queue_tail[bank]]=mem_req_tag[bank*64+:64];
        due[bank][queue_tail[bank]]=cycle+2+(requests%5);
        queue_tail[bank]=(queue_tail[bank]+1)&31; occupied[bank]=occupied[bank]+1; requests=requests+1;
        end
      end
      if (token_valid && token_ready) accepted_token=accepted_token+1;
      if (logit_valid && logit_ready) begin
        if (logit_index!==32'(compared_logits%3) || logit_data!==expected_logit[compared_logits])
          $fatal(1,"LOGIT index=%0d expected=%h got=%h",logit_index,expected_logit[compared_logits],logit_data);
        compared_logits=compared_logits+1;
      end
      if (done) begin
        if (error!==1'b0) $fatal(1,"TOP error after requests=%0d writes=%0d cycle=%0d",requests,compared_writes,cycle);
        completed_token=completed_token+1;
        if (completed_token==TOKENS) begin
        if (accepted_token!=TOKENS || compared_logits!=nlogit || compared_writes!=nexpected)
          $fatal(1,"INCOMPLETE writes=%0d/%0d logits=%0d/%0d outstanding=%0d",
            compared_writes,nexpected,compared_logits,nlogit,occupied[0]);
        for (bank=0;bank<B;bank=bank+1) if (occupied[bank]!=0) $fatal(1,"outstanding memory at done");
        $display("COMPARED top writes=%0d logits=%0d requests=%0d cycles=%0d",
          compared_writes,compared_logits,requests,cycle);
        $finish;
        end
      end
      cycle=cycle+1;
      if (cycle>400000) $fatal(1,"TOP progress bound writes=%0d requests=%0d",compared_writes,requests);
    end
  end
  always @(negedge clk) begin
    if (!rst_n) reset_check;
    else begin
      token_valid=accepted_token<TOKENS;
      token_id=accepted_token%3; token_pos=accepted_token;
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
