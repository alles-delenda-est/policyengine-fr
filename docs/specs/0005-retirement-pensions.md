# Spec 0005 — Retirement pensions + shared 10 % pension abattement merge

**Status:** Draft · **Priority:** P2 · **Depends on:** Spec 0001 (income
concepts) · **Est. effort:** 2–3 days

---

## 1. Problem

The model ingests only **salary** and **pensions alimentaires**. Retirement
pensions (`pensions de retraite`) are a first-order income type it cannot
represent. Adding them also **resolves an existing latent bug** flagged in
coverage.md (⚠️) and `modelled_policies.yaml`:

> The 10 % abattement on pensions (CGI art. 158, 5, a) has a floor (per
> beneficiary) and a ceiling (per foyer fiscal) that are, in law, **common to all
> pensions** — retraites *and* pensions alimentaires. The model currently applies
> them to pensions alimentaires alone. When retirement pensions are added, the
> abattement must be **merged** to share one floor/ceiling, or it is granted twice.

So this spec is *gated by correctness*: you cannot add retirement pensions without
merging the abattement, and the merge is only meaningful once both pension types exist.

## 2. Goal

1. Add `pension_retraite` (input, Individu, YEAR) as a taxable income.
2. Apply the CSG/CRDS on replacement income at the **reduced/exempt rates** — this
   is where 0005 meets **spec 0006** (CSG reduced rates); pick the RFR-based rate
   there and consume it here.
3. **Merge** the 10 % pension abattement so its floor (per beneficiary) and
   ceiling (per foyer fiscal) are computed over the **sum** of taxable pensions
   (retraite + alimentaire), once.

## 3. Design

### 3.1 New input
`variables/input/pension_retraite.py` (Individu, YEAR, EUR).

### 3.2 Refactor the abattement
Today `pensions_alimentaires_imposables` applies the abattement to pensions
alimentaires. Introduce `pensions_imposables` (Individu → aggregated FoyerFiscal)
that:
- sums `pension_retraite + pensions_alimentaires_percues` per beneficiary,
- applies the 10 % rate with the **per-beneficiary floor** (art. 158, 5, a) on the
  beneficiary's *total* pension,
- caps the total abattement at the **per-foyer ceiling**.

`revenu_net_imposable` consumes `pensions_imposables` in place of the current
pensions-alimentaires-only term. The existing pension-alimentaire tests become a
special case (retraite = 0) and must still pass unchanged.

### 3.3 CSG/CRDS on pensions
Retirement pensions bear CSG at the **reduced rates** (3,8 % / 6,6 % / 8,3 % by
RFR band, or exemption) — implement via **spec 0006**. If 0006 is not yet done,
land 0005 with retirement pensions **taxable to IR** but flag the CSG-on-pension
line as `not_modelled` rather than applying the 9,2 % activity rate (which is wrong
for pensions).

## 4. Files touched
- `variables/input/pension_retraite.py` — **new**
- `variables/gov/dgfip/ir/pensions_imposables.py` — **new** (merged abattement)
- `variables/gov/dgfip/ir/revenu_net_imposable.py` — consume the merged term
- `parameters/gov/dgfip/ir/abattement_pensions/*` — unchanged values, now shared base
- `modelled_policies.yaml` / `coverage.md` — remove the "abattement granted twice"
  risk caveat (now resolved); add retirement-pension income; note CSG-on-pension status
- tests: merged-abattement cases (retraite only; retraite + alimentaire sharing the
  ceiling; two beneficiaries); oracle rows from the DGFiP simulator (pension income)

## 5. Tests & acceptance
1. **Abattement not double-counted** — a foyer with both pension types gets the
   ceiling applied **once** over the sum (regression test for the flagged bug).
2. **Per-beneficiary floor** on total pension; **per-foyer ceiling** on the sum.
3. **Back-compat** — all existing pensions-alimentaires tests pass with retraite = 0.
4. **Oracle** — DGFiP simulator rows with retirement pension income match.
5. `make test` + pytest green; ruff; doc-currency parity.

## 6. Risks
- **CSG coupling** — doing pensions without 0006 means CSG-on-pension is either
  wrong (activity rate) or absent; prefer sequencing 0006 first, or land 0005
  IR-only with an explicit `not_modelled` on the pension CSG line.
- **Abattement edge cases** — the shared floor/ceiling interaction is exactly the
  logic the statute-review gate (0003) should scrutinise; label the PR `needs-review`.

## 7. Sequencing
Pairs with 0006 (CSG reduced rates). Do **0006 first** if CSG-on-pension accuracy
matters; otherwise land 0005 IR-only and follow with 0006.
