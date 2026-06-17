import { useState, useEffect, useCallback } from 'react'
import { Bell, RefreshCw, AlertTriangle, CheckCircle, Clock, BarChart2 } from 'lucide-react'
import api, { BASE } from '../../config/api'

const STATUT_BADGE = {
  envoye    : 'success',
  echec     : 'danger',
  en_attente: 'warning',
  lu        : 'info',
}

const CANAL_BADGE = {
  email   : 'info',
  sms     : 'navy',
  interne : 'neutral',
  push    : 'warning',
}

export default function NotificationsAdmin() {
  const [notifs,  setNotifs]  = useState([])
  const [stats,   setStats]   = useState(null)
  const [loading, setLoading] = useState(true)
  const [relance, setRelance] = useState(false)
  const [msg,     setMsg]     = useState(null)
  const [filterStatut, setFilterStatut] = useState('')
  const [filterCanal,  setFilterCanal]  = useState('')

  const flashMsg = (type, text) => {
    setMsg({ type, text })
    setTimeout(() => setMsg(null), 5000)
  }

  const charger = useCallback(() => {
    setLoading(true)
    const params = {}
    if (filterStatut) params.statut = filterStatut
    if (filterCanal)  params.canal  = filterCanal

    Promise.all([
      api.get(`${BASE.notification}/admin/`, { params }),
      api.get(`${BASE.notification}/statistiques/`),
    ])
      .then(([r1, r2]) => {
        setNotifs(r1.data.results || [])
        setStats(r2.data)
      })
      .catch(() => flashMsg('error', 'Erreur de chargement.'))
      .finally(() => setLoading(false))
  }, [filterStatut, filterCanal])

  useEffect(() => { charger() }, [charger])

  const relancerEchecs = async () => {
    setRelance(true)
    try {
      const r = await api.post(`${BASE.notification}/admin/relancer/`)
      flashMsg('success', r.data.message)
      charger()
    } catch (e) {
      flashMsg('error', e.response?.data?.error || 'Erreur lors de la relance.')
    } finally {
      setRelance(false)
    }
  }

  const nbEchecs = stats?.par_statut?.echec ?? notifs.filter(n => n.statut_envoi === 'echec').length

  return (
    <div className="page-content">
      {/* Header */}
      <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:'1.5rem', flexWrap:'wrap', gap:'1rem' }}>
        <div style={{ display:'flex', alignItems:'center', gap:'.75rem' }}>
          <Bell size={24} style={{ color:'var(--blue)' }}/>
          <div>
            <h1 className="page-title" style={{ margin:0 }}>Notifications — Administration</h1>
            <p className="page-subtitle" style={{ margin:0 }}>Supervision et relance des notifications échouées</p>
          </div>
        </div>
        <button
          className="btn btn-primary"
          disabled={relance || nbEchecs === 0}
          onClick={relancerEchecs}
          title={nbEchecs === 0 ? 'Aucune notification en échec' : `Relancer ${nbEchecs} notification(s) en échec`}
        >
          <RefreshCw size={15} style={relance ? { animation:'spin 1s linear infinite' } : {}}/>
          {relance ? 'Relance en cours…' : `Relancer les échecs${nbEchecs ? ` (${nbEchecs})` : ''}`}
        </button>
      </div>

      {/* Message flash */}
      {msg && (
        <div className={`alert alert-${msg.type === 'error' ? 'danger' : 'success'}`}
             style={{ marginBottom:'1rem' }}>
          {msg.type === 'success' ? <CheckCircle size={16}/> : <AlertTriangle size={16}/>}
          {' '}{msg.text}
        </div>
      )}

      {/* Stats */}
      {stats && (
        <div style={{ display:'grid', gridTemplateColumns:'repeat(auto-fit, minmax(150px,1fr))', gap:'1rem', marginBottom:'1.5rem' }}>
          {[
            { label:'Total',        value: stats.total,                          color:'var(--blue)',    icon: Bell },
            { label:'Envoyés',      value: stats.par_statut?.envoye ?? 0,        color:'var(--green)',   icon: CheckCircle },
            { label:'Échecs',       value: stats.par_statut?.echec  ?? 0,        color:'var(--red)',     icon: AlertTriangle },
            { label:'En attente',   value: stats.par_statut?.en_attente ?? 0,    color:'var(--yellow)',  icon: Clock },
            { label:'Taux réussite',value: `${stats.taux_reussite ?? 0}%`,       color:'var(--teal)',    icon: BarChart2 },
          ].map(({ label, value, color, icon: Icon }) => (
            <div key={label} className="card" style={{ padding:'1rem', textAlign:'center' }}>
              <Icon size={20} style={{ color, margin:'0 auto .5rem' }}/>
              <div style={{ fontSize:'1.5rem', fontWeight:700, color }}>{value}</div>
              <div style={{ fontSize:'.8rem', color:'var(--muted)' }}>{label}</div>
            </div>
          ))}
        </div>
      )}

      {/* Filtres */}
      <div className="card" style={{ padding:'1rem', marginBottom:'1.25rem' }}>
        <div style={{ display:'flex', flexWrap:'wrap', gap:'.75rem', alignItems:'flex-end' }}>
          <div>
            <label className="form-label">Statut</label>
            <select className="form-control" value={filterStatut} onChange={e => setFilterStatut(e.target.value)}>
              <option value="">Tous les statuts</option>
              {['en_attente','envoye','echec','lu'].map(s => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
          <div>
            <label className="form-label">Canal</label>
            <select className="form-control" value={filterCanal} onChange={e => setFilterCanal(e.target.value)}>
              <option value="">Tous les canaux</option>
              {['email','sms','interne','push'].map(c => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
          <button className="btn btn-secondary" onClick={charger}>Actualiser</button>
        </div>
      </div>

      {/* Tableau */}
      <div className="card">
        {loading ? (
          <div style={{ textAlign:'center', padding:'2rem' }}><div className="spinner spinner-dark"/></div>
        ) : (
          <div style={{ overflowX:'auto' }}>
            <table className="table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Type</th>
                  <th>Destinataire</th>
                  <th>Canal</th>
                  <th>Statut</th>
                  <th>Service émetteur</th>
                  <th>Tentatives</th>
                </tr>
              </thead>
              <tbody>
                {notifs.length === 0 && (
                  <tr>
                    <td colSpan={7} style={{ textAlign:'center', padding:'2rem', color:'var(--muted)' }}>
                      Aucune notification pour ces filtres.
                    </td>
                  </tr>
                )}
                {notifs.map(n => (
                  <tr key={n.id} style={n.statut_envoi === 'echec' ? { background:'rgba(239,68,68,.04)' } : {}}>
                    <td style={{ fontSize:'.8rem', fontFamily:'monospace', whiteSpace:'nowrap', color:'var(--muted)' }}>
                      {new Date(n.date_notification).toLocaleString('fr-FR')}
                    </td>
                    <td style={{ fontSize:'.85rem' }}>{n.type_notification || '—'}</td>
                    <td style={{ fontSize:'.85rem' }}>
                      {n.etudiant_username || `#${n.etudiant_id}` || '—'}
                    </td>
                    <td>
                      <span className={`badge badge-${CANAL_BADGE[n.canal] || 'neutral'}`} style={{ fontSize:'.75rem' }}>
                        {n.canal}
                      </span>
                    </td>
                    <td>
                      <span className={`badge badge-${STATUT_BADGE[n.statut_envoi] || 'neutral'}`} style={{ fontSize:'.75rem' }}>
                        {n.statut_envoi}
                      </span>
                    </td>
                    <td style={{ fontSize:'.8rem', color:'var(--muted)' }}>{n.emetteur_service || '—'}</td>
                    <td style={{ textAlign:'center', fontSize:'.85rem' }}>
                      {n.nb_tentatives ?? '—'}
                      {n.statut_envoi === 'echec' && n.message_erreur && (
                        <div style={{ fontSize:'.72rem', color:'var(--red)', marginTop:'.15rem', maxWidth:200, overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap' }}
                             title={n.message_erreur}>
                          {n.message_erreur}
                        </div>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div style={{ padding:'.75rem 1rem', color:'var(--muted)', fontSize:'.85rem' }}>
              {notifs.length} notification(s) affichée(s)
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
