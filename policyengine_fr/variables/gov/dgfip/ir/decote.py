from policyengine_fr.model_api import *


class decote(Variable):
    value_type = float
    entity = FoyerFiscal
    label = "Décote de l'impôt sur le revenu"
    unit = EUR
    documentation = (
        "Réduction d'impôt en faveur des foyers faiblement imposés "
        "(CGI art. 197-I-4). Lorsque l'impôt résultant du barème (après "
        "plafonnement du quotient familial) est inférieur à un seuil, une "
        "décote est appliquée: décote = seuil − taux × impôt, sans pouvoir "
        "être négative. Le seuil dépend de la situation du foyer (personne "
        "seule ou couple soumis à imposition commune). La décote est ensuite "
        "imputée sur l'impôt pour obtenir l'impôt sur le revenu net."
    )
    definition_period = YEAR
    reference = "https://www.service-public.fr/particuliers/vosdroits/F31193"

    def formula(foyer_fiscal, period, parameters):
        impot = foyer_fiscal("plafonnement_quotient_familial", period)
        nb_declarants = foyer_fiscal.nb_persons(FoyerFiscal.DECLARANT)
        decote = parameters(period).gov.dgfip.ir.decote

        seuil = where(
            nb_declarants >= 2,
            decote.seuil_couple,
            decote.seuil_celibataire,
        )
        return max_(0, seuil - decote.taux * impot)
