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
| `impot_revenu` (income tax) — **highest priority** | DGFiP "Simulateur de l'impôt sur le revenu", modèle **simplifié**, revenus **2024** | https://simulateur-ir-ifi.impots.gouv.fr/calcul_impot/2025/simplifie/index.htm |
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

## Runbook — exact steps for 3 representative profiles (do these first)

Oracle: **DGFiP simulateur, modèle simplifié, revenus 2024** —
https://simulateur-ir-ifi.impots.gouv.fr/calcul_impot/2025/simplifie/index.htm

**General flow (same for every profile):**
1. Open the URL; accept the intro/disclaimer.
2. **Situation** screen: set *Situation de famille* (Célibataire / Marié-Pacsé);
   answer *Parent isolé* (case **T**) Oui/Non; enter *Nombre d'enfants à charge*.
3. **Revenus** screen: under *Traitements et salaires*, enter case **1AJ** for
   adult 1 and **1BJ** for adult 2. Enter our `salaire_brut` **as-is** — the
   simulator applies the 10 % déduction itself (do not pre-deduct it).
4. Validate → read **« Impôt sur le revenu net »** (the final figure, after décote
   and plafonnement). That is the number to compare.

These three cover the distinct field paths: a plain single filer, a parent isolé
with a child, and a married couple with children. Tolerance: flag if
`|official − model| > 5 €`.

### Profile A — `single_30k` (célibataire, no children)
| Field | Enter |
|-------|-------|
| Situation de famille | Célibataire |
| Parent isolé (case T) | Non |
| Nombre d'enfants à charge | 0 |
| 1AJ (salaires adulte 1) | `30000` |
| 1BJ | (blank) |

→ Capture « Impôt sur le revenu net » = **______ €**
**policyengine-fr → `impot_revenu` = 1 587,99 €.** Flag if |official − 1587.99| > 5.

### Profile B — `single_parent_25k_1child` (parent isolé, 1 child)
| Field | Enter |
|-------|-------|
| Situation de famille | Célibataire |
| Parent isolé (case T) | **Oui** |
| Nombre d'enfants à charge | 1 |
| 1AJ | `25000` |

→ Capture « Impôt sur le revenu net » = **______ €**
**policyengine-fr → `impot_revenu` = 0,00 €** (2 parts — 1 + 0,5 enfant + 0,5
parent isolé — so the quotient 22 500 / 2 = 11 250 sits just under the first
barème threshold of 11 497). Flag if official > 5 €. *(This 0 is a strong, easy oracle
check — if the simulator shows a positive tax, our parts/décote is wrong.)*

### Profile C — `couple_60k_2children` (marié, 2 children, single earner)
| Field | Enter |
|-------|-------|
| Situation de famille | Marié / Pacsé |
| Parent isolé | Non |
| Nombre d'enfants à charge | 2 |
| 1AJ (salaires adulte 1) | `60000` |
| 1BJ (salaires adulte 2) | `0` |

→ Capture « Impôt sur le revenu net » = **______ €**
**policyengine-fr → `impot_revenu` = 1 647,05 €.** Flag if |official − 1647.05| > 5.

### Results template to fill in
| profile | inputs | official IR | model IR | Δ | status |
|---------|--------|-------------|----------|---|--------|
| A single_30k | cél., 0 enf., 1AJ 30000 | ____ | 1 587,99 | ____ | ____ |
| B single_parent_25k_1child | cél. isolé, 1 enf., 1AJ 25000 | ____ | 0,00 | ____ | ____ |
| C couple_60k_2children | marié, 2 enf., 1AJ 60000, 1BJ 0 | ____ | 1 647,05 | ____ | ____ |

If all three Δ ≤ 5 €, the income-tax core (barème + parts + plafonnement + décote)
is validated against the government for these points — then extend to the full
battery above. If any Δ > 5 €, that's a real bug: open a GitHub issue
`oracle divergence: impot_revenu for <profile>` with the numbers and this URL.

> AF note: the IR simulator does **not** output allocations familiales. Validate
> `allocations_familiales` separately on the CAF estimateur, feeding it the same
> household and income (mind the N‑2 caveat above).

## AF capture runbook (CAF / mesdroitssociaux estimateur)

Oracle: **CAF "Mes aides" estimateur** —
https://www.mesdroitssociaux.gouv.fr

This runbook covers the three AF profiles in `tests/fixtures/oracle_values.yaml`
(the `*_af` rows). Complete this after the IR battery above.

**General flow (same for every AF profile):**
1. Open the URL and start the estimateur ("Tester mes droits" or similar entry
   point); you may need to answer a short questionnaire to reach the family
   benefits section.
2. **Situation familiale:** select *Marié / Pacsé* or *Célibataire* as stated in
   the profile.
