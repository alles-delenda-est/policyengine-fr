"""Interactive Studio API & static UI server for `policyengine-fr`.

Exposes a zero-extra-dependency HTTP server (`ThreadingHTTPServer`) with:
- ``GET /api/metadata`` — live variable documentation/references, `modelled_policies.yaml`,
  and pinned `LVTShift` provenance + equal-yield scenario rates.
- ``POST /api/simulate`` — single-household baseline vs. counterfactual reform breakdown
  PLUS a vectorised 61-point earnings sweep (`salaire_brut` -> `revenu_disponible`,
  benefits, taxes, and effective marginal rate EMTR) in one numpy pass.
- Static serving of ``ui/dist`` when built (for 1-command ``python -m policyengine_fr.studio``).
"""

from __future__ import annotations

import argparse
import functools
import json
import mimetypes
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import numpy as np
import yaml
from policyengine_core.reforms import Reform
from policyengine_core.simulations import SimulationBuilder

from policyengine_fr import CountryTaxBenefitSystem
from policyengine_fr.reforms import (
    load_lvt_yields,
    make_csg_delta_reform,
    make_d_p6_targeted_pension_underindexation_reform,
    make_ir_freeze_brackets_reform,
    make_ir_proportional_reform,
    make_lvt_shift_reform,
)

PACKAGE_DIR = Path(__file__).resolve().parent
REPO_ROOT = PACKAGE_DIR.parent
UI_DIST_DIR = REPO_ROOT / "ui" / "dist"
POLICIES_YAML_PATH = PACKAGE_DIR / "modelled_policies.yaml"

BASE_SYSTEM = CountryTaxBenefitSystem()

INDIVIDU_VARS = (
    "salaire_brut",
    "cotisations_salariales",
    "csg",
    "csg_deductible",
    "crds",
    "salaire_declare",
    "salaire_imposable",
    "salaire_net",
    "cotisations_patronales",
    "reduction_generale",
    "cout_du_travail",
    "pension_retraite",
    "pension_retraite_declaree",
    "csg_retraite",
    "crds_retraite",
    "casa_retraite",
    "pension_retraite_nette",
)

FOYER_VARS = (
    "nombre_parts",
    "pensions_imposables",
    "revenus_fonciers_nets",
    "revenu_net_imposable",
    "revenu_fiscal_de_reference",
    "impot_brut",
    "plafonnement_quotient_familial",
    "decote",
    "impot_revenu",
    "taux_csg_pension",
    "cehr",
    "pfu_ir",
    "impot_plus_values_immobilieres",
    "prelevements_sociaux_patrimoine",
    "ifi",
)

FAMILLE_MONTH_SUM_VARS = (
    "allocations_familiales",
    "allocation_soutien_familial",
    "rsa",
    "prime_activite",
)

MENAGE_VARS = (
    "taxe_fonciere",
    "taxe_habitation_residence_secondaire",
    "taxe_valeur_sol",
    "revenu_disponible",
)


def _clamp_float(
    val: Any, default: float = 0.0, lo: float = 0.0, hi: float = 1e9
) -> float:
    try:
        x = float(val)
    except (TypeError, ValueError):
        return default
    if not np.isfinite(x):
        return default
    return float(min(max(x, lo), hi))


def _clamp_int(val: Any, default: int = 35, lo: int = 0, hi: int = 115) -> int:
    try:
        x = int(round(float(val)))
    except (TypeError, ValueError):
        return default
    return max(lo, min(hi, x))


