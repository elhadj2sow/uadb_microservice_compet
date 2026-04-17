import { useEffect, useState } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { CheckCircle, XCircle, Loader2, ArrowLeft } from 'lucide-react'

const API_BASE = ''  // URL relative — proxy Vite vers localhost:8002

export default function PaiementSuccess() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()

  // PayTech envoie ref_command et/ou token dans l'URL de succès
  const refCommand = searchParams.get('ref_command') || searchParams.get('ref')
  const token = searchParams.get('token')

  const [status, setStatus] = useState('loading') // loading | success | already | error
  const [message, setMessage] = useState('')
  const [inscriptionId, setInscriptionId] = useState(null)

  useEffect(() => {
    if (!refCommand) {
      setStatus('error')
      setMessage('Référence de paiement introuvable dans l\'URL. Contactez l\'administration.')
      return
    }

    const confirmer = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/paiements/confirmer-success/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ ref_command: refCommand, token }),
        })

        const data = await res.json()

        if (res.ok) {
          setInscriptionId(data.inscription_id)
          if (data.already_confirmed) {
            setStatus('already')
            setMessage('Votre paiement était déjà confirmé. Votre inscription est active.')
          } else {
            setStatus('success')
            setMessage(`Paiement de ${data.montant_paye?.toLocaleString('fr-FR')} FCFA confirmé avec succès.`)
          }
        } else {
          setStatus('error')
          setMessage(data.error || 'Impossible de confirmer le paiement. Contactez l\'administration.')
        }
      } catch {
        setStatus('error')
        setMessage('Erreur réseau. Votre paiement a peut-être été reçu — contactez l\'administration si votre inscription n\'est pas mise à jour.')
      }
    }

    confirmer()
  }, [refCommand, token])

  const goToInscription = () => {
    // Essayer de retourner vers la page inscription étudiant
    navigate('/etudiant/inscription')
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <div className="bg-white rounded-2xl shadow-lg p-10 max-w-md w-full text-center">

        {status === 'loading' && (
          <>
            <Loader2 className="w-16 h-16 text-blue-500 mx-auto mb-4 animate-spin" />
            <h1 className="text-xl font-semibold text-gray-700 mb-2">Confirmation du paiement…</h1>
            <p className="text-gray-500 text-sm">Veuillez patienter quelques secondes.</p>
          </>
        )}

        {(status === 'success' || status === 'already') && (
          <>
            <CheckCircle className="w-16 h-16 text-green-500 mx-auto mb-4" />
            <h1 className="text-2xl font-bold text-green-700 mb-3">Paiement accepté !</h1>
            <p className="text-gray-600 mb-6">{message}</p>
            {refCommand && (
              <p className="text-xs text-gray-400 mb-6 font-mono">Réf : {refCommand}</p>
            )}
            <button
              onClick={goToInscription}
              className="w-full flex items-center justify-center gap-2 px-6 py-3 bg-green-600 text-white rounded-xl font-semibold hover:bg-green-700 transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
              Voir mon inscription
            </button>
          </>
        )}

        {status === 'error' && (
          <>
            <XCircle className="w-16 h-16 text-red-400 mx-auto mb-4" />
            <h1 className="text-xl font-bold text-red-700 mb-3">Confirmation impossible</h1>
            <p className="text-gray-600 mb-6 text-sm">{message}</p>
            {refCommand && (
              <p className="text-xs text-gray-400 mb-6">
                Référence à communiquer : <span className="font-mono font-semibold">{refCommand}</span>
              </p>
            )}
            <button
              onClick={goToInscription}
              className="w-full flex items-center justify-center gap-2 px-6 py-3 bg-gray-600 text-white rounded-xl font-semibold hover:bg-gray-700 transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
              Retour à mon inscription
            </button>
          </>
        )}

      </div>
    </div>
  )
}
