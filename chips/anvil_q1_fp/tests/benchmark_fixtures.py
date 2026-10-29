"""Explicitly synthetic checker tests, never full-model execution evidence."""

import json
import shutil
import struct

from benchmark import DIMENSIONS, DOMAINS, FORBIDDEN, MODEL, Validator, load_json, measured_cycles, sha


NOTICE = "SYNTHETIC VALIDATOR FIXTURE ONLY; NO MODEL OR HARDWARE EXECUTION"


def library_entrypoint_check(root, ev):
    import sys

    label = "benchmark-library-direct-execution"
    completed = ev.run(label, [sys.executable, "tests/benchmark.py"], timeout=3600)
    record = ev.receipt["records"][-1]
    stdout = (root / record["stdout"]).read_text()
    stderr = (root / record["stderr"]).read_text()
    return ev.assertion(
        "fixture_library_entrypoint_rejects_execution",
        not completed and record["exit_code"] == 2 and
        not record["timed_out"] and stdout == "" and
        "validation library, not an inference entrypoint" in stderr and
        "python3 tests/verify.py --check benchmark-contract" in stderr and
        "that command does not perform inference" in stderr,
        scope=NOTICE, exit_code=record["exit_code"],
        diagnostic=stderr,
    )


def failure_diagnostics_check(root, ev):
    from contextlib import redirect_stderr
    import copy
    import io
    from types import SimpleNamespace
    from verify import report_failures

    good = True
    for label, assertions in (
        ("passed", [dict(name="input_integrity", passed=True)]),
        ("missing-results", [
            dict(name="input_integrity", passed=True),
            dict(name="full_model_inputs_and_execution", passed=False,
                 missing=["tests/data/full_model_results.json"],
                 reason="missing artifact(s): tests/data/full_model_results.json"),
        ]),
        ("multiple-failures", [
            dict(name="tool_iverilog", passed=False),
            dict(name="verification_exception", passed=False,
                 error="ValueError('retained failure')"),
        ]),
    ):
        holder = SimpleNamespace(path=ev.path, receipt={"assertions": assertions})
        original = copy.deepcopy(holder.receipt)
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            report_failures(holder)
        observed = [json.loads(line) for line in stderr.getvalue().splitlines()]
        expected = [
            dict(receipt=str((ev.path / "receipt.json").relative_to(root)), **item)
            for item in assertions if not item["passed"]
        ]
        good = ev.assertion(
            "fixture_failure_diagnostics_" + label,
            observed == expected and holder.receipt == original,
            scope=NOTICE, observed=observed, expected=expected,
            receipt_unchanged=holder.receipt == original) and good
    return good


def component_diagnostics_check(root, ev):
    """Failed children must expose their receipt and original assertion."""
    from contextlib import redirect_stderr
    import io
    from types import SimpleNamespace
    from unittest.mock import patch
    import verify

    good = True
    for label in ("passed", "failed", "false-with-passed-assertion",
                  "true-with-failed-assertion",
                  "true-without-assertion", "false-without-assertion",
                  "exception", "exception-before-assertion"):
        raises = label.startswith("exception")
        empty = label in ("true-without-assertion", "false-without-assertion",
                          "exception-before-assertion")
        child_assertions = ([] if empty else [
            dict(name="original_child_success", passed=True)]
            if label in ("passed", "false-with-passed-assertion") else [
            dict(name="original_child_failure", passed=False,
                 diagnostic="synthetic retained diagnostic")])
        expected_assertions = [item.copy() for item in child_assertions]
        if raises:
            expected_assertions.append(dict(
                name="verification_exception", passed=False,
                error="ValueError('synthetic component exception')"))
        elif empty:
            expected_assertions.append(dict(
                name="component_assertions_present", passed=False,
                error="component returned without recording an assertion"))
        elif label == "false-with-passed-assertion":
            expected_assertions.append(dict(
                name="component_return_value", passed=False,
                error="component returned false despite passing assertions"))
        child = SimpleNamespace(
            path=ev.path / ("synthetic-child-" + label),
            receipt={"assertions": child_assertions})
        statuses, parent_assertions = [], []
        child.finish = statuses.append

        def child_assertion(name, passed, **detail):
            child.receipt["assertions"].append(
                dict(name=name, passed=bool(passed), **detail))

        child.assertion = child_assertion
        parent = SimpleNamespace(path=ev.path, receipt={})

        def assertion(name, passed, **detail):
            parent_assertions.append(dict(name=name, passed=bool(passed), **detail))

        def check(holder):
            assert holder is child
            if raises:
                raise ValueError("synthetic component exception")
            return label in ("passed", "true-with-failed-assertion",
                             "true-without-assertion")

        parent.assertion = assertion
        stderr = io.StringIO()
        caught, result = None, None
        with patch.object(verify, "Evidence", return_value=child), redirect_stderr(stderr):
            try:
                result = verify.component(parent, "synthetic-" + label, check)
            except ValueError as error:
                caught = str(error)
        receipt = str((child.path / "receipt.json").relative_to(root))
        observed = [json.loads(line) for line in stderr.getvalue().splitlines()]
        passed = label == "passed"
        expected = [dict(receipt=receipt, **item) for item in expected_assertions
                    if not item["passed"]]
        good = ev.assertion(
            "fixture_component_diagnostics_" + label,
            statuses == ["passed" if passed else "failed"] and
            child.receipt["tool_versions_receipt"] ==
            str((ev.path / "receipt.json").relative_to(root)) and
            parent.receipt == {"children": [receipt]} and
            parent_assertions == [dict(name="component_synthetic-" + label,
                                       passed=passed, child_receipt=receipt)] and
            child.receipt["assertions"] == expected_assertions and
            observed == expected and
            (caught == "synthetic component exception" if raises
             else caught is None and result is passed),
            scope=NOTICE, observed=observed, expected=expected,
            exception_propagated=caught, processes_executed=0) and good
    return good


def prerequisite_dependencies_check(root, ev):
    import sys
    from types import SimpleNamespace
    from unittest.mock import patch
    import verify

    good = True
    for numpy_available in (False, True):
        commands, assertions, manifest_calls = [], [], []

        def run(label, argv, **kwargs):
            commands.append((label, argv, kwargs))
            return numpy_available if label == "reference-numpy-import" else True

        def assertion(name, passed, **detail):
            assertions.append(dict(name=name, passed=bool(passed), **detail))

        def manifests(holder):
            manifest_calls.append(holder)
            return True

        holder = SimpleNamespace(versions=lambda: True, run=run, assertion=assertion)
        with patch.object(verify, "benchmark_contract", side_effect=manifests):
            result = verify.prerequisites(holder)
        labels = [row[0] for row in commands]
        numpy_commands = [row for row in commands if row[0] == "reference-numpy-import"]
        observed = (
            result is numpy_available and manifest_calls == [holder] and
            labels == ["reference-dependency-discovery", "reference-numpy-import"] and
            numpy_commands[0][1] == [
                sys.executable, "-c", "import numpy; print(numpy.__version__)"] and
            numpy_commands[0][2]["timeout"] == 30 and
            len(assertions) == 1 and
            assertions[0]["name"] == "reference_numpy_import" and
            assertions[0]["passed"] is numpy_available)
        good = ev.assertion(
            "fixture_prerequisites_numpy_" + ("available" if numpy_available else "missing"),
            observed, scope=NOTICE, numpy_available=numpy_available,
            discovery_succeeded=True, prerequisite_result=result,
            input_validation_still_executed=bool(manifest_calls),
            observed_assertions=assertions, processes_executed=0) and good
    return good


def reference_environment_check(root, ev):
    """Synthetic protocol records cannot qualify the actual host environment."""
    import copy
    from input_prerequisites import qualified_reference_events

    control = [
        {"event": "parent", "same_executable_as_probe": True},
        {"event": "parent_import", "numpy_version": "fixture-version"},
        {"event": "child_import", "numpy_version": "fixture-version",
         "same_executable_as_parent": True},
    ]
    cases = [("complete-control", True, control, True),
             ("nonzero-exit", False, control, False)]
    for label, completed in (("integer-completion", 1),
                             ("string-completion", "passed"),
                             ("missing-completion", None)):
        cases.append((label, completed, control, False))
    for length in range(3):
        cases.append(("missing-event-" + str(length), True, control[:length], False))
    cases.extend([
        ("duplicate-event", True, control + [control[-1]], False),
        ("reordered-events", True, control[::-1], False),
        ("non-object-event", True, [control[0], None, control[2]], False),
    ])
    for label, index, field, value in (
        ("parent-interpreter-mismatch", 0, "same_executable_as_probe", False),
        ("parent-nonboolean-identity", 0, "same_executable_as_probe", 1),
        ("child-interpreter-mismatch", 2, "same_executable_as_parent", False),
        ("child-nonboolean-identity", 2, "same_executable_as_parent", 1),
        ("numpy-version-mismatch", 2, "numpy_version", "other-fixture-version"),
        ("missing-parent-event", 0, "event", None),
        ("missing-child-version", 2, "numpy_version", None),
    ):
        events = copy.deepcopy(control)
        if value is None:
            del events[index][field]
        else:
            events[index][field] = value
        cases.append((label, True, events, False))
    for label, version in (("empty-version", ""), ("whitespace-version", " "),
                           ("nonstring-version", 17), ("absent-version", None)):
        events = copy.deepcopy(control)
        for index in (1, 2):
            if version is None:
                del events[index]["numpy_version"]
            else:
                events[index]["numpy_version"] = version
        cases.append((label, True, events, False))
    good = True
    for label, completed, events, expected in cases:
        original = copy.deepcopy(events)
        observed = qualified_reference_events(completed, events)
        good = ev.assertion(
            "fixture_reference_environment_" + label,
            observed is expected and events == original,
            scope=NOTICE, expected_qualified=expected,
            observed_qualified=observed, processes_executed=0,
            actual_environment_qualified=False) and good
    return good