def normalize_reforms(raw: dict[str, Any] | None) -> tuple[Any, ...]:
    """Canonical hashable reform tuple; returns all-neutral tuple when inactive."""
    r = raw or {}
    lvt_scenario = str(r.get("lvt_scenario") or "OFF").upper()
    if lvt_scenario not in {"OFF", "S1", "S2", "S2_IFI", "S3", "S3_IFI"}:
        lvt_scenario = "OFF"
    custom_raw = r.get("lvt_custom_rate")
    lvt_custom = (
        None
        if custom_raw in (None, "", False)
        else round(_clamp_float(custom_raw, 0.0, 0.0, 0.10), 6)
    )
    ir_pct = round(_clamp_float(r.get("ir_rate_change_pct"), 0.0, -50.0, 50.0), 2)
    ir_freeze = bool(r.get("ir_freeze_2024", False))
    csg_delta_pts = round(_clamp_float(r.get("csg_delta_pts"), 0.0, -5.0, 5.0), 2)
    dp6_pct = round(_clamp_float(r.get("dp6_underindex_pct"), 0.0, 0.0, 20.0), 2)
    dp6_thresh = round(
        _clamp_float(r.get("dp6_threshold_annual"), 24_000.0, 0.0, 200_000.0), 0
    )
    return (
        lvt_scenario,
        lvt_custom,
        ir_pct,
        ir_freeze,
        csg_delta_pts,
        dp6_pct,
        dp6_thresh,
    )


def is_reform_active(norm: tuple[Any, ...]) -> bool:
    lvt_sc, _, ir_pct, ir_freeze, csg_pts, dp6_pct, _ = norm
    return (
        lvt_sc != "OFF"
        or abs(ir_pct) > 1e-6
        or ir_freeze
        or abs(csg_pts) > 1e-6
        or dp6_pct > 1e-6
    )


@functools.lru_cache(maxsize=64)
def get_reformed_system(norm: tuple[Any, ...]) -> CountryTaxBenefitSystem:
    """Build and cache a composite `CountryTaxBenefitSystem` for the given reform tuple."""
    if not is_reform_active(norm):
        return BASE_SYSTEM

    lvt_sc, lvt_custom, ir_pct, ir_freeze, csg_pts, dp6_pct, dp6_thresh = norm
    sub_reforms: list[type[Reform]] = []
    if ir_freeze:
        sub_reforms.append(make_ir_freeze_brackets_reform())
    if abs(ir_pct) > 1e-6:
        sub_reforms.append(make_ir_proportional_reform(1.0 + ir_pct / 100.0))
    if abs(csg_pts) > 1e-6:
        sub_reforms.append(make_csg_delta_reform(csg_pts / 100.0))
    if dp6_pct > 1e-6:
        sub_reforms.append(
            make_d_p6_targeted_pension_underindexation_reform(
                dp6_pct / 100.0, threshold_annual=dp6_thresh
            )
        )
    if lvt_sc != "OFF":
        sub_reforms.append(make_lvt_shift_reform(lvt_sc, custom_rate=lvt_custom))

    class StudioCombinedReform(Reform):
        name = "Studio combined reform"

        def apply(self):
            for cls in sub_reforms:
                cls.apply(self)

    return StudioCombinedReform(BASE_SYSTEM)


