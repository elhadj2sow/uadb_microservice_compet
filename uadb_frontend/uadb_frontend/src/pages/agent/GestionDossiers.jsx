import { useState, useEffect } from 'react'
import api, { BASE } from '../../config/api'
import toast from 'react-hot-toast'
import { Search, Eye, CheckCircle, XCircle, Filter, Edit3, ExternalLink } from 'lucide-react'

const ETATS = ['','en_cours','incomplet','complet','valide','rejete']
const BADGE = { en_cours:'info', incomplet:'warning', complet:'success', valide:'success', rejete:'danger' }
const PIECES_LABELS = {
  acte_naissance      : 'Acte de naissance',
  bac                 : 'Baccalauréat',
  certificat_medical  : 'Certificat médical',
  cni                 : 'Carte nationale d\'identité',
  diplome             : 'Diplôme',
  photo               : 'Photo d\'identité',
  relevé_notes        : 'Relevé de notes',
  releve_notes        : 'Relevé de notes',
  attestation         : 'Attestation',
  quittance           : 'Quittance de paiement',
}
const pieceLabel = (type) => PIECES_LABELS[type] || type?.replace(/_/g,' ').replace(/\b\w/g,c=>c.toUpperCase()) || type
const PIECE_ICON = { acte_naissance:'📄', bac:'🎓', certificat_medical:'🏥', cni:'🪪', photo:'🖼️', quittance:'🧾' }

