from policyengine_fr.model_api import *


class salaire_brut(Variable):
    value_type = float
    entity = Individu
    label = "Salaire brut imposable"
    unit = EUR
    documentation = (
        "Revenu d'activité salariée annuel déclaré (avant déduction forfaitaire "
        "de 10% pour frais professionnels)."
    )
    definition_period = YEAR
