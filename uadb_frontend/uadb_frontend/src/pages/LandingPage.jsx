import { Link } from 'react-router-dom'
import {
  GraduationCap, FolderOpen, ClipboardList, BookOpen,
  FileText, Bell, Shield, Cpu, BarChart2, CheckCircle,
  ArrowRight, Zap, Search, Lock, Sparkles, Users
} from 'lucide-react'

// ── CSS Animations ────────────────────────────────────────
const GLOBAL_STYLES = `
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

  * { box-sizing: border-box; margin: 0; padding: 0; }

  @keyframes fadeUp {
    from { opacity: 0; transform: translateY(28px); }
    to   { opacity: 1; transform: translateY(0); }
  }
  @keyframes fadeIn {
    from { opacity: 0; }
    to   { opacity: 1; }
  }
  @keyframes pulse-dot {
    0%, 100% { opacity: 1; transform: scale(1); }
    50%       { opacity: .5; transform: scale(1.4); }
  }
  @keyframes gradientShift {
    0%   { background-position: 0% 50%; }
    50%  { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
  }
  @keyframes floatOrb {
    0%, 100% { transform: translateY(0) scale(1); }
    50%       { transform: translateY(-18px) scale(1.04); }
  }
  @keyframes spin-slow {
    from { transform: rotate(0deg); }
    to   { transform: rotate(360deg); }
  }
  @keyframes shimmer {
    0%   { background-position: -200% center; }
    100% { background-position:  200% center; }
  }
  @keyframes blink {
    0%, 100% { opacity: 1; }
    50%       { opacity: 0; }
  }

  .hero-animate { animation: fadeUp .8s ease both; }
  .hero-animate-2 { animation: fadeUp .8s .15s ease both; }
  .hero-animate-3 { animation: fadeUp .8s .3s ease both; }
  .hero-animate-4 { animation: fadeUp .8s .45s ease both; }

  .nav-link {
    font-size: 13px; font-weight: 500;
    color: rgba(255,255,255,.55);
    padding: 6px 12px; border-radius: 6px;
    cursor: pointer; border: none; background: none;
    transition: color .2s, background .2s;
    text-decoration: none; display: inline-block;
  }
  .nav-link:hover { color: #fff; background: rgba(255,255,255,.07); }

  .stat-card {
    background: #fff; padding: 28px 24px; text-align: center;
    transition: transform .25s, box-shadow .25s;
    position: relative; overflow: hidden;
  }
  .stat-card::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0;
    height: 3px; background: linear-gradient(90deg,#1565c0,#38bdf8);
  }
  .stat-card:hover { transform: translateY(-4px); box-shadow: 0 16px 40px rgba(21,101,192,.12); }

  .service-card {
    background: #fff; border-radius: 16px;
    border: 1px solid #e2e8f0; padding: 22px;
    transition: all .25s; cursor: pointer; position: relative; overflow: hidden;
  }
  .service-card::after {
    content: ''; position: absolute; inset: 0; border-radius: 16px;
    background: linear-gradient(135deg, rgba(21,101,192,.04), transparent);
    opacity: 0; transition: opacity .25s;
  }
  .service-card:hover { border-color: #1565c0; transform: translateY(-5px); box-shadow: 0 20px 48px rgba(21,101,192,.14); }
  .service-card:hover::after { opacity: 1; }

  .role-card {
    border-radius: 20px; border: 1px solid rgba(255,255,255,.6);
    padding: 28px; transition: all .3s; position: relative; overflow: hidden;
  }
  .role-card:hover { transform: translateY(-6px); box-shadow: 0 24px 56px rgba(0,0,0,.1); }

  .process-card {
    background: #fff; border-radius: 18px; border: 1px solid #e2e8f0;
    padding: 28px; margin-bottom: 0; position: relative;
    transition: box-shadow .25s, border-color .25s;
  }
  .process-card:hover { box-shadow: 0 12px 40px rgba(0,0,0,.07); border-color: #cbd5e1; }

  .btn-primary {
    font-size: 14px; font-weight: 700; color: #fff;
    padding: 13px 28px; border-radius: 12px;
    background: linear-gradient(135deg, #1565c0, #1976d2);
    text-decoration: none; display: inline-flex; align-items: center; gap: 8px;
    border: none; cursor: pointer; transition: all .25s;
    box-shadow: 0 4px 20px rgba(21,101,192,.35);
  }
  .btn-primary:hover { transform: translateY(-2px); box-shadow: 0 8px 28px rgba(21,101,192,.45); }

  .btn-ghost {
    font-size: 14px; font-weight: 600; color: rgba(255,255,255,.75);
    padding: 13px 24px; border-radius: 12px;
    background: rgba(255,255,255,.08);
    border: 1px solid rgba(255,255,255,.15);
    text-decoration: none; display: inline-flex; align-items: center; gap: 8px;
    transition: all .25s;
  }
  .btn-ghost:hover { background: rgba(255,255,255,.13); color: #fff; border-color: rgba(255,255,255,.3); }

  .wf-step:hover .wf-circle { box-shadow: 0 0 0 6px rgba(21,101,192,.15); }

  .ia-rule-row {
    display: flex; align-items: center; gap: 10px;
    padding: 10px 14px;
    background: rgba(255,255,255,.04); border-radius: 10px;
    border: 1px solid rgba(255,255,255,.07); margin-bottom: 8px;
    transition: background .2s, border-color .2s;
  }
  .ia-rule-row:hover { background: rgba(255,255,255,.07); border-color: rgba(21,101,192,.3); }

  .footer-link {
    font-size: 12px; color: rgba(255,255,255,.35); cursor: pointer;
    transition: color .2s; text-decoration: none;
  }
  .footer-link:hover { color: rgba(255,255,255,.75); }

  .scrollbar-hide::-webkit-scrollbar { display: none; }
  .scrollbar-hide { -ms-overflow-style: none; scrollbar-width: none; }
`

