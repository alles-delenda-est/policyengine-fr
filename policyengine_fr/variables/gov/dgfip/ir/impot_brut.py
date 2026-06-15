from policyengine_fr.model_api import *


class impot_brut(Variable):
    value_type = float
    entity = FoyerFiscal
    label = "Impôt brut (barème appliqué au quotient familial)"
    unit = EUR
    documentation = (
        "Impôt issu de l'application du barème progressif au quotient familial: "
        "le revenu net imposable est divisé par le nombre de parts, le barème est "
        "appliqué à ce quotient, puis le résultat est remultiplié par le nombre "
        "de parts. Calculé avant plafonnement du quotient familial et avant décote."
    )
    definition_period = YEAR
    reference = "https://www.service-public.gouv.fr/particuliers/vosdroits/F1419"

    def formula(foyer_fiscal, period, parameters):
        rni = foyer_fiscal("revenu_net_imposable", period)
        parts = foyer_fiscal("nombre_parts", period)
        bareme = parameters(period).gov.dgfip.ir.bareme
        quotient = rni / max_(parts, 1)
        return bareme.calc(quotient) * parts
