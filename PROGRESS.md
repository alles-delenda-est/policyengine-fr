# PROGRESS — policyengine-fr "Disposable-income MVP" (2024)

Durable source of truth for the autonomous build. **Every work session reads this
file first**, does the next unchecked increment, and ticks it. Designed so any
trigger — local, cloud routine, or manual — resumes cleanly from repo state.

Plan: `~/.claude/plans/precious-baking-hejlsberg.md` (local). Repo:
`alles-delenda-est/policyengine-fr`.

## Definition of done (stop condition)

For a French household, tax year **2024, métropole**, from gross salary:
`revenu_net_imposable` → `nombre_parts` → `impot_revenu` (barème per part ×
parts, plafonnement du quotient familial, décote) → `csg`/`crds` →
`allocations_familiales` → **`revenu_disponible`**.

Done when: every increment below checked **AND** `main` CI green **AND** the
end-to-end household scenarios pass with reference values. Then stop the routine.

## How to resume (runbook — one increment per cycle)

1. `git fetch origin && git checkout main && git pull` (or clone fresh).
2. Activate env: `. .venv/bin/activate` (local) or `make install` (fresh/cloud).
3. Read this file; pick the **first unchecked** increment.
4. `git checkout -b feat/<increment-slug>`.
5. Implement: parameter YAML (with official `reference:`) + variable `.py`
   (`from policyengine_fr.model_api import *`) + YAML tests (periods `YYYY`/`YYYY-01`
   only) with **reference values**. Add a `changelog.d/added/<slug>.added.md`.
6. `make test` and `ruff format . && ruff check .` must pass locally.
7. `git push -u origin HEAD`; `gh pr create`; `gh pr merge --auto --squash`.
8. When CI is green the PR self-merges. Tick the box here (commit the tick on the
   same PR or a tiny follow-up), then loop to the next increment.
9. If all boxes checked and `main` CI green → run final verification, then stop.

Idempotent: re-running a half-done increment is safe (branch + tests gate it).

## Increment backlog

- [x] 0. Scaffolding + per-foyer income-tax barème slice (pre-MVP, on `main`)
- [ ] 1. `revenu_net_imposable` from `salaire_brut` — 10% abattement (floor/ceiling). `gov/dgfip/ir/abattement_salaires`
- [ ] 2. `nombre_parts` — quotient familial (declarants + personnes_à_charge; single-parent majoration). `gov/dgfip/ir/parts`
- [ ] 3. `impot_brut` — `bareme.calc(rni / parts) * parts` (refit existing `bareme.yaml`/`impot_revenu_bareme`)
- [ ] 4. `plafonnement_quotient_familial` — cap the advantage of extra half-parts
- [ ] 5. `decote` — low-income reduction (séparé vs couple)
- [ ] 6. `impot_revenu` — `max(0, impot_brut after plafonnement − décote)`
- [ ] 7. `csg` / `crds` — on employment income, 98.25% base. `gov/urssaf/...`
- [ ] 8. `allocations_familiales` — on `famille`; base by #children, 3-tranche modulation, age majoration. `gov/cnaf/prestations/af/...`
- [ ] 9. `revenu_disponible` — headline aggregate
- [ ] 10. Integration tests — whole-household end-to-end scenarios
- [ ] 11. Finalize — update `CLAUDE.md`, `modelled_policies.yaml`, `docs/`; review pass

## Validation oracles

- Income tax: official **impots.gouv.fr** simulator (authoritative).
- Benefits/contributions: **service-public.fr** / **CAF** / **URSSAF**.
- Optional cross-check: run **openfisca-france** locally as an oracle (compare
  numbers only; do not copy its AGPL code).

## Notes / decisions log

- 2026-06-15: GitHub configured for hands-off merge (auto-merge, squash-only,
  branch protection requiring Lint / Check changelog fragment / Test (3.11) /
  Test (3.12); no required reviews; admins bypass).
- Entities already defined: `individu`, `foyer_fiscal`, `famille`, `menage`.
- Local `.venv` exists (pip bootstrapped via get-pip.py; no system pip/uv).
