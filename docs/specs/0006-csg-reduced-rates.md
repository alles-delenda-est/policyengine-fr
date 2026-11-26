# Spec 0006 — CSG reduced rates (replacement income + low earners)

**Status:** Draft · **Priority:** P2 · **Depends on:** Spec 0001 (income base) ·
**Est. effort:** 2 days

---

## 1. Problem

CSG is modelled as a **flat 9,2 %** on salary (coverage.md ⚠️). In law the CSG
rate on **replacement income** (pensions de retraite, allocations chômage,
indemnités journalières) is **not** the activity rate: it depends on the
household's **revenu fiscal de référence (RFR)** and number of parts, giving
**four bands** — exonération / taux réduit / taux médian / taux normal:

| Band (pensions de retraite, 2024) | CSG | of which déductible |
|---|---|---|
| Exonération (RFR ≤ seuil 1) | 0 % | — |
| Taux réduit | 3,8 % | 3,8 % |
| Taux médian | 6,6 % | 4,2 % |
| Taux normal | 8,3 % | 5,9 % |

(Chômage uses 6,2 % normal instead of 8,3 %.) The activity CSG stays 9,2 %.
Applying the 9,2 % activity rate to a pension (as a naive extension would) is wrong.

## 2. Goal

Model the **RFR-banded CSG** on replacement income so that spec 0005 (retirement
pensions) can levy the correct CSG, and so the "flat 9,2 %" caveat is narrowed to
"activity only".

## 3. Design

### 3.1 RFR + seuils
- `revenu_fiscal_de_reference` (FoyerFiscal, YEAR): for the MVP, RFR ≈
  `revenu_net_imposable` before the QF (documented approximation — the exact RFR
  adds back some abattements/exonérations; disclose).
- `parameters/gov/urssaf/csg/remplacement/seuils/*.yaml`: the RFR thresholds by
  number of parts (2024 values, indexed) delimiting the four bands.

### 3.2 Banded rate
- `parameters/gov/urssaf/csg/remplacement/{exonere,reduit,median,normal}.yaml`:
  the CSG rate and its déductible share per band.
- `taux_csg_remplacement` (FoyerFiscal → Individu, YEAR): selects the band from RFR
  and parts, returns (taux, part déductible).

### 3.3 Apply to replacement income
`csg_remplacement`, `crds_remplacement` on `pension_retraite` (0005) and any future
chômage input, with the déductible share fed into the pension abattement / declared
income exactly as the activity CSG is in 0001.

## 4. Files touched
- `variables/gov/dgfip/ir/revenu_fiscal_de_reference.py` — **new** (MVP proxy)
- `parameters/gov/urssaf/csg/remplacement/**` — **new** (seuils + banded rates)
- `variables/gov/urssaf/csg_remplacement.py`, `crds_remplacement.py` — **new**
- `modelled_policies.yaml` / `coverage.md` — narrow the flat-9,2 % caveat to
  "activity CSG only"; add the RFR-proxy simplification
- tests: band-boundary cases (each seuil), the déductible split, exonération at 0 %

## 5. Tests & acceptance
1. **Band selection** — at each RFR seuil (± €1) the correct band is chosen for
   1 part and 2 parts.
2. **Rate + déductible split** per band matches the published 2024 values.
3. **Exonération** yields 0 CSG and 0 CRDS.
4. **RFR proxy** documented; a note on where it diverges from the legal RFR.
5. `make test` + pytest green; ruff; doc-currency parity.

## 6. Risks
- **RFR is a rabbit hole** — the exact RFR reintegrates many items the MVP doesn't
  model. Use the documented proxy and disclose; do not block on a perfect RFR.
- **Parts coupling** — the seuils depend on `nombre_parts`, already modelled; reuse it.

## 7. Sequencing
Do **before or with 0005** (retirement pensions), which is its main consumer.
