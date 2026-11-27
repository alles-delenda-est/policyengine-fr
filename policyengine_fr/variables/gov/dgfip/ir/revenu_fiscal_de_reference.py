from policyengine_fr.model_api import *


class revenu_fiscal_de_reference(Variable):
    value_type = float
    entity = FoyerFiscal
    label = "Revenu fiscal de référence (proxy MVP élargi)"
    unit = EUR
    documentation = (
        "Proxy du revenu fiscal de référence (RFR, CGI art. 1417 IV) du foyer "
        "fiscal : réunit le revenu imposable d'activité et de pensions "
        "(calculé avant CSG déductible sur pension pour éviter toute "
        "circularité), les revenus fonciers nets, ainsi que les revenus de "
        "capitaux mobiliers soumis au PFU et les plus-values immobilières "
        "imposées à taux forfaitaire (réintégrés au RFR en application du "
        "CGI art. 1417 IV, 1° c). Sert d'assiette à la CEHR (CGI art. 223 "
        "sexies, repris de `budget_fr_sim_test`) et de critère de taux CSG sur "
        "les pensions de retraite (spec 0006)."
    )
    definition_period = YEAR
    reference = "https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000048769395"

    def formula(foyer_fiscal, period, parameters):
        salaires = foyer_fiscal.sum(foyer_fiscal.members("salaire_imposable", period))
        p = parameters(period).gov.dgfip.ir.abattement_pensions
        pension_retraite = foyer_fiscal.sum(
            foyer_fiscal.members("pension_retraite", period)
        )
        pensions_alimentaires = foyer_fiscal.sum(
            foyer_fiscal.members("pensions_alimentaires_percues", period)
        )
        pensions_abattues = (pension_retraite + pensions_alimentaires) * (1 - p.taux)
        foncier_net = foyer_fiscal("revenus_fonciers_nets", period)
        capital = foyer_fiscal.sum(foyer_fiscal.members("revenus_capital", period))
        plus_values = foyer_fiscal("plus_values_immobilieres", period)
        versees = foyer_fiscal("pensions_alimentaires_versees", period)
        return max_(
            salaires
            + pensions_abattues
            + foncier_net
            + capital
            + plus_values
            - versees,
            0,
        )
