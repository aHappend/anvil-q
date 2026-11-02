"""Dense generated decoder fixtures and public-pin architectural scoreboards."""

import math
import random
from fractions import Fraction

from reference import (
    as_fraction, approximation_interval, bits32, decode, f32, mx_decode,
    round_dyadic,
)


GEOMETRIES = (
    (1, 8, 8, 1, 1, 8, 1, 1, 1),
    (2, 56, 64, 7, 1, 8, 8, 17, 3),
    (2, 112, 128, 14, 2, 8, 8, 17, 5),
)


def bf16(value):
    bits = bits32(value)
    _, sign, n, exponent = decode(bits)
    return round_dyadic(-n if sign else n, exponent, 7, bool(sign))[0]


def quantize_group(values):
    """Exhaustive nearest-code search on exact rationals, independently of RTL."""
    numbers = [as_fraction(value, 7) for value in values]
    largest = max(map(abs, numbers), default=Fraction(0))
    scale = next((s for s in range(255) if largest <= 448 * Fraction(2) ** (s - 127)), 254)
    candidates = [
        (code, as_fraction(mx_decode(code, scale)[0], 7))
        for code in range(127)
    ]
    codes = []
    for original, number in zip(values, numbers):
        magnitude = abs(number)
        code = min(candidates, key=lambda pair: (abs(pair[1] - magnitude), pair[0] & 1))[0]
        codes.append(code | (128 if original & 0x8000 else 0))
    return codes, scale


def rounded_vector(values, mx):
    encoded = [bf16(value) for value in values]
    if mx:
        result = []
        for first in range(0, len(encoded), 32):
            codes, scale = quantize_group(encoded[first:first + 32])
            result.extend(f32(mx_decode(code, scale)[0] << 16) for code in codes)
        return result
    return [f32(value << 16) for value in encoded]


