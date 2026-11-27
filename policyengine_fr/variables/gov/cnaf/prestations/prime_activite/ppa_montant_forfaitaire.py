from policyengine_fr.model_api import *


class ppa_montant_forfaitaire(Variable):
    value_type = float
    entity = Famille
    label = "Montant forfaitaire de la prime d'activité"
    unit = EUR
    documentation = (
        "Montant forfaitaire mensuel de la prime d'activité selon la "
        "composition de la famille et la majoration pour isolement (CSS art. "
        "L842-3, R842-1, D843-1). Applique au montant de base PPA la même "
        "échelle d'équivalence (+50 % 2e personne, +30 % 3e, +40 % au-delà) "
        "et les mêmes coefficients d'isolement (1,28412 + 0,42804 × enfants) "
        "que le RSA."
    )
    definition_period = MONTH
    reference = "https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000038009897"

    def formula(famille, period, parameters):
        p = parameters(period).gov.cnaf.prestations
        base = p.prime_activite.montant_de_base
        rsa = p.rsa

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

        taux = (
            1
            + (nb_personnes >= 2) * maj2
            + (nb_personnes >= 3) * maj3
            + (nb_personnes >= 4) * where(isole, maj_sup, maj3)
            + max_(nb_personnes - 4, 0) * maj_sup
        )
        montant_non_majore = base * taux

        a = rsa.majoration_isolement.montant_de_base
        b = rsa.majoration_isolement.par_enfant
        montant_majore = base * (a + b * nb_enfants)

        return where(isole & (nb_enfants >= 1), montant_majore, montant_non_majore)
