import { useState, useEffect } from 'react'
import api, { BASE } from '../../config/api'
import { Search, Eye, Shield } from 'lucide-react'

const NIVEAUX = { INFO:'info', WARNING:'warning', ERROR:'danger', CRITICAL:'danger' }
const STATUTS = { succes:'success', echec:'danger', partiel:'warning' }

export default function JournalAudit() {
  const [entries, setEntries] = useState([])
  const [total,   setTotal]   = useState(0)
  const [loading, setLoading] = useState(true)
  const [filters, setFilters] = useState({ action:'', service:'', niveau:'', statut:'', date_debut:'', date_fin:'' })
  const [selected,setSelected]= useState(null)
  const [offset,  setOffset]  = useState(0)
  const LIMIT = 50

  const charger = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams({ limit: LIMIT, offset })
      Object.entries(filters).forEach(([k,v]) => v && params.append(k, v))
      const r = await api.get(`${BASE.audit}/journal/?${params}`)
      setEntries(r.data.results || [])
      setTotal(r.data.count    || 0)
    } finally { setLoading(false) }
  }

  useEffect(() => { charger() }, [offset, filters])

  const setFilter = (k, v) => { setFilters(f=>({...f,[k]:v})); setOffset(0) }

  return (
    <div className="page">
      <div className="page-header flex items-center justify-between">
        <div>
          <h1 className="page-title">Journal d'Audit</h1>
          <p className="page-subtitle">{total} entrée(s) dans le journal</p>
        </div>
        <div style={{display:'flex',alignItems:'center',gap:8}}>
          <Shield size={16} style={{color:'var(--blue)'}}/>
          <span style={{fontSize:13,color:'var(--gray-400)'}}>Lecture seule</span>
        </div>
      </div>

      {/* Filtres */}
      <div className="card fade-up" style={{marginBottom:20}}>
        <div className="card-padded" style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(150px,1fr))',gap:10}}>
          <select className="form-control" value={filters.action} onChange={e=>setFilter('action',e.target.value)}>
            <option value="">Toutes actions</option>
            {['LOGIN','LOGOUT','LOGIN_ECHEC','CREATE','UPDATE','DELETE','VALIDATE','REJECT',
              'UPLOAD','DOWNLOAD','GENERATE','DECISION_AUTO','ALERTE','WORKFLOW_START','WORKFLOW_END'].map(a=>
              <option key={a} value={a}>{a}</option>)}
          </select>
          <select className="form-control" value={filters.service} onChange={e=>setFilter('service',e.target.value)}>
            <option value="">Tous services</option>
            {['auth','inscription','dossier','deliberation','attestation','notification','ia','audit'].map(s=>
              <option key={s} value={s}>{s}</option>)}
          </select>
          <select className="form-control" value={filters.niveau} onChange={e=>setFilter('niveau',e.target.value)}>
            <option value="">Tous niveaux</option>
            {['INFO','WARNING','ERROR','CRITICAL'].map(n=><option key={n}>{n}</option>)}
          </select>
          <select className="form-control" value={filters.statut} onChange={e=>setFilter('statut',e.target.value)}>
            <option value="">Tous statuts</option>
            {['succes','echec','partiel'].map(s=><option key={s}>{s}</option>)}
          </select>
          <input className="form-control" type="date" value={filters.date_debut}
            onChange={e=>setFilter('date_debut',e.target.value)} placeholder="Date début"/>
          <input className="form-control" type="date" value={filters.date_fin}
            onChange={e=>setFilter('date_fin',e.target.value)} placeholder="Date fin"/>
        </div>
      </div>

      {/* Table */}
      <div className="card fade-up" style={{animationDelay:'80ms'}}>
        {loading ? (
          <div className="card-body">
            {[1,2,3,4,5].map(i=><div key={i} className="skeleton" style={{height:50,marginBottom:10,borderRadius:8}}/>)}
          </div>
        ) : (
          <>
            <div className="table-wrap">
              <table>
                <thead><tr>
                  <th>Date</th><th>Action</th><th>Acteur</th>
                  <th>Service</th><th>Niveau</th><th>Statut</th>
                  <th>Ressource</th><th>IP</th><th></th>
                </tr></thead>
                <tbody>
                  {entries.map(e => (
                    <tr key={e.id}>
                      <td style={{fontSize:11,color:'var(--gray-400)',whiteSpace:'nowrap',fontFamily:'monospace'}}>
                        {new Date(e.date_action).toLocaleString('fr-FR')}
                      </td>
                      <td>
                        <span className="chip" style={{fontSize:11,fontFamily:'monospace'}}>
                          {e.action}
                        </span>
                      </td>
                      <td style={{fontSize:13,fontWeight:600}}>{e.acteur || '—'}</td>
                      <td>
                        <span className="badge badge-navy" style={{fontSize:11}}>{e.service||'—'}</span>
                      </td>
                      <td>
                        <span className={`badge badge-${NIVEAUX[e.niveau]||'neutral'}`} style={{fontSize:11}}>
                          {e.niveau}
                        </span>
                      </td>
                      <td>
                        <span className={`badge badge-${STATUTS[e.statut]||'neutral'}`} style={{fontSize:11}}>
                          {e.statut}
                        </span>
                      </td>
                      <td style={{fontSize:12,color:'var(--gray-400)',maxWidth:140,overflow:'hidden',textOverflow:'ellipsis',whiteSpace:'nowrap'}}>
                        {e.ressource || '—'}
                      </td>
                      <td style={{fontSize:11,fontFamily:'monospace',color:'var(--gray-400)'}}>
                        {e.adresse_ip || '—'}
                      </td>
                      <td>
                        <button className="btn btn-ghost btn-sm btn-icon" onClick={()=>setSelected(e)}>
                          <Eye size={13}/>
                        </button>
                      </td>
                    </tr>
                  ))}
                  {!entries.length && (
                    <tr><td colSpan={9} style={{textAlign:'center',padding:32,color:'var(--gray-300)'}}>
                      Aucune entrée pour ces filtres
                    </td></tr>
                  )}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            <div style={{display:'flex',alignItems:'center',justifyContent:'space-between',padding:'14px 20px',borderTop:'1px solid var(--gray-100)'}}>
              <span style={{fontSize:13,color:'var(--gray-400)'}}>
                {offset + 1}–{Math.min(offset + LIMIT, total)} sur {total}
              </span>
              <div style={{display:'flex',gap:8}}>
                <button className="btn btn-ghost btn-sm" disabled={offset===0}
                  onClick={()=>setOffset(o=>Math.max(0,o-LIMIT))}>← Précédent</button>
                <button className="btn btn-ghost btn-sm" disabled={offset+LIMIT>=total}
                  onClick={()=>setOffset(o=>o+LIMIT)}>Suivant →</button>
              </div>
            </div>
          </>
        )}
      </div>

      {/* Modal détail */}
      {selected && (
        <div className="modal-overlay" onClick={()=>setSelected(null)}>
          <div className="modal" style={{maxWidth:580}} onClick={e=>e.stopPropagation()}>
            <div className="modal-header">
              <span className="modal-title">Entrée d'audit #{selected.id}</span>
              <button className="btn btn-ghost btn-sm btn-icon" onClick={()=>setSelected(null)}>✕</button>
            </div>
            <div className="modal-body" style={{display:'flex',flexDirection:'column',gap:14}}>
              {[
                ['Date',       new Date(selected.date_action).toLocaleString('fr-FR')],
                ['Action',     selected.action],
                ['Acteur',     selected.acteur || '—'],
                ['Rôle',       selected.role_acteur || '—'],
                ['Service',    selected.service || '—'],
                ['Niveau',     selected.niveau],
                ['Statut',     selected.statut],
                ['Ressource',  selected.ressource || '—'],
                ['IP',         selected.adresse_ip || '—'],
                ['URL',        selected.url || '—'],
                ['Méthode',    selected.methode_http || '—'],
                ['Description',selected.description || '—'],
              ].map(([label, value]) => (
                <div key={label} style={{display:'flex',gap:16}}>
                  <div style={{width:100,fontSize:12,color:'var(--gray-400)',fontWeight:600,flexShrink:0,paddingTop:1}}>
                    {label}
                  </div>
                  <div style={{fontSize:13,color:'var(--gray-700)',wordBreak:'break-all',flex:1}}>
                    {value}
                  </div>
                </div>
              ))}
              {selected.details && (
                <div>
                  <div style={{fontSize:12,color:'var(--gray-400)',fontWeight:600,marginBottom:6}}>Détails</div>
                  <pre style={{
                    background:'var(--gray-50)', borderRadius:8, padding:'10px 12px',
                    fontSize:11, fontFamily:'monospace', overflow:'auto',
                    border:'1px solid var(--gray-200)', maxHeight:150,
                  }}>
                    {JSON.stringify(selected.details, null, 2)}
                  </pre>
                </div>
              )}
              {selected.message_erreur && (
                <div className="alert alert-danger" style={{fontSize:12}}>
                  {selected.message_erreur}
                </div>
              )}
            </div>
            <div className="modal-footer">
              <button className="btn btn-ghost" onClick={()=>setSelected(null)}>Fermer</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
