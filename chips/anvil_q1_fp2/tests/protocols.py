"""Independent public-channel CSR and two-outstanding DDR experiments."""

import random


COUNTER_ADDRESSES = (0x020, 0x030, 0x040, 0x050, 0x068, 0x070)


def csr_vectors(seed, counter_bits):
    rng = random.Random(seed)
    limit = (1 << counter_bits) - 1
    counts = [0] * 6
    snapshots = [0] * 6
    maximum = snapshot_maximum = 0
    enabled = sticky = False
    cycle = 0
    response = None
    due = None
    records = []
    coverage = dict(read=0, write=0, error=0, stall=0, clear=0, snapshot=0,
                    saturation=0, clear_with_event=0, snapshot_with_event=0)

    def edge(request=None, ready=True, events=None, reset=False):
        nonlocal counts, snapshots, maximum, snapshot_maximum, enabled, sticky
        nonlocal cycle, response, due
        # Event tuple is DDR, alignment population, bubble, ULP-valid, distance, error, active.
        if events is None:
            events = (
                rng.randrange(2), rng.randrange(65), rng.randrange(2), rng.randrange(2),
                rng.choice((0, 1, 123, 65535, 0xFFFFFFFF)), rng.randrange(19) == 0,
                rng.randrange(2),
            )
        ddr, alignment, bubble, ulp, distance, error, active = events
        valid = request is not None
        write, address, data, strobe = request or (0, 0, 0, 0)
        input_ready = not reset and response is None and due is None
        accepted = valid and input_ready
        read_data = 0
        request_error = False
        if accepted:
            mask = sum(255 << (8 * byte) for byte in range(4) if strobe >> byte & 1)
            if address & 3:
                request_error = True
            elif write:
                request_error = address != 4 or bool(data & mask & 0xFFFFFFF8)
            elif address == 0:
                read_data = 0x02020002
            elif address == 4:
                read_data = int(enabled)
            elif address == 8:
                read_data = int(active) | (int(sticky) << 1) | (
                    int(any(value == limit for value in counts)) << 2)
            elif address == 0x060:
                read_data = snapshot_maximum
            else:
                for index, base in enumerate(COUNTER_ADDRESSES):
                    if address in (base, base + 4):
                        read_data = (snapshots[index] >> (32 * (address != base))) & 0xFFFFFFFF
                        break
                else:
                    request_error = True
            coverage["write" if write else "read"] += 1
            coverage["error"] += request_error
        if reset:
            counts, snapshots = [0] * 6, [0] * 6
            maximum = snapshot_maximum = 0
            enabled = sticky = False
            response = due = None
        else:
            if response is not None:
                if ready:
                    response = None
                else:
                    coverage["stall"] += 1
            if due is not None:
                assert due[0] == cycle
                response = due[1:]
                due = None
            if accepted:
                due = (cycle + 1, read_data if not request_error else 0, int(request_error))
            control = accepted and write and not request_error and strobe & 1
            clear = control and data & 2
            snapshot = control and data & 4
            if clear:
                counts, snapshots = [0] * 6, [0] * 6
                maximum = snapshot_maximum = 0
                sticky = False
                coverage["clear"] += 1
                coverage["clear_with_event"] += bool(ddr or alignment or bubble or ulp)
            else:
                sticky |= bool(error)
                if snapshot:
                    snapshots, snapshot_maximum = counts[:], maximum
                    coverage["snapshot"] += 1
                    coverage["snapshot_with_event"] += bool(ddr or alignment or bubble or ulp)
                if enabled:
                    increments = (ddr, alignment, bubble,
                                  distance if ulp and distance != 0xFFFFFFFF else 0,
                                  int(ulp and distance != 0xFFFFFFFF),
                                  int(ulp and distance == 0xFFFFFFFF))
                    counts = [min(limit, value + increment)
                              for value, increment in zip(counts, increments)]
                    if ulp and distance != 0xFFFFFFFF:
                        maximum = max(maximum, distance)
                    coverage["saturation"] += any(value == limit for value in counts)
            if control:
                enabled = bool(data & 1)
        result_valid = response is not None and not reset
        records.append((
            int(not reset), int(valid), write, address, data, strobe, int(ready),
            int(ddr), alignment, int(bubble), int(ulp), distance, int(error), int(active),
            int(not reset and response is None and due is None),
            int(result_valid), response[0] if result_valid else 0,
            response[1] if result_valid else 0,
        ))
        cycle += 1
        return accepted

    def transaction(write, address, data=0, strobe=15, events=None):
        request = (write, address, data, strobe)
        while not edge(request, events=events):
            pass
        for _ in range(4):
            edge(ready=False)
        edge()

    edge(reset=True)
    edge(reset=True)
    transaction(0, 0)
    transaction(1, 4, 1)
    for _ in range(300):
        edge()
    transaction(1, 4, 5, events=(1, 64, 1, 1, 7, 0, 1))
    for address in (0x020, 0x024, 0x030, 0x034, 0x040, 0x044,
                    0x050, 0x054, 0x060, 0x068, 0x06C, 0x070, 0x074, 0x008):
        transaction(0, address)
    for address in (0, 1, 2, 3, 0xFFC, 0x020):
        transaction(1, address, 7)
        transaction(0, address)
    for strobe in range(16):
        transaction(1, 4, 0xFFFF0001, strobe)
        transaction(0, 4)
    transaction(1, 4, 7, events=(1, 64, 1, 1, 0xFFFFFFFF, 1, 1))
    for address in (*COUNTER_ADDRESSES, 0x060, 0x008):
        transaction(0, address)
    # Reset during a held response must abort it and reset counters/snapshots.
    edge((0, 0, 0, 15))
    edge(ready=False)
    edge(reset=True, ready=False)
    transaction(0, 0x020)
    for key, value in coverage.items():
        if key != "saturation" or counter_bits < 64:
            assert value, f"unexercised CSR bin: {key}"
    return records, coverage


