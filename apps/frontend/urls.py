"""
URLs do frontend - CORRIGIDO com indentação correta
"""
from django.urls import path
from . import views

app_name = "frontend"

urlpatterns = [
    # === PÁGINAS PRINCIPAIS ===
    path("", views.home_view, name="home"),
    path("upload/", views.upload_view, name="upload"),
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path("results/", views.results_view, name="results"),
    
    # === ENDPOINTS AJAX ===
    path("upload-ajax/", views.upload_ajax, name="upload_ajax"),
    
    # === API ENDPOINTS ===
    path("api/classifications/", views.api_classifications, name="api_classifications"),
    
    # === HEALTH CHECKS ===
    path("health/", views.health_check, name="health"),
    path("readiness/", views.readiness_check, name="readiness"),
    path("liveness/", views.liveness_check, name="liveness"),
    
    # === ALIASES PARA COMPATIBILIDADE ===
    path("history/", views.results_view, name="history"),
    path("dashboard/test/", views.dashboard_view, name="dashboard_test"),
]
