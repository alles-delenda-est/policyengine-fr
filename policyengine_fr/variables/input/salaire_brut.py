from policyengine_fr.model_api import *


class salaire_brut(Variable):
    value_type = float
    entity = Individu
    label = "Salaire brut"
    unit = EUR
    documentation = (
        "Revenu d'activité salariée annuel BRUT (avant cotisations sociales "
        "salariales, CSG/CRDS et impôt).\n\n"
        "Convention d'entrée: salaire brut réel. Le modèle en dérive le salaire "
        "déclaré (`salaire_declare` = brut − cotisations salariales − CSG "
        "déductible), sur lequel la chaîne impôt sur le revenu applique "
        "l'abattement de 10 %; la CSG/CRDS est assise sur 98,25 % du brut "
        "(art. L136-2 CSS). Les cotisations salariales sont calculées par risque "
        "avec plafonds (voir `cotisations_salariales`)."
    )
    definition_period = YEAR