def simulate_csr(run, seed, simulator, compile_and_run, counter_bits=64):
    stem = f"csr-{counter_bits}-{seed}-{simulator}"
    directory = run.path / stem
    directory.mkdir()
    records, coverage = csr_vectors(seed, counter_bits)
    vectors = directory / "vectors.txt"
    with vectors.open("x") as output:
        for record in records:
            output.write(" ".join(f"{value:x}" for value in record) + "\n")
    bench = directory / "tb.sv"
    bench.write_text(f"""`timescale 1ns/1ps
module tb;
  reg clk=0,rst_n=0,csr_req_valid=0,csr_req_write=0,csr_rsp_ready=0;
  reg [11:0] csr_req_addr=0;
  reg [31:0] csr_req_wdata=0,ulp_distance=0;
  reg [3:0] csr_req_wstrb=0;
  reg active=0,error_event=0,fp_ddr_stall_event=0,epilogue_bubble_event=0,ulp_valid=0;
  reg [6:0] alignment_events=0;
  wire csr_req_ready,csr_rsp_valid,csr_rsp_error;
  wire [31:0] csr_rsp_rdata;
  reg expected_ready,expected_valid,expected_error;
  reg [31:0] expected_data;
  integer file_handle,scan,cycle,compared=0;
  always #5 clk=~clk;
  anvil_q1_fp2_telemetry_csr #(.COUNTER_BITS({counter_bits})) dut(.*);
  task compare;
    if ({{csr_req_ready,csr_rsp_valid,csr_rsp_rdata,csr_rsp_error}} !==
        {{expected_ready,expected_valid,expected_data,expected_error}})
      $fatal(1,"CSR cycle=%0d got=%b/%b/%h/%b expected=%b/%b/%h/%b",
        cycle,csr_req_ready,csr_rsp_valid,csr_rsp_rdata,csr_rsp_error,
        expected_ready,expected_valid,expected_data,expected_error);
  endtask
  initial begin
    #1;
    if ({{csr_req_ready,csr_rsp_valid,csr_rsp_rdata,csr_rsp_error}} !== 0)
      $fatal(1,"time-zero reset outputs");
    @(posedge clk);
    if ({{csr_req_ready,csr_rsp_valid,csr_rsp_rdata,csr_rsp_error}} !== 0)
      $fatal(1,"first Active reset outputs");
    @(negedge clk);
    file_handle=$fopen("{run.relative / stem / 'vectors.txt'}","r");
    if (!file_handle) $fatal(1,"fixture open");
    for (cycle=0;cycle<{len(records)};cycle=cycle+1) begin
      scan=$fscanf(file_handle,"%h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h\\n",
        rst_n,csr_req_valid,csr_req_write,csr_req_addr,csr_req_wdata,csr_req_wstrb,
        csr_rsp_ready,fp_ddr_stall_event,alignment_events,epilogue_bubble_event,
        ulp_valid,ulp_distance,error_event,active,
        expected_ready,expected_valid,expected_data,expected_error);
      if (scan!=18) $fatal(1,"malformed fixture");
      @(posedge clk); #1; compare(); compared=compared+1;
      @(negedge clk); compare();
    end
    if (compared!={len(records)}) $fatal(1,"missing CSR comparisons");
    $display("SUMMARY csr: compared=%0d counter_bits={counter_bits}",compared);
    $finish;
  end
endmodule
""")
    compile_and_run(run, directory, bench, ["rtl/anvil_q1_fp2_telemetry_csr.sv"],
                    simulator, stem)
    run.receipt["comparisons"].append({
        "kind": "csr", "seed": seed, "counter_bits": counter_bits,
        "edges": len(records), "coverage": coverage, "result": "passed",
    })


