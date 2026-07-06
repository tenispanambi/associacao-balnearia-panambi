from pathlib import Path
from decouple import config
import dj_database_url


BASE_DIR = Path(__file__).resolve().parent.parent


# ===========================
# Segurança
# ===========================

SECRET_KEY = config(
    'SECRET_KEY',
    default='django-insecure-troque-esta-chave'
)

DEBUG = config('DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = ['*']

CSRF_TRUSTED_ORIGINS = [
    'https://associacao-balnearia-panambi-production.up.railway.app',
]


# ===========================
# Apps
# ===========================

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'crispy_forms',
    'crispy_bootstrap5',

    'reservas',
]


# ===========================
# Crispy
# ===========================

CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap5'
CRISPY_TEMPLATE_PACK = 'bootstrap5'


# ===========================
# Middleware
# ===========================

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',

    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


ROOT_URLCONF = 'reserva_balnearia.urls'


# ===========================
# Templates
# ===========================

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',

        'DIRS': [
            BASE_DIR / 'templates'
        ],

        'APP_DIRS': True,

        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


WSGI_APPLICATION = 'reserva_balnearia.wsgi.application'


# ===========================
# Banco
# ===========================

DATABASE_URL = config('DATABASE_URL', default='')

if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
            ssl_require=True
        )
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


# ===========================
# Senhas
# ===========================

AUTH_PASSWORD_VALIDATORS = []


# ===========================
# Idioma
# ===========================

LANGUAGE_CODE = 'pt-br'

TIME_ZONE = 'America/Sao_Paulo'

USE_I18N = True

USE_TZ = True


# ===========================
# Arquivos estáticos e mídia
# ===========================

STATIC_URL = '/static/'

STATICFILES_DIRS = [
    BASE_DIR / 'static'
]

STATIC_ROOT = BASE_DIR / 'staticfiles'

STORAGES = {
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedStaticFilesStorage',
    },
}

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'