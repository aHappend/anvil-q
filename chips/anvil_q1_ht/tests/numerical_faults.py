"""Invalid stored numbers must fail inference through public pins, then recover.

These are synthetic compact images, not checkpoint or hardware measurements.
Every case retains an observed poisoned DDR response, a drained one-cycle error
completion, and ordered reference logits after an explicitly repaired upload.
"""

from reference import fp_q16


def fault_cases():
    cases = []
    for mode in ("AWQ", "BF16"):
        entries = [
            ("embedding_inf", 0, 0, 0x7c00),
            ("embedding_nan", 0, 0, 0x7e01),
            ("input_gamma_inf", 5, 0, 0xfc00),
            ("post_gamma_nan", 6, 0, 0x7e01),
            ("final_gamma_inf", 7, 0, 0x7c00),
        ]
        entries.extend((f"bias_{proj}_nonfinite", 4, proj,
                        0x7c00 if proj % 2 == 0 else 0xfe01) for proj in range(3))
        if mode == "AWQ":
            entries.extend((f"scale_{proj}_nonfinite", 3, proj,
                            0x7c00 if proj % 2 == 0 else 0x7e01) for proj in range(7))
            entries.extend((f"scale_{proj}_negative", 3, proj, 0xbc00) for proj in range(7))
        else:
            entries.extend((f"weight_{proj}_nonfinite", 1, proj,
                            0x7f80 if proj % 2 == 0 else 0xffc1) for proj in range(7))
        cases.extend(dict(name=f"{mode.lower()}_{name}", mode=mode, kind=kind,
                          projection=proj, invalid_bits=bits)
                     for name, kind, proj, bits in entries)
    return cases


def poison_image(model, fault, first_token):
    if fault not in fault_cases() or fault["mode"] != model.mode:
        raise ValueError("unrecognized numerical fault fixture")
    kind, proj, bits = fault["kind"], fault["projection"], fault["invalid_bits"]
    dense = kind == 1 and model.mode == "BF16"
    try:
        fp_q16(bits, 8 if dense else 5, 7 if dense else 10,
               unsigned_scale=kind == 3)
    except ValueError as exc:
        rejection = str(exc)
    else:
        raise AssertionError("numerical fault input is legal under the independent contract")
    descriptor = next(entry for entry in model.descriptors if entry[1:4] == (kind, 0, proj))
    # Embedding is input-row/output-token panel-major; other cases use lane 7.
    offset = 2 * first_token if kind == 0 else 14
    address = descriptor[4] + offset
    if offset + 2 > len(model.tensors[kind, 0, proj]):
        raise AssertionError("numerical poison is outside the actual tensor payload")
    original = int.from_bytes(model.image[address:address + 2], "little")
    model.image[address:address + 2] = bits.to_bytes(2, "little")
    return {**fault, "byte_address": address, "original_bits": original,
            "independent_input_rejection": rejection}


def numerical_faults(evidence, seed, selected=None):
    from experiments import measurement_records, top_probe

    cases = fault_cases()
    if selected is not None:
        wanted = set(selected)
        if not wanted or not wanted.issubset({case["name"] for case in cases}):
            raise ValueError("numerical-fault selection must name existing cases")
        cases = [case for case in cases if case["name"] in wanted]
    ledger = evidence.record.setdefault("numerical_fault_cases", [])
    for case in cases:
        row = {**case, "outcome": "not_run"}
        ledger.append(row)
    evidence.flush()
    for row in ledger:
        row["outcome"] = "running"
        trial = evidence.__class__("numerical-" + row["name"],
                                 source_root=evidence.folder / "sources")
        trial.simulation_build_pool = evidence.simulation_build_pool
        trial.record["tool_version_receipt"] = evidence.relative(evidence.folder / "receipt.json")
        row["receipt"] = evidence.relative(trial.folder / "receipt.json")
        evidence.flush()
        try:
            fault = {key: row[key] for key in ("name", "mode", "kind", "projection", "invalid_bits")}
            top_probe(trial, row["mode"], seed, config=0, numerical_fault=fault)
            transcript = next(
                (trial.folder.parents[2] / command["stdout"]).read_text()
                for command in reversed(trial.record["commands"])
                if command["argv"][0].endswith("/compiled/Vtb"))
            records = measurement_records(transcript, "CHECKS_PASSED numerical_fault")
            if (len(records) != 1 or records[0]["poison_seen"] < 1 or
                    records[0]["error_completion"] != 1 or records[0]["drained"] != 1 or
                    records[0]["recovery_logits"] != 8):
                raise AssertionError("numerical fault lacks observed rejection/recovery comparisons")
            row.update(outcome="compared", observed=records[0])
            trial.record["observations"].append({
                "scope": "public_top_numerical_rejection_and_repaired_image_recovery",
                "case": fault, "observed": records[0],
                "fixture": "synthetic_compact_not_checkpoint",
            })
            trial.finish("probe_passed", "Observed poisoned response, error and repaired reference logits.")
        except (OSError, RuntimeError, AssertionError, ValueError) as exc:
            row.update(outcome="failed", reason=str(exc))
            trial.finish("failed", str(exc))
            evidence.flush()
            raise
        evidence.flush()