def production_interface_check(root, ev):
    """Help success must never be promoted to endpoint qualification."""
    from types import SimpleNamespace
    from unittest.mock import patch
    import input_prerequisites

    directory = ev.path / "production-interface"
    directory.mkdir()
    bindings = (
        "tests/data/model_manifest.json",
        "tests/data/benchmark_manifest.json",
        "evidence/preparation/verifier-reference-collector-full-6rkm2hzx/receipt.json",
        "evidence/preparation/verifier-reference-collector-full-6rkm2hzx/"
        "collected-reference/teacher_references.json",
    )
    for name in bindings:
        path = directory / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("x") as stream:
            stream.write(NOTICE)
    commands = (
        ("runtime-version", ["vulcan", "hardware", "--version"]),
        ("public-command-help", ["vulcan", "--help"]),
        ("hardware-command-help", ["vulcan", "hardware", "--help"]),
        ("fpga-command-help", ["vulcan", "hardware", "fpga", "--help"]),
        ("board-gate-help", ["vulcan", "hardware", "fpga", "board-hil", "--help"]),
        ("doctor-help", ["vulcan", "hardware", "doctor", "--help"]),
        ("status-help", ["vulcan", "hardware", "status", "--help"]),
    )
    source_hashes = {"rtl/fixture.sv": "1" * 64,
                     "fpga/fixture.sdc": "2" * 64, "tests/fixture.py": "3" * 64}
    good = True
    scenarios = [("help-success", None, None, None)]
    scenarios += [("failed-" + label, label, None, None) for label, _ in commands]
    scenarios += [("missing-binding-" + str(index), None, name, None)
                  for index, name in enumerate(bindings)]
    scenarios += [
        ("binding-target-" + str(index) + "-" + component, None, None, (name, component))
        for index, name in enumerate(bindings)
        for component in (*sorted(FORBIDDEN), "outside-project")
    ]
    resolve = type(directory).resolve
    for label, failed_command, missing_binding, relocated in scenarios:
        calls, assertions = [], []
        holder = SimpleNamespace(receipt={"source_sha256": source_hashes.copy()})

        def resolved(path, *args, **kwargs):
            result = resolve(path, *args, **kwargs)
            if relocated and result == directory / relocated[0]:
                if relocated[1] == "outside-project":
                    return directory.parent / "unread-external-fixture"
                return directory / relocated[1] / "unread-runtime-fixture"
            return result

        def run(name, argv, timeout):
            calls.append((name, list(argv), timeout))
            return name != failed_command

        def assertion(name, passed, **detail):
            assertions.append(dict(name=name, passed=bool(passed), **detail))
            return bool(passed)

        holder.run, holder.assertion = run, assertion
        missing = directory / missing_binding if missing_binding else None
        if missing:
            missing.unlink()
        try:
            with patch.object(input_prerequisites, "ROOT", directory), \
                    patch.object(type(directory), "resolve", resolved), \
                    patch.object(input_prerequisites, "digest",
                                 wraps=input_prerequisites.digest) as hashed, \
                    patch("subprocess.run", side_effect=AssertionError(
                        "offline interface fixture attempted a real process")):
                qualified = input_prerequisites.production_interface(holder)
        finally:
            if missing:
                with missing.open("x") as stream:
                    stream.write(NOTICE)
        qualification = holder.receipt["qualification"]
        intended = holder.receipt["intended_execution_bindings"]
        rejected_binding = missing_binding or (relocated[0] if relocated else None)
        expected_bindings = {name: sha(directory / name) for name in bindings
                             if name != rejected_binding}
        expected_help = failed_command is None and rejected_binding is None
        passed = (
            qualified is False and
            calls == [(name, argv, 60) for name, argv in commands] and
            qualification == dict(documentation_commands_completed=expected_help,
                                  endpoint_contacted=False,
                                  hardware_availability="not determined",
                                  observer_implemented=False, status="not-established") and
            intended["top"] == "anvil_q1_fp_top" and
            intended["source_sha256"] == {
                name: value for name, value in source_hashes.items()
                if name.startswith(("rtl/", "fpga/"))} and
            intended["artifacts"] == expected_bindings and
            assertions[-1]["name"] == "production_execution_interface_qualified" and
            assertions[-1]["passed"] is False and
            sum(not item["passed"] for item in assertions) ==
            1 + int(failed_command is not None or rejected_binding is not None) and
            (not relocated or all(
                call.args[0] != directory / relocated[0] for call in hashed.call_args_list))
        )
        good = ev.assertion(
            "fixture_production_interface_" + label, passed, scope=NOTICE,
            commands_mocked=True, endpoint_contacted=False,
            qualification=qualification, helper_assertions=assertions) and good
    return good


def artifact_path_check(root, ev):
    from unittest.mock import patch
    from benchmark import FORBIDDEN, product_source_hashes
    from verify import sources

    directory = ev.path / "artifact-paths"
    (directory / "rtl").mkdir(parents=True)
    target = directory / "rtl" / "fixture.sv"
    with target.open("x") as stream:
        stream.write(NOTICE)
    alias = directory / "alias.bin"
    alias.symlink_to("rtl/fixture.sv")
    outside = directory / "outside.bin"
    outside.symlink_to("../absent-outside-fixture")
    digest = sha(target)
    resolve = type(target).resolve
    cases = [
        ("regular", "rtl/fixture.sv", None, None),
        ("allowed-symlink", "alias.bin", None, None),
        ("escaping-symlink", "outside.bin", None, "artifact escapes project"),
        ("absolute", str(target), None, "nonportable artifact path"),
        ("parent", "../absent", None, "nonportable artifact path"),
    ]
    for name in sorted(FORBIDDEN):
        cases.append(("literal-" + name, name + "/absent", None,
                      "nonportable artifact path"))
        for path in ("rtl/fixture.sv", "alias.bin"):
            cases.append(("resolved-" + name + "-" + path.replace("/", "-"),
                          path, name, "runtime-owned artifact target"))
    good = True
    for label, path, relocated, expected in cases:
        # Model resolved targets without creating or reading runtime-owned files.
        def resolved(value, *args, **kwargs):
            result = resolve(value, *args, **kwargs)
            if relocated and result == target:
                return directory / relocated / "absent"
            return result

        diagnostic = None
        with patch.object(type(target), "resolve", resolved):
            try:
                Validator(directory, ev).artifact(dict(path=path, sha256=digest))
            except ValueError as error:
                diagnostic = str(error)
        good = ev.assertion(
            "fixture_artifact_path_" + label,
            diagnostic is None if expected is None else
            diagnostic is not None and expected in diagnostic,
            scope=NOTICE, path=path, resolved_target_component=relocated,
            runtime_owned_files_accessed=False, expected_diagnostic=expected,
            diagnostic=diagnostic) and good
        if relocated and path == "rtl/fixture.sv":
            diagnostic = None
            with patch.object(type(target), "resolve", resolved):
                try:
                    sources(directory)
                except ValueError as error:
                    diagnostic = str(error)
            good = ev.assertion(
                "fixture_source_path_" + relocated,
                diagnostic is not None and expected in diagnostic,
                scope=NOTICE, runtime_owned_files_accessed=False,
                expected_diagnostic=expected, diagnostic=diagnostic) and good
            diagnostic = None
            with patch.object(type(target), "resolve", resolved), \
                    patch("benchmark.sha", wraps=sha) as hashed:
                try:
                    product_source_hashes(directory)
                except ValueError as error:
                    diagnostic = str(error)
            good = ev.assertion(
                "fixture_source_hash_path_" + relocated,
                diagnostic is not None and expected in diagnostic and
                hashed.call_count == 0,
                scope=NOTICE, hash_callbacks=hashed.call_count,
                runtime_owned_files_accessed=False,
                expected_diagnostic=expected, diagnostic=diagnostic) and good
    good = ev.assertion(
        "fixture_source_path_allowed", sources(directory) == [target] and
        product_source_hashes(directory) == {"rtl/fixture.sv": digest},
        scope=NOTICE) and good
    return good


def measured_cycles_check(root, ev):
    pristine = dict(accepted_to_last=3, first_logit=1,
                    arithmetic=1, memory_stall=1, control=1)
    cases = [("integer", pristine, pristine, None)]
    for side in ("summary", "trace"):
        for field in pristine:
            for label, value in (("float", float(pristine[field])),
                                 ("boolean", True), ("negative", -1), ("missing", None)):
                changed = dict(pristine)
                if label == "missing":
                    del changed[field]
                else:
                    changed[field] = value
                cases.append((side + "-" + field + "-" + label,
                              changed if side == "summary" else pristine,
                              changed if side == "trace" else pristine,
                              "invalid measured cycle accounting"))
        for label, changed in (
            ("zero-first", dict(pristine, first_logit=0)),
            ("late-first", dict(pristine, first_logit=4)),
            ("inconsistent-total", dict(pristine, accepted_to_last=4)),
            ("nonobject", []),
        ):
            cases.append((side + "-" + label,
                          changed if side == "summary" else pristine,
                          changed if side == "trace" else pristine,
                          "invalid measured cycle accounting"))
    cases.append(("different-valid-trace", pristine, dict(pristine, first_logit=2),
                  "cycles differ from raw integrated trace"))
    good = True
    for label, summary, trace, expected in cases:
        path = ev.path / ("fixture-measured-cycles-" + label + ".json")
        with path.open("x") as stream:
            json.dump(dict(summary=summary, trace=trace, notice=NOTICE), stream)
        diagnostic = None
        try:
            measured_cycles(summary, trace)
        except ValueError as error:
            diagnostic = str(error)
        good = ev.assertion(
            "fixture_measured_cycles_" + label, diagnostic == expected,
            scope=NOTICE, expected_diagnostic=expected, diagnostic=diagnostic,
            input=str(path.relative_to(root)), sha256=sha(path)) and good
    return good


