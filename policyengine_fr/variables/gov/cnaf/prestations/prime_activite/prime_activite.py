from policyengine_fr.model_api import *


class prime_activite(Variable):
    value_type = float
    entity = Famille
    label = "Prime d'activité"
    unit = EUR
    documentation = (
        "Prime d'activité mensuelle (CSS art. L841-1 à L845-3, D843-1 à D843-3) :\n\n"
        "    montant_base = max(ppa_montant_forfaitaire + 61 % × revenus_activite\n"
        "                       + bonifications − ressources − ppa_forfait_logement, 0)\n"
        "    ppa_non_bonifiee = max(ppa_montant_forfaitaire − ressources\n"
        "                           − ppa_forfait_logement, 0)\n"
        "    prime_activite = max(montant_base − ppa_non_bonifiee, 0)\n\n"
        "Versée si au moins un parent a 18 ans ou plus et si le montant atteint "
        "15 €/mois (CSS art. D843-3). La soustraction de `ppa_non_bonifiee` "
        "(art. L842-3) garantit qu'un foyer sans revenu d'activité perçoit 0 € "
        "de prime d'activité (couvert par le RSA) et évite tout double compte "
        "du socle forfaitaire lorsque RSA et prime d'activité se cumulent.\n\n"
        "Simplifications MVP : revenus annuels ÷ 12 (pas de trimestrialisation "
        "ni de cristallisation), incluant les revenus de capitaux mobiliers "
        "(`revenus_capital`) et revenus fonciers nets (`revenus_fonciers_nets`) "
        "via `rsa_base_ressources` (hors taxation forfaitaire de 3 % de "
        "l'épargne non productrice) ; forfait logement toujours appliqué ; "
        "exclusion étudiants/apprentis sous seuil de 0,78 SMIC non modélisée ; "
        "RSA déduit implicitement via `ppa_non_bonifiee` ; métropole uniquement."
    )
    definition_period = MONTH
    reference = "https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000038009897"

    def formula(famille, period, parameters):
        ppa = parameters(period).gov.cnaf.prestations.prime_activite
        forfaitaire = famille("ppa_montant_forfaitaire", period)
        forfait_logement = famille("ppa_forfait_logement", period)
        ressources = famille("rsa_base_ressources", period)

        revenus_activite = (
            famille.sum(famille.members("salaire_net", period.this_year)) / 12
        )
        bonifications = famille.sum(famille.members("ppa_bonification", period))

        montant_base = max_(
            forfaitaire
            + ppa.taux_cumul_activite * revenus_activite
            + bonifications
            - ressources
            - forfait_logement,
            0,
        )
        ppa_non_bonifiee = max_(forfaitaire - ressources - forfait_logement, 0)
        montant = max_(montant_base - ppa_non_bonifiee, 0)
        montant = where(montant >= ppa.montant_minimum_verse, montant, 0)

        age = famille.members("age", period)
        est_parent = famille.members.has_role(Famille.PARENT)
        eligible = famille.sum(est_parent & (age >= ppa.age_minimum)) >= 1
        return where(eligible, montant, 0)
