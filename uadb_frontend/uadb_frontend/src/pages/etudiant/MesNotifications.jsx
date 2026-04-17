import { useState, useEffect } from 'react'
import api, { BASE } from '../../config/api'
import toast from 'react-hot-toast'
import { Bell, Mail, MessageSquare, CheckCheck, Circle } from 'lucide-react'

export default function MesNotifications() {
  const [notifs,  setNotifs]  = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get(`${BASE.notification}/mes-notifications/`)
      .then(r => setNotifs(r.data.results || []))
      .finally(() => setLoading(false))
  }, [])

  const marquerToutesLues = async () => {
    await api.post(`${BASE.notification}/tout-lire/`)
    setNotifs(n => n.map(x => ({ ...x, statut_envoi: 'lu', date_lecture: new Date() })))
    toast.success('Toutes les notifications marquées comme lues.')
  }

  const marquerLue = async id => {
    await api.patch(`${BASE.notification}/${id}/lire/`)
    setNotifs(n => n.map(x => x.id === id ? { ...x, statut_envoi: 'lu' } : x))
  }

  const nonLues = notifs.filter(n => n.statut_envoi === 'envoye').length

  const TYPE_ICON = {
    inscription: '🎓', dossier: '📁', deliberation: '📊',
    attestation: '📄', workflow: '⚙️', paiement: '💳',
    systeme: '🔔', chatbot: '🤖'
  }

  return (
    <div className="page">
      <div className="page-header flex items-center justify-between">
        <div>
          <h1 className="page-title">Notifications</h1>
          <p className="page-subtitle">{nonLues} non lue(s)</p>
        </div>
        {nonLues > 0 && (
          <button className="btn btn-ghost" onClick={marquerToutesLues}>
            <CheckCheck size={15}/> Tout marquer lu
          </button>
        )}
      </div>

      <div className="card fade-up">
        {loading ? (
          <div className="card-body">
            {[1,2,3,4].map(i=><div key={i} className="skeleton" style={{height:70,marginBottom:12,borderRadius:8}}/>)}
          </div>
        ) : notifs.length === 0 ? (
          <div className="card-body"><div className="empty-state">
            <div className="empty-state-icon"><Bell size={30}/></div>
            <p>Aucune notification pour le moment.</p>
          </div></div>
        ) : (
          <div>
            {notifs.map((n, i) => (
              <div
                key={n.id}
                onClick={() => n.statut_envoi === 'envoye' && marquerLue(n.id)}
                style={{
                  display:'flex', gap:14, padding:'16px 24px',
                  borderBottom: i<notifs.length-1 ? '1px solid var(--gray-100)' : 'none',
                  background: n.statut_envoi === 'envoye' ? 'rgba(2,132,199,.03)' : 'white',
                  cursor: n.statut_envoi === 'envoye' ? 'pointer' : 'default',
                  transition:'background .12s',
                }}
              >
                <div style={{
                  width:40, height:40, borderRadius:10, flexShrink:0,
                  background:'var(--gray-50)', border:'1px solid var(--gray-200)',
                  display:'flex', alignItems:'center', justifyContent:'center', fontSize:18,
                }}>
                  {TYPE_ICON[n.type_notification] || '🔔'}
                </div>
                <div style={{flex:1}}>
                  <div style={{
                    fontSize:14, fontWeight: n.statut_envoi==='envoye' ? 600 : 500,
                    color:'var(--gray-800)', lineHeight:1.4
                  }}>
                    {n.message}
                  </div>
                  <div style={{fontSize:12,color:'var(--gray-400)',marginTop:4,display:'flex',gap:12}}>
                    <span>{new Date(n.date_notification).toLocaleString('fr-FR')}</span>
                    <span className={`badge badge-${n.canal==='email'?'info':'navy'}`} style={{fontSize:10}}>
                      {n.canal}
                    </span>
                  </div>
                </div>
                {n.statut_envoi === 'envoye' && (
                  <Circle size={8} style={{color:'var(--blue)',fill:'var(--blue)',flexShrink:0,marginTop:6}}/>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
