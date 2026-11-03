"""Prefill observation of actual marker IDs, with no generated-token accounting."""

import hashlib
import json
import re

from execution import ROOT, relative
from marker_checks import MARKER_DRIVER, marker_reference, VOCABULARY
from speculation_checks import replace_once
import reference as fp


def prefill_driver():
    text = MARKER_DRIVER
    changes = [
        ("const std::array<U,2> host={opening ? 3U:151667U,target};",
         "const std::array<U,2> host={151667U,151668U};"),
        ("dut->new_sequence=0;dut->token_phase=1;",
         "dut->new_sequence=0;dut->token_phase=0;"),
        ("for (U tx=0;tx<2;++tx) {",
         "for (U tx=opening ? 0:1;tx<(opening ? 1U:2U);++tx) {"),
        ("dut->token_valid=1;dut->new_sequence=tx==0;",
         "dut->token_valid=1;dut->new_sequence=1;"),
        ("dut->token_id=host[tx];dut->token_pos=tx;",
         "dut->token_id=host[tx];dut->token_pos=0;"),
        ('check(!dut->error && !dut->cancel_done,"marker transaction fault");',
         'check(!dut->error && !dut->cancel_done && !dut->draft_ready &&\n'
         '              !dut->commit_valid,"PREFILL_MARKER_UNEXPECTED_PUBLICATION");'),
        ('row==tx && col<KD,"marker KV position"',
         'row==0 && col<KD,"marker KV position"'),
        ('row<=tx && col<KD,"marker causal KV position"',
         'row==0 && col<KD,"marker causal KV position"'),
        ('row==tx && col<8,"marker coefficient address"',
         'row==0 && col<8,"marker coefficient address"'),
        ("frame_words==vocabulary && commit_count==1 && cycle>last_logit &&\n"
         "                cycle>last_commit && frame_stalls && commit_stalls>=7 &&",
         "frame_words==vocabulary && commit_count==0 && cycle>last_logit &&\n"
         "                frame_stalls &&"),
        ("csr(false,0x028,0,opening ? 0:2);csr(false,0x030,0,opening ? 2:0);",
         "csr(false,0x028,0,0);csr(false,0x030,0,0);"),
        ("csr(false,0x050,0,opening ? 0:2);csr(false,0x058,0,0);",
         "csr(false,0x050,0,0);csr(false,0x058,0,0);"),
        ("csr(false,0x060,0,opening ? 0:2);csr(false,0x068,0,0);",
         "csr(false,0x060,0,0);csr(false,0x068,0,0);"),
        ("words==2*vocabulary && commits==2 && drafts==(opening ? 0U:2U)",
         "words==vocabulary && commits==0 && drafts==0"),
        ('"MARKER_SUMMARY opening="<<opening<<" frames=2 logits="',
         '"PREFILL_MARKER_SUMMARY opening="<<opening<<" frames=1 logits="'),
    ]
    for before, after in changes:
        text = replace_once(text, before, after)
    return text


def run_prefill_marker(run, opening=True, threads=8):
    images = run.path / "checkpoint-images"
    marker_reference(images, opening=False)
    rope = [value for position in range(2)
            for pair in zip(*fp.coefficients(8, position)) for value in pair]
    (images / "rope.hex").write_text("".join(f"{value:08x}\n" for value in rope))
    driver = run.path / "prefill_marker_driver.cpp"
    driver.write_text(prefill_driver())
    parameters = {"COMPACT": 1, "NUM_LAYERS": 1, "HIDDEN_SIZE": 8,
                  "INTERMEDIATE_SIZE": 8, "NUM_Q_HEADS": 2, "NUM_KV_HEADS": 1,
                  "HEAD_DIM": 8, "VOCAB_SIZE": VOCABULARY, "MAX_SEQ_LEN": 4,
                  "GROUP_SIZE": 8, "BANKS": 8, "QUEUE_DEPTH": 3}
    sources = [relative(p) for p in sorted((ROOT / "rtl").glob("anvil_qn1_*.sv"))]
    binding = {"driver_sha256": hashlib.sha256(driver.read_bytes()).hexdigest(),
               "parameters": parameters, "simulation_threads": threads,
               "rtl_sha256": {name: run.hashes[name] for name in sources},
               "tool_versions": {name: run.tool_versions[name]
                                 for name in ("verilator", "g++", "make")}}
    compiled = None
    receipts = []
    for parent in (ROOT / "evidence/preparation", ROOT / "evidence"):
        receipts.extend(parent.glob("*prefill-marker-*/receipt.json"))
    for path in sorted(receipts, key=lambda p: p.stat().st_mtime, reverse=True):
        receipt = json.loads(path.read_text())
        if receipt["status"] != "passed":
            continue
        candidate = receipt.get("results", {}).get("compiled")
        if candidate is None:
            continue
        binary = ROOT / candidate["binary"]
        if (candidate["binding"] == binding and binary.is_file() and
                hashlib.sha256(binary.read_bytes()).hexdigest() == candidate["binary_sha256"] and
                candidate.get("optimization") ==
                "OPT_FAST=-O3 OPT_SLOW=-O3 OPT_GLOBAL=-O3"):
            compiled = candidate
            break
    if compiled is None:
        from marker_builds import marker_build

        compiled = marker_build(run, driver.read_text(), binding, prefill=True)
    output = run.execute([compiled["binary"], relative(images),
                          str(int(opening)), str(threads)], "prefill-marker-simulation")
    records = re.findall(r"^PREFILL_MARKER_SUMMARY opening=(\d+) frames=1 logits=(\d+) "
                         r"commits=(\d+) drafts=(\d+) compared_writes=(\d+) "
                         r"requests=(\d+) cycles=(\d+)$", output, re.M)
    if len(records) != 1:
        raise AssertionError("missing/duplicate prefill marker comparisons")
    counts = list(map(int, records[0]))
    if counts[:5] != [int(opening), VOCABULARY, 0, 0, 152]:
        raise AssertionError("prefill marker coverage incomplete")
    return {"opening": opening, "input_marker": 151667 if opening else 151668,
            "counts": counts, "parameters": parameters, "compiled": compiled,
            "simulation_threads": threads,
            "scope": "prefill input observation and zero generated-token/draft CSR counts"}
