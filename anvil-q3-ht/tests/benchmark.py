"""Five-domain measurements using public module interfaces and a common service."""

import hashlib
import re
import struct

from model import Geometry, Image, Inference
from parent import POLICY, PARENT_TB, parent_bench
from ddr import ddr_bench


PROJECTION_MONITOR = r"""
module verify_projection_monitor(
  input wire clk, rst_n, flush, cmd_valid, cmd_ready, done, error,
  input wire [31:0] cmd_layer,
  input wire [2:0] cmd_proj,
  input wire write_valid, write_ready, write_enable,
  input wire [31:0] write_row, write_col, write_data
);
  localparam COUNT=@PROJECTION_VALUES@, COMMANDS=@PROJECTION_COMMANDS@, MAX_ROWS=@MAX_ROWS@;
  reg [31:0] expected [0:COUNT-1];
  reg [MAX_ROWS-1:0] seen=0;
  integer cycle=0, commands=0, completed=0, compared=0, base=0, rows=0;
  integer started=0, cycles=0, active_layer=0, active_proj=0;
  reg active=0;
  initial $readmemh("@PROJECTION_FILE@",expected);
  always @(posedge clk) begin
    cycle=cycle+1;
    if (rst_n && !flush) begin
      if (cmd_valid && cmd_ready) begin
        if (active || cmd_layer!==32'((commands/7)%@LAYERS@) ||
            cmd_proj!==3'(commands%7)) $fatal(1,"BENCH_PROJECTION_ORDER");
        active=1; active_layer=cmd_layer; active_proj=cmd_proj;
        rows=cmd_proj==1 || cmd_proj==2 ? @KV_WIDTH@ :
          cmd_proj==4 || cmd_proj==5 ? @INTERMEDIATE@ : @HIDDEN@;
        seen=0; started=cycle; commands=commands+1;
      end
      if (write_valid && write_ready && write_enable) begin
        if (!active || write_col>=rows || write_row!==32'(
            active_proj==0 ? 2 : active_proj==1 ? 3 : active_proj==2 ? 4 :
            active_proj==3 ? 6 : active_proj==4 ? 9 : active_proj==5 ? 10 : 12))
          $fatal(1,"BENCH_PROJECTION_WRITE_IDENTITY");
        if (seen[write_col] || write_data!==expected[base+write_col])
          $fatal(1,"BENCH_PROJECTION_NUMERICAL layer=%0d proj=%0d row=%0d actual=%0d expected=%0d",
                 active_layer,active_proj,write_col,$signed(write_data),$signed(expected[base+write_col]));
        seen[write_col]=1; compared=compared+1;
      end
      if (done) begin
        if (!active || error!==0 || $countones(seen)!=rows)
          $fatal(1,"BENCH_PROJECTION_COMPLETION");
        $display("COMPONENT_PROJECTION layer=%0d proj=%0d cycles=%0d rows=%0d",
                 active_layer,active_proj,cycle-started,rows);
        cycles=cycles+cycle-started; completed=completed+1; base=base+rows; active=0;
      end
    end
  end
  final begin
    if (completed!=COMMANDS || commands!=completed || compared!=COUNT || active)
      $fatal(1,"BENCH_PROJECTION_COVERAGE");
    $display("DOMAIN_PROJECTION cycles=%0d operations=%0d compared=%0d",cycles,completed,compared);
  end
endmodule
"""

