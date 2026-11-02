"""Measured operator comparisons; no resource or clock-based speed inference."""

from decimal import Decimal, localcontext
import math
import random
import re
from fractions import Fraction

from reference import approximation_interval, bits32, f32, as_fraction, mx_decode, round_dyadic
from architecture import bf16, quantize_group


def measured_cycles(run, stem, domain):
    log = run.path / f"{stem}-simulate.stdout.txt"
    rows = []
    for line in log.read_text().splitlines():
        if line.startswith("MEASUREMENT "):
            fields = {key: int(value) for key, value in
                      re.findall(r"\b([a-z][a-z0-9_]*)=(\d+)", line)}
            if not {"run", "parent_cycles", "fp2_cycles"} <= fields.keys():
                raise AssertionError(f"{domain}: incomplete cycle measurement")
            rows.append(fields)
    if len(rows) != 2 or [row["run"] for row in rows] != [0, 1]:
        raise AssertionError(f"{domain}: missing distinct cold and warm measurements")
    if any(row["fp2_cycles"] >= row["parent_cycles"] for row in rows):
        raise AssertionError(f"{domain}: non-improving measured cycles")
    run.receipt.setdefault("benchmarks", []).append({
        "domain": domain, "measurements": rows,
        "raw_stdout": str(run.relative / log.name),
    })
    return rows


