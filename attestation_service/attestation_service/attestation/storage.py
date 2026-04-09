import boto3
import logging
from django.conf import settings
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


def get_minio_client():
    protocol = 'https' if settings.MINIO_USE_SSL else 'http'
    return boto3.client(
        's3',
        endpoint_url          = f"{protocol}://{settings.MINIO_ENDPOINT}",
        aws_access_key_id     = settings.MINIO_ACCESS_KEY,
        aws_secret_access_key = settings.MINIO_SECRET_KEY,
        region_name           = 'us-east-1',
    )


def ensure_bucket_exists():
    client = get_minio_client()
    try:
        client.head_bucket(Bucket=settings.MINIO_BUCKET)
    except ClientError:
        try:
            client.create_bucket(Bucket=settings.MINIO_BUCKET)
            logger.info(f"Bucket '{settings.MINIO_BUCKET}' créé.")
        except Exception as e:
            logger.error(f"Erreur création bucket : {e}")


def stocker_pdf(buffer, chemin):
    """Stocke un buffer PDF sur MinIO. Retourne True si succès."""
    try:
        client = get_minio_client()
        ensure_bucket_exists()
        buffer.seek(0)
        client.upload_fileobj(
            buffer,
            settings.MINIO_BUCKET,
            chemin,
            ExtraArgs={'ContentType': 'application/pdf'}
        )
        logger.info(f"PDF stocké : {chemin}")
        return True
    except Exception as e:
        logger.error(f"Erreur stockage PDF : {e}")
        return False


def stocker_image(buffer, chemin):
    """Stocke un buffer image (QR code) sur MinIO."""
    try:
        client = get_minio_client()
        ensure_bucket_exists()
        buffer.seek(0)
        client.upload_fileobj(
            buffer,
            settings.MINIO_BUCKET,
            chemin,
            ExtraArgs={'ContentType': 'image/png'}
        )
        logger.info(f"Image stockée : {chemin}")
        return True
    except Exception as e:
        logger.error(f"Erreur stockage image : {e}")
        return False


def generer_url_telechargement(chemin, expiration=300):
    """URL signée valable {expiration} secondes."""
    try:
        client = get_minio_client()
        url = client.generate_presigned_url(
            'get_object',
            Params    = {
                'Bucket': settings.MINIO_BUCKET,
                'Key'   : chemin,
            },
            ExpiresIn = expiration
        )
        return url
    except Exception as e:
        logger.error(f"Erreur URL signée : {e}")
        return None