ATTENTION_MONITOR = r"""
module verify_attention_monitor(
  input wire clk, rst_n, flush, cmd_valid, cmd_ready, done, error,
  input wire [31:0] cmd_layer,
  input wire mem_req_valid, mem_req_ready, mem_req_write,
  input wire [31:0] mem_req_row, mem_req_col, mem_req_wdata
);
  localparam COUNT=@ATTENTION_VALUES@, COMMANDS=@ATTENTION_COMMANDS@, H=@HIDDEN@;
  reg [31:0] expected [0:COUNT-1];
  reg [H-1:0] seen=0;
  integer cycle=0, commands=0, completed=0, compared=0, started=0, cycles=0;
  reg active=0;
  initial $readmemh("@ATTENTION_FILE@",expected);
  always @(posedge clk) begin
    cycle=cycle+1;
    if (rst_n && !flush) begin
      if (cmd_valid && cmd_ready) begin
        if (active || cmd_layer!==32'(commands%@LAYERS@))
          $fatal(1,"BENCH_ATTENTION_ORDER");
        active=1; seen=0; started=cycle; commands=commands+1;
      end
      if (mem_req_valid && mem_req_ready && mem_req_write) begin
        if (!active || mem_req_row!==5 || mem_req_col>=H || seen[mem_req_col] ||
            mem_req_wdata!==expected[completed*H+mem_req_col])
          $fatal(1,"BENCH_ATTENTION_NUMERICAL row=%0d actual=%0d expected=%0d",
                 mem_req_col,$signed(mem_req_wdata),$signed(expected[completed*H+mem_req_col]));
        seen[mem_req_col]=1; compared=compared+1;
      end
      if (done) begin
        if (!active || error!==0 || $countones(seen)!=H)
          $fatal(1,"BENCH_ATTENTION_COMPLETION");
        cycles=cycles+cycle-started; completed=completed+1; active=0;
      end
    end
  end
  final begin
    if (completed!=COMMANDS || commands!=completed || compared!=COUNT || active)
      $fatal(1,"BENCH_ATTENTION_COVERAGE");
    $display("DOMAIN_ATTENTION cycles=%0d operations=%0d compared=%0d",cycles,completed,compared);
  end
endmodule
"""

KV_MONITOR = r"""
module verify_kv_monitor(
  input wire clk, rst_n, flush, cmd_valid, cmd_ready, done, error,
  input wire [1:0] cmd_op,
  input wire [31:0] cmd_layer, cmd_pos, cmd_head, cmd_dim,
  input wire signed [31:0] read_data
);
  localparam COUNT=@KV_VALUES@, WIDTH=@KV_WIDTH@, D=@HEAD_DIM@, LAYERS=@LAYERS@;
  reg [31:0] expected [0:COUNT-1];
  integer cycle=0, completed=0, compared=0, commits=0, started=0, cycles=0;
  integer active_op=0, selected=0, latest_token=0;
  reg active=0;
  initial $readmemh("@KV_FILE@",expected);
  always @(posedge clk) begin
    cycle=cycle+1;
    if (rst_n && !flush) begin
      if (cmd_valid && cmd_ready) begin
        if (active || cmd_op>2) $fatal(1,"BENCH_KV_OWNERSHIP");
        active=1; active_op=cmd_op; started=cycle;
        if (cmd_op==0) latest_token=commits/LAYERS;
        else begin
          selected=latest_token<2 ? cmd_pos : 2;
          selected=((selected*LAYERS+cmd_layer)*2+cmd_op-1)*WIDTH+cmd_head*D+cmd_dim;
          if (selected>=COUNT) $fatal(1,"BENCH_KV_REFERENCE_EXTENT");
        end
      end
      if (done) begin
        if (!active || error!==0) $fatal(1,"BENCH_KV_COMPLETION");
        if (active_op!=0) begin
          if (read_data!==expected[selected])
            $fatal(1,"BENCH_KV_NUMERICAL actual=%0d expected=%0d",
                   read_data,$signed(expected[selected]));
          compared=compared+1;
        end else commits=commits+1;
        cycles=cycles+cycle-started; completed=completed+1; active=0;
      end
    end
  end
  final begin
    if (commits!=@ATTENTION_COMMANDS@ || compared==0 || active)
      $fatal(1,"BENCH_KV_COVERAGE");
    $display("DOMAIN_KV cycles=%0d operations=%0d compared=%0d commits=%0d",
             cycles,completed,compared,commits);
  end
endmodule
"""


