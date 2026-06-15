from policyengine_fr.model_api import *


class revenu_net_imposable(Variable):
    value_type = float
    entity = FoyerFiscal
    label = "Revenu net imposable"
    unit = EUR
    documentation = (
        "Revenu net imposable du foyer fiscal: l'assiette à laquelle le barème "
        "progressif de l'impôt sur le revenu est appliqué. Pour le MVP, somme "
        "des salaires imposables (après abattement de 10%) des membres du foyer. "
        "Reste paramétrable directement en entrée pour les tests unitaires."
    )
    definition_period = YEAR

    def formula(foyer_fiscal, period, parameters):
        salaire_imposable_i = foyer_fiscal.members("salaire_imposable", period)
        return foyer_fiscal.sum(salaire_imposable_i)
