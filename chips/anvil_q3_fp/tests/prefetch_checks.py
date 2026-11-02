"""Selected production-shape row tiles, ping-pong overlap and public beat checks."""

from fractions import Fraction

from execution import compiled, relative, run_compiled
from ieee import dot, pack
from tensor_checks import SHIFTS


def check(evidence, banks=8, projections=range(7), row_count=3, input_counts=(128, 125)):
    results = []
    tb = PREFETCH_TB.replace("@B@", str(banks))
    binary = compiled(evidence, f"prefetch-b{banks}", tb,
                      ["rtl/anvil_q3_fp_00_pkg.sv", "rtl/anvil_q3_fp_add.sv",
                       "rtl/anvil_q3_fp_mul.sv", "rtl/anvil_q3_fp_dot8.sv",
                       "rtl/anvil_q3_fp_weight_prefetcher.sv"])
    for projection in projections:
        evidence.ensure_budget()
        ninput = 11008 if projection == 6 else 2048
        noutput = 256 if projection in (1, 2) else 11008 if projection in (4, 5) else 2048
        for dtype, fmt in enumerate(("bf16", "fp16")):
            for awq in (0, 1):
                memory, descriptors, expected = {}, [], []
                def weight(row, col):
                    return pack(Fraction((row * 31 + col * 17) % 127 - 63, 256), fmt)[0]
                def q(row, col):
                    return (row * 3 + col * 5 + 7) & 15
                def z(row, group):
                    return (row + group) & 15
                for tile in range(2):
                    for bank in range(banks):
                        evidence.ensure_budget()
                        output_base = bank * row_count if tile == 0 else noutput - (bank + 1) * row_count
                        count = input_counts[tile]
                        input_base = 0 if tile == 0 else ninput - count
                        descriptors.append((bank, tile + 1, output_base, input_base, row_count, count))
                        for row in range(output_base, output_base + row_count):
                            for col in range(input_base, input_base + count):
                                if awq:
                                    base = row & ~7
                                    memory[1, col, row >> 3] = sum(q(r, col) << SHIFTS[r & 7]
                                                                  for r in range(base, min(base + 8, noutput)))
                                    group = col // 128
                                    memory[2, group, row >> 3] = sum(z(r, group) << SHIFTS[r & 7]
                                                                   for r in range(base, min(base + 8, noutput)))
                                    memory[3, group, row] = 0x2000
                                else:
                                    base = row & ~1
                                    memory[1, col, row >> 1] = sum(weight(r, col) << (16 * (r - base))
                                                                  for r in range(base, min(base + 2, noutput)))
                            for offset in range(0, count, 8):
                                valid = min(8, count - offset)
                                cols = [input_base + offset + lane for lane in range(valid)]
                                weights = sum(weight(row, col) << (16 * lane) for lane, col in enumerate(cols))
                                qs = sum(q(row, col) << (4 * lane) for lane, col in enumerate(cols))
                                zs = sum(z(row, col // 128) << (4 * lane) for lane, col in enumerate(cols))
                                scales = sum(0x2000 << (16 * lane) for lane in range(valid))
                                dot_value, dot_flags = dot(
                                    [pack(Fraction(1), fmt)[0]] * 8,
                                    [weight(row, col) for col in cols] + [0] * (8 - valid),
                                    (1 << valid) - 1, fmt,
                                    ([q(row, col) for col in cols] + [0] * (8 - valid)) if awq else None,
                                    [z(row, col // 128) for col in cols] + [0] * (8 - valid),
                                    [0x2000] * 8)
                                expected.append((bank, tile + 1, row, input_base + offset,
                                                 (1 << valid) - 1, int(offset == 0),
                                                 int(offset + 8 >= count),
                                                 int(row == output_base + row_count - 1 and offset + 8 >= count),
                                                 qs if awq else 0, zs if awq else 0,
                                                 scales if awq else 0, weights if not awq else 0,
                                                 dot_value, dot_flags))
                lines = [f"{dtype} {awq} {projection} {len(memory)} {len(expected)}\n"]
                lines += [f"{kind:x} {row:08x} {col:08x} {data:08x}\n"
                          for (kind, row, col), data in sorted(memory.items())]
                lines += [" ".join(map(str, descriptor)) + "\n" for descriptor in descriptors]
                lines += [f"{b} {epoch} {row} {col} {mask:02x} {first} {last} {final} "
                          f"{qs:08x} {zs:08x} {scale:032x} {weight_bits:032x} {dot_value:08x} {dot_flags:02x}\n"
                          for b, epoch, row, col, mask, first, last, final, qs, zs, scale, weight_bits, dot_value, dot_flags in expected]
                name = f"prefetch-b{banks}-p{projection}-{fmt}-w{awq}-r{row_count}-c{input_counts[1]}"
                output = run_compiled(evidence, binary, name, {"vectors.txt": "".join(lines)})
                summary = [line for line in output.read_text().splitlines()
                           if line.startswith("COMPARED prefetch ")]
                if len(summary) != 1:
                    raise AssertionError("Missing measured prefetch/compute summary")
                observations = {key: int(value) for field in summary[0].split()[2:]
                                for key, value in [field.split("=")]}
                results.append({"banks": banks, "projection": projection, "input_shape": ninput,
                                "output_shape": noutput, "format": fmt, "awq": awq,
                                "sampled_tiles_per_bank": 2, "descriptor_rows": row_count,
                                "sampled_input_counts": list(input_counts), "compared_beats": len(expected),
                                "compared_dot_results": len(expected),
                                "observations": observations,
                                "stdout": relative(output)})
    return results


PREFETCH_TB = """
module tb;
  localparam B=@B@;
  reg clk=0;
  always #5 clk=~clk;
  reg rst_n,flush=0;
  reg [B-1:0] desc_valid=0,desc_fp16=0,desc_awq=0,c_req_ready=0,c_rsp_valid=0,c_rsp_error=0;
  wire [B-1:0] beat_ready;
  wire [B-1:0] desc_ready,fault,beat_valid,beat_row_first,beat_row_last,beat_tile_last;
  wire [B-1:0] c_req_valid,c_req_write,c_rsp_ready;
  reg [B*32-1:0] desc_epoch=0,desc_layer=0,desc_output_base=0,desc_input_base=0;
  reg [B*32-1:0] desc_valid_rows=0,desc_valid_inputs=0,c_rsp_rdata=0;
  reg [B*3-1:0] desc_proj=0;
  wire [B*32-1:0] beat_q,beat_z,beat_epoch,beat_row,beat_input,c_req_layer,c_req_row,c_req_col,c_req_wdata;
  wire [B*128-1:0] beat_scale,beat_weight16;
  wire [B*8-1:0] beat_mask;
  wire [B*4-1:0] c_req_kind;
  wire [B*3-1:0] c_req_proj;
  anvil_q3_fp_weight_prefetcher #(.BANKS(B)) dut(.*);
  wire [B-1:0] dot_ready,dot_valid,dot_error;
  wire [B*32-1:0] dot_result;
  wire [B*5-1:0] dot_flags;
  reg [B-1:0] compute_enable=0,dot_out_ready=0;
  assign beat_ready=compute_enable & dot_ready;
  reg dot_started=0;
  genvar g;
  generate for (g=0;g<B;g=g+1) begin: compute
    anvil_q3_fp_dot8 lane(
      .clk(clk),.rst_n(rst_n),.flush(flush),
      .in_valid(beat_valid[g] && compute_enable[g]),.in_ready(dot_ready[g]),
      .in_fp16(desc_fp16[g]),.in_awq(desc_awq[g]),
      .weight16(beat_weight16[g*128+:128]),
      .activation16(desc_fp16[g] ? {8{16'h3c00}} : {8{16'h3f80}}),
      .q_nibbles(beat_q[g*32+:32]),.z_nibbles(beat_z[g*32+:32]),
      .scale_f16(beat_scale[g*128+:128]),.lane_mask(beat_mask[g*8+:8]),
      .out_ready(dot_out_ready[g]),.out_valid(dot_valid[g]),.out_error(dot_error[g]),
      .out_dot(dot_result[g*32+:32]),.out_flags(dot_flags[g*5+:5]));
  end endgenerate
  reg [67:0] keys[0:262143],key;
  reg [31:0] data[0:262143],response[0:B-1];
  reg [426:0] expected[0:B-1][0:127],held_payload[0:B-1],payload;
  reg [31:0] output_base[0:B-1][0:1],input_base[0:B-1][0:1];
  reg [31:0] rows[0:B-1][0:1],inputs[0:B-1][0:1];
  reg pending[0:B-1];
  reg second_request_seen[0:B-1];
  reg [B-1:0] held=0;
  integer sent[0:B-1],received[0:B-1],due[0:B-1],counts[0:B-1];
  integer reduced[0:B-1],dot_total=0,dot_concurrent=0;
  reg [36:0] expected_dot[0:B-1][0:127];
  reg [31:0] scanned_dot;
  reg [4:0] scanned_flags;
  integer fd,rc,nmem,nexpected,dtype,awq,projection,index,b,t,e,r,c,m,first,last,tile_last;
  integer kind,value,epoch,low,high,mid,found,cycle=0,total=0,overlap=0,all_banks=0,stalls=0;
  reg [31:0] qs,zs;
  reg [127:0] scales,weights;
  task reset_check;
    begin
      if ({desc_ready,fault,beat_valid,beat_q,beat_z,beat_epoch,beat_row,beat_input,
          beat_scale,beat_weight16,beat_mask,beat_row_first,beat_row_last,beat_tile_last,
          c_req_valid,c_req_write,c_req_kind,c_req_layer,c_req_proj,c_req_row,c_req_col,
          c_req_wdata,c_rsp_ready,dot_ready,dot_valid,dot_error,dot_result,dot_flags}!==0)
        $fatal(1,"RESET prefetch/compute public outputs");
    end
  endtask
  initial begin
    rst_n=0;
    for (b=0;b<B;b=b+1) begin
      if ((beat_valid[b] && beat_ready[b]) !==
          (beat_valid[b] && compute_enable[b] && dot_ready[b]))
        $fatal(1,"prefetch/compute transfer disagreement");
      pending[b]=0; second_request_seen[b]=0; sent[b]=0; received[b]=0; counts[b]=0; reduced[b]=0;
    end
    #0; reset_check;
    #1; reset_check;
    fd=$fopen("vectors.txt","r");
    if (!fd) $fatal(1,"prefetch vectors");
    rc=$fscanf(fd,"%d %d %d %d %d\\n",dtype,awq,projection,nmem,nexpected);
    if (rc!=5 || nmem>262144) $fatal(1,"prefetch header");
    for (index=0;index<nmem;index=index+1) begin
      rc=$fscanf(fd,"%h %h %h %h\\n",kind,r,c,value);
      if (rc!=4) $fatal(1,"prefetch memory");
      keys[index]={4'(kind),32'(r),32'(c)}; data[index]=value;
    end
    for (index=0;index<2*B;index=index+1) begin
      rc=$fscanf(fd,"%d %d %d %d %d %d\\n",b,e,r,c,first,last);
      if (rc!=6) $fatal(1,"prefetch descriptor");
      output_base[b][e-1]=r; input_base[b][e-1]=c;
      rows[b][e-1]=first; inputs[b][e-1]=last;
    end
    for (index=0;index<nexpected;index=index+1) begin
      rc=$fscanf(fd,"%d %d %d %d %h %d %d %d %h %h %h %h %h %h\\n",
        b,epoch,r,c,m,first,last,tile_last,qs,zs,scales,weights,scanned_dot,scanned_flags);
      if (rc!=14 || counts[b]==128) $fatal(1,"prefetch expected");
      expected[b][counts[b]]={32'(epoch),32'(r),32'(c),8'(m),1'(first),1'(last),1'(tile_last),qs,zs,scales,weights};
      expected_dot[b][counts[b]]={scanned_flags,scanned_dot};
      counts[b]=counts[b]+1;
    end
    @(negedge clk); rst_n=1;
  end
  always @(posedge clk) begin
    if (!rst_n) reset_check;
    else begin
      if (fault!=0) $fatal(1,"prefetch fault");
      if (beat_valid=={B{1'b1}}) all_banks=all_banks+1;
      if (dot_valid=={B{1'b1}}) begin dot_concurrent=dot_concurrent+1; dot_started=1; end
      for (b=0;b<B;b=b+1) begin
        if (dot_valid[b] && dot_out_ready[b]) begin
          if (reduced[b]>=received[b] || dot_error[b]!==1'b0 ||
              {dot_flags[b*5+:5],dot_result[b*32+:32]}!==expected_dot[b][reduced[b]])
            $fatal(1,"PREFETCH DOT bank=%0d result=%0d expected=%h got=%h/%h",
              b,reduced[b],expected_dot[b][reduced[b]],dot_flags[b*5+:5],dot_result[b*32+:32]);
          reduced[b]=reduced[b]+1; dot_total=dot_total+1;
        end
        payload={beat_epoch[b*32+:32],beat_row[b*32+:32],beat_input[b*32+:32],beat_mask[b*8+:8],
          beat_row_first[b],beat_row_last[b],beat_tile_last[b],beat_q[b*32+:32],beat_z[b*32+:32],
          beat_scale[b*128+:128],beat_weight16[b*128+:128]};
        if (held[b] && (beat_valid[b]!==1'b1 || payload!==held_payload[b]))
          $fatal(1,"prefetch held beat changed");
        held[b]=beat_valid[b] && !beat_ready[b]; held_payload[b]=payload;
        if (held[b]) stalls=stalls+1;
        if (desc_valid[b] && desc_ready[b]) sent[b]=sent[b]+1;
        if (beat_valid[b] && beat_ready[b]) begin
          if (second_request_seen[b] && pending[b] && beat_epoch[b*32+:32]==1)
            overlap=overlap+1;
          if (received[b]>=counts[b] || payload!==expected[b][received[b]])
            $fatal(1,"PREFETCH bank=%0d beat=%0d expected=%h got=%h",b,received[b],expected[b][received[b]],payload);
          received[b]=received[b]+1; total=total+1;
        end
        if (c_rsp_valid[b] && c_rsp_ready[b]) pending[b]=0;
        if (c_req_valid[b] && c_req_ready[b]) begin
          if (c_req_kind[b*4+:4]==1 && c_req_row[b*32+:32]>=input_base[b][1])
            second_request_seen[b]=1;
          if (pending[b] || c_req_write[b] || c_req_layer[b*32+:32]!=0 ||
              c_req_proj[b*3+:3]!=projection) $fatal(1,"prefetch request protocol");
          key={c_req_kind[b*4+:4],c_req_row[b*32+:32],c_req_col[b*32+:32]};
          low=0; high=nmem-1; found=-1;
          while (low<=high) begin
            mid=(low+high)>>1;
            if (keys[mid]==key) begin found=mid; low=high+1; end
            else if (keys[mid]<key) low=mid+1;
            else high=mid-1;
          end
          if (found<0) $fatal(1,"prefetch uninitialized memory");
          response[b]=data[found]; pending[b]=1; due[b]=cycle+2+(cycle+b)%5;
        end
      end
      if (total==nexpected && dot_total==nexpected) begin
        if (overlap==0 || all_banks==0 || stalls==0 || dot_concurrent==0)
          $fatal(1,"prefetch missing actual events overlap=%0d concurrent=%0d stalls=%0d compute=%0d",
            overlap,all_banks,stalls,dot_concurrent);
        for (b=0;b<B;b=b+1) if (pending[b] || sent[b]!=2 || received[b]!=counts[b])
          $fatal(1,"prefetch transaction conservation");
        $display("COMPARED prefetch beats=%0d overlap=%0d concurrent=%0d stalls=%0d cycles=%0d dot_results=%0d concurrent_compute=%0d",
          total,overlap,all_banks,stalls,cycle,dot_total,dot_concurrent);
        $finish;
      end
      cycle=cycle+1;
      if (cycle>500000) $fatal(1,"prefetch progress");
    end
  end
  always @(negedge clk) begin
    if (!rst_n) reset_check;
    else for (b=0;b<B;b=b+1) begin
      desc_valid[b]=sent[b]<2;
      t=sent[b]<2 ? sent[b] : 1;
      desc_epoch[b*32+:32]=t+1; desc_output_base[b*32+:32]=output_base[b][t];
      desc_input_base[b*32+:32]=input_base[b][t]; desc_valid_rows[b*32+:32]=rows[b][t];
      desc_valid_inputs[b*32+:32]=inputs[b][t]; desc_fp16[b]=dtype; desc_awq[b]=awq;
      desc_proj[b*3+:3]=projection;
      compute_enable[b]=sent[b]==2 && second_request_seen[b] && (pending[b] || (cycle+b)%7<3);
      dot_out_ready[b]=dot_started && (cycle+b)%9<6;
      c_req_ready[b]=!pending[b] && (cycle+b)%7<5;
      c_rsp_valid[b]=pending[b] && due[b]<=cycle;
      c_rsp_rdata[b*32+:32]=c_rsp_valid[b] ? response[b] : 0;
    end
  end
endmodule
"""