def component_monitors(directory, relative, oracle, geometry, parent=False, banks=1):
    traces = oracle.traces
    vectors = dict(
        projection=[value for token in traces for layer in token["layers"]
                    for projection in range(7) for value in layer["projections"][projection]],
        attention=[value for token in traces for layer in token["layers"] for value in layer["context"]],
        kv=[value for token in traces for layer in token["layers"]
            for name in ("keys", "values") for value in layer[name]])
    prefix = (f"{'parent' if parent else 'ht'}-b{banks}-m{oracle.mode}-"
              f"{oracle.image.digest[:16]}")
    substitutions = dict(PROJECTION_VALUES=len(vectors["projection"]),
                         ATTENTION_VALUES=len(vectors["attention"]), KV_VALUES=len(vectors["kv"]),
                         PROJECTION_COMMANDS=len(traces) * geometry.layers * 7,
                         ATTENTION_COMMANDS=len(traces) * geometry.layers,
                         MAX_ROWS=max(geometry.hidden, geometry.intermediate),
                         LAYERS=geometry.layers, HIDDEN=geometry.hidden,
                         INTERMEDIATE=geometry.intermediate,
                         KV_WIDTH=geometry.kv_heads * geometry.head_dim, HEAD_DIM=geometry.head_dim)
    for kind, values in vectors.items():
        path = directory / "checkpoint-images" / f"{prefix}-{kind}-expected.hex"
        path.parent.mkdir(exist_ok=True)
        path.write_text("".join(f"{value & 0xFFFFFFFF:08x}\n" for value in values))
        substitutions[f"{kind.upper()}_FILE"] = relative(path)
    if parent:
        binds = f"""
bind anvil_q3_gemv verify_projection_monitor projection_observer(
  .clk(clk),.rst_n(rst_n),.flush(flush),.cmd_valid(cmd_valid),.cmd_ready(cmd_ready),
  .done(done),.error(error),.cmd_layer(cmd_layer),.cmd_proj(cmd_proj),
  .write_valid(c_req_valid[{banks}]),.write_ready(c_req_ready[{banks}]),
  .write_enable(c_req_write[{banks}]),.write_row(c_req_row[{banks * 32}+:32]),
  .write_col(c_req_col[{banks * 32}+:32]),.write_data(c_req_wdata[{banks * 32}+:32]));
"""
        attention, kv = "anvil_q3_gqa_attention", "anvil_q3_kv_cache"
    else:
        binds = """
bind anvil_q3_ht_projection verify_projection_monitor projection_observer(
  .clk(clk),.rst_n(rst_n),.flush(flush),.cmd_valid(cmd_valid),.cmd_ready(cmd_ready),
  .done(done),.error(error),.cmd_layer(cmd_layer),.cmd_proj(cmd_proj),
  .write_valid(mem_req_valid),.write_ready(mem_req_ready),.write_enable(mem_req_write),
  .write_row(mem_req_row),.write_col(mem_req_col),.write_data(mem_req_wdata));
"""
        attention, kv = "anvil_q3_ht_attention", "anvil_q3_ht_kv_hierarchy"
    binds += f"""
bind {attention} verify_attention_monitor attention_observer(
  .clk(clk),.rst_n(rst_n),.flush(flush),.cmd_valid(cmd_valid),.cmd_ready(cmd_ready),
  .done(done),.error(error),.cmd_layer(cmd_layer),
  .mem_req_valid(mem_req_valid),.mem_req_ready(mem_req_ready),.mem_req_write(mem_req_write),
  .mem_req_row(mem_req_row),.mem_req_col(mem_req_col),.mem_req_wdata(mem_req_wdata));
bind {kv} verify_kv_monitor kv_observer(
  .clk(clk),.rst_n(rst_n),.flush(flush),.cmd_valid(cmd_valid),.cmd_ready(cmd_ready),
  .done(done),.error(error),.cmd_op(cmd_op),.cmd_layer(cmd_layer),.cmd_pos(cmd_pos),
  .cmd_head(cmd_head),.cmd_dim(cmd_dim),.read_data(read_data));
"""
    if parent:
        for port in ("valid", "ready", "write"):
            binds = binds.replace(f".mem_req_{port}(mem_req_{port})",
                                  f".mem_req_{port}(c_req_{port}[0])")
        for port in ("row", "col", "wdata"):
            binds = binds.replace(f".mem_req_{port}(mem_req_{port})",
                                  f".mem_req_{port}(c_req_{port}[0+:32])")
    text = PROJECTION_MONITOR + ATTENTION_MONITOR + KV_MONITOR + binds
    for key, value in substitutions.items():
        text = text.replace(f"@{key}@", str(value))
    return text


