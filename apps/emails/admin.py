from django.contrib import admin
from .models import Email

@admin.register(Email)
class EmailAdmin(admin.ModelAdmin):
    list_display = ['subject', 'sender_email', 'received_at', 'get_content_preview']
    list_filter = ['received_at']
    search_fields = ['subject', 'content', 'sender_email']
    readonly_fields = ['received_at', 'created_at']
    
    def get_content_preview(self, obj):
        """Método para mostrar preview do conteúdo"""
        if obj.content:
            return obj.content[:100] + "..." if len(obj.content) > 100 else obj.content
        return "Sem conteúdo"
    get_content_preview.short_description = 'Preview do Conteúdo'
