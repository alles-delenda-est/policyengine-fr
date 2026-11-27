from policyengine_fr.model_api import *


class cotisations_patronales(Variable):
    value_type = float
    entity = Individu
    label = "Cotisations sociales patronales (avant réduction générale)"
    unit = EUR
    documentation = (
        "Cotisations sociales patronales brutes (avant réduction générale "
        "dégressive, spec 0008), secteur privé régime général :\n"
        "- maladie avec bandeau bas salaires (7 % jusqu'à 2,5 SMIC en 2024 / "
        "2,25 SMIC en 2025, 13 % au-delà),\n"
        "- allocations familiales avec bandeau (3,45 % jusqu'à 3,5 SMIC en "
        "2024 / 3,3 SMIC en 2025, 5,25 % au-delà),\n"
        "- vieillesse plafonnée (8,55 % sur 0-1 PASS) et déplafonnée (2,02 %),\n"
        "- retraite complémentaire AGIRC-ARRCO T1 (4,72 %) / T2 (12,95 %), "
        "CEG T1 (1,29 %) / T2 (1,62 %), CET (0,21 % sur 0-8 PASS si brut > 1 PASS),\n"
        "- APEC cadres (0,036 % sur 0-4 PASS),\n"
        "- assurance chômage (4,05 % sur 0-4 PASS) et AGS (0,20 % / 0,25 %),\n"
        "- FNAL selon l'effectif (< 50 salariés : 0,10 % sur 0-1 PASS ; >= 50 : "
        "0,50 % déplafonné), CSA (0,30 %), dialogue social (0,016 %) et AT/MP "
        "(entrée `taux_at_mp`, défaut 2,12 %).\n\n"
        "Couche additive de coût du travail : ne modifie ni `salaire_declare` "
        "ni `revenu_disponible`. Hors champ : versement mobilité local, taxe "
        "d'apprentissage/formation, forfait social."
    )
    definition_period = YEAR
    reference = (
        "https://www.urssaf.fr/accueil/employeur/cotisations/liste-cotisations.html"
    )

    def formula(individu, period, parameters):
        brut = individu("salaire_brut", period)
        cadre = individu("cadre", period)
        effectif = individu("effectif_entreprise", period)
        taux_at_mp = individu("taux_at_mp", period)

        cp = parameters(period).gov.urssaf.cotisations_patronales
        rg = parameters(period).gov.urssaf.reduction_generale
        pass_annuel = parameters(period).gov.urssaf.plafond_securite_sociale
        smic = parameters(period).gov.smic
        smic_annuel = smic.horaire_brut * smic.heures_mensuelles * 12

        tranche_1 = min_(brut, pass_annuel)
        tranche_2 = min_(max_(brut - pass_annuel, 0), 7 * pass_annuel)
        tranches_1_2 = min_(brut, 8 * pass_annuel)
        plafond_4_pass = min_(brut, 4 * pass_annuel)

        taux_maladie = where(
            brut <= cp.maladie_seuil_smic * smic_annuel,
            cp.maladie_taux_reduit,
            cp.maladie_taux_plein,
        )
        taux_famille = where(
            brut <= cp.famille_seuil_smic * smic_annuel,
            cp.famille_taux_reduit,
            cp.famille_taux_plein,
        )
        fnal = where(
            effectif < rg.seuil_effectif,
            cp.fnal_moins_50 * tranche_1,
            cp.fnal_50_et_plus * brut,
        )

        cotisations = (
            taux_maladie * brut
            + taux_famille * brut
            + cp.vieillesse_plafonnee * tranche_1
            + cp.vieillesse_deplafonnee * brut
            + cp.retraite_complementaire_t1 * tranche_1
            + cp.retraite_complementaire_t2 * tranche_2
            + cp.ceg_t1 * tranche_1
            + cp.ceg_t2 * tranche_2
            + where(brut > pass_annuel, cp.cet * tranches_1_2, 0)
            + where(cadre, cp.apec * plafond_4_pass, 0)
            + (cp.chomage + cp.ags) * plafond_4_pass
            + fnal
            + (cp.csa + cp.dialogue_social + taux_at_mp) * brut
        )
        return where(brut > 0, cotisations, 0)
