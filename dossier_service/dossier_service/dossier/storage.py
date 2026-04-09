import boto3
import uuid
import logging
from django.conf import settings
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


def get_minio_client():
    """Retourne un client boto3 configuré pour MinIO."""
    return boto3.client(
        's3',
        endpoint_url          = f"{'https' if settings.MINIO_USE_SSL else 'http'}://{settings.MINIO_ENDPOINT}",
        aws_access_key_id     = settings.MINIO_ACCESS_KEY,
        aws_secret_access_key = settings.MINIO_SECRET_KEY,
        region_name           = 'us-east-1',
    )


def ensure_bucket_exists():
    """Crée le bucket MinIO s'il n'existe pas."""
    client = get_minio_client()
    try:
        client.head_bucket(Bucket=settings.MINIO_BUCKET)
    except ClientError:
        try:
            client.create_bucket(Bucket=settings.MINIO_BUCKET)
            logger.info(f"Bucket '{settings.MINIO_BUCKET}' créé.")
        except Exception as e:
            logger.error(f"Impossible de créer le bucket : {e}")


def uploader_fichier(fichier, etudiant_id, type_piece):
    """
    Upload un fichier sur MinIO.
    Retourne le chemin de stockage ou None en cas d'erreur.

    Structure du chemin :
    dossiers/{etudiant_id}/{type_piece}/{uuid}.{extension}
    """
    try:
        extension   = fichier.name.rsplit('.', 1)[-1].lower()
        nom_unique  = f"{uuid.uuid4().hex}.{extension}"
        chemin      = f"dossiers/{etudiant_id}/{type_piece}/{nom_unique}"

        client = get_minio_client()
        ensure_bucket_exists()

        fichier.seek(0)
        client.upload_fileobj(
            fichier,
            settings.MINIO_BUCKET,
            chemin,
            ExtraArgs={'ContentType': fichier.content_type}
        )
        logger.info(f"Fichier uploadé : {chemin}")
        return chemin

    except Exception as e:
        logger.error(f"Erreur upload MinIO : {e}")
        return None


def supprimer_fichier(chemin_stockage):
    """Supprime un fichier de MinIO."""
    try:
        client = get_minio_client()
        client.delete_object(
            Bucket=settings.MINIO_BUCKET,
            Key   =chemin_stockage
        )
        logger.info(f"Fichier supprimé : {chemin_stockage}")
        return True
    except Exception as e:
        logger.error(f"Erreur suppression MinIO : {e}")
        return False


def generer_url_telechargement(chemin_stockage, expiration=300):
    """
    Génère une URL signée valable {expiration} secondes.
    Permet au frontend de télécharger directement depuis MinIO.
    """
    try:
        client = get_minio_client()
        url = client.generate_presigned_url(
            'get_object',
            Params     = {
                'Bucket': settings.MINIO_BUCKET,
                'Key'   : chemin_stockage,
            },
            ExpiresIn  = expiration
        )
        return url
    except Exception as e:
        logger.error(f"Erreur génération URL signée : {e}")
        return None
