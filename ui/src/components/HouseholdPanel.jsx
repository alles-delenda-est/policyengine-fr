import { useRef, useState } from 'react'
import { LVT_SCENARIOS } from '../lib/presets.js'
import {
  countActiveReforms,
  countPatrimoineInputs,
  fmtEur,
  fmtPct,
  scalePeriod,
  unscalePeriod,
} from '../lib/format.js'

function childBadgeText(age) {
  if (age < 14) return 'AF · ASF · RSA (< 14 ans)'
  if (age < 20) return 'Maj. âge AF +14 ans'
  return 'RSA & PPA seuls (20–24 ans)'
}

function DraftNumberInput({
  value,
  onCommit,
  min = 0,
  max,
  ariaLabel,
  className,
  integer = true,
}) {
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState('')
  const cancelledRef = useRef(false)
  const inputRef = useRef(null)

  const clampCommit = (raw) => {
    const trimmed = String(raw).trim()
    if (trimmed === '') {
      return min > 0 ? value : 0
    }
    const parsed = Number(trimmed)
    if (!Number.isFinite(parsed)) {
      return value
    }
    const normalized = integer ? Math.round(parsed) : parsed
    const lo = min !== undefined ? Math.max(min, normalized) : normalized
    return max !== undefined ? Math.min(max, lo) : lo
  }

  return (
    <input
      ref={inputRef}
      type="number"
      step={1}
      min={min}
      max={max}
      className={className}
      aria-label={ariaLabel}
      value={editing ? draft : String(value)}
      onFocus={() => {
        cancelledRef.current = false
        setEditing(true)
        setDraft(String(value))
      }}
      onChange={(e) => {
        const nextRaw = e.target.value
        setDraft(nextRaw)
        if (nextRaw.trim() === '') return
        const parsed = Number(nextRaw)
        if (!Number.isFinite(parsed)) return
        if (min !== undefined && parsed < min) return
        if (max !== undefined && parsed > max) return
        onCommit(integer ? Math.round(parsed) : parsed)
      }}
      onBlur={() => {
        setEditing(false)
        if (cancelledRef.current) {
          cancelledRef.current = false
          return
        }
        const nextVal = clampCommit(draft)
        if (nextVal !== value) {
          onCommit(nextVal)
        }
      }}
      onKeyDown={(e) => {
        if (e.key === 'Enter') {
          e.currentTarget.blur()
        } else if (e.key === 'Escape') {
          cancelledRef.current = true
          setEditing(false)
          e.currentTarget.blur()
        }
      }}
    />
  )
}

function MoneySliderInput({
  label,
  hint,
  annualValue,
  onChangeAnnual,
  periodMode,
  maxAnnual = 120000,
  stepAnnual = 600,
}) {
  const displayVal = Math.round(scalePeriod(annualValue, periodMode))
  const maxDisplay = Math.round(scalePeriod(maxAnnual, periodMode))
  const stepDisplay = Math.max(10, Math.round(scalePeriod(stepAnnual, periodMode)))
  const unitSuffix = periodMode === 'month' ? '€/mois' : '€/an'

  return (
    <div className="pe-field">
      <div className="pe-field-header">
        <label className="pe-field-label">{label}</label>
        <div className="pe-money-box">
          <DraftNumberInput
            min={0}
            value={displayVal}
            ariaLabel={`${label} (${unitSuffix})`}
            onCommit={(v) => onChangeAnnual(Math.max(0, unscalePeriod(v, periodMode)))}
          />
          <span>{unitSuffix}</span>
        </div>
      </div>
      <input
        type="range"
        className="pe-slider"
        min={0}
        max={maxDisplay}
        step={stepDisplay}
        value={Math.min(displayVal, maxDisplay)}
        aria-label={`Curseur ${label}`}
        onChange={(e) => onChangeAnnual(unscalePeriod(e.target.value, periodMode))}
      />
      {hint && <p className="pe-field-hint">{hint}</p>}
    </div>
  )
}

