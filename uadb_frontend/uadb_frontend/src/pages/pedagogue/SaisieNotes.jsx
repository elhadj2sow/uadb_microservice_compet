import { useState, useEffect, useMemo } from 'react'
import api, { BASE } from '../../config/api'
import toast from 'react-hot-toast'
import { Save, BookOpen, CheckCircle, AlertCircle, Users, GraduationCap, ClipboardList, Search, X } from 'lucide-react'

// ── Calcul prévisualisation note ──────────────────────────────────────────────
function calculerNote(cc, tp, ex, rattrapage) {
  const parts = []
  let poids   = 0
  if (cc  !== '' && cc  != null) { parts.push(parseFloat(cc)  * 0.3); poids += 0.3 }
  if (tp  !== '' && tp  != null) { parts.push(parseFloat(tp)  * 0.2); poids += 0.2 }
  if (ex  !== '' && ex  != null) { parts.push(parseFloat(ex)  * 0.5); poids += 0.5 }

  const noteNormale = (parts.length && poids > 0)
    ? parts.reduce((a, b) => a + b, 0) / poids
    : null

  if (rattrapage !== '' && rattrapage != null) {
    const r = parseFloat(rattrapage)
    const base = noteNormale !== null ? Math.max(noteNormale, r) : r
    return base.toFixed(2)
  }

  return noteNormale !== null ? noteNormale.toFixed(2) : null
}

