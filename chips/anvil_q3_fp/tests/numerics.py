"""Leaf requirement checks: exhaustive formats, exact IEEE arithmetic and dot8."""

import random

from execution import icarus
from ieee import binary, canonical, classify, convert, dot, float_bits, sqrt


PKG = "rtl/anvil_q3_fp_00_pkg.sv"
SPECIALS = [
    0, 0x80000000, 1, 2, 0x007fffff, 0x00800000, 0x00800001,
    0x3f800000, 0xbf800000, 0x3f000000, 0x3f800001, 0x3fffffff,
    0x33800000, 0x33000000, 0x7f7fffff, 0xff7fffff,
    0x7f800000, 0xff800000, 0x7fc00000, 0x7f800001, 0xff800001,
]


def conversions(evidence):
    vectors = []
    for dtype, fmt in enumerate(("bf16", "fp16")):
        for value in range(65536):
            wide = convert(value, fmt, "fp32", preserve_nan=True)[0]
            narrow, flags = convert(wide, "fp32", fmt)
            vectors.append(f"{dtype:x} {value:04x} {wide:08x} {narrow:04x} {flags:02x}\n")
    tb = """
module tb;
  import anvil_q3_fp_pkg::*;
  reg dtype;
  reg [15:0] source, expected_narrow;
  reg [31:0] expected_wide;
  reg [4:0] expected_flags;
  reg [20:0] narrowed;
  integer file_handle, rc, count;
  initial begin
    count=0;
    file_handle=$fopen("vectors.txt","r");
    if (!file_handle) $fatal(1,"vector open");
    while (!$feof(file_handle)) begin
      rc=$fscanf(file_handle,"%h %h %h %h %h\\n",
        dtype,source,expected_wide,expected_narrow,expected_flags);
      if (rc!=5) $fatal(1,"malformed conversion vector");
      if (widen16(source,dtype)!==expected_wide)
        $fatal(1,"WIDEN dtype=%d source=%h expected=%h got=%h",
          dtype,source,expected_wide,widen16(source,dtype));
      narrowed=narrow16(expected_wide,dtype);
      if (narrowed!=={expected_flags,expected_narrow})
        $fatal(1,"NARROW dtype=%d source=%h expected=%h/%h got=%h",
          dtype,source,expected_flags,expected_narrow,narrowed);
      count=count+1;
    end
    if (count!=131072) $fatal(1,"conversion count %d",count);
    $display("COMPARED conversions=%0d",count);
    $finish;
  end
endmodule
"""
    icarus(evidence, "conversions", tb, [PKG], {"vectors.txt": "".join(vectors)})
    return {"widen_narrow_encodings": 131072}


def operation_vectors(seed=17, count=4096):
    rng = random.Random(seed)
    pairs = [(a, b) for a in SPECIALS for b in SPECIALS]
    for fmt in ("bf16", "fp16"):
        pairs += [(convert(rng.randrange(65536), fmt, "fp32", True)[0],
                   convert(rng.randrange(65536), fmt, "fp32", True)[0]) for _ in range(count)]
    pairs += [(rng.getrandbits(32), rng.getrandbits(32)) for _ in range(count)]
    return pairs


def primitives(evidence, seed=17, count=4096):
    pairs = operation_vectors(seed, count)
    results = {}
    for operation in ("add", "mul"):
        text = "".join(f"{a:08x} {b:08x} {value:08x} {flags:02x}\n"
                       for a, b in pairs for value, flags in [binary(operation, a, b)])
        tb = PRIMITIVE_TB.replace("@MODULE@", f"anvil_q3_fp_{operation}")
        icarus(evidence, operation, tb,
               [PKG, f"rtl/anvil_q3_fp_{operation}.sv"], {"vectors.txt": text})
        results[operation] = len(pairs)
    return results


