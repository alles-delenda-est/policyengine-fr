# Theory: Building `policyengine-fr` — From Disposable-Income MVP to Multi-Year Fiscal & Benefit Microsimulation

## Problem

An early tax-benefit MVP (`salaire_brut` → `impot_revenu` → `csg`/`crds` → `AF` →
`ASF` → `revenu_disponible`) proves the engine pipeline works, but breaks down as
soon as means-tested solidarity benefits (`rsa`, `prime_activite`), replacement
incomes (`pension_retraite`), employer labour-cost wedges (`cout_du_travail`), or
patrimonial/land-tax reforms are introduced. Specifically, three structural seams
had to be resolved cleanly:

1. **The payslip seam (`salaire_brut` vs `salaire_declare` vs `salaire_net`):**
   Reading a single salary input as declared `1AJ` in IR and as gross salary in
   CSG/CRDS silently misstates take-home pay by ~21 % and corrupts both RSA and
   Prime d'activité resource bases.
2. **Interlocking benefit resource bases (`AF` ↔ `ASF` ↔ `RSA` ↔ `PPA`):**
   Means-tested French benefits interact non-linearly: RSA counts base AF
   (excluding age-14 majorations per CASF art. R262-11 3°) and caps counted ASF
   at the `0,225 × BMAF` forfait (CASF art. R262-10-1); Prime d'activité in turn
   subtracts the *non-bonified* RSA entitlement (`max(rsa_mf − rsa_fl − ressources, 0)`)
   so that its 61 % activity slope and individual SMIC bonification stack cleanly
   on top of the RSA floor without circular dependencies.
3. **Reform-ready `Simulation(reform=...)` architecture:**
   Downstream macro-fiscal tools (`budget_fr_sim_test`) and patrimonial tax-shift
   simulators (`LVTShift`) require parameterised `Reform` objects modifying YAML
   parameter trees in memory (`CountryTaxBenefitSystem(reform=...)`) without
   mutating baseline rules.

## Operating Theory & Key Architectural Resolutions

### 1. True-Gross Salary Chain & 2019 AGIRC-ARRCO Unification
`salaire_brut` is strictly gross pay before employee contributions. Per-risk
PASS-bracketed employee levies (`cotisations_salariales`) plus deductible CSG
(6,8 % on 98,25 % of gross) determine `salaire_declare` (case 1AJ, feeding the
10 % IR abatement), while further subtracting non-deductible CSG (2,4 %) and CRDS
(0,5 %) yields `salaire_net` (feeding `rsa_base_ressources`, `prime_activite`,
and `revenu_disponible`). Crucially, under the 2019 AGIRC-ARRCO unified scheme
(ANI of 17 Nov 2017), the *Contribution d'équilibre technique* (`CET`, 0,14 %
employee / 0,21 % employer on `0–8 PASS`) applies to **all** private-sector
employees (cadre and non-cadre alike) as soon as `salaire_brut > 1 PASS`; only
`APEC` (0,024 % / 0,036 % up to 4 PASS) is restricted to `cadre=True`.

### 2. Smoothing Threshold Cliffs & Exact Statutory Benefit Bases
- **AF *complément dégressif* (CSS art. D521-1, al. 3):** Eliminates the ~745 €/yr
  artificial marginal-tax-rate cliff at each AF plafond crossing via
  `max(0, plafond + 12 × af_retenue − ressources) / 12`.
- **RSA statutory resource exclusions:** Splitting AF base vs age majoration and
  capping counted ASF at `0,225 × BMAF` resolved a −1 090,54 €/yr single-parent
  under-estimation and brought all five RSA household archetypes within 0,01 € of
  `openfisca-france` (once OpenFisca's monthly `statut_occupation_logement = "loge_gratuitement"`
  was set across all 12 months so both engines apply *forfait logement* identically).
- **Prime d'activité (`prime_activite`):** Expresses the monthly entitlement in
  closed non-circular form as
  `max(ppa_mf − ppa_fl + ppa_bonification + 0,61 × rev_pro − ressources_hors_rsa − rsa_non_bonifie, 0)`,
  applying the 15 €/month payment floor (`CSS art. D843-2`) and matching
  `openfisca-france` across 0,5 SMIC, 1,0 SMIC, single-parent, and 2,0 SMIC
  phase-out cases.

### 3. Shared Pension Abattement & Replacement Levies
`pensions_imposables` merges `pension_retraite_declaree` (net of deductible
pension CSG: 0 % / 3,8 % / 4,2 % / 5,9 %) and `pensions_alimentaires_percues`
before applying the per-beneficiary floor and per-foyer ceiling (CGI art. 158, 5,
a), preventing double-counting for households receiving both. Replacement CSG
tiers (0 % / 3,8 % / 6,6 % / 8,3 %; CSS art. L136-8 III) use exact statutory
per-half-part RFR increments (2024 and 2025) alongside CRDS (0,5 %) and CASA
(0,3 % at median/normal tiers; CASF art. L14-10-4), and wire net pensions into
both RSA and AF resource bases.

### 4. Cross-Repository Micro-Macro Integration (`LVTShift` & `budget_fr_sim_test`)
Accepting `reform=None` in `CountryTaxBenefitSystem.__init__` unlocks native
`Simulation(reform=...)` counterfactuals:
- **`lvt_shift` (`S1`–`S3_IFI`):** Pairs household `taxe_fonciere`,
  `taxe_habitation_residence_secondaire`, `ifi`, and `taxe_valeur_sol` with
  pinned macro land-base yields from `LVTShift` (`lvt_yields.json`, SHA-256
  verified) to compute revenue-neutral Land Value Tax rates (`~0,42 %` to
  `~0,91 %`) and household winner/loser incidence.
- **`budget_levers` (including Decision D-P6):** Translates macro PLF levers
  (IR/CSG rate shifts, bracket freezes, and targeted pension under-indexation
  above a statutory pension threshold) into microsimulated household deltas,
  confirming from bottom-up IR + CSG/CRDS/CASA schedules that the mechanical
  fiscal clawback on a 48 000 €/yr pensioner sits inside `budget_fr_sim_test`'s
  `[0,35 ; 0,45]` calibration band.

## Verification Discipline

1. **Float32 calibration:** `policyengine-core` vectorises in `float32`; tests
   and rounding steps account for ~`0,01 €` single-precision tolerance.
2. **Four-layer test pyramid:** 146 YAML unit & integration cases + 25 grid
   property/invariant tests (`test_properties.py`) + golden-master locks + 25
   live DGFiP / `openfisca-france` oracle assertions (`test_oracle.py`) + 5
   cross-repo reform counterfactual tests (`test_reforms.py`).
3. **Automated doc currency (`bin/check_doc_currency.py`):** Blocks drift between
   code test counts and `CLAUDE.md`, and enforces exact 1-for-1 parity between
   `modelled_policies.yaml` (`simplifications:`) and `docs/coverage.md`.