// ── Données ───────────────────────────────────────────────
const STATS = [
  { val: '1 240',   lbl: 'Étudiants inscrits',    sub: '↑ +12% cette année',         icon: Users },
  { val: '98%',     lbl: 'Traitement auto',        sub: 'vs 45% avant le système',    icon: Zap },
  { val: '< 2 min', lbl: 'Génération attestation', sub: 'vs 3 jours en présentiel',   icon: FileText },
  { val: '12',      lbl: 'Règles IA actives',       sub: 'Sans redéploiement',         icon: Cpu },
]

const PROCESSUS = [
  {
    num: 1, color: '#1565c0', grad: 'linear-gradient(135deg,#1565c0,#38bdf8)', colorBg: '#e3f2fd',
    titre: 'Constitution du dossier numérique',
    badge: 'Service dossier', badgeColor: '#dbeafe', badgeText: '#1d4ed8',
    desc: "L'étudiant dépose ses pièces justificatives en ligne. Le système calcule automatiquement un score de complétude de 0 à 100%. Une notification est envoyée dès que le dossier est complet.",
    items: ['Baccalauréat', 'CNI', "Photo d'identité", 'Acte de naissance', 'Certificat médical', 'Quitus bibliothèque', 'Reçu de paiement'],
  },
  {
    num: 2, color: '#00897b', grad: 'linear-gradient(135deg,#00897b,#34d399)', colorBg: '#e0f2f1',
    titre: "Circuit d'inscription — workflow 4 étapes",
    badge: '100% automatique', badgeColor: '#d1fae5', badgeText: '#065f46',
    desc: "Après soumission, un workflow démarre automatiquement. Chaque service valide son étape. La validation débloque l'étape suivante et attribue le matricule définitif à la fin.",
    items: ['Scolarité — vérification administrative', 'Comptabilité — confirmation paiement', 'Service médical — certificat santé', 'Bibliothèque — quitus'],
  },
  {
    num: 3, color: '#d97706', grad: 'linear-gradient(135deg,#d97706,#fbbf24)', colorBg: '#fffde7',
    titre: 'Délibération et résultats académiques',
    badge: 'Service délibération', badgeColor: '#fef3c7', badgeText: '#92400e',
    desc: 'Les enseignants saisissent les notes (CC 30%, TP 20%, Examen 50%). La moyenne est calculée automatiquement. Le moteur IA applique les règles pour produire la décision et la mention. Le PV est généré en PDF.',
    items: ['Saisie notes CC + TP + Examen', 'Calcul automatique moyenne', 'Décision IA + mention', 'Génération PV PDF', 'Notification étudiants'],
  },
  {
    num: 4, color: '#7c3aed', grad: 'linear-gradient(135deg,#7c3aed,#a78bfa)', colorBg: '#ede9fe',
    titre: 'Génération et vérification des attestations',
    badge: 'Immédiat — QR code', badgeColor: '#ede9fe', badgeText: '#5b21b6',
    desc: "L'étudiant demande une attestation en un clic. Le moteur IA vérifie l'éligibilité, génère le PDF officiel avec QR code et le stocke sur MinIO. N'importe qui peut scanner le QR pour authentifier le document.",
    items: "Attestation d'inscription,Certificat de scolarité,Attestation de réussite,Relevé de notes,QR code d'authentification".split(','),
  },
]

const SERVICES = [
  { icon: Lock,         label: 'Authentification', desc: 'JWT, rôles, journal',       port: ':8001', grad: 'linear-gradient(135deg,#1565c0,#38bdf8)' },
  { icon: ClipboardList,label: 'Inscription',       desc: 'Workflow 4 étapes auto',    port: ':8002', grad: 'linear-gradient(135deg,#00897b,#34d399)' },
  { icon: FolderOpen,   label: 'Dossier',           desc: 'Pièces, score, MinIO',      port: ':8003', grad: 'linear-gradient(135deg,#475569,#94a3b8)' },
  { icon: BookOpen,     label: 'Délibération',      desc: 'Notes, moyennes, PV PDF',   port: ':8004', grad: 'linear-gradient(135deg,#d97706,#fbbf24)' },
  { icon: FileText,     label: 'Attestation',       desc: 'PDF + QR code vérifiable',  port: ':8005', grad: 'linear-gradient(135deg,#dc2626,#f87171)' },
  { icon: Bell,         label: 'Notification',      desc: 'Email, SMS, chatbot IA',    port: ':8006', grad: 'linear-gradient(135deg,#0284c7,#7dd3fc)' },
  { icon: Cpu,          label: 'Moteur IA',         desc: 'Règles configurables',       port: ':8007', grad: 'linear-gradient(135deg,#7c3aed,#a78bfa)' },
  { icon: Shield,       label: 'Audit',             desc: 'Journal, traçabilité',      port: ':8008', grad: 'linear-gradient(135deg,#0f766e,#5eead4)' },
]

