"""Household microsimulation counterparts of `budget_fr_sim_test` fiscal levers.

Bridges `PolicyEngineFR` (household microsimulation) and `budget_fr_sim_test`
(`review/day0` and `day1` macro-budget simulator):

1. ``make_ir_proportional_reform(multiplier)`` — proportional scaling of all IR
   marginal bracket rates (`τ_i × multiplier`), matching `src/engine/ir-tranches.js`
   in `budget_fr_sim_test`.
2. ``make_csg_delta_reform(delta_rate)`` — uniform shift in activity CSG rate
   (preserving the statutory 6.8 / 9.2 deductible share), matching the `csg`
   lever and `facteurCsgDeductible` of `budget_fr_sim_test`.
3. ``make_d_p6_targeted_pension_underindexation_reform(underindexation_rate, threshold_annual=24_000.0)``
   — targeted under-indexation on gross retirement pensions exceeding
   €2,000/month (€24,000/year), matching Decision D-P6 (`day1` commit `47c6491`,
   `comp.offset.pensions_hautes = 0.38` [0.35–0.45]) and allowing direct
   microsimulation of the mechanical IR + CSG/CRDS/CASA clawback.
"""

from __future__ import annotations

from policyengine_core.periods import period as make_period
from policyengine_core.reforms import Reform

from policyengine_fr.model_api import *


def make_ir_proportional_reform(multiplier: float) -> type[Reform]:
    """Scale every IR marginal bracket rate by ``multiplier`` (e.g. 1.01 for +1 %)."""
    if multiplier < 0:
        raise ValueError("multiplier must be non-negative")

    def _modify(parameters):
        span = make_period("year:2024:10")
        for bracket in parameters.gov.dgfip.ir.bareme.brackets:
            base_rate = float(bracket.rate("2024-01-01"))
            bracket.rate.update(period=span, value=min(base_rate * multiplier, 1.0))
        return parameters

    class ProportionalIRReform(Reform):
        name = f"Proportional IR bracket reform (×{multiplier:.4f})"

        def apply(self):
            self.modify_parameters(_modify)

    return ProportionalIRReform


def make_csg_delta_reform(delta_rate: float) -> type[Reform]:
    """Add ``delta_rate`` (e.g. +0.01 for +1 pp) to activity CSG."""

    def _modify(parameters):
        span = make_period("year:2024:10")
        act = parameters.gov.urssaf.csg.activite
        old_ded = float(act.deductible.taux("2024-01-01"))
        old_imp = float(act.imposable.taux("2024-01-01"))
        old_tot = old_ded + old_imp
        new_tot = max(old_tot + delta_rate, 0.0)
        share_ded = old_ded / old_tot
        act.deductible.taux.update(period=span, value=new_tot * share_ded)
        act.imposable.taux.update(period=span, value=new_tot * (1.0 - share_ded))
        return parameters

    class CSGDeltaReform(Reform):
        name = f"Activity CSG delta reform ({delta_rate:+.4f})"

        def apply(self):
            self.modify_parameters(_modify)

    return CSGDeltaReform