def entry_document_path_check(root, ev):
    """Reject excluded entry-document targets before any content hashing."""
    from types import SimpleNamespace
    from unittest.mock import patch
    from benchmark import FORBIDDEN, check as check_benchmark

    directory = ev.path / "entry-document-paths"
    data = directory / "tests/data"
    data.mkdir(parents=True)
    names = ("model_manifest", "benchmark_manifest", "full_model_results")
    for name in names:
        with (data / (name + ".json")).open("x") as stream:
            stream.write("{}\n")
    resolve = type(directory).resolve
    good = True
    entries = [("inputs", name) for name in names[:2]]
    entries += [("validate", names[2])]
    entries += [("check", name) for name in names]
    for entry, name in entries:
        target = data / (name + ".json")
        for component in sorted(FORBIDDEN) + ["outside-project"]:
            def resolved(value, *args, **kwargs):
                result = resolve(value, *args, **kwargs)
                if result == target:
                    if component == "outside-project":
                        return directory.parent / "absent-entry-document"
                    return directory / component / "absent-entry-document"
                return result

            assertions = []
            holder = SimpleNamespace(receipt={})
            holder.assertion = lambda label, passed, **detail: (
                assertions.append(dict(name=label, passed=passed, **detail)) or passed)
            validator = Validator(directory, holder)
            diagnostic = None
            with patch.object(type(directory), "resolve", resolved), \
                    patch("benchmark.sha", wraps=sha) as hashed, \
                    patch.object(Validator, "document", return_value={}), \
                    patch.object(Validator, "model"), \
                    patch.object(Validator, "suite", return_value={}):
                try:
                    if entry == "inputs":
                        validator.inputs()
                    else:
                        with patch.object(Validator, "inputs", return_value=({}, {}, {})):
                            if entry == "validate":
                                validator.validate()
                            else:
                                check_benchmark(directory, holder)
                except (ValueError, KeyError, TypeError) as error:
                    diagnostic = str(error)
                forbidden_hashes = sum(
                    call.args[0] == target for call in hashed.call_args_list)
            if entry == "check":
                diagnostic = next((a.get("reason") for a in assertions
                                   if a["name"] == "full_model_inputs_and_execution" and
                                   not a["passed"]), diagnostic)
            expected = ("artifact escapes project" if component == "outside-project"
                        else "runtime-owned artifact target")
            good = ev.assertion(
                "fixture_entry_document_path_" + entry + "_" + name + "_" + component,
                diagnostic is not None and expected in diagnostic and forbidden_hashes == 0,
                scope=NOTICE, diagnostic=diagnostic, expected_diagnostic=expected,
                forbidden_hash_callbacks=forbidden_hashes,
                runtime_owned_files_accessed=False, endpoint_contacted=False) and good
    return good


def teacher_descriptor_path_check(root, ev):
    """Reject disallowed teacher-reference targets before reading their bytes."""
    from unittest.mock import patch
    import teacher_observations

    directory = ev.path / "teacher-descriptor-paths"
    directory.mkdir()
    target = directory / "reference.json"
    with target.open("x") as stream:
        stream.write(NOTICE)
    alias = directory / "alias.json"
    alias.symlink_to("reference.json")
    resolve = type(target).resolve
    good = True
    for path in (target, alias):
        for component in (None, *sorted(FORBIDDEN), "outside-project"):
            def resolved(value, *args, **kwargs):
                result = resolve(value, *args, **kwargs)
                if result == target and component:
                    if component == "outside-project":
                        return directory.parent / "unread-external-reference"
                    return directory / component / "unread-runtime-reference"
                return result

            diagnostic = None
            descriptor = None
            with patch.object(teacher_observations, "ROOT", directory), \
                    patch.object(type(target), "resolve", resolved), \
                    patch.object(teacher_observations, "sha", return_value="1" * 64) as hashed:
                try:
                    descriptor = teacher_observations.descriptor(path)
                except ValueError as error:
                    diagnostic = str(error)
            expected = ("artifact escapes project" if component == "outside-project" else
                        "runtime-owned artifact target" if component else None)
            passed = (
                descriptor == dict(path=path.name, sha256="1" * 64) and
                diagnostic is None and hashed.call_count == 1
            ) if component is None else (
                descriptor is None and diagnostic is not None and
                expected in diagnostic and hashed.call_count == 0
            )
            good = ev.assertion(
                "fixture_teacher_descriptor_" + path.stem + "_" + str(component),
                passed, scope=NOTICE, expected_diagnostic=expected,
                diagnostic=diagnostic, hash_calls=hashed.call_count,
                runtime_owned_files_accessed=False, endpoint_contacted=False) and good
    return good


def zero_output_check(root, ev):
    """Undefined cosine fails native fidelity, not reporting-only comparisons."""
    directory = ev.path / "zero-output"
    directory.mkdir()

    def array(name, values, code):
        path = directory / name
        with path.open("xb") as stream:
            stream.write(struct.pack("<" + code * len(values), *values))
        return dict(path=str(path.relative_to(root)), sha256=sha(path))

    reference = array("nonzero-reference.f64", [1., -1.], "d")
    good = True
    for wide in (False, True):
        code = "d" if wide else "f"
        actual = array("zero-" + code, [0., -0.], code)
        repeated = array("repeat-zero-" + code, [0., -0.], code)
        for label, threshold, accepted in (
            ("report-only", (-1, float("inf")), True),
            ("native-layer", (.9999, .002), False),
            ("native-final", (.999, .01), False),
        ):
            validator = Validator(root, ev)
            diagnostic = None
            try:
                validator.arrays(actual, reference, repeated, 2, threshold,
                                 label, wide=wide)
            except ValueError as error:
                diagnostic = str(error)
            passed = (diagnostic is None and len(validator.metrics) == 1 and
                      validator.metrics[0]["cosine"] is None and
                      validator.metrics[0]["normalized_error"] == 1.) if accepted else (
                          diagnostic is not None and
                          "numerical fidelity failed" in diagnostic)
            good = ev.assertion(
                "fixture_zero_output_" + code + "_" + label, passed,
                scope=NOTICE, expected_acceptance=accepted,
                diagnostic=diagnostic, metrics=validator.metrics) and good
    return good


def numerical_boundary_check(root, ev):
    """Bracket each native fidelity limit with adjacent binary32 values."""
    from fractions import Fraction
    import math

    directory = ev.path / "numerical-boundaries"
    directory.mkdir()

    def array(name, values, code):
        path = directory / name
        with path.open("xb") as stream:
            stream.write(struct.pack("<" + code * len(values), *values))
        return dict(path=str(path.relative_to(root)), sha256=sha(path))

    good = True
    for level, threshold in (("layer", (.9999, .002)), ("final", (.999, .01))):
        for mechanism in ("cosine", "normalized-error", "zero-reference"):
            boundary = (math.sqrt(1 / threshold[0] ** 2 - 1)
                        if mechanism == "cosine" else threshold[1])
            center = struct.unpack("<I", struct.pack("<f", boundary))[0]
            decisions = []
            for offset in (-1, 0, 1):
                neighbor = struct.unpack("<f", struct.pack("<I", center + offset))[0]
                if mechanism == "cosine":
                    scale = 2. ** -10
                    values, expected = [scale, scale * neighbor], [scale, 0.]
                    x, y = map(Fraction, values)
                    limit = Fraction(str(threshold[0]))
                    accepted = x * x >= limit * limit * (x * x + y * y)
                    isolated = abs(values[1]) <= threshold[1]
                elif mechanism == "normalized-error":
                    values, expected = [2., 2 * neighbor], [2., 0.]
                    accepted = Fraction(neighbor) <= Fraction(str(threshold[1]))
                    isolated = 1 / math.hypot(1., neighbor) >= threshold[0]
                else:
                    values, expected = [neighbor, 0.], [0., 0.]
                    accepted = Fraction(neighbor) <= Fraction(str(threshold[1]))
                    isolated = True
                decisions.append(accepted)
                label = level + "-" + mechanism + "-" + str(offset)
                actual = array(label + ".f32", values, "f")
                reference = array(label + ".f64", expected, "d")
                validator = Validator(root, ev)
                diagnostic = None
                try:
                    validator.arrays(actual, reference, actual, 2, threshold, label)
                except ValueError as error:
                    diagnostic = str(error)
                metrics = validator.metrics
                passed = (isolated and (diagnostic is None) == accepted and
                          len(metrics) == int(accepted) and
                          (accepted or diagnostic.startswith("numerical fidelity failed:")))
                if accepted and mechanism == "zero-reference":
                    passed = passed and metrics[0]["cosine"] is None
                good = ev.assertion(
                    "fixture_numerical_boundary_" + label, passed,
                    scope=NOTICE, threshold=list(threshold), mechanism=mechanism,
                    expected_acceptance=accepted, diagnostic=diagnostic,
                    metrics=metrics, actual=actual, reference=reference) and good
            good = ev.assertion(
                "fixture_numerical_boundary_bracket_" + level + "-" + mechanism,
                any(decisions) and not all(decisions), scope=NOTICE,
                expected_acceptance=decisions) and good
    return good


