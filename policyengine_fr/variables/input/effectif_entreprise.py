from policyengine_fr.model_api import *


class effectif_entreprise(Variable):
    value_type = int
    entity = Individu
    label = "Effectif de l'entreprise employeur"
    default_value = 10
    documentation = (
        "Effectif salarié de l'entreprise employeur. Détermine le taux du FNAL "
        "(0,10 % plafonné au PASS en dessous de 50 salariés, 0,50 % déplafonné "
        "à partir de 50 salariés) et le paramètre maximal T de la réduction "
        "générale des cotisations patronales (0,3194 en dessous de 50 salariés, "
        "0,3234 à partir de 50 salariés en 2024). Défaut MVP : 10 (< 50)."
    )
    definition_period = YEAR
