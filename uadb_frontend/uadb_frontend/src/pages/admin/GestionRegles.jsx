import { useState, useEffect } from 'react'
import api, { BASE } from '../../config/api'
import toast from 'react-hot-toast'
import { Plus, Edit2, Trash2, Play, CheckCircle, XCircle, Sliders } from 'lucide-react'

const DOMAINES = ['','dossier','inscription','deliberation','attestation','workflow']
const BADGE_DOM = { dossier:'info', inscription:'success', deliberation:'navy', attestation:'warning', workflow:'neutral' }

const EMPTY = { code_regle:'', libelle:'', domaine:'dossier', condition:"contexte['']", action:'', priorite:10, active:true, description:'' }

export default function GestionRegles() {
  const [regles,   setRegles]   = useState([])
  const [total,    setTotal]    = useState(0)
  const [loading,  setLoading]  = useState(true)
  const [domaine,  setDomaine]  = useState('')
  const [modal,    setModal]    = useState(null) // null | 'create' | 'edit' | 'test'
  const [form,     setForm]     = useState(EMPTY)
  const [testCtx,  setTestCtx]  = useState('{}')
  const [testRes,  setTestRes]  = useState(null)
  const [saving,   setSaving]   = useState(false)

  const charger = async () => {
    setLoading(true)
    try {
      const r = await api.get(`${BASE.regles}/?domaine=${domaine}`)
      setRegles(r.data.results || [])
      setTotal(r.data.count || 0)
    } finally { setLoading(false) }
  }

  useEffect(() => { charger() }, [domaine])

  const ouvrirCreation = () => { setForm(EMPTY); setModal('create') }
  const ouvrirEdition  = r => { setForm({...r}); setModal('edit') }
  const ouvrirTest     = r => { setForm({...r}); setTestCtx('{}'); setTestRes(null); setModal('test') }

  const sauvegarder = async () => {
    setSaving(true)
    try {
      if (modal === 'create') {
        await api.post(`${BASE.regles}/`, form)
        toast.success('Règle créée !')
      } else {
        await api.patch(`${BASE.regles}/${form.id}/`, form)
        toast.success('Règle mise à jour !')
      }
      charger(); setModal(null)
    } catch (e) {
      const err = e.response?.data
      toast.error(err?.condition?.[0] || err?.detail || 'Erreur de validation.')
    } finally { setSaving(false) }
  }

  const supprimer = async id => {
    if (!confirm('Supprimer cette règle ?')) return
    try {
      await api.delete(`${BASE.regles}/${id}/`)
      toast.success('Règle supprimée.')
      charger()
    } catch { toast.error('Impossible de supprimer.') }
  }

  const tester = async () => {
    setSaving(true)
    try {
      const ctx = JSON.parse(testCtx)
      const r   = await api.post(`${BASE.regles}/${form.id}/tester/`, { contexte: ctx })
      setTestRes(r.data)
    } catch (e) {
      if (e.message.includes('JSON')) toast.error('JSON invalide.')
      else setTestRes({ erreur: e.response?.data?.error || 'Erreur' })
    } finally { setSaving(false) }
  }

  const toggleActif = async r => {
    try {
      await api.patch(`${BASE.regles}/${r.id}/`, { active: !r.active })
      charger()
    } catch { toast.error('Erreur.') }
  }

  return (
    <div className="page">
      <div className="page-header flex items-center justify-between">
        <div>
          <h1 className="page-title">Règles Métier IA</h1>
          <p className="page-subtitle">{total} règle(s) — modifiables sans redéploiement</p>
        </div>
        <button className="btn btn-primary" onClick={ouvrirCreation}>
          <Plus size={15}/> Nouvelle règle
        </button>
      </div>

      {/* Filtre domaine */}
      <div className="card fade-up" style={{marginBottom:20}}>
        <div className="card-padded" style={{display:'flex',gap:8,flexWrap:'wrap'}}>
          {DOMAINES.map(d => (
            <button key={d}
              className={`btn btn-sm ${domaine===d ? 'btn-primary' : 'btn-ghost'}`}
              onClick={() => setDomaine(d)}>
              {d || 'Tous'}
            </button>
          ))}
        </div>
      </div>

      {/* Table règles */}
      <div className="card fade-up" style={{animationDelay:'60ms'}}>
        {loading ? (
          <div className="card-body">
            {[1,2,3,4].map(i=><div key={i} className="skeleton" style={{height:55,marginBottom:10,borderRadius:8}}/>)}
          </div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead><tr>
                <th>Priorité</th><th>Code</th><th>Libellé</th>
                <th>Domaine</th><th>Action</th><th>Actif</th><th>Actions</th>
              </tr></thead>
              <tbody>
                {regles.map(r => (
                  <tr key={r.id}>
                    <td>
                      <span style={{
                        display:'inline-flex',alignItems:'center',justifyContent:'center',
                        width:28,height:28,borderRadius:'50%',
                        background:'var(--gray-100)',fontSize:12,fontWeight:700,
                      }}>{r.priorite}</span>
                    </td>
                    <td><span className="chip font-mono" style={{fontSize:12}}>{r.code_regle}</span></td>
                    <td style={{fontSize:13,maxWidth:200}}>{r.libelle}</td>
                    <td><span className={`badge badge-${BADGE_DOM[r.domaine]||'neutral'}`}>{r.domaine}</span></td>
                    <td>
                      <span style={{
                        fontFamily:'monospace',fontSize:12,
                        background:'var(--gray-50)',padding:'3px 8px',
                        borderRadius:4,border:'1px solid var(--gray-200)',
                        color:'var(--blue)',
                      }}>{r.action}</span>
                    </td>
                    <td>
                      <button onClick={()=>toggleActif(r)}
                        style={{background:'none',border:'none',cursor:'pointer',padding:0}}>
                        {r.active
                          ? <CheckCircle size={18} color="var(--success)"/>
                          : <XCircle    size={18} color="var(--gray-300)"/>}
                      </button>
                    </td>
                    <td>
                      <div style={{display:'flex',gap:4}}>
                        <button className="btn btn-ghost btn-sm btn-icon" onClick={()=>ouvrirTest(r)} title="Tester">
                          <Play size={13}/>
                        </button>
                        <button className="btn btn-ghost btn-sm btn-icon" onClick={()=>ouvrirEdition(r)} title="Modifier">
                          <Edit2 size={13}/>
                        </button>
                        <button className="btn btn-ghost btn-sm btn-icon" onClick={()=>supprimer(r.id)} title="Supprimer"
                          style={{color:'var(--danger)'}}>
                          <Trash2 size={13}/>
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
                {!regles.length && (
                  <tr><td colSpan={7} style={{textAlign:'center',padding:32,color:'var(--gray-300)'}}>
                    Aucune règle pour ce domaine
                  </td></tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Modal créer / éditer */}
      {(modal === 'create' || modal === 'edit') && (
        <div className="modal-overlay" onClick={() => setModal(null)}>
          <div className="modal" style={{maxWidth:600}} onClick={e=>e.stopPropagation()}>
            <div className="modal-header">
              <span className="modal-title">{modal==='create'?'Nouvelle règle':'Modifier la règle'}</span>
              <button className="btn btn-ghost btn-sm btn-icon" onClick={()=>setModal(null)}>✕</button>
            </div>
            <div className="modal-body">
              <div className="grid-2">
                <div className="form-group">
                  <label className="form-label">Code règle *</label>
                  <input className="form-control font-mono" value={form.code_regle}
                    onChange={e=>setForm(f=>({...f,code_regle:e.target.value}))}
                    placeholder="ex: DELIB_ADMIS"/>
                </div>
                <div className="form-group">
                  <label className="form-label">Priorité</label>
                  <input className="form-control" type="number" value={form.priorite}
                    onChange={e=>setForm(f=>({...f,priorite:+e.target.value}))}/>
                </div>
              </div>
              <div className="form-group">
                <label className="form-label">Libellé *</label>
                <input className="form-control" value={form.libelle}
                  onChange={e=>setForm(f=>({...f,libelle:e.target.value}))}/>
              </div>
              <div className="grid-2">
                <div className="form-group">
                  <label className="form-label">Domaine *</label>
                  <select className="form-control" value={form.domaine}
                    onChange={e=>setForm(f=>({...f,domaine:e.target.value}))}>
                    {DOMAINES.filter(Boolean).map(d=><option key={d}>{d}</option>)}
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Action *</label>
                  <input className="form-control" value={form.action}
                    onChange={e=>setForm(f=>({...f,action:e.target.value}))}
                    placeholder="ex: admis, eligible, complet"/>
                </div>
              </div>
              <div className="form-group">
                <label className="form-label">Condition Python *</label>
                <textarea className="form-control font-mono" rows={3} value={form.condition}
                  onChange={e=>setForm(f=>({...f,condition:e.target.value}))}
                  placeholder="contexte['moyenne'] >= 10 and contexte['credits'] >= 60"/>
                <span className="form-hint">Utilisez <code>contexte['cle']</code> pour accéder aux données</span>
              </div>
              <div className="form-group">
                <label className="form-label">Description</label>
                <textarea className="form-control" rows={2} value={form.description}
                  onChange={e=>setForm(f=>({...f,description:e.target.value}))}/>
              </div>
              <div style={{display:'flex',alignItems:'center',gap:10}}>
                <input type="checkbox" id="active" checked={form.active}
                  onChange={e=>setForm(f=>({...f,active:e.target.checked}))}/>
                <label htmlFor="active" style={{fontSize:13,fontWeight:500,cursor:'pointer'}}>Règle active</label>
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn btn-ghost" onClick={()=>setModal(null)}>Annuler</button>
              <button className="btn btn-primary" onClick={sauvegarder} disabled={saving}>
                {saving ? <div className="spinner"/> : 'Sauvegarder'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal tester */}
      {modal === 'test' && (
        <div className="modal-overlay" onClick={()=>setModal(null)}>
          <div className="modal" style={{maxWidth:560}} onClick={e=>e.stopPropagation()}>
            <div className="modal-header">
              <span className="modal-title">Tester — {form.code_regle}</span>
              <button className="btn btn-ghost btn-sm btn-icon" onClick={()=>setModal(null)}>✕</button>
            </div>
            <div className="modal-body">
              <div style={{
                background:'var(--gray-50)', borderRadius:8, padding:'10px 14px',
                fontFamily:'monospace', fontSize:12, marginBottom:16,
                border:'1px solid var(--gray-200)',
              }}>
                {form.condition}
              </div>
              <div className="form-group">
                <label className="form-label">Contexte JSON</label>
                <textarea className="form-control font-mono" rows={5} value={testCtx}
                  onChange={e=>setTestCtx(e.target.value)}
                  placeholder={'{\n  "moyenne": 13.5,\n  "credits": 60\n}'}/>
              </div>
              {testRes && (
                <div className={`alert ${testRes.erreur ? 'alert-danger' : testRes.resultat ? 'alert-success' : 'alert-warning'}`}>
                  {testRes.erreur
                    ? <><XCircle size={15}/> Erreur : {testRes.erreur}</>
                    : testRes.resultat
                    ? <><CheckCircle size={15}/> La règle se déclenche → action : <strong>{form.action}</strong></>
                    : <><XCircle size={15}/> La règle ne se déclenche pas.</>}
                </div>
              )}
            </div>
            <div className="modal-footer">
              <button className="btn btn-ghost" onClick={()=>setModal(null)}>Fermer</button>
              <button className="btn btn-primary" onClick={tester} disabled={saving}>
                {saving ? <div className="spinner"/> : <><Play size={14}/> Tester</>}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
