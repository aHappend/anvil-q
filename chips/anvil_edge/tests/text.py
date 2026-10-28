"""Independent synthetic Unicode/profile transactions, not official assets."""

import json
from pathlib import Path
import struct
import unicodedata

from protocol import bpe_reference


BENCH = r"""
module bench;
  reg clk=0;
  reg rst_n;
  always #5 clk=~clk;
  reg start=0,in_valid=0,in_last=0,out_ready=0;
  reg [31:0] in_value=0;
  wire in_ready,out_valid,out_last,busy,done,error;
  wire [63:0] out_value;
  wire [7:0] error_code;
  wire tbl_req_valid,tbl_rsp_ready;
  wire [63:0] tbl_req_addr;
  reg tbl_req_ready=0,tbl_rsp_valid=0,tbl_rsp_error=0;
  reg [31:0] tbl_rsp_data=0;
  @DUT@
  reg [63:0] expected[0:@ARRAY_LAST@];
  reg [31:0] rng=@SEED@;
  reg outstanding=0,req_held=0,out_held=0;
  reg [63:0] pending_addr=0,held_addr=0;
  reg [64:0] held_out=0;
  integer requests=0,responses=0,outputs=0,completions=0,cycle=0,delay_count=0;
  integer req_wait=0,out_wait=0,request_stalls=0,output_stalls=0,comparisons=0;
  integer inputs=0;
  @MEMORY_DECLARATIONS@
  function automatic [31:0] memory(input [63:0] address);
    begin
      @MEMORY_LOOKUP@
    end
  endfunction
  task automatic reset_check;
    begin
      if ({in_ready,out_valid,out_value,out_last,busy,done,error,error_code,
           tbl_req_valid,tbl_req_addr,tbl_rsp_ready} !== '0)
        $fatal(1,"TEXT_RESET t=%0t",$time);
    end
  endtask
  always @(posedge clk or negedge clk) if (!rst_n) reset_check();
  always @(negedge clk) begin
    if (rst_n) begin
      rng=rng ^ (rng<<13); rng=rng ^ (rng>>17); rng=rng ^ (rng<<5);
      tbl_req_ready=req_wait>=2 && rng[0] && cycle%5!=0;
      out_ready=out_wait>=3 && rng[1] && cycle%7!=0;
      if (outstanding && !tbl_rsp_valid) begin
        if (delay_count==0) begin
          tbl_rsp_valid<=1; tbl_rsp_data=memory(pending_addr);
          tbl_rsp_error=@BUS_ERROR@;
        end else delay_count=delay_count-1;
      end
    end
  end
  always @(posedge clk) begin
    cycle=cycle+1;
    if (rst_n) begin
      if ((^{in_ready,out_valid,out_value,out_last,busy,done,error,error_code,
             tbl_req_valid,tbl_req_addr,tbl_rsp_ready})===1'bx)
        $fatal(1,"TEXT_XZ");
      if (req_held && (!tbl_req_valid || tbl_req_addr!==held_addr))
        $fatal(1,"TEXT_REQUEST_STABILITY");
      if (out_held && (!out_valid || {out_last,out_value}!==held_out))
        $fatal(1,"TEXT_OUTPUT_STABILITY");
      req_held=tbl_req_valid && !tbl_req_ready;
      out_held=out_valid && !out_ready;
      held_addr=tbl_req_addr; held_out={out_last,out_value};
      if (req_held) request_stalls=request_stalls+1;
      if (out_held) output_stalls=output_stalls+1;
      if (tbl_req_valid) req_wait=req_wait+1;
      if (out_valid) out_wait=out_wait+1;
      if (in_valid && in_ready) inputs=inputs+1;
      if (tbl_rsp_valid && tbl_rsp_ready) begin
        if (!outstanding) $fatal(1,"TEXT_ORPHAN_RESPONSE");
        outstanding=0; responses=responses+1; tbl_rsp_valid<=0;
      end
      if (tbl_req_valid && tbl_req_ready) begin
        if (outstanding || tbl_req_addr[1:0]!=0)
          $fatal(1,"TEXT_REQUEST_CONSERVATION");
        pending_addr=tbl_req_addr; outstanding=1; delay_count=1+rng[4:2];
        requests=requests+1; comparisons=comparisons+1; req_wait=0;
      end
      if (out_valid && out_ready) begin
        if (outputs>=@OUTPUTS@ || out_value!==expected[outputs] ||
            out_last!==(outputs==@OUTPUTS@-1))
          $fatal(1,"TEXT_VECTOR item=%0d expected=%h observed=%h last=%b",
                 outputs,expected[outputs],out_value,out_last);
        outputs=outputs+1; comparisons=comparisons+1; out_wait=0;
      end
      if (done) begin
        if (error || outputs!=@OUTPUTS@ || outstanding || completions!=0)
          $fatal(1,"TEXT_PREMATURE_DONE");
        completions=completions+1;
      end
    end
  end
  task automatic tick; begin @(posedge clk); #1; end endtask
  task automatic item(input [31:0] value,input bit last);
    begin
      if (!error) begin
        @(negedge clk); #1; in_valid=1; in_value=value; in_last=last;
        do begin @(posedge clk); end while (!in_ready && !error);
        #1; @(negedge clk); #1; in_valid=0;
      end
    end
  endtask
  initial begin
    rst_n=0; #0; reset_check();
    @VECTORS@
    repeat (2) tick();
    @(negedge clk); #1; rst_n=1; start=1; tick();
    @(negedge clk); #1; start=0;
    @STIMULUS@
    if (@ERROR_CODE@!=0) begin
      while (!error && completions==0) tick();
      repeat (10) begin
        tick();
        if (error!==1 || error_code!==@ERROR_CODE@ || done!==0 ||
            out_valid!==0 || in_ready!==0)
          $fatal(1,"TEXT_ERROR expected=%h observed=%h",@ERROR_CODE@,error_code);
      end
      if (outputs!=@OUTPUTS@ || completions!=0 || outstanding)
        $fatal(1,"TEXT_ERROR_COUNTS");
    end else begin
      while (completions==0 && !error) tick();
      repeat (10) tick();
      if (error || completions!=1 || outputs!=@OUTPUTS@ ||
          responses!=requests || outstanding || busy || inputs!=@INPUTS@)
        $fatal(1,"TEXT_COUNTS inputs=%0d requests=%0d responses=%0d outputs=%0d error=%h",
               inputs,requests,responses,outputs,error_code);
    end
    if ((requests>0 && request_stalls==0) || (@OUTPUTS@>0 && output_stalls==0))
      $fatal(1,"TEXT_REQUIRED_STALLS");
    comparisons=comparisons+1;
    if (comparisons!=requests+@OUTPUTS@+1) $fatal(1,"TEXT_COMPARISONS");
    $display("TEXT_COUNTS inputs=%0d requests=%0d responses=%0d outputs=%0d",
             inputs,requests,responses,outputs);
    $display("COMPARED %0d",comparisons); $finish;
  end
  initial begin
    repeat (@CYCLES@) @(posedge clk); $fatal(1,"TEXT_CYCLE_BOUND");
  end
endmodule
"""


