import { useState, useEffect, useCallback } from 'react'
import api, { BASE } from '../../config/api'
import toast from 'react-hot-toast'
import { CheckCircle, Clock, XCircle, AlertCircle, Send, CreditCard, ArrowRight, Upload, FileText, Trash2 } from 'lucide-react'

const TYPES_PIECES = [
  { value: 'bac',            label: 'Baccalauréat',               obligatoire: true },
  { value: 'cni',            label: "Carte Nationale d'Identité", obligatoire: true },
  { value: 'photo',          label: "Photo d'identité",           obligatoire: true },
  { value: 'acte_naissance', label: 'Acte de naissance',          obligatoire: true },
]
const STATUT_ICON = {
  valide    : <CheckCircle size={14} color="var(--success)" />,
  rejete    : <XCircle    size={14} color="var(--danger)"  />,
  en_attente: <Clock      size={14} color="var(--warning)" />,
}
const STATUT_BADGE = { valide: 'success', rejete: 'danger', en_attente: 'warning' }

const ETAPES = [
  { key: 'scolarite',    label: 'Scolarité',    desc: 'Vérification administrative' },
  { key: 'comptabilite', label: 'Comptabilité', desc: 'Vérification du paiement' },
  { key: 'medical',      label: 'Médical',      desc: 'Certificat de santé' },
  { key: 'bibliotheque', label: 'Bibliothèque', desc: 'Quitus bibliothèque' },
]

const STATUT_COLOR = {
  validee: 'success', en_cours: 'info',
  en_attente: 'neutral', refusee: 'danger',
}

const NIVEAUX_ORDRE = ['L1', 'L2', 'L3', 'M1', 'M2', 'Doctorat']
const niveauSuivant = (niveau) => {
  const idx = NIVEAUX_ORDRE.indexOf(niveau)
  return idx >= 0 && idx < NIVEAUX_ORDRE.length - 1 ? NIVEAUX_ORDRE[idx + 1] : null
}

