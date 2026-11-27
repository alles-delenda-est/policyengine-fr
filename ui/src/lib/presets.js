export const DEFAULT_PATRIMOINE = {
  revenus_capital: 0,
  revenus_fonciers_bruts: 0,
  charges_foncieres_reelles: 0,
  regime_micro_foncier: true,
  plus_values_immobilieres: 0,
  patrimoine_immobilier_residence_principale: 0,
  patrimoine_immobilier_autre: 0,
  taxe_fonciere_locale: 0,
  thrs_locale: 0,
  valeur_terrain_imposable: 0,
  pensions_alimentaires_percues: 0,
  pensions_alimentaires_versees: 0,
}

export const DEFAULT_HOUSEHOLD = {
  couple: false,
  parent_isole: true,
  adults: [
    { age: 32, salaire_brut: 30000, pension_retraite: 0, cadre: false, effectif_entreprise: 10 },
    { age: 32, salaire_brut: 0, pension_retraite: 0, cadre: false, effectif_entreprise: 10 },
  ],
  children: [],
  patrimoine: { ...DEFAULT_PATRIMOINE },
}

export const DEFAULT_REFORMS = {
  lvt_scenario: 'OFF',
  lvt_custom_rate: null,
  ir_rate_change_pct: 0,
  ir_freeze_2024: false,
  csg_delta_pts: 0,
  dp6_underindex_pct: 0,
  dp6_threshold_annual: 24000,
}

export const PRESETS = [
  {
    id: 'smic_seul',
    titre: 'Salarié seul au SMIC',
    badge: '29 ans · 1 767 €/mois',
    resume: 'Réduction générale Fillon maximale + Prime d’activité (~152 €/mois)',
    household: {
      couple: false,
      parent_isole: false,
      adults: [
        { age: 29, salaire_brut: 21203, pension_retraite: 0, cadre: false, effectif_entreprise: 10 },
        { age: 29, salaire_brut: 0, pension_retraite: 0, cadre: false, effectif_entreprise: 10 },
      ],
      children: [],
      patrimoine: { ...DEFAULT_PATRIMOINE },
    },
  },
  {
    id: 'parent_isole_modeste',
    titre: 'Parent isolé, 1 enfant',
    badge: '34 ans · 1 000 €/mois',
    resume: 'Cumul RSA majoré, Prime d’activité, ASF et demi-part case T',
    household: {
      couple: false,
      parent_isole: true,
      adults: [
        { age: 34, salaire_brut: 12000, pension_retraite: 0, cadre: false, effectif_entreprise: 10 },
        { age: 34, salaire_brut: 0, pension_retraite: 0, cadre: false, effectif_entreprise: 10 },
      ],
      children: [{ age: 6 }],
      patrimoine: { ...DEFAULT_PATRIMOINE },
    },
  },
  {
    id: 'couple_classe_moyenne',
    titre: 'Couple, 2 enfants',
    badge: '39 & 37 ans · 3 500 + 2 333 €/mois',
    resume: 'Quotient familial (3 parts), décote et allocations familiales taux plein',
    household: {
      couple: true,
      parent_isole: false,
      adults: [
        { age: 39, salaire_brut: 42000, pension_retraite: 0, cadre: false, effectif_entreprise: 80 },
        { age: 37, salaire_brut: 28000, pension_retraite: 0, cadre: false, effectif_entreprise: 20 },
      ],
      children: [{ age: 8 }, { age: 14 }],
      patrimoine: { ...DEFAULT_PATRIMOINE },
    },
  },
  {
    id: 'cadre_sup',
    titre: 'Cadre supérieur, 2 enfants',
    badge: '44 & 42 ans · 7 917 €/mois',
    resume: 'Tranche 2 AGIRC-ARRCO, CET, APEC et modulation dégressive des AF',
    household: {
      couple: true,
      parent_isole: false,
      adults: [
        { age: 44, salaire_brut: 95000, pension_retraite: 0, cadre: true, effectif_entreprise: 250 },
        { age: 42, salaire_brut: 0, pension_retraite: 0, cadre: false, effectif_entreprise: 10 },
      ],
      children: [{ age: 10 }, { age: 16 }],
      patrimoine: { ...DEFAULT_PATRIMOINE },
    },
  },
  {
    id: 'couple_retraites',
    titre: 'Couple de retraités',
    badge: '69 & 67 ans · 2 667 + 1 333 €/mois',
    resume: 'CSG par tranches de RFR, CASA 0,3 %, abattement 10 % (test idéal D-P6)',
    household: {
      couple: true,
      parent_isole: false,
      adults: [
        { age: 69, salaire_brut: 0, pension_retraite: 32000, cadre: false, effectif_entreprise: 10 },
        { age: 67, salaire_brut: 0, pension_retraite: 16000, cadre: false, effectif_entreprise: 10 },
      ],
      children: [],
      patrimoine: { ...DEFAULT_PATRIMOINE },
    },
  },
  {
    id: 'proprietaire_bailleur',
    titre: 'Propriétaire bailleur',
    badge: '46 ans · Salaires + loyers',
    resume: 'Micro-foncier, PFU, taxe foncière (test idéal réformes LVTShift S1–S3)',
    household: {
      couple: false,
      parent_isole: false,
      adults: [
        { age: 46, salaire_brut: 54000, pension_retraite: 0, cadre: true, effectif_entreprise: 60 },
        { age: 46, salaire_brut: 0, pension_retraite: 0, cadre: false, effectif_entreprise: 10 },
      ],
      children: [],
      patrimoine: {
        ...DEFAULT_PATRIMOINE,
        revenus_capital: 6000,
        revenus_fonciers_bruts: 12000,
        regime_micro_foncier: true,
        taxe_fonciere_locale: 2200,
        thrs_locale: 600,
        valeur_terrain_imposable: 140000,
      },
    },
  },
  {
    id: 'haut_patrimoine_ifi',
    titre: 'Haut patrimoine (IFI & CEHR)',
    badge: '54 & 52 ans · 3,0 M€ immo.',
    resume: 'IFI (abattement RP 30 %), CEHR 3 %/4 %, PFU (test LVTShift S3_IFI)',
    household: {
      couple: true,
      parent_isole: false,
      adults: [
        { age: 54, salaire_brut: 180000, pension_retraite: 0, cadre: true, effectif_entreprise: 500 },
        { age: 52, salaire_brut: 90000, pension_retraite: 0, cadre: true, effectif_entreprise: 500 },
      ],
      children: [{ age: 17 }],
      patrimoine: {
        ...DEFAULT_PATRIMOINE,
        revenus_capital: 80000,
        revenus_fonciers_bruts: 36000,
        charges_foncieres_reelles: 9000,
        regime_micro_foncier: false,
        patrimoine_immobilier_residence_principale: 1800000,
        patrimoine_immobilier_autre: 1200000,
        taxe_fonciere_locale: 5500,
        thrs_locale: 1800,
        valeur_terrain_imposable: 850000,
      },
    },
  },
]

