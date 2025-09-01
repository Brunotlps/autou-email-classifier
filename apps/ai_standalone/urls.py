"""
URLs para IA standalone
"""
from django.urls import path
from . import views

urlpatterns = [
    path('health/', views.health_check, name='ai_health'),
    path('classify/', views.classify_text_direct, name='ai_classify'),
]
