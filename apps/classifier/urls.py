"""
URLs para o aplicativo de classificação
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ClassificationViewSet, dashboard_data_api, dashboard_stats_api

# Router para ViewSets
router = DefaultRouter()
router.register(r"classifications", ClassificationViewSet, basename="classification")

app_name = "classifier"

urlpatterns = [
    # Rotas do ViewSet (CRUD)
    path("", include(router.urls)),
    
    # Endpoints da API Dashboard
    path("dashboard-data/", dashboard_data_api, name="dashboard_data"),
    path("dashboard-stats/", dashboard_stats_api, name="dashboard_stats"),
]
