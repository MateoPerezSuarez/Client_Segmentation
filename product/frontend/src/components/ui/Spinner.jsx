export default function Spinner({ size = 20, dark = false }) {
  const track = dark ? 'rgba(0,0,0,0.15)' : 'rgba(255,255,255,0.3)'
  const head  = dark ? '#000' : '#fff'
  return (
    <div style={{
      width: size, height: size,
      border: `2px solid ${track}`,
      borderTop: `2px solid ${head}`,
      borderRadius: '50%',
      animation: 'spin 0.7s linear infinite',
      flexShrink: 0,
    }}>
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  )
}