def production_dimensions_check(root, ev):
    """Stop at the first artifact; this checks metadata, not model execution."""
    from types import SimpleNamespace

    good = True
    for label in ("integers", "float-layer", "boolean-layer", "missing", "extra"):
        dimensions = DIMENSIONS.copy()
        if label == "float-layer":
            dimensions["layers"] = 24.0
        elif label == "boolean-layer":
            dimensions["layers"] = True
        elif label == "missing":
            del dimensions["layers"]
        elif label == "extra":
            dimensions["slice"] = 1
        model = dict(schema=1, model=MODEL, dimensions=dimensions,
                     revision="a" * 40, rope_theta=1000000, rms_norm_eps=1e-6,
                     checkpoint=[{"fixture": NOTICE}])
        calls = []

        def stop_at_artifact(descriptor):
            calls.append(descriptor)
            raise StopIteration

        diagnostic = None
        try:
            Validator.model(SimpleNamespace(artifact=stop_at_artifact), model)
        except StopIteration:
            accepted = True
        except ValueError as error:
            accepted, diagnostic = False, str(error)
        good = ev.assertion(
            "fixture_production_dimensions_" + label,
            accepted == (label == "integers") and
            len(calls) == int(label == "integers"),
            scope=NOTICE, dimensions=dimensions,
            expected_acceptance=label == "integers", observed_acceptance=accepted,
            artifact_callbacks=len(calls), diagnostic=diagnostic) and good
    return good


def observation_index_check(root, ev):
    """Isolate metadata guards; numerical arrays are deliberately not evaluated."""
    import copy
    from types import SimpleNamespace
    from teacher_observations import TeacherObservations

    good = True
    for label, field, value, accepted in (
        ("integer", "position", 0, True),
        ("boolean-position", "position", False, False),
        ("float-position", "position", 0.0, False),
        ("boolean-reference-position", "reference-position", False, False),
        ("float-reference-position", "reference-position", 0.0, False),
        ("boolean-layer-zero", "layer-zero", False, False),
        ("boolean-layer-one", "layer-one", True, False),
        ("float-layer", "layer-zero", 0.0, False),
        ("boolean-reference-layer", "reference-layer", False, False),
        ("float-reference-layer", "reference-layer", 0.0, False),
        ("reordered-layer", "layer-zero", 1, False),
    ):
        actual = dict(position=0, logits={}, repeat_logits={},
                      layers=[dict(layer=i, output={}, repeat_output={}) for i in range(24)])
        expected = dict(position=0, fp64_logits={},
                        layers=[dict(layer=i, fp64_output={}) for i in range(24)])
        if field == "position":
            actual[field] = value
        elif field == "reference-position":
            expected["position"] = value
        elif field == "reference-layer":
            expected["layers"][0]["layer"] = value
        else:
            actual["layers"][int(field == "layer-one")]["layer"] = value
        path = ev.path / ("fixture-observation-index-" + label + ".json")
        with path.open("x") as stream:
            json.dump(dict(actual=actual, expected=expected, notice=NOTICE), stream)
        calls = []
        observer = SimpleNamespace(validator=SimpleNamespace(
            arrays=lambda *args: calls.append(args)))
        observed, diagnostic = True, None
        try:
            TeacherObservations.position(observer, copy.deepcopy(actual), expected,
                                         "bf16", label)
        except ValueError as error:
            observed, diagnostic = False, str(error)
        good = ev.assertion(
            "fixture_observation_index_" + label,
            observed == accepted and len(calls) == (25 if accepted else 0),
            scope=NOTICE, numerical_arrays_evaluated=False,
            expected_acceptance=accepted, observed_acceptance=observed,
            numerical_callbacks=len(calls), diagnostic=diagnostic,
            input=str(path.relative_to(root)), sha256=sha(path)) and good
    return good


def ordered_index_check(root, ev):
    from benchmark import ordered_indices

    good = True
    for label, rows, accepted in (
        ("integers", [{"position": 0}, {"position": 1}], True),
        ("booleans", [{"position": False}, {"position": True}], False),
        ("floats", [{"position": 0.0}, {"position": 1.0}], False),
        ("reordered", [{"position": 1}, {"position": 0}], False),
        ("duplicate", [{"position": 0}, {"position": 0}], False),
        ("missing", [{"position": 0}], False),
        ("extra", [{"position": 0}, {"position": 1}, {"position": 2}], False),
        ("missing-field", [{"position": 0}, {}], False),
        ("nonobject-row", [{"position": 0}, 1], False),
        ("nonarray", {"position": 0}, False),
    ):
        for key in ("position", "layer"):
            values = ([{key: row["position"]} if "position" in row else {}
                       for row in rows] if isinstance(rows, list) and
                      all(isinstance(row, dict) for row in rows) else rows)
            observed = ordered_indices(values, key, 2)
            good = ev.assertion(
                "fixture_ordered_" + key + "_" + label, observed is accepted,
                scope=NOTICE, rows=values, expected_acceptance=accepted,
                observed_acceptance=observed) and good
    return good


def decode_check(root, ev):
    from pinned_tokenizer import BYTE_POLICY, PinnedDecoder, byte_alphabet

    alphabet = byte_alphabet()
    specification = dict(
        decoder=BYTE_POLICY, model=dict(vocab={text: byte for byte, text in alphabet.items()}),
        added_tokens=[
            dict(content="<eos>", id=256, special=True),
            dict(content="<tool_call>", id=257, special=False)])
    path = ev.path / "fixture-decoder.json"
    with path.open("x") as stream:
        json.dump(specification, stream)
    tokenizer = dict(path=str(path.relative_to(root)), sha256=sha(path))
    validator = Validator(root, ev)
    good = True
    for label, tokens, text, accepted in (
        ("plain", [52, 50, 256], "42", True),
        ("forged-answer", [110, 111, 256], "42", False),
        ("special-only", [256], "", True),
        ("special-included", [52, 256], "4<eos>", False),
        ("nonspecial-added", [257, 256], "<tool_call>", True),
        ("nonspecial-stripped", [257, 256], "", False),
        ("utf8-split", [0xc3, 0xa9, 256], "\u00e9", True),
        ("invalid-utf8", [0xc3, 256], "\ufffd", True),
        ("no-whitespace-cleanup", [32, 52, 32, 256], " 4 ", True),
        ("trimmed-text", [32, 52, 32, 256], "4", False),
        ("boolean-id", [True, 256], "\x01", False),
        ("unknown-id", [258, 256], "", False),
        ("nonstring-text", [52, 256], 4, False),
    ):
        decode = dict(tokens=tokens, text=text, tokenizer_sha256=tokenizer["sha256"])
        observed, diagnostic = True, None
        try:
            validator.decoded_text(decode, tokens, tokenizer)
        except ValueError as error:
            observed, diagnostic = False, str(error)
        good = ev.assertion(
            "fixture_decode_" + label, observed == accepted, scope=NOTICE,
            expected_acceptance=accepted, observed_acceptance=observed,
            diagnostic=diagnostic) and good
    decoder = PinnedDecoder(specification)
    good = ev.assertion(
        "fixture_decode_literal_special_preserved",
        decoder.decode([0xc3, 256, 0xa9]) == "\ufffd<eos>\ufffd" and
        decoder.decode([0xc3, 256, 0xa9], skip_special=True) == "\u00e9",
        scope=NOTICE) and good
    return good


def greedy_stop_check(root, ev):
    from benchmark import greedy_stop

    good = True
    for label, tokens, reason, eos, accepted in (
        ("eos-single", [2], "eos", [2], True),
        ("eos-limit", [1] * 127 + [2], "eos", [2], True),
        ("limit", [1] * 128, "max_new_tokens", [2], True),
        ("multiple-eos", [1, 3], "eos", [2, 3], True),
        ("eos-mislabeled-limit", [1] * 127 + [2], "max_new_tokens", [2], False),
        ("early-eos", [2, 1], "eos", [2], False),
        ("early-eos-limit", [2] + [1] * 127, "max_new_tokens", [2], False),
        ("missing-eos", [1], "eos", [2], False),
        ("short-limit", [1], "max_new_tokens", [2], False),
        ("empty", [], "eos", [2], False),
        ("over-limit", [1] * 128 + [2], "eos", [2], False),
        ("unknown-reason", [2], "other", [2], False),
        ("boolean-token", [True, 2], "eos", [2], False),
        ("out-of-range-token", [151936, 2], "eos", [2], False),
        ("empty-eos", [2], "eos", [], False),
        ("boolean-eos", [2], "eos", [True], False),
    ):
        observed, diagnostic = True, None
        try:
            greedy_stop(tokens, reason, eos)
        except ValueError as error:
            observed, diagnostic = False, str(error)
        good = ev.assertion(
            "fixture_greedy_stop_" + label, observed == accepted,
            scope=NOTICE, tokens=tokens, stop_reason=reason, eos=eos,
            expected_acceptance=accepted, observed_acceptance=observed,
            diagnostic=diagnostic) and good
    return good


def json_number_check(root, ev):
    good = True
    for label, text, accepted in (
        ("finite-exponent", '{"value":1e300}', True),
        ("negative-zero", '{"value":-0.0}', True),
        ("positive-overflow", '{"value":1e999}', False),
        ("negative-overflow", '{"value":-1e999}', False),
        ("nested-overflow", '{"values":[0,{"value":1e999}]}', False),
        ("nan-constant", '{"value":NaN}', False),
        ("infinity-constant", '{"value":Infinity}', False),
        ("negative-infinity-constant", '{"value":-Infinity}', False),
    ):
        path = ev.path / ("fixture-json-" + label + ".json")
        with path.open("x") as stream:
            stream.write(text + "\n")
        observed = True
        diagnostic = None
        try:
            load_json(path)
        except ValueError as error:
            observed = False
            diagnostic = str(error)
        good = ev.assertion(
            "fixture_json_number_" + label,
            observed == accepted and (accepted or "nonfinite JSON" in diagnostic),
            scope=NOTICE, expected_acceptance=accepted,
            observed_acceptance=observed, diagnostic=diagnostic,
            input=str(path.relative_to(root)), sha256=sha(path)) and good
    return good


