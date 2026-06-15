# PolicyEngine France

An open-source tax-benefit microsimulation model for France, built on
PolicyEngine Core. See the repository `README.md` and
`docs/policyengine-ecosystem.md` for architecture and the development plan.

## What is modelled (Disposable-income MVP, revenus 2024)

From a household's gross salary, the model computes disposable income through
the following chain (métropole, tax year 2024):

| Step | Variable | Entity |
| --- | --- | --- |
| Net taxable salary (10 % abattement) | `revenu_net_imposable` | `foyer_fiscal` |
| Number of parts (quotient familial) | `nombre_parts` | `foyer_fiscal` |
| Gross income tax (barème per part) | `impot_brut` | `foyer_fiscal` |
| Family-quotient capping | `plafonnement_quotient_familial` | `foyer_fiscal` |
| Low-income reduction | `decote` | `foyer_fiscal` |
| Net income tax | `impot_revenu` | `foyer_fiscal` |
| CSG / CRDS on salary (assiette 98,25 %) | `csg`, `crds` | `individu` |
| Family allowances | `allocations_familiales` | `famille` |
| **Disposable income (headline)** | **`revenu_disponible`** | `menage` |

`revenu_disponible = salaire_brut − impot_revenu − csg − crds +
allocations_familiales`.

See `policyengine_fr/modelled_policies.yaml` for the exact modelled /
not-modelled boundary. Every parameter is dated YAML with an official `reference`
(legifrance / URSSAF / CAF), and every variable is covered by a YAML test suite
with reference values, including whole-household integration scenarios under
`policyengine_fr/tests/integration/`.
