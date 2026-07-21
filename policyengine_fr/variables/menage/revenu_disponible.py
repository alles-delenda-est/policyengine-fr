from policyengine_fr.model_api import *


class revenu_disponible(Variable):
    value_type = float
    entity = Menage
    label = "Revenu disponible du ménage"
    unit = EUR
    documentation = (
        "Revenu disponible annuel du ménage: l'agrégat de tête de l'MVP. "
        "Pour le périmètre modélisé, on part du revenu d'activité brut, on "
        "retranche les prélèvements modélisés (cotisations sociales salariales, "
        "CSG et CRDS sur les salaires, impôt sur le revenu net) et on ajoute les "
        "prestations familiales modélisées (allocations familiales et ASF "
        "annualisées):\n\n"
        "    revenu_disponible = salaire_brut + pensions_alimentaires_percues\n"
        "        − cotisations_salariales − csg − crds\n"
        "        − impot_revenu − pensions_alimentaires_versees\n"
        "        + allocations_familiales\n"
        "        + allocation_soutien_familial + rsa\n\n"
        "Définition et limites du périmètre MVP:\n"
        "- Le seul revenu d'activité est le `salaire_brut` (revenus du capital "
        "et revenus non salariés hors champ); les pensions alimentaires perçues "
        "sont toutefois comptées comme un revenu et celles versées comme une "
        "charge.\n"
        "- Les cotisations sociales salariales sont approchées par un taux "
        "effectif forfaitaire (voir `cotisations_salariales`), en plus de la "
        "CSG/CRDS: `salaire_brut − cotisations_salariales − csg − crds` est donc "
        "un salaire net approché (le « net » neutralise la cotisation "
        "forfaitaire et la CSG/CRDS, à raffiner — docs/specs/0004).\n"
        "- Les prestations modélisées sont les allocations familiales et "
        "l'allocation de soutien familial (familles monoparentales); les "
        "allocations mensuelles sont annualisées (somme des douze mois). Elles "
        "sont comptées brutes: la CRDS de 0,5 % due sur les prestations "
        "familiales n'est pas prélevée, donc le revenu disponible est "
        "surestimé d'environ 0,5 % du montant des prestations.\n"
        "- Agrégation inter-entités: les composantes vivent sur des entités "
        "différentes (individu pour le salaire/CSG/CRDS, foyer fiscal pour "
        "l'impôt, famille pour les allocations); chacune est ramenée au ménage "
        "en répartissant le total du groupe sur ses membres puis en sommant, ce "
        "qui compte chaque foyer/famille exactement une fois."
    )
    definition_period = YEAR
    reference = "https://www.insee.fr/fr/metadonnees/definition/c1352"

    def formula(menage, period, parameters):
        # Composantes au niveau de l'individu: somme directe sur le ménage.
        salaire_brut = menage.sum(menage.members("salaire_brut", period))
        pensions_percues = menage.sum(
            menage.members("pensions_alimentaires_percues", period)
        )
        cotisations_salariales = menage.sum(
            menage.members("cotisations_salariales", period)
        )
        csg = menage.sum(menage.members("csg", period))
        crds = menage.sum(menage.members("crds", period))

        # Composantes de groupe (foyer fiscal, famille): on répartit le total
        # du groupe sur ses membres (montant / nombre de membres) avant de
        # sommer sur le ménage, de sorte que chaque groupe ne soit compté
        # qu'une fois même si le ménage contient plusieurs foyers/familles.
        ones = menage.members("salaire_brut", period) * 0 + 1

        impot_revenu_groupe = menage.members.foyer_fiscal("impot_revenu", period)
        membres_foyer = menage.members.foyer_fiscal.sum(ones)
        impot_revenu = menage.sum(impot_revenu_groupe / membres_foyer)

        pensions_versees_groupe = menage.members.foyer_fiscal(
            "pensions_alimentaires_versees", period
        )
        pensions_versees = menage.sum(pensions_versees_groupe / membres_foyer)

        # Allocations familiales: variable mensuelle, annualisée via ADD.
        allocations_groupe = menage.members.famille(
            "allocations_familiales", period, options=[ADD]
        )
        membres_famille = menage.members.famille.sum(ones)
        allocations_familiales = menage.sum(allocations_groupe / membres_famille)

        # Allocation de soutien familial: mensuelle, annualisée via ADD,
        # répartie sur les membres de la famille comme les AF.
        asf_groupe = menage.members.famille(
            "allocation_soutien_familial", period, options=[ADD]
        )
        allocation_soutien_familial = menage.sum(asf_groupe / membres_famille)

        # RSA (socle): variable famille mensuelle, annualisée via ADD. Placée
        # après AF/ASF car celles-ci entrent dans sa base ressources.
        rsa_groupe = menage.members.famille("rsa", period, options=[ADD])
        rsa = menage.sum(rsa_groupe / membres_famille)

        return (
            salaire_brut
            + pensions_percues
            - cotisations_salariales
            - impot_revenu
            - csg
            - crds
            - pensions_versees
            + allocations_familiales
            + allocation_soutien_familial
            + rsa
        )
