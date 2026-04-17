import { useState, useEffect } from 'react'
import { useAuth } from '../../context/AuthContext'
import { Link } from 'react-router-dom'
import api, { BASE } from '../../config/api'
import { FolderOpen, ClipboardList, BookOpen, FileText, ArrowRight, CheckCircle, Clock, AlertCircle } from 'lucide-react'

export default function DashboardEtudiant() {
  const { user }   = useAuth()
  const [dossier, setDossier]       = useState(null)
  const [inscription, setInscription] = useState(null)
  const [resultats, setResultats]   = useState([])
  const [loading, setLoading]       = useState(true)

  useEffect(() => {
    const annee = `${new Date().getFullYear()}-${new Date().getFullYear()+1}`
    Promise.allSettled([
      api.get(`${BASE.dossier}/mon-dossier/?annee=${annee}`),
      api.get(`${BASE.inscription}/mon-inscription/?annee=${annee}`),
      api.get(`${BASE.resultat}/mes-resultats/`),
    ]).then(([d, i, r]) => {
      if (d.status === 'fulfilled') setDossier(d.value.data)
      if (i.status === 'fulfilled') setInscription(i.value.data)
      if (r.status === 'fulfilled') setResultats(r.value.data.results || [])
    }).finally(() => setLoading(false))
  }, [])

  const scoreColor = s => s === 100 ? 'teal' : s >= 50 ? 'gold' : 'red'
  const CARDS = [
    { label: 'Mon Dossier',  icon: FolderOpen,     to: '/dossier',    color: 'blue',
      value: dossier ? `${dossier.score_completude}%` : '—',
      sub  : dossier ? dossier.etat_dossier : 'Non créé' },
    { label: 'Inscription',  icon: ClipboardList,  to: '/inscription', color: 'teal',
      value: inscription ? inscription.statut_inscription : '—',
      sub  : inscription ? `Matricule : ${inscription.numero_inscription || '—'}` : 'Non soumise' },
    { label: 'Résultats',    icon: BookOpen,        to: '/resultats',  color: 'gold',
      value: resultats[0] ? `${resultats[0].moyenne_annuelle || '—'}/20` : '—',
      sub  : resultats[0] ? resultats[0].decision : 'Aucun résultat' },
    { label: 'Attestations', icon: FileText,        to: '/attestations',color: 'red',
      value: '5', sub: 'Types disponibles' },
  ]

  return (
    <div className="page">
      <div className="welcome-banner">
        <div className="welcome-content">
          <div className="welcome-title">Bonjour, {user?.username} 👋</div>
          <div className="welcome-subtitle">
            Bienvenue sur votre portail étudiant UADB — Année {new Date().getFullYear()}-{new Date().getFullYear()+1}
          </div>
        </div>
      </div>

      {/* Stats rapides */}
      <div className="stats-grid fade-up">
        {CARDS.map((c, i) => (
          <Link to={c.to} key={c.label} style={{textDecoration:'none',animationDelay:`${i*60}ms`}} className="fade-up">
            <div className={`stat-card ${c.color}`} style={{cursor:'pointer'}}>
              <div className={`stat-icon-wrap ${c.color}`}>
                <c.icon size={20} />
              </div>
              <div className="stat-value">{loading ? <div className="skeleton" style={{height:32,width:60}}/> : c.value}</div>
              <div>
                <div className="stat-label">{c.label}</div>
                <div style={{fontSize:12,color:'var(--gray-400)',marginTop:2}}>{c.sub}</div>
              </div>
            </div>
          </Link>
        ))}
      </div>

      <div className="grid-2" style={{gap:20}}>
        {/* Dossier */}
        <div className="card fade-up" style={{animationDelay:'200ms'}}>
          <div className="card-header">
            <span className="card-title">État du dossier</span>
            <Link to="/etudiant/dossier" className="btn btn-sm btn-ghost">
              Voir <ArrowRight size={13}/>
            </Link>
          </div>
          <div className="card-body">
            {loading ? (
              <div>
                {[1,2,3].map(i => <div key={i} className="skeleton" style={{height:16,marginBottom:12,width:`${70+i*10}%`}}/>)}
              </div>
            ) : dossier ? (
              <div>
                <div className="flex items-center justify-between mb-4">
                  <span style={{fontSize:13,color:'var(--gray-500)'}}>Complétude</span>
                  <span style={{fontWeight:700,color:'var(--gray-800)'}}>{dossier.score_completude}%</span>
                </div>
                <div className="progress mb-4">
                  <div
                    className={`progress-bar ${scoreColor(dossier.score_completude)}`}
                    style={{width:`${dossier.score_completude}%`}}
                  />
                </div>
                {dossier.pieces_manquantes?.length > 0 && (
                  <div className="alert alert-warning" style={{padding:'10px 14px',fontSize:12}}>
                    <AlertCircle size={14}/>
                    <span>{dossier.pieces_manquantes.length} pièce(s) manquante(s)</span>
                  </div>
                )}
                {dossier.score_completude === 100 && (
                  <div className="alert alert-success" style={{padding:'10px 14px',fontSize:12}}>
                    <CheckCircle size={14}/>
                    <span>Dossier complet !</span>
                  </div>
                )}
              </div>
            ) : (
              <div className="empty-state">
                <div className="empty-state-icon"><FolderOpen size={28}/></div>
                <p style={{fontSize:13}}>Aucun dossier pour cette année</p>
                <Link to="/etudiant/dossier" className="btn btn-primary btn-sm" style={{marginTop:12}}>
                  Créer mon dossier
                </Link>
              </div>
            )}
          </div>
        </div>

        {/* Workflow inscription */}
        <div className="card fade-up" style={{animationDelay:'260ms'}}>
          <div className="card-header">
            <span className="card-title">Workflow d'inscription</span>
            <Link to="/etudiant/inscription" className="btn btn-sm btn-ghost">
              Voir <ArrowRight size={13}/>
            </Link>
          </div>
          <div className="card-body">
            {loading ? (
              <div>{[1,2,3,4].map(i=><div key={i} className="skeleton" style={{height:14,marginBottom:14,width:'80%'}}/>)}</div>
            ) : inscription ? (
              <div>
                <div className="steps">
                  {['Scolarité','Comptabilité','Médical','Bibliothèque'].map((s, i) => {
                    const etapes = inscription.etapes || []
                    const etape  = etapes[i]
                    const done   = etape?.statut === 'valide'
                    const active = !done && etapes.slice(0,i).every(e=>e?.statut==='valide')
                    return (
                      <div key={s} className={`step ${done?'done':active?'active':''}`}>
                        <div className="step-circle">
                          {done ? <CheckCircle size={14}/> : i+1}
                        </div>
                        <div className="step-label">{s}</div>
                      </div>
                    )
                  })}
                </div>
                <div style={{marginTop:16,padding:'12px 14px',background:'var(--gray-50)',borderRadius:8}}>
                  <div style={{fontSize:12,color:'var(--gray-400)'}}>Statut</div>
                  <div style={{fontSize:14,fontWeight:600,color:'var(--gray-700)',marginTop:2}}>
                    {inscription.statut_inscription || 'en_cours'}
                  </div>
                </div>
              </div>
            ) : (
              <div className="empty-state">
                <div className="empty-state-icon"><ClipboardList size={28}/></div>
                <p style={{fontSize:13}}>Aucune inscription en cours</p>
                <Link to="/etudiant/inscription" className="btn btn-primary btn-sm" style={{marginTop:12}}>
                  Commencer l'inscription
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Derniers résultats */}
      {resultats.length > 0 && (
        <div className="card fade-up" style={{marginTop:20,animationDelay:'320ms'}}>
          <div className="card-header">
            <span className="card-title">Mes derniers résultats</span>
            <Link to="/etudiant/resultats" className="btn btn-sm btn-ghost">Voir tout <ArrowRight size={13}/></Link>
          </div>
          <div className="table-wrap">
            <table>
              <thead><tr>
                <th>Année</th><th>Semestre</th><th>Session</th>
                <th>Moyenne</th><th>Décision</th><th>Mention</th>
              </tr></thead>
              <tbody>
                {resultats.slice(0,4).map(r => (
                  <tr key={r.id}>
                    <td>{r.annee_universitaire}</td>
                    <td>S{r.semestre}</td>
                    <td><span className="badge badge-navy">{r.session}</span></td>
                    <td><strong>{r.moyenne_annuelle ? `${parseFloat(r.moyenne_annuelle).toFixed(2)}/20` : '—'}</strong></td>
                    <td>
                      <span className={`badge badge-${r.decision==='admis'?'success':r.decision==='rattrapage'?'warning':'danger'}`}>
                        {r.decision}
                      </span>
                    </td>
                    <td>{r.mention || '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
