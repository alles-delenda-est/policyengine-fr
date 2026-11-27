from policyengine_fr.model_api import *


class assiette_csg_crds_salaire(Variable):
    value_type = float
    entity = Individu
    label = "Assiette de la CSG et de la CRDS sur les revenus d'activité salariée"
    unit = EUR
    documentation = (
        "Base de calcul de la CSG et de la CRDS pour un salarié (CSS art. "
        "L136-2, I) : salaire brut diminué de l'abattement d'assiette pour "
        "frais professionnels de 1,75 %, dans la limite de 4 plafonds annuels "
        "de la sécurité sociale (PASS) ; la fraction excédant 4 PASS est "
        "assujettie à 100 %."
    )
    definition_period = YEAR
    reference = "https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000037948012"

    def formula(individu, period, parameters):
        salaire_brut = individu("salaire_brut", period)
        abattement = parameters(period).gov.urssaf.csg.activite.abattement
        pass_annuel = parameters(period).gov.urssaf.plafond_securite_sociale
        return salaire_brut - min_(salaire_brut, 4 * pass_annuel) * abattement
