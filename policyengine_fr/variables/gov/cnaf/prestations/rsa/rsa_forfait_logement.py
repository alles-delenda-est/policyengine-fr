from policyengine_fr.model_api import *


class rsa_forfait_logement(Variable):
    value_type = float
    entity = Famille
    label = "Forfait logement déduit du RSA"
    unit = EUR
    documentation = (
        "Forfait logement du RSA (CASF art. R262-9) : valeur forfaitaire du "
        "logement (ou de l'aide au logement) ajoutée aux ressources, donc "
        "déduite du RSA. Calculé comme un pourcentage du montant forfaitaire "
        "non majoré applicable au foyer — 12 % pour une personne, 16 % pour "
        "deux, 16,5 % pour trois et plus (base plafonnée à trois personnes).\n\n"
        "Simplification MVP : le forfait est toujours appliqué (foyer présumé "
        "logé ou bénéficiaire d'une aide au logement), l'APL n'étant pas "
        "modélisée. Métropole uniquement."
    )
    definition_period = MONTH
    reference = "https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000020526192"

    def formula(famille, period, parameters):
        rsa = parameters(period).gov.cnaf.prestations.rsa
        base = rsa.montant_forfaitaire
        fl = rsa.forfait_logement

        age = famille.members("age", period)
        est_enfant = famille.members.has_role(Famille.ENFANT)
        enfant_a_charge = est_enfant & (age >= 0) & (age < rsa.age_charge_maximum)
        nb_personnes = famille.nb_persons(Famille.PARENT) + famille.sum(enfant_a_charge)

        maj2 = rsa.majoration_taille.deuxieme_personne
        maj3 = rsa.majoration_taille.troisieme_personne

        # Non-majoré forfaitaire for the capped size (1 / 2 / 3+ persons).
        forfaitaire_1 = base
        forfaitaire_2 = base * (1 + maj2)
        forfaitaire_3 = base * (1 + maj2 + maj3)

        return where(
            nb_personnes <= 1,
            fl.une_personne * forfaitaire_1,
            where(
                nb_personnes == 2,
                fl.deux_personnes * forfaitaire_2,
                fl.trois_personnes_et_plus * forfaitaire_3,
            ),
        )
