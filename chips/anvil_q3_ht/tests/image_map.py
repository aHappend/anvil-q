"""Default model image-map tests without allocating the production tensors."""

from model import BASES, PRODUCTION, image_layout


MAP_TB = r"""
module verify_map;
  reg clk=0; always #5 clk=~clk;
  reg rst_n=0, flush=0, req_valid=0, req_write=0, rsp_ready=0;
  reg [3:0] req_kind=0;
  reg [31:0] req_layer=0, req_row=0, req_col=0;
  reg [2:0] req_proj=0;
  wire req_ready, rsp_valid, rsp_error, rsp_scratch;
  wire [32:0] rsp_address, rsp_qweight_base, rsp_qzeros_base, rsp_scales_base;
  wire [2:0] rsp_bytes;
  wire [31:0] rsp_inputs, rsp_outputs;
  wire [200:0] response={rsp_scales_base,rsp_qzeros_base,rsp_qweight_base,
                        rsp_outputs,rsp_inputs,rsp_bytes,rsp_address,rsp_scratch,rsp_error};
  anvil_q3_ht_image_map dut(.*);
  localparam N=@N@;
  reg [103:0] requests [0:N-1];
  reg [200:0] expected [0:N-1];
  integer i, compared=0, errors=0;
  task reset_check;
    begin
      if ({req_ready,rsp_valid,response} !== 203'd0) $fatal(1,"IMAGE_MAP_RESET_XZ");
    end
  endtask
  always @(posedge clk) if (!rst_n) reset_check();
  always @(negedge clk) if (!rst_n) reset_check();
  initial begin
    $readmemh("@REQUESTS@",requests);
    $readmemh("@EXPECTED@",expected);
    #1; reset_check();
    repeat(3) @(negedge clk);
    rst_n=1;
    for (i=0;i<N;i=i+1) begin
      @(negedge clk);
      {req_col,req_row,req_proj,req_layer,req_kind,req_write}=requests[i];
      req_valid=1;
      @(posedge clk);
      if (req_ready !== 1 || rsp_valid !== 0) $fatal(1,"IMAGE_MAP_REQUEST_TIMING");
      #1;
      if (rsp_valid !== 1 || response !== expected[i])
        $fatal(1,"PRODUCTION_IMAGE_ADDRESS case=%0d actual=%h expected=%h",i,response,expected[i]);
      @(negedge clk); req_valid=0;
      repeat(2) begin
        @(posedge clk); #1;
        if (rsp_valid !== 1 || response !== expected[i] || req_ready !== 0)
          $fatal(1,"IMAGE_MAP_STABILITY");
      end
      @(negedge clk); rsp_ready=1;
      @(posedge clk);
      if (response !== expected[i]) $fatal(1,"IMAGE_MAP_TRANSFER");
      compared=compared+1;
      if (rsp_error) errors=errors+1;
      #1;
      if (rsp_valid !== 0 || response !== 201'd0) $fatal(1,"IMAGE_MAP_INVALID_PAYLOAD");
      @(negedge clk); rsp_ready=0;
    end
    if (compared!=N || errors==0) $fatal(1,"IMAGE_MAP_COVERAGE");
    $display("IMAGE_MAP_PASS layers=36 projections=7 compared=%0d rejected=%0d",compared,errors);
    $finish;
  end
endmodule
"""


def map_vectors():
    g = PRODUCTION
    layout = image_layout(g)
    vectors = []

    def add(kind, layer=0, projection=0, row=0, col=0, write=False, error=False):
        matrix = layout["matrices"].get((layer, projection), {})
        n, m = matrix.get("inputs", g.hidden), matrix.get("outputs", g.hidden)
        if kind in (1, 2):
            address = matrix["qweight" if kind == 1 else "qzeros"]
            address += (col * ((m + 7) // 8) + row) * 4
            size = 4
        elif kind == 3:
            address, size = matrix["scales"] + (col * m + row) * 2, 2
        elif kind == 0:
            address, size = BASES["embedding"] + (row * g.hidden + col) * 2, 2
        elif kind == 4:
            per_layer = (g.hidden + 2 * g.kv_heads * g.head_dim) * 2
            before = (0, g.hidden, g.hidden + g.kv_heads * g.head_dim)[projection]
            address, size = BASES["bias"] + layer * per_layer + (before + col) * 2, 2
        elif kind in (5, 6, 7):
            index = 2 * g.layers if kind == 7 else 2 * layer + (kind == 6)
            address, size = BASES["norm"] + (index * g.hidden + col) * 2, 2
        elif kind == 11:
            address, size = BASES["rope"] + (row * g.head_dim + col) * 4, 4
        else:
            address, size = 0, 0
        request = (int(write) | (kind << 1) | (layer << 5) | (projection << 37)
                   | (row << 40) | (col << 72))
        if error:
            response = 1
        else:
            fields = ((0, 1), (0, 1), (address, 33), (size, 3), (n, 32), (m, 32),
                      (matrix["qweight"], 33), (matrix["qzeros"], 33), (matrix["scales"], 33))
            response, offset = 0, 0
            for field, bits in fields:
                response |= field << offset
                offset += bits
        vectors.append((request, response))

    for layer in range(g.layers):
        for projection, (n, m) in enumerate(g.shapes):
            for last in (False, True):
                add(1, layer, projection, ((m + 7) // 8 - 1) if last else 0,
                    n - 1 if last else 0)
                add(2, layer, projection, ((m + 7) // 8 - 1) if last else 0,
                    n // g.group - 1 if last else 0)
                add(3, layer, projection, m - 1 if last else 0,
                    n // g.group - 1 if last else 0)
            if projection < 3:
                add(4, layer, projection, col=0)
                add(4, layer, projection, col=m - 1)
        for kind in (5, 6):
            add(kind, layer, col=0)
            add(kind, layer, col=g.hidden - 1)
    for last in (False, True):
        add(0, row=g.vocab - 1 if last else 0, col=g.hidden - 1 if last else 0)
        add(7, col=g.hidden - 1 if last else 0)
        add(11, row=g.context - 1 if last else 0, col=g.head_dim - 1 if last else 0)
    add(0, row=g.vocab, error=True)
    add(0, col=g.hidden, error=True)
    add(0, write=True, error=True)
    add(1, row=g.hidden // 8, error=True)
    add(1, col=g.hidden, error=True)
    add(11, row=g.context, error=True)
    add(15, error=True)
    return vectors, layout


def map_bench(directory, relative):
    vectors, layout = map_vectors()
    bench = MAP_TB.replace("@N@", str(len(vectors)))
    for field, width, index in (("requests", 104, 0), ("expected", 201, 1)):
        path = directory / f"production-map-{field}.hex"
        path.write_text("".join(f"{vector[index]:0{(width + 3) // 4}x}\n" for vector in vectors))
        bench = bench.replace(f"@{field.upper()}@", relative(path))
    return bench, {key: value for key, value in layout.items() if key != "matrices"}
