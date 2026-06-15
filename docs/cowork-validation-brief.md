# CoWork task brief — independent oracle validation of policyengine-fr

This is a self-contained task spec for **Claude CoWork**. Its job is to be the
**independent oracle** that the in-repo tests cannot be: drive the *official*
French calculators in a browser, capture their authoritative numbers, and report
where `policyengine-fr` diverges. This breaks the self-validation loop of the
autonomous build (the build writes its own tests; CoWork checks against the
government's own simulators).

- **Suggested cadence:** weekly, or on-demand after a batch of merges.
- **Deliverable:** a divergence table + a short summary of which outputs are off
  and by how much, posted back to Patrick (email/Slack) and, optionally, as a
  GitHub issue on `alles-delenda-est/policyengine-fr`.

## What to compare against (oracles)

| Output | Official oracle | URL |
|--------|-----------------|-----|
| `impot_revenu` (income tax) — **highest priority** | DGFiP "Simulateur de l'impôt sur le revenu" (modèle **complet** or simplifié), revenus **2024** | https://www.impots.gouv.fr/simulateurs (open the income-tax simulator, "revenus 2024") |
| `allocations_familiales` | CAF "Mes aides" estimateur / mesdroitssociaux.gouv.fr | https://www.caf.fr → estimateur ; https://www.mesdroitssociaux.gouv.fr |
| `csg` / `crds` | Mechanically exact (9.2% / 0.5% × 98.25% of salaire_brut) — low priority; any payslip simulator confirms | — |

## How to get policyengine-fr's current numbers

Read them from the repo (always current): `tests/fixtures/golden_master.json` in
`alles-delenda-est/policyengine-fr`. Each key is a household id; values are the
model's outputs. Use those as the "policyengine-fr" column. (If you can run code,
`pip install -e .` and call `policyengine_fr.Simulation`; otherwise just read the
JSON.)

## Input mapping (read carefully — this is where errors hide)

- **`salaire_brut`** in our model = the **salaire déclaré** you type into the
  DGFiP simulator's *"Salaires, traitements"* field (the amount **before** the
  10% déduction forfaitaire — the simulator applies the 10% itself). Do **not**
  pre-apply the 10%.
- **Family situation:** 1 adult → *Célibataire* (or *Parent isolé*, case **T**,
  when the profile says `parent_isole`); 2 adults → *Marié/Pacsé*.
- **Children:** enter the number of *personnes à charge* = number of children in
  the profile. Enter each child's age where asked (for AF age majorations).
- **Year:** revenus **2024**.

## Household battery

Use exactly these profiles (they mirror the repo's golden-master grid, so the
model values are in `golden_master.json`). For each, enter the inputs into the
oracle and record the official output.

| id | adults' salaire_brut | children (ages) | situation |
|----|----------------------|-----------------|-----------|
| single_20k | 20 000 | — | célibataire |
| single_30k | 30 000 | — | célibataire |
| single_50k | 50 000 | — | célibataire |
| single_120k | 120 000 | — | célibataire |
| single_parent_25k_1child | 25 000 | 1 (8) | parent isolé (case T) |
| couple_60k_0child | 60 000 + 0 | — | marié/pacsé |
| couple_60k_2children | 60 000 + 0 | 2 (10, 16) | marié/pacsé |
| couple_90k_3children | 50 000 + 40 000 | 3 (3, 8, 15) | marié/pacsé |
| couple_200k_3children | 120 000 + 80 000 | 3 (5, 9, 15) | marié/pacsé |
| couple_40k_4children | 40 000 + 0 | 4 (2,6,11,15) | marié/pacsé |

## Output to capture & compare

For each profile, from the DGFiP simulator capture **"Impôt sur le revenu net"**
(the final tax after décote and plafonnement) and compare to the model's
`impot_revenu`.

- **Tolerance:** flag if `|official − model| > 5 €` (small rounding is fine).
- The model already covers: barème, quotient familial, **plafonnement du QF**,
  **décote**. So IR should match closely — divergences point to a real bug in one
  of those (most likely décote thresholds or the plafonnement base-parts logic).

For AF, compare the model's `allocations_familiales` (annual) to 12× the CAF
estimateur's monthly amount.

## Known MVP-boundary caveats — do NOT report these as bugs

- **`revenu_disponible` is NOT comparable** to any official "revenu disponible":
  the model nets only CSG/CRDS, **not** the ~22% cotisations sociales salariales,
  and includes only one benefit. **Validate components (`impot_revenu`, `csg`,
  `crds`, `allocations_familiales`) individually — not the headline.**
- **AF income test is simplified:** the model uses the household's **current-year**
  salaire_imposable instead of the real **base ressources N‑2**. So feed the CAF
  estimateur the *same* income for the reference year, and expect divergence for
  any household whose income changed year-on-year. Métropole only; no garde
  alternée / 20-year-old forfait.
- IR scope excludes réductions/crédits d'impôt, capital income, CEHR.

## Report format

A table per output:

| profile | input summary | official | policyengine-fr | Δ | status |
|---------|---------------|----------|-----------------|---|--------|

Then: a one-paragraph summary highlighting the largest divergences and a
hypothesis for each (e.g. "décote off by ~€30 for single filers → check seuil").
For any confirmed divergence, open a GitHub issue titled
`oracle divergence: <output> for <profile>` with the numbers and the oracle URL.

## Why this matters

The in-repo `make test` proves the model is **internally consistent and
structurally sound** (property tests) and **doesn't drift** (golden master). It
canNOT prove the numbers match French law, because the same process wrote the
code and the expected values. CoWork closes that gap by checking against the
government's own calculators — the one source the build pipeline never touches.
