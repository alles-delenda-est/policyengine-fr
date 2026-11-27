from policyengine_fr.model_api import *


class revenus_capital(Variable):
    value_type = float
    entity = Individu
    label = "Revenus de capitaux mobiliers et plus-values mobilières (assiette PFU)"
    unit = EUR
    documentation = (
        "Revenus financiers annuels bruts soumis de plein droit au prélèvement "
        "forfaitaire unique (PFU / flat tax : 12,8 % d'IR + 17,2 % de "
        "prélèvements sociaux = 30 %, CGI art. 200 A) : dividendes, intérêts "
        "et plus-values de cession de valeurs mobilières."
    )
    definition_period = YEAR


class revenus_fonciers_bruts(Variable):
    value_type = float
    entity = FoyerFiscal
    label = "Revenus fonciers bruts (loyers hors charges)"
    unit = EUR
    documentation = (
        "Recettes locatives annuelles brutes issues de la location nue du "
        "foyer fiscal (CGI art. 14 à 33 quinquies ; périmètre S3 de LVTShift)."
    )
    definition_period = YEAR


class charges_foncieres_reelles(Variable):
    value_type = float
    entity = FoyerFiscal
    label = "Charges foncières déductibles au régime réel"
    unit = EUR
    documentation = (
        "Charges foncières déductibles au régime réel d'imposition des revenus "
        "fonciers (CGI art. 31 : travaux, frais de gestion, intérêts d'emprunt, "
        "taxe foncière)."
    )
    definition_period = YEAR


class regime_micro_foncier(Variable):
    value_type = bool
    entity = FoyerFiscal
    label = "Application du régime micro-foncier (abattement de 30 % jusqu'à 15 000 €)"
    default_value = True
    documentation = (
        "Indique si le foyer relève de plein droit du régime micro-foncier "
        "(abattement forfaitaire de 30 % lorsque les recettes locatives brutes "
        "n'excèdent pas 15 000 €, CGI art. 32), sauf option pour le régime réel."
    )
    definition_period = YEAR


class plus_values_immobilieres(Variable):
    value_type = float
    entity = FoyerFiscal
    label = "Plus-values immobilières imposables (nettes d'abattement pour durée de détention)"
    unit = EUR
    documentation = (
        "Plus-values immobilières nettes imposables réalisées par le foyer "
        "fiscal hors résidence principale (CGI art. 150 U à 150 VH ; périmètre "
        "S2 de LVTShift), soumises au taux forfaitaire d'IR de 19 % et aux "
        "prélèvements sociaux de 17,2 %."
    )
    definition_period = YEAR


class patrimoine_immobilier_residence_principale(Variable):
    value_type = float
    entity = FoyerFiscal
    label = "Valeur vénale nette de la résidence principale (assiette IFI avant abattement de 30 %)"
    unit = EUR
    documentation = (
        "Valeur vénale nette (dettes déductibles retranchées) de la résidence "
        "principale du foyer au 1er janvier, avant application de l'abattement "
        "légal de 30 % de l'article 973 I du CGI."
    )
    definition_period = YEAR


class patrimoine_immobilier_autre(Variable):
    value_type = float
    entity = FoyerFiscal
    label = "Autre patrimoine immobilier net imposable à l'IFI"
    unit = EUR
    documentation = (
        "Valeur nette taxable au 1er janvier des biens et droits immobiliers "
        "du foyer autres que la résidence principale (CGI art. 965)."
    )
    definition_period = YEAR


class taxe_fonciere_locale(Variable):
    value_type = float
    entity = Menage
    label = "Taxe foncière locale (parts commune, EPCI et syndicats, hors frais d'État)"
    unit = EUR
    documentation = (
        "Montant annuel des cotisations locales de taxe foncière (TFPB/TFPNB : "
        "commune, intercommunalité, syndicats, GEMAPI) acquittées par le "
        "ménage propriétaire avant application des frais de gestion de l'État "
        "de 3 % (CGI art. 1641 ; périmètre S1 de LVTShift)."
    )
    definition_period = YEAR


class thrs_locale(Variable):
    value_type = float
    entity = Menage
    label = "Taxe d'habitation sur les résidences secondaires (parts locales, hors frais d'État)"
    unit = EUR
    documentation = (
        "Montant annuel local de la taxe d'habitation sur les résidences "
        "secondaires (commune, EPCI, majoration zone tendue art. 1407 ter CGI) "
        "avant les frais de gestion de l'État de 3 % (périmètre S1 de LVTShift)."
    )
    definition_period = YEAR


class valeur_terrain_imposable(Variable):
    value_type = float
    entity = Menage
    label = "Valeur vénale du terrain nu imposable du ménage (assiette LVT / TVTN)"
    unit = EUR
    documentation = (
        "Valeur vénale du foncier bâti et constructible détenu par le ménage "
        "(hors terres agricoles et naturelles exonérées, décision D6 de "
        "LVTShift). Sert d'assiette à `taxe_valeur_sol` dans les réformes de "
        "remplacement à rendement égal S1 à S3_IFI."
    )
    definition_period = YEAR
