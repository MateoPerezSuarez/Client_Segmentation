import { useState } from 'react'
import {
  ComposedChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ReferenceLine, ResponsiveContainer,
} from 'recharts'
import { getDownloadUrl, exportResult } from '../../api/segmentation'
import { useSessionStore } from '../../store/sessionStore'
import { useWizardStore } from '../../store/wizardStore'
import { useT } from '../../i18n/useT'
import Dashboard from '../results/Dashboard'

const SEGMENT_COLORS = [
  '#000000', '#333333', '#555555', '#777777', '#999999',
  '#111111', '#444444', '#666666', '#888888', '#222222',
]

function Bar({ pct, color }) {
  return (
    <div style={{ background: 'var(--surface-2)', borderRadius: 4, height: 8, overflow: 'hidden', flex: 1 }}>
      <div style={{ width: `${pct}%`, background: color, height: '100%', borderRadius: 4, transition: 'width 0.5s' }} />
    </div>
  )
}

export default function Step6_Results() {
  const sessionId = useSessionStore((s) => s.sessionId)
  const result = useWizardStore((s) => s.segmentResult)
  const setSegmentResult = useWizardStore((s) => s.setSegmentResult)
  const method = useWizardStore((s) => s.method)
  const reset = useWizardStore((s) => s.reset)
  const t = useT()
  const t6 = t.step6

  const handleSegmentsRenamed = (namesMap) => {
    setSegmentResult({
      ...result,
      segments: result.segments.map((s) => ({
        ...s,
        label: namesMap[s.label] ?? s.label,
      })),
    })
  }
  const [showDashboard, setShowDashboard] = useState(false)
  const [showExport, setShowExport] = useState(false)

  if (!result) return <p style={{ color: 'var(--text-muted)' }}>No results yet.</p>

  const downloadUrl = getDownloadUrl(sessionId, result.download_token)
  const isKmeans = result.method === 'rfm_kmeans' || result.method === 'lrfms'
  const optimal_k = result.extra?.optimal_k
  const methodName = t.step1.methods[method]?.name ?? method

  return (
    <>
      <div>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 }}>
          <h2 style={{ fontSize: 22, fontWeight: 800 }}>{t6.title}</h2>
          <span style={{
            background: 'var(--accent)', color: '#fff',
            borderRadius: 6, padding: '3px 12px', fontWeight: 600, fontSize: 13,
          }}>
            {methodName}
          </span>
        </div>
        <p style={{ color: 'var(--text-sub)', marginBottom: 28 }}>
          {result.total_customers.toLocaleString()} {t6.customers}
          {isKmeans && optimal_k && ` · ${t6.optimalK} ${optimal_k}`}
        </p>

        {/* Summary cards */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12, marginBottom: 28 }}>
          {[
            { label: t6.cards.totalCustomers, value: result.total_customers.toLocaleString() },
            { label: t6.cards.segments,       value: result.segments.length },
            { label: t6.cards.largestSegment, value: result.segments[0]?.label ?? '—' },
          ].map(({ label, value }) => (
            <div key={label} style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 8, padding: '16px', borderLeft: '3px solid var(--accent)' }}>
              <div style={{ color: 'var(--text-sub)', fontSize: 12, marginBottom: 4 }}>{label}</div>
              <div style={{ fontWeight: 700, fontSize: 20, color: 'var(--text)' }}>{value}</div>
            </div>
          ))}
        </div>

        {/* Segment table — columns vary per method */}
        {(() => {
          const showRFM = method === 'rfm_quintiles' || method === 'rfm_kmeans'
          const headers = showRFM
            ? [t6.table.segment, t6.table.customers, t6.table.share, t6.table.avgRecency, t6.table.avgFreq, t6.table.avgMonetary, t6.table.revenue]
            : [t6.table.segment, t6.table.customers, t6.table.share, t6.table.revenue]
          return (
            <div style={{ background: 'var(--surface)', borderRadius: 'var(--radius)', border: '1px solid var(--border)', overflow: 'hidden', marginBottom: 28 }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ background: 'var(--surface-2)' }}>
                    {headers.map((h) => (
                      <th key={h} style={{ padding: '10px 14px', textAlign: 'left', fontSize: 12, fontWeight: 600, color: 'var(--text-muted)', borderBottom: '1px solid var(--border)' }}>
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {result.segments.map((seg, i) => (
                    <tr key={seg.label} style={{ borderBottom: '1px solid var(--border)' }}>
                      <td style={{ padding: '10px 14px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                          <div style={{ width: 10, height: 10, borderRadius: '50%', background: SEGMENT_COLORS[i % SEGMENT_COLORS.length], flexShrink: 0 }} />
                          <span style={{ fontWeight: 600, fontSize: 13 }}>{seg.label}</span>
                        </div>
                      </td>
                      <td style={{ padding: '10px 14px', color: 'var(--text-sub)' }}>{seg.count.toLocaleString()}</td>
                      <td style={{ padding: '10px 14px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                          <Bar pct={seg.pct_customers} color={SEGMENT_COLORS[i % SEGMENT_COLORS.length]} />
                          <span style={{ fontSize: 12, color: 'var(--text-sub)', minWidth: 36 }}>{seg.pct_customers}%</span>
                        </div>
                      </td>
                      {showRFM && (
                        <>
                          <td style={{ padding: '10px 14px', color: 'var(--text-sub)', fontSize: 13 }}>{seg.avg_recency ?? '—'}</td>
                          <td style={{ padding: '10px 14px', color: 'var(--text-sub)', fontSize: 13 }}>{seg.avg_frequency ?? '—'}</td>
                          <td style={{ padding: '10px 14px', color: 'var(--text-sub)', fontSize: 13 }}>
                            {seg.avg_monetary != null ? `$${seg.avg_monetary.toLocaleString()}` : '—'}
                          </td>
                        </>
                      )}
                      <td style={{ padding: '10px 14px', color: 'var(--text-sub)', fontSize: 13 }}>{seg.pct_revenue != null ? `${seg.pct_revenue}%` : '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )
        })()}

        {/* K-scores / elbow chart */}
        {isKmeans && result.extra?.k_scores && (() => {
          const ks = result.extra.k_scores
          const mn = Math.min(...ks.wcss), mx = Math.max(...ks.wcss)
          const wcssNorm = ks.wcss.map((v) => mx === mn ? 1 : +((v - mn) / (mx - mn)).toFixed(3))
          const chartData = ks.ks.map((k, i) => ({
            k,
            'WCSS (norm)': wcssNorm[i],
            'Silhouette': +ks.silhouette[i].toFixed(3),
            'Combined': +ks.combined[i].toFixed(3),
          }))
          return (
            <div style={{ background: 'var(--surface)', borderRadius: 'var(--radius)', border: '1px solid var(--border)', padding: '16px 20px', marginBottom: 28 }}>
              <h3 style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 14 }}>
                {t6.elbowTitle}
              </h3>
              <ResponsiveContainer width="100%" height={200}>
                <ComposedChart data={chartData} margin={{ top: 4, right: 16, bottom: 8, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
                  <XAxis dataKey="k" tick={{ fontSize: 11 }} label={{ value: 'k (clusters)', position: 'insideBottom', offset: -4, fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} domain={[0, 1]} />
                  <Tooltip wrapperStyle={{ fontSize: 12 }} />
                  <Legend wrapperStyle={{ fontSize: 11 }} />
                  <Line type="monotone" dataKey="WCSS (norm)" stroke="#003f5c" strokeWidth={2} dot={{ r: 3 }} />
                  <Line type="monotone" dataKey="Silhouette" stroke="#f95d6a" strokeWidth={2} dot={{ r: 3 }} />
                  <Line type="monotone" dataKey="Combined" stroke="#ffa600" strokeWidth={2} strokeDasharray="5 3" dot={{ r: 3 }} />
                  <ReferenceLine x={optimal_k} stroke="var(--accent)" strokeWidth={2} strokeDasharray="4 3"
                    label={{ value: `k=${optimal_k}`, position: 'top', fontSize: 11, fontWeight: 700, fill: 'var(--accent)' }}
                  />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          )
        })()}

        {/* Actions */}
        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
          <button
            onClick={() => setShowDashboard(true)}
            style={{
              background: '#0a0a0a', color: '#fff',
              border: 'none', borderRadius: 8, padding: '10px 28px',
              fontWeight: 600, fontSize: 14, cursor: 'pointer',
              display: 'inline-flex', alignItems: 'center', gap: 8,
            }}
          >
            {t6.dashboardBtn}
          </button>

          <a
            href={downloadUrl}
            download="segmentation.csv"
            style={{
              background: 'transparent', color: 'var(--text)',
              border: '1px solid var(--border)',
              borderRadius: 8, padding: '10px 28px',
              fontWeight: 600, fontSize: 14, textDecoration: 'none',
              display: 'inline-flex', alignItems: 'center', gap: 8,
            }}
          >
            {t6.downloadBtn}
          </a>

          <button
            onClick={() => setShowExport(true)}
            style={{
              background: 'transparent', color: 'var(--text)',
              border: '1px solid var(--border)',
              borderRadius: 8, padding: '10px 28px',
              fontWeight: 600, fontSize: 14, cursor: 'pointer',
              display: 'inline-flex', alignItems: 'center', gap: 8,
            }}
          >
            {t6.exportBtn}
          </button>

          <button
            onClick={reset}
            style={{ background: 'transparent', border: '1px solid var(--border)', color: 'var(--text-sub)', borderRadius: 8, padding: '10px 22px', fontWeight: 500 }}
          >
            {t6.newBtn}
          </button>
        </div>
      </div>

      {showDashboard && (
        <Dashboard
          sessionId={sessionId}
          token={result.download_token}
          segments={result.segments}
          method={method}
          onClose={() => setShowDashboard(false)}
          onSegmentsRenamed={handleSegmentsRenamed}
        />
      )}

      {showExport && (
        <ExportModal
          sessionId={sessionId}
          token={result.download_token}
          t={t6.export}
          onClose={() => setShowExport(false)}
        />
      )}
    </>
  )
}

function ExportModal({ sessionId, token, t, onClose }) {
  const [bqTable, setBqTable] = useState('')
  const [gcsUri, setGcsUri] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [done, setDone] = useState(null)

  const canSubmit = bqTable.trim().length > 0 || gcsUri.trim().length > 0

  const submit = async () => {
    if (!canSubmit) { setError(t.needOne); return }
    setLoading(true)
    setError(null)
    try {
      const res = await exportResult(sessionId, token, {
        bqTable: bqTable.trim(),
        gcsUri: gcsUri.trim(),
      })
      setDone(res)
    } catch (e) {
      setError(e.response?.data?.detail ?? 'Export failed.')
    } finally {
      setLoading(false)
    }
  }

  const field = {
    width: '100%', fontFamily: 'monospace', fontSize: 13,
    background: 'var(--surface-2)', border: '1px solid var(--border)',
    borderRadius: 8, padding: '10px 12px', color: 'var(--text)',
    outline: 'none', boxSizing: 'border-box',
  }

  return (
    <div
      onClick={onClose}
      style={{
        position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.4)',
        display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000,
      }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          background: 'var(--surface)', borderRadius: 'var(--radius)',
          border: '1px solid var(--border)', padding: 28,
          width: 'min(520px, 92vw)', maxHeight: '90vh', overflowY: 'auto',
        }}
      >
        <h3 style={{ fontSize: 18, fontWeight: 700, marginBottom: 12 }}>{t.title}</h3>

        {done ? (
          <div>
            <div style={{
              background: 'var(--surface-2)', border: '1px solid var(--green, #2e7d32)',
              borderRadius: 8, padding: '14px 16px', marginBottom: 20, fontSize: 13, lineHeight: 1.7,
            }}>
              <p style={{ fontWeight: 600, marginBottom: 8 }}>✓ {t.successTitle}</p>
              <p style={{ color: 'var(--text-sub)' }}>{t.runId}: <code>{done.run_id}</code></p>
              {done.bigquery && (
                <p style={{ color: 'var(--text-sub)' }}>
                  {t.bqDone} <code>{done.bigquery.table}</code> ({done.bigquery.rows})
                  {done.bigquery.view && <> · {t.bqView} <code>{done.bigquery.view}</code></>}
                </p>
              )}
              {done.gcs && (
                <p style={{ color: 'var(--text-sub)' }}>{t.gcsDone}: <code>{done.gcs.uri}</code></p>
              )}
            </div>
            <button onClick={onClose} style={{ background: '#0a0a0a', color: '#fff', border: 'none', borderRadius: 8, padding: '10px 28px', fontWeight: 600, cursor: 'pointer' }}>
              {t.doneBtn}
            </button>
          </div>
        ) : (
          <div>
            <p style={{ color: 'var(--text-muted)', fontSize: 13, lineHeight: 1.6, marginBottom: 20 }}>{t.intro}</p>

            <div style={{ marginBottom: 18 }}>
              <label style={{ fontWeight: 600, fontSize: 13, display: 'block', marginBottom: 6 }}>{t.bqLabel}</label>
              <input type="text" value={bqTable} onChange={(e) => setBqTable(e.target.value)} placeholder={t.bqPlaceholder} spellCheck={false} style={field} />
              <p style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>{t.bqHint}</p>
            </div>

            <div style={{ marginBottom: 18 }}>
              <label style={{ fontWeight: 600, fontSize: 13, display: 'block', marginBottom: 6 }}>{t.gcsLabel}</label>
              <input type="text" value={gcsUri} onChange={(e) => setGcsUri(e.target.value)} placeholder={t.gcsPlaceholder} spellCheck={false} style={field} />
              <p style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>{t.gcsHint}</p>
            </div>

            {error && (
              <div style={{ background: '#f2f2f2', border: '1px solid #bbb', borderRadius: 8, padding: '10px 14px', marginBottom: 18, color: 'var(--text)', fontSize: 13 }}>
                {error}
              </div>
            )}

            <div style={{ display: 'flex', gap: 12 }}>
              <button
                disabled={!canSubmit || loading}
                onClick={submit}
                style={{
                  background: canSubmit && !loading ? 'var(--accent)' : 'var(--border)',
                  color: canSubmit && !loading ? '#fff' : 'var(--text-muted)',
                  border: 'none', borderRadius: 8, padding: '10px 28px',
                  fontWeight: 600, cursor: canSubmit && !loading ? 'pointer' : 'default',
                }}
              >
                {loading ? t.running : t.runBtn}
              </button>
              <button onClick={onClose} style={{ background: 'transparent', border: '1px solid var(--border)', color: 'var(--text-sub)', borderRadius: 8, padding: '10px 22px', fontWeight: 500, cursor: 'pointer' }}>
                {t.cancelBtn}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
