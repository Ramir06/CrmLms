from .base import *  # noqa

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

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

# Add back RoleMiddleware with security features
MIDDLEWARE = [
    m for m in MIDDLEWARE 
    if m != 'apps.core.middleware.RoleMiddleware'
]

# Add RoleMiddleware back for security
MIDDLEWARE.append('apps.core.middleware.RoleMiddleware')

# Временно отключаем DebugURLMiddleware
# MIDDLEWARE.append('config.urls.DebugURLMiddleware')

INTERNAL_IPS = ['127.0.0.1']

# Disable template caching for development
TEMPLATES[0]['OPTIONS']['debug'] = DEBUG