def execution_identity_check(root, ev):
    """Validate saved command identities only; no fixture command is executed."""
    directory = ev.path / "execution-identity"
    directory.mkdir()

    def artifact(name, content):
        path = directory / name
        with path.open("x") as stream:
            stream.write(content)
        return dict(path=str(path.relative_to(root)), sha256=sha(path))

    output = artifact("output", NOTICE)
    stdout = artifact("stdout", NOTICE)
    stderr = artifact("stderr", NOTICE)
    bindings = {"fixture_notice": NOTICE}
    base = dict(
        schema=1, purpose="full-model-execution", bindings=bindings,
        argv=["synthetic-not-executed", "", "argument with spaces"],
        cwd=".", tool_version="synthetic fixture version 1",
        started_at="2026-01-01T00:00:00+00:00",
        ended_at="2026-01-01T00:00:01+00:00",
        timeout_s=3600, exit_code=0, timed_out=False,
        outputs=[output], stdout=stdout, stderr=stderr)
    good = True
    for label, updates, expected in (
        ("valid-empty-argument", {}, None),
        ("boolean-version", {"tool_version": True}, "execution version/timestamps missing"),
        ("numeric-version", {"tool_version": 123}, "execution version/timestamps missing"),
        ("object-version", {"tool_version": {"version": "1"}},
         "execution version/timestamps missing"),
        ("blank-version", {"tool_version": " \t"}, "execution version/timestamps missing"),
        ("empty-argv", {"argv": []}, "missing exact argv"),
        ("empty-executable", {"argv": ["", "arg"]}, "missing exact argv"),
        ("blank-executable", {"argv": [" \t"]}, "missing exact argv"),
        ("null-executable", {"argv": ["synthetic\0command"]}, "missing exact argv"),
        ("null-argument", {"argv": ["synthetic", "arg\0value"]}, "missing exact argv"),
        ("nonstring-argument", {"argv": ["synthetic", 123]}, "missing exact argv"),
    ):
        descriptor = artifact(label + ".json", json.dumps(dict(base, **updates)) + "\n")
        diagnostic = None
        try:
            Validator(root, ev).run(descriptor, bindings)
        except ValueError as error:
            diagnostic = str(error)
        good = ev.assertion(
            "fixture_execution_identity_" + label, diagnostic == expected,
            scope=NOTICE, expected_diagnostic=expected, diagnostic=diagnostic,
            input=descriptor, command_executed=False) and good
    return good


def teacher_trace_check(root, ev):
    """Exercise the real results prefix, stopping before any array comparison."""
    from types import SimpleNamespace

    directory = ev.path / "teacher-trace-types"
    directory.mkdir()
    files = []
    for index in range(3):
        path = directory / str(index)
        with path.open("x") as stream:
            stream.write(NOTICE)
        files.append(path)
    bindings = {"fixture_notice": NOTICE}
    runs = [
        dict(backend="iverilog", top="anvil_q1_fp_top",
             dimensions=DIMENSIONS.copy(), outputs=[index], stdout=index, stderr=index)
        for index in range(3)]
    runs[2].update(arithmetic="ieee-fp64", independent_of_rtl=True,
                   weight_semantics="decoded-selected-stream",
                   source_sha256={"fixture": "fixture"}, dependencies={"fixture": NOTICE})
    good = True
    for label, updates, accepted in (
        ("integers", {}, True),
        ("boolean-token", {"accepted_tokens": [True, 2]}, False),
        ("float-token", {"accepted_tokens": [1.0, 2]}, False),
        ("float-logit-count", {"logit_count_per_token": 151936.0}, False),
        ("wrong-token", {"accepted_tokens": [1, 3]}, False),
        ("fault", {"faults": ["memory"]}, False),
    ):
        trace = dict(case="fixture", mode="bf16", accepted_tokens=[1, 2],
                     faults=[], logit_count_per_token=151936)
        trace.update(updates)
        record = dict(case="fixture", mode="bf16", teacher_tokens_sha256="teacher",
                      prompt_tokens_sha256="prompt", stream_sha256="weights",
                      trace=0, positions=[])
        results = dict(schema=1, purpose="full-model-execution",
                       dimensions=DIMENSIONS.copy(), bindings=bindings,
                       cases=[record] * 150, execution=0, repeat_execution=1,
                       reference_execution=2)
        holder = SimpleNamespace(
            run=lambda descriptor, *args: runs[descriptor],
            artifact=lambda descriptor: files[descriptor] if isinstance(descriptor, int)
            else files[2],
            document=lambda descriptor: trace, produced=lambda *args: None)
        cases = {"fixture": ("Math", dict(
            teacher_tokens={"sha256": "teacher"},
            prompt_tokens={"sha256": "prompt"}), {}, [1, 2])}
        model = {"streams": {"bf16": {"weights": {"sha256": "weights"}}}}
        diagnostic = None
        try:
            Validator.results(holder, results, cases, bindings, model)
        except ValueError as error:
            diagnostic = str(error)
        expected = ("missing teacher-forced positions" if accepted else
                    "incomplete integrated token/logit trace")
        good = ev.assertion(
            "fixture_teacher_trace_" + label, diagnostic == expected,
            scope=NOTICE, trace=trace, diagnostic=diagnostic,
            expected_diagnostic=expected, numerical_arrays_evaluated=False) and good
    return good


def token_ids_check(root, ev):
    from benchmark import token_ids

    good = True
    for label, value, accepted in (
        ("integers", [0, 1, 151935], True),
        ("empty", [], True),
        ("boolean", [True], False),
        ("float", [1.0], False),
        ("negative", [-1], False),
        ("out-of-range", [151936], False),
        ("string", "12", False),
        ("null", None, False),
    ):
        good = ev.assertion(
            "fixture_token_ids_" + label, token_ids(value) is accepted,
            scope=NOTICE, value=value, expected_acceptance=accepted) and good
    return good


def selected_weight_reference_check(root, ev):
    """Exercise the real numerical comparison prefix, not model execution."""
    from types import SimpleNamespace

    directory = ev.path / "selected-weight-reference"
    directory.mkdir()

    def artifact(name, data):
        path = directory / name
        with path.open("xb") as stream:
            stream.write(data)
        return dict(path=str(path.relative_to(root)), sha256=sha(path))

    actual = artifact("synthetic-logits.f32", struct.pack("<f", 1.) * 151936)
    reference = artifact("synthetic-reference.f64", struct.pack("<d", 1.) * 151936)
    identical = artifact("synthetic-identical.f64", struct.pack("<d", 1.) * 151936)
    different = artifact("synthetic-different.f64", struct.pack("<d", -1.) * 151936)
    near = artifact("synthetic-near.f64", struct.pack("<d", 1. + 2.**-52) * 151936)
    outputs = [artifact("synthetic-run-" + str(i), NOTICE.encode()) for i in range(3)]
    bindings = {"fixture_notice": NOTICE}
    runs = [dict(backend="iverilog", top="anvil_q1_fp_top",
                 dimensions=DIMENSIONS.copy(), outputs=[output], stdout=output, stderr=output)
            for output in outputs]
    runs[2].update(arithmetic="ieee-fp64", independent_of_rtl=True,
                   weight_semantics="decoded-selected-stream",
                   source_sha256={reference["path"]: reference["sha256"]},
                   dependencies={"fixture": NOTICE})
    good = True
    for mode in ("bf16", "fp16", "w4a16"):
        for label, selected, accepted in (
            ("same-descriptor", reference, True),
            ("separate-identical", identical, True),
            ("opposite", different, False),
            ("one-fp64-ulp", near, False),
        ):
            validator = Validator(root, ev)
            trace = dict(case="fixture", mode=mode, accepted_tokens=[1],
                         faults=[], logit_count_per_token=151936,
                         cycles=[dict(accepted_to_last=3, first_logit=1,
                                      arithmetic=1, memory_stall=1, control=1)])
            position = dict(position=0, logits=actual, repeat_logits=actual,
                            fp64_logits=reference, decoded_weight_logits=selected,
                            checkpoint_fp64_logits=reference, layers=[])
            record = dict(case="fixture", mode=mode, teacher_tokens_sha256="teacher",
                          prompt_tokens_sha256="prompt", stream_sha256="weights",
                          trace=outputs[0], positions=[position])
            results = dict(schema=1, purpose="full-model-execution",
                           dimensions=DIMENSIONS.copy(), bindings=bindings,
                           cases=[record] * 150, execution=0, repeat_execution=1,
                           reference_execution=2)
            holder = SimpleNamespace(
                run=lambda descriptor, *args: runs[descriptor],
                artifact=validator.artifact, arrays=validator.arrays,
                document=lambda descriptor: trace, produced=lambda *args: None)
            cases = {"fixture": ("Math", dict(
                teacher_tokens={"sha256": "teacher"},
                prompt_tokens={"sha256": "prompt"}), {}, [1])}
            model = {"streams": {mode: {"weights": {"sha256": "weights"}}}}
            path = directory / (mode + "-" + label + ".json")
            with path.open("x") as stream:
                json.dump(dict(notice=NOTICE, position=position), stream, indent=2)
            diagnostic = None
            try:
                Validator.results(holder, results, cases, bindings, model)
            except ValueError as error:
                diagnostic = str(error)
            expected = ("missing per-layer comparisons" if accepted else
                        "selected-weight FP64 references differ: fixture/" + mode + "/0")
            good = ev.assertion(
                "fixture_selected_weight_reference_" + mode + "_" + label,
                diagnostic == expected and len(validator.metrics) == int(accepted),
                scope=NOTICE, expected_diagnostic=expected, diagnostic=diagnostic,
                numerical_comparisons=len(validator.metrics),
                input=str(path.relative_to(root)), sha256=sha(path)) and good
    return good


