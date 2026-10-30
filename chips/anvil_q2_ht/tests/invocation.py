"""Fresh invocation namespaces for the two admitted supplemental entrypoints."""

import hashlib
import sys
import uuid

from retention import Experiment


def invocation_experiment(root, output, argv, sources):
    if output.is_absolute() or ".." in output.parts:
        raise ValueError("output must be project-relative")
    original = output / "receipt.json"
    original_path = root / original
    parent_receipt = None
    if original_path.exists():
        parent_receipt = {
            "path": str(original),
            "sha256": hashlib.sha256(original_path.read_bytes()).hexdigest(),
        }
    resolved = output / ("invocation-" + uuid.uuid4().hex)
    experiment = Experiment(root, resolved, argv, sources)
    experiment.receipt["invocation"] = {
        "parent_output": str(output),
        "output": str(resolved),
        "original_receipt": parent_receipt,
    }
    return experiment


def run_regression(experiment):
    experiment.run([
        sys.executable, "-B", "tests/progress_check.py",
        "--output", str(experiment.output / ("progress-" + uuid.uuid4().hex)),
    ], "progress-regression")
    experiment.run([
        sys.executable, "-B", "tests/invocation_check.py",
        "--output", str(experiment.output / "invocation-regression"),
    ], "invocation-regression")
