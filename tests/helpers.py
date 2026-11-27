"""Helpers to build whole-household simulations for property/golden-master tests."""

from __future__ import annotations

from policyengine_fr import Simulation

YEAR = 2024


def build_household(
    adult_incomes: list[float],
    child_ages: list[int],
    *,
    parent_isole: bool = False,
    adult_age: int = 40,
    year: int = YEAR,
    adult_pensions: list[float] | None = None,
    adult_retraites: list[float] | None = None,
    cadres: list[bool] | None = None,
) -> Simulation:
    """Build a single-household Simulation."""
    assert 1 <= len(adult_incomes) <= 2, "1 or 2 adults"
    assert adult_pensions is None or len(adult_pensions) == len(adult_incomes)
    assert adult_retraites is None or len(adult_retraites) == len(adult_incomes)
    assert cadres is None or len(cadres) == len(adult_incomes)

    y = str(year)
    individus: dict = {}
    adults: list[str] = []
    kids: list[str] = []
    for i, income in enumerate(adult_incomes):
        pid = f"adulte_{i + 1}"
        adults.append(pid)
        individus[pid] = {"salaire_brut": {y: income}, "age": {y: adult_age}}
        if adult_pensions is not None:
            individus[pid]["pensions_alimentaires_percues"] = {y: adult_pensions[i]}
        if adult_retraites is not None:
            individus[pid]["pension_retraite"] = {y: adult_retraites[i]}
        if cadres is not None:
            individus[pid]["cadre"] = {y: cadres[i]}
    for j, age in enumerate(child_ages):
        cid = f"enfant_{j + 1}"
        kids.append(cid)
        individus[cid] = {"salaire_brut": {y: 0}, "age": {y: age}}

    menage: dict = {"personnes_de_reference": [adults[0]]}
    if len(adults) > 1:
        menage["conjoints"] = [adults[1]]
    if kids:
        menage["enfants"] = kids

    situation = {
        "individus": individus,
        "foyers_fiscaux": {
            "ff": {
                "declarants": adults,
                "personnes_a_charge": kids,
                "parent_isole": {y: parent_isole},
            }
        },
        "familles": {"fam": {"parents": adults, "enfants": kids}},
        "menages": {"men": menage},
    }
    return Simulation(situation=situation)


ANNUAL_VARS = ["revenu_net_imposable", "impot_revenu", "revenu_disponible"]
PER_PERSON_ANNUAL_VARS = [
    "cotisations_salariales",
    "salaire_declare",
    "salaire_net",
    "csg",
    "crds",
    "cotisations_patronales",
    "reduction_generale",
    "cout_du_travail",
]
MONTHLY_VARS = [
    "allocations_familiales",
    "allocation_soutien_familial",
    "rsa",
    "prime_activite",
]


def totals(sim: Simulation, year: int = YEAR) -> dict[str, float]:
    """Return scalar household totals for the headline outputs."""
    y = str(year)
    out: dict[str, float] = {}
    for var in ANNUAL_VARS:
        out[var] = round(float(sim.calculate(var, y).sum()), 2)
    for var in PER_PERSON_ANNUAL_VARS:
        out[var] = round(float(sim.calculate(var, y).sum()), 2)
    for var in MONTHLY_VARS:
        out[var] = round(float(sim.calculate_add(var, y).sum()), 2)
    return out