const ROLES = [
  {
    emoji: '🎓', titre: 'Étudiant',
    grad: 'linear-gradient(145deg,#eff6ff,#dbeafe)',
    border: '#bfdbfe', titleC: '#1e40af', descC: '#1d4ed8', checkC: '#2563eb',
    desc: 'Gérez votre parcours universitaire de A à Z depuis une interface intuitive.',
    items: ['Créer et compléter son dossier', "Suivre le workflow d'inscription", 'Consulter ses résultats et notes', 'Télécharger ses attestations PDF', 'Chatbot disponible 24h/24'],
  },
  {
    emoji: '👔', titre: 'Agent administratif',
    grad: 'linear-gradient(145deg,#f0fdf4,#dcfce7)',
    border: '#bbf7d0', titleC: '#14532d', descC: '#166534', checkC: '#16a34a',
    desc: 'Traitez les dossiers et validez les étapes du workflow en quelques clics.',
    items: ['Valider / rejeter les dossiers', 'Gérer les étapes du workflow', 'Vérifier les pièces justificatives', 'Saisir les notes (enseignants)', 'Résoudre les alertes anomalies'],
  },
  {
    emoji: '⚙️', titre: 'Administrateur',
    grad: 'linear-gradient(145deg,#fffbeb,#fef3c7)',
    border: '#fde68a', titleC: '#78350f', descC: '#92400e', checkC: '#d97706',
    desc: "Pilotez le système, configurez les règles IA et supervisez toute l'activité.",
    items: ['Tableau de bord avec graphiques', 'Créer et tester les règles IA', "Consulter le journal d'audit", 'Statistiques toutes sections', 'Purger et maintenir le système'],
  },
]

const REGLES = [
  { code: 'DELIB_ADMIS',        cond: 'moyenne ≥ 10 et crédits ≥ 60',    action: 'admis',      dotC: '#34d399' },
  { code: 'DELIB_RATTRAPAGE',   cond: '8 ≤ moyenne < 10',                 action: 'rattrapage', dotC: '#fbbf24' },
  { code: 'ATT_INSCRIPTION_OK', cond: 'inscription_validee == True',       action: 'eligible',   dotC: '#34d399' },
  { code: 'DOSSIER_COMPLET',    cond: 'score_completude == 100',           action: 'complet',    dotC: '#60a5fa' },
  { code: 'INSC_ELIGIBLE',      cond: 'score == 100 et paiement == True',  action: 'eligible',   dotC: '#34d399' },
]

const WF_STEPS = [
  { label: 'Dossier',       sub: '100% complet', done: true,  active: false },
  { label: 'Préinscription',sub: 'Soumise',       done: true,  active: false },
  { label: 'Scolarité',     sub: '14/01/2025',    done: true,  active: false },
  { label: 'Comptabilité',  sub: '14/01/2025',    done: true,  active: false },
  { label: 'Médical',       sub: 'En attente',    done: false, active: true  },
  { label: 'Bibliothèque',  sub: 'Pas encore',    done: false, active: false },
  { label: 'Matricule',     sub: 'À attribuer',   done: false, active: false },
]

// ── Composants ────────────────────────────────────────────
function SectionBadge({ children, light }) {
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 6,
      fontSize: 11, fontWeight: 700, textTransform: 'uppercase',
      letterSpacing: '.1em',
      color: light ? 'rgba(255,255,255,.7)' : '#1d4ed8',
      background: light ? 'rgba(255,255,255,.1)' : '#dbeafe',
      padding: '5px 14px', borderRadius: 20, marginBottom: 14,
      border: light ? '1px solid rgba(255,255,255,.15)' : '1px solid #bfdbfe',
    }}>{children}</span>
  )
}

