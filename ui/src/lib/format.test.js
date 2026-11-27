import { describe, expect, it } from 'vitest'
import {
  buildStudioCsv,
  countActiveReforms,
  decodeStudioState,
  encodeStudioState,
  fmtEur,
  fmtPct,
  scalePeriod,
  unscalePeriod,
} from './format.js'
import { DEFAULT_HOUSEHOLD, DEFAULT_REFORMS, PRESETS } from './presets.js'

describe('Studio formatting & URL state helpers', () => {
  it('scales annual and monthly amounts accurately', () => {
    expect(scalePeriod(24000, 'month')).toBe(2000)
    expect(scalePeriod(24000, 'year')).toBe(24000)
    expect(unscalePeriod(2000, 'month')).toBe(24000)
    expect(unscalePeriod(30000, 'year')).toBe(30000)
  })

  it('formats French euros and signed deltas cleanly', () => {
    expect(fmtEur(2500)).toMatch(/2[\s\u202f]500 €/)
    expect(fmtEur(-120, { signed: true })).toBe('−120 €')
    expect(fmtEur(120, { signed: true })).toBe('+120 €')
    expect(fmtPct(18.6, { decimals: 1 })).toBe('18,6 %')
  })

  it('round-trips household + reform state via URL hash and clamps bounds', () => {
    const state = {
      year: '2025',
      periodMode: 'year',
      household: PRESETS[4].household,
      reforms: {
        ...DEFAULT_REFORMS,
        lvt_scenario: 'S2_IFI',
        dp6_underindex_pct: 2.5,
      },
    }
    const hash = encodeStudioState(state)
    const decoded = decodeStudioState(hash)
    expect(decoded.year).toBe('2025')
    expect(decoded.periodMode).toBe('year')
    expect(decoded.household.couple).toBe(true)
    expect(decoded.household.adults[0].pension_retraite).toBe(32000)
    expect(decoded.reforms.lvt_scenario).toBe('S2_IFI')
    expect(decoded.reforms.dp6_underindex_pct).toBe(2.5)
    expect(countActiveReforms(decoded.reforms)).toBe(2)

    const fallback = decodeStudioState('#s=not-valid-base64')
    expect(fallback.year).toBe('2024')
    expect(fallback.household.adults[0].salaire_brut).toBe(
      DEFAULT_HOUSEHOLD.adults[0].salaire_brut
    )
  })

  it('exports semicolon CSV with comma decimals and formula-injection guard', () => {
    const csv = buildStudioCsv({
      year: '2024',
      url: 'https://example.test/#s=abc',
      result: {
        reform_active: true,
        baseline: { revenu_disponible: 24000 },
        reform: { revenu_disponible: 25200 },
      },
      rows: [{ section: '=Injected', label: 'Revenu disponible', key: 'revenu_disponible' }],
    })
    expect(csv).toContain("'=Injected;Revenu disponible;revenu_disponible;24000,00;2000,00;25200,00;2100,00;1200,00")
  })
})
