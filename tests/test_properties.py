"""Property-based / metamorphic tests across all modelled blocks and seams."""

from __future__ import annotations

import math

import pytest
from hypothesis import given, settings, strategies as st

from helpers import YEAR, build_household

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
    low = build_household([income], []).calculate("impot_revenu", Y).sum()
    high = build_household([income + delta], []).calculate("impot_revenu", Y).sum()
    assert high >= low - 0.01


@SETTINGS
@given(income=incomes, delta=positive_delta)
def test_impot_revenu_marginal_below_one(income, delta):
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
def test_payslip_identities(income):
    """Spec 0001 + 0004 seam check: gross -> cotisations -> declared -> net."""
    sim = build_household([income], [])
    cotis = float(sim.calculate("cotisations_salariales", Y).sum())
    csg_ded = float(sim.calculate("csg_deductible", Y).sum())
    csg = float(sim.calculate("csg", Y).sum())
    crds = float(sim.calculate("crds", Y).sum())
    declare = float(sim.calculate("salaire_declare", Y).sum())
    net = float(sim.calculate("salaire_net", Y).sum())
    assert 0 <= cotis <= income + 0.01
    assert math.isclose(declare, income - cotis - csg_ded, abs_tol=0.05)
    assert math.isclose(net, income - cotis - csg - crds, abs_tol=0.05)


@SETTINGS
@given(income=incomes, kids=children)
def test_quotient_familial_only_reduces_tax(income, kids):
    base = build_household([income, 0], []).calculate("impot_revenu", Y).sum()
    with_kids = build_household([income, 0], kids).calculate("impot_revenu", Y).sum()
    assert with_kids <= base + 0.01


@SETTINGS
@given(income=st.integers(min_value=0, max_value=20_000), kids=children)
def test_allocations_familiales_eligibility(income, kids):
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
    for var in [
        "impot_revenu",
        "cotisations_salariales",
        "salaire_declare",
        "salaire_net",
        "csg",
        "crds",
        "cout_du_travail",
        "revenu_disponible",
    ]:
        val = float(sim.calculate(var, Y).sum())
        assert math.isfinite(val)
    for mvar in ["allocations_familiales", "rsa", "prime_activite"]:
        mval = float(sim.calculate_add(mvar, Y).sum())
        assert math.isfinite(mval)


# ---------------------------------------------------------------------------
# Deterministic-grid invariants
# ---------------------------------------------------------------------------

_INCOME_GRID = [0, 20_000, 80_000, 120_000, 200_000]
_CHILD_COUNTS = [0, 1, 2, 3, 4]
_AF_PERIOD = "2024-01"
_CSG_PERIOD = "2024"


def test_af_non_negative():
    for n_children in _CHILD_COUNTS:
        child_ages = [8] * n_children
        for income in _INCOME_GRID:
            sim = build_household([income, 0], child_ages)
            af = float(sim.calculate("allocations_familiales", _AF_PERIOD).sum())
            assert af >= -0.01


def test_af_zero_below_two_children():
    for n_children in [0, 1]:
        child_ages = [8] * n_children
        for income in _INCOME_GRID:
            sim = build_household([income, 0], child_ages)
            af = float(sim.calculate("allocations_familiales", _AF_PERIOD).sum())
            assert af <= 0.01


def test_af_monotonic_and_cliff_free_across_plafonds():
    """Verify both monotonicity AND absence of cliffs across plafond 1 (CSS D521-1)."""
    child_ages = [8, 10]
    prev_af = None
    # Sweep fine €200 gross steps across the plafond 1 crossing (~103k-106k gross)
    for income in range(101_000, 108_000, 200):
        af = float(
            build_household([income, 0], child_ages)
            .calculate("allocations_familiales", _AF_PERIOD)
            .sum()
        )
        if prev_af is not None:
            assert af <= prev_af + 0.01
            # €200 gross -> < €180 RNI -> monthly AF drop must be <= 180/12 = €15 (no €71 cliff!)
            assert (prev_af - af) <= 16.0, (
                f"Cliff detected at gross={income}: monthly AF dropped from {prev_af:.2f} to {af:.2f}"
            )
        prev_af = af


def test_csg_identity():
    for income in _INCOME_GRID:
        sim = build_household([income], [])
        csg = float(sim.calculate("csg", _CSG_PERIOD).sum())
        csg_ded = float(sim.calculate("csg_deductible", _CSG_PERIOD).sum())
        csg_imp = float(sim.calculate("csg_imposable", _CSG_PERIOD).sum())
        assert math.isclose(csg, csg_ded + csg_imp, abs_tol=0.02)


def test_assiette_identity():
    for income in _INCOME_GRID:
        sim = build_household([income], [])
        assiette = float(sim.calculate("assiette_csg_crds_salaire", _CSG_PERIOD).sum())
        assert math.isclose(assiette, income * 0.9825, abs_tol=0.02)


