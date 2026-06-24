from policyengine_fr.model_api import *


class pensions_alimentaires_imposables(Variable):
    value_type = float
    entity = FoyerFiscal
    label = "Pensions alimentaires perçues imposables (après abattement de 10%)"
    unit = EUR
    documentation = (
        "Pensions alimentaires perçues par les membres du foyer fiscal, nettes de "
        "l'abattement de 10% sur les pensions (CGI art. 158, 5, a). L'abattement "
        "vaut 10% des pensions, avec un plancher par bénéficiaire (borné à sa "
        "propre pension) et un plafond appliqué au total du foyer fiscal."
    )
    definition_period = YEAR
    reference = "https://www.service-public.gouv.fr/particuliers/vosdroits/F415"

    def formula(foyer_fiscal, period, parameters):
        percue_i = foyer_fiscal.members("pensions_alimentaires_percues", period)
        p = parameters(period).gov.dgfip.ir.abattement_pensions
        # Abattement par bénéficiaire: 10% de sa pension, au moins le plancher,
        # jamais supérieur à la pension elle-même.
        abattement_i = where(
            percue_i > 0,
            min_(percue_i, max_(p.taux * percue_i, p.plancher)),
            0,
        )
        # Le plafond s'apprécie au niveau du foyer fiscal.
        abattement = min_(p.plafond, foyer_fiscal.sum(abattement_i))
        return foyer_fiscal.sum(percue_i) - abattement
