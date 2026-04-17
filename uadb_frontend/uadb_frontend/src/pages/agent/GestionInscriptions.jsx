import { useState, useEffect } from 'react'
import api, { BASE } from '../../config/api'
import toast from 'react-hot-toast'
import { Search, CheckCircle, XCircle, Eye, Clock } from 'lucide-react'
import { getServiceFromRoles } from '../../utils/serviceConnecte'

const BADGE = {
  validee:'success', refusee:'danger',
  en_cours:'info', en_attente:'neutral', provisoire:'warning'
}
const ETAPES_LABELS = {
  scolarite:'Scolarité', comptabilite:'Comptabilité',
  medical:'Médical', bibliotheque:'Bibliothèque'
}

export default function GestionInscriptions() {
  const [inscriptions, setInscriptions] = useState([])
  const [total,        setTotal]        = useState(0)
  const [loading,      setLoading]      = useState(true)
  const [selected,     setSelected]     = useState(null)
  const [validating,   setValidating]   = useState(false)
  const [serviceConnecte, setServiceConnecte] = useState(null)
  // Pour la modale de validation/rejet
  const [etapeAction, setEtapeAction] = useState(null) // {etape, action}
  const [observation, setObservation] = useState("")

  // Ne plus enrichir le nom étudiant (évite les 403)
  const charger = async () => {
    setLoading(true)
    try {
      const r = await api.get(`${BASE.inscription}/liste/`)
      setInscriptions(r.data.results || [])
      setTotal(r.data.count || 0)
    } catch (e) {
      toast.error("Impossible de charger les inscriptions")
      console.error(e)
    } finally { setLoading(false) }
  }

  useEffect(() => {
    charger()
    // Récupérer le profil connecté pour déterminer le service
    api.get(`${BASE.auth}/me/`).then(r => {
      const roles = r.data.roles || []
      setServiceConnecte(getServiceFromRoles(roles))
    })
  }, [])

  const validerEtape = async (inscriptionId, etapeId, action, observation) => {
    setValidating(true)
    try {
      await api.patch(`${BASE.inscription}/${inscriptionId}/valider-etape/`, {
        etape_id: etapeId, action, observation
      })
      toast.success(`Étape ${action === 'valider' ? 'validée' : 'rejetée'} !`)
      charger()
      setSelected(null)
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Erreur.')
    } finally { setValidating(false); setEtapeAction(null); setObservation("") }
  }

  // Fonction pour charger une inscription complète (avec workflow)
  const handleVoirInscription = async (insc) => {
    try {
      const r = await api.get(`${BASE.inscription}/${insc.id}/`)
      // enrichir le nom étudiant si besoin
      let etudiant_nom = insc.etudiant_nom
      if (!etudiant_nom) {
        try {
          const r2 = await api.get(`${BASE.auth}/utilisateurs/${insc.etudiant_id}/`)
          etudiant_nom = r2.data.username || r2.data.email
        } catch {}
      }
      setSelected({ ...r.data, etudiant_nom })
    } catch (e) {
      toast.error("Impossible de charger l'inscription complète")
    }
  }

  return (
    <div className="page">
      <div className="page-header flex items-center justify-between">
        <div>
          <h1 className="page-title">Gestion des Inscriptions</h1>
          <p className="page-subtitle">{total} inscription(s)</p>
        </div>
      </div>

      <div className="card fade-up">
        {loading ? (
          <div className="card-body">
            {[1,2,3,4].map(i => <div key={i} className="skeleton" style={{height:55,marginBottom:10,borderRadius:8}}/>)}
          </div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead><tr>
                <th>N° Inscription</th><th>Étudiant</th>
                <th>Formation</th><th>Année</th>
                <th>Type</th><th>Statut</th><th>Date</th><th>Actions</th>
              </tr></thead>
              <tbody>
                {inscriptions.map(insc => (
                  <tr key={insc.id}>
                    <td className="font-mono" style={{fontSize:12,color:'var(--blue)'}}>
                      {insc.numero_inscription || insc.numero_provisoire || `#${insc.id}`}
                    </td>
                    <td style={{fontWeight:600}}>{insc.etudiant_nom || `Étudiant #${insc.etudiant_id}`}</td>
                    <td>{insc.formation_libelle || `Formation #${insc.formation_id}`}</td>
                    <td>{insc.annee_universitaire}</td>
                    <td>
                      <span style={{
                        fontSize:11,fontWeight:600,padding:'2px 7px',borderRadius:99,
                        background: insc.type_inscription==='reinscription' ? '#fff7ed' : '#ebf2ff',
                        color:      insc.type_inscription==='reinscription' ? 'var(--warning)' : 'var(--blue)',
                      }}>
                        {insc.type_inscription==='reinscription' ? '🔄 Réinsc.' : '🎓 1ère'}
                      </span>
                    </td>
                    <td>
                      <span className={`badge badge-${BADGE[insc.statut_inscription]||'neutral'}`}>
                        {insc.statut_inscription}
                      </span>
                    </td>
                    <td style={{fontSize:12,color:'var(--gray-400)'}}>
                      {insc.date_preinscription ? new Date(insc.date_preinscription).toLocaleDateString('fr-FR') : '—'}
                    </td>
                    <td>
                      <button className="btn btn-ghost btn-sm btn-icon" onClick={() => handleVoirInscription(insc)}>
                        <Eye size={14}/>
                      </button>
                    </td>
                  </tr>
                ))}
                {!inscriptions.length && (
                  <tr><td colSpan={7} style={{textAlign:'center',padding:32,color:'var(--gray-300)'}}>
                    Aucune inscription trouvée
                  </td></tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {selected && (
        <div className="modal-overlay" onClick={() => setSelected(null)}>
          <div className="modal" style={{maxWidth:600}} onClick={e => e.stopPropagation()}>
            {/* En-tête enrichi */}
            <div style={{
              padding:'20px 24px 16px',
              borderBottom:'1px solid var(--gray-100)',
              display:'flex', justifyContent:'space-between', alignItems:'flex-start', gap:12
            }}>
              <div style={{flex:1,minWidth:0}}>
                <div style={{fontSize:11,color:'var(--gray-400)',textTransform:'uppercase',letterSpacing:'.08em',marginBottom:4}}>
                  Dossier d'inscription
                </div>
                <div style={{fontWeight:800,fontSize:18,color:'var(--gray-900)',marginBottom:6,lineHeight:1.2}}>
                  {selected.etudiant_nom || `Étudiant #${selected.etudiant_id}`}
                </div>
                <div style={{display:'flex',flexWrap:'wrap',gap:8,alignItems:'center'}}>
                  {selected.numero_inscription && (
                    <span style={{
                      fontFamily:'monospace',fontSize:11,fontWeight:700,
                      color:'var(--blue)',background:'#ebf2ff',
                      padding:'2px 8px',borderRadius:99,letterSpacing:'.04em'
                    }}>
                      {selected.numero_inscription}
                    </span>
                  )}
                  {selected.formation_libelle && (
                    <span style={{fontSize:12,color:'var(--gray-500)'}}>
                      · {selected.formation_libelle}
                    </span>
                  )}
                  {selected.annee_universitaire && (
                    <span style={{fontSize:12,color:'var(--gray-400)'}}>
                      · {selected.annee_universitaire}
                    </span>
                  )}
                </div>
              </div>
              <div style={{display:'flex',alignItems:'center',gap:10,flexShrink:0}}>
                <span className={`badge badge-${BADGE[selected.statut_inscription]||'neutral'}`} style={{fontSize:12,padding:'4px 12px'}}>
                  {selected.statut_inscription === 'validee' ? '✓ Validée'
                    : selected.statut_inscription === 'refusee' ? '✗ Refusée'
                    : selected.statut_inscription === 'en_cours' ? '⏳ En cours'
                    : selected.statut_inscription === 'en_attente' ? '⏸ En attente'
                    : selected.statut_inscription}
                </span>
                <button className="btn btn-ghost btn-sm btn-icon" onClick={() => setSelected(null)}>✕</button>
              </div>
            </div>
            <div className="modal-body">

              {/* Infos workflow */}
              {selected.workflow && (
                <div style={{
                  background:'var(--gray-50)', border:'1px solid var(--gray-100)',
                  borderRadius:10, padding:'12px 16px', marginBottom:16
                }}>
                  <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:10}}>
                    <div>
                      <div style={{fontSize:12,color:'var(--gray-400)',textTransform:'uppercase',letterSpacing:'.05em',marginBottom:2}}>Workflow</div>
                      <div style={{fontWeight:700,fontSize:14}}>{selected.workflow.nom_workflow || 'Circuit inscription'}</div>
                    </div>
                    <div style={{textAlign:'right'}}>
                      <div style={{fontSize:12,color:'var(--gray-400)',marginBottom:2}}>Progression</div>
                      <div style={{fontWeight:700,fontSize:16,color:'var(--blue)'}}>{selected.workflow.progression ?? 0}%</div>
                    </div>
                  </div>
                  <div style={{background:'var(--gray-200)',borderRadius:99,height:6,overflow:'hidden'}}>
                    <div style={{
                      height:'100%', borderRadius:99,
                      width:`${selected.workflow.progression ?? 0}%`,
                      background: selected.workflow.progression >= 100 ? 'var(--success)' : 'var(--blue)',
                      transition:'width .4s ease'
                    }}/>
                  </div>
                  {selected.workflow.date_fin && (
                    <div style={{marginTop:8,fontSize:11,color:'var(--gray-400)'}}>
                      Terminé le {new Date(selected.workflow.date_fin).toLocaleDateString('fr-FR', {day:'2-digit',month:'long',year:'numeric'})}
                    </div>
                  )}
                </div>
              )}

              <div style={{fontSize:13,fontWeight:600,color:'var(--gray-600)',marginBottom:12}}>Étapes du circuit</div>
              <div style={{display:'flex',flexDirection:'column',gap:0}}>
                {(selected.workflow?.etapes && selected.workflow.etapes.length > 0) ? (
                  selected.workflow.etapes.map((etape, i) => {
                    const isLast = i === selected.workflow.etapes.length - 1
                    const couleur = etape.statut==='validee' ? 'var(--success)'
                      : etape.statut==='refusee' ? 'var(--danger)'
                      : etape.statut==='en_cours' ? 'var(--blue)'
                      : 'var(--gray-300)'
                    const bgCouleur = etape.statut==='validee' ? 'var(--success-bg)'
                      : etape.statut==='refusee' ? 'var(--danger-bg)'
                      : etape.statut==='en_cours' ? '#e8f0fe'
                      : 'var(--gray-100)'
                    return (
                    <div key={i} style={{display:'flex',gap:0,position:'relative'}}>
                      {/* Ligne verticale */}
                      <div style={{display:'flex',flexDirection:'column',alignItems:'center',width:40,flexShrink:0}}>
                        <div style={{
                          width:32, height:32, borderRadius:'50%', flexShrink:0,
                          background: bgCouleur, border:`2px solid ${couleur}`,
                          display:'flex', alignItems:'center', justifyContent:'center', zIndex:1
                        }}>
                          {etape.statut==='validee'
                            ? <CheckCircle size={14} color={couleur}/>
                            : etape.statut==='refusee'
                            ? <XCircle size={14} color={couleur}/>
                            : <Clock size={14} color={couleur}/>}
                        </div>
                        {!isLast && <div style={{width:2,flex:1,background:'var(--gray-200)',minHeight:20}}/>}
                      </div>
                      {/* Contenu */}
                      <div style={{
                        flex:1, marginLeft:8,
                        padding:'8px 12px 16px',
                        borderRadius:10,
                        background: etape.statut==='en_cours' ? '#f0f5ff' : 'transparent',
                        border: etape.statut==='en_cours' ? '1px solid #c7d8ff' : '1px solid transparent',
                        marginBottom: isLast ? 0 : 4
                      }}>
                        <div style={{display:'flex',justifyContent:'space-between',alignItems:'flex-start',flexWrap:'wrap',gap:4}}>
                          <div>
                            <div style={{fontSize:13,fontWeight:700,color:'var(--gray-800)'}}>
                              {etape.nom_etape || ETAPES_LABELS[etape.service] || etape.service}
                            </div>
                            <div style={{fontSize:11,color:'var(--gray-400)',marginTop:2}}>
                              Service : {ETAPES_LABELS[etape.service] || etape.service}
                              {etape.delai_max_heures && ` · délai max ${etape.delai_max_heures}h`}
                            </div>
                          </div>
                          <span className={`badge badge-${etape.statut==='validee'?'success':etape.statut==='refusee'?'danger':etape.statut==='en_cours'?'info':'neutral'}`}
                            style={{fontSize:11}}>
                            {etape.statut==='validee' ? 'Validée' : etape.statut==='refusee' ? 'Refusée' : etape.statut==='en_cours' ? 'En cours' : etape.statut}
                          </span>
                        </div>
                        {etape.observation && (
                          <div style={{marginTop:6,fontSize:12,color:'var(--gray-600)',background:'var(--gray-50)',borderRadius:6,padding:'4px 8px',borderLeft:'3px solid var(--gray-200)'}}>
                            {etape.observation}
                          </div>
                        )}
                        {etape.date_fin && (
                          <div style={{fontSize:11,color:'var(--gray-400)',marginTop:4}}>
                            ✓ {new Date(etape.date_fin).toLocaleDateString('fr-FR', {day:'2-digit',month:'short',year:'numeric',hour:'2-digit',minute:'2-digit'})}
                          </div>
                        )}
                      </div>
                      {(serviceConnecte && (etape.statut === 'en_cours' || etape.statut === 'en_attente') && etape.service === serviceConnecte) && (
                        <div style={{display:'flex',gap:6,marginTop:8}}>
                          <button className="btn btn-sm"
                            style={{background:'var(--success-bg)',color:'var(--success)',border:'1px solid var(--success)'}}
                            onClick={() => setEtapeAction({etape, action:'valider'})}
                            disabled={validating}>
                            <CheckCircle size={13}/> Valider
                          </button>
                          <button className="btn btn-sm"
                            style={{background:'var(--danger-bg)',color:'var(--danger)',border:'1px solid var(--danger)'}}
                            onClick={() => setEtapeAction({etape, action:'rejeter'})}
                            disabled={validating}>
                            <XCircle size={13}/> Rejeter
                          </button>
                        </div>
                      )}
                    </div>
                  )})
                ) : (
                  <div style={{textAlign:'center',padding:24,color:'var(--gray-400)',fontSize:13}}>Aucune étape disponible.</div>
                )}
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn btn-ghost" onClick={() => setSelected(null)}>Fermer</button>
            </div>
          </div>
        </div>
      )}

      {/* Modale de confirmation validation/rejet */}
      {etapeAction && (
        <div className="modal-overlay" onClick={() => { setEtapeAction(null); setObservation("") }}>
          <div className="modal" style={{maxWidth:400}} onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <span className="modal-title">
                {etapeAction.action === 'valider' ? 'Valider' : 'Rejeter'} l'étape
              </span>
              <button className="btn btn-ghost btn-sm btn-icon" onClick={() => { setEtapeAction(null); setObservation("") }}>✕</button>
            </div>
            <div className="modal-body">
              <div style={{marginBottom:12,fontSize:14,fontWeight:600}}>
                {etapeAction.etape.nom_etape || ETAPES_LABELS[etapeAction.etape.service] || etapeAction.etape.service}
              </div>
              <label style={{fontSize:13,fontWeight:500,marginBottom:6,display:'block'}}>
                Observation <span style={{color:'var(--danger)'}}>*</span>
              </label>
              <textarea
                value={observation}
                onChange={e => setObservation(e.target.value)}
                rows={3}
                style={{width:'100%',border:'1px solid var(--gray-200)',borderRadius:8,padding:8,resize:'vertical',fontSize:13,marginBottom:8}}
                placeholder={etapeAction.action === 'valider' ? 'Justifiez la validation...' : 'Expliquez la raison du rejet...'}
                autoFocus
              />
            </div>
            <div className="modal-footer" style={{display:'flex',justifyContent:'flex-end',gap:8}}>
              <button className="btn btn-ghost" onClick={() => { setEtapeAction(null); setObservation("") }}>Annuler</button>
              <button
                className={`btn btn-${etapeAction.action === 'valider' ? 'success' : 'danger'}`}
                disabled={validating || !observation.trim()}
                onClick={() => validerEtape(selected.id, etapeAction.etape.id, etapeAction.action, observation)}
              >
                {etapeAction.action === 'valider' ? <CheckCircle size={13}/> : <XCircle size={13}/>}
                {etapeAction.action === 'valider' ? ' Valider' : ' Rejeter'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
