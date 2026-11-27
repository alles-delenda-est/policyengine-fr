from policyengine_fr.model_api import *


class rsa(Variable):
    value_type = float
    entity = Famille
    label = "Revenu de solidarité active (RSA)"
    unit = EUR
    documentation = (
        "RSA mensuel (CASF art. L262-1 et s.) : revenu minimum garanti versé en "
        "complément des ressources du foyer. Égal au montant forfaitaire (le cas "
        "échéant majoré pour parent isolé) diminué du forfait logement et de la "
        "base ressources, borné à zéro, et non versé en deçà de 6 €/mois "
        "(CASF art. R262-39).\n\n"
        "Éligibilité (CASF art. L262-4) : au moins un parent âgé de 25 ans ou "
        "plus, ou présence d'au moins un enfant à charge (< 25 ans). Non "
        "modélisés : RSA jeune actif (18-24 ans sans enfant), conditions de "
        "résidence et de titre de séjour, exclusion des étudiants, moyenne "
        "trimestrielle des ressources. Métropole uniquement."
    )
    definition_period = MONTH
    reference = "https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000038833721"

    def formula(famille, period, parameters):
        rsa_p = parameters(period).gov.cnaf.prestations.rsa
        forfaitaire = famille("rsa_montant_forfaitaire", period)
        forfait_logement = famille("rsa_forfait_logement", period)
        ressources = famille("rsa_base_ressources", period)

        montant = max_(forfaitaire - forfait_logement - ressources, 0)
        montant = where(montant >= rsa_p.montant_minimum_verse, montant, 0)

        age = famille.members("age", period)
        est_parent = famille.members.has_role(Famille.PARENT)
        est_enfant = famille.members.has_role(Famille.ENFANT)
        parent_age_ok = famille.sum(est_parent & (age >= rsa_p.age_minimum)) >= 1
        a_enfant_charge = (
            famille.sum(est_enfant & (age >= 0) & (age < rsa_p.age_charge_maximum)) >= 1
        )
        eligible = parent_age_ok | a_enfant_charge

        return where(eligible, montant, 0)
