import { useEffect, useState } from 'react'
import {
  PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer,
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  ScatterChart, Scatter, ZAxis,
  ComposedChart, Line, ReferenceLine, ReferenceArea,
} from 'recharts'
import { getDashboardData, renameSegments } from '../../api/segmentation'
import { useT } from '../../i18n/useT'
import Spinner from '../ui/Spinner'

const PALETTE = [
  '#003f5c', '#2f4b7c', '#665191', '#a05195', '#d45087',
  '#f95d6a', '#ff7c43', '#ffa600', '#488f31', '#00827f',
  '#005f73', '#0a9396', '#ee9b00', '#ca6702', '#9b2226',
]

const METHOD_COLORS = {
  rfm_quintiles: '#1a1a1a',
  rfm_kmeans:   '#2f4b7c',
  abc:          '#665191',
  lrfms:        '#d45087',
}

const segColor = (segments, label) => {
  const i = segments.findIndex((s) => s.label === label)
  return PALETTE[i % PALETTE.length]
}

// ── Reusable chart wrapper ─────────────────────────────────────────────────────
function ChartCard({ title, children, span = 1 }) {
  return (
    <div style={{
      background: '#fff',
      border: '1px solid #e0e0e0',
      borderRadius: 10,
      padding: '20px',
      gridColumn: `span ${span}`,
    }}>
      <h3 style={{ fontSize: 13, fontWeight: 700, color: '#444', marginBottom: 16, textTransform: 'uppercase', letterSpacing: 0.5 }}>
        {title}
      </h3>
      {children}
    </div>
  )
}

function ChartTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  return (
    <div style={{ background: '#fff', border: '1px solid #ddd', borderRadius: 6, padding: '8px 12px', fontSize: 12 }}>
      {label && <p style={{ fontWeight: 600, marginBottom: 4 }}>{label}</p>}
      {payload.map((p) => (
        <p key={p.name} style={{ color: p.color ?? '#333' }}>
          {p.name}: <strong>{typeof p.value === 'number' ? p.value.toLocaleString() : p.value}</strong>
        </p>
      ))}
    </div>
  )
}

// ── Shared charts ──────────────────────────────────────────────────────────────