def word_memory(base, records):
    data = b"".join(records)
    assert len(data) % 4 == 0
    return {base + 32 + offset: int.from_bytes(data[offset:offset + 4], "little")
            for offset in range(0, len(data), 4)}


def record(*values):
    return struct.pack("<" + "I" * len(values), *values)


def ranges_for(properties, classes=None):
    """Cover scalars; assign explicitly selected fixture properties/classes."""
    classes = classes or {}
    boundaries = {0, 0xD800, 0xE000, 0x110000}
    for scalar in properties.keys() | classes.keys():
        boundaries.update((scalar, scalar + 1))
    boundaries = sorted(boundaries)
    return [record(first, end - 1, classes.get(first, 0), properties.get(first, 0))
            for first, end in zip(boundaries, boundaries[1:])
            if not (0xD800 <= first < 0xE000)]


def run_text_case(evidence, name, seed, dut, memory, inputs, expected, *,
                  error=0, bus_error=False, cycles=2000000, provenance=None):
    declarations = ""
    lookup = ("case (address)\n" +
              "\n".join(f"64'h{a:x}: memory=32'h{v:08x};"
                        for a, v in sorted(memory.items())) +
              '\ndefault: $fatal(1,"TEXT_UNMAPPED_READ address=%h",address);\nendcase')
    if len(memory) > 4096:
        # Keep complete source-derived tables without a huge C++ case statement.
        ordered = sorted(memory.items())
        groups = []
        for index, (address, value) in enumerate(ordered):
            if not groups or address != groups[-1][1]:
                groups.append([address, address + 4, index])
            else:
                groups[-1][1] = address + 4
        image = evidence.path / f"{name}-s{seed}-table.hex"
        with image.open("x", encoding="ascii") as output:
            output.write("".join(f"{value:08x}\n" for _, value in ordered))
        declarations = (
            f"reg [31:0] table_words[0:{len(ordered) - 1}];\n"
            f'  initial $readmemh("{evidence.relative(image)}",table_words);')
        lookup = ('if (address[1:0]!=0) $fatal(1,"TEXT_UNALIGNED_READ");\n' +
                  "\nelse ".join(
                      f"if (address>=64'h{first:x} && address<64'h{end:x}) "
                      f"memory=table_words[{index}+((address-64'h{first:x})>>2)];"
                      for first, end, index in groups) +
                  '\nelse $fatal(1,"TEXT_UNMAPPED_READ address=%h",address);')
    values = {
        "DUT": dut, "SEED": str(seed), "BUS_ERROR": str(int(bus_error)),
        "OUTPUTS": str(len(expected)), "INPUTS": str(len(inputs)),
        "ARRAY_LAST": str(max(0, len(expected) - 1)),
        "ERROR_CODE": f"8'h{error:02x}", "CYCLES": str(cycles),
        "MEMORY_DECLARATIONS": declarations, "MEMORY_LOOKUP": lookup,
        "VECTORS": "\n".join(f"expected[{i}]=64'h{v:x};"
                             for i, v in enumerate(expected)),
        "STIMULUS": "\n".join(f"item(32'h{v:x},{int(i == len(inputs)-1)});"
                              for i, v in enumerate(inputs)),
    }
    bench = BENCH
    for key, value in values.items():
        bench = bench.replace(f"@{key}@", value)
    root = Path(__file__).resolve().parent.parent
    sources = ["rtl/anvil_edge_numeric_pkg.sv",
               *[str(path.relative_to(root)) for path in sorted((root / "rtl").glob("*.sv"))
                 if path.name != "anvil_edge_numeric_pkg.sv"]]
    fixture = {
        "scope": "synthetic profile, not official tokenizer acceptance",
        "inputs": inputs, "expected": expected, "expected_error": error,
        "memory_words": [[address, value] for address, value in sorted(memory.items())],
        "reference": provenance,
    }
    (evidence.path / f"{name}-s{seed}-reference.json").write_text(
        json.dumps(fixture, indent=2) + "\n", encoding="ascii")
    evidence.simulate(f"{name}-s{seed}", bench, sources, None)


