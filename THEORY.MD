# Theory: Building policyengine-fr — From MVP to Accurate Benefit Modelling

## Problem

The French tax-benefit model (`policyengine-fr`) has a working MVP covering the
full disposable-income chain (salaire → IR → CSG/CRDS → AF → ASF →
revenu_disponible), but MVP models inevitably carry explicit simplifications that
over- or under-estimate for real households. The structural challenge is: how do
you extend from "roughly right for a canonical household" to "correct for the
range of household types that actually use the model"?

The ASF (Allocation de soutien familial) is the testbed for this extension
strategy. Its MVP approximation — pay full ASF to any single-parent famille —
systematically over-estimates for the significant subset of single parents who
already receive a pension alimentaire from the absent parent. The French statute
(CSS art. L523-1, L581-2) is explicit: ASF is a guarantee mechanism, not an
unconditional transfer. If the famille receives a pension, ASF fills only the
gap. The MVP ignored this because `pensions_alimentaires_percues` was not
connected into the ASF formula.

## Operating Theory

PolicyEngine's architecture makes the fix clean: `pensions_alimentaires_percues`
already exists as an Individu/YEAR input (created for the deductibility side of
pension modelling in IR). The ASF formula reads Famille-level aggregates via
`famille.sum(famille.members(...))`, and divides by 12 to convert annual →
monthly. The netting is `max_(asf_pleine − pension_mensuelle, 0)` — floored at
zero because ASF is a guarantee, not a subsidy that can go negative.

The key constraint the formula must honour: when pension is zero (parent
deceased, unknown, or pension unrecoverable), the result must equal full ASF. The
`max_(..., 0)` floor handles this transparently — zero pension → full ASF, no
special case needed.

The test period constraint (all pension-input cases must use 2024-01, not other
months in 2024) is a policyengine-core loader limitation: when a YEAR-typed
variable is set in a test case, the loader resolves it against `period.this_year`
of the test's period. For monthly periods other than January, the year period
does not start at the same point as the monthly period in the loader's internal
calendar, triggering a `ValueError: Expected a period; got: 'year'`. January is
safe because `period.this_year` for 2024-01 resolves unambiguously to 2024.

## Strategy

The overall development sequence:
1. **Lock down reference-value tests** (parameter + variable YAML tests) before
   extending the formula — regression prevention.
2. **TDD for each extension**: add failing cases first, confirm RED, implement,
   confirm GREEN. This proves the new cases actually test something.
3. **Property/invariant tests** (pytest grid) catch structural failures — e.g.,
   monotonicity, non-negativity — that reference tests might miss.
4. **Independent oracle validation** (openfisca-france) rules out shared-author
   blindspots: if both codebases agree, the statute interpretation is likely
   correct.
5. **Document the modelled/not-modelled boundary precisely** in
   `modelled_policies.yaml` — each simplification should be a named, explicit
   decision, not a silent gap.

The ASF différentielle completes the first realistic extension: eligibility is
unchanged (still single-parent proxy), but the amount now correctly reflects the
net benefit rather than the gross guarantee.

## Key Discoveries

**Float32 precision**: PolicyEngine uses numpy float32. Identity tests must use
tolerance ~0.01, not machine-epsilon. Any test asserting an arithmetic equality
must be calibrated to float32 noise.

**AF monotonicity holds**: The modulation property (AF weakly decreasing in
income across plafond thresholds) passed cleanly on a deterministic grid. The
formula is directionally correct; the exact threshold values remain a validation
task.

**ASF oracle confirmed**: openfisca-france (v175.0.45) agrees with policyengine-fr
on full ASF (taux simple) for a bare single-parent famille. Δ ≈ 0.00 EUR. The
oracle row is live in `oracle_values.yaml`.

**Integration test update required when a new benefit is wired in**: When ASF
joined revenu_disponible, the foyers_2024.yaml integration test updated from
34 998.87 → 37 334.95 (Δ ≈ 2 336 EUR/year = the ASF amount). This is the
expected pattern and signals correct wiring, not a bug.

**ASF différentielle (Task 1) now modelled**: The pension netting formula
`max_(asf_pleine − pension/12, 0)` was validated against four explicit cases
(partial pension, pension ≥ ASF → zero, two-child famille, couple with pension →
zero). RED → GREEN confirmed via TDD. 77/77 full suite passes. The previous
over-estimation for pension-receiving single parents is eliminated.

## Open Questions

- Whether the AF modulation thresholds (plafonds) are correctly parameterised for
  2024 remains a validation task. Monotonicity is confirmed; the exact values are not.
- CSG rates are modelled flat (9.2 % on salary). Reduced rates for low earners on
  pension income (3.8 % / 6.2 %) are out of scope.
- revenu_disponible covers AF + ASF. Next extensions (prime d'activité, APL) will
  follow the same `membres_famille` aggregation pattern.
- ASF taux majoré (orphelin de deux parents) remains unmodelled (one rate only).
- The ASF différentielle comparison is at famille level, not child by child. This
  is a simplification: the statute compares per-child, but the input
  `pensions_alimentaires_percues` is a single annual total. Multi-child households
  where pensions differ per child cannot be represented without restructuring the
  input. Documented in the variable docstring.
- Recouvrement (CAF advancing ASF then recovering from the absent parent) is not
  modelled — it is a CAF↔débiteur transfer with no net effect on the famille's
  income, so it is correctly excluded.
