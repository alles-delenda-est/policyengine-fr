# Spec 0001 — Resolve the `salaire_brut` input semantics

**Status:** Draft · **Priority:** P0 (blocker for every means-tested benefit) ·
**Source:** external review BUGS.md B1+B2, PROPOSED_NEXT_STEPS #1 ·
**Est. effort:** 2–3 days (engine + params + oracle re-capture + tests)

---

## 1. Problem

The single salary input `salaire_brut` is read under **two incompatible
conventions**:

- the **income-tax chain** treats it as *declared salary* (case 1AJ — already
  net of employee social contributions and of deductible CSG). This is the
  convention under which the model was validated to the euro against the DGFiP
  simulator (`tests/fixtures/oracle_values.yaml`, 10 IR rows).
- the **CSG/CRDS chain** (`variables/gov/urssaf/assiette_csg_crds_salaire.py`)
  treats it as *gross salary* — it applies the 1.75 % assiette abatement of
  CSS art. L136-2, which is defined on gross pay.

These differ by ~20–25 % on a real payslip. `revenu_disponible` subtracts IR
**and** CSG/CRDS from the *same* number, so it is the disposable income of no
real household under either reading. Additionally, `csg_deductible` is computed
but never deducted from `revenu_net_imposable` (CGI art. 154 quinquies) — which
is *correct* under the declared-salary reading and *wrong* under the gross one.

