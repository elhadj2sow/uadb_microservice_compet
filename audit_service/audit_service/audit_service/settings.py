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
    'audit',
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

ROOT_URLCONF = 'audit_service.urls'

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

WSGI_APPLICATION = 'audit_service.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE'  : 'django.db.backends.postgresql',
        'NAME'    : config('DB_NAME',     default='uadb7_db'),
        'USER'    : config('DB_USER',     default='uadb7_user'),
        'PASSWORD': config('DB_PASSWORD', default='uadb7_pass'),
        'HOST'    : config('DB_HOST',     default='localhost'),
        'PORT'    : config('DB_PORT',     default='5432'),
        'OPTIONS' : {
            'options': '-c search_path=audit,public'
        },
    }
}

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'audit.authentication.JWTFromAuthServiceAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS':
        'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME' : timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'AUTH_HEADER_TYPES'     : ('Bearer',),
    'USER_ID_FIELD'         : 'id',
    'USER_ID_CLAIM'         : 'user_id',
    # Doit matcher la clé de signature du auth_service.
    'SIGNING_KEY'           : config('JWT_SIGNING_KEY', default=SECRET_KEY),
}

CORS_ALLOWED_ORIGINS   = ['http://localhost:3000']
CORS_ALLOW_ALL_ORIGINS = config('DEBUG', default=False, cast=bool)

LANGUAGE_CODE = 'fr-fr'
TIME_ZONE     = 'Africa/Dakar'
USE_I18N      = True
USE_TZ        = True

STATIC_URL         = '/static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Service auth
SERVICE_AUTH = config('SERVICE_AUTH', default='http://localhost:8001')

SERVICE_INTERNAL_USER     = config('SERVICE_INTERNAL_USER',     default='service_audit')
SERVICE_INTERNAL_PASSWORD = config('SERVICE_INTERNAL_PASSWORD', default='secret')

# Token partagé pour appels inter-services sans JWT utilisateur
INTERNAL_SERVICE_TOKEN = config('INTERNAL_SERVICE_TOKEN', default='')

# Rétention des logs
RETENTION_JOURS = config('RETENTION_JOURS', default=365, cast=int)
