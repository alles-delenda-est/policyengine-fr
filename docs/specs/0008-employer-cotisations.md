# Spec 0008 — Employer social contributions (cotisations patronales) + réduction générale

**Status:** Draft · **Priority:** P2 · **Depends on:** Spec 0001 (gross salary),
Spec 0004 (employee side + PASS) · **Est. effort:** 3–4 days

---

## 1. Problem

The model stops at the **employee** side: gross salary → declared/net. It has no
notion of the **employer** cost of labour (super-brut = brut + cotisations
patronales), so it cannot answer:

- **coût du travail** / labour-cost questions (the gap between what an employer
  pays and what an employee receives),
- the effect of the **réduction générale des cotisations patronales** (ex-Fillon)
  — the dégressive low-wage relief up to **1,6 SMIC** — which is the "SMIC
  exonération" out of scope in spec 0004 (that spec is employee-only and points
  here),
- employer-financed items (allocations familiales patronales, chômage, AT/MP,
  AGIRC-ARRCO employer share, FNAL, versement mobilité, contribution au dialogue
  social, CSA, forfait social…).

This is only needed once a **labour-cost or reform question** arises; it is not on
the disposable-income critical path. Hence P2, and explicitly *after* 0004 (which
introduces the PASS and the per-risk pattern this reuses).

## 2. Goal

Model the **employer contributions** and the **réduction générale**, exposing:

- `cotisations_patronales` (Individu, YEAR) — sum of employer lines,
- `super_brut` / `cout_du_travail` = `salaire_brut + cotisations_patronales
  − reduction_generale`,
- `reduction_generale` (Individu, YEAR) — the dégressive allègement.

No change to `salaire_declare` or disposable income — this is an **additive**
labour-cost layer, so existing outputs are untouched.

## 3. Design

### 3.1 Parameters — `gov/urssaf/cotisations_patronales/`
Per-risk 2024 employer rates, with the **bandeaux** (reduced rates for low/mid
wages) modelled as thresholds, not a single rate:

| Risk (employer) | Rate | Notes |
|---|---|---|
| Maladie (bandeau) | 7 % ≤ 2,5 SMIC, else 13 % | "bandeau maladie" |
| Allocations familiales (bandeau) | 3,45 % ≤ 3,5 SMIC, else 5,25 % | "bandeau famille" |
| Vieillesse plafonnée / déplafonnée | 8,55 % / 2,02 % | PASS ceiling (reuse 0004) |
| AGIRC-ARRCO retraite T1/T2 (employer share) | 4,72 % / 12,95 % | employer ~60 % |
| CEG T1/T2 / CET | 1,29 % / 1,62 % / 0,21 % | |
| Chômage + AGS | 4,05 % + 0,20 % | |
| AT/MP | (input, sector-specific) | default a documented average |
| FNAL | 0,10 % (<50) / 0,50 % (≥50) | firm-size input |
| Versement mobilité, CSA, dialogue social | thresholds/rates | small lines |

Add a `taille_entreprise` (firm size) and `taux_at_mp` input where the schedule
requires them; default to documented MVP values and disclose.

### 3.2 Réduction générale (ex-Fillon)
`parameters/gov/urssaf/reduction_generale/` — the **coefficient formula**
(CSS art. L241-13, D241-7): dégressive from a maximum at SMIC to **0 at 1,6 SMIC**,
`coefficient = (T / 0.6) × (1.6 × SMIC_annuel / rémunération − 1)`, where `T` is the
published maximum (≈ 0.3194 for firms < 50, ≈ 0.3234 for ≥ 50 in 2024 — transcribe,
do not hardcode). `reduction_generale = coefficient × salaire_brut`, clipped to the
eligible contribution base. This is the single most error-prone piece — label the
PR `needs-review` for the statute-review gate.

### 3.3 SMIC
`parameters/gov/smic/smic_annuel.yaml` (2024: 1 766,92 €/mois × 12 = 21 203 €;
state the monthly/annual and the 35h basis) — reused by 0004 (low-wage) and here.

## 4. Files touched
- `parameters/gov/urssaf/cotisations_patronales/**`, `reduction_generale/**`,
  `gov/smic/**` — **new**
- `variables/gov/urssaf/cotisations_patronales.py`, `reduction_generale.py`,
  `variables/menage/cout_du_travail.py` (or `super_brut`) — **new**
- `variables/input/{taille_entreprise,taux_at_mp}.py` — **new** (defaults documented)
- `modelled_policies.yaml` / `coverage.md` — add the employer layer to ✅; the
  0004 note "employer side out of scope" is narrowed/removed
- tests: per-risk transcription; bandeau thresholds (2,5 / 3,5 SMIC crossings);
  réduction générale at SMIC / 1,3 SMIC / 1,6 SMIC (max / partial / zero);
  `super_brut` identity; oracle from a URSSAF/Mon-entreprise super-brut simulation

## 5. Tests & acceptance
1. **Bandeau crossings** — maladie rate flips at 2,5 SMIC, famille at 3,5 SMIC.
2. **Réduction générale** — equals the published coefficient at SMIC, tapers to
   **exactly 0 at 1,6 SMIC**, and never negative; firm-size `T` selected correctly.
3. **super_brut identity** — `super_brut = brut + cotisations_patronales
   − reduction_generale`, and `super_brut ≥ brut − reduction_generale`.
4. **No disposable-income regression** — employee-side outputs and
   `revenu_disponible` are unchanged (additive layer); golden master only gains
   the new columns.
5. **Oracle** — a URSSAF super-brut simulation matches within a few €.
6. `make test` + pytest green; ruff; doc-currency parity.

## 6. Risks
- **Réduction générale formula** is intricate (base éligible, annualisation,
  firm-size `T`, interaction with heures sup). Model the standard case; disclose
  the rest. `needs-review` label.
- **Rate/threshold churn** — pairs with 0007 (multi-year); these are very
  year-sensitive.
- **Scope discipline** — stop at the standard private-sector case; public sector,
  apprentis, ZRR/ZFU, exonérations spécifiques are explicit non-goals.

## 7. Sequencing
After 0004 (shares the PASS + per-risk pattern) and best after 0007 (the rates are
year-sensitive). Independent of the benefit track (0002/0005/0006).
