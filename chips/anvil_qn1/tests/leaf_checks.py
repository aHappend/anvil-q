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


TENSOR_BENCH = r"""
module tensor_tb;
  reg clk=0,rst_n,flush=0,in_valid=0,in_w4=0,out_ready=0;
  always #5 clk=~clk;
  wire in_ready,out_valid,out_error;
  reg [1023:0] q=0,z=0;
  reg [4095:0] scale_bf16=0,activation_bf16=0,weight_bf16=0;
  reg [255:0] lane_mask=0;
  reg [31:0] in_tag=0;
  wire [31:0] out_sum,out_tag;
  integer fd,rc,format_value,error_value,accepted=0,retired=0,cycles=0,enabled=0;
  integer front=0,tail=0,queued=0,birth[0:2047],blocked=0;
  reg [31:0] expected_input,expected[0:2047],tags[0:2047];
  reg errors[0:2047];
  reg [64:0] held_payload;
  reg holding=0,was_enabled;
  reg [4095:0] filename;
  anvil_qn1_tensor_array dut(.clk(clk),.rst_n(rst_n),.flush(flush),
    .in_valid(in_valid),.in_w4(in_w4),.in_ready(in_ready),.q(q),.z(z),
    .scale_bf16(scale_bf16),.activation_bf16(activation_bf16),.weight_bf16(weight_bf16),
    .lane_mask(lane_mask),.in_tag(in_tag),.out_valid(out_valid),
    .out_sum(out_sum),.out_tag(out_tag),.out_error(out_error),.out_ready(out_ready));
  task reset_outputs;
    begin
      if ({in_ready,out_valid,out_sum,out_tag,out_error}!==0) $fatal(1,"TENSOR_RESET");
    end
  endtask
  task next_vector;
    begin
      rc=$fscanf(fd,"%d %h %h %h %h %h %h %h %h %d\n",
        format_value,lane_mask,q,z,scale_bf16,activation_bf16,weight_bf16,
        in_tag,expected_input,error_value);
      in_valid=(rc==10); in_w4=format_value;
      if (rc!=10 && rc!=0 && rc!=-1) $fatal(1,"MALFORMED_TENSOR_VECTORS");
    end
  endtask
  always @(posedge clk or negedge clk) if (!rst_n) reset_outputs();
  initial begin
    rst_n=0; #1;reset_outputs();
    if (!$value$plusargs("vectors=%s",filename)) $fatal(1,"NO_VECTORS");
    fd=$fopen(filename,"r");if (!fd) $fatal(1,"OPEN_VECTORS");
    @(negedge clk);rst_n=1;next_vector();
    while (in_valid || queued>0 || accepted==0) begin
      out_ready=(cycles%67<49);
      @(posedge clk);
      was_enabled=!out_valid || out_ready;
      if (holding && (out_valid!==1 || {out_error,out_tag,out_sum}!==held_payload))
        $fatal(1,"TENSOR_GLOBAL_STALL");
      holding=out_valid && !out_ready;held_payload={out_error,out_tag,out_sum};
      if (holding) blocked=blocked+1;
      if (out_valid && out_ready) begin
        if (queued==0 || out_tag!==tags[front] || out_error!==errors[front] ||
            (!errors[front] && out_sum!==expected[front]))
          $fatal(1,"TENSOR_COMPARE record=%0d tag=%h expected_tag=%h got=%h expected=%h error=%b expected_error=%b",
            retired,out_tag,tags[front],out_sum,expected[front],out_error,errors[front]);
        if ((^{out_sum,out_tag,out_error})===1'bx) $fatal(1,"ACTIVE_TENSOR_XZ");
        front=front+1;queued=queued-1;retired=retired+1;
      end
      if (was_enabled) enabled=enabled+1;
      if (in_valid && in_ready) begin
        if (tail>=2048) $fatal(1,"SCOREBOARD_BOUND");
        birth[tail]=enabled;expected[tail]=expected_input;tags[tail]=in_tag;
        errors[tail]=error_value;tail=tail+1;queued=queued+1;accepted=accepted+1;
      end
      #1;
      if (queued>0 && enabled-birth[front]>=48) begin
        if (out_valid!==1 || out_tag!==tags[front])
          $fatal(1,"TENSOR_LATENCY expected=48 got=%0d",enabled-birth[front]);
      end else if (out_valid!==0) $fatal(1,"EARLY_TENSOR_OUTPUT");
      cycles=cycles+1;
      @(negedge clk);
      if (was_enabled) next_vector();
    end
    if (accepted!=retired || blocked==0) $fatal(1,"TENSOR_CONSERVATION_OR_STALL_COVERAGE");
    $fclose(fd);
    in_valid=0;out_ready=0;
    #2;rst_n=0;#1;reset_outputs();
    @(negedge clk);rst_n=1;in_valid=1;
    repeat (10) @(negedge clk);
    #2;rst_n=0;in_valid=0;#1;reset_outputs();
    @(negedge clk);rst_n=1;in_valid=1;
    repeat (10) @(negedge clk);
    flush=1;in_valid=0;#1;reset_outputs();
    @(negedge clk);flush=0;out_ready=1;
    repeat (60) begin @(posedge clk);#1;if (out_valid!==0) $fatal(1,"FLUSH_TENSOR_LEAK");end
    $display("SUMMARY tensor_cases=%0d latency=48 blocked_cycles=%0d reset_during_work=1 flush_during_work=1",
      retired,blocked);
    $finish;
  end
  initial begin repeat (500000) @(posedge clk);$fatal(1,"CYCLE_BOUND");end
endmodule
"""


