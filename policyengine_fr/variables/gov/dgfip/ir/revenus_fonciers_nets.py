from policyengine_fr.model_api import *


class revenus_fonciers_nets(Variable):
    value_type = float
    entity = FoyerFiscal
    label = "Revenus fonciers nets imposables"
    unit = EUR
    documentation = (
        "Revenu foncier net imposable au barème progressif de l'IR et aux "
        "prélèvements sociaux sur les revenus du patrimoine (17,2 %, CGI art. "
        "28 à 32 ; périmètre S3 de LVTShift). Applique l'abattement micro-foncier "
        "de 30 % lorsque `regime_micro_foncier` est vrai et que les recettes "
        "brutes n'excèdent pas 15 000 €, sinon retranche les charges réelles "
        "(borné à zéro hors imputation de déficit foncier)."
    )
    definition_period = YEAR
    reference = "https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000006302323"

    def formula(foyer_fiscal, period, parameters):
        bruts = foyer_fiscal("revenus_fonciers_bruts", period)
        charges = foyer_fiscal("charges_foncieres_reelles", period)
        micro = foyer_fiscal("regime_micro_foncier", period)
        mf = parameters(period).gov.dgfip.ir.micro_foncier

        eligible_micro = micro & (bruts <= mf.plafond)
        net_micro = bruts * (1 - mf.abattement)
        net_reel = max_(bruts - charges, 0)
        return where(eligible_micro, net_micro, net_reel)