export const LVT_SCENARIOS = [
  {
    id: 'OFF',
    label: 'Inactif (droit courant)',
    ratePct: 0,
    detail: 'Maintien de la taxe foncière, de la THRS, de l’imposition foncière et de l’IFI.',
  },
  {
    id: 'S1',
    label: 'S1 — Remplacement TF + THRS + DMTO (1,10 %)',
    ratePct: 1.1,
    detail: 'Supprime la taxe foncière et la THRS (frais d’État inclus) au profit d’une TVTN à 1,10 %.',
  },
  {
    id: 'S2',
    label: 'S2 — S1 + Plus-values immobilières (1,16 %)',
    ratePct: 1.16,
    detail: 'Ajoute la suppression de l’IR (19 %) et des PS (17,2 %) sur les plus-values immobilières.',
  },
  {
    id: 'S2_IFI',
    label: 'S2_IFI — S2 + Suppression de l’IFI (1,20 %)',
    ratePct: 1.2,
    detail: 'Remplace TF, THRS, plus-values immobilières et IFI par une TVTN nationale à 1,20 %.',
  },
  {
    id: 'S3',
    label: 'S3 — S2 + Revenus fonciers (1,30 %)',
    ratePct: 1.3,
    detail: 'Exonère aussi les loyers nets d’IR et de prélèvements sociaux (hors PFU financier).',
  },
  {
    id: 'S3_IFI',
    label: 'S3_IFI — Basculement foncier intégral + IFI (1,34 %)',
    ratePct: 1.34,
    detail: 'Remplace l’ensemble de la fiscalité immobilière récurrente, locative, de cession et l’IFI.',
  },
]
