"""Public logical-memory compatibility against immutable parent and integer model."""

import hashlib
import re

from reference import EngineeringModel, MATRIX


def logical_image(model):
    s = model.shape
    words, regions = [], []
    for (kind, layer, proj), data in sorted(model.tensors.items()):
        if kind == 0:
            rows, cols, size, panel = s.hidden, s.vocab, 2, 64
        elif kind in (1, 2, 3):
            inputs = s.intermediate if proj == 6 else s.hidden
            outputs = s.kv if proj in (1, 2) else (
                s.intermediate if proj in (4, 5) else s.hidden)
            rows = inputs if kind == 1 else inputs // s.group
            cols = outputs // 8 if kind in (1, 2) else outputs
            size, panel = (4, 8) if kind in (1, 2) else (2, 64)
        else:
            rows = (15 if kind == 8 else s.max_seq if kind in (9, 10, 11) else 1)
            cols = (max(s.hidden, s.intermediate) if kind == 8 else s.kv
                    if kind in (9, 10) else s.head_dim if kind == 11 else
                    s.kv if kind == 4 and proj in (1, 2) else s.hidden)
            size, panel = (4 if kind >= 8 else 2), cols
        values = [None] * (rows * cols)
        offset = 0
        for start in range(0, cols, panel):
            for row in range(rows):
                for col in range(start, min(start + panel, cols)):
                    values[row * cols + col] = int.from_bytes(data[offset:offset + size], "little")
                    offset += size
        if offset != len(data) or any(value is None for value in values):
            raise AssertionError(f"incomplete independent logical-memory inverse: {kind, layer, proj}")
        if kind == 0:
            values = [values[col * s.vocab + row]
                      for row in range(s.vocab) for col in range(s.hidden)]
            rows, cols = s.vocab, s.hidden
        regions.append((layer * 96 + kind * 8 + proj, len(words), rows, cols))
        words.extend(values)
    return words, regions


