from policyengine_fr.model_api import *


class rsa_base_ressources(Variable):
    value_type = float
    entity = Famille
    label = "Base ressources mensuelle du RSA"
    unit = EUR
    documentation = (
        "Ressources mensuelles prises en compte pour le RSA (CASF art. R262-6). "
        "Somme, au niveau de la famille et ramenée au mois:\n"
        "- salaires déclarés des membres (salaire_declare / 12),\n"
        "- pensions alimentaires perçues (/ 12),\n"
        "- prestations familiales incluses dans la base RSA: allocations "
        "familiales et allocation de soutien familial (mensuelles).\n\n"
        "Simplifications MVP (voir modelled_policies.yaml): la base légale est "
        "la moyenne des ressources des 3 mois précédant la demande (art. R262-3); "
        "on utilise ici le revenu annuel modélisé / 12 comme proxy mensuel (même "
        "simplification que la base ressources N des AF). L'abattement / la "
        "neutralisation des revenus d'activité des 3 premiers mois (art. R262-7) "
        "n'est pas appliqué. Le périmètre des ressources est réduit à ce que le "
        "MVP sait modéliser (ni capital, ni revenus de remplacement, ni autres "
        "prestations). Métropole uniquement."
    )
    definition_period = MONTH
    reference = "https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000037861678"

    def formula(famille, period, parameters):
        salaires = (
            famille.sum(famille.members("salaire_declare", period.this_year)) / 12
        )
        pensions = (
            famille.sum(
                famille.members("pensions_alimentaires_percues", period.this_year)
            )
            / 12
        )
        allocations_familiales = famille("allocations_familiales", period)
        asf = famille("allocation_soutien_familial", period)
        return salaires + pensions + allocations_familiales + asf
