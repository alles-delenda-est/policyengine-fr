# Spec 0003 — Enable the independent statute-review CI gate

**Status:** Draft · **Priority:** P1 (cheap, high-leverage) ·
**Source:** PENDING_NEXT_STEPS #4, `docs/reviewer-agent-gate.md` ·
**Est. effort:** ~1 hour (config) + one validation PR

---

## 1. Goal

Activate the dormant `claude-review.yml` workflow so every PR touching
`variables/**` or `parameters/**` gets an independent, adversarial statute
review. The workflow already exists and is wired correctly; it is gated off
behind a repo variable so it never shows a red X before it is configured.

This directly targets the defect class this project keeps producing: **silent
scope-narrowing** (the external review found it twice — B1, B3). The gate's
prompt explicitly checks for it, so it plausibly pays for itself on the next
benefit PR (RSA, Spec 0002).

## 2. Current state

`.github/workflows/claude-review.yml` runs only `if: vars.ENABLE_CLAUDE_REVIEW
== 'true'`, uses `anthropics/claude-code-action@v1` with `ANTHROPIC_API_KEY`,
is **advisory** (posts a review comment, does not block auto-merge), and scopes
to variable/parameter paths. The prompt already covers: statute fidelity vs the
cited article, independent reference values (openfisca-france / official
simulator), silent scope-narrowing disclosure, and entity/period correctness.

Nothing in the workflow needs to change to turn it on.

## 3. Steps

1. **Add the secret** `ANTHROPIC_API_KEY` (repo → Settings → Secrets and
   variables → Actions → Secrets). Use a key scoped/budgeted for CI.
2. **Set the variable** `ENABLE_CLAUDE_REVIEW = true` (same screen → Variables).
3. **Validation PR** — open a trivial variable-touching PR (e.g. a docstring
   line) and confirm the `statute-review` job runs, posts a review comment, and
   does **not** block merge. Confirm it does *not* run on docs-only PRs (path
   filter).
4. **Decide advisory vs blocking.** Keep advisory for now (recommended): a
   model-based reviewer should inform, not gate, until its false-positive rate
   on this repo is known. Revisit after ~5 PRs of observed output.

## 4. Cost & guardrails

- Runs only on `variables/**` / `parameters/**` PRs (not docs, not every push).
- One API call per such PR/synchronize. Budget the key; add a spending alert.
- If cost is a concern, restrict `on:` to `types: [labeled]` and require a
  `needs-statute-review` label to trigger — opt-in per PR.

## 5. Acceptance criteria

- The job runs on a variable-touching PR and skips on a docs-only PR.
- It posts a substantive review comment tied to articles/URLs.
- It does not block auto-merge (advisory).
- `docs/reviewer-agent-gate.md` updated: mark the gate **active**, note the
  advisory/blocking decision and the cost guardrail chosen.

## 6. Risks

- **Model false positives** could create review noise; mitigated by advisory
  mode and the "report findings tied to specific articles/URLs" instruction
  (unsourced complaints are easy to dismiss).
- **Key exposure** — standard Actions-secret hygiene; never echo the key.
