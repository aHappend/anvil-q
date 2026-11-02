"""Public-transfer command tests and independent mathematical operator fixtures."""

from decimal import Decimal, localcontext
import math
import random

from reference import approximation_interval, as_fraction, binary, bits32, f32, ordered


def decimal32(bits):
    value = as_fraction(bits)
    return Decimal(value.numerator) / Decimal(value.denominator)


def epilogue_cases(seed, count):
    rng = random.Random(seed)
    cases = []
    with localcontext() as context:
        context.prec = 70
        for operation in range(4):
            for case in range(count):
                length = (8, 16)[case % 2] if operation == 1 else (1, 3, 8, 16)[case % 4]
                position = (0, 1, 31, 32767)[case % 4]
                data = [bits32(rng.uniform(-5, 5)) for _ in range(length)]
                aux = [bits32(rng.uniform(-2, 2)) for _ in range(length)]
                residual = [bits32(rng.uniform(-3, 3)) for _ in range(length)]
                if operation == 2:
                    data[0] = bits32((-80, -20, -1, 0, 1, 20, 80)[case % 7])
                x = [decimal32(value) for value in data]
                a = [decimal32(value) for value in aux]
                if operation == 0:
                    factor = (sum(value * value for value in x) / length +
                              decimal32(0x358637BD)).sqrt()
                    expected = [float(value * gamma / factor) for value, gamma in zip(x, a)]
                elif operation == 1:
                    expected = [0.0] * length
                    for base in range(0, length, 8):
                        for j in range(4):
                            angle = position * 1000000 ** (-2 * j / 8)
                            cosine, sine = math.cos(angle), math.sin(angle)
                            aux[base + j] = bits32(cosine)
                            aux[base + j + 4] = bits32(sine)
                            left, right = float(x[base + j]), float(x[base + j + 4])
                            expected[base + j] = left * cosine - right * sine
                            expected[base + j + 4] = right * cosine + left * sine
                elif operation == 2:
                    expected = [
                        float(up * gate / (1 + (-gate).exp()))
                        for gate, up in zip(x, a)
                    ]
                else:
                    expected = [f32(binary(value, other, False)[0])
                                for value, other in zip(data, residual)]
                bounds = [
                    (bits32(value), bits32(value)) if operation == 3 else
                    approximation_interval(value, (0.005, 0.0005, 0.002)[operation])
                    for value in expected
                ]
                cases.append({
                    "operation": operation, "length": length, "position": position,
                    "input": list(zip(data, aux, residual)), "bounds": bounds,
                    "reference": list(map(bits32, expected)), "error": False,
                })
    for operation, length, position in ((0, 0, 0), (0, 17, 0), (1, 3, 0), (1, 8, 32768)):
        cases.append({
            "operation": operation, "length": length, "position": position,
            "input": [], "bounds": [], "reference": [], "error": True,
        })
    return cases


def attention_cases(seed, count):
    rng = random.Random(seed)
    cases = []
    with localcontext() as context:
        context.prec = 70
        for case in range(count):
            length = (1, 2, 3, 4, 15, 16, 17, 19)[case % 8]
            q = [bits32(rng.uniform(-2, 2)) >> 16 for _ in range(8)]
            keys, values = [], []
            for token in range(length):
                key = [bits32(rng.uniform(-2, 2)) >> 16 for _ in range(8)]
                value = [bits32(rng.uniform(-2, 2)) >> 16 for _ in range(8)]
                if case % 4 == 0:
                    key = [bits32((token - length / 2) * 0.5) >> 16] * 8
                elif case % 4 == 1:
                    key = [bits32((length / 2 - token) * 0.5) >> 16] * 8
                elif case % 4 == 2:
                    key = [0x3F80] * 8
                keys.append(key)
                values.append(value)
            query = [decimal32(value << 16) for value in q]
            scores = [
                sum(left * decimal32(right << 16) for left, right in zip(query, key)) /
                Decimal(8).sqrt() for key in keys
            ]
            maximum = max(scores)
            probabilities = [(score - maximum).exp() for score in scores]
            total = sum(probabilities)
            expected = [
                float(sum(probability * decimal32(value[j] << 16)
                          for probability, value in zip(probabilities, values)) / total)
                for j in range(8)
            ]
            cases.append({
                "length": length, "query": q, "keys": keys, "values": values,
                "bounds": [approximation_interval(value, 0.003) for value in expected],
                "reference": list(map(bits32, expected)), "error": False,
            })
    for length in (0, 33):
        cases.append({
            "length": length, "query": [], "keys": [], "values": [],
            "bounds": [], "reference": [], "error": True,
        })
    return cases