def build_situation(household: dict[str, Any], year: str) -> dict[str, Any]:
    """Translate clean UI household JSON into a PolicyEngine entity situation."""
    is_couple = bool(household.get("couple", False))
    adults_in = household.get("adults") or [{}]
    a1 = adults_in[0] if len(adults_in) >= 1 else {}
    a2 = adults_in[1] if (is_couple and len(adults_in) >= 2) else None

    children_in = household.get("children") or []
    pat = household.get("patrimoine") or {}

    cap_total = _clamp_float(pat.get("revenus_capital"), 0.0)
    alim_percues = _clamp_float(pat.get("pensions_alimentaires_percues"), 0.0)

    individus: dict[str, Any] = {
        "adulte_1": {
            "age": {year: _clamp_int(a1.get("age"), 35, 18, 110)},
            "salaire_brut": {year: _clamp_float(a1.get("salaire_brut"), 0.0)},
            "cadre": {year: bool(a1.get("cadre", False))},
            "effectif_entreprise": {
                year: _clamp_int(a1.get("effectif_entreprise"), 10, 1, 100_000)
            },
            "pension_retraite": {year: _clamp_float(a1.get("pension_retraite"), 0.0)},
            "revenus_capital": {year: cap_total},
            "pensions_alimentaires_percues": {year: alim_percues},
        }
    }

    declarants = ["adulte_1"]
    parents = ["adulte_1"]
    conjoints: list[str] = []

    if a2 is not None:
        individus["adulte_2"] = {
            "age": {year: _clamp_int(a2.get("age"), 35, 18, 110)},
            "salaire_brut": {year: _clamp_float(a2.get("salaire_brut"), 0.0)},
            "cadre": {year: bool(a2.get("cadre", False))},
            "effectif_entreprise": {
                year: _clamp_int(a2.get("effectif_entreprise"), 10, 1, 100_000)
            },
            "pension_retraite": {year: _clamp_float(a2.get("pension_retraite"), 0.0)},
            "revenus_capital": {year: 0.0},
            "pensions_alimentaires_percues": {year: 0.0},
        }
        declarants.append("adulte_2")
        parents.append("adulte_2")
        conjoints.append("adulte_2")

    enfant_ids: list[str] = []
    for idx, ch in enumerate(children_in[:8]):
        cid = f"enfant_{idx + 1}"
        c_age = _clamp_int(ch.get("age") if isinstance(ch, dict) else ch, 8, 0, 24)
        individus[cid] = {"age": {year: c_age}}
        enfant_ids.append(cid)

    parent_isole = bool(
        (not is_couple) and len(enfant_ids) >= 1 and household.get("parent_isole", True)
    )

    foyers_fiscaux = {
        "foyer_1": {
            "declarants": declarants,
            "personnes_a_charge": enfant_ids,
            "parent_isole": {year: parent_isole},
            "pensions_alimentaires_versees": {
                year: _clamp_float(pat.get("pensions_alimentaires_versees"), 0.0)
            },
            "revenus_fonciers_bruts": {
                year: _clamp_float(pat.get("revenus_fonciers_bruts"), 0.0)
            },
            "charges_foncieres_reelles": {
                year: _clamp_float(pat.get("charges_foncieres_reelles"), 0.0)
            },
            "regime_micro_foncier": {year: bool(pat.get("regime_micro_foncier", True))},
            "plus_values_immobilieres": {
                year: _clamp_float(pat.get("plus_values_immobilieres"), 0.0)
            },
            "patrimoine_immobilier_residence_principale": {
                year: _clamp_float(
                    pat.get("patrimoine_immobilier_residence_principale"), 0.0
                )
            },
            "patrimoine_immobilier_autre": {
                year: _clamp_float(pat.get("patrimoine_immobilier_autre"), 0.0)
            },
        }
    }

    familles = {
        "famille_1": {
            "parents": parents,
            "enfants": enfant_ids,
        }
    }

    menages = {
        "menage_1": {
            "personnes_de_reference": ["adulte_1"],
            "conjoints": conjoints,
            "enfants": enfant_ids,
            "taxe_fonciere_locale": {
                year: _clamp_float(pat.get("taxe_fonciere_locale"), 0.0)
            },
            "thrs_locale": {year: _clamp_float(pat.get("thrs_locale"), 0.0)},
            "valeur_terrain_imposable": {
                year: _clamp_float(pat.get("valeur_terrain_imposable"), 0.0)
            },
        }
    }

    return {
        "individus": individus,
        "foyers_fiscaux": foyers_fiscaux,
        "familles": familles,
        "menages": menages,
    }


