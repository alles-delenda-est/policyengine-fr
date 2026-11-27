from policyengine_fr.model_api import *


class cadre(Variable):
    value_type = bool
    entity = Individu
    label = "Statut cadre"
    default_value = False
    documentation = (
        "Statut cadre du salarié. Déclenche la cotisation salariale APEC "
        "(0,024 % dans la limite de 4 PASS). Par défaut False (non cadre) : "
        "en l'absence de l'information (microdonnées), le barème non cadre "
        "s'applique — simplification MVP documentée."
    )
    definition_period = YEAR
