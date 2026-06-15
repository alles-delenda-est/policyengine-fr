from policyengine_fr.model_api import *


class assiette_csg_crds_salaire(Variable):
    value_type = float
    entity = Individu
    label = "Assiette de la CSG et de la CRDS sur les revenus d'activité salariée"
    unit = EUR
    documentation = (
        "Base de calcul de la CSG et de la CRDS pour un salarié: le salaire brut "
        "diminué de l'abattement d'assiette pour frais professionnels (1,75 %), "
        "soit 98,25 % du salaire brut. Pour le MVP, le plafonnement de "
        "l'abattement à 4 plafonds annuels de la sécurité sociale n'est pas "
        "modélisé (l'abattement s'applique à la totalité du salaire)."
    )
    definition_period = YEAR
    reference = "https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000037948012"

    def formula(individu, period, parameters):
        salaire_brut = individu("salaire_brut", period)
        abattement = parameters(period).gov.urssaf.csg.activite.abattement
        return salaire_brut * (1 - abattement)
