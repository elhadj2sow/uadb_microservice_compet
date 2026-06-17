import { useState, useEffect, useCallback } from 'react'
import { BookOpen, Plus, Edit2, ChevronDown, ChevronRight, X, Save, Trash2 } from 'lucide-react'
import api, { BASE } from '../../config/api'

const NIVEAUX = ['L1','L2','L3','M1','M2','Doctorat']
const TYPES_UE = ['obligatoire','optionnel','libre']
const UE_VIDE  = { code_ue:'', libelle_ue:'', semestre:1, credit:3, coefficient:1.0, type_ue:'obligatoire', volume_horaire:'' }

function Modal({ title, onClose, children }) {
  return (
    <div style={{
      position:'fixed', inset:0, background:'rgba(0,0,0,.65)',
      display:'flex', alignItems:'center', justifyContent:'center', zIndex:1000,
      backdropFilter:'blur(3px)'
    }}>
      <div style={{
        background:'#ffffff',
        borderRadius:'12px',
        padding:'1.75rem 2rem',
        width:'min(560px,92vw)',
        maxHeight:'90vh',
        overflowY:'auto',
        boxShadow:'0 20px 60px rgba(0,0,0,.35), 0 0 0 1px rgba(0,0,0,.08)',
        border:'1px solid #e5e7eb'
      }}>
        <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:'1.25rem', paddingBottom:'.875rem', borderBottom:'1px solid #f0f0f0' }}>
          <h3 style={{ margin:0, fontSize:'1.05rem', fontWeight:700, color:'#111827' }}>{title}</h3>
          <button className="btn-icon" onClick={onClose}><X size={18}/></button>
        </div>
        {children}
      </div>
    </div>
  )
}

const FORM_VIDE = { code_formation:'', libelle:'', niveau:'L1', specialite:'', departement:'', credits_total:60, duree_semestres:6 }

