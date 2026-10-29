"""D3 public kernel/logical-memory/KV integration with independent causal sums.

Cold backing storage is a logical device-local spill service, not an EMIF or
board measurement. Complete context means every position of the stated compact
configuration; it does not mean the default 32768-position checkpoint workload.
"""

import hashlib
import math
import random

from experiments import CLOCK, measurement_records
from reference import exp_q24, round_div, sat32, signed


def attention_context(evidence, seed, window, positions):
    if window not in (1, 3, 128) or positions < window or positions > 131:
        raise ValueError("unsupported bounded attention experiment")
    layers, heads, kvheads, dimension = 2, 4, 2, 8
    hidden, width = heads * dimension, kvheads * dimension
    rng = random.Random(seed)
    queries = [[rng.randrange(-65536, 65537) for _ in range(hidden)]
               for _ in range(layers)]
    history = [[[[rng.randrange(-65536, 65537) for _ in range(width)]
                 for _ in range(positions)] for _ in range(2)] for _ in range(layers)]

    def context(layer, first):
        result = []
        for head in range(heads):
            base = (head // (heads // kvheads)) * dimension
            scores = [
                signed(round_div(signed(sum(
                    queries[layer][head * dimension + component] *
                    history[layer][0][position][base + component]
                    for component in range(dimension)), 96),
                    math.isqrt(dimension << 32)), 96)
                for position in range(first, positions)]
            exps = [exp_q24(score - max(scores)) for score in scores]
            for component in range(dimension):
                result.append(sat32(round_div(signed(sum(
                    history[layer][1][position][base + component] * exponential
                    for position, exponential in zip(range(first, positions), exps)), 96),
                    sum(exps))))
        return result

    expected = [context(layer, 0) for layer in range(layers)]
    cold_differences = sum(
        a != b for layer in range(layers)
        for a, b in zip(expected[layer], context(layer, max(0, positions - window))))
    if positions > window and cold_differences == 0:
        raise AssertionError("cold context did not affect independently expected attention")

    def fixture(name, values):
        path = evidence.folder / f"attention-{window}-{positions}-{name}.hex"
        path.write_text("".join(f"{value & 0xffffffff:08x}\n" for value in values))
        evidence.record.setdefault("runtime_input_sha256", {})[evidence.relative(path)] = (
            hashlib.sha256(path.read_bytes()).hexdigest())
        return evidence.relative(path)

    query_path = fixture("query", [x for row in queries for x in row])
    history_path = fixture("history", [x for layer in history for value in layer
                                      for position in value for x in position])
    expected_path = fixture("expected", [x for row in expected for x in row])
    evidence.flush()
    bench = CLOCK + r"""
localparam WINDOW=@WINDOW@,POSITIONS=@POSITIONS@,LAYERS=2,HIDDEN=32,WIDTH=16;
localparam CACHE_WORDS=LAYERS*2*POSITIONS*WIDTH;
reg host_mode=1,host_valid=0,host_write=0,host_rsp_ready=0;
reg [3:0] host_kind=0;
reg [31:0] host_layer=0,host_row=0,host_col=0,host_wdata=0;
reg cmd_valid=0;
reg [31:0] cmd_layer=0;
wire cmd_ready,done,error,k_valid,k_ready,k_write,k_rsp_valid,k_rsp_ready,k_rsp_error;
wire [3:0] k_kind;
wire [2:0] k_proj;
wire [31:0] k_layer,k_row,k_col,k_wdata,k_rsp_data;
wire mem_ready,mem_rsp_valid,mem_rsp_error;
wire [31:0] mem_rsp_data;
wire kv_valid,kv_ready,kv_write,kv_value,kv_rsp_valid,kv_rsp_ready,kv_rsp_error,kv_rsp_hit;
wire [31:0] kv_layer,kv_head,kv_pos,kv_dim,kv_wdata,kv_rsp_data;
wire initialized,protocol_error;
wire external_valid,external_rsp_ready;
wire spill_valid,spill_write,spill_value,spill_rsp_ready;
wire [31:0] spill_layer,spill_pos,spill_col,spill_wdata;
reg spill_ready=0,spill_rsp_valid=0;
reg [31:0] spill_rsp_data=0;
reg [31:0] query[0:LAYERS*HIDDEN-1],history[0:CACHE_WORDS-1];
reg [31:0] expected[0:LAYERS*HIDDEN-1],backing[0:CACHE_WORDS-1];
reg present[0:CACHE_WORDS-1],seen_output[0:LAYERS*HIDDEN-1];
integer cycles=0,pending_spill=0,spill_delay=0;
integer spill_reads=0,spill_writes=0,spill_stalls=0;
integer compared=0,kv_compared=0,hot_reads=0,cold_reads=0;
integer pending_kv=0,wanted_hit=0,wanted_write=0;
reg [31:0] wanted_data;
integer visits[0:LAYERS*2*POSITIONS*WIDTH-1];
integer i,l,p,v,c,host_transfers=0,reset_compares=0;
integer address=0,kv_address=0;
reg held_spill=0,held_k=0,held_rsp=0;
reg [129:0] held_spill_payload;
reg [135:0] held_k_payload;
reg [33:0] held_rsp_payload;
wire [129:0] spill_payload={spill_write,spill_value,spill_layer,spill_pos,spill_col,spill_wdata};
wire [135:0] k_payload={k_write,k_kind,k_layer,k_proj,k_row,k_col,k_wdata};
function automatic integer location(input integer layer,value,position,column);
 begin
  if(layer<0 || layer>=LAYERS || value<0 || value>1 ||
     position<0 || position>=POSITIONS || column<0 || column>=WIDTH)
   $fatal(1,"ATTENTION_CACHE_ADDRESS");
  location=((layer*2+value)*POSITIONS+position)*WIDTH+column;
 end
endfunction
anvil_q1_ht_kernel #(.NUM_LAYERS(2),.HIDDEN_SIZE(32),.INTERMEDIATE_SIZE(32),
 .NUM_Q_HEADS(4),.NUM_KV_HEADS(2),.HEAD_DIM(8),.MAX_SEQ_LEN(POSITIONS)) kernel(
 .clk(clk),.rst_n(rst_n),.abort_error(1'b0),.cmd_valid(cmd_valid),.cmd_ready(cmd_ready),
 .cmd_op(3'd7),.cmd_layer(cmd_layer),.cmd_pos(32'(POSITIONS-1)),.done(done),.error(error),
 .mem_req_valid(k_valid),.mem_req_ready(k_ready),.mem_req_write(k_write),
 .mem_req_kind(k_kind),.mem_req_layer(k_layer),.mem_req_proj(k_proj),
 .mem_req_row(k_row),.mem_req_col(k_col),.mem_req_wdata(k_wdata),
 .mem_rsp_valid(k_rsp_valid),.mem_rsp_ready(k_rsp_ready),.mem_rsp_rdata(k_rsp_data),
 .mem_rsp_error(k_rsp_error));
assign k_ready=!host_mode && mem_ready;
assign k_rsp_valid=!host_mode && mem_rsp_valid;
assign k_rsp_data=!host_mode ? mem_rsp_data : 0;
assign k_rsp_error=!host_mode && mem_rsp_error;
anvil_q1_ht_logical_memory #(.NUM_LAYERS(2),.HIDDEN_SIZE(32),.INTERMEDIATE_SIZE(32),
 .NUM_KV_HEADS(2),.HEAD_DIM(8),.MAX_SEQ_LEN(POSITIONS)) memory(
 .clk(clk),.rst_n(rst_n),.req_valid(host_mode ? host_valid : k_valid),.req_ready(mem_ready),
 .req_write(host_mode ? host_write : k_write),.req_kind(host_mode ? host_kind : k_kind),
 .req_layer(host_mode ? host_layer : k_layer),.req_proj(host_mode ? 3'b0 : k_proj),
 .req_row(host_mode ? host_row : k_row),.req_col(host_mode ? host_col : k_col),
 .req_wdata(host_mode ? host_wdata : k_wdata),.rsp_valid(mem_rsp_valid),
 .rsp_ready(host_mode ? host_rsp_ready : k_rsp_ready),
 .rsp_data(mem_rsp_data),.rsp_error(mem_rsp_error),
 .external_valid(external_valid),.external_ready(1'b0),
 .external_write(),.external_kind(),.external_layer(),.external_proj(),
 .external_row(),.external_col(),.external_wdata(),.external_rsp_valid(1'b0),
 .external_rsp_ready(external_rsp_ready),.external_rsp_data(32'b0),.external_rsp_error(1'b0),
 .kv_valid(kv_valid),.kv_ready(kv_ready),.kv_write(kv_write),.kv_value(kv_value),
 .kv_layer(kv_layer),.kv_head(kv_head),.kv_pos(kv_pos),.kv_dim(kv_dim),.kv_wdata(kv_wdata),
 .kv_rsp_valid(kv_rsp_valid),.kv_rsp_ready(kv_rsp_ready),.kv_rsp_data(kv_rsp_data),
 .kv_rsp_error(kv_rsp_error));
anvil_q1_ht_kv_window #(.NUM_LAYERS(2),.NUM_KV_HEADS(2),.HEAD_DIM(8),
 .MAX_SEQ_LEN(POSITIONS),.KV_WINDOW(WINDOW)) cache(
 .clk(clk),.rst_n(rst_n),.new_sequence(1'b0),.initialized(initialized),
 .req_valid(kv_valid),.req_ready(kv_ready),.req_write(kv_write),.req_value(kv_value),
 .req_layer(kv_layer),.req_head(kv_head),.req_pos(kv_pos),.req_dim(kv_dim),.req_wdata(kv_wdata),
 .rsp_valid(kv_rsp_valid),.rsp_ready(kv_rsp_ready),.rsp_data(kv_rsp_data),
 .rsp_error(kv_rsp_error),.rsp_hit(kv_rsp_hit),.protocol_error(protocol_error),
 .spill_valid(spill_valid),.spill_ready(spill_ready),.spill_write(spill_write),
 .spill_value(spill_value),.spill_layer(spill_layer),.spill_pos(spill_pos),
 .spill_col(spill_col),.spill_wdata(spill_wdata),.spill_rsp_valid(spill_rsp_valid),
 .spill_rsp_ready(spill_rsp_ready),.spill_rsp_data(spill_rsp_data),.spill_rsp_error(1'b0));
task reset_check;
 begin
  if({cmd_ready,done,error,k_valid,k_payload,k_rsp_ready,mem_ready,mem_rsp_valid,
      mem_rsp_data,mem_rsp_error,external_valid,external_rsp_ready,kv_valid,kv_write,kv_value,
      kv_layer,kv_head,kv_pos,kv_dim,kv_wdata,kv_rsp_ready,initialized,kv_ready,kv_rsp_valid,
      kv_rsp_data,kv_rsp_error,kv_rsp_hit,protocol_error,spill_valid,spill_payload,
      spill_rsp_ready} !== '0) $fatal(1,"ATTENTION_RESET_XZ_OR_NONZERO");
  reset_compares=reset_compares+1;
 end
endtask
always @(posedge clk or negedge clk) if(!rst_n) reset_check();
always @(negedge clk)
 spill_ready=rst_n && !pending_spill && cycles%11>3;
always @(posedge clk) if(rst_n) begin
 cycles=cycles+1;
 if((^{cmd_ready,done,error,k_valid,k_ready,k_rsp_valid,k_rsp_ready,k_rsp_error,
        mem_ready,mem_rsp_valid,mem_rsp_error,kv_valid,kv_ready,kv_rsp_valid,
        kv_rsp_ready,kv_rsp_error,kv_rsp_hit,initialized,protocol_error,spill_valid,
        spill_write,spill_rsp_ready})===1'bx) $fatal(1,"ATTENTION_ACTIVE_XZ");
 if(error!==0 || protocol_error!==0 || external_valid!==0 ||
    (mem_rsp_valid && mem_rsp_error!==0)) $fatal(1,"ATTENTION_UNEXPECTED_ERROR_OR_EXTERNAL");
 if(held_k && (k_valid!==1 || k_payload!==held_k_payload))
  $fatal(1,"ATTENTION_KERNEL_REQUEST_STALL");
 held_k=k_valid && !k_ready;
 if(held_k) held_k_payload=k_payload;
 if(held_rsp && (mem_rsp_valid!==1 ||
    {mem_rsp_error,mem_rsp_data}!==held_rsp_payload[32:0]))
  $fatal(1,"ATTENTION_RESPONSE_STALL");
 held_rsp=mem_rsp_valid && !(host_mode ? host_rsp_ready : k_rsp_ready);
 if(held_rsp) held_rsp_payload={1'b0,mem_rsp_error,mem_rsp_data};
 if(held_spill && (spill_valid!==1 || spill_payload!==held_spill_payload))
  $fatal(1,"ATTENTION_SPILL_STALL");
 held_spill=spill_valid && !spill_ready;
 if(held_spill) begin held_spill_payload=spill_payload;spill_stalls=spill_stalls+1;end
 if(spill_rsp_valid && spill_rsp_ready) begin spill_rsp_valid<=0;pending_spill=0;end
 if(pending_spill && !spill_rsp_valid) begin
  if(spill_delay==0) spill_rsp_valid<=1;
  else spill_delay=spill_delay-1;
 end
 if(spill_valid && spill_ready) begin
  if(pending_spill) $fatal(1,"ATTENTION_SPILL_OUTSTANDING");
  address=location(spill_layer,spill_value,spill_pos,spill_col);
  if(spill_write) begin
   if(present[address] || spill_wdata!==history[address])
    $fatal(1,"ATTENTION_SPILL_WRITE_MISMATCH");
   backing[address]=spill_wdata;present[address]=1;spill_writes=spill_writes+1;
   spill_rsp_data<=0;
  end else begin
   if(!present[address] || backing[address]!==history[address])
    $fatal(1,"ATTENTION_COLD_BACKING_MISMATCH");
   spill_rsp_data<=backing[address];spill_reads=spill_reads+1;
  end
  pending_spill=1;spill_delay=cycles%5;
 end
 if(kv_rsp_valid && kv_rsp_ready) begin
  if(!pending_kv || kv_rsp_error!==0 ||
     (!wanted_write && (kv_rsp_data!==wanted_data || kv_rsp_hit!==1'(wanted_hit))))
   $fatal(1,"ATTENTION_KV_REFERENCE_MISMATCH actual=%h expected=%h hit=%b expected_hit=%0d",
          kv_rsp_data,wanted_data,kv_rsp_hit,wanted_hit);
  pending_kv=0;
  if(!wanted_write) begin
   kv_compared=kv_compared+1;
   if(wanted_hit) hot_reads=hot_reads+1;else cold_reads=cold_reads+1;
  end
 end
 if(kv_valid && kv_ready) begin
  if(pending_kv || kv_head>=2 || kv_dim>=8) $fatal(1,"ATTENTION_KV_PROTOCOL");
  kv_address=location(kv_layer,kv_value,kv_pos,kv_head*8+kv_dim);
  wanted_write=kv_write;wanted_data=history[kv_address];
  if(kv_write && kv_wdata!==wanted_data) $fatal(1,"ATTENTION_KV_WRITE_REFERENCE");
  wanted_hit=kv_pos>=POSITIONS-WINDOW;
  pending_kv=1;
  if(!kv_write) visits[kv_address]=visits[kv_address]+1;
 end
 if(k_valid && k_ready && k_write && k_kind==8) begin
  if(k_layer!==0 || k_proj!==0 || k_row!==5 || k_col>=HIDDEN ||
     seen_output[cmd_layer*HIDDEN+k_col] ||
     k_wdata!==expected[cmd_layer*HIDDEN+k_col])
   $fatal(1,"ATTENTION_CONTEXT_MISMATCH layer=%0d col=%0d actual=%h expected=%h",
          cmd_layer,k_col,k_wdata,expected[cmd_layer*HIDDEN+k_col]);
  seen_output[cmd_layer*HIDDEN+k_col]=1;compared=compared+1;
 end
end
task host_put(input integer kind,layer,row,col,input reg [31:0] data);
 integer wait_edges;
 begin
  @(negedge clk);
  host_valid=1;host_write=1;host_kind=4'(kind);
  host_layer=layer;host_row=row;host_col=col;host_wdata=data;
  wait_edges=0;
  while(mem_ready!==1 && wait_edges<10000) begin edge_tick();wait_edges=wait_edges+1;end
  if(mem_ready!==1) $fatal(1,"ATTENTION_HOST_REQUEST_TIMEOUT");
  edge_tick();
  @(negedge clk);host_valid=0;
  wait_edges=0;
  while(mem_rsp_valid!==1 && wait_edges<10000) begin edge_tick();wait_edges=wait_edges+1;end
  if(mem_rsp_valid!==1 || mem_rsp_error!==0 || mem_rsp_data!==0)
   $fatal(1,"ATTENTION_HOST_WRITE_RESPONSE");
  repeat(2) edge_tick();
  @(negedge clk);host_rsp_ready=1;
  edge_tick();
  @(negedge clk);host_rsp_ready=0;host_transfers=host_transfers+1;
 end
endtask
task run_layer(input integer layer);
 integer start,elapsed,hot_before,cold_before,reads_before,writes_before,count_before;
 begin
  for(c=0;c<HIDDEN;c=c+1) host_put(8,0,2,c,query[layer*HIDDEN+c]);
  for(v=0;v<2;v=v+1) for(c=0;c<WIDTH;c=c+1)
   host_put(8,0,3+v,c,history[location(layer,v,POSITIONS-1,c)]);
  @(negedge clk);host_mode=0;cmd_valid=1;cmd_layer=layer;
  if(cmd_ready!==1) $fatal(1,"ATTENTION_NOT_READY");
  start=cycles;hot_before=hot_reads;cold_before=cold_reads;
  reads_before=spill_reads;writes_before=spill_writes;count_before=compared;
  edge_tick();
  if(cmd_ready!==0 || done!==0) $fatal(1,"ATTENTION_ACCEPT_EDGE");
  @(negedge clk);cmd_valid=0;
  elapsed=0;
  while(done!==1 && elapsed<100000000) begin edge_tick();elapsed=elapsed+1;end
  if(done!==1 || error!==0 || compared-count_before!=HIDDEN ||
     pending_kv!=0 || pending_spill!=0 || k_valid!==0 || kv_valid!==0)
   $fatal(1,"ATTENTION_COMPLETION_OR_COVERAGE");
  if(spill_reads-reads_before!=cold_reads-cold_before ||
     (POSITIONS==WINDOW && (cold_reads!=cold_before || spill_writes!=writes_before)) ||
     (POSITIONS>WINDOW && cold_reads==cold_before))
   $fatal(1,"ATTENTION_RESIDENCY_OR_COLD_READ_CONSERVATION");
  $display("MEASURED_ATTENTION window=%0d positions=%0d layer=%0d cycles=%0d compared=%0d hot_reads=%0d cold_reads=%0d spill_reads=%0d spill_writes=%0d",
           WINDOW,POSITIONS,layer,cycles-start,compared-count_before,
           hot_reads-hot_before,cold_reads-cold_before,spill_reads-reads_before,spill_writes-writes_before);
  edge_tick();
  if(done!==0 || cmd_ready!==1) $fatal(1,"ATTENTION_COMPLETION_PULSE");
  @(negedge clk);host_mode=1;
 end
endtask
initial begin
 rst_n=0;`RESET_DELTA reset_check();
 $readmemh("@QUERY@",query);$readmemh("@HISTORY@",history);$readmemh("@EXPECTED@",expected);
 for(i=0;i<CACHE_WORDS;i=i+1) begin present[i]=0;visits[i]=0;end
 for(i=0;i<LAYERS*HIDDEN;i=i+1) seen_output[i]=0;
 repeat(4) edge_tick();
 @(negedge clk);rst_n=1;
 while(initialized!==1) edge_tick();
 for(l=0;l<LAYERS;l=l+1)
  for(p=0;p<POSITIONS-1;p=p+1)
   for(v=0;v<2;v=v+1) for(c=0;c<WIDTH;c=c+1)
    host_put(9+v,l,p,c,history[location(l,v,p,c)]);
 for(l=0;l<LAYERS;l=l+1) run_layer(l);
 for(i=0;i<CACHE_WORDS;i=i+1) begin
  if(visits[i]==0) $fatal(1,"ATTENTION_UNVISITED_CAUSAL_WORD");
 end
 for(i=0;i<LAYERS*HIDDEN;i=i+1)
  if(seen_output[i]!==1) $fatal(1,"ATTENTION_MISSING_CONTEXT_OUTPUT");
 if(compared!=LAYERS*HIDDEN || kv_compared!=hot_reads+cold_reads ||
    spill_reads!=cold_reads || reset_compares==0 ||
    spill_writes!=LAYERS*2*(POSITIONS-WINDOW)*WIDTH ||
    (POSITIONS>WINDOW && spill_stalls==0))
  $fatal(1,"ATTENTION_FINAL_COVERAGE");
 $display("CHECKS_PASSED attention_context window=%0d positions=%0d outputs=%0d cache_words=%0d hot_reads=%0d cold_reads=%0d spill_writes=%0d spill_stalls=%0d reset_samples=%0d",
          WINDOW,POSITIONS,compared,kv_compared,hot_reads,cold_reads,spill_writes,spill_stalls,reset_compares);
 $finish;
end
endmodule
"""
    for key, value in {
        "WINDOW": window, "POSITIONS": positions, "QUERY": query_path,
        "HISTORY": history_path, "EXPECTED": expected_path,
    }.items():
        bench = bench.replace("@" + key + "@", str(value))
    transcript = evidence.simulate(f"attention-{window}-{positions}", bench,
                                   simulator="verilator", timeout=14400)
    measured = measurement_records(transcript, "MEASURED_ATTENTION")
    if (len(measured) != layers or {row["layer"] for row in measured} != set(range(layers))
            or any(row["cycles"] <= 0 or row["compared"] != hidden
                   or row["hot_reads"] <= 0 or row["spill_reads"] != row["cold_reads"]
                   for row in measured)):
        raise AssertionError("attention measurements lack independently compared results")
    evidence.record.setdefault("attention_benchmarks", []).append({
        "scope": "D3_compact_full_causal_kernel_logical_memory_KV_not_EMIF_or_checkpoint",
        "seed": seed, "layers": layers, "hidden": hidden, "qheads": heads,
        "kvheads": kvheads, "head_dim": dimension, "window": window,
        "max_sequence": positions, "position": positions - 1,
        "compared_causal_positions": list(range(positions)),
        "cold_context_sensitive_output_elements": cold_differences,
        "compute_period_ns": 10,
        "measurement": "accepted kernel command through post-edge done inclusive; "
                       "includes current K/V installation, eviction, cold retrieval, "
                       "nonlinear arithmetic and scratch accesses; excludes host preparation",
        "spill_service": "one outstanding logical word; ready when cycles modulo 11>3; "
                         "response delay cycles modulo 5 at acceptance, held until ready",
        "observed": measured,
        "limitations": ["logical spill transactions are not physical DDR beat measurements",
                        "compact dimensions do not certify default-width 32768-position context",
                        "synthetic input tensors are not checkpoint-backed inference"],
    })
    evidence.flush()
