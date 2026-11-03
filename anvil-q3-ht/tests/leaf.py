"""Public-pin leaf experiments; expected values are produced by model.py."""

import random

from model import encode_kv, decode_kv, half_scale, mac


MAC_TB = r"""
module verify_mac;
  reg clk=0; always #5 clk=~clk;
  reg rst_n=0, flush=0, in_valid=0, out_ready=0;
  reg [63:0] q_nibbles=0, z_nibbles=0;
  reg [255:0] scale_f16=0;
  reg [511:0] activation_q16=0;
  reg [15:0] lane_mask=0;
  reg [159:0] in_meta=0;
  wire in_ready, out_valid, out_error;
  wire signed [72:0] out_sum;
  wire [159:0] out_meta;
  anvil_q3_ht_mac16 dut(.*);
  localparam N=@N@;
  reg [63:0] vectors_q [0:N-1], vectors_z [0:N-1];
  reg [255:0] vectors_scale [0:N-1];
  reg [511:0] vectors_activation [0:N-1];
  reg [15:0] vectors_mask [0:N-1];
  reg [72:0] expected_sum [0:N-1];
  reg expected_error [0:N-1];
  integer accepted_id [0:N-1], accepted_tick [0:N-1];
  integer head=0, tail=0, tick=0, next_id=0, cycle=0;
  integer compared=0, errors=0, bubbles=0, blocked=0, cancelled=0, consecutive=0;
  integer prior_accept=-2;
  reg expected_valid, advance, input_blocked=0;
  reg [31:0] random_state=@SEED@;
  function automatic [31:0] next_random(input [31:0] x);
    reg [31:0] y;
    begin y=x^(x<<13); y=y^(y>>17); next_random=y^(y<<5); end
  endfunction
  task reset_check;
    begin
      if ({in_ready,out_valid,out_error,out_sum,out_meta} !== 236'd0)
        $fatal(1,"MAC_RESET_XZ");
    end
  endtask
  always @(posedge clk) begin
    if (!rst_n) reset_check();
    else begin
      cycle=cycle+1;
      if (cycle>30000) $fatal(1,"MAC_NO_COMPLETION");
      if (flush) begin
        if ({in_ready,out_valid,out_error,out_sum,out_meta} !== 236'd0)
          $fatal(1,"MAC_FLUSH_VISIBILITY");
        cancelled=cancelled+tail-head;
        head=tail;
        input_blocked=0;
      end else begin
        expected_valid=(head<tail && tick-accepted_tick[head]>=9);
        advance=!expected_valid || out_ready;
        if (out_valid !== expected_valid || in_ready !== advance)
          $fatal(1,"MAC_NINE_STAGE_TIMING cycle=%0d advance_tick=%0d valid=%b expected=%b ready=%b",
                 cycle,tick,out_valid,expected_valid,in_ready);
        if (expected_valid) begin
          if (out_meta !== 160'(accepted_id[head]) ||
              out_error !== expected_error[accepted_id[head]] ||
              (!out_error && out_sum !== expected_sum[accepted_id[head]]))
            $fatal(1,"MAC_NUMERICAL id=%0d sum=%0d expected=%0d error=%b expected_error=%b",
                   accepted_id[head],$signed(out_sum),$signed(expected_sum[accepted_id[head]]),
                   out_error,expected_error[accepted_id[head]]);
          if (out_ready) begin
            compared=compared+1;
            errors=errors+32'(out_error);
            head=head+1;
          end else blocked=blocked+1;
        end else if ({out_error,out_sum,out_meta} !== 234'd0)
          $fatal(1,"MAC_INVALID_PAYLOAD");
        if (in_valid && in_ready) begin
          accepted_id[tail]=next_id;
          accepted_tick[tail]=tick;
          tail=tail+1; next_id=next_id+1;
          if (prior_accept==cycle-1) consecutive=consecutive+1;
          prior_accept=cycle;
        end else if (advance && !in_valid) bubbles=bubbles+1;
        if (advance) tick=tick+1;
        input_blocked=in_valid && !in_ready;
        if (next_id==N && head==tail) begin
          if (compared<4096 || errors==0 || blocked==0 || bubbles==0 ||
              consecutive==0 || cancelled==0)
            $fatal(1,"MAC_COVERAGE compared=%0d errors=%0d blocked=%0d bubbles=%0d cancelled=%0d",
                   compared,errors,blocked,bubbles,cancelled);
          $display("MAC_PASS compared=%0d errors=%0d blocked=%0d bubbles=%0d cancelled=%0d consecutive=%0d",
                   compared,errors,blocked,bubbles,cancelled,consecutive);
          $finish;
        end
      end
    end
  end
  always @(negedge clk) if (!rst_n) reset_check();
  initial begin
    $readmemh("@Q@",vectors_q);
    $readmemh("@Z@",vectors_z);
    $readmemh("@SCALE@",vectors_scale);
    $readmemh("@ACTIVATION@",vectors_activation);
    $readmemh("@MASK@",vectors_mask);
    $readmemh("@SUM@",expected_sum);
    $readmemh("@ERROR@",expected_error);
    #1; reset_check();
    repeat(3) @(negedge clk);
    rst_n=1;
    forever begin
      @(negedge clk);
      random_state=next_random(random_state);
      flush=(cycle==2048);
      out_ready=(cycle<32 || random_state[2:0]>=2);
      if (!input_blocked || flush) begin
        in_valid=(next_id<N && (cycle<32 || random_state[5:3]!=0));
        if (next_id<N) begin
          q_nibbles=vectors_q[next_id]; z_nibbles=vectors_z[next_id];
          scale_f16=vectors_scale[next_id]; activation_q16=vectors_activation[next_id];
          lane_mask=vectors_mask[next_id]; in_meta=160'(next_id);
        end
      end
    end
  end
endmodule
"""


