"""Public HT command rejection, busy configuration and image-reuse checks.

The compact two-layer synthetic image is not a checkpoint benchmark. Rejected
commands are checked at the specified edges without consuming DDR traffic; valid
commands still compare every logit with the independent integer model.
"""

from pathlib import Path

from experiments import measurement_records, top_probe


def instrument_commands(bench, model):
    shape = model.shape
    if shape.max_seq < 3:
        raise ValueError("distinct in-range order checks require max_sequence >= 3")
    selected, kind, layer, proj, base, length = model.descriptors[-1]
    readbacks = [(0x0c, int(model.mode == "BF16")), (0x10, selected),
                 (0x14, kind), (0x18, layer), (0x1c, proj),
                 (0x20, base & 0xffffffff), (0x24, base >> 32), (0x28, length)]
    busy_readbacks = "\n".join(
        f"  csr(0,16'h{address:04x},0,0,32'd{value});"
        for address, value in readbacks)
    tasks = r"""
integer command_rejections=0,busy_mutations=0,busy_load_notready_edges=0,busy_checks=0;
integer maximum_rejection_edges=0;
task command_idle;
 integer waiting;
 begin
  waiting=0;
  while(token_ready!==1 && waiting<10000) begin edge_tick();waiting=waiting+1;end
  if(token_ready!==1 || done!==0 || error!==0 || logit_valid!==0)
   $fatal(1,"COMMAND_IDLE_NOT_RECOVERED");
 end
endtask
task rejected_command(input [31:0] id,position,input sequence_start);
 integer elapsed,before_reads,before_writes,before_uploads;
 begin
  command_idle();
  before_reads=reads;before_writes=writes;before_uploads=load_accepts;
  @(negedge clk);
  token_valid=1;token_id=id;token_pos=position;new_sequence=sequence_start;
  logit_ready=0;
  if(token_ready!==1) $fatal(1,"COMMAND_REJECTION_NOT_ACCEPTED");
  edge_tick();
  if(token_ready!==0 || logit_valid!==0)
   $fatal(1,"COMMAND_REJECTION_ACCEPT_EDGE");
  @(negedge clk);token_valid=0;
  elapsed=0;
  while(done!==1 && elapsed<2) begin
   edge_tick();elapsed=elapsed+1;
   if((^{done,error,logit_valid,token_ready})===1'bx || logit_valid!==0 ||
      reads!==before_reads || writes!==before_writes || load_accepts!==before_uploads ||
      outstanding!==0 || avm_read!==0 || avm_write!==0)
    $fatal(1,"COMMAND_REJECTION_TRAFFIC_XZ_OR_LOGIT");
  end
  if(done!==1 || error!==1)
   $fatal(1,"COMMAND_REJECTION_DEADLINE id=%0d position=%0d new_sequence=%0d edges=%0d",
          id,position,sequence_start,elapsed);
  if(elapsed>maximum_rejection_edges) maximum_rejection_edges=elapsed;
  repeat(4) begin
   edge_tick();
   if(done!==0 || error!==0 || logit_valid!==0 || token_ready!==0 ||
      reads!==before_reads || writes!==before_writes || load_accepts!==before_uploads ||
      avm_read!==0 || avm_write!==0)
    $fatal(1,"COMMAND_REJECTION_DUPLICATE_OR_SIDE_EFFECT");
  end
  csr(0,16'h0004,0,0,32'h0000000c);
  csr(1,16'h0008,4,0,0);
  command_idle();
  command_rejections=command_rejections+1;
 end
endtask
task busy_command_checks(input [31:0] expected_index,expected_data);
 integer n,before_writes,before_uploads;
 reg [15:0] address;
 begin
  if(logit_valid!==1 || logit_ready!==0 || done!==0 ||
     logit_index!==expected_index || logit_data!==expected_data)
   $fatal(1,"COMMAND_BUSY_NOT_STALLED_ON_COMPARED_LOGIT");
  csr(0,16'h0004,0,0,32'h00000006);
  for(n=0;n<10;n=n+1) begin
   address=16'h0008+4*n;
   csr(1,address,0,1,0);
   if(done!==0 || error!==0 || logit_valid!==1 || token_ready!==0 ||
      logit_index!==expected_index || logit_data!==expected_data)
    $fatal(1,"COMMAND_BUSY_MUTATION_CHANGED_ACTIVE_OUTPUT address=%h",address);
   busy_mutations=busy_mutations+1;
  end
  csr(0,16'h0004,0,0,32'h0000000e);
BUSY_READBACKS
  before_writes=writes;before_uploads=load_accepts;
  @(negedge ddr_clk);
  for(n=0;n<31;n=n+1) begin
   @(posedge ddr_clk);
   if(load_ready!==0 || writes!==before_writes || load_accepts!==before_uploads ||
      avm_write!==0 || done!==0 || error!==0 || logit_valid!==1 ||
      logit_index!==expected_index || logit_data!==expected_data)
    $fatal(1,"COMMAND_BUSY_UPLOAD_OR_OUTPUT_CHANGED");
   busy_load_notready_edges=busy_load_notready_edges+1;
  end
  @(negedge ddr_clk);
  busy_checks=busy_checks+1;
 end
endtask
"""
    bench = bench.replace("task run_token(", tasks.replace("BUSY_READBACKS", busy_readbacks) +
                          "\ntask run_token(", 1)
    marker = "   #0.001;\n   pre_valid=logit_valid;"
    if bench.count(marker) != 1:
        raise AssertionError("command check no longer identifies the public logit sink")
    bench = bench.replace(marker, r"""
   if(logit_valid===1 && logit_index==VOCAB_VALUE-1 && busy_checks==0) begin
    logit_ready=0;
    busy_command_checks(VOCAB_VALUE-1,expected[32*(VOCAB_VALUE-1)+:32]);
   end
   #0.001;
   pre_valid=logit_valid;""", 1)
    marker = "  held_data=csr_rdata;"
    bench = bench.replace(marker, r"""
  if(address!=16'h002c && !(wr && address==16'h0008 && data[1]) &&
     wait_cycles!=1)
   $fatal(1,"COMMAND_ORDINARY_CSR_RESPONSE_EDGE address=%h observed=%0d",address,wait_cycles);
  held_data=csr_rdata;""", 1)
    program = r"""
 rejected_command(VOCAB_VALUE,0,1'b1);
 rejected_command(32'hffffffff,0,1'b1);
 rejected_command(0,SEQ_VALUE,1'b0);
 rejected_command(0,32'hffffffff,1'b0);
 rejected_command(0,1,1'b1);
 rejected_command(0,1,1'b0);
 // Empty history accepts position zero without an explicit new-sequence command.
 run_token(token_words[0][31:0],0,1'b0,token_words[0][65+:VOCAB_VALUE*32]);
 csr(0,16'h0004,0,0,32'h0000000c);
 csr(1,16'h0008,4,0,0);
 command_idle();
 rejected_command(0,0,1'b0);
 rejected_command(0,2,1'b0);
 // Invalid commands did not alter history: the next expected position still matches.
 run_token(token_words[1][31:0],1,1'b0,token_words[1][65+:VOCAB_VALUE*32]);
 run_token(token_words[token_count-1][31:0],0,1'b1,
           token_words[token_count-1][65+:VOCAB_VALUE*32]);
 if(command_rejections!=8 || busy_mutations!=10 || busy_load_notready_edges!=31 ||
    busy_checks!=1 || logits!=3*VOCAB_VALUE || load_accepts!=IMAGE_LAST+1 ||
    writes!=load_accepts)
  $fatal(1,"COMMAND_MISSING_OBSERVED_COVERAGE");
 $display("CHECKS_PASSED command_checks rejected=%0d maximum_rejection_edges=%0d busy_mutations=%0d load_notready_edges=%0d busy_checks=%0d ordered_logits=%0d preload_beats=%0d",
          command_rejections,maximum_rejection_edges,busy_mutations,busy_load_notready_edges,
          busy_checks,logits,load_accepts);
 $finish;
"""
    return bench, program