// ── Composant principal ───────────────────────────────────────────────────────
export default function SaisieNotes() {
  // ── Données
  const [delibs,    setDelibs]    = useState([])
  const [resultats, setResultats] = useState([])
  const [notes,     setNotes]     = useState([])

  // ── Sélection courante
  const [delibId,   setDelibId]   = useState('')
  const [selected,  setSelected]  = useState(null)  // résultat étudiant sélectionné
  const [nomsMap,   setNomsMap]   = useState({})     // { etudiant_id: nom_complet }

  // ── Formulaire saisie
  const [form, setForm] = useState({
    ue_id: '', code_ue: '', libelle_ue: '',
    credit_ue: 3, coefficient_ue: 1.0, semestre: 1,
    note_cc: '', note_tp: '', note_examen: '', note_rattrapage: '',
  })

  // ── États
  const [loading,    setLoading]    = useState(false)
  const [loadingRes, setLoadingRes] = useState(false)
  const [saving,     setSaving]     = useState(false)

  // ── UEs de la formation
  const [ues,            setUes]            = useState([])
  const [ueSearch,       setUeSearch]       = useState('')
  const [showUeDropdown, setShowUeDropdown] = useState(false)

  // UEs filtrées selon la recherche
  const filteredUes = useMemo(() => {
    if (!ueSearch.trim()) return ues
    const q = ueSearch.toLowerCase()
    return ues.filter(u =>
      u.code_ue.toLowerCase().includes(q) ||
      u.libelle_ue.toLowerCase().includes(q)
    )
  }, [ues, ueSearch])

  // ── Chargement des délibérations en cours ─────────────────────────────────
  useEffect(() => {
    api.get(`${BASE.deliberation}/?statut=en_cours`)
      .then(r => setDelibs(r.data.results || []))
      .catch(() => toast.error('Erreur chargement des délibérations.'))
  }, [])

  // ── Charger les UEs dès qu'une délibération est sélectionnée ─────────────
  const [loadingUes, setLoadingUes] = useState(false)

  useEffect(() => {
    if (!delibId) { setUes([]); return }
    const delib = delibs.find(d => d.id == delibId)
    if (!delib?.formation_id) return
    setLoadingUes(true)
    setUes([])
    // Charger TOUTES les UEs de la formation (sans filtre semestre — le M2 utilise S3/S4)
    api.get(`${BASE.formation}/${delib.formation_id}/ues/`)
      .then(r => {
        const all = r.data.ues || []
        setUes(all)
        if (all.length === 0) toast('Aucune UE trouvée pour cette formation.', { icon: '⚠️' })
      })
      .catch(() => toast.error('Impossible de charger les matières. Saisissez l\'ID manuellement.'))
      .finally(() => setLoadingUes(false))
  }, [delibId, delibs])

  // ── Charger les résultats d'une délibération ──────────────────────────────
  const chargerResultats = async id => {
    setDelibId(id)
    setSelected(null)
    setNotes([])
    setResultats([])
    setNomsMap({})
    setUes([])
    setUeSearch('')
    if (!id) return
    setLoadingRes(true)
    try {
      const r = await api.get(`${BASE.deliberation}/${id}/resultats/`)
      const items = r.data.results || []
      setResultats(items)
      // Récupérer les noms en batch
      const ids = [...new Set(items.map(i => i.etudiant_id))].filter(Boolean)
      if (ids.length > 0) {
        try {
          const nr = await api.get(`${BASE.auth}/etudiants/noms/?ids=${ids.join(',')}`)
          setNomsMap(nr.data || {})
        } catch { /* silencieux */ }
      }
    } catch {
      toast.error('Erreur lors du chargement des étudiants.')
    } finally { setLoadingRes(false) }
  }

  // ── Sélectionner un étudiant → charger ses notes ──────────────────────────
  const selectionnerEtudiant = async resultat => {
    setSelected(resultat)
    setNotes([])
    setLoading(true)
    try {
      const r = await api.get(`${BASE.resultat}/${resultat.id}/notes/`)
      setNotes(r.data.notes || [])
    } catch {
      toast.error('Erreur lors du chargement des notes.')
    } finally { setLoading(false) }
  }

  // ── Saisir une note ───────────────────────────────────────────────────────
  const saisirNote = async () => {
    if (!form.ue_id) {
      toast.error("L'ID de l'UE est requis.")
      return
    }
    if (form.note_examen === '' && form.note_cc === '' && form.note_tp === '') {
      toast.error('Saisissez au moins une note (CC, TP ou Examen).')
      return
    }

    const payload = {
      ue_id          : parseInt(form.ue_id),
      code_ue        : form.code_ue.trim(),
      libelle_ue     : form.libelle_ue.trim(),
      credit_ue      : parseInt(form.credit_ue)      || 3,
      coefficient_ue : parseFloat(form.coefficient_ue) || 1.0,
      semestre       : parseInt(form.semestre)       || 1,
      note_cc        : form.note_cc        !== '' ? parseFloat(form.note_cc)        : null,
      note_tp        : form.note_tp        !== '' ? parseFloat(form.note_tp)        : null,
      note_examen    : form.note_examen    !== '' ? parseFloat(form.note_examen)    : null,
      note_rattrapage: form.note_rattrapage !== '' ? parseFloat(form.note_rattrapage) : null,
    }

    setSaving(true)
    try {
      await api.post(`${BASE.resultat}/${selected.id}/notes/saisir/`, payload)
      toast.success('Note enregistrée ! Moyenne recalculée automatiquement.')

      // Recharger les notes et le résultat mis à jour
      const [notesR, resR] = await Promise.all([
        api.get(`${BASE.resultat}/${selected.id}/notes/`),
        api.get(`${BASE.resultat}/${selected.id}/`),
      ])
      const notesReloaded = notesR.data.notes || []
      setNotes(notesReloaded)
      setSelected(resR.data)

      // Mettre à jour les champs de note dans le formulaire avec les valeurs sauvegardées
      const noteSauvegardee = notesReloaded.find(n => n.ue_id === parseInt(form.ue_id))
      if (noteSauvegardee) {
        setForm(f => ({
          ...f,
          note_cc        : noteSauvegardee.note_cc         ?? '',
          note_tp        : noteSauvegardee.note_tp         ?? '',
          note_examen    : noteSauvegardee.note_examen     ?? '',
          note_rattrapage: noteSauvegardee.note_rattrapage ?? '',
        }))
      }

      // Mettre à jour la liste des résultats
      setResultats(prev =>
        prev.map(r => r.id === selected.id ? { ...r, ...resR.data } : r)
      )
    } catch (e) {
      const status = e.response?.status
      if (status === 401) {
        toast.error('Session expirée. Veuillez vous reconnecter.', { duration: 5000 })
        setTimeout(() => { window.location.href = '/login' }, 2000)
        return
      }
      if (status === 403) {
        toast.error('Accès refusé : votre compte ne possède pas le rôle enseignant.')
        return
      }
      const err = e.response?.data
      toast.error(err?.detail || err?.error || err?.ue_id?.[0] || 'Erreur lors de la saisie.')
    } finally { setSaving(false) }
  }

  // ── Prévisualisation ──────────────────────────────────────────────────────
  const noteCalc = calculerNote(form.note_cc, form.note_tp, form.note_examen, form.note_rattrapage)

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <div className="page">

      {/* En-tête */}
      <div className="page-header">
        <h1 className="page-title">Saisie des Notes</h1>
        <p className="page-subtitle">
          Calcul automatique : CC × 30% + TP × 20% + Examen × 50%
        </p>
      </div>

      {/* Sélection de la délibération */}
      <div className="card fade-up" style={{ marginBottom: 20 }}>
        {/* Header sélecteur */}
        <div style={{
          display: 'flex', alignItems: 'center', gap: 12,
          padding: '14px 18px', borderBottom: '1px solid var(--gray-100)',
        }}>
          <div style={{
            width: 38, height: 38, borderRadius: 9,
            background: '#e8f0fe',
            display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
          }}>
            <ClipboardList size={18} color="var(--blue)" />
          </div>
          <div>
            <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--gray-800)' }}>Délibération active</div>
            <div style={{ fontSize: 12, color: 'var(--gray-400)', marginTop: 1 }}>Seules les délibérations "en cours" sont disponibles</div>
          </div>
        </div>
        <div className="card-padded">
          <div className="form-group" style={{ marginBottom: 0 }}>
            <label className="form-label">
              Choisir une délibération
            </label>
            <select
              className="form-control"
              value={delibId}
              onChange={e => chargerResultats(e.target.value)}
            >
              <option value="">-- Sélectionner une délibération --</option>
              {delibs.map(d => (
                <option key={d.id} value={d.id}>
                  S{d.semestre} — {d.niveau} — {d.session} — {d.annee_universitaire}
                  {d.nb_etudiants ? ` (${d.nb_etudiants} étud.)` : ''}
                </option>
              ))}
            </select>
            {delibs.length === 0 && (
              <span className="form-hint" style={{ color: 'var(--warning)' }}>
                Aucune délibération "en cours". Créez-en une depuis la page Délibérations.
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Contenu principal : liste étudiants + formulaire */}
      {delibId && (
        <div style={{
          display: 'grid',
          gridTemplateColumns: selected ? '280px 1fr' : '1fr',
          gap: 20,
          alignItems: 'start',
        }}>

          {/* ── Liste des étudiants ── */}
          <div className="card fade-up" style={{ animationDelay: '80ms' }}>
            <div className="card-header">
              <span className="card-title" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <Users size={15} color="var(--blue)" />
                Étudiants
              </span>
              <span className="badge badge-navy">{resultats.length}</span>
            </div>

            {loadingRes ? (
              <div className="card-body">
                {[1, 2, 3, 4].map(i => (
                  <div key={i} className="skeleton"
                    style={{ height: 46, marginBottom: 8, borderRadius: 6 }} />
                ))}
              </div>
            ) : resultats.length === 0 ? (
              <div className="card-body">
                <div className="empty-state" style={{ padding: '24px 12px' }}>
                  <div className="empty-state-icon"><BookOpen size={26} /></div>
                  <p style={{ fontSize: 13 }}>
                    Aucun étudiant dans cette délibération
                  </p>
                </div>
              </div>
            ) : (
              <div>
                {resultats.map((r, i) => {
                  const moy     = r.moyenne_annuelle ? parseFloat(r.moyenne_annuelle) : null
                  const isActive = selected?.id === r.id
                  return (
                    <div
                      key={r.id}
                      onClick={() => selectionnerEtudiant(r)}
                      style={{
                        display: 'flex', alignItems: 'center', gap: 10,
                        padding: '11px 16px', cursor: 'pointer',
                        borderBottom: i < resultats.length - 1 ? '1px solid var(--gray-100)' : 'none',
                        background: isActive ? 'var(--info-bg)' : 'white',
                        borderLeft: isActive ? '3px solid var(--blue)' : '3px solid transparent',
                        transition: 'all .12s',
                      }}
                      onMouseEnter={e => { if (!isActive) e.currentTarget.style.background = 'var(--gray-50)' }}
                      onMouseLeave={e => { if (!isActive) e.currentTarget.style.background = 'white' }}
                    >
                      {/* Avatar avec moyenne */}
                      <div style={{
                        width: 36, height: 36, borderRadius: '50%', flexShrink: 0,
                        background: moy != null
                          ? (moy >= 10 ? 'var(--success-bg)' : 'var(--danger-bg)')
                          : 'var(--gray-100)',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        fontSize: 11, fontWeight: 700,
                        color: moy != null
                          ? (moy >= 10 ? 'var(--success)' : 'var(--danger)')
                          : 'var(--gray-400)',
                      }}>
                        {moy != null ? moy.toFixed(1) : '—'}
                      </div>
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--gray-800)' }}>
                          {nomsMap[r.etudiant_id] || `Étudiant #${r.etudiant_id}`}
                        </div>
                        <div style={{ fontSize: 11, color: 'var(--gray-400)', marginTop: 1 }}>
                          {r.notes?.length || 0} note(s) saisie(s)
                        </div>
                      </div>
                      <span className={`badge badge-${
                        r.decision === 'admis'      ? 'success' :
                        r.decision === 'rattrapage' ? 'warning' :
                        r.decision === 'ajourné'   ? 'danger'  : 'neutral'
                      }`} style={{ fontSize: 10 }}>
                        {r.decision}
                      </span>
                    </div>
                  )
                })}
              </div>
            )}
          </div>

          {/* ── Formulaire saisie + notes existantes ── */}
          {selected && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>

              {/* Formulaire de saisie */}
              <div className="card fade-in">
                {/* ── En-tête gradient étudiant ── */}
              <div style={{
                background: 'linear-gradient(135deg, #1565c0 0%, #1e40af 100%)',
                padding: '18px 22px',
                color: 'white',
                borderRadius: '10px 10px 0 0',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  {/* Avatar initiales */}
                  <div style={{
                    width: 48, height: 48, borderRadius: 12, flexShrink: 0,
                    background: 'rgba(255,255,255,.18)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: 16, fontWeight: 800,
                  }}>
                    {(() => {
                      const nm = nomsMap[selected.etudiant_id] || ''
                      const parts = nm.trim().split(' ').filter(Boolean)
                      return parts.length >= 2
                        ? (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
                        : nm.length >= 2 ? nm.slice(0, 2).toUpperCase() : <GraduationCap size={20} />
                    })()}
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: 16, fontWeight: 700, lineHeight: 1.3 }}>
                      {nomsMap[selected.etudiant_id] || `Étudiant #${selected.etudiant_id}`}
                    </div>
                    <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginTop: 5 }}>
                      {(() => {
                        const delib = delibs.find(d => d.id == delibId)
                        return delib ? [
                          `Semestre ${delib.semestre}`, delib.niveau, `Session ${delib.session}`,
                        ].map(t => (
                          <span key={t} style={{
                            padding: '2px 9px', borderRadius: 20,
                            background: 'rgba(255,255,255,.15)', fontSize: 11, fontWeight: 500,
                          }}>{t}</span>
                        )) : null
                      })()}
                    </div>
                  </div>
                  {/* Aperçu note */}
                  {noteCalc && (
                    <div style={{
                      background: 'rgba(255,255,255,.15)', borderRadius: 10,
                      padding: '8px 14px', textAlign: 'center', flexShrink: 0,
                    }}>
                      <div style={{ fontSize: 10, opacity: .75, textTransform: 'uppercase', letterSpacing: '.06em', marginBottom: 2 }}>Aperçu</div>
                      <div style={{ fontSize: 20, fontWeight: 800, lineHeight: 1 }}>
                        {noteCalc}<span style={{ fontSize: 12, opacity: .7 }}>/20</span>
                      </div>
                      <div style={{ fontSize: 10, marginTop: 3, opacity: .8 }}>
                        {parseFloat(noteCalc) >= 10 ? '✓ Validée' : '✗ Non val.'}
                      </div>
                    </div>
                  )}
                </div>
              </div>
                <div className="card-body">

                  {/* Sélection UE */}
                  {loadingUes ? (
                    <div className="form-group" style={{ marginBottom: 16 }}>
                      <label className="form-label" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                        <Search size={13} color="var(--blue)" />
                        Unité d'enseignement <span style={{ color: 'var(--danger)' }}>*</span>
                      </label>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '10px 14px', borderRadius: 8, background: 'var(--gray-50)', border: '1px solid var(--gray-200)' }}>
                        <div className="spinner spinner-sm" />
                        <span style={{ fontSize: 13, color: 'var(--gray-500)' }}>Chargement des matières…</span>
                      </div>
                    </div>
                  ) : ues.length > 0 ? (
                    <div className="form-group" style={{ position: 'relative', marginBottom: 16 }}>
                      <label className="form-label" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                        <Search size={13} color="var(--blue)" />
                        Unité d'enseignement
                        <span style={{ color: 'var(--danger)' }}>*</span>
                      </label>
                      <div style={{ position: 'relative' }}>
                        <input
                          className="form-control"
                          placeholder="Rechercher une UE par code ou intitulé…"
                          value={ueSearch}
                          onChange={e => { setUeSearch(e.target.value); setShowUeDropdown(true) }}
                          onFocus={() => setShowUeDropdown(true)}
                          onBlur={() => setTimeout(() => setShowUeDropdown(false), 150)}
                          style={{ paddingRight: form.ue_id ? 36 : 12 }}
                        />
                        {form.ue_id && (
                          <button
                            type="button"
                            onClick={() => {
                              setUeSearch('')
                              setForm(f => ({
                                ...f,
                                ue_id: '', code_ue: '', libelle_ue: '',
                                credit_ue: 3, coefficient_ue: 1, semestre: 1,
                              }))
                            }}
                            style={{
                              position: 'absolute', right: 10, top: '50%', transform: 'translateY(-50%)',
                              background: 'none', border: 'none', cursor: 'pointer',
                              color: 'var(--gray-400)', display: 'flex', padding: 2,
                            }}
                          >
                            <X size={14} />
                          </button>
                        )}
                      </div>
                      {/* UE sélectionnée — badge */}
                      {form.ue_id && (
                        <div style={{
                          marginTop: 6, padding: '8px 12px', borderRadius: 8,
                          background: '#e8f0fe', border: '1px solid #c5d8fb',
                          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                        }}>
                          <div>
                            <span style={{ fontWeight: 700, fontSize: 13, color: 'var(--blue)' }}>
                              {form.code_ue}
                            </span>
                            <span style={{ fontSize: 12, color: 'var(--gray-600)', marginLeft: 8 }}>
                              {form.libelle_ue}
                            </span>
                          </div>
                          <div style={{ display: 'flex', gap: 6 }}>
                            <span style={{ fontSize: 11, color: 'var(--gray-500)' }}>
                              {form.credit_ue} créd. &bull; Coef. {form.coefficient_ue} &bull; S{form.semestre}
                            </span>
                          </div>
                        </div>
                      )}
                      {/* Dropdown */}
                      {showUeDropdown && filteredUes.length > 0 && (
                        <div style={{
                          position: 'absolute', top: '100%', left: 0, right: 0, zIndex: 50,
                          background: 'white', border: '1px solid var(--gray-200)',
                          borderRadius: 8, boxShadow: '0 4px 16px rgba(0,0,0,.12)',
                          maxHeight: 240, overflowY: 'auto', marginTop: 2,
                        }}>
                          {filteredUes.map((u, i) => {
                            const noteExistante = notes.find(n => n.ue_id === u.id)
                            return (
                            <button
                              key={u.id}
                              type="button"
                              onMouseDown={() => {
                                setForm(f => ({
                                  ...f,
                                  ue_id          : u.id,
                                  code_ue        : u.code_ue,
                                  libelle_ue     : u.libelle_ue,
                                  credit_ue      : u.credit,
                                  coefficient_ue : u.coefficient,
                                  semestre       : u.semestre,
                                  // Pré-remplir avec les notes déjà saisies si elles existent
                                  note_cc        : noteExistante ? (noteExistante.note_cc        ?? '') : '',
                                  note_tp        : noteExistante ? (noteExistante.note_tp        ?? '') : '',
                                  note_examen    : noteExistante ? (noteExistante.note_examen    ?? '') : '',
                                  note_rattrapage: noteExistante ? (noteExistante.note_rattrapage ?? '') : '',
                                }))
                                setUeSearch(`${u.code_ue} — ${u.libelle_ue}`)
                                setShowUeDropdown(false)
                              }}
                              style={{
                                width: '100%', textAlign: 'left', background: 'none',
                                border: 'none', padding: '10px 14px', cursor: 'pointer',
                                borderBottom: i < filteredUes.length - 1 ? '1px solid var(--gray-100)' : 'none',
                                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                                gap: 10,
                              }}
                              onMouseEnter={e => { e.currentTarget.style.background = 'var(--gray-50)' }}
                              onMouseLeave={e => { e.currentTarget.style.background = 'none' }}
                            >
                              <div style={{ flex: 1, minWidth: 0 }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                                  <span style={{ fontWeight: 700, fontSize: 13, color: 'var(--gray-800)' }}>
                                    {u.code_ue}
                                  </span>
                                  {noteExistante && (
                                    <span style={{
                                      fontSize: 10, padding: '1px 7px', borderRadius: 10,
                                      background: 'var(--success-bg)', color: 'var(--success)',
                                      fontWeight: 600,
                                    }}>
                                      ✓ {noteExistante.note_finale ?? '—'}/20
                                    </span>
                                  )}
                                </div>
                                <div style={{ fontSize: 12, color: 'var(--gray-500)', marginTop: 1 }}>
                                  {u.libelle_ue}
                                </div>
                              </div>
                              <div style={{ textAlign: 'right', flexShrink: 0 }}>
                                <div style={{ fontSize: 11, color: 'var(--gray-400)' }}>
                                  {u.credit} créd. &bull; Coef.{u.coefficient}
                                </div>
                                <div style={{ fontSize: 11, color: 'var(--gray-300)', marginTop: 1 }}>
                                  Semestre {u.semestre}
                                </div>
                              </div>
                            </button>
                          )})}
                        </div>
                      )}
                    </div>
                  ) : (
                    /* Mode manuel si UEs non disponibles */
                    <div className="grid-2">
                      <div className="form-group">
                        <label className="form-label">ID UE *</label>
                        <input
                          className="form-control"
                          type="number"
                          placeholder="ex: 5"
                          value={form.ue_id}
                          onChange={e => setForm(f => ({ ...f, ue_id: e.target.value }))}
                        />
                        <span className="form-hint">ID de l'UE dans le service dossier</span>
                      </div>
                      <div className="form-group">
                        <label className="form-label">Code UE</label>
                        <input
                          className="form-control"
                          placeholder="ex: INF401"
                          value={form.code_ue}
                          onChange={e => setForm(f => ({ ...f, code_ue: e.target.value }))}
                        />
                      </div>
                    </div>
                  )}

                  {/* Informations UE complémentaires (rééditables) */}
                  {!ues.length && !loadingUes && (
                    <>
                      <div className="form-group">
                        <label className="form-label">Intitulé de l'UE</label>
                        <input
                          className="form-control"
                          placeholder="ex: Bases de données avancées"
                          value={form.libelle_ue}
                          onChange={e => setForm(f => ({ ...f, libelle_ue: e.target.value }))}
                        />
                      </div>

                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 10 }}>
                        <div className="form-group">
                          <label className="form-label">Crédits</label>
                          <input
                            className="form-control"
                            type="number" min="1" max="10"
                            value={form.credit_ue}
                            onChange={e => setForm(f => ({ ...f, credit_ue: e.target.value }))}
                          />
                        </div>
                        <div className="form-group">
                          <label className="form-label">Coefficient</label>
                          <input
                            className="form-control"
                            type="number" step="0.5" min="0.5" max="5"
                            value={form.coefficient_ue}
                            onChange={e => setForm(f => ({ ...f, coefficient_ue: e.target.value }))}
                          />
                        </div>
                        <div className="form-group">
                          <label className="form-label">Semestre</label>
                          <select
                            className="form-control"
                            value={form.semestre}
                            onChange={e => setForm(f => ({ ...f, semestre: e.target.value }))}
                          >
                            {[1, 2, 3, 4].map(s => <option key={s} value={s}>S{s}</option>)}
                          </select>
                        </div>
                      </div>
                    </>
                  )}

                  {/* Bloc notes */}
                  <div style={{
                    background: 'var(--gray-50)', borderRadius: 10,
                    padding: '14px 16px', marginBottom: 14,
                    border: '1px solid var(--gray-200)',
                  }}>
                    <div style={{
                      display: 'flex', alignItems: 'center', gap: 6,
                      fontSize: 11, fontWeight: 700, color: 'var(--gray-500)',
                      textTransform: 'uppercase', letterSpacing: '.05em', marginBottom: 12,
                    }}>
                      <BookOpen size={13} />
                      Notes d'évaluation
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 10, marginBottom: 10 }}>
                      {[
                        { key: 'note_cc',     label: 'CC (30%)',    ph: '0 — 20' },
                        { key: 'note_tp',     label: 'TP (20%)',    ph: '0 — 20' },
                        { key: 'note_examen', label: 'Examen (50%)',ph: '0 — 20' },
                      ].map(f2 => (
                        <div key={f2.key} className="form-group" style={{ marginBottom: 0 }}>
                          <label className="form-label" style={{ fontSize: 11 }}>{f2.label}</label>
                          <input
                            className="form-control"
                            type="number" step="0.25" min="0" max="20"
                            placeholder={f2.ph}
                            value={form[f2.key]}
                            onChange={e => setForm(f => ({ ...f, [f2.key]: e.target.value }))}
                            style={{
                              borderColor: form[f2.key] !== ''
                                ? (parseFloat(form[f2.key]) >= 10 ? 'var(--success)' : 'var(--danger)')
                                : undefined,
                            }}
                          />
                        </div>
                      ))}
                    </div>

                    <div className="form-group" style={{ marginBottom: 0 }}>
                      <label className="form-label" style={{ fontSize: 11 }}>
                        Note de rattrapage (session de rattrapage uniquement)
                      </label>
                      <input
                        className="form-control"
                        type="number" step="0.25" min="0" max="20"
                        placeholder="0 — 20"
                        value={form.note_rattrapage}
                        onChange={e => setForm(f => ({ ...f, note_rattrapage: e.target.value }))}
                      />
                    </div>

                    {/* Aperçu note calculée */}
                    {noteCalc && (
                      <div style={{
                        marginTop: 12, padding: '10px 12px', borderRadius: 8,
                        display: 'flex', alignItems: 'center', gap: 8,
                        background: parseFloat(noteCalc) >= 10
                          ? 'var(--success-bg)' : 'var(--danger-bg)',
                      }}>
                        {parseFloat(noteCalc) >= 10
                          ? <CheckCircle size={14} color="var(--success)" />
                          : <AlertCircle size={14} color="var(--danger)" />}
                        <span style={{
                          fontSize: 13, fontWeight: 700,
                          color: parseFloat(noteCalc) >= 10 ? 'var(--success)' : 'var(--danger)',
                        }}>
                          Note finale calculée : {noteCalc}/20
                          {parseFloat(noteCalc) >= 10 ? ' — Validée ✓' : ' — Non validée ✗'}
                        </span>
                      </div>
                    )}
                  </div>

                  <button
                    className="btn btn-primary btn-block"
                    onClick={saisirNote}
                    disabled={saving}
                  >
                    {saving
                      ? <div className="spinner" />
                      : <><Save size={15} /> Enregistrer la note</>}
                  </button>
                </div>
              </div>

              {/* Notes existantes pour cet étudiant */}
              <div className="card fade-in">
                <div className="card-header">
                  <span className="card-title" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <CheckCircle size={15} color="var(--success)" />
                    Notes déjà saisies
                  </span>
                  <span className="badge badge-navy">{notes.length} UE(s)</span>
                </div>

                {loading ? (
                  <div className="card-body">
                    {[1, 2].map(i => (
                      <div key={i} className="skeleton"
                        style={{ height: 40, marginBottom: 8, borderRadius: 6 }} />
                    ))}
                  </div>
                ) : notes.length === 0 ? (
                  <div className="card-body">
                    <div className="empty-state" style={{ padding: '20px 12px' }}>
                      <p style={{ fontSize: 12, color: 'var(--gray-400)' }}>
                        Aucune note saisie pour cet étudiant
                      </p>
                    </div>
                  </div>
                ) : (
                  <>
                    <div className="table-wrap">
                      <table>
                        <thead>
                          <tr>
                            <th>UE</th>
                            <th>CC</th>
                            <th>TP</th>
                            <th>Exam</th>
                            <th>Finale</th>
                            <th>Créd.</th>
                            <th>Statut</th>
                          </tr>
                        </thead>
                        <tbody>
                          {notes.map(n => (
                            <tr key={n.id}>
                              <td>
                                <div style={{ fontWeight: 600, fontSize: 12 }}>
                                  {n.code_ue || `UE #${n.ue_id}`}
                                </div>
                                {n.libelle_ue && (
                                  <div style={{ fontSize: 10, color: 'var(--gray-400)', marginTop: 1 }}>
                                    {n.libelle_ue}
                                  </div>
                                )}
                              </td>
                              <td style={{ fontSize: 12 }}>
                                {n.note_cc != null ? parseFloat(n.note_cc).toFixed(1) : '—'}
                              </td>
                              <td style={{ fontSize: 12 }}>
                                {n.note_tp != null ? parseFloat(n.note_tp).toFixed(1) : '—'}
                              </td>
                              <td style={{ fontSize: 12 }}>
                                {n.note_examen != null ? parseFloat(n.note_examen).toFixed(1) : '—'}
                              </td>
                              <td>
                                <strong style={{
                                  color: n.valeur && parseFloat(n.valeur) >= 10
                                    ? 'var(--success)' : 'var(--danger)',
                                }}>
                                  {n.valeur ? `${parseFloat(n.valeur).toFixed(2)}/20` : '—'}
                                </strong>
                              </td>
                              <td style={{ fontSize: 12 }}>{n.credit_ue}</td>
                              <td>
                                <span className={`badge badge-${n.est_validee ? 'success' : 'danger'}`}
                                  style={{ fontSize: 10 }}>
                                  {n.est_validee ? 'Validée' : 'Non val.'}
                                </span>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>

                    {/* Résumé moyenne actuelle */}
                    <div style={{
                      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                      padding: '12px 18px', borderTop: '1px solid var(--gray-100)',
                    }}>
                      <div>
                        <div style={{ fontSize: 12, color: 'var(--gray-400)', fontWeight: 500 }}>
                          Moyenne actuelle (calculée automatiquement)
                        </div>
                        <div style={{ fontSize: 11, color: 'var(--gray-300)', marginTop: 2 }}>
                          Décision : <span style={{ fontWeight: 600, color: 'var(--gray-600)' }}>
                            {selected.decision}
                          </span>
                        </div>
                      </div>
                      <span style={{
                        fontSize: 20, fontWeight: 800,
                        color: selected.moyenne_annuelle && parseFloat(selected.moyenne_annuelle) >= 10
                          ? 'var(--success)' : 'var(--danger)',
                      }}>
                        {selected.moyenne_annuelle
                          ? `${parseFloat(selected.moyenne_annuelle).toFixed(2)}/20`
                          : '—/20'}
                      </span>
                    </div>
                  </>
                )}
              </div>

            </div>
          )}

          {/* Message si aucun étudiant sélectionné */}
          {!selected && resultats.length > 0 && (
            <div className="card" style={{
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              minHeight: 200, color: 'var(--gray-300)',
            }}>
              <div style={{ textAlign: 'center' }}>
                <BookOpen size={36} style={{ marginBottom: 12, opacity: .4 }} />
                <p style={{ fontSize: 13 }}>
                  Sélectionnez un étudiant à gauche<br />pour saisir ses notes
                </p>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
