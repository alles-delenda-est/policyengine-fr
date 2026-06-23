# ASF — Allocation de soutien familial (taux simple) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Model the allocation de soutien familial (ASF) at *taux simple* — a flat
0,422 × BMAF per eligible child, paid to a single-parent famille — and fold it into
`revenu_disponible`.

**Architecture:** One new Famille/MONTH variable mirroring `allocations_familiales`,
one new parameter (a BMAF fraction reusing the existing `gov.cnaf.bmaf` param),
wired into the ménage aggregate with the same group-distribution + `ADD` pattern AF
uses. Eligibility = famille with exactly one parent; no resource test. Design spec:
`docs/superpowers/specs/2026-06-22-asf-design.md`.

**Tech Stack:** policyengine-core (YAML parameters/tests, vectorised `Variable`
formulas), pytest property tests under `tests/`, openfisca-france as the independent
oracle.

## Global Constraints

- **Branch:** `feat/asf`, off `main`. One benefit, one PR. Do **not** add unrelated work.
- **Every parameter needs a legal `reference`** to its official source.
- **Formatting:** run `make format` (ruff) before committing; CI enforces.
- **Changelog:** towncrier fragment in `changelog.d/`; never hand-edit `CHANGELOG.md`.
- **Naming:** import package `policyengine_fr` (underscores); files mirror the
  parameters/variables/tests tree.
- **Test runner (this Windows box):** `.venv/Scripts/policyengine-core.exe test -c policyengine_fr <path>`
  for YAML tests; `.venv/Scripts/python.exe -m pytest tests/` for property tests.
- **ASF taux simple = 0,422 × BMAF per eligible child** (CSS art. R523-7; Décret
  2022-1370). BMAF: 445,93 € (→2024-03), 466,44 € (from 2024-04). Test float margin
  `0.01` (policyengine-core arrays are float32).
- **Eligible child:** role enfant, `0 <= age < gov.cnaf.prestations.af.age_limite`
  (< 20), reusing AF's age-limit parameter (one source of truth).

---

## File Structure

- **Create** `policyengine_fr/parameters/gov/cnaf/prestations/asf/taux_orphelin_un_parent.yaml`
  — the 0,422 BMAF fraction, dated, with legal reference.
- **Create** `policyengine_fr/variables/gov/cnaf/prestations/asf/allocation_soutien_familial.py`
  — the formula (Famille, MONTH, EUR).
- **Create** `policyengine_fr/tests/gov/cnaf/prestations/asf/allocation_soutien_familial.yaml`
  — YAML unit tests.
- **Modify** `policyengine_fr/variables/menage/revenu_disponible.py` — add ASF to the aggregate.
- **Modify** `tests/test_properties.py` + `tests/helpers.py` — ASF invariants + add to MONTHLY_VARS.
- **Modify** `policyengine_fr/modelled_policies.yaml` — move ASF to modelled + simplifications note.
- **Modify** `tests/oracle/compute_af_openfisca.py` + `tests/fixtures/oracle_values.yaml` — ASF oracle row.
- **Regenerate** `tests/fixtures/golden_master.json`; **add** `changelog.d/` fragment.

---

## Task 0: Branch

- [ ] **Step 1: Create the feature branch off an up-to-date main**

```bash
cd "C:/Users/patri/projects/PolicyEngineFR/policyengine-fr"
git checkout main && git pull
git checkout -b feat/asf
```

---

## Task 1: ASF parameter

**Files:**
- Create: `policyengine_fr/parameters/gov/cnaf/prestations/asf/taux_orphelin_un_parent.yaml`

**Interfaces:**
- Produces: parameter path `gov.cnaf.prestations.asf.taux_orphelin_un_parent` → `0.422` (float, /1), consumed by Task 2.

- [ ] **Step 1: Write the parameter file**

```yaml
description: Montant de l'allocation de soutien familial (ASF) à taux simple, exprimé en proportion de la BMAF, pour un enfant privé du soutien d'un seul de ses parents (orphelin d'un parent ou assimilé).
values:
  2022-11-01: 0.422
metadata:
  unit: /1
  label: Taux ASF orphelin d'un parent (en BMAF)
  reference:
    - title: Article R523-7 du Code de la sécurité sociale
      href: https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000046498993
    - title: Décret n° 2022-1370 du 27/10/2022 (art. 1)
      href: https://www.legifrance.gouv.fr/jorf/id/JORFTEXT000046497145
```