def component_records(output):
    records = {}
    for domain, marker in ((2, "DOMAIN_PROJECTION"), (3, "DOMAIN_KV"), (4, "DOMAIN_ATTENTION")):
        lines = [line for line in output.splitlines() if line.startswith(marker + " ")]
        if len(lines) != 1:
            raise AssertionError(f"missing or duplicate benchmark domain summary: {marker}")
        values = {key: int(value) for key, value in re.findall(r"(\w+)=(\d+)", lines[0])}
        if not all(values.get(key, 0) > 0 for key in ("cycles", "operations", "compared")):
            raise AssertionError(f"empty benchmark domain: {marker}")
        records[domain] = values
    return records


STREAM_MEMORY = r"""
  function automatic [31:0] stream_value(input integer index);
    reg [63:0] pair_value;
    begin
      pair_value=64'((index/16)*64)^(64'h9e3779b97f4a7c15*64'((index%16)/2+1));
      stream_value=(index&1) ? pair_value[63:32] : pair_value[31:0];
    end
  endfunction
  function automatic [31:0] read_logical(input integer kind_id, input integer layer_id,
                                        input integer proj_id, input integer row_id,
                                        input integer col_id);
    begin
      if (kind_id!=1 || layer_id!=0 || proj_id!=0 || col_id!=0 ||
          row_id<0 || row_id>=262144) $fatal(1,"STREAM_LOGICAL_ADDRESS");
      read_logical=stream_value(row_id);
    end
  endfunction
"""

STREAM_CLIENT = r"""
  reg [BANKS-1:0] c_req_valid=0, c_req_write=0, c_rsp_ready=0;
  wire [BANKS-1:0] c_req_ready, c_rsp_valid, c_rsp_error;
  reg [BANKS*4-1:0] c_req_kind=0;
  reg [BANKS*32-1:0] c_req_layer=0, c_req_row=0, c_req_col=0, c_req_wdata=0;
  reg [BANKS*3-1:0] c_req_proj=0;
  wire [BANKS*32-1:0] c_rsp_rdata;
  wire scheduler_idle, scheduler_drained, scheduler_fault;
  reg flush=0;
  integer next_word [0:BANKS-1], response_word [0:BANKS-1];
  integer first_operation=-1, last_operation=-1, upstream=0, responses=0, n;
  assign token_ready=0; assign logit_valid=0; assign done=0; assign error=0; assign cancel_done=0;
  anvil_q3_bank_scheduler #(.BANKS(BANKS),.CLIENTS(BANKS),.QUEUE_DEPTH(3)) dut(
    .clk(clk),.rst_n(rst_n),.flush(flush),
    .idle(scheduler_idle),.drain_done(scheduler_drained),.fault(scheduler_fault),
    .c_req_valid(c_req_valid),.c_req_ready(c_req_ready),.c_req_write(c_req_write),
    .c_req_kind(c_req_kind),.c_req_layer(c_req_layer),.c_req_proj(c_req_proj),
    .c_req_row(c_req_row),.c_req_col(c_req_col),.c_req_wdata(c_req_wdata),
    .c_rsp_valid(c_rsp_valid),.c_rsp_ready(c_rsp_ready),
    .c_rsp_rdata(c_rsp_rdata),.c_rsp_error(c_rsp_error),
    .mem_req_valid(mem_req_valid),.mem_req_ready(mem_req_ready),.mem_req_write(mem_req_write),
    .mem_req_kind(mem_req_kind),.mem_req_layer(mem_req_layer),.mem_req_proj(mem_req_proj),
    .mem_req_row(mem_req_row),.mem_req_col(mem_req_col),.mem_req_wdata(mem_req_wdata),
    .mem_req_tag(mem_req_tag),.mem_rsp_valid(mem_rsp_valid),.mem_rsp_ready(mem_rsp_ready),
    .mem_rsp_rdata(mem_rsp_rdata),.mem_rsp_error(mem_rsp_error),.mem_rsp_tag(mem_rsp_tag));
  always @(posedge clk) if (rst_n) begin
    if (scheduler_fault!==0) $fatal(1,"STREAM_SCHEDULER_FAULT");
    for (n=0;n<BANKS;n=n+1) begin
      if (c_req_valid[n] && c_req_ready[n]) begin
        if (first_operation<0) first_operation=cycle;
        next_word[n]=next_word[n]+BANKS; upstream=upstream+1;
      end
      if (c_rsp_valid[n] && c_rsp_ready[n]) begin
        if (response_word[n]>=262144 || c_rsp_error[n]!==0 ||
            c_rsp_rdata[n*32+:32]!==stream_value(response_word[n]))
          $fatal(1,"STREAM_SCALAR_NUMERICAL client=%0d index=%0d",n,response_word[n]);
        response_word[n]=response_word[n]+BANKS; responses=responses+1; last_operation=cycle;
      end
    end
  end
  always @(negedge clk) if (rst_n) begin
    c_rsp_ready='1;
    for (n=0;n<BANKS;n=n+1) begin
      c_req_valid[n]=next_word[n]<262144;
      c_req_kind[n*4+:4]=1;
      c_req_row[n*32+:32]=next_word[n];
    end
  end
  initial begin
    for (b=0;b<BANKS;b=b+1) begin
      qh[b]=0; qt[b]=0; qc[b]=0; next_word[b]=b; response_word[b]=b;
    end
    for (k=0;k<16;k=k+1) bytes_by_kind[k]=0;
    repeat(3) @(negedge clk); rst_n=1;
    @(posedge clk); while (responses!=262144) @(posedge clk);
    @(posedge clk); while (!scheduler_idle) @(posedge clk);
    if (upstream!=262144 || accepted!=262144 || serviced!=accepted || completed!=accepted ||
        read_bytes!=1048576 || write_bytes!=0 || maximum_queued>=64)
      $fatal(1,"STREAM_SCALAR_CONSERVATION");
    $display("PARENT_STREAM_PASS compared=%0d commands=%0d physical_bytes=%0d useful_bytes=1048576 first=%0d last=%0d window=%0d first_operation=%0d last_operation=%0d operation_cycles=%0d max_queued=%0d",
             responses,accepted,read_bytes,first_service,last_service,last_service-first_service+1,
             first_operation,last_operation,last_operation-first_operation+1,maximum_queued);
    $finish;
  end
endmodule
"""


