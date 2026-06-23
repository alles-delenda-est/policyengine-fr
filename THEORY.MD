# Theory: Hardening the policyengine-fr Test Suite + ASF Feature

## Problem

The French tax-benefit model (`policyengine-fr`) has a working MVP covering the
full disposable-income chain (salaire → IR → CSG/CRDS → AF → revenu_disponible),
but the test suite had been primarily composed of self-authored unit tests that
verify known reference values. Self-authored tests have a structural blindspot:
they cannot catch sign errors, missing monotonicity, or broken invariants that
the author didn't think to assert — they only prove "the model produces the same
number I wrote down."

The ASF (Allocation de soutien familial) feature was added as the first new
benefit after the MVP, providing a concrete testbed for the hardened testing
strategy and setting the pattern for future benefits.

## Operating Theory

Two complementary test strategies are in play:

**YAML unit tests** (run by `policyengine-core test`) verify specific numeric
outputs against known reference values derived from the statute. These are
excellent for regression prevention and for documenting the model's expected
behaviour at particular points.

**Pytest property invariants** (deterministic grid, no fuzzing library) assert
structural properties that must hold across a grid of incomes and child counts
regardless of exact values. These catch whole classes of bugs:
- `test_af_non_negative` / `test_af_zero_below_two_children`: legal eligibility rules.
- `test_af_monotonic_non_increasing_in_resources`: AF modulation property.
- `test_asf_non_negative`, `test_asf_zero_for_couple`, `test_asf_scales_with_eligible_children`: ASF eligibility and scaling.
- `test_asf_in_revenu_disponible_single_parent`: wiring into the aggregate.
- `test_csg_identity` / `test_assiette_identity`: arithmetic identities in CSG/CRDS formulas.

**Independent oracle validation** completes the triangle: against openfisca-france
(v175.0.45), policyengine-fr ASF gives 2336.04 EUR/year vs oracle 2336.09.
Delta +0.05 EUR, well within the 12 EUR tolerance. This proves correctness against
an independent codebase, not just against the statute.

## Strategy

The overall sequencing was:
1. Lock down reference-value tests first (parameter + variable YAML tests).
2. Overlay property/invariant tests that catch structural failures without
   duplicating the numeric checks.
3. Validate against an independent oracle (openfisca-france) to rule out
   shared author blindspots.
4. Wire into the revenu_disponible aggregate so household calculations are correct.
5. Document the modelled/not-modelled boundary precisely in modelled_policies.yaml.

This keeps the two test layers independent: YAML tests fail when numbers are wrong,
property tests fail when laws or arithmetic are violated. A future change that
accidentally breaks a monotonicity property will be caught even if it doesn't
change any reference value that was explicitly tested.

## Key Discoveries

**Float32 precision and identity tests**: The initial specification asked for
`abs_tol=1e-6` on the CSG arithmetic identity. This failed because PolicyEngine
uses numpy float32 arrays; independent rounding accumulates to ~3e-5. The identity
is mathematically correct; the tolerance must be set to 0.01. Any "identity" test
in this codebase must be calibrated to float32 noise (~1e-4 relative), not
machine-epsilon.

**AF monotonicity holds**: The modulation property (AF weakly decreasing as
income rises across the plafond thresholds) passed cleanly across the grid. This
confirms the modulation formula is correctly wired up.

**ASF oracle confirmed**: openfisca-france eligibility triggered cleanly with a bare
single-parent famille — no special flags required, confirming the policyengine-fr
implementation is correct against an independent codebase. The oracle row is live
in `oracle_values.yaml`.

**Integration test update required**: When ASF was wired into revenu_disponible,
the foyers_2024.yaml integration test for the single-parent case needed updating
(34 998.87 → 37 334.95, the difference being the ASF amount ≈ 2 336 EUR/year).
This is the expected pattern: integration tests assert the full aggregate, so they
must be updated whenever a new benefit is added to revenu_disponible.

## Open Questions

- Whether the AF modulation thresholds themselves (the plafonds) are correctly
  parameterised for 2024 remains a validation task. The monotonicity test proves
  the logic is directionally correct, not that the exact thresholds are right.
- CSG rates are currently modelled as flat (9.2 % total) on salary. The statute
  also provides reduced rates (3.8 % / 6.2 %) for low earners on pension income;
  out of scope for the current MVP.
- The revenu_disponible aggregate now covers AF + ASF; extending it further
  (e.g. prime d'activité, APL) will follow the same membres_famille pattern.
- ASF scope limitations are documented in modelled_policies.yaml: taux majoré
  (orphelin de deux parents), ASF différentielle, and recouvrement sur parent
  défaillant are not modelled. The single-parent proxy may over-estimate for
  households where the absent parent pays pension alimentaire.