def repeat_identity_check(root, ev):
    """Exercise only the run-provenance prefix, never synthetic model results."""
    directory = ev.path / "repeat-identity"
    directory.mkdir()

    def artifact(name, content):
        path = directory / name
        with path.open("x") as stream:
            stream.write(content)
        return dict(path=str(path.relative_to(root)), sha256=sha(path))

    output = artifact("original-output", NOTICE)
    repeated_output = artifact("repeat-output", NOTICE)
    logs = [artifact(name, NOTICE) for name in
            ("original.stdout", "original.stderr", "repeat.stdout", "repeat.stderr",
             "reference.stdout", "reference.stderr")]
    reference_output = artifact("reference-output", NOTICE)
    source = dict(path="tests/benchmark.py", sha256=sha(root / "tests/benchmark.py"))
    bindings = dict(fixture_notice=NOTICE)
    base = dict(
        schema=1, purpose="full-model-execution", bindings=bindings,
        argv=["synthetic-provenance-fixture"], cwd=".", tool_version=NOTICE,
        started_at="2026-01-01T00:00:00+00:00",
        ended_at="2026-01-01T00:00:01+00:00",
        timeout_s=3600, exit_code=0, timed_out=False,
        backend="iverilog", top="anvil_q1_fp_top", dimensions=DIMENSIONS.copy())
    reference = dict(
        base, purpose="full-model-reference", stdout=logs[4], stderr=logs[5],
        outputs=[reference_output], arithmetic="ieee-fp64", independent_of_rtl=True,
        weight_semantics="decoded-selected-stream",
        source_sha256={source["path"]: source["sha256"]},
        dependencies={"fixture": NOTICE})
    good = True
    for label in ("distinct", "output-alias", "cross-log-alias",
                  "symlink-output-alias", "hardlink-output-alias", "log-output-alias",
                  "reference-output-alias", "reference-repeat-output-alias",
                  "reference-cross-log-alias", "reference-symlink-output-alias",
                  "reference-hardlink-output-alias",
                  "hil-distinct", "hil-output-alias", "hil-cross-log-alias",
                  "hil-log-output-alias", "hil-symlink-output-alias",
                  "hil-hardlink-output-alias", "hil-wrong-backend",
                  "hil-wrong-top", "hil-reduced-dimensions",
                  "hil-float-dimensions", "float-execution-dimensions",
                  "float-repeat-dimensions", "float-result-dimensions"):
        original = dict(base, stdout=logs[0], stderr=logs[1], outputs=[output])
        repeat = dict(base, stdout=logs[2], stderr=logs[3], outputs=[repeated_output])
        selected_reference = dict(reference)
        if label == "output-alias":
            repeat["outputs"] = [dict(output, path="./" + output["path"])]
        elif label == "cross-log-alias":
            repeat["stdout"] = dict(logs[1], path="./" + logs[1]["path"])
        elif label in ("symlink-output-alias", "hardlink-output-alias"):
            path = directory / label
            if label == "symlink-output-alias":
                path.symlink_to("original-output")
            else:
                path.hardlink_to(root / output["path"])
            repeat["outputs"] = [dict(output, path=str(path.relative_to(root)))]
        elif label == "log-output-alias":
            repeat["stdout"] = output
        elif label == "reference-output-alias":
            selected_reference["outputs"] = [dict(output, path="./" + output["path"])]
        elif label == "reference-repeat-output-alias":
            selected_reference["outputs"] = [repeated_output]
        elif label == "reference-cross-log-alias":
            selected_reference["stderr"] = logs[2]
        elif label in ("reference-symlink-output-alias", "reference-hardlink-output-alias"):
            path = directory / label
            if label == "reference-symlink-output-alias":
                path.symlink_to("original-output")
            else:
                path.hardlink_to(root / output["path"])
            selected_reference["outputs"] = [dict(output, path=str(path.relative_to(root)))]
        if label.startswith("hil-"):
            bitstream = artifact(label + "-bitstream", NOTICE)
            passes = []
            for sequence in range(1, 4):
                prefix = label + "-pass-" + str(sequence)
                passes.append(dict(
                    base, backend="arria10", sequence=sequence,
                    bitstream=bitstream, deterministic=True,
                    coverage={name: True for name in (
                        "token_logit", "memory_bridge", "precision_selection",
                        "backpressure", "reset_recovery")},
                    stdout=artifact(prefix + ".stdout", NOTICE),
                    stderr=artifact(prefix + ".stderr", NOTICE),
                    outputs=[artifact(prefix + "-output", NOTICE)]))
            if label == "hil-output-alias":
                passes[2]["outputs"] = [
                    dict(passes[0]["outputs"][0],
                         path="./" + passes[0]["outputs"][0]["path"])]
            elif label == "hil-cross-log-alias":
                passes[2]["stdout"] = passes[0]["stderr"]
            elif label == "hil-log-output-alias":
                passes[2]["stderr"] = passes[0]["outputs"][0]
            elif label in ("hil-symlink-output-alias", "hil-hardlink-output-alias"):
                path = directory / label
                original_path = root / passes[0]["outputs"][0]["path"]
                if label == "hil-symlink-output-alias":
                    path.symlink_to(original_path.name)
                else:
                    path.hardlink_to(original_path)
                passes[2]["outputs"] = [
                    dict(passes[0]["outputs"][0], path=str(path.relative_to(root)))]
            elif label == "hil-wrong-backend":
                passes[1]["backend"] = "iverilog"
            elif label == "hil-wrong-top":
                passes[1]["top"] = "arithmetic_demo"
            elif label == "hil-reduced-dimensions":
                passes[1]["dimensions"] = dict(DIMENSIONS, layers=1)
            elif label == "hil-float-dimensions":
                passes[1]["dimensions"] = dict(DIMENSIONS, layers=24.0)
            hil = artifact(label + "-hil.json", json.dumps(dict(
                part="10AX115N2F45E1SG", pcie="Gen3x8",
                passes=[artifact(label + "-pass-" + str(index) + ".json",
                                 json.dumps(record))
                        for index, record in enumerate(passes)])))
            original.update(backend="arria10", bitstream=bitstream, hil=hil)
            repeat.update(backend="arria10", bitstream=bitstream, hil=hil)
        results = dict(
            schema=1, purpose="full-model-execution", dimensions=DIMENSIONS.copy(),
            bindings=bindings, cases=[dict(case="fixture", mode="bf16")] * 150,
            execution=artifact(label + "-original.json", json.dumps(original)),
            repeat_execution=artifact(label + "-repeat.json", json.dumps(repeat)),
            reference_execution=artifact(label + "-reference.json",
                                         json.dumps(selected_reference)))
        if label == "float-result-dimensions":
            results["dimensions"] = dict(DIMENSIONS, layers=24.0)
        elif label == "float-execution-dimensions":
            original["dimensions"] = dict(DIMENSIONS, layers=24.0)
            results["execution"] = artifact(label + "-float-original.json",
                                             json.dumps(original))
        elif label == "float-repeat-dimensions":
            repeat["dimensions"] = dict(DIMENSIONS, layers=24.0)
            results["repeat_execution"] = artifact(label + "-float-repeat.json",
                                                    json.dumps(repeat))
        diagnostic = None
        try:
            Validator(root, ev).results(results, {}, bindings, {})
        except ValueError as error:
            diagnostic = str(error)
        expected = ("physical HIL pass is not the complete integrated production product"
                    if label in ("hil-wrong-backend", "hil-wrong-top",
                                 "hil-reduced-dimensions", "hil-float-dimensions") else
                    "reduced-model results" if label == "float-result-dimensions" else
                    "execution is not the complete integrated production product"
                    if label in ("float-execution-dimensions", "float-repeat-dimensions") else
                    "unknown or duplicate result case/mode"
                    if label in ("distinct", "hil-distinct") else
                    "physical HIL passes must retain separate"
                    if label.startswith("hil-") else
                    "reference execution must retain separate" if label.startswith("reference-")
                    else "repeat execution must retain separate")
        good = ev.assertion(
            "fixture_repeat_identity_" + label,
            diagnostic is not None and expected in diagnostic,
            scope=NOTICE, expected_diagnostic=expected, diagnostic=diagnostic) and good
    return good