def _extract_metrics(
    system: CountryTaxBenefitSystem, situation: dict[str, Any], year: str
) -> dict[str, Any]:
    sim = SimulationBuilder().build_from_entities(system, situation)
    n_adults = 2 if "adulte_2" in situation["individus"] else 1

    ind_totals: dict[str, float] = {}
    adults_detail: list[dict[str, float]] = [{} for _ in range(n_adults)]
    for v in INDIVIDU_VARS:
        arr = np.asarray(sim.calculate(v, year), dtype=float)
        ind_totals[v] = round(float(arr.sum()), 2)
        for idx in range(n_adults):
            adults_detail[idx][v] = round(float(arr[idx]), 2)

    # If D-P6 targeted pension under-indexation is active, expose effective gross pension too
    if "pension_retraite_effective" in system.variables:
        arr_eff = np.asarray(
            sim.calculate("pension_retraite_effective", year), dtype=float
        )
        ind_totals["pension_retraite_effective"] = round(float(arr_eff.sum()), 2)
    else:
        ind_totals["pension_retraite_effective"] = ind_totals["pension_retraite"]

    foyer_vals: dict[str, float] = {}
    for v in FOYER_VARS:
        foyer_vals[v] = round(
            float(np.asarray(sim.calculate(v, year)).sum()),
            4 if v == "taux_csg_pension" else 2,
        )

    fam_vals: dict[str, float] = {}
    for v in FAMILLE_MONTH_SUM_VARS:
        fam_vals[v] = round(float(np.asarray(sim.calculate_add(v, year)).sum()), 2)

    men_vals: dict[str, float] = {}
    for v in MENAGE_VARS:
        men_vals[v] = round(float(np.asarray(sim.calculate(v, year)).sum()), 2)

    pat = situation["foyers_fiscaux"]["foyer_1"]
    loyers_eco = max(
        float(pat["revenus_fonciers_bruts"][year])
        - float(pat["charges_foncieres_reelles"][year]),
        0.0,
    )
    revenus_capital = float(situation["individus"]["adulte_1"]["revenus_capital"][year])
    plus_values = float(pat["plus_values_immobilieres"][year])
    pensions_alim_percues = float(
        situation["individus"]["adulte_1"]["pensions_alimentaires_percues"][year]
    )
    pensions_alim_versees = float(pat["pensions_alimentaires_versees"][year])

    prestations_totales = round(
        fam_vals["allocations_familiales"]
        + fam_vals["allocation_soutien_familial"]
        + fam_vals["rsa"]
        + fam_vals["prime_activite"],
        2,
    )
    cotisations_et_ps_activite = round(
        ind_totals["cotisations_salariales"] + ind_totals["csg"] + ind_totals["crds"],
        2,
    )
    ps_retraite = round(
        ind_totals["csg_retraite"]
        + ind_totals["crds_retraite"]
        + ind_totals["casa_retraite"],
        2,
    )
    impots_directs_et_locaux = round(
        foyer_vals["impot_revenu"]
        + foyer_vals["cehr"]
        + foyer_vals["pfu_ir"]
        + foyer_vals["impot_plus_values_immobilieres"]
        + foyer_vals["prelevements_sociaux_patrimoine"]
        + foyer_vals["ifi"]
        + men_vals["taxe_fonciere"]
        + men_vals["taxe_habitation_residence_secondaire"]
        + men_vals["taxe_valeur_sol"],
        2,
    )
    prelevements_totaux = round(
        cotisations_et_ps_activite + ps_retraite + impots_directs_et_locaux, 2
    )
    cotisations_patronales_nettes = round(
        max(
            ind_totals["cotisations_patronales"] - ind_totals["reduction_generale"], 0.0
        ),
        2,
    )
    cout_employeur_net = round(
        ind_totals["salaire_brut"] + cotisations_patronales_nettes, 2
    )

    revenu_primaire_brut = round(
        ind_totals["salaire_brut"]
        + ind_totals["pension_retraite_effective"]
        + pensions_alim_percues
        + revenus_capital
        + loyers_eco
        + plus_values,
        2,
    )
    taux_prelevement_effectif = (
        round(100.0 * prelevements_totaux / revenu_primaire_brut, 2)
        if revenu_primaire_brut > 0
        else 0.0
    )

    return {
        **ind_totals,
        **foyer_vals,
        **fam_vals,
        **men_vals,
        "adults": adults_detail,
        "revenus_capital": round(revenus_capital, 2),
        "loyers_economiques": round(loyers_eco, 2),
        "plus_values_immobilieres": round(plus_values, 2),
        "pensions_alimentaires_percues": round(pensions_alim_percues, 2),
        "pensions_alimentaires_versees": round(pensions_alim_versees, 2),
        "revenu_primaire_brut": revenu_primaire_brut,
        "prestations_totales": prestations_totales,
        "cotisations_et_ps_activite": cotisations_et_ps_activite,
        "ps_retraite": ps_retraite,
        "impots_directs_et_locaux": impots_directs_et_locaux,
        "prelevements_totaux": prelevements_totaux,
        "cotisations_patronales_nettes": cotisations_patronales_nettes,
        "cout_employeur_net": cout_employeur_net,
        "taux_prelevement_effectif": taux_prelevement_effectif,
    }


