"""Independent AF oracle via openfisca-france.

The DGFiP income-tax simulator does not output allocations familiales, so the
AF rows in ``tests/fixtures/oracle_values.yaml`` are validated against
**openfisca-france** instead — a fully independent French microsimulation
implementation (different team, different codebase). This is the independent
oracle the cowork-validation-brief lists alongside the official simulators.

This script is NOT part of the pytest suite: openfisca-france cannot share the
project's environment (it pins an older numpy and is incompatible with
policyengine-core in the same interpreter). It runs in a dedicated, separate
virtual environment named ``.venv-of312``.

The ``.venv-of312`` environment
-------------------------------
``.venv-of312`` is a throwaway Python 3.12 virtual environment used *only* to run
this openfisca-france oracle. It exists because:

- openfisca-france and policyengine-core **cannot coexist** in one interpreter
  (conflicting dependencies), so the oracle must live outside the project ``.venv``;
- openfisca-core 44.x **breaks on numpy >= 2.5** (a generic-ndarray metaclass
  clash), so numpy is pinned to 2.1.3 — note this is a numpy issue, not a Python
  version issue.

It is created **in the repo's parent directory** (``PolicyEngineFR/.venv-of312``),
i.e. *outside* the git repository, so it is never committed and never interferes
with the project ``.venv``. It is disposable: delete it any time and recreate it
with the two commands below. Keeping it around just saves the ~30 s reinstall when
you next refresh the AF oracle.

Reproduce (Windows, from the repo's parent dir)::

    uv venv --python 3.12 .venv-of312
    uv pip install --python .venv-of312 openfisca-france "numpy==2.1.3"
    .venv-of312/Scripts/python.exe policyengine-fr/tests/oracle/compute_af_openfisca.py

(``uv`` itself is installed with ``python -m pip install uv``; it fetches a
standalone, user-local CPython 3.12 — no system Python change required.)

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


def compute_asf_annual(child_ages, year=2024):
    """Return the openfisca-france annual `asf` total for a single-parent household.

    Builds a single-parent famille (one declarant, marked `isole`) with the
    supplied child ages and sums the monthly `asf` values across the year.
    No salary is set — ASF is not means-tested in openfisca-france for the
    basic orphelin-assimile / isole configuration.
    """
    individus = {"parent1": {}}
    enfants = []
    for j, age in enumerate(child_ages):
        cid = f"enfant{j + 1}"
        enfants.append(cid)
        individus[cid] = {"date_naissance": {"ETERNITY": f"{year - age}-06-01"}}
    situation = {
        "individus": individus,
        "familles": {"fam": {"parents": ["parent1"], "enfants": enfants}},
        "foyers_fiscaux": {
            "ff": {"declarants": ["parent1"], "personnes_a_charge": enfants}
        },
        "menages": {"men": {"personne_de_reference": ["parent1"], "enfants": enfants}},
    }
    sim = SimulationBuilder().build_from_entities(tbs, situation)
    return sum(float(sim.calculate("asf", f"{year}-{m:02d}")[0]) for m in range(1, 13))


def compute_asf_differentielle_annual(child_ages, pension_annuelle, year=2024):
    """Annual openfisca-france `asf` for a single parent receiving a pension.

    Models a single-parent famille with the given children and a partial
    annual pension alimentaire, returning the total annual ASF (which
    openfisca-france computes as ASF différentielle = ASF taux-plein − pension).
    """
    months = {f"{year}-{m:02d}": pension_annuelle / 12 for m in range(1, 13)}
    individus = {"parent1": {"pensions_alimentaires_percues": months}}
    enfants = []
    for j, age in enumerate(child_ages):
        cid = f"enfant{j + 1}"
        enfants.append(cid)
        individus[cid] = {"date_naissance": {"ETERNITY": f"{year - age}-06-01"}}
    situation = {
        "individus": individus,
        "familles": {"fam": {"parents": ["parent1"], "enfants": enfants}},
        "foyers_fiscaux": {
            "ff": {"declarants": ["parent1"], "personnes_a_charge": enfants}
        },
        "menages": {"men": {"personne_de_reference": ["parent1"], "enfants": enfants}},
    }
    sim = SimulationBuilder().build_from_entities(tbs, situation)
    return sum(float(sim.calculate("asf", f"{year}-{m:02d}")[0]) for m in range(1, 13))


def compute_rsa_annual(salaires, child_ages, pension_annuelle=0, year=2024):
    """Return the openfisca-france annual `rsa` total for a housed household.

    Feeds constant monthly salaries across N-1..N and marks `loge_gratuitement`
    across all 12 months so the statutory forfait logement applies identically
    to policyengine-fr's always-applied forfait logement.
    """
    individus, parents, enfants = {}, [], []
    for i, sal in enumerate(salaires):
        pid = f"parent{i + 1}"
        parents.append(pid)
        individus[pid] = {
            "date_naissance": {"ETERNITY": f"{year - 40}-01-01"},
            "salaire_de_base": {
                f"{y}-{m:02d}": sal / 12 for y in (year - 1, year) for m in range(1, 13)
            },
            "categorie_salarie": {
                f"{y}-{m:02d}": "prive_non_cadre"
                for y in (year - 1, year)
                for m in range(1, 13)
            },
        }
        if i == 0 and pension_annuelle > 0:
            individus[pid]["pensions_alimentaires_percues"] = {
                f"{y}-{m:02d}": pension_annuelle / 12
                for y in (year - 1, year)
                for m in range(1, 13)
            }
    for j, age in enumerate(child_ages):
        cid = f"enfant{j + 1}"
        enfants.append(cid)
        individus[cid] = {"date_naissance": {"ETERNITY": f"{year - age}-06-01"}}
    famille = {"parents": parents, "enfants": enfants}
    if len(parents) == 1 and len(enfants) >= 1:
        famille["rsa_isolement_recent"] = {
            f"{year}-{m:02d}": True for m in range(1, 13)
        }
    menage = {
        "personne_de_reference": [parents[0]],
        "enfants": enfants,
        "statut_occupation_logement": {
            f"{year}-{m:02d}": "loge_gratuitement" for m in range(1, 13)
        },
    }
    if len(parents) > 1:
        menage["conjoint"] = [parents[1]]
    situation = {
        "individus": individus,
        "familles": {"fam": famille},
        "foyers_fiscaux": {
            "ff": {"declarants": parents, "personnes_a_charge": enfants}
        },
        "menages": {"men": menage},
    }
    sim = SimulationBuilder().build_from_entities(tbs, situation)
    return sum(float(sim.calculate("rsa", f"{year}-{m:02d}")[0]) for m in range(1, 13))


if __name__ == "__main__":
    for name, salaires, child_ages in BATTERY:
        annual = compute_af_annual(salaires, child_ages)
        print(f"{name:<24} af_annual={annual:.2f}")
    print(f"{'single_parent_1child':<24} asf_annual={compute_asf_annual([8]):.2f}")
    print(
        f"{'single_parent_1child_pension':<28} "
        f"asf_diff={compute_asf_differentielle_annual([8], 1_200):.2f}"
    )
    print(f"{'single_0_rsa':<28} rsa={compute_rsa_annual([0], []):.2f}")
    print(
        f"{'couple_0_2children_rsa':<28} rsa={compute_rsa_annual([0, 0], [8, 10]):.2f}"
    )
    print(f"{'single_parent_0_1child_rsa':<28} rsa={compute_rsa_annual([0], [8]):.2f}")
    print(
        f"{'single_parent_1200pen_rsa':<28} "
        f"rsa={compute_rsa_annual([0], [8], pension_annuelle=1_200):.2f}"
    )
