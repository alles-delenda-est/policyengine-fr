# Project Review & Assumptions Log — `policyengine-fr`

> **Prepared for:** Patrick (`alles-delenda-est`)
> **Date:** 2026-11-27
> **Active Repository:** `C:\Users\patri\projects\PolicyEngineFR\policyengine-fr` (`https://github.com/alles-delenda-est/policyengine-fr.git`)
> **Implementation Branch:** `feat/roadmap-2026-consolidation` (branched cleanly off `origin/main` `27ec806`)
> **Verification Status:** `146` YAML tests + `56` `pytest` tests passing (`25/25` live DGFiP & `openfisca-france` v175.0.45 oracle rows, `0` skips, `ruff==0.17.4` clean, `check_doc_currency.py` in sync).

---

## 1. Objective Confirmation

1. **North-Star Goal:** Build **`policyengine-fr`**, a statute-accurate, open-source French tax-benefit, labour-cost, and patrimonial microsimulation country package on `policyengine-core` (modelled structurally on `policyengine-canada` so it plugs into the multi-country `policyengine.py` / API / web-app stack without forking `policyengine-core`).
2. **Engineering & Epistemic Standards:**
   - Mirrored `parameters/` (1-leaf-per-file dated YAML with official Légifrance/BOFiP/URSSAF `reference` links), `variables/` (vectorised `float32`-safe `Variable` formulas), and `tests/` (YAML unit + integration suites).
   - Multi-layer verification: YAML unit tests (`policyengine-core test`), property/invariant tests (`tests/test_properties.py`), golden-master regression (`tests/test_golden_master.py`), cross-repo reform tests (`tests/test_reforms.py`), and **independent oracle validation** (`tests/fixtures/oracle_values.yaml` checked against DGFiP and `openfisca-france` in `../.venv-of312`).
   - **Zero silent scope-narrowings:** Every departure from French statute is explicitly recorded in `policyengine_fr/modelled_policies.yaml` (`simplifications:`) and mirrored 1-for-1 in `docs/coverage.md`, enforced automatically by `bin/check_doc_currency.py`.
3. **Cross-Repository Reuse Mandate:**
   - Reuse and unify validated fiscal mechanisms, statutory constants, calibration data, and policy-lever specifications from:
     - `alles-delenda-est/budget_fr_sim_test` (`review/day0` and `review/day1`, plus local `C:\Users\patri\projects\budget_fr_sim_test`)
     - `alles-delenda-est/LVTShift` (`lvtshift-fr`, local `C:\Users\patri\projects\LVTshiftFR`)

---

## 2. Diagnostic Findings & Bugs Resolved During Review

