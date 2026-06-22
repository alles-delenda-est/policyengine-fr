from policyengine_fr.model_api import *


class revenu_disponible(Variable):
    value_type = float
    entity = Menage
    label = "Revenu disponible du ménage"
    unit = EUR
    documentation = (
        "Revenu disponible annuel du ménage: l'agrégat de tête de l'MVP. "
        "Pour le périmètre modélisé, on part du revenu d'activité brut, on "
        "retranche les prélèvements modélisés (impôt sur le revenu net, CSG et "
        "CRDS sur les salaires) et on ajoute les prestations familiales "
        "modélisées (allocations familiales et ASF annualisées):\n\n"
        "    revenu_disponible = salaire_brut\n"
        "        − impot_revenu − csg − crds\n"
        "        + allocations_familiales\n"
        "        + allocation_soutien_familial\n\n"
        "Définition et limites du périmètre MVP:\n"
        "- Le seul revenu d'activité est le `salaire_brut` (revenus du capital, "
        "pensions et revenus non salariés hors champ).\n"
        "- Les seuls prélèvements sociaux modélisés sur le salaire sont la CSG "
        "et la CRDS; les autres cotisations sociales salariales (maladie, "
        "retraite, chômage…) ne sont pas modélisées, donc le « net » ici ne "
        "neutralise que la CSG/CRDS.\n"
        "- Les prestations modélisées sont les allocations familiales et "
        "l'allocation de soutien familial (familles monoparentales); les "
        "allocations mensuelles sont annualisées (somme des douze mois).\n"
        "- L'allocation de soutien familial (familles monoparentales) est "
        "ajoutée, annualisée comme les AF.\n"
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

        return (
            salaire_brut
            - impot_revenu
            - csg
            - crds
            + allocations_familiales
            + allocation_soutien_familial
        )
