"""Public-pin KV backing, cache-hit, eviction and epoch comparisons."""

import random

from model import encode_kv, decode_kv
from leaf import packed


KV_TB = r"""
module verify_kv;
  localparam MODE=@MODE@, DIM=@DIM@, HEADS=2, CONTEXT=3, RESIDENT=@RESIDENT@;
  localparam SOURCE_COUNT=@SOURCE_COUNT@, WRITE_COUNT=@WRITE_COUNT@;
  reg clk=0; always #5 clk=~clk;
  reg rst_n=0, flush=0, cmd_valid=0;
  wire cmd_ready, done, error, idle, drain_done, fault;
  reg [1:0] cmd_op=0;
  reg [31:0] cmd_epoch=0, cmd_layer=0, cmd_pos=0, cmd_head=0, cmd_dim=0;
  reg cmd_phase=0, cmd_bypass=0;
  wire signed [31:0] read_data;
  wire scratch_req_valid, scratch_rsp_ready;
  reg scratch_req_ready=0, scratch_rsp_valid=0, scratch_rsp_error=0;
  wire [31:0] scratch_req_slot, scratch_req_index;
  reg [31:0] scratch_rsp_rdata=0;
  wire memory_req_valid, memory_req_write;
  reg memory_req_ready=0, memory_rsp_valid=0, memory_rsp_error=0;
  wire [32:0] memory_req_address;
  wire [511:0] memory_req_wdata;
  wire [63:0] memory_req_byteenable;
  reg [511:0] memory_rsp_rdata=0;
  anvil_q3_ht_kv_hierarchy #(.NUM_LAYERS(2),.NUM_KV_HEADS(HEADS),
    .HEAD_DIM(DIM),.MAX_SEQ_LEN(CONTEXT),.CACHE_MODE(MODE),
    .KV_RESIDENT_GROUPS(RESIDENT)) dut(.*);
  reg [31:0] source [0:SOURCE_COUNT-1];
  reg [544:0] expected_write [0:WRITE_COUNT-1];
  reg [32:0] addresses [0:1023];
  reg [511:0] records [0:1023];
  integer stored=0, writes=0, reads=0, scratch_reads=0, compared=0, commits=0;
  integer hits=0, misses=0, bypasses=0, rejected=0, epochs=0, stalls=0;
  integer cycle=0, source_base=0, j, found, pending_due=0, scratch_due=0;
  reg pending=0, scratch_pending=0;
  reg [511:0] pending_data;
  reg [31:0] scratch_pending_data, rng=@SEED@;
  reg inject_scratch_error=0, inject_memory_error=0, inject_record_error=0;
  integer scratch_errors=0, memory_errors=0, record_errors=0;
  reg held=0;
  reg [610:0] held_request;
  function automatic [31:0] next_random(input [31:0] x);
    reg [31:0] y;
    begin y=x^(x<<13); y=y^(y>>17); next_random=y^(y<<5); end
  endfunction
  task reset_check;
    begin
      if ({cmd_ready,done,error,read_data,idle,drain_done,fault,scratch_req_valid,
           scratch_req_slot,scratch_req_index,scratch_rsp_ready,memory_req_valid,
           memory_req_write,memory_req_address,memory_req_wdata,memory_req_byteenable}
          !== 715'd0) $fatal(1,"KV_RESET_XZ");
    end
  endtask
  always @(posedge clk) begin
    cycle=cycle+1;
    if (!rst_n) reset_check();
    else begin
      if (cycle>2000000) $fatal(1,"KV_PROGRESS");
      if (held && {memory_req_valid,memory_req_write,memory_req_address,
                   memory_req_wdata,memory_req_byteenable} !== held_request)
        $fatal(1,"KV_MEMORY_COMMAND_STABILITY");
      held=memory_req_valid && !memory_req_ready;
      held_request={memory_req_valid,memory_req_write,memory_req_address,
                    memory_req_wdata,memory_req_byteenable};
      if (held) stalls=stalls+1;
      if (memory_rsp_valid) begin
        if (!pending || cycle<pending_due) $fatal(1,"KV_RETURN_OWNERSHIP");
        if (memory_rsp_error) memory_errors=memory_errors+1;
        if (inject_record_error) record_errors=record_errors+1;
        pending=0;
      end
      if (scratch_rsp_valid && scratch_rsp_ready) begin
        if (scratch_rsp_error) scratch_errors=scratch_errors+1;
        scratch_pending=0;
      end
      if (scratch_req_valid && scratch_req_ready) begin
        if (scratch_pending || scratch_req_slot<3 || scratch_req_slot>4 ||
            scratch_req_index>=HEADS*DIM)
          $fatal(1,"KV_SCRATCH_OWNERSHIP");
        scratch_pending=1; scratch_due=cycle+2;
        scratch_pending_data=source[source_base+(scratch_req_slot-3)*HEADS*DIM+
                                    scratch_req_index];
        scratch_reads=scratch_reads+1;
      end
      if (memory_req_valid && memory_req_ready) begin
        if (memory_req_address<33'h100000000 || memory_req_address[5:0]!==0 ||
            memory_req_byteenable!==64'hffffffffffffffff)
          $fatal(1,"KV_BACKING_ADDRESS");
        found=-1;
        for (j=0;j<stored;j=j+1)
          if (addresses[j]==memory_req_address) found=j;
        if (memory_req_write) begin
          if (writes>=WRITE_COUNT ||
              {memory_req_address,memory_req_wdata} !== expected_write[writes])
            $fatal(1,"KV_WRITE_RECORD index=%0d address=%h actual=%h expected=%h",
                   writes,memory_req_address,memory_req_wdata,expected_write[writes]);
          writes=writes+1;
          if (found<0) begin
            if (stored==1024) $fatal(1,"KV_MODEL_CAPACITY");
            found=stored; stored=stored+1; addresses[found]=memory_req_address;
          end
          records[found]=memory_req_wdata;
        end else begin
          if (pending || found<0) $fatal(1,"KV_READ_UNWRITTEN");
          pending=1; pending_due=cycle+12; pending_data=records[found];
          reads=reads+1;
        end
      end
    end
  end
  always @(negedge clk) begin
    if (!rst_n) reset_check();
    else begin
      rng=next_random(rng);
      memory_req_ready=rng[3:0]>=3;
      scratch_req_ready=rng[7:4]>=3;
      memory_rsp_valid=pending && cycle+1>=pending_due && rng[11:8]>=3;
      memory_rsp_rdata=memory_rsp_valid ? pending_data : 512'd0;
      memory_rsp_error=memory_rsp_valid && inject_memory_error;
      if (memory_rsp_valid && inject_record_error)
        memory_rsp_rdata[MODE==0 ? 511 : 264]=1;
      scratch_rsp_valid=scratch_pending && cycle+1>=scratch_due;
      scratch_rsp_rdata=scratch_rsp_valid ? scratch_pending_data : 32'd0;
      scratch_rsp_error=scratch_rsp_valid && inject_scratch_error;
    end
  end
  task operation(input integer op, input integer epoch_id, input integer layer_id,
                 input integer position_id, input integer head_id, input integer dim_id,
                 input integer phase_id, input integer bypass_id, input integer expected,
                 input integer expect_error, input integer expect_traffic);
    integer before_reads;
    begin
      @(negedge clk);
      cmd_valid=1; cmd_op=2'(op); cmd_epoch=epoch_id; cmd_layer=layer_id;
      cmd_pos=position_id; cmd_head=head_id; cmd_dim=dim_id;
      cmd_phase=1'(phase_id); cmd_bypass=1'(bypass_id);
      @(posedge clk); while (!cmd_ready) @(posedge clk);
      before_reads=reads;
      if (done !== 0) $fatal(1,"KV_SAME_EDGE_COMPLETION");
      @(negedge clk); cmd_valid=0;
      @(posedge clk); while (!done) @(posedge clk);
      if (error !== 1'(expect_error) || read_data !== 32'(expected))
        $fatal(1,"KV_HIERARCHY_NUMERICAL op=%0d epoch=%0d layer=%0d pos=%0d head=%0d dim=%0d actual=%0d expected=%0d error=%b expected_error=%0d",
               op,epoch_id,layer_id,position_id,head_id,dim_id,
               read_data,expected,error,expect_error);
      if (expect_traffic>=0 && reads-before_reads!=expect_traffic)
        $fatal(1,"KV_CACHE_TRAFFIC actual=%0d expected=%0d",reads-before_reads,expect_traffic);
      if (op==0 && !expect_error) commits=commits+1;
      if (op!=0 && !expect_error) begin
        compared=compared+1;
        if (bypass_id) bypasses=bypasses+1;
        else if (reads==before_reads) hits=hits+1;
        else misses=misses+1;
      end
      if (expect_error) rejected=rejected+1;
      @(posedge clk); #1;
      if (done !== 0 || read_data !== 0) $fatal(1,"KV_COMPLETION_PULSE");
    end
  endtask
  task invalidate;
    begin
      @(negedge clk); flush=1;
      @(posedge clk);
      @(negedge clk); flush=0;
      @(posedge clk); while (!idle) @(posedge clk);
      if (pending || fault !== 0) $fatal(1,"KV_FLUSH_DRAIN");
      epochs=epochs+1;
    end
  endtask
  initial begin
    $readmemh("@SOURCE@",source); $readmemh("@WRITES@",expected_write);
    #1; reset_check();
    repeat(3) @(negedge clk); rst_n=1;
    @OPERATIONS@
    if (writes!=WRITE_COUNT || scratch_reads!=SOURCE_COUNT+1 || compared==0 ||
        hits==0 || misses<2*RESIDENT || bypasses==0 || commits!=8 || rejected!=6 ||
        epochs!=5 || stalls==0 || scratch_errors!=1 || memory_errors!=1 || record_errors!=1)
      $fatal(1,"KV_COVERAGE writes=%0d scratch=%0d compared=%0d hits=%0d misses=%0d epochs=%0d",
             writes,scratch_reads,compared,hits,misses,epochs);
    $display("KV_HIERARCHY_PASS mode=%0d residency=%0d seed=@SEED@ dim=%0d writes=%0d reads=%0d compared=%0d hits=%0d misses=%0d bypasses=%0d commits=%0d rejected=%0d epochs=%0d stalls=%0d scratch_errors=%0d memory_errors=%0d malformed_records=%0d",
             MODE,RESIDENT,DIM,writes,reads,compared,hits,misses,bypasses,commits,rejected,
             epochs,stalls,scratch_errors,memory_errors,record_errors);
    $finish;
  end
endmodule
"""


