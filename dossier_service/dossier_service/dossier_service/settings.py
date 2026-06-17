from pathlib import Path
from decouple import config
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY')
DEBUG      = config('DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'dossier',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'dossier_service.urls'

TEMPLATES = [
    {
        'BACKEND' : 'django.template.backends.django.DjangoTemplates',
        'DIRS'    : [],
        'APP_DIRS': True,
        'OPTIONS' : {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'dossier_service.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE'  : 'django.db.backends.postgresql',
        'NAME'    : config('DB_NAME',     default='uadb2_db'),
        'USER'    : config('DB_USER',     default='uadb2_user'),
        'PASSWORD': config('DB_PASSWORD', default='uadb2_pass'),
        'HOST'    : config('DB_HOST',     default='localhost'),
        'PORT'    : config('DB_PORT',     default='5432'),
        'OPTIONS' : {
            'options': '-c search_path=dossier,public'
        },
    }
}

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'dossier.authentication.JWTFromAuthServiceAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS':
        'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME' : timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'AUTH_HEADER_TYPES'     : ('Bearer',),
    'USER_ID_FIELD'         : 'id',
    'USER_ID_CLAIM'         : 'user_id',
}

CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
]
CORS_ALLOW_ALL_ORIGINS = config('DEBUG', default=False, cast=bool)

LANGUAGE_CODE = 'fr-fr'
TIME_ZONE     = 'Africa/Dakar'
USE_I18N      = True
USE_TZ        = True

STATIC_URL = '/static/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ── Stockage fichiers MinIO ───────────────────────────────
MINIO_ENDPOINT   = config('MINIO_ENDPOINT',   default='localhost:9000')
MINIO_ACCESS_KEY = config('MINIO_ACCESS_KEY', default='minioadmin')
MINIO_SECRET_KEY = config('MINIO_SECRET_KEY', default='minioadmin')
MINIO_BUCKET     = config('MINIO_BUCKET',     default='uadb-dossiers')
MINIO_USE_SSL    = config('MINIO_USE_SSL',    default=False, cast=bool)

# ── URLs des autres microservices ─────────────────────────
SERVICE_AUTH         = config('SERVICE_AUTH',         default='http://localhost:8001')
SERVICE_INSCRIPTION  = config('SERVICE_INSCRIPTION',  default='http://localhost:8002')
SERVICE_IA           = config('SERVICE_IA',           default='http://localhost:8007')
SERVICE_NOTIFICATION = config('SERVICE_NOTIFICATION', default='http://localhost:8006')

SERVICE_INTERNAL_USER     = config('SERVICE_INTERNAL_USER',     default='service_dossier')
SERVICE_INTERNAL_PASSWORD = config('SERVICE_INTERNAL_PASSWORD', default='secret')

# ── Taille max upload ─────────────────────────────────────
MAX_UPLOAD_SIZE = config('MAX_UPLOAD_SIZE', default=5242880, cast=int)

# ── Types MIME autorisés ──────────────────────────────────
ALLOWED_MIME_TYPES = [
    'application/pdf',
    'image/jpeg',
    'image/png',
    'image/jpg',
]

# -- Service audit centralise ------------------------------------------
AUDIT_SERVICE_URL      = config('AUDIT_SERVICE_URL',      default='http://localhost:8008')
INTERNAL_SERVICE_TOKEN = config('INTERNAL_SERVICE_TOKEN', default='')
