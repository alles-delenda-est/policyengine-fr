# PolicyEngine France

[![Code style: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

An open-source static tax-benefit microsimulation model for **France**, built on
the [PolicyEngine Core](https://github.com/PolicyEngine/policyengine-core)
framework (a fork of [OpenFisca](https://openfisca.org)). This is an early
work-in-progress, seeded from the structure of `policyengine-canada`.

All modelling lives in the `policyengine_fr/` package:

- `entities.py` — the French entities: `individu`, `foyer_fiscal`, `famille`, `menage`.
- `parameters/` — system parameters (rates, thresholds) as dated YAML, mirroring
  the government department structure (`gov/dgfip/ir/...`).
- `variables/` — the formulas and inputs, as Python `Variable` classes, in a tree
  parallel to `parameters/`.
- `tests/` — YAML test suites mirroring the `variables/` tree.
- `reforms/` — parameterised policy reforms (to come).

> For the wider PolicyEngine architecture and the plan for this project, see
> [`docs/policyengine-ecosystem.md`](docs/policyengine-ecosystem.md) and
> [`CLAUDE.md`](CLAUDE.md).

## Setup

```bash
pip install -e .[dev]   # or: make install
```

## Develop

```bash
make format   # ruff format + check (run before committing)
make test     # run the YAML test suite via the core test runner

# Run a single test file:
policyengine-core test -c policyengine_fr policyengine_fr/tests/gov/dgfip/ir/impot_revenu_bareme.yaml
```

## Current status

First vertical slice only: the progressive income-tax barème
(`impot_revenu_bareme`) applied to a foyer fiscal's `revenu_net_imposable`,
using the 2024 brackets. It is intentionally simplified — no quotient familial,
décote, or plafonnement yet (see the variable's docstring). The point so far is
to prove the parameter → variable → test pipeline end-to-end.

## License

Distributed under the AGPL License, consistent with the PolicyEngine ecosystem.