def packed(values, bits):
    return sum((value & ((1 << bits) - 1)) << (i * bits) for i, value in enumerate(values))


def mac_vectors(seed, count=4352):
    rng = random.Random(seed)
    legal_scales = (0, 0x8000, 1, 0x007F, 0x0080, 0x0081, 0x03FF,
                    0x0400, 0x0800, 0x1000, 0x3C00, 0x3C01, 0x7BFF)
    invalid_scales = (0x8001, 0xBC00, 0x7C00, 0xFC00, 0x7C01, 0x7FFF)
    endpoints = (-(1 << 31), (1 << 31) - 1, -65536, 65536, -1, 1, 0)
    for index in range(count):
        q = [rng.randrange(16) for _ in range(16)]
        z = [rng.randrange(16) for _ in range(16)]
        scales = [rng.choice(legal_scales) for _ in range(16)]
        activations = [rng.choice(endpoints) if index < 512
                       else rng.randrange(-(1 << 31), 1 << 31) for _ in range(16)]
        mask = rng.randrange(1 << 16)
        if index < 256:
            lane = index % 16
            q[lane], z[lane] = index // 16, index % 16
            scales[lane], activations[lane], mask = 0x3C00, 65536, 1 << lane
        elif index < 272:
            lane = index - 256
            scales = [invalid_scales[index % len(invalid_scales)]] * 16
            scales[lane], mask = 0x3C00, 1 << lane
        elif index % 11 == 0:
            scales[index % 16] = invalid_scales[index % len(invalid_scales)]
            mask |= 1 << (index % 16)
        error = False
        try:
            total = mac(q, z, scales, activations, mask)
        except ValueError:
            total, error = 0, True
        yield dict(q=packed(q, 4), z=packed(z, 4), scale=packed(scales, 16),
                   activation=packed(activations, 32), mask=mask, sum=total, error=int(error))


def mac_bench(directory, relative, seed):
    directory = directory / "checkpoint-images"
    directory.mkdir(exist_ok=True)
    vectors = list(mac_vectors(seed))
    bench = MAC_TB.replace("@N@", str(len(vectors))).replace("@SEED@", str(seed))
    for name, width in dict(q=64, z=64, scale=256, activation=512,
                            mask=16, sum=73, error=1).items():
        path = directory / f"mac-{seed}-{name}.hex"
        path.write_text("".join(f"{vector[name] & ((1 << width) - 1):0{(width + 3) // 4}x}\n"
                                for vector in vectors))
        bench = bench.replace(f"@{name.upper()}@", relative(path))
    return bench