def normalization_fixture(text):
    scalars = set(map(ord, text))
    for form in ("NFC", "NFD", "NFKC", "NFKD"):
        scalars.update(map(ord, unicodedata.normalize(form, text)))
    # Composition may need intermediate starters absent from the final result.
    pending = list(scalars)
    while pending:
        scalar = pending.pop()
        expansion = set()
        for form in ("NFD", "NFKD"):
            expansion.update(map(ord, unicodedata.normalize(form, chr(scalar))))
        expansion.update(int(part, 16) for part in unicodedata.decomposition(chr(scalar)).split()
                         if not part.startswith("<"))
        pending.extend(expansion - scalars)
        scalars.update(expansion)
    pool, decompositions = [], []
    compositions = {}
    for scalar in sorted(scalars):
        raw = unicodedata.decomposition(chr(scalar))
        if not raw:
            continue
        compatibility = raw.startswith("<")
        expansion = unicodedata.normalize("NFKD" if compatibility else "NFD", chr(scalar))
        decompositions.append(record(scalar, len(pool), len(expansion), int(compatibility)))
        pool.extend(map(ord, expansion))
        canonical = raw.split()
        if not compatibility and len(canonical) == 2:
            pair = tuple(int(value, 16) for value in canonical)
            if unicodedata.normalize("NFC", "".join(map(chr, pair))) == chr(scalar):
                compositions[pair] = scalar
    ranges = ranges_for({scalar: unicodedata.combining(chr(scalar)) for scalar in scalars})
    memory = {}
    for base, records in (
        (0x1000, ranges), (0x10000, decompositions),
        (0x20000, [record(scalar) for scalar in pool]),
        (0x30000, [record(*pair, scalar, 0)
                   for pair, scalar in sorted(compositions.items())]),
    ):
        memory.update(word_memory(base, records))
    return memory, (len(ranges), len(decompositions), len(pool), len(compositions))


