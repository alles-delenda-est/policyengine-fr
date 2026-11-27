from policyengine_fr.model_api import *


class rsa_base_ressources(Variable):
    value_type = float
    entity = Famille
    label = "Base ressources mensuelle du RSA"
    unit = EUR
    documentation = (
        "Ressources mensuelles prises en compte pour le RSA (CASF art. R262-6 "
        "et s.). Somme, au niveau de la famille :\n"
        "- salaire net annuel des membres (`salaire_net`) ÷ 12 ;\n"
        "- pension de retraite nette (`pension_retraite_nette`) ÷ 12 ;\n"
        "- pensions alimentaires perçues ÷ 12 ;\n"
        "- revenus de capitaux mobiliers perçus (`revenus_capital`) ÷ 12 et "
        "revenus fonciers nets du foyer (`revenus_fonciers_nets`) ÷ 12 ;\n"
        "- allocations familiales de base (hors majoration pour âge, exclue par "
        "le CASF art. R262-11 — LEGIARTI000031061971 en vigueur au 2015-08-23 / "
        "LEGIARTI000051258442 en vigueur au 2025-03-01) : prise au montant de "
        "base non modulé, qui égale le montant modulé réel pour tout foyer "
        "éligible au RSA (toujours en tranche 1, taux plein) ;\n"
        "- ASF plafonnée au forfait ASF (CASF art. R262-10-1 — "
        "LEGIARTI000029006452 en vigueur au 2014-06-01) : `min(asf, "
        "0,225 × BMAF × nb_enfants)`, qui forfaitise l'ASF à taux plein et "
        "borne l'ASF différentielle afin de neutraliser son effet sur le RSA.\n\n"
        "Simplifications MVP : moyenne trimestrielle remplacée par le revenu "
        "annuel ÷ 12 ; taxation forfaitaire de 3 % de l'épargne non productrice "
        "de revenus (CASF art. R132-1), plus-values immobilières exceptionnelles, "
        "neutralisation des revenus d'activité des 3 premiers mois (art. R262-7) "
        "et déduction des pensions versées non modélisées. Métropole uniquement."
    )
    definition_period = MONTH
    reference = (
        "https://www.legifrance.gouv.fr/codes/article_lc/"
        "LEGIARTI000051258442/2025-03-01/"
    )

    def formula(famille, period, parameters):
        rsa = parameters(period).gov.cnaf.prestations.rsa
        af = parameters(period).gov.cnaf.prestations.af
        bmaf = parameters(period).gov.cnaf.bmaf

        individus = famille.members
        salaire = famille.sum(individus("salaire_net", period.this_year)) / 12
        retraite = (
            famille.sum(individus("pension_retraite_nette", period.this_year)) / 12
        )
        pensions = (
            famille.sum(individus("pensions_alimentaires_percues", period.this_year))
            / 12
        )
        capital = famille.sum(individus("revenus_capital", period.this_year)) / 12
        foncier_foyer = individus.foyer_fiscal(
            "revenus_fonciers_nets", period.this_year
        )
        nb_membres_foyer = max_(individus.foyer_fiscal.nb_persons(), 1)
        foncier = famille.sum(foncier_foyer / nb_membres_foyer) / 12

        # Enfants ouvrant droit aux prestations familiales (< 20 ans).
        age = individus("age", period)
        est_enfant = individus.has_role(Famille.ENFANT)
        ouvre_droit = est_enfant & (age >= 0) & (age < af.age_limite)
        nb_enfants = famille.sum(ouvre_droit)

        # AF de base hors majoration pour âge (CASF art. R262-11).
        enfants_au_dela_de_deux = max_(nb_enfants - 2, 0)
        taux_af_base = (
            af.taux.enfant_2 + af.taux.enfant_supplementaire * enfants_au_dela_de_deux
        )
        af_base = where(nb_enfants >= 2, bmaf * taux_af_base, 0)

        # ASF retenue dans la limite du forfait ASF (0,225 BMAF / enfant, R262-10-1).
        asf = famille("allocation_soutien_familial", period)
        asf_plafond = bmaf * rsa.forfait_asf * nb_enfants
        asf_retenue = min_(asf, asf_plafond)

        return salaire + retraite + pensions + capital + foncier + af_base + asf_retenue
