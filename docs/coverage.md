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

`policyengine-fr` is a **multi-year (2024–2025) static tax-benefit and
patrimonial microsimulation model for France métropolitaine**. From true gross
salary (`salaire_brut`), retirement pensions, child support, capital income, and
real-estate / land endowments, it models employee and employer social
contributions (with the *réduction générale*), income tax (`impot_revenu`, CEHR,
PFU, rental and capital-gains taxes), property and land taxes (`ifi`,
`taxe_fonciere`, `taxe_habitation_residence_secondaire`, `taxe_valeur_sol`), and
major family and working-age benefits (`allocations_familiales`,
`allocation_soutien_familial`, `rsa`, `prime_activite`), aggregated into
household `revenu_disponible` and employer `cout_du_travail`.

---

## ✅ What is modelled

### Payslip & labour cost — social contributions (URSSAF / AGIRC-ARRCO)

- **Cotisations salariales (`cotisations_salariales`)** — per-risk PASS-bracketed
  employee contributions: vieillesse plafonnée (1 PASS) & déplafonnée,
  AGIRC-ARRCO Tranche 1 & Tranche 2 (1–8 PASS), CEG T1 & T2, CET (0–8 PASS when
  `salaire_brut > 1 PASS`), and APEC (`cadre=True`).
- **CSG / CRDS on salary (`csg`, `crds`)** — 98,25 % assiette; 6,8 % deductible
  CSG deducted to form `salaire_declare` (case 1AJ), and 2,4 % non-deductible CSG
  + 0,5 % CRDS deducted to form `salaire_net` (net perçu avant IR).
- **Cotisations patronales (`cotisations_patronales`), `reduction_generale` &
  `cout_du_travail`** — employer maladie and famille (with 2024 and 2025 LFSS
  SMIC bandeaux), vieillesse, chômage, AGS, FNAL (`< 50` vs `>= 50` employees),
  AT/MP, AGIRC-ARRCO, CEG, CET, APEC, CSA, net of the degressive *réduction
  générale* (ex-Fillon up to 1,6 SMIC), yielding super-brut `cout_du_travail`.

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
  up to 15 000 € or réel), optional barème capital income, deduction of paid
  alimony (`pensions_alimentaires_versees`) and 6,8 % deductible patrimonial CSG
  → `revenu_net_imposable` → `nombre_parts` (quotient familial + parent isolé) →
  `impot_brut` → `plafonnement_quotient_familial` → `decote` → `impot_revenu`.
- **Revenu fiscal de référence (`revenu_fiscal_de_reference`)** and **CEHR
  (`cehr`)** — 3 % / 4 % high-income surtax (250 k€ / 500 k€ single; doubled for
  couples).
- **PFU & patrimonial levies (`pfu_ir`, `prelevements_sociaux_patrimoine`,
  `impot_plus_values_immobilieres`)** — 12,8 % flat tax on `revenus_capitaux_mobiliers_pfu`
  (unless `option_bareme_rcm`), 19 % IR on `plus_values_immobilieres`, and 17,2 %
  social levies across PFU capital, net rental income, and real-estate gains.
- **IFI (`ifi`)** — 30 % principal-residence abatement, 1,3 M€ entry threshold
  with progressive brackets from 800 k€, and 1,3–1,4 M€ décote.
- **Local & land taxes (`taxe_fonciere`, `taxe_habitation_residence_secondaire`,
  `taxe_valeur_sol`)** — cadastral / land-value taxes with the 3 % State
  management fee (CGI art. 1641), paired with parameterised reforms in
  `policyengine_fr.reforms` (`lvt_shift` S1–S3_IFI and `budget_levers`).

### Family & solidarity benefits (CNAF)

- **Allocations familiales (`allocations_familiales`)** — base by child count
  (2+), income modulation across 3 tranches with the statutory **complément
  dégressif** (CSS art. D521-1, al. 3), and age-14 majoration.
