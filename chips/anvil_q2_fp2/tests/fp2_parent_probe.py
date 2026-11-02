"""Executed parent/compatibility baseline on matched independent compact tensors.

All projections and biases are zero; embeddings are distinct, gamma is one,
and genuine theta=1e6 coefficients are supplied. This diagnostic exercises
the complete architectural graph but does not establish nonzero projection
integration or official checkpoint accuracy.
"""

import argparse
from fractions import Fraction
import hashlib
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fp2_probe import Probe, ROOT, simulate
from fp2_reference import add, exact, finite, multiply, rope_coefficients, rounded, transcendental, ulp_distance
from fp2_top_probe import embedding


PARENT_TB = r"""
module tb;
  reg clk=0; always #5 clk=~clk;
  reg rst_n,cancel=0,token_valid=0,new_sequence=0,token_phase=0,logit_ready=0;
  reg [31:0] token_id=0,token_pos=0;
  wire token_ready,logit_valid,done,error,cancel_done;
  wire [31:0] logit_index,logit_data;
  wire req_valid,req_write,rsp_ready;
  reg req_ready=0,rsp_valid=0,rsp_error=0;
  wire [3:0] req_kind;
  wire [2:0] req_proj;
  wire [31:0] req_layer,req_row,req_col,req_wdata;
  wire [63:0] req_tag;
  reg [63:0] rsp_tag=0;
  reg [31:0] rsp_data=0;
  @MODULE@ #(.NUM_LAYERS(1),.HIDDEN_SIZE(48),.INTERMEDIATE_SIZE(64),
    .NUM_Q_HEADS(6),.NUM_KV_HEADS(1),.HEAD_DIM(8),.GROUP_SIZE(8),
    .VOCAB_SIZE(16),.MAX_SEQ_LEN(3),.BANKS(1),.CACHE_BLOCK(8),.QUEUE_DEPTH(3),
    .FP_FORMAT(@FORMAT@),.WEIGHT_MODE(@WEIGHT@),.CACHE_MODE(@CACHE@) @PARAMETERS@) accelerator(
    .clk(clk),.rst_n(rst_n),.cancel(cancel),.token_valid(token_valid),.token_ready(token_ready),
    .token_id(token_id),.token_pos(token_pos),.new_sequence(new_sequence),.token_phase(token_phase),
    .logit_valid(logit_valid),.logit_ready(logit_ready),.logit_index(logit_index),.logit_data(logit_data),
    .done(done),.error(error),.cancel_done(cancel_done),
    .mem_req_valid(req_valid),.mem_req_ready(req_ready),.mem_req_write(req_write),
    .mem_req_kind(req_kind),.mem_req_layer(req_layer),.mem_req_proj(req_proj),
    .mem_req_row(req_row),.mem_req_col(req_col),.mem_req_wdata(req_wdata),.mem_req_tag(req_tag),
    .mem_rsp_valid(rsp_valid),.mem_rsp_error(rsp_error),.mem_rsp_ready(rsp_ready),
    .mem_rsp_rdata(rsp_data),.mem_rsp_tag(rsp_tag) @PORTS@);
  reg [15:0] embeddings[0:767];
  reg [31:0] coefficients[0:23],scratch[0:959],kv[0:6][0:11];
  reg occupied[0:15];
  reg [63:0] tags[0:15];
  reg [31:0] responses[0:15];
  integer due[0:15];
  reg [31:0] command_token[0:7],command_pos[0:7];
  reg command_new[0:7],command_phase[0:7];
  integer command_count,command_index=0,accepted_tokens=0,completed_tokens=0;
  integer fd,n,i,j,cycle=0,slot,selected,active_response=-1,oldest;
  integer outstanding=0,maximum_outstanding=0,reordered=0,reads=0,writes=0,responses_count=0;
  integer logits=0,total_logits=0,request_stalls=0,logit_stalls=0;
  integer scan_token,scan_pos,scan_new,scan_phase;
  reg [15:0] scan_half;
  reg [31:0] scan_word;
  reg [31:0] random_state=17;
  reg held_request=0,held_logit=0,last_logit_accept=0,response_accepted;
  reg [199:0] saved_request;
  reg [63:0] saved_logit;
  reg [63:0] protocol_digest=64'hcbf29ce484222325;
  wire [199:0] request_payload={req_write,req_kind,req_layer,req_proj,req_row,req_col,req_wdata,req_tag};
  wire reset_ok=({token_ready,logit_valid,logit_index,logit_data,done,error,cancel_done,
    req_valid,req_write,req_kind,req_layer,req_proj,req_row,req_col,req_wdata,req_tag,rsp_ready}===0);
  string image_path,command_path,coefficient_path;
  always @(posedge clk) if(!rst_n && reset_ok !== 1'b1) $fatal(1,"RESET posedge");
  always @(negedge clk) if(!rst_n && reset_ok !== 1'b1) $fatal(1,"RESET negedge");
  function automatic [31:0] memory_read(input [3:0] kind,input [31:0] row,column);
    begin
      memory_read=0;
      case(kind)
        0: begin
          if(row>=16 || column>=48) $fatal(1,"EMBEDDING_RANGE");
          memory_read={16'd0,embeddings[row*48+column]};
        end
        1,2,4: memory_read=0;
        3,5,6,7: memory_read=@ONE@;
        8: begin
          if(row>=15 || column>=64) $fatal(1,"SCRATCH_RANGE");
          memory_read=scratch[row*64+column];
        end
        9,10,12,13: begin
          if(row>=3 || column>=4) $fatal(1,"KV_RANGE");
          memory_read=kv[kind-9][row*4+column];
        end
        14,15: begin
          if(row>=3 || column!=0) $fatal(1,"KV_SCALE_RANGE");
          memory_read=kv[kind-9][row*4+column];
        end
        11: begin
          if(row>=3 || column>=8) $fatal(1,"ROPE_RANGE");
          memory_read=coefficients[row*8+column];
        end
        default: $fatal(1,"UNKNOWN_READ_KIND %0d",kind);
      endcase
    end
  endfunction
  task automatic memory_write;
    begin
      if(req_kind==8) begin
        if(req_row>=15 || req_col>=64) $fatal(1,"SCRATCH_WRITE_RANGE");
        scratch[req_row*64+req_col]=req_wdata;
      end else if(req_kind>=9 && req_kind<=15 && req_kind!=11) begin
        if(req_row>=3 || req_col>=4) $fatal(1,"KV_WRITE_RANGE");
        kv[req_kind-9][req_row*4+req_col]=req_wdata;
      end else $fatal(1,"UNKNOWN_WRITE_KIND");
    end
  endtask
  initial begin
    rst_n=0; #1; if(reset_ok !== 1'b1) $fatal(1,"RESET time0");
    for(i=0;i<16;i=i+1) occupied[i]=0;
    for(i=0;i<960;i=i+1) scratch[i]=0;
    for(i=0;i<7;i=i+1) for(j=0;j<12;j=j+1) kv[i][j]=0;
    if(!$value$plusargs("IMAGE=%s",image_path) ||
       !$value$plusargs("COMMANDS=%s",command_path) ||
       !$value$plusargs("COEFFICIENTS=%s",coefficient_path) ||
       !$value$plusargs("SEED=%d",random_state)) $fatal(1,"missing fixture argument");
    fd=$fopen(image_path,"r"); if(!fd) $fatal(1,"image open");
    for(i=0;i<768;i=i+1) begin
      n=$fscanf(fd,"%h\n",scan_half); if(n!=1) $fatal(1,"image length");
      embeddings[i]=scan_half;
    end
    $fclose(fd);
    fd=$fopen(coefficient_path,"r"); if(!fd) $fatal(1,"coefficient open");
    for(i=0;i<24;i=i+1) begin
      n=$fscanf(fd,"%h\n",scan_word); if(n!=1) $fatal(1,"coefficient length");
      coefficients[i]=scan_word;
    end
    $fclose(fd);
    fd=$fopen(command_path,"r"); if(!fd) $fatal(1,"command open");
    n=$fscanf(fd,"%d\n",command_count);
    if(n!=1 || command_count<1 || command_count>8) $fatal(1,"command count");
    for(i=0;i<command_count;i=i+1) begin
      n=$fscanf(fd,"%d %d %d %d\n",scan_token,scan_pos,scan_new,scan_phase);
      if(n!=4) $fatal(1,"command length");
      command_token[i]=scan_token; command_pos[i]=scan_pos;
      command_new[i]=scan_new; command_phase[i]=scan_phase;
    end
    $fclose(fd);
    repeat(2) @(negedge clk); rst_n=1; token_valid=1;
    token_id=command_token[0]; token_pos=command_pos[0];
    new_sequence=command_new[0]; token_phase=command_phase[0];
    while(cycle<5000000) begin
      random_state=random_state^(random_state<<13);
      random_state=random_state^(random_state>>17);
      random_state=random_state^(random_state<<5);
      req_ready=random_state[2:0]!=0;
      logit_ready=(random_state[5:3]!=0) && (!logit_valid || logit_stalls>=3);
      if(!rsp_valid) begin
        selected=-1; oldest=-1;
        for(i=0;i<16;i=i+1) if(occupied[i]) begin
          if(oldest==-1 || tags[i]<tags[oldest]) oldest=i;
          if(due[i]<=cycle && (selected==-1 || tags[i]>tags[selected])) selected=i;
        end
        if(selected!=-1) begin
          if(selected!=oldest) reordered=reordered+1;
          active_response=selected; rsp_valid=1;
          rsp_tag=tags[selected]; rsp_data=responses[selected];
        end
      end
      @(posedge clk);
      if((^{token_ready,logit_valid,done,error,cancel_done,req_valid,req_write,rsp_ready}) === 1'bx)
        $fatal(1,"PARENT_CONTROL_X");
      if(held_request && (req_valid !== 1'b1 || request_payload !== saved_request))
        $fatal(1,"PARENT_STALLED_REQUEST");
      if(held_logit && (logit_valid !== 1'b1 || {logit_index,logit_data} !== saved_logit))
        $fatal(1,"PARENT_STALLED_LOGIT");
      held_request=req_valid && !req_ready;
      if(held_request) begin saved_request=request_payload; request_stalls=request_stalls+1; end
      held_logit=logit_valid && !logit_ready;
      if(held_logit) begin saved_logit={logit_index,logit_data}; logit_stalls=logit_stalls+1; end
      protocol_digest=(protocol_digest ^ {54'd0,token_ready,logit_valid,done,error,
        cancel_done,req_valid,req_write,rsp_ready,req_ready,rsp_valid})*64'h100000001b3;
      if(token_valid && token_ready) accepted_tokens=accepted_tokens+1;
      response_accepted=rsp_valid && rsp_ready;
      if(response_accepted) begin
        if(active_response<0 || !occupied[active_response]) $fatal(1,"PARENT_UNMATCHED_RESPONSE");
        occupied[active_response]=0; outstanding=outstanding-1; responses_count=responses_count+1;
      end
      if(req_valid && req_ready) begin
        if((^request_payload) === 1'bx) $fatal(1,"PARENT_REQUEST_X");
        protocol_digest=(protocol_digest ^ req_tag ^ req_row ^ req_col ^ req_wdata)*64'h100000001b3;
        slot=-1;
        for(i=0;i<16;i=i+1) begin
          if(occupied[i] && tags[i]==req_tag) $fatal(1,"PARENT_LIVE_TAG_REUSE");
          if(!occupied[i]) slot=i;
        end
        if(slot<0) $fatal(1,"PARENT_QUEUE_OVERFLOW");
        occupied[slot]=1; tags[slot]=req_tag; due[slot]=cycle+2+random_state[9:6];
        if(req_write) begin memory_write(); writes=writes+1; responses[slot]=0; end
        else begin responses[slot]=memory_read(req_kind,req_row,req_col); reads=reads+1; end
        outstanding=outstanding+1;
        if(outstanding>maximum_outstanding) maximum_outstanding=outstanding;
      end
      if(logit_valid && logit_ready) begin
        if((^{logit_index,logit_data}) === 1'bx || (&logit_data[30:23]) || logit_index!=logits)
          $fatal(1,"PARENT_LOGIT_ORDER_FINITE_X");
        $display("LOGIT %0d %0d %08h",command_index,logit_index,logit_data);
        protocol_digest=(protocol_digest ^ {logit_index,logit_data})*64'h100000001b3;
        logits=logits+1; total_logits=total_logits+1;
      end
      if(done) begin
        if(error || logits!=16 || accepted_tokens!=command_index+1 || outstanding!=0 ||
           !last_logit_accept) $fatal(1,"PARENT_COMPLETION");
        $display("TOKEN_DONE %0d %0d",command_index,cycle);
        command_index=command_index+1; logits=0;
        if(command_index==command_count) begin
          $display("SUMMARY %0d %0d %0d %0d %0d %0d %0d %0d %0d %016h",
            cycle,reads,writes,responses_count,maximum_outstanding,reordered,
            logit_stalls,request_stalls,total_logits,protocol_digest);
          $finish;
        end
      end
      last_logit_accept=logit_valid && logit_ready && logit_index==15;
      @(negedge clk);
      token_valid=accepted_tokens==command_index;
      if(command_index<command_count) begin
        token_id=command_token[command_index]; token_pos=command_pos[command_index];
        new_sequence=command_new[command_index]; token_phase=command_phase[command_index];
      end
      if(response_accepted) begin rsp_valid=0; active_response=-1; end
      cycle=cycle+1;
    end
    $fatal(1,"PARENT_CYCLE_BOUND");
  end
endmodule
"""