def simulate_earnings_curve(
    household: dict[str, Any],
    year: str,
    ref_system: CountryTaxBenefitSystem | None = None,
    n_points: int = 61,
) -> dict[str, Any]:
    """Vectorised N-point sweep over Adult 1's gross salary in a single Simulation."""
    adults_in = household.get("adults") or [{}]
    a1_brut = _clamp_float((adults_in[0] if adults_in else {}).get("salaire_brut"), 0.0)
    max_x = float(
        max(90_000, int(np.ceil((a1_brut * 1.4 + 10_000) / 10_000.0) * 10_000))
    )
    grid = np.linspace(0.0, max_x, n_points)

    base_sit = build_situation(household, year)
    individus: dict[str, Any] = {}
    foyers_fiscaux: dict[str, Any] = {}
    familles: dict[str, Any] = {}
    menages: dict[str, Any] = {}

    base_foyer = base_sit["foyers_fiscaux"]["foyer_1"]
    base_menage = base_sit["menages"]["menage_1"]
    has_a2 = "adulte_2" in base_sit["individus"]
    child_keys = [k for k in base_sit["individus"] if k.startswith("enfant_")]

    for i, x in enumerate(grid):
        a1_id = f"a1_{i}"
        src_a1 = base_sit["individus"]["adulte_1"]
        individus[a1_id] = {
            **src_a1,
            "salaire_brut": {year: float(x)},
        }
        decls = [a1_id]
        pars = [a1_id]
        conjs: list[str] = []
        if has_a2:
            a2_id = f"a2_{i}"
            individus[a2_id] = dict(base_sit["individus"]["adulte_2"])
            decls.append(a2_id)
            pars.append(a2_id)
            conjs.append(a2_id)

        c_ids: list[str] = []
        for ck in child_keys:
            cid = f"{ck}_{i}"
            individus[cid] = dict(base_sit["individus"][ck])
            c_ids.append(cid)

        foyers_fiscaux[f"ff_{i}"] = {
            **base_foyer,
            "declarants": decls,
            "personnes_a_charge": c_ids,
        }
        familles[f"fam_{i}"] = {"parents": pars, "enfants": c_ids}
        menages[f"m_{i}"] = {
            **base_menage,
            "personnes_de_reference": [a1_id],
            "conjoints": conjs,
            "enfants": c_ids,
        }

    vec_sit = {
        "individus": individus,
        "foyers_fiscaux": foyers_fiscaux,
        "familles": familles,
        "menages": menages,
    }

    sim_b = SimulationBuilder().build_from_entities(BASE_SYSTEM, vec_sit)
    rd_b = np.asarray(sim_b.calculate("revenu_disponible", year), dtype=float)
    rsa_b = np.asarray(sim_b.calculate_add("rsa", year), dtype=float)
    ppa_b = np.asarray(sim_b.calculate_add("prime_activite", year), dtype=float)
    af_b = np.asarray(
        sim_b.calculate_add("allocations_familiales", year), dtype=float
    ) + np.asarray(
        sim_b.calculate_add("allocation_soutien_familial", year), dtype=float
    )
    ir_b = np.asarray(sim_b.calculate("impot_revenu", year), dtype=float)

    # Adult 1 net wage at each grid point (every household step adds 1 + int(has_a2) + len(child_keys) individuals)
    stride = 1 + (1 if has_a2 else 0) + len(child_keys)
    snet_all = np.asarray(sim_b.calculate("salaire_net", year), dtype=float)
    snet_a1 = snet_all[0::stride]
    snet_a2 = snet_all[1::stride] if has_a2 else np.zeros_like(snet_a1)
    snet_b = snet_a1 + snet_a2

    dx = np.diff(grid)
    drd_b = np.diff(rd_b)
    emtr_raw = 100.0 * (1.0 - drd_b / np.maximum(dx, 1.0))
    emtr_b = np.concatenate([emtr_raw, emtr_raw[-1:]])
    emtr_b = np.clip(emtr_b, -50.0, 120.0)

    rd_r: np.ndarray | None = None
    emtr_r: np.ndarray | None = None
    if ref_system is not None and ref_system is not BASE_SYSTEM:
        sim_r = SimulationBuilder().build_from_entities(ref_system, vec_sit)
        rd_r = np.asarray(sim_r.calculate("revenu_disponible", year), dtype=float)
        drd_r = np.diff(rd_r)
        emtr_r_raw = 100.0 * (1.0 - drd_r / np.maximum(dx, 1.0))
        emtr_r = np.clip(np.concatenate([emtr_r_raw, emtr_r_raw[-1:]]), -50.0, 120.0)

    points = []
    for i in range(n_points):
        pt: dict[str, float] = {
            "salaire_brut": round(float(grid[i]), 0),
            "salaire_net": round(float(snet_b[i]), 2),
            "rsa": round(float(rsa_b[i]), 2),
            "prime_activite": round(float(ppa_b[i]), 2),
            "af_asf": round(float(af_b[i]), 2),
            "impot_revenu": round(float(ir_b[i]), 2),
            "revenu_disponible": round(float(rd_b[i]), 2),
            "emtr_pct": round(float(emtr_b[i]), 1),
        }
        if rd_r is not None and emtr_r is not None:
            pt["revenu_disponible_reforme"] = round(float(rd_r[i]), 2)
            pt["emtr_reforme_pct"] = round(float(emtr_r[i]), 1)
        points.append(pt)

    return {
        "current_salaire_brut": round(a1_brut, 2),
        "max_salaire_brut": max_x,
        "points": points,
    }