| Area | Finding Discovered | Resolution Implemented |
|---|---|---|
| **Workspace topology** | `C:\Users\patri\projects\PolicyEngineFR` contains an older shallow clone (`9f7cec3`, June 17), `.venv-of312` (Python 3.12 `openfisca-france` v175.0.45 oracle env), and `policyengine-fr\` (the canonical inner git repo). | Preserved all outer files and `.venv-of312` untouched; implemented all changes inside `policyengine-fr\` on branch `feat/roadmap-2026-consolidation`. |
| **RSA statutory & oracle bugs (`feat/rsa` vs PR #27)** | Local `feat/rsa` failed its OpenFisca check by `−890.27 €` because `compute_af_openfisca.py` set `statut_occupation_logement = {"2024-01": "locataire_vide"}` (only January, and tenant without APL = no *forfait logement* in OpenFisca). Meanwhile, remote PR #27 left RSA oracle rows `null` and introduced statutory errors: counting full `allocations_familiales` (including age majorations, violating CASF art. R262-11 3°) and full `allocation_soutien_familial` (`0.422 BMAF` instead of capped `0.225 BMAF` per CASF art. R262-10-1), understating single-parent RSA by **`−1,090.54 €/yr`** (`8,770.83 €` vs statutory `9,861.37 €`). | Reconciled both: excluded AF age majorations from `rsa_base_ressources`, capped counted ASF at `min(asf, 0.225 × BMAF)`, used `salaire_net`, enforced `(age >= 25) \| (nb_enfants >= 1)` (L262-4) and `6 €/mo` payment floor (R262-39), and set 12-month `loge_gratuitement` in the OpenFisca harness. All 5 RSA oracle rows pass within `0.00–0.01 €`. |
| **2019 AGIRC-ARRCO CET scope bug (PR #27 `Spec 0004`)** | PR #27 restricted CET (`0.14 %`) to `cadre=True` on `1–8 PASS`, producing an `82.56 €` gap vs `openfisca-france` at `60,000 €` non-cadre gross pay. Under the 2019 unified AGIRC-ARRCO scheme (ANI 17 Nov 2017), CET (`0.14 %` employee / `0.21 %` employer) applies on **`0–8 PASS` to all employees (cadre & non-cadre)** whenever `salaire_brut > 1 PASS`; only APEC (`0.024 %` / `0.036 %` up to `4 PASS`) is cadre-only. | Fixed CET condition (`salaire_brut > pass_annuel`, assiette `min(salaire_brut, 8 × PASS)`) for all employees and isolated APEC to `cadre=True`. Matches `openfisca-france` across `20k / 30k / 50k / 60k` non-cadre & cadre rows. |
| **PR #28 conflicts, CSG half-part increments & pension leak** | PR #28 was `CONFLICTING`, used linear-interpolated CSG thresholds instead of statutory per-half-part increments, omitted `0.3 %` CASA, and failed to wire `pension_retraite` into `rsa_base_ressources` or `allocations_familiales`. | Implemented exact statutory 1-part + per-half-part increments (CSS art. L136-8 III) for 2024 & 2025, added `casa_retraite` (`0.3 %`), merged the 10 % abattement in `pensions_imposables`, and wired pensions into RSA (`pension_retraite_nette`) and AF (`pensions_imposables`). |
| **`Simulation(reform=...)` broken in `CountryTaxBenefitSystem`** | `policyengine_fr/__init__.py` defined `def __init__(self): super().__init__(...)` without accepting `reform=None`, causing `policyengine_core.simulations.Simulation(reform=...)` to raise `TypeError`. Also `MANIFEST.in` omitted `*.json` data files. | Updated `CountryTaxBenefitSystem.__init__(self, reform=None)` to forward `reform=reform` to `super().__init__(...)`, and added `*.json` to `MANIFEST.in`. |
| **Ruff version drift** | Local `.venv` had `ruff 0.15.18`, whereas `origin/main` (PR #30) and PR #31 formatted Markdown Python blocks with `ruff==0.17.4`. | Upgraded `.venv` ruff to `0.17.4` and pinned `ruff==0.17.4` in `pyproject.toml` and `.github/workflows/ci.yaml`. |

---

## 3. Workflow, Git & Governance Assumptions

1. **Human Review Gate Respected (`REVIEW.md`):**
   - Per `REVIEW.md` (consolidated from PR #29), changes touching `.github/workflows/` and economic parameters/calculations are **High risk** and require Patrick's explicit sign-off before merging to `main`.
   - Accordingly, **no commits were pushed to `main`**, and existing local (`feat/rsa`) and remote PR branches (`#26`, `#27`, `#28`, `#29`, `#31`, `claude/pending-task-specs`) were left untouched. All work is delivered on `feat/roadmap-2026-consolidation` via a **Draft PR** with full test/oracle output.
2. **External Governance Decisions Left to Maintainer (`STRATEGY.md` S1 & S2):**
   - **S1 (GitHub org transfer / PyPI name registration):** Outreach letters (`docs/upstream-proposal.md` and `docs/upstream-proposal-2026-07.md`) are included in `docs/`, ready for Patrick to send when desired.
   - **S2 (Version tagging / PyPI release):** Changelog entries are recorded as `towncrier` fragments in `changelog.d/` without prematurely burning a `v0.1.0`/`v0.2.0` tag.

---

## 4. Policy, Statutory & Cross-Repository Modelling Assumptions

### 4.1 Payslip, Employee Cotisations & Employer Labour Cost (`Specs 0001, 0004, 0008`)

- **True-Gross Input Convention (`salaire_brut`):** `salaire_brut` is strictly annual gross pay before employee social contributions.
  - `salaire_declare = max(salaire_brut − cotisations_salariales − csg_deductible, 0)` corresponds to tax-return box `1AJ` (feeding the 10 % professional-expenses deduction in `salaire_imposable`).
  - `salaire_net = max(salaire_declare − csg_imposable − crds, 0)` corresponds to net take-home pay before income tax (`net à payer avant impôt`), feeding `rsa_base_ressources`, `prime_activite`, and `revenu_disponible`.