def tensor_vectors(full=True):
    vectors = []
    for seed in ([17, 89, 203] if full else [17]):
        rng = random.Random(seed)
        for index in range(256 if full else 12):
            w4 = index & 1
            q = [rng.randrange(16) for _ in range(256)]
            z = [rng.randrange(16) for _ in range(256)]
            scales = [ref.encode(Fraction(rng.randrange(1, 129), 128), 16)
                      for _ in range(256)]
            weights = [ref.encode(Fraction(rng.randrange(-64, 65), 16), 16)
                       for _ in range(256)]
            activations = [ref.encode(Fraction(rng.randrange(-256, 257), 32), 16)
                           for _ in range(256)]
            mask = ((1 << 256) - 1) if index % 4 else (1 << index)
            if index % 8 == 2:
                mask = (1 << (index % 255 + 1)) - 1
            if index % 16 == 3:
                mask = 0
            if index % 16 == 4:
                activations = [1 + lane % 127 for lane in range(256)]
                weights = [0x3F80] * 256
            if index % 16 == 5:
                activations = [0x3F80 if lane & 1 else 0xBF80 for lane in range(256)]
                q, z, scales = [9] * 256, [8] * 256, [0x3F80] * 256
            if index % 16 == 6:
                activations[0], weights[0], scales[0] = 0x7F7F, 0x4000, 0x7F7F
            if index % 16 == 7:
                mask |= 1
                activations[0] = 0x7F80
            if index % 16 == 8:
                mask &= ~1
                activations[0], scales[0], weights[0] = 0x7FC1, 0xBF80, 0xFF80
            if index % 16 == 9:
                mask |= 1
                scales[0] = 0xBF80
            try:
                expected = ref.tensor(q, z, scales, activations, weights, mask, w4)
                error = 0
            except ref.ArithmeticFault:
                expected, error = 0, 1
            vectors.append((w4, mask, q, z, scales, activations, weights,
                            len(vectors) + 1, expected, error))
        if full:
            for lane in range(256):
                vectors.append((lane & 1, 1 << lane, [9] * 256, [8] * 256,
                                [0x3F80] * 256, [0x3F80] * 256, [0x3F80] * 256,
                                len(vectors) + 1, 0x3F800000, 0))
    return vectors


