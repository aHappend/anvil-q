"""Full legal context traversal and final production KV backing-address checks."""

from model import PRODUCTION, encode_kv, decode_kv, image_layout


CONTEXT_TB = r"""
module verify_kv_context;
  localparam MODE=@MODE@, CAP=@CAP@, GROUPS=128/CAP, RECORDS=4*GROUPS;
  reg clk=0; always #5 clk=~clk;
  reg rst_n=0, flush=0, cmd_valid=0;
  wire cmd_ready, done, error, idle, drain_done, fault;
  reg [1:0] cmd_op=0;
  reg [31:0] cmd_epoch=17, cmd_layer=35, cmd_pos=0, cmd_head=0, cmd_dim=0;
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
  anvil_q3_ht_kv_hierarchy #(.CACHE_MODE(MODE),.KV_RESIDENT_GROUPS(3)) dut(.*);
  reg [31:0] source [0:511], expected [0:511];
  reg [511:0] encoded [0:RECORDS-1];
  reg scratch_pending=0, memory_pending=0;
  reg [31:0] pending_source;
  reg [511:0] pending_record;
  reg [32:0] last_address=0;
  integer cycle=0, writes=0, reads=0, commits=0, compared=0, scratch_reads=0;
  integer write_index=0, record_index, group_id, head_id, which, due=0;
  reg [63:0] expected_address, relative_address;
  always @(posedge clk) begin
    cycle=cycle+1;
    if (cycle>300000000) $fatal(1,"KV_CONTEXT_PROGRESS");
    if (rst_n) begin
      if (fault!==0) $fatal(1,"KV_CONTEXT_FAULT");
      if (scratch_rsp_valid && scratch_rsp_ready) scratch_pending=0;
      if (scratch_req_valid && scratch_req_ready) begin
        if (scratch_pending || scratch_req_slot<3 || scratch_req_slot>4 ||
            scratch_req_index>=256) $fatal(1,"KV_CONTEXT_SCRATCH");
        pending_source=source[(scratch_req_slot-3)*256+scratch_req_index];
        scratch_pending=1; scratch_reads=scratch_reads+1;
      end
      if (memory_rsp_valid) begin
        if (!memory_pending || cycle<due) $fatal(1,"KV_CONTEXT_READ_LATENCY");
        memory_pending=0;
      end
      if (memory_req_valid && memory_req_ready) begin
        if (memory_req_byteenable!==64'hffffffffffffffff ||
            memory_req_address[5:0]!==0) $fatal(1,"KV_CONTEXT_RECORD_EXTENT");
        if (memory_req_write) begin
          group_id=write_index%GROUPS; head_id=(write_index/GROUPS)%2;
          which=write_index/(GROUPS*2);
          expected_address=64'h100000000+
            ((((35*2+which)*32768+commits)*2+head_id)*GROUPS+group_id)*64;
          if (write_index>=RECORDS || memory_req_address!==33'(expected_address) ||
              memory_req_wdata!==encoded[write_index])
            $fatal(1,"KV_CONTEXT_WRITE_ADDRESS_OR_DATA pos=%0d record=%0d actual=%h expected=%h",
                   commits,write_index,memory_req_address,expected_address);
          last_address=memory_req_address; writes=writes+1; write_index=write_index+1;
        end else begin
          if (commits!=32768 || memory_pending)
            $fatal(1,"KV_CONTEXT_READ_COMMIT_VISIBILITY");
          relative_address=64'(memory_req_address)-64'h100000000;
          group_id=(relative_address>>6)%GROUPS;
          head_id=((relative_address>>6)/GROUPS)%2;
          which=((relative_address>>6)/(GROUPS*2))/32768-70;
          expected_address=64'h100000000+
            ((((35*2+which)*32768+32767)*2+head_id)*GROUPS+group_id)*64;
          record_index=(which*2+head_id)*GROUPS+group_id;
          if (which<0 || which>1 || memory_req_address!==33'(expected_address))
            $fatal(1,"KV_CONTEXT_REFILL_ADDRESS");
          pending_record=encoded[record_index]; memory_pending=1; due=cycle+12;
          reads=reads+1;
        end
      end
    end
  end
  always @(negedge clk) if (rst_n) begin
    scratch_req_ready=1; memory_req_ready=1;
    scratch_rsp_valid=scratch_pending;
    scratch_rsp_rdata=scratch_pending ? pending_source : 32'd0;
    memory_rsp_valid=memory_pending && cycle+1>=due;
    memory_rsp_rdata=memory_rsp_valid ? pending_record : 512'd0;
  end
  integer position_id, component, kind_id, h;
  initial begin
    $readmemh("@SOURCE@",source); $readmemh("@EXPECTED@",expected);
    $readmemh("@ENCODED@",encoded);
    repeat(3) @(negedge clk); rst_n=1;
    for (position_id=0;position_id<32768;position_id=position_id+1) begin
      @(negedge clk);
      cmd_valid=1; cmd_op=0; cmd_pos=position_id; cmd_phase=position_id!=0;
      @(posedge clk); while (!cmd_ready) @(posedge clk);
      @(negedge clk); cmd_valid=0;
      @(posedge clk); while (!done) @(posedge clk);
      if (error!==0 || read_data!==0 || write_index!=RECORDS)
        $fatal(1,"KV_CONTEXT_COMMIT");
      commits=commits+1; write_index=0;
      @(posedge clk);
      if ((commits&4095)==0) $display("KV_CONTEXT_PROGRESS commits=%0d",commits);
    end
    if (last_address!==33'h@FINAL_ADDRESS@) $fatal(1,"KV_CONTEXT_FINAL_ADDRESS");
    for (kind_id=0;kind_id<2;kind_id=kind_id+1)
      for (h=0;h<2;h=h+1)
        for (component=0;component<128;component=component+1) begin
          @(negedge clk);
          cmd_valid=1; cmd_op=2'(kind_id+1); cmd_pos=32767; cmd_head=h; cmd_dim=component;
          @(posedge clk); while (!cmd_ready) @(posedge clk);
          @(negedge clk); cmd_valid=0;
          @(posedge clk); while (!done) @(posedge clk);
          if (error!==0 || read_data!==expected[(kind_id*2+h)*128+component])
            $fatal(1,"KV_CONTEXT_NUMERICAL");
          compared=compared+1;
          @(posedge clk);
        end
    if (writes!=32768*RECORDS || commits!=32768 || compared!=512 ||
        scratch_reads!=32768*512 || reads!=RECORDS)
      $fatal(1,"KV_CONTEXT_COVERAGE");
    $display("KV_CONTEXT_PASS mode=%0d context=32768 final_address=%h commits=%0d writes=%0d compared=%0d refills=%0d scratch_reads=%0d",
             MODE,last_address,commits,writes,compared,reads,scratch_reads);
    $finish;
  end
endmodule
"""