def projection_benchmark(run, root, compile_and_run, mx, seed=17):
    """Execute matched 896-by-128 K projections and count accepted transport bytes."""
    hidden, outputs = 896, 128
    stem = f"benchmark-gemv-{'mx' if mx else 'bf16'}-{seed}"
    directory = run.path / stem
    directory.mkdir()
    images = directory / "checkpoint-images"
    images.mkdir()
    rng = random.Random(seed)
    activations = [bf16(rng.randint(-7, 7) / 16) for _ in range(hidden)]
    weights = [[bf16(rng.randint(-7, 7) / 1024) for _ in range(outputs)]
               for _ in range(hidden)]
    beats, scales, decoded = [], [], []
    for row in weights:
        if mx:
            codes, row_scales, decoded_row = [], [], []
            for first in range(0, outputs, 32):
                group, scale = quantize_group(row[first:first + 32])
                codes.extend(group)
                row_scales.append(scale)
                decoded_row.extend(mx_decode(code, scale)[0] for code in group)
            scales.append(sum(scale << (8 * i) for i, scale in enumerate(row_scales)))
            width, bits = 64, 8
        else:
            codes, decoded_row, width, bits = row, row, 32, 16
        decoded.append(decoded_row)
        beats.extend(sum(code << (bits * i) for i, code in
                         enumerate(codes[first:first + width]))
                     for first in range(0, outputs, width))
    if mx:
        decoded_x = []
        for first in range(0, hidden, 32):
            codes, scale = quantize_group(activations[first:first + 32])
            decoded_x.extend(mx_decode(code, scale)[0] for code in codes)
    else:
        decoded_x = activations
    expected = []
    for j in range(outputs):
        total = sum((as_fraction(x, 7) * as_fraction(decoded[i][j], 7)
                     for i, x in enumerate(decoded_x)), Fraction(0))
        if total.denominator & (total.denominator - 1):
            raise AssertionError("generated GEMV reference is not dyadic")
        expected.append(round_dyadic(
            total.numerator, -(total.denominator.bit_length() - 1),
        )[0])
    for name, words, digits in (
        ("activations.hex", activations, 4),
        ("weights.hex", [word for row in decoded for word in row], 4),
        ("beats.hex", beats, 128), ("scales.hex", scales or [0], 128),
        ("expected.hex", expected, 8),
    ):
        with (images / name).open("x") as output:
            output.write("".join(f"{word:0{digits}x}\n" for word in words))
    bench = directory / "tb.sv"
    bench.write_text(f"""`timescale 1ns/1ps
module tb;
  reg clk=0,rst_n=0,cmd=0;
  always #5 clk=~clk;
  wire pready,pdone,perror,mem_req_valid,mem_req_write,mem_rsp_ready;
  wire [3:0] mem_req_kind;
  wire [2:0] mem_req_proj;
  wire [31:0] mem_req_layer,mem_req_row,mem_req_col,mem_req_wdata;
  reg mem_req_ready=0,mem_rsp_valid=0;
  reg [31:0] mem_rsp_rdata=0;
  anvil_q1_fp_gemv parent(
    .clk(clk),.rst_n(rst_n),.cmd_valid(cmd),.cmd_ready(pready),
    .cmd_layer(32'd0),.cmd_pos(32'd0),.cmd_proj(3'd1),.cmd_precision(2'd1),
    .done(pdone),.error(perror),.mem_req_valid(mem_req_valid),
    .mem_req_ready(mem_req_ready),.mem_req_write(mem_req_write),
    .mem_req_kind(mem_req_kind),.mem_req_layer(mem_req_layer),.mem_req_proj(mem_req_proj),
    .mem_req_row(mem_req_row),.mem_req_col(mem_req_col),.mem_req_wdata(mem_req_wdata),
    .mem_rsp_valid(mem_rsp_valid),.mem_rsp_ready(mem_rsp_ready),
    .mem_rsp_rdata(mem_rsp_rdata),.mem_rsp_error(1'b0));
  wire fready,in_ready,out_valid,out_last,fdone,ferror;
  wire [31:0] out_data,out_index;
  wire [4:0] status;
  reg in_valid=0,in_last=0,out_ready=0;
  reg [31:0] in_data=0;
  wire tensor_valid,tensor_ready,tensor_result_valid;
  wire [1023:0] tensor_a,tensor_b;
  wire [63:0] tensor_mask;
  wire [31:0] tensor_acc,tensor_result;
  wire [4:0] tensor_status;
  wire fetch_valid,fetch_ready,fetch_scale,response_valid,response_ready;
  wire [3:0] fetch_kind;
  wire [2:0] fetch_proj;
  wire [31:0] fetch_layer,fetch_row,fetch_col,fetch_tag,response_tag;
  wire [511:0] response_data;
  wire response_write,response_error,work_active,result_needed;
  wire bias_req_valid,bias_rsp_ready;
  wire [31:0] bias_layer,bias_col;
  wire [2:0] bias_proj;
  reg bias_rsp_valid=0;
  anvil_q1_fp2_projection #(.MAX_INPUT(896),.MAX_OUTPUT(128)) fp2(
    .clk(clk),.rst_n(rst_n),.cmd_valid(cmd),.cmd_ready(fready),
    .cmd_format_mx(1'b{int(mx)}),.cmd_head(1'b0),.cmd_layer(32'd0),
    .cmd_inputs(32'd896),.cmd_outputs(32'd128),.cmd_proj(3'd1),
    .in_valid(in_valid),.in_ready(in_ready),.in_data(in_data),.in_last(in_last),
    .out_valid(out_valid),.out_ready(out_ready),.out_data(out_data),.out_index(out_index),
    .out_last(out_last),.done(fdone),.error(ferror),.status(status),
    .ulp_valid(),.ulp_distance(),
    .tensor_valid(tensor_valid),.tensor_ready(tensor_ready),.tensor_a(tensor_a),
    .tensor_b(tensor_b),.tensor_mask(tensor_mask),.tensor_acc(tensor_acc),
    .tensor_result_valid(tensor_result_valid),.tensor_result(tensor_result),
    .tensor_status(tensor_status),.fetch_valid(fetch_valid),.fetch_ready(fetch_ready),
    .fetch_scale(fetch_scale),.fetch_kind(fetch_kind),.fetch_layer(fetch_layer),
    .fetch_proj(fetch_proj),.fetch_row(fetch_row),.fetch_col(fetch_col),.fetch_tag(fetch_tag),
    .response_valid(response_valid),.response_ready(response_ready),
    .response_tag(response_tag),.response_write(response_write),.response_error(response_error),
    .response_data(response_data),.work_active(work_active),.result_needed(result_needed),
    .bias_req_valid(bias_req_valid),.bias_req_ready(!bias_rsp_valid),
    .bias_layer(bias_layer),.bias_col(bias_col),.bias_proj(bias_proj),
    .bias_rsp_valid(bias_rsp_valid),.bias_rsp_ready(bias_rsp_ready),
    .bias_rsp_data(32'd0),.bias_rsp_error(1'b0));
  anvil_q1_fp2_bfp_tensor_array tensor_array(
    .clk(clk),.rst_n(rst_n),.in_valid(tensor_valid),.in_ready(tensor_ready),
    .out_valid(tensor_result_valid),.out_ready(1'b1),.format_mx(1'b0),
    .a(tensor_a),.b(tensor_b),.a_scale(16'h7f7f),.b_scale(16'h7f7f),
    .lane_mask(tensor_mask),.acc_in(tensor_acc),.result(tensor_result),
    .status(tensor_status),.alignment_events());
  wire ddr_req_valid,ddr_req_write,ddr_req_id,ddr_req_scale,ddr_rsp_ready;
  wire [3:0] ddr_req_kind;
  wire [2:0] ddr_req_proj;
  wire [31:0] ddr_req_layer,ddr_req_row,ddr_req_col;
  wire [511:0] ddr_req_wdata;
  wire [63:0] ddr_req_wstrb;
  reg ddr_req_ready=0,ddr_rsp_valid=0,ddr_rsp_id=0;
  reg [511:0] ddr_rsp_rdata=0;
  anvil_q1_fp2_ddr_pingpong transport(
    .clk(clk),.rst_n(rst_n),.cmd_valid(fetch_valid),.cmd_ready(fetch_ready),
    .cmd_write(1'b0),.cmd_scale(fetch_scale),.cmd_kind(fetch_kind),.cmd_layer(fetch_layer),
    .cmd_proj(fetch_proj),.cmd_row(fetch_row),.cmd_col(fetch_col),.cmd_tag(fetch_tag),
    .cmd_wdata(512'd0),.cmd_wstrb(64'd0),.out_valid(response_valid),
    .out_ready(response_ready),.out_tag(response_tag),.out_write(response_write),
    .out_error(response_error),.out_data(response_data),.work_active(work_active),
    .result_needed(result_needed),.stall_event(),.ddr_req_valid(ddr_req_valid),
    .ddr_req_ready(ddr_req_ready),.ddr_req_write(ddr_req_write),.ddr_req_id(ddr_req_id),
    .ddr_req_scale(ddr_req_scale),.ddr_req_kind(ddr_req_kind),
    .ddr_req_layer(ddr_req_layer),.ddr_req_proj(ddr_req_proj),
    .ddr_req_row(ddr_req_row),.ddr_req_col(ddr_req_col),.ddr_req_wdata(ddr_req_wdata),
    .ddr_req_wstrb(ddr_req_wstrb),.ddr_rsp_valid(ddr_rsp_valid),
    .ddr_rsp_ready(ddr_rsp_ready),.ddr_rsp_id(ddr_rsp_id),
    .ddr_rsp_error(1'b0),.ddr_rsp_rdata(ddr_rsp_rdata));
  reg [15:0] x[0:895],w[0:114687];
  reg [511:0] packed_weights[0:{len(beats)-1}],scale_plane[0:{max(1,len(scales))-1}];
  reg [31:0] expected[0:127],pending_data=0,held_data=0;
  reg [511:0] responses[0:1];
  reg pending=0,owned[0:1],held=0,held_last=0;
  reg [31:0] held_index=0;
  reg [4:0] held_status=0;
  integer delay_count[0:1],remaining=0;
  integer cycle=0,start_edge,run_index,tx=0,prx=0,frx=0,j;
  integer pcycles[0:1],fcycles[0:1],pbytes[0:1],fbytes[0:1],metadata[0:1];
  reg pa,sa,da,ra,ia,oa,ba,bs;
  task tick;
    integer chosen;
    begin
      cycle=cycle+1;
      if (cycle>8000000) $fatal(1,"GEMV cycle watchdog");
      mem_req_ready=!pending && !mem_rsp_valid && cycle%17>=3;
      ddr_req_ready=cycle%17>=3; out_ready=cycle%17>=3;
      in_valid=tx<896 && !cmd;
      in_last=tx==895;
      if (in_valid) in_data={{x[tx],16'd0}};
      if (pending && remaining==0 && !mem_rsp_valid) begin
        mem_rsp_valid=1; mem_rsp_rdata=pending_data;
      end
      if (!ddr_rsp_valid) begin
        chosen=-1;
        if (owned[1] && delay_count[1]==0) chosen=1;
        else if (owned[0] && delay_count[0]==0) chosen=0;
        if (chosen>=0) begin ddr_rsp_valid=1; ddr_rsp_id=chosen;
          ddr_rsp_rdata=responses[chosen]; end
      end
      #1;
      if ((^{{pdone,perror,fdone,ferror,in_ready,out_valid,mem_req_valid,
          mem_rsp_ready,ddr_req_valid,ddr_rsp_ready,bias_req_valid,bias_rsp_ready}})===1'bx ||
          perror || ferror) $fatal(1,"GEMV control/error");
      pa=mem_req_valid && mem_req_ready; sa=mem_rsp_valid && mem_rsp_ready;
      da=ddr_req_valid && ddr_req_ready; ra=ddr_rsp_valid && ddr_rsp_ready;
      ia=in_valid && in_ready; oa=out_valid && out_ready;
      ba=bias_req_valid && !bias_rsp_valid; bs=bias_rsp_valid && bias_rsp_ready;
      if (held && {{out_valid,out_data,out_index,out_last,status}} !==
          {{1'b1,held_data,held_index,held_last,held_status}})
        $fatal(1,"GEMV output stability");
      held=out_valid && !out_ready;
      held_data=out_data; held_index=out_index; held_last=out_last; held_status=status;
      if (out_valid) begin
        if (frx>=128 || out_index!==frx || out_data!==expected[frx] ||
            out_last !== (frx==127) || |status[4:2])
          $fatal(1,"FP2 GEMV numerical/index got=%h expected=%h at=%0d",out_data,expected[frx],frx);
      end
      if (pa) begin
        if (mem_req_layer!=0 || (mem_req_kind!=8 && mem_req_proj!=1))
          $fatal(1,"parent GEMV identity");
        if (mem_req_write) begin
          if (mem_req_kind!=8 || mem_req_row!=3 || mem_req_col!==prx ||
              prx>=128 || mem_req_wdata!==expected[prx])
            $fatal(1,"parent GEMV numerical/order");
          prx=prx+1; pending_data=0;
        end else if (mem_req_kind==8 && mem_req_row==1 && mem_req_col<896)
          pending_data={{x[mem_req_col],16'd0}};
        else if (mem_req_kind==12 && mem_req_row<896 && mem_req_col<128)
          pending_data={{16'd0,w[mem_req_row*128+mem_req_col]}};
        else if (mem_req_kind==4 && mem_req_row==0 && mem_req_col<128)
          pending_data=0;
        else $fatal(1,"parent GEMV request");
        pbytes[run_index]=pbytes[run_index]+64;
      end
      if (ba) begin
        if (bias_layer!=0 || bias_proj!=1 || bias_col>=128) $fatal(1,"bias identity");
        fbytes[run_index]=fbytes[run_index]+64;
      end
      if (pdone && !pcycles[run_index]) begin
        if (prx!=128) $fatal(1,"parent GEMV missing output");
        pcycles[run_index]=cycle-start_edge;
      end
      if (fdone && !fcycles[run_index]) begin
        if (frx!=128) $fatal(1,"FP2 GEMV missing output");
        fcycles[run_index]=cycle-start_edge;
      end
      @(posedge clk);
      if (ia) tx=tx+1;
      if (oa) frx=frx+1;
      if (sa) pending=0;
      if (pa) begin pending=1; remaining=2; end
      if (ra) owned[ddr_rsp_id]=0;
      if (da) begin
        if (owned[ddr_req_id] || ddr_req_write || ddr_req_kind!=12 ||
            ddr_req_layer!=0 || ddr_req_proj!=1 || ddr_req_row>=896 ||
            ddr_req_col>=128 || ddr_req_wstrb!==0)
          $fatal(1,"GEMV DDR identity/ownership");
        owned[ddr_req_id]=1; delay_count[ddr_req_id]=2;
        if (ddr_req_scale) begin
          if (!{int(mx)} || ddr_req_col!=0) $fatal(1,"GEMV scale address");
          responses[ddr_req_id]=scale_plane[ddr_req_row];
          metadata[run_index]=metadata[run_index]+64;
        end else responses[ddr_req_id]=
          packed_weights[ddr_req_row*{outputs//(64 if mx else 32)}+
                         (ddr_req_col>>{6 if mx else 5})];
        fbytes[run_index]=fbytes[run_index]+64;
      end
      #1;
      if (sa) mem_rsp_valid=0;
      if (ra) ddr_rsp_valid=0;
      if (bs) bias_rsp_valid=0;
      if (ba) bias_rsp_valid=1;
      if (pending && remaining>0) remaining=remaining-1;
      for (j=0;j<2;j=j+1)
        if (owned[j] && delay_count[j]>0) delay_count[j]=delay_count[j]-1;
      @(negedge clk);
    end
  endtask
  initial begin
    $readmemh("{run.relative / stem / 'checkpoint-images' / 'activations.hex'}",x);
    $readmemh("{run.relative / stem / 'checkpoint-images' / 'weights.hex'}",w);
    $readmemh("{run.relative / stem / 'checkpoint-images' / 'beats.hex'}",packed_weights);
    $readmemh("{run.relative / stem / 'checkpoint-images' / 'scales.hex'}",scale_plane);
    $readmemh("{run.relative / stem / 'checkpoint-images' / 'expected.hex'}",expected);
    owned[0]=0; owned[1]=0; delay_count[0]=0; delay_count[1]=0;
    repeat(2) @(posedge clk); @(negedge clk); rst_n=1; #1;
    for (run_index=0;run_index<2;run_index=run_index+1) begin
      tx=0; prx=0; frx=0; pcycles[run_index]=0; fcycles[run_index]=0;
      pbytes[run_index]=0; fbytes[run_index]=0; metadata[run_index]=0;
      if (!pready || !fready) $fatal(1,"GEMV not idle");
      cmd=1; start_edge=cycle+1; tick(); cmd=0;
      while (!pcycles[run_index] || !fcycles[run_index]) tick();
      $display("MEASUREMENT gemv-{ 'mx' if mx else 'bf16'} run=%0d parent_cycles=%0d fp2_cycles=%0d parent_bytes=%0d fp2_bytes=%0d scale_bytes=%0d components=128",
        run_index,pcycles[run_index],fcycles[run_index],
        pbytes[run_index],fbytes[run_index],metadata[run_index]);
      if (fcycles[run_index]>=pcycles[run_index])
        $fatal(1,"PERFORMANCE GEMV requires strictly fewer cold/warm FP2 cycles");
      if ({int(mx)} && 2*fbytes[run_index]>pbytes[run_index])
        $fatal(1,"TRAFFIC MX requires at least fifty percent actual parent-relative reduction");
      tick(); tick();
    end
    $display("SUMMARY GEMV: compared=512 speedup=passed");
    $finish;
  end
endmodule
""")
    sources = [str(path.relative_to(root)) for pattern in (
        "anvil_q1_fp_reference/rtl/*.sv", "rtl/*.sv") for path in sorted(root.glob(pattern))]
    compile_and_run(run, directory, bench, sources, "verilator", stem)
    measured_cycles(run, stem, "tensor-mx" if mx else "tensor-bf16")
    run.receipt["comparisons"].append({
        "kind": "gemv-benchmark", "format": "mx" if mx else "bf16",
        "seed": seed, "inputs": hidden, "outputs": outputs,
        "components": outputs * 4, "result": "passed",
        "mx_dense_payload_bytes": hidden * outputs if mx else None,
        "equivalent_bf16_payload_bytes": hidden * outputs * 2,
        "mx_unpadded_scale_bytes": hidden * outputs // 32 if mx else None,
        "metadata_inclusive_dense_ratio": 33 / 64 if mx else None,
        "row_padded_scale_bytes_per_pass": hidden * 64 if mx else None,
        "transport": "uncached 64-byte parent scalar adapter; FP2 ping-pong DDR",
    })


