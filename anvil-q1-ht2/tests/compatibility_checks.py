"""Separate compilation of parent and delivered compatibility entry points.

The immutable parent is a compatibility comparator only. It is not the native
floating-point numerical oracle or evidence that HT2 has been accepted.
"""

from fractions import Fraction
import re
import uuid

from decoder_reference import Geometry, Image
from evidence import ROOT, relative, write_json
from integration_checks import CSR_TASK, MEMORY, TOP_PINS
import ieee_reference as fp
from leaf_checks import simulate


class ParentImage(Image):
    def panel(self, matrix):
        rows, columns = len(matrix), len(matrix[0])
        return self.halfwords([
            matrix[row][column]
            for panel in range((rows + 63) // 64)
            for column in range(columns)
            for row in range(panel * 64, min(rows, panel * 64 + 64))
        ])

    def awq(self, rows, columns):
        if rows > 64:
            raise ValueError("compact parent fixture requires rows <=64")
        weights, zeros, scales, matrix = super().awq(rows, columns)
        weight_bytes, scale_bytes = rows // 8 * 4, rows * 2
        weights = b"".join(weights[i:i + weight_bytes] for i in range(0, len(weights), 64))
        zeros = b"".join(zeros[i:i + weight_bytes] for i in range(0, len(zeros), 64))
        scales = b"".join(scales[i:i + scale_bytes] for i in range(0, len(scales), 128))
        return weights, zeros, scales, matrix

    def append(self, kind, layer, projection, data):
        g = self.geometry
        if kind in (9, 10):
            data = bytes(g.sequence * g.kv_heads * g.head_dim * 4)
        elif kind == 11:
            words = []
            for position in range(g.sequence):
                for j in range(g.head_dim // 2):
                    # The compatibility implementation consumes host Q16 RoPE.
                    from decoder_reference import frequency
                    angle = fp.multiply(fp.rounded(position), frequency(j, g.head_dim))
                    sine, cosine, error = fp.sincos32(angle)
                    if error:
                        raise ArithmeticError("parent RoPE fixture")
                    words.extend([int(fp.value(cosine) * 65536) & 0xFFFFFFFF,
                                  int(fp.value(sine) * 65536) & 0xFFFFFFFF])
            data = b"".join(word.to_bytes(4, "little") for word in words)
        super().append(kind, layer, projection, data)


def run(directory, mode=0, seed=17, top_name="anvil_q1_ht_top"):
    if top_name == "anvil_q1_top":
        return logical_top(directory)
    if mode not in (0, 2):
        raise ValueError("the parent compatibility ABI supports BF16 or AWQ, not native FP16")
    g = Geometry(vocabulary=8, sequence=3, window=1)
    image = ParentImage(g, mode, seed)
    (directory / "memory.hex").write_text("".join(
        f"{int.from_bytes(image.memory[i:i + 64], 'little'):0128x}\n"
        for i in range(0, len(image.memory), 64)))
    (directory / "descriptors.txt").write_text("".join(
        " ".join(f"{word:x}" for word in row) + "\n" for row in image.descriptors))
    pins = TOP_PINS.replace("anvil_q1_ht2_top", top_name).replace("PARAMETERS", ",".join(
        f".{key}({value})" for key, value in g.parameters().items()))
    pins = pins[:pins.index("  task reset_check;")]
    body = pins + MEMORY.replace("MEMORY_WORDS", str(len(image.memory) // 64)).replace(
        "MEMORY_PATH", relative(directory / "memory.hex")) + CSR_TASK + r"""
  integer descriptor_index,kind,layer,projection,base,length,token,received,outputs=0;
  initial begin
    repeat(4) tick(); @(negedge clk); rst_n=1; repeat(500) tick();
    csr(1,16'hc,STORAGE_MODE,0,0,0);
    fd=$fopen("DESCRIPTORS","r");
    if (!fd) $fatal(1,"FIXTURE_OPEN");
    while (!$feof(fd)) begin
      rc=$fscanf(fd,"%h %h %h %h %h %h\n",descriptor_index,kind,layer,projection,base,length);
      if (rc!=6) $fatal(1,"FIXTURE_PARSE");
      csr(1,16'h10,descriptor_index,0,0,0); csr(1,16'h14,kind,0,0,0);
      csr(1,16'h18,layer,0,0,0); csr(1,16'h1c,projection,0,0,0);
      csr(1,16'h20,base,0,0,0); csr(1,16'h24,0,0,0,0);
      csr(1,16'h28,length,0,0,0); csr(1,16'h2c,1,0,0,0);
    end
    $fclose(fd);
    csr(1,16'h8,6,0,0,0); repeat(100) tick();
    for (token=0;token<2;token=token+1) begin
      @(negedge clk); token_id=token+1; token_pos=token; token_valid=1; age=0;
      begin : accept
        forever begin
          @(posedge clk);
          if (token_ready===1) begin #1; disable accept; end
          #1; age=age+1; if (age>10000) $fatal(1,"PARENT_TOKEN_ADMISSION");
        end
      end
      @(negedge clk); token_valid=0; received=0; age=0;
      while (done!==1) begin
        logit_ready=age%7<4;
        @(posedge clk);
        if (logit_valid===1 && logit_ready) begin
          if (logit_index!==32'(received) || (^logit_data)===1'bx)
            $fatal(1,"PARENT_OUTPUT_ORDER_XZ");
          $display("RESULT %0d %0d %08h",token,logit_index,logit_data);
          if (logit_index==7)
            $display("FINAL_OBSERVATION t=%0t ready=%b done=%b error=%b", $time,logit_ready,done,error);
          checked=checked+1; received=received+1; outputs=outputs+1;
        end
        #1; age=age+1; cycles=cycles+1;
        if (age>350000)
          $fatal(1,"PARENT_COMPLETION token=%0d received=%0d ready=%b done=%b error=%b logit=%b/%0d",
                 token,received,token_ready,done,error,logit_valid,logit_index);
        @(negedge clk);
      end
      if (error!==0 || received!=8) $fatal(1,"PARENT_RESULT");
      logit_ready=0; tick(); tick();
    end
    if (outputs!=16 || reads==0 || writes==0) $fatal(1,"PARENT_COVERAGE");
    $display("CHECK compared=%0d outputs=%0d read_beats=%0d write_beats=%0d",
             checked,outputs,reads,writes);
    $finish;
  end
"""
    body = body.replace("STORAGE_MODE", "0" if mode == 2 else "1").replace(
        "DESCRIPTORS", relative(directory / "descriptors.txt"))
    records, traces = [], []
    for candidate in (False, True):
        sources = sorted((ROOT / "rtl").glob("anvil_q1_ht_*.sv")) if candidate else sorted(
            (ROOT / "anvil_q1_ht_reference" / "rtl").glob("*.sv"))
        if candidate:
            sources += [ROOT / "rtl" / "anvil_q1_top.sv"]
        record = simulate(directory, f"compatibility-{'candidate' if candidate else 'parent'}",
                          body, [], "verilator", source_paths_override=sources)
        raw = ROOT / record["receipt"]
        trace = re.findall(r"^RESULT (\d+) (\d+) ([0-9a-fA-F]{8})$", (
            raw.parent / "stdout.txt").read_text(), re.M)
        if len(trace) != 16:
            raise AssertionError("compatibility comparator missing transactions")
        traces.append(trace)
        records.append(record)
    if traces[0] != traces[1]:
        write_json(directory / "compatibility-mismatch.json", {
            "parent": traces[0], "candidate": traces[1]})
        raise AssertionError("delivered compatibility output differs from parent")
    return {"name": "compatibility", "mode": mode, "seed": seed,
            "top": top_name, "compared_logits": 16, "tokens": 2, "runs": records}


def logical_top(directory):
    body = r"""
  reg token_valid=0,logit_ready=0,new_sequence=0;
  reg [31:0] token_id=0,token_pos=0;
  wire token_ready,logit_valid,done,error;
  wire [31:0] logit_index,logit_data;
  wire mem_req_valid,mem_req_write,mem_rsp_ready;
  wire [3:0] mem_req_kind;
  wire [31:0] mem_req_layer,mem_req_row,mem_req_col,mem_req_wdata;
  wire [2:0] mem_req_proj;
  reg mem_req_ready=0,mem_rsp_valid=0,mem_rsp_error=0;
  reg [31:0] mem_rsp_rdata=0;
  reg [31:0] scratch[0:1535];
  integer mem_cycles=0,pending=0,delay_count=0,word_index,init_index,reads=0,writes=0;
  integer token,received,age,outputs=0;
  anvil_q1_top #(.NUM_LAYERS(1),.HIDDEN_SIZE(8),.INTERMEDIATE_SIZE(8),
    .NUM_Q_HEADS(1),.NUM_KV_HEADS(1),.HEAD_DIM(8),.GROUP_SIZE(1),
    .VOCAB_SIZE(8),.MAX_SEQ_LEN(3)) dut(.*);
  always @(negedge clk) begin
    mem_cycles=mem_cycles+1;
    mem_req_ready=rst_n && !pending && !mem_rsp_valid && mem_cycles%5!=1;
  end
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      pending<=0; mem_rsp_valid<=0; mem_rsp_rdata<=0; delay_count<=0;
    end else begin
      if (mem_rsp_valid && mem_rsp_ready) begin mem_rsp_valid<=0; pending<=0; end
      if (pending && !mem_rsp_valid) begin
        if (delay_count==0) mem_rsp_valid<=1;
        else delay_count<=delay_count-1;
      end
      if (mem_req_valid && mem_req_ready) begin
        if (pending || mem_req_layer!=0 || mem_req_row>=16 || mem_req_col>=8)
          $fatal(1,"LOGICAL_MEMORY_BOUNDS");
        pending<=1; delay_count<=2;
        word_index=mem_req_kind*128+mem_req_row*8+mem_req_col;
        if (mem_req_write) begin
          if (mem_req_kind<8 || mem_req_kind>10) $fatal(1,"LOGICAL_WRITE_KIND");
          scratch[word_index]=mem_req_wdata;
          mem_rsp_rdata<=0; writes=writes+1;
        end else begin
          reads=reads+1;
          case (mem_req_kind)
            0: mem_rsp_rdata<=32'h3800;
            1: mem_rsp_rdata<=32'h77777777;
            2: mem_rsp_rdata<=32'h88888888;
            3: mem_rsp_rdata<=32'h2400;
            4: mem_rsp_rdata<=0;
            5,6,7: mem_rsp_rdata<=32'h3c00;
            8,9,10: mem_rsp_rdata<=scratch[word_index];
            11: mem_rsp_rdata<=mem_req_col[0] ? 0 : 32'd65536;
            default: $fatal(1,"LOGICAL_READ_KIND");
          endcase
        end
      end
    end
  end
  initial begin
    for (init_index=0;init_index<1536;init_index=init_index+1) scratch[init_index]=0;
    repeat(4) tick(); @(negedge clk); rst_n=1; repeat(20) tick();
    for (token=0;token<2;token=token+1) begin
      @(negedge clk); token_id=token; token_pos=token; token_valid=1; new_sequence=(token==0);
      age=0;
      begin : accept
        forever begin
          @(posedge clk);
          if (token_ready===1) begin #1; disable accept; end
          #1; age=age+1; if (age>10000) $fatal(1,"LOGICAL_TOKEN_ADMISSION");
        end
      end
      @(negedge clk); token_valid=0; new_sequence=0; received=0; age=0;
      while (done!==1) begin
        logit_ready=age%7<3;
        @(posedge clk);
        if (logit_valid===1 && logit_ready) begin
          if (logit_index!==32'(received) || (^logit_data)===1'bx)
            $fatal(1,"LOGICAL_OUTPUT_ORDER");
          $display("RESULT %0d %0d %08h",token,logit_index,logit_data);
          received=received+1; outputs=outputs+1; checked=checked+1;
        end
        #1; age=age+1; cycles=cycles+1;
        if (age>200000) $fatal(1,"LOGICAL_COMPLETION");
        @(negedge clk);
      end
      if (received!=8 || error!==0) $fatal(1,"LOGICAL_RESULT");
      logit_ready=0; tick(); tick();
    end
    if (outputs!=16 || reads==0 || writes==0) $fatal(1,"LOGICAL_COVERAGE");
    $display("CHECK compared=%0d outputs=%0d reads=%0d writes=%0d",checked,outputs,reads,writes);
    $finish;
  end
"""
    results, traces = [], []
    for candidate in (False, True):
        parent = ROOT / ("rtl" if candidate else "anvil_q1_ht_reference/rtl")
        sources = [*sorted(parent.glob("anvil_q1_ht_*.sv")), parent / "anvil_q1_top.sv"]
        record = simulate(directory, f"logical-{'candidate' if candidate else 'parent'}",
                          body, [], "verilator", source_paths_override=sources)
        path = ROOT / record["receipt"]
        trace = re.findall(r"^RESULT (\d+) (\d+) ([0-9a-fA-F]{8})$",
                           (path.parent / "stdout.txt").read_text(), re.M)
        if len(trace) != 16:
            raise AssertionError("logical compatibility comparison missing outputs")
        traces.append(trace)
        results.append(record)
    if traces[0] != traces[1]:
        write_json(directory / "logical-mismatch.json", {"parent": traces[0], "candidate": traces[1]})
        raise AssertionError("anvil_q1_top compatibility mismatch")
    return {"name": "logical-compatibility", "compared_logits": 16, "tokens": 2, "runs": results}
