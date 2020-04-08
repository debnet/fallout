# coding: utf-8
import datetime
import os

from configurations import Configuration, values
from django.contrib import messages
from django.utils.translation import gettext_lazy as _


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Base(Configuration):

    # SECURITY WARNING: don't run with debug turned on in production!
    DEBUG = values.BooleanValue(False)
    INTERNAL_IPS = ['127.0.0.1']
    ALLOWED_HOSTS = values.ListValue(['*'])

    # Site
    SITE_ID = values.IntegerValue(1)
    HOSTNAME = values.Value('')

    # SECURITY WARNING: keep the secret key used in production secret!
    SECRET_KEY = values.SecretValue()

    # Application definition
    INSTALLED_APPS = [
        # Default
        'django.contrib.admin',
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.humanize',
        'django.contrib.sessions',
        'django.contrib.messages',
        'django.contrib.staticfiles',
        # Requirements
        'pytz',
        'corsheaders',
        'rest_framework',
        'rest_framework.authtoken',
        'rest_framework_simplejwt',
        'rest_framework_simplejwt.token_blacklist',
        'common',
        'multiselectfield',
        'compressor',
        # Applications
        'fallout',
    ]

    # Middleware
    MIDDLEWARE = [
        # CORS Headers
        'corsheaders.middleware.CorsMiddleware',
        # Default
        'django.middleware.security.SecurityMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.locale.LocaleMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
        'django.middleware.clickjacking.XFrameOptionsMiddleware',
        # Application defined
        'common.middleware.ServiceUsageMiddleware',
    ]

    # Database
    # https://docs.djangoproject.com/en/2.0/ref/settings/#databases
    DATABASES = values.DatabaseURLValue('sqlite://./db.sqlite3')
    DATABASE_ROUTERS = values.ListValue(('common.router.DatabaseOverrideRouter',))

    # URL router
    ROOT_URLCONF = 'rpg.urls'
    # WSGI entrypoint
    WSGI_APPLICATION = 'rpg.wsgi.application'

    # Templates configuration
    TEMPLATES = [
        {
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': (),
            'APP_DIRS': True,
            'OPTIONS': {
                'context_processors': [
                    'django.contrib.auth.context_processors.auth',
                    'django.contrib.messages.context_processors.messages',
                    'django.template.context_processors.request',
                    'django.template.context_processors.media',
                    'django.template.context_processors.debug',
                ],
            },
        },
    ]

    # Authentication backends
    AUTHENTICATION_BACKENDS = (
        'django.contrib.auth.backends.ModelBackend',
    )

    # Password validation
    # https://docs.djangoproject.com/en/2.0/ref/settings/#auth-password-validators
    AUTH_PASSWORD_VALIDATORS = [
        {
            'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
        },
        {
            'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        },
        {
            'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
        },
        {
            'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
        },
    ]

    # Internationalization
    # https://docs.djangoproject.com/en/2.0/topics/i18n/
    LANGUAGE_CODE = values.Value('fr')
    TIME_ZONE = values.Value('Europe/Paris')
    USE_I18N = values.BooleanValue(True)
    USE_L10N = values.BooleanValue(True)
    USE_TZ = values.BooleanValue(True)

    LANGUAGES = (
        ('fr', _('Français')),
        ('en', _('English')),
    )

    LOCALE_PATHS = (
        os.path.join(BASE_DIR, 'locale'),
        os.path.join(BASE_DIR, 'fallout/locale'),
    )

    # Static files (CSS, JavaScript, Images)
    # https://docs.djangoproject.com/en/2.0/howto/static-files/
    STATIC_URL = values.Value('/static/')
    STATIC_ROOT = os.path.join(BASE_DIR, 'static')

    STATICFILES_DIRS = (
        os.path.join(BASE_DIR, 'statics'),
    )

    STATICFILES_FINDERS = (
        'django.contrib.staticfiles.finders.AppDirectoriesFinder',
        'django.contrib.staticfiles.finders.FileSystemFinder',
        'compressor.finders.CompressorFinder',
    )

    # Media url and directory
    MEDIA_NAME = 'medias'
    MEDIA_URL = values.Value('/medias/')
    MEDIA_ROOT = values.Value(os.path.join(BASE_DIR, MEDIA_NAME))

    # Custom settings
    CELERY_ENABLE = values.BooleanValue(False)
    CORS_ORIGIN_ALLOW_ALL = values.BooleanValue(True)
    APPEND_SLASH = values.BooleanValue(True)

    # Django REST Framework configuration
    REST_FRAMEWORK = {
        'DEFAULT_PERMISSION_CLASSES': (
            'rest_framework.permissions.IsAuthenticated',
        ),
        'DEFAULT_AUTHENTICATION_CLASSES': (
            'rest_framework.authentication.TokenAuthentication',
            'rest_framework.authentication.SessionAuthentication',
            'rest_framework_simplejwt.authentication.JWTAuthentication',
        ),
        'DEFAULT_RENDERER_CLASSES': (
            'rest_framework.renderers.JSONRenderer',
            'rest_framework.renderers.BrowsableAPIRenderer',
            'rest_framework.renderers.AdminRenderer',
        ),
        'DEFAULT_PARSER_CLASSES': (
            'rest_framework.parsers.JSONParser',
            'rest_framework.parsers.FormParser',
            'rest_framework.parsers.MultiPartParser',
            'rest_framework.parsers.FileUploadParser',
        ),
        'DEFAULT_PAGINATION_CLASS': 'common.api.pagination.CustomPageNumberPagination',
        'PAGE_SIZE': 10,
        'TEST_REQUEST_DEFAULT_FORMAT': 'json',
        'COERCE_DECIMAL_TO_STRING': True,
        'HYPERLINKED': True,
    }

    # JSON Web Token Authentication
    SIMPLE_JWT = {
        'ACCESS_TOKEN_LIFETIME': datetime.timedelta(minutes=5),
        'REFRESH_TOKEN_LIFETIME': datetime.timedelta(days=1),
        'ROTATE_REFRESH_TOKENS': False,
        'BLACKLIST_AFTER_ROTATION': True,
        'ALGORITHM': 'HS256',
        'SIGNING_KEY': values.SecretValue(environ_name='SECRET_KEY'),
        'VERIFYING_KEY': None,
        'AUTH_HEADER_TYPES': ('Bearer', 'JWT',),
        'USER_ID_FIELD': 'id',
        'USER_ID_CLAIM': 'user_id',
        'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
        'TOKEN_TYPE_CLAIM': 'token_type',
        'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
        'SLIDING_TOKEN_LIFETIME': datetime.timedelta(minutes=5),
        'SLIDING_TOKEN_REFRESH_LIFETIME': datetime.timedelta(days=1),
    }

    # Login URLs
    LOGIN_URL = values.Value('login')
    LOGOUT_URL = values.Value('logout')
    LOGIN_REDIRECT_URL = values.Value('fallout:index')
    LOGOUT_REDIRECT_URL = values.Value('fallout:index')

    # User substitution
    AUTH_USER_MODEL = 'fallout.Player'

    # Messages
    MESSAGE_TAGS = {
        messages.DEBUG: values.Value('light', environ_name='CSS_DEBUG'),
        messages.INFO: values.Value('info', environ_name='CSS_INFO'),
        messages.SUCCESS: values.Value('success', environ_name='CSS_SUCCESS'),
        messages.WARNING: values.Value('warning', environ_name='CSS_WARNING'),
        messages.ERROR: values.Value('danger error', environ_name='CSS_ERROR'),
    }
    CSS_CLASSES = {
        (1, 1): values.Value('info', environ_name='CSS_INFO'),
        (1, 0): values.Value('success', environ_name='CSS_SUCCESS'),
        (0, 0): values.Value('warning', environ_name='CSS_WARNING'),
        (0, 1): values.Value('danger error', environ_name='CSS_ERROR'),
    }
    MESSAGE_INFOS = {
        (1, 1): messages.INFO,
        (1, 0): messages.SUCCESS,
        (0, 0): messages.WARNING,
        (0, 1): messages.ERROR,
    }

    # CSS and JS compression
    COMPRESS_ENABLED = values.BooleanValue(True)
    COMPRESS_OFFLINE = values.BooleanValue(False)
    COMPRESS_OUTPUT_DIR = values.Value('_cache')

    # Clé secrète pour les communications sécurisées entre le front et les APIs
    FRONTEND_SECRET_KEY = values.Value('')

    # Durée de validité du lien de réinitialisation de mot de passe
    PASSWORD_RESET_TIMEOUT_DAYS = values.IntegerValue(1)

    # Gestionnaire utilisé pour l'import des fichiers
    FILE_UPLOAD_HANDLERS = ('common.utils.TemporaryFileHandler', )

    # Taille du payload maximum autorisée et permissions à l'upload
    DATA_UPLOAD_MAX_MEMORY_SIZE = values.IntegerValue(10485760)
    FILE_UPLOAD_PERMISSIONS = values.IntegerValue(0o644)

    # Stocke le token CSRF en session plutôt que dans un cookie
    CSRF_USE_SESSIONS = values.BooleanValue(False)

    # E-mail configuration
    EMAIL_HOST = values.Value('')
    EMAIL_HOST_USER = values.Value('')
    EMAIL_HOST_PASSWORD = values.Value('')
    EMAIL_PORT = values.IntegerValue(25)
    EMAIL_SUBJECT_PREFIX = values.Value("")
    EMAIL_USE_TLS = values.BooleanValue(False)
    EMAIL_USE_SSL = values.BooleanValue(False)
    EMAIL_TIMEOUT = values.IntegerValue(300)
    DEFAULT_FROM_EMAIL = values.Value('Fallout <fallout@debnet.fr>')

    # Logging configuration
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'simple': {
                'format': '[%(asctime)s] %(levelname)7s: %(message)s',
                'datefmt': '%d/%m/%Y %H:%M:%S',
            },
        },
        'handlers': {
            'console': {
                'level': 'INFO',
                'class': 'logging.StreamHandler',
                'formatter': 'simple',
            },
            'file': {
                'level': 'WARNING',
                'class': 'logging.FileHandler',
                'filename': 'rpg.log',
                'formatter': 'simple',
            },
        },
        'loggers': {
            '': {
                'handlers': ['console'],
                'level': 'INFO',
                'propagate': True,
            },
            'django': {
                'handlers': ['console'],
                'level': 'INFO',
                'propagate': False,
            },
        }
    }


