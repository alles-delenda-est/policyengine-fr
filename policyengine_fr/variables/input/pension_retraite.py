from policyengine_fr.model_api import *


class pension_retraite(Variable):
    value_type = float
    entity = Individu
    label = "Pension de retraite annuelle (brute)"
    unit = EUR
    documentation = (
        "Pension de retraite annuelle brute perçue par la personne (avant CSG/CRDS "
        "et avant l'abattement de 10 % sur les pensions). Revenu de remplacement "
        "imposable (spec 0005). La CSG/CRDS applicable est à taux réduit selon le "
        "revenu fiscal de référence (spec 0006)."
    )
    definition_period = YEAR
