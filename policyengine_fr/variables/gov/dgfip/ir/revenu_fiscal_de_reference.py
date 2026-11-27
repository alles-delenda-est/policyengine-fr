from policyengine_fr.model_api import *


def compute_revenu_fiscal_de_reference(
    foyer_fiscal,
    period,
    parameters,
    *,
    pension_var: str = "pension_retraite",
    deduct_foncier_csg: bool = True,
):
    """Shared RFR formula parameterized for base simulation and reforms (D-P6 / LVT S3)."""
    salaires = foyer_fiscal.sum(foyer_fiscal.members("salaire_imposable", period))
    p = parameters(period).gov.dgfip.ir.abattement_pensions
    pension_i = foyer_fiscal.members(pension_var, period) + foyer_fiscal.members(
        "pensions_alimentaires_percues", period
    )
    abattement_i = where(
        pension_i > 0,
        min_(pension_i, max_(p.taux * pension_i, p.plancher)),
        0,
    )
    abattement = min_(p.plafond, foyer_fiscal.sum(abattement_i))
    pensions_abattues = max_(foyer_fiscal.sum(pension_i) - abattement, 0)

    foncier_net = foyer_fiscal("revenus_fonciers_nets", period)
    if deduct_foncier_csg:
        taux_csg_ded_pat = parameters(
            period
        ).gov.urssaf.patrimoine.csg_deductible_bareme
        csg_ded_foncier = foncier_net * taux_csg_ded_pat
    else:
        csg_ded_foncier = 0

    capital = foyer_fiscal.sum(foyer_fiscal.members("revenus_capital", period))
    plus_values = foyer_fiscal("plus_values_immobilieres", period)
    versees = foyer_fiscal("pensions_alimentaires_versees", period)
    return max_(
        salaires
        + pensions_abattues
        + foncier_net
        - csg_ded_foncier
        + capital
        + plus_values
        - versees,
        0,
    )


class revenu_fiscal_de_reference(Variable):
    value_type = float
    entity = FoyerFiscal
    label = "Revenu fiscal de référence (proxy périmètre modélisé)"
    unit = EUR
    documentation = (
        "Proxy du revenu fiscal de référence (RFR, CGI art. 1417 IV) du foyer "
        "fiscal sur le périmètre modélisé : additionne les salaires imposables, "
        "les pensions de retraite et pensions alimentaires perçues après "
        "l'abattement mutualisé de 10 % plafonné et assorti du plancher par "
        "bénéficiaire (CGI art. 158, 5, a — évalué sur `pension_retraite` brute "
        "de CSG déductible afin d'éviter toute circularité en année courante N "
        "avec `taux_csg_pension`), les revenus fonciers nets diminués de leur "
        "CSG déductible (6,8 %, CGI art. 154 quinquies II), ainsi que les "
        "revenus financiers soumis au PFU (`revenus_capital`) et les "
        "plus-values immobilières imposées à taux forfaitaire "
        "(`plus_values_immobilieres`), réintégrés au RFR en application du CGI "
        "art. 1417 IV, 1° c, sous déduction des `pensions_alimentaires_versees`."
    )
    definition_period = YEAR
    reference = "https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000048769395"

    def formula(foyer_fiscal, period, parameters):
        return compute_revenu_fiscal_de_reference(foyer_fiscal, period, parameters)
