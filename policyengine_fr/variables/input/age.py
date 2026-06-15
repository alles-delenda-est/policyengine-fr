from policyengine_fr.model_api import *


class age(Variable):
    value_type = int
    entity = Individu
    label = "Âge"
    unit = "year"
    documentation = (
        "Âge de la personne en années révolues. Variable d'entrée pour le MVP "
        "(renseignée directement dans les tests); à terme, dérivée de la date "
        "de naissance."
    )
    definition_period = MONTH