class Prod(Base):
    """
    Configuration de production
    """

    DEBUG = False

    # HTTPS/SSL
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = values.BooleanValue(True)
    SESSION_COOKIE_SECURE = values.BooleanValue(True)
    CSRF_COOKIE_SECURE = values.BooleanValue(True)

    DJANGO_REDIS_IGNORE_EXCEPTIONS = True
    SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
    SESSION_CACHE_ALIAS = 'default'

    CACHE_MIDDLEWARE_ALIAS = 'default'
    CACHE_MIDDLEWARE_SECONDS = 0
    CACHE_MIDDLEWARE_KEY_PREFIX = ''

    # Cache
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': [
                values.Value('127.0.0.1:6379:1', environ_name='REDIS_CACHE'),
            ],
            'KEY_PREFIX': 'cache',
            'TIMEOUT': 3600,
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'IGNORE_EXCEPTIONS': True,
            },
        }
    }

    # Cache middleware
    MIDDLEWARE = [
        'django.middleware.cache.UpdateCacheMiddleware',
        *Base.MIDDLEWARE,
        'django.middleware.cache.FetchFromCacheMiddleware',
    ]

    # Celery configuration
    CELERY_ENABLE = values.BooleanValue(True)
    CELERY_BROKER_URL = BROKER_URL = values.Value('redis://localhost:6379/1', environ_name='CELERY_BROKER_URL')
    CELERY_BROKER_TRANSPORT_OPTIONS = BROKER_TRANSPORT_OPTIONS = {
        'visibility_timeout': 3600,
        'fanout_prefix': True,
        'fanout_patterns': True,
    }
    CELERY_ACCEPT_CONTENT = ['json', 'msgpack', 'yaml', 'pickle']
    CELERY_RESULT_SERIALIZER = 'pickle'
    CELERY_RESULT_BACKEND = values.Value('redis')
    CELERY_TASK_SERIALIZER = 'pickle'
    CELERY_TASK_RESULT_EXPIRES = 3600
    CELERY_DISABLE_RATE_LIMITS = True
    CELERY_TASK_ALWAYS_EAGER = values.BooleanValue(False, environ_name='CELERY_TASK_ALWAYS_EAGER')
    CELERY_TASK_EAGER_PROPAGATES = False
    CELERY_TASK_DEFAULT_QUEUE = values.Value('celery', environ_name='QUEUE_NAME')


class Test(Base):
    """
    Configuration de développement
    """

    DEBUG = True
    INTERNAL_IPS = ('localhost', '127.0.0.1', '[::1]', 'testserver', '*')
    ALLOWED_HOSTS = INTERNAL_IPS

    # Celery configuration: toujours eager, permet d'éviter à avoir les workers et le broker activés
    CELERY_TASK_ALWAYS_EAGER = True
    CELERY_RESULT_BACKEND = 'cache'
    CELERY_CACHE_BACKEND = 'memory'

    # Django Debug Toolbar
    DEBUG_TOOLBAR_ENABLE = True
    if DEBUG_TOOLBAR_ENABLE:
        INSTALLED_APPS = Base.INSTALLED_APPS + ['debug_toolbar']
        MIDDLEWARE = ['debug_toolbar.middleware.DebugToolbarMiddleware'] + Base.MIDDLEWARE
        DEBUG_TOOLBAR_PATCH_SETTINGS = False
        DEBUG_TOOLBAR_CONFIG = {
            'JQUERY_URL': '',
        }

    # Disable password security
    AUTH_PASSWORD_VALIDATORS = []

    # Cache
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'unique-snowflake',
            'TIMEOUT': 3600,
        },
    }
