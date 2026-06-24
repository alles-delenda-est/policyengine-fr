# ASF différentielle — Design Spec

> Status: **approved design**, ready for an implementation plan (superpowers:writing-plans).
> Builds on the ASF taux-simple MVP (`docs/superpowers/specs/2026-06-22-asf-design.md`)
> and the pension-alimentaire inputs added by PR #23.
> One change, one branch (`feat/asf-differentielle`), one PR — off `main`.

## 1. Problem

The ASF taux-simple MVP pays the **full** allocation de soutien familial to every
single-parent famille, ignoring any pension alimentaire already received. This
**over-counts**: a family already receiving a pension alimentaire equal to or above
the ASF floor should receive little or no ASF. The CAF in fact pays only a
*complément différentiel* topping the pension up to the ASF level (CSS art. L523-1,
L581-2, R523-5).

PR #23 added the input `pensions_alimentaires_percues` (Individu, YEAR, EUR) and
already counts it as cash-in to `revenu_disponible`. This spec nets that pension off
the ASF amount, closing the over-count.

## 2. Scope

**In scope:** the différentielle netting — ASF amount only.
**Unchanged:** eligibility (`famille` with exactly one parent), the 0,422 BMAF
per-child rate, the MONTH period, and `revenu_disponible` (no edit needed there).
**No new parameter, no new input.**

## 3. Approach

Only the amount formula in
`policyengine_fr/variables/gov/cnaf/prestations/asf/allocation_soutien_familial.py`
changes. The pension received by the famille (summed over its members, annual ÷ 12)
is subtracted from the full ASF, floored at zero:

```python
def formula(famille, period, parameters):
    asf = parameters(period).gov.cnaf.prestations.asf
    bmaf = parameters(period).gov.cnaf.bmaf
    age_limite = parameters(period).gov.cnaf.prestations.af.age_limite

    age = famille.members("age", period)
    est_enfant = famille.members.has_role(Famille.ENFANT)
    ouvre_droit = est_enfant & (age >= 0) & (age < age_limite)
    nb_enfants = famille.sum(ouvre_droit)

    parent_unique = famille.nb_persons(Famille.PARENT) == 1

    asf_pleine = bmaf * asf.taux_orphelin_un_parent * nb_enfants

    # Pension alimentaire perçue par la famille, ramenée au mois (base annuelle
    # lue via period.this_year, comme la modulation AF lit ses ressources).
    pension_mensuelle = (
        famille.sum(famille.members("pensions_alimentaires_percues", period.this_year))
        / 12
    )

    # Complément différentiel: l'ASF ne verse que ce qui manque pour atteindre
    # le plancher ASF (CSS art. L523-1, L581-2). Borné à zéro.
    montant = max_(asf_pleine - pension_mensuelle, 0)
    return where(parent_unique, montant, 0)
```

### Why the formula needs no legal-case flag

French law distinguishes **ASF non-recouvrable** (absent parent cannot pay —
deceased, unknown) from **ASF différentielle** (parent should pay but pays
partially/nothing). The cash the family receives is identical in both:
`max(ASF_pleine − pension, 0)`. With no pension entered (pension = 0) the family
receives full ASF — covering the non-recouvrable case automatically. The only
difference between the two legal cases is *recouvrement* (the CAF recovering the
advance from the debtor), a CAF↔debtor transfer that never touches the beneficiary
family's disposable income. So no flag distinguishing the cases is needed.

### Coherence with revenu_disponible (no double-count)

`revenu_disponible` already adds the pension as cash-in (PR #23) and already adds
ASF. After this change the family nets:

```
pension + max(ASF_pleine − pension, 0) = max(ASF_pleine, pension)
```

— correct, and not a double-count, because the pension counted in
`revenu_disponible` is the same quantity netted inside ASF. `revenu_disponible`
itself is not edited.

Note the netting is applied **per month** (ASF is a MONTH variable, annualised via
`ADD`), so the annual aggregate is `Σ_month max(ASF_pleine_month − pension/12, 0)`,
not `max(Σ ASF_pleine, Σ pension)`. The two differ only in the narrow band where the
monthly pension straddles the ASF floor across the 1-April BMAF revalorisation; the
per-month behaviour is the more faithful one (the CAF assesses ASF monthly).

## 4. Tests

### Unit (`tests/gov/cnaf/prestations/asf/allocation_soutien_familial.yaml`)

The new pension cases use **period 2024-01** (ASF/child = 0,422 × 445,93 =
188,18246), not April: setting the YEAR `pensions_alimentaires_percues` input on a
February-or-later monthly test period crashes the policyengine-core test loader
(`ValueError: Expected a period; got: 'year'`); January is safe. (The pre-existing
no-pension cases already pin the April BMAF revalorisation, so April coverage is not
lost.)

| Case | Pension (annual €) | Expected ASF/mo (2024-01) |
|---|---|---|
| 1 parent, 1 child, **partial** | 1 200 (100/mo) | 88,18246 |
| 1 parent, 1 child, **≥ ASF** | 3 600 (300/mo) | 0 |
| 1 parent, **2 children**, partial | 2 400 (200/mo) | 176,36492 |
| **Couple**, pension present | 2 400 | 0 |

The pre-existing no-pension cases stay green (the netting is a no-op when
pension = 0), so they double as regressions covering the deceased/unknown-parent
case. Property tests (below) cover the April BMAF (2024-04, ASF/child 196,83768) via
the Python `Simulation` API, which handles YEAR inputs at any month.

### Property (`tests/test_properties.py`)

- ASF is (weakly) **non-increasing** in the pension received.
- **Floor guarantee:** for an eligible (single-parent) famille,
  `ASF_versée + min(pension/12, ASF_pleine) == ASF_pleine` (within float32 tol).

### Independent oracle (guarded)

openfisca-france models the différentielle. Extend
`tests/oracle/compute_af_openfisca.py` to feed a partial pension alimentaire and
compare its `asf`; add one row to `tests/fixtures/oracle_values.yaml`.
**Anti-rabbit-hole guard:** if openfisca's `asf` netting cannot be triggered
cleanly within a short timebox, record the row `official: null` (so `test_oracle.py`
skips it, never false-green) and note the reason — do not fight the oracle.

## 5. Documentation

- **ASF variable docstring** — remove the "ASF différentielle non modélisée /
  sur-estimation possible" limitation (now modelled); keep taux majoré, under-count,
  recouvrement, métropole-only.
- **`modelled_policies.yaml`** — replace the ASF over-count note with the new
  reality and its remaining simplifications (below). Update the `modelled` line to
  mention the différentielle.
- **Changelog** — towncrier fragment under `changelog.d/added/`.

### Deferred (documented honestly)

- **Family-total, not per-child** netting (chosen): slightly off when pensions are
  unevenly distributed across children.
- **Pension input treated as child support**: a *prestation compensatoire* (spousal
  support) must not be entered in `pensions_alimentaires_percues` for ASF purposes,
  since netting it against ASF would be wrong.
- **Recouvrement** (CAF ↔ debtor parent): out of scope; doesn't affect the family.
- **Under-count**: a defaulting parent *inside a couple* still isn't captured
  (eligibility unchanged).
- **Taux majoré** (orphelin de deux parents): still deferred.

## 6. Definition of done

New unit + property tests pass; the existing no-pension ASF cases stay green;
`make test` and `pytest tests/` green; ruff clean; golden master regenerated if any
tracked household gains a pension; ASF différentielle oracle row added (captured or
skipped per the guard); docstring + `modelled_policies.yaml` + changelog updated; PR
opened off `main`.