def parent_stream_bench(banks, seed):
    if banks not in (1, 4, 8):
        raise ValueError("illegal streaming parent comparison mapping")
    bench = PARENT_TB
    bench = bench.replace("anvil_q3_top #(@PARAMETERS@) dut(.*);", STREAM_CLIENT.split("  initial begin")[0])
    start = bench.index("  function automatic [32:0] matrix_base")
    end = bench.index("  always @(posedge clk)", start)
    bench = bench[:start] + STREAM_MEMORY + bench[end:]
    start = bench.index("  task run_token")
    bench = bench[:start] + "  initial begin" + STREAM_CLIENT.split("  initial begin", 1)[1]
    bench = bench.replace("module verify_parent;", "module verify_parent_stream;")
    substitutions = dict(BANKS=banks, H=16, I=16, D=2, LAYERS=1, CONTEXT=3,
                         IMAGE_RECORDS=1, VOCAB=3, N=1, SEED=seed)
    for key, value in substitutions.items():
        bench = bench.replace(f"@{key}@", str(value))
    return bench


def numbers(output, marker):
    lines = [line for line in output.splitlines() if line.startswith(marker + " ")]
    if len(lines) != 1:
        raise AssertionError(f"expected exactly one {marker} record")
    return {key: int(value) for key, value in re.findall(r"(\w+)=(\d+)", lines[0])}


def token_cycles(output, parent=False):
    marker = "PARENT_TOKEN " if parent else "TOKEN_COMPARED "
    values = [int(re.search(r"\bcycles=(\d+)", line)[1])
              for line in output.splitlines() if line.startswith(marker)]
    if len(values) != 3 or min(values) <= 0:
        raise AssertionError("benchmark requires three complete token operation windows")
    return values


