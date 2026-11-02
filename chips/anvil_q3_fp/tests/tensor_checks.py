"""Tensor public-command/load/result tests with independent packed-memory model."""

from fractions import Fraction
import random

from execution import compiled, relative, run_compiled
from ieee import binary, dot, exact, pack


SHIFTS = (0, 16, 4, 20, 8, 24, 12, 28)


def check(evidence, seed=17, banks=1, tile_rows=3, tile_k=8, hidden=16, intermediate=24,
          head_dim=2, repeats=3, parent=False):
    results = []
    tb = TENSOR_TB
    for key, value in {"@B@": banks, "@TR@": tile_rows, "@TK@": tile_k,
                       "@H@": hidden, "@I@": intermediate, "@D@": head_dim}.items():
        tb = tb.replace(key, str(value))
    rtl = ["rtl/anvil_q3_fp_00_pkg.sv", "rtl/anvil_q3_fp_add.sv", "rtl/anvil_q3_fp_mul.sv",
           "rtl/anvil_q3_fp_dot8.sv", "rtl/anvil_q3_fp_weight_prefetcher.sv",
           "rtl/anvil_q3_fp_tensor_array.sv"]
    if parent:
        tb = tb.replace("anvil_q3_fp_tensor_array", "anvil_q3_tensor_array")
        tb = tb.replace("reg [15:0] load_data", "reg [31:0] load_data")
        tb = tb.replace("reg [15:0] activations", "reg [31:0] activations")
        tb = tb.replace("result_row,result_sum,c_req_layer", "result_row,c_req_layer")
        tb = tb.replace("wire [B*4-1:0] c_req_kind;", "wire [B*128-1:0] result_sum;\nwire [B*4-1:0] c_req_kind;")
        tb = tb.replace("reg [31:0] data[0:262143],expected[0:16383];",
                        "reg [31:0] data[0:262143];\nreg [127:0] expected[0:16383];")
        tb = tb.replace("reg [63:0] held_payload", "reg [159:0] held_payload")
        tb = tb.replace("result_sum[bank*32+:32]", "result_sum[bank*128+:128]")
        rtl = [f"anvil_q3_reference/rtl/{name}.sv" for name in (
            "anvil_q3_00_pkg", "anvil_q3_awq_dot8", "anvil_q3_add128",
            "anvil_q3_weight_prefetcher", "anvil_q3_tensor_array")]
    prefix = "parent-" if parent else ""
    executable = compiled(evidence, f"{prefix}tensor-b{banks}-r{tile_rows}-k{tile_k}-h{hidden}", tb, rtl)
    for dtype, fmt in enumerate(("bf16", "fp16")):
        for awq in (0, 1):
            if parent and not awq:
                continue
            rng = random.Random(seed)
            memory, weights, qs, zs, scales = {}, {}, {}, {}, {}
            for projection in range(7):
                rows = head_dim if projection in (1, 2) else intermediate if projection in (4, 5) else hidden
                cols = intermediate if projection == 6 else hidden
                weights[projection] = [[pack(Fraction(rng.randrange(-127, 128), 64), fmt)[0]
                                        for _ in range(cols)] for _ in range(rows)]
                qs[projection] = [[rng.randrange(16) for _ in range(cols)] for _ in range(rows)]
                zs[projection] = [[rng.randrange(16) for _ in range((cols + 7) // 8)] for _ in range(rows)]
                scales[projection] = [[pack(Fraction(rng.randrange(1, 64), 256), "fp16")[0]
                                      for _ in range((cols + 7) // 8)] for _ in range(rows)]
                for col in range(cols):
                    stride = 8 if awq else 2
                    for base in range(0, rows, stride):
                        if awq:
                            word = sum(qs[projection][row][col] << SHIFTS[row % 8]
                                       for row in range(base, min(base + 8, rows)))
                        else:
                            word = sum(weights[projection][row][col] << (16 * (row - base))
                                       for row in range(base, min(base + 2, rows)))
                        memory[1, projection, col, base // stride] = word
                if awq:
                    for group in range((cols + 7) // 8):
                        for base in range(0, rows, 8):
                            memory[2, projection, group, base // 8] = sum(
                                zs[projection][row][group] << SHIFTS[row % 8]
                                for row in range(base, min(base + 8, rows)))
                        for row in range(rows):
                            memory[3, projection, group, row] = scales[projection][row][group]
            lines = [f"{dtype} {awq} {len(memory)} {7 * repeats}\n"]
            lines += [f"{kind:x} {proj:x} {row:08x} {col:08x} {value:08x}\n"
                      for (kind, proj, row, col), value in sorted(memory.items())]
            compared = 0
            for repetition in range(repeats):
                for projection in range(7):
                    rows, cols = len(weights[projection]), len(weights[projection][0])
                    activations = [pack(Fraction(rng.randrange(-127, 128), 32), fmt)[0] for _ in range(cols)]
                    lines.append(f"{projection} {cols} {rows}\n")
                    activation_q16 = [int(exact(a, fmt) * 65536) for a in activations]
                    lines += [f"{a & 0xffffffff:08x}\n" for a in activation_q16] if parent else [f"{a:04x}\n" for a in activations]
                    for row in range(rows):
                        total = 0
                        if parent:
                            for col, activation in enumerate(activation_q16):
                                scale = exact(scales[projection][row][col // 8], "fp16") * 65536
                                scale_q16 = (2 * scale.numerator + scale.denominator) // (2 * scale.denominator)
                                total += (qs[projection][row][col] - zs[projection][row][col // 8]) * scale_q16 * activation
                            lines.append(f"{total & ((1 << 128) - 1):032x}\n")
                            compared += 1
                            continue
                        for base in range(0, cols, 8):
                            count = min(8, cols - base)
                            a = activations[base:base + 8] + [0] * (8 - count)
                            w = weights[projection][row][base:base + 8] + [0] * (8 - count)
                            q = qs[projection][row][base:base + 8] + [0] * (8 - count)
                            z = [zs[projection][row][(base + lane) // 8] if lane < count else 0
                                 for lane in range(8)]
                            scale = [scales[projection][row][(base + lane) // 8] if lane < count else 0
                                     for lane in range(8)]
                            reduced = dot(a, w, (1 << count) - 1, fmt, q if awq else None, z, scale)[0]
                            total = binary("add", total, reduced)[0]
                        lines.append(f"{total:08x}\n")
                        compared += 1
            name = f"{prefix}tensor-b{banks}-r{tile_rows}-k{tile_k}-h{hidden}-{fmt}-w{awq}-s{seed}"
            output = run_compiled(evidence, executable, name, {"vectors.txt": "".join(lines)})
            commands = []
            for line in output.read_text().splitlines():
                if line.startswith("COMMAND "):
                    command, projection, cycles, rows, requests, request_stalls = map(int, line.split()[1:])
                    columns = intermediate if projection == 6 else hidden
                    byte_count = requests * 4
                    observed = byte_count * 100000000 / cycles
                    ideal = banks * 4 * 100000000
                    commands.append({"command": command, "projection": projection,
                                     "command_to_done_cycles": cycles, "compared_rows": rows,
                                     "useful_operations": rows * columns * 2,
                                     "response_bytes": byte_count, "request_stalls": request_stalls,
                                     "observed_bytes_per_second_at_100mhz": observed,
                                     "ideal_bank_bytes_per_second_at_100mhz": ideal,
                                     "bandwidth_gap_bytes_per_second": ideal - observed})
            if len(commands) != 7 * repeats:
                raise AssertionError(f"Missing measured tensor command records: {name}")
            results.append({"banks": banks, "tile_rows": tile_rows, "tile_k": tile_k,
                            "hidden": hidden, "intermediate": intermediate, "head_dim": head_dim,
                            "format": fmt, "awq": awq, "seed": seed,
                            "implementation": "immutable_parent" if parent else "floating_point",
                            "measured_commands": commands,
                            "commands": 7 * repeats, "accumulated_rows_compared": compared,
                            "stdout": relative(output)})
    return results


TENSOR_TB = """
module tb;
  localparam B=@B@,H=@H@,I=@I@,D=@D@;
  reg clk=0;
  always #5 clk=~clk;
  reg rst_n,flush=0,cmd_valid=0,cmd_fp16=0,cmd_awq=0;
  wire cmd_ready,done,error,load_ready;
  reg [31:0] cmd_epoch=1,cmd_layer=0;
  reg [2:0] cmd_proj=0;
  reg load_valid=0,load_last=0;
  reg [15:0] load_data=0;
  wire [B-1:0] result_valid,c_req_valid,c_req_write,c_rsp_ready;
  reg [B-1:0] result_ready=0,c_req_ready=0,c_rsp_valid=0,c_rsp_error=0;
  wire [B*32-1:0] result_row,result_sum,c_req_layer,c_req_row,c_req_col,c_req_wdata;
  wire [B*4-1:0] c_req_kind;
  wire [B*3-1:0] c_req_proj;
  reg [B*32-1:0] c_rsp_rdata=0;
  anvil_q3_fp_tensor_array #(.BANKS(B),.TILE_ROWS(@TR@),.TILE_K(@TK@),
    .NUM_LAYERS(1),.HIDDEN_SIZE(H),.INTERMEDIATE_SIZE(I),.NUM_KV_HEADS(1),
    .HEAD_DIM(D),.GROUP_SIZE(8)) dut(.*);
  reg [70:0] keys[0:262143],key;
  reg [31:0] data[0:262143],expected[0:16383];
  reg [15:0] activations[0:16383];
  reg consumed[0:16383],pending[0:B-1];
  reg [31:0] response[0:B-1];
  integer due[0:B-1],cycle=0,fd,rc,nmem,ncommands,dtype,awq,ninput,noutput;
  integer command=0,loaded=0,received=0,total=0,stalls=0,simultaneous=0;
  integer command_requests=0,command_request_stalls=0;
  integer bank,index,kind,proj,row,col,value,low,high,middle,found,latency;
  reg [B-1:0] held=0,request_held=0,activity=0;
  reg [63:0] held_payload[0:B-1];
  reg [134:0] request_payload[0:B-1];
  task reset_check;
    begin
      if ({cmd_ready,load_ready,done,error,result_valid,result_row,result_sum,
          c_req_valid,c_req_write,c_req_kind,c_req_layer,c_req_proj,c_req_row,
          c_req_col,c_req_wdata,c_rsp_ready} !== 0) $fatal(1,"RESET tensor outputs");
    end
  endtask
  initial begin
    rst_n=0;
    for (bank=0;bank<B;bank=bank+1) pending[bank]=0;
    #0; reset_check;
    #1; reset_check;
    fd=$fopen("vectors.txt","r");
    if (!fd) $fatal(1,"tensor vectors");
    rc=$fscanf(fd,"%d %d %d %d\\n",dtype,awq,nmem,ncommands);
    if (rc!=4 || nmem>262144) $fatal(1,"tensor header");
    cmd_fp16=dtype; cmd_awq=awq;
    for (index=0;index<nmem;index=index+1) begin
      rc=$fscanf(fd,"%h %h %h %h %h\\n",kind,proj,row,col,value);
      if (rc!=5) $fatal(1,"tensor memory vector");
      keys[index]={4'(kind),3'(proj),32'(row),32'(col)}; data[index]=value;
    end
    @(negedge clk); rst_n=1;
    for (command=0;command<ncommands;command=command+1) begin
      rc=$fscanf(fd,"%d %d %d\\n",proj,ninput,noutput);
      if (rc!=3 || ninput>16384 || noutput>16384) $fatal(1,"tensor command");
      for (index=0;index<ninput;index=index+1) begin
        rc=$fscanf(fd,"%h\\n",activations[index]);
        if (rc!=1) $fatal(1,"tensor activation");
      end
      for (index=0;index<noutput;index=index+1) begin
        rc=$fscanf(fd,"%h\\n",expected[index]);
        if (rc!=1) $fatal(1,"tensor expected");
        consumed[index]=0;
      end
      while (cmd_ready!==1'b1) @(negedge clk);
      cmd_proj=proj; cmd_valid=1; loaded=0; received=0; latency=0;
      command_requests=0; command_request_stalls=0;
      @(negedge clk); cmd_valid=0;
      while (done!==1'b1 && latency<2000000) begin
        load_valid=loaded<ninput && cycle%7!=4;
        load_data=loaded<ninput ? activations[loaded] : 16'd0;
        load_last=loaded+1==ninput;
        @(posedge clk);
        if (load_valid && load_ready) loaded=loaded+1;
        @(negedge clk);
        latency=latency+1;
      end
      load_valid=0;
      if (done!==1'b1 || error!==1'b0 || received!=noutput || loaded!=ninput)
        $fatal(1,"TENSOR completion command=%0d done=%b error=%b rows=%0d/%0d inputs=%0d/%0d",
          command,done,error,received,noutput,loaded,ninput);
      for (index=0;index<noutput;index=index+1) if (!consumed[index]) $fatal(1,"missing row");
      $display("COMMAND %0d %0d %0d %0d %0d %0d",
        command,proj,latency,received,command_requests,command_request_stalls);
      @(negedge clk);
      if (done!==1'b0) $fatal(1,"tensor done not pulse");
    end
    if (total==0 || stalls==0 || activity!=={B{1'b1}}) $fatal(1,"missing tensor coverage");
    $display("COMPARED tensor rows=%0d stalls=%0d simultaneous=%0d banks=%h",total,stalls,simultaneous,activity);
    $finish;
  end
  always @(posedge clk) begin
    if (!rst_n) reset_check;
    else begin
      for (bank=0;bank<B;bank=bank+1) begin
        if (held[bank] && (result_valid[bank]!==1'b1 ||
          {result_row[bank*32+:32],result_sum[bank*32+:32]}!==held_payload[bank]))
          $fatal(1,"STALL tensor result");
        held[bank]=result_valid[bank] && !result_ready[bank];
        held_payload[bank]={result_row[bank*32+:32],result_sum[bank*32+:32]};
        if (held[bank]) stalls=stalls+1;
        if (result_valid[bank] && result_ready[bank]) begin
          row=result_row[bank*32+:32];
          if (row>=noutput || consumed[row] || result_sum[bank*32+:32]!==expected[row])
            $fatal(1,"TENSOR row=%0d expected=%h got=%h command=%0d proj=%0d",
              row,expected[row],result_sum[bank*32+:32],command,cmd_proj);
          consumed[row]=1; received=received+1; total=total+1;
          if (c_req_valid!=0) simultaneous=simultaneous+1;
        end
        if (request_held[bank] && (c_req_valid[bank]!==1'b1 ||
          {c_req_kind[bank*4+:4],c_req_layer[bank*32+:32],c_req_proj[bank*3+:3],
           c_req_row[bank*32+:32],c_req_col[bank*32+:32],c_req_wdata[bank*32+:32]}!==request_payload[bank]))
          $fatal(1,"STALL tensor request");
        request_held[bank]=c_req_valid[bank] && !c_req_ready[bank];
        if (request_held[bank]) command_request_stalls=command_request_stalls+1;
        request_payload[bank]={c_req_kind[bank*4+:4],c_req_layer[bank*32+:32],c_req_proj[bank*3+:3],
          c_req_row[bank*32+:32],c_req_col[bank*32+:32],c_req_wdata[bank*32+:32]};
        if (c_rsp_valid[bank] && c_rsp_ready[bank]) pending[bank]=0;
        if (c_req_valid[bank] && c_req_ready[bank]) begin
          command_requests=command_requests+1;
          if (pending[bank] || c_req_write[bank] || c_req_layer[bank*32+:32]!==0)
            $fatal(1,"tensor memory protocol");
          activity[bank]=1;
          key={c_req_kind[bank*4+:4],c_req_proj[bank*3+:3],c_req_row[bank*32+:32],c_req_col[bank*32+:32]};
          low=0; high=nmem-1; found=-1;
          while (low<=high) begin
            middle=(low+high)>>1;
            if (keys[middle]==key) begin found=middle; low=high+1; end
            else if (keys[middle]<key) low=middle+1;
            else high=middle-1;
          end
          if (found<0) $fatal(1,"tensor uninitialized read key=%h",key);
          response[bank]=data[found]; pending[bank]=1; due[bank]=cycle+2+(cycle%5);
        end
      end
      cycle=cycle+1;
    end
  end
  always @(negedge clk) begin
    if (!rst_n) reset_check;
    else for (bank=0;bank<B;bank=bank+1) begin
      result_ready[bank]=(cycle+bank)%11<6;
      c_req_ready[bank]=!pending[bank] && (cycle+bank)%7<5;
      c_rsp_valid[bank]=pending[bank] && due[bank]<=cycle;
      c_rsp_rdata[bank*32+:32]=c_rsp_valid[bank] ? response[bank] : 32'd0;
    end
  end
endmodule
"""
