"""Banked public memory transactor for complete independent decoder comparisons."""

from integration import TOP_BENCH, generate_images
from model import Geometry
from speculation_checks import replace_once
from execution import ROOT, relative


def banked_bench():
    text = replace_once(
        TOP_BENCH, "parameter H=8,I=8,QH=2,KH=1,D=8,V=8,M=16,N=1;",
        "parameter H=8,I=8,QH=2,KH=1,D=8,V=8,M=16,N=1,B=8,QUEUE=3;")
    text = replace_once(text, ".BANKS(1),.QUEUE_DEPTH(3)", ".BANKS(B),.QUEUE_DEPTH(QUEUE)")
    fields = {"mem_req_valid": 1, "mem_req_write": 1, "mem_req_ready": 1,
              "mem_req_kind": 4, "mem_req_proj": 3, "mem_req_layer": 32,
              "mem_req_row": 32, "mem_req_col": 32, "mem_req_wdata": 32,
              "mem_req_tag": 64, "mem_rsp_valid": 1, "mem_rsp_error": 1,
              "mem_rsp_ready": 1, "mem_rsp_rdata": 32, "mem_rsp_tag": 64}
    declarations = []
    for name, width in fields.items():
        declarations.append(f"wire [B*{width}-1:0] bank_{name};")
        text = replace_once(text, f".{name}({name})", f".{name}(bank_{name})")
        if name.startswith("mem_req_") and name != "mem_req_ready":
            declarations.append(
                f"assign {name}=bank_{name}[request_bank*{width}+:{width}];")
    declarations.extend([
        "assign bank_mem_req_ready=mem_req_ready ? (B'(1)<<request_bank) : 0;",
        "assign bank_mem_rsp_valid=mem_rsp_valid ? (B'(1)<<response_bank) : 0;",
        "assign bank_mem_rsp_error=mem_rsp_error ? (B'(1)<<response_bank) : 0;",
        "assign bank_mem_rsp_rdata=(B*32)'(mem_rsp_rdata)<<(response_bank*32);",
        "assign bank_mem_rsp_tag=(B*64)'(mem_rsp_tag)<<(response_bank*64);",
        "assign mem_rsp_ready=bank_mem_rsp_ready[response_bank];",
        "integer request_bank=0,response_bank=0,response_slot=0,b,o,slot;",
        "integer queue_bank[0:63],bank_requests[0:B-1],reordered=0;",
        "reg [B-1:0] held_banks=0;",
        "reg [199:0] bank_saved[0:B-1];",
    ])
    text = replace_once(text, "reg [4095:0] prefix;",
                        "\n  ".join(declarations) + "\n  reg [4095:0] prefix;")
    text = replace_once(
        text, '$fatal(1,"TOP_RESET_XZ_OR_NONZERO");',
        '$fatal(1,"TOP_RESET_XZ_OR_NONZERO");\n'
        "      if ({bank_mem_req_valid,bank_mem_req_write,bank_mem_req_kind,\n"
        "           bank_mem_req_layer,bank_mem_req_proj,bank_mem_req_row,\n"
        "           bank_mem_req_col,bank_mem_req_wdata,bank_mem_req_tag,\n"
        "           bank_mem_rsp_ready}!==0) $fatal(1,\"BANK_RESET_XZ_OR_NONZERO\");")
    text = replace_once(
        text, "mem_req_ready=(cycle%7!=3);",
        "if (!held_request) begin\n"
        "        request_bank=0;\n"
        "        for (o=B-1;o>=0;o=o-1) begin\n"
        "          b=(cycle+o)%B;\n"
        "          if (bank_mem_req_valid[b]) request_bank=b;\n"
        "        end\n"
        "      end\n"
        "      mem_req_ready=(cycle%7!=3);")
    text = replace_once(
        text, "mem_rsp_valid=queued>0 && queue_delay[front]<=cycle;\n"
        "      mem_rsp_tag=mem_rsp_valid ? queue_tag[front] : 0;\n"
        "      mem_rsp_rdata=mem_rsp_valid ? queue_data[front] : 0;",
        "response_slot=front;mem_rsp_valid=0;\n"
        "      for (o=0;o<queued;o=o+1) begin\n"
        "        slot=(front+o)%64;\n"
        "        if (queue_delay[slot]<=cycle) begin\n"
        "          response_slot=slot;mem_rsp_valid=1;\n"
        "        end\n"
        "      end\n"
        "      response_bank=mem_rsp_valid ? queue_bank[response_slot] : 0;\n"
        "      mem_rsp_tag=mem_rsp_valid ? queue_tag[response_slot] : 0;\n"
        "      mem_rsp_rdata=mem_rsp_valid ? queue_data[response_slot] : 0;")
    text = replace_once(
        text, "cycle=cycle+1;",
        "cycle=cycle+1;\n"
        "      for (b=0;b<B;b=b+1) begin\n"
        "        if (held_banks[b] && (bank_mem_req_valid[b]!==1 ||\n"
        "            {bank_mem_req_write[b],bank_mem_req_kind[b*4+:4],\n"
        "             bank_mem_req_layer[b*32+:32],bank_mem_req_proj[b*3+:3],\n"
        "             bank_mem_req_row[b*32+:32],bank_mem_req_col[b*32+:32],\n"
        "             bank_mem_req_wdata[b*32+:32],bank_mem_req_tag[b*64+:64]}\n"
        "             !==bank_saved[b])) $fatal(1,\"BANK_REQUEST_STALL bank=%0d\",b);\n"
        "        held_banks[b]=bank_mem_req_valid[b] && !bank_mem_req_ready[b];\n"
        "        bank_saved[b]={bank_mem_req_write[b],bank_mem_req_kind[b*4+:4],\n"
        "          bank_mem_req_layer[b*32+:32],bank_mem_req_proj[b*3+:3],\n"
        "          bank_mem_req_row[b*32+:32],bank_mem_req_col[b*32+:32],\n"
        "          bank_mem_req_wdata[b*32+:32],bank_mem_req_tag[b*64+:64]};\n"
        "      end")
    text = replace_once(
        text, "if (queued<=0 || mem_rsp_tag!==queue_tag[front]) "
        '$fatal(1,"RESPONSE_SCOREBOARD");\n'
        "        front=(front+1)%64; queued=queued-1;",
        "if (queued<=0 || mem_rsp_tag!==queue_tag[response_slot] ||\n"
        "            response_bank!=queue_bank[response_slot]) "
        '$fatal(1,"RESPONSE_SCOREBOARD");\n'
        "        if (response_slot!=front) reordered=reordered+1;\n"
        "        queue_data[response_slot]=queue_data[front];\n"
        "        queue_tag[response_slot]=queue_tag[front];\n"
        "        queue_delay[response_slot]=queue_delay[front];\n"
        "        queue_bank[response_slot]=queue_bank[front];\n"
        "        front=(front+1)%64; queued=queued-1;")
    text = replace_once(text, "queue_data[tail]=read_data; queue_tag[tail]=mem_req_tag;",
                        "queue_data[tail]=read_data; queue_tag[tail]=mem_req_tag;\n"
                        "        queue_bank[tail]=request_bank;\n"
                        "        bank_requests[request_bank]=bank_requests[request_bank]+1;")
    text = replace_once(text, "queue_delay[tail]=cycle+2+(req_count%3);",
                        "queue_delay[tail]=cycle+2+((req_count*7)%19);")
    text = replace_once(text, "rst_n=0;\n    for (j=0;",
                        "rst_n=0;\n"
                        "    for (b=0;b<B;b=b+1) bank_requests[b]=0;\n"
                        "    for (j=0;")
    text = replace_once(
        text, '$display("SUMMARY transactions=%0d logits=%0d',
        "for (b=0;b<B;b=b+1) begin\n"
        "      if (bank_requests[b]==0) $fatal(1,\"UNEXERCISED_MEMORY_BANK\");\n"
        '      $display("BANK bank=%0d requests=%0d",b,bank_requests[b]);\n'
        "    end\n"
        '    $display("REORDER responses=%0d",reordered);\n'
        '$display("SUMMARY transactions=%0d logits=%0d')
    return text


