"""Regression for the current 86400-second shared execution allowance."""

import json
import os
from pathlib import Path
import sys
import time
from unittest.mock import patch

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

from receipts import ROOT, execute, relative
from verify import enter_tier


def check_budget(run):
    with patch.dict(os.environ, {}, clear=True):
        start, deadline = enter_tier()
        assert 86399 <= deadline - start <= 86401
        assert enter_tier()[1] == deadline
    with patch.dict(os.environ, {
            "HT2_L1_DEADLINE": str(time.monotonic() + 42)}, clear=True):
        inherited = os.environ["HT2_L1_DEADLINE"]
        assert enter_tier()[1] == float(inherited)
        assert os.environ["HT2_L1_DEADLINE"] == inherited
    for value in ("0", "nan", "inf"):
        with patch.dict(os.environ, {"HT2_L1_DEADLINE": value}, clear=True):
            try:
                enter_tier()
            except RuntimeError:
                pass
            else:
                raise AssertionError("invalid inherited deadline accepted")
    inherited = float(os.environ["HT2_L1_DEADLINE"])
    result = execute(run, "real-child", [
        sys.executable, "-c", "print('actual child completed')"],
        [sys.executable, "--version"])
    receipt = json.loads((result / "receipt.json").read_text())
    assert receipt["exit_code"] == 0 and not receipt["timed_out"]
    assert receipt["timeout_s"] > 3600
    assert receipt["shared_deadline_monotonic"] == str(inherited)
    assert (result / "stdout.txt").read_text() == "actual child completed\n"
    return {"status": "passed", "deadline_checks": 7,
            "child_receipt": relative(result / "receipt.json")}


if __name__ == "__main__":
    enter_tier()
    run = (ROOT / sys.argv[1]).resolve()
    if not run.is_relative_to(ROOT / "evidence/preparation") or not run.is_dir():
        raise ValueError("budget regression requires a new preparation directory")
    print(json.dumps(check_budget(run)), flush=True)
