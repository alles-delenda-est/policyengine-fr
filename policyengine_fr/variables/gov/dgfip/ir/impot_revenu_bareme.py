from policyengine_fr.model_api import *


class impot_revenu_bareme(Variable):
    value_type = float
    entity = FoyerFiscal
    label = "Impôt sur le revenu issu du barème"
    unit = EUR
    documentation = (
        "Impôt sur le revenu obtenu en appliquant le barème progressif au "
        "revenu net imposable du foyer fiscal. SIMPLIFICATION: ne tient pas "
        "encore compte du quotient familial (nombre de parts), de la décote, "
        "ni du plafonnement. Étape suivante: diviser par le nombre de parts, "
        "appliquer le barème, puis remultiplier."
    )
    definition_period = YEAR
    reference = "https://www.service-public.fr/particuliers/vosdroits/F1419"

    def formula(foyer_fiscal, period, parameters):
        revenu = foyer_fiscal("revenu_net_imposable", period)
        bareme = parameters(period).gov.dgfip.ir.bareme
        return bareme.calc(revenu)
