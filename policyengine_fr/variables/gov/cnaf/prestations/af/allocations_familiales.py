from policyengine_fr.model_api import *


class allocations_familiales(Variable):
    value_type = float
    entity = Famille
    label = "Allocations familiales"
    unit = EUR
    documentation = (
        "Allocations familiales mensuelles versées par la CAF/MSA à partir de "
        "deux enfants à charge (CSS art. L521-1 et s.). Le montant à taux plein "
        "vaut 0,32 BMAF pour deux enfants, majoré de 0,41 BMAF par enfant "
        "supplémentaire, plus une majoration de 0,16 BMAF par enfant ayant "
        "atteint 14 ans (l'aîné d'une famille de deux enfants n'y ouvre pas "
        "droit). Le montant est ensuite modulé selon les ressources annuelles "
        "(taux plein, moitié ou quart) en fonction de deux plafonds croissant "
        "avec le nombre d'enfants.\n\n"
        "Simplifications MVP: les ressources prises en compte sont la somme des "
        "salaires imposables de l'année courante des membres de la famille (à "
        "la place de la base ressources N-2 réelle); métropole uniquement; "
        "garde alternée, forfait des 20 ans et plancher de versement non "
        "modélisés."
    )
    definition_period = MONTH
    reference = "https://www.service-public.fr/particuliers/vosdroits/F13213"

    def formula(famille, period, parameters):
        af = parameters(period).gov.cnaf.prestations.af
        bmaf = parameters(period).gov.cnaf.bmaf

        age = famille.members("age", period)
        est_enfant = famille.members.has_role(Famille.ENFANT)
        # Enfant à charge ouvrant droit: rôle enfant et âge sous la limite.
        ouvre_droit = est_enfant & (age >= 0) & (age < af.age_limite)
        nb_enfants = famille.sum(ouvre_droit)

        # Montant de base (en BMAF): 0,32 pour deux enfants,
        # + 0,41 par enfant au-delà du deuxième.
        enfants_au_dela_de_deux = max_(nb_enfants - 2, 0)
        taux_base = (
            af.taux.enfant_2 + af.taux.enfant_supplementaire * enfants_au_dela_de_deux
        )
        montant_base = bmaf * taux_base

        # Majoration pour âge (0,16 BMAF par enfant ayant atteint 14 ans).
        # Dans une famille de deux enfants, l'aîné n'ouvre pas droit à la
        # majoration: on en retire un.
        enfant_majore = ouvre_droit & (age >= af.majoration_age.age)
        nb_majores = famille.sum(enfant_majore)
        nb_majores = where(nb_enfants == 2, max_(nb_majores - 1, 0), nb_majores)
        montant_majoration = bmaf * af.majoration_age.taux * nb_majores

        montant_plein = montant_base + montant_majoration

        # Modulation selon les ressources annuelles de la famille.
        ressources = famille.sum(famille.members("salaire_imposable", period.this_year))
        plafond_1 = (
            af.plafonds.tranche_1_base + af.plafonds.majoration_par_enfant * nb_enfants
        )
        plafond_2 = (
            af.plafonds.tranche_2_base + af.plafonds.majoration_par_enfant * nb_enfants
        )
        coefficient = where(
            ressources <= plafond_1,
            af.modulation.tranche_1,
            where(
                ressources <= plafond_2,
                af.modulation.tranche_2,
                af.modulation.tranche_3,
            ),
        )

        # Versées uniquement à partir du nombre d'enfants minimum (2).
        eligible = nb_enfants >= af.nombre_enfants_minimum
        return where(eligible, montant_plein * coefficient, 0)
