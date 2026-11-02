"""Real target-decoder speculative batches and exact deferred-final continuation."""

import copy
import json

from execution import ROOT, relative
from integration import TOP_BENCH
from model import Decoder, Geometry, Image
import reference as fp


def replace_once(text, old, new):
    if text.count(old) != 1:
        raise AssertionError(f"verification transactor adaptation not unique: {old[:100]}")
    return text.replace(old, new)


def speculative_bench():
    text = TOP_BENCH
    replacements = [
        ("parameter H=8,I=8,QH=2,KH=1,D=8,V=8,M=16,N=1;",
         "parameter H=8,I=8,QH=2,KH=1,D=8,V=8,M=16,N=1,T=3;"),
        ("wire csr_ready,csr_rsp_valid,csr_error;",
         "wire csr_ready,csr_rsp_valid,csr_error;\n"
         "  reg csr_valid=0,configured_mode=0;\n"
         "  integer active_tx=0,total_frames=0,draft_seen=0,tx_token_seen=0;\n"
         "  reg new_evaluation=1;\n"
         "  reg [31:0] eval_tokens[0:N-1],host_positions[0:T-1];\n"
         "  reg [31:0] expected_counts[0:T-1],expected_frames[0:T-1];\n"
         "  reg [31:0] expected_committed[0:T*5-1],draft_counts[0:T-1];\n"
         "  reg [127:0] draft_token_image[0:T-1];\n"
         "  reg [11:0] draft_parent_image[0:T-1];"),
        (".draft_valid(draft_valid),.draft_ready(draft_ready),.draft_count(3'd0),\n"
         "    .draft_tokens(128'd0),.draft_parents(12'd0),.commit_valid(commit_valid),",
         ".draft_valid(draft_valid),.draft_ready(draft_ready),\n"
         "    .draft_count(draft_counts[active_tx][2:0]),\n"
         "    .draft_tokens(draft_token_image[active_tx]),\n"
         "    .draft_parents(draft_parent_image[active_tx]),.commit_valid(commit_valid),"),
        (".csr_valid(1'b0),.csr_ready(csr_ready),.csr_write(1'b0),.csr_addr(12'd0),\n"
         "    .csr_wdata(32'd0),.csr_wstrb(4'd0),.csr_rsp_valid(csr_rsp_valid),",
         ".csr_valid(csr_valid),.csr_ready(csr_ready),.csr_write(1'b1),.csr_addr(12'h008),\n"
         "    .csr_wdata(32'd1),.csr_wstrb(4'hf),.csr_rsp_valid(csr_rsp_valid),"),
        ("commit_ready=(cycle%11>=5);",
         "commit_ready=(cycle%11>=5);\n"
         "      draft_valid=!draft_seen;"),
        ("if (error!==0 || cancel_done!==0 || think_active!==0 || draft_ready!==0)",
         "if (error!==0 || cancel_done!==0 || think_active!==configured_mode)"),
        ("active_case,cycle,error,cancel_done,think_active,draft_ready);",
         "active_case,cycle,error,cancel_done,think_active,draft_ready);\n"
         "      if (token_valid && token_ready) begin\n"
         "        if (tx_token_seen || draft_ready!==0) $fatal(1,\"SPEC_TOKEN_ORDER\");\n"
         "        tx_token_seen=1;\n"
         "      end\n"
         "      if (draft_valid && draft_ready) begin\n"
         "        if (!tx_token_seen || host_phases[active_tx]!=1 || draft_seen ||\n"
         "            logit_count!=V || queued!=0 || host_positions[active_tx]==M-1)\n"
         "          $fatal(1,\"SPEC_DRAFT_ORDER\");\n"
         "        draft_seen=1;\n"
         "      end"),
        ("read_data=0;\n        if (mem_req_write) begin",
         "read_data=0;\n"
         "        if (new_evaluation) begin\n"
         "          if (active_case>=N || mem_req_write || mem_req_kind!=0 ||\n"
         "              mem_req_row!==eval_tokens[active_case] || mem_req_col!=0)\n"
         "            $fatal(1,\"SPEC_OFFPATH_OR_WRONG_INPUT eval=%0d row=%0d expected=%0d\",\n"
         "              active_case,mem_req_row,eval_tokens[active_case]);\n"
         "          for (j=0;j<15*MAX;j=j+1) begin writes[j]=0;scratch_valid[j]=0;end\n"
         "          new_evaluation=0;\n"
         "        end\n"
         "        if (mem_req_write) begin"),
        ("if (logit_count>=V || logit_index!==logit_count ||\n"
         "            logit_data!==expected_logits[active_case*V+logit_count])",
         "if (active_case>=N || total_frames>=expected_frames[active_tx] ||\n"
         "            logit_index!==(logit_count%V) ||\n"
         "            logit_data!==expected_logits[active_case*V+(logit_count%V)])"),
        ("active_case,logit_count,logit_index,logit_data,expected_logits[active_case*V+logit_count]);",
         "active_case,logit_count,logit_index,logit_data,expected_logits[active_case*V+(logit_count%V)]);"),
        ("logit_count=logit_count+1;last_logit_cycle=cycle;",
         "logit_count=logit_count+1;last_logit_cycle=cycle;\n"
         "        if (logit_count%V==0) begin\n"
         "          total_frames=total_frames+1;active_case=active_case+1;new_evaluation=1;\n"
         "        end"),
        ("if (host_phases[active_case]!=1 || logit_count!=V || queued!=0 ||\n"
         "            commit_count!==3'd1 || commit_pos!==active_case+1 ||\n"
         "            commit_tokens!=={128'd0,expected_tokens[active_case]})",
         "if (host_phases[active_tx]!=1 || expected_counts[active_tx]==0 ||\n"
         "            total_frames!=expected_frames[active_tx] || queued!=0 ||\n"
         "            commit_count!==expected_counts[active_tx][2:0] ||\n"
         "            commit_pos!==host_positions[active_tx]+1)"),
        ("active_case,logit_count,commit_count,commit_pos,commit_tokens,expected_tokens[active_case]);",
         "active_tx,logit_count,commit_count,commit_pos,commit_tokens,expected_counts[active_tx]);\n"
         "        for (j=0;j<5;j=j+1) begin\n"
         "          if (commit_tokens[j*32+:32]!==expected_committed[active_tx*5+j])\n"
         "            $fatal(1,\"SPEC_COMMIT_TOKEN tx=%0d slice=%0d got=%0d expected=%0d\",\n"
         "              active_tx,j,commit_tokens[j*32+:32],expected_committed[active_tx*5+j]);\n"
         "        end"),
        ("if (logit_count!=V || queued!=0 || token_ready!==0 ||\n"
         "            cycle<=last_logit_cycle || (host_phases[active_case]==1 &&\n"
         "              (commit_seen!=1 || cycle<=last_commit_cycle))) $fatal(1,\"DONE_ORDER\");",
         "if (total_frames!=expected_frames[active_tx] || logit_count==0 ||\n"
         "            logit_count%V!=0 || queued!=0 || token_ready!==0 ||\n"
         "            cycle<=last_logit_cycle || (expected_counts[active_tx]>0 &&\n"
         "              (commit_seen!=1 || cycle<=last_commit_cycle)) ||\n"
         "            (expected_counts[active_tx]==0 && commit_seen)) $fatal(1,\"DONE_ORDER\");\n"
         "        if (host_phases[active_tx]==1 && host_positions[active_tx]<M-1 &&\n"
         "            configured_mode && !draft_seen) $fatal(1,\"SPEC_MISSING_DRAFT\");"),
        ('filename={prefix,"/expected-token.hex"};$readmemh(filename,expected_tokens);',
         'filename={prefix,"/expected-token.hex"};$readmemh(filename,expected_tokens);\n'
         '    filename={prefix,"/eval-token.hex"};$readmemh(filename,eval_tokens);\n'
         '    filename={prefix,"/host-position.hex"};$readmemh(filename,host_positions);\n'
         '    filename={prefix,"/expected-count.hex"};$readmemh(filename,expected_counts);\n'
         '    filename={prefix,"/expected-frames.hex"};$readmemh(filename,expected_frames);\n'
         '    filename={prefix,"/expected-committed.hex"};$readmemh(filename,expected_committed);\n'
         '    filename={prefix,"/draft-count.hex"};$readmemh(filename,draft_counts);\n'
         '    filename={prefix,"/draft-token.hex"};$readmemh(filename,draft_token_image);\n'
         '    filename={prefix,"/draft-parent.hex"};$readmemh(filename,draft_parent_image);'),
        ("for (c=0;c<N;c=c+1) begin\n"
         "      @(negedge clk);active_case=c;logit_count=0;commit_seen=0;\n"
         "      for (j=0;j<15*MAX;j=j+1) begin writes[j]=0;scratch_valid[j]=0;end",
         "for (c=0;c<T;c=c+1) begin\n"
         "      @(negedge clk);#1;active_tx=c;logit_count=0;commit_seen=0;\n"
         "      draft_seen=0;tx_token_seen=0;\n"
         "      if (c==1) begin\n"
         "        guard=0;\n"
         "        while (csr_ready!==1 && guard<100) begin @(negedge clk);#1;guard=guard+1;end\n"
         "        if (csr_ready!==1) $fatal(1,\"SPEC_CSR_READY\");\n"
         "        csr_valid=1;@(posedge clk);\n"
         "        if (csr_ready!==1) $fatal(1,\"SPEC_CSR_TRANSFER\");\n"
         "        #1;@(negedge clk);#1;csr_valid=0;\n"
         "        guard=0;\n"
         "        while (csr_rsp_valid!==1 && guard<100) begin @(negedge clk);#1;guard=guard+1;end\n"
         "        if (csr_rsp_valid!==1 || csr_error!==0) $fatal(1,\"SPEC_CSR_RESPONSE\");\n"
         "        @(posedge clk);#1;configured_mode=1;@(negedge clk);#1;\n"
         "      end"),
        ("token_id=host_tokens[c];token_pos=c;token_phase=host_phases[c];",
         "token_id=host_tokens[c];token_pos=host_positions[c];token_phase=host_phases[c];"),
        ("if (key_count!=(c+1)*KD || value_count!=(c+1)*KD) $fatal(1,\"KV_COVERAGE\");",
         "if (key_count!=total_frames*KD || value_count!=total_frames*KD)\n"
         "        $fatal(1,\"KV_COVERAGE\");"),
        ('$display("SUMMARY transactions=%0d logits=%0d key_writes=%0d value_writes=%0d memory_requests=%0d cycles=%0d",\n'
         "      completed,completed*V,key_count,value_count,req_count,cycle);",
         '$display("SUMMARY transactions=%0d frames=%0d logits=%0d key_writes=%0d value_writes=%0d memory_requests=%0d cycles=%0d",\n'
         "      completed,total_frames,total_frames*V,key_count,value_count,req_count,cycle);"),
    ]
    for old, new in replacements:
        text = replace_once(text, old, new)
    return text


