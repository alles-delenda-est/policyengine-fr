from policyengine_fr.model_api import *


class revenu_net_imposable(Variable):
    value_type = float
    entity = FoyerFiscal
    label = "Revenu net imposable du foyer fiscal"
    unit = EUR
    documentation = (
        "Revenu net global imposable au barème progressif de l'impôt sur le "
        "revenu : somme des salaires imposables, des pensions imposables "
        "(retraite + alimentaires perçues après abattement mutualisé de 10 %) "
        "et des revenus fonciers nets diminués de leur CSG déductible (6,8 %, "
        "CGI art. 154 quinquies II), sous déduction des pensions alimentaires "
        "versées (borné à zéro)."
    )
    definition_period = YEAR
    reference = "https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000006302219"

    def formula(foyer_fiscal, period, parameters):
        salaires = foyer_fiscal.sum(foyer_fiscal.members("salaire_imposable", period))
        pensions = foyer_fiscal("pensions_imposables", period)
        foncier_net = foyer_fiscal("revenus_fonciers_nets", period)
        taux_csg_ded_pat = parameters(
            period
        ).gov.urssaf.patrimoine.csg_deductible_bareme
        csg_ded_foncier = foncier_net * taux_csg_ded_pat
        pensions_versees = foyer_fiscal("pensions_alimentaires_versees", period)
        return max_(
            salaires + pensions + foncier_net - csg_ded_foncier - pensions_versees, 0
        )
