# Spec 0007 — Multi-year parameterisation

**Status:** Draft · **Priority:** P2 (enabler) · **Depends on:** — · **Est.
effort:** 2–3 days (mostly data entry + oracle re-capture per year)

---

## 1. Problem

The model is parameterised for **2024 only** (coverage.md "Structural limits"). A
2025 or 2026 question cannot be answered, and the single-year assumption is baked
into tests (`period: 2024`), the oracle, and the golden master. Because
`policyengine-core` parameters are already **dated YAML**, most of the machinery
exists — the gap is *data* (each year's values) and *test/oracle coverage*.

## 2. Goal

Parameterise a second year end-to-end (proposed: **2025**, revenus 2025 / LF 2026)
so the model answers a multi-year question, and establish the **pattern** for
adding further years cheaply.

## 3. Design

### 3.1 Add each year's parameter values
Every dated parameter gets its new-year entry (the `values:` maps already support
this — e.g. `bmaf.yaml` already carries 2023-04 and 2024-04):

- **IR** barème + décote seuils + abattement plancher/plafond + plafond QF
  (indexed by the LF each year)
- **CSG/CRDS/cotisations** rates and the **PASS** (0004/0006)
- **Prestations** — BMAF (1 April revalorisation), RSA montant forfaitaire
  (1 April), AF plafonds
- Effective dates matter: benefits revalorise **1 April**, tax barèmes apply to
  the **whole income year** — keep the existing date conventions.

### 3.2 Parameterise the tests
- The YAML unit tests hard-code `period: 2024`. Add a **parallel year** for the
  headline cases (or a small matrix) rather than rewriting — keep 2024 as the
  regression baseline.
- **Golden master**: extend `CASES` or add a `year` axis; regenerate.
- **Oracle**: capture the same households for the new year from the DGFiP/CAF
  simulators (the long pole — needs a human/CoWork run), skip-until-captured.

### 3.3 A default year, made explicit
Introduce a single source of truth for "the current modelling year" (a constant /
small helper) so docs, tests and examples don't drift; today `2024` is implicit in
many places.

## 4. Files touched
- `parameters/**` — new-year `values:` entries across the tree
- `policyengine_fr/tests/**` — parallel-year cases for headline variables
- `tests/helpers.py`, `tests/test_golden_master.py` — a `year` axis
- `tests/fixtures/oracle_values.yaml` — new-year rows (skip-until-captured)
- `docs/coverage.md` — update "2024 only" → the years modelled; note the date
  conventions (barème = income year; prestations = 1 April)
- `modelled_policies.yaml` — record the parameterised years

## 5. Tests & acceptance
1. **Both years compute** — headline variables return sensible values for 2024 and
   the new year; the 2024 values are **unchanged** (regression).
2. **Revalorisation dates** — a benefit computed for a month before vs after
   1 April uses the right value (already exercised for BMAF; extend to RSA).
3. **Oracle** — at least the single-earner IR case matches the new year's DGFiP
   simulator.
4. `make test` + pytest green; ruff; doc-currency parity (the CLAUDE.md test count
   moves as parallel-year cases are added).

## 6. Risks
- **Oracle re-capture per year** is the recurring cost — each year needs a fresh
  simulator run for the anchor rows. Budget it; the skip-until-captured pattern
  keeps CI honest meanwhile.
- **Silent value drift** — mis-entering one year's bracket is easy; the
  statute-review gate (0003) and per-parameter transcription tests are the guard.
- **Don't retrofit every test** — keep 2024 as the stable baseline; add years
  additively.

## 7. Sequencing
Independent, but most valuable **after** 0004/0006 (whose rates are the most
year-sensitive), so a new year is added once against a stable parameter surface.