Spec 0000-scope (this repo's `modelled_policies.yaml`) now **discloses** the
inconsistency (shipped in PR #25). This spec **resolves** it.

Why P0: RSA, prime d'activité and APL (the roadmap) are all means-tested on
net/declared-income concepts. Building them on an input that means "gross" to
one half of the model and "declared" to the other bakes the inconsistency into
every future benefit, and every oracle row captured in between becomes invalid
once the convention is fixed.

## 2. Decision — adopt **true-gross** semantics

Two options were on the table (review §Fix direction). We adopt **option (b),
true gross**, because it keeps the working CSG/CRDS code, converges on how
openfisca-france models France, and is the only convention that can express a
real payslip (needed for means-tested benefits).

- Input `salaire_brut` becomes **true gross salary** (before employee
  contributions), matching its name and the existing CSG/CRDS assiette.
- Add a **flat-rate employee-cotisations layer** producing `salaire_net` and
  the declared/taxable salary the IR chain consumes.
- Deduct `csg_deductible` in `revenu_net_imposable`.
- Re-capture the DGFiP oracle by entering the **derived** declared salary (1AJ)
  into the simulator, not the raw gross.

Rejected — option (a) (rename input to `salaire_declare`, drop CSG until
cotisations exist): honest but throws away the working CSG/CRDS code and still
cannot represent gross→net for benefits.

## 3. Design

### 3.1 New parameter: employee contribution rate

`parameters/gov/urssaf/cotisations_salariales/taux_effectif.yaml` — a single
flat effective rate approximating the employee-side wedge between gross and
declared salary for a private-sector non-cadre (health, vieillesse plafonnée +
déplafonnée, chômage via the 2018 CSG-swap = 0, retraite complémentaire
AGIRC-ARRCO T1). Target ≈ **0.22** (22 %) of gross for 2024; cite the URSSAF
barème and a worked payslip. This is explicitly an MVP flat rate — dispersion
by cadre status / PASS bracket is a documented simplification, not silence.

> Note: CSG/CRDS (9.2 % + 0.5 % on 98.25 %) are levied *separately* and must
> NOT be double-counted inside this rate. The rate covers only the "cotisations
> sociales salariales" line, i.e. the non-CSG wedge.

### 3.2 New variable: `salaire_net_imposable` (declared salary, 1AJ)

`variables/gov/dgfip/ir/salaire_declare.py` (entity Individu, YEAR):

```
salaire_declare = salaire_brut
                  − cotisations_salariales            # §3.1 rate × brut
                  − csg_deductible                    # 6.8 % × 98.25 % × brut
```

This is the amount a taxpayer copies into box 1AJ. `salaire_imposable`
(the existing 10 % abatement variable) must now take **`salaire_declare`** as
its base instead of `salaire_brut`.

### 3.3 `revenu_net_imposable` — deduct CSG déductible

Today `revenu_net_imposable = salaires_imposables + pensions_percues −
pensions_versees`, floored at 0. Under true gross the CSG deduction is already
folded into `salaire_declare` (§3.2), so **do not** subtract it again here — the
deduction happens exactly once, at the salary→declared step. Add an assertion
test that `csg_deductible` is reflected once and only once (see §5).

### 3.4 `cotisations_salariales` variable

`variables/gov/urssaf/cotisations_salariales.py` (Individu, YEAR):
`cotisations_salariales = salaire_brut × taux_effectif`. Surface it in
`revenu_disponible`'s documentation as a modelled deduction.

### 3.5 `revenu_disponible` update

New identity (documented in the docstring, replacing the current one):

```
revenu_disponible = salaire_brut
                    − cotisations_salariales
                    − csg − crds
                    − impot_revenu
                    + pensions_alimentaires_percues − pensions_alimentaires_versees
                    + allocations_familiales + allocation_soutien_familial
```

`salaire_brut − cotisations_salariales − csg − crds` is now genuine take-home
pay (net of the modelled wedge), so the coverage.md caveat "net here is not
take-home pay" is downgraded to "net of the flat-rate cotisations approximation".

## 4. Files touched

| File | Change |
|---|---|
| `parameters/gov/urssaf/cotisations_salariales/taux_effectif.yaml` | **new** — flat 2024 rate + reference |
| `variables/gov/urssaf/cotisations_salariales.py` | **new** — brut × rate |
| `variables/gov/dgfip/ir/salaire_declare.py` | **new** — brut − cotisations − csg_deductible |
| `variables/gov/dgfip/ir/salaire_imposable.py` | base becomes `salaire_declare` |
| `variables/input/salaire_brut.py` | docstring: now true gross; drop the dual-convention warning |
| `variables/menage/revenu_disponible.py` | subtract `cotisations_salariales`; new identity in docstring |
| `modelled_policies.yaml` / `docs/coverage.md` | replace the two disclosure entries (0001/0002) with the flat-cotisations simplification |
| `tests/fixtures/oracle_values.yaml` | **re-capture** all 10 IR rows on derived 1AJ |
| `tests/gov/...` YAML tests | update expected salaire_imposable/IR; add cotisations + salaire_declare tests |
| `changelog.d/` | fragment |

## 5. Tests & acceptance criteria

1. **Payslip identity (property test).** For random `salaire_brut`:
   `salaire_brut − cotisations_salariales − csg − crds ≈ take-home`, and
   `salaire_declare = salaire_brut − cotisations_salariales − csg_deductible`.
   Add to `tests/test_properties.py`.
2. **CSG deducted exactly once.** `impot_revenu(base with CSG folded in) <
   impot_revenu(hypothetical base without)` by the expected amount; assert the
   deduction is not applied a second time in `revenu_net_imposable`.
3. **Oracle re-capture.** Re-drive the DGFiP simulator (revenus 2024, modèle
   simplifié) entering the *derived* `salaire_declare` for each of the 10
   households; all rows match within €5. Update `captured_on`. Document in the
   fixture header which salary concept was entered (the omission of this note is
   how B2 slipped through).
4. **Golden master** regenerated; diff reviewed and justified (IR unchanged if
   the derived 1AJ equals the previously-entered number; CSG/CRDS now on true
   gross so they change — expected).
5. `make test` + `pytest tests/` green; ruff clean.

## 6. Risks & open questions

- **Flat-rate accuracy.** A single 22 % rate is wrong for cadres, part-timers,
  and high earners (PASS ceilings). Acceptable for the MVP *if disclosed*; the
  follow-up is a bracketed rate. Do not let scope creep here block the fix.
- **Oracle drift.** If the previously-entered oracle numbers were the *gross*
  values (not declared), the re-capture will move the IR rows. Verify against
  the 2026-06-22 capture notes before assuming "no change".
- **CoWork brief** (`docs/cowork-validation-brief.md`) must be updated to state
  the 1AJ concept explicitly (PENDING #5).

## 7. Sequencing

Do this **before** Spec 0002 (RSA) and any other means-tested benefit. Ships as
one PR; the oracle re-capture is the long pole and needs a human/CoWork run of
the DGFiP simulator.
