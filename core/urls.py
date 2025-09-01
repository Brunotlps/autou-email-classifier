"""
URLs principais - Sistema completo AutoU Email Classifier
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse

# Imports para documentação API
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

# Import direto do ViewSet para resolver o problema de roteamento
from apps.classifier.views import ClassificationViewSet

def health_check(request):
    """Health check do sistema"""
    return JsonResponse({
        "status": "ok",
        "message": "AutoU Email Classifier - Sistema Completo!",
        "version": "1.0",
        "features": [
            "ai_classification",
            "api_rest", 
            "documentation",
            "admin_interface"
        ],
        "endpoints": {
            "health": "/health/",
            "admin": "/admin/",
            "api_docs": "/api/docs/",
            "api_schema": "/api/schema/",
            "api_redoc": "/api/redoc/"
        }
    })

urlpatterns = [
    # === CORE ===
    path('admin/', admin.site.urls),
    path('health/', health_check, name='health'),
    
    # === ROTA DIRETA PARA /upload-ajax/ (SOLUÇÃO DO PROBLEMA) ===
    path('upload-ajax/', ClassificationViewSet.as_view({
        'post': 'upload_ajax_direct',
        'get': 'upload_ajax_form'
    }), name='upload_ajax_direct'),
    
    # === APIs REST ===
    path('api/emails/', include('apps.emails.urls')),
    path('api/classifier/', include(('apps.classifier.urls', 'classifier'), namespace='api_classifier')),
    
    # === DOCUMENTAÇÃO API ===
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    
    # === FRONTEND ===
    path('', include('apps.frontend.urls')),
]

# Servir arquivos estáticos em desenvolvimento
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
