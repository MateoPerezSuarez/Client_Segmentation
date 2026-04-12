import { useEffect, useState } from 'react'
import { getAutoMapping, confirmMapping } from '../../api/mapping'
import { useSessionStore } from '../../store/sessionStore'
import { useWizardStore } from '../../store/wizardStore'
import { useT } from '../../i18n/useT'
import Spinner from '../ui/Spinner'

const REQUIRED = ['customer_id', 'order_id', 'order_date']

export default function Step3_Mapping() {
  const sessionId = useSessionStore((s) => s.sessionId)
  const uploadResult = useWizardStore((s) => s.uploadResult)
  const method = useWizardStore((s) => s.method)
  const autoMapping = useWizardStore((s) => s.autoMapping)
  const setAutoMapping = useWizardStore((s) => s.setAutoMapping)
  const setConfirmedMapping = useWizardStore((s) => s.setConfirmedMapping)
  const treatNegativesAsReturns = useWizardStore((s) => s.treatNegativesAsReturns)
  const setTreatNegativesAsReturns = useWizardStore((s) => s.setTreatNegativesAsReturns)
  const nextStep = useWizardStore((s) => s.nextStep)
  const prevStep = useWizardStore((s) => s.prevStep)
  const loading = useWizardStore((s) => s.loading)
  const setLoading = useWizardStore((s) => s.setLoading)
  const setError = useWizardStore((s) => s.setError)
  const error = useWizardStore((s) => s.error)
  const t = useT()
  const tm = t.step3

  const [localMapping, setLocalMapping] = useState({})
  const [fetchError, setFetchError] = useState(null)

  useEffect(() => {
    if (!sessionId || autoMapping) {
      if (autoMapping) {
        const init = {}
        for (const [k, v] of Object.entries(autoMapping.mapping)) {
          init[k] = v.source_col ?? ''
        }
        setLocalMapping(init)
      }
      return
    }
    setLoading(true)
    getAutoMapping(sessionId)
      .then((res) => {
        setAutoMapping(res)
        const init = {}
        for (const [k, v] of Object.entries(res.mapping)) {
          init[k] = v.source_col ?? ''
        }
        setLocalMapping(init)
      })
      .catch((e) => setFetchError(e.response?.data?.detail ?? 'Failed to auto-map columns.'))
      .finally(() => setLoading(false))
  }, [sessionId])

  const allCols = autoMapping?.all_columns ?? uploadResult?.columns ?? []
  const hasTotal = !!localMapping.order_total
  const hasQtyPrice = !!localMapping.quantity && !!localMapping.unit_price
  const requiredOk = REQUIRED.every((k) => !!localMapping[k]) && (hasTotal || hasQtyPrice)

  const submit = async () => {
    const mapping = {}
    for (const [k, v] of Object.entries(localMapping)) {
      mapping[k] = v || null
    }
    setLoading(true)
    setError(null)
    try {
      await confirmMapping(sessionId, mapping)
      setConfirmedMapping(mapping)
      nextStep()
    } catch (e) {
      setError(e.response?.data?.detail ?? 'Failed to confirm mapping.')
    } finally {
      setLoading(false)
    }
  }

  if (loading && !autoMapping) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, color: 'var(--text-sub)' }}>
        <Spinner size={20} dark /> {t.loading}
      </div>
    )
  }

  return (
    <div>
      <h2 style={{ fontSize: 22, fontWeight: 800, marginBottom: 6 }}>{tm.title}</h2>
      <p style={{ color: 'var(--text-sub)', marginBottom: 28 }}>
        {tm.subtitle}
        <br />
        <span style={{ color: 'var(--text-muted)', fontSize: 12 }}>{tm.subtitleNote}</span>
      </p>

      {(fetchError || error) && (
        <div style={{ background: '#f2f2f2', border: '1px solid #bbbbbb', borderRadius: 8, padding: '12px 16px', marginBottom: 20, color: 'var(--text)' }}>
          {fetchError || error}
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14, marginBottom: 28 }}>
        {Object.keys(tm.fields).map((target) => {
          const info = autoMapping?.mapping?.[target]
          const score = info?.score ?? 0
          const isRequired = REQUIRED.includes(target)

          return (
            <div key={target} style={{ background: 'var(--surface)', borderRadius: 8, padding: '14px 16px', border: '1px solid var(--border)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                <label style={{ fontWeight: 600, fontSize: 13, color: isRequired ? 'var(--text)' : 'var(--text-sub)' }}>
                  {tm.fields[target]}
                </label>
                {score > 0 && (
                  <span style={{
                    fontSize: 11,
                    color: score >= 0.7 ? 'var(--green)' : score >= 0.5 ? 'var(--yellow)' : 'var(--text-muted)',
                    fontWeight: 600,
                  }}>
                    {Math.round(score * 100)}%
                  </span>
                )}
              </div>
              <select
                value={localMapping[target] ?? ''}
                onChange={(e) => setLocalMapping((m) => ({ ...m, [target]: e.target.value }))}
                style={{ width: '100%', background: 'var(--surface-2)', border: '1px solid var(--border)', borderRadius: 6, color: 'var(--text)', padding: '6px 8px' }}
              >
                <option value="">{tm.notMapped}</option>
                {allCols.map((c) => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
          )
        })}
      </div>

      {!hasTotal && !hasQtyPrice && (
        <div style={{ background: '#f5f5f5', border: '1px solid #bbbbbb', borderRadius: 8, padding: '10px 14px', marginBottom: 20, color: 'var(--text-sub)', fontSize: 13 }}>
          {tm.noTotalWarn}
        </div>
      )}

      {/* Satisfaction (S) measurement — LRFMS only */}
      {method === 'lrfms' && (
        <div style={{ borderTop: '1px solid var(--border)', paddingTop: 20, marginBottom: 24 }}>
          <p style={{ fontWeight: 700, fontSize: 14, marginBottom: 4 }}>{tm.satisfaction.title}</p>
          <p style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 14 }}>{tm.satisfaction.subtitle}</p>
          <label style={{ display: 'flex', alignItems: 'flex-start', gap: 10, cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={treatNegativesAsReturns}
              onChange={(e) => setTreatNegativesAsReturns(e.target.checked)}
              style={{ marginTop: 2, width: 15, height: 15, accentColor: 'var(--accent)', cursor: 'pointer', flexShrink: 0 }}
            />
            <span style={{ fontSize: 13 }}>
              <strong>{tm.satisfaction.checkboxLabel}</strong>
              <br />
              <span style={{ color: 'var(--text-muted)', fontSize: 12 }}>{tm.satisfaction.checkboxHint}</span>
            </span>
          </label>
        </div>
      )}

      <div style={{ display: 'flex', gap: 12 }}>
        <button onClick={prevStep} style={{ background: 'transparent', border: '1px solid var(--border)', color: 'var(--text-sub)', borderRadius: 8, padding: '10px 22px', fontWeight: 500 }}>
          {t.back}
        </button>
        <button
          disabled={!requiredOk || loading}
          onClick={submit}
          style={{
            background: requiredOk && !loading ? 'var(--accent)' : 'var(--border)',
            color: requiredOk && !loading ? '#fff' : 'var(--text-muted)',
            border: 'none', borderRadius: 8, padding: '10px 28px',
            fontWeight: 600, display: 'flex', alignItems: 'center', gap: 8,
          }}
        >
          {loading && <Spinner size={16} />}
          {loading ? tm.confirming : tm.confirmBtn}
        </button>
      </div>
    </div>
  )
}