export default function GestionDossiers() {
  const [dossiers, setDossiers] = useState([])
  const [total,    setTotal]    = useState(0)
  const [loading,  setLoading]  = useState(true)
  const [etat,     setEtat]     = useState('')
  const [search,   setSearch]   = useState('')
  const [selected, setSelected] = useState(null)
  const [action,   setAction]   = useState({ obs:'', etat:'' })
  // Modal rejet pièce
  const [rejetPiece,    setRejetPiece]    = useState(null)  // piece en cours de rejet
  const [motifRejet,    setMotifRejet]    = useState('')
  const [rejetLoading,  setRejetLoading]  = useState(false)

  const confirmerRejetPiece = async () => {
    if (!rejetPiece) return
    setRejetLoading(true)
    try {
      await api.patch(`${BASE.piece}/${rejetPiece.id}/verifier/`, {
        action: 'rejeter',
        motif_rejet: motifRejet,
      })
      toast.success('Pièce rejetée !')
      const r = await api.get(`${BASE.dossier}/${selected.id}/`)
      setSelected({ ...r.data, etudiant_nom: selected.etudiant_nom })
      setRejetPiece(null)
      setMotifRejet('')
    } catch { toast.error('Erreur lors du rejet de la pièce.') }
    finally { setRejetLoading(false) }
  }

  // Pour la validation d'étape d'inscription
  const [showValiderEtape, setShowValiderEtape] = useState(false)
  const [validerEtapeObs, setValiderEtapeObs] = useState('')
  const [validerEtapeId, setValiderEtapeId] = useState(null)
  // Fonction pour valider une étape d'inscription
  const validerEtapeInscription = async (id, observation = '') => {
    try {
      await api.patch(`/api/inscriptions/${id}/valider-etape/`, {
        action: 'valider',
        observation
      })
      toast.success('Étape validée !')
      setShowValiderEtape(false)
      setValiderEtapeObs('')
      setValiderEtapeId(null)
      charger(search, etat)
    } catch {
      toast.error("Erreur lors de la validation de l'étape.")
    }
  }

  const enrichirNomEtudiant = async (dossier) => {
    try {
      // Utilise l'endpoint etudiant, pas utilisateur
      const r = await api.get(`${BASE.auth}/etudiants/${dossier.etudiant_id}/`)
      const nom = r.data.prenom && r.data.nom
        ? `${r.data.prenom} ${r.data.nom}`
        : (r.data.username || r.data.email)
      return { ...dossier, etudiant_nom: nom }
    } catch {
      return { ...dossier, etudiant_nom: `ID ${dossier.etudiant_id}` }
    }
  }

  const charger = async (searchParam, etatParam) => {
    const s = searchParam !== undefined ? searchParam : search
    const e = etatParam   !== undefined ? etatParam   : etat
    setLoading(true)
    try {
      const r = await api.get(`${BASE.dossier}/liste/?etat=${e}&etudiant_id=${s}`)
      const dossiersData = r.data.results || []
      // Enrichir avec noms d'étudiants si la liste n'est pas trop grande
      const enrichis = dossiersData.length <= 100 
        ? await Promise.all(dossiersData.map(enrichirNomEtudiant))
        : dossiersData
      setDossiers(enrichis)
      setTotal(r.data.count || 0)
    } finally { setLoading(false) }
  }

  useEffect(() => { charger(search, etat) }, [etat, search])

  const validerDossier = async (id, etat_dossier, observation='') => {
    try {
      await api.patch(`${BASE.dossier}/${id}/`, { etat_dossier, observation })
      toast.success(`Dossier ${etat_dossier === 'valide' ? 'validé' : 'rejeté'} !`)
      setSelected(null)
      charger(search, etat)
    } catch { toast.error('Erreur lors de la mise à jour.') }
  }

  return (
    <div className="page">
      <div className="page-header flex items-center justify-between">
        <div>
          <h1 className="page-title">Gestion des Dossiers</h1>
          <p className="page-subtitle">{total} dossier(s)</p>
        </div>
      </div>

      {/* Filtres */}
      <div className="card fade-up" style={{marginBottom:20}}>
        <div className="card-padded" style={{display:'flex',gap:12,flexWrap:'wrap'}}>
          <div style={{flex:1,minWidth:200,position:'relative'}}>
            <Search size={15} style={{position:'absolute',left:12,top:'50%',transform:'translateY(-50%)',color:'var(--gray-300)'}}/>
            <input className="form-control" placeholder="ID étudiant..." style={{paddingLeft:36}}
              value={search} onChange={e => setSearch(e.target.value)} />
          </div>
          <select className="form-control" style={{width:'auto'}} value={etat} onChange={e=>setEtat(e.target.value)}>
            {ETATS.map(e => <option key={e} value={e}>{e || 'Tous les états'}</option>)}
          </select>
          <button className="btn btn-ghost" onClick={() => charger(search, etat)}><Filter size={15}/> Filtrer</button>
        </div>
      </div>

      {/* Table */}
      <div className="card fade-up" style={{animationDelay:'80ms'}}>
        {loading ? (
          <div className="card-body">
            {[1,2,3,4,5].map(i=><div key={i} className="skeleton" style={{height:50,marginBottom:10,borderRadius:8}}/>)}
          </div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead><tr>
                <th>ID</th><th>Étudiant</th><th>Formation</th>
                <th>Année</th><th>Score</th><th>État</th><th>Actions</th>
              </tr></thead>
              <tbody>
                {dossiers.map(d => (
                  <tr key={d.id}>
                    <td className="font-mono" style={{color:'var(--gray-400)'}}>{d.id}</td>
                    <td style={{fontWeight:600}}>{d.etudiant_nom || d.etudiant_id}</td>
                    <td>{d.formation_libelle || '—'}</td>
                    <td>{d.annee_universitaire}</td>
                    <td>
                      <div style={{display:'flex',alignItems:'center',gap:8}}>
                        <div className="progress" style={{width:60,height:6}}>
                          <div className={`progress-bar ${d.score_completude===100?'teal':d.score_completude>=50?'gold':'red'}`}
                            style={{width:`${d.score_completude}%`}}/>
                        </div>
                        <span style={{fontSize:12,fontWeight:600}}>{d.score_completude}%</span>
                      </div>
                    </td>
                    <td><span className={`badge badge-${BADGE[d.etat_dossier]||'neutral'}`}>{d.etat_dossier}</span></td>
                    <td>
                      <div style={{display:'flex',gap:6}}>
                        <button
                          className="btn btn-ghost btn-sm btn-icon"
                          onClick={async () => {
                            try {
                              const r = await api.get(`${BASE.dossier}/${d.id}/`);
                              setSelected({...r.data, etudiant_nom: d.etudiant_nom});
                            } catch {
                              toast.error("Impossible de charger le dossier.");
                            }
                          }}
                          title="Voir détail"
                        >
                          <Eye size={14}/>
                        </button>
                        {d.etat_dossier === 'complet' && (
                          <>
                            <button className="btn btn-sm" onClick={() => validerDossier(d.id,'valide')}
                              style={{background:'var(--success-bg)',color:'var(--success)',border:'1px solid',borderColor:'var(--success)'}}>
                              <CheckCircle size={13}/> Valider
                            </button>
                            <button className="btn btn-sm"
                              style={{background:'var(--danger-bg)',color:'var(--danger)',border:'1px solid',borderColor:'var(--danger)'}}
                              onClick={() => { setSelected(d); setAction({...action, etat:'rejete'}) }}>
                              <XCircle size={13}/> Rejeter
                            </button>
                          </>
                        )}
                        {/* Bouton Valider l'étape inscription : affiché seulement si inscription_id présent */}
                        {d.inscription_id && (
                          <button
                            className="btn btn-xs btn-info"
                            title="Valider l'étape d'inscription"
                            onClick={() => {
                              setValiderEtapeId(d.inscription_id)
                              setShowValiderEtape(true)
                              setValiderEtapeObs('')
                            }}
                          >
                            <Edit3 size={12}/> Valider étape
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
                      {/* Modal Valider Étape Inscription */}
                      {showValiderEtape && (
                        <div className="modal-overlay" onClick={()=>setShowValiderEtape(false)}>
                          <div className="modal" onClick={e=>e.stopPropagation()}>
                            <div className="modal-header">
                              <span className="modal-title">Valider l'étape d'inscription</span>
                              <button className="btn btn-ghost btn-sm btn-icon" onClick={()=>setShowValiderEtape(false)}>✕</button>
                            </div>
                            <div className="modal-body">
                              <div className="form-group">
                                <label className="form-label">Observation (optionnel)</label>
                                <textarea
                                  className="form-control"
                                  rows={3}
                                  value={validerEtapeObs}
                                  onChange={e=>setValiderEtapeObs(e.target.value)}
                                  placeholder="Observation sur la validation de l'étape..."
                                />
                              </div>
                            </div>
                            <div className="modal-footer">
                              <button className="btn btn-ghost" onClick={()=>setShowValiderEtape(false)}>Annuler</button>
                              <button
                                className="btn btn-primary"
                                onClick={()=>validerEtapeInscription(validerEtapeId, validerEtapeObs)}
                              >
                                <CheckCircle size={14}/> Valider l'étape
                              </button>
                            </div>
                          </div>
                        </div>
                      )}
                {!dossiers.length && (
                  <tr><td colSpan={7} style={{textAlign:'center',padding:32,color:'var(--gray-300)'}}>
                    Aucun dossier trouvé
                  </td></tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Modal détail */}
      {selected && (
        <div className="modal-overlay" onClick={()=>setSelected(null)}>
          <div className="modal" style={{maxWidth:620}} onClick={e=>e.stopPropagation()}>

            {/* En-tête enrichi */}
            <div style={{
              padding:'20px 24px 16px',
              borderBottom:'1px solid var(--gray-100)',
              display:'flex', justifyContent:'space-between', alignItems:'flex-start', gap:12
            }}>
              <div style={{flex:1,minWidth:0}}>
                <div style={{fontSize:11,color:'var(--gray-400)',textTransform:'uppercase',letterSpacing:'.08em',marginBottom:4}}>
                  Dossier académique
                </div>
                <div style={{fontWeight:800,fontSize:18,color:'var(--gray-900)',marginBottom:6,lineHeight:1.2}}>
                  {selected.etudiant_nom || `Étudiant #${selected.etudiant_id}`}
                </div>
                <div style={{display:'flex',flexWrap:'wrap',gap:8,alignItems:'center'}}>
                  {selected.formation_libelle && (
                    <span style={{fontSize:12,color:'var(--gray-600)',fontWeight:500}}>
                      {selected.formation_libelle}
                    </span>
                  )}
                  {selected.annee_universitaire && (
                    <span style={{fontSize:12,color:'var(--gray-400)'}}>· {selected.annee_universitaire}</span>
                  )}
                </div>
              </div>
              <div style={{display:'flex',alignItems:'center',gap:10,flexShrink:0}}>
                <span className={`badge badge-${BADGE[selected.etat_dossier]||'neutral'}`} style={{fontSize:12,padding:'4px 12px'}}>
                  {selected.etat_dossier === 'valide' ? '✓ Validé'
                    : selected.etat_dossier === 'rejete' ? '✗ Rejeté'
                    : selected.etat_dossier === 'complet' ? '● Complet'
                    : selected.etat_dossier === 'incomplet' ? '◐ Incomplet'
                    : selected.etat_dossier}
                </span>
                <button className="btn btn-ghost btn-sm btn-icon" onClick={()=>setSelected(null)}>✕</button>
              </div>
            </div>

            <div className="modal-body">
              {/* Barre de complétion */}
              <div style={{
                background:'var(--gray-50)', border:'1px solid var(--gray-100)',
                borderRadius:10, padding:'12px 16px', marginBottom:20
              }}>
                <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:8}}>
                  <span style={{fontSize:12,color:'var(--gray-500)',fontWeight:500}}>Complétion du dossier</span>
                  <span style={{fontWeight:700,fontSize:15,color: selected.score_completude===100 ? 'var(--success)' : 'var(--blue)'}}>
                    {selected.score_completude}%
                  </span>
                </div>
                <div style={{background:'var(--gray-200)',borderRadius:99,height:7,overflow:'hidden'}}>
                  <div style={{
                    height:'100%', borderRadius:99,
                    width:`${selected.score_completude}%`,
                    background: selected.score_completude===100 ? 'var(--success)' : 'var(--blue)',
                    transition:'width .4s ease'
                  }}/>
                </div>
              </div>

              {/* Liste des pièces justificatives */}
              <div style={{marginBottom:16}}>
                <div style={{fontSize:13,fontWeight:700,color:'var(--gray-700)',marginBottom:12}}>Pièces justificatives</div>
                {(selected.pieces && selected.pieces.length > 0) ? (
                  <div style={{display:'flex',flexDirection:'column',gap:8}}>
                    {selected.pieces.map(piece => (
                      <div key={piece.id} style={{
                        display:'flex', alignItems:'center', gap:12,
                        padding:'10px 14px', borderRadius:10,
                        background: piece.statut_verification==='valide' ? '#f0fdf4'
                          : piece.statut_verification==='rejete' ? '#fff5f5' : 'var(--gray-50)',
                        border: `1px solid ${
                          piece.statut_verification==='valide' ? '#bbf7d0'
                          : piece.statut_verification==='rejete' ? '#fecaca' : 'var(--gray-150,#eee)'}`
                      }}>
                        <span style={{fontSize:18,flexShrink:0}}>{PIECE_ICON[piece.type_piece] || '📎'}</span>
                        <div style={{flex:1,minWidth:0}}>
                          <div style={{fontWeight:600,fontSize:13,color:'var(--gray-800)'}}>
                            {pieceLabel(piece.type_piece)}
                          </div>
                          <div style={{fontSize:11,color:'var(--gray-400)',marginTop:1}}>
                            {piece.nom_fichier || 'Fichier d\'une pièce'}
                          </div>
                        </div>
                        <span className={`badge badge-${
                          piece.statut_verification==='valide' ? 'success'
                          : piece.statut_verification==='rejete' ? 'danger' : 'warning'}`}
                          style={{fontSize:11,flexShrink:0}}>
                          {piece.statut_verification==='valide' ? '✓ Validée'
                            : piece.statut_verification==='rejete' ? '✗ Rejetée' : 'En attente'}
                        </span>
                        <div style={{display:'flex',gap:4,flexShrink:0}}>
                          {/* Bouton Voir le fichier */}
                          <button
                            className="btn btn-sm btn-icon"
                            title="Ouvrir le fichier"
                            style={{background:'var(--info-bg,#e0f2fe)',color:'var(--blue)',border:'1px solid var(--blue)',padding:'4px 8px',borderRadius:6,display:'flex',alignItems:'center',gap:4,fontSize:12}}
                            onClick={async () => {
                              try {
                                const r = await api.get(`${BASE.piece}/${piece.id}/telecharger/`)
                                const url = r.data.url || r.data.download_url || piece.fichier
                                window.open(url, '_blank', 'noopener')
                              } catch {
                                if (piece.fichier) window.open(piece.fichier, '_blank', 'noopener')
                                else toast.error('Impossible d\'ouvrir le fichier')
                              }
                            }}
                          >
                            <ExternalLink size={12}/> Voir
                          </button>
                          {piece.statut_verification !== 'valide' && (
                            <button
                              className="btn btn-sm"
                              style={{background:'var(--success-bg)',color:'var(--success)',border:'1px solid var(--success)',padding:'3px 8px'}}
                              onClick={async()=>{
                                try {
                                  await api.patch(`${BASE.piece}/${piece.id}/verifier/`, { action: 'valider' });
                                  toast.success('Pièce validée !');
                                  const r = await api.get(`${BASE.dossier}/${selected.id}/`);
                                  setSelected({...r.data, etudiant_nom: selected.etudiant_nom});
                                } catch { toast.error('Erreur validation pièce'); }
                              }}>
                              <CheckCircle size={12}/>
                            </button>
                          )}
                          {piece.statut_verification !== 'rejete' && (
                            <button
                              className="btn btn-sm"
                              title="Rejeter cette pièce"
                              style={{background:'var(--danger-bg)',color:'var(--danger)',border:'1px solid var(--danger)',padding:'3px 8px'}}
                              onClick={() => { setRejetPiece(piece); setMotifRejet('') }}>
                              <XCircle size={12}/>
                            </button>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div style={{textAlign:'center',padding:24,color:'var(--gray-400)',fontSize:13}}>Aucune pièce déposée.</div>
                )}
              </div>

              {action.etat === 'rejete' && (
                <div className="form-group">
                  <label className="form-label">Motif du rejet</label>
                  <textarea className="form-control" rows={3}
                    value={action.obs} onChange={e=>setAction(a=>({...a,obs:e.target.value}))}
                    placeholder="Expliquez pourquoi le dossier est rejeté..."/>
                </div>
              )}
            </div>
            <div className="modal-footer">
              <button className="btn btn-ghost" onClick={()=>{setSelected(null);setAction({obs:'',etat:''})}}>Fermer</button>
              {selected.etat_dossier === 'complet' && action.etat !== 'rejete' && (
                <button
                  className="btn btn-primary"
                  onClick={() => validerDossier(selected.id, 'valide')}
                >
                  <CheckCircle size={14}/> Valider le dossier
                </button>
              )}
              {action.etat === 'rejete' && (
                <button className="btn btn-danger" onClick={()=>validerDossier(selected.id,'rejete',action.obs)}>
                  <XCircle size={14}/> Confirmer le rejet
                </button>
              )}
            </div>
          </div>
        </div>
      )}
      {/* Modal rejet pièce — motif */}
      {rejetPiece && (
        <div className="modal-overlay" onClick={() => { setRejetPiece(null); setMotifRejet('') }}>
          <div className="modal" style={{maxWidth:420}} onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <span className="modal-title">Rejeter la pièce</span>
              <button className="btn btn-ghost btn-sm btn-icon" onClick={() => { setRejetPiece(null); setMotifRejet('') }}>✕</button>
            </div>
            <div className="modal-body">
              <p style={{fontSize:13,color:'var(--gray-600)',marginBottom:14}}>
                Vous allez rejeter : <strong>{pieceLabel(rejetPiece.type_piece)}</strong>
              </p>
              <div className="form-group">
                <label className="form-label">Motif du rejet <span style={{color:'var(--danger)'}}>*</span></label>
                <textarea
                  className="form-control"
                  rows={3}
                  value={motifRejet}
                  onChange={e => setMotifRejet(e.target.value)}
                  placeholder="Ex : Document illisible, photo non conforme..."
                  autoFocus
                />
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn btn-ghost" onClick={() => { setRejetPiece(null); setMotifRejet('') }}>Annuler</button>
              <button
                className="btn btn-danger"
                disabled={!motifRejet.trim() || rejetLoading}
                onClick={confirmerRejetPiece}
              >
                <XCircle size={14}/> {rejetLoading ? 'En cours...' : 'Confirmer le rejet'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
