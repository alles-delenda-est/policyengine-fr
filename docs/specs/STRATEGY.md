# Design & strategic steps — policyengine-fr

Companion to the implementation specs (0001–0003). These are the **decisions**,
not the builds: choices about direction, positioning and process that shape (and
are shaped by) the specced work. Each carries: **Why**, **Interaction with the
specs**, **Pros / Cons**, **Next best alternative**.

Ordered roughly by leverage.

---

## S1 — Settle the relationship with the upstream PolicyEngine org

**Why.** This package is a *new country model*, not a fork: it consumes
`policyengine-core` as a pip dependency and copies `policyengine-canada`'s
structure. The strategic promise ("the API and web app are already multi-country
and introspect the country package — app/API come for free") **only materialises
if the package lives where that infrastructure looks**: PolicyEngine's API/app
load country packages from their own org's releases. Today it sits in a personal
account, is not on PyPI, has never cut a release, and `pyproject` used to point
Homepage at `PolicyEngine/policyengine-fr` (aspirationally). Until this is
settled, the honest description is "a self-contained library runnable via
policyengine-core", not "France in the PolicyEngine app". There is also a
name-squatting risk: anyone can claim `policyengine-fr` on PyPI today.

**Interaction with the specs.** Upstream of the release decision (S2) and the
doc-currency work (S5). It does **not** block 0001/0002/0003 — the modelling is
identical whether the repo stays independent or is transferred. But it should be
resolved *before* investing in app/API-facing polish, and before the first
public release names a home.

**Pros / Cons.**
- Transferring to the PolicyEngine org: unlocks the free app/API, gives the
  model reach and a maintenance community, resolves the PyPI-name risk.
  *Cons:* cedes governance/roadmap control; ties release cadence to upstream;
  requires their acceptance and a country-registry integration.
- Staying independent: full control, no external dependency on another org's
  goodwill. *Cons:* no free app/API, must build any UI oneself, and the
  "PolicyEngine France" framing becomes misleading.

**Next best alternative.** If upstream is unreachable or declines: stay
independent, **register the PyPI name defensively now**, and fix all outward
framing to "policyengine-core-based French microsim library" (drop any "in the
PolicyEngine app" language). A one-hour conversation with the PolicyEngine team
eliminates a rework risk that grows with every feature — do that first.

---

## S2 — Cut a real v0.1.0 (changelog + tag + release)

**Why.** `towncrier` is configured with ~24 waiting fragments but `CHANGELOG.md`
has never been generated; there is no git tag, no GitHub release. Versioned
releases are a prerequisite to anyone depending on the package (incl. upstream),
and cutting one flushes the towncrier pipeline so the CI fragment-gate keeps
meaning something.

**Interaction with the specs.** Should happen **after** 0001 (salary-input) so
the first release doesn't ship the known-inconsistent semantics as "v0.1.0". Pairs
naturally with S1 (a release needs to know its home/PyPI name). 0003 (statute
gate) ideally guards the release PR.

**Pros / Cons.** Pro: makes the project citable and installable, sets a baseline
for change tracking, signals maturity. Con: a version number implies a stability
contract; cutting it before the salary-input convention is fixed would bake the
inconsistency into a tagged artifact people pin to.

**Next best alternative.** If S1 is unresolved, cut an internal `v0.0.x`
pre-release (tag only, no PyPI) purely to flush the changelog and exercise the
pipeline, deferring the PyPI publish until the name/home is decided.

---

## S3 — Fix the benefit roadmap ordering (and where pensions sit)

**Why.** The stated order — RSA → prime d'activité → APL — is right by
distributional impact (these dominate low-income budgets). The review's one
correction: **sequence all three after the salary-input fix** (Spec 0001),
because each is means-tested on net/declared-income concepts the current input
can't represent honestly. Retirement pensions are a separate track with a subtle
double-abattement risk (the shared 10 % floor/ceiling must be merged with
pensions alimentaires).

**Interaction with the specs.** 0002 (RSA) is the first concrete step of this
roadmap and already encodes the "after 0001" dependency. This item is the
*meta-decision*: commit to the ordering and the gating, so specs for prime
d'activité and APL can be written against a stable resource base (the
`rsa_base_ressources` machinery in 0002 is deliberately reusable).

**Pros / Cons.** Pro (RSA-first): maximum distributional relevance, proves the
famille-aggregation + resource-base pattern once for all three. Con: benefits
are the largest, subtlest surface; each needs its own oracle capture and
scope-narrowing discipline — slower than tax-side work.

**Next best alternative.** If a specific policy question needs prime d'activité
or APL sooner, reorder — but never build any of them before 0001, or the
inconsistency bakes into every benefit's resource base.

---

## S4 — Open a contribution/feedback surface

**Why.** No issue templates, no CONTRIBUTING, no contact path. The CoWork
validation brief tells an *agent* to report divergences "to Patrick (email/Slack)"
with no address. A model whose credibility strategy is "named simplifications +
oracles" must let outsiders file counter-examples — it is a first-class review
criterion and an afternoon of work.

**Interaction with the specs.** Complements 0003 (statute gate) — the gate is the
*internal* adversarial check, this is the *external* one. Independent of the
modelling specs.

**Pros / Cons.** Pro: cheap, closes the weakest scored dimension, turns readers
who find errors into contributors. Con: creates an inbound queue someone must
triage; low value if the project stays private/personal.

**Next best alternative.** A single `.github/ISSUE_TEMPLATE/model-error.yaml`
(household, expected vs actual, official source) + a "Found an error?" README
section — the minimal version — if a full CONTRIBUTING is premature.

---

## S5 — Automate doc currency (single source of truth)

**Why.** The repo's front-door docs contradicting its actual state (test counts,
missing benefits) is a *recurring* failure mode of the autonomous-build workflow
— this review fixed it once (PR #25) but it will rot again. Generating the
README/CLAUDE status block and the docs chain table from `modelled_policies.yaml`
(or a CI check that fails when stated test count ≠ collected count) makes the
drift structurally impossible instead of relying on discipline.

**Interaction with the specs.** Every future benefit spec (0002 and beyond) adds
a row to modelled_policies + coverage.md; this automation removes the manual
sync step those specs currently require, and the CI check pairs with 0003.

**Pros / Cons.** Pro: kills a whole class of the review's findings permanently;
small one-time cost. Con: generated-doc tooling is itself code to maintain; a
too-clever generator can be more fragile than the discipline it replaces.

**Next best alternative.** The lighter version: a CI check that only asserts
"stated test count == collected count" and "every modelled_policies entry appears
in coverage.md", failing the build on drift — catches the worst offenders without
a full doc generator.

---

## S6 — Dependency-pinning & lint-hardening posture

**Why.** `policyengine_core>=3.23.6` has no upper bound — an engine major bump
could silently break the model. Ruff has many `F`-checks disabled (incl. F821
undefined-name), so a typo'd variable name sails through. Cheap resilience for a
model whose value is correctness.

**Interaction with the specs.** Orthogonal to the modelling specs but protective
of them: a payslip-identity property test (Spec 0001 §5) is worth little if a
core upgrade can change engine semantics unnoticed. Fold into the same PR as S2's
release hygiene.

**Pros / Cons.** Pro: cheap, prevents a class of silent breakage. Con: an upper
bound needs periodic bumping (maintenance); re-enabling F-checks may surface
churn in the `import *` idiom that needs `# noqa`.

**Next best alternative.** Minimal: pin `>=3.23.6,<4` and re-enable **only**
F821 (undefined-name) with targeted `# noqa` for the wildcard imports — the
highest-value check for the least churn.

---

### Explicitly parked (not strategic decisions — scope/timing only)
Multi-year parameterisation (data entry + oracle re-capture when a 2025/2026
question arises), CSG reduced rates (needs replacement income first), ASF taux
majoré / garde alternée / DOM (niche populations). See
`findings/policyengine-fr/PENDING_NEXT_STEPS.md`.
