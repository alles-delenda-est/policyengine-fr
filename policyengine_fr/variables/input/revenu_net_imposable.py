from policyengine_fr.model_api import *


class revenu_net_imposable(Variable):
    value_type = float
    entity = FoyerFiscal
    label = "Revenu net imposable"
    unit = EUR
    documentation = (
        "Revenu net imposable du foyer fiscal: l'assiette à laquelle le "
        "barème progressif de l'impôt sur le revenu est appliqué. Modélisé "
        "comme une entrée pour l'instant; sera dérivé des revenus dans une "
        "étape ultérieure."
    )
    definition_period = YEAR