def speculation_images(path, geometry, seed, prefix, branching=False):
    path.mkdir(exist_ok=False)
    image = Image(geometry, seed)
    decoder = Decoder(image)
    tables = image.memory_tables()
    tables.update({name: [] for name in (
        "expected-scratch", "expected-initial", "expected-key", "expected-value",
        "expected-logits", "host-token", "host-phase", "expected-token", "eval-token",
        "host-position", "expected-count", "expected-frames", "expected-committed",
        "draft-count", "draft-token", "draft-parent")})
    evaluations, transactions = [], []

    def evaluate(token, position):
        result = decoder.evaluate(token, position)
        tables["eval-token"].append(token)
        tables["expected-initial"].extend(result["initial"])
        tables["expected-key"].extend(result["keys"][0])
        tables["expected-value"].extend(result["values"][0])
        tables["expected-logits"].extend(result["logits"])
        scratch = [0] * (15 * geometry.maximum)
        for slot, values in result["stages"][0].items():
            scratch[slot * geometry.maximum:slot * geometry.maximum + len(values)] = values
        tables["expected-scratch"].extend(scratch)
        evaluations.append({"token": token, "position": position, "argmax": result["argmax"]})
        return result["argmax"]

    def transaction(token, position, phase, nodes, parents, generated):
        tables["host-token"].append(token)
        tables["host-position"].append(position)
        tables["host-phase"].append(phase)
        tables["expected-count"].append(len(generated))
        tables["expected-frames"].append(len(evaluations))
        tables["expected-token"].append(generated[-1] if generated else 0)
        tables["expected-committed"].extend(generated + [0] * (5 - len(generated)))
        tables["draft-count"].append(len(nodes))
        tables["draft-token"].append(fp.pack(nodes + [0] * (4 - len(nodes)), 32))
        tables["draft-parent"].append(fp.pack(parents + [0] * (4 - len(parents)), 3))
        transactions.append({"token": token, "position": position, "phase": phase,
                             "nodes": nodes, "parents": parents, "generated": generated,
                             "frames_through_transaction": len(evaluations)})

    prefill_token = 3 % geometry.vocabulary
    evaluate(prefill_token, 0)
    transaction(prefill_token, 0, 0, [], [], [])
    input_token = 4 % geometry.vocabulary
    target = evaluate(input_token, 1)
    preview = copy.deepcopy(decoder)
    available = min(4, geometry.max_sequence - 2)
    if prefix > available or branching and (prefix != 2 or available < 4):
        raise ValueError("speculative fixture exceeds legal capacity")
    greedy = [target]
    for position in range(2, 2 + available):
        greedy.append(preview.evaluate(greedy[-1], position)["argmax"])
    nodes = greedy[:available]
    if prefix < available:
        nodes[prefix] = (nodes[prefix] + 1) % geometry.vocabulary
    parents = [4, 0, 1, 2][:available]
    if branching:
        nodes = [(greedy[0] + 1) % geometry.vocabulary, greedy[0],
                 greedy[1], (greedy[0] + 2) % geometry.vocabulary]
        parents = [4, 4, 1, 0]
    generated = [target]
    for index in range(prefix):
        if 1 + len(generated) == geometry.max_sequence - 1:
            break
        generated.append(evaluate(generated[-1], 1 + len(generated)))
    transaction(input_token, 1, 1, nodes, parents, generated)
    deferred = generated[-1]
    next_position = 1 + len(generated)
    second_target = evaluate(deferred, next_position)
    if next_position == geometry.max_sequence - 1:
        transaction(deferred, next_position, 1, [], [], [])
    else:
        transaction(deferred, next_position, 1,
                    [(second_target + 1) % geometry.vocabulary], [4], [second_target])
    for name, values in tables.items():
        with (path / f"{name}.hex").open("x") as file:
            width = 32 if name == "draft-token" else 3 if name == "draft-parent" else 8
            file.writelines(f"{value:0{width}x}\n" for value in values)
    if [e["position"] for e in evaluations] != list(range(len(evaluations))):
        raise AssertionError("speculation oracle skipped or duplicated cache positions")
    return evaluations, transactions


