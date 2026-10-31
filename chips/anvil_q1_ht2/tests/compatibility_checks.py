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
