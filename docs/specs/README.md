# Implementation specs — policyengine-fr

Detailed specs for the high-priority "do first" items from the 2026-07 external
review (weekend-review `findings/policyengine-fr/`). One file per task. These
are drafts for the maintainer, not committed roadmap.

| # | Spec | Priority | Depends on | Status |
|---|---|---|---|---|
| 0001 | [Resolve `salaire_brut` input semantics](0001-salary-input-semantics.md) | P0 blocker | — | **Implemented** (PR #27) |
| 0002 | [Revenu de solidarité active (RSA)](0002-rsa.md) | P1 | 0001 | **Implemented** (PR #27) |
| 0003 | [Enable the statute-review CI gate](0003-enable-statute-review-gate.md) | P1 | — | **Active** (advisory) |
| 0004 | [Accurate employee cotisations](0004-employee-cotisations.md) | P1 | 0001 | Draft |
| 0005 | [Retirement pensions + shared abattement merge](0005-retirement-pensions.md) | P2 | 0001, 0006 | Draft |
| 0006 | [CSG reduced rates (replacement income)](0006-csg-reduced-rates.md) | P2 | 0001 | Draft |
| 0007 | [Multi-year parameterisation](0007-multi-year.md) | P2 | — | Draft |
| 0008 | [Employer cotisations + réduction générale](0008-employer-cotisations.md) | P2 | 0001, 0004 | Draft |

**Design & strategic decisions** (the non-code choices around these specs) live
in [STRATEGY.md](STRATEGY.md): upstreaming with PolicyEngine, the release cut,
the benefit-roadmap ordering, feedback surface, doc-currency automation, and
dependency/lint posture.

**Sequencing.** 0001 first (done — it fixed the income base every benefit needs).
0003 is active. 0002 (RSA) done. Next: **0004** refines the 0001 flat cotisations
rate; **0006** (CSG bands) should precede or accompany **0005** (retirement
pensions), which also resolves the shared-abattement double-count; **0007**
(multi-year) is an independent enabler, best done after 0004/0006 stabilise the
year-sensitive rates; **0008** (employer cotisations + réduction générale) is an
additive labour-cost layer, after 0004 (shares the PASS/per-risk pattern) and only
when a coût-du-travail or reform question needs it.

**Still not specced** (deferred as lower priority or non-code): the v0.2.0
release/changelog cut, ASF majoré / garde alternée / DOM, prime d'activité, APL,
and contacting the upstream PolicyEngine org (draft in `docs/upstream-proposal.md`
on the strategy branch). See `findings/policyengine-fr/PENDING_NEXT_STEPS.md` and
`PROPOSED_NEXT_STEPS.md` for the full list and rationale.
