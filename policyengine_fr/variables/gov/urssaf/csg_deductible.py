from policyengine_fr.model_api import *


class csg_deductible(Variable):
    value_type = float
    entity = Individu
    label = "CSG déductible sur les revenus d'activité"
    unit = EUR
    documentation = (
        "Part de la CSG sur les revenus d'activité déductible de l'impôt sur le "
        "revenu (taux de 6,8 %), assise sur 98,25 % du salaire brut. Cette "
        "déductibilité (CGI art. 154 quinquies) est appliquée exactement une "
        "fois, en amont: elle est retranchée du salaire brut pour former le "
        "salaire déclaré (`salaire_declare`), base de l'impôt sur le revenu. "
        "Elle ne doit donc PAS être retranchée de nouveau dans "
        "`revenu_net_imposable`."
    )
    definition_period = YEAR
    reference = "https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000041604370"

    def formula(individu, period, parameters):
        assiette = individu("assiette_csg_crds_salaire", period)
        taux = parameters(period).gov.urssaf.csg.activite.deductible.taux
        return assiette * taux
