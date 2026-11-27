from policyengine_fr.model_api import *


class ppa_bonification(Variable):
    value_type = float
    entity = Individu
    label = "Bonification individuelle de la prime d'activité"
    unit = EUR
    documentation = (
        "Bonification individuelle mensuelle de la prime d'activité (CSS art. "
        "L842-3, D843-2) attribuée à chaque membre actif âgé d'au moins 18 ans "
        "dont le salaire net mensuel dépasse 59 × SMIC horaire brut (au 1er "
        "janvier de l'année). Croît linéairement de 0 à `0,29101 × montant "
        "forfaitaire de base PPA` entre 59 et 120 × SMIC horaire brut, puis "
        "demeure constante au-delà."
    )
    definition_period = MONTH
    reference = "https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000037850516"

    def formula(individu, period, parameters):
        ppa = parameters(period).gov.cnaf.prestations.prime_activite
        smic_horaire_janvier = parameters(period.this_year).gov.smic.horaire_brut

        age = individu("age", period)
        salaire_mensuel = individu("salaire_net", period.this_year) / 12

        seuil_min = ppa.bonification.seuil_debut_smic_horaire * smic_horaire_janvier
        seuil_max = ppa.bonification.seuil_max_smic_horaire * smic_horaire_janvier
        bonification_max = ppa.montant_de_base * ppa.bonification.taux_max

        ratio = min_(
            max_((salaire_mensuel - seuil_min) / (seuil_max - seuil_min), 0),
            1,
        )
        return where(age >= ppa.age_minimum, bonification_max * ratio, 0)
