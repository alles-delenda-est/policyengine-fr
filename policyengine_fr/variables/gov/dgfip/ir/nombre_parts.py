from policyengine_fr.model_api import *


class nombre_parts(Variable):
    value_type = float
    entity = FoyerFiscal
    label = "Nombre de parts (quotient familial)"
    documentation = (
        "Nombre de parts du foyer fiscal (quotient familial). MVP: une part par "
        "déclarant; une demi-part pour chacune des deux premières personnes à "
        "charge, une part entière à partir de la troisième; majoration d'une "
        "demi-part pour parent isolé (case T). Hors champ pour l'instant: "
        "majorations invalidité, anciens combattants, garde alternée, etc."
    )
    definition_period = YEAR
    reference = "https://www.service-public.gouv.fr/particuliers/vosdroits/F2705"

    def formula(foyer_fiscal, period, parameters):
        nb_declarants = foyer_fiscal.nb_persons(FoyerFiscal.DECLARANT)
        nb_pac = foyer_fiscal.nb_persons(FoyerFiscal.PERSONNE_A_CHARGE)
        parent_isole = foyer_fiscal("parent_isole", period)
        # CGI art. 194: 0,5 part pour chacune des deux premières PAC,
        # 1 part entière à partir de la troisième.
        parts_pac = 0.5 * min_(nb_pac, 2) + max_(nb_pac - 2, 0)
        # CGI art. 194 II: +0,5 part pour parent isolé ayant au moins une PAC.
        majoration_parent_isole = where(parent_isole & (nb_pac >= 1), 0.5, 0)
        return nb_declarants + parts_pac + majoration_parent_isole