def run_speculation(run, prefix=4, geometry=Geometry(), seed=17, branching=False):
    images = run.path / "checkpoint-images"
    evaluations, transactions = speculation_images(images, geometry, seed, prefix, branching)
    bench = run.path / "speculative_tb.sv"
    bench.write_text(speculative_bench())
    parameters = {"H": geometry.hidden, "I": geometry.intermediate,
                  "QH": geometry.q_heads, "KH": geometry.kv_heads, "D": geometry.head_dim,
                  "V": geometry.vocabulary, "M": geometry.max_sequence,
                  "N": len(evaluations), "T": len(transactions)}
    objects = run.path / "obj-speculative"
    sources = [p.relative_to(ROOT).as_posix() for p in sorted((ROOT / "rtl").glob("anvil_qn1_*.sv"))]
    run.execute(["verilator", "--binary", "--timing", "-Wno-fatal", "-j", "2",
                 "--top-module", "top_tb", *[f"-G{k}={v}" for k, v in parameters.items()],
                 "--Mdir", relative(objects), "-o", "simulate", *sources, relative(bench)],
                "speculation-compile")
    text = run.execute([relative(objects / "simulate"), f"+images={relative(images)}"],
                       "speculation-simulation")
    frames = len(evaluations)
    expected = (f"SUMMARY transactions=3 frames={frames} logits={frames*geometry.vocabulary} "
                f"key_writes={frames*geometry.kv_dimension} value_writes={frames*geometry.kv_dimension}")
    if text.count(expected) != 1:
        raise AssertionError("speculation full-frame/KV/continuation coverage missing")
    result = {"seed": seed, "geometry": vars(geometry), "prefix": prefix,
              "branching": branching, "evaluations": evaluations,
              "transactions": transactions, "raw_summary": text[-1000:]}
    (run.path / "speculation-reference.json").write_text(json.dumps(result, indent=2) + "\n")
    return result
