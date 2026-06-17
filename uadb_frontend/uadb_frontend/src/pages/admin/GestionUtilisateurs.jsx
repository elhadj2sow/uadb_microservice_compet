import { useState, useEffect, useCallback } from 'react'
import { Users, Plus, Edit2, Shield, CheckCircle, XCircle, AlertTriangle, Search, X } from 'lucide-react'
import api, { BASE } from '../../config/api'

const ETATS = ['actif', 'inactif', 'bloque', 'suspendu']
const ETAT_BADGE = {
  actif    : 'success',
  inactif  : 'neutral',
  bloque   : 'danger',
  suspendu : 'warning',
}

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
        width:'min(520px,92vw)',
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

export default function GestionUtilisateurs() {
  const [users,   setUsers]   = useState([])
  const [roles,   setRoles]   = useState([])
  const [loading, setLoading] = useState(true)
  const [search,  setSearch]  = useState('')
  const [filterRole, setFilterRole] = useState('')
  const [filterEtat, setFilterEtat] = useState('')

  // Modals
  const [etatModal,  setEtatModal]  = useState(null) // { user }
  const [roleModal,  setRoleModal]  = useState(null) // { user }
  const [saving,     setSaving]     = useState(false)
  const [msg,        setMsg]        = useState(null)

  // Role modal form
  const [roleOp,     setRoleOp]     = useState('ajouter')
  const [roleTarget, setRoleTarget] = useState('')

  const charger = useCallback(() => {
    setLoading(true)
    const params = {}
    if (search)     params.search = search
    if (filterRole) params.role   = filterRole
    if (filterEtat) params.etat   = filterEtat
    api.get(`${BASE.auth}/utilisateurs/`, { params })
      .then(r => setUsers(r.data.results || []))
      .catch(() => setMsg({ type:'error', text:'Erreur chargement utilisateurs.' }))
      .finally(() => setLoading(false))
  }, [search, filterRole, filterEtat])

  useEffect(() => {
    api.get(`${BASE.auth}/roles/`).then(r => setRoles(r.data || []))
    charger()
  }, [charger])

  const flashMsg = (type, text) => {
    setMsg({ type, text })
    setTimeout(() => setMsg(null), 4000)
  }

  const sauvegarderEtat = async (user, etat) => {
    setSaving(true)
    try {
      await api.patch(`${BASE.auth}/utilisateurs/${user.id}/`, { etat_compte: etat })
      flashMsg('success', `Compte de ${user.username} mis à jour → ${etat}`)
      setEtatModal(null)
      charger()
    } catch {
      flashMsg('error', 'Erreur lors de la mise à jour.')
    } finally {
      setSaving(false)
    }
  }

  const sauvegarderRole = async () => {
    if (!roleTarget) return
    setSaving(true)
    try {
      const r = await api.post(`${BASE.auth}/utilisateurs/${roleModal.user.id}/roles/`, {
        role: roleTarget, action: roleOp
      })
      flashMsg('success', r.data.message)
      setRoleModal(null)
      charger()
    } catch (e) {
      flashMsg('error', e.response?.data?.error || 'Erreur assignation rôle.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="page-content">
      {/* Header */}
      <div className="page-header" style={{ marginBottom:'1.5rem' }}>
        <div style={{ display:'flex', alignItems:'center', gap:'.75rem' }}>
          <Users size={24} style={{ color:'var(--blue)' }}/>
          <div>
            <h1 className="page-title" style={{ margin:0 }}>Gestion des utilisateurs</h1>
            <p className="page-subtitle" style={{ margin:0 }}>Comptes, états et rôles</p>
          </div>
        </div>
      </div>

      {/* Message flash */}
      {msg && (
        <div className={`alert alert-${msg.type === 'error' ? 'danger' : 'success'}`}
             style={{ marginBottom:'1rem' }}>
          {msg.text}
        </div>
      )}

      {/* Filtres */}
      <div className="card" style={{ marginBottom:'1.25rem', padding:'1rem' }}>
        <div style={{ display:'flex', flexWrap:'wrap', gap:'.75rem', alignItems:'flex-end' }}>
          <div style={{ flex:'1 1 220px' }}>
            <label className="form-label">Recherche</label>
            <div style={{ position:'relative' }}>
              <Search size={16} style={{ position:'absolute', left:'.6rem', top:'50%', transform:'translateY(-50%)', color:'var(--muted)' }}/>
              <input
                className="form-control"
                style={{ paddingLeft:'2rem' }}
                placeholder="Nom d'utilisateur ou email…"
                value={search}
                onChange={e => setSearch(e.target.value)}
              />
            </div>
          </div>
          <div>
            <label className="form-label">Rôle</label>
            <select className="form-control" value={filterRole} onChange={e => setFilterRole(e.target.value)}>
              <option value="">Tous les rôles</option>
              {roles.map(r => <option key={r.id} value={r.libelle}>{r.libelle}</option>)}
            </select>
          </div>
          <div>
            <label className="form-label">État</label>
            <select className="form-control" value={filterEtat} onChange={e => setFilterEtat(e.target.value)}>
              <option value="">Tous les états</option>
              {ETATS.map(e => <option key={e} value={e}>{e}</option>)}
            </select>
          </div>
          <button className="btn btn-secondary" onClick={charger}>Actualiser</button>
        </div>
      </div>

      {/* Tableau */}
      <div className="card">
        {loading ? (
          <div style={{ textAlign:'center', padding:'2rem' }}><div className="spinner spinner-dark"/></div>
        ) : (
          <div style={{ overflowX:'auto' }}>
            <table className="table">
              <thead>
                <tr>
                  <th>Utilisateur</th>
                  <th>Email</th>
                  <th>Rôles</th>
                  <th>État</th>
                  <th>Inscrit le</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {users.length === 0 && (
                  <tr><td colSpan={6} style={{ textAlign:'center', color:'var(--muted)', padding:'2rem' }}>
                    Aucun utilisateur trouvé.
                  </td></tr>
                )}
                {users.map(u => (
                  <tr key={u.id}>
                    <td>
                      <strong>{u.username}</strong>
                      {u.prenom && u.nom && (
                        <div style={{ fontSize:'.8rem', color:'var(--muted)' }}>{u.prenom} {u.nom}</div>
                      )}
                    </td>
                    <td style={{ fontSize:'.875rem' }}>{u.email || '—'}</td>
                    <td>
                      <div style={{ display:'flex', flexWrap:'wrap', gap:'.25rem' }}>
                        {(u.roles || []).map(r => (
                          <span key={r} className="badge badge-info" style={{ fontSize:'.7rem' }}>{r}</span>
                        ))}
                        {(!u.roles || u.roles.length === 0) && <span style={{ color:'var(--muted)', fontSize:'.8rem' }}>—</span>}
                      </div>
                    </td>
                    <td>
                      <span className={`badge badge-${ETAT_BADGE[u.etat_compte] || 'neutral'}`}>
                        {u.etat_compte}
                      </span>
                    </td>
                    <td style={{ fontSize:'.8rem', color:'var(--muted)' }}>
                      {u.date_joined ? new Date(u.date_joined).toLocaleDateString('fr-FR') : '—'}
                    </td>
                    <td>
                      <div style={{ display:'flex', gap:'.5rem' }}>
                        <button
                          className="btn btn-secondary btn-sm"
                          title="Changer état"
                          onClick={() => setEtatModal({ user: u })}
                        >
                          <Edit2 size={14}/>
                        </button>
                        <button
                          className="btn btn-secondary btn-sm"
                          title="Gérer rôles"
                          onClick={() => { setRoleModal({ user: u }); setRoleTarget(''); setRoleOp('ajouter') }}
                        >
                          <Shield size={14}/>
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div style={{ padding:'.75rem 1rem', color:'var(--muted)', fontSize:'.85rem' }}>
              {users.length} utilisateur(s) affiché(s)
            </div>
          </div>
        )}
      </div>

      {/* Modal : changer état compte */}
      {etatModal && (
        <Modal title={`État du compte — ${etatModal.user.username}`} onClose={() => setEtatModal(null)}>
          <p style={{ color:'var(--muted)', marginTop:0 }}>
            État actuel : <strong>{etatModal.user.etat_compte}</strong>
          </p>
          <div style={{ display:'flex', flexDirection:'column', gap:'.75rem', marginBottom:'1.25rem' }}>
            {ETATS.map(e => (
              <button
                key={e}
                className={`btn ${etatModal.user.etat_compte === e ? 'btn-primary' : 'btn-secondary'}`}
                disabled={saving || etatModal.user.etat_compte === e}
                onClick={() => sauvegarderEtat(etatModal.user, e)}
                style={{ justifyContent:'flex-start', gap:'.5rem' }}
              >
                {e === 'actif'    && <CheckCircle size={16}/>}
                {e === 'inactif'  && <XCircle size={16}/>}
                {e === 'bloque'   && <AlertTriangle size={16}/>}
                {e === 'suspendu' && <AlertTriangle size={16}/>}
                {e}
              </button>
            ))}
          </div>
          <button className="btn btn-secondary" onClick={() => setEtatModal(null)}>Annuler</button>
        </Modal>
      )}

      {/* Modal : gérer rôles */}
      {roleModal && (
        <Modal title={`Rôles — ${roleModal.user.username}`} onClose={() => setRoleModal(null)}>
          <div style={{ marginBottom:'1rem' }}>
            <p style={{ margin:'0 0 .5rem', color:'var(--muted)', fontSize:'.9rem' }}>Rôles actuels :</p>
            <div style={{ display:'flex', flexWrap:'wrap', gap:'.35rem' }}>
              {(roleModal.user.roles || []).map(r => (
                <span key={r} className="badge badge-info">{r}</span>
              ))}
              {(!roleModal.user.roles || roleModal.user.roles.length === 0) && (
                <span style={{ color:'var(--muted)' }}>Aucun rôle</span>
              )}
            </div>
          </div>
          <div style={{ display:'flex', flexDirection:'column', gap:'1rem', marginBottom:'1.25rem' }}>
            <div>
              <label className="form-label">Opération</label>
              <div style={{ display:'flex', gap:'.75rem' }}>
                {['ajouter','retirer'].map(op => (
                  <label key={op} style={{ display:'flex', alignItems:'center', gap:'.4rem', cursor:'pointer' }}>
                    <input type="radio" name="roleOp" value={op} checked={roleOp===op} onChange={() => setRoleOp(op)}/>
                    {op.charAt(0).toUpperCase() + op.slice(1)}
                  </label>
                ))}
              </div>
            </div>
            <div>
              <label className="form-label">Rôle</label>
              <select className="form-control" value={roleTarget} onChange={e => setRoleTarget(e.target.value)}>
                <option value="">— Sélectionner un rôle —</option>
                {roles.map(r => <option key={r.id} value={r.libelle}>{r.libelle}</option>)}
              </select>
            </div>
          </div>
          <div style={{ display:'flex', gap:'.75rem' }}>
            <button className="btn btn-primary" disabled={!roleTarget || saving} onClick={sauvegarderRole}>
              {saving ? <span className="spinner"/> : 'Appliquer'}
            </button>
            <button className="btn btn-secondary" onClick={() => setRoleModal(null)}>Annuler</button>
          </div>
        </Modal>
      )}
    </div>
  )
}
