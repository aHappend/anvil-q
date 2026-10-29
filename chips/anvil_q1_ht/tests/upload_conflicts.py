"""Pending preload ownership across inference completion, using public pins only.

A single partial-byte write replays unchanged bytes from the synthetic image.
The offered request is never withdrawn before acceptance. Its completion must
invalidate the image; recommit must recover the same independently modeled logits.
"""

from experiments import measurement_records, top_probe


def instrument_upload(bench):
    declarations = r"""
integer pending_started=0,pending_accepts=0,pending_suppressed=0;
integer pending_completed=0,pending_final_transfers=0,pending_checks=0;
integer pending_before_writes=0,pending_before_uploads=0;
reg [609:0] pending_payload;
wire [609:0] preload_payload={load_address,load_data,load_byteenable,load_last};
always @(posedge clk) if(rst_n && pending_started &&
 logit_valid && logit_ready && logit_index==VOCAB_VALUE-1)
 pending_final_transfers=pending_final_transfers+1;
always @(posedge ddr_clk) if(rst_n && pending_started) begin
 if(load_valid && preload_payload !== pending_payload)
  $fatal(1,"PENDING_UPLOAD_REQUEST_CHANGED");
 if(pending_final_transfers==0) begin
  if(load_ready!==0 || load_accepts!==pending_before_uploads ||
     writes!==pending_before_writes || avm_write!==0 || done!==0 || error!==0)
   $fatal(1,"PENDING_UPLOAD_ACQUIRED_WHILE_INFERENCE_BUSY");
 end
 if(load_valid && load_ready) begin
  if(pending_final_transfers!=1 || pending_accepts!=0)
   $fatal(1,"PENDING_UPLOAD_EARLY_OR_DUPLICATED_ACCEPTANCE");
  pending_accepts=pending_accepts+1;
 end
 if(pending_accepts==1 && pending_completed==0 && load_done===1) begin
  if(load_error!==0 || writes!==pending_before_writes+1 ||
     response_writes!==writes || memory[0]!==image[0])
   $fatal(1,"PENDING_UPLOAD_COMPLETED_WITHOUT_EXACT_ACKNOWLEDGED_WRITE");
  pending_completed=1;
 end
end
always @(negedge ddr_clk)
 if(rst_n && pending_started && pending_accepts==1) load_valid=0;
task offer_pending_upload(input [31:0] expected_final);
 integer n;
 begin
  if(logit_valid!==1 || logit_ready!==0 || logit_index!==VOCAB_VALUE-1 ||
     logit_data!==expected_final || done!==0)
   $fatal(1,"PENDING_UPLOAD_FINAL_STALL_PRECONDITION");
  pending_before_writes=writes;pending_before_uploads=load_accepts;
  @(negedge ddr_clk);
  load_address=0;load_data=image[0];load_byteenable=64'h8040201008040201;
  load_last=1;load_valid=1;
  pending_payload={load_address,load_data,load_byteenable,load_last};
  pending_started=1;
  for(n=0;n<31;n=n+1) begin
   @(posedge ddr_clk);#0.001;
   if(load_ready!==0 || pending_accepts!==0 || logit_valid!==1 ||
      logit_data!==expected_final || logit_index!==VOCAB_VALUE-1 ||
      logit_ready!==0 || done!==0 || error!==0 ||
      load_accepts!==pending_before_uploads || writes!==pending_before_writes)
    $fatal(1,"PENDING_UPLOAD_BUSY_STALL_CHANGED ready=%b accepted=%0d logit_valid=%b index=%0d data=%h expected=%h sink_ready=%b done=%b error=%b uploads=%0d writes=%0d",
           load_ready,pending_accepts,logit_valid,logit_index,logit_data,expected_final,
           logit_ready,done,error,load_accepts,writes);
   pending_suppressed=pending_suppressed+1;
  end
  @(negedge clk);
  pending_checks=pending_checks+1;
 end
endtask
task settle_pending_upload;
 integer waiting;
 begin
  waiting=0;
  while(pending_completed!==1 && waiting<10000) begin
   edge_tick();waiting=waiting+1;
  end
  if(pending_completed!==1 || pending_accepts!==1 || load_error!==0 ||
     load_accepts!==pending_before_uploads+1 || writes!==pending_before_writes+1)
   $fatal(1,"PENDING_UPLOAD_DID_NOT_ACQUIRE_AND_COMPLETE_AFTER_INFERENCE");
  repeat(50) begin
   edge_tick();
   if(token_ready!==0 || logit_valid!==0 || done!==0 || error!==0 ||
      writes!==pending_before_writes+1 || pending_accepts!==1)
    $fatal(1,"PENDING_UPLOAD_IMAGE_REMAINED_USABLE_OR_DUPLICATED");
  end
  csr(0,16'h0004,0,0,0);
  csr(1,16'h0008,2,0,0);
  repeat(30) edge_tick();
  if(token_ready!==1) $fatal(1,"PENDING_UPLOAD_RECOMMIT_NOT_READY");
  csr(0,16'h0004,0,0,32'h00000005);
 end
endtask
"""
    marker = "task run_token("
    if bench.count(marker) != 1:
        raise AssertionError("pending-upload test cannot identify the public token driver")
    bench = bench.replace(marker, declarations + "\n" + marker, 1)
    marker = "   #0.001;\n   pre_valid=logit_valid;"
    if bench.count(marker) != 1:
        raise AssertionError("pending-upload test cannot identify the public logit sink")
    bench = bench.replace(marker, r"""
   if(logit_valid===1 && logit_index==VOCAB_VALUE-1 && pending_started==0) begin
    logit_ready=0;
    offer_pending_upload(expected[32*(VOCAB_VALUE-1)+:32]);
   end
   #0.001;
   pre_valid=logit_valid;""", 1)
    # This experiment intentionally performs one additional upload, unlike the
    # ordinary persistence campaign; keep its exact conservation assertion.
    marker = "load_accepts!==IMAGE_LAST+1"
    if bench.count(marker) != 1:
        raise AssertionError("pending-upload test lost ordinary upload conservation")
    bench = bench.replace(marker, "load_accepts!==IMAGE_LAST+1+pending_accepts", 1)
    program = r"""
 run_token(token_words[0][31:0],0,1'b1,token_words[0][65+:VOCAB_VALUE*32]);
 settle_pending_upload();
 run_token(token_words[0][31:0],0,1'b1,token_words[0][65+:VOCAB_VALUE*32]);
 if(pending_checks!=1 || pending_suppressed!=31 || pending_accepts!=1 ||
    pending_completed!=1 || pending_final_transfers!=2 || logits!=2*VOCAB_VALUE ||
    load_accepts!=IMAGE_LAST+2 || writes!=load_accepts)
  $fatal(1,"PENDING_UPLOAD_MISSING_OBSERVED_COVERAGE");
 $display("CHECKS_PASSED pending_upload suppressed_edges=%0d accepted=%0d completed=%0d final_transfers=%0d ordered_logits=%0d total_upload_beats=%0d",
          pending_suppressed,pending_accepts,pending_completed,pending_final_transfers,
          logits,load_accepts);
 $finish;
"""
    return bench, program


