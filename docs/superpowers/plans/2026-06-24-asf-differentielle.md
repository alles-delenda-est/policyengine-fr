# ASF différentielle Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Net any pension alimentaire already received off the ASF amount, so a
single-parent famille receives only the *complément différentiel* topping the
pension up to the ASF floor — closing the over-count of the taux-simple MVP.

**Architecture:** A one-formula change to the existing `allocation_soutien_familial`
variable (Famille/MONTH). Eligibility, rate, period, and `revenu_disponible` are
unchanged. The pension is read from the existing `pensions_alimentaires_percues`
input (Individu/YEAR, added by PR #23), summed over the famille and divided by 12.
No new parameter, no new input.

**Tech Stack:** policyengine-core (YAML tests, vectorised `Variable` formulas),
pytest property tests, openfisca-france as the independent oracle.

Design spec: `docs/superpowers/specs/2026-06-24-asf-differentielle-design.md`.

## Global Constraints

- **Branch:** `feat/asf-differentielle`, off `main` (already created; the design spec
  is already committed on it). One change, one PR. No unrelated work.
- **Formula:** `ASF_versée = max(0,422·BMAF·nb_enfants − pension_mensuelle, 0)`, gated on
  `famille.nb_persons(Famille.PARENT) == 1`. `pension_mensuelle = Σ famille members'
  pensions_alimentaires_percues (read via period.this_year) ÷ 12`.
- **No new parameter, no new input, no edit to `revenu_disponible`** (the pension is
  already counted there by PR #23; netting it inside ASF avoids double-counting).
- **⚠️ YAML unit tests that set `pensions_alimentaires_percues` (a YEAR variable) MUST use
  period `2024-01`.** Setting a YEAR input on a Feb-or-later monthly test period crashes
  the policyengine-core test loader (`in_memory_storage.py:74`,
  `ValueError: Expected a period; got: 'year'`). January is safe; this was verified
  empirically. At 2024-01, BMAF = 445,93 and ASF/child = **188,18246**.
- **Property tests** use the Python `Simulation` API (`tests/helpers.build_household`),
  which sets YEAR inputs with explicit year keys and handles a 2024-04 `calculate`
  fine. At 2024-04, ASF/child = **196,83768**.
- **Test float margin `0.01`** (policyengine-core arrays are float32).
- **Formatting:** `make format` (ruff) before each commit; CI enforces.
- **Changelog:** towncrier fragment under `changelog.d/added/`; never hand-edit `CHANGELOG.md`.
- **Test runners (this Windows box):**
  `.venv/Scripts/policyengine-core.exe test -c policyengine_fr <path>` (YAML);
  `.venv/Scripts/python.exe -m pytest tests/ -v` (property).

---

## File Structure

- **Modify** `policyengine_fr/variables/gov/cnaf/prestations/asf/allocation_soutien_familial.py`
  — add the pension netting to the formula; update the docstring (the différentielle is
  now modelled).
- **Modify** `policyengine_fr/tests/gov/cnaf/prestations/asf/allocation_soutien_familial.yaml`
  — add différentielle unit cases (period 2024-01).
- **Modify** `tests/helpers.py` — add an optional `adult_pensions` parameter to
  `build_household` so property tests can inject a pension.
- **Modify** `tests/test_properties.py` — add différentielle invariants.
- **Modify** `tests/oracle/compute_af_openfisca.py` + `tests/fixtures/oracle_values.yaml`
  — independent openfisca-france différentielle oracle row (guarded).
- **Modify** `policyengine_fr/modelled_policies.yaml` — replace the ASF over-count note
  with the new reality; mention the différentielle in the `modelled` line.
- **Add** `changelog.d/added/asf-differentielle.md`.

---

## Task 1: ASF différentielle formula (TDD)

**Files:**
- Modify: `policyengine_fr/variables/gov/cnaf/prestations/asf/allocation_soutien_familial.py`
- Test: `policyengine_fr/tests/gov/cnaf/prestations/asf/allocation_soutien_familial.yaml`

**Interfaces:**
- Consumes: `pensions_alimentaires_percues` (Individu/YEAR, existing), `gov.cnaf.bmaf`,
  `gov.cnaf.prestations.asf.taux_orphelin_un_parent`, `gov.cnaf.prestations.af.age_limite`.
- Produces: `allocation_soutien_familial` (Famille/MONTH) now nets the pension.

- [ ] **Step 1: Add the failing différentielle unit cases**

Append these cases to
`policyengine_fr/tests/gov/cnaf/prestations/asf/allocation_soutien_familial.yaml`.
**All use period 2024-01** (BMAF 445,93) — see Global Constraints for why. Do not
modify the existing cases.

```yaml
# ── ASF différentielle : la pension alimentaire perçue est défalquée ──────────
# (CSS art. L523-1, L581-2). Période 2024-01 : BMAF 445,93 → ASF/enfant 188,18246.
# NB : l'input pension (variable annuelle) impose une période de janvier ; les
# autres mois déclenchent un bug du chargeur de tests policyengine-core.
- name: Parent unique, un enfant, pension partielle (1 200 €/an) — complément différentiel
  absolute_error_margin: 0.01
  period: 2024-01
  input:
    individus:
      parent_1: {pensions_alimentaires_percues: 1_200}
      enfant_1: {age: 8}
    familles:
      famille_1:
        parents: [parent_1]
        enfants: [enfant_1]
  output:
    # 188,18246 − (1 200 / 12 = 100) = 88,18246
    allocation_soutien_familial: 88.18246

- name: Parent unique, un enfant, pension ≥ ASF (3 600 €/an) — aucune ASF
  absolute_error_margin: 0.01
  period: 2024-01
  input:
    individus:
      parent_1: {pensions_alimentaires_percues: 3_600}
      enfant_1: {age: 8}
    familles:
      famille_1:
        parents: [parent_1]
        enfants: [enfant_1]
  output:
    # 188,18246 − 300 < 0 → borné à 0
    allocation_soutien_familial: 0

- name: Parent unique, deux enfants, pension partielle (2 400 €/an) — total famille
  absolute_error_margin: 0.01
  period: 2024-01
  input:
    individus:
      parent_1: {pensions_alimentaires_percues: 2_400}
      enfant_1: {age: 4}
      enfant_2: {age: 9}
    familles:
      famille_1:
        parents: [parent_1]
        enfants: [enfant_1, enfant_2]
  output:
    # 2 × 188,18246 = 376,36492 ; − (2 400 / 12 = 200) = 176,36492
    allocation_soutien_familial: 176.36492

- name: Couple avec pension perçue — toujours aucune ASF (éligibilité inchangée)
  absolute_error_margin: 0.01
  period: 2024-01
  input:
    individus:
      parent_1: {pensions_alimentaires_percues: 2_400}
      parent_2: {}
      enfant_1: {age: 4}
      enfant_2: {age: 9}
    familles:
      famille_1:
        parents: [parent_1, parent_2]
        enfants: [enfant_1, enfant_2]
  output:
    allocation_soutien_familial: 0
```

- [ ] **Step 2: Run the new cases — confirm they fail (RED)**

Run: `.venv/Scripts/policyengine-core.exe test -c policyengine_fr policyengine_fr/tests/gov/cnaf/prestations/asf/allocation_soutien_familial.yaml`
Expected: the three single-parent-with-pension cases FAIL (current code ignores the
pension and returns full ASF: 188,18246 / 188,18246 / 376,36492). The couple case and
all pre-existing cases PASS. (If instead you see `ValueError: Expected a period; got:
'year'`, a case is on the wrong month — every pension case must be `period: 2024-01`.)

- [ ] **Step 3: Add the netting to the formula**

In `policyengine_fr/variables/gov/cnaf/prestations/asf/allocation_soutien_familial.py`,
replace the body of `formula` from the `montant = ...` line to the `return` with:

```python
        asf_pleine = bmaf * asf.taux_orphelin_un_parent * nb_enfants

        # Complément différentiel (CSS art. L523-1, L581-2) : la pension
        # alimentaire perçue par la famille, ramenée au mois, est défalquée de
        # l'ASF pleine ; le résultat est borné à zéro. La base annuelle de la
        # pension est lue via period.this_year, comme la modulation AF lit ses
        # ressources. Pension nulle → ASF pleine (cas de l'allocation non
        # recouvrable, parent décédé/inconnu).
        pension_mensuelle = (
            famille.sum(
                famille.members("pensions_alimentaires_percues", period.this_year)
            )
            / 12
        )
        montant = max_(asf_pleine - pension_mensuelle, 0)
        return where(parent_unique, montant, 0)
```

(The lines above this — `asf`, `bmaf`, `age_limite`, `age`, `est_enfant`,
`ouvre_droit`, `nb_enfants`, `parent_unique` — are unchanged.)

- [ ] **Step 4: Update the docstring**

The différentielle is now *modelled*, so the over-count bullet must go. Make this a
single exact-string replacement — do **not** add a new "Limitations" header or a
second taux-majoré bullet (both already exist in the docstring).

The docstring currently contains exactly this bullet (the over-count claim):

```
        "- ASF différentielle / recouvrement non modélisés : faute d'input "
        "pension alimentaire, le modèle verse l'ASF pleine à toute famille "
        "monoparentale, même si une pension alimentaire est déjà perçue "
        "(sur-estimation possible).\n"
```

Replace **only** that bullet with this one (same `- ` bullet position, no new header):

```
        "- ASF versée en complément différentiel : la pension alimentaire perçue "
        "(pensions_alimentaires_percues, ramenée au mois) est défalquée de l'ASF "
        "pleine, bornée à zéro ; pension nulle → ASF pleine. Comparaison au niveau "
        "de la famille (et non enfant par enfant) ; la pension saisie est supposée "
        "être une pension pour enfant (une prestation compensatoire ne doit pas y "
        "figurer). Recouvrement de l'avance sur le parent débiteur non modélisé "
        "(transfert CAF↔débiteur, sans effet sur la famille).\n"
```

The other docstring bullets are unchanged and must each still appear exactly once: the
taux-majoré bullet (above this one), the under-count "parent défaillant au sein d'un
couple" bullet, and "Métropole uniquement ; pas de partage en garde alternée."

- [ ] **Step 5: Run all ASF cases — confirm GREEN**

Run: `.venv/Scripts/policyengine-core.exe test -c policyengine_fr policyengine_fr/tests/gov/cnaf/prestations/asf/allocation_soutien_familial.yaml`
Expected: PASS (all cases — the four new différentielle cases plus the six pre-existing
taux-simple cases, which are unaffected because their pension is 0).

- [ ] **Step 6: Run the full core YAML suite — confirm no regression**

Run: `.venv/Scripts/policyengine-core.exe test -c policyengine_fr policyengine_fr/tests`
Expected: PASS (73/73 — the ASF change is a no-op wherever no pension is set, which is
every other test).

- [ ] **Step 7: `make format`, then commit**

```bash
make format
git add policyengine_fr/variables/gov/cnaf/prestations/asf/allocation_soutien_familial.py policyengine_fr/tests/gov/cnaf/prestations/asf/allocation_soutien_familial.yaml
git commit -m "feat(asf): différentielle — net pension alimentaire off ASF amount"
```

---

## Task 2: Property invariants + helper support

**Files:**
- Modify: `tests/helpers.py`
- Modify: `tests/test_properties.py`

**Interfaces:**
- Consumes: `allocation_soutien_familial` (Task 1), `build_household`.
- Produces: `build_household(..., adult_pensions=[...])` injects
  `pensions_alimentaires_percues` per adult.

- [ ] **Step 1: Extend `build_household` with an optional pension**

In `tests/helpers.py`, change the signature:

```python
def build_household(
    adult_incomes: list[float],
    child_ages: list[int],
    *,
    parent_isole: bool = False,
    adult_age: int = 40,
    year: int = YEAR,
    adult_pensions: list[float] | None = None,
) -> Simulation:
```

and, inside the adult loop, after the line
`individus[pid] = {"salaire_brut": {y: income}, "age": {y: adult_age}}`, add:

```python
        if adult_pensions is not None:
            individus[pid]["pensions_alimentaires_percues"] = {y: adult_pensions[i]}
```

Just above the adult loop (next to the existing `assert 1 <= len(adult_incomes) <= 2`),
add:

```python
    assert adult_pensions is None or len(adult_pensions) == len(adult_incomes), (
        "adult_pensions must match adult_incomes length"
    )
```

- [ ] **Step 2: Add the failing property tests**

Append to `tests/test_properties.py` (the module already imports `build_household` at
the top — use it directly, no in-function import):

```python
def test_asf_non_increasing_in_pension():
    # A received pension reduces ASF euro-for-euro until it reaches zero.
    base = float(
        build_household([0], [8]).calculate("allocation_soutien_familial", "2024-04").sum()
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
```

- [ ] **Step 3: Run the new property tests — confirm they pass**

Run: `.venv/Scripts/python.exe -m pytest tests/test_properties.py -k "asf" -v`
Expected: PASS (the two new tests plus the existing asf-tagged tests). If
`test_asf_non_increasing_in_pension` shows `with_pension == base`, the helper isn't
injecting the pension — check the `adult_pensions` wiring.

- [ ] **Step 4: Run the full pytest suite — confirm no regression**

Run: `.venv/Scripts/python.exe -m pytest tests/ -v`
Expected: PASS (existing 34 + the 2 new property tests).

- [ ] **Step 5: `make format`, then commit**

```bash
make format
git add tests/helpers.py tests/test_properties.py
git commit -m "test(asf): différentielle property invariants (non-increasing, floor guarantee)"
```

---

## Task 3: Independent openfisca-france oracle row (guarded)

**Files:**
- Modify: `tests/oracle/compute_af_openfisca.py`
- Modify: `tests/fixtures/oracle_values.yaml`

**Interfaces:**
- Consumes: `allocation_soutien_familial` (Task 1).

> **Anti-rabbit-hole guard (hard limit):** openfisca-france's `asf` differential keys
> off how the pension alimentaire is declared and may be fiddly to trigger cleanly.
> You have a few attempts / ~20 minutes. If you cannot get a clean differential `asf`
> from openfisca, STOP: add the oracle row with `official: null` (so `test_oracle.py`
> skips it — never false-green) and note the reason in `meta`. A skipped honest row
> beats a fought one. Report DONE_WITH_CONCERNS describing what you tried.

The openfisca env is the separate `../.venv-of312` (Python 3.12, numpy 2.1.3), run
from the repo's parent dir. See the docstring in `compute_af_openfisca.py`.

- [ ] **Step 1: Add a differential ASF computation to the oracle script**

In `tests/oracle/compute_af_openfisca.py`, add a function that builds a single-parent
famille with one child and a partial annual pension alimentaire, and returns the
annual `asf`:

```python
def compute_asf_differentielle_annual(child_ages, pension_annuelle, year=2024):
    """Annual openfisca-france `asf` for a single parent receiving a pension."""
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
        "foyers_fiscaux": {"ff": {"declarants": ["parent1"], "personnes_a_charge": enfants}},
        "menages": {"men": {"personne_de_reference": ["parent1"], "enfants": enfants}},
    }
    sim = SimulationBuilder().build_from_entities(tbs, situation)
    return sum(float(sim.calculate("asf", f"{year}-{m:02d}")[0]) for m in range(1, 13))
```

Add to the `__main__` block:

```python
    print(
        f"{'single_parent_1child_pension':<28} "
        f"asf_diff={compute_asf_differentielle_annual([8], 1_200):.2f}"
    )
```

> Note: openfisca-france's input name for received alimony may differ
> (`pensions_alimentaires_percues` vs a per-individual variant). If the build errors on
> an unknown variable, inspect openfisca's own variable name for received pensions
> alimentaires and adapt — this is within the guard's timebox, not a rabbit hole.

- [ ] **Step 2: Run it in the openfisca env**

Run (from the repo's parent dir `C:/Users/patri/projects/PolicyEngineFR`):
`../.venv-of312/Scripts/python.exe policyengine-fr/tests/oracle/compute_af_openfisca.py`
Expected: prints an `asf_diff` figure. The model's annual equivalent for the same
household (single parent, 1 child, 1 200 €/yr pension) over 2024 is
3 × (188,18246 − 100) + 9 × (196,83768 − 100) = 3 × 88,18246 + 9 × 96,83768 = **1 135,09 €**.
Cross-check the openfisca figure against that.

- [ ] **Step 3: Add the oracle row**

In `tests/fixtures/oracle_values.yaml`, append (use the captured openfisca figure for
`official`; `null` if the guard triggered). Add `allocation_soutien_familial` to
`meta.tolerances` only if not already present (Task from the taux-simple PR already
added it at 12.0).

```yaml
  - {id: single_parent_1child_pension_asf, variable: allocation_soutien_familial, inputs: {situation: celibataire, parent_isole: true, salaires: [0], pensions: [1200], enfants: [8]}, period: "2024", model: 1135.09, official: <captured-or-null>, captured_on: "2026-06-24"}
```

- [ ] **Step 4: Run the oracle test**

Run: `.venv/Scripts/python.exe -m pytest tests/test_oracle.py -v`
Expected: the new ASF row PASSES (within tolerance) or SKIPS (`official: null`). Never
a false green. (If `test_oracle.py` cannot read the extra `pensions` input key, it
only compares recorded `model` vs `official` and ignores `inputs` — confirm it does
not choke on the new key; the existing rows already carry arbitrary `inputs` maps.)

- [ ] **Step 5: Commit**

```bash
git add tests/oracle/compute_af_openfisca.py tests/fixtures/oracle_values.yaml
git commit -m "test(asf): independent openfisca-france différentielle oracle row"
```

---

## Task 4: Scope doc + changelog + full suite

**Files:**
- Modify: `policyengine_fr/modelled_policies.yaml`
- Add: `changelog.d/added/asf-differentielle.md`

- [ ] **Step 1: Update `modelled_policies.yaml`**

Change the ASF `modelled` line:

```yaml
    - Allocation de soutien familial (ASF) — taux simple, famille monoparentale
```

to:

```yaml
    - Allocation de soutien familial (ASF) — taux simple, en complément différentiel de la pension alimentaire perçue (famille monoparentale)
```

Then replace the existing ASF simplification note (the bullet beginning
"Allocation de soutien familial — le droit est inféré...") so it no longer claims the
over-count, and reflects the différentielle and its remaining simplifications:

```yaml
    - >-
      Allocation de soutien familial — le droit est inféré du seul fait que la
      famille n'a qu'un parent (proxy MVP). L'ASF est versée en complément
      différentiel : la pension alimentaire perçue (ramenée au mois) est
      défalquée de l'ASF pleine (taux simple 0,422 BMAF), bornée à zéro. La
      comparaison est faite au niveau de la famille et non enfant par enfant ;
      la pension saisie est supposée être une pension pour enfant (une prestation
      compensatoire ne doit pas y figurer). Non modélisés : le taux majoré
      « orphelin de deux parents », le recouvrement de l'avance sur le parent
      débiteur (transfert CAF↔débiteur sans effet sur la famille), et le cas d'un
      parent défaillant au sein d'un couple (sous-estimation, l'éligibilité reste
      « parent unique »). Métropole uniquement.
```

(If a separate "shared 10 % abattement" or other ASF-adjacent note exists, leave it
untouched — only the ASF over-count note changes.)

- [ ] **Step 2: Add the changelog fragment**

```bash
printf '%s\n' "ASF is now paid as a différentiel: any pension alimentaire received is netted off the allocation de soutien familial, closing the previous over-count for single-parent families already receiving support." > changelog.d/added/asf-differentielle.md
```

(Confirm the category dir with `ls changelog.d/`; use `added/` as the taux-simple PR did.)

- [ ] **Step 3: Full suite + format**

```bash
make format
make test
.venv/Scripts/python.exe -m pytest tests/ -v
```

Expected: all green. No golden-master regeneration is expected — no tracked household
is a single-parent *receiver* with a pension, so every golden ASF value is unchanged.
If `pytest` reports a golden-master diff, STOP and investigate (it would mean a tracked
household unexpectedly changed) rather than blindly regenerating.

- [ ] **Step 4: Commit**

```bash
git add policyengine_fr/modelled_policies.yaml changelog.d/
git commit -m "docs(asf): record différentielle in modelled policies + changelog"
```

---

## Self-Review

- **Spec coverage:** §3 formula → Task 1 (Steps 3–4); §3 no-flag/no-double-count
  reasoning → encoded in the formula comment + the unchanged `revenu_disponible`; §4
  unit tests → Task 1 Step 1; §4 property invariants → Task 2; §4 oracle (guarded) →
  Task 3; §5 docstring + modelled_policies + changelog → Tasks 1 (docstring), 4; §6
  done-criteria → Task 4 Step 3. All spec sections mapped.
- **Placeholder scan:** every code/test step carries full content. The only runtime
  variable is the openfisca oracle `official` figure, explicitly guarded to skip.
- **Type/name consistency:** `allocation_soutien_familial`, `pensions_alimentaires_percues`,
  `period.this_year`, `famille.nb_persons(Famille.PARENT)`, `build_household(...,
  adult_pensions=[...])`, and the 2024-01 (188,18246) / 2024-04 (196,83768) figures are
  used identically across Tasks 1–4 and match the existing code they extend.
