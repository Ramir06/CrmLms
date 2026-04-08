import os
from pathlib import Path
import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Безопасная загрузка .env с очисткой от Windows символов
def load_env_cleanly(env_path):
    """Загружает .env файл с полной очисткой от проблемных символов"""
    if not env_path.exists():
        return
    
    # Читаем файл в бинарном режиме для точного контроля
    with open(env_path, 'rb') as f:
        raw_content = f.read()
    
    # Декодируем с обработкой ошибок
    try:
        content = raw_content.decode('utf-8')
    except UnicodeDecodeError:
        # Пробуем Latin-1 как запасной вариант
        content = raw_content.decode('latin-1')
    
    # Очищаем каждую строку и устанавливаем переменные
    for line in content.split('\n'):
        line = line.strip().replace('\r', '').replace('\n', '')
        if line and '=' in line:
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip()
            os.environ[key] = value

# Загружаем .env с очисткой
load_env_cleanly(BASE_DIR / '.env')

env = environ.Env(
    DEBUG=(bool, False),
)

SECRET_KEY = env('SECRET_KEY', default='django-insecure-change-me-in-production')

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])

DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
]

THIRD_PARTY_APPS = [
    'widget_tweaks',
    'crispy_forms',
    'crispy_bootstrap5',
    'axes',
    'corsheaders',
    'rest_framework',
    'django_filters',
    'drf_spectacular',
    'ckeditor',
]

LOCAL_APPS = [
    'apps.core',
    'apps.accounts',
    'apps.dashboard',
    'apps.manager',
    'apps.news',
    'apps.courses',
    'apps.students',
    'apps.mentors',
    'apps.calendar_app',
    'apps.payments',
    'apps.debts',
    'apps.salaries',
    'apps.leads',
    'apps.finance',
    'apps.lectures',
    'apps.assignments',
    'apps.lessons',
    'apps.attendance',
    'apps.rating',
    'apps.reviews',
    'apps.reports',
    'apps.notifications',
    'apps.quizzes',
    'apps.students_portal',
    'apps.settings',
    'apps.organizations',
    'apps.codecoins',
    'apps.chat',
    'apps.feedback',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'axes.middleware.AxesMiddleware',
    'apps.core.middleware.OrganizationMiddleware',
    'apps.manager.middleware.ManagerRedirectMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.core.middleware.RoleMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.core.context_processors.global_context',
                'apps.students_portal.context_processors.notification_context',
                'apps.students_portal.context_processors.student_course_context',
                'apps.settings.context_processors.footer_content',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DB_NAME', default='crm_lms_db'),
        'USER': env('DB_USER', default='postgres'),
        'PASSWORD': env('DB_PASSWORD', default='postgres'),
        'HOST': env('DB_HOST', default='localhost'),
        'PORT': env('DB_PORT', default='5432'),
    }
}

# Безопасные хешеры паролей с PBKDF2 + bcrypt
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
]

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 12}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'ru'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

LANGUAGES = [
    ('ru', 'Русский'),
    ('en', 'English'),
    ('ky', 'Кыргызча'),
]

LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'accounts.CustomUser'

LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/accounts/login/'

# Настройки сессий - 30 минут неактивности
SESSION_COOKIE_AGE = 1800  # 30 минут в секундах
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Session Security
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'  # В production 'Strict'

# Дополнительные настройки безопасности
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Security Headers
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'

# Для development (в production будет True)
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False

# Rate limiting с django-axes
AXES_FAILURE_LIMIT = 5  # Максимум 5 неудачных попыток
AXES_COOLOFF_TIME = 0.5  # Блокировка на 30 минут (0.5 часа)
AXES_COOLOFF_TIME_MULTIPLIER = 1  # Множитель времени
AXES_RESET_ON_SUCCESS = True  # Сброс счетчика при успешном входе
AXES_LOCKOUT_TEMPLATE = 'auth/lockout.html'
AXES_LOCKOUT_URL = '/auth/lockout/'
AXES_VERBOSITY = 1  # Логирование попыток входа
AXES_LOGGER = 'axes'
AXES_ENABLE_ACCESS_FAILURE_LOG = True
AXES_LOCK_OUT_BY_COMBINATION_USER_AND_IP = True
AXES_ONLY_USER_FAILURES = False  # Блокировать и по IP для неизвестных пользователей

# CORS настройки
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = False

# REST Framework Configuration
from apps.core.api_settings import REST_FRAMEWORK, SPECTACULAR_SETTINGS

CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap5'
CRISPY_TEMPLATE_PACK = 'bootstrap5'

AUTHENTICATION_BACKENDS = [
    'axes.backends.AxesBackend',  # Добавляем Axes backend для rate limiting
    'apps.core.auth_backends.SecureAuthenticationBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# Email settings
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = env('EMAIL_HOST')
EMAIL_PORT = env('EMAIL_PORT', cast=int)
EMAIL_USE_TLS = True
EMAIL_HOST_USER = env('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL')

# Custom error pages
DEBUG_404 = False

# CKEditor Configuration
CKEDITOR_UPLOAD_PATH = "uploads/"
CKEDITOR_CONFIGS = {
    'default': {
        'toolbar': 'full',
        'height': 300,
        'width': '100%',
    }
}
