"""Metadata v1/v2 representation checks, not official-profile equivalence."""

import json
import struct

from storage import KINDS, boot_test, packed, synthetic_image


V2 = {0: 2, 8: 0x00100000, 24: 0x00090000, 25: 0x00100000}


def manifest_test(evidence, seed, simulator):
    fixture = synthetic_image(257)
    directory = evidence.path / f"metadata-manifest-s{seed}-{simulator}-input"
    directory.mkdir()
    extent = 16384
    memory = [0] * extent
    for kind, data in fixture["segments"].items():
        base = fixture["destinations"][kind]
        for offset in range(0, len(data), 4):
            memory[(base + offset) // 4] = int.from_bytes(data[offset:offset + 4], "little")
    image = directory / "ddr.hex"
    image.write_text("".join(f"{word:08x}\n" for word in memory), encoding="ascii")
    cases = [
        ("unchanged-v1", {}, 0),
        ("explicit-v2", V2, 0),
        *[(f"unsupported-{version}", {0: version}, 6)
          for version in (0, 3, 0xFFFFFFFF)],
        *[(f"v1-reserved-{index}", {index: 1}, 6) for index in range(24, 32)],
        *[(f"v2-reserved-{index}", {**V2, index: 1}, 6) for index in range(26, 32)],
        ("v2-explicit-zero-not-inherited", {**V2, 24: 0, 25: 0}, 0),
        ("recovery-v1", {}, 0),
        ("recovery-v2", V2, 0),
    ]
    (directory / "cases.json").write_text(json.dumps({
        "scope": "Structural metadata validation only; version labels do not certify tables",
        "seed": seed, "cases": cases,
    }, indent=2) + "\n")
    scenarios = []
    for index, (name, overrides, error) in enumerate(cases):
        data = bytearray(fixture["segments"][0x200])
        for word, value in overrides.items():
            struct.pack_into("<I", data, word * 4, value)
        expected = int.from_bytes(data, "little")
        scenarios.append(f"""
    expected_metadata=1024'h{expected:x};
    for (integer word_index=0;word_index<32;word_index=word_index+1)
      memory[{fixture['destinations'][0x200] // 4}+word_index]=
        expected_metadata[word_index*32+:32];
    run_case({index},8'h{error:02x});
""")
    counts = [0] + [struct.unpack_from("<I", fixture["segments"][kind], 12)[0]
                    for kind in range(0x201, 0x210)]
    bench = r"""
module bench;
  reg clk=0,rst_n,start=0;
  always #5 clk=~clk;
  wire busy,done,valid_manifest,error;
  wire [7:0] error_code;
  wire [1023:0] staged_metadata;
  wire [511:0] staged_table_counts;
  wire ddr_req_valid,ddr_rsp_ready;
  wire [63:0] ddr_req_addr;
  reg ddr_req_ready=0,ddr_rsp_valid=0,ddr_rsp_error=0;
  reg [31:0] ddr_rsp_rdata=0;
  wire [223:0] staged_config_words=224'h@CONFIG@;
  wire [1279:0] staged_segment_bases=1280'h@BASES@;
  wire [1279:0] staged_segment_bytes=1280'h@LENGTHS@;
  anvil_edge_manifest_validator #(
    .NUM_LAYERS(1),.HIDDEN_SIZE(8),.INTERMEDIATE_SIZE(8),
    .NUM_Q_HEADS(1),.NUM_KV_HEADS(1),.HEAD_DIM(8),.GROUP_SIZE(8),
    .VOCAB_SIZE(257),.MAX_SEQ_LEN(4),.DDR_BYTES(65536)
  ) dut(.*);
  reg [31:0] memory[0:16383];
  reg [1023:0] expected_metadata;
  reg [31:0] rng=@SEED@;
  reg pending=0,held=0;
  reg [63:0] pending_address=0,held_address=0;
  integer delay_count=0,requests=0,responses=0,comparisons=0;
  integer accepted_cases=0,rejected_cases=0,stalls=0,metadata_reads=0;
  integer successes=0;
  task automatic reset_check;
    begin
      if ({busy,done,valid_manifest,error,error_code,staged_metadata,
           staged_table_counts,ddr_req_valid,ddr_req_addr,ddr_rsp_ready}!==1614'd0)
        $fatal(1,"METADATA_RESET t=%0t",$time);
    end
  endtask
  always @(posedge clk or negedge clk) if (!rst_n) reset_check();
  always @(negedge clk) if (rst_n) begin
    rng=rng^(rng<<13); rng=rng^(rng>>17); rng=rng^(rng<<5);
    ddr_req_ready=rng[0];
    if (pending && !ddr_rsp_valid) begin
      if (delay_count==0) begin
        ddr_rsp_valid<=1;
        ddr_rsp_rdata=memory[pending_address>>2];
      end else delay_count=delay_count-1;
    end
  end
  always @(posedge clk) if (rst_n) begin
    if ((^{busy,done,valid_manifest,error,error_code,staged_metadata,
            staged_table_counts,ddr_req_valid,ddr_req_addr,ddr_rsp_ready})===1'bx)
      $fatal(1,"METADATA_XZ");
    if (!valid_manifest && {staged_metadata,staged_table_counts}!==0)
      $fatal(1,"METADATA_PARTIAL_PUBLICATION");
    if (done) successes=successes+1;
    if (held && (!ddr_req_valid || ddr_req_addr!==held_address))
      $fatal(1,"METADATA_REQUEST_HOLD");
    held=ddr_req_valid && !ddr_req_ready; held_address=ddr_req_addr;
    if (held) stalls=stalls+1;
    if (ddr_rsp_valid && ddr_rsp_ready) begin
      if (!pending) $fatal(1,"METADATA_ORPHAN_RESPONSE");
      pending=0; responses=responses+1; ddr_rsp_valid<=0;
    end
    if (ddr_req_valid && ddr_req_ready) begin
      if (pending || ddr_req_addr[1:0]!==0 || ddr_req_addr>=65536)
        $fatal(1,"METADATA_REQUEST_PROTOCOL");
      pending=1; pending_address=ddr_req_addr;
      delay_count=1+rng[3:2]; requests=requests+1;
      if (ddr_req_addr>=@META_BASE@ && ddr_req_addr<@META_BASE@+128)
        metadata_reads=metadata_reads+1;
      comparisons=comparisons+1;
    end
  end
  task automatic tick; begin @(posedge clk); #1; end endtask
  task automatic run_case(input integer case_id,input [7:0] code);
    integer previous_requests,previous_metadata_reads,previous_successes;
    begin
      previous_requests=requests; previous_metadata_reads=metadata_reads;
      previous_successes=successes;
      @(negedge clk); #1; start=1;
      tick();
      if (!busy || done || valid_manifest || error ||
          staged_metadata!==0 || staged_table_counts!==0)
        $fatal(1,"METADATA_RELOAD_ISOLATION case=%0d",case_id);
      @(negedge clk); #1; start=0;
      while (!valid_manifest && !error) tick();
      if (pending || ddr_rsp_valid || requests!=responses ||
          requests<=previous_requests || metadata_reads-previous_metadata_reads!=32)
        $fatal(1,"METADATA_RESPONSE_COUNTS case=%0d",case_id);
      if (code==0) begin
        if (error || !done || error_code!==0 ||
            staged_metadata!==expected_metadata ||
            staged_table_counts!==512'h@COUNTS@)
          $fatal(1,"METADATA_ACCEPT case=%0d",case_id);
        accepted_cases=accepted_cases+1;
      end else begin
        if (!error || valid_manifest || done || error_code!==code ||
            staged_metadata!==0 || staged_table_counts!==0)
          $fatal(1,"METADATA_REJECT case=%0d code=%h",case_id,error_code);
        rejected_cases=rejected_cases+1;
      end
      repeat (4) begin
        tick();
        if (done || ddr_req_valid || (code!=0 &&
            (!error || error_code!==code || valid_manifest || staged_metadata!==0)))
          $fatal(1,"METADATA_STICKY_OR_EXTRA_WORK case=%0d",case_id);
      end
      if (successes-previous_successes!=(code==0 ? 1 : 0))
        $fatal(1,"METADATA_DONE_COUNT case=%0d",case_id);
      comparisons=comparisons+1;
      $display("METADATA_CASE %0d code=%0d",case_id,code);
      if (code!=0) begin
        @(negedge clk); #1; rst_n=0;
        repeat (2) tick();
        @(negedge clk); #1; rst_n=1;
      end
    end
  endtask
  initial begin
    rst_n=0; #0; reset_check();
    $readmemh("@MEMORY@",memory);
    repeat (2) tick();
    @(negedge clk); #1; rst_n=1;
    @SCENARIOS@
    if (accepted_cases!=5 || rejected_cases!=17 || stalls==0 ||
        requests!=responses || pending)
      $fatal(1,"METADATA_COVERAGE accepted=%0d rejected=%0d",accepted_cases,rejected_cases);
    $display("METADATA_COVERAGE accepted=%0d rejected=%0d reads=%0d stalls=%0d",
             accepted_cases,rejected_cases,responses,stalls);
    $display("COMPARED %0d",comparisons); $finish;
  end
  initial begin
    repeat (100000) @(posedge clk);
    $fatal(1,"METADATA_CYCLE_BOUND");
  end
endmodule
"""
    values = {
        "CONFIG": packed(fixture["config"], 32),
        "BASES": packed([fixture["destinations"][kind] for kind in KINDS], 64),
        "LENGTHS": packed([len(fixture["segments"][kind]) for kind in KINDS], 64),
        "COUNTS": packed(counts, 32), "SEED": str(seed),
        "META_BASE": str(fixture["destinations"][0x200]),
        "MEMORY": evidence.relative(image), "SCENARIOS": "\n".join(scenarios),
    }
    for key, value in values.items():
        bench = bench.replace(f"@{key}@", value)
    evidence.simulate(f"metadata-manifest-s{seed}-{simulator}", bench, [
        "rtl/anvil_edge_numeric_pkg.sv", "rtl/anvil_edge_parameters.sv",
        "rtl/anvil_edge_boot_segment_reader.sv", "rtl/anvil_edge_manifest_validator.sv",
    ], None, simulator=simulator)


def run_metadata(evidence):
    evidence.tools(("iverilog", "vvp", "verilator", "g++", "make"))
    manifest_test(evidence, 17, "iverilog")
    evidence.run_cases([
        (f"metadata-manifest-{seed}",
         lambda scope, seed=seed: manifest_test(scope, seed, "verilator"))
        for seed in (1, 17, 89)
    ] + [
        (f"metadata-boot-reload-{seed}", lambda scope, seed=seed:
         boot_test(scope, 257, seed, label="metadata-v1-v2-reloads",
                   reload_metadata=[
                       (V2, 0),
                       ({**V2, 26: 1}, 6),
                       ({}, 0),
                   ]))
        for seed in (1, 17, 89)
    ])
