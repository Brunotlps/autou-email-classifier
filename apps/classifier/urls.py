"""
    URLs para o aplicativo de classificação / URLs for the classifier app

    CRUD Endpoints:
        GET    /api/classifier/classifications/           → Lista paginada / Paginated list
        POST   /api/classifier/classifications/           → Criar nova / Create new 
        GET    /api/classifier/classifications/1/         → Buscar por ID / Retrieve by ID
        PUT    /api/classifier/classifications/1/         → Atualizar completa / Full update
        PATCH  /api/classifier/classifications/1/         → Atualizar parcial / Partial update
        DELETE /api/classifier/classifications/1/         → Deletar / Delete
    
    Custom Actions:
        POST   /api/classifier/classifications/1/reprocess/ → Reprocessar / Reprocess
        GET    /api/classifier/classifications/stats/       → Estatísticas / Statistics

"""


from django.urls import path, include

from rest_framework.routers import DefaultRouter

from .views import ClassificationViewSet, dashboard_data_api, dashboard_stats_api


# Router para ViewSets / Routers for ViewSets
router = DefaultRouter()
router.register(r'classifications', ClassificationViewSet, basename='classification')


app_name = 'classifier'

urlpatterns = [
    # Rotas do ViewSet (CRUD) / ViewSet routes (CRUD)
    path('', include(router.urls)),

    # Endpoints da API Dashboard / Dashboard API endpoints
    path('dashboard-data/', dashboard_data_api, name='dashboard_data'),
    path('dashboard-stats/', dashboard_stats_api, name='dashboard_stats'),
]



