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
policyengine-core test -c policyengine_fr policyengine_fr/tests/gov/dgfip/ir/impot_revenu.yaml
```

## Current status

**Disposable-income MVP (revenus 2024, métropole).** From a household's gross
salary, the model computes the full chain end-to-end:

- **Impôt sur le revenu** — `revenu_net_imposable` (10 % abattement) →
  `nombre_parts` (quotient familial) → `impot_brut` (progressive barème per
  part) → plafonnement du quotient familial → décote → `impot_revenu` net.
- **Prélèvements sociaux** — `csg` (déductible + imposable) and `crds` on salary
  (assiette of 98,25 % of gross).
- **Prestations** — `allocations_familiales` on the famille (base by number of
  children, income modulation, age majoration).
- **Headline** — `revenu_disponible` on the ménage aggregates the above.

See [`policyengine_fr/modelled_policies.yaml`](policyengine_fr/modelled_policies.yaml)
for the exact modelled / not-modelled boundary. Out of scope for the MVP: other
social contributions, capital and non-salary income, and most benefits.

## License

Distributed under the AGPL License, consistent with the PolicyEngine ecosystem.