def normalizer_test(evidence, seed, name, text, mode, *, capacity=64, error=0,
                    bus_error=False):
    memory, counts = normalization_fixture(text)
    form = {0: None, 1: "NFC", 2: "NFKC", 3: "NFD", 4: "NFKD"}[mode]
    expected = list(map(ord, unicodedata.normalize(form, text) if form else text))
    if error:
        expected = []
    dut = f"""
  wire [31:0] normalized_scalar;
  assign out_value={{32'd0,normalized_scalar}};
  anvil_edge_normalizer #(.MAX_SCALARS({capacity})) dut(
    .clk(clk),.rst_n(rst_n),.start(start),.config_valid(1'b1),
    .cfg_normalization(32'd{mode}),.cfg_ranges_base(64'h1000),
    .cfg_decomposition_base(64'h10000),.cfg_scalar_pool_base(64'h20000),
    .cfg_composition_base(64'h30000),.cfg_range_count(32'd{counts[0]}),
    .cfg_class_count(32'd1),.cfg_decomposition_count(32'd{counts[1]}),
    .cfg_scalar_pool_count(32'd{counts[2]}),.cfg_composition_count(32'd{counts[3]}),
    .in_valid(in_valid),.in_ready(in_ready),.in_scalar(in_value),.in_last(in_last),
    .out_valid(out_valid),.out_ready(out_ready),.out_scalar(normalized_scalar),
    .out_last(out_last),.busy(busy),.done(done),.error(error),.error_code(error_code),
    .tbl_req_valid(tbl_req_valid),.tbl_req_ready(tbl_req_ready),
    .tbl_req_addr(tbl_req_addr),.tbl_rsp_valid(tbl_rsp_valid),
    .tbl_rsp_ready(tbl_rsp_ready),.tbl_rsp_data(tbl_rsp_data),.tbl_rsp_error(tbl_rsp_error));
"""
    run_text_case(evidence, f"normalize-{name}-m{mode}", seed, dut, memory,
                  list(map(ord, text)), expected, error=error, bus_error=bus_error,
                  provenance={"library": "Python unicodedata", "version": unicodedata.unidata_version,
                              "form": form, "capacity": capacity})


def run_normalization(evidence):
    evidence.tools(("iverilog", "vvp", "python3"))
    examples = (
        ("identity", "e\u0301 \ufb03 \uac01 \U0001f600", (0,)),
        ("canonical", "\u00e9 e\u0301 \u212b A\u030a", (1, 2, 3, 4)),
        ("compatibility", "\ufb03 \uff21 \u2460 \u00a0", (1, 2, 3, 4)),
        ("order", "e\u0315\u0300 A\u030a\u0301", (1, 2, 3, 4)),
        ("stable-block", "A\u0305\u030a e\u0301\u0300", (1, 3)),
        ("leading-marks", "\u0315\u0300\u0301a", (1, 3)),
        ("hangul", "\uac00\uac01\uac1c\ud7a3 \u1100\u1161\u11a8", (1, 2, 3, 4)),
        ("supplementary", "\U0001f600\U0001d400", (1, 2, 3, 4)),
    )
    for seed in (1, 17, 89):
        for name, text, modes in examples:
            for mode in modes:
                normalizer_test(evidence, seed, name, text, mode)
        normalizer_test(evidence, seed, "single", "a", 1, capacity=1)
        normalizer_test(evidence, seed, "capacity", "\ufb03", 4, capacity=1, error=0x30)
        normalizer_test(evidence, seed, "ddr-error", "\u00e9", 3, error=4, bus_error=True)


def dfa_profile(kind):
    # All real scalars use class zero, synthetic end-of-span uses class one.
    ops = [(2, 0, 0, 0)]
    accepts = [(0, 0, int(kind == "shortest"), 0)]
    states = [(0, 0, 0, 0), (2, 0, 1, 0), (4, 1, 0, 0)]
    transitions = [
        (1, 0, 1, 0), (2, 0, 0, 0),
        (1, 0, 1, 0), (2, 0, 0, 0),
        (2, 0, 0, 0), (2, 0, 0, 0),
    ]
    if kind == "unsigned-priority":
        accepts = [(0xFFFFFFFF, 0, 0, 0)]
    elif kind == "priority-over-length":
        ops = [(2, 0, 0, 0), (2, 1, 0, 0)]
        accepts = [(0, 0, 1, 0), (0xFFFFFFFF, 1, 0, 0)]
        states[1] = (2, 0, 2, 0)
        states[2] = (4, 2, 0, 0)
        transitions[0] = transitions[2] = (1, 0, 2, 0)
    elif kind == "copy-clear":
        ops = [(0, 0, 0, 0), (3, 1, 0, 0), (2, 2, 0, 0)]
        accepts = [(0, 1, 0, 0), (1, 2, 0, 0)]
        states[1] = (2, 0, 2, 0)
        states[2] = (4, 2, 0, 0)
        transitions[0] = transitions[2] = (1, 0, 3, 0)
    elif kind == "ordered-ops":
        ops = [(1, 0, 0, 0), (2, 1, 0, 0), (3, 0, 1, 0), (0, 1, 0, 0)]
        transitions[0] = transitions[2] = (1, 0, 4, 0)
    elif kind == "lookahead-rewind":
        ops = [(1, 0, 0, 0), (3, 1, 0, 0)]
        accepts = [(0, 1, 0, 0)]
        states = [(0, 0, 0, 0), (2, 0, 0, 0), (4, 0, 1, 0), (6, 1, 0, 0)]
        transitions = [
            (1, 0, 0, 0), (3, 0, 0, 0),
            (2, 0, 2, 0), (2, 0, 2, 0),
            (3, 0, 0, 0), (3, 0, 0, 0),
            (3, 0, 0, 0), (3, 0, 0, 0),
        ]
    elif kind == "no-candidate":
        accepts = []
        states[1] = (2, 0, 0, 0)
        states[2] = (4, 0, 0, 0)
    return {"states": states, "transitions": transitions, "ops": ops,
            "accepts": accepts, "dead": len(states) - 1}


