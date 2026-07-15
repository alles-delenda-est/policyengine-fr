I've built `policyengine-fr`, a France country model on top of `policyengine-core`, following the `policyengine-canada` package structure. I'd like to check whether France should become a PolicyEngine country package rather than sit alongside the ecosystem, since the multi-country API and web app only pick up a country package that lives in the PolicyEngine org.

## Current scope (an MVP)

Disposable income for a wage-earning *métropole* household, revenus 2024. It computes:

- Impôt sur le revenu: abattement 10 % → nombre de parts (quotient familial) → barème par part → plafonnement du QF → décote → IR;
- CSG (déductible + imposable) and CRDS on salary;
- Pensions alimentaires: deducted when paid, taxed after the 10 % abattement when received;
- Allocations familiales (base, income modulation, majoration âge) and allocation de soutien familial (ASF différentielle);
- aggregated into a household `revenu_disponible`.

## Validation

Results match the DGFiP IR simulator and CAF to the euro, via oracle tests (77 YAML + 37 pytest). Each scope-narrowing is a named `simplification` in `modelled_policies.yaml` with a legal reference and a matching entry in the coverage map. CI gates lint, tests, changelog, and a doc-currency check. Out of scope for now: means-tested benefits, non-salary income, DOM, and years other than 2024.

## Three questions

1. **Adoption** — is PolicyEngine interested in France as a country package? If so, what is the path (repo transfer, country-registry integration, release cadence, maintenance expectations)?
2. **PyPI name** — `policyengine-fr` is unclaimed. Do you want to hold it, or should I register a placeholder to prevent squatting while we talk?
3. **Requirements** — what is your bar for listing a country package in the app/API (coverage, data sourcing, review)?

I'll keep the outward description accurate (a `policyengine-core`-based French library vs "France in the PolicyEngine app") based on your answer.

Repo: https://github.com/alles-delenda-est/policyengine-fr

Happy to talk on a call or async.
