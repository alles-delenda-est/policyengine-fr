from policyengine_fr.model_api import *


class crds_retraite(Variable):
    value_type = float
    entity = Individu
    label = "CRDS sur les pensions de retraite"
    unit = EUR
    documentation = (
        "CRDS (0,5 %) sur la pension de retraite (spec 0006). Les pensions "
        "exonérées de CSG ou soumises au taux réduit (3,8 %) sont également "
        "exonérées de CRDS ; la CRDS n'est due qu'aux taux médian et normal. "
        "Simplification MVP: la CASA (0,3 %) n'est pas modélisée."
    )
    definition_period = YEAR
    reference = "https://www.service-public.fr/particuliers/vosdroits/F2971"

    def formula(individu, period, parameters):
        pension = individu("pension_retraite", period)
        taux_csg = individu.foyer_fiscal("taux_csg_pension", period)
        taux_crds = parameters(period).gov.urssaf.crds.activite.taux
        reduit = parameters(period).gov.urssaf.csg.remplacement.taux.reduit
        return where(taux_csg > reduit, pension * taux_crds, 0)
