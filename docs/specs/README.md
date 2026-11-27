# Implementation specs — policyengine-fr

Detailed specs for the core roadmap items from the 2026 external review and
benefit/fiscal expansion roadmap. One file per task.

| # | Spec | Priority | Depends on | Status |
|---|---|---|---|---|
| 0001 | [Resolve `salaire_brut` input semantics](0001-salary-input-semantics.md) | P0 blocker | — | **Implemented** |
| 0002 | [Revenu de solidarité active (RSA)](0002-rsa.md) | P1 | 0001 | **Implemented** (oracle-validated) |
| 0003 | [Enable the statute-review CI gate](0003-enable-statute-review-gate.md) | P1 | — | **Active** (advisory) |
| 0004 | [Accurate employee cotisations](0004-employee-cotisations.md) | P1 | 0001 | **Implemented** (oracle-validated) |
| 0005 | [Retirement pensions + shared abattement merge](0005-retirement-pensions.md) | P2 | 0001, 0006 | **Implemented** (oracle-validated) |
| 0006 | [CSG reduced rates (replacement income)](0006-csg-reduced-rates.md) | P2 | 0001 | **Implemented** (oracle-validated, + CASA) |
| 0007 | [Multi-year parameterisation (2024–2025)](0007-multi-year.md) | P2 | — | **Implemented** |
| 0008 | [Employer cotisations + réduction générale](0008-employer-cotisations.md) | P2 | 0001, 0004 | **Implemented** |
| 0009 | [Prime d'activité](0009-prime-activite.md) | P1 (Stage B3) | 0001, 0002, 0004 | **Implemented** (oracle-validated) |

**Design & strategic decisions** (the non-code choices around these specs) live
in [STRATEGY.md](STRATEGY.md): upstreaming with PolicyEngine, the release cut,
the benefit-roadmap ordering, feedback surface, doc-currency automation
(`bin/check_doc_currency.py`), and dependency/lint posture.

**Cross-repository extensions** integrated alongside Specs 0001–0009:
- **Patrimonial, capital & local property taxes** (`cehr`, `pfu_ir`,
  `prelevements_sociaux_patrimoine`, `revenus_fonciers_nets`,
  `impot_plus_values_immobilieres`, `ifi`, `taxe_fonciere`,
  `taxe_habitation_residence_secondaire`, `taxe_valeur_sol`).
- **Parameterised reforms** in `policyengine_fr.reforms`: `lvt_shift`
  (`S1`–`S3_IFI` calibrated to `LVTShift` yields) and `budget_levers` (IR/CSG
  rate shifts, brackets freeze, and targeted pension under-indexation D-P6 from
  `budget_fr_sim_test`).

**Next roadmap candidates** (Stage B4+): housing benefits (`APL` / `ALS` / `ALF`),
income-tax credits/reductions, unemployment replacement income (`ARE`), ASF
*taux majoré* / shared custody / DOM schedules, and upstreaming coordination
with the PolicyEngine organisation (`docs/upstream-proposal.md`).
