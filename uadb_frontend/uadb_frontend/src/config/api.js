import axios from 'axios'

export const BASE = {
  auth        : '/api/auth',
  inscription : '/api/inscriptions',
  formation   : '/api/formations',
  dossier     : '/api/dossiers',
  piece       : '/api/pieces',
  deliberation: '/api/deliberations',
  resultat    : '/api/resultats',
  attestation : '/api/attestations',
  notification: '/api/notifications',
  chatbot     : '/api/chatbot',
  ia          : '/api/evaluer',
  regles      : '/api/regles',
  audit       : '/api/audit',
}

const api = axios.create({
  headers: { 'Content-Type': 'application/json' },
  timeout: 12000,
})

api.interceptors.request.use(cfg => {
  const token = localStorage.getItem('access')
  if (token) cfg.headers.Authorization = `Bearer ${token}`
  return cfg
})

api.interceptors.response.use(
  r => r,
  async err => {
    const orig = err.config
    if (err.response?.status === 401 && !orig._retry) {
      orig._retry = true
      try {
        const refresh = localStorage.getItem('refresh')
        const res = await axios.post(`${BASE.auth}/refresh/`, { refresh })
        localStorage.setItem('access', res.data.access)
        orig.headers.Authorization = `Bearer ${res.data.access}`
        return api(orig)
      } catch {
        localStorage.clear()
        window.location.href = '/login'
      }
    }
    return Promise.reject(err)
  }
)

export default api