def run_tensor(run, simulator="icarus", full=False):
    if simulator == "verilator":
        return run_tensor_cpp(run, full)
    vectors = tensor_vectors(full)
    vector_file = run.path / "tensor-vectors.txt"
    with vector_file.open("x") as output:
        for w4, mask, q, z, scales, activations, weights, tag, expected, error in vectors:
            output.write(f"{w4} {mask:x} {ref.pack(q,4):x} {ref.pack(z,4):x} "
                         f"{ref.pack(scales,16):x} {ref.pack(activations,16):x} "
                         f"{ref.pack(weights,16):x} {tag:x} {expected:x} {error}\n")
    bench = run.path / "tensor_tb.sv"
    bench.write_text(TENSOR_BENCH)
    sources = [f"rtl/anvil_qn1_{name}.sv" for name in
               ("00_pkg", "fp32_mul", "fp32_add", "tensor_array")]
    if simulator == "icarus":
        binary = run.path / "tensor.vvp"
        run.execute(["iverilog", "-g2012", "-Wall", "-s", "tensor_tb", "-o",
                     relative(binary), *sources, relative(bench)], "tensor-compile")
        text = run.execute(["vvp", relative(binary), f"+vectors={relative(vector_file)}"],
                           "tensor-simulation", timeout=600)
    else:
        objects = run.path / "obj-tensor"
        run.execute(["verilator", "--binary", "--timing", "-Wno-fatal", "-j", "2",
                     "--top-module", "tensor_tb", "--Mdir", relative(objects),
                     "-o", "simulate", *sources, relative(bench)], "tensor-compile")
        text = run.execute([relative(objects / "simulate"), f"+vectors={relative(vector_file)}"],
                           "tensor-simulation")
        for pattern in ("*.o", "*.a", "*.gch"):
            for file in objects.glob(pattern):
                file.unlink()
    summary = f"SUMMARY tensor_cases={len(vectors)} latency=48"
    if text.count(summary) != 1:
        raise AssertionError("tensor comparisons missing")
    return {"tensor_cases": len(vectors), "simulator": simulator,
            "seeds": [17, 89, 203] if full else [17], "raw_summary": text[-1000:]}


TENSOR_DRIVER = r"""
#include "Vanvil_qn1_tensor_array.h"
#include "verilated.h"
#include <array>
#include <cstdint>
#include <deque>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>

template <size_t N> std::array<uint32_t,N> words(const std::string& hex) {
    std::array<uint32_t,N> result{};
    size_t end=hex.size(), index=0;
    while (end) {
        if (index>=N) throw std::runtime_error("wide vector overflow");
        size_t begin=end>8 ? end-8 : 0;
        result[index++]=std::stoul(hex.substr(begin,end-begin),nullptr,16);
        end=begin;
    }
    return result;
}
template <size_t N, class Port> void drive(Port& port,const std::array<uint32_t,N>& value) {
    for (size_t i=0;i<N;++i) port[i]=value[i];
}
struct Vector {
    unsigned w4,error,tag,result;
    std::array<uint32_t,8> mask;
    std::array<uint32_t,32> q,z;
    std::array<uint32_t,128> scale,activation,weight;
};
struct Pending {Vector vector; unsigned birth;};
int main(int argc,char** argv) {
    try {
        Verilated::commandArgs(argc,argv);
        if (argc!=2) throw std::runtime_error("vector filename required");
        std::ifstream input(argv[1]);
        if (!input) throw std::runtime_error("cannot open vectors");
        std::deque<Vector> vectors;
        unsigned w4,error;std::string mask,q,z,scale,activation,weight,tag,result;
        while (input>>w4>>mask>>q>>z>>scale>>activation>>weight>>tag>>result>>error)
            vectors.push_back({w4,error,unsigned(std::stoul(tag,nullptr,16)),
              unsigned(std::stoul(result,nullptr,16)),words<8>(mask),words<32>(q),
              words<32>(z),words<128>(scale),words<128>(activation),words<128>(weight)});
        if (!input.eof() || vectors.empty()) throw std::runtime_error("malformed or empty vectors");
        const auto count=vectors.size();
        Vanvil_qn1_tensor_array dut;
        dut.clk=0;dut.rst_n=0;dut.flush=0;dut.in_valid=0;dut.out_ready=0;dut.eval();
        if (dut.in_ready || dut.out_valid || dut.out_error || dut.out_sum || dut.out_tag)
            throw std::runtime_error("reset outputs");
        dut.clk=1;dut.eval();
        dut.clk=0;dut.rst_n=1;dut.eval();
        std::deque<Pending> queue;
        unsigned enabled=0,retired=0,blocked=0,cycles=0;
        bool holding=false;uint32_t held_sum=0,held_tag=0;unsigned held_error=0;
        while (!vectors.empty() || !queue.empty()) {
            if (cycles>=500000) throw std::runtime_error("cycle bound");
            dut.clk=0;dut.out_ready=cycles%67<49;dut.in_valid=!vectors.empty();
            if (!vectors.empty()) {
                const auto& v=vectors.front();
                dut.in_w4=v.w4;dut.in_tag=v.tag;drive(dut.q,v.q);drive(dut.z,v.z);
                drive(dut.scale_bf16,v.scale);drive(dut.activation_bf16,v.activation);
                drive(dut.weight_bf16,v.weight);drive(dut.lane_mask,v.mask);
            }
            dut.eval();
            if (holding && (!dut.out_valid || dut.out_sum!=held_sum ||
                            dut.out_tag!=held_tag || dut.out_error!=held_error))
                throw std::runtime_error("global output stall");
            holding=dut.out_valid && !dut.out_ready;
            held_sum=dut.out_sum;held_tag=dut.out_tag;held_error=dut.out_error;
            if (holding) ++blocked;
            const bool ce=!dut.out_valid || dut.out_ready;
            if (dut.out_valid && dut.out_ready) {
                if (queue.empty()) throw std::runtime_error("unsolicited tensor result");
                const auto& v=queue.front().vector;
                if (dut.out_tag!=v.tag || dut.out_error!=v.error ||
                    (!v.error && dut.out_sum!=v.result)) {
                    std::cerr<<"TENSOR_COMPARE record="<<retired<<" tag="<<dut.out_tag
                      <<" expected_tag="<<v.tag<<" got="<<std::hex<<dut.out_sum
                      <<" expected="<<v.result<<std::dec<<" error="<<unsigned(dut.out_error)
                      <<" expected_error="<<v.error<<"\n";
                    return 1;
                }
                queue.pop_front();++retired;
            }
            if (ce) ++enabled;
            if (dut.in_valid && dut.in_ready) {
                queue.push_back({vectors.front(),enabled});vectors.pop_front();
            }
            dut.clk=1;dut.eval();
            bool due=!queue.empty() && enabled-queue.front().birth>=48;
            if (bool(dut.out_valid)!=due || (due && dut.out_tag!=queue.front().vector.tag))
                throw std::runtime_error("48 enabled-edge latency");
            ++cycles;
        }
        if (retired!=count || !blocked) throw std::runtime_error("coverage/conservation");
        dut.final();
        std::cout<<"SUMMARY tensor_cases="<<retired<<" latency=48 blocked_cycles="
                 <<blocked<<" cycles="<<cycles<<"\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr<<"FAIL "<<error.what()<<"\n";return 1;
    }
}
"""


