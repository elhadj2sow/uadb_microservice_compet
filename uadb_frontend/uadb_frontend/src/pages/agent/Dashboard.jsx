import { useState, useEffect } from 'react'
import api, { BASE } from '../../config/api'
import { useAuth } from '../../context/AuthContext'
import { FolderOpen, ClipboardList, CheckCircle, Clock, AlertTriangle } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

export default function DashboardAgent() {
  const { user } = useAuth()
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const annee = `${new Date().getFullYear()}-${new Date().getFullYear()+1}`

  useEffect(() => {
    Promise.allSettled([
      api.get(`${BASE.dossier}/statistiques/?annee=${annee}`),
    ]).then(([d]) => {
      if (d.status==='fulfilled') setStats({ dossier: d.value.data })
    }).finally(() => setLoading(false))
  }, [])

  const CARDS = stats ? [
    { label: 'Total dossiers',   value: stats.dossier?.total || 0,             color: 'blue', icon: FolderOpen },
    { label: 'Complets',         value: stats.dossier?.par_etat?.complet || 0,  color: 'teal', icon: CheckCircle },
    { label: 'En cours',         value: stats.dossier?.par_etat?.en_cours || 0, color: 'gold', icon: Clock },
    { label: 'Incomplets',       value: stats.dossier?.par_etat?.incomplet || 0,color: 'red',  icon: AlertTriangle },
  ] : []

  const chartData = stats ? [
    { name: 'En cours',  value: stats.dossier?.par_etat?.en_cours  || 0, fill: '#1565c0' },
    { name: 'Incomplet', value: stats.dossier?.par_etat?.incomplet || 0, fill: '#f59e0b' },
    { name: 'Complet',   value: stats.dossier?.par_etat?.complet   || 0, fill: '#00897b' },
    { name: 'Validé',    value: stats.dossier?.par_etat?.valide    || 0, fill: '#059669' },
    { name: 'Rejeté',    value: stats.dossier?.par_etat?.rejete    || 0, fill: '#dc2626' },
  ] : []

  return (
    <div className="page">
      <div className="welcome-banner">
        <div className="welcome-content">
          <div className="welcome-title">Tableau de bord Agent</div>
          <div className="welcome-subtitle">
            Bienvenue {user?.username} — Année {annee}
          </div>
        </div>
      </div>

      {loading ? (
        <div className="stats-grid">
          {[1,2,3,4].map(i=><div key={i} className="skeleton" style={{height:120,borderRadius:16}}/>)}
        </div>
      ) : (
        <div className="stats-grid fade-up">
          {CARDS.map((c,i) => (
            <div key={c.label} className={`stat-card ${c.color}`}
              style={{animationDelay:`${i*60}ms`}}>
              <div className={`stat-icon-wrap ${c.color}`}><c.icon size={20}/></div>
              <div className="stat-value">{c.value}</div>
              <div className="stat-label">{c.label}</div>
            </div>
          ))}
        </div>
      )}

      {stats && (
        <div className="card fade-up" style={{animationDelay:'200ms'}}>
          <div className="card-header">
            <span className="card-title">Répartition des dossiers</span>
            <span className="badge badge-info">Année {annee}</span>
          </div>
          <div className="card-body">
            <div style={{height:260}}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} margin={{top:5,right:20,bottom:5,left:0}}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--gray-100)" vertical={false}/>
                  <XAxis dataKey="name" tick={{fontSize:12,fill:'var(--gray-400)'}} axisLine={false} tickLine={false}/>
                  <YAxis tick={{fontSize:12,fill:'var(--gray-400)'}} axisLine={false} tickLine={false}/>
                  <Tooltip
                    contentStyle={{borderRadius:10,border:'1px solid var(--gray-200)',fontSize:13}}
                    cursor={{fill:'rgba(0,0,0,.03)'}}
                  />
                  <Bar dataKey="value" radius={[6,6,0,0]}>
                    {chartData.map((entry,i) => (
                      <rect key={i} fill={entry.fill}/>
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
