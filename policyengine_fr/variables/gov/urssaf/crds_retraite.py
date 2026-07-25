from policyengine_fr.model_api import *


class crds_retraite(Variable):
    value_type = float
    entity = Individu
    label = "CRDS sur les pensions de retraite"
    unit = EUR
    documentation = (
        "CRDS (0,5 %) sur la pension de retraite (spec 0006). Seules les pensions "
        "exonérées de CSG (taux zéro) sont exonérées de CRDS ; la CRDS est due dès "
        "le taux réduit (3,8 %), ainsi qu'aux taux médian et normal. "
        "Simplification MVP: la CASA (0,3 %, due seulement aux taux médian/normal) "
        "n'est pas modélisée."
    )
    definition_period = YEAR
    reference = "https://www.service-public.fr/particuliers/vosdroits/F2971"

    def formula(individu, period, parameters):
        pension = individu("pension_retraite", period)
        taux_csg = individu.foyer_fiscal("taux_csg_pension", period)
        taux_crds = parameters(period).gov.urssaf.crds.activite.taux
        # CRDS due sauf exonération totale de CSG (taux zéro).
        return where(taux_csg > 0, pension * taux_crds, 0)