export default function GestionFormations() {
  const [formations, setFormations] = useState([])
  const [loading,    setLoading]    = useState(true)
  const [expanded,   setExpanded]   = useState({}) // { [id]: true/false }
  const [ues,        setUes]        = useState({}) // { [id]: [] }
  const [loadingUes, setLoadingUes] = useState({})
  const [modal,      setModal]      = useState(null) // null | { mode: 'creer'|'modifier', ... }
  const [form,       setForm]       = useState(FORM_VIDE)
  const [saving,     setSaving]     = useState(false)
  const [msg,        setMsg]        = useState(null)
  // UE modal
  const [modalUe,   setModalUe]   = useState(null) // null | { mode:'creer'|'modifier', formationId, ueId? }
  const [formUe,    setFormUe]    = useState(UE_VIDE)
  const [savingUe,  setSavingUe]  = useState(false)

  const flashMsg = (type, text) => {
    setMsg({ type, text })
    setTimeout(() => setMsg(null), 5000)
  }

  const chargerFormations = useCallback(() => {
    setLoading(true)
    // On charge toutes les formations (actives + inactives) — l'admin a besoin de voir toutes
    api.get(`${BASE.formation}/`)
      .then(r => setFormations(r.data.results || []))
      .catch(() => flashMsg('error', 'Erreur chargement des formations.'))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => { chargerFormations() }, [chargerFormations])

  const toggleUes = async (id) => {
    if (expanded[id]) {
      setExpanded(p => ({ ...p, [id]: false }))
      return
    }
    setExpanded(p => ({ ...p, [id]: true }))
    if (ues[id]) return
    setLoadingUes(p => ({ ...p, [id]: true }))
    try {
      const r = await api.get(`${BASE.formation}/${id}/ues/`)
      setUes(p => ({ ...p, [id]: r.data.ues || [] }))
    } catch {
      setUes(p => ({ ...p, [id]: [] }))
    } finally {
      setLoadingUes(p => ({ ...p, [id]: false }))
    }
  }

  const ouvrirCreer = () => {
    setForm(FORM_VIDE)
    setModal({ mode: 'creer' })
  }

  const ouvrirModifier = async (f) => {
    // Récupérer le détail complet (FormationListSerializer n'a pas departement/duree_semestres)
    try {
      const r = await api.get(`${BASE.formation}/${f.id}/`)
      const full = r.data
      setForm({
        code_formation  : full.code_formation || '',
        libelle         : full.libelle || '',
        niveau          : full.niveau || 'L1',
        specialite      : full.specialite || '',
        departement     : full.departement || '',
        credits_total   : full.credits_total || 60,
        duree_semestres : full.duree_semestres || 6,
      })
    } catch {
      // Fallback sur les données de la liste
      setForm({
        code_formation  : f.code_formation || '',
        libelle         : f.libelle || '',
        niveau          : f.niveau || 'L1',
        specialite      : f.specialite || '',
        departement     : f.departement || '',
        credits_total   : f.credits_total || 60,
        duree_semestres : f.duree_semestres || 6,
      })
    }
    setModal({ mode: 'modifier', id: f.id })
  }

  const sauvegarder = async () => {
    if (!form.libelle.trim() || !form.code_formation.trim()) {
      flashMsg('error', 'Le code et le libellé sont obligatoires.')
      return
    }
    setSaving(true)
    try {
      if (modal.mode === 'creer') {
        await api.post(`${BASE.formation}/creer/`, form)
        flashMsg('success', `Formation "${form.libelle}" créée.`)
      } else {
        await api.patch(`${BASE.formation}/${modal.id}/modifier/`, form)
        flashMsg('success', `Formation "${form.libelle}" mise à jour.`)
      }
      setModal(null)
      chargerFormations()
    } catch (e) {
      const errs = e.response?.data
      const msg  = errs ? Object.values(errs).flat().join(' ') : 'Erreur lors de la sauvegarde.'
      flashMsg('error', msg)
    } finally {
      setSaving(false)
    }
  }

  const rechargerUes = async (formationId) => {
    setLoadingUes(p => ({ ...p, [formationId]: true }))
    try {
      const r = await api.get(`${BASE.formation}/${formationId}/ues/`)
      setUes(p => ({ ...p, [formationId]: r.data.ues || [] }))
    } catch {
      setUes(p => ({ ...p, [formationId]: [] }))
    } finally {
      setLoadingUes(p => ({ ...p, [formationId]: false }))
    }
  }

  const ouvrirAjouterUe = (formationId) => {
    setFormUe(UE_VIDE)
    setModalUe({ mode: 'creer', formationId })
  }

  const ouvrirModifierUe = (formationId, ue) => {
    setFormUe({
      code_ue       : ue.code_ue || '',
      libelle_ue    : ue.libelle_ue || '',
      semestre      : ue.semestre || 1,
      credit        : ue.credit ?? 3,
      coefficient   : ue.coefficient ?? 1.0,
      type_ue       : ue.type_ue || 'obligatoire',
      volume_horaire: ue.volume_horaire ?? '',
    })
    setModalUe({ mode: 'modifier', formationId, ueId: ue.id })
  }

  const supprimerUe = async (formationId, ueId) => {
    if (!window.confirm('Supprimer cette UE ?')) return
    try {
      await api.delete(`${BASE.formation}/${formationId}/ues/${ueId}/supprimer/`)
      flashMsg('success', 'UE supprimée.')
      rechargerUes(formationId)
    } catch {
      flashMsg('error', 'Erreur lors de la suppression.')
    }
  }

  const sauvegarderUe = async () => {
    if (!formUe.code_ue.trim() || !formUe.libelle_ue.trim()) {
      flashMsg('error', 'Le code et le libellé UE sont obligatoires.')
      return
    }
    setSavingUe(true)
    const { formationId, ueId } = modalUe
    try {
      if (modalUe.mode === 'creer') {
        await api.post(`${BASE.formation}/${formationId}/ues/creer/`, formUe)
        flashMsg('success', `UE "${formUe.libelle_ue}" ajoutée.`)
      } else {
        await api.patch(`${BASE.formation}/${formationId}/ues/${ueId}/modifier/`, formUe)
        flashMsg('success', `UE "${formUe.libelle_ue}" mise à jour.`)
      }
      setModalUe(null)
      rechargerUes(formationId)
    } catch (e) {
      const errs = e.response?.data
      const errMsg = errs ? Object.values(errs).flat().join(' ') : 'Erreur lors de la sauvegarde.'
      flashMsg('error', errMsg)
    } finally {
      setSavingUe(false)
    }
  }

  return (
    <div className="page-content">
      {/* Header */}
      <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:'1.5rem' }}>
        <div style={{ display:'flex', alignItems:'center', gap:'.75rem' }}>
          <BookOpen size={24} style={{ color:'var(--blue)' }}/>
          <div>
            <h1 className="page-title" style={{ margin:0 }}>Référentiel des formations</h1>
            <p className="page-subtitle" style={{ margin:0 }}>Formations et unités d'enseignement</p>
          </div>
        </div>
        <button className="btn btn-primary" onClick={ouvrirCreer}>
          <Plus size={16}/> Nouvelle formation
        </button>
      </div>

      {/* Message flash */}
      {msg && (
        <div className={`alert alert-${msg.type === 'error' ? 'danger' : 'success'}`}
             style={{ marginBottom:'1rem' }}>
          {msg.text}
        </div>
      )}

      {/* Liste des formations */}
      {loading ? (
        <div style={{ textAlign:'center', padding:'3rem' }}><div className="spinner spinner-dark"/></div>
      ) : formations.length === 0 ? (
        <div className="card" style={{ padding:'2.5rem', textAlign:'center', color:'var(--muted)' }}>
          Aucune formation enregistrée. <br/>
          <button className="btn btn-primary" style={{ marginTop:'1rem' }} onClick={ouvrirCreer}>
            <Plus size={16}/> Créer la première formation
          </button>
        </div>
      ) : (
        <div style={{ display:'flex', flexDirection:'column', gap:'.75rem' }}>
          {formations.map(f => (
            <div key={f.id} className="card" style={{ overflow:'hidden' }}>
              {/* Formation header */}
              <div style={{ padding:'1rem 1.25rem', display:'flex', justifyContent:'space-between', alignItems:'center' }}>
                <div style={{ display:'flex', alignItems:'center', gap:'.75rem', flex:1 }}>
                  <button
                    className="btn-icon"
                    onClick={() => toggleUes(f.id)}
                    style={{ flexShrink:0 }}
                    title="Voir les UE"
                  >
                    {expanded[f.id] ? <ChevronDown size={18}/> : <ChevronRight size={18}/>}
                  </button>
                  <div style={{ flex:1 }}>
                    <div style={{ display:'flex', alignItems:'center', gap:'.5rem', flexWrap:'wrap' }}>
                      <strong>{f.libelle}</strong>
                      <span className="badge badge-info">{f.code_formation}</span>
                      <span className="badge badge-neutral">{f.niveau}</span>
                    </div>
                    {(f.specialite || f.departement) && (
                        <div style={{ fontSize:'.8rem', color:'var(--muted)', marginTop:'.2rem' }}>
                          {f.specialite || f.departement}
                          {f.duree_semestres && ` · ${f.duree_semestres} semestre(s)`}
                          {f.credits_total && ` · ${f.credits_total} crédits`}
                      </div>
                    )}
                  </div>
                </div>
                <button
                  className="btn btn-secondary btn-sm"
                  onClick={() => ouvrirModifier(f)}
                  style={{ flexShrink:0, marginLeft:'.75rem' }}
                >
                  <Edit2 size={14}/> Modifier
                </button>
              </div>

              {/* UE accordéon */}
              {expanded[f.id] && (
                <div style={{ borderTop:'1px solid var(--border)', background:'var(--bg-subtle, #f8f9fa)' }}>
                  {loadingUes[f.id] ? (
                    <div style={{ padding:'1rem', textAlign:'center' }}><div className="spinner spinner-dark" style={{ width:20, height:20 }}/></div>
                  ) : (
                    <>
                      {(!ues[f.id] || ues[f.id].length === 0) ? (
                        <div style={{ padding:'1rem 1.5rem', color:'var(--muted)', fontSize:'.875rem' }}>
                          Aucune UE enregistrée pour cette formation.
                        </div>
                      ) : (
                        <table className="table" style={{ margin:0 }}>
                          <thead>
                            <tr>
                              <th>Code</th>
                              <th>Libellé</th>
                              <th>Semestre</th>
                              <th>Type</th>
                              <th>Crédits</th>
                              <th>Coeff.</th>
                              <th>V.H.</th>
                              <th style={{ width:90 }}>Actions</th>
                            </tr>
                          </thead>
                          <tbody>
                            {ues[f.id].map(ue => (
                              <tr key={ue.id}>
                                <td><code style={{ fontSize:'.8rem' }}>{ue.code_ue}</code></td>
                                <td>{ue.libelle_ue}</td>
                                <td><span className="badge badge-neutral">S{ue.semestre}</span></td>
                                <td><span className="badge badge-info">{ue.type_ue}</span></td>
                                <td>{ue.credit ?? '—'}</td>
                                <td>{ue.coefficient ?? '—'}</td>
                                <td>{ue.volume_horaire ?? '—'}</td>
                                <td>
                                  <div style={{ display:'flex', gap:'.25rem' }}>
                                    <button className="btn-icon" title="Modifier"
                                      onClick={() => ouvrirModifierUe(f.id, ue)}>
                                      <Edit2 size={13}/>
                                    </button>
                                    <button className="btn-icon" title="Supprimer"
                                      style={{ color:'var(--danger, #dc2626)' }}
                                      onClick={() => supprimerUe(f.id, ue.id)}>
                                      <Trash2 size={13}/>
                                    </button>
                                  </div>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      )}
                      <div style={{ padding:'.625rem 1rem', borderTop: ues[f.id]?.length ? '1px solid var(--border)' : 'none' }}>
                        <button className="btn btn-secondary btn-sm" onClick={() => ouvrirAjouterUe(f.id)}>
                          <Plus size={13}/> Ajouter une UE
                        </button>
                      </div>
                    </>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Modal création / modification */}
      {modal && (
        <Modal
          title={modal.mode === 'creer' ? 'Nouvelle formation' : 'Modifier la formation'}
          onClose={() => setModal(null)}
        >
          <div style={{ display:'flex', flexDirection:'column', gap:'1rem' }}>
            <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:'1rem' }}>
              <div>
                <label className="form-label">Code formation <span style={{ color:'red' }}>*</span></label>
                <input className="form-control" value={form.code_formation}
                  onChange={e => setForm(p => ({ ...p, code_formation: e.target.value }))}
                  placeholder="ex: L1-INFO"/>
              </div>
              <div>
                <label className="form-label">Niveau <span style={{ color:'red' }}>*</span></label>
                <select className="form-control" value={form.niveau}
                  onChange={e => setForm(p => ({ ...p, niveau: e.target.value }))}>
                  {NIVEAUX.map(n => <option key={n} value={n}>{n}</option>)}
                </select>
              </div>
            </div>
            <div>
              <label className="form-label">Libellé <span style={{ color:'red' }}>*</span></label>
              <input className="form-control" value={form.libelle}
                onChange={e => setForm(p => ({ ...p, libelle: e.target.value }))}
                placeholder="ex: Licence 1 Informatique"/>
            </div>
            <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:'1rem' }}>
              <div>
                <label className="form-label">Spécialité</label>
                <input className="form-control" value={form.specialite}
                  onChange={e => setForm(p => ({ ...p, specialite: e.target.value }))}
                  placeholder="ex: Informatique"/>
              </div>
              <div>
                <label className="form-label">Département</label>
                <input className="form-control" value={form.departement}
                  onChange={e => setForm(p => ({ ...p, departement: e.target.value }))}
                  placeholder="ex: Sciences & Technologies"/>
              </div>
            </div>
            <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:'1rem' }}>
              <div>
                <label className="form-label">Crédits total</label>
                <input className="form-control" type="number" min={0}
                  value={form.credits_total}
                  onChange={e => setForm(p => ({ ...p, credits_total: +e.target.value }))}/>
              </div>
              <div>
                <label className="form-label">Durée (semestres)</label>
                <input className="form-control" type="number" min={1} max={12}
                  value={form.duree_semestres}
                  onChange={e => setForm(p => ({ ...p, duree_semestres: +e.target.value }))}/>
              </div>
            </div>
          </div>
          <div style={{ display:'flex', gap:'.75rem', marginTop:'1.5rem' }}>
            <button className="btn btn-primary" disabled={saving} onClick={sauvegarder}>
              {saving ? <span className="spinner"/> : <><Save size={15}/> Enregistrer</>}
            </button>
            <button className="btn btn-secondary" onClick={() => setModal(null)}>Annuler</button>
          </div>
        </Modal>
      )}

      {/* Modal ajout / modification UE */}
      {modalUe && (
        <Modal
          title={modalUe.mode === 'creer' ? 'Ajouter une UE' : 'Modifier l\'UE'}
          onClose={() => setModalUe(null)}
        >
          <div style={{ display:'flex', flexDirection:'column', gap:'1rem' }}>
            <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:'1rem' }}>
              <div>
                <label className="form-label">Code UE <span style={{ color:'red' }}>*</span></label>
                <input className="form-control" value={formUe.code_ue}
                  onChange={e => setFormUe(p => ({ ...p, code_ue: e.target.value }))}
                  placeholder="ex: INF301"/>
              </div>
              <div>
                <label className="form-label">Semestre <span style={{ color:'red' }}>*</span></label>
                <input className="form-control" type="number" min={1} max={12}
                  value={formUe.semestre}
                  onChange={e => setFormUe(p => ({ ...p, semestre: +e.target.value }))}/>
              </div>
            </div>
            <div>
              <label className="form-label">Libellé <span style={{ color:'red' }}>*</span></label>
              <input className="form-control" value={formUe.libelle_ue}
                onChange={e => setFormUe(p => ({ ...p, libelle_ue: e.target.value }))}
                placeholder="ex: Algorithmique et structures de données"/>
            </div>
            <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr 1fr', gap:'1rem' }}>
              <div>
                <label className="form-label">Crédits</label>
                <input className="form-control" type="number" min={0}
                  value={formUe.credit}
                  onChange={e => setFormUe(p => ({ ...p, credit: +e.target.value }))}/>
              </div>
              <div>
                <label className="form-label">Coefficient</label>
                <input className="form-control" type="number" min={0} step={0.1}
                  value={formUe.coefficient}
                  onChange={e => setFormUe(p => ({ ...p, coefficient: +e.target.value }))}/>
              </div>
              <div>
                <label className="form-label">Volume horaire</label>
                <input className="form-control" type="number" min={0}
                  value={formUe.volume_horaire}
                  onChange={e => setFormUe(p => ({ ...p, volume_horaire: e.target.value ? +e.target.value : '' }))}
                  placeholder="heures"/>
              </div>
            </div>
            <div>
              <label className="form-label">Type</label>
              <select className="form-control" value={formUe.type_ue}
                onChange={e => setFormUe(p => ({ ...p, type_ue: e.target.value }))}>
                {TYPES_UE.map(t => <option key={t} value={t}>{t}</option>)}
              </select>
            </div>
          </div>
          <div style={{ display:'flex', gap:'.75rem', marginTop:'1.5rem' }}>
            <button className="btn btn-primary" disabled={savingUe} onClick={sauvegarderUe}>
              {savingUe ? <span className="spinner"/> : <><Save size={15}/> Enregistrer</>}
            </button>
            <button className="btn btn-secondary" onClick={() => setModalUe(null)}>Annuler</button>
          </div>
        </Modal>
      )}
    </div>
  )
}
