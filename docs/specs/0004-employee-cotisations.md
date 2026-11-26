# Spec 0004 — Accurate employee social contributions (cotisations salariales)

**Status:** Draft · **Priority:** P1 (refines the 0001 flat rate) ·
**Depends on:** Spec 0001 (introduced `cotisations_salariales` as a flat rate) ·
**Est. effort:** 3–4 days (params + variable + oracle against a payslip)

---

## 1. Problem

Spec 0001 takes gross salary to declared salary through a **single flat effective
rate** (`gov.urssaf.cotisations_salariales.taux_effectif` ≈ 11,31 % for 2024,
excl. CSG/CRDS). That is honest for a mid-range private non-cadre but wrong for:

- **low wages** — the flat rate ignores that the *employee* schedule is largely
  proportional (no SMIC abatement on the employee side), while the big low-wage
  relief (**réduction générale**, ex-Fillon) is **employer-side** and dégressive
  up to 1,6 SMIC. Conflating the two mis-states the brut→net wedge at the bottom;
- **high wages** — no **PASS ceilings** (plafond de la sécurité sociale, 46 368 €/an
  in 2024): the vieillesse plafonnée (6,90 %) and AGIRC-ARRCO tranche 1 (up to
  1 PASS) vs tranche 2 (1–8 PASS, higher rate) are flat in the current model;
- **cadre status** — APEC (0,024 %) and the CET (above 1 PASS) apply to cadres only.

So the current `salaire_declare` is a good central estimate but has a systematic
error that grows away from ~1–2 SMIC, non-cadre.

## 2. Goal

Replace the flat rate with a **per-risk, bracketed** employee-cotisations schedule
(a `bareme`-style parameter set), so the brut→net wedge is right across the wage
distribution and cadre status, while keeping the same public surface
(`cotisations_salariales` → `salaire_declare`).

**Scope boundary to state up front:** the **employer** réduction générale and
employer contributions are a *separate* layer (relevant only if the model ever
computes employer cost / super-brut). This spec is **employee-side only**; the
"SMIC exonération" the user asked about is documented as employer-side and
explicitly out of scope here (with a pointer), so it is not silently omitted.

## 3. Design

### 3.1 Parameters — `gov/urssaf/cotisations_salariales/`
Replace the single `taux_effectif.yaml` with a per-risk set (2024 employee rates):

| Risk | Rate (employee) | Base |
|---|---|---|
| Vieillesse plafonnée | 6,90 % | up to 1 PASS |
| Vieillesse déplafonnée | 0,40 % | total gross |
| AGIRC-ARRCO retraite T1 | 3,15 % | up to 1 PASS |
| AGIRC-ARRCO retraite T2 | 8,64 % | 1–8 PASS |
| CEG T1 / T2 | 0,86 % / 1,08 % | resp. |
| CET (cadre, >1 PASS) | 0,14 % | 1–8 PASS |
| APEC (cadre) | 0,024 % | up to 4 PASS |

Add `gov/urssaf/pass.yaml` (plafond annuel de la sécurité sociale, 46 368 € for
2024) — reused by 0006 and any ceiling logic.

### 3.2 Variable — `cotisations_salariales`
Rewrite as the sum of the per-risk lines, each applied to its `min(brut, k·PASS)`
base, with a `cadre` input (boolean, default false). Keep it `Individu` / `YEAR`.
`salaire_declare` (0001) is unchanged — it still subtracts `cotisations_salariales`
and `csg_deductible`.

### 3.3 New input — `cadre`
`variables/input/cadre.py` (Individu, bool, default false). Drives the cadre-only
lines. Documented as an MVP input; if absent, non-cadre schedule applies.

## 4. Files touched
- `parameters/gov/urssaf/cotisations_salariales/*.yaml` — **replace** flat rate
  with per-risk rates + `pass.yaml`
- `variables/gov/urssaf/cotisations_salariales.py` — per-risk bracketed sum
- `variables/input/cadre.py` — **new**
- `tests/gov/urssaf/cotisations_salariales.yaml` — cases at 0,5 / 1 / 2 / 4 SMIC,
  non-cadre and cadre, crossing the PASS
- `oracle_values.yaml` — 2–3 payslip rows (a real bulletin de paie or a
  URSSAF/Mon-entreprise simulation), brut → net, skip-until-captured
- `modelled_policies.yaml` / `coverage.md` — the flat-rate simplification (⚠️ #1
  from 0001) becomes a much narrower one (ceilings modelled; still no ZRR /
  apprenti / heures-sup exonérations, employer side out of scope)
- `docs/specs/` README status

## 5. Tests & acceptance
1. **Per-risk transcription** — each rate = the published 2024 URSSAF/AGIRC-ARRCO value.
2. **PASS crossing** — at exactly 1 PASS and 2 PASS the plafonnée vs déplafonnée
   split is correct; cadre lines fire only when `cadre=true`.
3. **Monotone & bounded** — cotisations rise with gross, `0 ≤ cotisations < brut`.
4. **Payslip oracle** — a real bulletin: model net within a few € of the payslip net.
5. **Regression** — `salaire_declare` moves vs the 0001 flat rate; golden master
   regenerated and the shift explained (larger for high/cadre, smaller mid-range).
6. `make test` + pytest green; ruff; doc-currency parity.

## 6. Risks
- **Scope creep into the employer side.** Keep firm: employee-only. The employer
  réduction générale is its own future spec, only needed for super-brut / labour-cost.
- **Rate churn** — per-risk rates change yearly; pairs with 0007 (multi-year).
- **`cadre` unknown in microdata** — default non-cadre; document the bias.

## 7. Sequencing
After 0001 (which this refines) and ideally after 0007 (multi-year), since the
per-risk rates are the most year-sensitive parameters in the model.