def execute_benchmark(run, integration, simulate, relative, root, seeds=(17, 89, 101),
                      banks_matrix=(1, 4, 8, 16), modes=(0, 1, 2)):
    """Each invocation regenerates its real parent baselines; no cross-run cache."""
    run.tool("verilator")
    ht_hash = hashlib.sha256("".join(
        run.receipt["source_sha256"][str(path.relative_to(root))]
        for path in sorted((root / "rtl").glob("*.sv"))).encode()).hexdigest()
    parent_hash = hashlib.sha256("".join(
        run.receipt["source_sha256"][str(path.relative_to(root))]
        for path in sorted((root / "anvil_q3_reference/rtl").glob("*.sv"))).encode()).hexdigest()
    baselines = {}
    geometry = Geometry()
    stream_digest = hashlib.sha256()
    for address in range(0, 1048576, 64):
        stream_digest.update(b"".join(struct.pack(
            "<Q", address ^ ((0x9E3779B97F4A7C15 * (lane + 1)) & ((1 << 64) - 1)))
            for lane in range(8)))
    for seed in seeds:
        for mode in modes:
            for banks in banks_matrix:
                parent_banks = min(banks, 8)
                key = (seed, mode, parent_banks)
                if key not in baselines:
                    image = Image(geometry, seed)
                    oracle = Inference(image, mode)
                    for token, pos, fresh in ((0, 0, True), (1, 1, False), (2, 0, True)):
                        oracle.token(token, pos, fresh)
                    bench, metadata = parent_bench(run.path, relative, seed, parent_banks, mode)
                    bench += component_monitors(run.path, relative, oracle, geometry, True, parent_banks)
                    label = f"baseline-b{parent_banks}-m{mode}-s{seed}"
                    parent_output = simulate(run, label, bench, top="verify_parent",
                                             rtl_directory=root / "anvil_q3_reference/rtl")
                    stream_output = simulate(
                        run, f"{label}-stream", parent_stream_bench(parent_banks, seed),
                        top="verify_parent_stream", rtl_directory=root / "anvil_q3_reference/rtl")
                    baseline = dict(id=label, metadata=metadata, summary=parent_output,
                                    components=component_records(parent_output),
                                    stream=numbers(stream_output, "PARENT_STREAM_PASS"),
                                    token_cycles=token_cycles(parent_output, True))
                    baselines[key] = baseline
                    run.receipt["results"].append(dict(case="parent-baseline", **baseline))
                    run.save()
                baseline = baselines[key]
                result = integration(run, seed=seed, banks=banks, mode=mode, tokens=3,
                                     prefix="benchmark-", benchmark=True)
                ht_output = result["summary"]
                components = component_records(ht_output)
                ht_tokens = token_cycles(ht_output)
                stream_output = simulate(
                    run, f"ht-stream-b{banks}-m{mode}-s{seed}",
                    ddr_bench(seed, stress=False, count=256, base=0),
                    top="verify_ddr")
                stream = numbers(stream_output, "DDR_PASS")
                if (stream["compared"] != 16384 or stream["fill_consume"] == 0
                        or stream["operation_cycles"] >= baseline["stream"]["operation_cycles"]):
                    raise AssertionError("HT streaming useful throughput must exceed measured mapped parent")
                if baseline["metadata"]["image_sha256"] != result["image_sha256"]:
                    raise AssertionError("parent/HT workload image mismatch")
                for name, value in POLICY.items():
                    if baseline["metadata"][name] != value:
                        raise AssertionError(f"unequal common-service policy: {name}")
                lossless = Inference(Image(geometry, seed), 0)
                lossless_logits = [value for token, pos, fresh in
                                   ((0, 0, True), (1, 1, False), (2, 0, True))
                                   for value in lossless.token(token, pos, fresh)]
                differences = [abs(a - b) for a, b in zip(result["logits"], lossless_logits)]
                ht_traffic = [
                    {key: int(value) for key, value in re.findall(r"(\w+)=(\d+)", line)}
                    for line in ht_output.splitlines() if line.startswith("HT_TRAFFIC ")]
                parent_traffic = [
                    {key: int(value) for key, value in re.findall(r"(\w+)=(\d+)", line)}
                    for line in baseline["summary"].splitlines() if line.startswith("PARENT_TRAFFIC ")]
                if len(ht_traffic) != 9 or not parent_traffic:
                    raise AssertionError("missing interface traffic class accounting")
                for domain in range(1, 6):
                    ht_cycles = (stream["operation_cycles"] if domain == 1 else
                                 sum(ht_tokens) if domain == 5 else components[domain]["cycles"])
                    parent_cycles = (baseline["stream"]["operation_cycles"] if domain == 1 else
                                     sum(baseline["token_cycles"]) if domain == 5 else
                                     baseline["components"][domain]["cycles"])
                    operations = (16384 if domain == 1 else 3 if domain == 5 else
                                  components[domain]["operations"])
                    record = dict(
                        domain=domain, seed=seed, cache_mode=mode, ht_banks=banks,
                        parent_banks=parent_banks,
                        comparison_kind="ht16_vs_parent8" if banks == 16 else "matched_banks",
                        parent_profile=3, parent_baseline_id=baseline["id"],
                        shared_baseline=(banks == 16 and 8 in banks_matrix),
                        workload_id="qweight-4096x512-contiguous-v1" if domain == 1 else
                        "three-token-full-decoder-components-v1",
                        dimensions=dict(inputs=4096, outputs=512) if domain == 1 else geometry.__dict__,
                        image_kind="synthetic",
                        image_digest=stream_digest.hexdigest() if domain == 1 else result["image_sha256"],
                        ht_source_sha256=ht_hash, parent_source_sha256=parent_hash,
                        burst_beats=16, ht_outstanding_limit=4 if domain == 1 else 8,
                        ht_prefetch_outstanding_limit=4,
                        parent_outstanding_limit=parent_banks * 3, stall_schedule_id="unstalled-v1",
                        operations=operations, ht_cycles=ht_cycles, parent_cycles=parent_cycles,
                        ratio_numerator=parent_cycles, ratio_denominator=ht_cycles,
                        cycle_speedup=parent_cycles / ht_cycles,
                        windows="command-transfer-through-completion; nested component windows are not additive",
                        ht_expected_logits=result["logits"],
                        parent_expected_logits=baseline["metadata"]["expected_logits"],
                        numerical_mismatches=0, **POLICY)
                    record.update(
                        ht_traffic_classes=ht_traffic, parent_traffic_classes=parent_traffic,
                        traffic_scope="complete three-token workload; host loading/readback excluded",
                        compressed_vs_lossless_max_logit_error=max(differences),
                        compressed_vs_lossless_changed_logits=sum(value != 0 for value in differences),
                        ht_service=numbers(ht_output, "HT_SERVICE"),
                        parent_service=numbers(baseline["summary"], "PARENT_PASS"))
                    if record["ht_expected_logits"] != record["parent_expected_logits"]:
                        raise AssertionError("mode-specific parent/HT numerical mismatch")
                    if domain == 1:
                        record.update(
                            ht_only_host_loader=numbers(ht_output, "HT_LOADER"),
                            host_loader_comparison="HT-only; parent exposes no host loader",
                            host_loader_image_digest=result["image_sha256"],
                            streaming_payload="packed-qweight-only; zeros/scales measured in projection domain",
                            useful_bytes=1048576, ht_physical_bytes=stream["returns"] * 64,
                            parent_physical_bytes=baseline["stream"]["physical_bytes"],
                            ht_commands=stream["commands"],
                            parent_commands=baseline["stream"]["commands"],
                            ht_steady_window={key: stream[key] for key in ("first", "last", "window", "returns")},
                            parent_steady_window={key: baseline["stream"][key]
                                                  for key in ("first", "last", "window")},
                            ht_fill_consume=stream["fill_consume"],
                            useful_ratio_numerator=baseline["stream"]["operation_cycles"],
                            useful_ratio_denominator=stream["operation_cycles"])
                    run.receipt["results"].append(dict(case="five-domain-benchmark", **record))
                run.save()
    expected_records = len(seeds) * len(modes) * len(banks_matrix) * 5
    records = [record for record in run.receipt["results"]
               if record.get("case") == "five-domain-benchmark"]
    if len(records) != expected_records:
        raise AssertionError(f"benchmark matrix incomplete: {len(records)}/{expected_records}")
