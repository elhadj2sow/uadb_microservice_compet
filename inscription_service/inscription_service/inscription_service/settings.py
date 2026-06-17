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
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'inscription',
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

ROOT_URLCONF = 'inscription_service.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'inscription_service.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE'  : 'django.db.backends.postgresql',
        'NAME'    : config('DB_NAME', default='uadb_db1'),
        'USER'    : config('DB_USER', default='uadb1_user'), 
        'PASSWORD': config('DB_PASSWORD', default='uadb1_pass'),
        'HOST'    : config('DB_HOST', default='localhost'),
        'PORT'    : config('DB_PORT', default='5432'),
        'OPTIONS' : {
            'options': '-c search_path=inscription,public'
        },
    }
}

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'inscription.authentication.JWTFromAuthServiceAuthentication',
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
    'ALGORITHM'             : 'HS256',
    'SIGNING_KEY'           : config('JWT_SIGNING_KEY', default=SECRET_KEY),
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

# URLs des autres microservices
SERVICE_AUTH         = config('SERVICE_AUTH',         default='http://localhost:8001')
SERVICE_DOSSIER      = config('SERVICE_DOSSIER',      default='http://localhost:8003')
SERVICE_DELIBERATION = config('SERVICE_DELIBERATION', default='http://localhost:8004')
SERVICE_IA           = config('SERVICE_IA',           default='http://localhost:8007')
SERVICE_NOTIFICATION = config('SERVICE_NOTIFICATION', default='http://localhost:8006')

SERVICE_INTERNAL_USER     = config('SERVICE_INTERNAL_USER',     default='service_inscription')
SERVICE_INTERNAL_PASSWORD = config('SERVICE_INTERNAL_PASSWORD', default='secret')

# Paiement en ligne PayTech
PAYTECH_ENABLED = config('PAYTECH_ENABLED', default=False, cast=bool)
PAYTECH_SANDBOX = config('PAYTECH_SANDBOX', default=True, cast=bool)
PAYTECH_BASE_URL = config('PAYTECH_BASE_URL', default='https://paytech.sn/api')
PAYTECH_API_KEY = config('PAYTECH_API_KEY', default='')
PAYTECH_API_SECRET = config('PAYTECH_API_SECRET', default='')
PAYTECH_SUCCESS_URL = config(
    'PAYTECH_SUCCESS_URL',
    default='http://localhost:3000/paiement/success'
)
PAYTECH_CANCEL_URL = config(
    'PAYTECH_CANCEL_URL',
    default='http://localhost:3000/paiement/cancel'
)
PAYTECH_WEBHOOK_URL = config(
    'PAYTECH_WEBHOOK_URL',
    default='http://localhost:8002/api/paiements/paytech/webhook/'
)

# -- Service audit centralise ------------------------------------------
AUDIT_SERVICE_URL      = config('AUDIT_SERVICE_URL',      default='http://localhost:8008')
INTERNAL_SERVICE_TOKEN = config('INTERNAL_SERVICE_TOKEN', default='')
