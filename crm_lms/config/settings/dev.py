from .base import *  # noqa

DEBUG = True

ALLOWED_HOSTS = ['*']

CSRF_TRUSTED_ORIGINS = [
    'http://127.0.0.1:8000',
    'http://localhost:8000',
]

# In dev, replace CsrfViewMiddleware with a version that trusts all localhost origins
MIDDLEWARE = [
    m if m != 'django.middleware.csrf.CsrfViewMiddleware'
    else 'apps.core.middleware.DevCsrfMiddleware'
    for m in MIDDLEWARE
]

INTERNAL_IPS = ['127.0.0.1']
