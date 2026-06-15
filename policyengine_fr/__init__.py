from policyengine_fr.entities import entities
from policyengine_core.simulations import (
    Microsimulation as CoreMicrosimulation,
)
from policyengine_core.simulations import Simulation as CoreSimulation
from policyengine_core.taxbenefitsystems import TaxBenefitSystem

from .constants import COUNTRY_DIR


class CountryTaxBenefitSystem(TaxBenefitSystem):
    entities = entities
    variables_dir = COUNTRY_DIR / "variables"
    parameters_dir = COUNTRY_DIR / "parameters"
    auto_carry_over_input_variables = True
    basic_inputs = [
        "revenu_net_imposable",
    ]

    def __init__(self):
        super().__init__(entities)


system = CountryTaxBenefitSystem()


class Simulation(CoreSimulation):
    default_tax_benefit_system = CountryTaxBenefitSystem
    default_tax_benefit_system_instance = system
    default_role = "declarant"
    default_calculation_period = 2024
    default_input_period = 2024


class Microsimulation(CoreMicrosimulation):
    default_tax_benefit_system = CountryTaxBenefitSystem
    default_tax_benefit_system_instance = system
    default_calculation_period = 2024
