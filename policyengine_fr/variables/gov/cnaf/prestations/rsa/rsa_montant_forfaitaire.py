from policyengine_fr.model_api import *


class rsa_montant_forfaitaire(Variable):
    value_type = float
    entity = Famille
    label = "Montant forfaitaire du RSA"
    unit = EUR
    documentation = (
        "Montant forfaitaire mensuel du RSA pour la famille, selon l'échelle "
        "d'équivalence du CASF art. R262-1: montant de base (1 personne) majoré "
        "de 50 % pour un second adulte, de 30 % par enfant de rang 1-2 et de "
        "40 % par enfant de rang 3 et plus.\n\n"
        "Parent isolé (RSA majoré, CASF art. R262-1): lorsque la famille n'a "
        "qu'un parent et au moins un enfant, on applique le barème majoré "
        "(128,412 % du montant de base pour le parent seul, + 42,804 % par "
        "enfant à charge dès le premier — soit 171,216 % pour 1 enfant, "
        "214,020 % pour 2 enfants).\n\n"
        "Simplifications MVP (voir modelled_policies.yaml): l'isolement est "
        "inféré du seul fait qu'il n'y a qu'un parent (proxy, comme l'ASF); la "
        "durée du RSA majoré (jusqu'aux 3 ans du plus jeune enfant) n'est pas "
        "modélisée; femme enceinte sans enfant non captée. Métropole uniquement."
    )
    definition_period = MONTH
    reference = "https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000037861692"

    def formula(famille, period, parameters):
        mf = parameters(period).gov.cnaf.prestations.rsa.montant_forfaitaire
        age_limite = parameters(period).gov.cnaf.prestations.af.age_limite

        base = mf.base
        nb_parents = famille.nb_persons(Famille.PARENT)
        age = famille.members("age", period)
        est_enfant = famille.members.has_role(Famille.ENFANT)
        ouvre_droit = est_enfant & (age >= 0) & (age < age_limite)
        nb_enfants = famille.sum(ouvre_droit)

        # Barème standard: 1 + 0,5 (2e adulte) + 0,3 par enfant (rangs 1-2)
        # + 0,4 par enfant (rang 3 et +).
        coef_standard = (
            1.0
            + where(nb_parents >= 2, mf.majoration_couple, 0)
            + mf.majoration_enfant * min_(nb_enfants, 2)
            + mf.majoration_enfant_rang_3 * max_(nb_enfants - 2, 0)
        )

        # Barème majoré (parent isolé): 1,28412 pour le parent seul, + 0,42804
        # par enfant à charge (dès le premier). Ex. 1 enfant → 1,71216 ;
        # 2 enfants → 2,14020.
        coef_majore = mf.isole_base + mf.isole_enfant * nb_enfants

        parent_isole = (nb_parents == 1) & (nb_enfants >= 1)
        coef = where(parent_isole, coef_majore, coef_standard)
        return base * coef
