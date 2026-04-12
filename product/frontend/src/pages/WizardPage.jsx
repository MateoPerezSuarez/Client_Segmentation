import { useWizardStore } from '../store/wizardStore'
import { useT } from '../i18n/useT'
import StepIndicator from '../components/wizard/StepIndicator'
import Step1_Method from '../components/wizard/Step1_Method'
import Step2_Upload from '../components/wizard/Step2_Upload'
import Step3_Mapping from '../components/wizard/Step3_Mapping'
import Step4_Clean from '../components/wizard/Step4_Clean'
import Step5_Configure from '../components/wizard/Step5_Configure'
import Step6_Results from '../components/wizard/Step6_Results'

const STEPS = {
  1: Step1_Method,
  2: Step2_Upload,
  3: Step3_Mapping,
  4: Step4_Clean,
  5: Step5_Configure,
  6: Step6_Results,
}

export default function WizardPage() {
  const step = useWizardStore((s) => s.step)
  const method = useWizardStore((s) => s.method)
  const reset = useWizardStore((s) => s.reset)
  const t = useT()
  const StepComponent = STEPS[step]

  const s = t.steps
  const METHOD_STEP_LABELS = {
    rfm_quintiles: [s.method, s.upload, s.mapping, s.clean, s.segments,   s.results],
    rfm_kmeans:   [s.method, s.upload, s.mapping, s.clean, s.clustering, s.results],
    abc:          [s.method, s.upload, s.mapping, s.clean, s.thresholds, s.results],
    lrfms:        [s.method, s.upload, s.mappingS, s.clean, s.configure, s.results],
  }
  const DEFAULT_LABELS = [s.method, s.upload, s.mapping, s.clean, s.configure, s.results]
  const labels = METHOD_STEP_LABELS[method] ?? DEFAULT_LABELS

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <header style={{
        borderBottom: '1px solid var(--border)',
        padding: '16px 32px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        background: 'var(--surface)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <img src="/LIN3S_logo_black.png" alt="LIN3S" style={{ height: 28, display: 'block' }} />
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          {step > 1 && (
            <button
              onClick={reset}
              style={{
                background: 'transparent',
                border: '1px solid var(--border)',
                color: 'var(--text-sub)',
                borderRadius: 6,
                padding: '6px 14px',
              }}
            >
              {t.startOver}
            </button>
          )}
        </div>
      </header>

      {/* Step indicator */}
      <div style={{ padding: '24px 32px 0' }}>
        <StepIndicator currentStep={step} labels={labels} method={method} />
      </div>

      {/* Content */}
      <main style={{ flex: 1, padding: '32px', maxWidth: 900, width: '100%', margin: '0 auto' }}>
        <StepComponent />
      </main>
    </div>
  )
}
