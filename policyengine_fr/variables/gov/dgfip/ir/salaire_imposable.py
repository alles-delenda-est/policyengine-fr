from policyengine_fr.model_api import *


class salaire_imposable(Variable):
    value_type = float
    entity = Individu
    label = "Salaire imposable après abattement de 10%"
    unit = EUR
    documentation = (
        "Salaire net imposable d'une personne: salaire déclaré (case 1AJ) "
        "diminué de la déduction forfaitaire de 10% pour frais professionnels, "
        "bornée par un plancher et un plafond annuels et limitée au montant du "
        "salaire. La base est le salaire déclaré (`salaire_declare`), c'est-à-dire "
        "le brut net des cotisations salariales et de la CSG déductible."
    )
    definition_period = YEAR
    reference = "https://www.service-public.gouv.fr/particuliers/vosdroits/F1989"

    def formula(individu, period, parameters):
        salaire_declare = individu("salaire_declare", period)
        p = parameters(period).gov.dgfip.ir.abattement_salaires
        # Abattement = 10% du salaire, au moins le plancher, au plus le plafond,
        # et jamais supérieur au salaire lui-même.
        abattement = min_(
            salaire_declare,
            min_(p.plafond, max_(p.taux * salaire_declare, p.plancher)),
        )
        abattement = where(salaire_declare > 0, abattement, 0)
        return salaire_declare - abattement
