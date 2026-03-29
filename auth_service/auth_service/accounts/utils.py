from .models import JournalAudit


def tracer_action(request, action, ressource, details=None, utilisateur=None):
    """
    Enregistre une action dans le JournalAudit.
    Appelé depuis toutes les vues sensibles.
    """
    user = utilisateur or (
        request.user if request.user.is_authenticated else None
    )
    JournalAudit.objects.create(
        utilisateur = user,
        action      = action,
        ressource   = ressource,
        acteur      = user.username if user else 'anonyme',
        adresse_ip  = get_client_ip(request),
        user_agent  = request.META.get('HTTP_USER_AGENT', '')[:255],
        details     = details,
    )


def get_client_ip(request):
    """Récupère l'IP réelle du client (derrière proxy)."""
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        return x_forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')
