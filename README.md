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
- `data/` — pinned calibration artifacts with SHA-256 provenance (`lvt_yields.json`).
- `reforms/` — parameterised policy reforms (`lvt_shift` S1–S3_IFI and `budget_levers` IR/CSG/pension indexation levers).

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

### On Windows

Use Python 3.11 or 3.12 from [python.org](https://www.python.org/downloads/)
(its installer includes `pip`). `make` is usually not available, so run the
underlying commands directly (PowerShell or CMD):

```powershell
py -m venv .venv
.venv\Scripts\activate
pip install -e .[dev]

# format + lint (what `make format` runs)
ruff format .
ruff check .

# tests (what `make test` runs)
policyengine-core test -c policyengine_fr policyengine_fr\tests
pytest tests/ -q
```

The model itself is cross-platform (CI runs on Linux; PolicyEngine country
packages also test on Windows). `.gitattributes` keeps line endings as LF so
`ruff format --check` stays consistent across platforms.

## Current status

**Multi-year tax-benefit, labour-cost, and patrimonial model (revenus 2024–2025, France métropolitaine).** From a household's gross wages, pensions, capital income, and property/land endowments, the model computes end-to-end:

- **Cotisations sociales & coût du travail** — per-risk PASS-bracketed employee contributions (`cotisations_salariales`, `cadre` support) and CSG/CRDS (98,25 % assiette) mapping true-gross `salaire_brut` → `salaire_declare` (1AJ) and `salaire_net`; plus employer `cotisations_patronales` (SMIC bandeaux), `reduction_generale` (ex-Fillon), and super-brut `cout_du_travail`.
- **Pensions de retraite & pensions alimentaires** — RFR-banded replacement CSG (0 % / 3,8 % / 6,6 % / 8,3 %), CRDS (0,5 %), and CASA (0,3 %) → `pension_retraite_nette`; shared 10 % abattement merged across retirement pensions and received alimony (`pensions_imposables`); paid alimony deducted from global income.
- **Impôt sur le revenu, patrimoine & fiscalité locale** — `revenu_net_imposable` → `nombre_parts` → `impot_brut` → `plafonnement_quotient_familial` → `decote` → `impot_revenu` net; `revenu_fiscal_de_reference`, `cehr` (3 % / 4 %), `pfu_ir` (12,8 %) + 17,2 % `prelevements_sociaux_patrimoine`, `revenus_fonciers_nets` (micro-foncier / réel), `impot_plus_values_immobilieres` (19 %), `ifi` (30 % RP abatement + décote), `taxe_fonciere`, `taxe_habitation_residence_secondaire`, and `taxe_valeur_sol`.
- **Prestations sociales (CNAF)** — `allocations_familiales` (with statutory *complément dégressif*), `allocation_soutien_familial` (ASF différentielle), `rsa` (socle + majoré, forfait logement, statutory AF/ASF resource rules), and `prime_activite` (montant forfaitaire, individual SMIC bonification, 61 % activity slope).
- **Réformes & agrégats** — `revenu_disponible` on the ménage, `cout_du_travail` on the individu, and ready-to-simulate reforms in `policyengine_fr.reforms` (`create_lvt_shift_reform` and `budget_levers`).

See [`policyengine_fr/modelled_policies.yaml`](policyengine_fr/modelled_policies.yaml)
and [`docs/coverage.md`](docs/coverage.md) for the exact modelled / not-modelled boundary and documented statutory simplifications.

## Found an error?

The model's credibility rests on **named simplifications validated against the
official simulators** — so counter-examples are welcome and treated as
first-class input. If a household's result disagrees with the DGFiP
([simulateur IR](https://www.impots.gouv.fr/simulateur-ir-ir)) or CAF
([caf.fr](https://www.caf.fr)), please
[open a model-error report](../../issues/new?template=model-error.yaml).

Include the household inputs, the **expected** figure with its **official
source**, and the value the model produced. Before filing, check
[`docs/coverage.md`](docs/coverage.md) — the discrepancy may be a
**documented simplification** rather than a bug.

## License

Distributed under the AGPL License, consistent with the PolicyEngine ecosystem.
