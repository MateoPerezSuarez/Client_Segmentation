import { useState } from 'react'
import { cleanData } from '../../api/cleaning'
import { useSessionStore } from '../../store/sessionStore'
import { useWizardStore } from '../../store/wizardStore'
import { useT } from '../../i18n/useT'
import Spinner from '../ui/Spinner'

function StatRow({ label, value, sub }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 0', borderBottom: '1px solid var(--border)' }}>
      <span style={{ color: 'var(--text-sub)' }}>{label}</span>
      <span style={{ fontWeight: 600 }}>
        {value}
        {sub && <span style={{ color: 'var(--text-muted)', fontWeight: 400, fontSize: 12, marginLeft: 6 }}>{sub}</span>}
      </span>
    </div>
  )
}

function QualityTable({ quality, tq }) {
  if (!quality) return null
  const { null_per_column, negative_per_column, duplicate_rows, total_rows } = quality
  const cols = null_per_column ? Object.entries(null_per_column) : []
  const pct = (n) => total_rows > 0 ? ((n / total_rows) * 100).toFixed(1) : '0.0'
  const nullColor = (n) => n === 0 ? '' : n / total_rows > 0.1 ? '#842029' : '#664d03'
  const negColor  = (n) => n === 0 ? '' : n / total_rows > 0.1 ? '#842029' : '#664d03'
  const rowBg = (nulls, negs) => {
    if (nulls === 0 && negs === 0) return '#fff'
    return Math.max(nulls, negs) / total_rows > 0.1 ? '#f8d7da' : '#fff3cd'
  }

  return (
    <div style={{ marginBottom: 24 }}>
      <h3 style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-sub)', textTransform: 'uppercase', letterSpacing: 0.8, marginBottom: 10 }}>
        {tq.sectionTitle}
      </h3>
      <div style={{ border: '1px solid var(--border)', borderRadius: 8, overflow: 'hidden', marginBottom: 12 }}>
        <div style={{ background: 'var(--surface)', padding: '8px 14px', borderBottom: '1px solid var(--border)', display: 'grid', gridTemplateColumns: '1fr 100px 100px', gap: 8 }}>
          {[tq.colColumn, tq.colNulls, tq.colNegatives].map((h) => (
            <span key={h} style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 0.5, textAlign: h !== tq.colColumn ? 'right' : 'left' }}>{h}</span>
          ))}
        </div>
        {cols.map(([col, nullCount]) => {
          const negCount = negative_per_column?.[col] ?? null
          return (
            <div key={col} style={{ display: 'grid', gridTemplateColumns: '1fr 100px 100px', gap: 8, padding: '7px 14px', borderBottom: '1px solid var(--border)', background: rowBg(nullCount, negCount ?? 0), alignItems: 'center' }}>
              <span style={{ fontSize: 13, fontFamily: 'monospace', color: 'var(--text)' }}>{col}</span>
              <span style={{ fontSize: 13, fontWeight: nullCount > 0 ? 600 : 400, textAlign: 'right', color: nullColor(nullCount) }}>
                {nullCount > 0 ? `${nullCount.toLocaleString()} (${pct(nullCount)}%)` : '—'}
              </span>
              <span style={{ fontSize: 13, fontWeight: negCount > 0 ? 600 : 400, textAlign: 'right', color: negColor(negCount ?? 0) }}>
                {negCount == null ? <span style={{ color: 'var(--text-muted)', fontSize: 11 }}>{tq.na}</span>
                  : negCount > 0 ? `${negCount.toLocaleString()} (${pct(negCount)}%)`
                  : '—'}
              </span>
            </div>
          )
        })}
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 14px', borderRadius: 8, border: '1px solid var(--border)', background: duplicate_rows > 0 ? '#fff3cd' : '#d4edda' }}>
        <span style={{ fontSize: 13, color: 'var(--text)' }}>{tq.duplicates}</span>
        <span style={{ fontWeight: 700, fontSize: 14, color: duplicate_rows > 0 ? '#664d03' : '#2a7a3b' }}>
          {duplicate_rows?.toLocaleString() ?? 0}
          <span style={{ fontWeight: 400, fontSize: 12, marginLeft: 6 }}>({pct(duplicate_rows ?? 0)}%)</span>
        </span>
      </div>
    </div>
  )
}

