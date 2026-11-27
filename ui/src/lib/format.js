import { DEFAULT_HOUSEHOLD, DEFAULT_PATRIMOINE, DEFAULT_REFORMS } from './presets.js'

const NF_INT = new Intl.NumberFormat('fr-FR', { maximumFractionDigits: 0 })
const NF_DEC1 = new Intl.NumberFormat('fr-FR', { minimumFractionDigits: 1, maximumFractionDigits: 1 })
const NF_DEC2 = new Intl.NumberFormat('fr-FR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })

export function scalePeriod(annualValue, periodMode = 'month') {
  const x = Number(annualValue) || 0
  return periodMode === 'month' ? x / 12 : x
}

export function unscalePeriod(displayValue, periodMode = 'month') {
  const x = Number(displayValue) || 0
  return periodMode === 'month' ? Math.round(x * 12) : Math.round(x)
}

export function fmtEur(value, { decimals = 0, signed = false } = {}) {
  const x = Number(value)
  if (!Number.isFinite(x)) return '—'
  const absVal = Math.abs(x) < 0.005 ? 0 : Math.abs(x)
  const nf = decimals === 2 ? NF_DEC2 : decimals === 1 ? NF_DEC1 : NF_INT
  const formatted = nf.format(absVal)
  const sign = x < -0.005 ? '−' : signed && x > 0.005 ? '+' : ''
  return `${sign}${formatted} €`
}

export function fmtPct(value, { decimals = 1, signed = false } = {}) {
  const x = Number(value)
  if (!Number.isFinite(x)) return '—'
  const absVal = Math.abs(x) < 0.005 ? 0 : Math.abs(x)
  const nf = decimals === 2 ? NF_DEC2 : decimals === 1 ? NF_DEC1 : NF_INT
  const sign = x < -0.005 ? '−' : signed && x > 0.005 ? '+' : ''
  return `${sign}${nf.format(absVal)} %`
}

export function countActiveReforms(reforms) {
  if (!reforms) return 0
  let n = 0
  if (reforms.lvt_scenario && reforms.lvt_scenario !== 'OFF') n += 1
  if (Math.abs(Number(reforms.ir_rate_change_pct) || 0) > 0.001) n += 1
  if (reforms.ir_freeze_2024) n += 1
  if (Math.abs(Number(reforms.csg_delta_pts) || 0) > 0.001) n += 1
  if ((Number(reforms.dp6_underindex_pct) || 0) > 0.001) n += 1
  return n
}

export function countPatrimoineInputs(patrimoine) {
  if (!patrimoine) return 0
  const numericKeys = [
    'revenus_capital',
    'revenus_fonciers_bruts',
    'plus_values_immobilieres',
    'patrimoine_immobilier_residence_principale',
    'patrimoine_immobilier_autre',
    'taxe_fonciere_locale',
    'thrs_locale',
    'valeur_terrain_imposable',
    'pensions_alimentaires_percues',
    'pensions_alimentaires_versees',
  ]
  return numericKeys.filter((k) => (Number(patrimoine[k]) || 0) > 0).length
}

function clampNum(v, fallback, lo, hi) {
  const n = Number(v)
  if (!Number.isFinite(n)) return fallback
  return Math.min(Math.max(n, lo), hi)
}

export function encodeStudioState({ year, periodMode, household, reforms }) {
  const payload = {
    y: year === '2025' ? '2025' : '2024',
    m: periodMode === 'year' ? 'y' : 'm',
    h: household,
    r: reforms,
  }
  const json = JSON.stringify(payload)
  const b64 = btoa(encodeURIComponent(json))
  return `#s=${b64}`
}

export function decodeStudioState(hash) {
  const fallback = {
    year: '2024',
    periodMode: 'month',
    household: structuredClone(DEFAULT_HOUSEHOLD),
    reforms: { ...DEFAULT_REFORMS },
  }
  if (!hash || !hash.includes('s=')) return fallback
  try {
    const rawParam = hash.replace(/^#/, '').split('s=')[1]?.split('&')[0]
    if (!rawParam) return fallback
    const parsed = JSON.parse(decodeURIComponent(atob(rawParam)))
    const h = parsed.h || {}
    const r = parsed.r || {}
    const a1 = h.adults?.[0] || {}
    const a2 = h.adults?.[1] || {}
    const children = Array.isArray(h.children)
      ? h.children.slice(0, 8).map((c) => ({ age: Math.round(clampNum(c?.age, 8, 0, 24)) }))
      : []
    const patIn = h.patrimoine || {}
    const pat = { ...DEFAULT_PATRIMOINE }
    for (const k of Object.keys(DEFAULT_PATRIMOINE)) {
      if (typeof DEFAULT_PATRIMOINE[k] === 'boolean') {
        pat[k] = patIn[k] === undefined ? DEFAULT_PATRIMOINE[k] : Boolean(patIn[k])
      } else {
        pat[k] = clampNum(patIn[k], 0, 0, 1e8)
      }
    }
    const validLvt = ['OFF', 'S1', 'S2', 'S2_IFI', 'S3', 'S3_IFI']
    return {
      year: parsed.y === '2025' ? '2025' : '2024',
      periodMode: parsed.m === 'y' ? 'year' : 'month',
      household: {
        couple: Boolean(h.couple),
        parent_isole: h.parent_isole === undefined ? true : Boolean(h.parent_isole),
        adults: [
          {
            age: Math.round(clampNum(a1.age, 32, 18, 110)),
            salaire_brut: clampNum(a1.salaire_brut, 30000, 0, 2000000),
            pension_retraite: clampNum(a1.pension_retraite, 0, 0, 2000000),
            cadre: Boolean(a1.cadre),
            effectif_entreprise: Math.round(clampNum(a1.effectif_entreprise, 10, 1, 100000)),
          },
          {
            age: Math.round(clampNum(a2.age, 32, 18, 110)),
            salaire_brut: clampNum(a2.salaire_brut, 0, 0, 2000000),
            pension_retraite: clampNum(a2.pension_retraite, 0, 0, 2000000),
            cadre: Boolean(a2.cadre),
            effectif_entreprise: Math.round(clampNum(a2.effectif_entreprise, 10, 1, 100000)),
          },
        ],
        children,
        patrimoine: pat,
      },
      reforms: {
        lvt_scenario: validLvt.includes(r.lvt_scenario) ? r.lvt_scenario : 'OFF',
        lvt_custom_rate:
          r.lvt_custom_rate === null || r.lvt_custom_rate === undefined || r.lvt_custom_rate === ''
            ? null
            : clampNum(r.lvt_custom_rate, 0.01, 0, 0.1),
        ir_rate_change_pct: clampNum(r.ir_rate_change_pct, 0, -50, 50),
        ir_freeze_2024: Boolean(r.ir_freeze_2024),
        csg_delta_pts: clampNum(r.csg_delta_pts, 0, -5, 5),
        dp6_underindex_pct: clampNum(r.dp6_underindex_pct, 0, 0, 20),
        dp6_threshold_annual: clampNum(r.dp6_threshold_annual, 24000, 0, 200000),
      },
    }
  } catch {
    return fallback
  }
}

function safeCsvCell(text) {
  const s = String(text ?? '')
  if (/^[=+\-@\t\r]/.test(s)) return `'${s}`
  if (s.includes(';') || s.includes('"') || s.includes('\n')) {
    return `"${s.replace(/"/g, '""')}"`
  }
  return s
}

function frCsvNum(val) {
  const n = Number(val)
  if (!Number.isFinite(n)) return ''
  return n.toFixed(2).replace('.', ',')
}

export function buildStudioCsv({ year, result, rows, url }) {
  const headerMeta = [
    ['# PolicyEngine France — Export de simulation ménage'],
    ['# Année fiscale et sociale', year],
    ['# Lien du scénario', url || ''],
    [],
    [
      'Catégorie',
      'Indicateur',
      'Variable',
      'Droit courant (€/an)',
      'Droit courant (€/mois)',
      ...(result?.reform_active
        ? ['Après réforme (€/an)', 'Après réforme (€/mois)', 'Écart (€/an)']
        : []),
    ],
  ]

  const dataLines = rows.map((r) => {
    const b = Number(result?.baseline?.[r.key] ?? 0)
    const baseCols = [r.section, r.label, r.key, frCsvNum(b), frCsvNum(b / 12)]
    if (result?.reform_active && result?.reform) {
      const ref = Number(result.reform[r.key] ?? 0)
      baseCols.push(frCsvNum(ref), frCsvNum(ref / 12), frCsvNum(ref - b))
    }
    return baseCols
  })

  return [...headerMeta, ...dataLines]
    .map((line) => line.map(safeCsvCell).join(';'))
    .join('\r\n')
}

export function downloadCsv(csvContent, filename) {
  const blob = new Blob([`\uFEFF${csvContent}`], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  const url = URL.createObjectURL(blob)
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}
