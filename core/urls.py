from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

# Criar router para API Root
router = DefaultRouter()

urlpatterns = [
    # Django Admin
    path("admin/", admin.site.urls),

    # Redirect root to API
    path('', RedirectView.as_view(url='/api/', permanent=False)),

    # API Root (navegação principal)
    path('api/', include(router.urls)),
    
    # DRF Authentication
    path('api-auth/', include('rest_framework.urls')),

    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # Apps URLs
    path('api/emails/', include('apps.emails.urls')),
    path('api/classifier/', include('apps.classifier.urls')),
]