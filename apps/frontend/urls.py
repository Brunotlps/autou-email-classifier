from django.urls import path
from .views import HomeView, UploadView, DashboardView, DashboardTestView, ResultsView, HistoryView



app_name = 'frontend'

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('upload/', UploadView.as_view(), name='upload'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('dashboard/test/', DashboardTestView.as_view(), name='dashboard_test'),  
    path('results/', ResultsView.as_view(), name='results'),
    path('history/', HistoryView.as_view(), name='history'),
]