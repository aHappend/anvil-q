"""Public-pin arithmetic experiments; expected data is generated independently."""

from fractions import Fraction
import random

from execution import ROOT, relative
import reference as ref


QK_BENCH = r"""
module leaf_tb;
  parameter D=8;
  reg clk=0;
  always #5 clk=~clk;
  reg rst_n,flush=0,in_valid=0,in_is_key=0,out_ready=0;
  reg [5:0] in_head=0;
  reg [31:0] in_layer=0,in_pos=0;
  reg [D*16-1:0] in_data=0,in_gamma=0;
  reg [(D/2)*16-1:0] in_cos=0,in_sin=0;
  wire in_ready,out_valid,out_error,out_is_key;
  wire [5:0] out_head;
  wire [31:0] out_layer,out_pos;
  wire [D*16-1:0] out_data;
  reg [D*16-1:0] expected;
  integer fd,rc,expected_error,key_value,head_value,case_id=0,age,stall;
  integer position_value,layer_value;
  reg [4095:0] filename;
  anvil_qn1_qknorm_rope #(.HEAD_DIM(D)) dut(
    .clk(clk),.rst_n(rst_n),.flush(flush),.in_valid(in_valid),.in_ready(in_ready),
    .in_is_key(in_is_key),.in_head(in_head),.in_layer(in_layer),.in_pos(in_pos),
    .in_data(in_data),.in_gamma(in_gamma),.in_cos(in_cos),.in_sin(in_sin),
    .out_valid(out_valid),.out_error(out_error),.out_is_key(out_is_key),
    .out_head(out_head),.out_layer(out_layer),.out_pos(out_pos),.out_data(out_data),
    .out_ready(out_ready));
  task reset_outputs;
    begin
      if ({in_ready,out_valid,out_error,out_is_key,out_head,out_layer,out_pos,out_data}
          !== 0) $fatal(1,"RESET_XZ_OR_NONZERO");
    end
  endtask
  always @(posedge clk or negedge clk) if (!rst_n) reset_outputs();
  initial begin
    rst_n=0;
    #1; reset_outputs();
    @(negedge clk); rst_n=1;
    #1;
    if (!$value$plusargs("vectors=%s",filename)) $fatal(1,"MISSING_VECTORS");
    fd=$fopen(filename,"r");
    if (!fd) $fatal(1,"OPEN_VECTORS");
    rc=$fscanf(fd,"%d %d %d %d %h %h %h %h %d %h\n",
      key_value,head_value,layer_value,position_value,
      in_data,in_gamma,in_cos,in_sin,expected_error,expected);
    while (rc==10) begin
      if (case_id>0) @(negedge clk);
      if (in_ready!==1 || out_valid!==0) $fatal(1,"IDLE_NOT_READY case=%0d",case_id);
      in_is_key=key_value; in_head=head_value; in_layer=layer_value;
      in_pos=position_value; in_valid=1; out_ready=0;
      @(posedge clk); #1;
      if (in_ready!==0 || out_valid!==0) $fatal(1,"ACCEPT_OWNERSHIP");
      @(negedge clk); in_valid=0;
      for (age=1;age<=133;age=age+1) begin
        @(posedge clk); #1;
        if (age<133 && out_valid!==0)
          $fatal(1,"EARLY_QK_RESULT case=%0d age=%0d",case_id,age);
        if (in_ready!==0) $fatal(1,"OVERLAPPING_QK_ACCEPTANCE");
      end
      if (out_valid!==1 || out_error!==expected_error[0] ||
          out_data!==expected || out_is_key!==in_is_key || out_head!==in_head ||
          out_layer!==in_layer || out_pos!==in_pos)
        $fatal(1,"QK_COMPARE case=%0d age=133 valid=%b error=%b expected_error=%b data=%h expected=%h",
          case_id,out_valid,out_error,expected_error[0],out_data,expected);
      for (stall=0;stall<3;stall=stall+1) begin
        @(posedge clk); #1;
        if (out_valid!==1 || out_data!==expected || out_error!==expected_error[0] ||
            out_is_key!==in_is_key || out_head!==in_head || out_layer!==in_layer ||
            out_pos!==in_pos || in_ready!==0) $fatal(1,"QK_STALL_UNSTABLE");
      end
      @(negedge clk); out_ready=1;
      @(posedge clk);
      if (out_valid!==1 || in_ready!==0) $fatal(1,"RETIRE_PREEDGE");
      #1;
      if (out_valid!==0 || in_ready!==1) $fatal(1,"RETIRE_OWNERSHIP");
      @(negedge clk); out_ready=0;
      case_id=case_id+1;
      rc=$fscanf(fd,"%d %d %d %d %h %h %h %h %d %h\n",
        key_value,head_value,layer_value,position_value,
        in_data,in_gamma,in_cos,in_sin,expected_error,expected);
    end
    if (rc!=0 && rc!=-1) $fatal(1,"MALFORMED_VECTOR rc=%0d",rc);
    if (case_id==0) $fatal(1,"EMPTY_COMPARISON");
    $fclose(fd);
    @(negedge clk); in_valid=1; in_pos=0;
    @(posedge clk); #1;
    @(negedge clk); in_valid=0;
    repeat (20) @(posedge clk);
    @(negedge clk); rst_n=0;
    #1; reset_outputs();
    repeat (2) @(negedge clk);
    rst_n=1;
    @(negedge clk); in_valid=1;
    @(posedge clk); #1;
    @(negedge clk); in_valid=0;
    repeat (20) @(posedge clk);
    @(negedge clk); flush=1;
    #1; reset_outputs();
    @(posedge clk); #1;
    @(negedge clk); flush=0;
    repeat (140) begin
      @(posedge clk); #1;
      if (out_valid!==0) $fatal(1,"FLUSH_LEAK");
    end
    $display("SUMMARY qk_cases=%0d elements=%0d latency=133 stall_cycles=%0d reset_during_work=1 flush_during_work=1",
      case_id,case_id*D,3*case_id);
    $finish;
  end
  initial begin
    repeat (500000) @(posedge clk);
    $fatal(1,"CYCLE_BOUND");
  end
endmodule
"""


