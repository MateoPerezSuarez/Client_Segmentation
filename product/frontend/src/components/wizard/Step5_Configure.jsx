import { useEffect, useState } from 'react'
import {
  ComposedChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ReferenceLine, Legend, ResponsiveContainer,
} from 'recharts'
import { previewKScores, runSegmentation } from '../../api/segmentation'
import { useSessionStore } from '../../store/sessionStore'
import { useWizardStore } from '../../store/wizardStore'
import { useT } from '../../i18n/useT'
import Spinner from '../ui/Spinner'

function SliderField({ label, min, max, value, onChange, hint }) {
  return (
    <div style={{ marginBottom: 20 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
        <label style={{ fontWeight: 600, fontSize: 13 }}>{label}</label>
        <span style={{ color: 'var(--accent)', fontWeight: 700 }}>{value}</span>
      </div>
      <input
        type="range" min={min} max={max} value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        style={{ width: '100%', accentColor: 'var(--accent)' }}
      />
      {hint && <p style={{ color: 'var(--text-muted)', fontSize: 12, marginTop: 4 }}>{hint}</p>}
    </div>
  )
}

function SelectField({ label, value, onChange, options, hint }) {
  return (
    <div style={{ marginBottom: 20 }}>
      <label style={{ fontWeight: 600, fontSize: 13, display: 'block', marginBottom: 6 }}>{label}</label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        style={{ width: '100%', background: 'var(--surface-2)', border: '1px solid var(--border)', borderRadius: 6, color: 'var(--text)', padding: '8px 10px' }}
      >
        {options.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
      </select>
      {hint && <p style={{ color: 'var(--text-muted)', fontSize: 12, marginTop: 4 }}>{hint}</p>}
    </div>
  )
}

const DEFAULT_SEGMENTS = [
  { pattern: '[4-5][4-5][4-5]', name: 'Champions',           enabled: true },
  { pattern: '[2-3][4-5][4-5]', name: 'Loyal Customers',     enabled: true },
  { pattern: '[4-5][2-5][4-5]', name: 'Potential Loyalists', enabled: true },
  { pattern: '[4-5][2-5][1-3]', name: 'Recent Customers',    enabled: true },
  { pattern: '[2-3][2-3][4-5]', name: 'Occasional Customers',enabled: true },
  { pattern: '[2-4][1-5][1-4]', name: 'Potential Customers', enabled: true },
  { pattern: '[2-3][4-5][2-3]', name: 'Economic Loyalists',  enabled: true },
  { pattern: '[1][4-5][4-5]',   name: 'Risky Customers',     enabled: true },
  { pattern: '[1-2][1-3][4-5]', name: 'Nearly Lost',         enabled: true },
  { pattern: '[1-2][4-5][1-3]', name: 'Need Attention',      enabled: true },
  { pattern: '[3-4][1-3][1-3]', name: 'Average Customers',   enabled: true },
  { pattern: '[1-3][1-3][1-3]', name: 'Non Active',          enabled: true },
  { pattern: '[1-3][1-3][1-2]', name: 'Sleeping',            enabled: true },
  { pattern: '[4-5][1][1-5]',   name: 'New Customers',       enabled: true },
  { pattern: '[1][1][1]',       name: 'Lost',                 enabled: true },
]

const DEFAULT_CONFIG = {
  rfm_quintiles: { segments: DEFAULT_SEGMENTS },
  rfm_kmeans: { algorithm: 'kmeans', k_min: 2, k_max: 10, selection_method: 'combined', k_override: null, eps: 0.5, min_samples: 5 },
  abc: { a_threshold: 0.80, b_threshold: 0.95 },
  lrfms: { n_intervals: 4, p_value: 3, k_min: 2, k_max: 10, selection_method: 'combined', s_weight: 0 },
}

// ─── Elbow / k-scores chart ────────────────────────────────────────────────────

function normalise(arr) {
  const mn = Math.min(...arr), mx = Math.max(...arr)
  if (mx === mn) return arr.map(() => 1)
  return arr.map((v) => (v - mn) / (mx - mn))
}

function ElbowChart({ kScores, optimalK, onPickK }) {
  const t = useT()
  const tk = t.step5.kmeans
  if (!kScores) return null
  const wcssNorm = normalise(kScores.wcss)
  const data = kScores.ks.map((k, i) => ({
    k,
    'WCSS (norm)': +wcssNorm[i].toFixed(3),
    'Silhouette': +kScores.silhouette[i].toFixed(3),
    'Combined': +kScores.combined[i].toFixed(3),
  }))

  return (
    <div style={{ marginTop: 20 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
        <p style={{ fontWeight: 600, fontSize: 13 }}>{tk.kPreviewTitle}</p>
        {optimalK && (
          <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
            {tk.autoSelected} <strong style={{ color: 'var(--accent)' }}>k = {optimalK}</strong>
          </span>
        )}
      </div>
      <ResponsiveContainer width="100%" height={220}>
        <ComposedChart data={data} margin={{ top: 4, right: 16, bottom: 8, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
          <XAxis dataKey="k" tick={{ fontSize: 11 }} label={{ value: 'k (clusters)', position: 'insideBottom', offset: -4, fontSize: 11 }} />
          <YAxis tick={{ fontSize: 11 }} domain={[0, 1]} />
          <Tooltip wrapperStyle={{ fontSize: 12 }} />
          <Legend wrapperStyle={{ fontSize: 11 }} />
          <Line type="monotone" dataKey="WCSS (norm)" stroke="#003f5c" strokeWidth={2} dot={{ r: 3 }} />
          <Line type="monotone" dataKey="Silhouette" stroke="#f95d6a" strokeWidth={2} dot={{ r: 3 }} />
          <Line type="monotone" dataKey="Combined" stroke="#ffa600" strokeWidth={2} strokeDasharray="5 3" dot={{ r: 3 }} />
          {optimalK && (
            <ReferenceLine x={optimalK} stroke="var(--accent)" strokeWidth={2} strokeDasharray="4 3"
              label={{ value: `k=${optimalK}`, position: 'top', fontSize: 11, fontWeight: 700, fill: 'var(--accent)' }}
            />
          )}
        </ComposedChart>
      </ResponsiveContainer>

      <div style={{ marginTop: 12, display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
        <span style={{ fontSize: 13, color: 'var(--text-sub)' }}>{tk.overrideK}</span>
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
          <button
            onClick={() => onPickK(null)}
            style={{
              padding: '4px 12px', fontSize: 12, borderRadius: 6, cursor: 'pointer',
              background: optimalK == null ? 'var(--accent)' : 'var(--surface-2)',
              color: optimalK == null ? '#fff' : 'var(--text-sub)',
              border: '1px solid var(--border)', fontWeight: 600,
            }}
          >{tk.auto}</button>
          {kScores.ks.map((k) => (
            <button
              key={k}
              onClick={() => onPickK(k)}
              style={{
                padding: '4px 12px', fontSize: 12, borderRadius: 6, cursor: 'pointer',
                background: optimalK === k ? 'var(--accent)' : 'var(--surface-2)',
                color: optimalK === k ? '#fff' : 'var(--text-sub)',
                border: '1px solid var(--border)',
              }}
            >{k}</button>
          ))}
        </div>
      </div>
    </div>
  )
}

// ─── Segment editor (RFM Quintiles only) ──────────────────────────────────────

function parsePattern(pattern) {
  const m = pattern.match(/^\[([^\]]+)\]\[([^\]]+)\]\[([^\]]+)\]$/)
  return m ? { r: m[1], f: m[2], m: m[3] } : { r: '', f: '', m: '' }
}
function buildPattern(r, f, m) {
  return `[${r}][${f}][${m}]`
}

const CELL_INPUT = {
  background: 'var(--surface-2)',
  border: '1px solid var(--border)',
  borderRadius: 5,
  color: 'var(--text)',
  padding: '5px 6px',
  fontSize: 13,
  fontFamily: 'monospace',
  textAlign: 'center',
  outline: 'none',
  width: '100%',
}

const NAME_INPUT = {
  background: 'var(--surface-2)',
  border: '1px solid var(--border)',
  borderRadius: 5,
  color: 'var(--text)',
  padding: '5px 8px',
  fontSize: 13,
  fontFamily: 'inherit',
  outline: 'none',
  width: '100%',
}

const COL = '24px 1fr 72px 72px 72px 32px'

function HeaderRow() {
  const t = useT()
  const ts = t.step5.segments
  const cell = (label, hint) => (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
      <span style={{ fontSize: 12, fontWeight: 700, color: 'var(--text)', letterSpacing: 0.3 }}>{label}</span>
      {hint && <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>{hint}</span>}
    </div>
  )
  return (
    <div style={{ display: 'grid', gridTemplateColumns: COL, gap: 8, padding: '0 6px 6px', borderBottom: '2px solid var(--border)', marginBottom: 6 }}>
      <span />
      <span style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 0.5 }}>{ts.colName}</span>
      {cell(ts.colR, ts.colRecency)}
      {cell(ts.colF, ts.colFreq)}
      {cell(ts.colM, ts.colMonetary)}
      <span />
    </div>
  )
}

function SegmentEditor({ segments, onChange }) {
  const t = useT()
  const ts = t.step5.segments
  const [newR, setNewR] = useState('')
  const [newF, setNewF] = useState('')
  const [newM, setNewM] = useState('')
  const [newName, setNewName] = useState('')

  const updateRFM = (i, field, value) => {
    const seg = segments[i]
    const parts = parsePattern(seg.pattern)
    parts[field] = value
    const next = segments.map((s, idx) =>
      idx === i ? { ...s, pattern: buildPattern(parts.r, parts.f, parts.m) } : s
    )
    onChange(next)
  }

  const updateName = (i, value) => {
    onChange(segments.map((s, idx) => idx === i ? { ...s, name: value } : s))
  }

  const toggleEnabled = (i, value) => {
    onChange(segments.map((s, idx) => idx === i ? { ...s, enabled: value } : s))
  }

  const remove = (i) => onChange(segments.filter((_, idx) => idx !== i))

  const canAdd = newR.trim() && newF.trim() && newM.trim() && newName.trim()
  const add = () => {
    if (!canAdd) return
    onChange([...segments, {
      pattern: buildPattern(newR.trim(), newF.trim(), newM.trim()),
      name: newName.trim(),
      enabled: true,
    }])
    setNewR(''); setNewF(''); setNewM(''); setNewName('')
  }

  return (
    <div>
      <div style={{
        background: 'var(--surface-2)', borderRadius: 8, padding: '12px 16px',
        marginBottom: 18, border: '1px solid var(--border)',
        display: 'flex', gap: 24, flexWrap: 'wrap',
      }}>
        <span style={{ fontSize: 13, color: 'var(--text-sub)' }}>
          <strong>{ts.guideScores}</strong>
        </span>
        <span style={{ fontSize: 13, color: 'var(--text-sub)' }}>
          {ts.guideSingle} <code style={{ fontFamily: 'monospace', fontWeight: 700 }}>5</code>
        </span>
        <span style={{ fontSize: 13, color: 'var(--text-sub)' }}>
          {ts.guideRange} <code style={{ fontFamily: 'monospace', fontWeight: 700 }}>4-5</code>
        </span>
        <span style={{ fontSize: 13, color: 'var(--text-muted)' }}>
          {ts.guideMatter}
        </span>
      </div>

      <HeaderRow />

      <div style={{ display: 'flex', flexDirection: 'column', gap: 5, marginBottom: 16 }}>
        {segments.map((seg, i) => {
          const { r, f, m } = parsePattern(seg.pattern)
          return (
            <div key={i} style={{
              display: 'grid', gridTemplateColumns: COL,
              gap: 8, alignItems: 'center',
              background: seg.enabled ? 'var(--surface-2)' : 'transparent',
              border: '1px solid var(--border)',
              borderRadius: 7, padding: '5px 6px',
              opacity: seg.enabled ? 1 : 0.4,
              transition: 'opacity 0.15s',
            }}>
              <input
                type="checkbox"
                checked={seg.enabled}
                onChange={(e) => toggleEnabled(i, e.target.checked)}
                style={{ width: 15, height: 15, accentColor: 'var(--accent)', cursor: 'pointer', justifySelf: 'center' }}
              />
              <input value={seg.name} onChange={(e) => updateName(i, e.target.value)} style={NAME_INPUT} />
              <input value={r} onChange={(e) => updateRFM(i, 'r', e.target.value)} style={CELL_INPUT} placeholder="e.g. 4-5" />
              <input value={f} onChange={(e) => updateRFM(i, 'f', e.target.value)} style={CELL_INPUT} placeholder="e.g. 3" />
              <input value={m} onChange={(e) => updateRFM(i, 'm', e.target.value)} style={CELL_INPUT} placeholder="e.g. 1-3" />
              <button
                onClick={() => remove(i)}
                style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', fontSize: 16, cursor: 'pointer', padding: 0, justifySelf: 'center' }}
                title="Remove"
              >×</button>
            </div>
          )
        })}
      </div>

      <div style={{ borderTop: '1px solid var(--border)', paddingTop: 14 }}>
        <p style={{ fontWeight: 600, fontSize: 13, marginBottom: 8 }}>{ts.addTitle}</p>
        <div style={{ display: 'grid', gridTemplateColumns: COL, gap: 8, alignItems: 'center' }}>
          <span />
          <input value={newName} onChange={(e) => setNewName(e.target.value)} placeholder={ts.namePlaceholder} style={NAME_INPUT} onKeyDown={(e) => e.key === 'Enter' && add()} />
          <input value={newR} onChange={(e) => setNewR(e.target.value)} placeholder="R" style={CELL_INPUT} onKeyDown={(e) => e.key === 'Enter' && add()} />
          <input value={newF} onChange={(e) => setNewF(e.target.value)} placeholder="F" style={CELL_INPUT} onKeyDown={(e) => e.key === 'Enter' && add()} />
          <input value={newM} onChange={(e) => setNewM(e.target.value)} placeholder="M" style={CELL_INPUT} onKeyDown={(e) => e.key === 'Enter' && add()} />
          <button
            onClick={add}
            disabled={!canAdd}
            style={{
              background: canAdd ? 'var(--accent)' : 'var(--border)',
              color: canAdd ? '#fff' : 'var(--text-muted)',
              border: 'none', borderRadius: 5,
              width: 32, height: 30, fontSize: 18, cursor: canAdd ? 'pointer' : 'not-allowed',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}
          >+</button>
        </div>
      </div>
    </div>
  )
}

// ──────────────────────────────────────────────────────────────────────────────

export default function Step5_Configure() {
  const sessionId = useSessionStore((s) => s.sessionId)
  const method = useWizardStore((s) => s.method)
  const treatNegativesAsReturns = useWizardStore((s) => s.treatNegativesAsReturns)
  const methodConfig = useWizardStore((s) => s.methodConfig)
  const setMethodConfig = useWizardStore((s) => s.setMethodConfig)
  const setSegmentResult = useWizardStore((s) => s.setSegmentResult)
  const nextStep = useWizardStore((s) => s.nextStep)
  const prevStep = useWizardStore((s) => s.prevStep)
  const loading = useWizardStore((s) => s.loading)
  const setLoading = useWizardStore((s) => s.setLoading)
  const error = useWizardStore((s) => s.error)
  const setError = useWizardStore((s) => s.setError)
  const t = useT()
  const t5 = t.step5

  const [previewScores, setPreviewScores] = useState(null)
  const [previewLoading, setPreviewLoading] = useState(false)

  useEffect(() => {
    if (!Object.keys(methodConfig).length) {
      setMethodConfig(DEFAULT_CONFIG[method] ?? {})
    }
  }, [method])

  const cfg = { ...(DEFAULT_CONFIG[method] ?? {}), ...methodConfig }
  const set = (k) => (v) => setMethodConfig({ ...cfg, [k]: v })

  const previewK = async () => {
    setPreviewLoading(true)
    setError(null)
    try {
      const scores = await previewKScores(sessionId, cfg.k_min, cfg.k_max)
      setPreviewScores(scores)
    } catch (e) {
      setError(e.response?.data?.detail ?? 'Preview failed.')
    } finally {
      setPreviewLoading(false)
    }
  }

  const run = async () => {
    setLoading(true)
    setError(null)
    try {
      let payload = { ...cfg }

      if (method === 'rfm_quintiles') {
        const enabled = (cfg.segments ?? DEFAULT_SEGMENTS).filter((s) => s.enabled)
        payload = { custom_segments: enabled.map(({ pattern, name }) => ({ pattern, name })) }
      }

      if (method === 'lrfms') {
        payload.treat_negatives_as_returns = treatNegativesAsReturns
      }

      const result = await runSegmentation(method, sessionId, payload)
      setSegmentResult(result)
      nextStep()
    } catch (e) {
      setError(e.response?.data?.detail ?? 'Segmentation failed.')
    } finally {
      setLoading(false)
    }
  }

  const methodName = t.step1.methods[method]?.name ?? method
  const K_METHODS = t5.kMethods

  return (
    <div>
      <h2 style={{ fontSize: 22, fontWeight: 800, marginBottom: 6 }}>{t5.titlePrefix} {methodName}</h2>
      <p style={{ color: 'var(--text-sub)', marginBottom: 28 }}>{t5.subtitles[method]}</p>

      <div style={{ background: 'var(--surface)', borderRadius: 'var(--radius)', padding: '24px', border: '1px solid var(--border)', marginBottom: 24 }}>
        {method === 'rfm_quintiles' && (
          <SegmentEditor
            segments={cfg.segments ?? DEFAULT_SEGMENTS}
            onChange={(segs) => setMethodConfig({ ...cfg, segments: segs })}
          />
        )}

        {method === 'rfm_kmeans' && (
          <>
            <div style={{ marginBottom: 22 }}>
              <label style={{ fontWeight: 600, fontSize: 13, display: 'block', marginBottom: 8 }}>{t5.kmeans.algorithm}</label>
              <div style={{ display: 'flex', gap: 8 }}>
                {[{ value: 'kmeans', label: 'K-Means' }, { value: 'dbscan', label: 'DBSCAN' }].map((opt) => (
                  <button
                    key={opt.value}
                    onClick={() => { set('algorithm')(opt.value); setPreviewScores(null) }}
                    style={{
                      padding: '7px 20px', borderRadius: 7, fontWeight: 600, fontSize: 13, cursor: 'pointer',
                      background: cfg.algorithm === opt.value ? 'var(--accent)' : 'var(--surface-2)',
                      color: cfg.algorithm === opt.value ? '#fff' : 'var(--text-sub)',
                      border: `1px solid ${cfg.algorithm === opt.value ? 'var(--accent)' : 'var(--border)'}`,
                    }}
                  >{opt.label}</button>
                ))}
              </div>
            </div>

            {cfg.algorithm === 'kmeans' && (
              <>
                <SliderField label={t5.kmeans.minK} min={2} max={8} value={cfg.k_min}
                  onChange={(v) => { set('k_min')(v); setPreviewScores(null) }} />
                <SliderField label={t5.kmeans.maxK} min={cfg.k_min + 1} max={15} value={cfg.k_max}
                  onChange={(v) => { set('k_max')(v); setPreviewScores(null) }} />
                <SelectField label={t5.kmeans.selectionMethod} value={cfg.selection_method}
                  onChange={set('selection_method')} options={K_METHODS}
                  hint={t5.kmeans.selectionHint} />

                <button
                  onClick={previewK}
                  disabled={previewLoading}
                  style={{
                    background: 'transparent', border: '1px solid var(--accent)', color: 'var(--accent)',
                    borderRadius: 7, padding: '7px 18px', fontWeight: 600, fontSize: 13, cursor: 'pointer',
                    display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4,
                  }}
                >
                  {previewLoading ? <Spinner size={14} dark /> : '↗'}
                  {previewLoading ? t5.kmeans.previewing : t5.kmeans.previewBtn}
                </button>

                {previewScores && (
                  <ElbowChart
                    kScores={previewScores}
                    optimalK={cfg.k_override}
                    onPickK={(k) => set('k_override')(k)}
                  />
                )}
              </>
            )}

            {cfg.algorithm === 'dbscan' && (
              <>
                <SliderField
                  label={t5.kmeans.eps}
                  min={1} max={50} value={Math.round(cfg.eps * 10)}
                  onChange={(v) => set('eps')(v / 10)}
                  hint={t5.kmeans.epsHint.replace('{eps}', cfg.eps.toFixed(1))}
                />
                <SliderField
                  label={t5.kmeans.minSamples}
                  min={2} max={30} value={cfg.min_samples}
                  onChange={set('min_samples')}
                  hint={t5.kmeans.minSamplesHint}
                />
                <div style={{ background: 'var(--surface-2)', borderRadius: 7, padding: '10px 14px', border: '1px solid var(--border)', fontSize: 13, color: 'var(--text-sub)' }}>
                  {t5.kmeans.dbscanInfo}
                </div>
              </>
            )}
          </>
        )}

        {method === 'abc' && (
          <>
            <SliderField
              label={t5.abc.aThreshold}
              min={50} max={90} value={Math.round(cfg.a_threshold * 100)}
              onChange={(v) => set('a_threshold')(v / 100)}
              hint={t5.abc.aHint}
            />
            <SliderField
              label={t5.abc.bThreshold}
              min={Math.round(cfg.a_threshold * 100) + 1} max={99}
              value={Math.round(cfg.b_threshold * 100)}
              onChange={(v) => set('b_threshold')(v / 100)}
              hint={t5.abc.bHint}
            />
          </>
        )}

        {method === 'lrfms' && (
          <>
            <SliderField label={t5.lrfms.intervals} min={2} max={12} value={cfg.n_intervals} onChange={set('n_intervals')}
              hint={t5.lrfms.intervalsHint} />
            <SliderField label={t5.lrfms.pValue} min={1} max={10} value={cfg.p_value} onChange={set('p_value')}
              hint={t5.lrfms.pHint} />
            <SliderField label={t5.lrfms.minK} min={2} max={8} value={cfg.k_min} onChange={set('k_min')} />
            <SliderField label={t5.lrfms.maxK} min={cfg.k_min + 1} max={15} value={cfg.k_max} onChange={set('k_max')} />
            <SelectField label={t5.lrfms.kMethod} value={cfg.selection_method} onChange={set('selection_method')} options={K_METHODS} />

            <div style={{ borderTop: '1px solid var(--border)', paddingTop: 20, marginTop: 4 }}>
              <p style={{ fontWeight: 700, fontSize: 13, marginBottom: 4 }}>{t5.lrfms.sSection}</p>
              <p style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 16 }}>
                {t5.lrfms.sSectionHint}
              </p>

              {treatNegativesAsReturns ? (
                <div style={{
                  display: 'flex', alignItems: 'flex-start', gap: 10, marginBottom: 16,
                  padding: '8px 12px', borderRadius: 6,
                  background: '#d4edda', border: '1px solid #a3d4ae',
                }}>
                  <span style={{ fontSize: 16, lineHeight: 1.4 }}>↩</span>
                  <span style={{ fontSize: 13, color: '#1a4d2e' }}>
                    <strong>{t5.lrfms.returnsEnabled}</strong>{t5.lrfms.returnsEnabledSub}
                    <span style={{ display: 'block', fontSize: 11, color: '#2a7a3b', marginTop: 2 }}>
                      {t5.lrfms.returnsEnabledNote}
                    </span>
                  </span>
                </div>
              ) : (
                <div style={{
                  display: 'flex', alignItems: 'flex-start', gap: 10, marginBottom: 16,
                  padding: '8px 12px', borderRadius: 6,
                  background: 'var(--surface-2)', border: '1px solid var(--border)',
                }}>
                  <span style={{ fontSize: 16, lineHeight: 1.4 }}>ℹ</span>
                  <span style={{ fontSize: 13, color: 'var(--text-muted)' }}>
                    {t5.lrfms.returnsDisabled}
                    <span style={{ display: 'block', fontSize: 11, marginTop: 2 }}>
                      {t5.lrfms.returnsDisabledNote}
                    </span>
                  </span>
                </div>
              )}

              <div style={{ marginBottom: 8 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                  <label style={{ fontWeight: 600, fontSize: 13 }}>{t5.lrfms.sWeight}</label>
                  <span style={{ color: cfg.s_weight === 0 ? 'var(--text-muted)' : 'var(--accent)', fontWeight: 700 }}>
                    {cfg.s_weight === 0 ? t5.lrfms.sDisabled : cfg.s_weight.toFixed(1)}
                  </span>
                </div>
                <input
                  type="range" min={0} max={20} step={1}
                  value={Math.round(cfg.s_weight * 10)}
                  onChange={(e) => set('s_weight')(Number(e.target.value) / 10)}
                  style={{ width: '100%', accentColor: 'var(--accent)' }}
                />
                <p style={{ color: 'var(--text-muted)', fontSize: 12, marginTop: 4 }}>
                  {t5.lrfms.sWeightHint}
                </p>
              </div>

              {cfg.s_weight > 0 && (
                <div style={{ background: 'var(--surface-2)', borderRadius: 7, padding: '12px 14px', border: '1px solid var(--border)', fontSize: 12 }}>
                  <p style={{ fontWeight: 600, marginBottom: 8, color: 'var(--text-sub)' }}>{t5.lrfms.rateTable}</p>
                  <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                    <thead>
                      <tr style={{ color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 0.4 }}>
                        <th style={{ textAlign: 'left', paddingBottom: 4 }}>{t5.lrfms.rateReturn}</th>
                        <th style={{ textAlign: 'center', paddingBottom: 4 }}>{t5.lrfms.rateScore}</th>
                        <th style={{ textAlign: 'left', paddingBottom: 4 }}>{t5.lrfms.rateInterp}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {t5.lrfms.rates.map(([rate, score, interp]) => (
                        <tr key={rate} style={{ borderTop: '1px solid var(--border)' }}>
                          <td style={{ padding: '4px 0', fontFamily: 'monospace' }}>{rate}</td>
                          <td style={{ padding: '4px 0', textAlign: 'center', fontWeight: 700 }}>{score}</td>
                          <td style={{ padding: '4px 0', color: 'var(--text-muted)' }}>{interp}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </>
        )}
      </div>

      {error && (
        <div style={{ background: '#f2f2f2', border: '1px solid #bbbbbb', borderRadius: 8, padding: '12px 16px', marginBottom: 20, color: 'var(--text)' }}>
          {error}
        </div>
      )}

      <div style={{ display: 'flex', gap: 12 }}>
        <button onClick={prevStep} style={{ background: 'transparent', border: '1px solid var(--border)', color: 'var(--text-sub)', borderRadius: 8, padding: '10px 22px', fontWeight: 500 }}>
          {t.back}
        </button>
        <button
          disabled={loading}
          onClick={run}
          style={{
            background: loading ? 'var(--border)' : 'var(--accent)',
            color: loading ? 'var(--text-muted)' : '#fff',
            border: 'none', borderRadius: 8, padding: '10px 28px',
            fontWeight: 600, display: 'flex', alignItems: 'center', gap: 8,
          }}
        >
          {loading && <Spinner size={16} />}
          {loading ? t5.running : t5.runBtn}
        </button>
      </div>
    </div>
  )
}
