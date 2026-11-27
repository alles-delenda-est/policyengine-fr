export const LEDGER_ROWS = [
  // 1. Coût du travail & fiche de paie
  { section: '1. Coût du travail & fiche de paie', key: 'cout_employeur_net', label: 'Coût total employeur (super-brut net d’allègements)', highlight: true },
  { section: '1. Coût du travail & fiche de paie', key: 'cotisations_patronales', label: 'Cotisations patronales brutes', varMeta: 'cotisations_patronales' },
  { section: '1. Coût du travail & fiche de paie', key: 'reduction_generale', label: 'dont Réduction générale dégressive (ex-Fillon)', varMeta: 'reduction_generale', sign: 'deduction' },
  { section: '1. Coût du travail & fiche de paie', key: 'salaire_brut', label: 'Salaire brut total', varMeta: 'salaire_brut', highlight: true },
  { section: '1. Coût du travail & fiche de paie', key: 'cotisations_salariales', label: 'Cotisations sociales salariales (retraite, AGIRC-ARRCO, CET, APEC)', varMeta: 'cotisations_salariales', sign: 'levy' },
  { section: '1. Coût du travail & fiche de paie', key: 'csg', label: 'CSG sur revenus d’activité (9,2 % sur 98,25 %)', varMeta: 'csg', sign: 'levy' },
  { section: '1. Coût du travail & fiche de paie', key: 'crds', label: 'CRDS sur revenus d’activité (0,5 % sur 98,25 %)', varMeta: 'crds', sign: 'levy' },
  { section: '1. Coût du travail & fiche de paie', key: 'salaire_declare', label: 'Salaire net imposable déclaré (case 1AJ)', varMeta: 'salaire_declare' },
  { section: '1. Coût du travail & fiche de paie', key: 'salaire_net', label: 'Salaire net à payer avant impôt sur le revenu', varMeta: 'salaire_net', highlight: true },

  // 2. Pensions de retraite & pensions alimentaires
  { section: '2. Retraites & pensions alimentaires', key: 'pension_retraite_effective', label: 'Pension de retraite brute (effective)', varMeta: 'pension_retraite' },
  { section: '2. Retraites & pensions alimentaires', key: 'csg_retraite', label: 'CSG sur pensions de retraite (barème RFR 0 / 3,8 / 6,6 / 8,3 %)', varMeta: 'csg_retraite', sign: 'levy' },
  { section: '2. Retraites & pensions alimentaires', key: 'crds_retraite', label: 'CRDS sur pensions de retraite (0,5 %)', varMeta: 'crds_retraite', sign: 'levy' },
  { section: '2. Retraites & pensions alimentaires', key: 'casa_retraite', label: 'CASA sur pensions de retraite (0,3 %)', varMeta: 'casa_retraite', sign: 'levy' },
  { section: '2. Retraites & pensions alimentaires', key: 'pension_retraite_nette', label: 'Pension de retraite nette perçue', varMeta: 'pension_retraite_nette', highlight: true },
  { section: '2. Retraites & pensions alimentaires', key: 'pensions_alimentaires_percues', label: 'Pensions alimentaires perçues' },
  { section: '2. Retraites & pensions alimentaires', key: 'pensions_alimentaires_versees', label: 'Pensions alimentaires versées (déduites)', sign: 'levy' },

  // 3. Impôt sur le revenu & hauts revenus
  { section: '3. Impôt sur le revenu & hauts revenus (DGFiP)', key: 'revenu_net_imposable', label: 'Revenu net imposable au barème', varMeta: 'revenu_net_imposable', annualOnly: true },
  { section: '3. Impôt sur le revenu & hauts revenus (DGFiP)', key: 'revenu_fiscal_de_reference', label: 'Revenu fiscal de référence (RFR)', varMeta: 'revenu_fiscal_de_reference', annualOnly: true },
  { section: '3. Impôt sur le revenu & hauts revenus (DGFiP)', key: 'impot_brut', label: 'Impôt brut (barème progressif × quotient familial)', varMeta: 'impot_brut' },
  { section: '3. Impôt sur le revenu & hauts revenus (DGFiP)', key: 'decote', label: 'Décote bas revenus d’impôt', varMeta: 'decote', sign: 'benefit' },
  { section: '3. Impôt sur le revenu & hauts revenus (DGFiP)', key: 'impot_revenu', label: 'Impôt sur le revenu net', varMeta: 'impot_revenu', sign: 'levy', highlight: true },
  { section: '3. Impôt sur le revenu & hauts revenus (DGFiP)', key: 'cehr', label: 'Contribution exceptionnelle sur les hauts revenus (CEHR)', varMeta: 'cehr', sign: 'levy' },

  // 4. Patrimoine, capital & fiscalité locale
  { section: '4. Capital, immobilier & fiscalité locale', key: 'revenus_capital', label: 'Revenus financiers bruts (assiette PFU)' },
  { section: '4. Capital, immobilier & fiscalité locale', key: 'revenus_fonciers_nets', label: 'Revenus fonciers nets imposables', varMeta: 'revenus_fonciers_nets' },
  { section: '4. Capital, immobilier & fiscalité locale', key: 'pfu_ir', label: 'PFU — part impôt sur le revenu (12,8 %)', varMeta: 'pfu_ir', sign: 'levy' },
  { section: '4. Capital, immobilier & fiscalité locale', key: 'impot_plus_values_immobilieres', label: 'IR forfaitaire sur plus-values immobilières (19 %)', varMeta: 'impot_plus_values_immobilieres', sign: 'levy' },
  { section: '4. Capital, immobilier & fiscalité locale', key: 'prelevements_sociaux_patrimoine', label: 'Prélèvements sociaux sur patrimoine & capital (17,2 % ; 18,6 % capital en 2026)', varMeta: 'prelevements_sociaux_patrimoine', sign: 'levy' },
  { section: '4. Capital, immobilier & fiscalité locale', key: 'ifi', label: 'Impôt sur la fortune immobilière (IFI)', varMeta: 'ifi', sign: 'levy' },
  { section: '4. Capital, immobilier & fiscalité locale', key: 'taxe_fonciere', label: 'Taxe foncière (frais d’État 3 % inclus)', varMeta: 'taxe_fonciere', sign: 'levy' },
  { section: '4. Capital, immobilier & fiscalité locale', key: 'taxe_habitation_residence_secondaire', label: 'Taxe d’habitation résidence secondaire (THRS)', varMeta: 'taxe_habitation_residence_secondaire', sign: 'levy' },
  { section: '4. Capital, immobilier & fiscalité locale', key: 'taxe_valeur_sol', label: 'Taxe sur la valeur du terrain nu (LVT / TVTN)', varMeta: 'taxe_valeur_sol', sign: 'levy' },

  // 5. Prestations sociales & synthèse
  { section: '5. Prestations sociales (CNAF) & revenu disponible', key: 'allocations_familiales', label: 'Allocations familiales (modulées, complément dégressif inclus)', varMeta: 'allocations_familiales', sign: 'benefit' },
  { section: '5. Prestations sociales (CNAF) & revenu disponible', key: 'allocation_soutien_familial', label: 'Allocation de soutien familial (ASF différentielle)', varMeta: 'allocation_soutien_familial', sign: 'benefit' },
  { section: '5. Prestations sociales (CNAF) & revenu disponible', key: 'rsa', label: 'Revenu de solidarité active (RSA)', varMeta: 'rsa', sign: 'benefit' },
  { section: '5. Prestations sociales (CNAF) & revenu disponible', key: 'prime_activite', label: 'Prime d’activité (PPA)', varMeta: 'prime_activite', sign: 'benefit' },
  { section: '5. Prestations sociales (CNAF) & revenu disponible', key: 'revenu_disponible', label: 'Revenu disponible net du ménage', varMeta: 'revenu_disponible', highlight: true },
]