def compatibility(evidence, seed, config):
    from experiments import CLOCK, packed
    from verify import file_sha256

    shape = MATRIX[config]
    model = EngineeringModel(shape, seed, "AWQ")
    words, regions = logical_image(model)
    image = evidence.folder / "compatibility-memory.hex"
    image.write_text("".join(f"{word:08x}\n" for word in words))
    expected = []
    expected_writes = {}
    commands = []

    def success(token, position, sequence):
        logits = model.token(token, position, sequence)
        region_index = {key: (base, cols) for key, base, _, cols in regions}
        for kind, layer, row, col, value in model.last_writes:
            base, cols = region_index[layer * 96 + kind * 8]
            expected_writes.setdefault(base + row * cols + col, []).append(value)
        expected.extend(logits)
        commands.append((0, token, position, int(sequence), packed(logits, 32)))

    success(seed % shape.vocab, 0, False)
    commands += [
        (1, shape.vocab, 0, 1, 0),
        (1, 0, shape.max_seq, 0, 0),
        (1, 0, 1, 1, 0),
        (1, 0, 0, 0, 0),
    ]
    if shape.max_seq > 1:
        success((seed + 1) % shape.vocab, 1, False)
    success((seed + 2) % shape.vocab, 0, True)
    commands += [
        (2, 0, 0, 0, 0),
        (1, 0, 0, 0, 0),
    ]
    success((seed + 3) % shape.vocab, 0, True)
    commands += [(2, 1, 0, 0, 0), (1, 0, 0, 0, 0)]
    success((seed + 4) % shape.vocab, 0, True)
    commands += [(3, 0, 0, 0, 0)]
    model.history = [[] for _ in range(shape.layers)]
    success((seed + 5) % shape.vocab, 0, False)
    write_depth = max(map(len, expected_writes.values()))
    write_image = evidence.folder / "compatibility-writes.hex"
    write_image.write_text("".join(
        f"{(expected_writes.get(address, []) + [0] * write_depth)[index] & 0xffffffff:08x}\n"
        for address in range(len(words)) for index in range(write_depth)))
    stimulus = evidence.folder / "compatibility-stimulus.hex"
    stimulus.write_text("".join(
        format((logits << 67) | (sequence << 66) | (position << 34) | (token << 2) | op,
               f"0{(32 * shape.vocab + 70) // 4}x") + "\n"
        for op, token, position, sequence, logits in commands))
    evidence.record.setdefault("runtime_input_sha256", {}).update({
        evidence.relative(path): file_sha256(path) for path in (image, write_image, stimulus)})
    evidence.record["simulation_geometry"] = vars(shape)

    bench = CLOCK + r"""
localparam VOCAB=@VOCAB@;
reg token_valid=0,new_sequence=0,logit_ready=0;
reg [31:0] token_id=0,token_pos=0;
wire token_ready,logit_valid,done,error;
wire [31:0] logit_index;
wire signed [31:0] logit_data;
wire mem_req_valid,mem_req_write,mem_rsp_ready;
wire [3:0] mem_req_kind;
wire [2:0] mem_req_proj;
wire [31:0] mem_req_layer,mem_req_row,mem_req_col,mem_req_wdata;
reg mem_req_ready=0,mem_rsp_valid=0,mem_rsp_error=0;
reg [31:0] mem_rsp_rdata=0;
reg [31:0] memory [0:@MEMORY_LAST@];
reg [31:0] expected_writes [0:@WRITE_LAST@];
integer write_counts [0:@MEMORY_LAST@];
integer init_index;
string case_directory;
reg [VOCAB*32+66:0] stimulus [0:@COMMAND_LAST@];
integer cycles=0,requests=0,writes=0,compared=0,successes=0,invalids=0,faults=0;
integer pending=0,delay_left=0,address=0,reset_active=0,held=0;
integer read_fault=0,numerical_fault=0,injected=0;
integer quiet_edges=0;
reg [135:0] held_payload;
wire [135:0] payload={mem_req_write,mem_req_kind,mem_req_layer,mem_req_proj,
                     mem_req_row,mem_req_col,mem_req_wdata};
anvil_q1_top #(
 .NUM_LAYERS(@LAYERS@),.HIDDEN_SIZE(@HIDDEN@),.INTERMEDIATE_SIZE(@INTERMEDIATE@),
 .NUM_Q_HEADS(@QHEADS@),.NUM_KV_HEADS(@KVHEADS@),.HEAD_DIM(@HEAD_DIM@),
 .GROUP_SIZE(@GROUP@),.VOCAB_SIZE(VOCAB),.MAX_SEQ_LEN(@MAX_SEQ@)) product(
 .clk(clk),.rst_n(rst_n),.token_valid(token_valid),.token_ready(token_ready),
 .token_id(token_id),.token_pos(token_pos),.new_sequence(new_sequence),
 .logit_valid(logit_valid),.logit_ready(logit_ready),.logit_index(logit_index),
 .logit_data(logit_data),.done(done),.error(error),
 .mem_req_valid(mem_req_valid),.mem_req_ready(mem_req_ready),.mem_req_write(mem_req_write),
 .mem_req_kind(mem_req_kind),.mem_req_layer(mem_req_layer),.mem_req_proj(mem_req_proj),
 .mem_req_row(mem_req_row),.mem_req_col(mem_req_col),.mem_req_wdata(mem_req_wdata),
 .mem_rsp_valid(mem_rsp_valid),.mem_rsp_ready(mem_rsp_ready),
 .mem_rsp_rdata(mem_rsp_rdata),.mem_rsp_error(mem_rsp_error));
function automatic integer location(input integer kind,layer,proj,row,col);
 integer base,rows,cols;
 begin
  base=-1;rows=0;cols=0;
  case(layer*96+kind*8+proj)
   @REGIONS@
  endcase
  if(base<0 || row<0 || row>=rows || col<0 || col>=cols)
   $fatal(1,"COMPAT_MEMORY_IDENTITY kind=%0d layer=%0d proj=%0d row=%0d col=%0d",
          kind,layer,proj,row,col);
  location=base+row*cols+col;
 end
endfunction
always @(posedge clk) begin
 if(!rst_n) begin
  pending=0;held=0;mem_rsp_valid<=0;mem_rsp_error<=0;mem_rsp_rdata<=0;
 end else begin
  if((^{token_ready,logit_valid,done,error,mem_req_valid,mem_rsp_ready})===1'bx)
   $fatal(1,"COMPAT_ACTIVE_XZ");
  if(held && (!mem_req_valid || payload!==held_payload))
   $fatal(1,"COMPAT_REQUEST_CHANGED_UNDER_STALL");
  held=mem_req_valid && !mem_req_ready;
  if(held) held_payload=payload;
  if(mem_rsp_valid && mem_rsp_ready) begin mem_rsp_valid<=0;pending=0;end
  if(pending && !mem_rsp_valid) begin
   if(delay_left==0) mem_rsp_valid<=1;
   else delay_left=delay_left-1;
  end
  if(mem_req_valid && mem_req_ready) begin
   if(pending) $fatal(1,"COMPAT_MULTIPLE_OUTSTANDING");
   address=location(mem_req_kind,mem_req_layer,mem_req_proj,mem_req_row,mem_req_col);
   if(mem_req_write && mem_req_kind!=8 && mem_req_kind!=9 && mem_req_kind!=10)
    $fatal(1,"COMPAT_IMMUTABLE_WRITE");
   requests=requests+1;pending=1;
   if(requests%4096==0) begin
    $display("COMPAT_MEMORY_PROGRESS requests=%0d writes=%0d kind=%0d layer=%0d row=%0d col=%0d",
             requests,writes,mem_req_kind,mem_req_layer,mem_req_row,mem_req_col);
   end
   delay_left=(requests%3==0) ? 7 : 1;
   mem_rsp_error<=read_fault!=0;
   if(read_fault) begin read_fault=0;injected=injected+1;end
   if(numerical_fault) begin
    if(mem_req_kind!==0 || mem_req_write) $fatal(1,"COMPAT_NUMERICAL_FAULT_NOT_EMBEDDING");
    mem_rsp_rdata<=32'h7c00;numerical_fault=0;injected=injected+1;
   end else begin
    mem_rsp_rdata<=mem_req_write ? 0 : memory[address];
    if(mem_req_write) begin
     if(mem_req_wdata!==expected_writes[address*@WRITE_DEPTH@+write_counts[address]])
      $fatal(1,"COMPAT_WRITE_MISMATCH kind=%0d layer=%0d row=%0d col=%0d ordinal=%0d actual=%h expected=%h",
             mem_req_kind,mem_req_layer,mem_req_row,mem_req_col,write_counts[address],
             mem_req_wdata,expected_writes[address*@WRITE_DEPTH@+write_counts[address]]);
     write_counts[address]=write_counts[address]+1;
     memory[address]=mem_req_wdata;writes=writes+1;
    end
   end
  end
 end
end
always @(negedge clk) begin
 cycles=cycles+1;
 mem_req_ready=rst_n && pending==0 && cycles%11>3;
end
always @(posedge clk) begin
 if(!rst_n || token_ready || done || (mem_req_valid && mem_req_ready) ||
    (mem_rsp_valid && mem_rsp_ready) || (logit_valid && logit_ready)) quiet_edges=0;
 else begin
  quiet_edges=quiet_edges+1;
  if(quiet_edges>100000)
   $fatal(1,"COMPAT_NO_PUBLIC_PROGRESS token=%0d position=%0d requests=%0d writes=%0d logits=%0d pending=%0d req_valid=%b req_ready=%b rsp_valid=%b rsp_ready=%b done=%b error=%b",
          token_id,token_pos,requests,writes,compared,pending,mem_req_valid,mem_req_ready,
          mem_rsp_valid,mem_rsp_ready,done,error);
 end
end
task wait_idle;
 begin
  @(negedge clk);token_valid=0;logit_ready=0;
  while(token_ready!==1) begin
   edge_tick();
   if(logit_valid!==0) $fatal(1,"COMPAT_UNEXPECTED_IDLE_LOGIT");
  end
  repeat(6) edge_tick();
 end
endtask
task start_token(input integer id,position,sequence_start);
 begin
  wait_idle();
  @(negedge clk);token_valid=1;token_id=id;token_pos=position;new_sequence=sequence_start;
  if(token_ready!==1) $fatal(1,"COMPAT_START_NOT_READY");
  edge_tick();
  if(token_ready!==0 || logit_valid!==0) $fatal(1,"COMPAT_ACCEPT_EDGE");
  $display("COMPAT_COMMAND_ACCEPTED token=%0d position=%0d new_sequence=%0d",
           id,position,sequence_start);
  @(negedge clk);token_valid=0;
 end
endtask
task invalid_token(input integer id,position,sequence_start);
 integer edges,before_requests;
 begin
  before_requests=requests;
  start_token(id,position,sequence_start);
  edges=0;
  while(done!==1 && edges<2) begin edge_tick();edges=edges+1;end
  if(done!==1 || error!==1 || logit_valid!==0 || requests!=before_requests)
   $fatal(1,"COMPAT_INVALID_COMMAND_ERROR edges=%0d",edges);
  edge_tick();
  if(done!==0 || error!==0) $fatal(1,"COMPAT_ERROR_PULSE");
  invalids=invalids+1;
 end
endtask
task run_token(input integer id,position,sequence_start,input [VOCAB*32-1:0] expected);
 integer count,stall,last_stalls;
 reg transfer,valid_before;
 reg [31:0] index_before,data_before;
 begin
  start_token(id,position,sequence_start);
  count=0;stall=0;last_stalls=0;
  while(count<VOCAB) begin
   logit_ready=stall%11>3;
   if(logit_valid && logit_index==VOCAB-1 && last_stalls<31) begin
    logit_ready=0;last_stalls=last_stalls+1;
   end
   #0.001;
   if(token_ready!==0) $fatal(1,"COMPAT_READY_DURING_INFERENCE");
   valid_before=logit_valid;index_before=logit_index;data_before=logit_data;
   transfer=logit_valid && logit_ready;
   if(logit_valid && (logit_index!==count || logit_data!==expected[32*count+:32]))
    $fatal(1,"COMPAT_LOGIT_MISMATCH position=%0d index=%0d observed=%h expected=%h",
           position,count,logit_data,expected[32*count+:32]);
   edge_tick();
   if(valid_before && !transfer &&
      (logit_valid!==1 || logit_index!==index_before || logit_data!==data_before))
    $fatal(1,"COMPAT_STALLED_LOGIT");
   if(transfer) count=count+1;
   if(count==VOCAB) begin
    if(done!==1 || error!==0) $fatal(1,"COMPAT_FINAL_TRANSFER_COMPLETION");
   end else if(done!==0) $fatal(1,"COMPAT_EARLY_COMPLETION error=%b",error);
   stall=stall+1;
   if(count<VOCAB) @(negedge clk);
  end
  if(last_stalls!=31) $fatal(1,"COMPAT_MISSING_FINAL_STALL");
  edge_tick();
  if(done!==0 || error!==0) $fatal(1,"COMPAT_SUCCESS_PULSE");
  compared=compared+count;successes=successes+1;
  $display("TOKEN_COMPARED compatibility token=%0d position=%0d logits=%0d writes=%0d",
           successes,position,count,writes);
  $fflush();
 end
endtask
task fault_token(input integer numerical);
 integer before_injected;
 begin
  wait_idle();before_injected=injected;
  if(numerical) numerical_fault=1;else read_fault=1;
  start_token(0,0,1);
  while(done!==1) begin
   edge_tick();
   if(logit_valid!==0) $fatal(1,"COMPAT_FAULT_PUBLISHED_LOGIT");
  end
  if(error!==1 || injected!=before_injected+1 || pending)
   $fatal(1,"COMPAT_FAULT_NOT_REPORTED");
  edge_tick();
  if(done!==0 || error!==0) $fatal(1,"COMPAT_FAULT_PULSE");
  faults=faults+1;
 end
endtask
task reset_during_memory;
 integer before_requests;
 begin
  before_requests=requests;
  start_token(0,0,1);
  // start_token may return after the first request has already transferred.
  while(!pending) @(negedge clk);
  if(pending!==1 || requests<=before_requests)
   $fatal(1,"COMPAT_RESET_WITHOUT_OUTSTANDING");
  rst_n=0;token_valid=0;logit_ready=0;reset_active=reset_active+1;
  repeat(3) edge_tick();
  @(negedge clk);rst_n=1;
  repeat(8) edge_tick();
  if(done!==0 || logit_valid!==0 || token_ready!==1 || pending)
   $fatal(1,"COMPAT_RESET_RECOVERY");
 end
endtask
initial begin
 rst_n=0;
 if(!$value$plusargs("CASE_DIR=%s",case_directory)) $fatal(1,"MISSING_CASE_DIRECTORY");
 $readmemh({case_directory,"/compatibility-memory.hex"},memory);
 $readmemh({case_directory,"/compatibility-writes.hex"},expected_writes);
 $readmemh({case_directory,"/compatibility-stimulus.hex"},stimulus);
 for(init_index=0;init_index<=@MEMORY_LAST@;init_index=init_index+1) write_counts[init_index]=0;
 repeat(4) edge_tick();
 @(negedge clk);rst_n=1;
 for(init_index=0;init_index<=@COMMAND_LAST@;init_index=init_index+1) begin
  case(stimulus[init_index][1:0])
   0:run_token(stimulus[init_index][33:2],stimulus[init_index][65:34],
               stimulus[init_index][66],stimulus[init_index][67+:VOCAB*32]);
   1:invalid_token(stimulus[init_index][33:2],stimulus[init_index][65:34],
                   stimulus[init_index][66]);
   2:fault_token(stimulus[init_index][33:2]);
   3:reset_during_memory();
   default:$fatal(1,"INVALID_COMPATIBILITY_STIMULUS");
  endcase
 end
 if(compared==0 || requests==0 || writes==0 || faults!=2 || invalids!=6 || reset_active!=1)
  $fatal(1,"COMPAT_MISSING_COVERAGE");
 $display("CHECKS_PASSED compatibility logits=%0d tokens=%0d requests=%0d writes=%0d invalids=%0d faults=%0d active_resets=%0d",
          compared,successes,requests,writes,invalids,faults,reset_active);
 $finish;
end
endmodule
"""
    substitutions = {
        "VOCAB": shape.vocab, "MEMORY_LAST": len(words) - 1,
        "REGIONS": "\n".join(f"{key}:begin base={base};rows={rows};cols={cols};end"
                             for key, base, rows, cols in regions),
        "COMMAND_LAST": len(commands) - 1, "WRITE_DEPTH": write_depth,
        "WRITE_LAST": len(words) * write_depth - 1,
        **{name.upper(): value for name, value in vars(shape).items()},
    }
    for key, value in substitutions.items():
        bench = bench.replace("@" + key + "@", str(value))
    if re.search(r"@[A-Z_]+@", bench):
        raise AssertionError("unresolved compatibility bench substitution")
    record = {
        "scope": "parent_logical_interface_and_integer_reference_not_default_checkpoint",
        "seed": seed, "configuration": config, "shape": vars(shape),
        "input_sha256": hashlib.sha256(image.read_bytes()).hexdigest(),
        "expected_logits_sha256": hashlib.sha256(
            b"".join((x & 0xffffffff).to_bytes(4, "little") for x in expected)).hexdigest(),
        "implementations": [],
    }
    evidence.record.setdefault("compatibility", []).append(record)
    root = evidence.folder / "sources"
    for name, source in (("parent", root / "anvil_q1_reference/rtl"),
                         ("compatibility", root / "rtl")):
        simulator = "verilator"
        evidence.simulate("compat-" + name, bench, sources=sorted(source.glob("*.sv")),
                          timeout=14400, simulator=simulator,
                          runtime_args=("+CASE_DIR=" + evidence.relative(evidence.folder),),
                          build_pool=evidence.simulation_build_pool)
        ledger = [row for row in evidence.record["observations"][-1]["observed_counters"]
                  if "requests" in row]
        if len(ledger) != 1 or ledger[0]["logits"] != len(expected):
            raise AssertionError(f"{name}: missing complete ordered-logit comparisons")
        record["implementations"].append({"name": name, "simulator": simulator,
                                          "observed": ledger[0]})
        evidence.flush()


def compatibility_matrix(evidence):
    ledger = [{"configuration": config, "seed": seed, "outcome": "not_run"}
              for config in range(len(MATRIX)) for seed in (17, 89, 257)]
    evidence.record["compatibility_matrix"] = ledger
    evidence.flush()
    for row in ledger:
        trial = evidence.__class__(
            f"compatibility-{row['configuration']}-{row['seed']}",
            source_root=evidence.folder / "sources")
        trial.simulation_build_pool = evidence.simulation_build_pool
        row["receipt"] = evidence.relative(trial.folder / "receipt.json")
        trial.record["tool_version_receipt"] = evidence.relative(evidence.folder / "receipt.json")
        evidence.flush()
        try:
            compatibility(trial, row["seed"], row["configuration"])
        except (OSError, RuntimeError, AssertionError, ValueError) as exc:
            row.update(outcome="failed", reason=str(exc))
            trial.finish("failed", str(exc))
            evidence.flush()
            raise
        row.update(outcome="compared",
                   implementations=trial.record["compatibility"][0]["implementations"])
        trial.finish("probe_passed", "Parent compatibility parameter case only.")
        evidence.flush()
