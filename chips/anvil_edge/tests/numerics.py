"""Independent integer Transformer oracle and public typed-memory scoreboards.

Reduced synthetic weights exercise arithmetic, not official model quality.
No reference-RTL functions, Designer helpers or DUT internals are imported.
"""

from collections import defaultdict
from dataclasses import dataclass
from fractions import Fraction
import json
import math
from pathlib import Path
import random
import struct

from runtime_inputs import hex_input


def signed(value, width):
    value &= (1 << width) - 1
    return value - (1 << width) if value >> (width - 1) else value


def saturate(value):
    return max(-(1 << 31), min((1 << 31) - 1, value))


def round_ratio(value, divisor):
    magnitude, remainder = divmod(abs(value), divisor)
    magnitude += 2 * remainder >= divisor
    return -magnitude if value < 0 else magnitude


def toward_zero(value, divisor):
    return (-1 if value < 0 else 1) * (abs(value) // divisor)


def half(bits, *, scale=False):
    real = struct.unpack("<e", struct.pack("<H", bits))[0]
    if not math.isfinite(real):
        raise ValueError("nonfinite half tensor")
    if scale and real < 0:
        raise ValueError("negative AWQ scale")
    exact = Fraction(real) * 65536
    value = round_ratio(exact.numerator, exact.denominator)
    return value if scale else saturate(value)


def exponential(value):
    if value < -1048576:
        return 0
    if value >= 0:
        return 1 << 24
    exponent, remainder = divmod(-value * 256, 11629080)
    term = total = 1 << 24
    for order in range(1, 7):
        term = toward_zero(signed(-term * remainder, 64), (1 << 24) * order)
        total = signed(total + term, 64)
    return (max(0, total) >> exponent) & 0xFFFFFFFF


def silu(value):
    exp = exponential(-abs(value))
    numerator = (1 << 48) if value >= 0 else exp * (1 << 24)
    sigmoid = numerator // ((1 << 24) + exp)
    return saturate(round_ratio(signed(value * sigmoid, 65), 1 << 24))


@dataclass(frozen=True)
class Geometry:
    layers: int = 1
    hidden: int = 8
    intermediate: int = 8
    query_heads: int = 1
    kv_heads: int = 1
    head_dim: int = 8
    group: int = 8
    vocabulary: int = 3
    sequence: int = 4


class Reference:
    def __init__(self, geometry, seed):
        self.g = geometry
        self.initial = {}
        self.memory = {}
        self.writes = defaultdict(list)
        self.trace = []
        self.logits = []
        rng = random.Random(seed)
        g = geometry

        def fill(kind, layer, projection, rows, columns, values):
            for row in range(rows):
                for column in range(columns):
                    key = kind, layer, projection, row, column
                    value = values(row, column) & 0xFFFFFFFF
                    self.initial[key] = self.memory[key] = value

        def fp(value):
            return int.from_bytes(struct.pack("<e", value), "little")

        fill(0, 0, 0, g.vocabulary, g.hidden,
             lambda r, c: fp(rng.choice((-1, -.5, -.25, .125, .5, 1))))
        shifts = (0, 16, 4, 20, 8, 24, 12, 28)
        for layer in range(g.layers):
            for projection in range(7):
                inputs, outputs = self.dimensions(projection)
                zeros = {}
                for group in range(inputs // g.group):
                    for tile in range(outputs // 8):
                        zeros[group, tile] = [rng.randrange(3, 13) for _ in range(8)]
                fill(2, layer, projection, inputs // g.group, outputs // 8,
                     lambda r, c: sum(z << shift for z, shift in zip(zeros[r, c], shifts)))
                fill(1, layer, projection, inputs, outputs // 8,
                     lambda r, c: sum((z + rng.choice((-2, -1, 0, 1, 2))) << shift
                                      for z, shift in zip(zeros[r // g.group, c], shifts)))
                fill(3, layer, projection, inputs // g.group, outputs,
                     lambda r, c: fp(rng.choice((.015625, .03125, .0625))))
                if projection < 3:
                    fill(4, layer, projection, 1, outputs,
                         lambda r, c: fp(rng.choice((-.125, -.0625, .03125, .125))))
            for kind in (5, 6):
                fill(kind, layer, 0, 1, g.hidden,
                     lambda r, c: fp(rng.choice((-.5, .5, 1, 1.5))))
            for kind in (9, 10):
                fill(kind, layer, 0, g.sequence, g.kv_heads * g.head_dim, lambda r, c: 0)
        fill(7, 0, 0, 1, g.hidden, lambda r, c: fp(rng.choice((.5, 1, 1.5))))
        lengths = {
            0: g.hidden, 1: g.hidden, 2: g.hidden, 3: g.kv_heads * g.head_dim,
            4: g.kv_heads * g.head_dim, 5: g.hidden, 6: g.hidden, 7: g.hidden,
            8: g.hidden, 9: g.intermediate, 10: g.intermediate,
            11: g.intermediate, 12: g.hidden, 14: g.hidden,
        }
        for slot, length in lengths.items():
            for column in range(length):
                self.initial[8, 0, 0, slot, column] = self.memory[8, 0, 0, slot, column] = 0
        # Exact rational rotations include positive/negative cosines and sines.
        # These need not approximate any particular model's positional schedule.
        rotations = ((1 << 30, 0), (0, 1 << 30), (-(1 << 29), 1 << 29),
                     (1 << 29, -(1 << 29)))
        fill(11, 0, 0, g.sequence, g.head_dim,
             lambda r, c: rotations[(r + c // 2) % len(rotations)][c % 2])

    def dimensions(self, projection):
        g = self.g
        return (g.intermediate if projection == 6 else g.hidden,
                g.intermediate if projection in (4, 5) else
                g.kv_heads * g.head_dim if projection in (1, 2) else g.hidden)

    def get(self, kind, row, column, layer=0, projection=0):
        return self.memory[kind, layer, projection, row, column]

    def put(self, kind, row, values, stage, layer=0):
        for column, value in enumerate(values):
            key = kind, layer, 0, row, column
            if key not in self.initial:
                raise AssertionError(f"Reference wrote outside the frozen tensor shape: {key}")
            word = value & 0xFFFFFFFF
            self.memory[key] = word
            self.writes[key].append(word)
            self.trace.append({"stage": stage, "key": key, "word": word})

    def norm(self, values, kind, layer):
        total = sum(value * value for value in values)
        mean = ((total << 32) // self.g.hidden) + 18446744073710
        reciprocal = (1 << 64) // math.isqrt(mean)
        return [saturate(round_ratio(signed(signed(x * half(self.get(kind, 0, i, layer)), 64)
                                           * reciprocal, 128), 1 << 48))
                for i, x in enumerate(values)]

    def gemv(self, values, projection, layer):
        inputs, outputs = self.dimensions(projection)
        assert len(values) == inputs
        shifts = (0, 16, 4, 20, 8, 24, 12, 28)
        result = []
        for column in range(outputs):
            accumulator = 0
            for row, activation in enumerate(values):
                packed_w = self.get(1, row, column // 8, layer, projection)
                packed_z = self.get(2, row // self.g.group, column // 8, layer, projection)
                shift = shifts[column % 8]
                delta = ((packed_w >> shift) & 15) - ((packed_z >> shift) & 15)
                scale = half(self.get(3, row // self.g.group, column, layer, projection),
                             scale=True)
                weight = signed(delta * scale, 37)
                accumulator = signed(accumulator + signed(activation * weight, 69), 128)
            if projection < 3:
                accumulator = signed(accumulator +
                                     (half(self.get(4, 0, column, layer, projection)) << 16), 128)
            result.append(saturate(round_ratio(accumulator, 1 << 16)))
        return result

    def rotate(self, values, position):
        result = list(values)
        d = self.g.head_dim
        for base in range(0, len(values), d):
            for j in range(d // 2):
                cosine = signed(self.get(11, position, 2 * j), 32)
                sine = signed(self.get(11, position, 2 * j + 1), 32)
                x, y = values[base + j], values[base + j + d // 2]
                result[base + j] = saturate(round_ratio(x * cosine - y * sine, 1 << 30))
                result[base + j + d // 2] = saturate(round_ratio(y * cosine + x * sine, 1 << 30))
        return result

    def attention(self, query, layer, position):
        g = self.g
        result = []
        for head in range(g.query_heads):
            kv = head // (g.query_heads // g.kv_heads)
            scores = []
            for time in range(position + 1):
                dot = sum(query[head * g.head_dim + d] *
                          signed(self.get(9, time, kv * g.head_dim + d, layer), 32)
                          for d in range(g.head_dim))
                scores.append(round_ratio(signed(dot, 96), math.isqrt(g.head_dim << 32)))
            weights = [exponential(score - max(scores)) for score in scores]
            for d in range(g.head_dim):
                weighted = sum(signed(self.get(10, time, kv * g.head_dim + d, layer), 32) * weight
                               for time, weight in enumerate(weights))
                result.append(saturate(round_ratio(signed(weighted, 96), sum(weights))))
        return result

    def token(self, token_id, position):
        g = self.g
        hidden = [half(self.get(0, token_id, c)) for c in range(g.hidden)]
        self.put(8, 0, hidden, "embedding")
        for layer in range(g.layers):
            normalized = self.norm(hidden, 5, layer)
            self.put(8, 1, normalized, "input-norm")
            q, k, v = [self.gemv(normalized, p, layer) for p in range(3)]
            for slot, value in ((2, q), (3, k), (4, v)):
                self.put(8, slot, value, "qkv-projection")
            q, k = self.rotate(q, position), self.rotate(k, position)
            self.put(8, 2, q, "rope-q")
            self.put(8, 3, k, "rope-k")
            self.put(9, position, k, "cache-key", layer)
            self.put(10, position, v, "cache-value", layer)
            context = self.attention(q, layer, position)
            self.put(8, 5, context, "attention")
            attention = self.gemv(context, 3, layer)
            self.put(8, 6, attention, "attention-output")
            residual = [saturate(x + y) for x, y in zip(hidden, attention)]
            self.put(8, 7, residual, "attention-residual")
            normalized = self.norm(residual, 6, layer)
            self.put(8, 8, normalized, "post-attention-norm")
            gate, up = [self.gemv(normalized, p, layer) for p in (4, 5)]
            self.put(8, 9, gate, "gate")
            self.put(8, 10, up, "up")
            activated = [saturate(round_ratio(silu(x) * y, 1 << 16))
                         for x, y in zip(gate, up)]
            self.put(8, 11, activated, "swiglu")
            down = self.gemv(activated, 6, layer)
            self.put(8, 12, down, "down")
            hidden = [saturate(x + y) for x, y in zip(residual, down)]
            self.put(8, 0, hidden, "mlp-residual")
        final = self.norm(hidden, 7, 0)
        self.put(8, 14, final, "final-norm")
        logits = [saturate(round_ratio(sum(x * half(self.get(0, token, c))
                                            for c, x in enumerate(final)), 1 << 16))
                  for token in range(g.vocabulary)]
        self.logits.append(logits)
        return logits


CORE_BENCH = r"""
module bench;
  reg clk=0;
  reg rst_n;
  always #5 clk=~clk;
  reg token_valid=0,new_sequence=0,logit_ready=0;
  reg [31:0] token_id=0,token_pos=0;
  wire token_ready,logit_valid,done,error;
  wire [31:0] logit_index;
  wire signed [31:0] logit_data;
  wire mem_req_valid,mem_req_write,mem_rsp_ready;
  reg mem_req_ready=0,mem_rsp_valid=0,mem_rsp_error=0;
  wire [3:0] mem_req_kind;
  wire [2:0] mem_req_proj;
  wire [31:0] mem_req_layer,mem_req_row,mem_req_col,mem_req_wdata;
  reg [31:0] mem_rsp_rdata=0;
  anvil_q1_top #(@PARAMETERS@) dut(.*);
  localparam RECORDS=@RECORDS@,WRITES=@WRITES@,VOCAB=@VOCAB@,OPERATIONS=@OPERATIONS@;
  reg [31:0] memory[0:RECORDS-1],expected[0:WRITES-1];
  integer first[0:RECORDS-1],limit[0:RECORDS-1],count[0:RECORDS-1];
  reg writable[0:RECORDS-1];
  reg [31:0] expected_logits[0:VOCAB*OPERATIONS-1];
  reg [31:0] rng=@SEED@;
  integer cycles=0,requests=0,responses=0,write_count=0,logits=0,completions=0;
  integer request_stalls=0,logit_stalls=0,comparisons=0,delay_count=0;
  integer slot=0,pending_slot=0,accepted_cycle=0,active_operation=-1;
  reg pending=0,request_held=0,logit_held=0;
  reg [135:0] held_request;
  reg [63:0] held_logit;
  reg [11:0] kinds_seen=0;
  function automatic integer lookup(input [102:0] key);
    begin
      case (key)
        @LOOKUP@
        default: lookup=-1;
      endcase
    end
  endfunction
  task automatic reset_check;
    begin
      if ({token_ready,logit_valid,logit_index,logit_data,done,error,
           mem_req_valid,mem_req_write,mem_req_kind,mem_req_layer,mem_req_proj,
           mem_req_row,mem_req_col,mem_req_wdata,mem_rsp_ready}!==0)
        $fatal(1,"CORE_NUMERIC_RESET t=%0t",$time);
    end
  endtask
  always @(posedge clk or negedge clk) if (!rst_n) reset_check();
  always @(negedge clk) if (rst_n) begin
    rng=rng ^ (rng<<13); rng=rng ^ (rng>>17); rng=rng ^ (rng<<5);
    mem_req_ready=rng[0] && cycles%7!=0;
    logit_ready=rng[1] && cycles%5!=0;
    if (pending && !mem_rsp_valid) begin
      if (delay_count==0) begin mem_rsp_valid<=1; mem_rsp_rdata=memory[pending_slot]; end
      else delay_count=delay_count-1;
    end
  end
  always @(posedge clk) begin
    cycles=cycles+1;
    if (rst_n) begin
      if ((^{token_ready,logit_valid,logit_index,logit_data,done,error,
             mem_req_valid,mem_req_write,mem_req_kind,mem_req_layer,mem_req_proj,
             mem_req_row,mem_req_col,mem_req_wdata,mem_rsp_ready})===1'bx)
        $fatal(1,"CORE_NUMERIC_XZ");
      if (request_held && (!mem_req_valid ||
          {mem_req_write,mem_req_kind,mem_req_layer,mem_req_proj,
           mem_req_row,mem_req_col,mem_req_wdata}!==held_request))
        $fatal(1,"CORE_NUMERIC_REQUEST_STABILITY");
      if (logit_held && (!logit_valid || {logit_index,logit_data}!==held_logit))
        $fatal(1,"CORE_NUMERIC_LOGIT_STABILITY");
      request_held=mem_req_valid && !mem_req_ready;
      logit_held=logit_valid && !logit_ready;
      held_request={mem_req_write,mem_req_kind,mem_req_layer,mem_req_proj,
                    mem_req_row,mem_req_col,mem_req_wdata};
      held_logit={logit_index,logit_data};
      if (request_held) request_stalls=request_stalls+1;
      if (logit_held) logit_stalls=logit_stalls+1;
      if (mem_rsp_valid && mem_rsp_ready) begin
        if (!pending || cycles<=accepted_cycle) $fatal(1,"CORE_NUMERIC_ORPHAN_RESPONSE");
        pending=0; mem_rsp_valid<=0; responses=responses+1;
      end
      if (mem_req_valid && mem_req_ready) begin
        slot=lookup({mem_req_kind,mem_req_layer,mem_req_proj,mem_req_row,mem_req_col});
        if (pending || slot<0) $fatal(1,"CORE_NUMERIC_TENSOR_ADDRESS k=%0d l=%0d p=%0d r=%0d c=%0d",
          mem_req_kind,mem_req_layer,mem_req_proj,mem_req_row,mem_req_col);
        if (mem_req_write) begin
          if (!writable[slot] || count[slot]>=limit[slot] ||
              mem_req_wdata!==expected[first[slot]+count[slot]])
            $fatal(1,"CORE_NUMERIC_ACTIVATION slot=%0d occurrence=%0d expected=%h observed=%h",
                   slot,count[slot],expected[first[slot]+count[slot]],mem_req_wdata);
          count[slot]=count[slot]+1; write_count=write_count+1;
          memory[slot]=mem_req_wdata; comparisons=comparisons+1;
        end
        kinds_seen[mem_req_kind]=1;
        pending=1; pending_slot=slot; accepted_cycle=cycles; delay_count=1+rng[5:2];
        requests=requests+1;
      end
      if (token_valid && token_ready) begin
        if (active_operation!=completions-1 || logit_valid || pending)
          $fatal(1,"CORE_NUMERIC_TOKEN_OVERLAP");
        active_operation=active_operation+1;
      end
      if (logit_valid && logit_ready) begin
        if (logits>=VOCAB*OPERATIONS || logit_index!==32'(logits%VOCAB) ||
            logit_data!==expected_logits[logits] || active_operation!=logits/VOCAB)
          $fatal(1,"CORE_NUMERIC_LOGIT item=%0d expected=%h observed=%h index=%0d",
                 logits,expected_logits[logits],logit_data,logit_index);
        logits=logits+1; comparisons=comparisons+1;
      end
      if (done) begin
        if (error || logits!=(completions+1)*VOCAB || pending ||
            completions>=OPERATIONS || logit_valid)
          $fatal(1,"CORE_NUMERIC_COMPLETION error=%b logits=%0d",error,logits);
        completions=completions+1;
      end
    end
  end
  task automatic tick; begin @(posedge clk); #1; end endtask
  task automatic token(input integer id,input integer pos,input bit first_token);
    begin
      @(negedge clk); #1; token_id=id; token_pos=pos; new_sequence=first_token; token_valid=1;
      do begin @(posedge clk); end while (!token_ready);
      #1; @(negedge clk); #1; token_valid=0;
      while (completions<=pos) tick();
    end
  endtask
  integer i;
  initial begin
    rst_n=0; #0; reset_check();
    @VECTORS@
    repeat (2) tick(); @(negedge clk); #1; rst_n=1;
    @STIMULUS@
    repeat (20) tick();
    if (completions!=OPERATIONS || logits!=VOCAB*OPERATIONS ||
        write_count!=WRITES || requests!=responses || pending || error ||
        request_stalls==0 || logit_stalls==0 || kinds_seen!==12'hfff)
      $fatal(1,"CORE_NUMERIC_COUNTS done=%0d logits=%0d writes=%0d/%0d kinds=%h",
             completions,logits,write_count,WRITES,kinds_seen);
    for (i=0;i<RECORDS;i=i+1)
      if (count[i]!=limit[i]) $fatal(1,"CORE_NUMERIC_MISSING_WRITE slot=%0d",i);
    if (comparisons!=WRITES+VOCAB*OPERATIONS) $fatal(1,"CORE_NUMERIC_COMPARISONS");
    $display("CORE_NUMERIC requests=%0d writes=%0d logits=%0d completions=%0d",
             requests,write_count,logits,completions);
    $display("COMPARED %0d",comparisons); $finish;
  end
  initial begin repeat (20000000) @(posedge clk); $fatal(1,"CORE_NUMERIC_CYCLE_BOUND"); end
endmodule
"""


def core_test(evidence, geometry, seed, *, fault=None, bench_transform=None,
              runtime_inputs=True):
    reference = Reference(geometry, seed)
    tokens = [1, 2, 0]
    for position, token in enumerate(tokens):
        reference.token(token, position)
    if not any(value for frame in reference.logits for value in frame):
        raise RuntimeError("Nonzero-weight fixture accidentally produced only zero logits")
    label = f"numerical-h{geometry.hidden}-l{geometry.layers}-s{seed}"
    if fault:
        label += "-" + fault["name"]
    directory = evidence.path / (evidence.name_prefix + label + "-input")
    directory.mkdir()
    (directory / "reference.json").write_text(json.dumps({
        "geometry": geometry.__dict__, "seed": seed, "tokens": tokens,
        "initial": [{"key": key, "word": value} for key, value in sorted(reference.initial.items())],
        "write_trace": reference.trace, "logits": reference.logits,
        "fault": fault,
        "scope": "Independent synthetic integer reference; not official-model acceptance",
    }, indent=2) + "\n", encoding="ascii")
    vectors, lookup = [], []
    memory_records, expected_words = [], []
    total_writes = 0
    fault_slot = None
    for index, (key, value) in enumerate(sorted(reference.initial.items())):
        if fault and key == fault["key"]:
            fault_slot = index
            value = fault.get("word", value)
        kind, layer, projection, row, column = key
        encoded = (kind << 99) | (layer << 67) | (projection << 64) | (row << 32) | column
        lookup.append(f"103'h{encoded:x}: lookup={index};")
        expected = reference.writes[key]
        vectors.append(f"memory[{index}]=32'h{value:x}; first[{index}]={total_writes}; "
                       f"limit[{index}]={len(expected)}; count[{index}]=0; "
                       f"writable[{index}]={int(kind in (8, 9, 10))};")
        vectors.extend(f"expected[{total_writes+n}]=32'h{word:x};"
                       for n, word in enumerate(expected))
        memory_records.append(value | (total_writes << 32) | (len(expected) << 64)
                              | (int(kind in (8, 9, 10)) << 96))
        expected_words.extend(expected)
        total_writes += len(expected)
    vectors.extend(f"expected_logits[{i*geometry.vocabulary+j}]=32'h{value & 0xFFFFFFFF:x};"
                   for i, frame in enumerate(reference.logits) for j, value in enumerate(frame))
    parameters = {
        "NUM_LAYERS": geometry.layers, "HIDDEN_SIZE": geometry.hidden,
        "INTERMEDIATE_SIZE": geometry.intermediate, "NUM_Q_HEADS": geometry.query_heads,
        "NUM_KV_HEADS": geometry.kv_heads, "HEAD_DIM": geometry.head_dim,
        "GROUP_SIZE": geometry.group, "VOCAB_SIZE": geometry.vocabulary,
        "MAX_SEQ_LEN": geometry.sequence,
    }
    values = {
        "PARAMETERS": ",".join(f".{key}({value})" for key, value in parameters.items()),
        "RECORDS": len(reference.initial), "WRITES": total_writes,
        "VOCAB": geometry.vocabulary, "OPERATIONS": len(tokens), "SEED": seed,
        "LOOKUP": "\n".join(lookup), "VECTORS": "\n".join(vectors),
        "STIMULUS": "\n".join(f"token({token},{position},{int(position==0)});"
                              for position, token in enumerate(tokens)),
    }
    bench = CORE_BENCH
    for name, value in values.items():
        bench = bench.replace(f"@{name}@", str(value))
    if fault:
        assert fault_slot is not None
        bench = bench.replace("reg pending=0,request_held=0,logit_held=0;", """
  reg pending=0,request_held=0,logit_held=0;
  integer injected_responses=0;
""")
        response = "begin mem_rsp_valid<=1; mem_rsp_rdata=memory[pending_slot]; end"
        assert response in bench
        bench = bench.replace(response, f"""
begin
  mem_rsp_valid<=1; mem_rsp_rdata=memory[pending_slot];
  mem_rsp_error={int(fault.get("bus_error", False))} && pending_slot=={fault_slot};
  if (pending_slot=={fault_slot}) injected_responses=injected_responses+1;
end
""")
        begin = bench.index("        if (error || logits!=(completions+1)*VOCAB")
        end = bench.index("        completions=completions+1;", begin)
        bench = bench[:begin] + """
        if (error!==1 || logits!=0 || pending || completions!=0 ||
            injected_responses!=1 || active_operation!=0)
          $fatal(1,"CORE_EXPECTED_ERROR error=%b logits=%0d injected=%0d",
                 error,logits,injected_responses);
        comparisons=comparisons+1;
""" + bench[end:]
        # Retain the successful prefix comparisons before the injected error.
        original_stimulus = values["STIMULUS"]
        assert original_stimulus in bench
        bench = bench.replace(original_stimulus, "token(1,0,1);")
        begin = bench.index("    if (completions!=OPERATIONS")
        end = bench.index("    $display(\"CORE_NUMERIC requests=", begin)
        bench = bench[:begin] + """
    if (completions!=1 || logits!=0 || requests!=responses || pending ||
        error || done || token_ready!==1 || mem_req_valid)
      $fatal(1,"CORE_ERROR_SETTLEMENT done=%0d requests=%0d responses=%0d",
             completions,requests,responses);
    comparisons=comparisons+1;
""" + bench[end:]
    if runtime_inputs:
        # Array dimensions and typed-address lookup depend only on geometry.
        # Tensor contents, fault selection and traffic are case-local inputs.
        initialization = "\n".join((
            hex_input(evidence, directory, "initial_records", memory_records, 97),
            hex_input(evidence, directory, "expected", expected_words, 32),
            hex_input(evidence, directory, "expected_logits",
                      [value & 0xFFFFFFFF for frame in reference.logits for value in frame], 32),
            hex_input(evidence, directory, "token_words", tokens, 32),
            hex_input(evidence, directory, "fault_config",
                      [int(bool(fault)), fault_slot or 0,
                       int(bool(fault and fault.get("bus_error")))], 32),
            """for (i=0;i<RECORDS;i=i+1) begin
      memory[i]=initial_records[i][31:0]; first[i]=initial_records[i][63:32];
      limit[i]=initial_records[i][95:64]; writable[i]=initial_records[i][96]; count[i]=0;
    end""",
        ))
        # Start from the unmodified public scoreboard, making the error path a
        # runtime choice rather than a different compiled program for each fault.
        bench = CORE_BENCH
        runtime_values = dict(values, VECTORS=initialization)
        if bench_transform is None:
            runtime_values["STIMULUS"] = (
                "for (integer operation=0;operation<OPERATIONS;operation=operation+1) begin\n"
                "      if (!fault_config[0] || operation==0)\n"
                "        token(token_words[operation],operation,operation==0);\n"
                "    end")
        for name, value in runtime_values.items():
            bench = bench.replace(f"@{name}@", str(value))
        # Whole-vector accumulation keeps the mask shared with reset coroutines
        # in compiled simulation; it is the same accepted-kind bit union.
        bench = bench.replace("kinds_seen[mem_req_kind]=1;",
                              "kinds_seen=kinds_seen | (12'b1<<mem_req_kind);")
        bench = bench.replace("  reg [11:0] kinds_seen=0;", """  reg [11:0] kinds_seen=0;
  reg [96:0] initial_records[0:RECORDS-1];
  reg [31:0] token_words[0:OPERATIONS-1],fault_config[0:2];
  integer injected_responses=0;
""")
        response = "begin mem_rsp_valid<=1; mem_rsp_rdata=memory[pending_slot]; end"
        # Preserve the response anchor used by independent head-reuse controls.
        if bench_transform is None:
            bench = bench.replace(response, """
begin
  mem_rsp_valid<=1; mem_rsp_rdata=memory[pending_slot];
  mem_rsp_error=fault_config[0] && fault_config[2] && pending_slot==fault_config[1];
  if (fault_config[0] && pending_slot==fault_config[1])
    injected_responses=injected_responses+1;
end
""")
        begin = bench.index("        if (error || logits!=(completions+1)*VOCAB")
        end = bench.index("        completions=completions+1;", begin)
        success = bench[begin:end]
        bench = bench[:begin] + """
        if (fault_config[0]) begin
          if (error!==1 || logits!=0 || pending || completions!=0 ||
              injected_responses!=1 || active_operation!=0)
            $fatal(1,"CORE_EXPECTED_ERROR error=%b logits=%0d injected=%0d",
                   error,logits,injected_responses);
          comparisons=comparisons+1;
        end else begin
""" + success + "        end\n" + bench[end:]
        begin = bench.index("    if (completions!=OPERATIONS")
        end = bench.index('    $display("CORE_NUMERIC requests=', begin)
        success = bench[begin:end]
        bench = bench[:begin] + """
    if (fault_config[0]) begin
      if (completions!=1 || logits!=0 || requests!=responses || pending ||
          error || done || token_ready!==1 || mem_req_valid)
        $fatal(1,"CORE_ERROR_SETTLEMENT done=%0d requests=%0d responses=%0d",
               completions,requests,responses);
      comparisons=comparisons+1;
    end else begin
""" + success + "    end\n" + bench[end:]
    root = Path(__file__).resolve().parent.parent
    if bench_transform is not None:
        bench = bench_transform(bench)
    return evidence.simulate(label, bench, [
        "rtl/anvil_edge_numeric_pkg.sv",
        *[str(path.relative_to(root)) for path in sorted((root / "rtl").glob("*.sv"))
          if path.name != "anvil_edge_numeric_pkg.sv"],
    ], None if fault else total_writes + len(tokens) * geometry.vocabulary)


def nonlinear_test(evidence, unit, seed):
    rng = random.Random(seed)
    width, model = (64, exponential) if unit == "exp_q24" else (32, silu)
    low, high = -(1 << (width - 1)), (1 << (width - 1)) - 1
    values = [low, high, 0, -1, 1, -32768, 32768, -65536, 65536,
              -1048577, -1048576, -1048575, 1048576]
    values += [rng.randint(low, high) for _ in range(16)]
    values += [rng.randint(-1048576, 0) for _ in range(16)]
    vectors = "\n".join(
        f"transaction({width}'h{x & ((1 << width)-1):x},32'h{model(x) & 0xFFFFFFFF:x});"
        for x in values)
    bench = r"""
module bench;
  reg clk=0;
  reg rst_n;
  always #5 clk=~clk;
  reg in_valid=0,out_ready=0;
  reg signed [@WIDTH@-1:0] x=0;
  wire in_ready,out_valid,arithmetic_error;
  wire [31:0] value;
  anvil_edge_@UNIT@ dut(.*);
  integer comparisons=0;
  task automatic reset_check;
    begin
      if ({in_ready,out_valid,arithmetic_error,value}!==0)
        $fatal(1,"NONLINEAR_RESET");
    end
  endtask
  always @(posedge clk or negedge clk) begin
    if (!rst_n) reset_check();
    if ((^{in_ready,out_valid,arithmetic_error,value})===1'bx)
      $fatal(1,"NONLINEAR_XZ");
  end
  task automatic tick; begin @(posedge clk); #1; end endtask
  task automatic transaction(input signed [@WIDTH@-1:0] operand,input [31:0] expected);
    begin
      @(negedge clk); #1; x=operand; in_valid=1;
      if (in_ready!==1 || out_valid!==0) $fatal(1,"NONLINEAR_IDLE");
      @(posedge clk);
      if (out_valid!==0) $fatal(1,"NONLINEAR_E0");
      #1; @(negedge clk); #1; in_valid=0;
      while (!out_valid) tick();
      repeat (7) begin
        if (out_valid!==1 || in_ready!==0 || value!==expected || arithmetic_error!==0)
          $fatal(1,"NONLINEAR_VALUE input=%h expected=%h observed=%h",operand,expected,value);
        tick();
      end
      @(negedge clk); #1; out_ready=1; tick();
      if (out_valid!==0) $fatal(1,"NONLINEAR_RETIRE");
      @(negedge clk); #1; out_ready=0;
      comparisons=comparisons+1;
    end
  endtask
  initial begin
    rst_n=0; #0; reset_check();
    repeat (2) tick(); @(negedge clk); #1; rst_n=1;
    @VECTORS@
    @(negedge clk); #1; x=-12345; in_valid=1; tick();
    @(negedge clk); #1; in_valid=0; rst_n=0;
    #0; reset_check(); repeat (2) tick();
    @(negedge clk); #1; rst_n=1;
    repeat (1000) begin tick(); if (out_valid!==0) $fatal(1,"NONLINEAR_RESET_STALE"); end
    if (comparisons!=@COUNT@) $fatal(1,"NONLINEAR_COUNTS");
    $display("COMPARED %0d",comparisons); $finish;
  end
  initial begin repeat (200000) @(posedge clk); $fatal(1,"NONLINEAR_CYCLE_BOUND"); end
endmodule
"""
    for key, value in {"WIDTH": width, "UNIT": unit, "VECTORS": vectors,
                       "COUNT": len(values)}.items():
        bench = bench.replace(f"@{key}@", str(value))
    evidence.simulate(f"numerical-{unit}-s{seed}", bench, [
        "rtl/anvil_edge_numeric_pkg.sv", "rtl/anvil_edge_unsigned_divider.sv",
        "rtl/anvil_edge_signed_multiplier.sv", "rtl/anvil_edge_exp_q24.sv",
        "rtl/anvil_edge_silu_q16.sv",
    ], len(values))


def run_numerical(evidence):
    evidence.tools(("iverilog", "vvp"))
    for seed in (1, 17, 89):
        nonlinear_test(evidence, "exp_q24", seed)
        nonlinear_test(evidence, "silu_q16", seed)
        core_test(evidence, Geometry(), seed)
        core_test(evidence, Geometry(layers=2, hidden=16, intermediate=24, query_heads=2), seed)
    run_numerical_errors(evidence)


def run_numerical_errors(evidence):
    evidence.tools(("iverilog", "vvp"))
    faults = [
        {"name": "embedding-nan", "key": (0, 0, 0, 1, 0), "word": 0x7E00},
        {"name": "embedding-positive-inf", "key": (0, 0, 0, 1, 0), "word": 0x7C00},
        {"name": "embedding-negative-inf", "key": (0, 0, 0, 1, 0), "word": 0xFC00},
        {"name": "scale-negative", "key": (3, 0, 0, 0, 0), "word": 0xBC00},
        {"name": "scale-negative-subnormal", "key": (3, 0, 0, 0, 0), "word": 0x8001},
        {"name": "scale-nan", "key": (3, 0, 0, 0, 0), "word": 0x7E01},
        {"name": "scale-inf", "key": (3, 0, 0, 0, 0), "word": 0x7C00},
        {"name": "bias-inf", "key": (4, 0, 0, 0, 0), "word": 0xFC00},
        {"name": "input-gamma-nan", "key": (5, 0, 0, 0, 0), "word": 0x7E00},
        {"name": "post-gamma-nan", "key": (6, 0, 0, 0, 0), "word": 0x7E00},
        {"name": "final-gamma-nan", "key": (7, 0, 0, 0, 0), "word": 0x7E00},
        {"name": "read-response-error", "key": (0, 0, 0, 1, 0), "bus_error": True},
        {"name": "write-response-error", "key": (8, 0, 0, 0, 0), "bus_error": True},
    ]
    for seed in (1, 17, 89):
        for fault in faults:
            core_test(evidence, Geometry(), seed, fault=fault)
