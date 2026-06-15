"""Property-based / metamorphic tests.

These assert invariants that must hold *regardless of the exact reference
values* — so they catch whole classes of bugs (sign errors, non-monotonicity,
mis-wired benefits) that self-authored unit tests can miss. They do NOT prove
the numbers are correct against the statute — that is the job of the
independent-oracle validation (see docs/cowork-validation-brief.md).
"""

from __future__ import annotations

import math

from hypothesis import given, settings, strategies as st

from helpers import build_household, YEAR

Y = str(YEAR)
SETTINGS = settings(max_examples=40, deadline=None)

incomes = st.integers(min_value=0, max_value=300_000)
positive_delta = st.integers(min_value=1, max_value=50_000)
child_age = st.integers(min_value=0, max_value=17)
children = st.lists(child_age, min_size=0, max_size=4)


@SETTINGS
@given(income=incomes)
def test_impot_revenu_non_negative(income):
    sim = build_household([income], [])
    assert sim.calculate("impot_revenu", Y).sum() >= -0.01


@SETTINGS
@given(income=incomes, delta=positive_delta)
def test_impot_revenu_monotonic_in_income(income, delta):
    # More income never lowers the income tax (single adult, no children).
    low = build_household([income], []).calculate("impot_revenu", Y).sum()
    high = build_household([income + delta], []).calculate("impot_revenu", Y).sum()
    assert high >= low - 0.01


@SETTINGS
@given(income=incomes, delta=positive_delta)
def test_impot_revenu_marginal_below_one(income, delta):
    # The extra tax from extra income never exceeds the extra income
    # (no marginal rate above 100%).
    low = build_household([income], []).calculate("impot_revenu", Y).sum()
    high = build_household([income + delta], []).calculate("impot_revenu", Y).sum()
    assert (high - low) <= delta + 0.01


@SETTINGS
@given(income=incomes)
def test_csg_crds_exact_and_non_negative(income):
    sim = build_household([income], [])
    csg = sim.calculate("csg", Y).sum()
    crds = sim.calculate("crds", Y).sum()
    base = income * 0.9825
    assert csg >= -0.01 and crds >= -0.01
    assert math.isclose(csg, 0.092 * base, abs_tol=0.5)
    assert math.isclose(crds, 0.005 * base, abs_tol=0.5)


@SETTINGS
@given(income=incomes, kids=children)
def test_quotient_familial_only_reduces_tax(income, kids):
    # At equal income, more parts (children) never raise the income tax.
    base = build_household([income, 0], []).calculate("impot_revenu", Y).sum()
    with_kids = build_household([income, 0], kids).calculate("impot_revenu", Y).sum()
    assert with_kids <= base + 0.01


@SETTINGS
@given(income=st.integers(min_value=0, max_value=20_000), kids=children)
def test_allocations_familiales_eligibility(income, kids):
    # AF is paid only from the 2nd child; never negative.
    af = (
        build_household([income, 0], kids)
        .calculate_add("allocations_familiales", Y)
        .sum()
    )
    assert af >= -0.01
    if len(kids) < 2:
        assert af <= 0.01


@SETTINGS
@given(income=incomes, kids=children)
def test_outputs_finite(income, kids):
    sim = build_household([income, 0], kids)
    for var in ["impot_revenu", "csg", "crds", "revenu_disponible"]:
        val = float(sim.calculate(var, Y).sum())
        assert math.isfinite(val)
    af = float(sim.calculate_add("allocations_familiales", Y).sum())
    assert math.isfinite(af)
