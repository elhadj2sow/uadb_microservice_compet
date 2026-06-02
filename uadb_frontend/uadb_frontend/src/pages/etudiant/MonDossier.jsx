import { useState, useEffect } from 'react'
import api, { BASE } from '../../config/api'
import toast from 'react-hot-toast'
import { Upload, CheckCircle, XCircle, Clock, AlertTriangle, FileText, Trash2 } from 'lucide-react'

const TYPES_PIECES = [
  { value: 'bac',                 label: 'Baccalauréat',          obligatoire: true },
  { value: 'cni',                 label: "Carte Nationale d'Identité", obligatoire: true },
  { value: 'photo',               label: "Photo d'identité",      obligatoire: true },
  { value: 'acte_naissance',      label: 'Acte de naissance',     obligatoire: true },
]

const STATUT_ICON = {
  valide   : <CheckCircle size={15} color="var(--success)" />,
  rejete   : <XCircle    size={15} color="var(--danger)"  />,
  en_attente: <Clock     size={15} color="var(--warning)" />,
}
const STATUT_BADGE = { valide:'success', rejete:'danger', en_attente:'warning' }

const ANNEE_COURANTE = `${new Date().getFullYear()}-${new Date().getFullYear()+1}`

export default function MonDossier() {
  const [dossier,    setDossier]    = useState(null)
  const [formations, setFormations] = useState([])
  const [loading,    setLoading]    = useState(true)
  const [uploading,  setUploading]  = useState(null)
  const [showCreate, setShowCreate] = useState(false)
  const [annee,      setAnnee]      = useState(ANNEE_COURANTE)
  const [formCreate, setFormCreate] = useState({ formation: '', annee_universitaire: ANNEE_COURANTE })

  const chargerDossier = async (a) => {
    try {
      const r = await api.get(`${BASE.dossier}/mon-dossier/?annee=${a}`)
      setDossier(r.data)
      setAnnee(a)
    } catch {
      setShowCreate(true)
    }
  }

  useEffect(() => {
    chargerDossier(ANNEE_COURANTE).finally(() => setLoading(false))
    api.get(`${BASE.formation}/`).then(r => setFormations(r.data.results || []))
  }, [])

  const creerDossier = async () => {
    try {
      const r = await api.post(`${BASE.dossier}/`, formCreate)
      setDossier(r.data)
      setAnnee(r.data.annee_universitaire || formCreate.annee_universitaire)
      setShowCreate(false)
      toast.success('Dossier créé !')
    } catch (e) {
      const data = e.response?.data
      const msg = data?.detail
        || data?.non_field_errors?.[0]
        || (typeof data === 'object' ? Object.values(data).flat()[0] : null)
        || 'Erreur lors de la création.'
      toast.error(msg)
    }
  }

  const uploaderPiece = async (type_piece, file) => {
    setUploading(type_piece)
    const fd = new FormData()
    fd.append('type_piece', type_piece)
    fd.append('fichier', file)
    fd.append('est_obligatoire', 'true')
    try {
      await api.post(`${BASE.dossier}/${dossier.id}/pieces/`, fd, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      toast.success('Pièce déposée avec succès !')
      const r = await api.get(`${BASE.dossier}/mon-dossier/?annee=${annee}`)
      setDossier(r.data)
    } catch (e) {
      const msg = e.response?.data?.fichier?.[0]
        || e.response?.data?.error
        || e.response?.data?.detail
        || 'Erreur upload.'
      toast.error(msg)
    } finally { setUploading(null) }
  }

  const supprimerPiece = async pid => {
    try {
      await api.delete(`${BASE.piece}/${pid}/`)
      toast.success('Pièce supprimée.')
      const r = await api.get(`${BASE.dossier}/mon-dossier/?annee=${annee}`)
      setDossier(r.data)
    } catch (e) {
      const msg = e.response?.data?.error
        || e.response?.data?.detail
        || 'Impossible de supprimer cette pièce.'
      toast.error(msg)
      // Synchronise avec l'état réel du serveur (pièce peut-être déjà remplacée)
      try {
        const r = await api.get(`${BASE.dossier}/mon-dossier/?annee=${annee}`)
        setDossier(r.data)
      } catch {}
    }
  }

  if (loading) return (
    <div className="page">
      {[1,2,3].map(i => <div key={i} className="skeleton" style={{height:80,marginBottom:16,borderRadius:12}}/>)}
    </div>
  )

  if (showCreate) return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Mon Dossier</h1>
        <p className="page-subtitle">Créez votre dossier pour commencer votre inscription</p>
      </div>
      <div className="card" style={{maxWidth:500}}>
        <div className="card-header"><span className="card-title">Créer mon dossier</span></div>
        <div className="card-body">
          <div className="form-group">
            <label className="form-label">Formation souhaitée</label>
            <select className="form-control" value={formCreate.formation}
              onChange={e => setFormCreate(f=>({...f,formation:e.target.value}))}>
              <option value="">-- Choisir une formation --</option>
              {formations.map(f => <option key={f.id} value={f.id}>{f.code_formation} — {f.libelle}</option>)}
            </select>
          </div>
          <div className="form-group">
            <label className="form-label">Année universitaire</label>
            <input className="form-control" value={formCreate.annee_universitaire}
              onChange={e => setFormCreate(f=>({...f,annee_universitaire:e.target.value}))} />
          </div>
          <button className="btn btn-primary btn-block" onClick={creerDossier} disabled={!formCreate.formation}>
            Créer mon dossier
          </button>
        </div>
      </div>
    </div>
  )

  const pieces = dossier?.pieces || []
  const getPiece = type => pieces.find(p => p.type_piece === type)

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Mon Dossier</h1>
        <p className="page-subtitle">Gérez vos pièces justificatives</p>
      </div>

      {/* Score */}
      <div className="card fade-up" style={{marginBottom:20}}>
        <div className="card-padded">
          <div className="flex items-center justify-between mb-4">
            <div>
              <div style={{fontSize:15,fontWeight:700,color:'var(--gray-800)'}}>Score de complétude</div>
              <div style={{fontSize:13,color:'var(--gray-400)',marginTop:2}}>
                {dossier?.nb_pieces_validees || 0} / {TYPES_PIECES.length} pièces validées
              </div>
            </div>
            <div style={{fontSize:'2.2rem',fontWeight:800,color: dossier?.score_completude===100 ? 'var(--teal)' : 'var(--blue)'}}>
              {dossier?.score_completude}%
            </div>
          </div>
          <div className="progress">
            <div className={`progress-bar ${dossier?.score_completude===100?'teal':'blue'}`}
              style={{width:`${dossier?.score_completude}%`}}/>
          </div>
          {dossier?.etat_dossier === 'complet' && (
            <div className="alert alert-success" style={{marginTop:14,marginBottom:0}}>
              <CheckCircle size={16}/> Votre dossier est complet et prêt pour l'inscription !
            </div>
          )}
        </div>
      </div>

      {/* Liste des pièces */}
      <div className="card fade-up" style={{animationDelay:'100ms'}}>
        <div className="card-header">
          <span className="card-title">Pièces justificatives</span>
          <span className="badge badge-info">{TYPES_PIECES.length} pièces requises</span>
        </div>
        <div style={{padding:'8px 0'}}>
          {TYPES_PIECES.map((tp, i) => {
            const piece = getPiece(tp.value)
            return (
              <div key={tp.value} style={{
                display:'flex', alignItems:'center', gap:16,
                padding:'16px 24px',
                borderBottom: i < TYPES_PIECES.length-1 ? '1px solid var(--gray-100)' : 'none',
                transition:'background .12s',
              }}
              onMouseEnter={e=>e.currentTarget.style.background='var(--gray-50)'}
              onMouseLeave={e=>e.currentTarget.style.background='transparent'}
              >
                <div style={{
                  width:38, height:38, borderRadius:8, flexShrink:0,
                  background: piece?.statut_verification==='valide' ? 'var(--success-bg)' :
                               piece?.statut_verification==='rejete' ? 'var(--danger-bg)' :
                               piece ? 'var(--warning-bg)' : 'var(--gray-100)',
                  display:'flex', alignItems:'center', justifyContent:'center',
                }}>
                  {piece ? STATUT_ICON[piece.statut_verification] : <FileText size={15} color="var(--gray-400)"/>}
                </div>

                <div style={{flex:1}}>
                  <div style={{fontSize:14,fontWeight:600,color:'var(--gray-800)'}}>{tp.label}</div>
                  {piece && (
                    <div style={{fontSize:12,color:'var(--gray-400)',marginTop:2}}>
                      {piece.nom_fichier} • {piece.date_depot && new Date(piece.date_depot).toLocaleDateString('fr-FR')}
                    </div>
                  )}
                  {piece?.motif_rejet && (
                    <div style={{fontSize:12,color:'var(--danger)',marginTop:3}}>
                      Motif rejet : {piece.motif_rejet}
                    </div>
                  )}
                </div>

                {piece && (
                  <span className={`badge badge-${STATUT_BADGE[piece.statut_verification]}`}>
                    {piece.statut_verification}
                  </span>
                )}

                <div style={{display:'flex',gap:8}}>
                  {(!piece || piece.statut_verification === 'rejete') && (
                    <label className="btn btn-primary btn-sm" style={{cursor:'pointer',margin:0}}>
                      {uploading === tp.value ? <div className="spinner"/> : <><Upload size={13}/> Déposer</>}
                      <input type="file" accept=".pdf,.jpg,.jpeg,.png" style={{display:'none'}}
                        onChange={e => e.target.files[0] && uploaderPiece(tp.value, e.target.files[0])} />
                    </label>
                  )}
                  {piece && piece.statut_verification !== 'valide' && (
                    <button className="btn btn-ghost btn-sm btn-icon"
                      onClick={() => supprimerPiece(piece.id)}>
                      <Trash2 size={13}/>
                    </button>
                  )}
                  {piece?.url_telechargement && (
                    <a href={piece.url_telechargement} target="_blank" rel="noreferrer"
                      className="btn btn-ghost btn-sm">Voir</a>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