def run_tensor_cpp(run, full=False):
    vectors = tensor_vectors(full)
    vector_file = run.path / "tensor-vectors.txt"
    with vector_file.open("x") as output:
        for w4, mask, q, z, scales, activations, weights, tag, expected, error in vectors:
            output.write(f"{w4} {mask:x} {ref.pack(q,4):x} {ref.pack(z,4):x} "
                         f"{ref.pack(scales,16):x} {ref.pack(activations,16):x} "
                         f"{ref.pack(weights,16):x} {tag:x} {expected:x} {error}\n")
    driver = run.path / "tensor_driver.cpp"
    driver.write_text(TENSOR_DRIVER)
    objects = run.path / "obj-tensor"
    sources = [f"rtl/anvil_qn1_{name}.sv" for name in
               ("00_pkg", "fp32_mul", "fp32_add", "tensor_array")]
    run.execute(["verilator", "--cc", "--exe", "--build", "-Wno-fatal", "-j", "2",
                 "--top-module", "anvil_qn1_tensor_array", "--Mdir", relative(objects),
                 "-o", "simulate", *sources, "../tensor_driver.cpp"], "tensor-cpp-compile")
    text = run.execute([relative(objects / "simulate"), relative(vector_file)],
                       "tensor-cpp-simulation")
    for pattern in ("*.o", "*.a", "*.gch"):
        for file in objects.glob(pattern):
            file.unlink()
    if text.count(f"SUMMARY tensor_cases={len(vectors)} latency=48") != 1:
        raise AssertionError("C++ tensor comparison count")
    return {"tensor_cases": len(vectors), "simulator": "verilator-cpp",
            "raw_summary": text[-1000:]}