function PieSegments({ segments }) {
  const data = segments.map((s) => ({ name: s.label, value: s.count }))
  return (
    <ResponsiveContainer width="100%" height={260}>
      <PieChart>
        <Pie data={data} cx="50%" cy="50%" outerRadius={90} dataKey="value"
          label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`} labelLine={false}>
          {data.map((_, i) => <Cell key={i} fill={PALETTE[i % PALETTE.length]} />)}
        </Pie>
        <Tooltip content={<ChartTooltip />} />
      </PieChart>
    </ResponsiveContainer>
  )
}

function BarCustomers({ segments }) {
  const t = useT()
  const data = [...segments].sort((a, b) => b.count - a.count)
  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={data} margin={{ left: 0, right: 8, top: 4, bottom: 40 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
        <XAxis dataKey="label" tick={{ fontSize: 11 }} angle={-35} textAnchor="end" interval={0} />
        <YAxis tick={{ fontSize: 11 }} />
        <Tooltip content={<ChartTooltip />} />
        <Bar dataKey="count" name={t.dashboard.barLabels.customers} radius={[4, 4, 0, 0]}>
          {data.map((_, i) => <Cell key={i} fill={PALETTE[i % PALETTE.length]} />)}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}

function BarRevenueShare({ segments }) {
  const t = useT()
  const td = t.dashboard
  const data = segments.filter((s) => s.pct_revenue != null).map((s) => ({
    label: s.label,
    pctCust: s.pct_customers,
    pctRev: s.pct_revenue,
  }))
  if (!data.length) return <p style={{ color: '#999', fontSize: 13 }}>{td.top.noRevenue}</p>
  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={data} margin={{ left: 0, right: 8, top: 4, bottom: 40 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
        <XAxis dataKey="label" tick={{ fontSize: 11 }} angle={-35} textAnchor="end" interval={0} />
        <YAxis tick={{ fontSize: 11 }} unit="%" />
        <Tooltip content={<ChartTooltip />} />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        <Bar dataKey="pctCust" name={td.barLabels.pctCust} fill="#003f5c" radius={[4, 4, 0, 0]} />
        <Bar dataKey="pctRev" name={td.barLabels.pctRev} fill="#ffa600" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  )
}

function BarAvgProfile({ segments }) {
  const t = useT()
  const bl = t.dashboard.barLabels
  const data = segments.filter((s) => s.avg_recency != null).map((s) => {
    const maxR = Math.max(...segments.map((x) => x.avg_recency ?? 0)) || 1
    const maxF = Math.max(...segments.map((x) => x.avg_frequency ?? 0)) || 1
    const maxM = Math.max(...segments.map((x) => x.avg_monetary ?? 0)) || 1
    return {
      label: s.label,
      recency:   +(((s.avg_recency ?? 0) / maxR) * 100).toFixed(1),
      frequency: +(((s.avg_frequency ?? 0) / maxF) * 100).toFixed(1),
      monetary:  +(((s.avg_monetary ?? 0) / maxM) * 100).toFixed(1),
    }
  })
  if (!data.length) return <p style={{ color: '#999', fontSize: 13 }}>{t.dashboard.top.noProfile}</p>
  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={data} margin={{ left: 0, right: 8, top: 4, bottom: 40 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
        <XAxis dataKey="label" tick={{ fontSize: 11 }} angle={-35} textAnchor="end" interval={0} />
        <YAxis tick={{ fontSize: 11 }} unit="%" />
        <Tooltip content={<ChartTooltip />} />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        <Bar dataKey="recency"   name={bl.recency}   fill="#665191" radius={[4, 4, 0, 0]} />
        <Bar dataKey="frequency" name={bl.frequency} fill="#f95d6a" radius={[4, 4, 0, 0]} />
        <Bar dataKey="monetary"  name={bl.monetary}  fill="#ffa600" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  )
}

function BubbleRFM({ segments }) {
  const t = useT()
  const tb = t.dashboard.bubble
  const data = segments
    .filter((s) => s.avg_recency != null && s.avg_monetary != null)
    .map((s) => ({
      label: s.label,
      x: s.avg_recency,
      y: s.avg_monetary,
      z: s.count,
      freq: s.avg_frequency,
    }))

  if (!data.length) return <p style={{ color: '#999', fontSize: 13 }}>{tb.noData}</p>

  return (
    <ResponsiveContainer width="100%" height={320}>
      <ScatterChart margin={{ top: 8, right: 24, bottom: 32, left: 16 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
        <XAxis
          dataKey="x" name={tb.axisX} type="number" tick={{ fontSize: 11 }}
          label={{ value: tb.axisX, position: 'insideBottom', offset: -20, fontSize: 11 }}
        />
        <YAxis
          dataKey="y" name={tb.axisY} type="number" tick={{ fontSize: 11 }}
          label={{ value: tb.axisY, angle: -90, position: 'insideLeft', offset: 8, fontSize: 11 }}
        />
        <ZAxis dataKey="z" range={[800, 6000]} name={t.dashboard.barLabels.customers} />
        <Tooltip
          cursor={{ strokeDasharray: '3 3' }}
          content={({ active, payload }) => {
            if (!active || !payload?.length) return null
            const d = payload[0]?.payload
            return (
              <div style={{ background: '#fff', border: '1px solid #ddd', borderRadius: 6, padding: '8px 12px', fontSize: 12 }}>
                <p style={{ fontWeight: 700, marginBottom: 4 }}>{d?.label}</p>
                <p><strong>{tb.ttRecency}</strong> {d?.x?.toFixed(1)}</p>
                <p><strong>{tb.ttMonetary}</strong> {d?.y?.toLocaleString(undefined, { maximumFractionDigits: 1 })}</p>
                <p><strong>{tb.ttFreq}</strong> {d?.freq?.toFixed(1)}</p>
                <p><strong>{tb.ttCustomers}</strong> {d?.z?.toLocaleString()}</p>
              </div>
            )
          }}
        />
        {data.map((d, i) => (
          <Scatter
            key={d.label}
            name={d.label}
            data={[d]}
            fill={PALETTE[i % PALETTE.length]}
            fillOpacity={0.82}
          />
        ))}
        <Legend wrapperStyle={{ fontSize: 11 }} />
      </ScatterChart>
    </ResponsiveContainer>
  )
}

function ABCParetoChart({ paretoData, thresholds }) {
  const t = useT()
  const tp = t.dashboard.pareto
  if (!paretoData?.length) return <p style={{ color: '#999', fontSize: 13 }}>{tp.noData}</p>
  const { a_x, b_x, a_y, b_y } = thresholds

  const abcTooltip = ({ active, payload }) => {
    if (!active || !payload?.length) return null
    const d = payload[0]?.payload
    return (
      <div style={{ background: '#fff', border: '1px solid #ddd', borderRadius: 6, padding: '8px 12px', fontSize: 12 }}>
        <p><strong>{tp.ttCust}</strong> {d?.x}%</p>
        <p><strong>{tp.ttRev}</strong> {d?.y}%</p>
        <p><strong>{tp.ttSeg}</strong> {d?.segment}</p>
      </div>
    )
  }

  return (
    <ResponsiveContainer width="100%" height={380}>
      <ComposedChart data={paretoData} margin={{ top: 16, right: 24, bottom: 40, left: 16 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
        <XAxis
          dataKey="x" type="number" domain={[0, 100]} tick={{ fontSize: 11 }}
          label={{ value: tp.axisX, position: 'insideBottom', offset: -28, fontSize: 11 }}
        />
        <YAxis
          domain={[0, 100]} tick={{ fontSize: 11 }} unit="%"
          label={{ value: tp.axisY, angle: -90, position: 'insideLeft', offset: 8, fontSize: 11 }}
        />
        <Tooltip content={abcTooltip} />

        <ReferenceArea x1={0}    x2={a_x} fill="#003f5c" fillOpacity={0.07} />
        <ReferenceArea x1={a_x} x2={b_x} fill="#ffa600" fillOpacity={0.09} />
        <ReferenceArea x1={b_x} x2={100} fill="#d45087" fillOpacity={0.07} />

        <ReferenceLine x={a_x} stroke="#003f5c" strokeDasharray="6 3" strokeWidth={2}
          label={{ value: `A  ${a_x}%`, position: 'insideTopRight', fontSize: 11, fill: '#003f5c', fontWeight: 700 }} />
        <ReferenceLine x={b_x} stroke="#e08000" strokeDasharray="6 3" strokeWidth={2}
          label={{ value: `B  ${b_x}%`, position: 'insideTopRight', fontSize: 11, fill: '#e08000', fontWeight: 700 }} />
        <ReferenceLine y={a_y} stroke="#003f5c" strokeDasharray="4 4" strokeWidth={1} strokeOpacity={0.5}
          label={{ value: `${a_y}%`, position: 'right', fontSize: 10, fill: '#003f5c' }} />
        <ReferenceLine y={b_y} stroke="#e08000" strokeDasharray="4 4" strokeWidth={1} strokeOpacity={0.5}
          label={{ value: `${b_y}%`, position: 'right', fontSize: 10, fill: '#e08000' }} />

        <Line type="monotone" dataKey="y" stroke="#0a0a0a" strokeWidth={2.5} dot={false} name={tp.axisY} />

        <ReferenceLine x={a_x / 2} stroke="transparent"
          label={{ value: 'A', position: 'insideTop', fontSize: 22, fill: '#003f5c', fontWeight: 800, opacity: 0.25 }} />
        <ReferenceLine x={(a_x + b_x) / 2} stroke="transparent"
          label={{ value: 'B', position: 'insideTop', fontSize: 22, fill: '#e08000', fontWeight: 800, opacity: 0.25 }} />
        <ReferenceLine x={(b_x + 100) / 2} stroke="transparent"
          label={{ value: 'C', position: 'insideTop', fontSize: 22, fill: '#d45087', fontWeight: 800, opacity: 0.25 }} />
      </ComposedChart>
    </ResponsiveContainer>
  )
}

// ── Cluster profile ────────────────────────────────────────────────────────────

function ClusterProfileSection({ clusterStats, segments, sessionId, token, onSaved, method }) {
  const t = useT()
  const tc = t.dashboard.cluster
  const [names, setNames] = useState(() =>
    Object.fromEntries(clusterStats.map((c) => [c.segment, c.segment]))
  )
  const [saveState, setSaveState] = useState('idle')

  const rename = (seg, value) => {
    setNames((n) => ({ ...n, [seg]: value }))
    setSaveState('idle')
  }

  const save = async () => {
    setSaveState('saving')
    try {
      await renameSegments(sessionId, token, names)
      setSaveState('saved')
      onSaved?.(names)
    } catch {
      setSaveState('error')
    }
  }

  const METRICS = method === 'lrfms' ? tc.metricsLRFMS : tc.metricsRFM

  const TH = {
    padding: '9px 12px', textAlign: 'left', fontSize: 11, fontWeight: 700,
    color: 'var(--text-muted)', borderBottom: '1px solid var(--border)',
    textTransform: 'uppercase', letterSpacing: 0.4, whiteSpace: 'nowrap',
  }
  const TD = { padding: '9px 12px', fontSize: 12 }

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'flex-end', gap: 10, flexWrap: 'wrap', marginBottom: 20 }}>
        {clusterStats.map((c, i) => (
          <div key={c.segment} style={{ display: 'flex', flexDirection: 'column', gap: 4, minWidth: 140 }}>
            <label style={{
              fontSize: 11, fontWeight: 700, color: PALETTE[i % PALETTE.length],
              textTransform: 'uppercase', letterSpacing: 0.5,
            }}>
              {c.segment}
            </label>
            <input
              value={names[c.segment]}
              onChange={(e) => rename(c.segment, e.target.value)}
              placeholder={c.segment}
              style={{
                background: 'var(--surface-2)', border: `1px solid ${PALETTE[i % PALETTE.length]}55`,
                borderRadius: 6, padding: '5px 9px', fontSize: 13,
                color: 'var(--text)', outline: 'none', width: '100%',
              }}
            />
          </div>
        ))}

        <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          <span style={{ fontSize: 11, color: 'transparent', userSelect: 'none' }}>_</span>
          <button
            onClick={save}
            disabled={saveState === 'saving'}
            style={{
              padding: '6px 18px', borderRadius: 6, fontWeight: 600, fontSize: 13,
              cursor: saveState === 'saving' ? 'not-allowed' : 'pointer',
              border: 'none',
              background: saveState === 'saved' ? '#1a7a3b' : saveState === 'error' ? '#9b2226' : '#0a0a0a',
              color: '#fff',
              transition: 'background 0.2s',
              whiteSpace: 'nowrap',
            }}
          >
            {saveState === 'saving' ? tc.saving
              : saveState === 'saved' ? tc.saved
              : saveState === 'error' ? tc.error
              : tc.saveBtn}
          </button>
          {saveState === 'saved' && (
            <span style={{ fontSize: 11, color: '#1a7a3b' }}>{tc.csvUpdated}</span>
          )}
        </div>
      </div>

      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
          <thead>
            <tr style={{ background: 'var(--surface-2)' }}>
              <th style={TH}>{tc.colCluster}</th>
              {METRICS.map((m) => (
                <>
                  <th key={`${m.key}-mean`} style={{ ...TH, borderLeft: '2px solid var(--border)' }}>
                    {m.label} — {tc.colMean}
                  </th>
                  <th key={`${m.key}-std`}  style={TH}>{tc.colStd}</th>
                  <th key={`${m.key}-min`}  style={TH}>{tc.colMin}</th>
                  <th key={`${m.key}-max`}  style={TH}>{tc.colMax}</th>
                </>
              ))}
            </tr>
          </thead>
          <tbody>
            {clusterStats.map((c, i) => (
              <tr key={c.segment} style={{ borderBottom: '1px solid var(--border)' }}>
                <td style={{ padding: '9px 12px', whiteSpace: 'nowrap' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
                    <div style={{ width: 10, height: 10, borderRadius: '50%', background: PALETTE[i % PALETTE.length], flexShrink: 0 }} />
                    <span style={{ fontWeight: 600 }}>
                      {names[c.segment] !== c.segment ? names[c.segment] : c.segment}
                    </span>
                  </div>
                </td>

                {METRICS.map((m) => {
                  const s = c[m.key]
                  if (!s) return <td key={m.key} colSpan={4} style={{ ...TD, color: '#aaa' }}>—</td>
                  const fmt = (v) => v == null ? '—' : v.toLocaleString(undefined, { maximumFractionDigits: 1 })
                return (
                    <>
                      <td key={`${m.key}-mean`} style={{ ...TD, borderLeft: '2px solid var(--border)', fontWeight: 600 }}>
                        {fmt(s.mean)}
                        {m.unit && <span style={{ color: '#aaa', fontWeight: 400, marginLeft: 3 }}>{m.unit}</span>}
                      </td>
                      <td key={`${m.key}-std`}  style={{ ...TD, color: '#888' }}>
                        {s.std == null ? '—' : `±${fmt(s.std)}`}
                      </td>
                      <td key={`${m.key}-min`}  style={{ ...TD, color: '#555' }}>{fmt(s.min)}</td>
                      <td key={`${m.key}-max`}  style={{ ...TD, color: '#555' }}>{fmt(s.max)}</td>
                    </>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function TopCustomersTable({ topCustomers, segments }) {
  const segLabels = [...new Set(topCustomers.map((r) => r.segment))].sort()
  const [activeSeg, setActiveSeg] = useState(segLabels[0] ?? '')

  const rows = topCustomers.filter((r) => r.segment === activeSeg)
  const cols = rows.length ? Object.keys(rows[0]).filter((k) => k !== 'segment') : []

  return (
    <div>
      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 14 }}>
        {segLabels.map((seg) => (
          <button
            key={seg}
            onClick={() => setActiveSeg(seg)}
            style={{
              background: activeSeg === seg ? segColor(segments, seg) : '#f5f5f5',
              color: activeSeg === seg ? '#fff' : '#444',
              border: 'none', borderRadius: 5,
              padding: '4px 12px', fontSize: 12, fontWeight: 600, cursor: 'pointer',
            }}
          >{seg}</button>
        ))}
      </div>

      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
          <thead>
            <tr style={{ background: '#f7f7f7' }}>
              <th style={{ padding: '8px 10px', textAlign: 'left', color: '#666', fontWeight: 600, borderBottom: '1px solid #e0e0e0' }}>#</th>
              {cols.map((c) => (
                <th key={c} style={{ padding: '8px 10px', textAlign: 'left', color: '#666', fontWeight: 600, borderBottom: '1px solid #e0e0e0', textTransform: 'capitalize' }}>
                  {c.replace(/_/g, ' ')}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, i) => (
              <tr key={i} style={{ borderBottom: '1px solid #f0f0f0' }}>
                <td style={{ padding: '7px 10px', color: '#999' }}>{i + 1}</td>
                {cols.map((c) => (
                  <td key={c} style={{ padding: '7px 10px', fontWeight: c === 'monetary' ? 600 : 400 }}>
                    {typeof row[c] === 'number' ? row[c].toLocaleString(undefined, { maximumFractionDigits: 1 }) : row[c]}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// ── Method-specific chart grids ────────────────────────────────────────────────

function DashboardRFMQuintiles({ data, segments, sessionId, token, onSegmentsRenamed, t }) {
  const ch = t.dashboard.charts
  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 20 }}>
      <ChartCard title={ch.pieTitle}>
        <PieSegments segments={segments} />
      </ChartCard>
      <ChartCard title={ch.barCustomers}>
        <BarCustomers segments={segments} />
      </ChartCard>
      <ChartCard title={ch.barRevenue}>
        <BarRevenueShare segments={segments} />
      </ChartCard>
      <ChartCard title={ch.avgProfile} span={3}>
        <BarAvgProfile segments={segments} />
      </ChartCard>
      {data.top_customers?.length > 0 && (
        <ChartCard title={ch.topCustomers} span={3}>
          <TopCustomersTable topCustomers={data.top_customers} segments={segments} />
        </ChartCard>
      )}
    </div>
  )
}

function DashboardRFMKMeans({ data, segments, sessionId, token, onSegmentsRenamed, t }) {
  const ch = t.dashboard.charts
  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 20 }}>
      <ChartCard title={ch.pieTitle}>
        <PieSegments segments={segments} />
      </ChartCard>
      <ChartCard title={ch.barCustomers}>
        <BarCustomers segments={segments} />
      </ChartCard>
      <ChartCard title={ch.barRevenue}>
        <BarRevenueShare segments={segments} />
      </ChartCard>
      {data.has_rfm && (
        <ChartCard title={ch.bubble} span={2}>
          <BubbleRFM segments={segments} />
        </ChartCard>
      )}
      <ChartCard title={ch.avgProfile}>
        <BarAvgProfile segments={segments} />
      </ChartCard>
      {data.cluster_stats?.length > 0 && (
        <ChartCard title={ch.clusterRFM} span={3}>
          <ClusterProfileSection
            clusterStats={data.cluster_stats}
            segments={segments}
            sessionId={sessionId}
            token={token}
            onSaved={onSegmentsRenamed}
            method="rfm_kmeans"
          />
        </ChartCard>
      )}
      {data.top_customers?.length > 0 && (
        <ChartCard title={ch.topCustomers} span={3}>
          <TopCustomersTable topCustomers={data.top_customers} segments={segments} />
        </ChartCard>
      )}
    </div>
  )
}

function DashboardABC({ data, segments, sessionId, token, t }) {
  const ch = t.dashboard.charts
  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 20 }}>
      {data.pareto_curve?.length > 0 && (
        <ChartCard title={ch.pareto} span={3}>
          <ABCParetoChart paretoData={data.pareto_curve} thresholds={data.abc_thresholds} />
        </ChartCard>
      )}
      <ChartCard title={ch.pieTitle}>
        <PieSegments segments={segments} />
      </ChartCard>
      <ChartCard title={ch.barCustomers}>
        <BarCustomers segments={segments} />
      </ChartCard>
      <ChartCard title={ch.barRevenue}>
        <BarRevenueShare segments={segments} />
      </ChartCard>
      {data.top_customers?.length > 0 && (
        <ChartCard title={ch.topCustomers} span={3}>
          <TopCustomersTable topCustomers={data.top_customers} segments={segments} />
        </ChartCard>
      )}
    </div>
  )
}

function DashboardLRFMS({ data, segments, sessionId, token, onSegmentsRenamed, t }) {
  const ch = t.dashboard.charts
  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 20 }}>
      <ChartCard title={ch.pieTitle}>
        <PieSegments segments={segments} />
      </ChartCard>
      <ChartCard title={ch.barCustomers}>
        <BarCustomers segments={segments} />
      </ChartCard>
      <ChartCard title={ch.barRevenue}>
        <BarRevenueShare segments={segments} />
      </ChartCard>
      <ChartCard title={ch.bubble} span={3}>
        <BubbleRFM segments={segments} />
      </ChartCard>
      {data.cluster_stats?.length > 0 && (
        <ChartCard title={ch.clusterLRFMS} span={3}>
          <ClusterProfileSection
            clusterStats={data.cluster_stats}
            segments={segments}
            sessionId={sessionId}
            token={token}
            onSaved={onSegmentsRenamed}
            method="lrfms"
          />
        </ChartCard>
      )}
      {data.top_customers?.length > 0 && (
        <ChartCard title={ch.topCustomers} span={3}>
          <TopCustomersTable topCustomers={data.top_customers} segments={segments} />
        </ChartCard>
      )}
    </div>
  )
}

// ── Main Dashboard modal ───────────────────────────────────────────────────────

export default function Dashboard({ sessionId, token, segments, method, onClose, onSegmentsRenamed }) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const t = useT()
  const td = t.dashboard

  useEffect(() => {
    getDashboardData(sessionId, token)
      .then(setData)
      .catch((e) => setError(e.response?.data?.detail ?? 'Failed to load dashboard.'))
      .finally(() => setLoading(false))
  }, [sessionId, token])

  const methodName = t.step1.methods[method]?.name ?? method
  const methodColor = METHOD_COLORS[method] ?? '#0a0a0a'

  return (
    <div style={{
      position: 'fixed', inset: 0,
      background: 'rgba(0,0,0,0.45)',
      zIndex: 1000,
      display: 'flex', flexDirection: 'column',
      overflowY: 'auto',
    }}>
      <div style={{
        background: '#f9f9f9',
        minHeight: '100vh',
        width: '100%',
        padding: '32px 40px',
      }}>
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 28 }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 4 }}>
              <h2 style={{ fontSize: 22, fontWeight: 800, color: '#0a0a0a' }}>{td.title}</h2>
              <span style={{
                background: methodColor + '18',
                color: methodColor,
                border: `1px solid ${methodColor}44`,
                borderRadius: 5,
                padding: '3px 12px',
                fontSize: 12,
                fontWeight: 700,
              }}>
                {methodName}
              </span>
            </div>
            <p style={{ color: '#666', fontSize: 13 }}>
              {segments.length} {td.segments} · {segments.reduce((a, s) => a + s.count, 0).toLocaleString()} {td.customers}
            </p>
          </div>
          <button
            onClick={onClose}
            style={{
              background: '#0a0a0a', color: '#fff',
              border: 'none', borderRadius: 8,
              padding: '8px 20px', fontWeight: 600, fontSize: 13, cursor: 'pointer',
            }}
          >{td.closeBtn}</button>
        </div>

        {loading && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, color: '#666' }}>
            <Spinner size={20} dark /> {td.loading}
          </div>
        )}

        {error && (
          <div style={{ background: '#f2f2f2', border: '1px solid #bbb', borderRadius: 8, padding: '12px 16px', color: '#333' }}>
            {error}
          </div>
        )}

        {!loading && !error && data && (() => {
          const props = { data, segments, sessionId, token, onSegmentsRenamed, t }
          if (method === 'abc')        return <DashboardABC {...props} />
          if (method === 'rfm_kmeans') return <DashboardRFMKMeans {...props} />
          if (method === 'lrfms')      return <DashboardLRFMS {...props} />
          return <DashboardRFMQuintiles {...props} />
        })()}
      </div>
    </div>
  )
}