def qk_vectors(dimension, full=False):
    vectors = []
    positions = [0, 1, 32767, 32768, 40959]
    for seed in ([17, 89, 203] if full else [17]):
        rng = random.Random(seed)
        count = 64 if full else 5
        for key in (0, 1):
            for index in range(count):
                position = positions[index % len(positions)]
                gamma = [ref.encode(Fraction(rng.randrange(64, 193), 128), 16)
                         for _ in range(dimension)]
                if index == 0:
                    data = [0] * dimension
                elif index == 1:
                    data = [0x3F80] * dimension
                elif index == 2:
                    data = [ref.encode(Fraction((-1) ** lane * (lane + 1), 32), 16)
                            for lane in range(dimension)]
                elif index == 3:
                    data = [1 + (lane % 127) for lane in range(dimension)]
                else:
                    data = [ref.encode(Fraction(rng.randrange(-512, 513), 64), 16)
                            for _ in range(dimension)]
                cosine, sine = ref.coefficients(dimension, position)
                expected = ref.qknorm(data, gamma, cosine, sine, position)
                vectors.append((key, index % (8 if key else 32), seed % 36,
                                position, data, gamma, cosine, sine, 0, expected))
    for category in ("position", "head", "layer", "data", "gamma", "cosine", "overflow"):
        key, head, layer, position = 0, 0, 0, 1
        data, gamma = [0x3F80] * dimension, [0x3F80] * dimension
        cosine, sine = ref.coefficients(dimension, position)
        if category == "position":
            position = 40960
        elif category == "head":
            head = 32
        elif category == "layer":
            layer = 36
        elif category == "data":
            data[0] = 0x7FC1
        elif category == "gamma":
            gamma[-1] = 0x7F80
        elif category == "cosine":
            cosine[0] = 0xFF80
        else:
            data[0] = 0x7F7F
        vectors.append((key, head, layer, position, data, gamma, cosine, sine,
                        1, [0] * dimension))
    return vectors


