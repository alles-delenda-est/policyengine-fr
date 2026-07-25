"""Property-based / metamorphic tests.

These assert invariants that must hold *regardless of the exact reference
values* — so they catch whole classes of bugs (sign errors, non-monotonicity,
mis-wired benefits) that self-authored unit tests can miss. They do NOT prove
the numbers are correct against the statute — that is the job of the
independent-oracle validation (see docs/cowork-validation-brief.md).
"""

from __future__ import annotations

import math

import pytest
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
@given(income=incomes)
def test_payslip_identity(income):
    # Spec 0001 §5.1: the brut → déclaré → net chain is coherent.
    sim = build_household([income], [])
    brut = sim.calculate("salaire_brut", Y).sum()
    cotisations = sim.calculate("cotisations_salariales", Y).sum()
    csg = sim.calculate("csg", Y).sum()
    crds = sim.calculate("crds", Y).sum()
    csg_deductible = sim.calculate("csg_deductible", Y).sum()
    declare = sim.calculate("salaire_declare", Y).sum()

    # salaire_declare = brut − cotisations − CSG déductible (deduction applied once).
    assert math.isclose(
        declare, max(brut - cotisations - csg_deductible, 0.0), abs_tol=0.5
    )
    # Take-home (net of the modelled wedge) is between 0 and gross, and below
    # the declared salary is never above gross.
    take_home = brut - cotisations - csg - crds
    assert -0.01 <= take_home <= brut + 0.01
    assert declare <= brut + 0.01


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
@given(income=incomes)
def test_rsa_non_negative_and_decreasing_in_income(income):
    # RSA (socle) is a differential top-up: never negative, and never rises
    # with income (single adult, no children — clean base ressources).
    low = build_household([income], []).calculate_add("rsa", Y).sum()
    high = build_household([income + 3_000], []).calculate_add("rsa", Y).sum()
    assert low >= -0.01
    assert high <= low + 0.01


def test_rsa_lifts_low_income_disposable_income():
    # A zero-income single adult receives RSA, so disposable income is positive
    # and equals the annualised RSA (no other income/benefit).
    sim = build_household([0], [])
    rsa = float(sim.calculate_add("rsa", Y).sum())
    rdb = float(sim.calculate("revenu_disponible", Y).sum())
    assert rsa > 0
    assert math.isclose(rdb, rsa, abs_tol=0.5)


@SETTINGS
@given(income=incomes, kids=children)
def test_outputs_finite(income, kids):
    sim = build_household([income, 0], kids)
    for var in ["impot_revenu", "csg", "crds", "revenu_disponible"]:
        val = float(sim.calculate(var, Y).sum())
        assert math.isfinite(val)
    af = float(sim.calculate_add("allocations_familiales", Y).sum())
    assert math.isfinite(af)


# ---------------------------------------------------------------------------
# Deterministic-grid invariants (no Hypothesis — fixed income × child grid)
# ---------------------------------------------------------------------------

_INCOME_GRID = [0, 20_000, 80_000, 120_000, 200_000]
_CHILD_COUNTS = [0, 1, 2, 3, 4]
# Monthly period for AF: avoids upstream policyengine-core storage bug with
# YEAR-level inputs on non-January months.
_AF_PERIOD = "2024-01"
_CSG_PERIOD = "2024"  # annual


def test_af_non_negative():
    """allocations_familiales >= 0 for all (income, n_children) grid points."""
    for n_children in _CHILD_COUNTS:
        child_ages = [8] * n_children
        for income in _INCOME_GRID:
            sim = build_household([income, 0], child_ages)
            af = float(sim.calculate("allocations_familiales", _AF_PERIOD).sum())
            assert af >= -0.01, (
                f"AF negative ({af:.4f}) at income={income}, {n_children} children"
            )


def test_af_zero_below_two_children():
    """allocations_familiales == 0 whenever the family has fewer than 2 children."""
    for n_children in [0, 1]:
        child_ages = [8] * n_children
        for income in _INCOME_GRID:
            sim = build_household([income, 0], child_ages)
            af = float(sim.calculate("allocations_familiales", _AF_PERIOD).sum())
            assert af <= 0.01, (
                f"AF non-zero ({af:.4f}) with only {n_children} child(ren), income={income}"
            )


def test_af_monotonic_non_increasing_in_resources():
    """For couple + 2 children (aged 8 and 10), AF weakly decreases as income rises.

    The income steps span the modulation thresholds:
    taux plein -> demi -> quart -> potentially zero.
    """
    income_steps = [20_000, 80_000, 110_000, 130_000]
    child_ages = [8, 10]
    epsilon = 0.01
    prev_af = None
    for income in income_steps:
        sim = build_household([income, 0], child_ages)
        af = float(sim.calculate("allocations_familiales", _AF_PERIOD).sum())
        if prev_af is not None:
            assert af <= prev_af + epsilon, (
                f"AF not non-increasing: {af:.4f} > {prev_af:.4f} "
                f"when income rose to {income}"
            )
        prev_af = af


