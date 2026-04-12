import { useWizardStore } from '../../store/wizardStore'
import { useT } from '../../i18n/useT'

const METHOD_IDS = ['rfm_quintiles', 'rfm_kmeans', 'abc', 'lrfms']

const TAG_COLORS = {
  rfm_quintiles: '#1a1a1a',
  rfm_kmeans:   '#444444',
  abc:          '#666666',
  lrfms:        '#888888',
}

export default function Step1_Method() {
  const method = useWizardStore((s) => s.method)
  const setMethod = useWizardStore((s) => s.setMethod)
  const nextStep = useWizardStore((s) => s.nextStep)
  const t = useT()

  return (
    <div>
      <h2 style={{ fontSize: 22, fontWeight: 800, marginBottom: 6 }}>{t.step1.title}</h2>
      <p style={{ color: 'var(--text-sub)', marginBottom: 28 }}>{t.step1.subtitle}</p>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 32 }}>
        {METHOD_IDS.map((id) => {
          const m = t.step1.methods[id]
          const tagColor = TAG_COLORS[id]
          return (
            <button
              key={id}
              onClick={() => setMethod(id)}
              style={{
                background: method === id ? 'var(--surface-2)' : 'var(--surface)',
                border: method === id ? '2px solid var(--accent)' : '2px solid var(--border)',
                borderRadius: 'var(--radius)', padding: '20px',
                textAlign: 'left', color: 'var(--text)',
                transition: 'all 0.15s', cursor: 'pointer',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
                <span style={{ fontWeight: 700, fontSize: 15 }}>{m.name}</span>
                <span style={{
                  background: tagColor + '22', color: tagColor,
                  border: `1px solid ${tagColor}44`,
                  borderRadius: 4, padding: '1px 8px', fontSize: 11, fontWeight: 600,
                }}>{m.tag}</span>
              </div>
              <p style={{ color: 'var(--text-sub)', fontSize: 13, marginBottom: 8, lineHeight: 1.5 }}>{m.desc}</p>
              <p style={{ color: 'var(--text-muted)', fontSize: 12 }}>{m.best}</p>
            </button>
          )
        })}
      </div>

      <button
        disabled={!method}
        onClick={nextStep}
        style={{
          background: method ? 'var(--accent)' : 'var(--border)',
          color: method ? '#fff' : 'var(--text-muted)',
          border: 'none', borderRadius: 8, padding: '10px 28px',
          fontWeight: 600, fontSize: 14,
          cursor: method ? 'pointer' : 'not-allowed', transition: 'background 0.15s',
        }}
      >
        {t.continue}
      </button>
    </div>
  )
}
