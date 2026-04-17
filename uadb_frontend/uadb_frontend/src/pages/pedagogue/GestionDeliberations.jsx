import { useState, useEffect } from 'react'
import api, { BASE } from '../../config/api'
import { useAuth } from '../../context/AuthContext'
import toast from 'react-hot-toast'
import {
  Plus, BookOpen, Users, Lock, FileDown,
  X, ChevronDown, ChevronUp, UserPlus, Hash, CreditCard, GraduationCap, Play
} from 'lucide-react'

// ── Constantes ────────────────────────────────────────────────────────────────
const NIVEAUX  = ['L1', 'L2', 'L3', 'M1', 'M2']
const SESSIONS = ['normale', 'rattrapage']

const STATUT_BADGE  = { en_preparation: 'neutral', en_cours: 'info', cloturee: 'success' }
const DECISION_BADGE = { admis: 'success', rattrapage: 'warning', 'ajourné': 'danger', en_attente: 'neutral' }
const MENTION_LABEL  = { tres_bien: 'Très Bien', bien: 'Bien', assez_bien: 'Assez Bien', passable: 'Passable', '': '—' }

const EMPTY_FORM    = { session: 'normale', annee_universitaire: '', semestre: 1, niveau: 'M1', formation_id: '', date_deliberation: '' }
const EMPTY_CLOTURE = { decision_finale: '', observation: '' }
const EMPTY_AJOUT   = { etudiant_id: '', inscription_id: '', credits_total: 60 }

