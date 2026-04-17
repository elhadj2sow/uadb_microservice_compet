import { useState, useEffect } from 'react'
import { useAuth } from '../../context/AuthContext'
import { Link } from 'react-router-dom'
import api, { BASE } from '../../config/api'
import {
  BookOpen, Users, CheckCircle, Clock,
  TrendingUp, FileText, ArrowRight
} from 'lucide-react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Cell
} from 'recharts'

export default function DashboardPedagogue() {
  const { user }          = useAuth()
  const [delibs,  setDelibs]  = useState([])
  const [stats,   setStats]   = useState(null)
  const [loading, setLoading] = useState(true)
  const annee = `${new Date().getFullYear()}-${new Date().getFullYear() + 1}`

  useEffect(() => {
    Promise.allSettled([
      api.get(`${BASE.deliberation}/?annee=${annee}`),
      api.get(`${BASE.deliberation}/statistiques/?annee=${annee}`),
    ]).then(([d, s]) => {
      if (d.status === 'fulfilled') setDelibs((d.value.data.results || []).slice(0, 5))
      if (s.status === 'fulfilled') setStats(s.value.data)
    }).finally(() => setLoading(false))
  }, [])

  const CARDS = [
    { label: 'Total étudiants', value: stats?.nb_etudiants_total || 0,          color: 'blue', icon: Users },
    { label: 'Admis',           value: stats?.par_decision?.admis || 0,          color: 'teal', icon: CheckCircle },
    { label: 'Rattrapage',      value: stats?.par_decision?.rattrapage || 0,     color: 'gold', icon: Clock },
    { label: 'Délibérations',   value: stats?.nb_deliberations || 0,             color: 'blue', icon: BookOpen },
  ]

  const chartData = stats ? [
    { name: 'Admis',      value: stats.par_decision?.admis          || 0, fill: '#00897b' },
    { name: 'Rattrapage', value: stats.par_decision?.rattrapage     || 0, fill: '#f59e0b' },
    { name: 'Ajourné',    value: stats.par_decision?.['ajourné']    || 0, fill: '#e53935' },
    { name: 'En attente', value: stats.par_decision?.en_attente     || 0, fill: '#94a3b8' },
  ] : []

  const STATUT_COLOR = { cloturee: 'success', en_cours: 'info', en_preparation: 'neutral' }

  return (
    <div className="page">

      {/* Banner */}
      <div className="welcome-banner">
        <div className="welcome-content">
          <div className="welcome-title">Espace Responsable Pédagogique</div>
          <div className="welcome-subtitle">
            Bienvenue {user?.username} — Délibérations {annee}
          </div>
        </div>
      </div>

      {/* Stats cards */}
      {loading ? (
        <div className="stats-grid">
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="skeleton" style={{ height: 120, borderRadius: 16 }} />
          ))}
        </div>
      ) : (
        <div className="stats-grid fade-up">
          {CARDS.map((c, i) => (
            <div key={c.label} className={`stat-card ${c.color}`}
              style={{ animationDelay: `${i * 60}ms` }}>
              <div className={`stat-icon-wrap ${c.color}`}><c.icon size={20} /></div>
              <div className="stat-value">{c.value}</div>
              <div className="stat-label">{c.label}</div>
              {c.label === 'Admis' && stats?.taux_reussite != null && (
                <div style={{ fontSize: 11, color: 'var(--teal)', fontWeight: 600, marginTop: 2 }}>
                  Taux : {stats.taux_reussite}%
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Graphique + liste */}
      <div className="grid-2" style={{ gap: 20, marginBottom: 20 }}>

        {/* Graphique répartition */}
        <div className="card fade-up" style={{ animationDelay: '200ms' }}>
          <div className="card-header">
            <span className="card-title">Répartition des décisions</span>
            <span className="badge badge-navy">{annee}</span>
          </div>
          <div className="card-body">
            {chartData.every(d => d.value === 0) ? (
              <div className="empty-state" style={{ padding: 24 }}>
                <div className="empty-state-icon"><TrendingUp size={26} /></div>
                <p style={{ fontSize: 13 }}>Aucune délibération clôturée</p>
              </div>
            ) : (
              <div style={{ height: 220 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData} margin={{ top: 5, right: 10, bottom: 5, left: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--gray-100)" vertical={false} />
                    <XAxis dataKey="name" tick={{ fontSize: 11, fill: 'var(--gray-400)' }} axisLine={false} tickLine={false} />
                    <YAxis tick={{ fontSize: 11, fill: 'var(--gray-400)' }} axisLine={false} tickLine={false} />
                    <Tooltip
                      contentStyle={{ borderRadius: 10, border: '1px solid var(--gray-200)', fontSize: 12 }}
                      cursor={{ fill: 'rgba(0,0,0,.03)' }}
                    />
                    <Bar dataKey="value" radius={[6, 6, 0, 0]}>
                      {chartData.map((entry, i) => <Cell key={i} fill={entry.fill} />)}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>
        </div>

        {/* Délibérations récentes */}
        <div className="card fade-up" style={{ animationDelay: '260ms' }}>
          <div className="card-header">
            <span className="card-title">Délibérations récentes</span>
            <Link to="/pedagogue/deliberations" className="btn btn-sm btn-ghost">
              Voir tout <ArrowRight size={13} />
            </Link>
          </div>
          {loading ? (
            <div className="card-body">
              {[1, 2, 3].map(i => (
                <div key={i} className="skeleton" style={{ height: 50, marginBottom: 10, borderRadius: 8 }} />
              ))}
            </div>
          ) : delibs.length === 0 ? (
            <div className="card-body">
              <div className="empty-state">
                <div className="empty-state-icon"><BookOpen size={28} /></div>
                <p style={{ fontSize: 13 }}>Aucune délibération pour cette année</p>
                <Link to="/pedagogue/deliberations" className="btn btn-primary btn-sm" style={{ marginTop: 12 }}>
                  Créer une délibération
                </Link>
              </div>
            </div>
          ) : (
            <div>
              {delibs.map((d, i) => (
                <div key={d.id} style={{
                  display: 'flex', alignItems: 'center', gap: 14,
                  padding: '12px 20px',
                  borderBottom: i < delibs.length - 1 ? '1px solid var(--gray-100)' : 'none',
                }}>
                  <div style={{
                    width: 36, height: 36, borderRadius: 8, flexShrink: 0,
                    background: d.statut === 'cloturee' ? 'var(--success-bg)'
                      : d.statut === 'en_cours' ? 'var(--info-bg)' : 'var(--gray-100)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    color: d.statut === 'cloturee' ? 'var(--success)'
                      : d.statut === 'en_cours' ? 'var(--info)' : 'var(--gray-400)',
                  }}>
                    <BookOpen size={16} />
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--gray-800)' }}>
                      S{d.semestre} — {d.niveau} — {d.session}
                    </div>
                    <div style={{ fontSize: 11, color: 'var(--gray-400)', marginTop: 1 }}>
                      {d.nb_etudiants || 0} étudiant(s) • {d.annee_universitaire}
                    </div>
                  </div>
                  <span className={`badge badge-${STATUT_COLOR[d.statut] || 'neutral'}`}>
                    {d.statut}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Actions rapides */}
      <div className="card fade-up" style={{ animationDelay: '320ms' }}>
        <div className="card-header"><span className="card-title">Actions rapides</span></div>
        <div className="card-body" style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 12 }}>
          {[
            { label: 'Créer une délibération', icon: BookOpen,    to: '/pedagogue/deliberations', bg: '#e3f2fd', tc: '#1565c0' },
            { label: 'Saisir des notes',        icon: FileText,    to: '/pedagogue/notes',          bg: '#e0f2f1', tc: '#00897b' },
            { label: 'Voir statistiques',       icon: TrendingUp,  to: '/pedagogue/deliberations',  bg: '#fffde7', tc: '#f59e0b' },
          ].map(a => (
            <Link key={a.label} to={a.to} style={{
              display: 'flex', alignItems: 'center', gap: 12,
              padding: '14px 16px', borderRadius: 10,
              background: a.bg, border: `1px solid ${a.bg}`,
              textDecoration: 'none', transition: 'all .15s',
            }}
              onMouseEnter={e => e.currentTarget.style.transform = 'translateY(-2px)'}
              onMouseLeave={e => e.currentTarget.style.transform = 'none'}
            >
              <a.icon size={18} color={a.tc} />
              <span style={{ fontSize: 13, fontWeight: 600, color: a.tc }}>{a.label}</span>
            </Link>
          ))}
        </div>
      </div>
    </div>
  )
}
