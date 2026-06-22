"""Compare model outputs to official French government simulator values.

The independent-oracle layer: rows whose ``official`` is still null are SKIPPED
(not failed), so an uncaptured oracle never produces a false green. Capture
official numbers by driving the simulators in ``meta`` (see
docs/cowork-validation-brief.md) and fill ``official`` + ``captured_on``.
"""

import pathlib

import yaml
import pytest

FIXTURE = pathlib.Path(__file__).parent / "fixtures" / "oracle_values.yaml"
_DATA = yaml.safe_load(FIXTURE.read_text(encoding="utf-8"))
_TOL = _DATA["meta"]["tolerances"]


@pytest.mark.parametrize("row", _DATA["households"], ids=lambda r: r["id"])
def test_model_matches_official_oracle(row):
    official = row.get("official")
    if official is None:
        pytest.skip(f"{row['id']}: official value not yet captured")
    tol = _TOL[row["variable"]]
    delta = row["model"] - official
    assert abs(delta) <= tol, (
        f"{row['id']} {row['variable']}: model {row['model']} vs official "
        f"{official} (Δ {delta:+.2f}, tol {tol})"
    )
