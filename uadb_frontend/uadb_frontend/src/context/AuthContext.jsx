import { createContext, useContext, useState, useEffect } from 'react'
import api, { BASE } from '../config/api'

const Ctx = createContext(null)

function decodeToken(token) {
  try {
    const p = JSON.parse(atob(token.split('.')[1]))
    return {
      id         : p.user_id,
      username   : p.login || p.username || '',
      email      : p.email || '',
      roles      : p.roles || [],
      etudiant_id: p.etudiant_id || null,
      etat       : p.etat || 'actif',
    }
  } catch { return null }
}

export function AuthProvider({ children }) {
  const [user, setUser]       = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('access')
    if (token) {
      const u = decodeToken(token)
      if (u) setUser(u)
      else localStorage.clear()
    }
    setLoading(false)
  }, [])

  const login = async (username, password) => {
    const res = await api.post(`${BASE.auth}/login/`, { username, password })
    localStorage.setItem('access',  res.data.access)
    localStorage.setItem('refresh', res.data.refresh)
    const u = decodeToken(res.data.access)
    setUser(u)
    return u
  }

  const logout = async () => {
    try { await api.post(`${BASE.auth}/logout/`, { refresh: localStorage.getItem('refresh') }) } catch {}
    localStorage.clear()
    setUser(null)
  }

  const hasRole    = r  => user?.roles?.includes(r)
  const isEtudiant = () => hasRole('etudiant')
  const isAdmin    = () => hasRole('admin')
  const isAgent    = () => ['agent_scolarite','agent_comptable','service_medical','bibliotheque']
                             .some(r => hasRole(r))

  return (
    <Ctx.Provider value={{ user, loading, login, logout, hasRole, isEtudiant, isAdmin, isAgent }}>
      {children}
    </Ctx.Provider>
  )
}

export const useAuth = () => useContext(Ctx)