def dfa_reference(text, profile):
    """Interpret the specified tagged-table language, without RTL state timing."""
    ends = [0]
    for scalar in text:
        ends.append(ends[-1] + len(scalar.encode("utf-8")))
    anchor, result = 0, []
    while anchor < len(text):
        tags = [None] * 32
        state, candidates = 0, []
        for cursor in range(anchor, len(text) + 1):
            at_end = cursor == len(text)
            before, after = ends[cursor], ends[cursor + int(not at_end)]
            first, _, _, _ = profile["states"][state]
            state, op_start, op_count, _ = profile["transitions"][first + int(at_end)]
            for opcode, dest, source, _ in profile["ops"][op_start:op_start + op_count]:
                tags[dest] = (None if opcode == 0 else before if opcode == 1
                              else after if opcode == 2 else tags[source])
            _, first_accept, count, _ = profile["states"][state]
            for priority, end_register, policy, _ in profile["accepts"][first_accept:first_accept + count]:
                end = tags[end_register]
                if end is not None and ends[anchor] < end <= after:
                    candidates.append((priority, end if policy else -end, end))
            if at_end or state == profile["dead"]:
                break
        if not candidates:
            raise ValueError("No valid pretoken candidate")
        end = min(candidates)[2]
        result.append((ends[anchor], end))
        anchor = ends.index(end)
    return result


def dfa_test(evidence, seed, kind, text="a\u00e9\u4e2d\U0001f600b"):
    profile = dfa_profile(kind)
    ranges = ranges_for({})
    memory = word_memory(0x1000, ranges)
    for base, name in ((0x10000, "states"), (0x20000, "transitions"),
                       (0x30000, "ops"), (0x40000, "accepts")):
        memory.update(word_memory(base, [record(*values) for values in profile[name]]))
    error = 0x12 if kind == "no-candidate" else 0
    expected = []
    if not error:
        spans = dfa_reference(text, profile)
        if kind in ("shortest", "priority-over-length", "lookahead-rewind"):
            positions = [0]
            for char in text:
                positions.append(positions[-1] + len(char.encode()))
            assert spans == list(zip(positions, positions[1:]))
        else:
            assert spans == [(0, len(text.encode()))]
        expected = [(start << 32) | end for start, end in spans]
    dut = f"""
  wire [31:0] span_start,span_end;
  assign out_value={{span_start,span_end}};
  anvil_edge_tagged_dfa #(.MAX_SPAN_BYTES(64)) dut(
    .clk(clk),.rst_n(rst_n),.start(start),.config_valid(1'b1),
    .cfg_ranges_base(64'h1000),.cfg_states_base(64'h10000),
    .cfg_transitions_base(64'h20000),.cfg_tag_ops_base(64'h30000),
    .cfg_accepts_base(64'h40000),.cfg_range_count(32'd{len(ranges)}),
    .cfg_class_count(32'd1),.cfg_state_count(32'd{len(profile["states"])}),
    .cfg_transition_count(32'd{len(profile["transitions"])}),
    .cfg_tag_op_count(32'd{len(profile["ops"])}),
    .cfg_accept_count(32'd{len(profile["accepts"])}),
    .cfg_start_state(32'd0),.cfg_dead_state(32'd{profile["dead"]}),
    .cfg_tag_register_count(32'd32),.in_valid(in_valid),.in_ready(in_ready),
    .in_scalar(in_value),.in_last(in_last),.out_valid(out_valid),
    .out_ready(out_ready),.out_start(span_start),.out_end(span_end),.out_last(out_last),
    .busy(busy),.done(done),.error(error),.error_code(error_code),
    .tbl_req_valid(tbl_req_valid),.tbl_req_ready(tbl_req_ready),
    .tbl_req_addr(tbl_req_addr),.tbl_rsp_valid(tbl_rsp_valid),
    .tbl_rsp_ready(tbl_rsp_ready),.tbl_rsp_data(tbl_rsp_data),.tbl_rsp_error(tbl_rsp_error));
"""
    run_text_case(evidence, "dfa-" + kind, seed, dut, memory,
                  list(map(ord, text)), expected, error=error, provenance=profile)


