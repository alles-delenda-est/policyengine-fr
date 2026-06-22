"""Independent AF oracle via openfisca-france.

The DGFiP income-tax simulator does not output allocations familiales, so the
AF rows in ``tests/fixtures/oracle_values.yaml`` are validated against
**openfisca-france** instead — a fully independent French microsimulation
implementation (different team, different codebase). This is the independent
oracle the cowork-validation-brief lists alongside the official simulators.

This script is NOT part of the pytest suite: openfisca-france cannot share the
project's environment (it pins an older numpy and is incompatible with
policyengine-core in the same interpreter). Run it in a throwaway venv and paste
the results into the fixture's ``official`` fields.

Reproduce (Windows, from the repo's parent dir)::

    uv venv --python 3.12 .venv-of312
    uv pip install --python .venv-of312 openfisca-france "numpy==2.1.3"
    .venv-of312/Scripts/python.exe policyengine-fr/tests/oracle/compute_af_openfisca.py

(numpy is pinned to 2.1.3 because openfisca-core 44.x clashes with numpy >= 2.5's
generic-ndarray metaclass.)

Fairness note: policyengine-fr's MVP uses *current-year* salaire_imposable as a
proxy for the legal base-ressources N-2. To compare like with like, this script
feeds openfisca-france the same salary across years N-2..N, so its N-2 base
ressources sees the same resources the model assumes (stable income). For a
household whose income actually changed year-on-year the two would diverge — that
is the documented MVP simplification, not a bug.
"""

from openfisca_france import FranceTaxBenefitSystem
from openfisca_core.simulations import SimulationBuilder

tbs = FranceTaxBenefitSystem()

# Mirror of the AF battery in tests/fixtures/oracle_values.yaml.
BATTERY = [
    ("couple_60k_2children", [60000, 0], [10, 16]),
    ("couple_90k_3children", [50000, 40000], [3, 8, 15]),
    ("couple_40k_4children", [40000, 0], [2, 6, 11, 15]),
]


def compute_af_annual(salaires, child_ages, year=2024):
    """Return the openfisca-france annual `af` total for a household."""
    individus, parents, enfants = {}, [], []
    for i, sal in enumerate(salaires):
        pid = f"parent{i + 1}"
        parents.append(pid)
        months = {
            f"{y}-{m:02d}": sal / 12
            for y in (year - 2, year - 1, year)
            for m in range(1, 13)
        }
        individus[pid] = {"salaire_de_base": months}
    for j, age in enumerate(child_ages):
        cid = f"enfant{j + 1}"
        enfants.append(cid)
        individus[cid] = {"date_naissance": {"ETERNITY": f"{year - age}-06-01"}}
    menage = {"personne_de_reference": [parents[0]], "enfants": enfants}
    if len(parents) > 1:
        menage["conjoint"] = [parents[1]]
    situation = {
        "individus": individus,
        "familles": {"fam": {"parents": parents, "enfants": enfants}},
        "foyers_fiscaux": {
            "ff": {"declarants": parents, "personnes_a_charge": enfants}
        },
        "menages": {"men": menage},
    }
    sim = SimulationBuilder().build_from_entities(tbs, situation)
    return sum(float(sim.calculate("af", f"{year}-{m:02d}")[0]) for m in range(1, 13))


if __name__ == "__main__":
    for name, salaires, child_ages in BATTERY:
        annual = compute_af_annual(salaires, child_ages)
        print(f"{name:<24} af_annual={annual:.2f}")
