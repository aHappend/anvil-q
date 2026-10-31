"""Fast negative checks for the verification/bridge entry points themselves."""

import ast
from collections import Counter
import importlib

from benchmark_manifest import CASES, MANIFEST, MANIFEST_SHA256, sha256
from evidence import ROOT, write_json
import hardware_workload as bridge


def run(directory):
    files = sorted((ROOT / "tests").glob("*.py"))
    for path in files:
        ast.parse(path.read_text(), filename=str(path.relative_to(ROOT)))
        importlib.import_module(path.stem)
    counts = Counter(case["domain"] for case in CASES)
    if len(counts) != 5 or any(count < 2 for count in counts.values()):
        raise AssertionError("frozen five-domain workload coverage")
    if len({case["id"] for case in CASES}) != len(CASES):
        raise AssertionError("duplicate benchmark case")
    if MANIFEST_SHA256 != sha256(MANIFEST) or MANIFEST["decode_limit"] < 16:
        raise AssertionError("workload freeze mismatch")
    rejected = []
    for path in ("/tmp/private", "../escape", ".vulcan/receipt.json", ".git/config",
                 ".tooling/input.json", "VULCAN/state.json"):
        try:
            bridge.project_path(path)
        except ValueError:
            rejected.append(path)
        else:
            raise AssertionError("forbidden bridge artifact selector survived")
    for values in ([], [-1], [True], [151936], [1.5]):
        try:
            bridge.token_ids(values)
        except ValueError:
            rejected.append(repr(values))
        else:
            raise AssertionError("invalid token sequence survived")
    req = {key: key for key in bridge.IDENTITY_FIELDS}
    req["schema_version"] = 1
    req["integration_only"] = False
    candidate = dict(req, request_sha256=sha256(req), integration_only=True,
                     execution_kind="compiled_rtl")
    for field in ("run_nonce", "config_sha256", "workload_manifest_sha256"):
        bad = dict(candidate, **{field: "wrong"})
        try:
            bridge.validate_response(bad, req)
        except ValueError as exc:
            if "identity mismatch" not in str(exc):
                raise
            rejected.append(field)
        else:
            raise AssertionError("response identity defect survived")
    try:
        bridge.validate_response(candidate, req, full=True)
    except ValueError as exc:
        if "rejects simulated" not in str(exc):
            raise
        rejected.append("simulated-as-physical")
    else:
        raise AssertionError("simulated full-model result survived")
    record = {"name": "harness-selfcheck", "python_sources_parsed": len(files),
              "python_sources_imported": len(files),
              "workload_manifest_sha256": MANIFEST_SHA256, "domains": dict(counts),
              "expected_rejections": rejected,
              "scope": "verification/adapter negative checks, not hardware/model measurements"}
    write_json(directory / "selfcheck.json", record)
    return record
