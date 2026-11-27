"""Equal-yield Land Value Tax (LVT / TVTN) replacement reforms from LVTShift-FR.

Reuses the pinned `lvt_yields.json` snapshot (from `alles-delenda-est/LVTShift`,
`lvtshift-fr/site/public/data/yields.json`, provenance in
`policyengine_fr/data/lvt_yields.source.json`) to parameterise the five
equal-yield replacement scenarios (spec 0005 of LVTShift and `LVT_MODULE` of
`budget_fr_sim_test`):

- ``S1``     : replaces TFPB, TFPNB, THRS, and DMTO -> indicative national rate 1.10 %
- ``S2``     : ``S1`` + IR & PS on real-estate capital gains -> 1.16 %
- ``S2_IFI`` : ``S2`` + IFI -> 1.20 %
- ``S3``     : ``S2`` + IR & PS on net rental income -> 1.30 %
- ``S3_IFI`` : ``S3`` + IFI -> 1.34 %
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from policyengine_core.periods import period as make_period
from policyengine_core.reforms import Reform

from policyengine_fr.model_api import *

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
YIELDS_PATH = DATA_DIR / "lvt_yields.json"
SOURCE_PATH = DATA_DIR / "lvt_yields.source.json"


def load_lvt_yields() -> tuple[dict, dict]:
    """Load and verify SHA-256 provenance of the pinned LVTShift yields.json."""
    raw = YIELDS_PATH.read_bytes()
    source = json.loads(SOURCE_PATH.read_text(encoding="utf-8"))
    actual_sha = hashlib.sha256(raw).hexdigest()
    if actual_sha != source["sha256"]:
        raise ValueError(
            f"lvt_yields.json SHA-256 mismatch: expected {source['sha256']}, got {actual_sha}"
        )
    return json.loads(raw.decode("utf-8")), source


def lvt_variant_rate(scenario_id: str) -> float:
    """Return the equal-yield LVT rate (as a fraction in [0, 1]) for a variant id."""
    yields_data, _ = load_lvt_yields()
    mapping = {
        "S1": ("S1", False),
        "S2": ("S2", False),
        "S2_IFI": ("S2", True),
        "S3": ("S3", False),
        "S3_IFI": ("S3", True),
    }
    if scenario_id not in mapping:
        raise ValueError(
            f"Unknown LVT scenario {scenario_id!r}; expected one of {sorted(mapping)}"
        )
    sc, include_ifi = mapping[scenario_id]
    for v in yields_data["variants"]:
        if v["scenario"] == sc and v["include_ifi"] is include_ifi:
            return float(v["rate_pct"]) / 100.0
    raise KeyError(f"Variant {scenario_id} missing from lvt_yields.json")


def make_lvt_shift_reform(
    scenario_id: str = "S1",
    *,
    custom_rate: float | None = None,
) -> type[Reform]:
    """Build a PolicyEngine `Reform` implementing an LVTShift equal-yield scenario."""
    rate = lvt_variant_rate(scenario_id) if custom_rate is None else float(custom_rate)
    replace_gains = scenario_id in {"S2", "S2_IFI", "S3", "S3_IFI"}
    replace_ifi = scenario_id in {"S2_IFI", "S3_IFI"}
    replace_rents = scenario_id in {"S3", "S3_IFI"}

    def _modify_params(parameters):
        span = make_period("year:2020:20")
        parameters.gov.dgfip.fiscalite_locale.taux_lvt_national.update(
            period=span, value=rate
        )
        if replace_gains:
            parameters.gov.dgfip.plus_values_immobilieres.taux_ir.update(
                period=span, value=0.0
            )
        return parameters

    class LVTShiftReform(Reform):
        name = f"LVTShift equal-yield reform ({scenario_id})"

        def apply(self):
            self.modify_parameters(_modify_params)
            self.neutralize_variable("taxe_fonciere")
            self.neutralize_variable("taxe_habitation_residence_secondaire")
            if replace_ifi:
                self.neutralize_variable("ifi")
            if replace_rents:
                self.neutralize_variable("revenus_fonciers_nets")
            if replace_gains or replace_rents:

                class prelevements_sociaux_patrimoine_lvt(Variable):
                    value_type = float
                    entity = FoyerFiscal
                    label = "Prélèvements sociaux sur le patrimoine (réforme LVT)"
                    unit = EUR
                    definition_period = YEAR

                    def formula(foyer_fiscal, period, parameters):
                        capital = foyer_fiscal.sum(
                            foyer_fiscal.members("revenus_capital", period)
                        )
                        foncier = (
                            0
                            if replace_rents
                            else foyer_fiscal("revenus_fonciers_nets", period)
                        )
                        pv = (
                            0
                            if replace_gains
                            else foyer_fiscal("plus_values_immobilieres", period)
                        )
                        p = parameters(period).gov.urssaf.patrimoine
                        return (
                            capital * p.taux_global + (foncier + pv) * p.taux_immobilier
                        )

                prelevements_sociaux_patrimoine_lvt.__name__ = (
                    "prelevements_sociaux_patrimoine"
                )
                self.replace_variable(prelevements_sociaux_patrimoine_lvt)

    return LVTShiftReform