def context_bench(directory, relative, mode):
    cap = (16, 32, 64)[mode]
    sources, reconstructed, records = [], [], []
    for which in range(2):
        for head in range(2):
            values = [((index * 104729 + which * 37 + head * 101) % (1 << 22)) *
                      (-1 if index & 1 else 1) for index in range(128)]
            sources.extend(values)
            for start in range(0, 128, cap):
                group = values[start:start + cap]
                record = encode_kv(group, mode)
                records.append(int.from_bytes(record, "little"))
                reconstructed.extend(decode_kv(record, len(group), mode))
    substitutions = dict(MODE=mode, CAP=cap,
                         FINAL_ADDRESS=f"{0x100000000 + image_layout(PRODUCTION)['kv_bytes'][mode] - 64:x}")
    for name, values, width in (("source", sources, 32), ("expected", reconstructed, 32),
                                ("encoded", records, 512)):
        path = directory / "checkpoint-images" / f"kv-context-m{mode}-{name}.hex"
        path.parent.mkdir(exist_ok=True)
        path.write_text("".join(f"{value & ((1 << width) - 1):0{width // 4}x}\n"
                                for value in values))
        substitutions[name.upper()] = relative(path)
    bench = CONTEXT_TB
    for name, value in substitutions.items():
        bench = bench.replace(f"@{name}@", str(value))
    return bench