def command_checks(evidence, seed):
    ledger = evidence.record.setdefault("command_checks", [])
    for mode in ("AWQ", "BF16"):
        trial = evidence.__class__("commands-" + mode.lower(),
                                  source_root=evidence.folder / "sources")
        trial.simulation_build_pool = evidence.simulation_build_pool
        row = {"mode": mode, "configuration": 1, "seed": seed, "outcome": "running",
               "receipt": evidence.relative(trial.folder / "receipt.json")}
        ledger.append(row)
        evidence.flush()
        try:
            top_probe(trial, mode, seed, config=1, command_validation=True)
            transcript = next(
                (trial.folder.parents[2] / command["stdout"]).read_text()
                for command in reversed(trial.record["commands"])
                if Path(command["argv"][0]).parts[-2:] == ("compiled", "Vtb"))
            records = measurement_records(transcript, "CHECKS_PASSED command_checks")
            if (len(records) != 1 or records[0]["rejected"] != 8 or
                    records[0]["maximum_rejection_edges"] not in (0, 1, 2) or
                    records[0]["busy_mutations"] != 10 or
                    records[0]["load_notready_edges"] != 31 or
                    records[0]["busy_checks"] != 1 or
                    records[0]["ordered_logits"] != 51 or records[0]["preload_beats"] <= 0):
                raise AssertionError("missing public command/error/recovery comparisons")
            row.update(outcome="compared", observed=records[0])
            row["load_scope"] = (
                "Observed load_ready low and no upload during busy inference; "
                "no offered load request or busy-to-idle upload acquisition is certified.")
            trial.finish("probe_passed", "Observed command rejection, busy conflicts and reference logits.")
        except (OSError, RuntimeError, AssertionError, ValueError) as exc:
            row.update(outcome="failed", reason=str(exc))
            trial.finish("failed", str(exc))
            raise
        finally:
            evidence.flush()