def make_d_p6_targeted_pension_underindexation_reform(
    underindexation_rate: float = 0.02,
    *,
    threshold_annual: float = 24_000.0,
) -> type[Reform]:
    """Under-index gross retirement pensions above €24,000/year (`day1` Decision D-P6).

    Applies ``underindexation_rate`` to a pensioner's gross pension when
    ``pension_retraite > threshold_annual`` (with a smooth floor at
    ``threshold_annual`` so no pensioner just above €2,000/month falls below one
    at €2,000/month).
    """
    if not (0.0 <= underindexation_rate < 1.0):
        raise ValueError("underindexation_rate must be in [0, 1)")

    class DP6TargetedPensionReform(Reform):
        name = (
            f"Targeted pension under-indexation D-P6 "
            f"(-{underindexation_rate * 100:.1f}% above {threshold_annual:.0f} EUR/yr)"
        )

        def apply(self):
            base_var = self.get_variable("pension_retraite")

            class pension_retraite_dp6(Variable):
                value_type = float
                entity = Individu
                label = base_var.label
                unit = EUR
                definition_period = YEAR

            pension_retraite_dp6.__name__ = "pension_retraite"

            # Replace consumers via an effective gross pension wrapper on CSG/CRDS/CASA/IR/disposable?
            # Since `pension_retraite` is an input variable set in the situation, overriding
            # its downstream adjustment via `modify_pension_situations` or replacing the
            # four consumers (`pension_retraite_declaree`, `csg_retraite`, `crds_retraite`,
            # `casa_retraite`, `pension_retraite_nette`, `revenu_fiscal_de_reference`,
            # `revenu_disponible`) is cleaner if factored through a helper variable.
            # Add `pension_retraite_effective` and route the 5 readers through it:
            class pension_retraite_effective(Variable):
                value_type = float
                entity = Individu
                label = "Pension de retraite brute effective après mesure d'indexation"
                unit = EUR
                definition_period = YEAR

                def formula(individu, period, parameters):
                    brut = individu("pension_retraite", period)
                    reduit = max_(brut * (1.0 - underindexation_rate), threshold_annual)
                    return where(brut > threshold_annual, reduit, brut)

            self.add_variable(pension_retraite_effective)

            class csg_retraite_r(Variable):
                value_type = float
                entity = Individu
                label = "CSG sur les pensions de retraite"
                unit = EUR
                definition_period = YEAR

                def formula(individu, period, parameters):
                    p = individu("pension_retraite_effective", period)
                    return p * individu.foyer_fiscal("taux_csg_pension", period)

            csg_retraite_r.__name__ = "csg_retraite"

            class csg_retraite_deductible_r(Variable):
                value_type = float
                entity = Individu
                label = "CSG déductible sur les pensions de retraite"
                unit = EUR
                definition_period = YEAR

                def formula(individu, period, parameters):
                    p = individu("pension_retraite_effective", period)
                    return p * individu.foyer_fiscal(
                        "taux_csg_pension_deductible", period
                    )

            csg_retraite_deductible_r.__name__ = "csg_retraite_deductible"

            class crds_retraite_r(Variable):
                value_type = float
                entity = Individu
                label = "CRDS sur les pensions de retraite"
                unit = EUR
                definition_period = YEAR

                def formula(individu, period, parameters):
                    p = individu("pension_retraite_effective", period)
                    taux_csg = individu.foyer_fiscal("taux_csg_pension", period)
                    taux_crds = parameters(period).gov.urssaf.crds.activite.taux
                    return where(taux_csg > 0, p * taux_crds, 0)

            crds_retraite_r.__name__ = "crds_retraite"

            class casa_retraite_r(Variable):
                value_type = float
                entity = Individu
                label = "CASA sur les pensions de retraite"
                unit = EUR
                definition_period = YEAR

                def formula(individu, period, parameters):
                    p = individu("pension_retraite_effective", period)
                    taux_csg = individu.foyer_fiscal("taux_csg_pension", period)
                    taux_med = parameters(
                        period
                    ).gov.urssaf.csg.remplacement.taux.median
                    taux_casa = parameters(period).gov.urssaf.casa.retraite.taux
                    return where(taux_csg >= taux_med, p * taux_casa, 0)

            casa_retraite_r.__name__ = "casa_retraite"

            class pension_retraite_declaree_r(Variable):
                value_type = float
                entity = Individu
                label = "Pension de retraite déclarée"
                unit = EUR
                definition_period = YEAR

                def formula(individu, period, parameters):
                    p = individu("pension_retraite_effective", period)
                    return max_(p - individu("csg_retraite_deductible", period), 0)

            pension_retraite_declaree_r.__name__ = "pension_retraite_declaree"

            class pension_retraite_nette_r(Variable):
                value_type = float
                entity = Individu
                label = "Pension de retraite nette"
                unit = EUR
                definition_period = YEAR

                def formula(individu, period, parameters):
                    p = individu("pension_retraite_effective", period)
                    return max_(
                        p
                        - individu("csg_retraite", period)
                        - individu("crds_retraite", period)
                        - individu("casa_retraite", period),
                        0,
                    )

            pension_retraite_nette_r.__name__ = "pension_retraite_nette"

            for v in (
                csg_retraite_r,
                csg_retraite_deductible_r,
                crds_retraite_r,
                casa_retraite_r,
                pension_retraite_declaree_r,
                pension_retraite_nette_r,
            ):
                self.replace_variable(v)

    return DP6TargetedPensionReform
