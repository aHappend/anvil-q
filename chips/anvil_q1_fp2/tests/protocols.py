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
