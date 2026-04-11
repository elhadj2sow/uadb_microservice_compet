import logging
from django.utils import timezone

logger = logging.getLogger(__name__)


def get_client_ip(request):
    """Récupère l'IP réelle du client (derrière proxy)."""
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        return x_forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')


def tracer(
    action,
    service,
    request=None,
    utilisateur_id=None,
    acteur='',
    role_acteur='',
    ressource='',
    ressource_id=None,
    ressource_type='',
    description='',
    niveau='INFO',
    statut='succes',
    details=None,
    message_erreur='',
    **refs
):
    """
    Fonction utilitaire pour créer une entrée dans le journal.
    Peut être appelée depuis n'importe quel service Django
    ou depuis l'endpoint REST.

    refs : etudiant_id, inscription_id, dossier_id,
           deliberation_id, attestation_id
    """
    from .models import JournalAudit

    adresse_ip  = ''
    user_agent  = ''
    methode_http= ''
    url         = ''

    if request:
        adresse_ip   = get_client_ip(request)
        user_agent   = request.META.get('HTTP_USER_AGENT', '')[:500]
        methode_http = request.method
        url          = request.path

        if not utilisateur_id and hasattr(request, 'user'):
            utilisateur_id = getattr(request.user, 'id', None)
        if not acteur and hasattr(request, 'user'):
            acteur = getattr(request.user, 'username', '')
        if not role_acteur and hasattr(request, 'user'):
            roles = getattr(request.user, 'roles', [])
            role_acteur = roles[0] if roles else ''

    try:
        JournalAudit.objects.create(
            utilisateur_id  = utilisateur_id,
            acteur          = acteur,
            role_acteur     = role_acteur,
            action          = action,
            niveau          = niveau,
            statut          = statut,
            description     = description,
            service         = service,
            ressource       = ressource,
            ressource_id    = ressource_id,
            ressource_type  = ressource_type,
            adresse_ip      = adresse_ip,
            user_agent      = user_agent,
            methode_http    = methode_http,
            url             = url,
            details         = details,
            message_erreur  = message_erreur,
            etudiant_id     = refs.get('etudiant_id'),
            inscription_id  = refs.get('inscription_id'),
            dossier_id      = refs.get('dossier_id'),
            deliberation_id = refs.get('deliberation_id'),
            attestation_id  = refs.get('attestation_id'),
        )
    except Exception as e:
        logger.error(f"Erreur création entrée audit : {e}")


def calculer_statistiques_jour(date=None):
    """
    Calcule les statistiques d'audit pour une date donnée
    et les stocke dans StatistiqueAudit.
    """
    from .models import JournalAudit, StatistiqueAudit
    from django.db.models import Count

    if date is None:
        date = timezone.now().date()

    qs = JournalAudit.objects.filter(date_action__date=date)

    nb_actions   = qs.count()
    nb_connexions   = qs.filter(action='LOGIN').count()
    nb_echecs    = qs.filter(statut='echec').count()
    nb_alertes   = qs.filter(action='ALERTE').count()

    # Stats par service
    stats_services = {}
    for item in qs.values('service').annotate(nb=Count('id')):
        stats_services[item['service'] or 'inconnu'] = item['nb']

    # Stats par action
    stats_actions = {}
    for item in qs.values('action').annotate(nb=Count('id')):
        stats_actions[item['action']] = item['nb']

    stat, _ = StatistiqueAudit.objects.update_or_create(
        date=date,
        defaults={
            'nb_actions'    : nb_actions,
            'nb_connexions' : nb_connexions,
            'nb_echecs'     : nb_echecs,
            'nb_alertes'    : nb_alertes,
            'stats_services': stats_services,
            'stats_actions' : stats_actions,
        }
    )
    return stat