export default function LandingPage() {
  return (
    <>
      <style>{GLOBAL_STYLES}</style>
      <div style={{ fontFamily: "'Inter', system-ui, sans-serif", color: '#1e293b', lineHeight: 1.6, overflowX: 'hidden' }}>

        {/* ── NAVBAR ── */}
        <nav style={{
          background: 'rgba(10,22,40,.9)',
          backdropFilter: 'blur(20px)',
          WebkitBackdropFilter: 'blur(20px)',
          padding: '0 48px',
          display: 'flex', alignItems: 'center', height: 64,
          gap: 24, position: 'sticky', top: 0, zIndex: 200,
          borderBottom: '1px solid rgba(255,255,255,.07)',
          boxShadow: '0 4px 30px rgba(0,0,0,.3)',
        }}>
          {/* Logo */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexShrink: 0 }}>
            <div style={{
              width: 38, height: 38, borderRadius: 10,
              background: 'linear-gradient(135deg,#1565c0,#38bdf8)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 17, fontWeight: 900, color: '#fff',
              boxShadow: '0 4px 14px rgba(21,101,192,.5)',
            }}>U</div>
            <div>
              <div style={{ fontSize: 15, fontWeight: 800, color: '#fff', letterSpacing: '-.01em' }}>UADB</div>
              <div style={{ fontSize: 9.5, color: 'rgba(255,255,255,.3)', marginTop: 0.5, fontWeight: 500 }}>Portail intelligent</div>
            </div>
          </div>

          {/* Nav links */}
          <div style={{ marginLeft: 'auto', display: 'flex', gap: 2, alignItems: 'center' }}>
            {['Processus', 'Services', 'IA', 'Rôles'].map(l => (
              <a key={l} href={`#${l.toLowerCase()}`} className="nav-link">{l}</a>
            ))}
            <div style={{ width: 1, height: 20, background: 'rgba(255,255,255,.1)', margin: '0 8px' }} />
            <Link to="/login" style={{
              fontSize: 13, fontWeight: 600, color: 'rgba(255,255,255,.7)',
              padding: '7px 16px', borderRadius: 8,
              background: 'rgba(255,255,255,.07)',
              border: '1px solid rgba(255,255,255,.12)',
              textDecoration: 'none', transition: 'all .2s',
            }}
              onMouseEnter={e => { e.currentTarget.style.background = 'rgba(255,255,255,.12)'; e.currentTarget.style.color = '#fff' }}
              onMouseLeave={e => { e.currentTarget.style.background = 'rgba(255,255,255,.07)'; e.currentTarget.style.color = 'rgba(255,255,255,.7)' }}
            >Connexion</Link>
            <Link to="/register" className="btn-primary" style={{ fontSize: 13, padding: '7px 18px', borderRadius: 8, marginLeft: 4 }}>
              Créer un compte
            </Link>
          </div>
        </nav>

        {/* ── HERO ── */}
        <section style={{
          background: '#060d1a',
          padding: '96px 48px 100px',
          textAlign: 'center',
          position: 'relative',
          overflow: 'hidden',
          minHeight: '88vh',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          {/* Gradient mesh background */}
          <div style={{
            position: 'absolute', inset: 0, zIndex: 0,
            background: 'radial-gradient(ellipse 80% 60% at 50% -10%, rgba(21,101,192,.3) 0%, transparent 70%), radial-gradient(ellipse 60% 50% at 80% 80%, rgba(124,58,237,.15) 0%, transparent 60%)',
          }} />
          {/* Animated orbs */}
          {[
            { w: 500, h: 500, top: '-15%', left: '60%', c: 'rgba(21,101,192,.12)', delay: '0s' },
            { w: 350, h: 350, top: '50%',  left: '-8%', c: 'rgba(124,58,237,.1)',  delay: '2s' },
            { w: 280, h: 280, top: '20%',  left: '80%', c: 'rgba(56,189,248,.08)', delay: '1s' },
          ].map((o, i) => (
            <div key={i} style={{
              position: 'absolute', width: o.w, height: o.h, top: o.top, left: o.left,
              borderRadius: '50%', background: o.c, filter: 'blur(80px)',
              animation: `floatOrb ${6 + i}s ease-in-out ${o.delay} infinite`,
              pointerEvents: 'none', zIndex: 0,
            }} />
          ))}
          {/* Grid overlay */}
          <div style={{
            position: 'absolute', inset: 0,
            backgroundImage: 'linear-gradient(rgba(255,255,255,.03) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.03) 1px, transparent 1px)',
            backgroundSize: '64px 64px', zIndex: 0, pointerEvents: 'none',
          }} />

          <div style={{ position: 'relative', zIndex: 1, maxWidth: 720, margin: '0 auto' }}>
            {/* Live badge */}
            <div className="hero-animate" style={{
              display: 'inline-flex', alignItems: 'center', gap: 8,
              background: 'rgba(21,101,192,.15)',
              border: '1px solid rgba(21,101,192,.35)',
              borderRadius: 24, padding: '6px 16px 6px 12px', marginBottom: 28,
              backdropFilter: 'blur(10px)',
            }}>
              <div style={{ width: 7, height: 7, borderRadius: '50%', background: '#4ade80', animation: 'pulse-dot 2s ease-in-out infinite' }} />
              <span style={{ fontSize: 12.5, color: 'rgba(255,255,255,.7)', fontWeight: 500 }}>
                Système d'Information Intelligent — UADB 2025
              </span>
            </div>

            <h1 className="hero-animate-2" style={{
              fontSize: 'clamp(2.2rem,5vw,3.4rem)', fontWeight: 900, color: '#fff',
              lineHeight: 1.1, marginBottom: 20, letterSpacing: '-.03em',
            }}>
              La gestion universitaire<br />
              <span style={{
                background: 'linear-gradient(135deg,#fbbf24,#f97316)',
                WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
                backgroundClip: 'text',
              }}>automatisée et intelligente</span>
            </h1>

            <p className="hero-animate-3" style={{
              fontSize: 16, color: 'rgba(255,255,255,.5)',
              lineHeight: 1.75, marginBottom: 40, maxWidth: 540, margin: '0 auto 40px',
            }}>
              Inscriptions, dossiers, délibérations et attestations —
              tout en ligne, tout automatique, tout tracé.
              Un seul portail pour toute votre vie universitaire.
            </p>

            <div className="hero-animate-4" style={{ display: 'flex', gap: 12, justifyContent: 'center', flexWrap: 'wrap' }}>
              <Link to="/register" className="btn-primary" style={{ fontSize: 14.5, padding: '14px 32px', borderRadius: 12 }}>
                <GraduationCap size={17} /> Commencer l'inscription
              </Link>
              <Link to="/login" className="btn-ghost" style={{ fontSize: 14.5, padding: '14px 26px', borderRadius: 12 }}>
                Accéder au portail <ArrowRight size={15} />
              </Link>
            </div>

            {/* Hero stats */}
            <div style={{
              display: 'flex', gap: 48, justifyContent: 'center',
              marginTop: 64, paddingTop: 48,
              borderTop: '1px solid rgba(255,255,255,.07)',
              flexWrap: 'wrap', animation: 'fadeUp .8s .6s ease both',
            }}>
              {[['8', 'Microservices'], ['100%', 'Automatisé'], ['24/7', 'Disponible'], ['QR', 'Vérification docs']].map(([v, l]) => (
                <div key={l} style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '2rem', fontWeight: 900, color: '#fff', letterSpacing: '-.03em' }}>{v}</div>
                  <div style={{ fontSize: 12, color: 'rgba(255,255,255,.3)', marginTop: 4, fontWeight: 500 }}>{l}</div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ── STATS BANDE ── */}
        <section style={{ background: '#f8fafc', borderTop: '1px solid #e2e8f0', borderBottom: '1px solid #e2e8f0', padding: '52px 48px' }}>
          <div style={{
            maxWidth: 960, margin: '0 auto',
            display: 'grid', gridTemplateColumns: 'repeat(4,1fr)',
            gap: 1, background: '#e2e8f0', borderRadius: 18, overflow: 'hidden',
            boxShadow: '0 8px 40px rgba(0,0,0,.06)',
          }}>
            {STATS.map(s => {
              const Icon = s.icon
              return (
                <div key={s.lbl} className="stat-card">
                  <div style={{
                    width: 40, height: 40, borderRadius: 10, margin: '0 auto 14px',
                    background: 'linear-gradient(135deg,#1565c0,#38bdf8)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    color: '#fff',
                  }}>
                    <Icon size={18} />
                  </div>
                  <div style={{ fontSize: '1.9rem', fontWeight: 900, color: '#1565c0', marginBottom: 4, letterSpacing: '-.03em' }}>
                    {s.val}
                  </div>
                  <div style={{ fontSize: 12.5, color: '#64748b', fontWeight: 600 }}>{s.lbl}</div>
                  <div style={{ fontSize: 11, color: '#059669', marginTop: 6, fontWeight: 600 }}>{s.sub}</div>
                </div>
              )
            })}
          </div>
        </section>

        {/* ── PROCESSUS ── */}
        <section id="processus" style={{ padding: '80px 48px', background: '#fff' }}>
          <div style={{ maxWidth: 960, margin: '0 auto' }}>
            <SectionBadge>Processus administratif</SectionBadge>
            <h2 style={{ fontSize: 'clamp(1.5rem,3vw,2rem)', fontWeight: 800, color: '#0f172a', marginBottom: 10, letterSpacing: '-.02em' }}>
              De la préinscription à l'attestation
            </h2>
            <p style={{ fontSize: 14.5, color: '#64748b', lineHeight: 1.7, maxWidth: 520, marginBottom: 56 }}>
              Chaque étape est numérisée, automatisée et tracée en temps réel.
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
              {PROCESSUS.map((p, idx) => (
                <div key={p.num} style={{ display: 'grid', gridTemplateColumns: '72px 1fr', gap: '0 24px' }}>
                  {/* Timeline */}
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                    <div style={{
                      width: 52, height: 52, borderRadius: '50%',
                      background: p.grad, color: '#fff',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      fontSize: 18, fontWeight: 900, flexShrink: 0, zIndex: 1,
                      boxShadow: `0 6px 20px ${p.color}40`,
                    }}>{p.num}</div>
                    {idx < PROCESSUS.length - 1 && (
                      <div style={{
                        width: 2, flex: 1, minHeight: 28,
                        background: `linear-gradient(to bottom, ${p.color}80, #e2e8f0)`,
                        margin: '6px 0',
                      }} />
                    )}
                  </div>

                  {/* Card */}
                  <div className="process-card" style={{ marginBottom: idx < PROCESSUS.length - 1 ? 24 : 0 }}>
                    {/* Left accent */}
                    <div style={{
                      position: 'absolute', left: 0, top: 0, bottom: 0, width: 4,
                      background: p.grad, borderRadius: '18px 0 0 18px',
                    }} />
                    <div style={{ paddingLeft: 4 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10, flexWrap: 'wrap' }}>
                        <span style={{ fontSize: 15.5, fontWeight: 800, color: '#0f172a' }}>{p.titre}</span>
                        <span style={{
                          fontSize: 11, fontWeight: 700, padding: '3px 11px',
                          borderRadius: 12, background: p.badgeColor, color: p.badgeText,
                          border: `1px solid ${p.badgeColor}`,
                        }}>{p.badge}</span>
                      </div>
                      <p style={{ fontSize: 13.5, color: '#64748b', lineHeight: 1.65, marginBottom: 16 }}>{p.desc}</p>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                        {p.items.map(item => (
                          <div key={item} style={{
                            display: 'flex', alignItems: 'center', gap: 6,
                            fontSize: 12, color: '#475569',
                            background: '#f8fafc',
                            padding: '5px 12px', borderRadius: 8,
                            border: '1px solid #e2e8f0',
                          }}>
                            <div style={{
                              width: 16, height: 16, borderRadius: '50%',
                              background: p.grad,
                              display: 'flex', alignItems: 'center', justifyContent: 'center',
                              fontSize: 9, color: '#fff', flexShrink: 0, fontWeight: 800,
                            }}>✓</div>
                            {item}
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ── WORKFLOW VISUEL ── */}
        <section style={{ background: 'linear-gradient(135deg,#060d1a,#0d1f3c)', padding: '72px 48px', position: 'relative', overflow: 'hidden' }}>
          <div style={{
            position: 'absolute', inset: 0, zIndex: 0,
            backgroundImage: 'linear-gradient(rgba(255,255,255,.025) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.025) 1px, transparent 1px)',
            backgroundSize: '48px 48px', pointerEvents: 'none',
          }} />
          <div style={{ maxWidth: 960, margin: '0 auto', position: 'relative', zIndex: 1 }}>
            {/* Header */}
            <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 48, flexWrap: 'wrap', gap: 16 }}>
              <div>
                <SectionBadge light>Suivi en temps réel</SectionBadge>
                <div style={{ fontSize: 'clamp(1.3rem,2.5vw,1.7rem)', fontWeight: 800, color: '#fff', letterSpacing: '-.02em' }}>
                  Étudiant Amadou Diallo
                </div>
                <div style={{ fontSize: 13, color: 'rgba(255,255,255,.35)', marginTop: 4 }}>
                  Année 2024-2025 • M1 Systèmes d'Information
                </div>
              </div>
              <div style={{
                background: 'rgba(0,137,123,.15)', border: '1px solid rgba(0,137,123,.3)',
                borderRadius: 12, padding: '10px 18px', textAlign: 'right',
              }}>
                <div style={{ fontSize: 11, color: '#5dcaa5', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '.08em' }}>Progression</div>
                <div style={{ fontSize: '1.6rem', fontWeight: 900, color: '#fff', marginTop: 2 }}>57%</div>
              </div>
            </div>

            {/* Steps */}
            <div className="scrollbar-hide" style={{ display: 'flex', overflowX: 'auto', paddingBottom: 12 }}>
              {WF_STEPS.map((s, i) => (
                <div key={s.label} className="wf-step" style={{ flex: 1, minWidth: 110, display: 'flex', flexDirection: 'column', alignItems: 'center', position: 'relative', cursor: 'default' }}>
                  {/* Connector */}
                  {i < WF_STEPS.length - 1 && (
                    <div style={{
                      position: 'absolute', top: 24, left: '50%', right: '-50%', height: 2,
                      background: s.done
                        ? 'linear-gradient(90deg,#00897b,#34d399)'
                        : 'rgba(255,255,255,.1)',
                      zIndex: 0,
                    }} />
                  )}
                  {/* Circle */}
                  <div className="wf-circle" style={{
                    width: 48, height: 48, borderRadius: '50%', zIndex: 1,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: 14, fontWeight: 800, marginBottom: 12,
                    border: `2px solid ${s.done ? '#00897b' : s.active ? '#1565c0' : 'rgba(255,255,255,.15)'}`,
                    background: s.done
                      ? 'linear-gradient(135deg,#00897b,#34d399)'
                      : s.active
                        ? 'linear-gradient(135deg,#1565c0,#38bdf8)'
                        : 'rgba(255,255,255,.05)',
                    color: (s.done || s.active) ? '#fff' : 'rgba(255,255,255,.25)',
                    boxShadow: s.done ? '0 4px 16px rgba(0,137,123,.35)' : s.active ? '0 4px 16px rgba(21,101,192,.35)' : 'none',
                    transition: 'box-shadow .2s',
                  }}>
                    {s.done ? '✓' : i + 1}
                  </div>
                  <div style={{ fontSize: 12, fontWeight: 700, color: s.done || s.active ? 'rgba(255,255,255,.85)' : 'rgba(255,255,255,.35)', textAlign: 'center', marginBottom: 3 }}>{s.label}</div>
                  <div style={{ fontSize: 10.5, color: 'rgba(255,255,255,.25)', textAlign: 'center', marginBottom: 7 }}>{s.sub}</div>
                  <span style={{
                    fontSize: 10, fontWeight: 700, padding: '3px 9px', borderRadius: 10,
                    background: s.done ? 'rgba(0,137,123,.2)' : s.active ? 'rgba(21,101,192,.25)' : 'rgba(255,255,255,.05)',
                    color: s.done ? '#5dcaa5' : s.active ? '#7dd3fc' : 'rgba(255,255,255,.25)',
                    border: `1px solid ${s.done ? 'rgba(0,137,123,.3)' : s.active ? 'rgba(21,101,192,.3)' : 'rgba(255,255,255,.08)'}`,
                  }}>
                    {s.done ? 'Validé' : s.active ? 'En cours' : 'En attente'}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ── SERVICES ── */}
        <section id="services" style={{ padding: '80px 48px', background: '#f8fafc' }}>
          <div style={{ maxWidth: 960, margin: '0 auto' }}>
            <SectionBadge>Architecture microservices</SectionBadge>
            <h2 style={{ fontSize: 'clamp(1.5rem,3vw,2rem)', fontWeight: 800, color: '#0f172a', marginBottom: 10, letterSpacing: '-.02em' }}>
              8 services indépendants
            </h2>
            <p style={{ fontSize: 14.5, color: '#64748b', lineHeight: 1.7, maxWidth: 520, marginBottom: 40 }}>
              Chaque service gère un domaine métier précis avec sa propre base de données PostgreSQL.
            </p>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 16 }}>
              {SERVICES.map(s => (
                <div key={s.label} className="service-card">
                  <div style={{
                    width: 46, height: 46, borderRadius: 12,
                    background: s.grad,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    marginBottom: 14, color: '#fff',
                    boxShadow: '0 4px 14px rgba(0,0,0,.15)',
                  }}>
                    <s.icon size={20} />
                  </div>
                  <div style={{ fontSize: 13.5, fontWeight: 800, color: '#0f172a', marginBottom: 5 }}>{s.label}</div>
                  <div style={{ fontSize: 12, color: '#94a3b8', lineHeight: 1.55, marginBottom: 12 }}>{s.desc}</div>
                  <div style={{ fontSize: 11, fontWeight: 700, color: '#1d4ed8', display: 'flex', alignItems: 'center', gap: 4 }}>
                    <span style={{ background: '#dbeafe', borderRadius: 6, padding: '2px 8px' }}>{s.port}</span>
                    <ArrowRight size={11} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ── RÔLES ── */}
        <section id="rôles" style={{ padding: '80px 48px', background: '#fff' }}>
          <div style={{ maxWidth: 960, margin: '0 auto' }}>
            <SectionBadge>Accès par rôle</SectionBadge>
            <h2 style={{ fontSize: 'clamp(1.5rem,3vw,2rem)', fontWeight: 800, color: '#0f172a', marginBottom: 10, letterSpacing: '-.02em' }}>
              Un portail, trois espaces distincts
            </h2>
            <p style={{ fontSize: 14.5, color: '#64748b', lineHeight: 1.7, maxWidth: 520, marginBottom: 40 }}>
              Chaque acteur accède uniquement aux fonctionnalités qui lui sont destinées.
            </p>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 20 }}>
              {ROLES.map(r => (
                <div key={r.titre} className="role-card" style={{ background: r.grad, borderColor: r.border }}>
                  {/* Icon bubble */}
                  <div style={{
                    width: 54, height: 54, borderRadius: 16,
                    background: 'rgba(255,255,255,.7)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: 26, marginBottom: 18,
                    boxShadow: '0 4px 14px rgba(0,0,0,.07)',
                    backdropFilter: 'blur(8px)',
                  }}>{r.emoji}</div>
                  <div style={{ fontSize: 16, fontWeight: 800, color: r.titleC, marginBottom: 8 }}>{r.titre}</div>
                  <div style={{ fontSize: 13, color: r.descC, lineHeight: 1.65, marginBottom: 18 }}>{r.desc}</div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 7 }}>
                    {r.items.map(item => (
                      <div key={item} style={{ fontSize: 12.5, color: r.descC, display: 'flex', alignItems: 'center', gap: 7 }}>
                        <CheckCircle size={13} color={r.checkC} style={{ flexShrink: 0 }} /> {item}
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ── IA SECTION ── */}
        <section id="ia" style={{ background: '#f8fafc', padding: '80px 48px', borderTop: '1px solid #e2e8f0' }}>
          <div style={{ maxWidth: 960, margin: '0 auto', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 56, alignItems: 'center' }}>
            {/* Left */}
            <div>
              <SectionBadge>Intelligence artificielle</SectionBadge>
              <h2 style={{ fontSize: 'clamp(1.5rem,3vw,2rem)', fontWeight: 800, color: '#0f172a', marginBottom: 12, letterSpacing: '-.02em' }}>
                Règles métier sans redéploiement
              </h2>
              <p style={{ fontSize: 14.5, color: '#64748b', lineHeight: 1.75, marginBottom: 28 }}>
                Le moteur de décision évalue les règles en temps réel.
                Un administrateur peut modifier le seuil d'admission sans toucher au code.
              </p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                {[
                  { icon: Zap,      grad: 'linear-gradient(135deg,#1565c0,#38bdf8)', t: 'Décisions automatiques',  d: 'Admission, rattrapage, éligibilité aux attestations' },
                  { icon: Search,   grad: 'linear-gradient(135deg,#00897b,#34d399)', t: "Détection d'anomalies",   d: 'Notes aberrantes, dossiers incomplets, pièces expirées' },
                  { icon: BarChart2, grad: 'linear-gradient(135deg,#d97706,#fbbf24)', t: 'Traçabilité complète',    d: 'Chaque décision enregistrée avec contexte complet' },
                ].map(f => (
                  <div key={f.t} style={{
                    display: 'flex', alignItems: 'flex-start', gap: 16,
                    padding: 18, background: '#fff', borderRadius: 14,
                    border: '1px solid #e2e8f0',
                    boxShadow: '0 2px 12px rgba(0,0,0,.04)',
                    transition: 'box-shadow .2s, border-color .2s',
                  }}
                    onMouseEnter={e => { e.currentTarget.style.boxShadow = '0 8px 24px rgba(0,0,0,.08)'; e.currentTarget.style.borderColor = '#cbd5e1' }}
                    onMouseLeave={e => { e.currentTarget.style.boxShadow = '0 2px 12px rgba(0,0,0,.04)'; e.currentTarget.style.borderColor = '#e2e8f0' }}
                  >
                    <div style={{
                      width: 40, height: 40, borderRadius: 10,
                      background: f.grad, flexShrink: 0,
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      color: '#fff', boxShadow: '0 4px 12px rgba(0,0,0,.15)',
                    }}>
                      <f.icon size={18} />
                    </div>
                    <div>
                      <div style={{ fontSize: 13.5, fontWeight: 700, color: '#0f172a', marginBottom: 4 }}>{f.t}</div>
                      <div style={{ fontSize: 12.5, color: '#94a3b8', lineHeight: 1.55 }}>{f.d}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Right — terminal panel */}
            <div style={{
              background: '#0d1117', borderRadius: 20,
              padding: 24, border: '1px solid rgba(255,255,255,.07)',
              boxShadow: '0 32px 72px rgba(0,0,0,.4)',
              overflow: 'hidden', position: 'relative',
            }}>
              {/* Traffic lights */}
              <div style={{ display: 'flex', gap: 7, marginBottom: 18 }}>
                {['#ff5f57', '#febc2e', '#28c840'].map(c => (
                  <div key={c} style={{ width: 12, height: 12, borderRadius: '50%', background: c }} />
                ))}
                <div style={{ marginLeft: 12, fontSize: 11, color: 'rgba(255,255,255,.25)', fontFamily: 'monospace', display: 'flex', alignItems: 'center', gap: 6 }}>
                  <Cpu size={11} />  moteur-ia — règles actives
                </div>
              </div>
              {/* Rules */}
              {REGLES.map((r, i) => (
                <div key={r.code} className="ia-rule-row">
                  <div style={{ width: 6, height: 6, borderRadius: '50%', background: r.dotC, flexShrink: 0 }} />
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontFamily: 'monospace', fontSize: 12, color: '#7dd3fc', fontWeight: 600 }}>{r.code}</div>
                    <div style={{ fontSize: 10.5, color: 'rgba(255,255,255,.3)', marginTop: 2, fontFamily: 'monospace' }}>{r.cond}</div>
                  </div>
                  <span style={{
                    fontSize: 10.5, fontWeight: 700, padding: '3px 10px', borderRadius: 8,
                    background: r.dotC === '#34d399' ? 'rgba(52,211,153,.15)' : r.dotC === '#fbbf24' ? 'rgba(251,191,36,.15)' : 'rgba(96,165,250,.15)',
                    color: r.dotC, border: `1px solid ${r.dotC}30`,
                    fontFamily: 'monospace',
                  }}>{r.action}</span>
                </div>
              ))}
              {/* Footer */}
              <div style={{
                marginTop: 16, padding: '12px 14px',
                background: 'rgba(255,255,255,.02)', borderRadius: 10,
                border: '1px solid rgba(255,255,255,.05)',
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              }}>
                <div style={{ fontSize: 11, color: 'rgba(255,255,255,.2)', fontFamily: 'monospace' }}>
                  admin → modifiable sans redéploiement
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <div style={{ width: 6, height: 6, borderRadius: '50%', background: '#4ade80', animation: 'pulse-dot 2s ease-in-out infinite' }} />
                  <span style={{ fontSize: 11, color: '#4ade80', fontWeight: 700, fontFamily: 'monospace' }}>12 actives</span>
                </div>
              </div>
              {/* Glow */}
              <div style={{
                position: 'absolute', bottom: -40, right: -40,
                width: 160, height: 160, borderRadius: '50%',
                background: 'rgba(124,58,237,.12)', filter: 'blur(40px)',
                pointerEvents: 'none',
              }} />
            </div>
          </div>
        </section>

        {/* ── CTA FINAL ── */}
        <section style={{
          background: 'linear-gradient(135deg,#060d1a,#0d1f3c)',
          padding: '100px 48px', textAlign: 'center', position: 'relative', overflow: 'hidden',
        }}>
          <div style={{
            position: 'absolute', inset: 0,
            background: 'radial-gradient(ellipse 70% 70% at 50% 0%, rgba(21,101,192,.25) 0%, transparent 70%)',
            pointerEvents: 'none',
          }} />
          <div style={{ maxWidth: 600, margin: '0 auto', position: 'relative', zIndex: 1 }}>
            <div style={{
              display: 'inline-flex', alignItems: 'center', gap: 7,
              background: 'rgba(251,191,36,.12)', border: '1px solid rgba(251,191,36,.25)',
              borderRadius: 20, padding: '5px 14px 5px 10px', marginBottom: 24,
            }}>
              <Sparkles size={13} color="#fbbf24" />
              <span style={{ fontSize: 12, color: 'rgba(255,255,255,.65)', fontWeight: 500 }}>Rejoignez 1 240 étudiants</span>
            </div>
            <h2 style={{ fontSize: 'clamp(1.7rem,4vw,2.4rem)', fontWeight: 900, color: '#fff', marginBottom: 16, letterSpacing: '-.03em' }}>
              Prêt à commencer<br />votre parcours ?
            </h2>
            <p style={{ fontSize: 15, color: 'rgba(255,255,255,.45)', lineHeight: 1.75, marginBottom: 44, maxWidth: 460, margin: '0 auto 44px' }}>
              Créez votre compte en 2 minutes et accédez à tous les services
              administratifs de l'UADB depuis n'importe où.
            </p>
            <div style={{ display: 'flex', gap: 14, justifyContent: 'center', flexWrap: 'wrap' }}>
              <Link to="/register" className="btn-primary" style={{ fontSize: 15, padding: '15px 36px', borderRadius: 14 }}>
                <GraduationCap size={18} /> Créer mon compte
              </Link>
              <Link to="/login" className="btn-ghost" style={{ fontSize: 15, padding: '15px 28px', borderRadius: 14 }}>
                J'ai déjà un compte <ArrowRight size={15} />
              </Link>
            </div>
          </div>
        </section>

        {/* ── FOOTER ── */}
        <footer style={{ background: '#040810', padding: '48px 48px 32px' }}>
          <div style={{ maxWidth: 960, margin: '0 auto' }}>
            {/* Top */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr auto', gap: 40, marginBottom: 40, alignItems: 'start' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
                  <div style={{
                    width: 36, height: 36, borderRadius: 9,
                    background: 'linear-gradient(135deg,#1565c0,#38bdf8)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: 16, fontWeight: 900, color: '#fff',
                    boxShadow: '0 4px 14px rgba(21,101,192,.4)',
                  }}>U</div>
                  <div>
                    <div style={{ fontSize: 15, fontWeight: 800, color: '#fff' }}>UADB</div>
                    <div style={{ fontSize: 10, color: 'rgba(255,255,255,.3)' }}>Université Alioune Diop de Bambey</div>
                  </div>
                </div>
                <p style={{ fontSize: 13, color: 'rgba(255,255,255,.3)', lineHeight: 1.65, maxWidth: 320 }}>
                  Système d'Information Intelligent conçu pour moderniser la gestion universitaire au Sénégal.
                </p>
              </div>
              <div style={{ display: 'flex', gap: 40 }}>
                {[
                  { title: 'Portail', links: ['Connexion', 'Inscription', 'Mon dossier'] },
                  { title: 'Info', links: ['Documentation', 'Contact', 'Vérifier attestation'] },
                ].map(col => (
                  <div key={col.title}>
                    <div style={{ fontSize: 11, fontWeight: 700, color: 'rgba(255,255,255,.5)', textTransform: 'uppercase', letterSpacing: '.08em', marginBottom: 14 }}>{col.title}</div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 9 }}>
                      {col.links.map(l => <a key={l} className="footer-link" href="#">{l}</a>)}
                    </div>
                  </div>
                ))}
              </div>
            </div>
            {/* Divider */}
            <div style={{ height: 1, background: 'rgba(255,255,255,.06)', marginBottom: 24 }} />
            {/* Bottom */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
              <p style={{ fontSize: 12, color: 'rgba(255,255,255,.15)' }}>
                © 2025 UADB — Projet de fin d'études — Bambey, Sénégal
              </p>
              <div style={{ display: 'flex', gap: 6 }}>
                {['8 microservices', 'PostgreSQL', 'MinIO', 'Django REST'].map(t => (
                  <span key={t} style={{
                    fontSize: 10.5, color: 'rgba(255,255,255,.25)',
                    background: 'rgba(255,255,255,.04)', border: '1px solid rgba(255,255,255,.07)',
                    borderRadius: 6, padding: '3px 8px',
                  }}>{t}</span>
                ))}
              </div>
            </div>
          </div>
        </footer>
      </div>
    </>
  )
}
