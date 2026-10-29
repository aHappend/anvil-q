"""Bounded routing, single-flight build reuse and dual-simulator regressions."""

from concurrent.futures import ThreadPoolExecutor
import json


def check(root, ev):
    # Import the active entrypoint, not a second copy with a separate build cache.
    import sys
    verify = sys.modules.get("__main__")
    if not hasattr(verify, "simulation_tier"):
        import verify

    cases = (
        ("compact", {}, "iverilog"),
        ("compact32", {"hidden": 32}, "iverilog"),
        ("gqa56", {"hidden": 56}, "verilator"),
        ("medium64", {"hidden": 64}, "verilator"),
        ("multi-token", {"tokens": 3}, "verilator"),
        ("multi-seed", {"seeds": 3}, "verilator"),
        ("cycle-boundary", {"cycles": 500000}, "iverilog"),
        ("long-cycle", {"cycles": 500001}, "verilator"),
        ("full-leaves", {"full": True}, "verilator"),
        ("mutant", {"mutation": True}, "verilator"),
        ("protocol", {"protocol": True}, "verilator"),
    )
    good = True
    for name, options, expected in cases:
        actual = verify.simulation_tier("iverilog", **options)
        good = ev.assertion("route_" + name, actual == expected,
                            options=options, expected=expected, observed=actual) and good
    good = ev.assertion("compiled_never_downgraded",
                        verify.simulation_tier("verilator") == "verilator") and good
    jobs = verify.l1_jobs()
    ev.receipt["planned_l1_shards"] = [
        {"name": name, "check": check.__name__, "args": list(args),
         "options": options, "status": "planned"}
        for name, check, args, options in jobs]
    ev.finish("running")
    names = [name for name, _, _, _ in jobs]
    integrations = [
        (name, mode, seed, options)
        for _, check, _, options in jobs
        if check is verify.integration_check and options.get("full")
        for name in options["configurations"] for mode in options["modes"]
        for seed in options["seeds"]]
    required_integrations = [(name, mode, seed) for name in verify.CONFIGURATIONS
                             for mode in (0, 1, 2) for seed in (17, 53, 89)]
    good = ev.assertion(
        "fresh_complete_integration_shards",
        len(names) == len(set(names)) and
        sorted((name, mode, seed) for name, mode, seed, _ in integrations) ==
        sorted(required_integrations) and all(
            options["configurations"] == {name: verify.CONFIGURATIONS[name]} and
            len(options["modes"]) == len(options["seeds"]) == 1
            for name, _, _, options in integrations),
        cases=[list(case) for case in required_integrations]) and good
    production = [
        (operator, selector, mode)
        for _, check, _, options in jobs
        if check is verify.operator_check and options.get("production")
        for operator, selector, mode in options["cases"]]
    required = [(operator, selector, mode)
                for operator in verify.OPERATOR_IDS
                for selector in (range(7) if operator == "gemv" else
                                 range(3) if operator in ("norm", "elementwise") else (0,))
                for mode in (0, 1, 2)]
    good = ev.assertion(
        "fresh_complete_production_shards",
        sorted(production) == sorted(required) and all(
            len(options["cases"]) == 1 for _, check, _, options in jobs
            if check is verify.operator_check and options.get("production")),
        expected_cases=len(required), scheduled_cases=len(production)) and good
    good = ev.assertion(
        "missing_and_duplicate_shards_detected",
        sorted(production[1:]) != sorted(required) and
        sorted(production + production[:1]) != sorted(required)) and good

    parent = verify.Evidence("scheduling-inventory")
    parent.receipt["tool_versions_receipt"] = str((ev.path / "receipt.json").relative_to(root))

    def inventory_fixture(child, index):
        rows = parent.receipt["shards"]
        complete = (len(rows) == 7 and all(
            [step["status"] for step in row["history"]][:2] == ["planned", "queued"]
            for row in rows))
        return child.assertion("complete_inventory_before_launch", complete, index=index)

    scheduled = verify.parallel_components(parent, [
        ("inventory" + str(index), inventory_fixture, (index,), {}) for index in range(7)])
    parent.finish("passed" if all(scheduled.values()) else "failed")
    ev.receipt.setdefault("children", []).append(str((parent.path / "receipt.json").relative_to(root)))
    good = ev.assertion(
        "complete_queue_running_completion_ledger",
        len(scheduled) == 7 and all(scheduled.values()) and all(
            [step["status"] for step in row["history"]] ==
            ["planned", "queued", "running", "completed"] and
            row["child_receipt"] and row["passed"] for row in parent.receipt["shards"])
        and parent.receipt["shard_counts"] ==
        {"planned": 0, "queued": 0, "running": 0, "completed": 7, "failed": 0}) and good

    fixture = ev.path / "cache-fixture.sv"
    original_source = (
        'module cache_fixture; parameter VALUE=17; initial begin '
        '$display("CACHE_VALUE %0d",VALUE); $finish; end endmodule\n')
    fixture.write_text(original_source)
    ev.receipt.setdefault("data_sha256", {})[str(fixture.relative_to(root))] = verify.digest(fixture)

    def build_run(index, value=17, tag="CACHE_VALUE"):
        child = verify.Evidence("scheduling-cache-" + str(index))
        child.receipt["tool_versions_receipt"] = str((ev.path / "receipt.json").relative_to(root))
        binary = child.path / "fixture.sim"
        argv = ["verilator", "--binary", "--timing", "-Wno-fatal", "-j", "2",
                "--top-module", "cache_fixture", "--Mdir",
                str((child.path / "obj").relative_to(root)), "-o", str(binary),
                f"-GVALUE={value}", str(fixture.relative_to(root))]
        passed = False
        try:
            compiled = verify.compile_simulation(child, "fixture-compile", argv, binary)
            executed = compiled and child.run("fixture-run", [str(binary)])
            output = (child.path / "fixture-run.stdout").read_text() if executed else ""
            passed = child.assertion(
                "fixture_result", executed and f"{tag} {value}" in output.splitlines())
            return passed, child
        finally:
            child.finish("passed" if passed else "failed")

    with ev.profile("single-flight-concurrent-build"), ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(build_run, range(4)))
    builds = [child.receipt["builds"][0] for _, child in results]
    same = all(passed for passed, _ in results) and len({b["key"] for b in builds}) == 1
    good = ev.assertion("single_flight_identical_build",
                        same and sum(not b["reused"] for b in builds) == 1,
                        builds=builds) and good
    changed_parameter, parameter_child = build_run("parameter", 53)
    good = ev.assertion(
        "parameter_change_rebuilds",
        changed_parameter and parameter_child.receipt["builds"][0]["key"] != builds[0]["key"]
        and not parameter_child.receipt["builds"][0]["reused"]) and good
    fixture.write_text(fixture.read_text().replace("CACHE_VALUE", "CHANGED_CACHE_VALUE"))
    changed_source, source_child = build_run("source", tag="CHANGED_CACHE_VALUE")
    good = ev.assertion(
        "source_change_rebuilds",
        changed_source and source_child.receipt["builds"][0]["key"] != builds[0]["key"]
        and not source_child.receipt["builds"][0]["reused"]) and good
    # A missing cache output triggers fresh execution, never a historical pass.
    fixture.write_text(original_source)
    entry = verify._BUILDS.entries[builds[0]["key"]]
    original_binary = entry["binary"]
    missing_binary = original_binary.with_name("absent.sim")
    entry["binary"] = missing_binary
    try:
        missing_passed, missing_child = build_run("missing")
    finally:
        entry["binary"] = original_binary
    good = ev.assertion(
        "missing_build_regenerated",
        missing_passed and not missing_child.receipt["builds"][0]["reused"]
        and original_binary.is_file(),
        original_receipt=builds[0]["receipt"],
        repair_receipt=missing_child.receipt["builds"][0]["receipt"]) and good
    for _, child in results:
        ev.receipt.setdefault("children", []).append(str((child.path / "receipt.json").relative_to(root)))
    for child in (parameter_child, source_child, missing_child):
        ev.receipt["children"].append(str((child.path / "receipt.json").relative_to(root)))

    # Actual public-pin, unchanged numerical assertions in both simulators.
    leaves = []
    for name, simulator in (("icarus", "iverilog"), ("compiled", "verilator")):
        good = verify.component(ev, "scheduling-leaf-" + name, verify.leaf_check,
                                full=False, simulator=simulator) and good
        leaves.append(root / ev.receipt["children"][-1])
    good = ev.assertion(
        "compact_dual_simulator_exact_trace",
        all(verify.digest(leaves[0].parent / name) ==
            verify.digest(leaves[1].parent / name)
            for name in ("leaf-input.txt", "leaf-output.txt")),
        receipts=[str(path.relative_to(root)) for path in leaves]) and good
    good = verify.component(
        ev, "scheduling-auto-integration", verify.integration_check,
        configurations={"minimum": verify.CONFIGURATIONS["minimum"]},
        modes=(1,), seeds=(17, 53), simulator="iverilog") and good
    integration = json.loads((root / ev.receipt["children"][-1]).read_text())
    good = ev.assertion(
        "multi_seed_actually_compiled",
        integration["simulation_routes"][0]["selected"] == "verilator" and
        all(record["argv"][0] != "vvp" for record in integration["records"])) and good
    good = verify.component(ev, "scheduling-icarus-startup", verify.startup_check) and good
    return good
