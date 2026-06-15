from policyengine_fr.model_api import *


class crds(Variable):
    value_type = float
    entity = Individu
    label = "CRDS sur les revenus d'activité"
    unit = EUR
    documentation = (
        "Contribution au remboursement de la dette sociale sur les revenus "
        "d'activité salariée (taux de 0,5 %), assise sur 98,25 % du salaire "
        "brut. La CRDS n'est pas déductible de l'impôt sur le revenu."
    )
    definition_period = YEAR
    reference = "https://www.legifrance.gouv.fr/loda/id/JORFTEXT000000742159"

    def formula(individu, period, parameters):
        assiette = individu("assiette_csg_crds_salaire", period)
        taux = parameters(period).gov.urssaf.crds.activite.taux
        return assiette * taux
