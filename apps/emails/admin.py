from django.contrib import admin
from .models import Email


@admin.register(Email)
class EmailAdmin(admin.ModelAdmin):
    """
        Configuração do admin para o modelo Email. / Admin configuration for the Email model.
    """


    # Campos exibidos na lista de emails. / Fields displayed in the email list.
    list_display = [
        'id',
        'content_preview_admin',
        'file_type', 
        'get_processing_status',  
        'uploaded_at',
        'user'
    ]

    # Filtros laterais. / Side filters.
    list_filter = [
        'file_type',  
        'uploaded_at', 
        'processed_at', 
        'user'
    ]


    # Campos de busca. / Search fields.
    search_fields = [
        'content',
        'original_filename',
        'user__username',
    ]

    
    # Campos não editáveis. / Read-only fields.
    readonly_fields = [
        'content',
        'uploaded_at',
        'content_preview',
    ]


    # Organização dos campos no formulário de edição. / Field organization in the edit form.
    fieldsets = (
        ('Conteúdo do Email', {
            'fields': ('content', 'content_preview')
        }),
        ('Arquivo', {
            'fields': ('file_type', 'original_filename')
        }),
        ('Auditoria', {
            'fields': ('uploaded_at', 'processed_at', 'is_processed')
        }),
        ('Usuário', {
            'fields': ('user',),
            'classes': ('collapse',)  # Seção colapsável
        }),
    )


    ordering = ['-uploaded_at']  # Ordenação padrão: mais recente primeiro. / Default ordering: most recent first.


    items_per_page = 20  # Itens por página. / Items per page.


    def content_preview_admin(self, obj):
        """
            Exibe uma prévia do conteúdo no admin. / Displays a content preview in the admin.
        """
        
        
        return obj.content_preview
    content_preview_admin.short_description = "Prévia do Conteúdo"


    def get_processing_status(self, obj):
        """
            Status de processamento / Processing status
        """


        return "✅ Processado" if obj.is_processed else "⏳ Pendente"
    get_processing_status.short_description = "Status"
