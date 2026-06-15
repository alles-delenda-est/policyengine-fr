from policyengine_fr.model_api import *


class impot_revenu(Variable):
    value_type = float
    entity = FoyerFiscal
    label = "Impôt sur le revenu net"
    unit = EUR
    documentation = (
        "Impôt sur le revenu dû par le foyer fiscal après application du "
        "barème progressif, du plafonnement du quotient familial et de la "
        "décote (CGI art. 197). On part de l'impôt après plafonnement du "
        "quotient familial, on impute la décote, et on plancher le résultat "
        "à zéro: impôt = max(0, impôt après plafonnement − décote). "
        "Hors champ pour le MVP: réductions et crédits d'impôt, "
        "contribution exceptionnelle sur les hauts revenus, prélèvements "
        "sur les revenus du capital."
    )
    definition_period = YEAR
    reference = "https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000048833693"

    def formula(foyer_fiscal, period, parameters):
        impot = foyer_fiscal("plafonnement_quotient_familial", period)
        decote = foyer_fiscal("decote", period)
        return max_(0, impot - decote)
