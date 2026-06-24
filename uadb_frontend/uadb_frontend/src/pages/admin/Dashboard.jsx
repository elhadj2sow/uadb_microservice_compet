import { useState, useEffect } from 'react'
import api, { BASE } from '../../config/api'
import { useAuth } from '../../context/AuthContext'
import { Shield, Sliders, FileText, Users, TrendingUp, AlertTriangle } from 'lucide-react'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, PieChart, Pie, Cell
} from 'recharts'

const COLORS = ['#1565c0','#00897b','#f59e0b','#e53935','#7b1fa2']

export default function DashboardAdmin() {
  const { user }        = useAuth()
  const [stats, setStats] = useState(null)
  const [audit, setAudit] = useState(null)
  const [loading, setLoading] = useState(true)
  const annee = `${new Date().getFullYear()}-${new Date().getFullYear()+1}`

  useEffect(() => {
    Promise.allSettled([
      api.get(`${BASE.dossier}/statistiques/?annee=${annee}`),
      api.get(`${BASE.audit}/statistiques/`),
      api.get(`${BASE.audit}/statistiques/daily/?jours=7`),
    ]).then(([d, a, ad]) => {
      if (d.status==='fulfilled') setStats(d.value.data)
      if (a.status==='fulfilled') setAudit({
        global: a.value.data,
        daily : ad.status==='fulfilled' ? ad.value.data.results : []
      })
    }).finally(() => setLoading(false))
  }, [])

  const CARDS = stats ? [
    { label:'Total dossiers',   value:stats.total         || 0, color:'blue', icon:FileText },
    { label:'Score moyen',      value:`${stats.score_moyen||0}%`, color:'teal', icon:TrendingUp },
    { label:'Dossiers complets',value:stats.complets       || 0, color:'gold', icon:Shield },
    { label:'Incomplets',       value:stats.incomplets     || 0, color:'red',  icon:AlertTriangle },
  ] : []

  const pieData = stats ? Object.entries(stats.par_etat||{}).map(([k,v]) => ({name:k,value:v})) : []
  const lineData = audit?.daily?.map(d => ({
    date   : d.date,
    actions: d.nb_actions,
    echecs : d.nb_echecs,
  })).reverse() || []

  return (
    <div className="page">
      <div className="welcome-banner">
        <div className="welcome-content">
          <div className="welcome-title">Administration UADB</div>
          <div className="welcome-subtitle">Tableau de bord global — {annee}</div>
        </div>
      </div>

      {loading ? (
        <div className="stats-grid">
          {[1,2,3,4].map(i=><div key={i} className="skeleton" style={{height:120,borderRadius:16}}/>)}
        </div>
      ) : (
        <div className="stats-grid fade-up">
          {CARDS.map((c,i) => (
            <div key={c.label} className={`stat-card ${c.color}`} style={{animationDelay:`${i*60}ms`}}>
              <div className={`stat-icon-wrap ${c.color}`}><c.icon size={20}/></div>
              <div className="stat-value">{c.value}</div>
              <div className="stat-label">{c.label}</div>
            </div>
          ))}
        </div>
      )}

      <div className="grid-2" style={{gap:20,marginBottom:20}}>
        {/* Activité audit 7 jours */}
        <div className="card fade-up" style={{animationDelay:'200ms'}}>
          <div className="card-header">
            <span className="card-title">Activité système (7 jours)</span>
          </div>
          <div className="card-body">
            <div style={{height:220}}>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={lineData} margin={{top:5,right:10,bottom:5,left:0}}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--gray-100)" vertical={false}/>
                  <XAxis dataKey="date" tick={{fontSize:11,fill:'var(--gray-400)'}} axisLine={false} tickLine={false}/>
                  <YAxis tick={{fontSize:11,fill:'var(--gray-400)'}} axisLine={false} tickLine={false}/>
                  <Tooltip contentStyle={{borderRadius:10,border:'1px solid var(--gray-200)',fontSize:12}}/>
                  <Line type="monotone" dataKey="actions" stroke="var(--blue)" strokeWidth={2}
                    dot={{r:3,fill:'var(--blue)'}} name="Actions"/>
                  <Line type="monotone" dataKey="echecs"  stroke="var(--red)"  strokeWidth={2}
                    dot={{r:3,fill:'var(--red)'}}  name="Échecs" strokeDasharray="4 2"/>
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* Répartition dossiers */}
        <div className="card fade-up" style={{animationDelay:'260ms'}}>
          <div className="card-header">
            <span className="card-title">Répartition des dossiers</span>
          </div>
          <div className="card-body">
            {pieData.length > 0 ? (
              <div style={{display:'flex',flexDirection:'column',alignItems:'center',gap:16}}>
                <div style={{height:180,width:'100%'}}>
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie data={pieData} cx="50%" cy="50%"
                        innerRadius={52} outerRadius={80}
                        dataKey="value" nameKey="name"
                        paddingAngle={3}>
                        {pieData.map((_,i) => <Cell key={i} fill={COLORS[i%COLORS.length]}/>)}
                      </Pie>
                      <Tooltip
                        contentStyle={{borderRadius:10,fontSize:12,border:'1px solid var(--gray-200)'}}
                        formatter={(value, name) => [value, name]}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
                {/* Légende personnalisée */}
                <div style={{display:'flex',flexWrap:'wrap',justifyContent:'center',gap:'8px 20px'}}>
                  {pieData.map((entry, i) => {
                    const total = pieData.reduce((s,d)=>s+d.value,0)
                    const pct   = total > 0 ? Math.round(entry.value/total*100) : 0
                    return (
                      <div key={entry.name} style={{display:'flex',alignItems:'center',gap:6,fontSize:12}}>
                        <span style={{width:10,height:10,borderRadius:3,background:COLORS[i%COLORS.length],flexShrink:0}}/>
                        <span style={{color:'var(--gray-600)',textTransform:'capitalize'}}>{entry.name}</span>
                        <span style={{fontWeight:700,color:'var(--gray-800)'}}>{entry.value}</span>
                        <span style={{color:'var(--gray-400)'}}>({pct}%)</span>
                      </div>
                    )
                  })}
                </div>
              </div>
            ) : (
              <div style={{height:220,display:'flex',alignItems:'center',justifyContent:'center'}}>
                <span style={{color:'var(--gray-300)',fontSize:14}}>Aucune donnée</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Stats audit globales */}
      {audit?.global && (
        <div className="card fade-up" style={{animationDelay:'320ms'}}>
          <div className="card-header">
            <span className="card-title">Journal d'audit — Vue globale</span>
            <span className="badge badge-navy">{audit.global.total} entrées</span>
          </div>
          <div className="card-body">
            <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(140px,1fr))',gap:12}}>
              {Object.entries(audit.global.par_statut||{}).map(([k,v]) => (
                <div key={k} style={{
                  background:'var(--gray-50)', borderRadius:10,
                  padding:'12px 14px', border:'1px solid var(--gray-100)',
                }}>
                  <div style={{fontSize:20,fontWeight:800,color:'var(--gray-800)'}}>{v}</div>
                  <div style={{fontSize:12,color:'var(--gray-400)',marginTop:3}}>{k}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
