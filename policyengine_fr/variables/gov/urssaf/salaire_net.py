from policyengine_fr.model_api import *


class salaire_net(Variable):
    value_type = float
    entity = Individu
    label = "Salaire net à payer avant impôt sur le revenu"
    unit = EUR
    documentation = (
        "Salaire annuel net des cotisations sociales salariales et de la "
        "totalité de la CSG (déductible et imposable) et de la CRDS:\n\n"
        "    salaire_net = salaire_brut − cotisations_salariales − csg − crds\n\n"
        "Correspond au « net à payer avant impôt sur le revenu » du bulletin "
        "de paie (égal à `salaire_declare − csg_imposable − crds`). Sert de "
        "base de ressources d'activité pour les prestations sous conditions de "
        "ressources mensuelles (RSA, prime d'activité), conformément aux "
        "articles R262-6 CASF et R844-1 CSS."
    )
    definition_period = YEAR
    reference = "https://www.service-public.fr/particuliers/vosdroits/F2302"

    def formula(individu, period, parameters):
        salaire_brut = individu("salaire_brut", period)
        cotisations = individu("cotisations_salariales", period)
        csg = individu("csg", period)
        crds = individu("crds", period)
        return max_(salaire_brut - cotisations - csg - crds, 0)
