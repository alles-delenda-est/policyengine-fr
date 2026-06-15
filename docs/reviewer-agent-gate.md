# Reviewer-agent gate

An **independent reviewer** that inspects model PRs against French statute before
they land. It exists to break the **self-validation loop** of the autonomous
build: the build routine writes the implementation, its tests, *and* sources the
reference values — so a misread of the law produces a wrong formula with a
matching wrong test that passes CI. CI proves *internal consistency*; this gate
checks *fidelity to the law*.

It is deliberately **separate from the builder** (a different agent, a fresh
adversarial prompt) so it doesn't inherit the builder's assumptions.

## What the reviewer checks (adversarial checklist)

1. **Statute fidelity** — does each variable's formula actually match the cited
   article (CGI / CSS / arrêté)? Is the `reference:` real, current, and on-point
   (not a vaguely-related page)?
2. **Independent reference values** — are the test expected values traceable to an
   **independent** source (openfisca-france parameter, official simulator), not
   merely re-derived from the same code? Hand-check at least one value.
3. **Silent scope-narrowing** — does the PR quietly simplify (e.g. AF without the
   real N‑2 base ressources, a benefit without its phase-out) while ticking the
   increment "done"? Every simplification must be explicit in the variable
   docstring **and** `modelled_policies.yaml`.
4. **Entity & period correctness** — right entity (`individu` / `foyer_fiscal` /
   `famille` / `menage`)? right `definition_period` (YEAR vs MONTH)? correct
   cross-entity aggregation (no double counting, no divide-by-group-size hacks
   that break for multi-foyer households)?
5. **Edge cases** — zero income, exactly-at-threshold values, single vs couple vs
   parent isolé, many children, age boundaries (14 / 18 / 20). Are they tested?
6. **Vectorisation & safety** — numpy-safe (`max_`/`min_`/`where`, no Python
   `if`), no divide-by-zero, no NaN/inf.
7. **Regression** — does it move golden-master values? If so, is the change
   justified and the fixture regenerated intentionally?

**Verdict:** `APPROVE` or `REQUEST CHANGES`, each finding tied to a specific
statute citation. (This mirrors the PolicyEngine plugin's `program-reviewer` and
`reference-validator` agents — use them directly if the plugin is installed.)

## Two modes

- **Advisory (default):** the reviewer posts its findings as a PR comment on every
  PR touching `policyengine_fr/**`. Auto-merge still proceeds — the comment is a
  safety net and an audit trail.
- **Blocking (for hard increments):** the PR is labelled `needs-review`, is **not**
  `--auto`-merged, and waits for the reviewer (and/or a human) to sign off. Use
  this for anything with **eligibility, means-tests, or phase-outs** (benefits,
  minima sociaux) — exactly the logic most prone to plausible-but-wrong code.

## How to turn it on

1. Add the repo secret **`ANTHROPIC_API_KEY`**
   (Settings → Secrets and variables → Actions → New repository secret).
2. Set the repo variable **`ENABLE_CLAUDE_REVIEW`** = `true`
   (same screen → Variables tab). The workflow stays dormant until this is set, so
   it never shows a red ✗ before it's configured.
3. **(Blocking)** To gate a specific PR, add the `needs-review` label and create it
   without auto-merge. To gate a whole class, see the routine integration below.

## Integrating with the build routine (next scope expansion)

When the `policyengine-fr MVP autonomous build` routine is re-enabled for new
scope (cotisations salariales, RSA / APL / prime d'activité, microdata…), update
its standing prompt so it **classifies each increment**:

- **Mechanical** (a rate, a bracket, a deterministic formula with an exact
  official value) → keep `gh pr merge --auto --squash`.
- **Hard / means-tested** (eligibility, income phase-outs, benefit modulation) →
  create the PR **without** `--auto`, apply the `needs-review` label, and stop;
  let the reviewer gate + a human sign off before merge.

This keeps velocity on the easy 80% while putting human/independent eyes exactly
where the correctness risk concentrates.

## Why not just trust CI?

CI runs the builder's own tests. Green CI on a self-authored test only proves the
code does what the *same author thought* the law says. The reviewer gate (like the
CoWork oracle in `cowork-validation-brief.md`) introduces an **independent check** —
the two together cover the gap that unit tests structurally cannot.
