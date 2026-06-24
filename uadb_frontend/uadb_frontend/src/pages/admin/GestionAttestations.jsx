import { useState, useEffect, useCallback } from 'react'
import api, { BASE } from '../../config/api'
import { FileText, CheckCircle, XCircle, Eye, RefreshCw } from 'lucide-react'
import toast from 'react-hot-toast'

const STATUT_BADGE = {
  en_attente: 'warning',
  approuvee : 'info',
  generee   : 'success',
  refusee   : 'danger',
}

const TYPE_LABEL = {
  inscription  : "Attestation d'inscription",
  passage      : 'Attestation de passage',
  reussite     : 'Attestation de réussite',
  releve_notes : 'Relevé de notes',
  scolarite    : 'Certificat de scolarité',
}

export default function GestionAttestations() {
  const [demandes,   setDemandes]   = useState([])
  const [total,      setTotal]      = useState(0)
  const [loading,    setLoading]    = useState(true)
  const [usersMap,   setUsersMap]   = useState({})
  const [selected,   setSelected]   = useState(null)      // demande en détail
  const [rejet,      setRejet]      = useState(null)      // demande à refuser
  const [motifRejet, setMotifRejet] = useState('')
  const [saving,     setSaving]     = useState(false)

  const [filtreStatut, setFiltreStatut] = useState('')
  const [filtreType,   setFiltreType]   = useState('')

  // ── Chargement des demandes ───────────────────────────────────────────────
  const charger = useCallback(async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      if (filtreStatut) params.append('statut', filtreStatut)
      if (filtreType)   params.append('type',   filtreType)
      const r = await api.get(`${BASE.attestation}/admin/demandes/?${params}`)
      setDemandes(r.data.results || [])
      setTotal(r.data.count || 0)
    } catch {
      toast.error('Erreur lors du chargement des demandes.')
    } finally {
      setLoading(false)
    }
  }, [filtreStatut, filtreType])

  useEffect(() => { charger() }, [charger])

  // ── Résolution noms étudiants ─────────────────────────────────────────────
  useEffect(() => {
    api.get(`${BASE.auth}/utilisateurs/`)
      .then(r => {
        const map = {}
        ;(r.data.results || []).forEach(u => {
          map[u.id] = u.nom_complet || u.username
        })
        setUsersMap(map)
      })
      .catch(() => {})
  }, [])

  // ── Approuver ─────────────────────────────────────────────────────────────
  const approuver = async (demande) => {
    if (!window.confirm(`Approuver et générer l'attestation pour "${TYPE_LABEL[demande.type_attestation] || demande.type_attestation}" ?`)) return
    setSaving(true)
    try {
      await api.patch(`${BASE.attestation}/admin/demandes/${demande.id}/`, { action: 'approuver' })
      toast.success('Demande approuvée — attestation générée.')
      charger()
      if (selected?.id === demande.id) setSelected(null)
    } catch (e) {
      toast.error(e.response?.data?.error || 'Erreur lors de l\'approbation.')
    } finally {
      setSaving(false)
    }
  }

  // ── Refuser ───────────────────────────────────────────────────────────────
  const confirmerRejet = async () => {
    if (!motifRejet.trim()) { toast.error('Veuillez saisir un motif de refus.'); return }
    setSaving(true)
    try {
      await api.patch(`${BASE.attestation}/admin/demandes/${rejet.id}/`, {
        action     : 'refuser',
        motif_refus: motifRejet.trim(),
      })
      toast.success('Demande refusée.')
      setRejet(null)
      setMotifRejet('')
      charger()
    } catch (e) {
      toast.error(e.response?.data?.error || 'Erreur lors du refus.')
    } finally {
      setSaving(false)
    }
  }

  const nomEtudiant = (id) => usersMap[id] || `Étudiant #${id}`

  return (
    <div className="page">
      <div className="page-header">
        <div style={{ display:'flex', alignItems:'center', gap:10 }}>
          <FileText size={22} style={{ color:'var(--blue)' }}/>
          <div>
            <h1 className="page-title">Demandes d'attestation</h1>
            <p className="page-subtitle">{total} demande(s) au total</p>
          </div>
        </div>
        <button className="btn btn-ghost btn-sm" onClick={charger} disabled={loading}>
          <RefreshCw size={14} style={loading ? { animation:'spin 1s linear infinite' } : {}}/>
          Actualiser
        </button>
      </div>

      {/* Filtres */}
      <div className="card fade-up" style={{ marginBottom:16 }}>
        <div className="card-padded" style={{ display:'flex', flexWrap:'wrap', gap:10, alignItems:'flex-end' }}>
          <div>
            <label className="form-label">Statut</label>
            <select className="form-control" value={filtreStatut} onChange={e => setFiltreStatut(e.target.value)}>
              <option value="">Tous les statuts</option>
              <option value="en_attente">En attente</option>
              <option value="approuvee">Approuvée</option>
              <option value="generee">Générée</option>
              <option value="refusee">Refusée</option>
            </select>
          </div>
          <div>
            <label className="form-label">Type</label>
            <select className="form-control" value={filtreType} onChange={e => setFiltreType(e.target.value)}>
              <option value="">Tous les types</option>
              {Object.entries(TYPE_LABEL).map(([k, v]) => (
                <option key={k} value={k}>{v}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="card fade-up" style={{ animationDelay:'80ms' }}>
        {loading ? (
          <div className="card-body">
            {[1,2,3,4,5].map(i => (
              <div key={i} className="skeleton" style={{ height:50, marginBottom:10, borderRadius:8 }}/>
            ))}
          </div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Étudiant</th>
                  <th>Type</th>
                  <th>Année</th>
                  <th>Statut</th>
                  <th style={{ textAlign:'center' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {demandes.map(d => (
                  <tr key={d.id}>
                    <td style={{ fontSize:12, fontFamily:'monospace', color:'var(--gray-400)', whiteSpace:'nowrap' }}>
                      {new Date(d.date_demande).toLocaleDateString('fr-FR')}
                    </td>
                    <td style={{ fontWeight:600, fontSize:13 }}>
                      {nomEtudiant(d.etudiant_id)}
                    </td>
                    <td style={{ fontSize:13 }}>
                      {TYPE_LABEL[d.type_attestation] || d.type_attestation}
                    </td>
                    <td style={{ fontSize:13, color:'var(--gray-400)' }}>
                      {d.annee_universitaire || '—'}
                    </td>
                    <td>
                      <span className={`badge badge-${STATUT_BADGE[d.statut] || 'neutral'}`} style={{ fontSize:11 }}>
                        {d.statut.replace('_', ' ')}
                      </span>
                    </td>
                    <td>
                      <div style={{ display:'flex', gap:6, justifyContent:'center' }}>
                        {/* Détail */}
                        <button className="btn btn-ghost btn-sm btn-icon" title="Voir détail"
                          onClick={() => setSelected(d)}>
                          <Eye size={13}/>
                        </button>
                        {/* Approuver */}
                        {(d.statut === 'en_attente' || d.statut === 'refusee') && (
                          <button className="btn btn-sm" title="Approuver"
                            style={{ background:'var(--green)', color:'#fff', padding:'4px 10px', fontSize:12 }}
                            disabled={saving}
                            onClick={() => approuver(d)}>
                            <CheckCircle size={13}/> Approuver
                          </button>
                        )}
                        {/* Refuser */}
                        {d.statut === 'en_attente' && (
                          <button className="btn btn-sm" title="Refuser"
                            style={{ background:'var(--red)', color:'#fff', padding:'4px 10px', fontSize:12 }}
                            disabled={saving}
                            onClick={() => { setRejet(d); setMotifRejet('') }}>
                            <XCircle size={13}/> Refuser
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
                {!demandes.length && (
                  <tr>
                    <td colSpan={6} style={{ textAlign:'center', padding:32, color:'var(--gray-300)' }}>
                      Aucune demande pour ces filtres
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Modal détail */}
      {selected && (
        <div className="modal-overlay" onClick={() => setSelected(null)}>
          <div className="modal" style={{ maxWidth:480 }} onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <span className="modal-title">Demande #{selected.id}</span>
              <button className="btn btn-ghost btn-sm btn-icon" onClick={() => setSelected(null)}>✕</button>
            </div>
            <div className="modal-body" style={{ display:'flex', flexDirection:'column', gap:12 }}>
              {[
                ['Étudiant',    nomEtudiant(selected.etudiant_id)],
                ['Type',        TYPE_LABEL[selected.type_attestation] || selected.type_attestation],
                ['Année',       selected.annee_universitaire || '—'],
                ['Statut',      selected.statut],
                ['Date demande',new Date(selected.date_demande).toLocaleString('fr-FR')],
              ].map(([label, val]) => (
                <div key={label} style={{ display:'flex', gap:16 }}>
                  <div style={{ width:110, fontSize:12, color:'var(--gray-400)', fontWeight:600, flexShrink:0 }}>{label}</div>
                  <div style={{ fontSize:13, color:'var(--gray-700)', flex:1 }}>{val}</div>
                </div>
              ))}
            </div>
            <div className="modal-footer">
              {(selected.statut === 'en_attente' || selected.statut === 'refusee') && (
                <button className="btn btn-primary btn-sm" disabled={saving}
                  onClick={() => { approuver(selected); setSelected(null) }}>
                  <CheckCircle size={13}/> Approuver
                </button>
              )}
              {selected.statut === 'en_attente' && (
                <button className="btn btn-sm" disabled={saving}
                  style={{ background:'var(--red)', color:'#fff' }}
                  onClick={() => { setRejet(selected); setSelected(null); setMotifRejet('') }}>
                  <XCircle size={13}/> Refuser
                </button>
              )}
              <button className="btn btn-ghost" onClick={() => setSelected(null)}>Fermer</button>
            </div>
          </div>
        </div>
      )}

      {/* Modal refus */}
      {rejet && (
        <div className="modal-overlay" onClick={() => setRejet(null)}>
          <div className="modal" style={{ maxWidth:440 }} onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <span className="modal-title">Refuser la demande #{rejet.id}</span>
              <button className="btn btn-ghost btn-sm btn-icon" onClick={() => setRejet(null)}>✕</button>
            </div>
            <div className="modal-body">
              <p style={{ fontSize:13, color:'var(--gray-600)', marginBottom:12 }}>
                Étudiant : <strong>{nomEtudiant(rejet.etudiant_id)}</strong><br/>
                Type : <strong>{TYPE_LABEL[rejet.type_attestation] || rejet.type_attestation}</strong>
              </p>
              <label className="form-label">Motif de refus <span style={{ color:'var(--red)' }}>*</span></label>
              <textarea
                className="form-control"
                rows={3}
                placeholder="Expliquer la raison du refus…"
                value={motifRejet}
                onChange={e => setMotifRejet(e.target.value)}
                style={{ resize:'vertical' }}
              />
            </div>
            <div className="modal-footer">
              <button className="btn btn-sm" disabled={saving || !motifRejet.trim()}
                style={{ background:'var(--red)', color:'#fff' }}
                onClick={confirmerRejet}>
                {saving ? 'En cours…' : 'Confirmer le refus'}
              </button>
              <button className="btn btn-ghost" onClick={() => setRejet(null)}>Annuler</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
