# ASF — Allocation de soutien familial (MVP, taux simple) — Design Spec

> Status: **approved design**, ready for an implementation plan (superpowers:writing-plans).
> Scope: Stage B1 of `docs/superpowers/plans/2026-06-19-validation-hardening-and-benefit-roadmap.md`.
> One benefit, one branch (`feat/asf`), one PR — off `main`.

## 1. What ASF is

The **allocation de soutien familial** (ASF) is a CAF/MSA family benefit paid for a
child who is *deprived of the support of one (or both) of its parents* — in
practice the everyday case is the **single-parent** household raising a child
whose other parent is absent. Unlike the allocations familiales it is paid **from
the first child** and is **not means-tested** (taux simple). Legal basis:
**CSS art. L523-1 et s.**; amount set by **CSS art. R523-7**.

## 2. The number (researched, not guessed)

ASF **taux simple** (child deprived of *one* parent's support) =
**0,422 × BMAF per eligible child per month**, in force since the décret of
27 Oct 2022. Source: openfisca-france parameter
`prestations_sociales.prestations_familiales.education_presence_parentale.asf.montant_asf.orphelin_assimile_seul_parent`
(unit BMAF), citing:

- **Article R523-7 CSS** — https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000046498993
- **Décret n° 2022-1370 du 27/10/2022, art. 1** — https://www.legifrance.gouv.fr/jorf/id/JORFTEXT000046497145

Reusing the in-repo BMAF parameter (445,93 € to 2024‑03, 466,44 € from 2024‑04),
this gives, for one eligible child in 2024:

| Period      | BMAF    | ASF/month (× 0,422)         |
|-------------|---------|-----------------------------|
| Jan–Mar 24  | 445,93  | **188,18 €**  (188,18246)   |
| Apr–Dec 24  | 466,44  | **196,84 €**  (196,83768)   |

These exactly match openfisca-france's computed `asf`, so the parameter is
independently corroborated before a line of formula is written.

## 3. Architecture (mirrors `allocations_familiales`)

**New parameter** — `policyengine_fr/parameters/gov/cnaf/prestations/asf/taux_orphelin_un_parent.yaml`

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

Named `taux_orphelin_un_parent` (not a generic `montant_par_enfant`) precisely so
the **deferred** taux majoré (orphelin *de deux* parents) has an obvious sibling
slot later. Reuses the existing `gov.cnaf.bmaf` parameter — no duplication.

**New variable** — `policyengine_fr/variables/gov/cnaf/prestations/asf/allocation_soutien_familial.py`

- `entity = Famille`, `definition_period = MONTH`, `unit = EUR`.
- **Eligibility:** the famille has exactly one parent —
  `famille.nb_persons(Famille.PARENT) == 1`. No resource test (taux simple is not
  means-tested).
- **Eligible children:** à-charge children under the family-benefit age limit —
  the *same* `gov.cnaf.prestations.af.age_limite` (< 20) AF already uses, so the
  two benefits agree on "enfant à charge" (one source of truth; CSS art. R512-2).
- **Amount:** `bmaf × taux_orphelin_un_parent × nb_enfants_eligibles` when the
  famille has one parent, else `0`. Paid from the first child.

**Aggregate** — wire ASF into `policyengine_fr/variables/menage/revenu_disponible.py`
using the identical group-distribution + `ADD`-annualisation pattern used for
`allocations_familiales` (so a famille is counted exactly once across the ménage).

## 4. Explicit limitations (documented in docstring AND modelled_policies.yaml)

The eligibility proxy "famille with one parent" captures the core single-parent
case but knowingly departs from the full statute. To be stated plainly:

- **Taux majoré** (orphelin *de deux* parents) — not modelled; needs a second
  coefficient (openfisca's `orphelin_assimile_deux_parents`) + an orphan flag.
  The parameter name leaves room for it.
- **ASF différentielle / recouvrement** — when the absent parent pays a *partial*
  pension alimentaire, real ASF tops it up to the ASF level and the CAF recovers
  it from the defaulting parent. Not modelled (no pension-alimentaire input). So
  the model **over-counts**: it pays full simple ASF to any single-parent famille,
  even one already receiving a full pension alimentaire.
- **Non-paying parent within a couple** — a child whose second parent fails to pay
  support can open ASF even in a two-parent famille; the 1-parent proxy **misses**
  this (under-counts).
- **Loss on re-partnering** — a single parent who re-partners normally loses simple
  ASF; modelled correctly only insofar as the famille then has two parents.
- Métropole only; no garde alternée split.

Mitigation path for a later PR: add a `pension_alimentaire_recue` input and an
orphan flag, then model the différentielle and the taux majoré.

## 5. Tests

YAML unit tests — `policyengine_fr/tests/gov/cnaf/prestations/asf/allocation_soutien_familial.yaml`:

- Single parent, 1 child, **2024‑01** → **188,1825** (0,422 × 445,93).
- Single parent, 1 child, **2024‑04** → **196,8377** (BMAF revalorisation).
- Single parent, 2 children, **2024‑04** → **393,6754** (per-child, from the first).
- **Couple**, 2 children → **0** (two parents → not eligible).
- Single parent, **no child** → **0**.

(If the policyengine-core YEAR-on-monthly-period storage bug bites again when a
`salaire_brut` is set on a non-January monthly test period, omit income from those
cases — ASF has no resource test, so resources are irrelevant to the expected
value. Document if so.)

Property test (`tests/test_properties.py`): ASF ≥ 0 always; ASF == 0 whenever the
famille has ≠ 1 parent; ASF scales linearly with eligible-child count.

Independent oracle: add one single-parent ASF row to
`tests/fixtures/oracle_values.yaml` sourced from openfisca-france's `asf`
(extend `tests/oracle/compute_af_openfisca.py` to also emit `asf`), keeping the
"validated against an independent codebase" guarantee.

## 6. Definition of done

New YAML + property tests pass; `make test` and `pytest tests/` green; ruff clean;
ASF present in `revenu_disponible`; `modelled_policies.yaml` updated (moved out of
not_modelled, with the simplifications note); golden master regenerated; an ASF
oracle row added; towncrier changelog fragment; PR opened off `main`.
