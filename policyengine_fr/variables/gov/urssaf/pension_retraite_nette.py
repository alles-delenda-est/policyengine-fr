from policyengine_fr.model_api import *


class pension_retraite_nette(Variable):
    value_type = float
    entity = Individu
    label = "Pension de retraite nette de prélèvements sociaux"
    unit = EUR
    documentation = (
        "Pension de retraite annuelle nette de CSG, de CRDS et de CASA :\n\n"
        "    pension_retraite_nette = pension_retraite − csg_retraite "
        "− crds_retraite − casa_retraite\n\n"
        "Correspond au montant net perçu avant impôt sur le revenu et entre "
        "dans la base ressources des prestations sous conditions de ressources "
        "(RSA, prime d'activité) ainsi que dans `revenu_disponible`."
    )
    definition_period = YEAR
    reference = "https://www.service-public.fr/particuliers/vosdroits/F2971"

    def formula(individu, period, parameters):
        pension = individu("pension_retraite", period)
        csg = individu("csg_retraite", period)
        crds = individu("crds_retraite", period)
        casa = individu("casa_retraite", period)
        return max_(pension - csg - crds - casa, 0)