def fixture(project):
    data = project / "tests/data"
    data.mkdir(parents=True)

    def artifact(name, content):
        path = data / name
        path.write_text(json.dumps(content) + "\n")
        return dict(path=str(path.relative_to(project)), sha256=sha(path))

    dummy = artifact("fixture-blob.json", dict(notice=NOTICE))
    tensors = {"model.embed_tokens.weight": dict(shape=[151936, 896]),
               "model.norm.weight": dict(shape=[896])}
    for layer in range(24):
        for suffix, shape in {
            "input_layernorm.weight": [896], "post_attention_layernorm.weight": [896],
            "self_attn.q_proj.weight": [896, 896], "self_attn.k_proj.weight": [128, 896],
            "self_attn.v_proj.weight": [128, 896], "self_attn.o_proj.weight": [896, 896],
            "self_attn.q_proj.bias": [896], "self_attn.k_proj.bias": [128],
            "self_attn.v_proj.bias": [128], "mlp.gate_proj.weight": [4864, 896],
            "mlp.up_proj.weight": [4864, 896], "mlp.down_proj.weight": [896, 4864],
        }.items():
            tensors[f"model.layers.{layer}.{suffix}"] = dict(shape=shape)
    for tensor in tensors.values():
        tensor["checkpoint_path"] = dummy["path"]
    layout = artifact("fixture-layout.json", dict(
        model_revision="a"*40, tensors=tensors, tied_output_embedding=True))
    config = artifact("fixture-config.json", dict(
        num_hidden_layers=24, hidden_size=896, intermediate_size=4864,
        num_attention_heads=14, num_key_value_heads=2, vocab_size=151936,
        max_position_embeddings=32768, rope_theta=1000000.0, rms_norm_eps=1e-6,
        tie_word_embeddings=True, eos_token_id=151645))
    model = dict(
        schema=1, fixture_notice=NOTICE, model=MODEL, revision="a"*40,
        dimensions=DIMENSIONS.copy(), rope_theta=1000000, rms_norm_eps=1e-6,
        checkpoint=[dummy], tokenizer=dummy, chat_template=dummy, config=config,
        tensor_layout=layout, streams={})
    for mode in ("bf16", "fp16", "w4a16"):
        model["streams"][mode] = dict(
            checkpoint_sha256={dummy["path"]: dummy["sha256"]},
            weights=dummy, layout=layout, recipe=NOTICE, tool_version="fixture",
            encoding=mode, rounding="nearest-even", bits=4, group_size=128,
            nibble_order=[0, 4, 1, 5, 2, 6, 3, 7],
            scales=dummy, zeros=dummy, calibration=dummy)
    suite = dict(
        schema=1, fixture_notice=NOTICE, suite="anvil-five-domain-v1",
        tokenizer_sha256=dummy["sha256"], chat_template_sha256=dummy["sha256"],
        decoding=dict(greedy=True, tie_break="lowest-token-id", max_new_tokens=128,
                      sampling=False), domains={})
    ids = [f"{i:03d}" for i in range(10)]
    tokens = artifact("fixture-tokens.json", [1])
    for domain, dataset in DOMAINS.items():
        cases = []
        for case_id in ids:
            content = artifact(f"fixture-{domain}-{case_id}.json", dict(
                id=case_id, prompt=NOTICE, answers=["fixture"], verified=True))
            cases.append(dict(id=case_id, content=content, prompt_tokens=tokens,
                              teacher_tokens=tokens))
        inventory = artifact("fixture-" + domain + "-ids.json", dict(
            ids=ids, dataset=dataset, revision="b"*40,
            content_sha256={case["id"]: case["content"]["sha256"] for case in cases}))
        suite["domains"][domain] = dict(
            dataset=dataset, revision="b"*40, canonical_inventory=inventory,
            cases=cases, seed=17, generator_version=1, generator=dummy,
            verified_only=True)
    artifact("model_manifest.json", model)
    artifact("benchmark_manifest.json", suite)
    bindings = dict(
        model_manifest=sha(data / "model_manifest.json"),
        benchmark_manifest=sha(data / "benchmark_manifest.json"),
        source_sha256={str(p.relative_to(project)): sha(p)
                       for selector in ("rtl/*.sv", "fpga/*")
                       for p in project.glob(selector) if p.is_file()})
    result = dict(schema=1, fixture_notice=NOTICE, purpose="full-model-execution",
                  dimensions=DIMENSIONS.copy(), bindings=bindings, cases=[])
    artifact("full_model_results.json", result)
    return model, suite, result


