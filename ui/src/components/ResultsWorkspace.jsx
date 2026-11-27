import { memo, useMemo, useState } from 'react'
import {
  Area,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ComposedChart,
  Legend,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import InfoPopover from './InfoPopover.jsx'
import { fmtEur, fmtPct, scalePeriod } from '../lib/format.js'
import { LEDGER_ROWS } from '../lib/ledgerRows.js'

const COLORS = {
  marine: '#1a2744',
  indigo: '#365399',
  emerald: '#1e6b4b',
  teal: '#2b7a78',
  amber: '#b45309',
  crimson: '#b5281e',
  slate: '#6b6560',
  border: '#e2ddd5',
}

function DeltaBadge({ deltaAnnual, periodMode, lowerIsBetter = false }) {
  if (deltaAnnual === null || deltaAnnual === undefined || Math.abs(deltaAnnual) < 0.5) {
    return <span className="pe-delta pe-delta-neutral">inchangé vs droit courant</span>
  }
  const scaled = scalePeriod(deltaAnnual, periodMode)
  const good = lowerIsBetter ? deltaAnnual < 0 : deltaAnnual > 0
  return (
    <span className={`pe-delta ${good ? 'pe-delta-good' : 'pe-delta-bad'}`}>
      {fmtEur(scaled, { signed: true })} / {periodMode === 'month' ? 'mois' : 'an'} vs réf.
    </span>
  )
}

function HeadlineStrip({ result, periodMode }) {
  const active = result.reform_active && result.reform ? result.reform : result.baseline
  const deltas = result.reform_active ? result.deltas : null
  const suffix = periodMode === 'month' ? 'par mois' : 'par an'

  return (
    <section className="pe-headline-grid" aria-label="Indicateurs clés du ménage">
      <article className="pe-kpi-card pe-kpi-primary">
        <span className="pe-kpi-label">Revenu disponible net</span>
        <strong className="pe-kpi-value">
          {fmtEur(scalePeriod(active.revenu_disponible, periodMode))}
        </strong>
        <span className="pe-kpi-sub">{suffix}, après impôts et prestations</span>
        {deltas && <DeltaBadge deltaAnnual={deltas.revenu_disponible} periodMode={periodMode} />}
      </article>

      <article className="pe-kpi-card">
        <span className="pe-kpi-label">Prélèvements totaux</span>
        <strong className="pe-kpi-value pe-text-crimson">
          {fmtEur(scalePeriod(active.prelevements_totaux, periodMode))}
        </strong>
        <span className="pe-kpi-sub">
          Taux effectif : <strong>{fmtPct(active.taux_prelevement_effectif)}</strong> du revenu brut
        </span>
        {deltas && (
          <DeltaBadge
            deltaAnnual={deltas.prelevements_totaux}
            periodMode={periodMode}
            lowerIsBetter
          />
        )}
      </article>

      <article className="pe-kpi-card">
        <span className="pe-kpi-label">Prestations sociales (CNAF)</span>
        <strong className="pe-kpi-value pe-text-emerald">
          {fmtEur(scalePeriod(active.prestations_totales, periodMode))}
        </strong>
        <span className="pe-kpi-sub">AF, ASF, RSA et Prime d’activité cumulés</span>
        {deltas && <DeltaBadge deltaAnnual={deltas.prestations_totales} periodMode={periodMode} />}
      </article>

      <article className="pe-kpi-card">
        <span className="pe-kpi-label">Coût employeur (super-brut)</span>
        <strong className="pe-kpi-value">
          {fmtEur(scalePeriod(active.cout_employeur_net, periodMode))}
        </strong>
        <span className="pe-kpi-sub">
          Allègement Fillon :{' '}
          <strong>{fmtEur(scalePeriod(active.reduction_generale, periodMode))}</strong>
        </span>
        <span className="pe-kpi-meta">Quotient familial : {active.nombre_parts} part(s)</span>
      </article>
    </section>
  )
}

function OverviewWaterfall({ result, periodMode }) {
  const active = result.reform_active && result.reform ? result.reform : result.baseline
  const unit = periodMode === 'month' ? '€/mois' : '€/an'

  const steps = useMemo(() => {
    const items = [
      {
        name: 'Coût employeur',
        val: scalePeriod(active.cout_employeur_net, periodMode),
        color: COLORS.slate,
      },
      {
        name: 'Revenu primaire brut',
        val: scalePeriod(active.revenu_primaire_brut, periodMode),
        color: COLORS.indigo,
      },
      {
        name: 'Cotis. & CSG/CRDS',
        val: -scalePeriod(active.cotisations_et_ps_activite + active.ps_retraite, periodMode),
        color: COLORS.amber,
      },
      {
        name: 'IR, PFU, IFI & local',
        val: -scalePeriod(active.impots_directs_et_locaux, periodMode),
        color: COLORS.crimson,
      },
      {
        name: 'Prestations CNAF',
        val: scalePeriod(active.prestations_totales, periodMode),
        color: COLORS.emerald,
      },
      {
        name: 'Revenu disponible',
        val: scalePeriod(active.revenu_disponible, periodMode),
        color: COLORS.marine,
      },
    ]
    return items.filter((d, idx) => idx === 1 || idx === 5 || Math.abs(d.val) >= 1)
  }, [active, periodMode])

  const reformDiffs = useMemo(() => {
    if (!result.reform_active || !result.deltas) return []
    const watch = [
      { key: 'impot_revenu', label: 'Impôt sur le revenu' },
      { key: 'csg', label: 'CSG activité' },
      { key: 'pension_retraite_nette', label: 'Pension de retraite nette' },
      { key: 'taxe_fonciere', label: 'Taxe foncière' },
      { key: 'taxe_habitation_residence_secondaire', label: 'TH résidence secondaire' },
      { key: 'ifi', label: 'IFI' },
      { key: 'impot_plus_values_immobilieres', label: 'IR plus-values immo.' },
      { key: 'prelevements_sociaux_patrimoine', label: 'Prélèvements sociaux patrimoine' },
      { key: 'taxe_valeur_sol', label: 'Taxe valeur du sol (LVT)' },
      { key: 'rsa', label: 'RSA' },
      { key: 'prime_activite', label: 'Prime d’activité' },
      { key: 'allocations_familiales', label: 'Allocations familiales' },
    ]
    return watch
      .map((w) => ({
        ...w,
        delta: scalePeriod(result.deltas[w.key] || 0, periodMode),
      }))
      .filter((w) => Math.abs(w.delta) >= 0.5)
  }, [result, periodMode])

  return (
    <div className="pe-panel-stack">
      {result.reform_active && result.reform && (
        <section className="pe-card pe-reform-banner">
          <div className="pe-reform-banner-top">
            <div>
              <h3>Impact net de la réforme sur ce ménage</h3>
              <p className="pe-muted-note">
                Comparaison directe entre le droit courant ({result.year}) et votre scénario de
                réforme.
              </p>
            </div>
            <div className="pe-reform-big-delta">
              <span
                className={
                  result.deltas.revenu_disponible >= 0 ? 'pe-text-emerald' : 'pe-text-crimson'
                }
              >
                {fmtEur(scalePeriod(result.deltas.revenu_disponible, periodMode), { signed: true })}{' '}
                <small>/ {periodMode === 'month' ? 'mois' : 'an'}</small>
              </span>
              <span className="pe-muted-note">
                Droit courant :{' '}
                {fmtEur(scalePeriod(result.baseline.revenu_disponible, periodMode))} → Réforme :{' '}
                <strong>{fmtEur(scalePeriod(result.reform.revenu_disponible, periodMode))}</strong>
              </span>
            </div>
          </div>

          {reformDiffs.length > 0 && (
            <div className="pe-diff-pills">
              {reformDiffs.map((d) => (
                <div key={d.key} className="pe-diff-chip">
                  <span>{d.label}</span>
                  <strong>{fmtEur(d.delta, { signed: true })}</strong>
                </div>
              ))}
            </div>
          )}
        </section>
      )}

      <section className="pe-card">
        <div className="pe-card-head">
          <div>
            <h3>Du coût du travail au revenu disponible ({unit})</h3>
            <p className="pe-muted-note">
              Décomposition complète des prélèvements sociaux, fiscaux et des transferts CNAF.
            </p>
          </div>
        </div>

        <div className="pe-chart-box">
          <ResponsiveContainer width="100%" height={290}>
            <BarChart data={steps} margin={{ top: 12, right: 18, left: 8, bottom: 6 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={COLORS.border} />
              <XAxis dataKey="name" tick={{ fontSize: 12, fill: COLORS.slate }} />
              <YAxis
                tick={{ fontSize: 11, fill: COLORS.slate }}
                tickFormatter={(v) => fmtEur(v)}
                width={84}
              />
              <Tooltip
                formatter={(v) => [fmtEur(v, { signed: v < 0 }), 'Montant']}
                contentStyle={{ borderRadius: 6, borderColor: COLORS.border }}
              />
              <ReferenceLine y={0} stroke={COLORS.marine} strokeWidth={1} />
              <Bar dataKey="val" radius={[4, 4, 0, 0]} isAnimationActive={false}>
                {steps.map((entry) => (
                  <Cell key={entry.name} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="pe-mini-breakdown">
          <div className="pe-mini-col">
            <h4>Revenus primaires</h4>
            <dl>
              <div>
                <dt>Salaires bruts</dt>
                <dd>{fmtEur(scalePeriod(active.salaire_brut, periodMode))}</dd>
              </div>
              {active.pension_retraite_effective > 0 && (
                <div>
                  <dt>Pensions de retraite brutes</dt>
                  <dd>{fmtEur(scalePeriod(active.pension_retraite_effective, periodMode))}</dd>
                </div>
              )}
              {active.revenus_capital + active.loyers_economiques + active.plus_values_immobilieres >
                0 && (
                <div>
                  <dt>Capital, loyers nets &amp; plus-values</dt>
                  <dd>
                    {fmtEur(
                      scalePeriod(
                        active.revenus_capital +
                          active.loyers_economiques +
                          active.plus_values_immobilieres,
                        periodMode
                      )
                    )}
                  </dd>
                </div>
              )}
            </dl>
          </div>

          <div className="pe-mini-col">
            <h4>Prélèvements obligatoires</h4>
            <dl>
              <div>
                <dt>Cotisations &amp; CSG/CRDS activité</dt>
                <dd>{fmtEur(scalePeriod(active.cotisations_et_ps_activite, periodMode))}</dd>
              </div>
              {active.ps_retraite > 0 && (
                <div>
                  <dt>CSG / CRDS / CASA retraite</dt>
                  <dd>{fmtEur(scalePeriod(active.ps_retraite, periodMode))}</dd>
                </div>
              )}
              <div>
                <dt>Impôt sur le revenu &amp; CEHR</dt>
                <dd>{fmtEur(scalePeriod(active.impot_revenu + active.cehr, periodMode))}</dd>
              </div>
              {active.pfu_ir +
                active.prelevements_sociaux_patrimoine +
                active.impot_plus_values_immobilieres +
                active.ifi +
                active.taxe_fonciere +
                active.taxe_habitation_residence_secondaire +
                active.taxe_valeur_sol >
                0 && (
                <div>
                  <dt>Patrimoine, PFU, IFI &amp; taxes locales/LVT</dt>
                  <dd>
                    {fmtEur(
                      scalePeriod(
                        active.pfu_ir +
                          active.prelevements_sociaux_patrimoine +
                          active.impot_plus_values_immobilieres +
                          active.ifi +
                          active.taxe_fonciere +
                          active.taxe_habitation_residence_secondaire +
                          active.taxe_valeur_sol,
                        periodMode
                      )
                    )}
                  </dd>
                </div>
              )}
            </dl>
          </div>

          <div className="pe-mini-col">
            <h4>Prestations sociales</h4>
            <dl>
              <div>
                <dt>RSA socle / majoré</dt>
                <dd>{fmtEur(scalePeriod(active.rsa, periodMode))}</dd>
              </div>
              <div>
                <dt>Prime d’activité</dt>
                <dd>{fmtEur(scalePeriod(active.prime_activite, periodMode))}</dd>
              </div>
              <div>
                <dt>Allocations familiales &amp; ASF</dt>
                <dd>
                  {fmtEur(
                    scalePeriod(
                      active.allocations_familiales + active.allocation_soutien_familial,
                      periodMode
                    )
                  )}
                </dd>
              </div>
            </dl>
          </div>
        </div>
      </section>
    </div>
  )
}

function CurvesView({ curve, periodMode, reformActive }) {
  const unit = periodMode === 'month' ? '€/mois' : '€/an'
  const currentX = curve ? Math.round(scalePeriod(curve.current_salaire_brut, periodMode)) : 0

  const chartData = useMemo(() => {
    if (!curve?.points) return []
    return curve.points.map((pt) => {
      const salaireNetApresIr = Math.max(
        0,
        scalePeriod(pt.salaire_net - pt.impot_revenu, periodMode)
      )
      const rsa = scalePeriod(pt.rsa, periodMode)
      const primeActivite = scalePeriod(pt.prime_activite, periodMode)
      const afAsf = scalePeriod(pt.af_asf, periodMode)
      const rd = scalePeriod(pt.revenu_disponible, periodMode)
      const autresRevenus = Math.max(0, rd - salaireNetApresIr - primeActivite - rsa - afAsf)
      return {
        brut: Math.round(scalePeriod(pt.salaire_brut, periodMode)),
        salaire_net_apres_ir: salaireNetApresIr,
        autres_revenus: autresRevenus,
        rsa,
        prime_activite: primeActivite,
        af_asf: afAsf,
        revenu_disponible: rd,
        revenu_disponible_reforme:
          pt.revenu_disponible_reforme !== undefined
            ? scalePeriod(pt.revenu_disponible_reforme, periodMode)
            : undefined,
        emtr_pct: pt.emtr_pct,
        emtr_reforme_pct: pt.emtr_reforme_pct,
      }
    })
  }, [curve, periodMode])

  const hasAutresRevenus = useMemo(
    () => chartData.some((d) => d.autres_revenus > 1),
    [chartData]
  )

  if (!chartData.length) return null

  return (
    <div className="pe-panel-stack">
      <section className="pe-card">
        <div className="pe-card-head">
          <div>
            <h3>Contrainte budgétaire et empilement des prestations ({unit})</h3>
            <p className="pe-muted-note">
              Balayage vectorisé du salaire brut du déclarant 1 (toutes autres caractéristiques du
              foyer maintenues constantes). La ligne verticale marque votre salaire actuel (
              <strong>{fmtEur(currentX)}</strong>).
            </p>
          </div>
        </div>

        <div className="pe-chart-box">
          <ResponsiveContainer width="100%" height={320}>
            <ComposedChart data={chartData} margin={{ top: 10, right: 18, left: 8, bottom: 6 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={COLORS.border} />
              <XAxis
                dataKey="brut"
                type="number"
                domain={['dataMin', 'dataMax']}
                tick={{ fontSize: 11, fill: COLORS.slate }}
                tickFormatter={(v) => fmtEur(v)}
              />
              <YAxis
                tick={{ fontSize: 11, fill: COLORS.slate }}
                tickFormatter={(v) => fmtEur(v)}
                width={84}
              />
              <Tooltip
                labelFormatter={(v) => `Salaire brut : ${fmtEur(v)}`}
                formatter={(val, name) => [fmtEur(val), name]}
              />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <Area
                type="monotone"
                dataKey="salaire_net_apres_ir"
                stackId="1"
                name="Salaire net après IR"
                stroke={COLORS.indigo}
                fill="#dbe4f8"
                isAnimationActive={false}
              />
              {hasAutresRevenus && (
                <Area
                  type="monotone"
                  dataKey="autres_revenus"
                  stackId="1"
                  name="Pensions, capital & foncier nets"
                  stroke={COLORS.slate}
                  fill="#e5e1d8"
                  isAnimationActive={false}
                />
              )}
              <Area
                type="monotone"
                dataKey="prime_activite"
                stackId="1"
                name="Prime d’activité"
                stroke={COLORS.emerald}
                fill="#c6ebd9"
                isAnimationActive={false}
              />
              <Area
                type="monotone"
                dataKey="rsa"
                stackId="1"
                name="RSA"
                stroke={COLORS.teal}
                fill="#bce3e2"
                isAnimationActive={false}
              />
              <Area
                type="monotone"
                dataKey="af_asf"
                stackId="1"
                name="AF & ASF"
                stroke={COLORS.amber}
                fill="#fde8c8"
                isAnimationActive={false}
              />
              <Line
                type="monotone"
                dataKey="revenu_disponible"
                name="Revenu disponible (droit courant)"
                stroke={COLORS.marine}
                strokeWidth={2.5}
                dot={false}
                isAnimationActive={false}
              />
              {reformActive && (
                <Line
                  type="monotone"
                  dataKey="revenu_disponible_reforme"
                  name="Revenu disponible (après réforme)"
                  stroke={COLORS.crimson}
                  strokeWidth={2.2}
                  strokeDasharray="6 4"
                  dot={false}
                  isAnimationActive={false}
                />
              )}
              <ReferenceLine
                x={currentX}
                stroke={COLORS.marine}
                strokeDasharray="3 3"
                label={{
                  value: 'Votre foyer',
                  position: 'insideTopRight',
                  fontSize: 11,
                  fill: COLORS.marine,
                }}
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </section>

      <section className="pe-card">
        <div className="pe-card-head">
          <div>
            <h3>Taux marginal effectif de prélèvement (EMTR, en %)</h3>
            <p className="pe-muted-note">
              Part de chaque euro supplémentaire de salaire brut absorbée par les cotisations, la
              CSG/CRDS, l’impôt sur le revenu et la sortie progressive du RSA / de la Prime
              d’activité (100 % − ΔRevenu disponible / ΔSalaire brut).{' '}
              <em>
                Hors aides au logement (APL non modélisées, qui ajoutent en pratique ~30 pts de
                dégressivité entre 0 et 1,5 SMIC).
              </em>
            </p>
          </div>
        </div>

        <div className="pe-chart-box">
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={chartData} margin={{ top: 10, right: 18, left: 8, bottom: 6 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={COLORS.border} />
              <XAxis
                dataKey="brut"
                type="number"
                domain={['dataMin', 'dataMax']}
                tick={{ fontSize: 11, fill: COLORS.slate }}
                tickFormatter={(v) => fmtEur(v)}
              />
              <YAxis
                tick={{ fontSize: 11, fill: COLORS.slate }}
                tickFormatter={(v) => `${v} %`}
                domain={[0, 100]}
                width={56}
              />
              <Tooltip
                labelFormatter={(v) => `Salaire brut : ${fmtEur(v)}`}
                formatter={(val, name) => [fmtPct(val, { decimals: 1 }), name]}
              />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <ReferenceLine y={50} stroke={COLORS.border} strokeDasharray="4 4" />
              <ReferenceLine x={currentX} stroke={COLORS.marine} strokeDasharray="3 3" />
              <Line
                type="stepAfter"
                dataKey="emtr_pct"
                name="EMTR droit courant"
                stroke={COLORS.indigo}
                strokeWidth={2.25}
                dot={false}
                isAnimationActive={false}
              />
              {reformActive && (
                <Line
                  type="stepAfter"
                  dataKey="emtr_reforme_pct"
                  name="EMTR après réforme"
                  stroke={COLORS.crimson}
                  strokeWidth={2}
                  strokeDasharray="5 4"
                  dot={false}
                  isAnimationActive={false}
                />
              )}
            </LineChart>
          </ResponsiveContainer>
        </div>
      </section>
    </div>
  )
}

function LedgerTable({ result, periodMode, metadata }) {
  const [hideZeros, setHideZeros] = useState(true)
  const varMetaMap = metadata?.variables || {}

  const grouped = useMemo(() => {
    const map = new Map()
    for (const row of LEDGER_ROWS) {
      const b = Number(result.baseline[row.key] || 0)
      const r = result.reform ? Number(result.reform[row.key] || 0) : b
      if (hideZeros && !row.highlight && Math.abs(b) < 0.01 && Math.abs(r) < 0.01) {
        continue
      }
      if (!map.has(row.section)) map.set(row.section, [])
      map.get(row.section).push({ ...row, baseVal: b, refVal: r, diffVal: r - b })
    }
    return [...map.entries()]
  }, [result, hideZeros])

  const fmtCell = (val, row) => {
    const mode = row.annualOnly ? 'year' : periodMode
    return fmtEur(scalePeriod(val, mode)) + (row.annualOnly && periodMode === 'month' ? ' /an' : '')
  }

  return (
    <section className="pe-card">
      <div className="pe-card-head">
        <div>
          <h3>Fiche détaillée — Cotisations, Impôts &amp; Prestations ({result.year})</h3>
          <p className="pe-muted-note">
            Cliquez sur <strong>i</strong> pour consulter la règle légale et le texte officiel
            Légifrance associé à chaque variable du moteur Python.
          </p>
        </div>
        <label className="pe-check-inline">
          <input
            type="checkbox"
            checked={hideZeros}
            onChange={(e) => setHideZeros(e.target.checked)}
          />
          <span>Masquer les lignes à 0 €</span>
        </label>
      </div>

      <div className="pe-table-wrap">
        <table className="pe-table">
          <thead>
            <tr>
              <th scope="col">Poste fiscal ou social</th>
              <th scope="col" className="pe-num">
                Droit courant ({periodMode === 'month' ? '€/mois' : '€/an'})
              </th>
              {result.reform_active && (
                <>
                  <th scope="col" className="pe-num">Après réforme</th>
                  <th scope="col" className="pe-num">Écart</th>
                </>
              )}
            </tr>
          </thead>
          {grouped.map(([sectionTitle, rows]) => (
            <tbody key={sectionTitle}>
              <tr className="pe-section-row">
                <th colSpan={result.reform_active ? 4 : 2} scope="colgroup">
                  {sectionTitle}
                </th>
              </tr>
              {rows.map((row) => {
                const vm = row.varMeta ? varMetaMap[row.varMeta] : null
                return (
                  <tr key={row.key} className={row.highlight ? 'pe-row-highlight' : ''}>
                    <th scope="row">
                      <span>{row.label}</span>
                      {vm && (
                        <InfoPopover
                          label={row.label}
                          doc={vm.documentation}
                          reference={vm.reference}
                        />
                      )}
                    </th>
                    <td className="pe-num">{fmtCell(row.baseVal, row)}</td>
                    {result.reform_active && (
                      <>
                        <td className="pe-num">{fmtCell(row.refVal, row)}</td>
                        <td
                          className={`pe-num ${
                            Math.abs(row.diffVal) < 0.5
                              ? 'pe-muted'
                              : (row.sign === 'levy' ? row.diffVal < 0 : row.diffVal > 0)
                                ? 'pe-text-emerald'
                                : 'pe-text-crimson'
                          }`}
                        >
                          {Math.abs(row.diffVal) < 0.5
                            ? '—'
                            : fmtEur(
                                scalePeriod(row.diffVal, row.annualOnly ? 'year' : periodMode),
                                { signed: true }
                              )}
                        </td>
                      </>
                    )}
                  </tr>
                )
              })}
            </tbody>
          ))}
        </table>
      </div>
    </section>
  )
}

function ScopeTransparencyView({ metadata }) {
  const policies = metadata?.policies
  if (!policies) return null

  return (
    <div className="pe-panel-stack">
      <section className="pe-card">
        <h3>Ce qui est modélisé ({policies.modelled?.length || 0} briques législatives)</h3>
        <p className="pe-muted-note">
          Synchronisé directement avec <code>policyengine_fr/modelled_policies.yaml</code> et
          vérifié face aux simulateurs officiels DGFiP et à <code>openfisca-france</code>.
        </p>
        <ul className="pe-scope-list pe-scope-ok">
          {(policies.modelled || []).map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </section>

      <section className="pe-card">
        <h3>
          Simplifications assumées ({policies.simplifications?.length || 0} écarts documentés à la
          loi)
        </h3>
        <p className="pe-muted-note">
          Aucune approximation implicite : chaque simplification ci-dessous est contrôlée par{' '}
          <code>bin/check_doc_currency.py</code>.
        </p>
        <ol className="pe-scope-list pe-scope-warn">
          {(policies.simplifications || []).map((item, idx) => (
            <li key={idx}>{item}</li>
          ))}
        </ol>
      </section>

      <section className="pe-card">
        <h3>Hors périmètre actuel</h3>
        <ul className="pe-scope-list pe-scope-muted">
          {(policies.not_modelled || []).map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </section>
    </div>
  )
}

const ResultsWorkspace = memo(function ResultsWorkspace({ result, periodMode, metadata }) {
  const [activeTab, setActiveTab] = useState('synthese')

  if (!result?.baseline) {
    return (
      <div className="pe-workspace">
        <div className="pe-card pe-empty-state" role="status">
          Initialisation du moteur PolicyEngine France…
        </div>
      </div>
    )
  }

  return (
    <div className="pe-workspace">
      <HeadlineStrip result={result} periodMode={periodMode} />

      <nav className="pe-view-tabs" aria-label="Vues d’analyse">
        {[
          { id: 'synthese', label: 'Vue d’ensemble & cascade' },
          { id: 'courbes', label: 'Courbes d’activité & taux marginal' },
          { id: 'detail', label: 'Fiche de paie, impôts & prestations' },
          { id: 'perimetre', label: 'Périmètre légal & hypothèses' },
        ].map((t) => (
          <button
            key={t.id}
            type="button"
            className={`pe-view-tab${activeTab === t.id ? ' active' : ''}`}
            aria-pressed={activeTab === t.id}
            onClick={() => setActiveTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </nav>

      {activeTab === 'synthese' && <OverviewWaterfall result={result} periodMode={periodMode} />}
      {activeTab === 'courbes' && (
        <CurvesView
          curve={result.curve}
          periodMode={periodMode}
          reformActive={result.reform_active}
        />
      )}
      {activeTab === 'detail' && (
        <LedgerTable result={result} periodMode={periodMode} metadata={metadata} />
      )}
      {activeTab === 'perimetre' && <ScopeTransparencyView metadata={metadata} />}
    </div>
  )
})

export default ResultsWorkspace