def run_qk(run, simulator="icarus", dimension=8, full=False):
    vectors = qk_vectors(dimension, full)
    vector_file = run.path / f"qk-{dimension}.txt"
    with vector_file.open("x") as output:
        for key, head, layer, position, data, gamma, cosine, sine, error, expected in vectors:
            output.write(f"{key} {head} {layer} {position} "
                         f"{ref.pack(data,16):x} {ref.pack(gamma,16):x} "
                         f"{ref.pack(cosine,16):x} {ref.pack(sine,16):x} "
                         f"{error} {ref.pack(expected,16):x}\n")
    bench = run.path / "qk_tb.sv"
    bench.write_text(QK_BENCH)
    sources = [f"rtl/anvil_qn1_{name}.sv" for name in
               ("00_pkg", "fp32_mul", "fp32_add", "fp32_div", "fp32_sqrt", "qknorm_rope")]
    stem = f"qk-{dimension}-{simulator}"
    if simulator == "icarus":
        binary = run.path / f"{stem}.vvp"
        run.execute(["iverilog", "-g2012", "-Wall", "-s", "leaf_tb",
                     f"-Pleaf_tb.D={dimension}", "-o", relative(binary),
                     *sources, relative(bench)], f"{stem}-compile")
        text = run.execute(["vvp", relative(binary),
                            f"+vectors={relative(vector_file)}"], f"{stem}-simulation",
                           timeout=600)
    else:
        objects = run.path / f"obj-{stem}"
        run.execute(["verilator", "--binary", "--timing", "-Wno-fatal", "-j", "2",
                     "--top-module", "leaf_tb", f"-GD={dimension}",
                     "--Mdir", relative(objects), "-o", "simulate", *sources,
                     relative(bench)], f"{stem}-compile")
        text = run.execute([relative(objects / "simulate"),
                            f"+vectors={relative(vector_file)}"], f"{stem}-simulation")
        for pattern in ("*.o", "*.a", "*.gch"):
            for file in objects.glob(pattern):
                file.unlink()
    expected_record = f"SUMMARY qk_cases={len(vectors)} elements={len(vectors)*dimension} latency=133"
    if text.count(expected_record) != 1:
        raise AssertionError(f"missing/excess QK comparisons: expected {expected_record}")
    return {"qk_cases": len(vectors), "compared_elements": len(vectors) * dimension,
            "dimension": dimension, "simulator": simulator, "latency": 133}


SCALAR_BENCH = r"""
module scalar_tb;
  reg clk=0,rst_n,flush=0,in_valid=0,out_ready=0;
  always #5 clk=~clk;
  reg [2:0] in_op=0;
  reg [31:0] in_a=0,in_b=0;
  reg in_error=0;
  wire in_ready,out_valid,out_error;
  wire [31:0] out_data;
  integer fd,rc,operation,error_value,expected_error,count=0,cycles,stall;
  reg [31:0] expected;
  reg [4095:0] filename;
  anvil_qn1_scalar dut(.clk(clk),.rst_n(rst_n),.flush(flush),
    .in_valid(in_valid),.in_ready(in_ready),.in_op(in_op),
    .in_a(in_a),.in_b(in_b),.in_error(in_error),
    .out_valid(out_valid),.out_ready(out_ready),.out_data(out_data),.out_error(out_error));
  task reset_outputs;
    begin
      if ({in_ready,out_valid,out_data,out_error}!==0) $fatal(1,"SCALAR_RESET");
    end
  endtask
  always @(posedge clk or negedge clk) if (!rst_n) reset_outputs();
  initial begin
    rst_n=0; #1; reset_outputs();
    @(negedge clk); rst_n=1; #1;
    if (!$value$plusargs("vectors=%s",filename)) $fatal(1,"NO_VECTORS");
    fd=$fopen(filename,"r"); if (!fd) $fatal(1,"OPEN_VECTORS");
    rc=$fscanf(fd,"%d %h %h %d %h %d\n",
      operation,in_a,in_b,error_value,expected,expected_error);
    while (rc==6) begin
      @(negedge clk);
      if (in_ready!==1 || out_valid!==0) $fatal(1,"SCALAR_NOT_READY");
      in_op=operation; in_error=error_value; in_valid=1; out_ready=0;
      @(posedge clk); #1;
      if (in_ready!==0 || out_valid!==0) $fatal(1,"SCALAR_ACCEPT");
      @(negedge clk); in_valid=0; cycles=0;
      while (out_valid===0 && cycles<100) begin
        @(posedge clk); #1; cycles=cycles+1;
      end
      if (out_valid!==1 || out_data!==expected || out_error!==expected_error[0])
        $fatal(1,"SCALAR_COMPARE case=%0d op=%0d a=%h b=%h got=%h expected=%h error=%b expected_error=%b cycles=%0d",
          count,operation,in_a,in_b,out_data,expected,out_error,expected_error[0],cycles);
      for (stall=0;stall<2;stall=stall+1) begin
        @(posedge clk); #1;
        if (out_valid!==1 || out_data!==expected || out_error!==expected_error[0] ||
            in_ready!==0) $fatal(1,"SCALAR_STALL");
      end
      @(negedge clk); out_ready=1;
      @(posedge clk); #1;
      if (out_valid!==0 || in_ready!==1) $fatal(1,"SCALAR_RETIRE");
      @(negedge clk); out_ready=0; count=count+1;
      rc=$fscanf(fd,"%d %h %h %d %h %d\n",
        operation,in_a,in_b,error_value,expected,expected_error);
    end
    if (rc!=0 && rc!=-1) $fatal(1,"MALFORMED_VECTORS");
    if (count==0) $fatal(1,"NO_COMPARISONS");
    $fclose(fd);
    $display("SUMMARY scalar_cases=%0d stalled_outputs=%0d",count,count);
    $finish;
  end
  initial begin repeat (500000) @(posedge clk); $fatal(1,"CYCLE_BOUND"); end
endmodule
"""