def simulate_household(payload: dict[str, Any]) -> dict[str, Any]:
    """Top-level simulation entrypoint used by `/api/simulate` and unit tests."""
    year = str(payload.get("year") or "2024")
    if year not in {"2024", "2025"}:
        year = "2024"
    household = payload.get("household") or {}
    norm_ref = normalize_reforms(payload.get("reforms"))
    reform_active = is_reform_active(norm_ref)

    situation = build_situation(household, year)
    baseline = _extract_metrics(BASE_SYSTEM, situation, year)

    ref_system = get_reformed_system(norm_ref) if reform_active else None
    reform_metrics: dict[str, Any] | None = None
    deltas: dict[str, float] | None = None
    dp6_clawback_share: float | None = None

    if reform_active and ref_system is not None:
        reform_metrics = _extract_metrics(ref_system, situation, year)
        # Note: in D-P6, `revenu_disponible` automatically reflects `pension_retraite_nette`!
        deltas = {}
        for k, v in baseline.items():
            if isinstance(v, (int, float)) and k in reform_metrics:
                deltas[k] = round(float(reform_metrics[k]) - float(v), 2)

        gross_pen_cut = (
            baseline["pension_retraite"] - reform_metrics["pension_retraite_effective"]
        )
        if gross_pen_cut > 1.0:
            net_loss = (
                baseline["revenu_disponible"] - reform_metrics["revenu_disponible"]
            )
            dp6_clawback_share = round(1.0 - (net_loss / gross_pen_cut), 4)

    include_curve = bool(payload.get("include_curve", True))
    curve = (
        simulate_earnings_curve(household, year, ref_system=ref_system)
        if include_curve
        else None
    )

    return {
        "year": year,
        "reform_active": reform_active,
        "baseline": baseline,
        "reform": reform_metrics,
        "deltas": deltas,
        "dp6_clawback_share": dp6_clawback_share,
        "curve": curve,
    }


