"""
URLs para o app de emails
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'emails'

router = DefaultRouter()
router.register(r'', views.EmailViewSet, basename='email')

urlpatterns = [
    path('', include(router.urls)),
]
