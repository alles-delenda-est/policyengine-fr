from policyengine_fr.model_api import *


class cotisations_salariales(Variable):
    value_type = float
    entity = Individu
    label = "Cotisations sociales salariales (hors CSG/CRDS)"
    unit = EUR
    documentation = (
        "Cotisations sociales salariales prélevées sur le salaire brut, hors "
        "CSG/CRDS (qui sont calculées séparément). Approximation MVP: taux "
        "effectif forfaitaire (≈ 11,31 % pour 2024, voir le paramètre "
        "`gov.urssaf.cotisations_salariales.taux_effectif`) appliqué au salaire "
        "brut, sans plafond de la sécurité sociale ni distinction cadre/non "
        "cadre. Sert à passer du salaire brut au salaire déclaré (case 1AJ)."
    )
    definition_period = YEAR
    reference = (
        "https://www.urssaf.fr/accueil/employeur/cotisations/liste-cotisations.html"
    )

    def formula(individu, period, parameters):
        salaire_brut = individu("salaire_brut", period)
        taux = parameters(period).gov.urssaf.cotisations_salariales.taux_effectif
        return salaire_brut * taux