def run_dfa(evidence):
    evidence.tools(("iverilog", "vvp"))
    for seed in (1, 17, 89):
        for kind in ("longest", "shortest", "unsigned-priority", "priority-over-length",
                     "copy-clear", "ordered-ops", "lookahead-rewind", "no-candidate"):
            dfa_test(evidence, seed, kind)


WHITE_SPACE = frozenset(
    [*range(0x9, 0xE), 0x20, 0x85, 0xA0, 0x1680, *range(0x2000, 0x200B),
     0x2028, 0x2029, 0x202F, 0x205F, 0x3000])


def word_scalar(char):
    category = unicodedata.category(char)
    return category[0] in "LMN" or category == "Pc"


def split_special_reference(text, specials, phase, policy):
    """Return ordinary spans and protected token IDs with AddedToken policy."""
    if policy == 0:
        return [text] if text else []
    plan, ordinary, position = [], "", 0
    while position < len(text):
        candidates = []
        for index, (piece, token, flags) in enumerate(specials):
            if not flags & 1 or bool(flags & 16) != phase or not text.startswith(piece, position):
                continue
            end = position + len(piece)
            if flags & 8 and ((position and word_scalar(text[position - 1]))
                              or (end < len(text) and word_scalar(text[end]))):
                continue
            candidates.append((-len(piece.encode()), index, end, token, flags))
        if not candidates:
            ordinary += text[position]
            position += 1
            continue
        if policy == 2:
            raise ValueError("Raw special rejected")
        _, _, end, token, flags = min(candidates)
        if flags & 2:
            while ordinary and ord(ordinary[-1]) in WHITE_SPACE:
                ordinary = ordinary[:-1]
        if ordinary:
            plan.append(ordinary)
            ordinary = ""
        plan.append(token)
        position = end
        if flags & 4:
            while position < len(text) and ord(text[position]) in WHITE_SPACE:
                position += 1
    if ordinary:
        plan.append(ordinary)
    return plan


def tokenizer_reference(text, specials, mode, policy, bos, merges, dfa_kind):
    form = {0: None, 1: "NFC", 2: "NFKC", 3: "NFD", 4: "NFKD"}[mode]
    result = [254] if bos else []
    for raw_part in split_special_reference(text, specials, False, policy):
        if isinstance(raw_part, int):
            result.append(raw_part)
            continue
        normalized = unicodedata.normalize(form, raw_part) if form else raw_part
        for part in split_special_reference(normalized, specials, True, policy):
            if isinstance(part, int):
                result.append(part)
            else:
                raw = part.encode()
                for start, end in dfa_reference(part, dfa_profile(dfa_kind)):
                    result.extend(bpe_reference(raw[start:end], merges))
    return result


