from policyengine_fr.model_api import *


class rsa_forfait_logement(Variable):
    value_type = float
    entity = Famille
    label = "Forfait logement déduit du RSA"
    unit = EUR
    documentation = (
        "Forfait logement mensuel (CASF art. R262-9): montant forfaitaire déduit "
        "des ressources pour le calcul du RSA lorsque le foyer est logé "
        "gratuitement, propriétaire, ou bénéficie d'une aide au logement. Il "
        "vaut 12 % du montant forfaitaire d'une personne (foyer d'1 personne), "
        "16 % de celui de deux personnes, ou 16,5 % de celui de trois personnes "
        "(foyer de 3 personnes et plus).\n\n"
        "Simplification MVP (voir modelled_policies.yaml): le statut de logement "
        "n'est pas modélisé; le forfait est appliqué systématiquement (hypothèse "
        "que le foyer perçoit une aide au logement ou est logé à titre gratuit, "
        "cas de la grande majorité des foyers au RSA). Métropole uniquement."
    )
    definition_period = MONTH
    reference = "https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000021666480"

    def formula(famille, period, parameters):
        rsa = parameters(period).gov.cnaf.prestations.rsa
        fl = rsa.forfait_logement
        base = rsa.montant_forfaitaire.base
        majoration_couple = rsa.montant_forfaitaire.majoration_couple

        nb_parents = famille.nb_persons(Famille.PARENT)
        age = famille.members("age", period)
        est_enfant = famille.members.has_role(Famille.ENFANT)
        age_limite = parameters(period).gov.cnaf.prestations.af.age_limite
        nb_enfants = famille.sum(est_enfant & (age >= 0) & (age < age_limite))
        nb_personnes = nb_parents + nb_enfants

        # Montant forfaitaire d'une / deux / trois personnes (échelle R262-1):
        # 1 pers = base ; 2 pers = base × (1 + 0,5) ; 3 pers = base × (1 + 0,5 + 0,3).
        mf_une = base
        mf_deux = base * (1.0 + majoration_couple)
        mf_trois = base * (
            1.0 + majoration_couple + rsa.montant_forfaitaire.majoration_enfant
        )

        return where(
            nb_personnes <= 1,
            fl.une_personne * mf_une,
            where(
                nb_personnes == 2,
                fl.deux_personnes * mf_deux,
                fl.trois_plus_personnes * mf_trois,
            ),
        )
