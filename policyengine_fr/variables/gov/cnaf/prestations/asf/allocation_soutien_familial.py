from policyengine_fr.model_api import *


class allocation_soutien_familial(Variable):
    value_type = float
    entity = Famille
    label = "Allocation de soutien familial (taux simple)"
    unit = EUR
    documentation = (
        "Allocation de soutien familial (ASF) versée par la CAF/MSA pour un "
        "enfant privé du soutien d'un de ses parents (CSS art. L523-1 et s.). "
        "Au taux simple, le montant vaut 0,422 BMAF par enfant à charge "
        "(art. R523-7), versé dès le premier enfant et sans condition de "
        "ressources. Le périmètre MVP infère le droit du seul fait que la "
        "famille n'a qu'un parent.\n\n"
        "Limitations MVP (départs explicites du droit, voir modelled_policies.yaml):\n"
        "- Taux majoré « orphelin de deux parents » non modélisé (un seul taux).\n"
        "- ASF différentielle / recouvrement non modélisés : faute d'input "
        "pension alimentaire, le modèle verse l'ASF pleine à toute famille "
        "monoparentale, même si une pension alimentaire est déjà perçue "
        "(sur-estimation possible).\n"
        "- Le cas d'un parent défaillant au sein d'un couple (ouvrant droit à "
        "l'ASF) n'est pas capté par le proxy « parent unique » (sous-estimation).\n"
        "- Métropole uniquement ; pas de partage en garde alternée."
    )
    definition_period = MONTH
    reference = "https://www.service-public.fr/particuliers/vosdroits/F815"

    def formula(famille, period, parameters):
        asf = parameters(period).gov.cnaf.prestations.asf
        bmaf = parameters(period).gov.cnaf.bmaf
        age_limite = parameters(period).gov.cnaf.prestations.af.age_limite

        age = famille.members("age", period)
        est_enfant = famille.members.has_role(Famille.ENFANT)
        # Enfant à charge ouvrant droit: rôle enfant et âge sous la limite AF.
        ouvre_droit = est_enfant & (age >= 0) & (age < age_limite)
        nb_enfants = famille.sum(ouvre_droit)

        # Proxy MVP du droit: la famille n'a qu'un seul parent.
        parent_unique = famille.nb_persons(Famille.PARENT) == 1

        montant = bmaf * asf.taux_orphelin_un_parent * nb_enfants
        return where(parent_unique, montant, 0)
