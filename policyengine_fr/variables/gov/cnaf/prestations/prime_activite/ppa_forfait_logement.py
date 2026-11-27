from policyengine_fr.model_api import *


class ppa_forfait_logement(Variable):
    value_type = float
    entity = Famille
    label = "Forfait logement de la prime d'activité"
    unit = EUR
    documentation = (
        "Forfait logement mensuel pris en compte dans les ressources de la "
        "prime d'activité (CSS art. R844-4) : 12 % (1 personne), 16 % × 1,5 "
        "(2 personnes), ou 16,5 % × 1,8 (3 personnes et plus) du montant "
        "forfaitaire de base PPA. Appliqué systématiquement (même hypothèse "
        "de foyer logé que pour le RSA)."
    )
    definition_period = MONTH
    reference = "https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000031673915"

    def formula(famille, period, parameters):
        p = parameters(period).gov.cnaf.prestations
        base = p.prime_activite.montant_de_base
        rsa = p.rsa
        fl = rsa.forfait_logement

        age = famille.members("age", period)
        est_enfant = famille.members.has_role(Famille.ENFANT)
        enfant_a_charge = est_enfant & (age >= 0) & (age < rsa.age_charge_maximum)
        nb_personnes = famille.nb_persons(Famille.PARENT) + famille.sum(enfant_a_charge)

        maj2 = rsa.majoration_taille.deuxieme_personne
        maj3 = rsa.majoration_taille.troisieme_personne

        return where(
            nb_personnes <= 1,
            fl.une_personne * base,
            where(
                nb_personnes == 2,
                fl.deux_personnes * base * (1 + maj2),
                fl.trois_personnes_et_plus * base * (1 + maj2 + maj3),
            ),
        )
