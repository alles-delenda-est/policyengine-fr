import { useRef, useState } from 'react'

export default function ShareBar({
  year,
  onYearChange,
  periodMode,
  onPeriodModeChange,
  getShareUrl,
  onExportCsv,
  onResetAll,
  canExport = true,
  isSimulating,
}) {
  const [copyState, setCopyState] = useState('idle')
  const urlInputRef = useRef(null)

  const handleCopy = async () => {
    const url = getShareUrl()
    try {
      if (!navigator.clipboard?.writeText) throw new Error('no-clipboard')
      await navigator.clipboard.writeText(url)
      setCopyState('copied')
      setTimeout(() => setCopyState('idle'), 2400)
    } catch {
      setCopyState('manual')
      setTimeout(() => urlInputRef.current?.select(), 0)
    }
  }

  return (
    <div className="pe-command-bar" role="region" aria-label="Réglages globaux d’affichage et partage">
      <div className="pe-command-group">
        <span className="pe-command-label">Législation</span>
        <div className="pe-segmented" role="group" aria-label="Année de législation">
          {['2024', '2025'].map((y) => (
            <button
              key={y}
              type="button"
              className={`pe-seg-btn${year === y ? ' active' : ''}`}
              aria-pressed={year === y}
              onClick={() => onYearChange(y)}
            >
              {y}
            </button>
          ))}
        </div>

        <span className="pe-command-divider" aria-hidden="true" />

        <span className="pe-command-label">Affichage</span>
        <div className="pe-segmented" role="group" aria-label="Fréquence des montants">
          <button
            type="button"
            className={`pe-seg-btn${periodMode === 'month' ? ' active' : ''}`}
            aria-pressed={periodMode === 'month'}
            onClick={() => onPeriodModeChange('month')}
          >
            € / mois
          </button>
          <button
            type="button"
            className={`pe-seg-btn${periodMode === 'year' ? ' active' : ''}`}
            aria-pressed={periodMode === 'year'}
            onClick={() => onPeriodModeChange('year')}
          >
            € / an
          </button>
        </div>

        {isSimulating && (
          <span className="pe-live-pill" role="status" aria-live="polite">
            Calcul…
          </span>
        )}
      </div>

      <div className="pe-command-actions">
        <button type="button" className="pe-btn pe-btn-ghost" onClick={onResetAll}>
          Réinitialiser
        </button>
        <button
          type="button"
          className="pe-btn pe-btn-secondary"
          onClick={onExportCsv}
          disabled={!canExport}
        >
          Exporter CSV
        </button>
        <button type="button" className="pe-btn pe-btn-primary" onClick={handleCopy}>
          {copyState === 'copied' ? '✓ Lien copié' : 'Partager le scénario'}
        </button>
      </div>

      {copyState === 'manual' && (
        <input
          ref={urlInputRef}
          className="pe-manual-url"
          readOnly
          value={getShareUrl()}
          aria-label="Lien du scénario à copier"
          onFocus={(e) => e.target.select()}
        />
      )}
    </div>
  )
}
