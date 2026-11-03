"""Numerical matrix with exact-bit DUT comparisons and independent analytic checks."""

from decimal import Decimal, localcontext
from fractions import Fraction
import json

from leaf_checks import run_elementary, run_qk, run_tensor_cpp
import reference as fp


def analytic_coefficients():
    """Decimal transcendental evaluation cross-checks the binary64 oracle."""
    pi = Decimal("3.141592653589793238462643383279502884197169399375105820974944592307816406286208998628")
    records = []
    with localcontext() as context:
        context.prec = 80
        for dimension in (8, 128):
            for position in (0, 1, 32767, 32768, 40959):
                cosines, sines = fp.coefficients(dimension, position)
                for coordinate in range(dimension // 2):
                    power = Decimal(-2 * coordinate) / dimension
                    angle = Decimal(position) * (Decimal(1000000).ln() * power).exp()
                    reduced = angle % (2 * pi)
                    if reduced > pi:
                        reduced -= 2 * pi
                    # Evaluate cosine and sine independently, with no shared float table.
                    values = []
                    for start, first_denominator in ((Decimal(1), 1), (reduced, 2)):
                        term = total = start
                        denominator = first_denominator
                        for _ in range(200):
                            term *= -(reduced * reduced) / (denominator * (denominator + 1))
                            total += term
                            denominator += 2
                            if abs(term) < Decimal("1e-70"):
                                break
                        else:
                            raise AssertionError("Decimal trigonometric convergence")
                        values.append(fp.encode(Fraction(total), 16))
                    if values != [cosines[coordinate], sines[coordinate]]:
                        raise AssertionError(f"independent RoPE coefficient mismatch D={dimension} "
                                             f"position={position} coordinate={coordinate}")
                records.append({"dimension": dimension, "position": position,
                                "coefficient_comparisons": dimension})
    if sum(r["coefficient_comparisons"] for r in records) != 680:
        raise AssertionError("required independent coefficient coverage missing")
    return records


def run_numerical(run):
    coefficients = analytic_coefficients()
    (run.path / "analytic-coefficients.json").write_text(json.dumps(coefficients, indent=2) + "\n")
    results = {
        "coefficients": coefficients,
        "tensor": run.component("numerical-tensor", lambda child: run_tensor_cpp(child, True)),
        "qk": run.component("numerical-qk",
                            lambda child: run_qk(child, "verilator", 128, True, stress=True)),
        "elementary": run.component("numerical-elementary", run_elementary),
    }
    if (results["tensor"]["tensor_cases"] != 1536 or results["qk"]["qk_cases"] != 775 or
            results["qk"]["compared_elements"] != 99200 or
            results["qk"]["analytic"]["scale_pairs"] != 96):
        raise AssertionError("mandatory numerical matrix counts incomplete")
    return results
