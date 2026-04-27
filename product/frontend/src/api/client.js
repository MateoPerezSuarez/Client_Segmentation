import axios from 'axios'

// In local dev (no env var) the empty baseURL lets the Vite proxy route to localhost:8000.
// In production (Netlify) set VITE_API_BASE_URL to the Cloud Run service URL.
const api = axios.create({ baseURL: import.meta.env.VITE_API_BASE_URL || '' })

export default api
