from policyengine_fr.model_api import *


class pensions_imposables(Variable):
    value_type = float
    entity = FoyerFiscal
    label = "Pensions imposables (retraite + alimentaires, abattement de 10% mutualisé)"
    unit = EUR
    documentation = (
        "Total des pensions imposables du foyer après l'abattement de 10 % sur "
        "les pensions (CGI art. 158, 5, a), MUTUALISÉ entre pensions de retraite "
        "et pensions alimentaires perçues (spec 0005). L'abattement a un plancher "
        "par bénéficiaire (borné à sa propre pension) et un plafond unique au "
        "niveau du foyer fiscal, communs à l'ensemble des pensions — ce qui "
        "corrige le risque de double comptage du plancher/plafond signalé tant "
        "que seules les pensions alimentaires étaient couvertes.\n\n"
        "La pension de retraite entre pour son montant déclaré "
        "(`pension_retraite_declaree`, net de CSG déductible) ; les pensions "
        "alimentaires perçues pour leur montant brut."
    )
    definition_period = YEAR
    reference = "https://www.service-public.gouv.fr/particuliers/vosdroits/F415"

    def formula(foyer_fiscal, period, parameters):
        retraite_i = foyer_fiscal.members("pension_retraite_declaree", period)
        alimentaire_i = foyer_fiscal.members("pensions_alimentaires_percues", period)
        pension_i = retraite_i + alimentaire_i
        p = parameters(period).gov.dgfip.ir.abattement_pensions
        # Abattement par bénéficiaire: 10% de sa pension totale, au moins le
        # plancher, jamais supérieur à la pension elle-même.
        abattement_i = where(
            pension_i > 0,
            min_(pension_i, max_(p.taux * pension_i, p.plancher)),
            0,
        )
        # Plancher par bénéficiaire (ci-dessus), plafond unique au foyer.
        abattement = min_(p.plafond, foyer_fiscal.sum(abattement_i))
        return max_(foyer_fiscal.sum(pension_i) - abattement, 0)