- **Employee Per-Risk Rates (2024–2025, `gov/urssaf/cotisations_salariales/`):**
  - `PASS` = `46,368 €` (2024) / `47,100 €` (2025).
  - Vieillesse plafonnée (`0–1 PASS`): `6.90 %`; Vieillesse déplafonnée (all gross): `0.40 %`.
  - AGIRC-ARRCO T1 (`0–1 PASS`): `3.15 %`; T2 (`1–8 PASS`): `8.64 %`.
  - CEG T1 (`0–1 PASS`): `0.86 %`; CEG T2 (`1–8 PASS`): `1.08 %`.
  - CET (`0–8 PASS`, active iff `salaire_brut > 1 PASS` for **all** employees): `0.14 %`.
  - APEC (`0–4 PASS`, active iff `cadre == True`, default `False`): `0.024 %`.
  - Standard private-sector full-time assumption: no mandatory *mutuelle* deduction, overtime exemption, Alsace-Moselle (`1.30 %`), or civil-service regime.
- **Employer Contributions & *Réduction générale* (`Spec 0008`, `gov/urssaf/cotisations_patronales/` & `reduction_generale/`):**
  - Maladie bandeau: `7.00 %` up to `2.5 SMIC` in 2024 (`≤ 2.25 SMIC` from 2025-01-01 per LFSS 2025 art. 18), `13.00 %` (`7 % + 6 %` complement) above.
  - Famille bandeau: `3.45 %` up to `3.5 SMIC` in 2024 (`≤ 3.3 SMIC` from 2025-01-01 per LFSS 2025 art. 18), `5.25 %` (`3.45 % + 1.80 %`) above.
  - Vieillesse plafonnée `8.55 %` (`1 PASS`), déplafonnée `2.02 %` (2024–2025), Chômage `4.05 %` (`4 PASS`, `4.00 %` from 2025-05-01 simplified to annual 2025 `4.05 %` / standard January 1 reference; documented in YAML), AGS `0.20 %` (`2024-01-01`) → `0.25 %` (`2024-07-01`, `4 PASS`), FNAL `0.10 %` (`< 50` employees on `1 PASS`) or `0.50 %` (`≥ 50` employees on all gross, controlled by `effectif_entreprise`, default `10`), CSA `0.30 %`, AT/MP input `taux_at_mp` (default `0.0212` national average, of which `0.46 pt` in 2024 / `0.50 pt` in 2025 enters the Fillon `T` perimeter), AGIRC-ARRCO `4.72 %` / `12.95 %`, CEG `1.29 %` / `1.62 %`, CET `0.21 %`, APEC `0.036 %`.
  - *Réduction générale* (CSS art. L241-13 / D241-7): `C = round((T / 0.6) × (1.6 × SMIC_annuel / salaire_brut − 1), 4)` clipped to `[0, T]`, with `T = 0.3194` (`< 50`) / `0.3234` (`≥ 50`) in 2024 and `0.3193` / `0.3233` in 2025. Assumes full-time `1,820 h/yr` SMIC without part-time hourly proration.

### 4.2 Family & Working-Age Solidarity Benefits (`Bug B3`, `Spec 0002`, `Spec 0009`)

- **AF *Complément dégressif* (`Bug B3`, CSS art. D521-1, al. 3):** Smooths both income thresholds via `max(0, plafond + 12 × af_retenue − ressources) / 12`, eliminating the `~745 €/yr` cliff. Parental resource proxy sums `salaire_imposable + pensions_imposables`.
- **RSA (`Spec 0002`, CASF art. L262-1 et s.):**
  - Eligibility: `(age_adulte_max >= 25) | (nb_enfants_charge >= 1)` with dependent children `< 25` (CASF art. L262-4, R262-3). *RSA jeune actif* (`< 25` with 3,214 hours worked) is documented under `simplifications:`.
  - `rsa_montant_forfaitaire`: base `607.75 €` (`2024-01`) → `635.71 €` (`2024-04`) → `646.52 €` (`2025-04`), with standard couple/child weights (`+50 %` spouse/1st child, `+30 %` 2nd, `+40 %` 3rd+) and *RSA majoré* (`1.28412` isolated parent + `0.42804` per child) when `parent_isole` is true.
  - `rsa_forfait_logement`: `12 % / 24 % / 29.7 %` of base RSA for `1 / 2 / 3+` persons, applied unconditionally (documented simplification; matches OpenFisca `loge_gratuitement` / APL-recipient regime).
  - `rsa_base_ressources`: `(salaire_net + pension_retraite_nette + pensions_alimentaires_percues) / 12 + af_hors_majoration_age + min(asf, 0.225 × BMAF)`. Payment suppressed below `6 €/month` (CASF art. R262-39).