class Fixture:
    def __init__(self, geometry, seed, mx):
        self.geometry, self.seed, self.mx = geometry, seed, mx
        layers, hidden, intermediate, queries, kvheads, dimension, _, vocab, sequence = geometry
        rng = random.Random(seed)
        self.raw = {}
        self.decoded = {}
        self.beats = []
        self.planes = {}

        def table(kind, layer, proj, rows, columns, magnitude):
            values = [
                [bf16(rng.randint(-15, 15) * magnitude) for _ in range(columns)]
                for _ in range(rows)
            ]
            self.raw[kind, layer, proj] = values
            data, scales, decoded = [], [], []
            width = 64 if mx else 32
            for row in values:
                codes, scale_bytes, decoded_row = [], [], []
                if mx:
                    for first in range(0, columns, 32):
                        group, scale = quantize_group(row[first:first + 32])
                        codes.extend(group)
                        scale_bytes.append(scale)
                        decoded_row.extend(f32(mx_decode(code, scale)[0] << 16) for code in group)
                else:
                    codes, decoded_row = row, [f32(value << 16) for value in row]
                decoded.append(decoded_row)
                for first in range(0, columns, width):
                    data.append(sum(value << ((8 if mx else 16) * lane)
                                    for lane, value in enumerate(codes[first:first + width])))
                if mx:
                    for first in range(0, len(scale_bytes), 64):
                        scales.append(sum(value << (8 * lane) for lane, value in
                                          enumerate(scale_bytes[first:first + 64])))
            self.decoded[kind, layer, proj] = decoded
            self.add_plane(kind, layer, proj, False, rows, columns, data)
            if mx:
                self.add_plane(kind, layer, proj, True, rows, columns, scales)

        table(0, 0, 0, vocab, hidden, 1 / 64)
        for layer in range(layers):
            for proj, inputs, outputs in (
                (0, hidden, hidden), (1, hidden, kvheads * dimension),
                (2, hidden, kvheads * dimension), (3, hidden, hidden),
                (4, hidden, intermediate), (5, hidden, intermediate),
                (6, intermediate, hidden),
            ):
                table(12, layer, proj, inputs, outputs, 1 / (64 * math.sqrt(inputs)))
            for kind in (9, 10):
                columns = kvheads * dimension
                self.add_plane(kind, layer, 0, False, sequence, columns,
                               [0] * (sequence * ((columns + (63 if mx else 31)) //
                                                  (64 if mx else 32))))
                if mx:
                    self.add_plane(kind, layer, 0, True, sequence, columns,
                                   [0] * (sequence * ((columns + 2047) // 2048)))
        self.gamma = {
            (kind, layer): [bf16(1 + rng.randint(-3, 3) / 32) for _ in range(hidden)]
            for kind in (5, 6, 7) for layer in (range(layers) if kind != 7 else (0,))
        }
        self.bias = {
            (layer, proj): [bf16(rng.randint(-7, 7) / 1024) for _ in range(
                hidden if proj == 0 else kvheads * dimension)]
            for layer in range(layers) for proj in (0, 1, 2)
        }

    def add_plane(self, kind, layer, proj, scale, rows, columns, data):
        stride = ((columns + 2047) // 2048) if scale else (
            columns + (63 if self.mx else 31)) // (64 if self.mx else 32)
        assert len(data) == rows * stride
        self.planes[kind, layer, proj, scale] = (len(self.beats), rows, columns, stride)
        self.beats.extend(data)

    def expected_tokens(self, count):
        layers, hidden, intermediate, queries, kvheads, dimension, _, vocab, _ = self.geometry
        history = {}
        results = []
        eps = f32(0x358637BD)

        def norm(vector, kind, layer):
            factor = math.sqrt(sum(value * value for value in vector) / len(vector) + eps)
            gamma = self.gamma[kind, layer if kind != 7 else 0]
            return [value * f32(g << 16) / factor for value, g in zip(vector, gamma)]

        def project(vector, layer, proj, head=False):
            vector = rounded_vector(vector, self.mx)
            weights = self.decoded[(0, 0, 0) if head else (12, layer, proj)]
            if head:
                return [sum(x * w for x, w in zip(vector, row)) for row in weights]
            outputs = len(weights[0])
            biases = self.bias.get((layer, proj))
            return [sum(vector[i] * weights[i][j] for i in range(len(vector))) +
                    (f32(biases[j] << 16) if biases is not None else 0)
                    for j in range(outputs)]

        def rotate(vector, position):
            out = vector[:]
            for base in range(0, len(vector), dimension):
                for j in range(dimension // 2):
                    angle = position * 1000000 ** (-2 * j / dimension)
                    left, right = vector[base + j], vector[base + j + dimension // 2]
                    out[base + j] = left * math.cos(angle) - right * math.sin(angle)
                    out[base + j + dimension // 2] = right * math.cos(angle) + left * math.sin(angle)
            return out

        for position in range(count):
            vector = self.decoded[0, 0, 0][position % vocab][:]
            for layer in range(layers):
                normalized = norm(vector, 5, layer)
                query = rotate(project(normalized, layer, 0), position)
                key = rotate(project(normalized, layer, 1), position)
                value = project(normalized, layer, 2)
                history[layer, position] = (
                    rounded_vector(key, self.mx), rounded_vector(value, self.mx))
                query = rounded_vector(query, False)
                attention = []
                for head in range(queries):
                    first = (head // (queries // kvheads)) * dimension
                    q = query[head * dimension:(head + 1) * dimension]
                    scores = [
                        sum(q[j] * history[layer, t][0][first + j] for j in range(dimension)) /
                        math.sqrt(dimension) for t in range(position + 1)
                    ]
                    maximum = max(scores)
                    probabilities = [math.exp(score - maximum) for score in scores]
                    total = sum(probabilities)
                    attention.extend(
                        sum(probabilities[t] * history[layer, t][1][first + j]
                            for t in range(position + 1)) / total
                        for j in range(dimension))
                residual = [x + y for x, y in zip(vector, project(attention, layer, 3))]
                normalized = norm(residual, 6, layer)
                gate, up = project(normalized, layer, 4), project(normalized, layer, 5)
                activated = [g * u / (1 + math.exp(-g)) for g, u in zip(gate, up)]
                vector = [x + y for x, y in zip(residual, project(activated, layer, 6))]
            results.append(project(norm(vector, 7, 0), 0, 0, True))
        return results


def top_tb(fixture, stem, relative, tokens, cycle_limit):
    layers, hidden, intermediate, queries, kvheads, dimension, group, vocab, sequence = fixture.geometry
    table_cases = []
    for (kind, layer, proj, scale), (base, rows, columns, stride) in fixture.planes.items():
        key = (kind << 16) | (layer << 8) | (proj << 1) | int(scale)
        shift = 6 if scale or fixture.mx else 5
        table_cases.append(f"""
        32'h{key:08x}: begin
          if (row>={rows} || (col>>{shift})>={stride})
            $fatal(1,"DDR row/column outside tensor");
          address={base}+row*{stride}+(col>>{shift});
        end""")
    scalar_cases = []
    configuration = []
    for (kind, layer), values in fixture.gamma.items():
        for col, value in enumerate(values):
            key = (kind << 24) | (layer << 16) | col
            scalar_cases.append(f"32'h{key:08x}: scalar=configuration[{len(configuration)}];")
            configuration.append(value)
    for (layer, proj), values in fixture.bias.items():
        for col, value in enumerate(values):
            key = (4 << 24) | (layer << 16) | (proj << 12) | col
            scalar_cases.append(f"32'h{key:08x}: scalar=configuration[{len(configuration)}];")
            configuration.append(value)
    rope_cases = []
    for position in range(tokens):
        for col in range(dimension):
            angle = position * 1000000 ** (-2 * (col // 2) / dimension)
            value = bits32(math.sin(angle) if col & 1 else math.cos(angle))
            rope_cases.append(
                f"{position*dimension+col}: scalar=configuration[{len(configuration)}];")
            configuration.append(value)
    with (fixture.output_path / "configuration.hex").open("x") as output:
        output.write("".join(f"{word:08x}\n" for word in configuration))
    return f"""`timescale 1ns/1ps
module tb;
  reg clk=0,rst_n=0,token_valid=0,new_sequence=0,logit_ready=0;
  reg [31:0] token_id=0,token_pos=0;
  reg [1:0] precision_mode=2'd{3 if fixture.mx else 1};
  wire token_ready,logit_valid,done,error;
  wire [31:0] logit_index,logit_data;
  wire mem_req_valid,mem_req_write,mem_rsp_ready;
  wire [3:0] mem_req_kind;
  wire [31:0] mem_req_layer,mem_req_row,mem_req_col,mem_req_wdata;
  wire [2:0] mem_req_proj;
  reg mem_req_ready=0,mem_rsp_valid=0,mem_rsp_error=0;
  reg [31:0] mem_rsp_rdata=0;
  wire ddr_req_valid,ddr_req_write,ddr_req_id,ddr_req_scale,ddr_rsp_ready;
  wire [3:0] ddr_req_kind;
  wire [31:0] ddr_req_layer,ddr_req_row,ddr_req_col;
  wire [2:0] ddr_req_proj;
  wire [511:0] ddr_req_wdata;
  wire [63:0] ddr_req_wstrb;
  reg ddr_req_ready=0,ddr_rsp_valid=0,ddr_rsp_id=0,ddr_rsp_error=0;
  reg [511:0] ddr_rsp_rdata=0;
  reg csr_req_valid=0,csr_req_write=0,csr_rsp_ready=0;
  reg [11:0] csr_req_addr=0;
  reg [31:0] csr_req_wdata=0;
  reg [3:0] csr_req_wstrb=0;
  wire csr_req_ready,csr_rsp_valid,csr_rsp_error;
  wire [31:0] csr_rsp_rdata;
  always #5 clk=~clk;
  anvil_q1_fp2_top #(
    .NUM_LAYERS({layers}),.HIDDEN_SIZE({hidden}),.INTERMEDIATE_SIZE({intermediate}),
    .NUM_Q_HEADS({queries}),.NUM_KV_HEADS({kvheads}),.HEAD_DIM({dimension}),
    .GROUP_SIZE({group}),.VOCAB_SIZE({vocab}),.MAX_SEQ_LEN({sequence})) dut(.*);
  reg [511:0] memory[0:{len(fixture.beats)-1}];
  reg [31:0] configuration[0:{len(configuration)-1}];
  string fixture_root;
  reg [31:0] lower[0:{tokens*vocab-1}],upper[0:{tokens*vocab-1}];
  reg [31:0] expected_lo,expected_hi;
  reg occupied[0:1];
  reg [511:0] response[0:1];
  integer delay_count[0:1],scalar_delay=0;
  reg scalar_pending=0;
  reg [31:0] scalar_payload=0;
  reg [31:0] rng=0;
  reg held_logit=0,held_req=0;
  reg [63:0] held_logit_payload;
  reg [681:0] held_req_payload;
  integer cycle=0,position,j,byte_index,address_index,compared=0,received=0;
  integer requests=0,read_bytes=0,write_bytes=0,two_slots=0,reordered=0;
  integer output_stalls=0,request_stalls=0,completed=0,fixture_fd,scan;
  integer csr_issued=0,csr_compared=0,csr_accept_edge=-1,csr_overlap=0;
  reg csr_pending=0,csr_expected_error=0,csr_running=1;
  reg [31:0] csr_expected_data=0;
  function [31:0] ordered(input [31:0] value);
    ordered=value[31] ? ~value : value^32'h80000000;
  endfunction
  function integer address(input [3:0] kind,input [31:0] layer,
    input [2:0] proj,input scale,input [31:0] row,col);
    begin
      case (({{28'd0,kind}}<<16)|(layer<<8)|({{29'd0,proj}}<<1)|scale)
        {"".join(table_cases)}
        default: $fatal(1,"unmapped DDR tensor %0d/%0d/%0d/%0d",kind,layer,proj,scale);
      endcase
    end
  endfunction
  function [31:0] scalar(input [3:0] kind,input [31:0] layer,
    input [2:0] proj,input [31:0] row,col);
    begin
      scalar=0;
      if (kind==11) begin
        if (layer!=0 || proj!=0 || col>={dimension} || row>={tokens})
          $fatal(1,"RoPE table indexing");
        case (row*{dimension}+col)
          {" ".join(rope_cases)}
          default: $fatal(1,"RoPE coefficient absent");
        endcase
      end else begin
        if (row!=0) $fatal(1,"scalar row must be zero");
        case (({{28'd0,kind}}<<24)|(layer<<16)|({{29'd0,proj}}<<12)|col)
          {" ".join(scalar_cases)}
          default: $fatal(1,"optimized scalar weight/KV or unmapped configuration request");
        endcase
      end
    end
  endfunction
  task reset_check;
    if ({{token_ready,logit_valid,logit_index,logit_data,done,error,
      mem_req_valid,mem_req_write,mem_req_kind,mem_req_layer,mem_req_proj,
      mem_req_row,mem_req_col,mem_req_wdata,mem_rsp_ready,ddr_req_valid,
      ddr_req_write,ddr_req_id,ddr_req_scale,ddr_req_kind,ddr_req_layer,ddr_req_proj,
      ddr_req_row,ddr_req_col,ddr_req_wdata,ddr_req_wstrb,ddr_rsp_ready,
      csr_req_ready,csr_rsp_valid,csr_rsp_rdata,csr_rsp_error}} !== 0)
      $fatal(1,"public reset mismatch");
  endtask
  task tick;
    reg req_transfer,rsp_transfer,scalar_req_transfer,scalar_rsp_transfer;
    reg output_transfer,token_transfer,finished;
    reg csr_request_transfer,csr_response_transfer;
    integer chosen;
    begin
      cycle=cycle+1;
      if (cycle>{cycle_limit}) $fatal(1,"architectural cycle watchdog");
      rng=rng^(rng<<13); rng=rng^(rng>>17); rng=rng^(rng<<5);
      ddr_req_ready=rng[2:0]!=0 && cycle%23>=3;
      mem_req_ready=!scalar_pending && !mem_rsp_valid && rng[3:0]!=0;
      logit_ready=cycle%17>=4 && rng[4:2]!=0;
      csr_req_valid=csr_running && !csr_pending && cycle%13==0;
      csr_req_addr=csr_issued[0] ? 12'h003 : 12'h000;
      csr_rsp_ready=cycle%11>=4 && rng[6:4]!=0;
      if (!ddr_rsp_valid) begin
        chosen=-1;
        if (occupied[1] && delay_count[1]==0) chosen=1;
        else if (occupied[0] && delay_count[0]==0) chosen=0;
        if (chosen>=0) begin
          ddr_rsp_valid=1; ddr_rsp_id=chosen; ddr_rsp_rdata=response[chosen];
          if (chosen==1 && occupied[0]) reordered=reordered+1;
        end
      end
      if (!mem_rsp_valid && scalar_pending && scalar_delay==0) begin
        mem_rsp_valid=1; mem_rsp_rdata=scalar_payload;
      end
      #1;
      if ((^{{token_ready,logit_valid,done,error,mem_req_valid,mem_rsp_ready,
        ddr_req_valid,ddr_rsp_ready,csr_req_ready,csr_rsp_valid}})===1'bx)
        $fatal(1,"active control X/Z");
      req_transfer=ddr_req_valid && ddr_req_ready;
      rsp_transfer=ddr_rsp_valid && ddr_rsp_ready;
      scalar_req_transfer=mem_req_valid && mem_req_ready;
      scalar_rsp_transfer=mem_rsp_valid && mem_rsp_ready;
      output_transfer=logit_valid && logit_ready;
      token_transfer=token_valid && token_ready;
      csr_request_transfer=csr_req_valid && csr_req_ready;
      csr_response_transfer=csr_rsp_valid && csr_rsp_ready;
      finished=done;
      if (csr_rsp_valid) begin
        if (!csr_pending || cycle<=csr_accept_edge+1 ||
            {{csr_rsp_rdata,csr_rsp_error}} !== {{csr_expected_data,csr_expected_error}})
          $fatal(1,"architectural CSR latency/value/error mismatch");
      end
      if (error) $fatal(1,"nontrivial finite token failed");
      if (held_logit && ({{logit_valid,logit_index,logit_data}} !==
        {{1'b1,held_logit_payload}})) $fatal(1,"logit changed under stall");
      if (held_req && ({{ddr_req_valid,ddr_req_write,ddr_req_id,ddr_req_scale,
          ddr_req_kind,ddr_req_layer,ddr_req_proj,ddr_req_row,ddr_req_col,
          ddr_req_wdata,ddr_req_wstrb}} !== {{1'b1,held_req_payload}}))
        $fatal(1,"DDR request changed under stall");
      held_req=ddr_req_valid && !ddr_req_ready;
      held_req_payload={{ddr_req_write,ddr_req_id,ddr_req_scale,ddr_req_kind,
        ddr_req_layer,ddr_req_proj,ddr_req_row,ddr_req_col,ddr_req_wdata,ddr_req_wstrb}};
      held_logit=logit_valid && !logit_ready;
      held_logit_payload={{logit_index,logit_data}};
      if (held_logit) output_stalls=output_stalls+1;
      if (held_req) request_stalls=request_stalls+1;
      if (logit_valid) begin
        if ((^logit_data)===1'bx || received>={vocab} || logit_index!==received)
          $fatal(1,"logit count/index/XZ");
        if (ordered(logit_data)<ordered(lower[position*{vocab}+received]) ||
            ordered(logit_data)>ordered(upper[position*{vocab}+received]))
          $fatal(1,"ARCH NUMERICAL token=%0d logit=%0d got=%h expected=[%h,%h]",
            position,received,logit_data,
            lower[position*{vocab}+received],upper[position*{vocab}+received]);
      end
      @(posedge clk);
      if (output_transfer) begin received=received+1; compared=compared+1; end
      if (finished) begin
        if (received!={vocab}) $fatal(1,"premature done");
        completed=completed+1;
      end
      if (csr_response_transfer) begin
        csr_pending=0; csr_compared=csr_compared+1;
        if (rsp_transfer || scalar_rsp_transfer) csr_overlap=csr_overlap+1;
      end
      if (csr_request_transfer) begin
        if (csr_pending) $fatal(1,"architectural CSR duplicate ownership");
        csr_pending=1; csr_accept_edge=cycle;
        csr_expected_error=csr_issued[0];
        csr_expected_data=csr_issued[0] ? 32'd0 : 32'h02020002;
        csr_issued=csr_issued+1;
      end
      if (rsp_transfer) begin occupied[ddr_rsp_id]=0; end
      if (req_transfer) begin
        if (occupied[ddr_req_id]) $fatal(1,"DDR ID reused before response");
        address_index=address(ddr_req_kind,ddr_req_layer,ddr_req_proj,
          ddr_req_scale,ddr_req_row,ddr_req_col);
        if ((^ddr_req_wstrb)===1'bx || (^ddr_req_wdata)===1'bx)
          $fatal(1,"DDR request X/Z");
        if (ddr_req_write) begin
          if (ddr_req_kind!=9 && ddr_req_kind!=10) $fatal(1,"external scratchpad write");
          for (byte_index=0;byte_index<64;byte_index=byte_index+1)
            if (ddr_req_wstrb[byte_index]) begin
              memory[address_index][8*byte_index+:8]=ddr_req_wdata[8*byte_index+:8];
              write_bytes=write_bytes+1;
            end
        end else begin
          if (ddr_req_wstrb!==0) $fatal(1,"read write-strobes");
          read_bytes=read_bytes+64;
        end
        occupied[ddr_req_id]=1; response[ddr_req_id]=memory[address_index];
        delay_count[ddr_req_id]=3+(rng[7:4]);
        requests=requests+1;
      end
      if (scalar_rsp_transfer) scalar_pending=0;
      if (scalar_req_transfer) begin
        if (mem_req_write || scalar_pending) $fatal(1,"scalar ownership/write");
        scalar_payload=scalar(mem_req_kind,mem_req_layer,mem_req_proj,mem_req_row,mem_req_col);
        scalar_pending=1; scalar_delay=2+rng[5:4];
      end
      #1;
      if (csr_rsp_valid !== (csr_pending && cycle>csr_accept_edge))
        $fatal(1,"architectural CSR registered response latency");
      if (token_transfer) token_valid=0;
      if (rsp_transfer) ddr_rsp_valid=0;
      if (scalar_rsp_transfer) mem_rsp_valid=0;
      if (occupied[0] && occupied[1]) two_slots=two_slots+1;
      for (j=0;j<2;j=j+1)
        if (occupied[j] && delay_count[j]>0) delay_count[j]=delay_count[j]-1;
      if (scalar_pending && scalar_delay>0) scalar_delay=scalar_delay-1;
      @(negedge clk);
    end
  endtask
  initial begin
    occupied[0]=0; occupied[1]=0;
    delay_count[0]=0; delay_count[1]=0;
    #1; reset_check(); @(posedge clk); reset_check();
    #1; reset_check(); @(negedge clk); reset_check();
    if (!$value$plusargs("fixture=%s",fixture_root) || !$value$plusargs("seed=%d",rng))
      $fatal(1,"missing fixture/seed arguments");
    $readmemh({{fixture_root,"/checkpoint-images/memory.hex"}},memory);
    $readmemh({{fixture_root,"/configuration.hex"}},configuration);
    fixture_fd=$fopen({{fixture_root,"/expected.txt"}},"r");
    if (!fixture_fd) $fatal(1,"expected fixture open");
    for (j=0;j<{tokens*vocab};j=j+1) begin
      scan=$fscanf(fixture_fd,"%h %h\\n",expected_lo,expected_hi);
      if (scan!=2) $fatal(1,"expected fixture malformed");
      lower[j]=expected_lo; upper[j]=expected_hi;
    end
    rst_n=1;
    for (position=0;position<{tokens};position=position+1) begin
      token_id=position%{vocab}; token_pos=position; new_sequence=position==0;
      received=0; token_valid=1;
      while (token_valid) tick();
      while (completed<=position) tick();
    end
    csr_running=0;
    while (csr_pending) tick();
    if (compared!={tokens*vocab} || requests==0 || write_bytes==0 || csr_compared==0 ||
        csr_issued!=csr_compared ||
        request_stalls==0) $fatal(1,"architectural coverage absent");
    $display("SUMMARY architecture: tokens=%0d logits=%0d cycles=%0d read_bytes=%0d write_bytes=%0d two_slots=%0d reordered=%0d output_stalls=%0d csr_compared=%0d csr_memory_overlap=%0d",
      completed,compared,cycle,read_bytes,write_bytes,two_slots,reordered,output_stalls,
      csr_compared,csr_overlap);
    $finish;
  end
endmodule
"""


def simulate_architecture(run, seed, geometry, mx, simulator, compile_and_run, root, tokens=None):
    tokens = min(3, geometry[-1]) if tokens is None else tokens
    if simulator == "iverilog" and (geometry[1] > 32 or tokens > 1):
        simulator = "verilator"
    stem = f"architecture-h{geometry[1]}-{'mx' if mx else 'bf16'}-{seed}-{simulator}"
    directory = run.path / stem
    directory.mkdir()
    fixture = Fixture(geometry, seed, mx)
    fixture.output_path = directory
    images = directory / "checkpoint-images"
    images.mkdir()
    with (images / "memory.hex").open("x") as output:
        output.write("".join(f"{beat:0128x}\n" for beat in fixture.beats))
    expected = fixture.expected_tokens(tokens)
    quantization_drift = None
    if mx:
        original_expected = Fixture(geometry, seed, False).expected_tokens(tokens)
        differences = [abs(quantized - original)
                       for quantized_row, original_row in zip(expected, original_expected)
                       for quantized, original in zip(quantized_row, original_row)]
        quantization_drift = {
            "compared_logits": len(differences),
            "maximum_absolute": max(differences),
            "mean_absolute": sum(differences) / len(differences),
            "reference": "independent decoded-MX mathematical model versus original BF16 model",
        }
    with (directory / "expected.txt").open("x") as output:
        for vector in expected:
            for value in vector:
                low, high = approximation_interval(value, 0.02)
                output.write(f"{low:08x} {high:08x}\n")
    bench = directory / "tb.sv"
    bench.write_text(top_tb(fixture, stem, run.relative, tokens,
                            500000 if simulator == "iverilog" else 10000000))
    sources = [str(path.relative_to(root)) for pattern in (
        "anvil_q1_fp_reference/rtl/*.sv", "rtl/*.sv") for path in sorted(root.glob(pattern))]
    compile_and_run(
        run, directory, bench, sources, simulator, stem,
        arguments=[f"+fixture={run.relative / stem}", f"+seed={seed}"], cache=True,
    )
    run.receipt["comparisons"].append({
        "kind": "architecture", "seed": seed, "geometry": geometry,
        "format": "mx" if mx else "bf16", "tokens": tokens,
        "logits": tokens * geometry[-2], "simulator": simulator, "result": "passed",
        "quantization_drift": quantization_drift,
    })
