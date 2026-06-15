import { useRef, useState } from 'react'
import { uploadFile, uploadBigQuery } from '../../api/upload'
import { useSessionStore } from '../../store/sessionStore'
import { useWizardStore } from '../../store/wizardStore'
import { useT } from '../../i18n/useT'
import Spinner from '../ui/Spinner'

// ── Source toggle ──────────────────────────────────────────────────────────────

function SourceTab({ active, onClick, children }) {
  return (
    <button
      onClick={onClick}
      style={{
        flex: 1, padding: '9px 0', fontWeight: 600, fontSize: 13,
        border: 'none', cursor: 'pointer', transition: 'all 0.15s',
        borderBottom: active ? '2px solid var(--accent)' : '2px solid transparent',
        background: 'transparent',
        color: active ? 'var(--accent)' : 'var(--text-muted)',
      }}
    >
      {children}
    </button>
  )
}

// ── File upload panel ──────────────────────────────────────────────────────────

function FilePanel({ onResult }) {
  const [dragging, setDragging] = useState(false)
  const [file, setFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const inputRef = useRef(null)
  const t = useT().step2.file

  const handle = (f) => { if (f) setFile(f) }

  const submit = async () => {
    if (!file) return
    setLoading(true)
    setError(null)
    try {
      const result = await uploadFile(file)
      onResult(result)
    } catch (e) {
      setError(e.response?.data?.detail ?? 'Upload failed.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <div
        onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => { e.preventDefault(); setDragging(false); handle(e.dataTransfer.files[0]) }}
        onClick={() => inputRef.current?.click()}
        style={{
          border: `2px dashed ${dragging ? 'var(--accent)' : file ? 'var(--green)' : 'var(--border)'}`,
          borderRadius: 'var(--radius)', padding: '48px 32px',
          textAlign: 'center', cursor: 'pointer',
          background: dragging ? '#f0f0f0' : 'var(--surface)',
          transition: 'all 0.15s', marginBottom: 24,
        }}
      >
        <input ref={inputRef} type="file" accept=".csv,.xlsx,.xls"
          style={{ display: 'none' }} onChange={(e) => handle(e.target.files[0])} />
        <div style={{ fontSize: 36, marginBottom: 12 }}>{file ? '📄' : '☁️'}</div>
        {file ? (
          <>
            <p style={{ fontWeight: 600, marginBottom: 4 }}>{file.name}</p>
            <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>
              {(file.size / 1024 / 1024).toFixed(2)} MB — {t.clickChange}
            </p>
          </>
        ) : (
          <>
            <p style={{ fontWeight: 600, marginBottom: 4 }}>{t.dropHint}</p>
            <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>{t.dropSub}</p>
          </>
        )}
      </div>

      {error && (
        <div style={{ background: '#f2f2f2', border: '1px solid #bbb', borderRadius: 8, padding: '12px 16px', marginBottom: 20, color: 'var(--text)' }}>
          {error}
        </div>
      )}

      <button
        disabled={!file || loading}
        onClick={submit}
        style={{
          background: file && !loading ? 'var(--accent)' : 'var(--border)',
          color: file && !loading ? '#fff' : 'var(--text-muted)',
          border: 'none', borderRadius: 8, padding: '10px 28px',
          fontWeight: 600, display: 'flex', alignItems: 'center', gap: 8,
        }}
      >
        {loading && <Spinner size={16} />}
        {loading ? t.uploading : t.uploadBtn}
      </button>
    </div>
  )
}

// ── BigQuery panel ─────────────────────────────────────────────────────────────

function BigQueryPanel({ onResult }) {
  const [tablePath, setTablePath] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const t = useT().step2.bq

  const canSubmit = tablePath.trim().length > 0

  const submit = async () => {
    if (!canSubmit) return
    setLoading(true)
    setError(null)
    try {
      const result = await uploadBigQuery(tablePath.trim())
      onResult(result)
    } catch (e) {
      setError(e.response?.data?.detail ?? 'BigQuery connection failed.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      {/* How-to hint */}
      <div style={{
        background: 'var(--surface-2)', border: '1px solid var(--border)',
        borderRadius: 8, padding: '12px 16px', marginBottom: 24, fontSize: 13,
        color: 'var(--text-muted)', lineHeight: 1.6,
      }}>
        <strong style={{ color: 'var(--text-sub)' }}>{t.howToTitle}</strong> {t.howToText}
      </div>

      {/* Table path */}
      <div style={{ marginBottom: 20 }}>
        <label style={{ fontWeight: 600, fontSize: 13, display: 'block', marginBottom: 8 }}>
          {t.tableLabel}
        </label>
        <input
          type="text"
          value={tablePath}
          onChange={(e) => setTablePath(e.target.value)}
          placeholder={t.tablePlaceholder}
          spellCheck={false}
          style={{
            width: '100%', fontFamily: 'monospace', fontSize: 13,
            background: 'var(--surface-2)', border: '1px solid var(--border)',
            borderRadius: 8, padding: '10px 12px', color: 'var(--text)',
            outline: 'none', boxSizing: 'border-box',
          }}
        />
        <p style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>{t.tableSub}</p>
      </div>

      {error && (
        <div style={{ background: '#f2f2f2', border: '1px solid #bbb', borderRadius: 8, padding: '12px 16px', marginBottom: 20, color: 'var(--text)' }}>
          {error}
        </div>
      )}

      <button
        disabled={!canSubmit || loading}
        onClick={submit}
        style={{
          background: canSubmit && !loading ? 'var(--accent)' : 'var(--border)',
          color: canSubmit && !loading ? '#fff' : 'var(--text-muted)',
          border: 'none', borderRadius: 8, padding: '10px 28px',
          fontWeight: 600, display: 'flex', alignItems: 'center', gap: 8,
        }}
      >
        {loading && <Spinner size={16} />}
        {loading ? t.running : t.runBtn}
      </button>
    </div>
  )
}

// ── Main step ──────────────────────────────────────────────────────────────────

export default function Step2_Upload() {
  const [source, setSource] = useState('file') // 'file' | 'bigquery'

  const setSessionId = useSessionStore((s) => s.setSessionId)
  const setUploadResult = useWizardStore((s) => s.setUploadResult)
  const nextStep = useWizardStore((s) => s.nextStep)
  const prevStep = useWizardStore((s) => s.prevStep)
  const t = useT()

  const handleResult = (result) => {
    setSessionId(result.session_id)
    setUploadResult(result)
    nextStep()
  }

  return (
    <div>
      <h2 style={{ fontSize: 22, fontWeight: 800, marginBottom: 6 }}>{t.step2.title}</h2>
      <p style={{ color: 'var(--text-sub)', marginBottom: 24 }}>{t.step2.subtitle}</p>

      {/* Source tabs */}
      <div style={{ display: 'flex', borderBottom: '1px solid var(--border)', marginBottom: 28 }}>
        <SourceTab active={source === 'file'} onClick={() => setSource('file')}>
          {t.step2.tabFile}
        </SourceTab>
        <SourceTab active={source === 'bigquery'} onClick={() => setSource('bigquery')}>
          {t.step2.tabBQ}
        </SourceTab>
      </div>

      {source === 'file' ? (
        <FilePanel onResult={handleResult} />
      ) : (
        <BigQueryPanel onResult={handleResult} />
      )}

      <div style={{ marginTop: 20 }}>
        <button
          onClick={prevStep}
          style={{ background: 'transparent', border: '1px solid var(--border)', color: 'var(--text-sub)', borderRadius: 8, padding: '10px 22px', fontWeight: 500 }}
        >
          {t.back}
        </button>
      </div>
    </div>
  )
}