def test_asf_and_rsa_in_revenu_disponible_single_parent():
    # Single parent (age 40), 1 child (age 8), 0 income: receives ASF (2336.09) + RSA (9861.37).
    sim = build_household([0], [8], parent_isole=True, adult_age=40)
    rd = float(sim.calculate("revenu_disponible", "2024").sum())
    assert abs(rd - (2336.09 + 9861.37)) < 0.5


@pytest.mark.parametrize("child_ages", [[], [8], [4, 9], [1, 7, 12]])
def test_asf_non_negative(child_ages):
    sim = build_household([20000], child_ages)
    asf = sim.calculate("allocation_soutien_familial", "2024-04")
    assert (asf >= 0).all()


def test_asf_zero_for_couple():
    sim = build_household([20000, 15000], [4, 9])
    assert float(sim.calculate("allocation_soutien_familial", "2024-04").sum()) == 0


def test_asf_scales_with_eligible_children():
    one = float(
        build_household([0], [8])
        .calculate("allocation_soutien_familial", "2024-04")
        .sum()
    )
    two = float(
        build_household([0], [4, 9])
        .calculate("allocation_soutien_familial", "2024-04")
        .sum()
    )
    assert one > 0 and abs(two - 2 * one) < 0.01


def test_asf_floor_guarantee():
    asf_pleine = 196.83768
    for annual_pension in [0, 600, 1_200, 2_400, 3_600]:
        asf = float(
            build_household([0], [8], adult_pensions=[annual_pension])
            .calculate("allocation_soutien_familial", "2024-04")
            .sum()
        )
        topup = min(annual_pension / 12, asf_pleine)
        assert abs(asf + topup - asf_pleine) < 0.02


# ---------------------------------------------------------------------------
# RSA & Prime d'activité invariants
# ---------------------------------------------------------------------------

_RSA_PERIOD = "2024-01"


def test_rsa_invariants():
    # Non-negative & non-increasing in income
    prev = None
    for income in [0, 3_000, 6_000, 9_000, 12_000]:
        val = float(
            build_household([income], [], adult_age=40)
            .calculate("rsa", _RSA_PERIOD)
            .sum()
        )
        assert val >= 0
        assert val == 0 or val >= 6.0 - 0.01
        if prev is not None:
            assert val <= prev + 0.01
        prev = val

    # Under-25 without child -> 0; under-25 WITH child -> eligible (> 0)
    assert (
        float(
            build_household([0], [], adult_age=22).calculate("rsa", _RSA_PERIOD).sum()
        )
        == 0
    )
    assert (
        float(
            build_household([0], [2], parent_isole=True, adult_age=22)
            .calculate("rsa", _RSA_PERIOD)
            .sum()
        )
        > 700
    )


def test_prime_activite_invariants():
    # Zero at 0 activity income; positive at SMIC; never in (0, 15); eligible at age 19
    assert (
        float(
            build_household([0], [], adult_age=30)
            .calculate("prime_activite", _RSA_PERIOD)
            .sum()
        )
        == 0
    )
    for income in range(0, 36_000, 1_500):
        ppa = float(
            build_household([income], [], adult_age=30)
            .calculate("prime_activite", _RSA_PERIOD)
            .sum()
        )
        assert ppa == 0 or ppa >= 15.0 - 0.01
    ppa_19 = float(
        build_household([21_203], [], adult_age=19)
        .calculate("prime_activite", _RSA_PERIOD)
        .sum()
    )
    assert ppa_19 > 140


def test_shared_pension_abattement_not_double_counted():
    """Spec 0005 regression guard: 10 % pension ceiling (€4,399 in 2024) applies once."""
    sim = build_household([0], [], adult_pensions=[50_000], adult_retraites=[50_000])
    # Declared retirement (net of 5.9% CSG ded = 47,050) + 50,000 alimony = 97,050.
    # Shared ceiling = 4,399 -> taxable pensions must be 97,050 - 4,399 = 92,651 (NOT - 8,798!).
    imposable = float(sim.calculate("pensions_imposables", Y).sum())
    assert abs(imposable - (97_050.0 - 4_399.0)) < 0.05


def test_employer_cout_du_travail_and_fillon_invariants():
    """Spec 0008 invariants: Fillon vanishes >= 1.6 SMIC and super_brut >= brut."""
    for income in [0, 15_000, 21_203, 27_564, 34_000, 60_000, 150_000]:
        sim = build_household([income], [])
        rg = float(sim.calculate("reduction_generale", Y).sum())
        cp = float(sim.calculate("cotisations_patronales", Y).sum())
        ct = float(sim.calculate("cout_du_travail", Y).sum())
        assert rg >= -0.01 and cp >= -0.01
        if income >= 34_000:
            assert rg == 0.0
        assert math.isclose(ct, income + cp - rg, abs_tol=0.05)
        assert ct >= income - 0.01
