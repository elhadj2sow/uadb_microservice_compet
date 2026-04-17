import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './context/AuthContext'
import Layout from './components/layout/Layout'

// Pages publiques
import LoginPage    from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import LandingPage  from './pages/LandingPage'

// Pages étudiant
import DashboardEtudiant from './pages/etudiant/Dashboard'
import MonDossier        from './pages/etudiant/MonDossier'
import MonInscription    from './pages/etudiant/MonInscription'
import MesResultats      from './pages/etudiant/MesResultats'
import MesAttestations   from './pages/etudiant/MesAttestations'
import MesNotifications  from './pages/etudiant/MesNotifications'

// Pages agent
import DashboardAgent    from './pages/agent/Dashboard'
import GestionDossiers   from './pages/agent/GestionDossiers'
import GestionInscriptions from './pages/agent/GestionInscriptions'

// Pages pédagogue / enseignant
import DashboardPedagogue    from './pages/pedagogue/Dashboard'
import GestionDeliberations  from './pages/pedagogue/GestionDeliberations'
import SaisieNotes           from './pages/pedagogue/SaisieNotes'

// Pages admin
import DashboardAdmin    from './pages/admin/Dashboard'
import GestionRegles     from './pages/admin/GestionRegles'
import JournalAudit      from './pages/admin/JournalAudit'

// Pages paiement (accessibles sans rôle, après redirection PayTech)
import PaiementSuccess from './pages/PaiementSuccess'
import PaiementCancel  from './pages/PaiementCancel'

function ProtectedRoute({ children, roles }) {
  const { user, loading } = useAuth()
  if (loading) return <div style={{display:'flex',alignItems:'center',justifyContent:'center',height:'100vh'}}><div className="spinner spinner-dark"/></div>
  if (!user)   return <Navigate to="/login" replace />
  if (roles && !roles.some(r => user.roles.includes(r))) return <Navigate to="/login" replace />
  return children
}

function getRoleHome(user) {
  if (!user) return '/'
  if (user.roles.includes('admin')) return '/admin'
  if (user.roles.some(r => ['agent_scolarite','agent_comptable','service_medical','bibliotheque'].includes(r))) return '/agent'
  if (user.roles.some(r => ['responsable_pedagogique','enseignant'].includes(r))) return '/pedagogue'
  return '/etudiant'
}

export default function App() {
  const { user } = useAuth()

  return (
    <Routes>
      {/* ── Accueil public ── */}
      <Route path="/" element={user ? <Navigate to={getRoleHome(user)} replace /> : <LandingPage />} />

      <Route path="/login"    element={user ? <Navigate to={getRoleHome(user)} replace /> : <LoginPage />} />
      <Route path="/register" element={user ? <Navigate to={getRoleHome(user)} replace /> : <RegisterPage />} />

      {/* ── Étudiant ── */}
      <Route path="/etudiant" element={
        <ProtectedRoute roles={['etudiant']}>
          <Layout role="etudiant" />
        </ProtectedRoute>
      }>
        <Route index                   element={<DashboardEtudiant />} />
        <Route path="dossier"          element={<MonDossier />} />
        <Route path="inscription"      element={<MonInscription />} />
        <Route path="resultats"        element={<MesResultats />} />
        <Route path="attestations"     element={<MesAttestations />} />
        <Route path="notifications"    element={<MesNotifications />} />
      </Route>

      {/* ── Agent ── */}
      <Route path="/agent" element={
        <ProtectedRoute roles={['agent_scolarite','agent_comptable','service_medical','bibliotheque','admin']}>
          <Layout role="agent" />
        </ProtectedRoute>
      }>
        <Route index               element={<DashboardAgent />} />
        <Route path="dossiers"     element={<GestionDossiers />} />
        <Route path="inscriptions" element={<GestionInscriptions />} />
      </Route>

      {/* ── Pédagogue / Enseignant ── */}
      <Route path="/pedagogue" element={
        <ProtectedRoute roles={['responsable_pedagogique','enseignant','admin']}>
          <Layout role="pedagogue" />
        </ProtectedRoute>
      }>
        <Route index                  element={<DashboardPedagogue />} />
        <Route path="deliberations"   element={<GestionDeliberations />} />
        <Route path="notes"           element={<SaisieNotes />} />
      </Route>

      {/* ── Admin ── */}
      <Route path="/admin" element={
        <ProtectedRoute roles={['admin']}>
          <Layout role="admin" />
        </ProtectedRoute>
      }>
        <Route index          element={<DashboardAdmin />} />
        <Route path="regles"  element={<GestionRegles />} />
        <Route path="audit"   element={<JournalAudit />} />
      </Route>

      {/* ── Pages paiement PayTech (sans auth requise) ── */}
      <Route path="/paiement/success" element={<PaiementSuccess />} />
      <Route path="/paiement/cancel"  element={<PaiementCancel />} />

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
