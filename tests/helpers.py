"""Helpers to build whole-household simulations for property/golden-master tests.

These tests exercise the model through the public ``policyengine_fr.Simulation``
API on realistic households, complementing the per-variable YAML unit tests.

Scope note: the builder wires one person into each of the four entities
(individu / foyer_fiscal / famille / menage) as a single foyer = single famille
= single menage household. That keeps the inter-entity aggregation in
``revenu_disponible`` (which averages group totals over members) well-defined.
"""

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
) -> Simulation:
    """Build a single-household Simulation.

    adult_incomes: gross annual salary (salaire_brut) for each adult (1 or 2).
    child_ages: age of each dependent child (placed as enfant/personne à charge).
    """
    assert 1 <= len(adult_incomes) <= 2, "1 or 2 adults"
    y = str(year)
    individus: dict = {}
    adults: list[str] = []
    kids: list[str] = []
    for i, income in enumerate(adult_incomes):
        pid = f"adulte_{i + 1}"
        adults.append(pid)
        individus[pid] = {"salaire_brut": {y: income}, "age": {y: adult_age}}
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


# Output variables and how to read them (allocations_familiales is monthly).
ANNUAL_VARS = ["revenu_net_imposable", "impot_revenu", "revenu_disponible"]
PER_PERSON_ANNUAL_VARS = ["csg", "crds"]
MONTHLY_VARS = ["allocations_familiales"]


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
