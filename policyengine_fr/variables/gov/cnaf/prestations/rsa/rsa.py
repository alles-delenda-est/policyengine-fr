from policyengine_fr.model_api import *


class rsa(Variable):
    value_type = float
    entity = Famille
    label = "Revenu de solidarité active (socle)"
    unit = EUR
    documentation = (
        "Revenu de solidarité active — socle (CASF art. L262-1 et s.). "
        "Complément différentiel portant les ressources du foyer au niveau du "
        "montant forfaitaire garanti:\n\n"
        "    RSA = max(montant_forfaitaire − forfait_logement − base_ressources, 0)\n\n"
        "Périmètre MVP: seul le socle est modélisé. Hors champ (voir "
        "modelled_policies.yaml): prime d'activité, RSA jeune, contrat "
        "d'engagement et sanctions, abattement/neutralisation des revenus "
        "d'activité des 3 premiers mois, cumul intéressement, cristallisation. "
        "Métropole uniquement, revenus 2024."
    )
    definition_period = MONTH
    reference = "https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000037861670"

    def formula(famille, period, parameters):
        montant_forfaitaire = famille("rsa_montant_forfaitaire", period)
        forfait_logement = famille("rsa_forfait_logement", period)
        base_ressources = famille("rsa_base_ressources", period)
        return max_(montant_forfaitaire - forfait_logement - base_ressources, 0)