def attention_benchmark(run, root, compile_and_run, seed=17):
    """One production-width query, causal prefix 17; real parent two-pass traffic."""
    stem = f"benchmark-attention-{seed}"
    directory = run.path / stem
    directory.mkdir()
    rng = random.Random(seed)
    query = [bf16(rng.randint(-7, 7) / 8) for _ in range(64)]
    keys = [[bf16(rng.randint(-7, 7) / 8) for _ in range(64)] for _ in range(17)]
    values = [[bf16(rng.randint(-7, 7) / 8) for _ in range(64)] for _ in range(17)]
    with localcontext() as context:
        context.prec = 70
        q = [Decimal.from_float(f32(word << 16)) for word in query]
        scores = [sum(left * Decimal.from_float(f32(right << 16))
                      for left, right in zip(q, key)) / Decimal(64).sqrt() for key in keys]
        maximum = max(scores)
        p = [(score - maximum).exp() for score in scores]
        denominator = sum(p)
        expected = [float(sum(probability * Decimal.from_float(f32(row[j] << 16))
                              for probability, row in zip(p, values)) / denominator)
                    for j in range(64)]
    for name, words in (
        ("query.hex", query), ("keys.hex", [word for row in keys for word in row]),
        ("values.hex", [word for row in values for word in row]),
    ):
        with (directory / name).open("x") as output:
            output.write("".join(f"{word:04x}\n" for word in words))
    with (directory / "expected.txt").open("x") as output:
        for value in expected:
            lo, hi = approximation_interval(value, 0.003)
            output.write(f"{lo:08x} {hi:08x}\n")
    bench = directory / "tb.sv"
    bench.write_text(f"""`timescale 1ns/1ps
module tb;
  reg clk=0,rst_n=0,cmd=0;
  always #5 clk=~clk;
  wire pready,pdone,perror,mem_req_valid,mem_req_write,mem_rsp_ready;
  wire [3:0] mem_req_kind;
  wire [2:0] mem_req_proj;
  wire [31:0] mem_req_layer,mem_req_row,mem_req_col,mem_req_wdata;
  reg mem_req_ready=0,mem_rsp_valid=0;
  reg [31:0] mem_rsp_rdata=0;
  anvil_q1_fp_gqa_attention #(.HIDDEN_SIZE(64),.NUM_Q_HEADS(1),
    .NUM_KV_HEADS(1),.HEAD_DIM(64),.MAX_SEQ_LEN(17)) parent(
    .clk(clk),.rst_n(rst_n),.cmd_valid(cmd),.cmd_ready(pready),
    .cmd_layer(32'd0),.cmd_pos(32'd16),.cmd_precision(2'd1),
    .done(pdone),.error(perror),.mem_req_valid(mem_req_valid),
    .mem_req_ready(mem_req_ready),.mem_req_write(mem_req_write),
    .mem_req_kind(mem_req_kind),.mem_req_layer(mem_req_layer),.mem_req_proj(mem_req_proj),
    .mem_req_row(mem_req_row),.mem_req_col(mem_req_col),.mem_req_wdata(mem_req_wdata),
    .mem_rsp_valid(mem_rsp_valid),.mem_rsp_ready(mem_rsp_ready),
    .mem_rsp_rdata(mem_rsp_rdata),.mem_rsp_error(1'b0));
  wire fready,q_ready,kv_ready,out_valid,out_last,fdone,ferror;
  wire [31:0] out_data;
  wire [4:0] status;
  reg q_valid=0,kv_valid=0,out_ready=0;
  reg [15:0] q_data=0,k_data=0,v_data=0;
  reg q_last=0,kv_last=0;
  anvil_q1_fp2_flash_attn #(.HEAD_DIM(64),.TILE_TOKENS(16),.MAX_SEQ_LEN(17)) fp2(
    .clk(clk),.rst_n(rst_n),.cmd_valid(cmd),.cmd_ready(fready),.cmd_len(32'd17),
    .q_valid(q_valid),.q_ready(q_ready),.q_data(q_data),.q_last(q_last),
    .kv_valid(kv_valid),.kv_ready(kv_ready),.k_data(k_data),.v_data(v_data),
    .kv_last(kv_last),.out_ready(out_ready),.out_valid(out_valid),.out_data(out_data),
    .out_last(out_last),.done(fdone),.error(ferror),.status(status));
  reg [15:0] q[0:63],k[0:1087],v[0:1087];
  reg [31:0] lower[0:63],upper[0:63],s0,s1,pending_data=0;
  reg [511:0] qbeat=0,kbeat=0,vbeat=0;
  reg pending=0,qbuffer=0,kvbuffer=0,held=0,held_last=0;
  reg [31:0] held_data=0;
  reg [4:0] held_status=0;
  integer qload=0,kvload=0,remaining=0,cycle=0,start_edge,run_index,j,fd,scan;
  integer qtx=0,kvtx=0,prx=0,frx=0,kvread=0;
  integer pcycles[0:1],fcycles[0:1],pbytes[0:1],fbytes[0:1];
  reg pa,sa,qa,ka,oa;
  function [31:0] ordered(input [31:0] word);
    ordered=word[31] ? ~word : word^32'h80000000;
  endfunction
  task compare(input [31:0] word,input integer index);
    if (index>=64 || (^word)===1'bx || ordered(word)<ordered(lower[index]) ||
        ordered(word)>ordered(upper[index]))
      $fatal(1,"ATTENTION numerical index=%0d value=%h bounds=[%h,%h]",
        index,word,lower[index],upper[index]);
  endtask
  task tick;
    begin
      cycle=cycle+1;
      if (cycle>8000000) $fatal(1,"attention benchmark cycle watchdog");
      mem_req_ready=!pending && !mem_rsp_valid && cycle%17>=3;
      out_ready=cycle%17>=3;
      // Each buffer loads only after a modeled physical beat request and response.
      if (!cmd && qtx<64 && !qbuffer && qload==0 && cycle%17>=3) begin
        qload=3; fbytes[run_index]=fbytes[run_index]+64;
      end
      if (qload==1) begin
        for (j=0;j<32;j=j+1) qbeat[16*j+:16]=q[qtx+j];
        qbuffer=1;
      end
      if (qtx==64 && kvtx<1088 && !kvbuffer && kvload==0 && cycle%17>=3) begin
        kvload=5; fbytes[run_index]=fbytes[run_index]+128;
        kvread=kvread+32;
      end
      if (kvload==1) begin
        for (j=0;j<32;j=j+1) begin
          kbeat[16*j+:16]=k[kvtx+j]; vbeat[16*j+:16]=v[kvtx+j];
        end
        kvbuffer=1;
      end
      q_valid=qbuffer && qtx<64; q_data=qbeat[16*(qtx%32)+:16]; q_last=qtx==63;
      kv_valid=kvbuffer && kvtx<1088;
      k_data=kbeat[16*(kvtx%32)+:16]; v_data=vbeat[16*(kvtx%32)+:16];
      kv_last=kvtx%64==63;
      if (pending && remaining==0 && !mem_rsp_valid) begin
        mem_rsp_valid=1; mem_rsp_rdata=pending_data;
      end
      #1;
      if ((^{{pdone,perror,fdone,ferror,q_ready,kv_ready,out_valid,
          mem_req_valid,mem_rsp_ready}})===1'bx || perror || ferror)
        $fatal(1,"attention benchmark control/error");
      pa=mem_req_valid && mem_req_ready; sa=mem_rsp_valid && mem_rsp_ready;
      qa=q_valid && q_ready; ka=kv_valid && kv_ready; oa=out_valid && out_ready;
      if (held && {{out_valid,out_data,out_last,status}} !==
          {{1'b1,held_data,held_last,held_status}}) $fatal(1,"attention output stability");
      held=out_valid && !out_ready; held_data=out_data; held_last=out_last; held_status=status;
      if (out_valid) begin
        compare(out_data,frx);
        if (out_last !== (frx==63) || |status[4:2]) $fatal(1,"attention output metadata");
      end
      if (pa) begin
        if (mem_req_layer!=0 || mem_req_proj!=0 || mem_req_col>=64)
          $fatal(1,"parent attention identity");
        if (mem_req_write) begin
          if (mem_req_kind==9 && mem_req_row==16) begin
            if (mem_req_wdata!=={{k[1024+mem_req_col],16'd0}})
              $fatal(1,"parent K caching");
          end else if (mem_req_kind==10 && mem_req_row==16) begin
            if (mem_req_wdata!=={{v[1024+mem_req_col],16'd0}})
              $fatal(1,"parent V caching");
          end else if (mem_req_kind==8 && mem_req_row==5 && mem_req_col===prx) begin
            compare(mem_req_wdata,prx); prx=prx+1;
          end else $fatal(1,"parent attention write identity");
          pending_data=0;
        end else if (mem_req_kind==8 && mem_req_row==2)
          pending_data={{q[mem_req_col],16'd0}};
        else if (mem_req_kind==8 && mem_req_row==3)
          pending_data={{k[1024+mem_req_col],16'd0}};
        else if (mem_req_kind==8 && mem_req_row==4)
          pending_data={{v[1024+mem_req_col],16'd0}};
        else if (mem_req_kind==9 && mem_req_row<17)
          pending_data={{k[mem_req_row*64+mem_req_col],16'd0}};
        else if (mem_req_kind==10 && mem_req_row<17)
          pending_data={{v[mem_req_row*64+mem_req_col],16'd0}};
        else $fatal(1,"parent attention read identity");
        pbytes[run_index]=pbytes[run_index]+64;
      end
      if (pdone && !pcycles[run_index]) begin
        if (prx!=64) $fatal(1,"parent attention output count");
        pcycles[run_index]=cycle-start_edge;
      end
      if (fdone && !fcycles[run_index]) begin
        if (frx!=64 || kvtx!=1088 || qtx!=64 || kvread!=1088)
          $fatal(1,"single-pass attention conservation");
        fcycles[run_index]=cycle-start_edge;
      end
      @(posedge clk);
      if (qa) begin qtx=qtx+1; if (qtx%32==0) qbuffer=0; end
      if (ka) begin kvtx=kvtx+1; if (kvtx%32==0) kvbuffer=0; end
      if (oa) frx=frx+1;
      if (sa) pending=0;
      if (pa) begin pending=1; remaining=2; end
      #1;
      if (sa) mem_rsp_valid=0;
      if (pending && remaining>0) remaining=remaining-1;
      if (qload>0) qload=qload-1;
      if (kvload>0) kvload=kvload-1;
      @(negedge clk);
    end
  endtask
  initial begin
    $readmemh("{run.relative / stem / 'query.hex'}",q);
    $readmemh("{run.relative / stem / 'keys.hex'}",k);
    $readmemh("{run.relative / stem / 'values.hex'}",v);
    fd=$fopen("{run.relative / stem / 'expected.txt'}","r");
    if (!fd) $fatal(1,"attention fixture open");
    for (j=0;j<64;j=j+1) begin
      scan=$fscanf(fd,"%h %h\\n",s0,s1);
      if (scan!=2) $fatal(1,"attention fixture malformed");
      lower[j]=s0; upper[j]=s1;
    end
    repeat(2) @(posedge clk); @(negedge clk); rst_n=1; #1;
    for (run_index=0;run_index<2;run_index=run_index+1) begin
      qtx=0; kvtx=0; prx=0; frx=0; kvread=0;
      pcycles[run_index]=0; fcycles[run_index]=0;
      pbytes[run_index]=0; fbytes[run_index]=0;
      if (!pready || !fready) $fatal(1,"attention not idle");
      cmd=1; start_edge=cycle+1; tick(); cmd=0;
      while (!pcycles[run_index] || !fcycles[run_index]) tick();
      $display("MEASUREMENT attention run=%0d parent_cycles=%0d fp2_cycles=%0d parent_bytes=%0d fp2_bytes=%0d components=64 prefix=17",
        run_index,pcycles[run_index],fcycles[run_index],pbytes[run_index],fbytes[run_index]);
      if (fcycles[run_index]>=pcycles[run_index])
        $fatal(1,"PERFORMANCE attention requires strictly fewer cold/warm FP2 cycles");
      tick(); tick();
    end
    $display("SUMMARY attention: compared=256 single_pass=passed speedup=passed");
    $finish;
  end
endmodule
""")
    sources = [str(path.relative_to(root)) for pattern in (
        "anvil_q1_fp_reference/rtl/*.sv", "rtl/*.sv") for path in sorted(root.glob(pattern))]
    compile_and_run(run, directory, bench, sources, "verilator", stem)
    measured_cycles(run, stem, "attention")
    run.receipt["comparisons"].append({
        "kind": "attention-benchmark", "seed": seed, "head_dim": 64,
        "prefix": 17, "components": 256, "result": "passed",
        "transport": "uncached 64-byte parent scalar adapter; single-pass packed BF16 beat buffers",
    })