- [ ] **Step 2: Sanity-check it loads**

Run: `.venv/Scripts/python.exe -c "from policyengine_fr import CountryTaxBenefitSystem as S; import datetime; p=S().parameters; print(p.gov.cnaf.prestations.asf.taux_orphelin_un_parent('2024-01-01'))"`
Expected: prints `0.422`. (If the import name differs, use the one already used in `tests/helpers.py`'s `Simulation`; the point is just that the parameter resolves.)

- [ ] **Step 3: Commit**

```bash
git add policyengine_fr/parameters/gov/cnaf/prestations/asf/taux_orphelin_un_parent.yaml
git commit -m "feat(asf): add taux orphelin d'un parent parameter (0,422 BMAF, R523-7)"
```

---

## Task 2: ASF variable (TDD)

**Files:**
- Create: `policyengine_fr/variables/gov/cnaf/prestations/asf/allocation_soutien_familial.py`
- Test: `policyengine_fr/tests/gov/cnaf/prestations/asf/allocation_soutien_familial.yaml`

**Interfaces:**
- Consumes: `gov.cnaf.prestations.asf.taux_orphelin_un_parent` (Task 1), `gov.cnaf.bmaf`,
  `gov.cnaf.prestations.af.age_limite` (existing).
- Produces: Famille/MONTH variable `allocation_soutien_familial` (float, EUR), consumed by Tasks 3, 4, 6, 7.

- [ ] **Step 1: Write the failing YAML tests**

Create `policyengine_fr/tests/gov/cnaf/prestations/asf/allocation_soutien_familial.yaml`.
No `salaire_brut` is set: ASF has no resource test, and omitting income on monthly
periods sidesteps the known policyengine-core YEAR-on-monthly storage bug.

```yaml
# Allocation de soutien familial (ASF), taux simple — CSS art. L523-1 s., R523-7.
# Taux simple = 0,422 BMAF par enfant éligible ; famille à parent unique ;
# pas de condition de ressources. BMAF 445,93 € (jan-mars 2024) puis 466,44 €.
- name: Parent unique, un enfant, janvier 2024 (BMAF 445,93)
  absolute_error_margin: 0.01
  period: 2024-01
  input:
    individus:
      parent_1: {}
      enfant_1: {age: 8}
    familles:
      famille_1:
        parents: [parent_1]
        enfants: [enfant_1]
  output:
    # 0,422 × 445,93 = 188,18246
    allocation_soutien_familial: 188.18246

- name: Parent unique, un enfant, avril 2024 (BMAF revalorisée 466,44)
  absolute_error_margin: 0.01
  period: 2024-04
  input:
    individus:
      parent_1: {}
      enfant_1: {age: 8}
    familles:
      famille_1:
        parents: [parent_1]
        enfants: [enfant_1]
  output:
    # 0,422 × 466,44 = 196,83768
    allocation_soutien_familial: 196.83768

- name: Parent unique, deux enfants, avril 2024 (versée dès le premier enfant)
  absolute_error_margin: 0.01
  period: 2024-04
  input:
    individus:
      parent_1: {}
      enfant_1: {age: 4}
      enfant_2: {age: 9}
    familles:
      famille_1:
        parents: [parent_1]
        enfants: [enfant_1, enfant_2]
  output:
    # 2 × 0,422 × 466,44 = 393,67536
    allocation_soutien_familial: 393.67536

- name: Couple (deux parents), deux enfants — pas d'ASF à taux simple
  absolute_error_margin: 0.01
  period: 2024-04
  input:
    individus:
      parent_1: {}
      parent_2: {}
      enfant_1: {age: 4}
      enfant_2: {age: 9}
    familles:
      famille_1:
        parents: [parent_1, parent_2]
        enfants: [enfant_1, enfant_2]
  output:
    allocation_soutien_familial: 0

- name: Parent unique sans enfant à charge — aucune ASF
  absolute_error_margin: 0.01
  period: 2024-04
  input:
    individus:
      parent_1: {}
    familles:
      famille_1:
        parents: [parent_1]
        enfants: []
  output:
    allocation_soutien_familial: 0

- name: Parent unique, enfant de 20 ans (au-delà de la limite) — aucune ASF
  absolute_error_margin: 0.01
  period: 2024-04
  input:
    individus:
      parent_1: {}
      enfant_1: {age: 20}
    familles:
      famille_1:
        parents: [parent_1]
        enfants: [enfant_1]
  output:
    allocation_soutien_familial: 0
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `.venv/Scripts/policyengine-core.exe test -c policyengine_fr policyengine_fr/tests/gov/cnaf/prestations/asf/allocation_soutien_familial.yaml`
Expected: FAIL — `allocation_soutien_familial` is not a known variable.

- [ ] **Step 3: Write the variable**

Create `policyengine_fr/variables/gov/cnaf/prestations/asf/allocation_soutien_familial.py`:

```python
from policyengine_fr.model_api import *


class allocation_soutien_familial(Variable):
    value_type = float
    entity = Famille
    label = "Allocation de soutien familial (taux simple)"
    unit = EUR
    documentation = (
        "Allocation de soutien familial (ASF) versée par la CAF/MSA pour un "
        "enfant privé du soutien d'un de ses parents (CSS art. L523-1 et s.). "
        "Au taux simple, le montant vaut 0,422 BMAF par enfant à charge "
        "(art. R523-7), versé dès le premier enfant et sans condition de "
        "ressources. Le périmètre MVP infère le droit du seul fait que la "
        "famille n'a qu'un parent.\n\n"
        "Limitations MVP (départs explicites du droit, voir modelled_policies.yaml):\n"
        "- Taux majoré « orphelin de deux parents » non modélisé (un seul taux).\n"
        "- ASF différentielle / recouvrement non modélisés : faute d'input "
        "pension alimentaire, le modèle verse l'ASF pleine à toute famille "
        "monoparentale, même si une pension alimentaire est déjà perçue "
        "(sur-estimation possible).\n"
        "- Le cas d'un parent défaillant au sein d'un couple (ouvrant droit à "
        "l'ASF) n'est pas capté par le proxy « parent unique » (sous-estimation).\n"
        "- Métropole uniquement ; pas de partage en garde alternée."
    )
    definition_period = MONTH
    reference = "https://www.service-public.fr/particuliers/vosdroits/F815"

    def formula(famille, period, parameters):
        asf = parameters(period).gov.cnaf.prestations.asf
        bmaf = parameters(period).gov.cnaf.bmaf
        age_limite = parameters(period).gov.cnaf.prestations.af.age_limite

        age = famille.members("age", period)
        est_enfant = famille.members.has_role(Famille.ENFANT)
        # Enfant à charge ouvrant droit: rôle enfant et âge sous la limite AF.
        ouvre_droit = est_enfant & (age >= 0) & (age < age_limite)
        nb_enfants = famille.sum(ouvre_droit)

        # Proxy MVP du droit: la famille n'a qu'un seul parent.
        parent_unique = famille.nb_persons(Famille.PARENT) == 1

        montant = bmaf * asf.taux_orphelin_un_parent * nb_enfants
        return where(parent_unique, montant, 0)
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `.venv/Scripts/policyengine-core.exe test -c policyengine_fr policyengine_fr/tests/gov/cnaf/prestations/asf/allocation_soutien_familial.yaml`
Expected: PASS (6/6). If the couple case is non-zero, `nb_persons(Famille.PARENT)`
is wrong — debug with superpowers:systematic-debugging before proceeding.

- [ ] **Step 5: `make format`, then commit**

```bash
make format
git add policyengine_fr/variables/gov/cnaf/prestations/asf/allocation_soutien_familial.py policyengine_fr/tests/gov/cnaf/prestations/asf/allocation_soutien_familial.yaml
git commit -m "feat(asf): allocation de soutien familial variable (taux simple, parent unique)"
```

---

## Task 3: Wire ASF into revenu_disponible

**Files:**
- Modify: `policyengine_fr/variables/menage/revenu_disponible.py`

**Interfaces:**
- Consumes: `allocation_soutien_familial` (Task 2), Famille/MONTH.
- Produces: `revenu_disponible` now includes annualised ASF.

- [ ] **Step 1: Add a failing whole-household test**

Add to `tests/test_properties.py` (full helper-based assertion; reuse `build_household`):

```python
def test_asf_in_revenu_disponible_single_parent():
    # Single parent, 1 child, no income: revenu_disponible == annual ASF.
    from tests.helpers import build_household
    sim = build_household([0], [8])
    rd = float(sim.calculate("revenu_disponible", "2024").sum())
    # 3×188,18246 (jan-mars) + 9×196,83768 (avr-déc) = 2336.0407...
    assert abs(rd - 2336.04) < 0.5
```

Run: `.venv/Scripts/python.exe -m pytest tests/test_properties.py::test_asf_in_revenu_disponible_single_parent -v`
Expected: FAIL (revenu_disponible still excludes ASF → 0.0).

- [ ] **Step 2: Add ASF to the aggregate**

In `policyengine_fr/variables/menage/revenu_disponible.py`, inside `formula`, after the
`allocations_familiales` block and before `return`, add:

```python
        # Allocation de soutien familial: mensuelle, annualisée via ADD,
        # répartie sur les membres de la famille comme les AF.
        asf_groupe = menage.members.famille(
            "allocation_soutien_familial", period, options=[ADD]
        )
        allocation_soutien_familial = menage.sum(asf_groupe / membres_famille)
```

Change the return line to:

```python
        return (
            salaire_brut
            - impot_revenu
            - csg
            - crds
            + allocations_familiales
            + allocation_soutien_familial
        )
```

Update the docstring: in the formula comment block add `+ allocation_soutien_familial`,
and add a bullet: "L'allocation de soutien familial (familles monoparentales) est
ajoutée, annualisée comme les AF."

- [ ] **Step 3: Run the test to verify it passes**

Run: `.venv/Scripts/python.exe -m pytest tests/test_properties.py::test_asf_in_revenu_disponible_single_parent -v`
Expected: PASS.

- [ ] **Step 4: `make format`, then commit**

```bash
make format
git add policyengine_fr/variables/menage/revenu_disponible.py tests/test_properties.py
git commit -m "feat(asf): include ASF in revenu_disponible aggregate"
```

---

## Task 4: Property invariants

**Files:**
- Modify: `tests/test_properties.py`

**Interfaces:**
- Consumes: `allocation_soutien_familial` (Task 2), `build_household` helper.

- [ ] **Step 1: Add invariant tests**

Append to `tests/test_properties.py`:

```python
import pytest


@pytest.mark.parametrize("child_ages", [[], [8], [4, 9], [1, 7, 12]])
def test_asf_non_negative(child_ages):
    from tests.helpers import build_household
    sim = build_household([20000], child_ages)
    asf = sim.calculate("allocation_soutien_familial", "2024-04")
    assert (asf >= 0).all()


def test_asf_zero_for_couple():
    from tests.helpers import build_household
    sim = build_household([20000, 15000], [4, 9])
    asf = float(sim.calculate("allocation_soutien_familial", "2024-04").sum())
    assert asf == 0


def test_asf_scales_with_eligible_children():
    from tests.helpers import build_household
    one = float(build_household([0], [8]).calculate("allocation_soutien_familial", "2024-04").sum())
    two = float(build_household([0], [4, 9]).calculate("allocation_soutien_familial", "2024-04").sum())
    assert abs(two - 2 * one) < 0.01
```

- [ ] **Step 2: Run**

Run: `.venv/Scripts/python.exe -m pytest tests/test_properties.py -k asf -v`
Expected: PASS (all asf-tagged tests).

- [ ] **Step 3: Commit**

```bash
git add tests/test_properties.py
git commit -m "test(asf): property invariants — non-negativity, couple→0, linear in children"
```

---

## Task 5: Golden master + helper

**Files:**
- Modify: `tests/helpers.py`
- Regenerate: `tests/fixtures/golden_master.json`

**Interfaces:**
- Consumes: `allocation_soutien_familial` (Task 2).

- [ ] **Step 1: Add ASF to the helper's monthly outputs**

In `tests/helpers.py`, change:

```python
MONTHLY_VARS = ["allocations_familiales"]
```

to:

```python
MONTHLY_VARS = ["allocations_familiales", "allocation_soutien_familial"]
```

- [ ] **Step 2: Regenerate the golden master**

Find the regeneration command (look for a script or a `if __name__` block driving
`totals()`): `grep -rn "golden_master" tests/` and run the documented regen path.
If regeneration is manual, run:

Run: `.venv/Scripts/python.exe -m pytest tests/ -k golden -v`
Expected: FAIL first (new ASF key absent from fixture), then regenerate per the
repo's documented mechanism and re-run to GREEN. Do **not** hand-edit the JSON if a
generator exists.

- [ ] **Step 3: Run full pytest**

Run: `.venv/Scripts/python.exe -m pytest tests/ -v`
Expected: PASS (properties + golden master + oracle skips).

- [ ] **Step 4: Commit**

```bash
git add tests/helpers.py tests/fixtures/golden_master.json
git commit -m "test(asf): add ASF to golden-master household outputs"
```

---

## Task 6: Independent oracle row (openfisca-france)

**Files:**
- Modify: `tests/oracle/compute_af_openfisca.py`
- Modify: `tests/fixtures/oracle_values.yaml`

**Interfaces:**
- Consumes: `allocation_soutien_familial` (Task 2).

> **Anti-rabbit-hole guard:** openfisca-france's `asf` eligibility can be fiddly to
> trigger cleanly (it keys off `isole`/pension-alimentaire). If you cannot get a
> clean single-parent `asf` value out of openfisca within ~20 minutes, STOP: the
> 0,422 × BMAF parameter is already independently corroborated against openfisca's
> *parameter* (recorded in the design spec). In that case, add the oracle row with
> `official: null` (so the comparison test skips it, never false-green) and note the
> reason in `meta`. Do not keep fighting the oracle.

- [ ] **Step 1: Extend the oracle script**

In `tests/oracle/compute_af_openfisca.py`, add a function mirroring `compute_af_annual`
that builds a single-parent famille (one declarant, marked `isole`) with one child and
returns the annual `asf`:

```python
def compute_asf_annual(child_ages, year=2024):
    """Return the openfisca-france annual `asf` total for a single-parent household."""
    individus = {"parent1": {}}
    enfants = []
    for j, age in enumerate(child_ages):
        cid = f"enfant{j + 1}"
        enfants.append(cid)
        individus[cid] = {"date_naissance": {"ETERNITY": f"{year - age}-06-01"}}
    situation = {
        "individus": individus,
        "familles": {"fam": {"parents": ["parent1"], "enfants": enfants}},
        "foyers_fiscaux": {"ff": {"declarants": ["parent1"], "personnes_a_charge": enfants}},
        "menages": {"men": {"personne_de_reference": ["parent1"], "enfants": enfants}},
    }
    sim = SimulationBuilder().build_from_entities(tbs, situation)
    return sum(float(sim.calculate("asf", f"{year}-{m:02d}")[0]) for m in range(1, 13))
```

Add to the `__main__` block:

```python
    print(f"{'single_parent_1child':<24} asf_annual={compute_asf_annual([8]):.2f}")
```

- [ ] **Step 2: Run it in the openfisca env**

Run (from the repo's parent dir):
`../.venv-of312/Scripts/python.exe policyengine-fr/tests/oracle/compute_af_openfisca.py`
Expected: prints an `asf_annual` figure. Cross-check against the model:
3×188,18246 + 9×196,83768 = **2336,04 €** (single parent, 1 child age 8, 2024).

- [ ] **Step 3: Add the oracle row**

In `tests/fixtures/oracle_values.yaml`, append (use the captured openfisca figure for
`official`; if the guard above triggered, set `official: null`):

```yaml
  - {id: single_parent_1child_asf, variable: allocation_soutien_familial, inputs: {situation: celibataire, parent_isole: true, salaires: [0], enfants: [8]}, period: "2024", model: 2336.04, official: <captured>, captured_on: "2026-06-22"}
```

Add `allocation_soutien_familial` to the `tolerances` map in `meta` (e.g. `12.0`).
Confirm `tests/test_oracle.py` reads the tolerance generically (it keys off
`variable`); if it has a hardcoded variable list, extend it to accept the ASF row.

- [ ] **Step 4: Run the oracle test**

Run: `.venv/Scripts/python.exe -m pytest tests/test_oracle.py -v`
Expected: ASF row PASSES (within tolerance) or SKIPS (if `official: null`). Never a
false green.

- [ ] **Step 5: Commit**

```bash
git add tests/oracle/compute_af_openfisca.py tests/fixtures/oracle_values.yaml
git commit -m "test(asf): independent openfisca-france oracle row for single-parent ASF"
```

---

## Task 7: Scope doc + changelog + PR

**Files:**
- Modify: `policyengine_fr/modelled_policies.yaml`
- Create: `changelog.d/added/<name>.md`

- [ ] **Step 1: Update modelled_policies.yaml**

Add to `core.modelled`:

```yaml
    - Allocation de soutien familial (ASF) — taux simple, famille monoparentale
```

Remove `ASF` from the `Autres prestations sociales (RSA, APL, prime d'activité, ASF…)`
line in `not_modelled` (leave the others: `RSA, APL, prime d'activité…`).

Append to `core.simplifications`:

```yaml
    - >-
      Allocation de soutien familial — le droit est inféré du seul fait que la
      famille n'a qu'un parent (proxy MVP). Taux simple uniquement (0,422 BMAF) ;
      le taux majoré « orphelin de deux parents », l'ASF différentielle et le
      recouvrement sur parent défaillant ne sont pas modélisés. Faute d'input
      pension alimentaire, l'ASF pleine est versée à toute famille monoparentale
      (sur-estimation possible) ; un parent défaillant au sein d'un couple n'ouvre
      pas droit dans le modèle (sous-estimation). Métropole uniquement.
```

- [ ] **Step 2: Add the changelog fragment**

```bash
printf '%s\n' "Added the allocation de soutien familial (ASF) at taux simple (0,422 BMAF per eligible child for single-parent families) and included it in revenu disponible." > changelog.d/added/asf.md
```

(Confirm the towncrier category dir name — `ls changelog.d/` — and adjust `added/` if
the repo uses a different category folder.)

- [ ] **Step 3: Full suite + format**

```bash
make format
make test
.venv/Scripts/python.exe -m pytest tests/ -v
```

Expected: all green (existing suite + new ASF YAML cases + property/oracle).

- [ ] **Step 4: Commit and push**

```bash
git add policyengine_fr/modelled_policies.yaml changelog.d/
git commit -m "docs(asf): record ASF in modelled policies + simplifications + changelog"
git push -u origin feat/asf
```

- [ ] **Step 5: Open the PR**

Open a PR off `main` summarising: ASF taux simple (0,422 BMAF, single-parent proxy),
the documented deferred scope (taux majoré, différentielle, recouvrement), and the
independent openfisca-france oracle. Before merge, use superpowers:requesting-code-review.

---

## Self-Review

- **Spec coverage:** parameter §3 → Task 1; variable + eligibility + amount §3 → Task 2;
  aggregate §3 → Task 3; limitations §4 → Task 2 docstring + Task 7 modelled_policies;
  tests §5 → Tasks 2 (YAML), 4 (property), 6 (oracle); golden master + done-criteria §6
  → Tasks 5, 7. All spec sections mapped.
- **Placeholder scan:** every code/test step carries full content; the only deliberate
  variable is the openfisca oracle `official` figure (captured at runtime) — guarded so
  it skips rather than guesses.
- **Type/name consistency:** `allocation_soutien_familial` (Famille/MONTH),
  `gov.cnaf.prestations.asf.taux_orphelin_un_parent`, `famille.nb_persons(Famille.PARENT)`,
  and `age_limite` reuse are used identically across Tasks 1–7 and match the existing
  AF code they mirror.
