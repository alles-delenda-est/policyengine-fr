# Coverage map — what `policyengine-fr` does and doesn't model

> **Human-readable companion to [`policyengine_fr/modelled_policies.yaml`](../policyengine_fr/modelled_policies.yaml).**
> That YAML is the machine-readable modelled / not-modelled boundary (and the
> reviewer-gate's source of truth); this document is the narrative version for
> readers. Keep the two in sync — when a policy is added or a simplification
> changes, update both. **A CI check (`make check-docs`,
> `bin/check_doc_currency.py`) fails the build if the simplification counts here
> and in the YAML diverge, or if the test-count headline in `CLAUDE.md` no longer
> matches the collected tests.**
>
> **State as of 2026-07-08** (post-review disclosure pass). Scope:
> **revenus 2024, métropole**, a single tax year.

## One-line summary

This is a **disposable-income MVP for a wage-earning métropole household in
2024**. It models income tax (IR) properly, CSG/CRDS on salary, and the two
family benefits AF + ASF, aggregated into a household `revenu_disponible`. It is
**not** yet a full payslip calculator (employee social contributions are missing)
nor a means-tested-benefits engine (no RSA / prime d'activité / APL), and it only
understands **salary** and **pensions alimentaires** as income.

---

## ✅ What is modelled

### Income tax — impôt sur le revenu (DGFiP)

The full chain from gross salary to net tax is modelled end-to-end:

- **Salaire imposable** — gross salary less the 10 % professional-expenses
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

- **CSG** on activity income — assiette 98,25 %, split into deductible and
  imposable portions
- **CRDS** on activity income

### Family benefits (CNAF)

- **Allocations familiales** — base amount, income-based modulation (3 tranches),
  age majoration
- **Allocation de soutien familial (ASF)** — taux simple, paid as a *complément
  différentiel* (received pension alimentaire netted off), single-parent famille

### Aggregate

- **Revenu disponible** — the household top-line, combining net-of-tax income +
  AF + ASF

### Inputs accepted

Salaire brut, age, parent-isolé flag, pensions alimentaires perçues, pensions
alimentaires versées.

---

## ⚠️ Partial coverage — caveats *inside* what is modelled

These are modelled, but with a documented departure from the exact statute. (The
authoritative list with legal references lives under `simplifications:` in
`modelled_policies.yaml`.)

1. **`salaire_brut → net` is NOT a full payslip.** Only CSG/CRDS come off salary.
   The other employee contributions (health, retraite, chômage, AGIRC-ARRCO
   complémentaire) are **not** deducted — so "net" here is not take-home pay.
   Worse, the single salary input is read under **two different conventions**:
   the income-tax chain treats it as *declared* salary (1AJ — the convention the
   DGFiP-oracle validation used), while the CSG/CRDS formulas treat it as *gross*
   salary (1,75 % assiette abatement). The two differ by ~20-25 % on a real
   payslip. Entering declared salary gives an exact IR and an under-estimated
   CSG/CRDS; `revenu_disponible` mixes both.
2. **CSG déductible is computed but not deducted.** `csg_deductible` exists as a
   levy, but the deduction from taxable income mandated by CGI art. 154
   quinquies is not applied in `revenu_net_imposable`. Consistent with the
   declared-salary reading of the input (a 1AJ amount is already net of
   deductible CSG); to revisit if the input ever becomes true gross.
3. **AF income test uses a proxy.** The modulation uses current-year (N) salary
   instead of the legal N-2 *base ressources* (revenu net catégoriel, art. R532-3
   CSS). Identical for stable incomes; diverges when income changed year-on-year.
4. **AF modulation has hard cliffs.** The statutory *complément dégressif*
   (CSS art. D521-1, al. 3) that tapers each threshold crossing is not modelled:
   a family €1 over a plafond loses the full tranche (~€745/year at the first
   threshold) instead of being smoothed. Amounts are exact away from the
   thresholds; marginal rates right at them are overstated.
5. **ASF is family-total, not per-child**, and the pension input is assumed to be
   child support — a *prestation compensatoire* (spousal support) entered there
   would wrongly suppress ASF. Taux majoré (orphelin de deux parents) and
   recouvrement (CAF↔débiteur) are not modelled.
6. **Paid pensions alimentaires** are taken as already-deductible — the
   per-major-child deduction ceiling (CGI art. 156, II, 2°) and eligibility
   conditions are not enforced.
7. **CSG is flat 9,2 %** on salary; reduced rates (3,8 % / 6,2 %) for low earners
   and rates on replacement income are out of scope.
8. **Shared 10 % pension abattement.** The floor/ceiling on the pension abattement
   are, in law, common to *all* pensions (retraites incluses). The model applies
   them to pensions alimentaires alone; when retirement pensions are added the
   abattement must be merged to share one floor/ceiling, or it is granted twice.
9. **Benefits are paid gross of CRDS.** AF and ASF are returned at their gross
   amounts; the 0,5 % CRDS due on family benefits is never levied, so
   `revenu_disponible` overstates benefit income by ~0,5 %. The AF age-14
   majoration is also granted from the birthday month instead of the following
   month (one extra month, once per child).
10. **Widowed parents get single-declarant parts.** CGI art. 194 grants a
    veuf/veuve with dependent children the base parts of a married couple
    (e.g. 2,5 parts with one child); the model can only represent them as a
    single declarant (1,5-2 parts), understating parts by 0,5-1.

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

- Cotisations sociales salariales — maladie, vieillesse, chômage, retraite
  complémentaire (the bulk of the brut → net gap)
- Employer contributions (relevant only if modelling from super-brut)
- CSG/CRDS on non-salary income (retirement pensions at reduced rates, capital,
  replacement income)

### Social benefits (the largest gap)

- **RSA** — revenu de solidarité active
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
