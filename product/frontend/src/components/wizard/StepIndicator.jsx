import { useT } from '../../i18n/useT'

const METHOD_COLORS = {
  rfm_quintiles: '#1a1a1a',
  rfm_kmeans:   '#2f4b7c',
  abc:          '#665191',
  lrfms:        '#d45087',
}

export default function StepIndicator({ currentStep, labels, method }) {
  const t = useT()
  const methodLabel = method ? t.step1.methods[method]?.name : null
  const color = METHOD_COLORS[method]
  const meta = methodLabel ? { label: methodLabel, color } : null

  return (
    <div style={{ marginBottom: 8 }}>
      {/* Method badge — visible once a method is chosen and we're past step 1 */}
      {meta && currentStep > 1 && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 14 }}>
          <span style={{
            background: meta.color + '18',
            color: meta.color,
            border: `1px solid ${meta.color}44`,
            borderRadius: 5,
            padding: '3px 12px',
            fontSize: 12,
            fontWeight: 700,
            letterSpacing: 0.3,
          }}>
            {meta.label}
          </span>
          <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>{t.flowLabel}</span>
        </div>
      )}

      {/* Step dots */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 0 }}>
        {labels.map((label, i) => {
          const num = i + 1
          const done = num < currentStep
          const active = num === currentStep
          const accentColor = meta?.color ?? 'var(--accent)'

          return (
            <div key={num} style={{ display: 'flex', alignItems: 'center', flex: num < labels.length ? 1 : 'none' }}>
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
                <div style={{
                  width: 28, height: 28, borderRadius: '50%',
                  background: done ? 'var(--green)' : active ? accentColor : 'var(--surface-2)',
                  border: active ? `2px solid ${accentColor}` : done ? '2px solid var(--green)' : '2px solid var(--border)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: 12, fontWeight: 700,
                  color: done || active ? '#fff' : 'var(--text-muted)',
                  transition: 'all 0.2s',
                }}>
                  {done ? '✓' : num}
                </div>
                <span style={{
                  fontSize: 11,
                  color: active ? 'var(--text)' : done ? 'var(--text-sub)' : 'var(--text-muted)',
                  fontWeight: active ? 600 : 400,
                  whiteSpace: 'nowrap',
                }}>
                  {label}
                </span>
              </div>
              {num < labels.length && (
                <div style={{
                  flex: 1, height: 2, marginBottom: 18,
                  background: done ? 'var(--green)' : 'var(--border)',
                  transition: 'background 0.2s',
                }} />
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