def test_csg_identity():
    """csg == csg_deductible + csg_imposable (arithmetic identity) across income grid.

    Tolerance is 0.01 (matching suite-wide absolute_error_margin) rather than
    the theoretical 1e-6 because PolicyEngine uses float32 arrays: computing
    assiette*0.068, assiette*0.024, and assiette*0.092 independently introduces
    independent float32 rounding that exceeds 1e-6 at values in the thousands.
    The identity itself is correct; 0.01 captures any real deviation far above
    float32 noise.
    """
    for income in _INCOME_GRID:
        sim = build_household([income], [])
        csg = float(sim.calculate("csg", _CSG_PERIOD).sum())
        csg_ded = float(sim.calculate("csg_deductible", _CSG_PERIOD).sum())
        csg_imp = float(sim.calculate("csg_imposable", _CSG_PERIOD).sum())
        assert math.isclose(csg, csg_ded + csg_imp, abs_tol=0.01), (
            f"CSG identity broken at income={income}: "
            f"csg={csg:.6f}, ded+imp={csg_ded + csg_imp:.6f}"
        )


def test_asf_in_revenu_disponible_single_parent():
    # Single parent, 1 child, no income: revenu_disponible == annual ASF + RSA.
    # (ASF ≈ 2336.09/yr; the parent also draws RSA majoré, whose base ressources
    # include the ASF — so both flow into revenu_disponible.)
    sim = build_household([0], [8])
    rd = float(sim.calculate("revenu_disponible", "2024").sum())
    asf = float(sim.calculate_add("allocation_soutien_familial", "2024").sum())
    rsa = float(sim.calculate_add("rsa", "2024").sum())
    assert asf > 0 and rsa > 0
    assert math.isclose(rd, asf + rsa, abs_tol=0.5)


def test_assiette_identity():
    """assiette_csg_crds_salaire == salaire_brut * 0.9825 across income grid.

    Tolerance is 0.01 for the same float32 reason as test_csg_identity.
    """
    for income in _INCOME_GRID:
        sim = build_household([income], [])
        assiette = float(sim.calculate("assiette_csg_crds_salaire", _CSG_PERIOD).sum())
        expected = income * 0.9825
        assert math.isclose(assiette, expected, abs_tol=0.01), (
            f"Assiette identity broken at income={income}: "
            f"got {assiette:.6f}, expected {expected:.6f}"
        )


# ---------------------------------------------------------------------------
# ASF property invariants
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("child_ages", [[], [8], [4, 9], [1, 7, 12]])
def test_asf_non_negative(child_ages):
    sim = build_household([20000], child_ages)
    asf = sim.calculate("allocation_soutien_familial", "2024-04")
    assert (asf >= 0).all()


def test_asf_zero_for_couple():
    sim = build_household([20000, 15000], [4, 9])
    asf = float(sim.calculate("allocation_soutien_familial", "2024-04").sum())
    assert asf == 0


def test_asf_scales_with_eligible_children():
    one = float(
        build_household([0], [8])
        .calculate("allocation_soutien_familial", "2024-04")
        .sum()
    )
    assert one > 0, (
        "ASF for 1 eligible child must be positive (guard against vacuous linearity)"
    )
    two = float(
        build_household([0], [4, 9])
        .calculate("allocation_soutien_familial", "2024-04")
        .sum()
    )
    assert abs(two - 2 * one) < 0.01


def test_asf_non_increasing_in_pension():
    # A received pension reduces ASF euro-for-euro until it reaches zero.
    base = float(
        build_household([0], [8])
        .calculate("allocation_soutien_familial", "2024-04")
        .sum()
    )
    with_pension = float(
        build_household([0], [8], adult_pensions=[1_200])
        .calculate("allocation_soutien_familial", "2024-04")
        .sum()
    )
    assert with_pension <= base
    # 196.83768 − (1200/12 = 100) = 96.83768
    assert abs(with_pension - 96.83768) < 0.01


def test_asf_floor_guarantee():
    # For an eligible single parent, ASF tops the pension up to the ASF floor:
    # ASF_versée + min(pension/12, ASF_pleine) == ASF_pleine.
    asf_pleine = 196.83768  # 0.422 × 466.44 (2024-04), 1 child
    for annual_pension in [0, 600, 1_200, 2_400, 3_600]:
        asf = float(
            build_household([0], [8], adult_pensions=[annual_pension])
            .calculate("allocation_soutien_familial", "2024-04")
            .sum()
        )
        topup = min(annual_pension / 12, asf_pleine)
        assert abs(asf + topup - asf_pleine) < 0.02
