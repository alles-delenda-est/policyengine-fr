from policyengine_fr.model_api import *


class cehr(Variable):
    value_type = float
    entity = FoyerFiscal
    label = "Contribution exceptionnelle sur les hauts revenus (CEHR)"
    unit = EUR
    documentation = (
        "Contribution exceptionnelle sur les hauts revenus (CGI art. 223 "
        "sexies, alignée sur le coin marginal supérieur de `budget_fr_sim_test` "
        "`src/engine/ir-tranches.js`) : barème progressif appliqué au revenu "
        "fiscal de référence — 3 % de 250 k€ à 500 k€ et 4 % au-delà pour un "
        "déclarant seul ; 3 % de 500 k€ à 1 M€ et 4 % au-delà pour un couple "
        "soumis à imposition commune. Hors lissage interannuel (II de l'art. "
        "223 sexies, modèle statique mono-période)."
    )
    definition_period = YEAR
    reference = "https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000025049309"

    def formula(foyer_fiscal, period, parameters):
        rfr = foyer_fiscal("revenu_fiscal_de_reference", period)
        nb_declarants = foyer_fiscal.nb_persons(FoyerFiscal.DECLARANT)
        p = parameters(period).gov.dgfip.cehr
        return where(
            nb_declarants >= 2,
            p.bareme_couple.calc(rfr),
            p.bareme_celibataire.calc(rfr),
        )


class pfu_ir(Variable):
    value_type = float
    entity = FoyerFiscal
    label = "Prélèvement forfaitaire unique — part impôt sur le revenu (12,8 %)"
    unit = EUR
    documentation = (
        "Part impôt sur le revenu (12,8 %, CGI art. 200 A) du prélèvement "
        "forfaitaire unique sur les revenus de capitaux mobiliers et "
        "plus-values mobilières (`revenus_capital`). Les prélèvements sociaux "
        "de 17,2 % sont comptabilisés dans `prelevements_sociaux_patrimoine`."
    )
    definition_period = YEAR
    reference = "https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000036386538"

    def formula(foyer_fiscal, period, parameters):
        capital = foyer_fiscal.sum(foyer_fiscal.members("revenus_capital", period))
        taux = parameters(period).gov.dgfip.pfu.taux_ir
        return capital * taux


class impot_plus_values_immobilieres(Variable):
    value_type = float
    entity = FoyerFiscal
    label = "Impôt sur le revenu forfaitaire sur les plus-values immobilières (19 %)"
    unit = EUR
    documentation = (
        "Impôt sur le revenu forfaitaire au taux de 19 % (CGI art. 200 B ; "
        "ligne `gains_ir` du scénario S2 de LVTShift) sur les plus-values "
        "immobilières imposables des particuliers. Hors surtaxe de l'article "
        "1609 nonies G."
    )
    definition_period = YEAR
    reference = "https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000025049174"

    def formula(foyer_fiscal, period, parameters):
        pv = foyer_fiscal("plus_values_immobilieres", period)
        taux = parameters(period).gov.dgfip.plus_values_immobilieres.taux_ir
        return pv * taux


class prelevements_sociaux_patrimoine(Variable):
    value_type = float
    entity = FoyerFiscal
    label = "Prélèvements sociaux sur les revenus du patrimoine et du capital (17,2 %)"
    unit = EUR
    documentation = (
        "Prélèvements sociaux au taux global de 17,2 % (CSG 9,2 % + CRDS "
        "0,5 % + prélèvement de solidarité 7,5 %, CSS art. L136-6/L136-7 et "
        "CGI art. 235 ter) sur les revenus du capital financier, les revenus "
        "fonciers nets et les plus-values immobilières imposables (lignes "
        "`gains_ps` et `rents_ps + rents_csg` de LVTShift)."
    )
    definition_period = YEAR
    reference = "https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000037947692"

    def formula(foyer_fiscal, period, parameters):
        capital = foyer_fiscal.sum(foyer_fiscal.members("revenus_capital", period))
        foncier = foyer_fiscal("revenus_fonciers_nets", period)
        pv = foyer_fiscal("plus_values_immobilieres", period)
        taux = parameters(period).gov.urssaf.patrimoine.taux_global
        return (capital + foncier + pv) * taux


class ifi(Variable):
    value_type = float
    entity = FoyerFiscal
    label = "Impôt sur la fortune immobilière (IFI)"
    unit = EUR
    documentation = (
        "Impôt sur la fortune immobilière (CGI art. 964 à 977 ; ligne `ifi` "
        "des scénarios S2_IFI et S3_IFI de LVTShift). Assiette égale à la "
        "résidence principale après abattement de 30 % (art. 973 I) augmentée "
        "des autres biens immobiliers nets ; assujettissement dès 1 300 000 €, "
        "barème progressif dès 800 000 € (0,50 % à 1,50 %), et décote "
        "`17 500 − 1,25 % × assiette` entre 1,3 M€ et 1,4 M€ (art. 977 II). "
        "Hors plafonnement IFI à 75 % des revenus (art. 979)."
    )
    definition_period = YEAR
    reference = "https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000036385056"

    def formula(foyer_fiscal, period, parameters):
        rp = foyer_fiscal("patrimoine_immobilier_residence_principale", period)
        autre = foyer_fiscal("patrimoine_immobilier_autre", period)
        p = parameters(period).gov.dgfip.ifi

        assiette = rp * (1 - p.abattement_residence_principale) + autre
        brut = p.bareme.calc(assiette)
        decote = where(
            (assiette >= p.seuil_imposition) & (assiette < p.decote_seuil),
            max_(p.decote_base - p.decote_taux * assiette, 0),
            0,
        )
        return where(assiette >= p.seuil_imposition, max_(brut - decote, 0), 0)
