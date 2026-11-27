from policyengine_fr.model_api import *


class cotisations_salariales(Variable):
    value_type = float
    entity = Individu
    label = "Cotisations sociales salariales (hors CSG/CRDS)"
    unit = EUR
    documentation = (
        "Cotisations sociales salariales prélevées sur le salaire brut, hors "
        "CSG/CRDS (calculées séparément). Somme des principales lignes de la "
        "part salariale du secteur privé (régime général + AGIRC-ARRCO fusionné "
        "depuis 2019), chacune assise sur sa tranche (spec 0004):\n"
        "- vieillesse plafonnée (6,90 %) sur la tranche 0-1 PASS,\n"
        "- vieillesse déplafonnée (0,40 %) sur la totalité,\n"
        "- retraite complémentaire AGIRC-ARRCO T1 (3,15 %) + CEG T1 (0,86 %) "
        "sur 0-1 PASS, T2 (8,64 %) + CEG T2 (1,08 %) sur 1-8 PASS,\n"
        "- CET (0,14 %) sur 0-8 PASS dès lors que le salaire brut excède 1 PASS "
        "(tous salariés, cadres et non-cadres, ANI AGIRC-ARRCO du 17 nov. 2017),\n"
        "- cadres uniquement: APEC (0,024 %) sur 0-4 PASS.\n\n"
        "Sert à passer du salaire brut au salaire déclaré (case 1AJ) et au "
        "salaire net (`salaire_net`). Simplifications MVP (voir "
        "modelled_policies.yaml): chômage et maladie salariales nuls depuis "
        "2018 (remplacés par la CSG, hors Alsace-Moselle) ; pas d'exonérations "
        "spécifiques (heures supplémentaires, apprentis, ZRR) ; mutuelle "
        "obligatoire d'entreprise non modélisée ; les allègements bas salaires "
        "(réduction générale) sont côté employeur (spec 0008). Variable "
        "annuelle (`YEAR`) : `parameters(period)` lit les taux et le PASS en "
        "vigueur au 1er janvier de l'année simulée (sans proratisation "
        "infra-annuelle)."
    )
    definition_period = YEAR
    reference = (
        "https://www.urssaf.fr/accueil/employeur/cotisations/liste-cotisations.html"
    )

    def formula(individu, period, parameters):
        brut = individu("salaire_brut", period)
        cadre = individu("cadre", period)
        c = parameters(period).gov.urssaf.cotisations_salariales
        pass_annuel = parameters(period).gov.urssaf.plafond_securite_sociale

        # Bases par tranche.
        tranche_1 = min_(brut, pass_annuel)  # 0-1 PASS
        tranche_2 = min_(max_(brut - pass_annuel, 0), 7 * pass_annuel)  # 1-8 PASS
        tranches_1_2 = min_(brut, 8 * pass_annuel)  # 0-8 PASS
        base_apec = min_(brut, 4 * pass_annuel)  # 0-4 PASS

        base = (
            c.vieillesse_plafonnee * tranche_1
            + c.vieillesse_deplafonnee * brut
            + c.retraite_complementaire_t1 * tranche_1
            + c.retraite_complementaire_t2 * tranche_2
            + c.ceg_t1 * tranche_1
            + c.ceg_t2 * tranche_2
            + where(brut > pass_annuel, c.cet * tranches_1_2, 0)
        )
        supplement_cadre = c.apec * base_apec
        return base + where(cadre, supplement_cadre, 0)
