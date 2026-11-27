from policyengine_fr.model_api import *


class reduction_generale(Variable):
    value_type = float
    entity = Individu
    label = "Réduction générale dégressive des cotisations patronales (ex-Fillon)"
    unit = EUR
    documentation = (
        "Réduction générale des cotisations patronales sur les bas salaires "
        "(CSS art. L241-13 et D241-7, spec 0008). Pour un salarié à temps "
        "plein dont la rémunération annuelle brute est inférieure à 1,6 SMIC :\n\n"
        "    C = min(T, max((T / 0,6) × (1,6 × SMIC_annuel / brut − 1), 0))\n"
        "    reduction_generale = min(C × brut, cotisations_patronales)\n\n"
        "avec T = 0,3194 (< 50 salariés) ou 0,3234 (>= 50 salariés) en 2024 "
        "(0,3193 / 0,3233 en 2025), arrondi légalement à 4 décimales. Variable "
        "annuelle (`YEAR`) : le SMIC annuel (1 820 h) et le coefficient T sont "
        "lus au 1er janvier de l'année simulée, sans proratisation infra-annuelle "
        "(la revalorisation anticipée du SMIC au 1er nov. 2024 prend effet sur "
        "l'exercice 2025)."
    )
    definition_period = YEAR
    reference = "https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000048770016"

    def formula(individu, period, parameters):
        brut = individu("salaire_brut", period)
        effectif = individu("effectif_entreprise", period)
        cotis_pat = individu("cotisations_patronales", period)

        rg = parameters(period).gov.urssaf.reduction_generale
        smic = parameters(period).gov.smic
        smic_annuel = smic.horaire_brut * smic.heures_mensuelles * 12

        t_max = where(effectif < rg.seuil_effectif, rg.t_moins_50, rg.t_50_et_plus)
        brut_safe = max_(brut, 1.0)
        coef_brut = (t_max / 0.6) * (rg.seuil_sortie_smic * smic_annuel / brut_safe - 1)
        coef = min_(t_max, max_(coef_brut, 0))
        # Arrondi réglementaire du coefficient à 4 décimales (CSS art. D241-7).
        coef = (coef * 10_000).round() / 10_000
        montant = where(
            (brut > 0) & (brut < rg.seuil_sortie_smic * smic_annuel), coef * brut, 0
        )
        return min_(montant, cotis_pat)