function AdultCard({ index, adult, onChange, periodMode, title }) {
  const setField = (k, v) => onChange(index, { ...adult, [k]: v })
  const isLargeFirm = (adult.effectif_entreprise || 10) >= 50

  return (
    <div className="pe-subcard">
      <div className="pe-subcard-head">
        <h4>{title}</h4>
        <div className="pe-inline-controls">
          <label className="pe-age-pill">
            <span>Âge</span>
            <DraftNumberInput
              min={18}
              max={105}
              value={adult.age}
              ariaLabel={`Âge ${title}`}
              onCommit={(v) => setField('age', v)}
            />
          </label>
          <button
            type="button"
            className={`pe-chip-toggle${adult.cadre ? ' active' : ''}`}
            aria-pressed={adult.cadre}
            onClick={() => setField('cadre', !adult.cadre)}
            title="Active la cotisation APEC (0,024 % salarial / 0,036 % patronal jusqu’à 4 PASS)"
          >
            Cadre
          </button>
          <button
            type="button"
            className={`pe-chip-toggle${isLargeFirm ? ' active' : ''}`}
            aria-pressed={isLargeFirm}
            onClick={() => setField('effectif_entreprise', isLargeFirm ? 10 : 100)}
            title="Effectif de l’employeur : FNAL 0,10 % (< 50) vs 0,50 % (≥ 50) et paramètre T Fillon"
          >
            {isLargeFirm ? '≥ 50 sal.' : '< 50 sal.'}
          </button>
        </div>
      </div>

      <MoneySliderInput
        label="Salaire brut"
        annualValue={adult.salaire_brut}
        onChangeAnnual={(v) => setField('salaire_brut', v)}
        periodMode={periodMode}
        maxAnnual={180000}
        stepAnnual={600}
      />

      <MoneySliderInput
        label="Pension de retraite brute"
        annualValue={adult.pension_retraite}
        onChangeAnnual={(v) => setField('pension_retraite', v)}
        periodMode={periodMode}
        maxAnnual={120000}
        stepAnnual={600}
      />
    </div>
  )
}