- **Prime d'activité (`Spec 0009`, CSS art. L841-1 et s.):**
  - Base `ppa_montant_forfaitaire`: `604.60 €` (`2024-01`) → `622.63 €` (`2024-04`) → `633.21 €` (`2025-04`), using the statutory household-composition scale + `parent_isole` majoration (`1.28412` + `0.42804`/child).
  - Individual `ppa_bonification` (CSS art. L842-3, D843-2): for each active member aged `>= 18`, ramps linearly from `0` at `59 × SMIC_horaire_brut` (evaluated at Jan 1 of the year) to `0.29101 × montant_forfaitaire_base` at `120 × SMIC_horaire_brut`, remaining constant above. Verified to **`0.00–0.05 €` annual delta** against `openfisca-france` across 4 live oracle rows.
  - Closed-form monthly formula: `max(ppa_mf − ppa_fl + bonif + 0.61 × rev_pro − ressources_hors_rsa − rsa_non_bonifie, 0)`, with `15 €/month` payment floor (CSS art. D843-2).

### 4.3 Retirement Pensions & Banded CSG/CRDS/CASA (`Specs 0005, 0006`)

- **Statutory RFR Thresholds (CSS art. L136-8 III):**
  - 2024 (1 part + per-half-part increment): Exonération `12,230 €` (`+3,265 €`), Taux réduit (`3.8 %`, all deductible) `15,988 €` (`+4,269 €`), Taux médian (`6.6 %`, `4.2 %` deductible + `0.3 %` CASA) `24,813 €` (`+6,623 €`), Taux normal (`8.3 %`, `5.9 %` deductible + `0.3 %` CASA) above; CRDS `0.5 %` applies whenever CSG > 0.
  - 2025 (+4.8 % statutory revalorisation): `12,817 €` (`+3,422 €`), `16,755 €` (`+4,474 €`), `26,004 €` (`+6,941 €`).
  - Evaluates against current-year `revenu_fiscal_de_reference` as a proxy for N-2 RFR (documented caveat #3).
- **Merged 10 % Pension Abattement (`pensions_imposables`, CGI art. 158, 5, a):**
  - Sums `pension_retraite_declaree` (`pension_retraite − csg_retraite_deductible`) and `pensions_alimentaires_percues` per individual before applying the per-beneficiary floor (`442 €` in 2024 / `450 €` in 2025) and per-foyer ceiling (`4,321 €` in 2024 / `4,399 €` in 2025).

### 4.4 Multi-Year Parameterisation (`Spec 0007`: 2024 & 2025)

- **IR 2025 (LFI 2025, Loi n° 2025-127 art. 2, +2.0 %):** Brackets `11,497 / 29,315 / 83,823 / 180,294 €`; QF cap `1,791 €` per half-part (`4,224 €` parent isolé first child); Décote `889 € / 1,470 €` (`seuil` via `889 / 0.4525 ≈ 1,964 €` single, `1,470 / 0.4525 ≈ 3,248 €` couple); 10 % salary floor/cap `504 € / 14,426 €`.
- **Social & Benefit 2025 Dates:** `PASS = 47,100 €` (`2025-01-01`); `SMIC horaire = 11.88 €` (`2024-11-01`, early Nov 2024 revalorisation carrying into 2025); `BMAF = 466.44 €` (`2024-04-01`) → `474.37 €` (`2025-04-01`, +1.7 %); AF 2025 plafonds `+4.8 %` (`78,565 €` / `104,719 €`, `+6,546 €`/child).

### 4.5 Cross-Repository Reuse Matrix (`budget_fr_sim_test` & `LVTShift`)

| Source Repo & Ref | Source File / Specification | Integrated Target in `policyengine-fr` | Notes & Assumptions |
|---|---|---|---|
| `LVTShift` (`de85827`) | `lvtshift-fr/src/lvtshift/taxes_2024.py` | `variables/gov/dgfip/patrimoine_et_hauts_revenus.py` (`ifi`, `impot_plus_values_immobilieres`), `variables/gov/dgfip/fiscalite_locale.py` (`taxe_fonciere`, `taxe_habitation_residence_secondaire`, `taxe_valeur_sol`), `parameters/gov/dgfip/ifi/` & `fiscalite_locale/` | Reused exact statutory CGI art. 977 IFI brackets, 30 % RP abatement (art. 973), `1.3–1.4 M€` décote (`17,500 − 1.25 % × V`), 3 % State fee on TFPB/THRS (CGI art. 1641), 50 % built-property VLC coefficient (CGI art. 1388), and national average TFPB (`39.74 %`) & THRS (`24.80 %`) rates. |
| `LVTShift` (`de85827`) | `lvtshift-fr/data/processed/tax_yields_2024.json` + `scenarios.py` | `policyengine_fr/data/lvt_yields.json` + `lvt_yields.source.json` (SHA-256 `239561e7afe238d7...`) + `policyengine_fr/reforms/lvt_shift.py` (`S1`, `S2`, `S2_IFI`, `S3`, `S3_IFI`) | Pinned DGFiP/INSEE Comptes nationaux patrimonial land-base (`AN.2111` `3,962.5 Md€` taxable land base) and tax yields (`16.76–36.22 Md€`) with full SHA-256 provenance, computing revenue-neutral LVT rates (`0.423 %`–`0.914 %`) inside `Reform` subclasses. |
| `budget_fr_sim_test` (`review/day0`, `review/day1`) | `data/reference/baseline_2026.yaml`, `parameters.yaml`, `levers_catalog.yaml` | `variables/gov/dgfip/patrimoine_et_hauts_revenus.py` (`cehr`, `pfu_ir`, `prelevements_sociaux_patrimoine`), `variables/gov/dgfip/ir/revenus_fonciers_nets.py` | Added CEHR (`3 % / 4 %` above `250k / 500k`), PFU (`12.8 %` IR + `17.2 %` PS, with `option_bareme_rcm` toggle), `revenus_fonciers_nets` (30 % micro-foncier ≤ `15k €` or réel + 6.8 % deductible CSG), and RFR integration. |
| `budget_fr_sim_test` (`review/day1`) | `docs/DECISIONS.md` (**Decision D-P6**: targeted pension under-indexation above threshold, clawback `[0.35, 0.45]`) | `policyengine_fr/reforms/budget_levers.py` (`create_ir_rate_shift_reform`, `create_ir_freeze_brackets_reform`, `create_csg_activity_shift_reform`, `create_targeted_pension_underindexation_reform`) + `tests/test_reforms.py` | Microsimulates PLF budget levers directly on households. Bottom-up simulation of D-P6 (`−2 %` above `24,000 €/yr` on a `48,000 €/yr` retiree) confirms mechanical IR + CSG/CRDS/CASA clawback falls squarely inside `day1`'s `[0.35, 0.45]` calibration band. |

### 4.6 Independent Oracle Validation Summary (`25/25` Live Rows Passing)

All 25 rows in `tests/fixtures/oracle_values.yaml` have `official != null` (`0` skipped rows) and pass live in `tests/test_oracle.py`:

| Module | Oracle Source | Rows | Max Observed Delta |
|---|---|---|---|
| `impot_revenu` (2024 cases: single, couple, 1–4 children, up to `200k €`) | Official DGFiP IR Simulator (`impots.gouv.fr`) | 10 | `≤ 0.52 €` (statutory integer rounding) |
| `allocations_familiales` + `allocation_soutien_familial` (incl. differential ASF) | `openfisca-france` `175.0.45` (`../.venv-of312`) | 5 | `0.00–0.02 €` |
| `rsa` (single `0 €`, couple+2 `0 €`, single parent+1 w/ & w/o pension, `6k €` gross wage) | `openfisca-france` `175.0.45` | 5 | `0.00–0.01 €` |
| `prime_activite` (`6k €` gross wage stacked with RSA; plus YAML & grid checks up to `2 SMIC`) | `openfisca-france` `175.0.45` | 1 (+7 YAML) | `0.00 €` |
| `salaire_net` & `salaire_declare` (`30k €`, `60k €` non-cadre & `60k €` cadre) | `openfisca-france` `175.0.45` | 3 | `0.01–1.44 €` (`< 0.003 %`, float32 rounding) |
| `reduction_generale` (employer Fillon reduction at full-time SMIC `21,203 €`) | `openfisca-france` `175.0.45` | 1 | `0.00 €` |