def command_tb(kind, path, cases, seed, tile):
    epilogue = kind == "epilogue"
    instance = (
        """anvil_q1_fp2_epilogue_fusion #(.MAX_VECTOR(16),.HEAD_DIM(8)) dut(
          .clk(clk),.rst_n(rst_n),.cmd_valid(cmd_valid),.cmd_ready(cmd_ready),
          .cmd_op(cmd_op),.cmd_len(cmd_len),.cmd_pos(cmd_pos),
          .in_valid(in_valid),.in_ready(in_ready),.in_data(in_data),
          .in_aux(in_aux),.in_residual(in_residual),.in_last(in_last),
          .out_valid(out_valid),.out_ready(out_ready),.out_data(out_data),
          .out_last(out_last),.status(status),.done(done),.error(error));"""
        if epilogue else
        f"""anvil_q1_fp2_flash_attn #(.HEAD_DIM(8),.MAX_SEQ_LEN(32),.TILE_TOKENS({tile})) dut(
          .clk(clk),.rst_n(rst_n),.cmd_valid(cmd_valid),.cmd_ready(cmd_ready),
          .cmd_len(cmd_len),.q_valid(q_valid),.q_ready(q_ready),
          .q_data(q_data),.q_last(q_last),.kv_valid(kv_valid),.kv_ready(kv_ready),
          .k_data(k_data),.v_data(v_data),.kv_last(kv_last),
          .out_valid(out_valid),.out_ready(out_ready),.out_data(out_data),
          .out_last(out_last),.status(status),.done(done),.error(error));"""
    )
    drive = """
      for (j=0;j<input_count;j=j+1) begin
        repeat ((j+test)%3) tick();
        in_data=data[j]; in_aux=aux[j]; in_residual=residual[j];
        in_last=(j+1==input_count); in_valid=1; accepted_input=0;
        while (!accepted_input) tick();
        in_valid=0;
      end
""" if epilogue else """
      for (j=0;j<8 && !expect_error;j=j+1) begin
        repeat ((j+test)%3) tick();
        q_data=query[j]; q_last=(j==7); q_valid=1; accepted_query=0;
        while (!accepted_query) tick();
        q_valid=0;
      end
      for (j=0;j<input_count;j=j+1) begin
        repeat ((j+test)%3) tick();
        k_data=keys[j]; v_data=values[j]; kv_last=((j&7)==7);
        kv_valid=1; accepted_kv=0;
        while (!accepted_kv) tick();
        kv_valid=0;
      end
"""
    return f"""`timescale 1ns/1ps
module tb;
  reg clk=0,rst_n=0,cmd_valid=0,in_valid=0,in_last=0,out_ready=0;
  reg q_valid=0,q_last=0,kv_valid=0,kv_last=0;
  reg [1:0] cmd_op=0;
  reg [31:0] cmd_len=0,cmd_pos=0,in_data=0,in_aux=0,in_residual=0;
  reg [15:0] q_data=0,k_data=0,v_data=0;
  wire cmd_ready,out_valid,out_last,done,error;
  wire in_ready,q_ready,kv_ready;
  wire [31:0] out_data;
  wire [4:0] status;
  {instance}
  {"assign q_ready=0; assign kv_ready=0;" if epilogue else "assign in_ready=0;"}
  always #5 clk=~clk;
  integer file_handle,scan,test,j,n,operation,length,position,input_count,output_count;
  integer edge_count=0,command_edge=-1,last_edge=-1,compared=0,outputs=0;
  integer completed=0,stalls=0,input_stalls=0,ulp_max=0;
  reg [31:0] data[0:255],aux[0:255],residual[0:255];
  reg [15:0] query[0:7],keys[0:255],values[0:255];
  reg [31:0] low[0:15],high[0:15],reference_value[0:15];
  reg [31:0] rng=0,scanned0,scanned1,scanned2;
  string vector_file;
  reg [31:0] held_data;
  reg [4:0] held_status;
  reg held_last,held=0,expect_error,seen_done=0;
  reg accepted_command,accepted_input,accepted_query,accepted_kv;
  function [31:0] ordered(input [31:0] value);
    ordered=value[31] ? ~value : value ^ 32'h80000000;
  endfunction
  task reset_check;
    if ({{cmd_ready,in_ready,q_ready,kv_ready,out_valid,out_data,out_last,status,done,error}} !== 0)
      $fatal(1,"RESET public outputs not zero");
  endtask
  task tick;
    reg final_transfer;
    reg [31:0] ulp;
    begin
      edge_count=edge_count+1;
      if (edge_count>{500000 if cases < 100 else 10000000}) $fatal(1,"bounded cycle watchdog");
      rng=rng^(rng<<13); rng=rng^(rng>>17); rng=rng^(rng<<5);
      out_ready=(edge_count%19>=4) && rng[2:0]!=0;
      #1;
      if ((^{{cmd_ready,in_ready,q_ready,kv_ready,out_valid,done,error,status}})===1'bx)
        $fatal(1,"active public control X/Z");
      if (done || error) $fatal(1,"completion must be one edge pulse");
      accepted_command=cmd_valid && cmd_ready;
      accepted_input=in_valid && in_ready;
      accepted_query=q_valid && q_ready;
      accepted_kv=kv_valid && kv_ready;
      if (accepted_command) begin
        if (command_edge!=-1) $fatal(1,"duplicate command");
        command_edge=edge_count;
        if (in_ready || q_ready || kv_ready) $fatal(1,"operand accepted before command");
      end
      if (held && ({{out_valid,out_data,out_last,status}} !==
                   {{1'b1,held_data,held_last,held_status}}))
        $fatal(1,"output changed under backpressure");
      final_transfer=0;
      if (out_valid) begin
        if (expect_error || outputs>=output_count) $fatal(1,"unexpected output");
        if ((^out_data)===1'bx || (^status)===1'bx) $fatal(1,"active data X/Z");
        if (ordered(out_data)<ordered(low[outputs]) ||
            ordered(out_data)>ordered(high[outputs]) || |status[4:2])
          $fatal(1,"NUMERICAL {kind} test=%0d op=%0d component=%0d got=%h/%h expected=[%h,%h]",
            test,operation,outputs,out_data,status,low[outputs],high[outputs]);
        if (out_last !== (outputs+1==output_count)) $fatal(1,"last mismatch");
        ulp=ordered(out_data)>ordered(reference_value[outputs]) ?
          ordered(out_data)-ordered(reference_value[outputs]) :
          ordered(reference_value[outputs])-ordered(out_data);
        if (ulp>ulp_max) ulp_max=ulp;
        if (out_ready) begin
          outputs=outputs+1; compared=compared+1;
          if (out_last) begin final_transfer=1; last_edge=edge_count; end
        end else stalls=stalls+1;
      end
      held=out_valid && !out_ready;
      held_data=out_data; held_last=out_last; held_status=status;
      @(posedge clk);
      #1;
      if (done) begin
        if (error !== expect_error) $fatal(1,"error completion mismatch");
        if (expect_error) begin
          if (edge_count!=command_edge+2 || outputs!=0)
            $fatal(1,"invalid command latency or output");
        end else if (edge_count!=last_edge+1 || outputs!=output_count)
          $fatal(1,"final transfer completion latency");
        completed=completed+1; seen_done=1;
      end else if ((expect_error && command_edge>=0 && edge_count==command_edge+2) ||
                   (!expect_error && last_edge>=0 && edge_count==last_edge+1))
        $fatal(1,"missing completion");
      @(negedge clk);
    end
  endtask
  initial begin
    #1; reset_check(); @(posedge clk); reset_check();
    #1; reset_check(); @(negedge clk); reset_check(); rst_n=1;
    if (!$value$plusargs("vectors=%s",vector_file) || !$value$plusargs("seed=%d",rng))
      $fatal(1,"missing command vector/seed arguments");
    file_handle=$fopen(vector_file,"r");
    if (!file_handle) $fatal(1,"fixture open");
    for (test=0;test<{cases};test=test+1) begin
      scan=$fscanf(file_handle,"%d %d %d %d %d %d\\n",
        operation,length,position,input_count,output_count,n);
      if (scan!=6) $fatal(1,"fixture header");
      expect_error=n; outputs=0; seen_done=0; command_edge=-1; last_edge=-1;
      {"for (j=0;j<input_count;j=j+1) begin" if epilogue else "for (j=0;j<8 && !expect_error;j=j+1) begin"}
        scan=$fscanf(file_handle,"{"%h %h %h" if epilogue else "%h"}\\n",scanned0{",scanned1,scanned2" if epilogue else ""});
        if (scan!={3 if epilogue else 1}) $fatal(1,"input fixture");
        {"data[j]=scanned0; aux[j]=scanned1; residual[j]=scanned2;" if epilogue else "query[j]=scanned0[15:0];"}
      end
      {"" if epilogue else '''
      for (j=0;j<input_count;j=j+1) begin
        scan=$fscanf(file_handle,"%h %h\\n",scanned0,scanned1);
        if (scan!=2) $fatal(1,"KV fixture");
        keys[j]=scanned0[15:0]; values[j]=scanned1[15:0];
      end'''}
      for (j=0;j<output_count;j=j+1) begin
        scan=$fscanf(file_handle,"%h %h %h\\n",scanned0,scanned1,scanned2);
        if (scan!=3) $fatal(1,"output fixture");
        low[j]=scanned0; high[j]=scanned1; reference_value[j]=scanned2;
      end
      cmd_op=operation[1:0]; cmd_len=length; cmd_pos=position;
      cmd_valid=1; accepted_command=0;
      while (!accepted_command) tick();
      cmd_valid=0;
      {drive}
      while (!seen_done) tick();
      #1;
      @(posedge clk); #1;
      if (done || error || !cmd_ready) $fatal(1,"return to idle");
      @(negedge clk);
    end
    if (completed!={cases} || compared==0 || stalls==0)
      $fatal(1,"required comparison/completion/backpressure coverage absent");
    $display("SUMMARY {kind}: commands=%0d compared=%0d stalls=%0d max_ulp=%0d",
      completed,compared,stalls,ulp_max);
    $finish;
  end
endmodule
"""


