"""Bounded routing, single-flight build reuse and dual-simulator regressions."""

from concurrent.futures import ThreadPoolExecutor


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

    fixture = ev.path / "cache-fixture.sv"
    original_source = (
        'module cache_fixture; parameter VALUE=17; initial begin '
        '$display("CACHE_VALUE %0d",VALUE); $finish; end endmodule\n')
    fixture.write_text(original_source)
    ev.receipt.setdefault("data_sha256", {})[str(fixture.relative_to(root))] = verify.digest(fixture)

    def build_run(index, value=17):
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
            passed = child.assertion("fixture_result", executed and f"CACHE_VALUE {value}" in output)
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
    changed_source, source_child = build_run("source")
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
    for name, simulator in (("icarus", "iverilog"), ("compiled", "verilator")):
        good = verify.component(ev, "scheduling-leaf-" + name, verify.leaf_check,
                                full=False, simulator=simulator) and good
    good = verify.component(
        ev, "scheduling-auto-integration", verify.integration_check,
        configurations={"minimum": verify.CONFIGURATIONS["minimum"]},
        modes=(1,), seeds=(17, 53), simulator="iverilog") and good
    return good
