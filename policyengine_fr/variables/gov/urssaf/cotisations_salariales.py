from policyengine_fr.model_api import *


class cotisations_salariales(Variable):
    value_type = float
    entity = Individu
    label = "Cotisations sociales salariales (hors CSG/CRDS)"
    unit = EUR
    documentation = (
        "Cotisations sociales salariales prélevées sur le salaire brut, hors "
        "CSG/CRDS (calculées séparément). Somme des principales lignes de la "
        "part salariale, chacune assise sur sa tranche (spec 0004):\n"
        "- vieillesse plafonnée (6,90 %) sur la tranche 0-1 PASS,\n"
        "- vieillesse déplafonnée (0,40 %) sur la totalité,\n"
        "- retraite complémentaire AGIRC-ARRCO T1 (3,15 %) + CEG T1 (0,86 %) "
        "sur 0-1 PASS, T2 (8,64 %) + CEG T2 (1,08 %) sur 1-8 PASS,\n"
        "- cadres uniquement: CET (0,14 %) sur 1-8 PASS et APEC (0,024 %) sur "
        "0-4 PASS.\n\n"
        "Sert à passer du salaire brut au salaire déclaré (case 1AJ). "
        "Simplifications MVP (voir modelled_policies.yaml): chômage et maladie "
        "salariales nuls depuis 2018 (remplacés par la CSG) ; pas d'exonérations "
        "spécifiques (heures supplémentaires, apprentis, ZRR) ; les allègements "
        "bas salaires (réduction générale) sont côté employeur (spec 0008)."
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
        base_apec = min_(brut, 4 * pass_annuel)  # 0-4 PASS

        base = (
            c.vieillesse_plafonnee * tranche_1
            + c.vieillesse_deplafonnee * brut
            + c.retraite_complementaire_t1 * tranche_1
            + c.retraite_complementaire_t2 * tranche_2
            + c.ceg_t1 * tranche_1
            + c.ceg_t2 * tranche_2
        )
        supplement_cadre = c.cet * tranche_2 + c.apec * base_apec
        return base + where(cadre, supplement_cadre, 0)