def upload_conflicts(evidence, seed):
    ledger = evidence.record.setdefault("pending_upload_cases", [])
    for mode in ("AWQ", "BF16"):
        trial = evidence.__class__("pending-upload-" + mode.lower(),
                                  source_root=evidence.folder / "sources")
        trial.simulation_build_pool = evidence.simulation_build_pool
        row = {"mode": mode, "configuration": 0, "seed": seed, "outcome": "running",
               "receipt": evidence.relative(trial.folder / "receipt.json")}
        ledger.append(row)
        evidence.flush()
        try:
            top_probe(trial, mode, seed, pending_upload_validation=True)
            transcript = next(
                (trial.folder.parents[2] / command["stdout"]).read_text()
                for command in reversed(trial.record["commands"])
                if command["argv"][0].endswith("/compiled/Vtb"))
            records = measurement_records(transcript, "CHECKS_PASSED pending_upload")
            expected = {"suppressed_edges": 31, "accepted": 1, "completed": 1,
                        "final_transfers": 2, "ordered_logits": 16}
            if (len(records) != 1 or any(records[0].get(key) != value
                                         for key, value in expected.items()) or
                    records[0]["total_upload_beats"] <= 1):
                raise AssertionError("pending-upload comparisons or conservation are missing")
            row.update(outcome="compared", observed=records[0])
            trial.finish("probe_passed", "Observed pending upload exclusion, acquisition, "
                         "invalidation, recommit and ordered reference recovery logits.")
        except (OSError, RuntimeError, AssertionError, ValueError) as exc:
            row.update(outcome="failed", reason=str(exc))
            trial.finish("failed", str(exc))
            raise
        finally:
            evidence.flush()