PRIMITIVE_TB = """
module tb;
  reg clk=0;
  always #5 clk=~clk;
  reg rst_n,flush=0,in_valid=0,out_ready=0;
  reg [31:0] in_a=0,in_b=0;
  wire in_ready,out_valid;
  wire [31:0] out_data;
  wire [4:0] out_flags;
  @MODULE@ dut(.*);
  reg [31:0] a[0:20000],b[0:20000],expected[0:20000];
  reg [4:0] flags[0:20000];
  integer fd,rc,n=0,sent=0,received=0,cycle=0,accepted_cycle[0:20000];
  integer stalls=0,simultaneous=0;
  reg held=0;
  reg [36:0] held_payload;
  task reset_check;
    begin
      if ({in_ready,out_valid,out_data,out_flags}!==39'd0)
        $fatal(1,"RESET nonzero/X public outputs");
    end
  endtask
  initial begin
    rst_n=0;
    #0; reset_check;
    #1; reset_check;
    fd=$fopen("vectors.txt","r");
    if (!fd) $fatal(1,"vector open");
    while (!$feof(fd)) begin
      rc=$fscanf(fd,"%h %h %h %h\\n",a[n],b[n],expected[n],flags[n]);
      if (rc!=4) $fatal(1,"malformed arithmetic vector");
      n=n+1;
    end
    @(negedge clk); rst_n=1;
  end
  always @(posedge clk) begin
    if (!rst_n) reset_check;
    else begin
      if (held && {out_flags,out_data}!==held_payload)
        $fatal(1,"STALL payload changed index=%0d",received);
      if (held && out_valid!==1'b1) $fatal(1,"STALL valid dropped");
      held=out_valid && !out_ready;
      held_payload={out_flags,out_data};
      if (out_valid && !out_ready) stalls=stalls+1;
      if (out_valid && out_ready) begin
        if (received>=sent || {out_flags,out_data}!=={flags[received],expected[received]})
          $fatal(1,"IEEE index=%0d a=%h b=%h expected=%h/%h got=%h/%h",
            received,a[received],b[received],flags[received],expected[received],out_flags,out_data);
        if (received<32 && cycle-accepted_cycle[received]!=3)
          $fatal(1,"LATENCY expected earliest handshake E3 got=%0d",cycle-accepted_cycle[received]);
        received=received+1;
      end
      if (in_valid && in_ready) begin
        accepted_cycle[sent]=cycle; sent=sent+1;
        if (out_valid && out_ready) simultaneous=simultaneous+1;
      end
      cycle=cycle+1;
      if (received==n) begin
        if (stalls==0 || simultaneous==0) $fatal(1,"missing stall/replace coverage");
        $display("COMPARED operations=%0d stalls=%0d simultaneous=%0d",received,stalls,simultaneous);
        $finish;
      end
      if (cycle>100000) $fatal(1,"PROGRESS bound");
    end
  end
  always @(negedge clk) begin
    if (!rst_n) reset_check;
    else begin
      out_ready=cycle<40 || cycle%11<7;
      in_valid=sent<n;
      if (in_valid) begin in_a=a[sent]; in_b=b[sent]; end
    end
  end
endmodule
"""


def iterative(evidence, seed=17, count=4096):
    pairs = operation_vectors(seed, count)
    results = {}
    for operation in ("div", "sqrt"):
        text = "".join(f"{a:08x} {b:08x} {value:08x} {flags:02x}\n"
                       for a, b in pairs for value, flags in
                       [binary("div", a, b) if operation == "div" else sqrt(a)])
        module = "anvil_q3_fp_divider" if operation == "div" else "anvil_q3_fp_sqrt"
        connection = (".numerator(a),.denominator(b),.quotient(value)" if operation == "div"
                      else ".radicand(a),.value(value)")
        tb = ITERATIVE_TB.replace("@MODULE@", module).replace("@CONNECTION@", connection)
        icarus(evidence, operation, tb, [PKG, f"rtl/{module}.sv"], {"vectors.txt": text})
        results[operation] = len(pairs)
    return results


def dots(evidence, seed=17, count=256):
    rng = random.Random(seed)
    vectors = []
    for dtype, fmt in enumerate(("bf16", "fp16")):
        for awq in (0, 1):
            for index in range(count):
                activations = [rng.randrange(65536) for _ in range(8)]
                weights = [rng.randrange(65536) for _ in range(8)]
                scales = [rng.randrange(0x7c00) for _ in range(8)]
                q = [rng.randrange(16) for _ in range(8)]
                z = [rng.randrange(16) for _ in range(8)]
                mask = (0, 1, 0x80, 0x55, 0xaa, 0xff)[index % 6] if index < 36 else rng.randrange(256)
                value, flags = dot(activations, weights, mask, fmt,
                                   q if awq else None, z, scales)
                packed = lambda values, width: sum(v << (width * i) for i, v in enumerate(values))
                vectors.append(f"{dtype:x} {awq:x} {mask:02x} "
                               f"{packed(activations,16):032x} {packed(weights,16):032x} "
                               f"{packed(q,4):08x} {packed(z,4):08x} {packed(scales,16):032x} "
                               f"{value:08x} {flags:02x}\n")
    icarus(evidence, "dot8", DOT_TB, [PKG, "rtl/anvil_q3_fp_mul.sv",
           "rtl/anvil_q3_fp_add.sv", "rtl/anvil_q3_fp_dot8.sv"],
           {"vectors.txt": "".join(vectors)})
    return {"dot8_per_format_mode": count, "dot8_total": len(vectors)}


