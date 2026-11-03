"""Public-memory causal GQA/cache probes, independent of projection geometry."""

from fractions import Fraction

from execution import ROOT, compiled, relative, run_compiled
from integration import key_bits
from model import Fixture


def check(evidence, head_dim=34, mode=0, fp8=0, affine=0, fmt="bf16", tokens=2):
    model = object.__new__(Fixture)
    model.check_budget = evidence.ensure_budget
    model.fmt, model.d, model.qh, model.kh = fmt, head_dim, 16, 2
    model.cache_mode, model.fp8, model.affine = mode, fp8, affine
    model.memory, model.writes, model.cache = {}, [], {}
    records = [f"{int(fmt == 'fp16')} {tokens}\n"]
    for position in range(tokens):
        # Distinct head values and nonzero Q/K make head 7/8 and the final head
        # observable without manufacturing a large projection checkpoint.
        query = [model.raw(Fraction((head % 3) + 1, 64))
                 for head in range(16) for _ in range(head_dim)]
        key = [model.raw(Fraction((head + 1) * (position + 1), 32))
               for head in range(2) for _ in range(head_dim)]
        value = [model.raw(Fraction((head + 1) * (position + 1) * (1 if d % 2 else -1), 16))
                 for head in range(2) for d in range(head_dim)]
        image = {(8, 0, 0, slot, col): raw
                 for slot, vector in ((2, query), (3, key), (4, value))
                 for col, raw in enumerate(vector)}
        model.writes = []
        model.attention(query, key, value, 0, position)
        records.append(f"{position} {int(position >= 2)} {len(image)} {len(model.writes)}\n")
        records += [f"{key_bits(k):026x} {v:08x}\n" for k, v in sorted(image.items())]
        records += [f"{key_bits(k):026x} {v:08x}\n" for k, v in model.writes]
    tb = ATTENTION_TB
    for name, value in (("@D@", head_dim), ("@M@", mode), ("@F@", fp8), ("@A@", affine)):
        tb = tb.replace(name, str(value))
    rtl = [relative(path) for path in sorted((ROOT / "rtl").glob("*.sv"))]
    rtl += ["anvil_q3_reference/rtl/anvil_q3_mem_port.sv"]
    name = f"attention-d{head_dim}-m{mode}-f{fp8}-a{affine}-{fmt}-n{tokens}"
    binary = compiled(evidence, name, tb, rtl)
    output = run_compiled(evidence, binary, name, {"vectors.txt": "".join(records)})
    return {"head_dim": head_dim, "q_heads": 16, "kv_heads": 2,
            "cache_mode": mode, "fp8": fp8, "affine": affine, "activation": fmt,
            "tokens": tokens, "compared_context_elements": tokens * 16 * head_dim,
            "head_boundary_checks": [7, 8, 15], "stdout": relative(output)}


