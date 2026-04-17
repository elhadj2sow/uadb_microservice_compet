import { useState, useEffect } from 'react'
import api, { BASE } from '../../config/api'
import { BookOpen, TrendingUp, Award, BarChart2 } from 'lucide-react'

const MENTION_COLOR = { tres_bien:'success', bien:'info', assez_bien:'navy', passable:'warning', '':'neutral' }
const DECISION_COLOR = { admis:'success', rattrapage:'warning', 'ajourné':'danger', en_attente:'neutral' }

export default function MesResultats() {
  const [resultats, setResultats] = useState([])
  const [selected,  setSelected]  = useState(null)
  const [notes,     setNotes]     = useState([])
  const [loading,   setLoading]   = useState(true)

  useEffect(() => {
    api.get(`${BASE.resultat}/mes-resultats/`)
      .then(r => {
        const res = r.data.results || []
        setResultats(res)
        if (res.length) setSelected(res[0])
      })
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    if (!selected) return
    api.get(`${BASE.resultat}/${selected.id}/notes/`)
      .then(r => setNotes(r.data.notes || []))
  }, [selected])

  if (loading) return (
    <div className="page">
      {[1,2,3].map(i=><div key={i} className="skeleton" style={{height:80,marginBottom:16,borderRadius:12}}/>)}
    </div>
  )

  if (!resultats.length) return (
    <div className="page">
      <div className="page-header"><h1 className="page-title">Mes Résultats</h1></div>
      <div className="card"><div className="card-body"><div className="empty-state">
        <div className="empty-state-icon"><BookOpen size={32}/></div>
        <p>Aucun résultat disponible pour le moment.</p>
      </div></div></div>
    </div>
  )

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Mes Résultats</h1>
        <p className="page-subtitle">Consultez vos résultats de délibération par semestre</p>
      </div>

      {/* Onglets sessions */}
      <div className="tabs">
        {resultats.map(r => (
          <div
            key={r.id}
            className={`tab-item ${selected?.id === r.id ? 'active' : ''}`}
            onClick={() => setSelected(r)}
          >
            S{r.semestre} — {r.annee_universitaire} ({r.session})
          </div>
        ))}
      </div>

      {selected && (
        <>
          {/* Résumé */}
          <div className="stats-grid fade-up" style={{marginBottom:20}}>
            <div className="stat-card blue">
              <div className="stat-icon-wrap blue"><TrendingUp size={20}/></div>
              <div className="stat-value">
                {selected.moyenne_annuelle ? parseFloat(selected.moyenne_annuelle).toFixed(2) : '—'}
              </div>
              <div className="stat-label">Moyenne / 20</div>
            </div>
            <div className="stat-card teal">
              <div className="stat-icon-wrap teal"><BookOpen size={20}/></div>
              <div className="stat-value">{selected.credits_valides}/{selected.credits_total}</div>
              <div className="stat-label">Crédits validés</div>
            </div>
            <div className="stat-card gold">
              <div className="stat-icon-wrap gold"><Award size={20}/></div>
              <div className="stat-value" style={{fontSize:'1.2rem'}}>
                {selected.decision || '—'}
              </div>
              <div className="stat-label">Décision du jury</div>
            </div>
            <div className="stat-card" style={{border:'1px solid var(--gray-200)'}}>
              <div className="stat-icon-wrap" style={{background:'var(--gray-100)',color:'var(--gray-500)'}}><BarChart2 size={20}/></div>
              <div className="stat-value" style={{fontSize:'1.3rem'}}>
                {selected.rang ? `#${selected.rang}` : '—'}
              </div>
              <div className="stat-label">Rang de promotion</div>
            </div>
          </div>

          {/* Badges décision/mention */}
          <div className="card fade-up" style={{marginBottom:20}}>
            <div className="card-padded" style={{display:'flex',alignItems:'center',gap:12,flexWrap:'wrap'}}>
              <span style={{fontSize:14,fontWeight:600,color:'var(--gray-600)'}}>Résumé :</span>
              <span className={`badge badge-${DECISION_COLOR[selected.decision]||'neutral'}`}
                style={{fontSize:13,padding:'5px 14px'}}>
                Décision : {selected.decision || 'En attente'}
              </span>
              {selected.mention && (
                <span className={`badge badge-${MENTION_COLOR[selected.mention]||'neutral'}`}
                  style={{fontSize:13,padding:'5px 14px'}}>
                  Mention : {selected.mention.replace('_',' ')}
                </span>
              )}
            </div>
          </div>

          {/* Notes par UE */}
          {notes.length > 0 && (
            <div className="card fade-up" style={{animationDelay:'120ms'}}>
              <div className="card-header">
                <span className="card-title">Détail des notes par UE</span>
                <span className="badge badge-navy">{notes.length} UEs</span>
              </div>
              <div className="table-wrap">
                <table>
                  <thead><tr>
                    <th>Code UE</th><th>Intitulé</th>
                    <th>CC (30%)</th><th>TP (20%)</th><th>Examen (50%)</th>
                    <th>Note finale</th><th>Crédits</th><th>Statut</th>
                  </tr></thead>
                  <tbody>
                    {notes.map(n => (
                      <tr key={n.id}>
                        <td><span className="chip font-mono">{n.code_ue || `UE${n.ue_id}`}</span></td>
                        <td style={{maxWidth:200}}>{n.libelle_ue || '—'}</td>
                        <td>{n.note_cc    != null ? parseFloat(n.note_cc).toFixed(1)    : '—'}</td>
                        <td>{n.note_tp    != null ? parseFloat(n.note_tp).toFixed(1)    : '—'}</td>
                        <td>{n.note_examen!= null ? parseFloat(n.note_examen).toFixed(1): '—'}</td>
                        <td>
                          <strong style={{color: n.valeur && parseFloat(n.valeur)>=10 ? 'var(--success)' : 'var(--danger)'}}>
                            {n.valeur ? parseFloat(n.valeur).toFixed(2) : '—'}/20
                          </strong>
                        </td>
                        <td>{n.credit_ue}</td>
                        <td>
                          <span className={`badge badge-${n.est_validee ? 'success':'danger'}`}>
                            {n.est_validee ? 'Validée' : 'Non validée'}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}