- **Allocation de soutien familial (`allocation_soutien_familial`)** — taux
  simple (0,422 BMAF), paid as a *complément différentiel* net of received child
  support for single-parent families.
- **Revenu de solidarité active (`rsa`)** — `rsa_montant_forfaitaire` (including
  *RSA majoré* for single parents), `rsa_forfait_logement`, `rsa_base_ressources`
  (`salaire_net`, `pension_retraite_nette`, AF excluding age majorations per CASF
  art. R262-11 3°, and forfaitised ASF `min(asf, 0,225 BMAF)` per art. R262-10-1),
  age ≥ 25 or dependent-child eligibility (art. L262-4), and 6 €/month minimum
  payment threshold (art. R262-39).
- **Prime d'activité (`prime_activite`)** — `ppa_montant_forfaitaire`, individual
  `ppa_bonification` ramping linearly between 59 and 120 hourly SMIC, 61 % slope on
  professional income, `ppa_forfait_logement`, netting off non-bonified RSA, and
  15 €/month minimum payment threshold.

### Aggregates

- **`revenu_disponible`** (`menage`) — net household disposable income combining
  net wages, net pensions, child support, net capital/rental/gain cashflows, plus
  AF, ASF, RSA, and Prime d'activité, minus IR, CEHR, PFU, patrimonial PS,
  real-estate CGT, IFI, TFPB, THRS, and LVT.
- **`cout_du_travail`** (`individu`) — total employer cost (`salaire_brut + cotisations_patronales`).

---

## ⚠️ Partial coverage — caveats *inside* what is modelled

These policies are modelled, with every departure from exact statute explicitly
enumerated below and mirrored 1-for-1 under `simplifications:` in
`policyengine_fr/modelled_policies.yaml`:

1. **Employee cotisations cover full-time general private-sector rules only.**
   `cotisations_salariales` models a standard non-agricultural private-sector
   employee (`cadre=False` by default, or `cadre=True` for APEC) without
   mandatory employer health-insurance (*mutuelle*), tax-exempt overtime,
   apprenticeship exemptions, civil-service / special schemes, or Alsace-Moselle
   additional sickness levy. Activity CSG uses the standard 9,2 % rate on 98,25 %
   of gross pay.
2. **Employer cotisations and *réduction générale* assume full-time annual SMIC.**
   The health and family rate bandeaux and the Fillon degressive reduction
   (`< 1,6 SMIC`, split by `effectif_entreprise` `< 50` vs `>= 50`) compare
   annual pay against full-time annual SMIC (1 820 h) without part-time hourly
   proration, and omit local *versement mobilité*, *forfait social*, DFS, and
   geographic exemptions (ZRR, ZFU, JEI, LODEOM).
3. **Pension CSG/CRDS/CASA uses current-year RFR instead of N-2.** The four-tier
   replacement CSG schedule (0 % / 3,8 % / 6,6 % / 8,3 %; CSS art. L136-8 III)
   and 0,3 % CASA (CASF art. L14-10-4) read current-year `revenu_fiscal_de_reference`
   rather than N-2 RFR and do not model the two-consecutive-year upward-crossing
   smoothing rule (CSS art. L136-8 III bis).
4. **`revenu_fiscal_de_reference` spans modelled income categories only.** RFR
   (CGI art. 1417, IV) sums `revenu_net_imposable` and flat-taxed capital income
   (`revenus_capitaux_mobiliers_pfu` when `option_bareme_rcm` is false), omitting
   exempt equity gains, deducted retirement-savings contributions, and unmodelled
   exempt foreign incomes.
5. **Shared 10 % pension abattement caps at the foyer total without per-person
   proration.** Individual floors are bounded by each member's combined
   `pension_retraite_declaree + pensions_alimentaires_percues`, and the foyer sum
   is capped at the statutory foyer ceiling (CGI art. 158, 5, a) without
   allocating the cap back across individual declarants.
