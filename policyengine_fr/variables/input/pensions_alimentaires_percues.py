from policyengine_fr.model_api import *


class pensions_alimentaires_percues(Variable):
    value_type = float
    entity = Individu
    label = "Pensions alimentaires perçues (imposables)"
    unit = EUR
    documentation = (
        "Montant annuel des pensions alimentaires perçues par une personne. "
        "Imposable dans la catégorie des pensions et bénéficiant de l'abattement "
        "de 10% (CGI art. 158, 5, a). Le plancher de l'abattement s'applique par "
        "bénéficiaire, son plafond au niveau du foyer fiscal."
    )
    definition_period = YEAR
    reference = "https://www.service-public.gouv.fr/particuliers/vosdroits/F18526"