@functools.lru_cache(maxsize=1)
def get_metadata() -> dict[str, Any]:
    """Return package coverage, variable dictionary, and LVTShift provenance."""
    policies = yaml.safe_load(POLICIES_YAML_PATH.read_text(encoding="utf-8"))
    yields_data, lvt_source = load_lvt_yields()

    tracked_vars = (
        list(INDIVIDU_VARS)
        + list(FOYER_VARS)
        + list(FAMILLE_MONTH_SUM_VARS)
        + list(MENAGE_VARS)
    )
    variables_meta: dict[str, dict[str, str]] = {}
    for name in tracked_vars:
        var = BASE_SYSTEM.variables.get(name)
        if var is None:
            continue
        ref = getattr(var, "reference", None)
        if isinstance(ref, (list, tuple)):
            ref_str = str(ref[0]) if ref else ""
        else:
            ref_str = str(ref or "")
        variables_meta[name] = {
            "label": str(getattr(var, "label", name) or name),
            "documentation": str(getattr(var, "documentation", "") or ""),
            "reference": ref_str,
            "entity": str(getattr(getattr(var, "entity", None), "key", "")),
            "unit": str(getattr(var, "unit", "") or ""),
        }

    return {
        "years": ["2024", "2025"],
        "policies": policies.get("core", {}),
        "variables": variables_meta,
        "lvt": {
            "source": lvt_source,
            "land_base": yields_data.get("land_base", {}),
            "variants": yields_data.get("variants", []),
        },
    }


class StudioRequestHandler(BaseHTTPRequestHandler):
    """HTTP handler serving `/api/*` and static Vite assets from `ui/dist`."""

    def log_message(self, fmt: str, *args: Any) -> None:
        return  # Keep console clean during rapid 60fps slider requests

    def _send_json(self, data: Any, status: int = HTTPStatus.OK) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()

    def do_GET(self) -> None:
        path = self.path.split("?", 1)[0]
        if path == "/api/health":
            self._send_json({"status": "ok"})
            return
        if path == "/api/metadata":
            self._send_json(get_metadata())
            return

        if UI_DIST_DIR.is_dir():
            rel = path.lstrip("/") or "index.html"
            candidate = (UI_DIST_DIR / rel).resolve()
            if (
                str(candidate).startswith(str(UI_DIST_DIR.resolve()))
                and candidate.is_file()
            ):
                target = candidate
            else:
                target = UI_DIST_DIR / "index.html"
            if target.is_file():
                raw = target.read_bytes()
                mime, _ = mimetypes.guess_type(str(target))
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", mime or "application/octet-stream")
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)
                return

        self._send_json(
            {
                "message": "PolicyEngine France Studio API active.",
                "endpoints": ["/api/health", "/api/metadata", "/api/simulate"],
            }
        )

    def do_POST(self) -> None:
        path = self.path.split("?", 1)[0]
        if path != "/api/simulate":
            self._send_json({"error": "Not found"}, status=HTTPStatus.NOT_FOUND)
            return
        try:
            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length) if length > 0 else b"{}"
            payload = json.loads(raw.decode("utf-8"))
            result = simulate_household(payload)
            self._send_json(result)
        except Exception as exc:
            self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)


def create_server(host: str = "127.0.0.1", port: int = 8765) -> ThreadingHTTPServer:
    return ThreadingHTTPServer((host, port), StudioRequestHandler)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Launch the PolicyEngine France Interactive Studio server."
    )
    parser.add_argument(
        "--host", default="127.0.0.1", help="Bind host (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--port", type=int, default=8765, help="Bind port (default: 8765)"
    )
    parser.add_argument(
        "--open", action="store_true", help="Open the Studio URL in the default browser"
    )
    args = parser.parse_args(argv)

    server = create_server(args.host, args.port)
    url = f"http://{args.host}:{args.port}"
    print(f"PolicyEngine France Studio listening on {url}")
    if args.open:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
