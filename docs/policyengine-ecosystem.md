# PolicyEngine ecosystem reference

A working map of PolicyEngine's repositories and architecture, written to support
building **`policyengine-fr`** — a French tax-benefit microsimulation model — by
reusing the existing UK/US stack rather than copying any single app wholesale.

> Last reviewed: 2026-06-06, against the live `github.com/orgs/PolicyEngine` org
> (288 repos total; ~99% are one-off analysis dashboards). This document only
> covers the **canonical stack** that actually matters for a new country.

---

## 1. The big picture: PolicyEngine is layered, not monolithic

PolicyEngine is **not** one app you fork. It is a stack of independent packages,
each published to PyPI/npm, where lower layers know nothing about higher ones:

```
┌─────────────────────────────────────────────────────────────┐
│  Web app        policyengine-app (React, live)               │  ← country-agnostic UI
│                 policyengine-app-v2 (next-gen, in dev)        │
├─────────────────────────────────────────────────────────────┤
│  API            policyengine-api (Flask, live)               │  ← introspects country pkg
│                 policyengine-api-v2 (next-gen, in dev)        │     for metadata
│  Python facade  policyengine.py  (pe.uk / pe.us helpers)     │
├─────────────────────────────────────────────────────────────┤
│  Country models policyengine-us / -uk / -canada / -il / -ng  │  ← THE WORK for a new
│                 (+ matching *-data repos for microdata)      │     country lives here
├─────────────────────────────────────────────────────────────┤
│  Engine         policyengine-core (fork of OpenFisca-Core)   │  ← simulation, params,
│                                                              │     variables, reforms
└─────────────────────────────────────────────────────────────┘
```

**Key consequence for France:** the API and app are already multi-country. They
discover a country's variables, parameters, and entities by *introspecting the
country package at runtime*. So "add France to the UI" mostly means "build a
correct `policyengine-fr` country package" — the app/API largely come for free.
**~90% of the effort is the country package**, and most of *that* effort is
policy modelling (knowing French law), not software engineering.

---

## 2. Repository map (the canonical stack)

| Repo | Lang | Default branch | Role | Reuse strategy for FR |
|------|------|---------------|------|-----------------------|
| **policyengine-core** | Python | `master` | Simulation engine, parameter tree, `Variable` system, reform machinery. Fork of OpenFisca-Core. | **Depend on it.** Don't fork. |
| **policyengine-us** | Python | `main` | US model (146★). Federal + 50 states → most complex layout. | Reference only. |
| **policyengine-uk** | Python | `main` | UK model (42★). Single national system. | **Closest structural model for FR.** |
| **policyengine-canada** | Python | `master` | Canada model. Newest/simplest full country package. | **Best starter template to copy.** |
| **policyengine-us-data / -uk-data** | Python | — | Build representative survey microdata for population-level simulation. | FR equivalent needed eventually; not for a PoC. |
| **policyengine.py** | Python | `main` | User-facing facade: `pe.uk.calculate_household(...)`, population analysis, impact comparisons. | Add `pe.fr` once the model exists. |
| **policyengine-api** | Python | `master` | Flask REST API computing policy impacts. Py 3.10/3.11. | Country-aware; add FR support later. |
| **policyengine-api-v2** | Python | — | Next-gen API (active dev). | Watch direction. |
| **policyengine-app** | JS/React | `main` | Live web app (67★). Node 22. | Multi-country; extend, don't fork. |
| **policyengine-app-v2** | — | — | Next-gen web app (active dev). | Watch direction. |
| **policyengine-ui-kit** | TS | — | Design tokens, Tailwind v4 theme, React components. | Reuse for any custom FR UI. |
| **policyengine-claude** | — | `main` | **Official Claude Code plugin** (agents/commands/skills for PE dev). | **Install this** (see §6). |
| **policyengine-skills** | Python | — | Source that generates `policyengine-claude`. | Source of the above. |

Everything else in the org (e.g. `utah-2026-tax-changes`, `marriage`,
`givecalc`, `cliff-watch`) is a downstream **analysis dashboard** built *on top
of* this stack — useful as examples of consuming the API, not as architecture.

---

## 3. Anatomy of a country package (what `policyengine-fr` becomes)

Based on `policyengine-canada` (the cleanest example). A country package is a
pip-installable Python package whose import name uses an underscore
(`policyengine_canada`) while the repo/PyPI name uses a hyphen
(`policyengine-canada`). For France: repo `policyengine-fr`, package
`policyengine_fr`.

