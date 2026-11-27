from policyengine_fr.model_api import *


class rsa_montant_forfaitaire(Variable):
    value_type = float
    entity = Famille
    label = "Montant forfaitaire du RSA"
    unit = EUR
    documentation = (
        "Montant forfaitaire mensuel du RSA pour la famille (CASF art. L262-2, "
        "L262-3). Égal au montant pour une personne seule, majoré selon la "
        "composition du foyer : +50 % pour la 2e personne, +30 % pour la 3e, "
        "+40 % par personne supplémentaire (la 4e personne n'ouvre +40 % que "
        "pour un parent isolé, sinon +30 %, conformément à l'implémentation "
        "openfisca-france de l'art. R262-1). Pour un parent isolé avec enfant(s) "
        "à charge, le RSA majoré s'applique : base × (1,28412 + 0,42804 × "
        "nombre d'enfants) (CASF L262-9).\n\n"
        "Simplifications MVP : le RSA majoré est appliqué dès qu'un parent isolé "
        "a au moins un enfant à charge ; la limite de durée (12 mois, prolongée "
        "jusqu'aux 3 ans du plus jeune enfant) n'est pas modélisée. La règle de "
        "l'art. R262-1 pour les familles de 4 personnes et plus est approchée "
        "comme dans openfisca-france. Métropole uniquement."
    )
    definition_period = MONTH
    reference = "https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000031694448"

    def formula(famille, period, parameters):
        rsa = parameters(period).gov.cnaf.prestations.rsa
        base = rsa.montant_forfaitaire

        # Foyer size: parents + dependent children under the RSA charge age (25).
        age = famille.members("age", period)
        est_enfant = famille.members.has_role(Famille.ENFANT)
        enfant_a_charge = est_enfant & (age >= 0) & (age < rsa.age_charge_maximum)
        nb_enfants = famille.sum(enfant_a_charge)
        nb_parents = famille.nb_persons(Famille.PARENT)
        nb_personnes = nb_parents + nb_enfants
        isole = nb_parents == 1

        maj2 = rsa.majoration_taille.deuxieme_personne
        maj3 = rsa.majoration_taille.troisieme_personne
        maj_sup = rsa.majoration_taille.personne_supplementaire

        # Composition scale (mirrors openfisca-france rsa_socle): the 4th person
        # adds +40 % for an isolated parent, otherwise +30 %.
        taux = (
            1
            + (nb_personnes >= 2) * maj2
            + (nb_personnes >= 3) * maj3
            + (nb_personnes >= 4) * where(isole, maj_sup, maj3)
            + max_(nb_personnes - 4, 0) * maj_sup
        )
        montant_non_majore = base * taux

        # RSA majoré (parent isolé avec enfant) : base × (A + B × nb_enfants).
        a = rsa.majoration_isolement.montant_de_base
        b = rsa.majoration_isolement.par_enfant
        montant_majore = base * (a + b * nb_enfants)

        applique_majore = isole & (nb_enfants >= 1)
        return where(applique_majore, montant_majore, montant_non_majore)