3. **Enfants:** enter the number of children and each child's age as given in
   the profile (ages matter for the AF majorations de l'enfant de 14 ans et +).
4. **Ressources:** enter the household's **annual salaire brut** from the
   `salaires` field of the profile as the reference income. The estimateur may
   ask for net or brut — use the amount shown in the fixture; if it asks for
   *revenus nets*, divide by 1.2285 (the standard gross-to-net conversion) as an
   approximation, or check the site's help text. Note the **base-ressources N‑2
   caveat** documented above: the model uses current-year income as a
   simplification; for the oracle, feed the same income for the reference year so
   the two are directly comparable.
5. Read the **monthly** *allocations familiales* figure from the results page.
   Multiply by **12** to get the annual amount and enter that into the row's
   `official` field. Record today's date in `captured_on`.

**Profiles to capture:**

| id | situation | children (ages) | salaires (annual) |
|----|-----------|-----------------|-------------------|
| `couple_60k_2children_af` | Marié / Pacsé | 2 (10, 16) | 60 000 € (adult 1) + 0 € (adult 2) |
| `couple_90k_3children_af` | Marié / Pacsé | 3 (3, 8, 15) | 50 000 € (adult 1) + 40 000 € (adult 2) |
| `couple_40k_4children_af` | Marié / Pacsé | 4 (2, 6, 11, 15) | 40 000 € (adult 1) + 0 € (adult 2) |

**Tolerance:** flag if `|official − model| > 12 €` on the annual figure (≈ 1 €/month).
This tolerance is looser than IR because of two known sources of noise:
- The BMAF (base mensuelle des allocations familiales) is revalorised each
  1 April, so the annual total depends on which month you query.
- The model's base-ressources N‑2 simplification (uses current-year income).

**Results template — fill in after capture:**

| profile | inputs | official AF (annual = 12×monthly) | model AF | Δ | status |
|---------|--------|-----------------------------------|----------|---|--------|
| couple_60k_2children_af | marié, 2 enf. (10,16), sal. 60k+0 | ____ | 1 771,44 | ____ | ____ |
| couple_90k_3children_af | marié, 3 enf. (3,8,15), sal. 50k+40k | ____ | 4 926,82 | ____ | ____ |
| couple_40k_4children_af | marié, 4 enf. (2,6,11,15), sal. 40k+0 | ____ | 7 196,48 | ____ | ____ |

Once captured, update `tests/fixtures/oracle_values.yaml` — set `official` to
the computed annual value and `captured_on` to today's date (ISO 8601). The
`test_oracle.py` harness will then automatically run these as live assertions
(tolerance 12 €) instead of skipping them.

## Government AF spot-check (mesdroitssociaux.gouv.fr) — captured 2026-06-22

The DGFiP income-tax simulator does not output allocations familiales, so AF was
also cross-checked against the **government's own benefits engine** at
mesdroitssociaux.gouv.fr (the official interministerial "Simuler mes aides"
questionnaire — there is no quick AF-only calculator). This is a third,
fully independent anchor on top of openfisca-france.

**Caveat — read first:** the estimateur computes *today's* entitlement, so it
uses the **2026 BMAF**, whereas the model is revenus-2024 (BMAF 445,93 → 466,44).
Euro amounts therefore differ by the BMAF year; the meaningful check is the
**per-BMAF coefficient** (= AF ÷ BMAF) and the **modulation tier**. The site
rounds displayed amounts to the nearest 10 €.

| household | 2024 income | govt AF/mo | implied coef | model coef | structure validated |
|-----------|-------------|-----------|--------------|------------|---------------------|
| couple, 2 enf. (one ≥14) | 54 k (low) | 150 € | 0.32 | 0.32 | 2-child base; **no** majoration (eldest-of-two exclusion) |
| couple, 3 enf. (one ≥14) | ~0 | 430 € | 0.89 | 0.89 | 3-child base 0.73 + majoration 0.16 |
| couple, 3 enf. (one ≥14) | 180 k (high) | 110 € | 0.2225 | 0.2225 | quarter-rate modulation (= 0.89 ÷ 4) |
| couple, 4 enf. (one ≥14) | 36 k (low) | 620 € | 1.30 | 1.30 | 4-child base 1.14 (= 0.32 + 2×0.41) + majoration 0.16 |

All four amounts are internally consistent with a single **BMAF ≈ 478 €** (2026):
478 × {0.32, 0.89, 0.2225, 1.30} = {153, 425, 106, 621} → displayed
{150, 430, 110, 620}. Every coefficient the model uses is reproduced by the
government engine — confirming the base rates, the +0.41-per-extra-child
increment, the age majoration, the eldest-of-two exclusion, and the income
modulation (taux plein at low income, quarter rate at high income).

**Operational note for re-capture:** in this simulator the AF modulation is
driven by the **per-person "Total de l'année 2024"** salary field, *not* the
foyer "Revenu fiscal de référence 2024" field. With income entered only in the
RFR field, AF stays at taux plein even at 180 k (the 430 € row above was first
observed this way, then corrected to 110 € once the per-person 2024 total was
filled). Always enter the N-2 income per person.

## Why this matters

The in-repo `make test` proves the model is **internally consistent and
structurally sound** (property tests) and **doesn't drift** (golden master). It
canNOT prove the numbers match French law, because the same process wrote the
code and the expected values. CoWork closes that gap by checking against the
government's own calculators — the one source the build pipeline never touches.
