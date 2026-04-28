import { useState, useRef } from 'react'
import api, { BASE } from '../../config/api'
import toast from 'react-hot-toast'
import { Search, BookOpen, AlertTriangle, Plus, CheckCircle, XCircle, User } from 'lucide-react'

const STATUT_EMPRUNT_BADGE = { emprunte: 'info', rendu: 'success', perdu: 'danger' }
const STATUT_PENALITE_BADGE = { en_attente: 'warning', payee: 'success', annulee: 'neutral' }

const initEmprunt = {
  etudiant_id: '', numero_inventaire: '', titre_livre: '',
  date_emprunt: new Date().toISOString().slice(0, 10),
  date_retour_prevue: '', note: '',
}
const initPenalite = {
  etudiant_id: '', emprunt: '', motif: '', montant: '', observation: '',
}

export default function GestionBibliotheque() {
  const [query,       setQuery]       = useState('')
  const [suggestions, setSuggestions] = useState([])
  const [showSug,     setShowSug]     = useState(false)
  const [situation,   setSituation]   = useState(null)
  const [emprunts,    setEmprunts]    = useState([])
  const [penalites,   setPenalites]   = useState([])
  const [loading,     setLoading]     = useState(false)
  const [etudiantNom, setEtudiantNom] = useState('')
  const [etudiantId,  setEtudiantId]  = useState(null)
  const searchTimer = useRef(null)

  // Modales
  const [showEmprunt,  setShowEmprunt]  = useState(false)
  const [showPenalite, setShowPenalite] = useState(false)
  const [formEmprunt,  setFormEmprunt]  = useState(initEmprunt)
  const [formPenalite, setFormPenalite] = useState(initPenalite)
  const [saving,       setSaving]       = useState(false)

  const chargerEtudiant = async (id, nom) => {
    if (!id) return
    setLoading(true)
    setEtudiantId(id)
    setEtudiantNom(nom)
    setShowSug(false)
    try {
      const [sit, emp, pen] = await Promise.all([
        api.get(`${BASE.bibliotheque}/situation/${id}/`),
        api.get(`${BASE.bibliotheque}/emprunts/?etudiant_id=${id}`),
        api.get(`${BASE.bibliotheque}/penalites/?etudiant_id=${id}`),
      ])
      setSituation(sit.data)
      setEmprunts(emp.data)
      setPenalites(pen.data)
    } catch (e) {
      toast.error(e.response?.data?.error || 'Étudiant introuvable ou accès refusé.')
      setSituation(null); setEmprunts([]); setPenalites([]); setEtudiantNom(''); setEtudiantId(null)
    } finally { setLoading(false) }
  }

  const handleQueryChange = (e) => {
    const val = e.target.value
    setQuery(val)
    setSituation(null); setEtudiantId(null); setEtudiantNom('')
    clearTimeout(searchTimer.current)
    if (val.length < 2) { setSuggestions([]); setShowSug(false); return }
    searchTimer.current = setTimeout(async () => {
      try {
        const r = await api.get(`${BASE.auth}/etudiants/search/?q=${encodeURIComponent(val)}`)
        setSuggestions(r.data.results || [])
        setShowSug(true)
      } catch { setSuggestions([]) }
    }, 300)
  }

  const choisirEtudiant = (s) => {
    setQuery(s.nom_complet || s.username)
    setSuggestions([]); setShowSug(false)
    chargerEtudiant(s.id, s.nom_complet || s.username)
  }

  const marquerRendu = async (emprunt) => {
    try {
      await api.patch(`${BASE.bibliotheque}/emprunts/${emprunt.id}/`, { statut: 'rendu' })
      toast.success('Livre marqué comme rendu.')
      chargerEtudiant(emprunt.etudiant_id, etudiantNom)
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Erreur.')
    }
  }

  const marquerPaye = async (pen) => {
    try {
      await api.patch(`${BASE.bibliotheque}/penalites/${pen.id}/`, { statut: 'payee' })
      toast.success('Pénalité marquée comme payée.')
      chargerEtudiant(pen.etudiant_id, etudiantNom)
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Erreur.')
    }
  }

  const soumettreEmprunt = async (e) => {
    e.preventDefault()
    setSaving(true)
    try {
      await api.post(`${BASE.bibliotheque}/emprunts/`, {
        ...formEmprunt,
        etudiant_id: parseInt(formEmprunt.etudiant_id, 10),
      })
      toast.success('Emprunt enregistré.')
      setShowEmprunt(false)
      setFormEmprunt(initEmprunt)
      chargerEtudiant(formEmprunt.etudiant_id, etudiantNom)
    } catch (e) {
      const err = e.response?.data
      toast.error(err ? Object.values(err).flat().join(' ') : 'Erreur.')
    } finally { setSaving(false) }
  }

  const soumettrePenalite = async (e) => {
    e.preventDefault()
    setSaving(true)
    try {
      await api.post(`${BASE.bibliotheque}/penalites/`, {
        ...formPenalite,
        etudiant_id: parseInt(formPenalite.etudiant_id, 10),
        montant: parseFloat(formPenalite.montant),
        emprunt: formPenalite.emprunt ? parseInt(formPenalite.emprunt, 10) : null,
      })
      toast.success('Pénalité créée.')
      setShowPenalite(false)
      setFormPenalite(initPenalite)
      chargerEtudiant(formPenalite.etudiant_id, etudiantNom)
    } catch (e) {
      const err = e.response?.data
      toast.error(err ? Object.values(err).flat().join(' ') : 'Erreur.')
    } finally { setSaving(false) }
  }

  const ouvrirNouvelEmprunt = () => {
    if (!situation) { toast.error('Recherchez un étudiant d’abord.'); return }
    setFormEmprunt({ ...initEmprunt, etudiant_id: etudiantId })
    setShowEmprunt(true)
  }

  const ouvrirNouvellePenalite = () => {
    if (!situation) { toast.error('Recherchez un étudiant d’abord.'); return }
    setFormPenalite({ ...initPenalite, etudiant_id: etudiantId })
    setShowPenalite(true)
  }

  return (
    <div className="page">
      <div className="page-header flex items-center justify-between">
        <div>
          <h1 className="page-title">Gestion Bibliothèque</h1>
          <p className="page-subtitle">Emprunts et pénalités des étudiants</p>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button className="btn btn-primary" onClick={ouvrirNouvelEmprunt}>
            <Plus size={16} /> Nouvel emprunt
          </button>
          <button className="btn btn-warning" onClick={ouvrirNouvellePenalite}>
            <AlertTriangle size={16} /> Nouvelle pénalité
          </button>
        </div>
      </div>

      {/* Recherche par nom */}
      <div className="card fade-up" style={{ padding: '16px 20px', overflow: 'visible' }}>
        <div style={{ position: 'relative', maxWidth: 380 }}>
          <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
            <Search size={16} style={{ position: 'absolute', left: 12, color: 'var(--gray-400)', pointerEvents: 'none' }} />
            <input
              className="form-control"
              placeholder="Rechercher un étudiant par nom..."
              value={query}
              onChange={handleQueryChange}
              onFocus={() => suggestions.length > 0 && setShowSug(true)}
              onBlur={() => setTimeout(() => setShowSug(false), 150)}
              autoComplete="off"
              style={{ paddingLeft: 36, fontSize: 14 }}
            />
            {loading && <div className="spinner" style={{ position: 'absolute', right: 10, width: 16, height: 16 }} />}
          </div>
          {showSug && suggestions.length > 0 && (
            <div style={{
              position: 'absolute', top: '100%', left: 0, right: 0, zIndex: 100,
              background: '#fff', border: '1px solid var(--gray-200)',
              borderRadius: 10, boxShadow: '0 4px 20px rgba(0,0,0,.1)',
              marginTop: 4, overflow: 'hidden',
            }}>
              {suggestions.map(s => (
                <button
                  key={s.id}
                  type="button"
                  onMouseDown={() => choisirEtudiant(s)}
                  style={{
                    width: '100%', textAlign: 'left', padding: '10px 14px',
                    display: 'flex', alignItems: 'center', gap: 10,
                    background: 'none', border: 'none', cursor: 'pointer',
                    borderBottom: '1px solid var(--gray-100)',
                    fontSize: 14,
                  }}
                  onMouseEnter={e => e.currentTarget.style.background = 'var(--gray-50)'}
                  onMouseLeave={e => e.currentTarget.style.background = 'none'}
                >
                  <div style={{
                    width: 32, height: 32, borderRadius: '50%',
                    background: 'var(--blue-light)', color: 'var(--blue)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontWeight: 700, fontSize: 13, flexShrink: 0,
                  }}>
                    {(s.nom_complet || s.username).slice(0,2).toUpperCase()}
                  </div>
                  <div>
                    <div style={{ fontWeight: 600 }}>{s.nom_complet || s.username}</div>
                    <div style={{ fontSize: 11, color: 'var(--gray-400)' }}>@{s.username} · ID {s.id}</div>
                  </div>
                </button>
              ))}
            </div>
          )}
          {showSug && suggestions.length === 0 && query.length >= 2 && !loading && (
            <div style={{
              position: 'absolute', top: '100%', left: 0, right: 0, zIndex: 100,
              background: '#fff', border: '1px solid var(--gray-200)',
              borderRadius: 10, padding: '12px 14px',
              fontSize: 13, color: 'var(--gray-400)', marginTop: 4,
            }}>Aucun étudiant trouvé</div>
          )}
        </div>
      </div>

      {/* Situation résumée */}
      {situation && (
        <div className={`card fade-up ${situation.peut_valider ? '' : 'border-warning'}`}
          style={{ borderLeft: `4px solid ${situation.peut_valider ? 'var(--teal)' : 'var(--warning)'}`, marginTop: 16 }}>
          <div className="card-body" style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            {situation.peut_valider
              ? <CheckCircle size={28} color="var(--teal)" />
              : <AlertTriangle size={28} color="var(--warning)" />
            }
            <div>
              <div style={{ fontWeight: 700, fontSize: 15 }}>
                {situation.peut_valider ? 'Quitus bibliothèque : OK' : 'Quitus bibliothèque : BLOQUÉ'}
              </div>
              {situation.motif_blocage && (
                <div style={{ fontSize: 13, color: 'var(--gray-400)', marginTop: 2 }}>
                  {situation.motif_blocage}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Emprunts */}
      {situation && (
        <div className="card fade-up" style={{ marginTop: 16 }}>
          <div className="card-header">
            <span className="card-title"><BookOpen size={16} style={{ marginRight: 6 }} />Emprunts</span>
            <span className="badge badge-info">{emprunts.length}</span>
          </div>
          <div className="card-body" style={{ padding: 0 }}>
            {emprunts.length === 0 ? (
              <div style={{ padding: '24px', textAlign: 'center', color: 'var(--gray-400)' }}>Aucun emprunt</div>
            ) : (
              <div className="table-wrap">
                <table>
                  <thead><tr>
                    <th>N° Inventaire</th><th>Titre</th><th>Emprunté le</th>
                    <th>Retour prévu</th><th>Retour effectif</th><th>Statut</th><th>Actions</th>
                  </tr></thead>
                  <tbody>
                    {emprunts.map(emp => (
                      <tr key={emp.id}>
                        <td className="font-mono" style={{ fontSize: 12 }}>{emp.numero_inventaire}</td>
                        <td style={{ fontWeight: 600 }}>{emp.titre_livre}</td>
                        <td style={{ fontSize: 12 }}>{emp.date_emprunt}</td>
                        <td style={{ fontSize: 12, color: emp.est_en_retard ? 'var(--danger)' : undefined }}>
                          {emp.date_retour_prevue}
                          {emp.est_en_retard && ' ⚠'}
                        </td>
                        <td style={{ fontSize: 12 }}>{emp.date_retour_effective || '—'}</td>
                        <td>
                          <span className={`badge badge-${STATUT_EMPRUNT_BADGE[emp.statut] || 'neutral'}`}>
                            {emp.statut_display || emp.statut}
                          </span>
                        </td>
                        <td>
                          {emp.statut === 'emprunte' && (
                            <button className="btn btn-sm btn-success" onClick={() => marquerRendu(emp)}>
                              Rendu
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Pénalités */}
      {situation && (
        <div className="card fade-up" style={{ marginTop: 16 }}>
          <div className="card-header">
            <span className="card-title"><AlertTriangle size={16} style={{ marginRight: 6 }} />Pénalités</span>
            <span className="badge badge-warning">{penalites.length}</span>
          </div>
          <div className="card-body" style={{ padding: 0 }}>
            {penalites.length === 0 ? (
              <div style={{ padding: '24px', textAlign: 'center', color: 'var(--gray-400)' }}>Aucune pénalité</div>
            ) : (
              <div className="table-wrap">
                <table>
                  <thead><tr>
                    <th>Motif</th><th>Montant (FCFA)</th><th>Date création</th>
                    <th>Date paiement</th><th>Statut</th><th>Actions</th>
                  </tr></thead>
                  <tbody>
                    {penalites.map(pen => (
                      <tr key={pen.id}>
                        <td>{pen.motif}</td>
                        <td style={{ fontWeight: 600 }}>{Number(pen.montant).toLocaleString('fr-FR')}</td>
                        <td style={{ fontSize: 12 }}>{pen.date_creation ? new Date(pen.date_creation).toLocaleDateString('fr-FR') : '—'}</td>
                        <td style={{ fontSize: 12 }}>{pen.date_paiement ? new Date(pen.date_paiement).toLocaleDateString('fr-FR') : '—'}</td>
                        <td>
                          <span className={`badge badge-${STATUT_PENALITE_BADGE[pen.statut] || 'neutral'}`}>
                            {pen.statut === 'en_attente' ? 'En attente' : pen.statut === 'payee' ? 'Payée' : 'Annulée'}
                          </span>
                        </td>
                        <td>
                          {pen.statut === 'en_attente' && (
                            <button className="btn btn-sm btn-success" onClick={() => marquerPaye(pen)}>
                              Payée
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Modale Nouvel Emprunt */}
      {showEmprunt && (
        <div
          onClick={() => setShowEmprunt(false)}
          style={{
            position: 'fixed', inset: 0, zIndex: 1000,
            background: 'rgba(0,0,0,.45)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            padding: '16px', overflow: 'auto',
          }}
        >
          <div
            onClick={e => e.stopPropagation()}
            style={{
              background: '#fff', borderRadius: 16, width: '100%', maxWidth: 460,
              boxShadow: '0 8px 40px rgba(0,0,0,.18)', margin: 'auto',
            }}
          >
            {/* Header */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '16px 20px', borderBottom: '1px solid var(--gray-100)' }}>
              <span style={{ fontWeight: 700, fontSize: 16 }}>Enregistrer un emprunt</span>
              <button className="btn-icon" onClick={() => setShowEmprunt(false)} style={{ color: 'var(--gray-400)' }}><XCircle size={20} /></button>
            </div>
            <form onSubmit={soumettreEmprunt}>
              <div style={{ padding: '16px 20px', display: 'flex', flexDirection: 'column', gap: 12 }}>
                {/* Etudiant */}
                <div style={{ background: 'var(--gray-50)', borderRadius: 8, padding: '8px 12px', display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span style={{ fontSize: 12, color: 'var(--gray-400)', minWidth: 70 }}>Étudiant</span>
                  <span style={{ fontWeight: 700, color: 'var(--blue)', fontSize: 14 }}>{etudiantNom}</span>
                </div>
                {/* Ligne 1 : N° inv + Titre */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.5fr', gap: 10 }}>
                  <div>
                    <label style={{ fontSize: 12, fontWeight: 600, color: 'var(--gray-500)', display: 'block', marginBottom: 4 }}>N° Inventaire *</label>
                    <input className="form-control" required style={{ fontSize: 13 }}
                      value={formEmprunt.numero_inventaire}
                      onChange={e => setFormEmprunt(p => ({ ...p, numero_inventaire: e.target.value }))} />
                  </div>
                  <div>
                    <label style={{ fontSize: 12, fontWeight: 600, color: 'var(--gray-500)', display: 'block', marginBottom: 4 }}>Titre du livre *</label>
                    <input className="form-control" required style={{ fontSize: 13 }}
                      value={formEmprunt.titre_livre}
                      onChange={e => setFormEmprunt(p => ({ ...p, titre_livre: e.target.value }))} />
                  </div>
                </div>
                {/* Ligne 2 : Dates */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                  <div>
                    <label style={{ fontSize: 12, fontWeight: 600, color: 'var(--gray-500)', display: 'block', marginBottom: 4 }}>Date emprunt *</label>
                    <input className="form-control" type="date" required style={{ fontSize: 13 }}
                      value={formEmprunt.date_emprunt}
                      onChange={e => setFormEmprunt(p => ({ ...p, date_emprunt: e.target.value }))} />
                  </div>
                  <div>
                    <label style={{ fontSize: 12, fontWeight: 600, color: 'var(--gray-500)', display: 'block', marginBottom: 4 }}>Retour prévu *</label>
                    <input className="form-control" type="date" required style={{ fontSize: 13 }}
                      value={formEmprunt.date_retour_prevue}
                      onChange={e => setFormEmprunt(p => ({ ...p, date_retour_prevue: e.target.value }))} />
                  </div>
                </div>
                {/* Note */}
                <div>
                  <label style={{ fontSize: 12, fontWeight: 600, color: 'var(--gray-500)', display: 'block', marginBottom: 4 }}>Note</label>
                  <textarea className="form-control" rows={2} style={{ fontSize: 13, resize: 'none' }}
                    value={formEmprunt.note}
                    onChange={e => setFormEmprunt(p => ({ ...p, note: e.target.value }))} />
                </div>
              </div>
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, padding: '12px 20px', borderTop: '1px solid var(--gray-100)' }}>
                <button type="button" className="btn btn-ghost" onClick={() => setShowEmprunt(false)}>Annuler</button>
                <button type="submit" className="btn btn-primary" disabled={saving}>
                  {saving ? 'Enregistrement…' : 'Enregistrer'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modale Nouvelle Pénalité */}
      {showPenalite && (
        <div
          onClick={() => setShowPenalite(false)}
          style={{
            position: 'fixed', inset: 0, zIndex: 1000,
            background: 'rgba(0,0,0,.45)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            padding: '16px', overflow: 'auto',
          }}
        >
          <div
            onClick={e => e.stopPropagation()}
            style={{
              background: '#fff', borderRadius: 16, width: '100%', maxWidth: 460,
              boxShadow: '0 8px 40px rgba(0,0,0,.18)', margin: 'auto',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '16px 20px', borderBottom: '1px solid var(--gray-100)' }}>
              <span style={{ fontWeight: 700, fontSize: 16 }}>Créer une pénalité</span>
              <button className="btn-icon" onClick={() => setShowPenalite(false)} style={{ color: 'var(--gray-400)' }}><XCircle size={20} /></button>
            </div>
            <form onSubmit={soumettrePenalite}>
              <div style={{ padding: '16px 20px', display: 'flex', flexDirection: 'column', gap: 12 }}>
                {/* Etudiant */}
                <div style={{ background: 'var(--gray-50)', borderRadius: 8, padding: '8px 12px', display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span style={{ fontSize: 12, color: 'var(--gray-400)', minWidth: 70 }}>Étudiant</span>
                  <span style={{ fontWeight: 700, color: 'var(--blue)', fontSize: 14 }}>{etudiantNom}</span>
                </div>
                {/* Emprunt lié + Motif */}
                <div style={{ display: 'grid', gridTemplateColumns: '120px 1fr', gap: 10 }}>
                  <div>
                    <label style={{ fontSize: 12, fontWeight: 600, color: 'var(--gray-500)', display: 'block', marginBottom: 4 }}>Emprunt (ID)</label>
                    <input className="form-control" type="number" min="1" style={{ fontSize: 13 }}
                      placeholder="Optionnel"
                      value={formPenalite.emprunt}
                      onChange={e => setFormPenalite(p => ({ ...p, emprunt: e.target.value }))} />
                  </div>
                  <div>
                    <label style={{ fontSize: 12, fontWeight: 600, color: 'var(--gray-500)', display: 'block', marginBottom: 4 }}>Motif *</label>
                    <input className="form-control" required style={{ fontSize: 13 }}
                      value={formPenalite.motif}
                      onChange={e => setFormPenalite(p => ({ ...p, motif: e.target.value }))} />
                  </div>
                </div>
                {/* Montant */}
                <div>
                  <label style={{ fontSize: 12, fontWeight: 600, color: 'var(--gray-500)', display: 'block', marginBottom: 4 }}>Montant (FCFA) *</label>
                  <input className="form-control" type="number" min="0" step="0.01" required style={{ fontSize: 13 }}
                    value={formPenalite.montant}
                    onChange={e => setFormPenalite(p => ({ ...p, montant: e.target.value }))} />
                </div>
                {/* Observation */}
                <div>
                  <label style={{ fontSize: 12, fontWeight: 600, color: 'var(--gray-500)', display: 'block', marginBottom: 4 }}>Observation</label>
                  <textarea className="form-control" rows={2} style={{ fontSize: 13, resize: 'none' }}
                    value={formPenalite.observation}
                    onChange={e => setFormPenalite(p => ({ ...p, observation: e.target.value }))} />
                </div>
              </div>
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, padding: '12px 20px', borderTop: '1px solid var(--gray-100)' }}>
                <button type="button" className="btn btn-ghost" onClick={() => setShowPenalite(false)}>Annuler</button>
                <button type="submit" className="btn btn-primary" disabled={saving}>
                  {saving ? 'Création…' : 'Créer'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
