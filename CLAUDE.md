# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## ⚠️ Read this first

**Before doing any work, read [`docs/policyengine-ecosystem.md`](docs/policyengine-ecosystem.md).**
It is the canonical reference for this project: the full PolicyEngine repository
map, the layered architecture, the anatomy of a country package, build/test
commands, and the plan for building France. Don't re-derive it from GitHub each
session — consult that doc, and update it when you learn something new.

## What this project is

This repo (`PolicyEngineFR`) **is** the `policyengine-fr` package — a French
tax-benefit microsimulation model that reuses PolicyEngine's existing
UK/US/Canada stack. Seeded from `policyengine-canada`'s structure (2026-06-15).

Current state: scaffolding in place + one working vertical slice — the
progressive income-tax barème (`impot_revenu_bareme`) on the `foyer_fiscal`,
2024 brackets, intentionally simplified (no quotient familial / décote /
plafonnement yet — see the variable docstring). `make test` passes (5/5), ruff
clean. A local `.venv/` exists (pip was bootstrapped via get-pip.py since the
system has no pip); activate it with `. .venv/bin/activate`.

## The one thing to internalise

PolicyEngine is a **layered stack, not a monolith**:
`policyengine-core` (engine) → country models (`-us`/`-uk`/`-canada`) → API → app.
The API and web app are **already multi-country** and introspect the country
package at runtime. So building France is ~90% **building the `policyengine-fr`
country package** (and most of that is policy modelling, not engineering); the
app/API mostly come for free. **Model France on `policyengine-canada`** (simplest
complete country package). Do **not** fork the engine, API, or app.

## Core authoring loop

Adding a French benefit/tax = three files in mirrored directory paths:
- `policyengine_fr/parameters/.../x.yaml` — the **numbers** (dated, with legal `reference`)
- `policyengine_fr/variables/.../x.py` — the **formula** (`Variable` subclass; vectorised; `from policyengine_fr.model_api import *`)
- `policyengine_fr/tests/.../x.yaml` — the **test** (household setup → expected output)

See §3 of the ecosystem doc for full examples of each.

## Commands (once `policyengine-fr` exists)

```bash
make install     # pip install -e .[dev]
make format      # ruff — CI enforces; run before committing
make test        # policyengine-core test -c policyengine_fr policyengine_fr/tests
# single test file:
policyengine-core test -c policyengine_fr policyengine_fr/tests/gov/.../foo.yaml
```

For `policyengine-core` and other `uv`-based repos, prefix Python with `uv run`.

## Conventions

- **Formatting:** `ruff`; CI enforces. Run `make format` before committing.
- **Changelog:** `towncrier` — add a fragment in `changelog.d/`; never hand-edit `CHANGELOG.md`.
- **Naming:** repo/PyPI use hyphens (`policyengine-fr`), the import package uses underscores (`policyengine_fr`).
- **Branches differ across repos:** `master` for core/canada/api, `main` for uk/app/py — check before branching.
- **Every parameter needs a `reference`** to its official/legal source.

## Official tooling

There is an official Claude Code plugin for PolicyEngine development. Install it:
```text
/plugin marketplace add PolicyEngine/policyengine-claude
/plugin install complete@policyengine-claude   # or country-models@policyengine-claude
```
