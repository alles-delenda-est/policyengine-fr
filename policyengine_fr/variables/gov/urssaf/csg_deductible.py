from policyengine_fr.model_api import *


class csg_deductible(Variable):
    value_type = float
    entity = Individu
    label = "CSG déductible sur les revenus d'activité"
    unit = EUR
    documentation = (
        "Part de la CSG sur les revenus d'activité déductible de l'impôt sur le "
        "revenu (taux de 6,8 %), assise sur 98,25 % du salaire brut."
    )
    definition_period = YEAR
    reference = "https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000041604370"

    def formula(individu, period, parameters):
        assiette = individu("assiette_csg_crds_salaire", period)
        taux = parameters(period).gov.urssaf.csg.activite.deductible.taux
        return assiette * taux
