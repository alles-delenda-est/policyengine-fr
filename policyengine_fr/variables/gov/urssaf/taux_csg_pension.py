from policyengine_fr.model_api import *


class taux_csg_pension(Variable):
    value_type = float
    entity = FoyerFiscal
    label = "Taux de CSG applicable aux pensions de retraite"
    unit = "/1"
    documentation = (
        "Taux total de CSG sur les pensions de retraite (spec 0006), sélectionné "
        "selon le revenu fiscal de référence du foyer et son nombre de parts : "
        "exonération (0 %), taux réduit (3,8 %), médian (6,6 %) ou normal (8,3 %). "
        "Les seuils de RFR (barème 2024) sont majorés par demi-part supplémentaire."
    )
    definition_period = YEAR
    reference = "https://www.service-public.fr/particuliers/vosdroits/F2971"

    def formula(foyer_fiscal, period, parameters):
        rfr = foyer_fiscal("revenu_fiscal_de_reference", period)
        parts = foyer_fiscal("nombre_parts", period)
        s = parameters(period).gov.urssaf.csg.remplacement.seuils
        t = parameters(period).gov.urssaf.csg.remplacement.taux

        demi_parts_sup = max_(2 * (parts - 1), 0)
        seuil_exo = (
            s.exoneration.base + s.exoneration.majoration_demi_part * demi_parts_sup
        )
        seuil_reduit = s.reduit.base + s.reduit.majoration_demi_part * demi_parts_sup
        seuil_median = s.median.base + s.median.majoration_demi_part * demi_parts_sup

        return where(
            rfr <= seuil_exo,
            0,
            where(
                rfr <= seuil_reduit,
                t.reduit,
                where(rfr <= seuil_median, t.median, t.normal),
            ),
        )
