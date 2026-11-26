from policyengine_fr.model_api import *


class cadre(Variable):
    value_type = bool
    entity = Individu
    label = "Statut cadre"
    default_value = False
    documentation = (
        "Statut cadre du salarié. Déclenche les cotisations salariales propres "
        "aux cadres (CET au-delà d'un PASS, APEC). Par défaut False (non cadre) : "
        "en l'absence de l'information (microdonnées), le barème non cadre "
        "s'applique — simplification MVP documentée."
    )
    definition_period = YEAR