def tokenizer_fixture(text, *, mode=0, policy=0, bos=False, special_options=(),
                      dfa_kind="longest", family=1):
    bases = [0x100000 + index * 0x10000 for index in range(16)]
    pieces = [bytes([byte]) for byte in range(256)] + [b"AB", b"BC", b"ABC"]
    merges = {(65, 66): (256, 10), (66, 67): (257, 1), (256, 67): (258, 0)}
    specials = []
    for piece, flags in special_options:
        specials.append((piece, len(pieces), flags))
        pieces.append(piece.encode())
    token_bytes, records = bytearray(), []
    for index, piece in enumerate(pieces):
        records.append(struct.pack("<QII", len(token_bytes), len(piece), 1 if index < 259 else 2))
        token_bytes.extend(piece)
    nodes = [{"edges": {}, "terminal": 0xFFFFFFFF}]
    for special_index, (piece, _, _) in enumerate(specials):
        node = 0
        for byte in piece.encode():
            if byte not in nodes[node]["edges"]:
                nodes[node]["edges"][byte] = len(nodes)
                nodes.append({"edges": {}, "terminal": 0xFFFFFFFF})
            node = nodes[node]["edges"][byte]
        assert nodes[node]["terminal"] == 0xFFFFFFFF
        nodes[node]["terminal"] = special_index
    edges, node_records = [], []
    for node in nodes:
        node_records.append(record(len(edges), len(node["edges"]), node["terminal"], 0))
        edges.extend(record(byte, next_node) for byte, next_node in sorted(node["edges"].items()))
    profile = dfa_profile(dfa_kind)
    norm_memory, norm_counts = normalization_fixture(text + "".join(p[0] for p in specials))
    scalar_properties = {}
    for address in range(0x1020, 0x1020 + norm_counts[0] * 16, 16):
        first, last, _, ccc = [norm_memory[address + offset] for offset in range(0, 16, 4)]
        if first == last:
            scalar_properties[first] = ccc
    # Only fixture-reachable scalars need non-default classification values.
    relevant = set(map(ord, text + "".join(p[0] for p in specials)))
    for form in ("NFC", "NFD", "NFKC", "NFKD"):
        relevant.update(map(ord, unicodedata.normalize(form, text)))
    for scalar in relevant:
        scalar_properties[scalar] = (unicodedata.combining(chr(scalar))
                                     | (int(scalar in WHITE_SPACE) << 8)
                                     | (int(word_scalar(chr(scalar))) << 9))
    ranges = ranges_for(scalar_properties)
    tables = {
        1: (16, records),
        2: (1, [bytes([byte]) for byte in token_bytes]),
        3: (4, [record(byte) for byte in range(256)]),
        4: (16, [record(left, right, result, rank)
                 for (left, right), (result, rank) in sorted(merges.items())]),
        5: (16, node_records), 6: (8, edges), 7: (16, ranges),
        8: (16, [record(*value) for value in profile["states"]]),
        9: (16, [record(*value) for value in profile["transitions"]]),
        10: (16, [record(token, flags, 0, 0) for _, token, flags in specials]),
        11: (16, [record(*value) for value in profile["ops"]]),
        12: (16, [record(*value) for value in profile["accepts"]]),
    }
    for index, old_base, count, width in (
        (13, 0x10000, norm_counts[1], 16),
        (14, 0x20000, norm_counts[2], 4),
        (15, 0x30000, norm_counts[3], 16),
    ):
        values = [norm_memory[old_base + 32 + offset] for offset in range(0, count * width, 4)]
        data = record(*values)
        tables[index] = (width, [data[offset:offset + width]
                                 for offset in range(0, len(data), width)])
    memory, counts = {}, [0] * 16
    for index, (_, values) in tables.items():
        data = b"".join(values)
        memory.update(word_memory(bases[index], [data + bytes(-len(data) % 4)]))
        counts[index] = len(values)
    unicode_version = tuple(map(int, unicodedata.unidata_version.split(".")))
    assert len(unicode_version) == 3
    metadata = [
        1, family, len(pieces), mode, policy, int(bos), 254 if bos else 0, 255,
        (unicode_version[0] << 16) | (unicode_version[1] << 8) | unicode_version[2],
        1, 0, profile["dead"], 32, 0,
        max(map(len, pieces)), 4096, *([0] * 16),
    ]
    return memory, bases, counts, metadata, specials, merges


def tokenizer_test(evidence, seed, name, text, *, mode=0, policy=0, bos=False,
                   special_options=(), dfa_kind="longest", family=1,
                   byte_capacity=64, token_capacity=64, error=0, raw=None):
    memory, bases, counts, metadata, specials, merges = tokenizer_fixture(
        text, mode=mode, policy=policy, bos=bos, special_options=special_options,
        dfa_kind=dfa_kind, family=family)
    expected = [] if error else tokenizer_reference(text, specials, mode, policy, bos, merges, dfa_kind)
    assert error or len(expected) <= token_capacity
    packed_bases = sum(base << (64 * index) for index, base in enumerate(bases))
    packed_counts = sum(count << (32 * index) for index, count in enumerate(counts))
    packed_metadata = sum(value << (32 * index) for index, value in enumerate(metadata))
    dut = f"""
  wire [31:0] token_id;
  assign out_value={{32'd0,token_id}};
  anvil_edge_bpe_tokenizer #(.MAX_PROMPT_BYTES({byte_capacity}),
    .MAX_PROMPT_TOKENS({token_capacity}),.MAX_PRETOKEN_BYTES(4096)) dut(
    .clk(clk),.rst_n(rst_n),.start(start),.config_valid(1'b1),
    .cfg_table_bases(1024'h{packed_bases:x}),.cfg_table_counts(512'h{packed_counts:x}),
    .cfg_metadata(1024'h{packed_metadata:x}),.in_valid(in_valid),.in_ready(in_ready),
    .in_data(in_value[7:0]),.in_last(in_last),.out_valid(out_valid),.out_ready(out_ready),
    .out_token_id(token_id),.out_last(out_last),.busy(busy),.done(done),
    .error(error),.error_code(error_code),.tbl_req_valid(tbl_req_valid),
    .tbl_req_ready(tbl_req_ready),.tbl_req_addr(tbl_req_addr),.tbl_rsp_valid(tbl_rsp_valid),
    .tbl_rsp_ready(tbl_rsp_ready),.tbl_rsp_data(tbl_rsp_data),.tbl_rsp_error(tbl_rsp_error));
"""
    inputs = list(text.encode() if raw is None else raw)
    run_text_case(evidence, "tokenizer-" + name, seed, dut, memory, inputs, expected,
                  error=error, cycles=max(2000000, len(inputs) * len(inputs) * 100),
                  provenance={"metadata": metadata, "specials": specials,
                              "unicodedata_version": unicodedata.unidata_version,
                              "dfa": dfa_profile(dfa_kind), "merges": [
                                  [*pair, *value] for pair, value in sorted(merges.items())]})


