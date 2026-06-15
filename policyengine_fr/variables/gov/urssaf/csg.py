from policyengine_fr.model_api import *


class csg(Variable):
    value_type = float
    entity = Individu
    label = "CSG sur les revenus d'activité"
    unit = EUR
    documentation = (
        "Contribution sociale généralisée totale sur les revenus d'activité "
        "salariée: somme des parts déductible (6,8 %) et imposable (2,4 %), soit "
        "un taux global de 9,2 % sur 98,25 % du salaire brut."
    )
    definition_period = YEAR
    reference = "https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000041604370"

    def formula(individu, period, parameters):
        return individu("csg_deductible", period) + individu("csg_imposable", period)