def run_elementary(run):
    import math
    records = {}
    for kind in ("exp", "silu"):
        if kind == "exp":
            values = [ref.encode(Fraction(-16 * index, 255)) for index in range(256)]
            values += [0, 0x80000000, 0xC1800001, 0xC17FFFFF, 0x7F800000,
                       0x7FC00001, 0x3F800000]
            for m in range(1, 24):
                boundary = ref.encode(-m * ref.decode(0x3F317218))
                values.extend([boundary - 1, boundary, boundary + 1])
            function = ref.exp32
        else:
            values = [ref.encode(Fraction(-32 * index, 127) + 16, 16) << 16
                      for index in range(128)]
            values += [0, 0x80000000, 0x00010000, 0x80010000, 0x00800000, 0x80800000,
                       0x7F800000, 0xFF800000, 0x7FC00001]
            function = ref.silu32
        vector_file = run.path / f"{kind}-vectors.txt"
        maximum_analytic_error = 0
        with vector_file.open("x") as output:
            for value in values:
                try:
                    expected, error = function(value), 0
                    if kind == "silu":
                        expected = ref.bf16(expected) << 16
                    real = float(ref.decode(value))
                    if kind == "exp":
                        difference = abs(float(ref.decode(expected)) - math.exp(real))
                        if difference > 3e-5:
                            raise AssertionError(f"E analytic error {difference} at {real}")
                    else:
                        exact = real / (1 + math.exp(-real))
                        rounded = float(ref.decode(ref.bf16(expected), 16))
                        difference = abs(rounded - exact)
                        if difference > 0.02 * max(1, abs(exact)):
                            raise AssertionError(f"SiLU analytic error {difference} at {real}")
                    maximum_analytic_error = max(maximum_analytic_error, difference)
                except ref.ArithmeticFault:
                    expected, error = 0, 1
                output.write(f"0 {value:08x} 00000000 0 {expected:08x} {error}\n")
        original = r"""anvil_qn1_scalar dut(.clk(clk),.rst_n(rst_n),.flush(flush),
    .in_valid(in_valid),.in_ready(in_ready),.in_op(in_op),
    .in_a(in_a),.in_b(in_b),.in_error(in_error),
    .out_valid(out_valid),.out_ready(out_ready),.out_data(out_data),.out_error(out_error));"""
        replacement = f"""anvil_qn1_{kind} dut(.clk(clk),.rst_n(rst_n),.flush(flush),
    .in_valid(in_valid),.in_ready(in_ready),.in_data(in_a),
    .out_valid(out_valid),.out_ready(out_ready),.out_data(out_data),.out_error(out_error));"""
        if kind == "silu":
            replacement = """wire [15:0] silu_output;
  assign out_data={silu_output,16'd0};
  anvil_qn1_silu dut(.clk(clk),.rst_n(rst_n),.flush(flush),
    .in_valid(in_valid),.in_ready(in_ready),.in_data(in_a[31:16]),
    .out_valid(out_valid),.out_ready(out_ready),.out_data(silu_output),.out_error(out_error));"""
        if SCALAR_BENCH.count(original) != 1:
            raise AssertionError("elementary transactor adaptation failed")
        bench = run.path / f"{kind}_tb.sv"
        bench.write_text(SCALAR_BENCH.replace(original, replacement)
                         .replace("cycles<100", "cycles<1000")
                         .replace('if (in_ready!==0 || out_valid!==0) $fatal(1,"SCALAR_ACCEPT");',
                                  'if (in_ready!==0) $fatal(1,"SCALAR_ACCEPT");'))
        binary = run.path / f"{kind}.vvp"
        sources = [f"rtl/anvil_qn1_{name}.sv" for name in
                   ("00_pkg", "fp32_mul", "fp32_add", "fp32_div", "fp32_sqrt",
                    "scalar", "exp", "silu")]
        run.execute(["iverilog", "-g2012", "-Wall", "-s", "scalar_tb", "-o",
                     relative(binary), *sources, relative(bench)], f"{kind}-compile")
        text = run.execute(["vvp", relative(binary), f"+vectors={relative(vector_file)}"],
                           f"{kind}-simulation", timeout=600)
        if text.count(f"SUMMARY scalar_cases={len(values)} stalled_outputs={len(values)}") != 1:
            raise AssertionError(f"{kind} comparison coverage")
        records[kind] = {"compared_values": len(values),
                         "maximum_analytic_absolute_error": maximum_analytic_error}
    return records
