from policyengine_fr.model_api import *


class csg_retraite_deductible(Variable):
    value_type = float
    entity = Individu
    label = "CSG déductible sur les pensions de retraite"
    unit = EUR
    documentation = (
        "Part déductible de la CSG sur la pension de retraite (spec 0006): "
        "pension_retraite × taux_csg_pension_deductible. Retranchée de la pension "
        "pour former la pension déclarée imposable, comme la CSG déductible sur "
        "salaire (spec 0001)."
    )
    definition_period = YEAR
    reference = "https://www.service-public.fr/particuliers/vosdroits/F2971"

    def formula(individu, period, parameters):
        pension = individu("pension_retraite", period)
        taux_d = individu.foyer_fiscal("taux_csg_pension_deductible", period)
        return pension * taux_d
