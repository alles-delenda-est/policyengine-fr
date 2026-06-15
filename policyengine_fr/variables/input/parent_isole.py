from policyengine_fr.model_api import *


class parent_isole(Variable):
    value_type = bool
    entity = FoyerFiscal
    label = "Parent isolé (case T)"
    documentation = (
        "Le déclarant vit seul et assume seul la charge d'au moins une personne "
        "à charge (case T de la déclaration), ouvrant droit à une majoration de "
        "0,5 part."
    )
    definition_period = YEAR
