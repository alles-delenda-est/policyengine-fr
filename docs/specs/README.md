# Implementation specs — policyengine-fr

Detailed specs for the high-priority "do first" items from the 2026-07 external
review (weekend-review `findings/policyengine-fr/`). One file per task. These
are drafts for the maintainer, not committed roadmap.

| # | Spec | Priority | Depends on | Status |
|---|---|---|---|---|
| 0001 | [Resolve `salaire_brut` input semantics](0001-salary-input-semantics.md) | P0 blocker | — | Draft |
| 0002 | [Revenu de solidarité active (RSA)](0002-rsa.md) | P1 | 0001 | Draft |
| 0003 | [Enable the statute-review CI gate](0003-enable-statute-review-gate.md) | P1 | — | Draft |

**Sequencing.** 0001 first (it invalidates any oracle captured after it, and
every means-tested benefit depends on a coherent resource base). 0003 can land
in parallel (config-only) and will help review 0002. 0002 last.

**Not specced here** (deferred per the review as lower priority or non-code):
retirement pensions + shared abattement merge, CSG reduced rates, multi-year
parameterisation, the v0.2.0 release/changelog cut, ASF majoré / garde alternée
/ DOM, contacting the upstream PolicyEngine org. See
`findings/policyengine-fr/PENDING_NEXT_STEPS.md` and `PROPOSED_NEXT_STEPS.md`
for the full list and rationale.
