"""Executable mutations of disposable source copies, never the accepted RTL."""

import hashlib
import shutil


CASES = {
    "bf16-rounding-tie": (
        "anvil_q2_ht2_convert_pipe.sv",
        "((|significand2[17:0]) || significand2[19])",
        "((|significand2[17:0]) || !significand2[19])",
        "conversion", ("NUMERICAL_MISMATCH kind=3",)),
    "w2-difference-sign": (
        "anvil_q2_ht2_unpack_lane.sv",
        "sign2<=difference1[4]^scale1[15];",
        "sign2<=(formats[1]==3 ? !difference1[4] : difference1[4])^scale1[15];",
        "unpack", ("NUMERICAL_MISMATCH kind=4",)),
    "broadcast-slot": (
        "anvil_q2_ht2_tile_batch_mac.sv",
        ".b(s_weight[j*16+:16])",
        ".b(s_weight[((j+(t==2 ? 1 : 0)) & 127)*16+:16])",
        "mac", ("MAC_NUMERICAL",)),
    "sparse-token-union": (
        "anvil_q2_ht2_sparse_w2w4_dma.sv",
        "union_lanes[j]=union_lanes[j] || union_keep[128*t+j];",
        "union_lanes[j]=union_lanes[j] || (t==0 && union_keep[128*t+j]);",
        "dma", ("DMA_NUMERICAL", "DMA_MISSING_BEAT")),
    "attention-sibling": (
        "anvil_q2_ht2_kv_map.sv",
        "ancestors[4*r_slot+query_i] && query_i<count",
        "query_i<count",
        "kv", ("KV_STORE_READ",)),
    "publish-without-kv-ack": (
        "anvil_q2_ht2_spec_verifier.sv",
        "if (!completions[28*t+l]) bad_input=1;",
        "if (1'b0) bad_input=1;",
        "tree", ("TREE_RESPONSE",)),
    "retain-rejected-generation": (
        "anvil_q2_ht2_kv_map.sv",
        """            write_data=scratch[k];
          end
        end
      end""",
        """            write_data=scratch[k];
          end
        end
        if (annul && batch_active && bank==0) begin
          write_enable=1;
          write_address=0;
          write_data=scratch[0];
        end
      end""",
        "kv", ("KV_STORE_READ",)),
    "sequence-pointer": (
        "anvil_q2_ht2_spec_verifier.sv",
        "pointer<=response_position;",
        "pointer<=response_position+32'd1;",
        "tree", ("TREE_ATOMIC_PUBLICATION",)),
    "integrated-attention-zero": (
        "anvil_q2_ht2_attention.sv",
        "assign m_data=m_valid && !response_error ? response : {QWORDS*16{1'b0}};",
        "assign m_data={QWORDS*16{1'b0}};",
        "integrated", ("MATRIX_NUMERICAL", "MATRIX_BATCH_RESULT")),
}


def exercise(run, fixture):
    from verify import (ROOT, BF16, FP32, convert, dequant, simulate, mac_behavior,
                        dma_behavior, kv_store_behavior, tree_behavior)
    if fixture == "integrated":
        from integrated import execute
        execute(run, cells=[(17, False, 16, False, False)], smokes=False)
    elif fixture in ("conversion", "unpack"):
        rows = []
        if fixture == "conversion":
            kind = 3
            # Exact adjacent midpoints with even and odd retained significands.
            for value in (0x3f808000, 0x3f818000, 0xbf808000, 0xbf818000,
                          0x00008000, 0x00018000, 0x7f7f8000):
                result, error = convert(value, FP32, BF16)
                rows.append((value, 0, 0, result, error))
        else:
            kind = 4
            for q in range(4):
                for zero in (1, 0, 2, 3):
                    for scale in (1, 64, 0x3f00, 0x3f80, 0xbf80):
                        result, error = dequant(q, zero, scale)
                        rows.append((q, scale, 64 | (zero << 2) | 3, result, error))
        path = run.path / "mutation-vectors.txt"
        path.write_text(f"{len(rows)}\n" + "".join(
            f"{a:08x} {b:08x} {aux:08x} {expected:08x} {int(error)}\n"
            for a, b, aux, expected, error in rows))
        run.receipt["independent_vectors"] = {
            "kind": kind, "count": len(rows),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
        simulate(run, ROOT / "tests/numerics_tb.sv", {"KIND": kind},
                 simulator="verilator", plusargs=["+vectors=" + run.relative(path)])
    else:
        {"mac": mac_behavior, "dma": dma_behavior, "kv": kv_store_behavior,
         "tree": tree_behavior}[fixture](run, "verilator")


def execute(run, selected=None):
    from verify import ROOT, Run, sources, DetectedDefect
    names = [selected] if selected else list(CASES)
    if any(name not in CASES for name in names):
        raise RuntimeError(f"unknown mutation: {selected}; choose {', '.join(CASES)}")
    completed_fixtures = {}
    run.receipt["mutations"] = []
    for name in names:
        filename, old, new, fixture, assertions = CASES[name]
        if fixture not in completed_fixtures:
            baseline = Run(f"mutation-control-{fixture}",
                           run.receipt["kind"] == "advisory-preparation")
            baseline.started, baseline.budget_s = run.started, run.budget_s
            try:
                exercise(baseline, fixture)
            except Exception as exc:
                baseline.finish(False, f"{type(exc).__name__}: {exc}")
                raise
            if baseline.finish(True, "unmodified-source independent comparisons passed"):
                raise RuntimeError(f"mutation control source changed: {fixture}")
            completed_fixtures[fixture] = run.relative(baseline.path / "receipt.json")
        case = Run(f"mutation-{name}", run.receipt["kind"] == "advisory-preparation")
        case.started, case.budget_s = run.started, run.budget_s
        case.receipt["mutation"] = {
            "id": name, "control_receipt": completed_fixtures[fixture],
            "file": "rtl/" + filename, "old": old, "new": new,
            "required_assertions": assertions,
        }
        case.design_root = case.path / "source-copy"
        for path in sources():
            destination = case.design_root / path.relative_to(ROOT)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, destination)
        path = case.design_root / "rtl" / filename
        text = path.read_text()
        if text.count(old) != 1:
            case.finish(False, "mutation anchor is not unique")
            raise RuntimeError(f"mutation anchor is not unique: {name}")
        path.write_text(text.replace(old, new))
        case.receipt["mutation"]["mutated_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        case.receipt["disposable_source_hashes"] = {
            str(p.relative_to(case.design_root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sources(case.design_root)
        }
        case.expected_failure = assertions
        try:
            exercise(case, fixture)
        except DetectedDefect as exc:
            actual_hashes = {
                str(p.relative_to(case.design_root)): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sources(case.design_root)
            }
            if actual_hashes != case.receipt["disposable_source_hashes"]:
                case.finish(False, "disposable source changed during execution")
                raise RuntimeError(f"disposable source changed during mutation: {name}")
            if case.finish(True, str(exc)):
                raise RuntimeError(f"accepted source changed during mutation: {name}")
        except Exception as exc:
            case.finish(False, f"{type(exc).__name__}: {exc}")
            raise
        else:
            case.finish(False, "mutation survived")
            raise RuntimeError(f"mutation survived: {name}")
        run.receipt["mutations"].append({
            "id": name, "receipt": run.relative(case.path / "receipt.json"),
            "control_receipt": completed_fixtures[fixture], "detected": True,
            "assertions": case.receipt["detected_defect"]["assertions"],
        })
        run.save()
