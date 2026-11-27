# PolicyEngine France

An open-source static tax-benefit, labour-cost, and patrimonial microsimulation
model for **France métropolitaine (2024–2025)**, built on PolicyEngine Core. See
the repository `README.md`, `docs/coverage.md`, and
`docs/policyengine-ecosystem.md` for architecture, coverage, and design specs.

## What is modelled (2024–2025, France métropolitaine)

| Domain | Key Variables | Entity |
| --- | --- | --- |
| Employee cotisations & net pay | `cotisations_salariales`, `csg`, `crds`, `salaire_declare`, `salaire_net` | `individu` |
| Employer cotisations & labour cost | `cotisations_patronales`, `reduction_generale`, `cout_du_travail` | `individu` |
| Retirement pensions & replacement levies | `pension_retraite`, `csg_retraite`, `crds_retraite`, `casa_retraite`, `pension_retraite_nette` | `individu` |
| Taxable income & merged 10 % pension allowance | `salaire_imposable`, `pensions_imposables`, `revenus_fonciers_nets`, `revenu_net_imposable` | `individu` / `foyer_fiscal` |
| Income tax & RFR | `nombre_parts`, `impot_brut`, `plafonnement_quotient_familial`, `decote`, `impot_revenu`, `revenu_fiscal_de_reference` | `foyer_fiscal` |
| Capital, wealth & high-income levies | `pfu_ir`, `prelevements_sociaux_patrimoine`, `impot_plus_values_immobilieres`, `cehr`, `ifi` | `foyer_fiscal` |
| Local property & land-value taxes | `taxe_fonciere`, `taxe_habitation_residence_secondaire`, `taxe_valeur_sol` | `menage` |
| Family & solidarity benefits | `allocations_familiales`, `allocation_soutien_familial`, `rsa`, `prime_activite` | `famille` |
| **Disposable income (headline)** | **`revenu_disponible`** | `menage` |

Parameterised policy reforms live under `policyengine_fr.reforms` (`lvt_shift`
scenarios `S1`–`S3_IFI` and `budget_levers` macro-fiscal levers).

See `policyengine_fr/modelled_policies.yaml` and `docs/coverage.md` for the
exact modelled / not-modelled boundary. Every parameter is dated YAML with an
official `reference` (Légifrance / BOFiP / URSSAF / CAF), and every variable is
covered by YAML unit and integration tests, property tests, and independent
DGFiP / `openfisca-france` oracle checks.