ATTENTION_TB = """
module tb;
  localparam [63:0] PROGRESS_BOUND=64'd16*(@D@+1)*4*(2048*@D@+4096)+1000000;
  reg clk=0;
  always #5 clk=~clk;
  reg rst_n,flush=0,cmd_valid=0,cmd_fp16=0,cmd_phase=0;
  reg [31:0] cmd_layer=0,cmd_pos=0;
  wire cmd_ready,done,error;
  wire [1:0] c_req_valid,c_req_write,c_rsp_ready;
  reg [1:0] c_req_ready=0,c_rsp_valid=0,c_rsp_error=0;
  wire [7:0] c_req_kind;
  wire [5:0] c_req_proj;
  wire [63:0] c_req_layer,c_req_row,c_req_col,c_req_wdata;
  reg [63:0] c_rsp_rdata=0;
  anvil_q3_fp_gqa_attention #(.NUM_LAYERS(1),.HIDDEN_SIZE(16*@D@),
    .NUM_Q_HEADS(16),.NUM_KV_HEADS(2),.HEAD_DIM(@D@),.MAX_SEQ_LEN(4),
    .CACHE_MODE(@M@),.MODE1_FP8(@F@),.INT4_ASYM(@A@)) dut(.*);
  reg [102:0] keys[0:16383],expected_key[0:4095],key,scanned_key;
  reg [31:0] data[0:16383],expected_data[0:4095],scanned_data;
  reg used[0:16383];
  reg pending[0:1];
  reg [31:0] response[0:1];
  integer due[0:1],cycle=0,fd,rc,dtype,tokens,position,phase,nimage,nexpected;
  integer nm=0,compared=0,received=0,requests=0,stalls=0,latency,i,j,b,found;
  reg [1:0] held=0;
  reg [134:0] held_payload[0:1];
  task reset_check;
    begin
      if ({cmd_ready,done,error,c_req_valid,c_req_write,c_req_kind,c_req_layer,
          c_req_proj,c_req_row,c_req_col,c_req_wdata,c_rsp_ready}!==0)
        $fatal(1,"RESET attention public outputs");
    end
  endtask
  task store(input reg [102:0] k,input reg [31:0] v);
    integer index,match_index;
    begin
      match_index=(k[31:0]*97+k[63:32]*193+k[98:67]*389+k[102:99]*769)&16383;
      index=0;
      while (used[match_index] && keys[match_index]!=k && index<16384) begin
        match_index=(match_index+1)&16383; index=index+1;
      end
      if (index==16384) $fatal(1,"attention memory capacity");
      keys[match_index]=k; used[match_index]=1;
      data[match_index]=v;
    end
  endtask
  initial begin
    rst_n=0; pending[0]=0; pending[1]=0;
    for (i=0;i<16384;i=i+1) used[i]=0;
    #0; reset_check;
    #1; reset_check;
    fd=$fopen("vectors.txt","r");
    if (!fd) $fatal(1,"attention vectors");
    rc=$fscanf(fd,"%d %d\\n",dtype,tokens);
    if (rc!=2) $fatal(1,"attention header");
    cmd_fp16=dtype;
    @(negedge clk); rst_n=1;
    for (position=0;position<tokens;position=position+1) begin
      rc=$fscanf(fd,"%d %d %d %d\\n",j,phase,nimage,nexpected);
      if (rc!=4 || j!=position || nexpected>4096) $fatal(1,"attention command");
      for (i=0;i<nimage;i=i+1) begin
        rc=$fscanf(fd,"%h %h\\n",scanned_key,scanned_data);
        if (rc!=2) $fatal(1,"attention image");
        store(scanned_key,scanned_data);
      end
      for (i=0;i<nexpected;i=i+1) begin
        rc=$fscanf(fd,"%h %h\\n",expected_key[i],expected_data[i]);
        if (rc!=2) $fatal(1,"attention expected");
      end
      while (cmd_ready!==1'b1) @(negedge clk);
      cmd_pos=position; cmd_phase=phase; cmd_valid=1; received=0; latency=0;
      @(negedge clk); cmd_valid=0;
      while (done!==1'b1 && latency<PROGRESS_BOUND) begin
        @(negedge clk); latency=latency+1;
      end
      if (done!==1'b1 || error!==1'b0 || received!=nexpected)
        $fatal(1,"GQA completion pos=%0d writes=%0d/%0d",position,received,nexpected);
      if (pending[0] || pending[1]) $fatal(1,"GQA done before drain");
      $display("ATTENTION %0d %0d %0d",position,latency,received);
      @(negedge clk);
      if (done!==1'b0) $fatal(1,"GQA done not pulse");
    end
    if (compared==0 || stalls==0) $fatal(1,"missing GQA comparisons/stalls");
    $display("COMPARED GQA writes=%0d requests=%0d stalls=%0d",compared,requests,stalls);
    $finish;
  end
  always @(posedge clk) begin
    if (!rst_n) reset_check;
    else begin
      for (b=0;b<2;b=b+1) begin
        if (held[b] && (c_req_valid[b]!==1'b1 ||
            {c_req_kind[b*4+:4],c_req_layer[b*32+:32],c_req_proj[b*3+:3],
             c_req_row[b*32+:32],c_req_col[b*32+:32],c_req_wdata[b*32+:32]}!==held_payload[b]))
          $fatal(1,"GQA held request");
        held[b]=c_req_valid[b] && !c_req_ready[b];
        held_payload[b]={c_req_kind[b*4+:4],c_req_layer[b*32+:32],c_req_proj[b*3+:3],
          c_req_row[b*32+:32],c_req_col[b*32+:32],c_req_wdata[b*32+:32]};
        if (held[b]) stalls=stalls+1;
        if (c_rsp_valid[b] && c_rsp_ready[b]) pending[b]=0;
        if (c_req_valid[b] && c_req_ready[b]) begin
          key={c_req_kind[b*4+:4],c_req_layer[b*32+:32],c_req_proj[b*3+:3],
            c_req_row[b*32+:32],c_req_col[b*32+:32]};
          if (c_req_write[b]) begin
            if (received>=nexpected || key!==expected_key[received] ||
                c_req_wdata[b*32+:32]!==expected_data[received])
              $fatal(1,"GQA write=%0d key=%h expected=%h got=%h",
                received,key,expected_data[received],c_req_wdata[b*32+:32]);
            store(key,c_req_wdata[b*32+:32]); received=received+1; compared=compared+1;
          end
          found=(key[31:0]*97+key[63:32]*193+key[98:67]*389+key[102:99]*769)&16383;
          j=0;
          while (used[found] && keys[found]!=key && j<16384) begin
            found=(found+1)&16383; j=j+1;
          end
          if (!used[found] || j==16384 || pending[b]) $fatal(1,"GQA unowned read/transaction");
          response[b]=c_req_write[b] ? 0 : data[found];
          pending[b]=1; due[b]=cycle+2+(requests%5); requests=requests+1;
        end
      end
      cycle=cycle+1;
    end
  end
  always @(negedge clk) begin
    if (!rst_n) reset_check;
    else for (b=0;b<2;b=b+1) begin
      c_req_ready[b]=!pending[b] && (cycle+b)%7<5;
      c_rsp_valid[b]=pending[b] && due[b]<=cycle;
      c_rsp_rdata[b*32+:32]=c_rsp_valid[b] ? response[b] : 0;
    end
  end
endmodule
"""