// ─── Carte réutilisable pour afficher le statut d'une inscription ─────────────
function InscriptionCard({ inscription, paiement, paying, onPayer, titre, accent }) {
  return (
    <div className="card fade-up" style={{ marginBottom: 20, border: accent ? '2px solid #c7d8ff' : undefined }}>
      <div className="card-padded">
        <div className="flex items-center justify-between mb-4">
          <div>
            <div style={{ fontSize: 15, fontWeight: 700 }}>{titre}</div>
            <div style={{ fontSize: 12, color: 'var(--gray-400)', marginTop: 2, fontFamily: 'monospace' }}>
              {inscription.numero_inscription || inscription.numero_provisoire || '—'}
            </div>
            {inscription.type_inscription && (
              <span style={{
                fontSize: 11, fontWeight: 600, display: 'inline-block', marginTop: 4,
                padding: '1px 7px', borderRadius: 99,
                color: inscription.type_inscription === 'reinscription' ? 'var(--warning)' : 'var(--blue)',
                background: inscription.type_inscription === 'reinscription' ? '#fff7ed' : '#ebf2ff',
              }}>
                {inscription.type_inscription === 'reinscription' ? '🔄 Réinscription' : '🎓 Première inscription'}
              </span>
            )}
          </div>
          <span className={`badge badge-${STATUT_COLOR[inscription.statut_inscription] || 'neutral'}`}
            style={{ fontSize: 13, padding: '5px 14px' }}>
            {inscription.statut_inscription}
          </span>
        </div>

        <div className="steps" style={{ marginTop: 24 }}>
          {ETAPES.map((etape, i) => {
            const etapes = inscription.workflow?.etapes || []
            const e = etapes.find(x => x.service === etape.key) || etapes[i]
            const done   = e?.statut === 'validee'
            const rejete = e?.statut === 'rejetee'
            return (
              <div key={etape.key} className={`step ${done ? 'done' : rejete ? 'rejected' : ''}`}>
                <div className="step-circle"
                  style={rejete ? { background: 'var(--danger)', color: 'white', borderColor: 'var(--danger)' } : {}}>
                  {done ? <CheckCircle size={14} /> : rejete ? <XCircle size={14} /> : i + 1}
                </div>
                <div className="step-label">{etape.label}</div>
              </div>
            )
          })}
        </div>

        <div style={{ marginTop: 24, display: 'flex', flexDirection: 'column', gap: 10 }}>
          {ETAPES.map((etape, i) => {
            const etapes = inscription.workflow?.etapes || []
            const e = etapes.find(x => x.service === etape.key) || etapes[i]
            const showPaiementBtn =
              etape.key === 'comptabilite' &&
              (e?.statut === 'en_cours' || e?.statut === 'en_attente') &&
              (!paiement?.statut_paiement || paiement.statut_paiement !== 'confirme')

            let iconEl
            if (e?.statut === 'validee') iconEl = <CheckCircle size={14} color="var(--success)" />
            else if (e?.statut === 'rejetee') iconEl = <XCircle size={14} color="var(--danger)" />
            else if (e?.statut) iconEl = <Clock size={14} color="var(--warning)" />
            else iconEl = <Clock size={14} color="var(--gray-300)" />

            let bgColor = 'var(--gray-100)'
            if (e?.statut === 'validee') bgColor = 'var(--success-bg)'
            else if (e?.statut === 'rejetee') bgColor = 'var(--danger-bg)'
            else if (e?.statut) bgColor = 'var(--warning-bg)'

            return (
              <div key={etape.key} style={{
                display: 'flex', alignItems: 'center', gap: 14,
                padding: '12px 16px', borderRadius: 10,
                background: 'var(--gray-50)', border: '1px solid var(--gray-100)',
              }}>
                <div style={{
                  width: 32, height: 32, borderRadius: '50%', flexShrink: 0,
                  background: bgColor, display: 'flex', alignItems: 'center', justifyContent: 'center',
                }}>
                  {iconEl}
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--gray-700)' }}>{etape.label}</div>
                  <div style={{ fontSize: 12, color: 'var(--gray-400)' }}>{etape.desc}</div>
                </div>
                {e?.statut && (
                  <span className={`badge badge-${e.statut === 'validee' ? 'success' : e.statut === 'rejetee' ? 'danger' : 'warning'}`}>
                    {e.statut}
                  </span>
                )}
                {e?.date_validation && (
                  <span style={{ fontSize: 11, color: 'var(--gray-400)' }}>
                    {new Date(e.date_validation).toLocaleDateString('fr-FR')}
                  </span>
                )}
                {showPaiementBtn && (
                  <button className="btn btn-primary" style={{ marginLeft: 8 }} onClick={onPayer} disabled={paying}>
                    {paying ? <div className="spinner" /> : <><CreditCard size={15} /> Payer les frais</>}
                  </button>
                )}
                {etape.key === 'comptabilite' && paiement && (
                  <span style={{ marginLeft: 8, fontSize: 12 }}>
                    Paiement : <b>{paiement.statut_paiement}</b>
                  </span>
                )}
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

// ─── Page principale ──────────────────────────────────────────────────────────
export default function MonInscription() {
  const [inscription,      setInscription]      = useState(null)  // année courante
  const [inscProchaine,    setInscProchaine]    = useState(null)  // réinscription année prochaine
  const [dossier,          setDossier]          = useState(null)
  const [loading,          setLoading]          = useState(true)
  const [submitting,       setSubmitting]       = useState(false)
  const [paiement,         setPaiement]         = useState(null)
  const [paiementProchain, setPaiementProchain] = useState(null)
  const [paying,           setPaying]           = useState(false)
  const [formations,       setFormations]       = useState([])
  const [formationChoisie, setFormationChoisie] = useState(null)
  const [niveauCourant,    setNiveauCourant]    = useState(null)
  const [eligibilite,      setEligibilite]      = useState(null)
  const [checkingElig,     setCheckingElig]     = useState(false)
  const [uploadingPiece,   setUploadingPiece]   = useState(null)

  const now            = new Date()
  // Année académique en cours (ex: 2026-2027)
  const anneeCourante  = `${now.getFullYear()}-${now.getFullYear() + 1}`
  // Année cible pour la réinscription (ex: 2027-2028)
  const anneeProchaine = `${now.getFullYear() + 1}-${now.getFullYear() + 2}`

  const rafraichirDossier = useCallback(async () => {
    try {
      const r = await api.get(`${BASE.dossier}/mon-dossier/?annee=${anneeCourante}`)
      setDossier(r.data)
    } catch { /* silencieux */ }
  }, [anneeCourante])

  const uploaderPiece = useCallback(async (type_piece, file) => {
    if (!dossier?.id) return toast.error('Aucun dossier trouvé.')
    setUploadingPiece(type_piece)
    const fd = new FormData()
    fd.append('type_piece', type_piece)
    fd.append('fichier', file)
    fd.append('est_obligatoire', 'true')
    try {
      await api.post(`${BASE.dossier}/${dossier.id}/pieces/`, fd, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      toast.success('Pièce déposée !')
      rafraichirDossier()
    } catch (e) {
      toast.error(e.response?.data?.fichier?.[0] || "Erreur lors de l'upload.")
    } finally { setUploadingPiece(null) }
  }, [dossier, rafraichirDossier])

  const supprimerPiece = useCallback(async (pid) => {
    try {
      await api.delete(`${BASE.piece}/${pid}/`)
      toast.success('Pièce supprimée.')
      rafraichirDossier()
    } catch { toast.error('Impossible de supprimer cette pièce.') }
  }, [rafraichirDossier])

  const verifierEligibilite = useCallback(async () => {
    setCheckingElig(true)
    setEligibilite(null)
    try {
      const r = await api.get(`${BASE.inscription}/reinscription/eligibilite/?annee=${anneeProchaine}`)
      setEligibilite(r.data)
      if (r.data.formation_id) {
        setFormationChoisie(prev => prev || r.data.formation_id)
      }
    } catch (e) {
      setEligibilite({ eligible: false, message: e.response?.data?.error || 'Erreur de vérification.' })
    } finally { setCheckingElig(false) }
  }, [anneeProchaine])

  useEffect(() => {
    api.get('/api/formations/').then(r => {
      const data = r?.data?.results || r?.data || []
      setFormations(Array.isArray(data) ? data : [])
    }).catch(() => {})

    Promise.allSettled([
      api.get(`${BASE.inscription}/mon-inscription/?annee=${anneeCourante}`),
      api.get(`${BASE.dossier}/mon-dossier/?annee=${anneeCourante}`),
      api.get(`${BASE.inscription}/mon-inscription/?annee=${anneeProchaine}`),
    ]).then(([i, d, iProch]) => {
      if (i.status === 'fulfilled') {
        const insc = i.value.data
        setInscription(insc)
        if (insc?.id) {
          api.get(`${BASE.inscription}/${insc.id}/paiement/`)
            .then(r => setPaiement(r.data)).catch(() => setPaiement(null))
        }
        // Inscription courante validée → déclencher vérif d'éligibilité auto
        if (insc?.statut_inscription === 'validee') {
          verifierEligibilite()
        }
      }
      if (d.status === 'fulfilled') {
        const dos = d.value.data
        setDossier(dos)
        if (dos?.formation_detail?.niveau) {
          setNiveauCourant(dos.formation_detail.niveau)
        } else if (dos?.formation) {
          api.get(`/api/formations/${dos.formation}/`).then(fr => {
            setNiveauCourant(fr.data?.niveau || null)
          }).catch(() => {})
        }
      }
      if (iProch.status === 'fulfilled' && iProch.value.data?.id) {
        const insc = iProch.value.data
        setInscProchaine(insc)
        if (insc?.id) {
          api.get(`${BASE.inscription}/${insc.id}/paiement/`)
            .then(r => setPaiementProchain(r.data)).catch(() => setPaiementProchain(null))
        }
      }
    }).finally(() => setLoading(false))
  }, [verifierEligibilite, anneeCourante, anneeProchaine])

  const handlePaiement = async (insc) => {
    if (!insc) return
    setPaying(true)
    const payWindow = window.open('', '_blank')
    try {
      const r = await api.post(`${BASE.inscription}/${insc.id}/paiement/paytech/initier/`)
      const url = r.data?.payment_url || r.data?.url || r.data?.redirect_url || r.data?.redirectUrl
      if (url) {
        payWindow.location = url
        toast.success('Redirection vers la plateforme de paiement...')
      } else {
        payWindow.close()
        toast.error("Impossible d'obtenir l'URL de paiement.")
      }
    } catch (e) {
      payWindow.close()
      toast.error(e.response?.data?.detail || 'Erreur lors de la génération du paiement.')
    } finally { setPaying(false) }
  }

  const soumettre = async () => {
    setSubmitting(true)
    try {
      if (inscription?.statut_inscription === 'validee') {
        // ── RÉINSCRIPTION pour l'année prochaine ──────────────────────────
        const body = { annee_universitaire: anneeProchaine }
        if (formationChoisie) body.formation_id = formationChoisie
        const r = await api.post(`${BASE.inscription}/reinscription/`, body)
        // Recharger depuis le serveur pour avoir le workflow complet
        const rFull = await api.get(`${BASE.inscription}/mon-inscription/?annee=${anneeProchaine}`)
        const nouvelleInsc = rFull.data
        setInscProchaine(nouvelleInsc)
        if (nouvelleInsc?.id) {
          api.get(`${BASE.inscription}/${nouvelleInsc.id}/paiement/`)
            .then(p => setPaiementProchain(p.data)).catch(() => setPaiementProchain(null))
        }
        const msg = r.data.avertissement || r.data.message_condition
        toast.success(
          msg ? `Réinscription soumise ! ${msg}` : 'Réinscription soumise ! Le circuit démarre automatiquement.',
          { duration: 6000 }
        )
      } else {
        // ── PREMIÈRE INSCRIPTION pour l'année courante ─────────────────────
        if (!dossier) {
          toast.error('Créez votre dossier avant de vous inscrire.')
          setSubmitting(false)
          return
        }
        if (dossier.score_completude < 100) {
          toast.error('Votre dossier doit être complet avant de soumettre.')
          setSubmitting(false)
          return
        }
        const r = await api.post(`${BASE.inscription}/`, {
          formation_id:        formationChoisie || dossier.formation,
          annee_universitaire: anneeCourante,
          dossier_id:          dossier.id,
          type_inscription:    'premiere',
        })
        setInscription(r.data)
        toast.success('Préinscription soumise ! Le workflow démarre automatiquement.')
      }
    } catch (e) {
      toast.error(e.response?.data?.error || e.response?.data?.detail || 'Erreur lors de la soumission.')
    } finally { setSubmitting(false) }
  }

  if (loading) return (
    <div className="page">
      {[1, 2].map(i => <div key={i} className="skeleton" style={{ height: 100, marginBottom: 16, borderRadius: 12 }} />)}
    </div>
  )

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Mon Inscription</h1>
        <p className="page-subtitle">Suivez votre processus d'inscription administrative</p>
      </div>

      {/* ── SECTION 1 : Formulaire première inscription ── */}
      {!inscription && (
        <div className="card fade-up" style={{ maxWidth: 580, marginBottom: 20 }}>
          <div className="card-header">
            <span className="card-title">🎓 Première inscription — {anneeCourante}</span>
          </div>
          <div className="card-body">
            {!dossier ? (
              <div className="alert alert-warning">
                <AlertCircle size={16} /> Créez d'abord votre dossier avant de vous inscrire.
              </div>
            ) : dossier.score_completude < 100 ? (
              <div className="alert alert-warning">
                <AlertCircle size={16} /> Dossier complet à {dossier.score_completude}%. Déposez toutes les pièces avant de soumettre.
              </div>
            ) : (
              <div className="alert alert-success">
                <CheckCircle size={16} /> Dossier complet. Vous pouvez soumettre votre inscription.
              </div>
            )}
            <button
              className="btn btn-primary btn-block"
              style={{ marginTop: 16 }}
              onClick={soumettre}
              disabled={submitting || !dossier || dossier.score_completude < 100}
            >
              {submitting ? <div className="spinner" /> : <><Send size={15} /> Soumettre ma préinscription</>}
            </button>
          </div>
        </div>
      )}

      {/* ── SECTION 2 : Statut inscription année courante ── */}
      {inscription && (
        <InscriptionCard
          inscription={inscription}
          paiement={paiement}
          paying={paying}
          onPayer={() => handlePaiement(inscription)}
          titre={`Statut inscription — ${anneeCourante}`}
        />
      )}

      {/* ── SECTION 3 : Formulaire réinscription (visible si inscription courante = validée) ── */}
      {inscription?.statut_inscription === 'validee' && !inscProchaine && (
        <div className="card fade-up" style={{ maxWidth: 580, marginBottom: 20, border: '2px solid #c7d8ff' }}>
          <div className="card-header" style={{ background: 'linear-gradient(135deg,#ebf2ff,#f0f5ff)' }}>
            <div>
              <span className="card-title" style={{ color: 'var(--blue)' }}>🔄 Réinscription — {anneeProchaine}</span>
              <div style={{ fontSize: 12, color: 'var(--gray-400)', marginTop: 2 }}>
                Votre inscription {anneeCourante} est validée — vous pouvez vous réinscrire pour l'année prochaine
              </div>
            </div>
          </div>
          <div className="card-body">
            {/* Résultat éligibilité */}
            {checkingElig && (
              <div className="alert alert-info" style={{ fontSize: 13, display: 'flex', alignItems: 'center', gap: 8 }}>
                <div className="spinner" style={{ width: 14, height: 14 }} /> Vérification de votre éligibilité…
              </div>
            )}
            {!checkingElig && eligibilite && (
              <div className={`alert alert-${
                !eligibilite.eligible ? 'danger' :
                eligibilite.avertissement ? 'warning' : 'success'
              }`} style={{ fontSize: 13, display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8 }}>
                <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  {!eligibilite.eligible ? <XCircle size={15} /> :
                   eligibilite.avertissement ? <AlertCircle size={15} /> :
                   <CheckCircle size={15} />}
                  <span>{eligibilite.avertissement || eligibilite.message}</span>
                  {eligibilite.eligible && eligibilite.frais_estimatifs && (
                    <span style={{ marginLeft: 8, opacity: .75 }}>
                      — Frais : <strong>{eligibilite.frais_estimatifs.toLocaleString('fr-FR')} FCFA</strong>
                    </span>
                  )}
                </span>
                {!eligibilite.eligible && (
                  <button className="btn btn-ghost" style={{ padding: '2px 10px', fontSize: 12 }} onClick={verifierEligibilite}>
                    Réessayer
                  </button>
                )}
              </div>
            )}
            {!checkingElig && !eligibilite && (
              <button className="btn btn-ghost" style={{ marginBottom: 12 }} onClick={verifierEligibilite}>
                Vérifier mon éligibilité
              </button>
            )}

            {/* ── Pièces justificatives ── */}
            <div style={{ marginTop: 18, marginBottom: 6 }}>
              <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--gray-700)', marginBottom: 10, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span>📎 Pièces justificatives</span>
                {dossier && (
                  <span style={{ fontSize: 12, fontWeight: 600, color: dossier.score_completude === 100 ? 'var(--success)' : 'var(--warning)' }}>
                    {dossier.score_completude}% complet
                  </span>
                )}
              </div>
              {!dossier ? (
                <div className="alert alert-warning" style={{ fontSize: 12 }}>
                  <AlertCircle size={14} /> Aucun dossier trouvé. Créez d'abord votre dossier dans l'onglet "Mon Dossier".
                </div>
              ) : (
                <div style={{ border: '1px solid var(--gray-100)', borderRadius: 10, overflow: 'hidden' }}>
                  {TYPES_PIECES.map((tp, i) => {
                    const pieces = dossier?.pieces || []
                    const piece  = pieces.find(p => p.type_piece === tp.value)
                    return (
                      <div key={tp.value} style={{
                        display: 'flex', alignItems: 'center', gap: 12,
                        padding: '12px 16px',
                        borderBottom: i < TYPES_PIECES.length - 1 ? '1px solid var(--gray-100)' : 'none',
                        background: piece?.statut_verification === 'valide' ? '#f0fdf4' : 'white',
                      }}>
                        <div style={{
                          width: 32, height: 32, borderRadius: 8, flexShrink: 0,
                          background: piece?.statut_verification === 'valide' ? 'var(--success-bg)' :
                                       piece?.statut_verification === 'rejete' ? 'var(--danger-bg)' :
                                       piece ? 'var(--warning-bg)' : 'var(--gray-100)',
                          display: 'flex', alignItems: 'center', justifyContent: 'center',
                        }}>
                          {piece ? (STATUT_ICON[piece.statut_verification] || <FileText size={14} color="var(--gray-400)" />) : <FileText size={14} color="var(--gray-400)" />}
                        </div>
                        <div style={{ flex: 1, minWidth: 0 }}>
                          <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--gray-800)' }}>
                            {tp.label} {tp.obligatoire && <span style={{ color: 'var(--danger)', fontSize: 11 }}>*</span>}
                          </div>
                          {piece && (
                            <div style={{ fontSize: 11, color: 'var(--gray-400)', marginTop: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                              {piece.nom_fichier}
                            </div>
                          )}
                          {piece?.motif_rejet && (
                            <div style={{ fontSize: 11, color: 'var(--danger)', marginTop: 2 }}>Rejet : {piece.motif_rejet}</div>
                          )}
                        </div>
                        {piece && (
                          <span className={`badge badge-${STATUT_BADGE[piece.statut_verification] || 'neutral'}`} style={{ fontSize: 11 }}>
                            {piece.statut_verification}
                          </span>
                        )}
                        <div style={{ display: 'flex', gap: 6, flexShrink: 0 }}>
                          {(!piece || piece.statut_verification === 'rejete') && (
                            <label className="btn btn-primary btn-sm" style={{ cursor: 'pointer', margin: 0, fontSize: 12 }}>
                              {uploadingPiece === tp.value ? <div className="spinner" style={{ width: 12, height: 12 }} /> : <><Upload size={12} /> Déposer</>}
                              <input type="file" accept=".pdf,.jpg,.jpeg,.png" style={{ display: 'none' }}
                                onChange={e => e.target.files[0] && uploaderPiece(tp.value, e.target.files[0])} />
                            </label>
                          )}
                          {piece && piece.statut_verification !== 'valide' && (
                            <button className="btn btn-ghost btn-sm btn-icon" onClick={() => supprimerPiece(piece.id)}>
                              <Trash2 size={12} />
                            </button>
                          )}
                          {piece?.url_telechargement && (
                            <a href={piece.url_telechargement} target="_blank" rel="noreferrer" className="btn btn-ghost btn-sm" style={{ fontSize: 12 }}>Voir</a>
                          )}
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}
            </div>

            {/* Sélecteur formation niveau supérieur */}
            {niveauCourant && eligibilite?.eligible && (
              <div style={{ marginTop: 10, padding: '12px 16px', borderRadius: 10, background: '#f0f5ff', border: '1px solid #c7d8ff' }}>
                <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--blue)', marginBottom: 10, display: 'flex', alignItems: 'center', gap: 6 }}>
                  <ArrowRight size={14} /> Passage en année supérieure
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 }}>
                  <span style={{ fontWeight: 700, fontSize: 13, background: '#dbeafe', color: '#1d4ed8', padding: '3px 10px', borderRadius: 99 }}>
                    {niveauCourant}
                  </span>
                  <ArrowRight size={14} color="var(--gray-400)" />
                  <span style={{ fontWeight: 700, fontSize: 13, background: '#dcfce7', color: '#15803d', padding: '3px 10px', borderRadius: 99 }}>
                    {niveauSuivant(niveauCourant) || '?'}
                  </span>
                </div>
                <label style={{ fontSize: 12, fontWeight: 600, color: 'var(--gray-700)', display: 'block', marginBottom: 6 }}>
                  Formation pour {anneeProchaine} <span style={{ color: 'var(--danger)' }}>*</span>
                </label>
                <select
                  className="form-control"
                  value={formationChoisie || ''}
                  onChange={e => setFormationChoisie(e.target.value ? Number.parseInt(e.target.value, 10) : null)}
                  style={{ fontSize: 13 }}
                >
                  <option value="">— Choisir une formation —</option>
                  {(() => {
                    const suivant    = niveauSuivant(niveauCourant)
                    const formSuiv   = formations.filter(f => f.niveau === suivant)
                    const formAutres = formations.filter(f => f.niveau !== suivant)
                    return (
                      <>
                        {formSuiv.length > 0 && (
                          <optgroup label={`${suivant} — Recommandé`}>
                            {formSuiv.map(f => <option key={f.id} value={f.id}>{f.libelle} ({f.code_formation})</option>)}
                          </optgroup>
                        )}
                        {formAutres.length > 0 && (
                          <optgroup label="Autres formations">
                            {formAutres.map(f => <option key={f.id} value={f.id}>{f.niveau} — {f.libelle}</option>)}
                          </optgroup>
                        )}
                      </>
                    )
                  })()}
                </select>
              </div>
            )}

            {dossier && dossier.score_completude < 100 && (
              <div className="alert alert-warning" style={{ fontSize: 12, marginTop: 10 }}>
                <AlertCircle size={14} /> Déposez toutes les pièces obligatoires avant de soumettre ({dossier.score_completude}% complet).
              </div>
            )}

            <button
              className="btn btn-primary btn-block"
              style={{ marginTop: 12 }}
              onClick={soumettre}
              disabled={submitting || checkingElig || (eligibilite && !eligibilite.eligible) || (dossier && dossier.score_completude < 100)}
            >
              {submitting
                ? <div className="spinner" />
                : <><Send size={15} /> Soumettre ma réinscription {anneeProchaine}</>}
            </button>
          </div>
        </div>
      )}

      {/* ── SECTION 4 : Statut réinscription (si déjà soumise) ── */}
      {inscProchaine && (
        <>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
            <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--gray-700)' }}>
              🔄 Réinscription — {anneeProchaine}
            </div>
            <button className="btn btn-ghost btn-sm" style={{ fontSize: 12 }} onClick={async () => {
              try {
                const r = await api.get(`${BASE.inscription}/mon-inscription/?annee=${anneeProchaine}`)
                setInscProchaine(r.data)
                if (r.data?.id) {
                  api.get(`${BASE.inscription}/${r.data.id}/paiement/`)
                    .then(p => setPaiementProchain(p.data)).catch(() => {})
                }
                toast.success('Statut mis à jour.')
              } catch { toast.error('Erreur lors du rafraîchissement.') }
            }}>
              ↻ Rafraîchir
            </button>
          </div>
          <InscriptionCard
            inscription={inscProchaine}
            paiement={paiementProchain}
            paying={paying}
            onPayer={() => handlePaiement(inscProchaine)}
            titre={`Réinscription — ${anneeProchaine}`}
            accent
          />
        </>
      )}
    </div>
  )
}
