from policyengine_fr.model_api import *


class pensions_alimentaires_versees(Variable):
    value_type = float
    entity = FoyerFiscal
    label = "Pensions alimentaires versées (déductibles du revenu global)"
    unit = EUR
    documentation = (
        "Montant total des pensions alimentaires versées par le foyer fiscal et "
        "déductibles du revenu global (CGI art. 156, II, 2°). Le montant est pris "
        "comme déjà déductible: le plafond par enfant majeur n'est pas appliqué "
        "ici (cf. modelled_policies.yaml), à l'image de openfisca-france qui "
        "retient les montants déclarés."
    )
    definition_period = YEAR
    reference = "https://www.service-public.gouv.fr/particuliers/vosdroits/F18526"
