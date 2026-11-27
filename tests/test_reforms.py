"""Tests for cross-repo reforms reused from `LVTShift` and `budget_fr_sim_test`."""

from __future__ import annotations

import pytest

from policyengine_fr import CountryTaxBenefitSystem, Simulation
from policyengine_fr.reforms import (
    load_lvt_yields,
    lvt_variant_rate,
    make_csg_delta_reform,
    make_d_p6_targeted_pension_underindexation_reform,
    make_ir_proportional_reform,
    make_lvt_shift_reform,
)


def _owner_situation(
    *,
    salaire_brut: float = 50_000.0,
    tf_locale: float = 2_000.0,
    thrs_locale: float = 500.0,
    terrain: float = 120_000.0,
    loyers_bruts: float = 0.0,
    regime_micro_foncier: bool = True,
    plus_values: float = 0.0,
    patrimoine_autre: float = 0.0,
    revenus_capital: float = 0.0,
) -> dict:
    return {
        "individus": {
            "a1": {
                "age": {"2024": 45},
                "salaire_brut": {"2024": salaire_brut},
                "revenus_capital": {"2024": revenus_capital},
            }
        },
        "foyers_fiscaux": {
            "ff1": {
                "declarants": ["a1"],
                "revenus_fonciers_bruts": {"2024": loyers_bruts},
                "regime_micro_foncier": {"2024": regime_micro_foncier},
                "plus_values_immobilieres": {"2024": plus_values},
                "patrimoine_immobilier_autre": {"2024": patrimoine_autre},
            }
        },
        "familles": {"fam1": {"parents": ["a1"], "enfants": []}},
        "menages": {
            "m1": {
                "personnes_de_reference": ["a1"],
                "taxe_fonciere_locale": {"2024": tf_locale},
                "thrs_locale": {"2024": thrs_locale},
                "valeur_terrain_imposable": {"2024": terrain},
            }
        },
    }


def test_country_tax_benefit_system_accepts_reform_directly():
    tbs = CountryTaxBenefitSystem(reform=make_lvt_shift_reform("S1"))
    assert tbs.variables["taxe_fonciere"].is_neutralized is True


def test_lvt_yields_provenance_and_rates():
    yields_data, source = load_lvt_yields()
    assert source["repo"] == "alles-delenda-est/LVTShift"
    assert len(source["sha256"]) == 64
    assert yields_data["land_base"]["taxable_meur"] == 6_122_450
    assert pytest.approx(lvt_variant_rate("S1"), rel=1e-6) == 0.0110
    assert pytest.approx(lvt_variant_rate("S2"), rel=1e-6) == 0.0116
    assert pytest.approx(lvt_variant_rate("S2_IFI"), rel=1e-6) == 0.0120
    assert pytest.approx(lvt_variant_rate("S3"), rel=1e-6) == 0.0130
    assert pytest.approx(lvt_variant_rate("S3_IFI"), rel=1e-6) == 0.0134


def test_lvt_s1_replaces_tf_and_thrs_with_land_value_tax():
    sit = _owner_situation(tf_locale=2_000, thrs_locale=500, terrain=100_000)
    base = Simulation(situation=sit)
    ref = Simulation(situation=sit, reform=make_lvt_shift_reform("S1"))

    assert float(base.calculate("taxe_fonciere", "2024")[0]) == pytest.approx(2_060.0)
    assert float(
        base.calculate("taxe_habitation_residence_secondaire", "2024")[0]
    ) == pytest.approx(515.0)
    assert float(base.calculate("taxe_valeur_sol", "2024")[0]) == 0.0

    assert float(ref.calculate("taxe_fonciere", "2024")[0]) == 0.0
    assert (
        float(ref.calculate("taxe_habitation_residence_secondaire", "2024")[0]) == 0.0
    )
    # 100 000 × 1,10 % = 1 100 € -> apartment with low land share gains disposable income
    assert float(ref.calculate("taxe_valeur_sol", "2024")[0]) == pytest.approx(1_100.0)
    delta_rd = float(ref.calculate("revenu_disponible", "2024")[0]) - float(
        base.calculate("revenu_disponible", "2024")[0]
    )
    assert delta_rd == pytest.approx(2_060.0 + 515.0 - 1_100.0, abs=0.05)


def test_lvt_s3_ifi_removes_ifi_gains_and_rental_taxes_but_keeps_pfu():
    sit = _owner_situation(
        tf_locale=3_000,
        thrs_locale=0,
        terrain=800_000,
        loyers_bruts=12_000,
        plus_values=30_000,
        patrimoine_autre=2_000_000,
        revenus_capital=10_000,
    )
    base = Simulation(situation=sit)
    ref = Simulation(situation=sit, reform=make_lvt_shift_reform("S3_IFI"))

    assert float(base.calculate("ifi", "2024")[0]) > 0
    assert float(
        base.calculate("impot_plus_values_immobilieres", "2024")[0]
    ) == pytest.approx(5_700.0)
    assert float(ref.calculate("ifi", "2024")[0]) == 0.0
    assert float(ref.calculate("impot_plus_values_immobilieres", "2024")[0]) == 0.0
    # S3_IFI removes net rental income from taxable RNI while keeping financial PFU + PS untouched
    assert float(ref.calculate("revenu_net_imposable", "2024")[0]) < float(
        base.calculate("revenu_net_imposable", "2024")[0]
    )
    assert float(ref.calculate("pfu_ir", "2024")[0]) == pytest.approx(1_280.0)
    assert float(
        ref.calculate("prelevements_sociaux_patrimoine", "2024")[0]
    ) == pytest.approx(1_720.0)
    assert float(ref.calculate("taxe_valeur_sol", "2024")[0]) == pytest.approx(
        800_000 * 0.0134
    )


