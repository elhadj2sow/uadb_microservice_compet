import axios from 'axios'

export const BASE = {
  auth        : '/api/auth',
  inscription : '/api/inscriptions',
  bibliotheque: '/api/bibliotheque',
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
  timeout: 15000,
})

api.interceptors.request.use(cfg => {
  const token = localStorage.getItem('access')
  if (token) cfg.headers.Authorization = `Bearer ${token}`
  return cfg
})

// ── Gestion du refresh token avec verrou anti-concurrence ──────────────────
// Sans ce mécanisme, si 3 requêtes échouent en 401 simultanément, elles
// essaient toutes de rafraîchir → seule la première réussit, les autres
// reçoivent une erreur et déconnectent l'utilisateur.
let _refreshing = false
let _refreshQueue = [] // Requêtes en attente pendant le refresh

const _runQueue = (error, token = null) => {
  _refreshQueue.forEach(({ resolve, reject }) =>
    error ? reject(error) : resolve(token)
  )
  _refreshQueue = []
}

api.interceptors.response.use(
  r => r,
  async err => {
    const orig = err.config

    // ── Retry automatique pour erreurs transitoires (réseau, 502, 503, 504) ──
    // Les microservices Django en dev peuvent mettre un instant à répondre
    // après un redémarrage. On retente une fois après 1 seconde.
    const isNetworkError = !err.response
    const isTransient    = err.response?.status >= 500
    if ((isNetworkError || isTransient) && !orig._retried) {
      orig._retried = true
      await new Promise(res => setTimeout(res, 1000))
      return api(orig)
    }

    if (err.response?.status !== 401 || orig._retry) {
      return Promise.reject(err)
    }

    // Si un refresh est déjà en cours, mettre cette requête en file d'attente
    if (_refreshing) {
      return new Promise((resolve, reject) => {
        _refreshQueue.push({ resolve, reject })
      }).then(token => {
        orig.headers.Authorization = `Bearer ${token}`
        orig._retry = true
        return api(orig)
      })
    }

    orig._retry = true
    _refreshing = true

    try {
      const refresh = localStorage.getItem('refresh')
      if (!refresh) throw new Error('No refresh token')
      const res = await axios.post(`${BASE.auth}/refresh/`, { refresh })
      const newToken = res.data.access
      localStorage.setItem('access', newToken)
      orig.headers.Authorization = `Bearer ${newToken}`
      _runQueue(null, newToken)
      return api(orig)
    } catch (e) {
      _runQueue(e, null)
      localStorage.clear()
      window.location.href = '/login'
      return Promise.reject(e)
    } finally {
      _refreshing = false
    }
  }
)

export default api
