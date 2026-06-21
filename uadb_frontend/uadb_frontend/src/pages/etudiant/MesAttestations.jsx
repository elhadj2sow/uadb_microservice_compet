import { useState, useEffect } from 'react'
import api, { BASE } from '../../config/api'
import toast from 'react-hot-toast'
import { FileText, Download, Plus, CheckCircle, Clock, XCircle } from 'lucide-react'

const TYPES = [
  { value: 'inscription',  label: "Attestation d'inscription",  icon: '🎓' },
  { value: 'scolarite',    label: 'Certificat de scolarité',     icon: '📋' },
  { value: 'passage',      label: 'Attestation de passage',      icon: '⬆️' },
  { value: 'reussite',     label: 'Attestation de réussite',     icon: '🏆' },
  { value: 'releve_notes', label: 'Relevé de notes',             icon: '📊' },
]
const STATUT_ICON = {
  generee: <CheckCircle size={14} color="var(--success)"/>,
  refusee: <XCircle size={14} color="var(--danger)"/>,
  en_attente: <Clock size={14} color="var(--warning)"/>,
  approuvee: <Clock size={14} color="var(--info)"/>,
}

export default function MesAttestations() {
  const [demandes,  setDemandes]  = useState([])
  const [loading,   setLoading]   = useState(true)
  const [requesting,setRequesting]= useState(null)
  const anneeCourante = `${new Date().getFullYear()}-${new Date().getFullYear()+1}`
  const [anneeSelectionnee, setAnneeSelectionnee] = useState(anneeCourante)
  const anneesDisponibles = [
    `${new Date().getFullYear()-1}-${new Date().getFullYear()}`,
    anneeCourante,
    `${new Date().getFullYear()+1}-${new Date().getFullYear()+2}`,
  ]

  useEffect(() => {
    api.get(`${BASE.attestation}/mes-demandes/`)
      .then(r => setDemandes(r.data.results || []))
      .finally(() => setLoading(false))
  }, [])

  const demanderAttestation = async type => {
    setRequesting(type)
    try {
      const r = await api.post(`${BASE.attestation}/demandes/`, {
        type_attestation   : type,
        annee_universitaire: anneeSelectionnee,
      })
      setDemandes(d => [r.data.demande, ...d.filter(x => x.id !== r.data.demande?.id)])
      if (r.data.demande?.statut === 'generee') {
        toast.success('Attestation générée ! Vous pouvez la télécharger.')
      } else if (r.data.demande?.statut === 'refusee') {
        toast.error(`Refusée : ${r.data.demande.motif_refus}`)
      } else {
        toast.success('Demande traitée.')
      }
    } catch (e) {
      // Même en cas d'erreur réseau, l'attestation a pu être générée côté serveur
      toast.error(e.response?.data?.detail || 'Génération en cours, vérifiez la liste ci-dessous.')
      // Recharger la liste pour voir si l'attestation a été créée
      try {
        const r2 = await api.get(`${BASE.attestation}/mes-demandes/`)
        setDemandes(r2.data.results || [])
      } catch {}
    } finally { setRequesting(null) }
  }

  const telecharger = async (attestationId) => {
    try {
      const r = await api.get(`${BASE.attestation}/${attestationId}/telecharger/`)
      window.open(r.data.url, '_blank')
    } catch { toast.error('Impossible de télécharger.') }
  }

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Mes Attestations</h1>
        <p className="page-subtitle">Demandez et téléchargez vos documents officiels</p>
      </div>

      {/* Types disponibles */}
      <div className="card fade-up" style={{marginBottom:20}}>
        <div className="card-header">
          <span className="card-title">Demander une attestation</span>
          <select
            value={anneeSelectionnee}
            onChange={e => setAnneeSelectionnee(e.target.value)}
            style={{padding:'4px 10px',borderRadius:8,border:'1.5px solid var(--gray-200)',fontSize:13,fontWeight:600,color:'var(--gray-700)',cursor:'pointer'}}
          >
            {anneesDisponibles.map(a => (
              <option key={a} value={a}>{a}</option>
            ))}
          </select>
        </div>
        <div className="card-body">
          <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(180px,1fr))',gap:12}}>
            {TYPES.map(t => (
              <button
                key={t.value}
                className="btn btn-ghost"
                style={{
                  flexDirection:'column', height:'auto', padding:'16px',
                  gap:8, border:'1.5px solid var(--gray-200)',
                  borderRadius:12, transition:'all .18s',
                }}
                onClick={() => demanderAttestation(t.value)}
                disabled={requesting === t.value}
                onMouseEnter={e=>{e.currentTarget.style.borderColor='var(--blue)';e.currentTarget.style.background='var(--info-bg)'}}
                onMouseLeave={e=>{e.currentTarget.style.borderColor='var(--gray-200)';e.currentTarget.style.background=''}}
              >
                <span style={{fontSize:24}}>{t.icon}</span>
                <span style={{fontSize:12,fontWeight:600,color:'var(--gray-700)',textAlign:'center',lineHeight:1.3}}>
                  {t.label}
                </span>
                {requesting === t.value ? (
                  <div className="spinner spinner-dark" style={{width:16,height:16}}/>
                ) : (
                  <Plus size={14} style={{color:'var(--blue)'}}/>
                )}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Historique des demandes */}
      <div className="card fade-up" style={{animationDelay:'100ms'}}>
        <div className="card-header">
          <span className="card-title">Mes demandes</span>
          <span className="badge badge-navy">{demandes.length}</span>
        </div>
        {loading ? (
          <div className="card-body">
            {[1,2,3].map(i=><div key={i} className="skeleton" style={{height:60,marginBottom:12,borderRadius:8}}/>)}
          </div>
        ) : demandes.length === 0 ? (
          <div className="card-body"><div className="empty-state">
            <div className="empty-state-icon"><FileText size={30}/></div>
            <p>Aucune demande d'attestation pour le moment.</p>
          </div></div>
        ) : (
          <div style={{padding:'8px 0'}}>
            {demandes.map((d, i) => (
              <div key={d.id} style={{
                display:'flex', alignItems:'center', gap:14,
                padding:'14px 24px',
                borderBottom: i<demandes.length-1 ? '1px solid var(--gray-100)' : 'none'
              }}>
                <div style={{
                  width:38, height:38, borderRadius:8, flexShrink:0,
                  background:'var(--gray-50)',
                  display:'flex',alignItems:'center',justifyContent:'center',
                  fontSize:18
                }}>
                  {TYPES.find(t=>t.value===d.type_attestation)?.icon || '📄'}
                </div>
                <div style={{flex:1}}>
                  <div style={{fontSize:14,fontWeight:600,color:'var(--gray-800)'}}>{d.type_label}</div>
                  <div style={{fontSize:12,color:'var(--gray-400)',marginTop:2}}>
                    {d.annee_universitaire} • {new Date(d.date_demande).toLocaleDateString('fr-FR')}
                    {d.attestation?.numero_ordre && (
                      <span style={{fontFamily:'monospace',marginLeft:8,color:'var(--blue)'}}>
                        {d.attestation.numero_ordre}
                      </span>
                    )}
                  </div>
                  {d.motif_refus && (
                    <div style={{fontSize:12,color:'var(--danger)',marginTop:3}}>{d.motif_refus}</div>
                  )}
                </div>
                <div style={{display:'flex',alignItems:'center',gap:8}}>
                  {STATUT_ICON[d.statut]}
                  <span className={`badge badge-${d.statut==='generee'?'success':d.statut==='refusee'?'danger':d.statut==='approuvee'?'info':'warning'}`}>
                    {d.statut}
                  </span>
                  {d.statut === 'generee' && d.attestation && (
                    <button className="btn btn-primary btn-sm"
                      onClick={() => telecharger(d.attestation.id)}>
                      <Download size={13}/> PDF
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
