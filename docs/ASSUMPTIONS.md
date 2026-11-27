# Project Review & Assumptions Log — `policyengine-fr`

> **Prepared for:** Patrick (`alles-delenda-est`)
> **Date:** 2026-11-27
> **Active Repository:** `C:\Users\patri\projects\PolicyEngineFR\policyengine-fr` (`https://github.com/alles-delenda-est/policyengine-fr.git`)
> **Implementation Branch & PR:** `feat/roadmap-2026-consolidation` ([Draft PR #32](https://github.com/alles-delenda-est/policyengine-fr/pull/32))
> **Verification Status:** `160` YAML tests + `56` `pytest` tests passing (`25/25` live DGFiP & `openfisca-france` v175.0.45 oracle rows, `0` skips, `ruff==0.17.4` clean, `check_doc_currency.py` in sync; all P1–P3 findings from independent statute review `pullrequestreview-6084243252` addressed).

---

## 1. Objective Confirmation

1. **North-Star Goal:** Build **`policyengine-fr`**, a statute-accurate, open-source French tax-benefit, labour-cost, and patrimonial microsimulation country package on `policyengine-core` (modelled structurally on `policyengine-canada` so it plugs into the multi-country `policyengine.py` / API / web-app stack without forking `policyengine-core`).
2. **Engineering & Epistemic Standards:**
   - Mirrored `parameters/` (1-leaf-per-file dated YAML with official Légifrance/BOFiP/URSSAF/BO Santé `reference` links), `variables/` (vectorised `float32`-safe `Variable` formulas), and `tests/` (YAML unit + integration suites).
   - Multi-layer verification: YAML unit tests (`policyengine-core test`), property/invariant tests (`tests/test_properties.py`), golden-master regression (`tests/test_golden_master.py`), cross-repo reform tests (`tests/test_reforms.py`), and **independent oracle validation** (`tests/fixtures/oracle_values.yaml` checked against DGFiP and `openfisca-france` in `../.venv-of312`).
   - **Zero silent scope-narrowings:** Every departure from French statute is explicitly recorded in `policyengine_fr/modelled_policies.yaml` (`simplifications:`) and mirrored 1-for-1 in `docs/coverage.md`, enforced automatically by `bin/check_doc_currency.py`.
3. **Cross-Repository Reuse Mandate:**
   - Reuse and unify validated fiscal mechanisms, statutory constants, calibration data, and policy-lever specifications from:
     - `alles-delenda-est/budget_fr_sim_test` (`review/day0` and `review/day1`, plus local `C:\Users\patri\projects\budget_fr_sim_test`)
     - `alles-delenda-est/LVTShift` (`lvtshift-fr`, local `C:\Users\patri\projects\LVTshiftFR`)

---

## 2. Diagnostic Findings & Review Issues Resolved

| Area | Finding Discovered | Resolution Implemented |
|---|---|---|
| **Workspace topology** | `C:\Users\patri\projects\PolicyEngineFR` contains an older shallow clone (`9f7cec3`, June 17), `.venv-of312` (Python 3.12 `openfisca-france` v175.0.45 oracle env), and `policyengine-fr\` (the canonical inner git repo). | Preserved all outer files and `.venv-of312` untouched; implemented all changes inside `policyengine-fr\` on branch `feat/roadmap-2026-consolidation`. |
| **RSA statutory & oracle bugs (`feat/rsa` vs PR #27)** | Local `feat/rsa` failed its OpenFisca check by `−890.27 €` because `compute_af_openfisca.py` set `statut_occupation_logement = {"2024-01": "locataire_vide"}` (only January, and tenant without APL = no *forfait logement* in OpenFisca). Meanwhile, remote PR #27 left RSA oracle rows `null` and introduced statutory errors: counting full `allocations_familiales` (including age majorations, violating CASF art. R262-11) and full `allocation_soutien_familial` (`0.422 BMAF` instead of capped `0.225 BMAF` per CASF art. R262-10-1), understating single-parent RSA by **`−1,090.54 €/yr`** (`8,770.83 €` vs statutory `9,861.37 €`). | Excluded AF age majorations from `rsa_base_ressources` (`LEGIARTI000051258442`), capped counted ASF at `min(asf, 0.225 × BMAF)` (`LEGIARTI000029006452`), used `salaire_net`, enforced `(age >= 25) \| (nb_enfants >= 1)` (L262-4) and `6 €/mo` payment floor (R262-39), and set 12-month `loge_gratuitement` in the OpenFisca harness. All 5 RSA oracle rows pass within `0.00–0.01 €`. |
| **2019 AGIRC-ARRCO CET scope bug (PR #27 `Spec 0004`)** | PR #27 restricted CET (`0.14 %`) to `cadre=True` on `1–8 PASS`, producing an `82.56 €` gap vs `openfisca-france` at `60,000 €` non-cadre gross pay. Under the 2019 unified AGIRC-ARRCO scheme (ANI 17 Nov 2017), CET (`0.14 %` employee / `0.21 %` employer) applies on **`0–8 PASS` to all employees (cadre & non-cadre)** whenever `salaire_brut > 1 PASS`; only APEC (`0.024 %` / `0.036 %` up to `4 PASS`) is cadre-only. | Fixed CET condition (`salaire_brut > pass_annuel`, assiette `min(salaire_brut, 8 × PASS)`) for all employees and isolated APEC to `cadre=True`. |
| **PR #28 conflicts, CSG half-part increments & pension leak** | PR #28 was `CONFLICTING`, used linear-interpolated CSG thresholds instead of statutory per-half-part increments, omitted `0.3 %` CASA, and failed to wire `pension_retraite` into `rsa_base_ressources` or `allocations_familiales`. | Implemented exact statutory 1-part + per-half-part increments (CSS art. L136-8 III) for 2024 & 2025, added `casa_retraite` (`0.3 %`), merged the 10 % abattement in `pensions_imposables`, and wired pensions into both RSA (`pension_retraite_nette`) and AF (`pensions_imposables`). |
| **`Simulation(reform=...)` broken in `CountryTaxBenefitSystem`** | `policyengine_fr/__init__.py` lacked `reform=None`, causing `Simulation(reform=...)` to raise `TypeError`. Also `MANIFEST.in` omitted `*.json` data files. | Updated `CountryTaxBenefitSystem.__init__(self, reform=None)` and added `*.json` to `MANIFEST.in`. |
| **PR #32 Independent Statute Review (`pullrequestreview-6084243252`)** | Automated statute review verified all headline CAF/URSSAF/DGFiP calculations and flagged 4 P1, 5 P2, and 5 P3 items: (P1-1) `allocations_familiales.py` omitted `pensions_imposables`; (P1-2) `revenu_fiscal_de_reference.py` applied uncapped `× 0.9` to pensions, skipped 6.8 % deductible rental CSG, and `modelled_policies.yaml` named non-existent variables; (P1-3) `YEAR` cotisations/RG variables read 1-Jan parameters without documenting mid-year AGS/SMIC/chômage dates; (P1-4) shared `JORFTEXT000049486510` across RSA/PPA/BMAF & missing 2025 AF/LFI 2026 hrefs; (P2-5..9) `taux_csg_pension` docstring, capital/rent in RSA/PPA resources, dated `LEGIARTI` links, LFSS 2026 `18.6 %` vs `17.2 %` split, IFI `> 1.3 M€` strict inequality; (P3) edge-case tests. | Resolved **all 14 items**: wired `pensions_imposables` into `allocations_familiales.py`; capped/floored pension abattement + deducted 6.8 % rental CSG in `revenu_fiscal_de_reference.py`; wired `revenus_capital` & `revenus_fonciers_nets` into `rsa_base_ressources.py`; split `taux_global` (`18.6 %` in 2026) vs `taux_immobilier` (`17.2 %`) per LFSS 2026 art. 12; changed IFI to `>`; fixed all JORF/LEGIARTI/BO Santé references (`2024-403`, `2025-293`, `2025-294`, `DSS/2B/2025/38`, `DSS/2B/2024/181`, `2026-103`, `2025-1403`); aligned all docs/YAML variable names; and added 14 new YAML edge-case tests (`146 → 160`). |

---

## 3. Workflow, Git & Governance Assumptions

1. **Human Review Gate Respected (`REVIEW.md`):**
   - Per `REVIEW.md` (consolidated from PR #29), changes touching `.github/workflows/` and economic parameters/calculations are **High risk** and require Patrick's explicit sign-off before merging to `main`.
   - **No commits were pushed to `main`**, and existing local (`feat/rsa`) and remote PR branches (`#26`, `#27`, `#28`, `#29`, `#31`, `claude/pending-task-specs`) were left untouched. All work is delivered on `feat/roadmap-2026-consolidation` via [Draft PR #32](https://github.com/alles-delenda-est/policyengine-fr/pull/32).
2. **External Governance Decisions Left to Maintainer (`STRATEGY.md` S1 & S2):**
   - **S1 (GitHub org transfer / PyPI name registration):** Outreach drafts (`docs/upstream-proposal.md` and `docs/upstream-proposal-2026-07.md`) are included in `docs/`, ready for dispatch.
   - **S2 (Version tagging / PyPI release):** Changelog entries are maintained as `towncrier` fragments in `changelog.d/`.

---

## 4. Policy, Statutory & Cross-Repository Modelling Assumptions

### 4.1 Payslip, Employee Cotisations & Employer Labour Cost (`Specs 0001, 0004, 0008`)

- **True-Gross Input Convention (`salaire_brut`):** `salaire_brut` is strictly annual gross pay before employee social contributions.
  - `salaire_declare = max(salaire_brut − cotisations_salariales − csg_deductible, 0)` corresponds to tax-return box `1AJ`.
  - `salaire_net = max(salaire_declare − csg_imposable − crds, 0)` corresponds to net take-home pay before income tax (`net à payer avant impôt`), feeding `rsa_base_ressources`, `prime_activite`, and `revenu_disponible`.
- **1-January Annual Parameter Convention (`YEAR` variables):** `cotisations_salariales`, `cotisations_patronales`, and `reduction_generale` are annual (`YEAR`) variables reading `parameters(period)` on 1 January of the simulated year without infra-annual proration. Mid-year changes (`AGS` `0.20 % → 0.25 %` on `2024-07-01`, anticipated `SMIC` `11.65 € → 11.88 €` on `2024-11-01`, `chômage` `4.05 % → 4.00 %` on `2025-05-01`) take effect in the model on 1 January of the following year.
- **Employee Per-Risk Rates (2024–2025, `gov/urssaf/cotisations_salariales/`):**
  - `PASS` = `46,368 €` (2024) / `47,100 €` (2025).
  - Vieillesse plafonnée (`0–1 PASS`): `6.90 %`; Vieillesse déplafonnée (all gross): `0.40 %`.
  - AGIRC-ARRCO T1 (`0–1 PASS`): `3.15 %`; T2 (`1–8 PASS`): `8.64 %`; CEG T1: `0.86 %`; CEG T2: `1.08 %`.
  - CET (`0–8 PASS`, active iff `salaire_brut > 1 PASS` for **all** employees): `0.14 %`; APEC (`0–4 PASS`, active iff `cadre == True`): `0.024 %`.
- **Employer Contributions & *Réduction générale* (`Spec 0008`):**
  - Maladie bandeau: `7.00 %` up to `2.5 SMIC` in 2024 (`≤ 2.25 SMIC` in 2025 per LFSS 2025 art. 18), `13.00 %` above.
  - Famille bandeau: `3.45 %` up to `3.5 SMIC` in 2024 (`≤ 3.3 SMIC` in 2025 per LFSS 2025 art. 18), `5.25 %` above.
  - Vieillesse `8.55 %` / `2.02 %`, Chômage `4.05 %` (`4.00 %` from `2025-05-01`), AGS `0.20 %` (`0.25 %` from `2024-07-01`), FNAL `0.10 %` (`< 50`) / `0.50 %` (`≥ 50`), CSA `0.30 %`, dialogue social `0.016 %`, AT/MP `taux_at_mp` (default `2.12 %`), AGIRC-ARRCO `4.72 %` / `12.95 %`, CEG `1.29 %` / `1.62 %`, CET `0.21 %`, APEC `0.036 %`.
  - *Réduction générale* (CSS art. L241-13 / D241-7): `C = round((T / 0.6) × (1.6 × SMIC_annuel / salaire_brut − 1), 4)` clipped to `[0, T]`, with `T = 0.3194` (`< 50`) / `0.3234` (`≥ 50`) in 2024 and `0.3193` / `0.3233` in 2025 (full-time `1,820 h/yr` SMIC).

### 4.2 Family & Working-Age Solidarity Benefits (`Bug B3`, `Spec 0002`, `Spec 0009`)

- **AF *Complément dégressif* (`Bug B3`, CSS art. D521-1, al. 3):** Smooths both income thresholds via `max(0, montant_module − depassement / 12)`. Family resources sum current-year `salaire_imposable + pensions_imposables`.
- **RSA (`Spec 0002`, CASF art. L262-1 et s.):**
  - Eligibility: `(age_parent >= 25) | (nb_enfants_charge >= 1)` with dependent children `< 25` (CASF art. L262-4, R262-3).
  - `rsa_montant_forfaitaire`: base `607.75 €` (`2024-01`, Décret 2023-342) → `635.71 €` (`2024-04`, Décret 2024-396) → `646.52 €` (`2025-04`, Décret 2025-293), with CASF art. R262-1 composition weights (`+50 %` 2nd person, `+30 %` 3rd person and 2nd child of a couple, `+40 %` from the 3rd child onwards) and *RSA majoré* (`1.28412 + 0.42804 × nb_enfants`) for isolated parents.
  - `rsa_base_ressources`: `(salaire_net + pension_retraite_nette + pensions_alimentaires_percues + revenus_capital + revenus_fonciers_nets) / 12 + af_hors_majoration_age + min(asf, 0.225 × BMAF × nb_enfants)`. Payment floor: `6 €/month` (CASF art. R262-39).
- **Prime d'activité (`Spec 0009`, CSS art. L841-1 et s.):**
  - Base `ppa_montant_forfaitaire`: `595.25 €` (`2024-01`) → `622.63 €` (`2024-04`, Décret 2024-403) → `633.21 €` (`2025-04`, Décret 2025-294).
  - Individual `ppa_bonification` (CSS art. L842-3, D843-2): for each active member aged `>= 18`, ramps linearly from `0` at `59 × SMIC_horaire_brut` (at Jan 1) to `0.29101 × montant_de_base` at `120 × SMIC_horaire_brut`.
  - Formula: `max(montant_base − ppa_non_bonifiee, 0)` with `15 €/month` payment floor (CSS art. D843-3).

### 4.3 Retirement Pensions, RFR & Banded CSG/CRDS/CASA (`Specs 0005, 0006`)

- **Statutory RFR Thresholds (CSS art. L136-8 III):**
  - 2024 (1 part + per-half-part increment): Exonération `12,230 €` (`+3,265 €`), Taux réduit (`3.8 %`, all deductible) `15,988 €` (`+4,269 €`), Taux médian (`6.6 %`, `4.2 %` deductible + `0.3 %` CASA) `24,813 €` (`+6,623 €`), Taux normal (`8.3 %`, `5.9 %` deductible + `0.3 %` CASA) above; CRDS `0.5 %` whenever CSG > 0.
  - 2025: `12,817 €` (`+3,422 €`), `16,755 €` (`+4,474 €`), `26,004 €` (`+6,941 €`).
  - Evaluated on current-year `revenu_fiscal_de_reference` (which applies the floored and capped 10 % CGI art. 158-5-a allowance to pre-CSG pensions + alimony, avoiding circularity in year N while preserving exact CEHR and CSG tiering for high pensions).

### 4.4 Multi-Year Parameterisation (`Spec 0007`: 2024, 2025 & LFSS 2026 Capital Split)

- **IR 2024 (LFI 2025, Loi n° 2025-127, +1.8 %)** & **IR 2025 (LFI 2026, Loi n° 2026-103 art. 4, +0.9 %):** 2025 brackets `11,600 / 29,579 / 84,577 / 181,917 €`; QF cap `1,807 €` (`4,262 €` case T); Décote `897 € / 1,483 €`.
- **Social & Benefit 2025 Dates:** `PASS = 47,100 €` (`2025-01-01`); `SMIC horaire = 11.88 €` (`2024-11-01`); `BMAF = 466.44 €` (`2024-04-01`) → `474.37 €` (`2025-04-01`, Instruction DSS/2B/2025/38); AF 2025 plafonds `65,473 € / 91,627 €` + `6,546 €`/child (Instruction DSS/2B/2024/181).
- **LFSS 2026 Social Levies Split (Loi n° 2025-1403 du 30 déc. 2025, art. 12):** `patrimoine/taux_global` rises from `17.2 %` to `18.6 %` on `2026-01-01` for financial capital (`revenus_capital` *produits de placement*), while `patrimoine/taux_immobilier` stays at `17.2 %` for bare rents (`revenus_fonciers_nets`) and real-estate capital gains (`plus_values_immobilieres`).

### 4.5 Cross-Repository Reuse Matrix (`budget_fr_sim_test` & `LVTShift`)

| Source Repo & Ref | Source File / Specification | Integrated Target in `policyengine-fr` | Notes & Assumptions |
|---|---|---|---|
| `LVTShift` (`de85827`) | `lvtshift-fr/src/lvtshift/taxes_2024.py` | `variables/gov/dgfip/patrimoine_et_hauts_revenus.py` (`ifi`, `impot_plus_values_immobilieres`), `variables/gov/dgfip/fiscalite_locale.py` (`taxe_fonciere`, `taxe_habitation_residence_secondaire`, `taxe_valeur_sol`) | Exact statutory CGI art. 964–977 IFI (`assiette > 1,300,000 €`, 30 % RP abatement, `1.3–1.4 M€` décote) and 3 % State management fee on local TFPB/THRS bills (CGI art. 1641). |
| `LVTShift` (`de85827`) | `lvtshift-fr/site/public/data/yields.json` + scenarios | `policyengine_fr/data/lvt_yields.json` + `lvt_yields.source.json` (SHA-256 verified) + `policyengine_fr/reforms/lvt_shift.py` (`S1`–`S3_IFI`) | Pinned equal-yield LVT replacement scenarios (`1.10 %` in `S1` to `1.34 %` in `S3_IFI`) neutralizing replaced property/gain/rental/IFI taxes via `Reform` subclasses. |
| `budget_fr_sim_test` (`review/day0`, `review/day1`) | `src/engine/ir-tranches.js`, `levers_catalog.yaml` | `cehr`, `pfu_ir`, `prelevements_sociaux_patrimoine`, `revenus_fonciers_nets` | CEHR (`3 % / 4 %` above `250k / 500k`), PFU (`12.8 %` IR + `17.2 % / 18.6 %` PS), micro-foncier (`30 %` ≤ `15k €`) / réel + `6.8 %` deductible CSG. |
| `budget_fr_sim_test` (`review/day1`) | `docs/DECISIONS.md` (**Decision D-P6**: targeted pension under-indexation above threshold, clawback `[0.35, 0.45]`) | `policyengine_fr/reforms/budget_levers.py` + `tests/test_reforms.py` | Bottom-up simulation of D-P6 (`−2 %` above `24,000 €/yr` on a `48,000 €/yr` retiree) confirms mechanical IR + CSG/CRDS/CASA clawback falls squarely inside `day1`'s `[0.35, 0.45]` calibration band. |

### 4.6 Independent Oracle Validation Summary (`25/25` Live Rows Passing)

All 25 rows in `tests/fixtures/oracle_values.yaml` have `official != null` (`0` skipped rows) and pass live in `tests/test_oracle.py`:

| Module | Oracle Source | Rows | Max Observed Delta |
|---|---|---|---|
| `impot_revenu` (2024 cases: single, couple, 1–4 children, up to `200k €`) | Official DGFiP IR Simulator (`impots.gouv.fr`) | 10 | `≤ 0.52 €` (statutory integer rounding) |
| `allocations_familiales` + `allocation_soutien_familial` (incl. differential ASF) | `openfisca-france` `175.0.45` (`../.venv-of312`) | 5 | `0.00–0.02 €` |
| `rsa` (single `0 €`, couple+2 `0 €`, single parent+1 w/ & w/o pension, `6k €` gross wage) | `openfisca-france` `175.0.45` | 5 | `0.00–0.01 €` |
| `prime_activite` (`6k €` gross wage stacked with RSA; plus 9 YAML & grid checks) | `openfisca-france` `175.0.45` | 1 (+9 YAML) | `0.00 €` |
| `salaire_net` & `salaire_declare` (`30k €`, `60k €` non-cadre & `60k €` cadre) | `openfisca-france` `175.0.45` | 3 | `0.01–1.44 €` (`< 0.003 %`, float32 rounding) |
| `reduction_generale` (employer Fillon reduction at full-time SMIC `21,203 €`) | `openfisca-france` `175.0.45` | 1 | `0.00 €` |


---

## 5. Interactive Studio UI Architecture & Design Assumptions (`feat/ui-studio`)

1. **Zero-Extra-Dependency Python Microsimulation Server (`policyengine_fr/studio.py`):**
   - Uses stdlib `http.server.ThreadingHTTPServer` so `policyengine-fr` keeps its minimal `pyproject.toml` dependency footprint (no Flask/FastAPI install required).
   - Caches compiled `CountryTaxBenefitSystem(reform=...)` instances via `@lru_cache(maxsize=64)` and evaluates the **61-point earnings curve** (`salaire_brut` → `revenu_disponible`, stacked benefits, and effective marginal rate `EMTR %`) in a **single vectorised `Simulation` pass** (`< 15 ms` end-to-end).
2. **Cross-Repository UX & Design Reuse (`budget_fr_sim_test` & `LVTShift`):**
   - Reuses the French Civic Editorial palette & typography (`Crimson Pro` + `Inter`, deep marine `#1a2744`, emerald `#1e6b4b`, crimson `#b5281e`, warm stone `#f6f4ef`, `tabular-nums` anti-jitter numbers), `useDeferredValue` + `AbortController` 60fps slider responsiveness, URL hash state sharing (`#s=...`), `;`-delimited French CSV export with formula-injection protection, and inline `InfoPopover` statutory citations wired directly to `/api/metadata`.
   - Provides a global **`€ / mois` ↔ `€ / an` toggle** (scaling inputs and outputs instantaneously on the client), `2024` ↔ `2025` legislation toggle, 7 one-click household presets, and combinable `LVTShift` (`S1`–`S3_IFI`) + `budget_fr_sim_test` (`IR`, `CSG`, `ir_freeze_2024`, and `day1` `D-P6` targeted pension under-indexation with live mechanical clawback readout) reforms.
