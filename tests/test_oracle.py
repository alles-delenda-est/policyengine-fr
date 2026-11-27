"""Compare live model outputs to official DGFiP and openfisca-france oracle values."""

import pathlib

import pytest
import yaml

from policyengine_fr import Simulation

FIXTURE = pathlib.Path(__file__).parent / "fixtures" / "oracle_values.yaml"
_DATA = yaml.safe_load(FIXTURE.read_text(encoding="utf-8"))
_TOL = _DATA["meta"]["tolerances"]
_MONTHLY_VARS = {
    "allocations_familiales",
    "allocation_soutien_familial",
    "rsa",
    "prime_activite",
}


def _live_model_value(row: dict) -> float:
    inp = row["inputs"]
    y = str(row["period"])
    salaires_decl = inp.get("salaires")
    salaires_bruts = inp.get("salaires_bruts")
    incomes = salaires_bruts if salaires_bruts is not None else salaires_decl
    use_brut = salaires_bruts is not None
    pensions = inp.get("pensions")
    is_cadre = bool(inp.get("cadre", False))

    individus = {}
    adults, kids = [], []
    for i, val in enumerate(incomes):
        pid = f"a{i + 1}"
        adults.append(pid)
        individus[pid] = {
            ("salaire_brut" if use_brut else "salaire_declare"): {y: val},
            "age": {y: 40},
        }
        if is_cadre:
            individus[pid]["cadre"] = {y: True}
        if pensions is not None:
            individus[pid]["pensions_alimentaires_percues"] = {y: pensions[i]}
    for j, age in enumerate(inp.get("enfants", [])):
        cid = f"e{j + 1}"
        kids.append(cid)
        individus[cid] = {"age": {y: age}}

    menage = {"personnes_de_reference": [adults[0]]}
    if len(adults) > 1:
        menage["conjoints"] = [adults[1]]
    if kids:
        menage["enfants"] = kids

    sit = {
        "individus": individus,
        "foyers_fiscaux": {
            "ff": {
                "declarants": adults,
                "personnes_a_charge": kids,
                "parent_isole": {y: bool(inp.get("parent_isole", False))},
            }
        },
        "familles": {"fam": {"parents": adults, "enfants": kids}},
        "menages": {"men": menage},
    }
    sim = Simulation(situation=sit)
    var = row["variable"]
    if var in _MONTHLY_VARS:
        return float(sim.calculate_add(var, y).sum())
    return float(sim.calculate(var, y).sum())


@pytest.mark.parametrize("row", _DATA["households"], ids=lambda r: r["id"])
def test_model_matches_official_oracle(row):
    official = row.get("official")
    if official is None:
        pytest.skip(f"{row['id']}: official value not yet captured")
    tol = _TOL[row["variable"]]
    live = _live_model_value(row)
    # 1. Verify recorded `model` in fixture has not drifted from live simulation
    assert abs(live - row["model"]) <= 0.10, (
        f"{row['id']} {row['variable']}: live {live:.2f} drifted from recorded model {row['model']}"
    )
    # 2. Verify live simulation matches the independent oracle within tolerance
    delta = live - official
    assert abs(delta) <= tol, (
        f"{row['id']} {row['variable']}: live {live:.2f} vs official "
        f"{official} (Δ {delta:+.2f}, tol {tol})"
    )