```
policyengine-fr/
├── Makefile                 # install / format / test / build / changelog
├── pyproject.toml           # deps (incl. policyengine-core), version
├── CHANGELOG.md + changelog.d/   # towncrier-managed changelog
├── docs/                    # jupyter-book documentation
└── policyengine_fr/
    ├── __init__.py
    ├── entities.py          # Person, Household, (+ tax/benefit units) — see §3.1
    ├── model_api.py         # re-exports core DSL + FR constants (e.g. EUR)
    ├── constants.py         # COUNTRY_DIR, etc.
    ├── modelled_policies.yaml
    ├── parameters/          # the NUMBERS (rates, thresholds) as dated YAML
    │   ├── gov/             # mirrors government department structure
    │   └── simulation/
    ├── variables/           # the FORMULAS as Python Variable classes
    │   ├── gov/             # mirrors gov structure, parallel to parameters/
    │   ├── household/       # demographic / geographic inputs & derived vars
    │   └── input/           # raw input variables
    ├── reforms/             # parameterised policy reforms
    ├── situation_examples/  # canned example households
    ├── tests/               # YAML test suites mirroring variables/ tree
    │   ├── gov/
    │   └── household/
    └── tools/general.py
```

The three file types you write constantly — **parameter, variable, test** — form
the core authoring loop. A single new benefit/tax usually = one parameter YAML +
one variable `.py` + one test YAML, in mirrored paths.

### 3.1 Entities

Defined in `entities.py` via `build_entity` from
`policyengine_core.entities`. Canada uses just `Person` + `Household`. The US adds
`tax_unit`, `family`, `spm_unit`; the UK adds `benunit`. **France will need its
own entity design** reflecting the *foyer fiscal* (tax household), the *ménage*,
and the *famille* used by CAF benefits — this is an early design decision, not a
copy-paste. Each entity declares roles and one is flagged `is_person=True`.

### 3.2 Variables (the formulas) — `variables/.../foo.py`

```python
from policyengine_canada.model_api import *   # → policyengine_fr.model_api for FR

class child_benefit(Variable):
    value_type = float
    entity = Household          # which entity this is computed on
    label = "Canada child benefit"
    unit = CAD                  # FR: define EUR = "currency-EUR" in model_api
    documentation = "Non taxable amount paid monthly per child under 18."
    definition_period = YEAR    # YEAR / MONTH / etc.

    def formula(household, period, parameters):
        base = household("child_benefit_base", period)        # call other vars
        reduction = household("child_benefit_reduction", period)
        return max_(0, base - reduction)                       # vectorised (numpy)
```

- The class **name = the variable name** other variables/tests reference.
- `formula(entity, period, parameters)` is **vectorised** — it runs over a whole
  population at once. Use `max_`, `min_`, `where`, etc. (exported from the engine),
  not Python `if`/`max`.
- Read parameters via the `parameters` arg:
  `parameters(period).gov.cra.benefits.ccb.base` (dotted path mirrors the
  `parameters/` directory tree).
- `model_api.py` re-exports the entire core DSL (`Variable`, `Household`, `YEAR`,
  `max_`, ...) plus country constants, so every variable file just does
  `from policyengine_fr.model_api import *`.

### 3.3 Parameters (the numbers) — `parameters/.../foo.yaml`

Dated values so the model is correct for any year. Two common shapes:

```yaml
# Scalar parameter
description: Some rate.
values:
  2024-01-01: 0.2
  2025-01-01: 0.21
metadata:
  unit: /1
  reference:
    - title: <official source>
      href: <url>
```

```yaml
# Bracketed/scale parameter (e.g. amount by child age)
description: Canada Child Benefit amount by child age.
brackets:
  - amount: {2024-07-01: 7_787, 2025-07-01: 7_997}
    threshold: {2022-07-01: 0}
  - amount: {2024-07-01: 6_570, 2025-07-01: 6_748}
    threshold: {2022-07-01: 6}
metadata:
  type: single_amount
  threshold_unit: year
  amount_unit: currency-CAD     # FR: currency-EUR
  period: year
  reference:
    - title: <official source>
      href: <url>
```

**Every parameter must carry a `reference` to the legal/official source.** Dates
are ISO `YYYY-MM-DD`; numeric underscores (`7_997`) are allowed.

### 3.4 Tests (the validation) — `tests/.../foo.yaml`

YAML test suites mirroring the `variables/` tree. The engine runs them.

```yaml
- name: One eligible child under 6 - full custody
  period: 2023
  input:
    people:
      person: {age: 5, full_custody: true}
    households:
      household:
        members: [person]
        adjusted_family_net_income: 30_000
        child_benefit_eligible_children: 1
  output:
    child_benefit: 6_997
```

