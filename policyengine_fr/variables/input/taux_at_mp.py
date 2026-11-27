from policyengine_fr.model_api import *


class taux_at_mp(Variable):
    value_type = float
    entity = Individu
    label = "Taux de cotisation patronale accidents du travail / maladies professionnelles (AT/MP)"
    unit = "/1"
    default_value = 0.0212
    documentation = (
        "Taux de la cotisation patronale AT/MP, propre au secteur et à la "
        "sinistralité de l'établissement. Par défaut 2,12 % (taux net moyen "
        "national 2024, arrêté du 27 décembre 2023). Seule la fraction "
        "forfaitaire mutualisée (0,46 % en 2024) entre dans le périmètre de "
        "la réduction générale."
    )
    definition_period = YEAR