def run_tokenizer(evidence):
    evidence.tools(("iverilog", "vvp", "python3"))
    specials = (("<X>", 1), ("<X>Y", 1), ("word", 9), ("[S]", 7),
                ("\u00e9", 17), ("\uff21", 1), ("!", 0))
    for seed in (1, 17, 89):
        for name, text, options in (
            ("ranked", "ABC AB \u00e9 \u4e2d \U0001f600 e\u0301\n123", {}),
            ("pretoken-boundary", "AB", {"dfa_kind": "shortest"}),
            ("bos", "ABC", {"bos": True}),
            ("special-longest", "a<X>Y<X>b", {"policy": 1}),
            ("special-word", "word sword word2 _word word\u0301 word", {"policy": 1}),
            ("special-strip", " a\u2003[S]\u00a0 b ", {"policy": 1}),
            ("ordinary-special-spelling", "<X> [S] word \uff21", {"policy": 0, "mode": 2}),
            ("disabled-special", "a!b", {"policy": 1}),
            ("normalized-special", "e\u0301 x \uff21", {"policy": 1, "mode": 1}),
            ("protected-before-normalization", "\uff21 e\u0301 \uff21", {"policy": 1, "mode": 2}),
            ("all-special", "<X><X>Y", {"policy": 1, "bos": True}),
            ("reject-raw", "a<X>b", {"policy": 2, "error": 0x13}),
            ("reject-normalized", "e\u0301", {"policy": 2, "mode": 1, "error": 0x13}),
            ("nfd", "\u00e9\uac01", {"mode": 3}),
            ("nfkc", "\ufb03 \uff21 A\u030a\u0301", {"mode": 2}),
        ):
            tokenizer_test(evidence, seed, name, text, special_options=specials, **options)
        for capacity in (1, 3):
            tokenizer_test(evidence, seed, f"bytes-{capacity}", "x" * capacity,
                           byte_capacity=capacity, token_capacity=capacity)
            tokenizer_test(evidence, seed, f"bytes-over-{capacity}", "x" * (capacity + 1),
                           byte_capacity=capacity, token_capacity=capacity + 1, error=0x30)
            tokenizer_test(evidence, seed, f"tokens-over-{capacity}", "x" * (capacity + 1),
                           byte_capacity=capacity + 1, token_capacity=capacity, error=0x30)
        for name, raw in (("overlong", b"\xc0\x80"), ("surrogate", b"\xed\xa0\x80"),
                          ("range", b"\xf4\x90\x80\x80"), ("truncated", b"\xe2\x82"),
                          ("continuation", b"\x80"), ("late-invalid", b"ABC\xf0\x80")):
            tokenizer_test(evidence, seed, name, "ABC", raw=raw, error=0x10)
    run_tokenizer_capacity(evidence)


def run_tokenizer_capacity(evidence):
    evidence.tools(("iverilog", "vvp", "python3"))
    for seed in (1, 17, 89):
        for capacity in (1, 3):
            tokenizer_test(evidence, seed, f"bos-tokens-over-{capacity}", "x" * capacity,
                           byte_capacity=capacity, token_capacity=capacity,
                           bos=True, error=0x30)
        tokenizer_test(evidence, seed, "special-one-token", "<X>", policy=1,
                       byte_capacity=16, token_capacity=1,
                       special_options=(("<X>", 1),))
        tokenizer_test(evidence, seed, "bos-special-exact-three", "<X><X>", policy=1,
                       bos=True, byte_capacity=16, token_capacity=3,
                       special_options=(("<X>", 1),))
        tokenizer_test(evidence, seed, "bos-special-over-three", "<X><X><X>", policy=1,
                       bos=True, byte_capacity=16, token_capacity=3, error=0x30,
                       special_options=(("<X>", 1),))
        tokenizer_test(evidence, seed, "bytes-and-tokens-4096", "x" * 4096,
                       byte_capacity=4096, token_capacity=4096)
        tokenizer_test(evidence, seed, "bytes-over-4096", "x" * 4097,
                       byte_capacity=4096, token_capacity=4097, error=0x30)
        tokenizer_test(evidence, seed, "bos-tokens-over-4096", "x" * 4096,
                       byte_capacity=4096, token_capacity=4096, bos=True, error=0x30)