COMPAT_PORTS = """
    ,.ddr_req_ready(1'b1),.ddr_rsp_valid(1'b0),.ddr_rsp_error(1'b0),
    .ddr_rsp_tag(64'd0),.ddr_rsp_rdata(512'd0),
    .csr_req_valid(1'b0),.csr_req_write(1'b0),.csr_req_addr(16'd0),
    .csr_req_wdata(32'd0),.csr_req_wstrb(4'd0),.csr_rsp_ready(1'b1)
"""


def with_public_pin_comparator(text):
    outputs = {
        "token_ready": 1, "logit_valid": 1, "logit_index": 32, "logit_data": 32,
        "done": 1, "error": 1, "cancel_done": 1, "req_valid": 1, "req_write": 1,
        "req_kind": 4, "req_layer": 32, "req_proj": 3, "req_row": 32,
        "req_col": 32, "req_wdata": 32, "req_tag": 64, "rsp_ready": 1,
    }
    ports = {
        "token_ready": "token_ready", "logit_valid": "logit_valid", "logit_index": "logit_index",
        "logit_data": "logit_data", "done": "done", "error": "error", "cancel_done": "cancel_done",
        "mem_req_valid": "req_valid", "mem_req_write": "req_write", "mem_req_kind": "req_kind",
        "mem_req_layer": "req_layer", "mem_req_proj": "req_proj", "mem_req_row": "req_row",
        "mem_req_col": "req_col", "mem_req_wdata": "req_wdata", "mem_req_tag": "req_tag",
        "mem_rsp_ready": "rsp_ready",
    }
    inputs = {
        "clk": "clk", "rst_n": "rst_n", "cancel": "cancel", "token_valid": "token_valid",
        "token_id": "token_id", "token_pos": "token_pos", "new_sequence": "new_sequence",
        "token_phase": "token_phase", "logit_ready": "logit_ready", "mem_req_ready": "req_ready",
        "mem_rsp_valid": "rsp_valid", "mem_rsp_error": "rsp_error", "mem_rsp_rdata": "rsp_data",
        "mem_rsp_tag": "rsp_tag",
    }
    start = text.index("  anvil_q2_fp2_top #(")
    end = text.index(" accelerator(", start)
    parameters = text[start:end].replace("anvil_q2_fp2_top", "anvil_q2_fp_top").replace(",.ACCEL_ENABLE(0)", "")
    declarations = "".join(f"wire [{size-1}:0] reference_{name};\n" for name, size in outputs.items())
    connections = [f".{port}(reference_{signal})" for port, signal in ports.items()]
    connections += [f".{port}({signal})" for port, signal in inputs.items()]
    actual = "{" + ",".join(outputs) + "}"
    reference = "{" + ",".join(f"reference_{name}" for name in outputs) + "}"
    comparator = f"""
  {declarations}
  {parameters} independent_parent({','.join(connections)});
  integer pin_comparisons=0;
  always @(posedge clk or negedge clk) begin
    if(rst_n) begin
      if({actual} !== {reference}) $fatal(1,"COMPATIBILITY_PUBLIC_PIN_MISMATCH");
      pin_comparisons=pin_comparisons+1;
    end
  end
"""
    text = text.replace("  reg [15:0] embeddings[0:767];", comparator + "\n  reg [15:0] embeddings[0:767];")
    return text.replace("          $finish;", '          $display("PIN_COMPARISONS %0d",pin_comparisons);\n          $finish;')