export default function Step4_Clean() {
  const sessionId = useSessionStore((s) => s.sessionId)
  const uploadResult = useWizardStore((s) => s.uploadResult)
  const method = useWizardStore((s) => s.method)
  const treatNegativesAsReturns = useWizardStore((s) => s.treatNegativesAsReturns)
  const cleanResult = useWizardStore((s) => s.cleanResult)
  const setCleanResult = useWizardStore((s) => s.setCleanResult)
  const nextStep = useWizardStore((s) => s.nextStep)
  const prevStep = useWizardStore((s) => s.prevStep)
  const loading = useWizardStore((s) => s.loading)
  const setLoading = useWizardStore((s) => s.setLoading)
  const error = useWizardStore((s) => s.error)
  const setError = useWizardStore((s) => s.setError)
  const t = useT()
  const tc = t.step4

  const [opts, setOpts] = useState({ removeNulls: true, removeNegatives: !treatNegativesAsReturns, removeDuplicates: true })
  const toggle = (k) => setOpts((o) => ({ ...o, [k]: !o[k] }))

  const run = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await cleanData(sessionId, opts)
      setCleanResult(res)
    } catch (e) {
      setError(e.response?.data?.detail ?? 'Cleaning failed.')
    } finally {
      setLoading(false)
    }
  }

  const CheckOpt = ({ k, label }) => (
    <label style={{ display: 'flex', alignItems: 'center', gap: 10, cursor: 'pointer', marginBottom: 12 }}>
      <input type="checkbox" checked={opts[k]} onChange={() => toggle(k)}
        style={{ width: 16, height: 16, accentColor: 'var(--accent)', cursor: 'pointer' }} />
      <span style={{ fontSize: 14 }}>{label}</span>
    </label>
  )

  return (
    <div>
      <h2 style={{ fontSize: 22, fontWeight: 800, marginBottom: 6 }}>{tc.title}</h2>
      <p style={{ color: 'var(--text-sub)', marginBottom: 28 }}>{tc.subtitle}</p>

      <QualityTable quality={uploadResult?.quality} tq={tc.quality} />

      <div style={{ background: 'var(--surface)', borderRadius: 'var(--radius)', padding: '20px 24px', marginBottom: 24, border: '1px solid var(--border)' }}>
        <CheckOpt k="removeNulls" label={tc.options.removeNulls} />
        {method === 'lrfms' && treatNegativesAsReturns ? (
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12, padding: '8px 12px', borderRadius: 6, background: 'var(--surface-2)', border: '1px solid var(--border)' }}>
            <span style={{ fontSize: 18 }}>↩</span>
            <span style={{ fontSize: 13, color: 'var(--text-muted)' }}>
              <strong style={{ color: 'var(--text-sub)' }}>{tc.returnsbanner}</strong>
              {' '}{tc.returnsbannersub}
            </span>
          </div>
        ) : (
          <CheckOpt k="removeNegatives" label={tc.options.removeNegatives} />
        )}
        <CheckOpt k="removeDuplicates" label={tc.options.removeDuplicates} />
      </div>

      {error && (
        <div style={{ background: '#f2f2f2', border: '1px solid #bbbbbb', borderRadius: 8, padding: '12px 16px', marginBottom: 20, color: 'var(--text)' }}>
          {error}
        </div>
      )}

      {!cleanResult && (
        <div style={{ display: 'flex', gap: 12, marginBottom: 28 }}>
          <button onClick={prevStep} style={{ background: 'transparent', border: '1px solid var(--border)', color: 'var(--text-sub)', borderRadius: 8, padding: '10px 22px', fontWeight: 500 }}>
            {t.back}
          </button>
          <button disabled={loading} onClick={run}
            style={{ background: loading ? 'var(--border)' : 'var(--accent)', color: loading ? 'var(--text-muted)' : '#fff', border: 'none', borderRadius: 8, padding: '10px 28px', fontWeight: 600, display: 'flex', alignItems: 'center', gap: 8 }}>
            {loading && <Spinner size={16} />}
            {loading ? tc.running : tc.runBtn}
          </button>
        </div>
      )}

      {cleanResult && (
        <div>
          <div style={{ background: 'var(--surface)', borderRadius: 'var(--radius)', padding: '20px 24px', border: '1px solid var(--border)', marginBottom: 24 }}>
            <h3 style={{ fontWeight: 700, marginBottom: 12, color: 'var(--text-sub)', fontSize: 13, textTransform: 'uppercase', letterSpacing: 1 }}>{tc.report.title}</h3>
            <StatRow label={tc.report.rowsBefore}  value={cleanResult.rows_before.toLocaleString()} />
            <StatRow label={tc.report.rowsAfter}   value={cleanResult.rows_after.toLocaleString()} sub={`−${(cleanResult.rows_before - cleanResult.rows_after).toLocaleString()} removed`} />
            <StatRow label={tc.report.nullsRemoved} value={cleanResult.removed_nulls.toLocaleString()} />
            <StatRow label={tc.report.negsRemoved}  value={cleanResult.removed_negatives.toLocaleString()} />
            <StatRow label={tc.report.dupsRemoved}  value={cleanResult.removed_duplicates.toLocaleString()} />
            <StatRow label={tc.report.zeroRemoved}  value={cleanResult.removed_zero_total.toLocaleString()} />
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginTop: 16 }}>
              {[
                { label: tc.report.uniqueCustomers, value: cleanResult.unique_customers.toLocaleString() },
                { label: tc.report.uniqueOrders,    value: cleanResult.unique_orders.toLocaleString() },
              ].map(({ label, value }) => (
                <div key={label} style={{ background: 'var(--surface-2)', borderRadius: 8, padding: '14px', borderLeft: '3px solid var(--accent)' }}>
                  <div style={{ color: 'var(--text-sub)', fontSize: 12, marginBottom: 4 }}>{label}</div>
                  <div style={{ fontWeight: 700, fontSize: 24, color: 'var(--text)' }}>{value}</div>
                </div>
              ))}
            </div>
          </div>
          <div style={{ display: 'flex', gap: 12 }}>
            <button onClick={prevStep} style={{ background: 'transparent', border: '1px solid var(--border)', color: 'var(--text-sub)', borderRadius: 8, padding: '10px 22px', fontWeight: 500 }}>
              {t.back}
            </button>
            <button onClick={nextStep} style={{ background: 'var(--accent)', color: '#fff', border: 'none', borderRadius: 8, padding: '10px 28px', fontWeight: 600 }}>
              {t.continue}
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
