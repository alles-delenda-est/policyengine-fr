from policyengine_fr.model_api import *


class taxe_fonciere(Variable):
    value_type = float
    entity = Menage
    label = "Taxe foncière totale acquittée par le ménage (frais d'État de 3 % inclus)"
    unit = EUR
    documentation = (
        "Avis total de taxe foncière du ménage : parts locales (`taxe_fonciere_locale`) "
        "majorées des frais de gestion, de dégrèvement et de non-valeurs de "
        "l'État au taux de 3 % (CGI art. 1641 ; lignes `tfpb` + `tfpnb` + "
        "`tf_etat` du scénario S1 de LVTShift)."
    )
    definition_period = YEAR
    reference = "https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000053546093"

    def formula(menage, period, parameters):
        locale = menage("taxe_fonciere_locale", period)
        frais = parameters(period).gov.dgfip.fiscalite_locale.frais_gestion_etat
        return locale * (1 + frais)


class taxe_habitation_residence_secondaire(Variable):
    value_type = float
    entity = Menage
    label = (
        "Taxe d'habitation sur les résidences secondaires (frais d'État de 3 % inclus)"
    )
    unit = EUR
    documentation = (
        "Avis total de taxe d'habitation sur les résidences secondaires du "
        "ménage : parts locales (`thrs_locale`) majorées des frais de gestion "
        "de l'État de 3 % (CGI art. 1641 ; lignes `thrs` + `thrs_etat` du "
        "scénario S1 de LVTShift)."
    )
    definition_period = YEAR
    reference = "https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000053546093"

    def formula(menage, period, parameters):
        locale = menage("thrs_locale", period)
        frais = parameters(period).gov.dgfip.fiscalite_locale.frais_gestion_etat
        return locale * (1 + frais)


class taxe_valeur_sol(Variable):
    value_type = float
    entity = Menage
    label = "Taxe sur la valeur du terrain nu (LVT / TVTN)"
    unit = EUR
    documentation = (
        "Taxe annuelle sur la valeur vénale du terrain nu imposable du ménage "
        "(`valeur_terrain_imposable × taux_lvt_national`). Nulle en droit "
        "courant (taux = 0) ; activée par les réformes de remplacement à "
        "rendement égal de `policyengine_fr.reforms.lvt_shift` réutilisant "
        "les taux calibrés de `LVTShift` (`yields.json`)."
    )
    definition_period = YEAR
    reference = "https://github.com/alles-delenda-est/LVTShift"

    def formula(menage, period, parameters):
        terrain = menage("valeur_terrain_imposable", period)
        taux = parameters(period).gov.dgfip.fiscalite_locale.taux_lvt_national
        return terrain * taux
