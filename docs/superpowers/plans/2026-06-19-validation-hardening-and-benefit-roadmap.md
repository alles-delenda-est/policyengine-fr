# Validation Hardening + Benefit Roadmap — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the *already-modelled* social benefits (allocations familiales, CSG/CRDS) provably correct against independent sources and robust at their edges, then lay a staged, dependency-ordered roadmap for the *not-yet-modelled* ones (ASF → RSA → prime d'activité → APL).

**Architecture:** Two clearly separated bodies of work. **Part A (PR 1)** is test-only hardening of existing variables — no formula changes unless a test surfaces a real bug. **Part B** is new-benefit modelling, one benefit per branch/PR, sequenced by how much each depends on the others. ASF is specced concretely here as the next feature; RSA / prime d'activité / APL each get their *own* brainstorm + plan when reached (they are independent subsystems — see Scope Check).

**Tech stack:** PolicyEngine-core YAML tests (`policyengine-core test`), pytest property + golden-master tests under `tests/`, parameters/variables in mirrored `policyengine_fr/` trees. Independent oracles: openfisca-france (public codebase/params) and the official CAF/DGFiP simulators (browser capture, optionally via CoWork or claude-in-chrome).

---

## Branch & PR hygiene (read before starting)

- **Do NOT build on `fix/bareme-revenus-2024`** — that branch is a focused barème fix awaiting merge. Adding tests or features there violates the "no new work in an existing PR" rule.
- **PR 1 (Part A):** branch `test/harden-af-csg-validation`, off `main` (after the bareme fix merges, or off `main` and rebased). Test-only + docs.
- **PR 2 (Part B, Stage B1):** branch `feat/asf`, off `main`. New benefit.
- Stages B2–B4 (RSA, prime d'activité, APL) are roadmap only — each starts with its own `superpowers:brainstorming` then `superpowers:writing-plans` pass.

---

## File structure

**Part A — hardening (PR 1):**
- Modify: `policyengine_fr/tests/gov/cnaf/prestations/af/allocations_familiales.yaml` (add edge-case cases)
- Modify: `policyengine_fr/tests/gov/urssaf/csg_crds.yaml` (add edge-case cases)
- Modify: `tests/test_properties.py` (add AF + CSG invariants)
- Create: `tests/fixtures/oracle_values.yaml` (externally-sourced official numbers, with provenance)
- Create: `tests/test_oracle.py` (compare live Simulation to oracle fixture, skip rows not yet captured)
- Modify: `docs/cowork-validation-brief.md` (add the AF capture runbook so the oracle column can be filled)
- Modify: `policyengine_fr/variables/gov/cnaf/prestations/af/allocations_familiales.py` (docstring only — sharpen the N-2 simplification wording) and `policyengine_fr/modelled_policies.yaml` (make the simplification explicit)

**Part B — ASF (PR 2):**
- Create: `policyengine_fr/parameters/gov/cnaf/prestations/asf/montant_par_enfant.yaml`
- Create: `policyengine_fr/variables/gov/cnaf/prestations/asf/allocation_soutien_familial.py`
- Create: `policyengine_fr/tests/gov/cnaf/prestations/asf/allocation_soutien_familial.yaml`
- Modify: `policyengine_fr/variables/menage/revenu_disponible.py` (add ASF to the aggregate)
- Modify: `policyengine_fr/modelled_policies.yaml`, `tests/fixtures/golden_master.json` (regenerate), `changelog.d/`

---

## Reference values used below (all from in-repo parameters, revenus 2024)

- BMAF: **445,93 €** (2024-01 → 2024-03), **466,44 €** (from 2024-04).
- AF coefficients: 2 enfants **0,32** ; par enfant supplémentaire **0,41** ; majoration âge **0,16** à partir de **14 ans** ; limite d'âge enfant à charge **< 20 ans**.
- AF plafonds 2024: base n°1 **62 474**, base n°2 **87 430**, majoration **6 246 €/enfant**.
  - 2 enfants → plafond 1 = 62 474 + 2×6 246 = **74 966** ; plafond 2 = 87 430 + 2×6 246 = **99 922**.
- Modulation coefficients: **1 / 0,5 / 0,25**.
- `salaire_imposable` = `salaire_brut` × 0,90 (abattement 10 %); AF resources = Σ `salaire_imposable` (current-year MVP proxy for base ressources N-2).

---

# PART A — Harden existing benefits (PR 1)

## Task A1: AF — pin the BMAF mid-year revalorisation

**Files:**
- Test: `policyengine_fr/tests/gov/cnaf/prestations/af/allocations_familiales.yaml`

- [ ] **Step 1: Add a failing test for the April BMAF (466,44 €)**

Append this case:

```yaml
- name: Couple, deux enfants, avril 2024 (BMAF revalorisée à 466,44 €)
  absolute_error_margin: 0.01
  period: 2024-04
  input:
    individus:
      parent_1: {salaire_brut: 30_000}
      parent_2: {}
      enfant_1: {age: 8}
      enfant_2: {age: 10}
    familles:
      famille_1:
        parents: [parent_1, parent_2]
        enfants: [enfant_1, enfant_2]
  output:
    # 466,44 × 0,32 = 149,2608 (revalorisation du 1er avril)
    allocations_familiales: 149.2608
```

- [ ] **Step 2: Run it**

Run: `policyengine-core test -c policyengine_fr policyengine_fr/tests/gov/cnaf/prestations/af/allocations_familiales.yaml`
Expected: PASS (445,93 case stays at 142,6976; the new 2024-04 case gives 149,2608). If the April case fails, the BMAF date logic is wrong — stop and debug with `superpowers:systematic-debugging`.

- [ ] **Step 3: Commit**

```bash
git add policyengine_fr/tests/gov/cnaf/prestations/af/allocations_familiales.yaml
git commit -m "test(af): pin BMAF April revalorisation (445,93 vs 466,44)"
```

## Task A2: AF — age boundaries (newborn, 14 = majoration, 20 = drops out)

**Files:**
- Test: `policyengine_fr/tests/gov/cnaf/prestations/af/allocations_familiales.yaml`

- [ ] **Step 1: Add the boundary cases**

```yaml
- name: Enfant de 20 ans exclu (la limite est stricte < 20)
  absolute_error_margin: 0.01
  period: 2024-01
  input:
    individus:
      parent_1: {salaire_brut: 30_000}
      parent_2: {}
      enfant_1: {age: 8}
      enfant_2: {age: 10}
      enfant_3: {age: 20}
    familles:
      famille_1:
        parents: [parent_1, parent_2]
        enfants: [enfant_1, enfant_2, enfant_3]
  output:
    # l'aîné de 20 ans n'ouvre plus droit -> 2 enfants -> 445,93 × 0,32
    allocations_familiales: 142.6976

- name: Enfant de 19 ans encore à charge (limite non atteinte)
  absolute_error_margin: 0.01
  period: 2024-01
  input:
    individus:
      parent_1: {salaire_brut: 30_000}
      parent_2: {}
      enfant_1: {age: 8}
      enfant_2: {age: 10}
      enfant_3: {age: 19}
    familles:
      famille_1:
        parents: [parent_1, parent_2]
        enfants: [enfant_1, enfant_2, enfant_3]
  output:
    # 3 enfants, aucun >= 14 -> 445,93 × (0,32 + 0,41) = 325,5289
    allocations_familiales: 325.5289

- name: Majoration d'âge exactement à 14 ans (3 enfants, pas d'exclusion d'aîné)
  absolute_error_margin: 0.01
  period: 2024-01
  input:
    individus:
      parent_1: {salaire_brut: 30_000}
      parent_2: {}
      enfant_1: {age: 5}
      enfant_2: {age: 8}
      enfant_3: {age: 14}
    familles:
      famille_1:
        parents: [parent_1, parent_2]
        enfants: [enfant_1, enfant_2, enfant_3]
  output:
    # base 325,5289 + majoration 445,93 × 0,16 × 1 = 71,3488 -> 396,8777
    allocations_familiales: 396.8777

- name: Nouveau-né (âge 0) compte comme enfant à charge
  absolute_error_margin: 0.01
  period: 2024-01
  input:
    individus:
      parent_1: {salaire_brut: 30_000}
      parent_2: {}
      enfant_1: {age: 0}
      enfant_2: {age: 3}
    familles:
      famille_1:
        parents: [parent_1, parent_2]
        enfants: [enfant_1, enfant_2]
  output:
    allocations_familiales: 142.6976
```

- [ ] **Step 2: Run**

Run: `policyengine-core test -c policyengine_fr policyengine_fr/tests/gov/cnaf/prestations/af/allocations_familiales.yaml`
Expected: PASS. A failure on the age-20 case would mean the `age < af.age_limite` bound is off-by-one — debug before proceeding.

- [ ] **Step 3: Commit**

```bash
git add policyengine_fr/tests/gov/cnaf/prestations/af/allocations_familiales.yaml
git commit -m "test(af): age boundaries — newborn, 14 (majoration), 19/20 (charge limit)"
```

## Task A3: AF — plafond boundaries (bracket the modulation steps) + 4 enfants

**Files:**
- Test: `policyengine_fr/tests/gov/cnaf/prestations/af/allocations_familiales.yaml`

- [ ] **Step 1: Add bracketing cases**

Incomes chosen so `salaire_imposable = brut × 0,9` lands just under / just over each plafond (2 enfants: plafond 1 = 74 966, plafond 2 = 99 922):

```yaml
- name: Ressources juste sous le plafond 1 (taux plein)
  absolute_error_margin: 0.01
  period: 2024-01
  input:
    individus:
      parent_1: {salaire_brut: 83_000}   # imposable 74 700 < 74 966
      parent_2: {}
      enfant_1: {age: 8}
      enfant_2: {age: 10}
    familles:
      famille_1: {parents: [parent_1, parent_2], enfants: [enfant_1, enfant_2]}
  output:
    allocations_familiales: 142.6976

- name: Ressources juste au-dessus du plafond 1 (tranche 2, demi-montant)
  absolute_error_margin: 0.01
  period: 2024-01
  input:
    individus:
      parent_1: {salaire_brut: 83_500}   # imposable 75 150 > 74 966
      parent_2: {}
      enfant_1: {age: 8}
      enfant_2: {age: 10}
    familles:
      famille_1: {parents: [parent_1, parent_2], enfants: [enfant_1, enfant_2]}
  output:
    allocations_familiales: 71.3488

- name: Ressources juste au-dessus du plafond 2 (tranche 3, quart de montant)
  absolute_error_margin: 0.01
  period: 2024-01
  input:
    individus:
      parent_1: {salaire_brut: 111_100}  # imposable 99 990 > 99 922
      parent_2: {}
      enfant_1: {age: 8}
      enfant_2: {age: 10}
    familles:
      famille_1: {parents: [parent_1, parent_2], enfants: [enfant_1, enfant_2]}
  output:
    allocations_familiales: 35.6744

- name: Quatre enfants à charge, ressources sous plafond (base 1,14 BMAF)
  absolute_error_margin: 0.01
  period: 2024-01
  input:
    individus:
      parent_1: {salaire_brut: 30_000}
      parent_2: {}
      enfant_1: {age: 2}
      enfant_2: {age: 6}
      enfant_3: {age: 9}
      enfant_4: {age: 11}
    familles:
      famille_1: {parents: [parent_1, parent_2], enfants: [enfant_1, enfant_2, enfant_3, enfant_4]}
  output:
    # base 445,93 × (0,32 + 0,41 × 2) = 445,93 × 1,14 = 508,3602 ; aucune majoration d'âge
    allocations_familiales: 508.3602
```

- [ ] **Step 2: Run**

Run: `policyengine-core test -c policyengine_fr policyengine_fr/tests/gov/cnaf/prestations/af/allocations_familiales.yaml`
Expected: PASS. These pin the `<=` semantics of the modulation thresholds and the 0,41-per-extra-child base.

- [ ] **Step 3: Commit**

```bash
git add policyengine_fr/tests/gov/cnaf/prestations/af/allocations_familiales.yaml
git commit -m "test(af): bracket modulation plafonds + 4-children base amount"
```

## Task A4: CSG/CRDS — high salary + decomposition regression

**Files:**
- Test: `policyengine_fr/tests/gov/urssaf/csg_crds.yaml`

- [ ] **Step 1: Add cases**

```yaml
- name: Salaire brut élevé 200 000 € — pas de plafonnement (CSG/CRDS déplafonnées)
  absolute_error_margin: 0.01
  period: 2024
  input:
    salaire_brut: 200_000
  output:
    assiette_csg_crds_salaire: 196_500   # 200 000 × 0,9825
    csg_deductible: 13_362.00            # × 0,068
    csg_imposable: 4_716.00              # × 0,024
    csg: 18_078.00                       # × 0,092
    crds: 982.50                         # × 0,005

- name: Décomposition CSG — déductible + imposable = CSG totale
  absolute_error_margin: 0.01
  period: 2024
  input:
    salaire_brut: 37_000
  output:
    # 37 000 × 0,9825 = 36 352,50 ; 0,068 + 0,024 = 0,092
    csg_deductible: 2_471.97
    csg_imposable: 872.46
    csg: 3_344.43
```

- [ ] **Step 2: Run**

Run: `policyengine-core test -c policyengine_fr policyengine_fr/tests/gov/urssaf/csg_crds.yaml`
Expected: PASS.

- [ ] **Step 3: Commit**

```bash
git add policyengine_fr/tests/gov/urssaf/csg_crds.yaml
git commit -m "test(csg): déplafonnement at 200k + déductible/imposable decomposition"
```

## Task A5: Property invariants for AF and CSG

**Files:**
- Modify: `tests/test_properties.py`

- [ ] **Step 1: Read the existing property tests to match style**

Run: open `tests/test_properties.py` and note how a `Simulation` is built and which helper in `tests/helpers.py` constructs households. Reuse that helper; do not hand-roll simulation setup.

- [ ] **Step 2: Add invariants**

Add property tests asserting, for randomised/representative inputs:

```python
# AF is never negative.
# AF is zero whenever the family has fewer than 2 children under 20.
# AF is (weakly) monotonically NON-INCREASING in family resources
#   (taux plein >= demi >= quart for the same household composition).
# CSG identity: csg == csg_deductible + csg_imposable (within 1e-6).
# Assiette identity: assiette_csg_crds_salaire == salaire_brut * 0.9825 (within 1e-6).
```

Implement each as a separate `def test_...` using the existing helper. Use a small grid of incomes (e.g. 0, 20_000, 80_000, 120_000, 200_000) and child counts (0,1,2,3,4) rather than a fuzzing library, to match the repo's deterministic style.

- [ ] **Step 3: Run**

Run: `pytest tests/test_properties.py -v`
Expected: PASS. A failure of the monotonicity property would reveal a real modulation bug — debug, don't weaken the property.

- [ ] **Step 4: Commit**

```bash
git add tests/test_properties.py
git commit -m "test(properties): AF non-negativity/monotonicity + CSG identities"
```

## Task A6: Independent-oracle harness (the piece in-repo tests cannot be)

**Files:**
- Create: `tests/fixtures/oracle_values.yaml`
- Create: `tests/test_oracle.py`
- Modify: `docs/cowork-validation-brief.md`

- [ ] **Step 1: Create the oracle fixture with provenance, official column initially empty**

```yaml
# Official reference values captured from government / independent simulators.
# Each row records WHERE the number came from so it is independent of our code.
# Fill `official` by running the named oracle; leave null until captured.
meta:
  ir_oracle: "DGFiP simulateur simplifié, revenus 2024"
  ir_url: "https://simulateur-ir-ifi.impots.gouv.fr/calcul_impot/2025/simplifie/index.htm"
  af_oracle: "CAF estimateur / mesdroitssociaux.gouv.fr"
  af_url: "https://www.mesdroitssociaux.gouv.fr"
households:
  - id: single_30k
    inputs: {situation: celibataire, parent_isole: false, enfants: [], salaires: [30000]}
    variable: impot_revenu
    period: 2024
    model: 1587.99
    official: null
    captured_on: null
  - id: couple_60k_2children
    inputs: {situation: maries, parent_isole: false, enfants: [10, 16], salaires: [60000, 0]}
    variable: impot_revenu
    period: 2024
    model: 1647.05
    official: null
    captured_on: null
  - id: couple_60k_2children_af
    inputs: {situation: maries, parent_isole: false, enfants: [10, 16], salaires: [60000, 0]}
    variable: allocations_familiales   # compare model annual vs 12 × CAF monthly
    period: 2024-01
    model: null      # fill from golden_master at scaffold time
    official: null
    captured_on: null
```

- [ ] **Step 2: Create the comparison test that skips uncaptured rows**

```python
import yaml, pathlib, pytest

FIX = pathlib.Path(__file__).parent / "fixtures" / "oracle_values.yaml"

def _rows():
    data = yaml.safe_load(FIX.read_text(encoding="utf-8"))
    return data["households"]

@pytest.mark.parametrize("row", _rows(), ids=lambda r: r["id"])
def test_model_matches_official_oracle(row):
    if row.get("official") is None:
        pytest.skip(f"{row['id']}: official value not yet captured")
    # tolerance: 5 € for IR, 1 € for AF monthly
    tol = 5.0 if row["variable"] == "impot_revenu" else 1.0
    assert abs(row["model"] - row["official"]) <= tol, (
        f"{row['id']} {row['variable']}: model {row['model']} vs official "
        f"{row['official']} (Δ {row['model'] - row['official']:.2f})"
    )
```

- [ ] **Step 3: Run (rows skip until captured)**

Run: `pytest tests/test_oracle.py -v`
Expected: all rows SKIPPED with "official value not yet captured" — harness is wired, no false green.

- [ ] **Step 4: Add the AF capture runbook to the CoWork brief**

In `docs/cowork-validation-brief.md`, add an "### AF capture (CAF estimateur)" subsection mirroring the IR runbook: exact household inputs from the battery, where to read the monthly amount, and "record 12× monthly into `tests/fixtures/oracle_values.yaml` `official`, set `captured_on`". Note the N-2 caveat already documented.

- [ ] **Step 5: Commit**

```bash
git add tests/fixtures/oracle_values.yaml tests/test_oracle.py docs/cowork-validation-brief.md
git commit -m "test(oracle): scaffold independent-oracle harness + AF capture runbook"
```

> **Execution note:** the official numbers can be captured in this session with the claude-in-chrome browser tools (drive the DGFiP + CAF simulators for the battery), or handed to CoWork. Capturing turns the skipped rows green and is the genuinely independent check.

## Task A7: Make the resource-base simplification explicit

**Files:**
- Modify: `policyengine_fr/variables/gov/cnaf/prestations/af/allocations_familiales.py` (docstring)
- Modify: `policyengine_fr/modelled_policies.yaml`

- [ ] **Step 1: Sharpen the docstring** — state plainly that AF modulation uses **current-year `salaire_imposable`** as a proxy for the legal **base ressources N-2** (revenu net catégoriel of year N-2), and that this diverges for any household whose income changed year-on-year.

- [ ] **Step 2: Record it in `modelled_policies.yaml`** under a `simplifications:` note for allocations familiales (so the boundary is machine-discoverable, per the reviewer-agent gate's "silent scope-narrowing" check).

- [ ] **Step 3: Commit**

```bash
git add policyengine_fr/variables/gov/cnaf/prestations/af/allocations_familiales.py policyengine_fr/modelled_policies.yaml
git commit -m "docs(af): make base-ressources N-2 simplification explicit"
```

## Task A8: Full suite + changelog, open PR 1

- [ ] **Step 1:** `make format`
- [ ] **Step 2:** `make test` — expect all green (existing 46 + new AF/CSG cases).
- [ ] **Step 3:** `pytest tests/ -v` — properties + golden master + oracle (skips) green.
- [ ] **Step 4:** add a `changelog.d/` fragment (towncrier; never edit CHANGELOG.md by hand): "Hardened AF & CSG/CRDS test coverage; added independent-oracle harness."
- [ ] **Step 5:** push `test/harden-af-csg-validation`, open PR. Use `superpowers:requesting-code-review` before merge.

---

# PART B — New-benefit roadmap (one PR each, in this order)

Ordered by dependency and modelling cost. **Each stage past B1 starts with its own `superpowers:brainstorming` + `superpowers:writing-plans`** — they are independent subsystems and must not be jammed into one mega-PR.

## Stage B1 (PR 2): ASF — Allocation de soutien familial *(do first: simplest, high synergy)*

**Why first:** flat per-child amount for a child deprived of one/both parents' support — typically the single-parent (`parent_isole`, already an input) case. No resource test, no barème. Exercises the same Famille/enfant plumbing as AF, so it is low-risk and immediately useful for single-parent households.

**Legal basis:** CSS art. L523-1 s. ; montant = a fixed fraction of BMAF per child (taux "orphelin d'un parent"). Confirm the exact 2024 coefficient/amount from service-public (F815) during brainstorming — do **not** hardcode from memory.

**File skeleton (TDD, fill exact numbers from the oracle during the plan):**
- `policyengine_fr/parameters/gov/cnaf/prestations/asf/montant_par_enfant.yaml` — dated amount, legal `reference`.
- `policyengine_fr/variables/gov/cnaf/prestations/asf/allocation_soutien_familial.py` — `entity = Famille`, `MONTH`; eligible children = enfants à charge of a `parent_isole` family (MVP scope); amount = `nb_enfants_eligibles × montant_par_enfant`. Docstring must state the MVP scope (parent isolé only; orphelin-de-deux-parents taux and recouvrement not modelled).
- `policyengine_fr/tests/gov/cnaf/prestations/asf/allocation_soutien_familial.yaml` — single parent 1 child, single parent 2 children, couple (→ 0), childless (→ 0).
- Wire into `revenu_disponible.py`; add to `modelled_policies.yaml`; regenerate `golden_master.json`; changelog fragment.

**Definition of done:** new YAML tests pass; ASF appears in `revenu_disponible`; an oracle row for a single-parent household added to `oracle_values.yaml`.

## Stage B2: RSA — Revenu de Solidarité Active *(foundational for prime d'activité)*

**Why before prime d'activité:** prime d'activité reuses RSA's montant forfaitaire, forfait logement, and resource base. Build the shared machinery once.

**Scope to settle in brainstorming:** montant forfaitaire by family configuration, majoration isolement, forfait logement, and the resource base (which income sources count). This needs a real resource-aggregation design and is **not** a test-only task — its own plan.

## Stage B3: Prime d'activité *(depends on B2)*

Bonification individuelle + family resource test on top of the RSA base. Own brainstorm + plan; do not start before RSA's resource base exists.

## Stage B4: APL — Aide Personnalisée au Logement *(hardest, last)*

**Why last:** zone-based loyer plafonds, participation personnelle, RLS (réduction de loyer de solidarité), and a non-trivial barème — the most complex benefit and the least reusable. Needs its own brainstorm, a parameter-sourcing research pass (zones, plafonds), and a dedicated plan. Note for clarity: APL is a **logement** benefit (CNAF/logement branch), not a sécurité-sociale contribution — keep it in its own parameter subtree.

---

## Self-review

- **Spec coverage:** "Independent oracle values" → A6 (+ A8 capture note). "More edge cases" → A1–A4. "Modulation/plafond accuracy" → A3 + A5 monotonicity + A7 (N-2 documentation). "Plan new (APL etc.)" → B1–B4, dependency-ordered, each its own PR. All four of Patrick's asks are mapped.
- **Placeholder scan:** Part A tasks carry exact inputs and computed expected values. Part B intentionally stops at skeleton/scope for B2–B4 because each is an independent subsystem requiring its own plan (Scope Check) — B1 (ASF) is the only new benefit specced to file level, and even its exact coefficient is flagged for oracle confirmation rather than guessed.
- **Consistency:** variable/entity names (`allocations_familiales`, `allocation_soutien_familial`, `Famille`, `salaire_imposable`) match the existing tree; oracle fixture keys (`model`/`official`/`captured_on`) are used identically in fixture and `test_oracle.py`.
