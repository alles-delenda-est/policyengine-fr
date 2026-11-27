from policyengine_fr.model_api import *


class csg_retraite(Variable):
    value_type = float
    entity = Individu
    label = "CSG sur les pensions de retraite"
    unit = EUR
    documentation = (
        "CSG totale sur la pension de retraite de la personne, au taux du foyer "
        "(spec 0006): pension_retraite × taux_csg_pension (0 / 3,8 / 6,6 / 8,3 %)."
    )
    definition_period = YEAR
    reference = "https://www.service-public.fr/particuliers/vosdroits/F2971"

    def formula(individu, period, parameters):
        pension = individu("pension_retraite", period)
        taux = individu.foyer_fiscal("taux_csg_pension", period)
        return pension * taux