def kv_bench(directory, relative, mode=0, resident=3, seed=17, dim=66):
    cap = (16, 32, 64)[mode]
    groups = (dim + cap - 1) // cap
    rng = random.Random(seed)
    sources, writes, operations = [], [], []

    def operation(op, epoch, layer=0, pos=0, head=0, index=0, phase=0,
                  bypass=0, expected=0, error=0, traffic=-1):
        operations.append("operation(" + ",".join(map(str, (
            op, epoch, layer, pos, head, index, phase, bypass, expected, error, traffic))) + ");")

    operation(1, 1, error=1, traffic=0)
    operations.append("invalidate();")
    operations.append("inject_scratch_error=1;")
    operation(0, 1, error=1, traffic=0)
    operations.append('if (fault!==1) $fatal(1,"KV_SCRATCH_FAULT_PROPAGATION");')
    operations.append("inject_scratch_error=0; invalidate();")
    for epoch in (1, 2):
        decoded = {}
        for layer in range(2):
            for pos in range(2):
                operations.append(f"source_base={len(sources)};")
                for which in range(2):
                    for head in range(2):
                        values = [rng.randrange(-(1 << 31), 1 << 31) for _ in range(dim)]
                        sources.extend(values)
                        reconstructed = []
                        for group in range(groups):
                            part = values[group * cap:(group + 1) * cap]
                            record = encode_kv(part, mode)
                            address = (0x100000000 + (((layer * 2 + which) * 3 + pos) * 2 + head)
                                       * groups * 64 + group * 64)
                            writes.append((address << 512) | int.from_bytes(record, "little"))
                            reconstructed.extend(decode_kv(record, len(part), mode))
                        decoded[layer, pos, which, head] = reconstructed
                operation(0, epoch, layer, pos, phase=pos)
                operation(2, epoch, layer, pos, 1, dim - 1, expected=decoded[layer, pos, 1, 1][-1],
                          traffic=0)
        # Two complete cyclic scans force replacement/refill rather than only bypass.
        for scan in range(2):
            for (layer, pos, which, head), values in decoded.items():
                for group in range(groups):
                    index = group * cap
                    operation(1 + which, epoch, layer, pos, head, index,
                              bypass=int(scan == 0), expected=values[index],
                              traffic=1 if scan == 0 else -1)
                    operation(1 + which, epoch, layer, pos, head, index,
                              expected=values[index], traffic=0 if scan else -1)
        injection = "inject_record_error" if epoch == 1 else "inject_memory_error"
        operations.append(f"{injection}=1;")
        operation(1, epoch, index=dim - 1, bypass=1, error=1, traffic=1)
        operations.append('if (fault!==1) $fatal(1,"KV_BACKING_FAULT_PROPAGATION");')
        operations.append(f"{injection}=0;")
        # Failed reads may not recover old committed data after invalidation.
        operations.append("invalidate();")
        operation(1, epoch, error=1, traffic=0)
        operations.append("invalidate();")
    # The last invalidation is redundant with the next epoch's clean state.
    # Fault recovery invalidates visibility before each subsequent epoch.
    operations.pop()
    paths = {}
    for name, values, width in (("source", sources, 32), ("writes", writes, 545)):
        path = directory / f"kv-m{mode}-r{resident}-s{seed}-{name}.hex"
        path.write_text("".join(f"{value & ((1 << width) - 1):0{(width + 3) // 4}x}\n"
                                for value in values))
        paths[name.upper()] = relative(path)
    substitutions = dict(MODE=mode, DIM=dim, RESIDENT=resident, SEED=seed,
                         SOURCE_COUNT=len(sources), WRITE_COUNT=len(writes),
                         OPERATIONS="\n".join(operations), **paths)
    bench = KV_TB
    for name, value in substitutions.items():
        bench = bench.replace(f"@{name}@", str(value))
    return bench
