from policyengine_fr.model_api import *


class pension_retraite_declaree(Variable):
    value_type = float
    entity = Individu
    label = "Pension de retraite déclarée (nette de CSG déductible)"
    unit = EUR
    documentation = (
        "Pension de retraite retenue au revenu imposable, avant l'abattement de "
        "10 % : pension brute diminuée de la CSG déductible sur pension "
        "(specs 0005/0006), par cohérence avec le traitement du salaire (0001). "
        "L'abattement de 10 % sur les pensions est ensuite appliqué, mutualisé "
        "avec les pensions alimentaires perçues, par `pensions_imposables`."
    )
    definition_period = YEAR

    def formula(individu, period, parameters):
        pension = individu("pension_retraite", period)
        csg_deductible = individu("csg_retraite_deductible", period)
        return max_(pension - csg_deductible, 0)