def simulate_commands(run, kind, seed, count, simulator, compile_and_run, tile=3):
    if simulator == "iverilog" and count > 2:
        simulator = "verilator"
    cases = epilogue_cases(seed, count) if kind == "epilogue" else attention_cases(seed, count)
    stem = f"{kind}-{tile}-{seed}-{simulator}"
    directory = run.path / stem
    directory.mkdir()
    fixtures = directory / "vectors.txt"
    with fixtures.open("x") as output:
        for case in cases:
            epilogue = kind == "epilogue"
            inputs = case["input"] if epilogue else [
                pair for key, value in zip(case["keys"], case["values"])
                for pair in zip(key, value)
            ]
            output.write(
                f"{case.get('operation', 0)} {case['length']} {case.get('position', 0)} "
                f"{len(inputs)} {len(case['bounds'])} {int(case['error'])}\n"
            )
            if not epilogue:
                for value in case["query"]:
                    output.write(f"{value:04x}\n")
            for values in inputs:
                output.write(" ".join(f"{value:08x}" for value in values) + "\n")
            for (low, high), reference in zip(case["bounds"], case["reference"]):
                assert ordered(low) <= ordered(high)
                output.write(f"{low:08x} {high:08x} {reference:08x}\n")
    bench = directory / "tb.sv"
    bench.write_text(command_tb(
        kind, str(run.relative / stem / "vectors.txt"),
        len(cases), seed, tile,
    ))
    sources = [
        "rtl/anvil_q1_fp2_00_pkg.sv", "rtl/anvil_q1_fp2_fp32_binary.sv",
        "rtl/anvil_q1_fp2_fast_rsqrt.sv", "rtl/anvil_q1_fp2_reciprocal.sv",
        "rtl/anvil_q1_fp2_exp.sv",
        f"rtl/anvil_q1_fp2_{'epilogue_fusion' if kind == 'epilogue' else 'flash_attn'}.sv",
    ]
    compile_and_run(run, directory, bench, sources, simulator, stem,
                    arguments=[f"+vectors={run.relative / stem / 'vectors.txt'}",
                               f"+seed={seed}"], cache=True)
    run.receipt["comparisons"].append({
        "kind": kind, "seed": seed, "simulator": simulator, "tile": tile,
        "commands": len(cases), "components": sum(len(case["bounds"]) for case in cases),
        "result": "passed",
    })
