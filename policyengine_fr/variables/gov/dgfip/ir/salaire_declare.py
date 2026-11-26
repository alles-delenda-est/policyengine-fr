from policyengine_fr.model_api import *


class salaire_declare(Variable):
    value_type = float
    entity = Individu
    label = "Salaire déclaré (case 1AJ)"
    unit = EUR
    documentation = (
        "Salaire net imposable déclaré à l'impôt sur le revenu (case 1AJ de la "
        "déclaration): salaire brut diminué des cotisations sociales salariales "
        "et de la CSG déductible.\n\n"
        "    salaire_declare = salaire_brut − cotisations_salariales − csg_deductible\n\n"
        "C'est le montant que le contribuable reporte en case 1AJ (déjà net de "
        "cotisations et de CSG déductible), et la base sur laquelle "
        "`salaire_imposable` applique l'abattement de 10 %. La déductibilité de "
        "la CSG (CGI art. 154 quinquies) est ainsi appliquée exactement une fois, "
        "à cette étape, et ne doit pas l'être de nouveau dans "
        "`revenu_net_imposable`."
    )
    definition_period = YEAR
    reference = "https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000042683600"

    def formula(individu, period, parameters):
        salaire_brut = individu("salaire_brut", period)
        cotisations = individu("cotisations_salariales", period)
        csg_deductible = individu("csg_deductible", period)
        return max_(salaire_brut - cotisations - csg_deductible, 0)
