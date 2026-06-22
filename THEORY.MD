# Theory: Hardening the policyengine-fr Test Suite

## Problem

The French tax-benefit model (`policyengine-fr`) has a working MVP covering the
full disposable-income chain (salaire → IR → CSG/CRDS → AF → revenu_disponible),
but the test suite has been primarily composed of self-authored unit tests that
verify known reference values. Self-authored tests have a structural blindspot:
they cannot catch sign errors, missing monotonicity, or broken invariants that
the author didn't think to assert — they only prove "the model produces the same
number I wrote down."

The goal of this hardening work is to add a second layer: tests that enforce
mathematical and legal invariants independently of any particular reference value.

## Operating Theory

Two complementary test strategies are in play:

**YAML unit tests** (run by `policyengine-core test`) verify specific numeric
outputs against known reference values derived from the statute. These are
excellent for regression prevention and for documenting the model's expected
behaviour at particular points. The CSG/CRDS file has been extended to cover:
the high-income uncapped case (200 000 €, demonstrating no plafonnnement applies
to activité contributions) and a decomposition test (37 000 €, asserting
csg_déductible + csg_imposable = csg_totale at a specific salary).

**Pytest property invariants** (deterministic grid, no fuzzing library) assert
structural properties that must hold across a grid of incomes and child counts
regardless of exact values. These catch whole classes of bugs:
- `test_af_non_negative` / `test_af_zero_below_two_children`: legal eligibility
  rules (AF requires ≥ 2 children under 20).
- `test_af_monotonic_non_increasing_in_resources`: modulation — higher income
  must never increase AF (taux plein → demi → quart).
- `test_csg_identity` / `test_assiette_identity`: arithmetic identities in the
  CSG/CRDS formulas.

## Strategy

The overall sequencing is:
1. Lock down reference-value tests first (the 55→57 YAML expansion).
2. Then overlay invariant tests that catch structural failures without
   duplicating the numeric checks.
3. Keep the two layers independent: YAML tests fail when numbers are wrong,
   property tests fail when laws or arithmetic are violated.

This separation means a future change that accidentally breaks a monotonicity
property will be caught by the property tests even if it doesn't change any
reference value that was explicitly tested.

## Key Discoveries

**Float32 precision and identity tests**: The initial specification asked for
`abs_tol=1e-6` on the CSG arithmetic identity (`csg == csg_deductible +
csg_imposable`). This failed because PolicyEngine uses numpy float32 arrays;
computing `assiette * 0.068`, `assiette * 0.024`, and `assiette * 0.092`
independently in float32 produces independent rounding errors that accumulate to
~3e-5 — three orders of magnitude above 1e-6 but well within the model's
intended precision. The identity is mathematically correct; the tolerance must
be set to 0.01 (consistent with the suite's `absolute_error_margin`) to avoid
false positives from float32 arithmetic rather than model errors.

This is an important pattern: any "identity" test in this codebase must be
calibrated to float32 noise (~1e-4 relative), not machine-epsilon.

**AF monotonicity holds**: The modulation property (AF weakly decreasing as
income rises across the plafond thresholds) passed cleanly across the grid. This
confirms the modulation formula is correctly wired up.

## Open Questions

- Whether the AF modulation thresholds themselves (the plafonds that determine
  taux plein / demi / quart) are correctly parameterised for 2024 remains a
  validation task for the independent-oracle review (see
  docs/cowork-validation-brief.md). The monotonicity test proves the logic is
  directionally correct, not that the exact thresholds are right.
- CSG rates are currently modelled as flat (9.2 % total) on salary. The statute
  also provides reduced rates (3.8 % / 6.2 %) for low earners on pension income;
  this is out of scope for the current MVP but should be flagged when that
  revenue type is added.