def test_lvt_s3_does_not_leak_rsa_or_wipe_rfr():
    """S3 exempts rents from IR/PS without falsely making landlords RSA-eligible."""
    sit = _owner_situation(
        salaire_brut=0,
        tf_locale=2_000,
        thrs_locale=0,
        terrain=150_000,
        loyers_bruts=30_000,
        regime_micro_foncier=False,
    )
    base = Simulation(situation=sit)
    ref = Simulation(situation=sit, reform=make_lvt_shift_reform("S3"))

    assert float(base.calculate_add("rsa", "2024")[0]) == 0.0
    assert float(ref.calculate_add("rsa", "2024")[0]) == 0.0
    assert float(ref.calculate("revenu_fiscal_de_reference", "2024")[0]) > 0.0
    assert float(ref.calculate("revenu_net_imposable", "2024")[0]) == 0.0


def test_budget_levers_ir_proportional_and_csg_delta():
    sit = _owner_situation(salaire_brut=80_000, tf_locale=0, thrs_locale=0, terrain=0)
    base = Simulation(situation=sit)
    ir_up = Simulation(situation=sit, reform=make_ir_proportional_reform(1.05))
    csg_up = Simulation(situation=sit, reform=make_csg_delta_reform(0.01))

    # Above the décote zone, scaling all IR bracket rates by 1.05 scales impot_brut by 1.05
    assert float(ir_up.calculate("impot_brut", "2024")[0]) == pytest.approx(
        1.05 * float(base.calculate("impot_brut", "2024")[0]), rel=1e-4
    )
    # +1 pp CSG on 98.25 % of 80 000 € = +786 € CSG
    assert float(csg_up.calculate("csg", "2024")[0]) - float(
        base.calculate("csg", "2024")[0]
    ) == pytest.approx(80_000 * 0.9825 * 0.01, abs=0.1)


def test_d_p6_targeted_pension_underindexation_matches_day1_clawback_band():
    """Verify `budget_fr_sim_test` day1 Decision D-P6:
    1) Pensions <= €24,000/yr (€2,000/mo) are strictly unaffected.
    2) For higher pensions (e.g. €48,000/yr = €4,000/mo, TMI 30 % + CSG 8.3 % /
       CRDS 0.5 % / CASA 0.3 %), the mechanical fiscal offset (clawback of gross
       savings via lower IR + CSG/CRDS/CASA) falls inside D-P6's [0.35, 0.45] band.
    """
    reform = make_d_p6_targeted_pension_underindexation_reform(0.02)

    low_sit = {
        "individus": {
            "a1": {"age": {"2024": 68}, "pension_retraite": {"2024": 20_000}}
        },
        "foyers_fiscaux": {"ff1": {"declarants": ["a1"]}},
        "familles": {"fam1": {"parents": ["a1"], "enfants": []}},
        "menages": {"m1": {"personnes_de_reference": ["a1"]}},
    }
    assert float(
        Simulation(situation=low_sit, reform=reform).calculate(
            "revenu_disponible", "2024"
        )[0]
    ) == pytest.approx(
        float(Simulation(situation=low_sit).calculate("revenu_disponible", "2024")[0]),
        abs=0.01,
    )

    high_sit = {
        "individus": {
            "a1": {"age": {"2024": 68}, "pension_retraite": {"2024": 48_000}}
        },
        "foyers_fiscaux": {"ff1": {"declarants": ["a1"]}},
        "familles": {"fam1": {"parents": ["a1"], "enfants": []}},
        "menages": {"m1": {"personnes_de_reference": ["a1"]}},
    }
    b_sim = Simulation(situation=high_sit)
    r_sim = Simulation(situation=high_sit, reform=reform)
    gross_cut = 48_000 * 0.02  # €960 gross pension cut
    net_loss = float(b_sim.calculate("revenu_disponible", "2024")[0]) - float(
        r_sim.calculate("revenu_disponible", "2024")[0]
    )
    fiscal_clawback_share = 1.0 - (net_loss / gross_cut)
    assert 0.34 <= fiscal_clawback_share <= 0.45, (
        f"Expected mechanical fiscal offset in [0.34, 0.45] per day1 D-P6, got {fiscal_clawback_share:.4f}"
    )


def test_d_p6_updates_rfr_and_csg_tier():
    """Verify D-P6 propagates effective pension into RFR and pension CSG tiers."""
    sit = {
        "individus": {
            "a1": {"age": {"2024": 68}, "pension_retraite": {"2024": 27_700}}
        },
        "foyers_fiscaux": {"ff1": {"declarants": ["a1"]}},
        "familles": {"fam1": {"parents": ["a1"], "enfants": []}},
        "menages": {"m1": {"personnes_de_reference": ["a1"]}},
    }
    b_sim = Simulation(situation=sit)
    r_sim = Simulation(
        situation=sit, reform=make_d_p6_targeted_pension_underindexation_reform(0.05)
    )
    assert float(
        b_sim.calculate("revenu_fiscal_de_reference", "2024")[0]
    ) == pytest.approx(24_930.0)
    assert float(b_sim.calculate("taux_csg_pension", "2024")[0]) == pytest.approx(0.083)
    assert float(
        r_sim.calculate("revenu_fiscal_de_reference", "2024")[0]
    ) == pytest.approx(23_683.50, abs=0.1)
    assert float(r_sim.calculate("taux_csg_pension", "2024")[0]) == pytest.approx(0.066)
