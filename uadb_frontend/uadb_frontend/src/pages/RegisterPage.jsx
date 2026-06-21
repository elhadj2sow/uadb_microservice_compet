import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import api, { BASE } from '../config/api'
import toast from 'react-hot-toast'
import {
  User, Mail, Lock, Phone, Calendar,
  Eye, EyeOff, GraduationCap, CheckCircle,
  ArrowLeft, AlertCircle
} from 'lucide-react'

const ETAPES = ['Compte', 'Identité', 'Confirmation']

const INIT = {
  // Étape 1 — Compte
  username    : '',
  email       : '',
  password    : '',
  password2   : '',
  // Étape 2 — Identité
  nom         : '',
  prenom      : '',
  telephone   : '',
  date_naissance: '',
  lieu_naissance: '',
  sexe        : '',
  nationalite : 'Sénégalaise',
}

export default function RegisterPage() {
  const [etape,    setEtape]    = useState(0)
  const [form,     setForm]     = useState(INIT)
  const [errors,   setErrors]   = useState({})
  const [loading,  setLoading]  = useState(false)
  const [showPwd,  setShowPwd]  = useState(false)
  const [showPwd2, setShowPwd2] = useState(false)
  const navigate = useNavigate()

  const set = (k, v) => {
    setForm(f => ({ ...f, [k]: v }))
    setErrors(e => ({ ...e, [k]: '' }))
  }

  // ── Validation étape 1 ──────────────────────────────────
  const validerEtape1 = () => {
    const errs = {}
    if (!form.username.trim())
      errs.username = 'Le nom d\'utilisateur est requis.'
    else if (form.username.length < 3)
      errs.username = 'Minimum 3 caractères.'
    else if (!/^[a-zA-Z0-9._]+$/.test(form.username))
      errs.username = 'Caractères autorisés : lettres, chiffres, point, underscore.'

    if (!form.email.trim())
      errs.email = 'L\'adresse email est requise.'
    else if (!/^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.(com|fr|sn)$/.test(form.email))
      errs.email = 'Seules les adresses en .com, .fr ou .sn sont acceptées.'

    if (!form.password)
      errs.password = 'Le mot de passe est requis.'
    else if (form.password.length < 8)
      errs.password = 'Minimum 8 caractères.'
    else if (!/[A-Z]/.test(form.password))
      errs.password = 'Au moins une majuscule requise.'
    else if (!/[0-9]/.test(form.password))
      errs.password = 'Au moins un chiffre requis.'

    if (!form.password2)
      errs.password2 = 'Veuillez confirmer votre mot de passe.'
    else if (form.password !== form.password2)
      errs.password2 = 'Les mots de passe ne correspondent pas.'

    setErrors(errs)
    return Object.keys(errs).length === 0
  }

  // ── Validation étape 2 ──────────────────────────────────
  const validerEtape2 = () => {
    const errs = {}
    if (!form.nom.trim())    errs.nom    = 'Le nom est requis.'
    if (!form.prenom.trim()) errs.prenom = 'Le prénom est requis.'
    if (!form.telephone.trim())
      errs.telephone = 'Le téléphone est requis.'
    else if (!/^(\+221|221)?[0-9]{9}$/.test(form.telephone.replace(/\s/g,'')))
      errs.telephone = 'Numéro sénégalais invalide (ex: 77 123 45 67).'
    if (!form.date_naissance)
      errs.date_naissance = 'La date de naissance est requise.'
    if (!form.sexe)
      errs.sexe = 'Le sexe est requis.'
    setErrors(errs)
    return Object.keys(errs).length === 0
  }

  const suivant = () => {
    if (etape === 0 && validerEtape1()) setEtape(1)
    if (etape === 1 && validerEtape2()) setEtape(2)
  }

  const soumettre = async () => {
    setLoading(true)
    try {
      await api.post(`${BASE.auth}/register/`, {
        username      : form.username,
        email         : form.email,
        password      : form.password,
        password_confirm     : form.password2,
        nom           : form.nom,
        prenom        : form.prenom,
        telephone     : form.telephone,
        date_naissance: form.date_naissance,
        lieu_naissance: form.lieu_naissance,
        sexe          : form.sexe,
        nationalite   : form.nationalite,
        role          : 'etudiant',
      })
      toast.success('Compte créé avec succès ! Vous pouvez maintenant vous connecter.')
      navigate('/login')
    } catch (err) {
      const data = err.response?.data
      if (data && typeof data === 'object') {
        // Afficher les erreurs de chaque champ
        const errs = {}
        Object.entries(data).forEach(([k, v]) => {
          errs[k] = Array.isArray(v) ? v[0] : v
        })
        setErrors(errs)
        // Revenir à l'étape concernée
        if (errs.username || errs.email || errs.password)
          setEtape(0)
        else if (errs.nom || errs.prenom || errs.telephone)
          setEtape(1)
        toast.error('Veuillez corriger les erreurs.')
      } else {
        toast.error('Erreur lors de la création du compte.')
      }
    } finally {
      setLoading(false)
    }
  }

  // ── Force du mot de passe ───────────────────────────────
  const forceMotDePasse = () => {
    const p = form.password
    if (!p) return { score: 0, label: '', color: '' }
    let score = 0
    if (p.length >= 8)  score++
    if (p.length >= 12) score++
    if (/[A-Z]/.test(p)) score++
    if (/[0-9]/.test(p)) score++
    if (/[^A-Za-z0-9]/.test(p)) score++
    if (score <= 1) return { score, label: 'Très faible', color: 'var(--danger)' }
    if (score === 2) return { score, label: 'Faible',     color: 'var(--warning)' }
    if (score === 3) return { score, label: 'Moyen',      color: '#f59e0b' }
    if (score === 4) return { score, label: 'Fort',       color: 'var(--success)' }
    return { score, label: 'Très fort', color: 'var(--teal)' }
  }
  const forcePwd = forceMotDePasse()

  return (
    <div className="login-page" style={{gridTemplateColumns:'1fr 1.3fr'}}>

      {/* ── Côté gauche ── */}
      <div className="login-left">
        <div className="login-left-content">
          <div className="login-uni-badge">
            <div className="login-uni-dot"/>
            <span className="login-uni-text">Université Alioune Diop de Bambey</span>
          </div>
          <h1 className="login-headline">
            Rejoignez<br/>l'UADB<br/><span>en ligne</span>
          </h1>
          <p className="login-desc">
            Créez votre compte étudiant en quelques minutes.
            Accédez instantanément au portail d'inscription,
            de gestion de dossier et de suivi de vos résultats.
          </p>

          {/* Indicateur étapes */}
          <div style={{marginTop:36}}>
            <div style={{fontSize:11,color:'rgba(255,255,255,.35)',fontWeight:600,letterSpacing:'.08em',textTransform:'uppercase',marginBottom:16}}>
              Progression
            </div>
            {ETAPES.map((e, i) => (
              <div key={e} style={{
                display:'flex', alignItems:'center', gap:12,
                marginBottom:14, opacity: i > etape ? 0.35 : 1,
                transition:'opacity .3s'
              }}>
                <div style={{
                  width:28, height:28, borderRadius:'50%', flexShrink:0,
                  background: i < etape
                    ? 'var(--teal)'
                    : i === etape
                    ? 'rgba(255,255,255,.15)'
                    : 'rgba(255,255,255,.05)',
                  border: i === etape
                    ? '1.5px solid rgba(255,255,255,.3)'
                    : 'none',
                  display:'flex', alignItems:'center', justifyContent:'center',
                  color:'white', fontSize:12, fontWeight:700,
                }}>
                  {i < etape ? '✓' : i + 1}
                </div>
                <div>
                  <div style={{fontSize:13,fontWeight:600,color:'white'}}>{e}</div>
                  <div style={{fontSize:11,color:'rgba(255,255,255,.35)'}}>
                    {i === 0 && 'Identifiants de connexion'}
                    {i === 1 && 'Informations personnelles'}
                    {i === 2 && 'Vérification et création'}
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div style={{marginTop:32,paddingTop:24,borderTop:'1px solid rgba(255,255,255,.08)'}}>
            <p style={{fontSize:12,color:'rgba(255,255,255,.35)'}}>
              Déjà inscrit ?{' '}
              <Link to="/login" style={{color:'#fbbf24',fontWeight:600}}>
                Se connecter →
              </Link>
            </p>
          </div>
        </div>
      </div>

      {/* ── Côté droit ── */}
      <div className="login-right" style={{alignItems:'flex-start',overflowY:'auto'}}>
        <div style={{width:'100%', maxWidth:480, padding:'20px 0'}}>

          {/* Header formulaire */}
          <div style={{marginBottom:28}}>
            {etape > 0 && (
              <button
                onClick={() => setEtape(e => e - 1)}
                style={{background:'none',border:'none',cursor:'pointer',
                  display:'flex',alignItems:'center',gap:6,
                  color:'var(--gray-400)',fontSize:13,fontWeight:500,
                  marginBottom:16,padding:0}}
              >
                <ArrowLeft size={14}/> Retour
              </button>
            )}
            <div style={{display:'flex',alignItems:'center',gap:10,marginBottom:6}}>
              <div style={{
                width:36,height:36,borderRadius:8,flexShrink:0,
                background:'linear-gradient(135deg,var(--blue),var(--teal))',
                display:'flex',alignItems:'center',justifyContent:'center',
                fontSize:15,fontWeight:800,color:'white'
              }}>U</div>
              <div>
                <div style={{fontSize:11,color:'var(--gray-400)',fontWeight:600,
                  textTransform:'uppercase',letterSpacing:'.05em'}}>
                  Étape {etape + 1} sur {ETAPES.length}
                </div>
              </div>
            </div>
            <h2 style={{fontSize:'1.5rem',fontWeight:800,color:'var(--gray-900)'}}>
              {etape === 0 && 'Créer mon compte'}
              {etape === 1 && 'Mes informations'}
              {etape === 2 && 'Confirmation'}
            </h2>
            <p style={{fontSize:13,color:'var(--gray-400)',marginTop:4}}>
              {etape === 0 && 'Choisissez vos identifiants de connexion'}
              {etape === 1 && 'Complétez vos informations personnelles'}
              {etape === 2 && 'Vérifiez vos informations avant de valider'}
            </p>
          </div>

          {/* Barre de progression */}
          <div style={{display:'flex',gap:4,marginBottom:28}}>
            {ETAPES.map((_, i) => (
              <div key={i} style={{
                flex:1, height:3, borderRadius:2,
                background: i <= etape ? 'var(--blue)' : 'var(--gray-200)',
                transition:'background .3s',
              }}/>
            ))}
          </div>

          {/* ── ÉTAPE 1 — Compte ── */}
          {etape === 0 && (
            <div className="fade-up">
              <div className="form-group">
                <label className="form-label">
                  <span style={{display:'flex',alignItems:'center',gap:6}}>
                    <User size={13}/> Nom d'utilisateur *
                  </span>
                </label>
                <input
                  className="form-control"
                  placeholder="ex: amadou.diallo"
                  value={form.username}
                  onChange={e => set('username', e.target.value)}
                  style={errors.username ? {borderColor:'var(--danger)'} : {}}
                />
                {errors.username
                  ? <span className="form-error">{errors.username}</span>
                  : <span className="form-hint">Lettres, chiffres, point et underscore uniquement</span>
                }
              </div>

              <div className="form-group">
                <label className="form-label">
                  <span style={{display:'flex',alignItems:'center',gap:6}}>
                    <Mail size={13}/> Adresse email *
                  </span>
                </label>
                <input
                  className="form-control"
                  type="email"
                  placeholder="votre@email.com"
                  value={form.email}
                  onChange={e => set('email', e.target.value)}
                  style={errors.email ? {borderColor:'var(--danger)'} : {}}
                />
                {errors.email && <span className="form-error">{errors.email}</span>}
              </div>

              <div className="form-group">
                <label className="form-label">
                  <span style={{display:'flex',alignItems:'center',gap:6}}>
                    <Lock size={13}/> Mot de passe *
                  </span>
                </label>
                <div style={{position:'relative'}}>
                  <input
                    className="form-control"
                    type={showPwd ? 'text' : 'password'}
                    placeholder="Minimum 8 caractères"
                    value={form.password}
                    onChange={e => set('password', e.target.value)}
                    style={{
                      paddingRight:44,
                      ...(errors.password ? {borderColor:'var(--danger)'} : {})
                    }}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPwd(v => !v)}
                    style={{position:'absolute',right:12,top:'50%',transform:'translateY(-50%)',
                      background:'none',border:'none',cursor:'pointer',color:'var(--gray-400)'}}
                  >
                    {showPwd ? <EyeOff size={15}/> : <Eye size={15}/>}
                  </button>
                </div>
                {/* Indicateur force */}
                {form.password && (
                  <div style={{marginTop:8}}>
                    <div style={{display:'flex',gap:3,marginBottom:4}}>
                      {[1,2,3,4,5].map(i => (
                        <div key={i} style={{
                          flex:1, height:3, borderRadius:2,
                          background: i <= forcePwd.score
                            ? forcePwd.color
                            : 'var(--gray-200)',
                          transition:'all .2s'
                        }}/>
                      ))}
                    </div>
                    <span style={{fontSize:11,color:forcePwd.color,fontWeight:600}}>
                      {forcePwd.label}
                    </span>
                  </div>
                )}
                {errors.password && <span className="form-error">{errors.password}</span>}
                {!errors.password && (
                  <div style={{marginTop:6,fontSize:11,color:'var(--gray-400)'}}>
                    Requis : 8 caractères minimum, 1 majuscule, 1 chiffre
                  </div>
                )}
              </div>

              <div className="form-group">
                <label className="form-label">
                  <span style={{display:'flex',alignItems:'center',gap:6}}>
                    <Lock size={13}/> Confirmer le mot de passe *
                  </span>
                </label>
                <div style={{position:'relative'}}>
                  <input
                    className="form-control"
                    type={showPwd2 ? 'text' : 'password'}
                    placeholder="Répétez votre mot de passe"
                    value={form.password2}
                    onChange={e => set('password2', e.target.value)}
                    style={{
                      paddingRight:44,
                      ...(errors.password2 ? {borderColor:'var(--danger)'} : {}),
                      ...(form.password2 && form.password === form.password2
                        ? {borderColor:'var(--success)'}
                        : {})
                    }}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPwd2(v => !v)}
                    style={{position:'absolute',right:12,top:'50%',transform:'translateY(-50%)',
                      background:'none',border:'none',cursor:'pointer',color:'var(--gray-400)'}}
                  >
                    {showPwd2 ? <EyeOff size={15}/> : <Eye size={15}/>}
                  </button>
                </div>
                {errors.password2 && <span className="form-error">{errors.password2}</span>}
                {form.password2 && form.password === form.password2 && (
                  <span style={{fontSize:11,color:'var(--success)',display:'flex',alignItems:'center',gap:4,marginTop:4}}>
                    <CheckCircle size={12}/> Mots de passe identiques
                  </span>
                )}
              </div>

              <button
                className="btn btn-primary btn-lg btn-block"
                onClick={suivant}
                style={{marginTop:8}}
              >
                Continuer →
              </button>
            </div>
          )}

          {/* ── ÉTAPE 2 — Identité ── */}
          {etape === 1 && (
            <div className="fade-up">
              <div className="grid-2">
                <div className="form-group">
                  <label className="form-label">
                    <span style={{display:'flex',alignItems:'center',gap:6}}>
                      <User size={13}/> Nom de famille *
                    </span>
                  </label>
                  <input
                    className="form-control"
                    placeholder="DIALLO"
                    value={form.nom}
                    onChange={e => set('nom', e.target.value.toUpperCase())}
                    style={errors.nom ? {borderColor:'var(--danger)'} : {}}
                  />
                  {errors.nom && <span className="form-error">{errors.nom}</span>}
                </div>

                <div className="form-group">
                  <label className="form-label">Prénom *</label>
                  <input
                    className="form-control"
                    placeholder="Amadou"
                    value={form.prenom}
                    onChange={e => set('prenom', e.target.value)}
                    style={errors.prenom ? {borderColor:'var(--danger)'} : {}}
                  />
                  {errors.prenom && <span className="form-error">{errors.prenom}</span>}
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">
                  <span style={{display:'flex',alignItems:'center',gap:6}}>
                    <Phone size={13}/> Téléphone *
                  </span>
                </label>
                <input
                  className="form-control"
                  placeholder="77 123 45 67"
                  value={form.telephone}
                  onChange={e => set('telephone', e.target.value)}
                  style={errors.telephone ? {borderColor:'var(--danger)'} : {}}
                />
                {errors.telephone
                  ? <span className="form-error">{errors.telephone}</span>
                  : <span className="form-hint">Format sénégalais : 7X XXX XX XX</span>
                }
              </div>

              <div className="grid-2">
                <div className="form-group">
                  <label className="form-label">
                    <span style={{display:'flex',alignItems:'center',gap:6}}>
                      <Calendar size={13}/> Date de naissance *
                    </span>
                  </label>
                  <input
                    className="form-control"
                    type="date"
                    value={form.date_naissance}
                    onChange={e => set('date_naissance', e.target.value)}
                    style={errors.date_naissance ? {borderColor:'var(--danger)'} : {}}
                  />
                  {errors.date_naissance && <span className="form-error">{errors.date_naissance}</span>}
                </div>

                <div className="form-group">
                  <label className="form-label">Sexe *</label>
                  <select
                    className="form-control"
                    value={form.sexe}
                    onChange={e => set('sexe', e.target.value)}
                    style={errors.sexe ? {borderColor:'var(--danger)'} : {}}
                  >
                    <option value="">-- Choisir --</option>
                    <option value="M">Masculin</option>
                    <option value="F">Féminin</option>
                  </select>
                  {errors.sexe && <span className="form-error">{errors.sexe}</span>}
                </div>
              </div>

              <div className="grid-2">
                <div className="form-group">
                  <label className="form-label">Lieu de naissance</label>
                  <input
                    className="form-control"
                    placeholder="Bambey"
                    value={form.lieu_naissance}
                    onChange={e => set('lieu_naissance', e.target.value)}
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Nationalité</label>
                  <input
                    className="form-control"
                    value={form.nationalite}
                    onChange={e => set('nationalite', e.target.value)}
                  />
                </div>
              </div>

              <div style={{display:'flex',gap:10,marginTop:8}}>
                <button
                  className="btn btn-ghost btn-lg"
                  onClick={() => setEtape(0)}
                  style={{flex:1}}
                >
                  ← Retour
                </button>
                <button
                  className="btn btn-primary btn-lg"
                  onClick={suivant}
                  style={{flex:2}}
                >
                  Continuer →
                </button>
              </div>
            </div>
          )}

          {/* ── ÉTAPE 3 — Confirmation ── */}
          {etape === 2 && (
            <div className="fade-up">
              {/* Récapitulatif */}
              <div style={{
                background:'var(--gray-50)', borderRadius:12,
                border:'1px solid var(--gray-200)', padding:20,
                marginBottom:20,
              }}>
                {/* Avatar initiales */}
                <div style={{display:'flex',alignItems:'center',gap:14,marginBottom:18,
                  paddingBottom:14,borderBottom:'1px solid var(--gray-200)'}}>
                  <div style={{
                    width:52,height:52,borderRadius:'50%',
                    background:'linear-gradient(135deg,var(--blue),var(--teal))',
                    display:'flex',alignItems:'center',justifyContent:'center',
                    fontSize:18,fontWeight:800,color:'white',flexShrink:0
                  }}>
                    {(form.prenom[0]||'?').toUpperCase()}{(form.nom[0]||'').toUpperCase()}
                  </div>
                  <div>
                    <div style={{fontSize:16,fontWeight:800,color:'var(--gray-900)'}}>
                      {form.prenom} {form.nom}
                    </div>
                    <div style={{fontSize:13,color:'var(--gray-400)',marginTop:2}}>
                      Futur étudiant UADB
                    </div>
                  </div>
                </div>

                <div style={{display:'grid',gridTemplateColumns:'auto 1fr',gap:'8px 16px',alignItems:'center'}}>
                  {[
                    ['Identifiant',   form.username],
                    ['Email',         form.email],
                    ['Téléphone',     form.telephone],
                    ['Naissance',     form.date_naissance],
                    ['Lieu',          form.lieu_naissance || '—'],
                    ['Sexe',          form.sexe === 'M' ? 'Masculin' : 'Féminin'],
                    ['Nationalité',   form.nationalite],
                  ].map(([label, value]) => (
                    <>
                      <span key={`l-${label}`} style={{fontSize:11,color:'var(--gray-400)',fontWeight:600,textTransform:'uppercase',letterSpacing:'.04em'}}>
                        {label}
                      </span>
                      <span key={`v-${label}`} style={{fontSize:13,color:'var(--gray-700)',fontWeight:500}}>
                        {value}
                      </span>
                    </>
                  ))}
                </div>
              </div>

              {/* Alerte info */}
              <div style={{
                display:'flex',gap:10,alignItems:'flex-start',
                padding:'12px 14px',borderRadius:10,
                background:'var(--info-bg)',border:'1px solid #bae6fd',
                marginBottom:20,fontSize:12.5,color:'var(--info)',
              }}>
                <AlertCircle size={15} style={{flexShrink:0,marginTop:1}}/>
                <span>
                  En créant ce compte, vous acceptez le règlement intérieur
                  de l'UADB. Votre compte sera activé avec le rôle étudiant.
                </span>
              </div>

              {/* Boutons */}
              <div style={{display:'flex',gap:10}}>
                <button
                  className="btn btn-ghost btn-lg"
                  onClick={() => setEtape(1)}
                  style={{flex:1}}
                >
                  ← Modifier
                </button>
                <button
                  className="btn btn-primary btn-lg"
                  onClick={soumettre}
                  disabled={loading}
                  style={{flex:2}}
                >
                  {loading
                    ? <div className="spinner"/>
                    : <><GraduationCap size={16}/> Créer mon compte</>
                  }
                </button>
              </div>
            </div>
          )}

          {/* Lien connexion */}
          <p style={{
            textAlign:'center', marginTop:24,
            fontSize:13, color:'var(--gray-400)'
          }}>
            Déjà un compte ?{' '}
            <Link to="/login" style={{color:'var(--blue)',fontWeight:600,textDecoration:'none'}}>
              Se connecter
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}
