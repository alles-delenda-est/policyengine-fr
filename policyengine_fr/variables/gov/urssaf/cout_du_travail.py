from policyengine_fr.model_api import *


class cout_du_travail(Variable):
    value_type = float
    entity = Individu
    label = "Coût du travail employeur (salaire super-brut)"
    unit = EUR
    documentation = (
        "Coût annuel total du travail salarié pour l'employeur (super-brut, "
        "spec 0008) :\n\n"
        "    cout_du_travail = salaire_brut + cotisations_patronales − reduction_generale"
    )
    definition_period = YEAR
    reference = "https://www.urssaf.fr/accueil/outils-documentation/simulateurs/cotisations-employeur.html"

    def formula(individu, period, parameters):
        brut = individu("salaire_brut", period)
        cotis_pat = individu("cotisations_patronales", period)
        rg = individu("reduction_generale", period)
        return max_(brut + cotis_pat - rg, 0)