DOT_TB = """
module tb;
  reg clk=0;
  always #5 clk=~clk;
  reg rst_n,flush=0,in_valid=0,out_ready=0,in_fp16=0,in_awq=0;
  reg [127:0] weight16=0,activation16=0,scale_f16=0;
  reg [31:0] q_nibbles=0,z_nibbles=0;
  reg [7:0] lane_mask=0;
  wire in_ready,out_valid,out_error;
  wire [31:0] out_dot;
  wire [4:0] out_flags;
  anvil_q3_fp_dot8 dut(.*);
  reg dtype[0:4095],awq[0:4095];
  reg [7:0] mask[0:4095];
  reg [127:0] act[0:4095],weight[0:4095],scale[0:4095];
  reg [31:0] q[0:4095],z[0:4095],expected[0:4095];
  reg [4:0] flags[0:4095];
  integer fd,rc,n=0,sent=0,received=0,cycle=0,stalls=0,simultaneous=0;
  integer accepted_cycle[0:4095];
  reg held=0;
  reg [37:0] held_payload;
  task reset_check;
    begin
      if ({in_ready,out_valid,out_error,out_dot,out_flags}!==40'd0)
        $fatal(1,"RESET nonzero/X dot outputs");
    end
  endtask
  initial begin
    rst_n=0;
    #0; reset_check;
    #1; reset_check;
    fd=$fopen("vectors.txt","r");
    if (!fd) $fatal(1,"vector open");
    while (!$feof(fd)) begin
      rc=$fscanf(fd,"%h %h %h %h %h %h %h %h %h %h\\n",
        dtype[n],awq[n],mask[n],act[n],weight[n],q[n],z[n],scale[n],expected[n],flags[n]);
      if (rc!=10) $fatal(1,"malformed dot vector");
      n=n+1;
    end
    @(negedge clk); rst_n=1;
  end
  always @(posedge clk) begin
    if (!rst_n) reset_check;
    else begin
      if (held && ({out_error,out_flags,out_dot}!==held_payload || out_valid!==1'b1))
        $fatal(1,"STALL dot payload changed index=%0d",received);
      held=out_valid && !out_ready;
      held_payload={out_error,out_flags,out_dot};
      if (held) stalls=stalls+1;
      if (out_valid && out_ready) begin
        if (received>=sent || {out_error,out_flags,out_dot}!=={1'b0,flags[received],expected[received]})
          $fatal(1,"DOT index=%0d fp16=%b awq=%b mask=%h expected=%h/%h got=%b/%h/%h",
            received,dtype[received],awq[received],mask[received],
            flags[received],expected[received],out_error,out_flags,out_dot);
        if (received<32 && cycle-accepted_cycle[received]!=12)
          $fatal(1,"LATENCY native dot expected E12 got=%0d",cycle-accepted_cycle[received]);
        received=received+1;
      end
      if (in_valid && in_ready) begin
        accepted_cycle[sent]=cycle; sent=sent+1;
        if (out_valid && out_ready) simultaneous=simultaneous+1;
      end
      cycle=cycle+1;
      if (received==n) begin
        if (stalls==0 || simultaneous==0) $fatal(1,"missing stall/replace coverage");
        $display("COMPARED dots=%0d stalls=%0d simultaneous=%0d",received,stalls,simultaneous);
        $finish;
      end
      if (cycle>100000) $fatal(1,"PROGRESS bound");
    end
  end
  always @(negedge clk) begin
    if (!rst_n) reset_check;
    else begin
      out_ready=cycle<64 || cycle%11<7;
      in_valid=sent<n;
      if (in_valid) begin
        in_fp16=dtype[sent]; in_awq=awq[sent]; lane_mask=mask[sent];
        activation16=act[sent]; weight16=weight[sent]; scale_f16=scale[sent];
        q_nibbles=q[sent]; z_nibbles=z[sent];
      end
    end
  end
endmodule
"""


ITERATIVE_TB = """
module tb;
  reg clk=0;
  always #5 clk=~clk;
  reg rst_n,flush=0,start=0;
  reg [31:0] a=0,b=0;
  wire ready,done,error;
  wire [31:0] value;
  wire [4:0] flags;
  @MODULE@ dut(.clk(clk),.rst_n(rst_n),.flush(flush),.start(start),
    @CONNECTION@,.ready(ready),.done(done),.error(error),.flags(flags));
  integer fd,rc,n=0,latency;
  reg [31:0] expected;
  reg [4:0] expected_flags;
  task reset_check;
    begin
      if ({ready,done,error,value,flags}!==40'd0)
        $fatal(1,"RESET nonzero/X public outputs");
    end
  endtask
  always @(posedge clk or negedge clk) if (!rst_n) reset_check;
  initial begin
    rst_n=0;
    #0; reset_check;
    #1; reset_check;
    @(negedge clk); rst_n=1;
    fd=$fopen("vectors.txt","r");
    if (!fd) $fatal(1,"vector open");
    while (!$feof(fd)) begin
      @(negedge clk);
      while (ready!==1'b1) @(negedge clk);
      rc=$fscanf(fd,"%h %h %h %h\\n",a,b,expected,expected_flags);
      if (rc!=4) $fatal(1,"malformed iterative vector");
      start=1;
      @(negedge clk); start=0;
      latency=0;
      while (done!==1'b1 && latency<128) begin @(negedge clk); latency=latency+1; end
      if (done!==1'b1) $fatal(1,"PROGRESS finite-operation bound index=%0d",n);
      if (error!==1'b0 || {flags,value}!=={expected_flags,expected})
        $fatal(1,"IEEE index=%0d a=%h b=%h expected=%h/%h got=%h/%h error=%b",
          n,a,b,expected_flags,expected,flags,value,error);
      n=n+1;
      @(negedge clk);
      if (done!==1'b0) $fatal(1,"done not a pulse");
    end
    if (n==0) $fatal(1,"no comparisons");
    $display("COMPARED iterative=%0d",n);
    $finish;
  end
endmodule
"""
