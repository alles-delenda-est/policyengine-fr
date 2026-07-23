# Coverage map — what `policyengine-fr` does and doesn't model

> **Human-readable companion to [`policyengine_fr/modelled_policies.yaml`](../policyengine_fr/modelled_policies.yaml).**
> That YAML is the machine-readable modelled / not-modelled boundary (and the
> reviewer-gate's source of truth); this document is the narrative version for
> readers. Keep the two in sync — when a policy is added or a simplification
> changes, update both.
>
> **State as of 2026-07-08** (post-review disclosure pass). Scope:
> **revenus 2024, métropole**, a single tax year.

## One-line summary

This is a **disposable-income MVP for a wage-earning métropole household in
2024**. It models income tax (IR) properly, CSG/CRDS and a flat-rate employee
cotisations layer on salary, and the two family benefits AF + ASF, the **RSA socle** (the first means-tested benefit),
aggregated into a household `revenu_disponible`. The salary input is **true
gross**; a flat effective cotisations rate derives the declared salary (case
1AJ) the IR chain uses. It is **not** yet a full payslip calculator (the
cotisations rate is a flat approximation, not a per-risk payslip); the
means-tested layer covers **RSA socle only** (no prime d'activité / APL), and it
only understands **salary** and **pensions alimentaires** as income.

---

## ✅ What is modelled

### Income tax — impôt sur le revenu (DGFiP)

The full chain from gross salary to net tax is modelled end-to-end:

- **Salaire déclaré (case 1AJ)** — gross salary less the flat-rate employee
  cotisations and the deductible CSG (the CGI art. 154 quinquies deduction,
  applied once here)
- **Salaire imposable** — declared salary less the 10 % professional-expenses
  abattement (with floor and ceiling)
- **Pensions alimentaires** — received pensions are taxable after a 10 %
  abattement (floor per beneficiary, ceiling per foyer fiscal); paid pensions are
  deducted from global income
- **Revenu net imposable** — the assembled taxable base
- **Nombre de parts** — quotient familial: declarants + dependants, plus the
  parent-isolé extra half-part
- **Impôt brut** — the progressive barème applied per part
- **Plafonnement du quotient familial** — caps the advantage of extra parts
- **Décote** — relief for low tax liabilities
- **Impôt sur le revenu** — the final net figure

### Social levies on salary (URSSAF)

- **Cotisations salariales** — per-risk (vieillesse plafonnée/déplafonnée,
  AGIRC-ARRCO retraite + CEG T1/T2, and CET/APEC for cadres), with PASS-delimited
  tranches, taking gross salary to declared salary
- **CSG** on activity income — assiette 98,25 %, split into deductible and
  imposable portions
- **CRDS** on activity income

### Family benefits (CNAF)

- **Allocations familiales** — base amount, income-based modulation (3 tranches),
  age majoration
- **Allocation de soutien familial (ASF)** — taux simple, paid as a *complément
  différentiel* (received pension alimentaire netted off), single-parent famille

### Means-tested benefits (CNAF)

- **RSA socle** — the differential minimum-income top-up:
  `max(montant forfaitaire − forfait logement − base ressources, 0)`. Models the
  equivalence scale (couple + per-child majorations, and the RSA *majoré* for a
  single parent), the forfait logement, and a differential base ressources that
  includes salary, pensions alimentaires, AF and ASF.

### Aggregate

- **Revenu disponible** — the household top-line: gross salary less cotisations,
  CSG/CRDS and net IR, plus AF + ASF

### Inputs accepted

Salaire brut (**true gross**), age, parent-isolé flag, pensions alimentaires
perçues, pensions alimentaires versées.

---

## ⚠️ Partial coverage — caveats *inside* what is modelled

These are modelled, but with a documented departure from the exact statute. (The
authoritative list with legal references lives under `simplifications:` in
`modelled_policies.yaml`.)

1. **Employee cotisations are modelled per-risk but not a full payslip.** Gross
   salary is taken to declared salary (case 1AJ) via the per-risk employee
   schedule (vieillesse plafonnée/déplafonnée, AGIRC-ARRCO retraite + CEG T1/T2,
   CET/APEC for cadres) with PASS-delimited tranches, plus the deductible CSG
   (applied once, in `salaire_declare`). This resolves the former dual
   brut/déclaré convention. Still out of scope: chômage/maladie salariales (0 %
   since 2018), specific exonérations (heures sup, apprentis, ZRR), and the
   `cadre` flag when unknown (defaults non-cadre). The **low-wage réduction
   générale is employer-side** (docs/specs/0008), not modelled here.
2. **AF income test uses a proxy.** The modulation uses current-year (N) salary
   instead of the legal N-2 *base ressources* (revenu net catégoriel, art. R532-3
   CSS). Identical for stable incomes; diverges when income changed year-on-year.
3. **AF modulation has hard cliffs.** The statutory *complément dégressif*
   (CSS art. D521-1, al. 3) that tapers each threshold crossing is not modelled:
   a family €1 over a plafond loses the full tranche (~€745/year at the first
   threshold) instead of being smoothed. Amounts are exact away from the
   thresholds; marginal rates right at them are overstated.
4. **ASF is family-total, not per-child**, and the pension input is assumed to be
   child support — a *prestation compensatoire* (spousal support) entered there
   would wrongly suppress ASF. Taux majoré (orphelin de deux parents) and
   recouvrement (CAF↔débiteur) are not modelled.
5. **Paid pensions alimentaires** are taken as already-deductible — the
   per-major-child deduction ceiling (CGI art. 156, II, 2°) and eligibility
   conditions are not enforced.
6. **CSG is flat 9,2 %** on salary; reduced rates (3,8 % / 6,2 %) for low earners
   and rates on replacement income are out of scope.
7. **Shared 10 % pension abattement.** The floor/ceiling on the pension abattement
   are, in law, common to *all* pensions (retraites incluses). The model applies
   them to pensions alimentaires alone; when retirement pensions are added the
   abattement must be merged to share one floor/ceiling, or it is granted twice.
8. **Benefits are paid gross of CRDS.** AF and ASF are returned at their gross
   amounts; the 0,5 % CRDS due on family benefits is never levied, so
   `revenu_disponible` overstates benefit income by ~0,5 %. The AF age-14
   majoration is also granted from the birthday month instead of the following
   month (one extra month, once per child).
9. **Widowed parents get single-declarant parts.** CGI art. 194 grants a
   veuf/veuve with dependent children the base parts of a married couple
   (e.g. 2,5 parts with one child); the model can only represent them as a
   single declarant (1,5-2 parts), understating parts by 0,5-1.
10. **RSA base ressources is an annual/12 proxy.** The legal base is the average
    of the 3 months before the claim (CASF art. R262-3); the model uses annual
    modelled income ÷ 12. The resource perimeter is limited to what the MVP
    models (salary, pensions alimentaires, AF, ASF); the 3-month activity-income
    neutralisation (art. R262-7) is not applied.
11. **RSA forfait logement is always applied.** Housing status is not modelled,
    so the forfait logement (art. R262-9) is always deducted (assumes a housing
    aid or free lodging). A renter with no housing aid would see RSA understated
    by the forfait.
12. **RSA is socle-only, isolement by proxy.** Only the RSA socle is modelled (no
    prime d'activité, RSA jeune, intéressement, contrat d'engagement/sanctions).
    RSA *majoré* (single parent) is triggered by the "one parent with a child"
    proxy, and its duration limit (until the youngest turns 3) is not modelled.

---

## ❌ What is missing from the tax-benefit system

### Other income taxes

- Réductions et crédits d'impôt (dons, emploi à domicile, frais de garde, …)
- Contribution exceptionnelle sur les hauts revenus (CEHR)
- Prélèvement forfaitaire unique / flat tax on capital income (PFU, 12,8 %)
- Prélèvements sociaux sur revenus du capital et de remplacement (17,2 %)
- Impôt sur la fortune immobilière (IFI)
- Local taxes — taxe foncière, taxe d'habitation (résidences secondaires)

### Social contributions

- Cotisations sociales salariales **détaillées** — per-risk (maladie, vieillesse,
  chômage, retraite complémentaire), PASS ceilings, cadre status and low-wage
  (SMIC) relief. Only a single flat effective rate is modelled today (see ⚠️ #1)
- Employer contributions (relevant only if modelling from super-brut)
- CSG/CRDS on non-salary income (retirement pensions at reduced rates, capital,
  replacement income)

### Social benefits (the largest gap)

- **RSA** — ✅ socle modelled (see above); still missing: prime d'activité,
  RSA majoré duration, intéressement/cumul, the 3-month resource neutralisation
- **Prime d'activité**
- **Aides au logement** — APL / ALS / ALF
- **Complément familial**
- **PAJE** — allocation de base, prime à la naissance, complément de libre choix
  du mode de garde (CMG)
- **Allocation de rentrée scolaire (ARS)**
- **AAH** (adulte handicapé), **AEEH** (enfant handicapé)
- **ASPA** (minimum vieillesse)
- **ASF taux majoré** (orphelin de deux parents)
- Bourses scolaires

### Income types not handled

The model ingests only **salary** and **pensions alimentaires**. Not modelled:

- Pensions de retraite
- Revenus de remplacement (chômage, indemnités journalières)
- Revenus du capital (dividendes, intérêts, plus-values)
- Revenus fonciers (locatif)
- Revenus non-salariés — BIC / BNC / BA, professions libérales, micro-entreprise,
  agriculteurs

### Structural limits

- **Métropole only** — no DOM-specific rules
- **2024 only** — a single year is parameterised
- Garde alternée (shared custody), forfait des 20 ans, and the AF plancher de
  versement are not modelled
