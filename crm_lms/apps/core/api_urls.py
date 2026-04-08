"""
Secure API URLs Configuration
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken import views as drf_authtoken_views
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

from .api_views import (
    UserViewSet,
    UserProfileView,
    PublicAPIListView,
    SecureDataView,
    DataValidationView
)

# Создаем router для ViewSets
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='api-users')

app_name = 'api'

urlpatterns = [
    # API Documentation
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='api:schema'), name='swagger-ui'),
    path('redoc/', SpectacularRedocView.as_view(url_name='api:schema'), name='redoc'),
    
    # Authentication
    path('auth/token/', drf_authtoken_views.obtain_auth_token, name='api_token'),
    
    # ViewSet URLs
    path('', include(router.urls)),
    
    # Custom API Views
    path('profile/', UserProfileView.as_view(), name='user_profile'),
    path('public/', PublicAPIListView.as_view(), name='public_api'),
    path('secure/', SecureDataView.as_view(), name='secure_data'),
    path('validate/', DataValidationView.as_view(), name='data_validation'),
]