def rms_benchmark(run, root, compile_and_run, hidden=896, seed=None):
    """Parent scalar transport: one uncached 64-byte beat per logical request.

    Both paths have the same 512-bit physical bandwidth available. The fused
    epilogue consumes the preceding operator's on-chip stream, whereas the parent
    uses its actual external kind-8 interface. Parent responses have two cycles
    of latency and the common periodic downstream/request stall schedule.
    Cold includes complete input intake; warm reruns without reinitializing RTL.
    This diagnostic measures RMSNorm only, not the five-domain aggregate.
    """
    stem = f"benchmark-rmsnorm-h{hidden}" + (f"-{seed}" if seed is not None else "")
    directory = run.path / stem
    directory.mkdir()
    with localcontext() as context:
        context.prec = 70
        offset = random.Random(seed).randrange(31) if seed is not None else 0
        x = [Decimal(((i + offset) % 31) - 15) / 16 for i in range(hidden)]
        gamma = [1 + Decimal(i % 7) / 32 for i in range(hidden)]
        denominator = (sum(value * value for value in x) / hidden +
                       Decimal.from_float(9.999999974752427e-7)).sqrt()
        expected = [float(value * scale / denominator) for value, scale in zip(x, gamma)]
    with (directory / "vectors.txt").open("x") as output:
        for value, scale, reference in zip(x, gamma, expected):
            low, high = approximation_interval(reference, 0.005)
            output.write(f"{bits32(float(value)):08x} {bits32(float(scale)):08x} "
                         f"{low:08x} {high:08x}\n")
    bench = directory / "tb.sv"
    bench.write_text(f"""`timescale 1ns/1ps
module tb;
  reg clk=0,rst_n=0,cmd_valid=0;
  wire parent_cmd_ready,parent_done,parent_error;
  wire mem_req_valid,mem_req_write,mem_rsp_ready;
  wire [3:0] mem_req_kind;
  wire [31:0] mem_req_layer,mem_req_row,mem_req_col,mem_req_wdata;
  wire [2:0] mem_req_proj;
  reg mem_req_ready=0,mem_rsp_valid=0,mem_rsp_error=0;
  reg [31:0] mem_rsp_rdata=0;
  wire cmd_ready,in_ready,out_valid,out_last,done,error;
  wire [31:0] out_data;
  wire [4:0] status;
  reg in_valid=0,in_last=0,out_ready=0;
  reg [31:0] in_data=0,in_aux=0;
  anvil_q1_fp_rmsnorm #(.HIDDEN_SIZE({hidden})) parent(
    .clk(clk),.rst_n(rst_n),.cmd_valid(cmd_valid),.cmd_ready(parent_cmd_ready),
    .cmd_layer(32'd0),.cmd_pos(32'd0),.cmd_mode(2'd0),.cmd_precision(2'd1),
    .done(parent_done),.error(parent_error),
    .mem_req_valid(mem_req_valid),.mem_req_ready(mem_req_ready),
    .mem_req_write(mem_req_write),.mem_req_kind(mem_req_kind),.mem_req_layer(mem_req_layer),
    .mem_req_proj(mem_req_proj),.mem_req_row(mem_req_row),.mem_req_col(mem_req_col),
    .mem_req_wdata(mem_req_wdata),.mem_rsp_valid(mem_rsp_valid),.mem_rsp_ready(mem_rsp_ready),
    .mem_rsp_rdata(mem_rsp_rdata),.mem_rsp_error(mem_rsp_error));
  anvil_q1_fp2_epilogue_fusion #(.MAX_VECTOR({hidden}),.HEAD_DIM(64)) fp2(
    .clk(clk),.rst_n(rst_n),.cmd_valid(cmd_valid),.cmd_ready(cmd_ready),
    .cmd_op(2'd0),.cmd_len(32'd{hidden}),.cmd_pos(32'd0),
    .in_valid(in_valid),.in_ready(in_ready),.in_data(in_data),.in_aux(in_aux),
    .in_residual(32'd0),.in_last(in_last),.out_ready(out_ready),
    .out_valid(out_valid),.out_data(out_data),.out_last(out_last),
    .status(status),.done(done),.error(error));
  always #5 clk=~clk;
  reg [31:0] values[0:{hidden-1}],gammas[0:{hidden-1}];
  reg [31:0] low[0:{hidden-1}],high[0:{hidden-1}];
  reg [31:0] scanned0,scanned1,scanned2,scanned3;
  integer file_handle,scan,j,run_index,cycle=0,start_edge,tx=0,rx=0,parent_rx=0;
  integer parent_cycles[0:1],fp2_cycles[0:1],parent_bytes=0,parent_requests=0;
  integer remaining=0;
  reg pending=0;
  reg [31:0] pending_data=0;
  reg req_accept,rsp_accept,input_accept,output_accept;
  function [31:0] ordered(input [31:0] value);
    ordered=value[31] ? ~value : value^32'h80000000;
  endfunction
  task compare(input [31:0] value,input integer index);
    if ((^value)===1'bx || index>={hidden} ||
        ordered(value)<ordered(low[index]) || ordered(value)>ordered(high[index]))
      $fatal(1,"RMS numerical index=%0d value=%h",index,value);
  endtask
  task tick;
    begin
      cycle=cycle+1;
      if (cycle>500000) $fatal(1,"benchmark cycle watchdog");
      mem_req_ready=!pending && !mem_rsp_valid && cycle%17>=3;
      out_ready=cycle%17>=3;
      in_valid=tx<{hidden};
      in_last=tx+1=={hidden};
      if (in_valid) begin in_data=values[tx]; in_aux=gammas[tx]; end
      if (pending && remaining==0 && !mem_rsp_valid) begin
        mem_rsp_valid=1; mem_rsp_rdata=pending_data;
      end
      #1;
      if ((^{{parent_done,parent_error,done,error,out_valid,in_ready,mem_req_valid,
          mem_rsp_ready}})===1'bx) $fatal(1,"benchmark active X/Z");
      if (parent_error || error) $fatal(1,"RMS operator error");
      req_accept=mem_req_valid && mem_req_ready;
      rsp_accept=mem_rsp_valid && mem_rsp_ready;
      input_accept=in_valid && in_ready;
      output_accept=out_valid && out_ready;
      if (parent_done && parent_cycles[run_index]==0) begin
        parent_cycles[run_index]=cycle-start_edge;
        if (parent_rx!={hidden}) $fatal(1,"parent missing output");
      end
      if (done && fp2_cycles[run_index]==0) begin
        fp2_cycles[run_index]=cycle-start_edge;
        if (rx!={hidden}) $fatal(1,"FP2 missing output");
      end
      if (out_valid) begin
        compare(out_data,rx);
        if (out_last !== (rx+1=={hidden}) || |status[4:2])
          $fatal(1,"FP2 status/last");
      end
      if (req_accept) begin
        if (mem_req_layer!=0 || mem_req_proj!=0 || mem_req_col>={hidden})
          $fatal(1,"parent memory indexing");
        if (mem_req_write) begin
          if (mem_req_kind!=8 || mem_req_row!=1 || mem_req_col!=parent_rx)
            $fatal(1,"parent output addressing/order");
          compare(mem_req_wdata,parent_rx); parent_rx=parent_rx+1;
          pending_data=0;
        end else if (mem_req_kind==8 && mem_req_row==0)
          pending_data=values[mem_req_col];
        else if (mem_req_kind==5 && mem_req_row==0)
          pending_data={{16'd0,gammas[mem_req_col][31:16]}};
        else $fatal(1,"unexpected parent memory identity");
        parent_bytes=parent_bytes+64; parent_requests=parent_requests+1;
      end
      @(posedge clk);
      if (input_accept) tx=tx+1;
      if (output_accept) rx=rx+1;
      if (rsp_accept) pending=0;
      if (req_accept) begin pending=1; remaining=2; end
      #1;
      if (rsp_accept) mem_rsp_valid=0;
      if (pending && remaining>0) remaining=remaining-1;
      @(negedge clk);
    end
  endtask
  initial begin
    file_handle=$fopen("{run.relative / stem / 'vectors.txt'}","r");
    if (!file_handle) $fatal(1,"benchmark fixture open");
    for (j=0;j<{hidden};j=j+1) begin
      scan=$fscanf(file_handle,"%h %h %h %h\\n",scanned0,scanned1,scanned2,scanned3);
      if (scan!=4) $fatal(1,"benchmark fixture malformed");
      values[j]=scanned0; gammas[j]=scanned1; low[j]=scanned2; high[j]=scanned3;
    end
    repeat (2) @(posedge clk);
    @(negedge clk); rst_n=1; #1;
    for (run_index=0;run_index<2;run_index=run_index+1) begin
      parent_cycles[run_index]=0; fp2_cycles[run_index]=0;
      tx=0; rx=0; parent_rx=0;
      if (!cmd_ready || !parent_cmd_ready) $fatal(1,"benchmark command not idle");
      cmd_valid=1; start_edge=cycle+1; tick(); cmd_valid=0;
      while (parent_cycles[run_index]==0 || fp2_cycles[run_index]==0) tick();
      $display("MEASUREMENT rmsnorm run=%0d parent_cycles=%0d fp2_cycles=%0d components={hidden} parent_physical_bytes=%0d",
        run_index,parent_cycles[run_index],fp2_cycles[run_index],parent_bytes);
      tx={hidden}; tick(); tick();
    end
    if (parent_requests!={hidden*8} || parent_bytes!={hidden*8*64})
      $fatal(1,"physical transaction accounting");
    if (fp2_cycles[0]>=parent_cycles[0] || fp2_cycles[1]>=parent_cycles[1])
      $fatal(1,"PERFORMANCE rmsnorm requires strictly fewer FP2 cycles on cold and warm runs");
    $display("SUMMARY RMSNorm: compared={hidden*4} cold_and_warm_speedup=passed");
    $finish;
  end
endmodule
""")
    sources = [str(path.relative_to(root)) for pattern in (
        "anvil_q1_fp_reference/rtl/*.sv", "rtl/*.sv") for path in sorted(root.glob(pattern))]
    compile_and_run(run, directory, bench, sources, "verilator", stem)
    measured_cycles(run, stem, "rmsnorm")
    run.receipt["comparisons"].append({
        "kind": "rmsnorm-benchmark", "hidden": hidden,
        "components": hidden * 4, "result": "passed",
    })


