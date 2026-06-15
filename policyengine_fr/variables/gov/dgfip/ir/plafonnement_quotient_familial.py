from policyengine_fr.model_api import *


class plafonnement_quotient_familial(Variable):
    value_type = float
    entity = FoyerFiscal
    label = "Impôt après plafonnement du quotient familial"
    unit = EUR
    documentation = (
        "Impôt sur le revenu après application du plafonnement du quotient "
        "familial (CGI art. 197-I-2). L'avantage en impôt procuré par les "
        "demi-parts excédant le nombre de parts de base (1 part pour un "
        "déclarant seul, 2 parts pour un couple) est plafonné: il ne peut "
        "dépasser un montant fixe par demi-part supplémentaire. L'impôt "
        "résultant est donc le maximum entre l'impôt brut (avantage QF intégral) "
        "et l'impôt calculé sur les parts de base diminué de l'avantage maximal "
        "autorisé. Pour un parent isolé (case T), les deux premières demi-parts "
        "excédant une part bénéficient d'un plafond majoré. Hors champ pour "
        "l'instant: réduction d'impôt complémentaire (invalidité, veuf), cas DOM."
    )
    definition_period = YEAR
    reference = "https://www.service-public.fr/particuliers/vosdroits/F1419"

    def formula(foyer_fiscal, period, parameters):
        rni = foyer_fiscal("revenu_net_imposable", period)
        parts = foyer_fiscal("nombre_parts", period)
        nb_declarants = foyer_fiscal.nb_persons(FoyerFiscal.DECLARANT)
        nb_pac = foyer_fiscal.nb_persons(FoyerFiscal.PERSONNE_A_CHARGE)
        parent_isole = foyer_fiscal("parent_isole", period)
        impot_brut = foyer_fiscal("impot_brut", period)

        bareme = parameters(period).gov.dgfip.ir.bareme
        plafond = parameters(period).gov.dgfip.ir.plafond_quotient_familial

        # Impôt calculé sur le nombre de parts "de base", sans avantage tiré
        # des personnes à charge: 1 part pour un déclarant seul, 2 pour un couple.
        parts_base = max_(nb_declarants, 1)
        impot_sans_qf = bareme.calc(rni / parts_base) * parts_base

        # Demi-parts excédant les parts de base (chacune plafonnée).
        demi_parts_sup = (parts - parts_base) * 2
        # Parent isolé (case T): les deux premières demi-parts au-delà d'une
        # part (la part entière du premier enfant) ouvrent droit au plafond
        # majoré "celib_enf"; les suivantes au plafond général.
        demi_parts_celib_enf = min_((parts - 1) * 2, 2)
        condition_isole = parent_isole & (nb_pac >= 1)

        avantage_max_general = plafond.general * demi_parts_sup
        avantage_max_isole = (
            plafond.celib_enf * demi_parts_celib_enf / 2
            + plafond.general * (demi_parts_sup - demi_parts_celib_enf)
        )
        avantage_max = where(condition_isole, avantage_max_isole, avantage_max_general)

        # Plancher d'impôt: impôt sans QF diminué de l'avantage maximal autorisé.
        plancher = max_(0, impot_sans_qf - avantage_max)
        return max_(impot_brut, plancher)