def check(root, ev):
    import sys

    ev.receipt["scope"] = NOTICE
    good = library_entrypoint_check(root, ev)
    good = failure_diagnostics_check(root, ev) and good
    good = component_diagnostics_check(root, ev) and good
    good = prerequisite_dependencies_check(root, ev) and good
    good = reference_environment_check(root, ev) and good
    good = production_interface_check(root, ev) and good
    good = artifact_path_check(root, ev) and good
    good = entry_document_path_check(root, ev) and good
    good = teacher_descriptor_path_check(root, ev) and good
    good = json_number_check(root, ev) and good
    good = execution_identity_check(root, ev) and good
    good = measured_cycles_check(root, ev) and good
    good = zero_output_check(root, ev) and good
    good = numerical_boundary_check(root, ev) and good
    good = teacher_trace_check(root, ev) and good
    good = selected_weight_reference_check(root, ev) and good
    good = token_ids_check(root, ev) and good
    good = production_dimensions_check(root, ev) and good
    good = observation_index_check(root, ev) and good
    good = ordered_index_check(root, ev) and good
    good = decode_check(root, ev) and good
    good = greedy_stop_check(root, ev) and good
    good = repeat_identity_check(root, ev) and good
    cases = (
        ("missing", "missing artifact"),
        ("missing-results", "missing artifact"),
        ("missing-results-bad-model", "missing artifact"),
        ("missing-results-bad-suite", "missing artifact"),
        ("malformed", "JSONDecodeError"),
        ("duplicate-json", "duplicate JSON key"),
        ("nonfinite-json", "nonfinite JSON constant"),
        ("overflow-json", "nonfinite JSON number"),
        ("boolean-schema", "wrong checkpoint"),
        ("integer-greedy", "different decoding settings"),
        ("integer-sampling", "different decoding settings"),
        ("float-generation-limit", "different decoding settings"),
        ("wrong-dimensions", "not the complete production model"),
        ("float-config-layers", "checkpoint configuration mismatch: num_hidden_layers"),
        ("integer-config-tied", "checkpoint configuration mismatch: tie_word_embeddings"),
        ("integer-config-theta", "requires 50 cases"),
        ("float-tensor-shape", "tensor missing/wrong shape"),
        ("float-awq-bits", "AWQ layout differs from parent"),
        ("float-awq-group", "AWQ layout differs from parent"),
        ("float-awq-nibble", "AWQ layout differs from parent"),
        ("boolean-awq-zero", "AWQ layout differs from parent"),
        ("boolean-awq-one", "AWQ layout differs from parent"),
        ("hash-mismatch", "artifact hash mismatch"),
        ("escaping-path", "nonportable artifact path"),
        ("case-completeness", "requires 50 cases"),
        ("source-binding", "results bound to different sources"),
        ("fixture-purpose", "synthetic/fixture results"),
        ("wrong-corpus-order", "first ten canonical IDs"),
        ("unverified-qa", "unverified TriviaQA"),
    )
    for label, expected in cases:
        project = ev.path / ("fixture-" + label)
        (project / "tests").mkdir(parents=True)
        for path in (root / "tests").glob("*.py"):
            shutil.copy2(path, project / "tests" / path.name)
        # The validator binds the real sources but does not execute them here.
        for directory in ("rtl", "fpga"):
            shutil.copytree(root / directory, project / directory)
        model, suite, result = fixture(project)
        data = project / "tests/data"
        if label == "missing":
            (data / "model_manifest.json").unlink()
        elif label == "missing-results":
            for domain in suite["domains"].values():
                for index, case in enumerate(domain["cases"], 1):
                    tokens = data / ("fixture-teacher-" + str(index) + ".json")
                    tokens.write_text(json.dumps([1] * index) + "\n")
                    case["teacher_tokens"] = dict(
                        path=str(tokens.relative_to(project)), sha256=sha(tokens))
        elif label == "malformed":
            (data / "model_manifest.json").write_text('{"bad":')
        elif label == "duplicate-json":
            (data / "model_manifest.json").write_text('{"schema":1,"schema":1}')
        elif label == "nonfinite-json":
            (data / "model_manifest.json").write_text('{"bad":NaN}')
        elif label == "overflow-json":
            (data / "model_manifest.json").write_text('{"bad":1e999}')
        elif label == "wrong-dimensions":
            model["dimensions"]["layers"] = 1
        elif label in ("float-config-layers", "integer-config-tied", "integer-config-theta"):
            config_path = project / model["config"]["path"]
            config = load_json(config_path)
            if label == "float-config-layers":
                config["num_hidden_layers"] = 24.0
            elif label == "integer-config-tied":
                config["tie_word_embeddings"] = 1
            else:
                config["rope_theta"] = 1000000
            config_path.write_text(json.dumps(config) + "\n")
            model["config"]["sha256"] = sha(config_path)
        elif label == "missing-results-bad-model":
            model["dimensions"]["layers"] = 1
        elif label == "float-tensor-shape":
            layout_path = project / model["tensor_layout"]["path"]
            layout = load_json(layout_path)
            layout["tensors"]["model.embed_tokens.weight"]["shape"][0] = 151936.0
            layout_path.write_text(json.dumps(layout) + "\n")
            model["tensor_layout"]["sha256"] = sha(layout_path)
            for stream in model["streams"].values():
                stream["layout"]["sha256"] = sha(layout_path)
        elif label.startswith(("float-awq-", "boolean-awq-")):
            stream = model["streams"]["w4a16"]
            if label == "float-awq-bits":
                stream["bits"] = 4.0
            elif label == "float-awq-group":
                stream["group_size"] = 128.0
            elif label == "float-awq-nibble":
                stream["nibble_order"][1] = 4.0
            elif label == "boolean-awq-zero":
                stream["nibble_order"][0] = False
            else:
                stream["nibble_order"][2] = True
        elif label == "missing-results-bad-suite":
            suite["domains"]["Math"]["cases"].reverse()
        elif label == "boolean-schema":
            model["schema"] = True
        elif label == "integer-greedy":
            suite["decoding"]["greedy"] = 1
        elif label == "integer-sampling":
            suite["decoding"]["sampling"] = 0
        elif label == "float-generation-limit":
            suite["decoding"]["max_new_tokens"] = 128.0
        elif label == "hash-mismatch":
            (data / "fixture-blob.json").write_text(NOTICE + "\nchanged\n")
        elif label == "escaping-path":
            model["tokenizer"] = dict(path="../not-project-data", sha256="0"*64)
        elif label == "source-binding":
            result["bindings"]["source_sha256"] = {}
        elif label == "fixture-purpose":
            result["purpose"] = "fixture-only"
        elif label == "wrong-corpus-order":
            suite["domains"]["Math"]["cases"].reverse()
        elif label == "unverified-qa":
            content = data / "fixture-QA-000.json"
            item = json.loads(content.read_text())
            item["verified"] = False
            content.write_text(json.dumps(item) + "\n")
            suite["domains"]["QA"]["cases"][0]["content"]["sha256"] = sha(content)
            inventory = data / "fixture-QA-ids.json"
            item = json.loads(inventory.read_text())
            item["content_sha256"]["000"] = sha(content)
            inventory.write_text(json.dumps(item) + "\n")
            suite["domains"]["QA"]["canonical_inventory"]["sha256"] = sha(inventory)
        if label not in ("missing", "malformed", "duplicate-json", "nonfinite-json",
                         "overflow-json"):
            for name, document in (("model_manifest", model), ("benchmark_manifest", suite),
                                   ("full_model_results", result)):
                (data / (name + ".json")).write_text(json.dumps(document) + "\n")
            if label != "source-binding":
                result["bindings"]["model_manifest"] = sha(data / "model_manifest.json")
                result["bindings"]["benchmark_manifest"] = sha(data / "benchmark_manifest.json")
                (data / "full_model_results.json").write_text(json.dumps(result) + "\n")
        if label.startswith("missing-results"):
            (data / "full_model_results.json").unlink()
        ev.run("entrypoint-" + label, [
            sys.executable, "tests/verify.py", "--check", "benchmark-contract"],
            timeout=3600, cwd=project)
        record = ev.receipt["records"][-1]
        output = (root / record["stdout"]).read_text().splitlines()
        require_rejection = record.get("exit_code") == 1 and not record["timed_out"] and bool(output)
        child_path = None
        if require_rejection:
            child_path = project / json.loads(output[-1])["receipt"]
            child = json.loads(child_path.read_text())
            require_rejection = (child["status"] == "failed" and any(
                a["name"] == "full_model_inputs_and_execution" and not a["passed"] and
                expected in a["reason"] for a in child["assertions"]))
            if label.startswith("missing-results"):
                expected_input = label == "missing-results"
                diagnostic = {
                    "missing-results-bad-model": "not the complete production model",
                    "missing-results-bad-suite": "first ten canonical IDs",
                }.get(label)
                require_rejection = require_rejection and any(
                    a["name"] == "full_model_available_inputs" and
                    a["passed"] == expected_input and
                    (diagnostic is None or diagnostic in a.get("reason", ""))
                    for a in child["assertions"])
                reports = [a["collection_requirements"] for a in child["assertions"]
                           if a["name"] == "full_model_available_inputs" and
                           a["passed"] and "collection_requirements" in a]
                if expected_input:
                    require_rejection = require_rejection and len(reports) == 1
                    if len(reports) == 1:
                        report_path = project / reports[0]["path"]
                        report = load_json(report_path)
                        expected_positions = sum(
                            len(load_json(project / case["teacher_tokens"]["path"]))
                            for domain in suite["domains"].values()
                            for case in domain["cases"]) * 3
                        expected_cases = {
                            name + "/" + case["id"]: case
                            for name, domain in suite["domains"].items()
                            for case in domain["cases"]}
                        require_rejection = require_rejection and (
                            sha(report_path) == reports[0]["sha256"] and
                            report["purpose"] == "offline-collection-requirements" and
                            report["acceptance_evidence"] is False and
                            report["execution_established"] is False and
                            report["endpoint_contacted"] is False and
                            report["resume_prerequisites"]["status"] ==
                            "qualification-not-established" and
                            report["resume_prerequisites"].get("scope") ==
                            "physical-benchmark-collection" and
                            report["resume_prerequisites"].get("permitted_benchmark_backends") ==
                            ["iverilog", "verilator", "arria10"] and
                            report["resume_prerequisites"].get("simulation_alternative") == dict(
                                backends=["iverilog", "verilator"],
                                status="execution-not-established",
                                requires_complete_production_model=True,
                                requires_all_cases_modes_and_repeats=True,
                                requires_independent_fp64_and_measured_cycles=True,
                                substitutes_for_native_gates=False) and
                            report["resume_prerequisites"].get("mandatory_native_gates") ==
                            ["rtl-timing-lint", "quartus-sta", "board-hil"] and
                            report["resume_prerequisites"]["endpoint_availability"] ==
                            "not-determined" and
                            report["resume_prerequisites"]["policy_denial_is_rtl_failure"]
                            is False and
                            next(item for item in child["assertions"]
                                 if item["name"] == "full_model_inputs_and_execution")[
                                     "resume_prerequisites"] ==
                            report["resume_prerequisites"] and
                            len(report["resume_prerequisites"]["required_platform_inputs"]) == 3 and
                            len(report["resume_prerequisites"]["qualification_must_establish"]) == 5 and
                            report["required"]["case_mode_records"] == 150 and
                            report["required"]["teacher_position_mode_records"] ==
                            expected_positions and len(report["cases"]) == 50 and
                            [row["case"] for row in report["cases"]] ==
                            sorted(expected_cases) and
                            all(row["teacher_tokens"] ==
                                expected_cases[row["case"]]["teacher_tokens"] and
                                row["prompt_tokens"] ==
                                expected_cases[row["case"]]["prompt_tokens"] and
                                row["teacher_positions"] == len(load_json(
                                    project / row["teacher_tokens"]["path"]))
                                for row in report["cases"]) and
                            report["modes"] == ["bf16", "fp16", "w4a16"] and
                            report["required"]["logits_per_position"] == 151936 and
                            report["required"]["layer_outputs_per_position"] == 24 and
                            report["required"]["values_per_layer"] == 896 and
                            report["required"]["independent_dut_runs"] == 2 and
                            report["bindings"] == result["bindings"])
                else:
                    require_rejection = require_rejection and not reports and not (
                        child_path.parent / "collection-requirements.json").exists() and (
                            next(item for item in child["assertions"]
                                 if item["name"] == "full_model_inputs_and_execution")[
                                     "resume_prerequisites"] is None)
            ev.receipt.setdefault("children", []).append(str(child_path.relative_to(root)))
        good = ev.assertion("fixture_entrypoint_rejects_" + label, require_rejection,
                            scope=NOTICE, expected_diagnostic=expected) and good

    validator = Validator(root, ev)

    def array(name, values, code):
        path = ev.path / name
        path.write_bytes(struct.pack("<" + code*len(values), *values))
        return dict(path=str(path.relative_to(root)), sha256=sha(path))

    actual = array("fixture-good.f32", [1., -2., 3.], "f")
    reference = array("fixture-reference.f64", [1., -2., 3.], "d")
    zero = array("fixture-zero.f32", [0., 0., 0.], "f")
    zero_ref = array("fixture-zero.f64", [0., 0., 0.], "d")
    opposite = array("fixture-opposite.f32", [-1., 2., -3.], "f")
    nonfinite = array("fixture-infinity.f32", [float("inf"), -2., 3.], "f")
    nan = array("fixture-nan.f32", [float("nan"), -2., 3.], "f")
    small = array("fixture-small.f32", [.001, 0., 0.], "f")
    orthogonal = array("fixture-orthogonal.f64", [0., .001, 0.], "d")
    scaled = array("fixture-scaled.f32", [1.1, -2.2, 3.3], "f")
    for label, a, r, repeat, accepted in (
        ("known-positive", actual, reference, actual, True),
        ("zero-absolute", zero, zero_ref, zero, True),
        ("cosine-negative", opposite, reference, opposite, False),
        ("cosine-only-failure", small, orthogonal, small, False),
        ("absolute-error-only-failure", scaled, reference, scaled, False),
        ("zero-reference-error", actual, zero_ref, actual, False),
        ("nondeterministic", actual, reference, opposite, False),
        ("nonfinite", nonfinite, reference, nonfinite, False),
        ("nan", nan, reference, nan, False),
        ("truncated", array("fixture-short.f32", [1.], "f"), reference, actual, False),
    ):
        passed = True
        try:
            validator.arrays(a, r, repeat, 3, (.999, .01), NOTICE + "/" + label)
        except ValueError:
            passed = False
        good = ev.assertion("fixture_numerical_" + label, passed == accepted,
                            scope=NOTICE, expected_acceptance=accepted) and good
    good = ev.assertion("fixture_zero_reference_has_no_invented_cosine",
                        validator.metrics[1]["cosine"] is None) and good
    one_ulp = array("fixture-one-ulp.f32", [1. + 2.**-23], "f")
    one = array("fixture-one.f64", [1.], "d")
    validator.arrays(one_ulp, one, one_ulp, 1, (.999, .01), NOTICE + "/one-ulp")
    good = ev.assertion("fixture_ordered_ulp_and_xor",
                        validator.metrics[-1]["max_ulp"] == 1 and
                        validator.metrics[-1]["max_xor"] == 1) and good
    # Never emit production benchmark results or task scores from these fixtures.
    return good
