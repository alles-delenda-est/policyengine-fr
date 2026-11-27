from policyengine_fr.model_api import *


class taux_csg_pension_deductible(Variable):
    value_type = float
    entity = FoyerFiscal
    label = "Part déductible de la CSG sur les pensions de retraite"
    unit = "/1"
    documentation = (
        "Part déductible de la CSG sur les pensions de retraite (spec 0006), "
        "selon la tranche de taux : 0 (exonération), 3,8 % (taux réduit, "
        "intégralement déductible), 4,2 % (taux médian) ou 5,9 % (taux normal). "
        "La part non déductible (2,4 % aux taux médian et normal) reste imposable."
    )
    definition_period = YEAR
    reference = "https://www.service-public.fr/particuliers/vosdroits/F2971"

    def formula(foyer_fiscal, period, parameters):
        taux = foyer_fiscal("taux_csg_pension", period)
        t = parameters(period).gov.urssaf.csg.remplacement.taux
        td = parameters(period).gov.urssaf.csg.remplacement.taux_deductible
        return where(
            taux <= 0,
            0,
            where(
                taux <= t.reduit,
                td.reduit,
                where(taux <= t.median, td.median, td.normal),
            ),
        )
