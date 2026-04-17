import { useSearchParams, useNavigate } from 'react-router-dom'
import { XCircle, ArrowLeft, RefreshCw } from 'lucide-react'

export default function PaiementCancel() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()

  const refCommand = searchParams.get('ref_command') || searchParams.get('ref')

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <div className="bg-white rounded-2xl shadow-lg p-10 max-w-md w-full text-center">

        <XCircle className="w-16 h-16 text-orange-400 mx-auto mb-4" />
        <h1 className="text-2xl font-bold text-orange-700 mb-3">Paiement annulé</h1>
        <p className="text-gray-600 mb-4">
          Vous avez annulé le paiement. Aucun montant n'a été débité.
        </p>
        <p className="text-gray-500 text-sm mb-6">
          Vous pouvez réessayer à tout moment depuis votre espace inscription.
        </p>

        {refCommand && (
          <p className="text-xs text-gray-400 mb-6 font-mono">Réf : {refCommand}</p>
        )}

        <div className="flex flex-col gap-3">
          <button
            onClick={() => navigate('/etudiant/inscription')}
            className="w-full flex items-center justify-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-xl font-semibold hover:bg-blue-700 transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            Réessayer le paiement
          </button>
          <button
            onClick={() => navigate('/etudiant')}
            className="w-full flex items-center justify-center gap-2 px-6 py-3 border border-gray-300 text-gray-600 rounded-xl font-semibold hover:bg-gray-50 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Retour au tableau de bord
          </button>
        </div>

      </div>
    </div>
  )
}