def stream_operator_benchmark(run, root, compile_and_run, kind, seed=None):
    """Matched cold/warm command workloads with real parent scratchpad traffic."""
    rope = kind == "rope"
    first_length = 896 if rope else 4864
    second_length = 128 if rope else 896
    total = first_length + second_length
    stem = "benchmark-" + kind + (f"-{seed}" if seed is not None else "")
    directory = run.path / stem
    directory.mkdir()
    data, aux, residual, references = [], [], [], []
    offset = random.Random(seed).randrange(31) if seed is not None else 0
    for phase, length in enumerate((first_length, second_length)):
        x = [f32(bits32((((i + offset) % 31) - 15) / 16)) for i in range(length)]
        a = [f32(bits32(1 + (i % 7) / 32)) for i in range(length)]
        r = [f32(bits32(((i % 11) - 5) / 32)) for i in range(length)]
        if rope:
            expected = x[:]
            for base in range(0, length, 64):
                for j in range(32):
                    angle = 31 * 1000000 ** (-2 * j / 64)
                    cosine, sine = f32(bits32(math.cos(angle))), f32(bits32(math.sin(angle)))
                    a[base + j], a[base + j + 32] = cosine, sine
                    left, right = x[base + j], x[base + j + 32]
                    expected[base + j] = left * cosine - right * sine
                    expected[base + j + 32] = right * cosine + left * sine
        elif phase == 0:
            with localcontext() as context:
                context.prec = 70
                expected = [
                    float(Decimal.from_float(g) * Decimal.from_float(u) /
                          (1 + (-Decimal.from_float(g)).exp())) for g, u in zip(x, a)
                ]
        else:
            expected = [value + addend for value, addend in zip(references[:length], r)]
        data.extend(map(bits32, x))
        aux.extend(map(bits32, a))
        residual.extend(map(bits32, r))
        references.extend(expected)
    with (directory / "vectors.txt").open("x") as output:
        for x, a, r, reference in zip(data, aux, residual, references):
            low, high = approximation_interval(reference, 0.0005 if rope else 0.002)
            output.write(f"{x:08x} {a:08x} {r:08x} {low:08x} {high:08x}\n")
    parent_instance = """
  anvil_q1_fp_rope #(.HIDDEN_SIZE(896),.NUM_Q_HEADS(14),.NUM_KV_HEADS(2),.HEAD_DIM(64)) parent(
    .clk(clk),.rst_n(rst_n),.cmd_valid(pcmd),.cmd_ready(pready),
    .cmd_layer(32'd0),.cmd_pos(32'd31),.cmd_precision(2'd1),
""" if rope else """
  anvil_q1_fp_elementwise #(.HIDDEN_SIZE(896),.INTERMEDIATE_SIZE(4864)) parent(
    .clk(clk),.rst_n(rst_n),.cmd_valid(pcmd),.cmd_ready(pready),
    .cmd_layer(32'd0),.cmd_pos(32'd31),.cmd_precision(2'd1),
    .cmd_mode(pphase==0 ? 2'd2 : 2'd1),
"""
    bench = directory / "tb.sv"
    bench.write_text(f"""`timescale 1ns/1ps
module tb;
  reg clk=0,rst_n=0,pcmd=0,fcmd=0,in_valid=0,in_last=0,out_ready=0;
  wire pready,pdone,perror,fready,in_ready,out_valid,out_last,fdone,ferror;
  wire [31:0] out_data;
  wire [4:0] status;
  reg [31:0] in_data=0,in_aux=0,in_residual=0;
  integer pphase=0,fphase=0;
  wire mem_req_valid,mem_req_write,mem_rsp_ready;
  wire [3:0] mem_req_kind;
  wire [2:0] mem_req_proj;
  wire [31:0] mem_req_layer,mem_req_row,mem_req_col,mem_req_wdata;
  reg mem_req_ready=0,mem_rsp_valid=0;
  reg [31:0] mem_rsp_rdata=0;
  {parent_instance}
    .done(pdone),.error(perror),.mem_req_valid(mem_req_valid),.mem_req_ready(mem_req_ready),
    .mem_req_write(mem_req_write),.mem_req_kind(mem_req_kind),.mem_req_layer(mem_req_layer),
    .mem_req_proj(mem_req_proj),.mem_req_row(mem_req_row),.mem_req_col(mem_req_col),
    .mem_req_wdata(mem_req_wdata),.mem_rsp_valid(mem_rsp_valid),.mem_rsp_ready(mem_rsp_ready),
    .mem_rsp_rdata(mem_rsp_rdata),.mem_rsp_error(1'b0));
  anvil_q1_fp2_epilogue_fusion #(.MAX_VECTOR(4864),.HEAD_DIM(64)) fp2(
    .clk(clk),.rst_n(rst_n),.cmd_valid(fcmd),.cmd_ready(fready),
    .cmd_op({"2'd1" if rope else "fphase==0 ? 2'd2 : 2'd3"}),
    .cmd_len(fphase==0 ? 32'd{first_length} : 32'd{second_length}),.cmd_pos(32'd31),
    .in_valid(in_valid),.in_ready(in_ready),.in_data(in_data),.in_aux(in_aux),
    .in_residual(in_residual),.in_last(in_last),.out_ready(out_ready),
    .out_valid(out_valid),.out_data(out_data),.out_last(out_last),.status(status),
    .done(fdone),.error(ferror));
  always #5 clk=~clk;
  reg [31:0] values[0:{total-1}],auxiliary[0:{total-1}],residuals[0:{total-1}];
  reg [31:0] lower[0:{total-1}],upper[0:{total-1}],presult[0:{total-1}],fresult[0:{total-1}];
  reg pseen[0:{total-1}];
  reg [31:0] s0,s1,s2,s3,s4,pending_data=0,held_data;
  reg [4:0] held_status;
  reg held_last,held=0,pending=0,pa,fa,ia,oa,ra,sa;
  integer fd,scan,j,cycle=0,start_edge,run_index,tx=0,rx=0,prx=0,remaining=0;
  integer pcycles[0:1],fcycles[0:1],pcount[0:1],fcount[0:1];
  integer base,length,index,bytes=0;
  function [31:0] ordered(input [31:0] value);
    ordered=value[31] ? ~value : value^32'h80000000;
  endfunction
  task compare(input [31:0] value,input integer at);
    if ((^value)===1'bx || at<0 || at>={total} ||
        ordered(value)<ordered(lower[at]) || ordered(value)>ordered(upper[at]))
      $fatal(1,"NUMERICAL {kind} index=%0d got=%h bounds=[%h,%h]",at,value,lower[at],upper[at]);
  endtask
  task tick;
    begin
      cycle=cycle+1;
      if (cycle>2000000) $fatal(1,"benchmark cycle watchdog");
      base=fphase==0 ? 0 : {first_length};
      length=fphase==0 ? {first_length} : {second_length};
      mem_req_ready=!pending && !mem_rsp_valid && cycle%17>=3;
      out_ready=cycle%17>=3;
      in_valid=fphase<2 && tx<length && !fcmd;
      in_last=tx+1==length;
      if (in_valid) begin
        in_data={("values[base+tx]" if rope else "fphase==0 ? values[tx] : fresult[tx]")};
        in_aux=auxiliary[base+tx]; in_residual=residuals[base+tx];
      end
      if (pending && remaining==0 && !mem_rsp_valid) begin
        mem_rsp_valid=1; mem_rsp_rdata=pending_data;
      end
      #1;
      if ((^{{pready,pdone,perror,fready,fdone,ferror,in_ready,out_valid,mem_req_valid,
          mem_rsp_ready}})===1'bx || perror || ferror) $fatal(1,"benchmark control/error");
      pa=pcmd && pready; fa=fcmd && fready;
      ia=in_valid && in_ready; oa=out_valid && out_ready;
      ra=mem_req_valid && mem_req_ready; sa=mem_rsp_valid && mem_rsp_ready;
      if (held && {{out_valid,out_data,out_last,status}} !==
        {{1'b1,held_data,held_last,held_status}}) $fatal(1,"benchmark output stall stability");
      if (out_valid) begin
        compare(out_data,base+rx);
        if (out_last !== (rx+1==length) || |status[4:2]) $fatal(1,"benchmark last/status");
        if (oa) begin fresult[base+rx]=out_data; rx=rx+1; fcount[run_index]=fcount[run_index]+1; end
      end
      held=out_valid && !out_ready; held_data=out_data; held_last=out_last; held_status=status;
      if (ra) begin
        if (mem_req_layer!=0 || mem_req_proj!=0) $fatal(1,"parent tensor identity");
        if (mem_req_write) begin
          {("index=(mem_req_row==2 ? 0 : 896)+mem_req_col;" if rope else
            f"index=(pphase==0 ? 0 : {first_length})+mem_req_col;")}
          if (mem_req_kind!=8 ||
              {("(mem_req_row!=2 && mem_req_row!=3)" if rope else
                "(mem_req_row!=(pphase==0 ? 11 : 0))")} ||
              index>={total} || pseen[index]) $fatal(1,"parent output identity/duplication");
          compare(mem_req_wdata,index);
          pseen[index]=1; presult[index]=mem_req_wdata; prx=prx+1;
          pcount[run_index]=pcount[run_index]+1; pending_data=0;
        end else begin
          {('''
          if (mem_req_kind==8 && (mem_req_row==2 || mem_req_row==3)) begin
            index=(mem_req_row==2 ? 0 : 896)+mem_req_col;
            if (index>=1024) $fatal(1,"parent input index");
            pending_data=values[index];
          end else if (mem_req_kind==11 && mem_req_row==31 && mem_req_col<64)
            pending_data=auxiliary[(mem_req_col>>1)+((mem_req_col&1) ? 32 : 0)];
          else $fatal(1,"parent RoPE input identity");
          ''' if rope else '''
          if (mem_req_kind!=8 || mem_req_col>=(pphase==0 ? 4864 : 896))
            $fatal(1,"parent elementwise input index");
          if (pphase==0 && mem_req_row==9) pending_data=values[mem_req_col];
          else if (pphase==0 && mem_req_row==10) pending_data=auxiliary[mem_req_col];
          else if (pphase==1 && mem_req_row==7) pending_data=presult[mem_req_col];
          else if (pphase==1 && mem_req_row==12) pending_data=residuals[4864+mem_req_col];
          else $fatal(1,"parent elementwise input identity");
          ''')}
        end
        bytes=bytes+64;
      end
      if (fdone) begin
        if (rx!=length) $fatal(1,"FP2 missing components");
        fphase=fphase+1; tx=0; rx=0;
        if (fphase==2) fcycles[run_index]=cycle-start_edge;
      end
      if (pdone) begin
        pphase=pphase+1;
        if (pphase=={1 if rope else 2}) begin
          if (prx!={total}) $fatal(1,"parent missing components");
          pcycles[run_index]=cycle-start_edge;
        end
      end
      @(posedge clk);
      if (ia) tx=tx+1;
      if (sa) pending=0;
      if (ra) begin pending=1; remaining=2; end
      #1;
      if (pa) pcmd=0;
      if (fa) fcmd=0;
      if (sa) mem_rsp_valid=0;
      if (pending && remaining>0) remaining=remaining-1;
      @(negedge clk);
      if (fphase==1 && fready) fcmd=1;
      if ({0 if rope else 1} && pphase==1 && pready) pcmd=1;
    end
  endtask
  initial begin
    fd=$fopen("{run.relative / stem / 'vectors.txt'}","r");
    if (!fd) $fatal(1,"benchmark fixture open");
    for (j=0;j<{total};j=j+1) begin
      scan=$fscanf(fd,"%h %h %h %h %h\\n",s0,s1,s2,s3,s4);
      if (scan!=5) $fatal(1,"benchmark fixture malformed");
      values[j]=s0; auxiliary[j]=s1; residuals[j]=s2; lower[j]=s3; upper[j]=s4;
    end
    repeat(2) @(posedge clk); @(negedge clk); rst_n=1; #1;
    for (run_index=0;run_index<2;run_index=run_index+1) begin
      for (j=0;j<{total};j=j+1) pseen[j]=0;
      pphase=0; fphase=0; tx=0; rx=0; prx=0;
      pcycles[run_index]=0; fcycles[run_index]=0;
      pcount[run_index]=0; fcount[run_index]=0;
      if (!pready || !fready) $fatal(1,"benchmark not idle");
      pcmd=1; fcmd=1; start_edge=cycle+1;
      while (!pcycles[run_index] || !fcycles[run_index]) tick();
      $display("MEASUREMENT {kind} run=%0d parent_cycles=%0d fp2_cycles=%0d parent_bytes=%0d components={total}",
        run_index,pcycles[run_index],fcycles[run_index],bytes);
      tick(); tick();
    end
    if (pcount[0]!={total} || pcount[1]!={total} ||
        fcount[0]!={total} || fcount[1]!={total}) $fatal(1,"benchmark comparison coverage");
    if (pcycles[0]<=fcycles[0] || pcycles[1]<=fcycles[1])
      $fatal(1,"PERFORMANCE {kind} requires strictly fewer cold/warm FP2 cycles");
    $display("SUMMARY {kind}: compared={total*4} cold_and_warm_speedup=passed");
    $finish;
  end
endmodule
""")
    sources = [str(path.relative_to(root)) for pattern in (
        "anvil_q1_fp_reference/rtl/*.sv", "rtl/*.sv") for path in sorted(root.glob(pattern))]
    compile_and_run(run, directory, bench, sources, "verilator", stem)
    measured_cycles(run, stem, kind)
    run.receipt["comparisons"].append({
        "kind": kind + "-benchmark", "components": total * 4, "result": "passed",
    })
