from policyengine_fr.model_api import *


class casa_retraite(Variable):
    value_type = float
    entity = Individu
    label = "CASA sur les pensions de retraite"
    unit = EUR
    documentation = (
        "Contribution additionnelle de solidarité pour l'autonomie (CASA, "
        "0,3 %, CASF art. L14-10-4) prélevée sur les pensions de retraite. "
        "Due uniquement lorsque le foyer fiscal relève du taux médian (6,6 %) "
        "ou du taux normal (8,3 %) de CSG ; exonération totale en cas de taux "
        "zéro ou de taux réduit (3,8 %). Non déductible de l'impôt sur le revenu."
    )
    definition_period = YEAR
    reference = "https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000038011510"

    def formula(individu, period, parameters):
        pension = individu("pension_retraite", period)
        taux_csg = individu.foyer_fiscal("taux_csg_pension", period)
        taux_median = parameters(period).gov.urssaf.csg.remplacement.taux.median
        taux_casa = parameters(period).gov.urssaf.casa.retraite.taux
        return where(taux_csg >= taux_median, pension * taux_casa, 0)