Each case sets up a household, fixes inputs, asserts expected outputs. Tests are
the contract — verifying a formula against a known statutory example is how
correctness is demonstrated.

---

## 4. How a simulation actually runs (mental model)

1. A **dataset** (or a hand-built situation) supplies *input* variable values for
   a population of entities.
2. You request an *output* variable (e.g. `child_benefit`) for a `period`.
3. The engine lazily evaluates that variable's `formula`, which recursively
   requests the variables/parameters it depends on, caching as it goes — a
   dependency graph resolved on demand, vectorised across the whole population.
4. **Reforms** are diffs over the parameter tree (or variable overrides) layered
   on top of a baseline; "impact of policy X" = run baseline vs. reformed
   simulation and compare aggregates/distributions.

`policyengine.py` wraps this:
`pe.uk.calculate_household(people=[...], year=2026)` for a single household, and
`Simulation(dataset=..., tax_benefit_model_version=pe.uk.model)` +
`Aggregate(...)` for population analysis.

---

## 5. Build / test / dev commands (per country package)

Country packages use a `Makefile` and the `policyengine-core` test runner.
`policyengine-core` itself uses **`uv`** and insists on `uv run` for all Python.

```bash
make install     # pip install -e .[dev]   (core: `make install` via uv)
make format      # ruff format . && ruff check .   (CI enforces)
make test        # policyengine-core test -c policyengine_<country> .../tests
make build       # python -m build
make changelog   # towncrier; version bumped from pyproject.toml

# Run a single test file (engine YAML runner):
policyengine-core test -c policyengine_fr policyengine_fr/tests/gov/.../foo.yaml

# In policyengine-core (and uv-based repos), prefix Python with uv run:
uv run pytest tests/core/test_file.py::test_name -v
```

Conventions worth knowing:
- **Formatting:** `ruff` (core) / `black`-style; CI enforces. Always `make format`
  before committing.
- **Changelog:** `towncrier` — add a fragment in `changelog.d/`; don't hand-edit
  `CHANGELOG.md`. Version is bumped from the fragment, not manually.
- **Python:** core supports 3.9–3.14; the API is pinned to 3.10/3.11.
- **Default branches differ:** `master` for core/canada/api, `main` for uk/app/py.
  Check before branching.

---

## 6. Tooling: the official Claude Code plugin

PolicyEngine ships an official Claude Code plugin (`policyengine-claude`,
generated from `policyengine-skills`) with agents/commands/skills tuned for
exactly this kind of work. Install in a session:

```text
/plugin marketplace add PolicyEngine/policyengine-claude
/plugin install complete@policyengine-claude
```

Narrower bundles also exist: `essential`, `country-models`, `api-development`,
`app-development`, `analysis-tools`, `data-science`, `dashboard-builder`,
`content`. For FR model work, `country-models` (or `complete`) is the relevant one.

---

## 7. Recommended path to `policyengine-fr`

Strategy: **fork-and-contribute, start with one vertical slice.** France does not
yet exist in the org (only `-us`, `-uk`, `-canada`, `-il`, `-ng` country models).

1. **Engage upstream first** (cheapest feedback): open a GitHub Discussion/issue
   on PolicyEngine stating the intent to start France — check for prior interest,
   partial work, or structural guidance before building much.
2. **Bootstrap `policyengine-fr`** by copying `policyengine-canada`'s structure
   (simplest complete country package), renaming `policyengine_canada` →
   `policyengine_fr`, defining `EUR` and FR `entities` (foyer fiscal / ménage).
3. **Implement one vertical slice end-to-end**: one French benefit or tax bracket
   = parameter YAML + variable `.py` + test YAML, all green under `make test`.
4. **Wire it into `policyengine.py`** (`pe.fr.calculate_household`) and/or the API
   so it renders, proving the multi-country path works.
5. **Share that slice for feedback**, then iterate breadth.

Engine changes should be avoided in a PoC; if France genuinely needs them, that's
a conversation to have with maintainers (step 1) before diverging.

---

## 8. Open questions to resolve early

- **Entity model for France** — foyer fiscal vs. ménage vs. famille; this shapes
  every variable's `entity =` and has no UK/US/CA equivalent to copy directly.
- **Microdata source** — the FR analogue of FRS (UK) / CPS (US); needed for
  population-level (not household-level) analysis. Not required for a PoC.
- **Upstream vs. standalone** — only diverge into a private clone if maintainers
  reject needed engine changes; default to fork-and-contribute.