export default function HouseholdPanel({
  household,
  onHouseholdChange,
  reforms,
  onReformsChange,
  periodMode,
  year,
  dp6ClawbackShare,
  lvtMeta,
  presetSeq = 0,
}) {
  const [sidebarTab, setSidebarTab] = useState('foyer')
  const patCount = countPatrimoineInputs(household.patrimoine)
  const [patOverride, setPatOverride] = useState(null)
  const patOpen =
    patOverride && patOverride.seq === presetSeq ? patOverride.open : patCount > 0

  const activeReformsCount = countActiveReforms(reforms)

  const updateAdult = (idx, nextAdult) => {
    const nextAdults = [...household.adults]
    nextAdults[idx] = nextAdult
    onHouseholdChange({ ...household, adults: nextAdults })
  }

  const addChild = () => {
    if (household.children.length >= 6) return
    onHouseholdChange({
      ...household,
      children: [...household.children, { age: 8 }],
    })
  }

  const updateChildAge = (idx, nextAge) => {
    const clamped = Math.max(0, Math.min(24, nextAge))
    const next = household.children.map((c, i) => (i === idx ? { age: clamped } : c))
    onHouseholdChange({ ...household, children: next })
  }

  const removeChild = (idx) => {
    onHouseholdChange({
      ...household,
      children: household.children.filter((_, i) => i !== idx),
    })
  }

  const setPat = (k, v) => {
    onHouseholdChange({
      ...household,
      patrimoine: { ...household.patrimoine, [k]: v },
    })
  }

  const setRef = (k, v) => onReformsChange({ ...reforms, [k]: v })

  const activeLvtObj =
    LVT_SCENARIOS.find((s) => s.id === reforms.lvt_scenario) || LVT_SCENARIOS[0]

  return (
    <aside className="pe-sidebar" aria-label="Paramètres du foyer et des réformes">
      <div className="pe-sidebar-tabs" role="tablist">
        <button
          type="button"
          role="tab"
          aria-selected={sidebarTab === 'foyer'}
          className={`pe-sidebar-tab${sidebarTab === 'foyer' ? ' active' : ''}`}
          onClick={() => setSidebarTab('foyer')}
        >
          Mon foyer
          {patCount > 0 && (
            <span
              className="pe-count-pill"
              title="Champs patrimoniaux ou pensions alimentaires actifs"
            >
              {patCount}
            </span>
          )}
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={sidebarTab === 'reformes'}
          className={`pe-sidebar-tab${sidebarTab === 'reformes' ? ' active' : ''}`}
          onClick={() => setSidebarTab('reformes')}
        >
          Réformes
          {activeReformsCount > 0 && (
            <span className="pe-count-pill pe-count-pill-accent">{activeReformsCount}</span>
          )}
        </button>
      </div>

      {sidebarTab === 'foyer' ? (
        <div className="pe-sidebar-body">
          <div className="pe-subcard">
            <div className="pe-subcard-head">
              <h4>Situation familiale</h4>
            </div>
            <div className="pe-segmented pe-segmented-full" role="group" aria-label="Composition adulte">
              <button
                type="button"
                className={`pe-seg-btn${!household.couple ? ' active' : ''}`}
                aria-pressed={!household.couple}
                onClick={() => onHouseholdChange({ ...household, couple: false })}
              >
                Personne seule
              </button>
              <button
                type="button"
                className={`pe-seg-btn${household.couple ? ' active' : ''}`}
                aria-pressed={household.couple}
                onClick={() => onHouseholdChange({ ...household, couple: true })}
              >
                Couple (marié / pacsé)
              </button>
            </div>

            {!household.couple && household.children.length > 0 && (
              <label className="pe-check-row">
                <input
                  type="checkbox"
                  checked={household.parent_isole}
                  onChange={(e) =>
                    onHouseholdChange({ ...household, parent_isole: e.target.checked })
                  }
                />
                <span>Parent isolé (case T : +0,5 part QF &amp; plafond majoré)</span>
              </label>
            )}
          </div>

          <AdultCard
            index={0}
            title={household.couple ? 'Déclarant 1' : 'Adulte'}
            adult={household.adults[0]}
            onChange={updateAdult}
            periodMode={periodMode}
          />

          {household.couple && (
            <AdultCard
              index={1}
              title="Conjoint / Déclarant 2"
              adult={household.adults[1]}
              onChange={updateAdult}
              periodMode={periodMode}
            />
          )}

          <div className="pe-subcard">
            <div className="pe-subcard-head">
              <h4>Enfants à charge ({household.children.length})</h4>
              <button
                type="button"
                className="pe-btn pe-btn-small"
                onClick={addChild}
                disabled={household.children.length >= 6}
              >
                + Ajouter
              </button>
            </div>

            {household.children.length === 0 ? (
              <p className="pe-muted-note">
                Aucun enfant à charge. Ajoutez des enfants (0 à 24 ans) pour activer le
                quotient familial, les allocations familiales, l’ASF et les majorations RSA/PPA.
              </p>
            ) : (
              <div className="pe-children-list">
                {household.children.map((ch, idx) => (
                  <div key={idx} className="pe-child-row">
                    <div>
                      <strong>Enfant {idx + 1}</strong>
                      <span className="pe-child-tag">{childBadgeText(ch.age)}</span>
                    </div>
                    <div className="pe-child-controls">
                      <button
                        type="button"
                        className="pe-step-btn"
                        aria-label={`Diminuer l’âge de l’enfant ${idx + 1}`}
                        onClick={() => updateChildAge(idx, ch.age - 1)}
                      >
                        −
                      </button>
                      <span className="pe-child-age">{ch.age} ans</span>
                      <button
                        type="button"
                        className="pe-step-btn"
                        aria-label={`Augmenter l’âge de l’enfant ${idx + 1}`}
                        onClick={() => updateChildAge(idx, ch.age + 1)}
                      >
                        +
                      </button>
                      <button
                        type="button"
                        className="pe-remove-btn"
                        aria-label={`Retirer l’enfant ${idx + 1}`}
                        onClick={() => removeChild(idx)}
                      >
                        ×
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="pe-subcard">
            <button
              type="button"
              className="pe-drawer-toggle"
              aria-expanded={patOpen}
              onClick={() => setPatOverride({ seq: presetSeq, open: !patOpen })}
            >
              <span>
                Patrimoine, loyers, capital &amp; pensions alimentaires
                {patCount > 0 && <span className="pe-count-pill">{patCount} actif(s)</span>}
              </span>
              <span>{patOpen ? '▴' : '▾'}</span>
            </button>

            {patOpen && (
              <div className="pe-drawer-content">
                <MoneySliderInput
                  label="Revenus financiers (PFU : dividendes, intérêts)"
                  annualValue={household.patrimoine.revenus_capital}
                  onChangeAnnual={(v) => setPat('revenus_capital', v)}
                  periodMode="year"
                  maxAnnual={200000}
                  stepAnnual={1000}
                />

                <MoneySliderInput
                  label="Loyers bruts annuels (location nue)"
                  annualValue={household.patrimoine.revenus_fonciers_bruts}
                  onChangeAnnual={(v) => setPat('revenus_fonciers_bruts', v)}
                  periodMode="year"
                  maxAnnual={100000}
                  stepAnnual={1000}
                />

                {household.patrimoine.revenus_fonciers_bruts > 0 && (
                  <>
                    <label className="pe-check-row">
                      <input
                        type="checkbox"
                        checked={household.patrimoine.regime_micro_foncier}
                        onChange={(e) => setPat('regime_micro_foncier', e.target.checked)}
                      />
                      <span>Régime micro-foncier (−30 % jusqu’à 15 000 € bruts)</span>
                    </label>
                    {(!household.patrimoine.regime_micro_foncier ||
                      household.patrimoine.revenus_fonciers_bruts > 15000) && (
                      <MoneySliderInput
                        label="Charges foncières déductibles (régime réel)"
                        annualValue={household.patrimoine.charges_foncieres_reelles}
                        onChangeAnnual={(v) => setPat('charges_foncieres_reelles', v)}
                        periodMode="year"
                        maxAnnual={60000}
                        stepAnnual={500}
                      />
                    )}
                  </>
                )}

                <MoneySliderInput
                  label="Plus-values immobilières imposables"
                  annualValue={household.patrimoine.plus_values_immobilieres}
                  onChangeAnnual={(v) => setPat('plus_values_immobilieres', v)}
                  periodMode="year"
                  maxAnnual={200000}
                  stepAnnual={2000}
                />

                <MoneySliderInput
                  label="Résidence principale nette (avant abattement IFI 30 %)"
                  annualValue={household.patrimoine.patrimoine_immobilier_residence_principale}
                  onChangeAnnual={(v) => setPat('patrimoine_immobilier_residence_principale', v)}
                  periodMode="year"
                  maxAnnual={4000000}
                  stepAnnual={50000}
                />

                <MoneySliderInput
                  label="Autre immobilier net taxable (IFI)"
                  annualValue={household.patrimoine.patrimoine_immobilier_autre}
                  onChangeAnnual={(v) => setPat('patrimoine_immobilier_autre', v)}
                  periodMode="year"
                  maxAnnual={4000000}
                  stepAnnual={50000}
                />

                <MoneySliderInput
                  label="Taxe foncière locale (hors frais État 3 %)"
                  annualValue={household.patrimoine.taxe_fonciere_locale}
                  onChangeAnnual={(v) => setPat('taxe_fonciere_locale', v)}
                  periodMode="year"
                  maxAnnual={12000}
                  stepAnnual={100}
                />

                <MoneySliderInput
                  label="TH résidence secondaire locale"
                  annualValue={household.patrimoine.thrs_locale}
                  onChangeAnnual={(v) => setPat('thrs_locale', v)}
                  periodMode="year"
                  maxAnnual={8000}
                  stepAnnual={100}
                />

                <MoneySliderInput
                  label="Valeur du terrain nu imposable (assiette LVT / TVTN)"
                  annualValue={household.patrimoine.valeur_terrain_imposable}
                  onChangeAnnual={(v) => setPat('valeur_terrain_imposable', v)}
                  periodMode="year"
                  maxAnnual={1500000}
                  stepAnnual={10000}
                />

                <MoneySliderInput
                  label="Pensions alimentaires perçues"
                  annualValue={household.patrimoine.pensions_alimentaires_percues}
                  onChangeAnnual={(v) => setPat('pensions_alimentaires_percues', v)}
                  periodMode={periodMode}
                  maxAnnual={24000}
                  stepAnnual={300}
                />

                <MoneySliderInput
                  label="Pensions alimentaires versées (déductibles)"
                  annualValue={household.patrimoine.pensions_alimentaires_versees}
                  onChangeAnnual={(v) => setPat('pensions_alimentaires_versees', v)}
                  periodMode={periodMode}
                  maxAnnual={24000}
                  stepAnnual={300}
                />
              </div>
            )}
          </div>
        </div>
      ) : (
        <div className="pe-sidebar-body">
          <div className="pe-subcard pe-subcard-accent">
            <div className="pe-subcard-head">
              <h4>LVTShift — Taxe sur la valeur du sol</h4>
              <span className="pe-tag">À rendement égal</span>
            </div>
            <p className="pe-muted-note">
              Bascule des impôts immobiliers existants vers une taxe nationale sur la valeur du
              terrain nu (<code>valeur_terrain_imposable</code>), calibrée sur les rendements
              épinglés de{' '}
              <a
                href="https://github.com/alles-delenda-est/LVTShift"
                target="_blank"
                rel="noopener noreferrer"
              >
                LVTShift-FR ↗
              </a>
              {lvtMeta?.source?.commit && (
                <> (commit <code>{lvtMeta.source.commit.slice(0, 7)}</code>)</>
              )}
              .
            </p>

            <label className="pe-field-label" htmlFor="pe-lvt-select">
              Scénario de remplacement
            </label>
            <select
              id="pe-lvt-select"
              className="pe-select"
              value={reforms.lvt_scenario}
              onChange={(e) =>
                onReformsChange({
                  ...reforms,
                  lvt_scenario: e.target.value,
                  lvt_custom_rate: null,
                })
              }
            >
              {LVT_SCENARIOS.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.label}
                </option>
              ))}
            </select>
            <p className="pe-field-hint">{activeLvtObj.detail}</p>

            {reforms.lvt_scenario !== 'OFF' && (
              <div className="pe-field">
                <div className="pe-field-header">
                  <label className="pe-field-label">
                    Taux TVTN appliqué :{' '}
                    <strong>
                      {fmtPct(
                        reforms.lvt_custom_rate !== null
                          ? reforms.lvt_custom_rate * 100
                          : activeLvtObj.ratePct,
                        { decimals: 2 }
                      )}
                    </strong>
                  </label>
                  {reforms.lvt_custom_rate !== null && (
                    <button
                      type="button"
                      className="pe-link-btn"
                      onClick={() => setRef('lvt_custom_rate', null)}
                    >
                      Taux neutre ({fmtPct(activeLvtObj.ratePct, { decimals: 2 })})
                    </button>
                  )}
                </div>
                <input
                  type="range"
                  className="pe-slider"
                  aria-label="Taux TVTN appliqué"
                  min={0.2}
                  max={3.0}
                  step={0.02}
                  value={
                    reforms.lvt_custom_rate !== null
                      ? Number((reforms.lvt_custom_rate * 100).toFixed(2))
                      : activeLvtObj.ratePct
                  }
                  onChange={(e) => setRef('lvt_custom_rate', Number(e.target.value) / 100)}
                />
                {household.patrimoine.valeur_terrain_imposable <= 0 && (
                  <p className="pe-callout-warn">
                    Astuce : renseignez une <strong>Valeur du terrain nu imposable</strong> dans
                    « Mon foyer → Patrimoine » (ou choisissez le profil « Propriétaire bailleur »)
                    pour observer la taxe foncière remplacée par la TVTN.
                  </p>
                )}
              </div>
            )}
          </div>

          <div className="pe-subcard">
            <div className="pe-subcard-head">
              <h4>Leviers budgétaires PLF</h4>
              <span className="pe-tag">budget_fr_sim_test</span>
            </div>
            <p className="pe-muted-note">
              Contreparties microsimulées des leviers macro-budgétaires de{' '}
              <code>Simulateur Budget France</code> (<code>review/day0</code> &amp;{' '}
              <code>day1</code>).
            </p>

            <div className="pe-field">
              <div className="pe-field-header">
                <label className="pe-field-label">Échelle des taux marginaux IR</label>
                <span className="pe-mono-val">
                  {fmtPct(reforms.ir_rate_change_pct, { decimals: 1, signed: true })}
                </span>
              </div>
              <input
                type="range"
                className="pe-slider"
                aria-label="Échelle des taux marginaux IR"
                min={-20}
                max={20}
                step={0.5}
                value={reforms.ir_rate_change_pct}
                onChange={(e) => setRef('ir_rate_change_pct', Number(e.target.value))}
              />
            </div>

            <label className="pe-check-row">
              <input
                type="checkbox"
                checked={reforms.ir_freeze_2024}
                onChange={(e) => setRef('ir_freeze_2024', e.target.checked)}
              />
              <span>
                Gel du barème IR, de la décote et du plafonnement QF aux seuils 2024
                {year === '2024' && ' (actif en 2025)'}
              </span>
            </label>

            <div className="pe-field">
              <div className="pe-field-header">
                <label className="pe-field-label">Variation du taux de CSG activité</label>
                <span className="pe-mono-val">
                  {reforms.csg_delta_pts > 0 ? '+' : ''}
                  {reforms.csg_delta_pts.toFixed(1).replace('.', ',')} pt
                </span>
              </div>
              <input
                type="range"
                className="pe-slider"
                aria-label="Variation du taux de CSG activité"
                min={-2.0}
                max={2.0}
                step={0.1}
                value={reforms.csg_delta_pts}
                onChange={(e) => setRef('csg_delta_pts', Number(e.target.value))}
              />
            </div>
          </div>

          <div className="pe-subcard">
            <div className="pe-subcard-head">
              <h4>Sous-indexation ciblée des retraites</h4>
              <span className="pe-tag">Décision D-P6</span>
            </div>
            <p className="pe-muted-note">
              Sous-indexe les pensions brutes individuelles excédant un seuil annuel avec lissage
              au seuil (aucun retraité juste au-dessus ne passe sous le seuil).
            </p>

            <div className="pe-field">
              <div className="pe-field-header">
                <label className="pe-field-label">Sous-indexation au-dessus du seuil</label>
                <span className="pe-mono-val">
                  {reforms.dp6_underindex_pct > 0
                    ? `−${reforms.dp6_underindex_pct.toFixed(1).replace('.', ',')} %`
                    : '0,0 %'}
                </span>
              </div>
              <input
                type="range"
                className="pe-slider"
                aria-label="Sous-indexation au-dessus du seuil"
                min={0}
                max={6}
                step={0.2}
                value={reforms.dp6_underindex_pct}
                onChange={(e) => setRef('dp6_underindex_pct', Number(e.target.value))}
              />
            </div>

            {reforms.dp6_underindex_pct > 0 && (
              <>
                <div className="pe-field">
                  <div className="pe-field-header">
                    <label className="pe-field-label">Seuil de protection pension brute</label>
                    <span className="pe-mono-val">
                      {fmtEur(scalePeriod(reforms.dp6_threshold_annual, periodMode))} /{' '}
                      {periodMode === 'month' ? 'mois' : 'an'}
                    </span>
                  </div>
                  <input
                    type="range"
                    className="pe-slider"
                    aria-label="Seuil de protection pension brute"
                    min={12000}
                    max={48000}
                    step={1200}
                    value={reforms.dp6_threshold_annual}
                    onChange={(e) => setRef('dp6_threshold_annual', Number(e.target.value))}
                  />
                </div>
                {dp6ClawbackShare !== null && dp6ClawbackShare !== undefined && (
                  <p className="pe-callout-info">
                    Retour fiscal mécanique observé sur ce foyer (moindre IR + CSG/CRDS/CASA) :{' '}
                    <strong>{fmtPct(dp6ClawbackShare * 100, { decimals: 1 })}</strong> de la baisse
                    brute (bande calibrée D-P6 : 35 %–45 %).
                  </p>
                )}
              </>
            )}
          </div>
        </div>
      )}
    </aside>
  )
}
