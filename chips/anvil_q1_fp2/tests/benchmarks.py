"""Measured operator comparisons; no resource or clock-based speed inference."""

from decimal import Decimal, localcontext

from reference import approximation_interval, bits32


def rms_benchmark(run, root, compile_and_run, hidden=896):
    """Parent scalar transport: one uncached 64-byte beat per logical request.

    Both paths have the same 512-bit physical bandwidth available. The fused
    epilogue consumes the preceding operator's on-chip stream, whereas the parent
    uses its actual external kind-8 interface. Parent responses have two cycles
    of latency and the common periodic downstream/request stall schedule.
    Cold includes complete input intake; warm reruns without reinitializing RTL.
    This diagnostic measures RMSNorm only, not the five-domain aggregate.
    """
    stem = f"benchmark-rmsnorm-h{hidden}"
    directory = run.path / stem
    directory.mkdir()
    with localcontext() as context:
        context.prec = 70
        x = [Decimal((i % 31) - 15) / 16 for i in range(hidden)]
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
    run.receipt["comparisons"].append({
        "kind": "rmsnorm-benchmark", "hidden": hidden,
        "components": hidden * 4, "result": "passed",
    })