def scalar_vectors():
    functions = (ref.add, ref.subtract, ref.multiply, ref.divide,
                 lambda a, b: ref.sqrt32(a))
    directed = [0, 0x80000000, 1, 0x80000001, 0x007FFFFF, 0x00800000,
                0x3F800000, 0xBF800000, 0x3F800001, 0x3F7FFFFF, 0x40000000,
                0x7F7FFFFF, 0xFF7FFFFF, 0x7F800000, 0x7FC00001]
    vectors = []
    for operation in range(5):
        pairs = [(a, b) for a in directed for b in directed]
        for seed in (17, 89, 203):
            rng = random.Random(seed + operation * 1000)
            pairs += [(rng.getrandbits(32), rng.getrandbits(32)) for _ in range(256)]
        for a, b in pairs:
            try:
                expected = functions[operation](a, b)
                error = 0
            except ref.ArithmeticFault:
                expected, error = 0, 1
            vectors.append((operation, a, b, 0, expected, error))
    for operation in range(8):
        vectors.append((operation, 0x3F800000, 0x40000000, 1, 0, 1))
    return vectors


def run_scalar(run):
    vectors = scalar_vectors()
    vector_file = run.path / "scalar-vectors.txt"
    with vector_file.open("x") as output:
        for operation, a, b, injected_error, expected, error in vectors:
            output.write(f"{operation} {a:08x} {b:08x} {injected_error} "
                         f"{expected:08x} {error}\n")
    bench = run.path / "scalar_tb.sv"
    bench.write_text(SCALAR_BENCH)
    binary = run.path / "scalar.vvp"
    sources = [f"rtl/anvil_qn1_{name}.sv" for name in
               ("00_pkg", "fp32_mul", "fp32_add", "fp32_div", "fp32_sqrt", "scalar")]
    run.execute(["iverilog", "-g2012", "-Wall", "-s", "scalar_tb", "-o",
                 relative(binary), *sources, relative(bench)], "scalar-compile")
    text = run.execute(["vvp", relative(binary), f"+vectors={relative(vector_file)}"],
                       "scalar-simulation", timeout=600)
    summary = f"SUMMARY scalar_cases={len(vectors)} stalled_outputs={len(vectors)}"
    if text.count(summary) != 1:
        raise AssertionError("scalar comparison count missing")
    return {"scalar_cases": len(vectors), "seeds": [17, 89, 203],
            "operations": ["add", "subtract", "multiply", "divide", "sqrt"]}
