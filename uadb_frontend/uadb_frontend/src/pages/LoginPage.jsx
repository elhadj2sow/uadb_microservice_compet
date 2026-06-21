import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import toast from 'react-hot-toast'
import { GraduationCap, Shield, FileText, Bell, Eye, EyeOff } from 'lucide-react'

export default function LoginPage() {
  const [form, setForm]         = useState({ username: '', password: '' })
  const [loading, setLoading]   = useState(false)
  const [showPwd, setShowPwd]   = useState(false)
  const { login }               = useAuth()
  const navigate                = useNavigate()

  const handleSubmit = async e => {
    e.preventDefault()
    if (!form.username || !form.password) {
      toast.error('Veuillez remplir tous les champs.')
      return
    }
    setLoading(true)
    try {
      const user = await login(form.username, form.password)
      toast.success(`Bienvenue, ${user.username} !`)
      if (user.roles.includes('admin')) {
        navigate('/admin')
      } else if (user.roles.some(r => ['agent_scolarite','agent_comptable','service_medical','bibliotheque'].includes(r))) {
        navigate('/agent')
      } else if (user.roles.some(r => ['responsable_pedagogique','enseignant'].includes(r))) {
        navigate('/pedagogue')
      } else {
        navigate('/etudiant')
      }
    } catch (err) {
      const msg = err.response?.data?.detail || 'Identifiants incorrects.'
      toast.error(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-page">
      {/* ── Côté gauche ── */}
      <div className="login-left">
        <div className="login-left-content">
          <div className="login-uni-badge">
            <div className="login-uni-dot" />
            <span className="login-uni-text">Université Alioune Diop de Bambey</span>
          </div>
          <h1 className="login-headline">
            Votre parcours<br />
            universitaire <span>réinventé</span>
          </h1>
          <p className="login-desc">
            Gérez vos inscriptions, dossiers, résultats et attestations
            depuis un portail intelligent et intégré.
          </p>
          <div className="login-features">
            {[
              { icon: GraduationCap, text: 'Inscription administrative en ligne' },
              { icon: FileText,      text: 'Dossier numérique et attestations PDF' },
              { icon: Shield,        text: 'Résultats de délibération en temps réel' },
              { icon: Bell,          text: 'Notifications et chatbot IA 24h/24' },
            ].map(({ icon: Icon, text }) => (
              <div className="login-feature" key={text}>
                <div className="login-feature-icon"><Icon size={14} /></div>
                <span>{text}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── Côté droit ── */}
      <div className="login-right">
        <div className="login-form-box">
          <div className="login-form-header">
            <h2 className="login-form-title">Connexion</h2>
            <p className="login-form-sub">Accédez à votre espace personnel</p>
          </div>

          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label className="form-label">Identifiant ou email</label>
              <input
                className="form-control"
                placeholder="Nom d'utilisateur ou email"
                value={form.username}
                onChange={e => setForm(f => ({ ...f, username: e.target.value }))}
                autoComplete="username"
              />
            </div>

            <div className="form-group">
              <label className="form-label">Mot de passe</label>
              <div style={{position:'relative'}}>
                <input
                  className="form-control"
                  type={showPwd ? 'text' : 'password'}
                  placeholder="Votre mot de passe"
                  value={form.password}
                  onChange={e => setForm(f => ({ ...f, password: e.target.value }))}
                  autoComplete="current-password"
                  style={{paddingRight:44}}
                />
                <button
                  type="button"
                  onClick={() => setShowPwd(v => !v)}
                  style={{
                    position:'absolute', right:14, top:'50%', transform:'translateY(-50%)',
                    background:'none', border:'none', cursor:'pointer', color:'var(--gray-400)'
                  }}
                >
                  {showPwd ? <EyeOff size={16}/> : <Eye size={16}/>}
                </button>
              </div>
            </div>

            <button
              type="submit"
              className="btn btn-primary btn-lg btn-block"
              disabled={loading}
              style={{marginTop:8}}
            >
              {loading ? <div className="spinner"/> : 'Se connecter'}
            </button>
          </form>

          <p style={{textAlign:'center',marginTop:20,fontSize:13,color:'var(--gray-400)'}}>
            Pas encore de compte ?{' '}
            <Link to="/register" style={{color:'var(--blue)',fontWeight:600,textDecoration:'none'}}>
              Créer un compte
            </Link>
          </p>

          <p style={{textAlign:'center',marginTop:12,fontSize:12,color:'var(--gray-300)'}}>
            Université Alioune Diop de Bambey — Bambey, Sénégal<br/>
            © 2025 Système d'Information Intelligent
          </p>
        </div>
      </div>
    </div>
  )
}
