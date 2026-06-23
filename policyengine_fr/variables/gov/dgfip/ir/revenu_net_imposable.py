from policyengine_fr.model_api import *


class revenu_net_imposable(Variable):
    value_type = float
    entity = FoyerFiscal
    label = "Revenu net imposable"
    unit = EUR
    documentation = (
        "Revenu net imposable du foyer fiscal: l'assiette à laquelle le barème "
        "progressif de l'impôt sur le revenu est appliqué. Somme des salaires "
        "imposables (après abattement de 10%) et des pensions alimentaires "
        "perçues imposables des membres du foyer, diminuée des pensions "
        "alimentaires versées déductibles, et bornée à zéro. Reste paramétrable "
        "directement en entrée pour les tests unitaires."
    )
    definition_period = YEAR

    def formula(foyer_fiscal, period, parameters):
        salaire_imposable_i = foyer_fiscal.members("salaire_imposable", period)
        salaires = foyer_fiscal.sum(salaire_imposable_i)
        pensions_percues = foyer_fiscal("pensions_alimentaires_imposables", period)
        pensions_versees = foyer_fiscal("pensions_alimentaires_versees", period)
        return max_(salaires + pensions_percues - pensions_versees, 0)
