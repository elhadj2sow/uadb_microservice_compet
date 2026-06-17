import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { useAuth } from '../../context/AuthContext'
import {
  LayoutDashboard, FolderOpen, ClipboardList, BookOpen,
  FileText, Bell, LogOut, Settings, Users, Shield,
  FileCheck, ChevronRight, BookMarked, BarChart2, Sliders, GraduationCap
} from 'lucide-react'
import Chatbot from '../ui/Chatbot'
import api, { BASE } from '../../config/api'

const NAV = {
  etudiant: [
    { label: 'Tableau de bord', icon: LayoutDashboard, to: '/etudiant' },
    { label: 'Mon Dossier',     icon: FolderOpen,      to: '/etudiant/dossier' },
    { label: 'Inscription',     icon: ClipboardList,   to: '/etudiant/inscription' },
    { label: 'Résultats',       icon: BookOpen,        to: '/etudiant/resultats' },
    { label: 'Attestations',    icon: FileText,        to: '/etudiant/attestations' },
    { label: 'Notifications',   icon: Bell,            to: '/etudiant/notifications', badge: true },
  ],
  agent: [
    { label: 'Tableau de bord', icon: LayoutDashboard, to: '/agent' },
    { label: 'Dossiers',        icon: FolderOpen,      to: '/agent/dossiers' },
    { label: 'Inscriptions',    icon: ClipboardList,   to: '/agent/inscriptions' },
    { label: 'Bibliothèque',    icon: BookMarked,      to: '/agent/bibliotheque' },
  ],
  admin: [
    { label: 'Tableau de bord',     icon: LayoutDashboard, to: '/admin' },
    { label: 'Utilisateurs',        icon: Users,           to: '/admin/utilisateurs' },
    { label: 'Formations & UE',     icon: GraduationCap,   to: '/admin/formations' },
    { label: 'Règles IA',           icon: Sliders,         to: '/admin/regles' },
    { label: 'Notifications',       icon: Bell,            to: '/admin/notifications' },
    { label: 'Journal d\'audit',    icon: Shield,          to: '/admin/audit' },
  ],
  pedagogue: [
    { label: 'Tableau de bord', icon: LayoutDashboard, to: '/pedagogue' },
    { label: 'Délibérations',   icon: BookOpen,        to: '/pedagogue/deliberations' },
    { label: 'Saisie des notes',icon: FileText,        to: '/pedagogue/notes' },
  ],
}

export default function Layout({ role }) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const nav = NAV[role] || []
  const [nbNonLues, setNbNonLues] = useState(0)

  useEffect(() => {
    if (role !== 'etudiant') return
    const charger = () => {
      api.get(`${BASE.notification}/mes-notifications/`)
        .then(r => {
          // La vue retourne { count, non_lues, results }
          setNbNonLues(r.data.non_lues || 0)
        })
        .catch(() => {})
    }
    charger()
    const interval = setInterval(charger, 60000) // rafraîchir toutes les minutes
    return () => clearInterval(interval)
  }, [role])

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  const initials = (user?.username || 'U').slice(0,2).toUpperCase()
  const roleLabel = {
    etudiant: 'Étudiant',
    agent_scolarite: 'Agent Scolarité',
    admin: 'Administrateur',
    agent_comptable: 'Agent Comptable',
    service_medical: 'Service Médical',
    bibliotheque: 'Bibliothèque',
    responsable_pedagogique: 'Resp. Pédagogique',
    enseignant: 'Enseignant',
  }[user?.roles?.[0]] || user?.roles?.[0] || 'Utilisateur'

  return (
    <div className="app-shell">
      {/* ── Sidebar ── */}
      <aside className="sidebar">
        <div className="sidebar-logo">
          <div className="sidebar-brand">
            <div className="sidebar-brand-icon">U</div>
            <div className="sidebar-brand-text">
              <div className="sidebar-brand-title">UADB</div>
              <div className="sidebar-brand-sub">Système Intelligent</div>
            </div>
          </div>
        </div>

        <nav className="sidebar-nav">
          <div className="nav-section-title">Navigation</div>
          {nav.map(item => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/' || item.to === '/agent' || item.to === '/admin'}
              className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
            >
              <item.icon size={16} />
              {item.label}
              {item.badge && nbNonLues > 0 && <span className="nav-badge">{nbNonLues}</span>}
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div className="user-card" onClick={handleLogout} title="Se déconnecter">
            <div className="user-avatar">{initials}</div>
            <div style={{flex:1,minWidth:0}}>
              <div className="user-name">{user?.username}</div>
              <div className="user-role">{roleLabel}</div>
            </div>
            <LogOut size={14} style={{color:'rgba(255,255,255,.3)',flexShrink:0}} />
          </div>
        </div>
      </aside>

      {/* ── Header ── */}
      <header className="header" style={{marginLeft: 'var(--sidebar-w)'}}>
        <div>
          <div className="header-breadcrumb">
            <span>UADB</span>
            <ChevronRight size={13} />
            <span style={{color:'var(--gray-600)',fontWeight:600}}>Portail</span>
          </div>
        </div>
        <div className="header-actions">
          <div style={{
            width:34, height:34, borderRadius:8,
            background:'var(--gray-100)',
            display:'flex', alignItems:'center', justifyContent:'center',
            color:'var(--gray-400)', cursor:'pointer'
          }}>
            <Bell size={16} />
          </div>
          <div style={{
            display:'flex', alignItems:'center', gap:8,
            background:'var(--gray-100)', borderRadius:8,
            padding:'6px 12px', cursor:'pointer'
          }}>
            <div style={{
              width:26, height:26, borderRadius:'50%',
              background:'linear-gradient(135deg,var(--blue),var(--teal))',
              display:'flex', alignItems:'center', justifyContent:'center',
              fontSize:11, fontWeight:700, color:'white'
            }}>{initials}</div>
            <span style={{fontSize:13,fontWeight:600,color:'var(--gray-700)'}}>{user?.username}</span>
          </div>
        </div>
      </header>

      {/* ── Main ── */}
      <main className="main-area" style={{marginLeft:'var(--sidebar-w)'}}>
        <Outlet />
      </main>

      {/* ── Chatbot flottant (étudiant seulement) ── */}
      {role === 'etudiant' && <Chatbot />}
    </div>
  )
}
