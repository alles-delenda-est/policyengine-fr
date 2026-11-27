from policyengine_fr.model_api import *


class taux_csg_pension(Variable):
    value_type = float
    entity = FoyerFiscal
    label = "Taux de CSG applicable aux pensions de retraite"
    unit = "/1"
    documentation = (
        "Taux total de CSG sur les pensions de retraite (CSS art. L136-8 III, "
        "spec 0006), sélectionné selon le revenu fiscal de référence du foyer et "
        "son nombre de parts : exonération (0 %), taux réduit (3,8 %), médian "
        "(6,6 %) ou normal (8,3 %). Les seuils de RFR (barèmes 2024 et 2025) "
        "sont majorés par demi-part supplémentaire.\n\n"
        "Simplifications (voir `modelled_policies.yaml`) : la loi apprécie les "
        "seuils sur le RFR de l'année N-2 (p. ex. RFR 2022 pour les pensions "
        "versées en 2024) et subordonne le passage du taux réduit aux taux "
        "médian/normal au franchissement du seuil deux années consécutives (CSS "
        "art. L136-8 III bis) ; ce modèle statique mono-période utilise le "
        "`revenu_fiscal_de_reference` de l'année courante N sans condition de "
        "lissage bisannuel."
    )
    definition_period = YEAR
    reference = "https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000048768785"

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
