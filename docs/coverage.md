# Coverage map — what `policyengine-fr` does and doesn't model

> **Human-readable companion to [`policyengine_fr/modelled_policies.yaml`](../policyengine_fr/modelled_policies.yaml).**
> That YAML is the machine-readable modelled / not-modelled boundary (and the
> reviewer-gate's source of truth); this document is the narrative version for
> readers. Keep the two in sync — `bin/check_doc_currency.py` enforces exact
> parity between `simplifications:` and the numbered items under **Partial
> coverage** below.
>
> **State as of 2026-11-27.** Scope: **revenus 2024–2025, France métropolitaine**.

## One-line summary

`policyengine-fr` is a **multi-year (2024–2025) static tax-benefit, labour-cost,
and patrimonial microsimulation model for France métropolitaine**. From true
gross salary (`salaire_brut`), retirement pensions, child support, capital and
rental income, and real-estate / land endowments, it models employee and
employer social contributions (with the *réduction générale*), income tax
(`impot_revenu`, CEHR, PFU, rental and real-estate capital-gains taxes),
property and land taxes (`ifi`, `taxe_fonciere`,
`taxe_habitation_residence_secondaire`, `taxe_valeur_sol`), and major family and
working-age benefits (`allocations_familiales`, `allocation_soutien_familial`,
`rsa`, `prime_activite`), aggregated into household `revenu_disponible` and
employer `cout_du_travail`.

---

## ✅ What is modelled

### Payslip & labour cost — social contributions (URSSAF / AGIRC-ARRCO)

- **Cotisations salariales (`cotisations_salariales`)** — per-risk PASS-bracketed
  employee contributions: vieillesse plafonnée (1 PASS) & déplafonnée,
  AGIRC-ARRCO Tranche 1 & Tranche 2 (1–8 PASS), CEG T1 & T2, CET (0–8 PASS when
  `salaire_brut > 1 PASS`), and APEC (`cadre=True`).
- **CSG / CRDS on salary (`csg`, `crds`)** — 98,25 % assiette capped at 4 PASS
  (100 % above); 6,8 % deductible CSG deducted to form `salaire_declare` (case
  1AJ), and 2,4 % non-deductible CSG + 0,5 % CRDS deducted to form `salaire_net`
  (net perçu avant IR).
- **Cotisations patronales (`cotisations_patronales`), `reduction_generale` &
  `cout_du_travail`** — employer maladie and famille (with 2024 and 2025 LFSS
  SMIC bandeaux), vieillesse, chômage, AGS, FNAL (`< 50` vs `>= 50` employees),
  AT/MP, AGIRC-ARRCO, CEG, CET, APEC, CSA, dialogue social, net of the degressive
  *réduction générale* (ex-Fillon up to 1,6 SMIC), yielding super-brut
  `cout_du_travail`.

### Retirement pensions & replacement levies (URSSAF / DGFiP)

- **Pensions de retraite (`pension_retraite`)** — RFR-banded replacement CSG
  (0 % / 3,8 % / 6,6 % / 8,3 % per CSS art. L136-8 III), deductible CSG
  (0 % / 3,8 % / 4,2 % / 5,9 %) netted off `pension_retraite_declaree`, CRDS
  (0,5 %), and CASA (0,3 % at median/normal tiers), yielding
  `pension_retraite_nette`.
- **Merged 10 % pension abattement (`pensions_imposables`)** — shared per-person
  floor and per-foyer ceiling across retirement pensions and received child
  support (`pensions_alimentaires_percues`, CGI art. 158, 5, a).

### Income, capital & wealth taxes (DGFiP)

- **Impôt sur le revenu (`impot_revenu`)** — `salaire_imposable` (10 % expenses
  abattement), `pensions_imposables`, `revenus_fonciers_nets` (30 % micro-foncier
  up to 15 000 € or réel) less 6,8 % deductible CSG, minus paid alimony
  (`pensions_alimentaires_versees`) → `revenu_net_imposable` → `nombre_parts`
  (quotient familial + parent isolé) → `impot_brut` →
  `plafonnement_quotient_familial` → `decote` → `impot_revenu`.
- **Revenu fiscal de référence (`revenu_fiscal_de_reference`)** and **CEHR
  (`cehr`)** — non-circular RFR combining taxable wages, capped-abattement
  pensions, net rents after deductible CSG, `revenus_capital`, and
  `plus_values_immobilieres`; 3 % / 4 % high-income surtax (250 k€ / 500 k€
  single; doubled for couples).
- **PFU & patrimonial levies (`pfu_ir`, `prelevements_sociaux_patrimoine`,
  `impot_plus_values_immobilieres`)** — 12,8 % flat IR on `revenus_capital`, 19 %
  IR on `plus_values_immobilieres`, and social levies of 17,2 % in 2024–2025
  (18,6 % on `revenus_capital` from 2026-01-01 per LFSS 2026 art. 12, while
  `revenus_fonciers_nets` and `plus_values_immobilieres` stay at 17,2 %).
- **IFI (`ifi`)** — 30 % principal-residence abatement, strict `> 1 300 000 €`
  entry threshold (CGI art. 964) with progressive brackets from 800 k€, and
  1,3–1,4 M€ décote.
- **Local & land taxes (`taxe_fonciere`, `taxe_habitation_residence_secondaire`,
  `taxe_valeur_sol`)** — local bills (`taxe_fonciere_locale`, `thrs_locale`)
  plus the 3 % State management fee (CGI art. 1641), and land-value tax on
  `valeur_terrain_imposable`, paired with parameterised reforms in
  `policyengine_fr.reforms` (`lvt_shift` S1–S3_IFI — where S3 exempts net rents
  from IR and social levies while retaining them in RFR and means-tests — and
  `budget_levers`).

### Family & solidarity benefits (CNAF)

- **Allocations familiales (`allocations_familiales`)** — base by child count
  (2+), income modulation on `salaire_imposable + pensions_imposables` across 3
  tranches with the statutory **complément dégressif** (CSS art. D521-1, al. 3),
  and age-14 majoration.
- **Allocation de soutien familial (`allocation_soutien_familial`)** — taux
  simple (0,422 BMAF), paid as a *complément différentiel* net of received child
  support for single-parent families.
- **Revenu de solidarité active (`rsa`)** — `rsa_montant_forfaitaire` (including
  *RSA majoré* for single parents and +40 % from the 3rd child),
  `rsa_forfait_logement`, `rsa_base_ressources` (`salaire_net`,
  `pension_retraite_nette`, `pensions_alimentaires_percues`, `revenus_capital`,
  `revenus_fonciers_nets`, AF excluding age majorations per CASF art. R262-11,
  and forfaitised ASF `min(asf, 0,225 BMAF)` per art. R262-10-1), age ≥ 25 or
  dependent-child eligibility (art. L262-4), and 6 €/month minimum payment
  threshold (art. R262-39).
- **Prime d'activité (`prime_activite`)** — `ppa_montant_forfaitaire`, individual
  `ppa_bonification` ramping linearly between 59 and 120 hourly SMIC, 61 % slope
  on professional income, `ppa_forfait_logement`, netting off non-bonified RSA,
  and 15 €/month minimum payment threshold.

### Aggregates

- **`revenu_disponible`** (`menage`) — net household disposable income combining
  net wages, net pensions, child support, net capital/rental/gain cashflows, plus
  AF, ASF, RSA, and Prime d'activité, minus IR, CEHR, PFU, patrimonial PS,
  real-estate CGT, IFI, TFPB, THRS, and LVT.
- **`cout_du_travail`** (`individu`) — total employer cost (`salaire_brut + cotisations_patronales - reduction_generale`).

---

## ⚠️ Partial coverage — caveats *inside* what is modelled

These policies are modelled, with every departure from exact statute explicitly
enumerated below and mirrored 1-for-1 under `simplifications:` in
`policyengine_fr/modelled_policies.yaml`:

1. **Employee cotisations cover full-time private-sector rules and read parameters
   on 1 January.** `cotisations_salariales` models a non-agricultural
   private-sector employee (`cadre=False` by default, `cadre=True` for APEC)
   without mandatory *mutuelle*, exempt overtime, apprenticeship, civil-service
   or Alsace-Moselle rules; activity CSG is flat 9,2 % (98,25 % assiette capped
   at 4 PASS, 100 % above), and `YEAR` parameters are evaluated on 1 January of
   the simulated year.
2. **Employer cotisations and *réduction générale* evaluate rates and SMIC on
   1 January without infra-annual proration.** Because `cotisations_patronales`
   and `reduction_generale` are `YEAR` variables, `parameters(period)` reads the
   values in force on 1 January (so mid-year updates such as AGS 0,25 % on
   `2024-07-01`, SMIC 11,88 € on `2024-11-01`, or chômage 4,00 % on `2025-05-01`
   take effect on 1 January of the following year); annual SMIC assumes full-time
   1 820 h and omits local *versement mobilité*, *forfait social*, DFS, and
   geographic exemptions (ZRR, ZFU, JEI, LODEOM).
3. **Pension CSG/CRDS/CASA uses current-year RFR instead of N-2.** The four-tier
   replacement CSG schedule (0 % / 3,8 % / 6,6 % / 8,3 %; CSS art. L136-8 III)
   and 0,3 % CASA (CASF art. L14-10-4) read current-year
   `revenu_fiscal_de_reference` rather than N-2 RFR and do not model the
   two-consecutive-year upward-crossing smoothing rule (CSS art. L136-8 III bis).
4. **`revenu_fiscal_de_reference` uses pre-pension-CSG gross pensions to avoid
   same-year circularity and spans modelled incomes only.** RFR (CGI art. 1417,
   IV) sums `salaire_imposable`, `pension_retraite + pensions_alimentaires_percues`
   after the floored and capped 10 % allowance (CGI art. 158, 5, a — evaluated
   before deductible pension CSG so `taux_csg_pension` has no cycle in year N),
   `revenus_fonciers_nets` less 6,8 % deductible CSG, `revenus_capital`, and
   `plus_values_immobilieres`, minus `pensions_alimentaires_versees` (omitting
   life-insurance allowances, retirement-savings deductions, and unmodelled
   exempt incomes).
5. **Shared 10 % pension abattement caps at the foyer total without per-person
   proration.** Individual floors are bounded by each member's combined
   `pension_retraite_declaree + pensions_alimentaires_percues`, and the foyer sum
   is capped at the statutory foyer ceiling (CGI art. 158, 5, a) without
   allocating the cap back across individual declarants.
6. **Paid `pensions_alimentaires_versees` are taken as already deductible.** The
   per-adult-child deduction cap (CGI art. 156, II, 2°) and legal eligibility
   checks are not enforced (matching `openfisca-france`), and
   `revenu_net_imposable` is floored at zero (no multi-year deficit carry-forward).
7. **Widowed parents with dependants receive single-declarant parts.** CGI art.
   194 grants a *veuf/veuve* with dependent children the base parts of a married
   couple (2,5 parts with one child); without a marital-status input, the model
   assigns single-declarant parts (1,5 or 2 with `parent_isole`).
8. **AF means-testing uses current-year (N) `salaire_imposable + pensions_imposables`
   instead of N-2.** Both the 3-tranche modulation and *complément dégressif*
   (CSS art. D521-1) read current-year family `salaire_imposable` and
   `pensions_imposables` rather than N-2 *revenu net catégoriel* (CSS art.
   R532-3, omitting rental income). Shared custody (*garde alternée*), the
   age-20 flat allowance, and minimum payment floor are not modelled.
9. **ASF is computed at the family total on a single-parent proxy.** Eligibility
   is inferred solely from `nb_parents == 1`, and the differential offset
   (`max(asf_pleine - pension/12, 0)`) is netted at the family level rather than
   child by child. Orphan *taux majoré*, defaulting parent within a couple, and
   CAF↔debtor recovery are not modelled.
10. **Family and solidarity benefits are paid gross of 0,5 % CRDS, and AF age-14
    majoration starts on the birthday period.** AF, ASF, and Prime d'activité are
    credited gross in `revenu_disponible`, and the AF age-14 supplement starts on
    the 14th-birthday period rather than the following month.
11. **RSA smooths annual incomes (`/ 12`), applies *forfait logement*
    unconditionally, and simplifies eligibility.** `rsa_base_ressources` divides
    annual `salaire_net`, `pension_retraite_nette`, `pensions_alimentaires_percues`,
    `revenus_capital`, and `revenus_fonciers_nets` by 12 instead of quarterly CAF
    declarations (CASF art. R262-7) and counts AF at its unmodulated Tranche-1
    base; *forfait logement* is deducted for every eligible household; every
    `ENFANT` under 25 is treated as *à charge* (art. R262-3); single-parent *RSA
    majoré* has no duration cap (art. L262-9); *RSA jeune actif* (< 25 with 2
    years of work, art. L262-7-1), the 3 % imputed return on dormant liquid
    savings (art. R132-1), and paid-alimony deductions are not modelled.
12. **Prime d'activité smooths annual incomes (`/ 12`), reads 1-January SMIC in
    bonification, applies *forfait logement* unconditionally, and omits the
    student/apprentice floor.** Monthly activity income (`salaire_net / 12`) and
    other resources from `rsa_base_ressources` (including `revenus_capital` and
    `revenus_fonciers_nets`) are annual figures divided by 12; `ppa_bonification`
    evaluates the hourly SMIC as of 1 January (`period.this_year`); *forfait
    logement* is applied unconditionally; and the ~0,78 SMIC net activity-income
    floor for working students and apprentices (CSS art. L842-2) is not enforced.
13. **Capital, rental, and real-estate CGT apply flat regimes without the
    progressive-barème option or holding-period tapers.** `revenus_capital` is
    taxed at the 12,8 % PFU (no progressive-barème election or 40 % dividend
    allowance) plus 17,2 % social levies in 2024–2025 and 18,6 % from
    `2026-01-01` (*produits de placement* effective date under LFSS 2026 art. 12
    II, whereas roll-assessed securities gains shifted on 2025 income); *régime
    réel* rental losses do not offset global income (10 700 € cap, CGI art. 156,
    I, 3°); and `plus_values_immobilieres` is entered net of holding-period
    tapers (CGI art. 150 VC) and omits the art. 1609 nonies G surtax.
14. **CEHR omits exceptional-income quotient smoothing and IFI omits the 75 % cap.**
    CEHR (CGI art. 223 sexies) is evaluated on current RFR without
    exceptional-income smoothing, and IFI models the 30 % principal-residence
    abatement, strict `> 1 300 000 €` threshold (CGI art. 964), and 1,3–1,4 M€
    décote without charitable-gift reductions (CGI art. 978) or the 75 % income
    cap (*plafonnement*, CGI art. 979).
15. **Local property taxes take household local tax bills as direct inputs.**
    `taxe_fonciere` and `taxe_habitation_residence_secondaire` add the 3 % State
    management fee (CGI art. 1641) to input `taxe_fonciere_locale` and
    `thrs_locale` without computing cadastral rental values or municipal rate
    schedules and without age- or RFR-based reliefs.
16. **Metropolitan France only.** DOM income-tax reductions (30 % / 40 %, CGI
    art. 197, I, 3), overseas benefit schedules (RSA, AF, LODEOM), and
    Alsace-Moselle local rules are not modelled.

---

## ❌ What is missing from the tax-benefit system

- **Differential high-income tax (CDHR)** — *contribution différentielle sur les
  hauts revenus* (20 % minimum rate, CGI art. 224, created by LFI 2025 art. 10
  for 2025 incomes).
- **Income tax reductions & credits** — childcare (*frais de garde*), domestic
  employment (*emploi à domicile*), charitable donations, Pinel/Denormandie.
- **Housing benefits** — APL, ALS, ALF (Stage B4 of the benefit roadmap).
- **Other family, disability & minimum-old-age benefits** — PAJE, *complément
  familial*, ARS, AAH, AEEH, ASPA, Bourses scolaires.
- **Non-pension replacement income** — unemployment insurance (ARE) and daily
  sickness/maternity allowances (*indemnités journalières*).
- **Self-employed & unincorporated business income** — BIC, BNC, BA,
  *micro-entrepreneurs*.
- **Overseas departments (DOM)** and special / civil-service pension & contribution
  schemes.
