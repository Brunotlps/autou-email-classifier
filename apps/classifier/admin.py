from django.contrib import admin
from django.utils.html import format_html
from .models import Classification



@admin.register(Classification)
class ClassificationAdmin(admin.ModelAdmin):
    """
        Configuração do Django Admin para o modelo Classification. / Django Admin configuration for the Classification model
    """


    #  Campos exibidos na lista de classificações / Fields displayed in the classification list
    list_display = [
        'id',
        'email_preview_admin',
        'get_category_display_admin',
        'get_status_display_admin',
        'confidence_badge',
        'processing_time_display',
        'created_at_short',
        'ai_model_used',
    ]


    # Filtros laterais / Side filters
    list_filter = [
        'classification_result',
        'processing_status',
        'ai_model_used',
        'created_at',
        'classified_at',
        'confidence_score',
    ]


    # Campos pesquisáveis / Searchable fields
    search_fields = [
        'email__content',
        'suggested_response',
        'ai_model_used',
        'error_message',
    ]


    # Campos não editáveis / Non-editable fields
    readonly_fields = [
        'created_at',
        'classified_at',
        'confidence_percentage',
        'processing_duration_display',
        'email_content_preview',
    ]


    # Organização dos campos no formulário / Organization of fields in the form
    fieldsets = (
        ('Email Associado', {
            'fields': ('email', 'email_content_preview')
        }),
        ('Resultado da Classificação', {
            'fields': (
                'classification_result',
                'confidence_score',
                'confidence_percentage',
                'suggested_response'
            )
        }),
        ('Processamento', {
            'fields': (
                'processing_status',
                'ai_model_used',
                'processing_time_seconds',
                'processing_duration_display'
            )
        }),
        ('Auditoria', {
            'fields': ('created_at', 'classified_at'),
            'classes': ('collapse',)
        }),
        ('Debug/Erro', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
    )


    ordering = ('-created_at',)  # Ordenação padrão / Default ordering
    list_per_page = 25 # Itens por página / Items per page
    list_display_links = ('id', 'email_preview_admin')  # Campos clicáveis / Clickable fields
    date_hierarchy = 'created_at'  # Hierarquia de datas / Date hierarchy


    # Métodos personalizados para o admin / Custom methods for admin
    def email_preview_admin(self, obj):
        """ Exibe uma prévia do conteúdo do email. / Displays a preview of the email content. """
        

        if obj.email:
            return obj.email.content_preview
        return "Email não encontrado"  # Email not found
    email_preview_admin.short_description = 'Email Preview'


    def get_category_display_admin(self, obj):
        """ Exibe a categoria da classificação com formatação. / Displays the classification category with formatting. """
        

        if obj.classification_result == 'productive':
            return format_html(
                '<span style="color: green; font-weight: bold;">✅ {}</span>',
                obj.get_classification_result_display()
            )
        elif obj.classification_result == 'unproductive':
            return format_html(
                '<span style="color: red; font-weight: bold;">❌ {}</span>',
                obj.get_classification_result_display()
            )
        else:
            return format_html(
            '<span style="color: gray;">⏳ Não classificado</span>'
        )
    
    get_category_display_admin.short_description = 'Categoria'


    def get_status_display_admin(self, obj):
        """ Exibe o status do processamento / Displays the processing status """


        status_colors = {
            'pending': ('⏳', 'orange'),
            'processing': ('🔄', 'blue'),
            'completed': ('✅', 'green'),
            'failed': ('❌', 'red'),
        }
        icon, color = status_colors.get(obj.processing_status, ('❓', 'gray'))
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {}</span>',
            color,
            icon,
            obj.get_processing_status_display()
        )
    
    get_status_display_admin.short_description = 'Status'


    def confidence_badge(self, obj):
        """ Exibe o score de confiança com um badge colorido. / Displays the confidence score with a colored badge. """


        if obj.confidence_score is None:
            return format_html(
                '<span style="color: gray;">N/A</span>'
            )
        
        percentage = obj.confidence_percentage  # Este já retorna 87.0 (float)
        
        if percentage >= 80:
            color = 'green'
        elif percentage >= 60:
            color = 'orange'
        else:
            color = 'red'
    
        # Usar % em vez de {:.1f}% para evitar conflito
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 3px; font-weight: bold;">{}%</span>',
            color,
            percentage  # ← Sem formatação adicional, só concatenar %
        )
    
    confidence_badge.short_description = 'Confiança'


    def processing_time_display(self, obj):
        """Tempo de processamento formatado / Formatted processing time"""


        return obj.processing_duration_display
    
    processing_time_display.short_description = 'Tempo Proc.'
    
    def created_at_short(self, obj):
        """Data de criação resumida / Short creation date"""
        
        
        return obj.created_at.strftime('%d/%m/%Y %H:%M')
    
    created_at_short.short_description = 'Criado em'
    
    def email_content_preview(self, obj):
        """Preview do conteúdo do email (readonly) / Email content preview (readonly)"""
        
        
        if obj.email:
            return obj.email.content[:200] + "..." if len(obj.email.content) > 200 else obj.email.content
        return "N/A"
    
    email_content_preview.short_description = 'Conteúdo do Email'
    
    # Actions customizadas / Custom actions
    actions = ['reprocess_classifications', 'mark_as_needs_review']
    
    def reprocess_classifications(self, request, queryset):
        """Ação para reprocessar classificações selecionadas / Action to reprocess selected classifications"""
        
        
        updated = queryset.update(processing_status='pending')
        self.message_user(
            request,
            f'{updated} classificação(ões) marcada(s) para reprocessamento.'
        )
    reprocess_classifications.short_description = "Reprocessar classificações selecionadas"
    
    def mark_as_needs_review(self, request, queryset):
        """Ação para marcar como precisa revisão / Action to mark as needs review"""
        
        
        # Aqui você pode implementar lógica personalizada / Here you can implement custom logic
        count = queryset.count()
        self.message_user(
            request,
            f'{count} classificação(ões) marcada(s) para revisão.'
        )
    mark_as_needs_review.short_description = "Marcar para revisão humana"