// ── Composant principal ───────────────────────────────────────────────────────
export default function GestionDeliberations() {
  const { user } = useAuth()
  const anneeActuelle = `${new Date().getFullYear()}-${new Date().getFullYear() + 1}`
  const annee         = anneeActuelle  // rétrocompatibilité interne

  // ── Filtres année : génère 3 années (n-1, n, n+1)
  const anneesDisponibles = [
    `${new Date().getFullYear() - 1}-${new Date().getFullYear()}`,
    anneeActuelle,
    `${new Date().getFullYear() + 1}-${new Date().getFullYear() + 2}`,
  ]
  const [anneeFiltre, setAnneeFiltre] = useState(anneeActuelle)

  // ── Listes
  const [delibs,     setDelibs]     = useState([])
  const [total,      setTotal]      = useState(0)
  const [formations, setFormations] = useState([])

  // ── Panneau résultats
  const [selected,   setSelected]   = useState(null)
  const [resultats,  setResultats]  = useState([])
  const [nomsMap,    setNomsMap]    = useState({})  // { etudiant_id: nom_complet }

  // ── Chargements
  const [loading,    setLoading]    = useState(true)
  const [loadingRes, setLoadingRes] = useState(false)
  const [saving,     setSaving]     = useState(false)

  // ── Filtres
  const [filtreStat, setFiltreStat] = useState('')

  // ── Modals
  const [modalCreate,  setModalCreate]  = useState(false)
  const [modalCloture, setModalCloture] = useState(null)
  const [modalAjout,   setModalAjout]   = useState(null)

  // ── Formulaires
  const [form,        setForm]        = useState(EMPTY_FORM)
  const [formCloture, setFormCloture] = useState(EMPTY_CLOTURE)
  const [formAjout,   setFormAjout]   = useState(EMPTY_AJOUT)

  // ── Recherche étudiant par nom
  const [nomSearch,    setNomSearch]    = useState('')
  const [nomResults,   setNomResults]   = useState([])
  const [nomLoading,   setNomLoading]   = useState(false)
  const [nomSelected,  setNomSelected]  = useState(null)   // { id, nom_complet }
  const [nomTimer,     setNomTimer]     = useState(null)

  // ── Chargement initial ────────────────────────────────────────────────────
  const charger = async () => {
    setLoading(true)
    try {
      const params = `annee=${anneeFiltre}${filtreStat ? `&statut=${filtreStat}` : ''}`
      const r = await api.get(`${BASE.deliberation}/?${params}`)
      setDelibs(r.data.results || [])
      setTotal(r.data.count    || 0)
    } catch { toast.error('Erreur lors du chargement.') }
    finally  { setLoading(false) }
  }

  useEffect(() => { charger() }, [filtreStat, anneeFiltre])

  useEffect(() => {
    api.get(`${BASE.formation}/`)
      .then(r => setFormations(r.data.results || []))
      .catch(() => {})
  }, [])

  // ── Charger les résultats d'une délibération ──────────────────────────────
  const chargerResultats = async delib => {
    if (selected?.id === delib.id) { setSelected(null); setResultats([]); return }
    setSelected(delib)
    setResultats([])
    setLoadingRes(true)
    try {
      const r = await api.get(`${BASE.deliberation}/${delib.id}/resultats/`)
      const items = r.data.results || []
      setResultats(items)
      // Récupérer les noms en batch
      const ids = [...new Set(items.map(i => i.etudiant_id))].filter(Boolean)
      if (ids.length > 0) {
        try {
          const nr = await api.get(`${BASE.auth}/etudiants/noms/?ids=${ids.join(',')}`)
          setNomsMap(nr.data || {})
        } catch { /* silencieux, on garde les IDs */ }
      }
    } catch { toast.error('Erreur chargement des résultats.') }
    finally  { setLoadingRes(false) }
  }

  // ── Créer une délibération ────────────────────────────────────────────────
  const creerDelib = async () => {
    if (!form.annee_universitaire || !form.formation_id) {
      toast.error('Veuillez remplir tous les champs obligatoires.')
      return
    }
    setSaving(true)
    try {
      await api.post(`${BASE.deliberation}/`, {
        ...form,
        formation_id      : parseInt(form.formation_id),
        semestre          : parseInt(form.semestre),
        jury_president_id : user?.id || null,
      })
      toast.success('Délibération créée avec succès !')
      setModalCreate(false)
      setForm(EMPTY_FORM)
      charger()
    } catch (e) {
      const err = e.response?.data
      toast.error(err?.non_field_errors?.[0] || err?.detail || 'Erreur lors de la création.')
    } finally { setSaving(false) }
  }

  // ── Recherche étudiant par nom (débouncé) ──────────────────────────────
  const handleNomChange = (val) => {
    setNomSearch(val)
    setNomSelected(null)
    setFormAjout(f => ({ ...f, etudiant_id: '' }))
    if (nomTimer) clearTimeout(nomTimer)
    if (val.length < 2) { setNomResults([]); return }
    const t = setTimeout(async () => {
      setNomLoading(true)
      try {
        const r = await api.get(`${BASE.auth}/etudiants/search/?q=${encodeURIComponent(val)}`)
        setNomResults(r.data.results || [])
      } catch { setNomResults([]) }
      finally { setNomLoading(false) }
    }, 350)
    setNomTimer(t)
  }

  const selectNomResult = (etudiant) => {
    setNomSelected(etudiant)
    setNomSearch(etudiant.nom_complet)
    setNomResults([])
    setFormAjout(f => ({ ...f, etudiant_id: etudiant.id }))
  }

  const resetNomSearch = () => {
    setNomSearch('')
    setNomResults([])
    setNomSelected(null)
    setFormAjout(f => ({ ...f, etudiant_id: '' }))
  }

  // ── Ajouter un étudiant ──────────────────────────────────────────────────
  const ajouterEtudiant = async () => {
    if (!formAjout.etudiant_id) { toast.error("Veuillez sélectionner un étudiant."); return }
    setSaving(true)
    try {
      await api.post(`${BASE.deliberation}/${modalAjout.id}/resultats/`, {
        etudiant_id    : parseInt(formAjout.etudiant_id),
        inscription_id : formAjout.inscription_id ? parseInt(formAjout.inscription_id) : null,
        credits_total  : parseInt(formAjout.credits_total) || 60,
      })
      toast.success('Étudiant ajouté à la délibération.')
      // Mettre à jour le cache des noms
      if (nomSelected) {
        setNomsMap(prev => ({ ...prev, [nomSelected.id]: nomSelected.nom_complet }))
      }
      setModalAjout(null)
      setFormAjout(EMPTY_AJOUT)
      resetNomSearch()
      if (selected?.id === modalAjout.id) chargerResultats(selected)
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Cet étudiant est peut-être déjà dans la délibération.')
    } finally { setSaving(false) }
  }

  // ── Clôturer une délibération ───────────────────────────────────────────────
  const demarrerDelib = async (delib) => {
    try {
      await api.post(`${BASE.deliberation}/${delib.id}/demarrer/`)
      toast.success('Délibération démarrée — les enseignants peuvent saisir les notes.')
      charger()
      if (selected?.id === delib.id) {
        setSelected(prev => ({ ...prev, statut: 'en_cours' }))
      }
    } catch (e) {
      toast.error(e.response?.data?.error || 'Erreur lors du démarrage.')
    }
  }

  // ── Clôturer une délibération ───────────────────────────────────────────────
  const cloturerDelib = async () => {
    setSaving(true)
    try {
      await api.post(`${BASE.deliberation}/${modalCloture.id}/cloturer/`, formCloture)
      toast.success('Délibération clôturée ! Rangs calculés et étudiants notifiés.')
      setModalCloture(null)
      setFormCloture(EMPTY_CLOTURE)
      charger()
      if (selected?.id === modalCloture.id) {
        const r = await api.get(`${BASE.deliberation}/${modalCloture.id}/`)
        setSelected(r.data)
        chargerResultats(r.data)
      }
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Erreur lors de la clôture.')
    } finally { setSaving(false) }
  }

  // ── Télécharger le PV PDF ─────────────────────────────────────────────────
  const telechargerPV = async delib => {
    try {
      const r = await api.get(`${BASE.deliberation}/${delib.id}/pv/`, { responseType: 'blob' })
      const url = URL.createObjectURL(r.data)
      const a   = document.createElement('a')
      a.href     = url
      a.download = `PV_S${delib.semestre}_${delib.annee_universitaire}_${delib.session}.pdf`
      a.click()
      URL.revokeObjectURL(url)
      toast.success('PV téléchargé !')
    } catch {
      toast.error('Le PV n\'est disponible qu\'après la clôture.')
    }
  }

  // ── Modifier la décision d'un résultat ───────────────────────────────────
  const modifierDecision = async (resultatId, decision) => {
    try {
      await api.patch(`${BASE.resultat}/${resultatId}/`, { decision, mention: '' })
      toast.success('Décision mise à jour.')
      if (selected) {
        setResultats(prev => prev.map(r => r.id === resultatId ? { ...r, decision } : r))
      }
    } catch { toast.error('Erreur lors de la modification.') }
  }

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <div className="page">

      {/* En-tête */}
      <div className="page-header flex items-center justify-between">
        <div>
          <h1 className="page-title">Gestion des Délibérations</h1>
          <p className="page-subtitle">{total} délibération(s) — Année {anneeFiltre}</p>
        </div>
        <button className="btn btn-primary" onClick={() => {
          setForm({ ...EMPTY_FORM, annee_universitaire: anneeFiltre })
          setModalCreate(true)
        }}>
          <Plus size={15} /> Nouvelle délibération
        </button>
      </div>

      {/* Filtres */}
      <div className="card fade-up" style={{ marginBottom: 20 }}>
        <div className="card-padded" style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
          {/* Sélecteur d'année */}
          <select
            value={anneeFiltre}
            onChange={e => { setAnneeFiltre(e.target.value); setSelected(null); setResultats([]) }}
            style={{
              border: '1px solid var(--gray-200)', borderRadius: 8, padding: '5px 10px',
              fontSize: 13, fontWeight: 600, color: 'var(--gray-700)', background: 'white',
              cursor: 'pointer', marginRight: 8,
            }}
          >
            {anneesDisponibles.map(a => (
              <option key={a} value={a}>{a}</option>
            ))}
          </select>

          {/* Filtre statut */}
          {[
            { val: '',                label: 'Toutes'          },
            { val: 'en_preparation',  label: 'En préparation'  },
            { val: 'en_cours',        label: 'En cours'        },
            { val: 'cloturee',        label: 'Clôturées'       },
          ].map(f => (
            <button
              key={f.val}
              className={`btn btn-sm ${filtreStat === f.val ? 'btn-primary' : 'btn-ghost'}`}
              onClick={() => { setFiltreStat(f.val); setSelected(null); setResultats([]) }}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      {/* Grille : liste + panneau résultats */}
      <div style={{ display: 'grid', gridTemplateColumns: selected ? '1fr 1.5fr' : '1fr', gap: 20 }}>

        {/* ── Liste des délibérations ── */}
        <div className="card fade-up" style={{ animationDelay: '60ms' }}>
          {loading ? (
            <div className="card-body">
              {[1, 2, 3, 4].map(i => (
                <div key={i} className="skeleton" style={{ height: 80, marginBottom: 12, borderRadius: 8 }} />
              ))}
            </div>
          ) : delibs.length === 0 ? (
            <div className="card-body">
              <div className="empty-state">
                <div className="empty-state-icon"><BookOpen size={30} /></div>
                <p>Aucune délibération trouvée pour {anneeFiltre}.</p>
                <button className="btn btn-primary btn-sm" style={{ marginTop: 12 }}
                  onClick={() => { setForm({ ...EMPTY_FORM, annee_universitaire: anneeFiltre }); setModalCreate(true) }}>
                  <Plus size={13} /> Créer la première
                </button>
              </div>
            </div>
          ) : (
            <div>
              {delibs.map((d, i) => (
                <div
                  key={d.id}
                  onClick={() => chargerResultats(d)}
                  style={{
                    padding: '16px 20px',
                    borderBottom: i < delibs.length - 1 ? '1px solid var(--gray-100)' : 'none',
                    cursor: 'pointer',
                    background: selected?.id === d.id ? 'var(--info-bg)' : 'white',
                    borderLeft: selected?.id === d.id ? '3px solid var(--blue)' : '3px solid transparent',
                    transition: 'all .15s',
                  }}
                  onMouseEnter={e => { if (selected?.id !== d.id) e.currentTarget.style.background = 'var(--gray-50)' }}
                  onMouseLeave={e => { if (selected?.id !== d.id) e.currentTarget.style.background = 'white' }}
                >
                  <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 10 }}>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 5, flexWrap: 'wrap' }}>
                        <span style={{ fontSize: 14, fontWeight: 700, color: 'var(--gray-800)' }}>
                          S{d.semestre} — {d.niveau} — Session {d.session}
                        </span>
                        <span className={`badge badge-${STATUT_BADGE[d.statut] || 'neutral'}`}>
                          {d.statut}
                        </span>
                      </div>
                      <div style={{ display: 'flex', gap: 14, fontSize: 12, color: 'var(--gray-400)', flexWrap: 'wrap' }}>
                        <span><Users size={11} style={{ verticalAlign: 'middle', marginRight: 3 }} />{d.nb_etudiants || 0} étud.</span>
                        <span>Formation #{d.formation_id}</span>
                        {d.date_deliberation && (
                          <span>📅 {new Date(d.date_deliberation).toLocaleDateString('fr-FR')}</span>
                        )}
                      </div>
                    </div>

                    {/* Boutons actions */}
                    <div style={{ display: 'flex', gap: 5, flexShrink: 0 }} onClick={e => e.stopPropagation()}>
                      {d.statut !== 'cloturee' && (
                        <button
                          className="btn btn-ghost btn-sm btn-icon"
                          title="Ajouter un étudiant"
                          onClick={() => { setModalAjout(d); setFormAjout(EMPTY_AJOUT); resetNomSearch() }}
                        >
                          <Users size={13} />
                        </button>
                      )}
                      {d.statut === 'en_preparation' && (
                        <button
                          className="btn btn-sm"
                          style={{ background: 'var(--success-bg)', color: 'var(--success)', border: '1px solid var(--success)', fontSize: 11 }}
                          onClick={() => demarrerDelib(d)}
                        >
                          <Play size={12} /> Démarrer
                        </button>
                      )}
                      {d.statut === 'en_cours' && (
                        <button
                          className="btn btn-sm"
                          style={{ background: 'var(--danger-bg)', color: 'var(--danger)', border: '1px solid var(--danger)', fontSize: 11 }}
                          onClick={() => { setModalCloture(d); setFormCloture(EMPTY_CLOTURE) }}
                        >
                          <Lock size={12} /> Clôturer
                        </button>
                      )}
                      {d.statut === 'cloturee' && (
                        <button
                          className="btn btn-primary btn-sm"
                          onClick={() => telechargerPV(d)}
                        >
                          <FileDown size={12} /> PV PDF
                        </button>
                      )}
                      <button className="btn btn-ghost btn-sm btn-icon">
                        {selected?.id === d.id ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* ── Panneau résultats ── */}
        {selected && (
          <div className="card fade-in">
            <div className="card-header" style={{ flexWrap: 'wrap', gap: 8 }}>
              <div>
                <div className="card-title">
                  Résultats — S{selected.semestre} / {selected.session} / {selected.annee_universitaire}
                </div>
                <div style={{ fontSize: 11, color: 'var(--gray-400)', marginTop: 2 }}>
                  {resultats.length} étudiant(s)
                </div>
              </div>
              <div style={{ display: 'flex', gap: 8, marginLeft: 'auto' }}>
                {selected.statut === 'cloturee' && (
                  <button className="btn btn-primary btn-sm" onClick={() => telechargerPV(selected)}>
                    <FileDown size={13} /> PV PDF
                  </button>
                )}
                <button className="btn btn-ghost btn-sm btn-icon" onClick={() => { setSelected(null); setResultats([]) }}>
                  <X size={14} />
                </button>
              </div>
            </div>

            {/* Résumé statistique */}
            {resultats.length > 0 && (
              <div style={{
                display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 10,
                padding: '14px 20px', borderBottom: '1px solid var(--gray-100)',
              }}>
                {[
                  { label: 'Admis',      val: resultats.filter(r => r.decision === 'admis').length,      color: 'var(--success)' },
                  { label: 'Rattrapage', val: resultats.filter(r => r.decision === 'rattrapage').length,  color: 'var(--warning)' },
                  { label: 'Ajournés',   val: resultats.filter(r => r.decision === 'ajourné').length,    color: 'var(--danger)'  },
                  {
                    label: 'Taux réussite',
                    val: resultats.length > 0
                      ? `${Math.round(resultats.filter(r => r.decision === 'admis').length / resultats.length * 100)}%`
                      : '0%',
                    color: 'var(--blue)',
                  },
                ].map(s => (
                  <div key={s.label} style={{
                    textAlign: 'center', padding: '8px 4px',
                    borderRadius: 8, background: 'var(--gray-50)',
                  }}>
                    <div style={{ fontSize: 18, fontWeight: 800, color: s.color }}>{s.val}</div>
                    <div style={{ fontSize: 10, color: 'var(--gray-400)', fontWeight: 500, marginTop: 2 }}>{s.label}</div>
                  </div>
                ))}
              </div>
            )}

            {/* Table des résultats */}
            {loadingRes ? (
              <div className="card-body">
                {[1, 2, 3].map(i => (
                  <div key={i} className="skeleton" style={{ height: 44, marginBottom: 8, borderRadius: 6 }} />
                ))}
              </div>
            ) : resultats.length === 0 ? (
              <div className="card-body">
                <div className="empty-state">
                  <div className="empty-state-icon"><Users size={28} /></div>
                  <p style={{ fontSize: 13 }}>Aucun étudiant dans cette délibération</p>
                  {selected.statut !== 'cloturee' && (
                    <button className="btn btn-primary btn-sm" style={{ marginTop: 12 }}
                      onClick={() => { setModalAjout(selected); setFormAjout(EMPTY_AJOUT); resetNomSearch() }}>
                      <Plus size={13} /> Ajouter des étudiants
                    </button>
                  )}
                </div>
              </div>
            ) : (
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Rang</th>
                      <th>Étudiant</th>
                      <th>Moyenne</th>
                      <th>Crédits</th>
                      <th>Décision</th>
                      <th>Mention</th>
                      {selected.statut !== 'cloturee' && <th>Modifier</th>}
                    </tr>
                  </thead>
                  <tbody>
                    {resultats.map(r => (
                      <tr key={r.id}>
                        <td>
                          <span style={{
                            display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
                            width: 26, height: 26, borderRadius: '50%',
                            background: 'var(--gray-100)', fontSize: 11, fontWeight: 700,
                          }}>
                            {r.rang || '—'}
                          </span>
                        </td>
                        <td style={{ fontWeight: 600, fontSize: 13 }}>
                          {nomsMap[r.etudiant_id]
                            ? nomsMap[r.etudiant_id]
                            : <span style={{ color: 'var(--gray-400)', fontSize: 12 }}>#{r.etudiant_id}</span>
                          }
                        </td>
                        <td>
                          <span style={{
                            fontWeight: 700,
                            color: r.moyenne_annuelle
                              ? parseFloat(r.moyenne_annuelle) >= 10 ? 'var(--success)' : 'var(--danger)'
                              : 'var(--gray-400)',
                          }}>
                            {r.moyenne_annuelle
                              ? `${parseFloat(r.moyenne_annuelle).toFixed(2)}/20`
                              : '—'}
                          </span>
                        </td>
                        <td style={{ fontSize: 12 }}>{r.credits_valides}/{r.credits_total}</td>
                        <td>
                          <span className={`badge badge-${DECISION_BADGE[r.decision] || 'neutral'}`}>
                            {r.decision}
                          </span>
                        </td>
                        <td style={{ fontSize: 12, color: 'var(--gray-500)' }}>
                          {MENTION_LABEL[r.mention] || '—'}
                        </td>
                        {selected.statut !== 'cloturee' && (
                          <td>
                            <select
                              className="form-control"
                              style={{ padding: '4px 8px', fontSize: 11, height: 'auto', width: 'auto', minWidth: 100 }}
                              value={r.decision}
                              onChange={e => modifierDecision(r.id, e.target.value)}
                            >
                              {['en_attente', 'admis', 'rattrapage', 'ajourné', 'exclu'].map(d => (
                                <option key={d} value={d}>{d}</option>
                              ))}
                            </select>
                          </td>
                        )}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </div>

      {/* ── MODAL : Créer délibération ── */}
      {modalCreate && (
        <div className="modal-overlay" onClick={() => setModalCreate(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <span className="modal-title">Nouvelle délibération</span>
              <button className="btn btn-ghost btn-sm btn-icon" onClick={() => setModalCreate(false)}>✕</button>
            </div>
            <div className="modal-body">
              <div className="grid-2">
                <div className="form-group">
                  <label className="form-label">Session *</label>
                  <select className="form-control" value={form.session}
                    onChange={e => setForm(f => ({ ...f, session: e.target.value }))}>
                    {SESSIONS.map(s => <option key={s} value={s}>{s}</option>)}
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Semestre *</label>
                  <select className="form-control" value={form.semestre}
                    onChange={e => setForm(f => ({ ...f, semestre: parseInt(e.target.value) }))}>
                    {[1, 2, 3, 4].map(s => <option key={s} value={s}>Semestre {s}</option>)}
                  </select>
                </div>
              </div>
              <div className="grid-2">
                <div className="form-group">
                  <label className="form-label">Niveau *</label>
                  <select className="form-control" value={form.niveau}
                    onChange={e => setForm(f => ({ ...f, niveau: e.target.value }))}>
                    {NIVEAUX.map(n => <option key={n} value={n}>{n}</option>)}
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Année universitaire *</label>
                  <input className="form-control" placeholder="ex: 2024-2025"
                    value={form.annee_universitaire}
                    onChange={e => setForm(f => ({ ...f, annee_universitaire: e.target.value }))} />
                </div>
              </div>
              <div className="form-group">
                <label className="form-label">Formation *</label>
                <select className="form-control" value={form.formation_id}
                  onChange={e => setForm(f => ({ ...f, formation_id: e.target.value }))}>
                  <option value="">-- Choisir une formation --</option>
                  {formations.map(f => (
                    <option key={f.id} value={f.id}>{f.code_formation} — {f.libelle}</option>
                  ))}
                </select>
              </div>
              <div className="form-group" style={{ marginBottom: 0 }}>
                <label className="form-label">Date prévue de délibération</label>
                <input className="form-control" type="date"
                  value={form.date_deliberation}
                  onChange={e => setForm(f => ({ ...f, date_deliberation: e.target.value }))} />
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn btn-ghost" onClick={() => setModalCreate(false)}>Annuler</button>
              <button className="btn btn-primary" onClick={creerDelib} disabled={saving}>
                {saving ? <div className="spinner" /> : <><Plus size={14} /> Créer</>}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── MODAL : Ajouter un étudiant ── */}
      {modalAjout && (
        <div className="modal-overlay" onClick={() => setModalAjout(null)}>
          <div className="modal" style={{ maxWidth: 460, padding: 0, overflow: 'hidden' }} onClick={e => e.stopPropagation()}>

            {/* En-tête riche */}
            <div style={{
              background: 'linear-gradient(135deg, #1565c0 0%, #1e40af 100%)',
              padding: '22px 24px 18px',
              color: 'white',
              position: 'relative',
            }}>
              <button
                className="btn btn-ghost btn-sm btn-icon"
                onClick={() => setModalAjout(null)}
                style={{ position: 'absolute', top: 14, right: 14, color: 'rgba(255,255,255,.7)' }}
              >
                <X size={16} />
              </button>

              {/* Icône + titre */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
                <div style={{
                  width: 42, height: 42, borderRadius: 10,
                  background: 'rgba(255,255,255,.15)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  flexShrink: 0,
                }}>
                  <UserPlus size={20} />
                </div>
                <div>
                  <h2 style={{ margin: 0, fontSize: 16, fontWeight: 700 }}>Ajouter un étudiant</h2>
                  <p style={{ margin: 0, fontSize: 12, opacity: .75, marginTop: 1 }}>Inscrire à la délibération en cours</p>
                </div>
              </div>

              {/* Contexte délibération */}
              <div style={{
                display: 'flex', gap: 8, flexWrap: 'wrap',
              }}>
                {[
                  { label: `Semestre ${modalAjout.semestre}` },
                  { label: modalAjout.niveau },
                  { label: `Session ${modalAjout.session}` },
                  { label: modalAjout.annee_universitaire },
                ].map(tag => (
                  <span key={tag.label} style={{
                    padding: '3px 10px', borderRadius: 20,
                    background: 'rgba(255,255,255,.15)',
                    fontSize: 11.5, fontWeight: 500,
                  }}>{tag.label}</span>
                ))}
              </div>
            </div>

            {/* Corps du formulaire */}
            <div style={{ padding: '20px 24px 4px' }}>

              {/* Recherche étudiant par nom */}
              <div className="form-group" style={{ position: 'relative' }}>
                <label className="form-label" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <Users size={13} style={{ color: 'var(--blue)' }} />
                  Nom de l'étudiant <span style={{ color: 'var(--danger)' }}>*</span>
                </label>
                <div style={{ position: 'relative' }}>
                  <input
                    className="form-control"
                    type="text"
                    placeholder="Rechercher par nom ou prénom…"
                    value={nomSearch}
                    onChange={e => handleNomChange(e.target.value)}
                    style={{ fontSize: 14, paddingRight: nomSelected ? 36 : 12 }}
                    autoComplete="off"
                  />
                  {nomSelected && (
                    <button
                      onClick={resetNomSearch}
                      style={{ position: 'absolute', right: 8, top: '50%', transform: 'translateY(-50%)',
                               background: 'none', border: 'none', cursor: 'pointer', color: 'var(--gray-400)',
                               display: 'flex', alignItems: 'center' }}
                    >
                      <X size={14} />
                    </button>
                  )}
                </div>

                {/* Résultats */}
                {(nomResults.length > 0 || nomLoading) && !nomSelected && (
                  <div style={{ position: 'absolute', zIndex: 999, left: 0, right: 0,
                                background: 'white', border: '1px solid var(--gray-200)',
                                borderRadius: 8, boxShadow: '0 4px 16px rgba(0,0,0,.1)',
                                maxHeight: 200, overflowY: 'auto', marginTop: 2 }}>
                    {nomLoading && (
                      <div style={{ padding: '10px 14px', fontSize: 13, color: 'var(--gray-400)' }}>Recherche…</div>
                    )}
                    {nomResults.map(e => (
                      <button
                        key={e.id}
                        type="button"
                        onClick={() => selectNomResult(e)}
                        style={{ width: '100%', padding: '9px 14px', cursor: 'pointer', fontSize: 13,
                                 borderBottom: '1px solid var(--gray-100)', background: 'white',
                                 border: 'none', borderBottomColor: 'var(--gray-100)', borderBottomStyle: 'solid', borderBottomWidth: 1,
                                 display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                                 textAlign: 'left' }}
                        onMouseEnter={ev => ev.currentTarget.style.background = '#f0f4ff'}
                        onMouseLeave={ev => ev.currentTarget.style.background = 'white'}
                      >
                        <span style={{ fontWeight: 500 }}>{e.nom_complet}</span>
                        <span style={{ fontSize: 11, color: 'var(--gray-400)' }}>@{e.username}</span>
                      </button>
                    ))}
                    {!nomLoading && nomResults.length === 0 && (
                      <div style={{ padding: '10px 14px', fontSize: 13, color: 'var(--gray-400)' }}>Aucun résultat</div>
                    )}
                  </div>
                )}

                {nomSelected && (
                  <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4, marginTop: 6,
                                 background: '#ebf2ff', color: 'var(--blue)', borderRadius: 20,
                                 padding: '2px 10px', fontSize: 12, fontWeight: 600 }}>
                    <Hash size={10} /> ID {nomSelected.id}
                  </span>
                )}
              </div>

              {/* ID Inscription + Crédits */}
              <div className="grid-2">
                <div className="form-group">
                  <label className="form-label" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <GraduationCap size={13} style={{ color: 'var(--gray-400)' }} />
                    ID Inscription
                  </label>
                  <input
                    className="form-control"
                    type="number"
                    placeholder="optionnel"
                    value={formAjout.inscription_id}
                    onChange={e => setFormAjout(f => ({ ...f, inscription_id: e.target.value }))}
                  />
                </div>
                <div className="form-group">
                  <label className="form-label" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <CreditCard size={13} style={{ color: 'var(--gray-400)' }} />
                    Crédits total
                  </label>
                  <input
                    className="form-control"
                    type="number"
                    min="1"
                    max="120"
                    value={formAjout.credits_total}
                    onChange={e => setFormAjout(f => ({ ...f, credits_total: e.target.value }))}
                  />
                </div>
              </div>
            </div>

            <div className="modal-footer" style={{ padding: '12px 24px 20px', borderTop: '1px solid var(--gray-100)' }}>
              <button className="btn btn-ghost" onClick={() => setModalAjout(null)}>Annuler</button>
              <button className="btn btn-primary" onClick={ajouterEtudiant} disabled={saving}>
                {saving ? <div className="spinner" /> : <><UserPlus size={14} /> Ajouter l'étudiant</>}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── MODAL : Clôturer ── */}
      {modalCloture && (
        <div className="modal-overlay" onClick={() => setModalCloture(null)}>
          <div className="modal" style={{ maxWidth: 500 }} onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <span className="modal-title">Clôturer la délibération</span>
              <button className="btn btn-ghost btn-sm btn-icon" onClick={() => setModalCloture(null)}>✕</button>
            </div>
            <div className="modal-body">
              <div style={{
                padding: '12px 14px', borderRadius: 8, marginBottom: 16,
                background: 'var(--warning-bg)', border: '1px solid #fde68a',
                fontSize: 13, color: 'var(--warning)', lineHeight: 1.5,
              }}>
                ⚠️ Cette action est <strong>irréversible</strong>. Toutes les notes seront
                verrouillées, les rangs calculés automatiquement et chaque étudiant sera
                notifié par email de sa décision.
              </div>
              <div style={{
                padding: '10px 14px', borderRadius: 8, marginBottom: 16,
                background: 'var(--gray-50)', border: '1px solid var(--gray-200)',
                fontSize: 12.5, color: 'var(--gray-600)',
              }}>
                <strong>Délibération :</strong> S{modalCloture.semestre} — {modalCloture.niveau} — {modalCloture.session}
                <br />{modalCloture.nb_etudiants || 0} étudiant(s) concerné(s)
              </div>
              <div className="form-group">
                <label className="form-label">Décision finale du jury</label>
                <textarea className="form-control" rows={2}
                  placeholder="ex: Session normale 2024-2025 clôturée. Taux de réussite : 78%."
                  value={formCloture.decision_finale}
                  onChange={e => setFormCloture(f => ({ ...f, decision_finale: e.target.value }))} />
              </div>
              <div className="form-group" style={{ marginBottom: 0 }}>
                <label className="form-label">Observations</label>
                <textarea className="form-control" rows={2}
                  placeholder="Remarques du jury (optionnel)..."
                  value={formCloture.observation}
                  onChange={e => setFormCloture(f => ({ ...f, observation: e.target.value }))} />
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn btn-ghost" onClick={() => setModalCloture(null)}>Annuler</button>
              <button className="btn btn-danger" onClick={cloturerDelib} disabled={saving}>
                {saving ? <div className="spinner" /> : <><Lock size={14} /> Clôturer définitivement</>}
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  )
}
