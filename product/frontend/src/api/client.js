import axios from 'axios'

const api = axios.create({ baseURL: '' })  // Vite proxy handles routing

export default api
