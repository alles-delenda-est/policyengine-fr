import { useCallback, useDeferredValue, useEffect, useState } from 'react'
import './App.css'
import HouseholdPanel from './components/HouseholdPanel.jsx'
import ResultsWorkspace from './components/ResultsWorkspace.jsx'
import ShareBar from './components/ShareBar.jsx'
import {
  buildStudioCsv,
  decodeStudioState,
  downloadCsv,
  encodeStudioState,
} from './lib/format.js'
import { LEDGER_ROWS } from './lib/ledgerRows.js'
import { DEFAULT_HOUSEHOLD, DEFAULT_REFORMS, PRESETS } from './lib/presets.js'

const API_BASE = import.meta.env.VITE_API_BASE || ''

export default function App() {
  const [initial] = useState(() => decodeStudioState(window.location.hash))
  const [year, setYear] = useState(initial.year)
  const [periodMode, setPeriodMode] = useState(initial.periodMode)
  const [household, setHousehold] = useState(initial.household)
  const [reforms, setReforms] = useState(initial.reforms)
  const [activePresetId, setActivePresetId] = useState('custom')
  const [presetSeq, setPresetSeq] = useState(0)

  const [metadata, setMetadata] = useState(null)
  const [result, setResult] = useState(null)
  const [isSimulating, setIsSimulating] = useState(false)
  const [apiError, setApiError] = useState(null)

  const deferredHousehold = useDeferredValue(household)
  const deferredReforms = useDeferredValue(reforms)

  // Fetch static model metadata once
  useEffect(() => {
    fetch(`${API_BASE}/api/metadata`)
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`))))
      .then((data) => setMetadata(data))
      .catch(() => {})
  }, [])

  // Run microsimulation whenever deferred inputs or year change
  useEffect(() => {
    const controller = new AbortController()
    const timer = setTimeout(() => {
      setIsSimulating(true)
      fetch(`${API_BASE}/api/simulate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          year,
          household: deferredHousehold,
          reforms: deferredReforms,
          include_curve: true,
        }),
        signal: controller.signal,
      })
        .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`))))
        .then((data) => {
          setResult(data)
          setApiError(null)
          setIsSimulating(false)
        })
        .catch((err) => {
          if (err.name === 'AbortError') return
          setApiError(
            'Serveur Python indisponible. Lancez « python -m policyengine_fr.studio » pour activer le calcul en direct.'
          )
          setIsSimulating(false)
        })
    }, 35)

    return () => {
      clearTimeout(timer)
      controller.abort()
    }
  }, [year, deferredHousehold, deferredReforms])

  // Keep URL hash synced without polluting browser history
  useEffect(() => {
    const timer = setTimeout(() => {
      const nextHash = encodeStudioState({ year, periodMode, household, reforms })
      window.history.replaceState(window.history.state, '', nextHash)
    }, 280)
    return () => clearTimeout(timer)
  }, [year, periodMode, household, reforms])

  const getShareUrl = useCallback(() => {
    const hash = encodeStudioState({ year, periodMode, household, reforms })
    return `${window.location.origin}${window.location.pathname}${hash}`
  }, [year, periodMode, household, reforms])

  const handleExportCsv = useCallback(() => {
    if (!result) return
    const csv = buildStudioCsv({
      year,
      result,
      rows: LEDGER_ROWS,
      url: getShareUrl(),
    })
    downloadCsv(csv, `policyengine-fr-simulation-${year}.csv`)
  }, [year, result, getShareUrl])

  const handleResetAll = useCallback(() => {
    setHousehold(structuredClone(DEFAULT_HOUSEHOLD))
    setReforms({ ...DEFAULT_REFORMS })
    setActivePresetId('custom')
    setPresetSeq((s) => s + 1)
  }, [])

  const handleSelectPreset = (preset) => {
    setHousehold(structuredClone(preset.household))
    setActivePresetId(preset.id)
    setPresetSeq((s) => s + 1)
  }

  const handleHouseholdChange = useCallback((nextH) => {
    setHousehold(nextH)
    setActivePresetId('custom')
  }, [])

  return (
    <div className="pe-shell">
      <header className="pe-hero">
        <div className="pe-hero-inner">
          <div>
            <div className="pe-eyebrow">
              <span className="pe-tricolore" aria-hidden="true" />
              PolicyEngine France · Microsimulation socio-fiscale ouverte
            </div>
            <h1>Studio fiscal, social &amp; patrimonial</h1>
            <p className="pe-subtitle">
              Calculez en temps réel la fiche de paie, l’impôt sur le revenu, les cotisations, le
              RSA, la Prime d’activité, les allocations familiales et l’impact des réformes{' '}
              <strong>LVTShift</strong> &amp; <strong>PLF</strong> sur chaque ménage (2024–2025).
            </p>
          </div>
          <div className="pe-hero-badges">
            <span className="pe-stat-pill">
              {metadata?.policies
                ? `${metadata.policies.modelled?.length ?? 0} briques · ${
                    metadata.policies.simplifications?.length ?? 0
                  } simplifications`
                : 'Moteur Python vectorisé (2024–2025)'}
            </span>
            <span className="pe-stat-pill">Validé DGFiP &amp; OpenFisca (2024)</span>
          </div>
        </div>
      </header>

      <ShareBar
        year={year}
        onYearChange={setYear}
        periodMode={periodMode}
        onPeriodModeChange={setPeriodMode}
        getShareUrl={getShareUrl}
        onExportCsv={handleExportCsv}
        onResetAll={handleResetAll}
        canExport={Boolean(result)}
        isSimulating={isSimulating}
      />

      {apiError && (
        <div className="pe-alert-error" role="alert">
          {apiError}
        </div>
      )}

      <section className="pe-presets-strip" aria-label="Foyers types en un clic">
        <div className="pe-presets-header">
          <h2>Profils types en un clic</h2>
          <span>
            Charge un profil type complet (remplace les paramètres du foyer, conserve vos réformes)
          </span>
        </div>
        <div className="pe-presets-scroll">
          {PRESETS.map((p) => {
            const active = activePresetId === p.id
            return (
              <button
                key={p.id}
                type="button"
                className={`pe-preset-card${active ? ' active' : ''}`}
                aria-pressed={active}
                onClick={() => handleSelectPreset(p)}
              >
                <div className="pe-preset-top">
                  <strong>{p.titre}</strong>
                  <span className="pe-preset-badge">{p.badge}</span>
                </div>
                <p>{p.resume}</p>
              </button>
            )
          })}
        </div>
      </section>

      <main className="pe-main-grid">
        <HouseholdPanel
          household={household}
          onHouseholdChange={handleHouseholdChange}
          reforms={reforms}
          onReformsChange={setReforms}
          periodMode={periodMode}
          year={year}
          dp6ClawbackShare={result?.dp6_clawback_share}
          lvtMeta={metadata?.lvt}
          presetSeq={presetSeq}
        />

        <ResultsWorkspace result={result} periodMode={periodMode} metadata={metadata} />
      </main>

      <footer className="pe-footer">
        <p>
          <strong>PolicyEngine France</strong> (AGPL-3.0) · Moteur Python vectorisé sur{' '}
          <code>policyengine-core</code> · Réformes connectées à{' '}
          <a
            href="https://github.com/alles-delenda-est/LVTShift"
            target="_blank"
            rel="noopener noreferrer"
          >
            LVTShift
          </a>{' '}
          et{' '}
          <a
            href="https://github.com/alles-delenda-est/budget_fr_sim_test"
            target="_blank"
            rel="noopener noreferrer"
          >
            Simulateur Budget France
          </a>
          .
        </p>
      </footer>
    </div>
  )
}