def run_banked_top(run, geometry=Geometry(), seed=17, cases=6, banks=8, queue=3):
    images = run.path / "checkpoint-images"
    records = generate_images(images, geometry, seed, cases)
    bench = run.path / "banked_top_tb.sv"
    bench.write_text(banked_bench())
    parameters = {"H": geometry.hidden, "I": geometry.intermediate,
                  "QH": geometry.q_heads, "KH": geometry.kv_heads,
                  "D": geometry.head_dim, "V": geometry.vocabulary,
                  "M": geometry.max_sequence, "N": cases, "B": banks, "QUEUE": queue}
    objects = run.path / "obj-banked-top"
    sources = [p.relative_to(ROOT).as_posix()
               for p in sorted((ROOT / "rtl").glob("anvil_qn1_*.sv"))]
    unrolling = (["--unroll-count", "256", "--unroll-stmts", "100000"]
                 if banks * queue >= 128 else [])
    run.execute(["verilator", "--binary", "--timing", "-Wno-fatal", "-j", "2",
                 *unrolling,
                 "--top-module", "top_tb",
                 *[f"-G{k}={v}" for k, v in parameters.items()],
                 "--Mdir", relative(objects), "-o", "simulate", *sources, relative(bench)],
                "banked-top-compile")
    text = run.execute([relative(objects / "simulate"), f"+images={relative(images)}"],
                       "banked-top-simulation")
    summary = (f"SUMMARY transactions={cases} logits={cases*geometry.vocabulary} "
               f"key_writes={cases*geometry.kv_dimension} "
               f"value_writes={cases*geometry.kv_dimension}")
    if text.count(summary) != 1 or text.count("BANK bank=") != banks:
        raise AssertionError("missing banked decoder/full-frame/KV comparisons")
    import re
    match = re.search(r"REORDER responses=(\d+)", text)
    if match is None or banks > 1 and queue > 1 and int(match[1]) == 0:
        raise AssertionError("out-of-order bank responses not exercised")
    return {"geometry": vars(geometry), "seed": seed, "banks": banks,
            "queue_depth": queue, "transactions": records,
            "reordered_responses": int(match[1]), "raw_summary": text[-1500:]}


def run_memory_matrix(run):
    results = []
    for index, (banks, queue) in enumerate(
            ((1, 1), (8, 3), (1, 16), (8, 1), (1, 3), (8, 16))):
        geometry = Geometry(q_heads=2 if index % 2 == 0 else 4)
        seed = (17, 89, 203)[index % 3]
        results.append(run.component(
            f"memory-matrix-case{index:02d}",
            lambda child, banks=banks, queue=queue, geometry=geometry, seed=seed:
            run_banked_top(child, geometry=geometry, seed=seed, banks=banks, queue=queue)))
    return {"scope": "pairwise direct decode memory matrix, not full fault coverage",
            "cases": results, "compared_frames": sum(len(r["transactions"]) for r in results),
            "compared_logit_words": sum(
                len(r["transactions"]) * r["geometry"]["vocabulary"] for r in results)}