def simulate_ddr(run, seed, simulator, compile_and_run):
    stem = f"ddr-{seed}-{simulator}"
    directory = run.path / stem
    directory.mkdir()
    bench = directory / "tb.sv"
    bench.write_text(f"""`timescale 1ns/1ps
module tb;
  reg clk=0,rst_n=0,cmd_valid=0,cmd_write=0,cmd_scale=0,out_ready=0;
  reg [3:0] cmd_kind=0;
  reg [31:0] cmd_layer=0,cmd_row=0,cmd_col=0,cmd_tag=0;
  reg [2:0] cmd_proj=0;
  reg [511:0] cmd_wdata=0;
  reg [63:0] cmd_wstrb=0;
  wire cmd_ready,out_valid,out_write,out_error,stall_event;
  wire [31:0] out_tag;
  wire [511:0] out_data;
  reg work_active=0,result_needed=0,ddr_req_ready=0,ddr_rsp_valid=0;
  reg ddr_rsp_id=0,ddr_rsp_error=0;
  reg [511:0] ddr_rsp_rdata=0;
  wire ddr_req_valid,ddr_req_write,ddr_req_id,ddr_req_scale,ddr_rsp_ready;
  wire [3:0] ddr_req_kind;
  wire [31:0] ddr_req_layer,ddr_req_row,ddr_req_col;
  wire [2:0] ddr_req_proj;
  wire [511:0] ddr_req_wdata;
  wire [63:0] ddr_req_wstrb;
  anvil_q1_fp2_ddr_pingpong dut(.*);
  always #5 clk=~clk;
  integer accepted=0,issued=0,retired=0,cycle=0,i,chosen;
  integer transaction[0:1],due[0:1];
  integer returned[0:95];
  integer out_of_order=0,two_outstanding=0,refill=0,stalls=0,zero_latency=0;
  reg live[0:1],pop,push,issue,response;
  reg [31:0] rng=32'd{seed};
  reg held_output=0,held_request=0;
  reg [545:0] saved_output;
  reg [681:0] saved_request;
  function [511:0] data(input integer index);
    integer n;
    for (n=0;n<16;n=n+1) data[32*n+:32]=32'h9e3779b9*(index+1)^32'hdeadbeef*n;
  endfunction
  function fault(input integer index);
    fault=index%13==5;
  endfunction
  task reset_check;
    if ({{cmd_ready,out_valid,out_tag,out_write,out_error,out_data,stall_event,
      ddr_req_valid,ddr_req_write,ddr_req_id,ddr_req_scale,ddr_req_kind,
      ddr_req_layer,ddr_req_proj,ddr_req_row,ddr_req_col,ddr_req_wdata,
      ddr_req_wstrb,ddr_rsp_ready}} !== 0) $fatal(1,"DDR reset");
  endtask
  initial begin
    live[0]=0; live[1]=0;
    for (i=0;i<96;i=i+1) returned[i]=0;
    #1; reset_check(); @(posedge clk); reset_check();
    #1; reset_check(); @(negedge clk); reset_check(); rst_n=1; work_active=1;
    for (cycle=0;cycle<10000;cycle=cycle+1) begin
      rng=rng^(rng<<13); rng=rng^(rng>>17); rng=rng^(rng<<5);
      cmd_valid=accepted<96;
      cmd_tag=accepted; cmd_write=accepted[0]; cmd_scale=accepted[1];
      cmd_kind=accepted%15; cmd_layer=accepted/15; cmd_proj=accepted%7;
      cmd_row=accepted*3; cmd_col=accepted*64;
      cmd_wdata=data(accepted); cmd_wstrb=64'hffffffffffffffff >> (accepted%64);
      ddr_req_ready=(cycle%29>4) && rng[3:0]!=0;
      out_ready=(cycle%31>8) && rng[2:0]!=0;
      result_needed=accepted>retired;
      if (!ddr_rsp_valid) begin
        chosen=-1;
        if (live[1] && cycle>=due[1]) chosen=1;
        else if (live[0] && cycle>=due[0]) chosen=0;
        if (chosen>=0) begin
          ddr_rsp_id=chosen; ddr_rsp_valid=1;
          ddr_rsp_error=fault(transaction[chosen]);
          ddr_rsp_rdata=data(transaction[chosen])^512'd17;
          if (live[!chosen] && transaction[chosen]>transaction[!chosen])
            out_of_order=out_of_order+1;
        end
      end
      #1;
      // Some transactions receive a legal same-edge bridge response.
      if (!ddr_rsp_valid && ddr_req_valid && ddr_req_ready && issued%7==0) begin
        ddr_rsp_valid=1; ddr_rsp_id=ddr_req_id;
        ddr_rsp_error=fault(issued); ddr_rsp_rdata=data(issued)^512'd17;
        zero_latency=zero_latency+1;
      end
      #1;
      if ((^{{cmd_ready,out_valid,ddr_req_valid,ddr_rsp_ready,stall_event}})===1'bx)
        $fatal(1,"DDR active control X/Z");
      if (held_output && ({{out_valid,out_tag,out_write,out_error,out_data}} !==
        {{1'b1,saved_output}})) $fatal(1,"DDR returned payload changed while stalled");
      if (held_request && ({{ddr_req_valid,ddr_req_write,ddr_req_id,ddr_req_scale,
        ddr_req_kind,ddr_req_layer,ddr_req_proj,ddr_req_row,ddr_req_col,
        ddr_req_wdata,ddr_req_wstrb}} !== {{1'b1,saved_request}}))
        $fatal(1,"DDR offered request changed while stalled");
      held_output=out_valid && !out_ready;
      saved_output={{out_tag,out_write,out_error,out_data}};
      held_request=ddr_req_valid && !ddr_req_ready;
      saved_request={{ddr_req_write,ddr_req_id,ddr_req_scale,ddr_req_kind,ddr_req_layer,
        ddr_req_proj,ddr_req_row,ddr_req_col,ddr_req_wdata,ddr_req_wstrb}};
      if (held_request) begin
        stalls=stalls+1;
        if (stall_event!==1) $fatal(1,"missing DDR backpressure event");
      end
      pop=out_valid && out_ready; push=cmd_valid && cmd_ready;
      issue=ddr_req_valid && ddr_req_ready;
      response=ddr_rsp_valid && ddr_rsp_ready;
      if (out_valid) begin
        if (retired>=issued || !returned[retired] ||
            {{out_tag,out_write,out_error,out_data}} !==
              {{32'(retired),retired[0],fault(retired),(data(retired)^512'd17)}})
          $fatal(1,"DDR RESPONSE OWNERSHIP index=%0d tag=%0d got=%h",
            retired,out_tag,out_data);
      end
      if (issue) begin
        if (issued>=accepted || live[ddr_req_id]) $fatal(1,"DDR issue without ownership");
        if ({{ddr_req_write,ddr_req_scale,ddr_req_kind,ddr_req_layer,
          ddr_req_proj,ddr_req_row,ddr_req_col,ddr_req_wdata,ddr_req_wstrb}} !==
          {{issued[0],issued[1],4'(issued%15),32'(issued/15),3'(issued%7),
            32'(issued*3),32'(issued*64),data(issued),
            (64'hffffffffffffffff>>(issued%64))}})
          $fatal(1,"DDR descriptor mismatch");
      end
      if (ddr_rsp_valid && !ddr_rsp_ready) $fatal(1,"bridge response rejected for live ID");
      @(posedge clk);
      if (issue) begin
        live[ddr_req_id]=1; transaction[ddr_req_id]=issued;
        due[ddr_req_id]=cycle+(ddr_req_id ? 2 : 15);
        issued=issued+1;
      end
      if (response) begin
        if (!live[ddr_rsp_id]) $fatal(1,"DDR unexpected response");
        returned[transaction[ddr_rsp_id]]=1; live[ddr_rsp_id]=0;
      end
      if (push) accepted=accepted+1;
      if (pop) retired=retired+1;
      if (pop && push && accepted-retired==2) refill=refill+1;
      if (live[0] && live[1]) two_outstanding=two_outstanding+1;
      #1;
      if (response) ddr_rsp_valid=0;
      @(negedge clk);
      if (retired==96) begin
        if (accepted!=96 || issued!=96 || out_of_order==0 || two_outstanding==0 ||
            refill==0 || stalls==0 || zero_latency==0)
          $fatal(1,"DDR coverage missing: reordered=%0d two=%0d refill=%0d zero=%0d",
            out_of_order,two_outstanding,refill,zero_latency);
        $display("SUMMARY ddr: compared=%0d reordered=%0d two=%0d refill=%0d zero=%0d",
          retired,out_of_order,two_outstanding,refill,zero_latency);
        $finish;
      end
    end
    $fatal(1,"DDR cycle watchdog");
  end
endmodule
""")
    compile_and_run(run, directory, bench, ["rtl/anvil_q1_fp2_ddr_pingpong.sv"],
                    simulator, stem)
    run.receipt["comparisons"].append({
        "kind": "ddr", "seed": seed, "transactions": 96, "result": "passed",
    })
