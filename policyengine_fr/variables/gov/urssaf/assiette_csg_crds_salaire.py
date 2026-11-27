from policyengine_fr.model_api import *


class assiette_csg_crds_salaire(Variable):
    value_type = float
    entity = Individu
    label = "Assiette de la CSG et de la CRDS sur les revenus d'activité salariée"
    unit = EUR
    documentation = (
        "Base de calcul de la CSG et de la CRDS pour un salarié (CSS art. "
        "L136-2, I) : salaire brut diminué de l'abattement d'assiette pour "
        "frais professionnels de 1,75 %, dans la limite annuelle de 4 PASS "
        "appréciée en année pleine temps plein sans proratisation infra-annuelle "
        "ni temps partiel (CSS art. L241-3) ; la fraction excédant 4 PASS est "
        "assujettie à 100 %."
    )
    definition_period = YEAR
    reference = "https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000025013432"

    def formula(individu, period, parameters):
        salaire_brut = individu("salaire_brut", period)
        csg_params = parameters(period).gov.urssaf.csg.activite
        abattement = csg_params.abattement
        plafond_pass = csg_params.plafond_abattement_pass
        pass_annuel = parameters(period).gov.urssaf.plafond_securite_sociale
        return (
            salaire_brut - min_(salaire_brut, plafond_pass * pass_annuel) * abattement
        )
