from policyengine_fr.model_api import *


class salaire_brut(Variable):
    value_type = float
    entity = Individu
    label = "Salaire brut imposable"
    unit = EUR
    documentation = (
        "Revenu d'activité salariée annuel déclaré (avant déduction forfaitaire "
        "de 10% pour frais professionnels).\n\n"
        "Attention à la convention d'entrée (simplification MVP, voir "
        "modelled_policies.yaml): la chaîne impôt sur le revenu traite ce "
        "montant comme le salaire DÉCLARÉ (case 1AJ — net de cotisations "
        "sociales et de CSG déductible; c'est la convention sous laquelle le "
        "modèle a été validé à l'euro près face au simulateur DGFiP), tandis "
        "que les formules CSG/CRDS le traitent comme un salaire BRUT "
        "(l'abattement d'assiette de 1,75 % de l'art. L136-2 CSS s'applique au "
        "brut). Ces deux lectures diffèrent d'environ 20-25 % sur une fiche de "
        "paie réelle; tant que les cotisations salariales ne sont pas "
        "modélisées, saisir le salaire déclaré donne un IR exact et une "
        "CSG/CRDS sous-estimée."
    )
    definition_period = YEAR
