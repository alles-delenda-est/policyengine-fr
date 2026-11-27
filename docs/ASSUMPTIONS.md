# Project Review & Assumptions Log — `policyengine-fr`

> **Prepared for:** Patrick (`alles-delenda-est`)
> **Date:** 2026-11-27
> **Active Repository:** `C:\Users\patri\projects\PolicyEngineFR\policyengine-fr` (`https://github.com/alles-delenda-est/policyengine-fr.git`)
> **Mainline & Active PR:** `main` at `4b73099` (squash-merged PR #32) · Active branch `feat/ui-studio` ([PR #33](https://github.com/alles-delenda-est/policyengine-fr/pull/33))
> **Verification Status:** `161` YAML tests + `62` `pytest` tests + `4` Vitest tests (`25/25` live 2024 DGFiP & `openfisca-france` v175.0.45 oracle rows, `0` skips, `ruff==0.17.4` clean, `eslint` clean, `check_doc_currency.py` in sync).

---

## 1. Objective Confirmation

1. **North-Star Goal:** Build **`policyengine-fr`**, a statute-accurate, open-source French tax-benefit, labour-cost, and patrimonial microsimulation country package on `policyengine-core` (modelled structurally on `policyengine-canada` so it plugs into the multi-country `policyengine.py` / API / web-app stack without forking `policyengine-core`), paired with an accessible French Studio UI.
2. **Engineering & Epistemic Standards:**
   - Mirrored `parameters/` (1-leaf-per-file dated YAML with official Légifrance/BOFiP/URSSAF/BO Santé `reference` links), `variables/` (vectorised `float32`-safe `Variable` formulas), and `tests/` (YAML unit + integration suites).
   - Multi-layer verification: YAML unit tests (`policyengine-core test`), property/invariant tests (`tests/test_properties.py`), golden-master regression (`tests/test_golden_master.py`), cross-repo reform tests (`tests/test_reforms.py`), Studio API tests (`tests/test_studio_api.py`), UI unit tests (`ui/src/lib/format.test.js`), and **independent 2024 oracle validation** (`tests/fixtures/oracle_values.yaml` checked against DGFiP and `openfisca-france` in `../.venv-of312`).
   - **Zero silent scope-narrowings:** Every departure from French statute is explicitly recorded in `policyengine_fr/modelled_policies.yaml` (`simplifications:`) and mirrored 1-for-1 in `docs/coverage.md`, enforced automatically by `bin/check_doc_currency.py`.
3. **Cross-Repository Reuse Mandate:**
   - Reuse and unify validated fiscal mechanisms, statutory constants, calibration data, and policy-lever specifications from:
     - `alles-delenda-est/budget_fr_sim_test` (`review/day0` and `review/day1`, plus local `C:\Users\patri\projects\budget_fr_sim_test`)
     - `alles-delenda-est/LVTShift` (`lvtshift-fr`, local `C:\Users\patri\projects\LVTshiftFR`)

---

## 2. Diagnostic Findings & Review Issues Resolved

| Area | Finding Discovered | Resolution Implemented |
|---|---|---|
| **Workspace topology** | `C:\Users\patri\projects\PolicyEngineFR` contains an older shallow clone (`9f7cec3`, June 17), `.venv-of312` (Python 3.12 `openfisca-france` v175.0.45 oracle env), and `policyengine-fr\` (the canonical inner git repo). | Preserved outer artifacts and `.venv-of312`; always `cd` into `policyengine-fr\` so the outer shallow clone never shadows `policyengine_fr`. |
| **RSA statutory & oracle bugs (`feat/rsa` vs PR #27)** | Local `feat/rsa` failed its OpenFisca check by `−890.27 €` because `statut_occupation_logement` was set only for `2024-01` and to `locataire_vide`. Remote PR #27 left RSA oracle rows `null` and counted full `allocations_familiales` + full `allocation_soutien_familial` (`−1,090.54 €/yr` single-parent error). | Excluded AF age majorations (`LEGIARTI000051258442`), capped counted ASF at `min(asf, 0.225 × BMAF)` (`LEGIARTI000029006452`), used `salaire_net`, enforced `(age >= 25) \| (nb_enfants >= 1)` (L262-4) & `6 €/mo` floor (R262-39), and fixed the OpenFisca housing setup. |
| **2019 AGIRC-ARRCO CET scope bug (PR #27 `Spec 0004`)** | PR #27 restricted CET (`0.14 %`) to `cadre=True` on `1–8 PASS`, producing an `82.56 €` gap vs `openfisca-france`. | Applied CET (`0–8 PASS`, `salaire_brut > 1 PASS`) to all employees (ANI 17 Nov 2017) and isolated APEC (`0.024 %` / `0.036 %`) to `cadre=True`. |
| **PR #28 conflicts, CSG half-part increments & pension leak** | PR #28 was `CONFLICTING`, interpolated CSG thresholds linearly, omitted `0.3 %` CASA, and omitted pensions from RSA and AF resource bases. | Implemented exact statutory 1-part + per-half-part increments (CSS art. L136-8 III) for 2024 & 2025, added `casa_retraite`, merged the 10 % abattement in `pensions_imposables`, and wired pensions into RSA and AF. |
| **`CountryTaxBenefitSystem(reform=...)` & D-P6 / S3 audit bugs** | `CountryTaxBenefitSystem.__init__(self, reform=None)` ignored `reform`; `LVTShift` `S3` neutralized `revenus_fonciers_nets` globally (falsely qualifying landlords for RSA and zeroing their RFR); `D-P6` did not propagate `pension_retraite_effective` into `revenu_fiscal_de_reference`; `assiette_csg_crds_salaire` omitted the `4 PASS` cap on the `1.75 %` abatement; 2025 salary/pension abatement caps were missing. | Wired idempotent `reform` support in `__init__.py` (so both `CountryTaxBenefitSystem(reform=...)` and `Simulation(reform=...)` work without double-apply); exempted rents inside `revenu_net_imposable` under `S3`; wired `pension_retraite_effective` into `D-P6` RFR; added `min(brut, 4 × PASS)` CSG abatement cap; added LFI 2026 2025 abatement parameters (`14,555 / 509 €` & `4,439 / 454 €`). |
| **PR #32 Independent Statute Reviews** | First review (`pullrequestreview-6084243252`) raised 14 P1–P3 items; second review (`pullrequestreview-6084768334`) gave `VERDICT: APPROVE` with 5 minor non-blocking notes (`CDHR` in `not_modelled`, RSA R262-3 / D843-1 refs, 1-Jan SMIC in `ppa_bonification`). | Resolved all P1–P3 items + follow-up notes and squash-merged PR #32 into `main` (`4b73099`). |

---

## 3. Workflow, Git & Governance Assumptions

1. **Human Review Gate (`REVIEW.md`):**
   - Per `REVIEW.md`, PR #32 remained gated until human confirmation, passed all 6 CI checks, and was squash-merged into `main` at Patrick's instruction (`4b73099`).
   - All subsequent UI & audit-fix work lives on branch `feat/ui-studio` ([PR #33](https://github.com/alles-delenda-est/policyengine-fr/pull/33)) for review.
2. **External Governance Decisions Left to Maintainer (`STRATEGY.md` S1 & S2):**
   - **S1 (GitHub org transfer / PyPI name registration):** Outreach drafts (`docs/upstream-proposal.md` and `docs/upstream-proposal-2026-07.md`) remain in `docs/`.
   - **S2 (Version tagging / PyPI release):** Changelog entries are maintained as `towncrier` fragments in `changelog.d/`.

---

## 4. Policy, Statutory & Cross-Repository Modelling Assumptions

### 4.1 Payslip, Employee Cotisations & Employer Labour Cost (`Specs 0001, 0004, 0008`)

- **True-Gross Input Convention (`salaire_brut`):** Strictly annual gross pay before employee contributions. `salaire_declare` (`1AJ`) deducts `cotisations_salariales` + `csg_deductible`; `salaire_net` deducts `csg` + `crds` on `assiette_csg_crds_salaire = brut − min(brut, 4 × PASS) × 1.75 %` (CSS art. L136-2 I).
- **1-January Annual Parameter Convention (`YEAR` variables):** `cotisations_salariales`, `cotisations_patronales`, and `reduction_generale` read `parameters(period)` on 1 January without infra-annual proration. Mid-year updates (`AGS` `0.25 %` `2024-07-01`, `SMIC` `11.88 €` `2024-11-01`, `chômage` `4.00 %` `2025-05-01`) take effect on 1 January of the following year.
- **Rates & Ceilings:** `PASS` = `46,368 €` (2024) / `47,100 €` (2025). Employee per-risk rates: vieillesse `6.90 %` (`1 PASS`) + `0.40 %`, AGIRC-ARRCO `3.15 %` / `8.64 %`, CEG `0.86 %` / `1.08 %`, CET `0.14 %` (`0–8 PASS` when `> 1 PASS`, all employees), APEC `0.024 %` (`0–4 PASS`, `cadre=True`). Employer contributions include 2024/2025 LFSS SMIC bandeaux and Fillon *réduction générale* (`T = 0.3194 / 0.3234` in 2024, `0.3193 / 0.3233` in 2025, full-time `1,820 h/yr` SMIC).

### 4.2 Family & Working-Age Solidarity Benefits (`Bug B3`, `Spec 0002`, `Spec 0009`)

- **AF *Complément dégressif* (`Bug B3`, CSS art. D521-1, al. 3):** Smooths both income thresholds via `max(0, montant_module − depassement / 12)`. Family resources sum current-year `salaire_imposable + pensions_imposables`.
- **RSA (`Spec 0002`, CASF art. L262-1 et s.):** `(age_parent >= 25) | (nb_enfants_charge >= 1)` with dependent children `< 25`; `rsa_montant_forfaitaire` `607.75 / 635.71 / 646.52 €` + R262-1 weights (`+40 %` from 3rd child) and *RSA majoré*; `rsa_base_ressources` counts `/ 12` of net wages, net pensions, alimony received, capital, and net rents, plus unmodulated Tranche-1 base AF (excl. age majoration) and `min(asf, 0.225 × BMAF × nb_enfants)`.
- **Prime d'activité (`Spec 0009`, CSS art. L841-1 et s.):** `595.25 / 622.63 / 633.21 €`, `61 %` activity slope, individual bonification (`59 → 120 × SMIC_horaire` evaluated on Jan 1, max `0.29101 × base`), netting `ppa_non_bonifiee`, `15 €/month` floor.

### 4.3 Retirement Pensions, RFR & Banded CSG/CRDS/CASA (`Specs 0005, 0006`)

- **Statutory RFR Thresholds (CSS art. L136-8 III):** 2024 (`12,230 / 15,988 / 24,813 €` + `3,265 / 4,269 / 6,623 €` per half-part) and 2025 (`12,817 / 16,755 / 26,004 €` + `3,422 / 4,474 / 6,941 €`), rates `0 / 3.8 / 6.6 / 8.3 %` CSG, `0.5 %` CRDS, `0.3 %` CASA.
- **Known Proxy Limitation:** Evaluated on current-year `revenu_fiscal_de_reference` computed with pre-pension-CSG gross `pension_retraite` (after the floored/capped CGI art. 158-5-a 10 % allowance) to avoid circularity in year N. This slightly overstates RFR (and CEHR by `~3 %` of deductible pension CSG) for very high pensions above `250 k€`.

### 4.4 Multi-Year Parameterisation (`Spec 0007`: 2024, 2025 & LFSS 2026 Capital Split)

- **IR 2024 (LFI 2025, +1.8 %)** & **IR 2025 (LFI 2026, Loi n° 2026-103 art. 4, +0.9 %):** 2025 brackets `11,600 / 29,579 / 84,577 / 181,917 €`; QF cap `1,807 €` (`4,262 €` case T); Décote `897 € / 1,483 €`; 10 % salary cap/floor `14,555 / 509 €`; 10 % pension cap/floor `4,439 / 454 €`. (2025 `CDHR` art. 224 CGI is documented in `not_modelled`.)
- **Social & Benefit 2025 Dates:** `PASS = 47,100 €` (`2025-01-01`); `SMIC horaire = 11.88 €` (`2024-11-01`); `BMAF = 474.37 €` (`2025-04-01`, Instruction DSS/2B/2025/38); AF 2025 plafonds `65,473 / 91,627 €` + `6,546 €`/child (Instruction DSS/2B/2024/181).
- **LFSS 2026 Social Levies Split (Loi n° 2025-1403 art. 12):** `taux_global` rises from `17.2 %` to `18.6 %` on `2026-01-01` for `revenus_capital`, while `taux_immobilier` stays at `17.2 %` for bare rents and real-estate gains.

### 4.5 Cross-Repository Reuse Matrix (`budget_fr_sim_test` & `LVTShift`)

| Source Repo & Ref | Actual Source File(s) Reused | Integrated Target in `policyengine-fr` | Notes & Assumptions |
|---|---|---|---|
| `LVTShift` (`de85827`) | `lvtshift-fr/yields.py`, `lvtshift-fr/estimate.py`, `lvtshift-fr/export_web.py`, `lvtshift-fr/METHODOLOGIE.md` | `variables/gov/dgfip/patrimoine_et_hauts_revenus.py` (`ifi`, `impot_plus_values_immobilieres`), `variables/gov/dgfip/fiscalite_locale.py` (`taxe_fonciere`, `taxe_habitation_residence_secondaire`, `taxe_valeur_sol`) | Exact statutory CGI art. 964–977 IFI (`assiette > 1,300,000 €`, 30 % RP abatement, `1.3–1.4 M€` décote) and 3 % State management fee on local TFPB/THRS bills (CGI art. 1641). |
| `LVTShift` (`de85827`) | `lvtshift-fr/site/public/data/yields.json` | `policyengine_fr/data/lvt_yields.json` + `lvt_yields.source.json` (LF-normalized SHA-256) + `policyengine_fr/reforms/lvt_shift.py` (`S1`–`S3_IFI`) | Pinned equal-yield LVT rates (`1.10 %` in `S1` to `1.34 %` in `S3_IFI`). Under `S3`/`S3_IFI`, rental income is removed inside `revenu_net_imposable` and `prelevements_sociaux_patrimoine` without suppressing `rsa_base_ressources` or RFR. |
| `budget_fr_sim_test` (`review/day0`, `day1`) | `app/src/engine/ir-tranches.js`, `app/src/engine/levers.js`, `app/src/engine/params.js` | `cehr`, `pfu_ir`, `prelevements_sociaux_patrimoine`, `revenus_fonciers_nets`, `reforms/budget_levers.py` | CEHR (`3 % / 4 %`), PFU (`12.8 %` IR + `17.2 % / 18.6 %` PS), micro-foncier/réel + `6.8 %` deductible CSG, plus `ir_rate_change`, `ir_freeze_brackets`, and `csg_delta` reforms. |
| `budget_fr_sim_test` (`day1`) | `app/docs/policyengine-fr-linkage.md`, `app/src/engine/params.js` (**Decision D-P6**) | `reforms/budget_levers.py` (`make_d_p6_targeted_pension_underindexation_reform`) + `tests/test_reforms.py` | Propagates `pension_retraite_effective` through CSG, CRDS, CASA, IR, RFR, and `revenu_disponible`; confirms mechanical clawback sits in `[0.35, 0.45]` at `48 k€`. |

### 4.6 Independent Oracle Validation Scope (`25/25` Live 2024 Rows Passing)

All 25 rows in `tests/fixtures/oracle_values.yaml` have `official != null` (`0` skipped) and pass in `tests/test_oracle.py`:

| Module | Oracle Source | Rows | Caveats / Uncovered Modules |
|---|---|---|---|
| `impot_revenu` (2024) | Official DGFiP IR Simulator | 10 (`Δ ≤ 0.52 €`) | Feeds `salaire_declare` directly (bypasses payslip stage). |
| `allocations_familiales` + `asf` (2024) | `openfisca-france` `175.0.45` | 5 (`Δ ≤ 0.02 €`) | Covers tranches 1–3 + differential ASF; *complément dégressif* cross-checked manually (`127.36` vs `127.37 €`). |
| `rsa` (2024) | `openfisca-france` `175.0.45` | 5 (`Δ ≤ 0.01 €`) | Covers 0 € single/couple/single-parent and `6 k€` gross. |
| `prime_activite` (2024) | `openfisca-france` `175.0.45` | 1 (`Δ = 0.00 €`) | Live oracle covers `6 k€`; bonification cases (`15 k€`, `SMIC`) cross-checked in YAML comments. |
| `salaire_net` & `salaire_declare` (2024) | `openfisca-france` `175.0.45` | 3 (`Δ ≤ 1.44 €`) | Covers `30 k€` net and `60 k€` non-cadre / cadre declared. |
| `reduction_generale` (2024) | `openfisca-france` `175.0.45` | 1 (`Δ = 0.00 €`) | Full-time SMIC baseline; gross `cotisations_patronales`, **2025**, pensions/CSG, patrimonial/IFI, and **reforms** have YAML/property tests only (no automated oracle rows yet). |

---

## 5. Interactive Studio UI Architecture & Design Assumptions (`feat/ui-studio`, PR #33)

1. **Zero-Extra-Dependency Python Microsimulation Server (`policyengine_fr/studio.py`):**
   - Uses stdlib `http.server.ThreadingHTTPServer` (`MAX_REQUEST_BYTES = 65_536`, localhost-restricted CORS, sanitized `400`/`413` responses) so `policyengine-fr` needs no Flask/FastAPI dependency.
   - Caches compiled composite reform systems (`StudioCombinedReform(BASE_SYSTEM)`) via `@lru_cache(maxsize=64)` and evaluates the **61-point earnings curve** (`salaire_brut` → `revenu_disponible`, stacked benefits/incomes, and `EMTR %`) in a single vectorised `Simulation` pass (measured `~60 ms` warm / `~85 ms` cold on a couple with 2 children, plus `menage`-indexed `salaire_net` extraction).
   - **Couples Limitation:** In the UI household form, `revenus_capital` and `pensions_alimentaires_percues` are entered at the household level and assigned to `adulte_1` in the situation builder.
2. **Cross-Repository UX & Design Reuse (`budget_fr_sim_test` & `LVTShift`):**
   - Reuses the French Civic Editorial palette & typography (`Crimson Pro` + `Inter`, deep marine `#1a2744`, emerald `#1e6b4b`, crimson `#b5281e`, warm stone `#f6f4ef`, `tabular-nums` anti-jitter numerals), `useDeferredValue` + `AbortController` responsive sliders, URL hash state sharing (`#s=...`), `;`-delimited French CSV export with formula-injection protection, and inline `InfoPopover` statutory citations fed from `/api/metadata`.
   - Includes a global **`€ / mois` ↔ `€ / an`** toggle, `2024` ↔ `2025` toggle, 7 one-click presets, collapsible Patrimoine drawer, stacked earnings + EMTR curves (including non-wage income band and APL omission note), and combinable `LVTShift` (`S1`–`S3_IFI`) + `budget_fr_sim_test` (`IR`, `CSG`, `ir_freeze_2024`, `D-P6`) reforms.
