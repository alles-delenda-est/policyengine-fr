from policyengine_fr.model_api import *


class revenu_fiscal_de_reference(Variable):
    value_type = float
    entity = FoyerFiscal
    label = "Revenu fiscal de référence (proxy MVP)"
    unit = EUR
    documentation = (
        "Proxy du revenu fiscal de référence (RFR) du foyer, utilisé pour "
        "déterminer le taux de CSG sur les pensions de retraite (spec 0006).\n\n"
        "Simplifications MVP (voir modelled_policies.yaml): le RFR légal réintègre "
        "de nombreux revenus et abattements que le MVP ne modélise pas ; on utilise "
        "ici une approximation = salaires imposables + pensions (retraite et "
        "alimentaires perçues, abattues de 10 %) − pensions alimentaires versées. "
        "De plus, le taux de CSG sur pension dépend légalement du RFR de l'année "
        "N-2 ; le modèle étant mono-année, on utilise le RFR de l'année courante "
        "(même simplification N-vs-N-2 que la base ressources des AF). Ce proxy "
        "est calculé indépendamment de la CSG déductible pour éviter toute "
        "circularité."
    )
    definition_period = YEAR

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
        versees = foyer_fiscal("pensions_alimentaires_versees", period)
        return max_(salaires + pensions_abattues - versees, 0)