6. **Paid `pensions_alimentaires_versees` are taken as already deductible.** The
   per-adult-child deduction cap (CGI art. 156, II, 2°) and legal eligibility
   checks are not enforced (matching `openfisca-france`), and `revenu_net_imposable`
   is floored at zero (no multi-year deficit carry-forward).
7. **Widowed parents with dependants receive single-declarant parts.** CGI art.
   194 grants a *veuf/veuve* with dependent children the base parts of a married
   couple (2,5 parts with one child); without a marital-status input, the model
   assigns single-declarant parts (1,5 or 2 with `parent_isole`).
8. **AF means-testing uses current-year (N) taxable income instead of N-2.** Both
   the 3-tranche modulation and *complément dégressif* (CSS art. D521-1) read
   current-year parental `salaire_imposable + pensions_imposables` rather than N-2
   *revenu net catégoriel* (CSS art. R532-3). Shared custody (*garde alternée*),
   the age-20 flat allowance, and minimum payment floor are not modelled.
9. **ASF is computed at the family total on a single-parent proxy.** Eligibility
   is inferred solely from `nb_parents == 1`, and the differential offset
   (`max(asf_pleine - pension/12, 0)`) is netted at the family level rather than
   child by child. Orphan *taux majoré*, defaulting parent within a couple, and
   CAF↔debtor recovery are not modelled.
10. **Family and solidarity benefits are paid gross of 0,5 % CRDS, and AF age-14
    majoration starts on the birthday period.** AF, ASF, and Prime d'activité are
    credited gross in `revenu_disponible`, and the AF age-14 supplement starts on
    the 14th-birthday period rather than the following month.
11. **RSA smooths annual net income (`/ 12`), applies *forfait logement*
    unconditionally, and simplifies eligibility.** `rsa_base_ressources` divides
    annual `salaire_net` and `pension_retraite_nette` by 12 instead of quarterly
    CAF declarations (CASF art. R262-7); *forfait logement* is deducted for every
    eligible household; single-parent *RSA majoré* has no duration cap (art.
    L262-9); *RSA jeune actif* (< 25 with 2 years of work, art. L262-7-1) and the
    3 % imputed return on liquid savings are not modelled.
12. **Prime d'activité smooths annual income (`/ 12`), applies *forfait logement*
    unconditionally, and omits the student/apprentice floor.** Monthly activity
    and replacement resources are annual figures divided by 12; *forfait logement*
    is applied unconditionally; and the ~0,78 SMIC net activity-income floor for
    working students and apprentices (CSS art. L842-2) is not enforced.
13. **Capital, rental, and real-estate CGT omit holding-period tapers and global
    deficit offsets.** `option_bareme_rcm` does not apply the 40 % dividend
    allowance; *régime réel* rental losses do not offset global income up to the
    10 700 € cap (CGI art. 156, I, 3°); and input `plus_values_immobilieres` is
    taken as already net of holding-period allowances (CGI art. 150 VC) and omits
    the art. 1609 nonies G high-gain surtax.
14. **CEHR omits exceptional-income quotient smoothing and IFI omits the 75 % cap.**
    CEHR (CGI art. 223 sexies) is evaluated on current RFR without exceptional-income
    smoothing, and IFI models the 30 % principal-residence abatement and 1,3–1,4 M€
    décote without charitable-gift reductions (CGI art. 978) or the 75 % income
    cap (*plafonnement*, CGI art. 979).
15. **Local property taxes default to national average rates.** Without commune
    codes or municipal rate tables, `taxe_fonciere` and
    `taxe_habitation_residence_secondaire` use national average DGFiP rates
    (overridable per household or via `lvt_shift` reforms) plus the 3 % State
    management fee (CGI art. 1641), without age- or RFR-based exemptions.
16. **Metropolitan France only.** DOM income-tax reductions (30 % / 40 %, CGI
    art. 197, I, 3), overseas benefit schedules (RSA, AF, LODEOM), and
    Alsace-Moselle local rules are not modelled.

---

## ❌ What is missing from the tax-benefit system

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
