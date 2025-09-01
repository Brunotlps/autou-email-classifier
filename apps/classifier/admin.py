"""
Admin configuration for Email Classifier - CORRIGIDO
"""

from django.contrib import admin
from .models import Email


@admin.register(Email)
class EmailAdmin(admin.ModelAdmin):
    """Admin interface for Email model"""
    list_display = [
        'subject', 
        'sender', 
        'classification_result', 
        'confidence_score', 
        'created_at'
    ]
    
    list_filter = [
        'classification_result',
        'confidence_score',
        'created_at',
        'processing_status'
    ]
    
    search_fields = [
        'subject',
        'content', 
        'sender',
        'reasoning'
    ]
    
    readonly_fields = [
        'created_at',
        'updated_at',
        'classified_at'
    ]
    
    fieldsets = (
        ('Informações do Email', {
            'fields': ('subject', 'content', 'sender')
        }),
        ('Classificação', {
            'fields': (
                'classification_result', 
                'confidence_score', 
                'reasoning',
                'ai_model_used',
                'processing_status'
            )
        }),
        ('Metadados', {
            'fields': (
                'processing_time_seconds',
                'suggested_response',
                'created_at',
                'classified_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        })
    )
    
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
