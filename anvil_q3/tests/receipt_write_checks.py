"""Project JSON update fault sensitivity; not shared-runtime recovery evidence."""

import errno
import json
from pathlib import Path
import sys
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from execution import write_json


def receipt_write_checks(folder):
    folder.mkdir()
    target = folder / "fixture.json"
    original = {"status": "running", "exit_code": None}
    write_json(target, original)
    before = target.read_bytes()
    for operation in ("fsync", "replace"):
        with patch("execution.os." + operation,
                   side_effect=OSError(errno.ENOSPC, "injected disk-full fixture")):
            try:
                write_json(target, {"status": "passed"})
            except OSError as exc:
                if exc.errno != errno.ENOSPC:
                    raise
            else:
                raise AssertionError("JSON update suppressed disk-full error")
        if target.read_bytes() != before:
            raise AssertionError("failed JSON update damaged previous fixture")
        if sorted(p.name for p in folder.iterdir()) != ["fixture.json"]:
            raise AssertionError("failed JSON update leaked temporary file")
    try:
        write_json(target, {"invalid": object()})
    except TypeError:
        pass
    else:
        raise AssertionError("JSON update accepted unserializable fixture")
    if target.read_bytes() != before:
        raise AssertionError("serialization failure damaged previous fixture")
    write_json(target, {"status": "finished"})
    if json.loads(target.read_text()) != {"status": "finished"}:
        raise AssertionError("successful JSON update was not readable")
    return {"disk_full_failures_propagated": 2, "previous_bytes_preserved": True,
            "serialization_failure_propagated": True, "successful_update_read_back": True,
            "scope": "project JSON fixtures only; not shared-runtime persistence repair"}


if __name__ == "__main__":
    print(json.dumps(receipt_write_checks(Path(sys.argv[1])), sort_keys=True))
