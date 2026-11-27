from policyengine_fr.model_api import *


class revenu_disponible(Variable):
    value_type = float
    entity = Menage
    label = "Revenu disponible du ménage"
    unit = EUR
    documentation = (
        "Revenu disponible annuel du ménage : agrège les revenus d'activité, "
        "de remplacement (retraites), alimentaires, fonciers et financiers du "
        "ménage, retranche les cotisations salariales, les prélèvements "
        "sociaux (activité, retraite, patrimoine), l'impôt sur le revenu, la "
        "CEHR, le PFU, l'impôt sur les plus-values immobilières, l'IFI et les "
        "impôts fonciers locaux (ou la taxe sur la valeur du sol en réforme "
        "LVTShift), et ajoute les prestations sociales annualisées (AF, ASF, "
        "RSA et prime d'activité) :\n\n"
        "    revenu_disponible =\n"
        "        salaire_brut + pension_retraite + pensions_alimentaires_percues\n"
        "        + revenus_capital + max(revenus_fonciers_bruts − charges_foncieres_reelles, 0)\n"
        "        + plus_values_immobilieres\n"
        "        − cotisations_salariales − csg − crds\n"
        "        − csg_retraite − crds_retraite − casa_retraite\n"
        "        − impot_revenu − cehr − pfu_ir − impot_plus_values_immobilieres\n"
        "        − prelevements_sociaux_patrimoine − ifi − pensions_alimentaires_versees\n"
        "        − taxe_fonciere − taxe_habitation_residence_secondaire − taxe_valeur_sol\n"
        "        + allocations_familiales + allocation_soutien_familial\n"
        "        + rsa + prime_activite"
    )
    definition_period = YEAR
    reference = "https://www.insee.fr/fr/metadonnees/definition/c1352"

    def formula(menage, period, parameters):
        salaire_brut = menage.sum(menage.members("salaire_brut", period))
        pension_retraite_nette = menage.sum(
            menage.members("pension_retraite_nette", period)
        )
        pensions_percues = menage.sum(
            menage.members("pensions_alimentaires_percues", period)
        )
        revenus_capital = menage.sum(menage.members("revenus_capital", period))

        cotisations_salariales = menage.sum(
            menage.members("cotisations_salariales", period)
        )
        csg = menage.sum(menage.members("csg", period))
        crds = menage.sum(menage.members("crds", period))

        ones = menage.members("salaire_brut", period) * 0 + 1
        membres_foyer = menage.members.foyer_fiscal.sum(ones)
        membres_famille = menage.members.famille.sum(ones)

        def sum_foyer(var_name):
            return menage.sum(
                menage.members.foyer_fiscal(var_name, period) / membres_foyer
            )

        def sum_famille_add(var_name):
            return menage.sum(
                menage.members.famille(var_name, period, options=[ADD])
                / membres_famille
            )

        loyers_economiques = menage.sum(
            max_(
                menage.members.foyer_fiscal("revenus_fonciers_bruts", period)
                - menage.members.foyer_fiscal("charges_foncieres_reelles", period),
                0,
            )
            / membres_foyer
        )
        plus_values_immo = sum_foyer("plus_values_immobilieres")

        impot_revenu = sum_foyer("impot_revenu")
        cehr = sum_foyer("cehr")
        pfu_ir = sum_foyer("pfu_ir")
        impot_pv = sum_foyer("impot_plus_values_immobilieres")
        ps_patrimoine = sum_foyer("prelevements_sociaux_patrimoine")
        ifi = sum_foyer("ifi")
        pensions_versees = sum_foyer("pensions_alimentaires_versees")

        taxe_fonciere = menage("taxe_fonciere", period)
        thrs = menage("taxe_habitation_residence_secondaire", period)
        lvt = menage("taxe_valeur_sol", period)

        allocations_familiales = sum_famille_add("allocations_familiales")
        allocation_soutien_familial = sum_famille_add("allocation_soutien_familial")
        rsa = sum_famille_add("rsa")
        prime_activite = sum_famille_add("prime_activite")

        return (
            salaire_brut
            + pension_retraite_nette
            + pensions_percues
            + revenus_capital
            + loyers_economiques
            + plus_values_immo
            - cotisations_salariales
            - csg
            - crds
            - impot_revenu
            - cehr
            - pfu_ir
            - impot_pv
            - ps_patrimoine
            - ifi
            - pensions_versees
            - taxe_fonciere
            - thrs
            - lvt
            + allocations_familiales
            + allocation_soutien_familial
            + rsa
            + prime_activite
        )