def expected_logits(token, fp_format, embedding_fn=embedding):
    fraction_bits, exponent_bits = (7, 8) if fp_format == 0 else (10, 5)
    values = [embedding_fn(token, column) for column in range(48)]
    vector = [rounded(exact(value, fraction_bits=7)) for value in values]
    total = 0
    for value in vector:
        total = add(total, multiply(value, value))
    inverse = transcendental(add(multiply(total, rounded(Fraction(1, 48))), 0x358637BD), "rsqrt")
    narrowed = [rounded(exact(multiply(value, inverse)), fraction_bits=fraction_bits,
                        exponent_bits=exponent_bits) for value in vector]
    normalized = [rounded(exact(value, fraction_bits=fraction_bits, exponent_bits=exponent_bits))
                  for value in narrowed]
    results = []
    for row in range(16):
        result = 0
        for column, value in enumerate(normalized):
            weight = rounded(exact(embedding_fn(row, column), fraction_bits=7))
            result = add(result, multiply(value, weight))
        results.append(result)
    return results


def run(probe, simulator="verilator", compatibility=False, fp_format=0,
        weight_mode=0, cache_mode=0, commands=None, seed=17, binary=None, expanded_sources=None,
        dual_reference=False, embedding_fn=embedding, tb_template=PARENT_TB,
        expected_results=None):
    commands = commands or [(3, 0, 1, 0)]
    if simulator == "iverilog" and len(commands) > 1:
        simulator = "verilator"
    source = probe.directory / "tb.sv"
    text = tb_template.replace("@MODULE@", "anvil_q2_fp2_top" if compatibility else "anvil_q2_fp_top")
    if simulator == "iverilog":
        text = text.replace("cycle<5000000", "cycle<500000")
    for needle, value in (("@FORMAT@", fp_format), ("@WEIGHT@", weight_mode), ("@CACHE@", cache_mode)):
        text = text.replace(needle, str(value))
    text = text.replace("@PARAMETERS@", ",.ACCEL_ENABLE(0)" if compatibility else "")
    text = text.replace("@PORTS@", COMPAT_PORTS if compatibility else "")
    text = text.replace("@ONE@", "32'h00003f80" if fp_format == 0 else "32'h00003c00")
    if dual_reference:
        if not compatibility:
            raise ValueError("public-pin comparator requires compatibility DUT")
        text = with_public_pin_comparator(text)
    source.write_text(text)
    images = probe.directory / "checkpoint-images"
    images.mkdir()
    image, command_image, coefficients = (images / name for name in
                                          ("embeddings.hex", "commands.txt", "rope.hex"))
    image.write_text("".join(
        f"{embedding_fn(row, c) if fp_format == 0 else rounded(exact(embedding_fn(row, c), fraction_bits=7), fraction_bits=10, exponent_bits=5):04x}\n"
        for row in range(16) for c in range(48)))
    command_image.write_text(str(len(commands)) + "\n" +
                             "".join(" ".join(map(str, command)) + "\n" for command in commands))
    coefficients.write_text("".join(
        f"{value:08x}\n" for position in range(3) for pair in range(4)
        for value in rope_coefficients(position, pair, 8)))
    rtl = expanded_sources or sorted((ROOT / "anvil_q2_fp_reference/rtl").glob("*.sv"))
    if compatibility:
        rtl += sorted((ROOT / "rtl").glob("*.sv"))
    arguments = [f"+IMAGE={image.relative_to(ROOT)}", f"+COMMANDS={command_image.relative_to(ROOT)}",
                 f"+COEFFICIENTS={coefficients.relative_to(ROOT)}", f"+SEED={seed}"]
    if binary:
        probe.receipt["executable_sha256"] = hashlib.sha256(binary.read_bytes()).hexdigest()
        output = probe.command([str(binary), *arguments], "simulation")
    else:
        output = simulate(probe, source, rtl, simulator, arguments)
    expected = (expected_results if expected_results is not None else
                [expected_logits(command[0], fp_format, embedding_fn) for command in commands])
    logits, completions, summary = {}, [], None
    pin_comparisons = None
    metrics = []
    for line in output.read_text().splitlines():
        words = line.split()
        if words[:1] == ["LOGIT"]:
            command, index, value = int(words[1]), int(words[2]), int(words[3], 16)
            if (command, index) in logits or not 0 <= command < len(commands) or not 0 <= index < 16:
                raise AssertionError("parent duplicate/out-of-range logit")
            logits[command, index] = value
            reference = expected[command][index]
            error = abs(exact(value) - exact(reference)) if finite(value) else None
            threshold = Fraction(5, 10000) * (1 + abs(exact(reference)))
            metrics.append({"ulp": ulp_distance(reference, value),
                            "absolute": float(error) if error is not None else None,
                            "relative": float(error / abs(exact(reference)))
                            if error is not None and exact(reference) else None})
            probe.compare("parent-independent-logit", True, error is not None and error <= threshold,
                          {"command": command, "index": index, "observed": f"{value:08x}",
                           "reference": f"{reference:08x}", "absolute_error": float(error) if error is not None else None})
        elif words[:1] == ["TOKEN_DONE"]:
            completions.append((int(words[1]), int(words[2])))
        elif words[:1] == ["SUMMARY"]:
            summary = [*map(int, words[1:10]), words[10]]
        elif words[:1] == ["PIN_COMPARISONS"]:
            pin_comparisons = int(words[1])
    probe.compare("parent-logit-count", 16 * len(commands), len(logits), {})
    probe.compare("parent-completion-order", list(range(len(commands))), [row[0] for row in completions], {})
    if summary is None:
        raise AssertionError("missing parent accounting summary")
    probe.compare("parent-response-conservation", summary[1] + summary[2], summary[3], {})
    for name, index in (("scratch-and-cache-writes", 2), ("logit-stalls", 6), ("request-stalls", 7)):
        probe.compare(name, True, summary[index] > 0, {})
    probe.summary["transactions"] = dict(zip(
        ("cycles", "read_words", "write_words", "responses", "maximum_outstanding",
         "reordered_responses", "logit_stalls", "request_stalls", "logits", "protocol_digest"), summary, strict=True))
    probe.summary["completion_cycles"] = completions
    probe.summary["logit_bits"] = [[command, index, value] for (command, index), value in sorted(logits.items())]
    probe.summary["numerical_metrics"] = metrics
    probe.summary["configuration"] = {
        "compatibility": compatibility, "fp_format": fp_format, "weight_mode": weight_mode,
        "cache_mode": cache_mode, "seed": seed, "commands": commands}
    if dual_reference:
        probe.compare("compatibility-public-pin-comparison-count", True,
                      pin_comparisons is not None and pin_comparisons > 0, {})
        probe.summary["public_pin_comparisons"] = pin_comparisons


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compatibility", action="store_true")
    parser.add_argument("--fp-format", type=int, choices=(0, 1), default=0)
    parser.add_argument("--weight-mode", type=int, choices=(0, 1), default=0)
    parser.add_argument("--cache-mode", type=int, choices=(0, 1), default=0)
    parser.add_argument("--multi-token", action="store_true")
    parser.add_argument("--seed", type=int, choices=(17, 89, 203), default=17)
    parser.add_argument("--repair-of")
    parser.add_argument("--dual-reference", action="store_true")
    args = parser.parse_args()
    probe = Probe("parent", args.repair_of)
    try:
        commands = [(3, 0, 1, 0), (5, 1, 0, 0), (7, 2, 0, 1),
                    (4, 0, 1, 0), (8, 1, 0, 1)] if args.multi_token else None
        run(probe, compatibility=args.compatibility, fp_format=args.fp_format,
            weight_mode=args.weight_mode, cache_mode=args.cache_mode, commands=commands, seed=args.seed,
            dual_reference=args.dual_reference)
        return probe.settle()
    except Exception as error:
        return probe.settle(f"{type(error).__name__}: {error}")


if __name__ == "__main__":
    raise SystemExit(main())
