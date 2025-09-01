"""
Serializers para o app de emails - CORRIGIDO
"""
from rest_framework import serializers
from .models import Email
from drf_spectacular.utils import extend_schema_field

class EmailSerializer(serializers.ModelSerializer):
    """Serializer para o modelo Email - campos compatíveis"""
    
    # ✅ CORRIGIDO: Usar campos que existem no modelo
    content_preview = serializers.SerializerMethodField()
    classification_display = serializers.CharField(source='get_classification_display', read_only=True)
    confidence_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = Email
        fields = [
            'id', 'subject', 'content', 'content_preview',
            'sender_email', 'recipient_email', 'sender',  # Campos de email
            'file_type', 'original_filename',  # Informações do arquivo
            'classification', 'classification_display', 'confidence', 'confidence_percentage',  # Classificação legada
            'model_version', 'user',  # Metadados
            'uploaded_at', 'received_at', 'created_at', 'processed_at'  # Timestamps
        ]
        read_only_fields = ['id', 'uploaded_at', 'created_at', 'processed_at']
    
    @extend_schema_field(serializers.CharField)
    def get_content_preview(self, obj):
        """Preview do conteúdo do email"""
        if obj.content:
            return obj.content[:100] + "..." if len(obj.content) > 100 else obj.content
        return "Sem conteúdo"
    
    @extend_schema_field(serializers.CharField)
    def get_confidence_percentage(self, obj):
        """Confiança em porcentagem"""
        if obj.confidence:
            return f"{obj.confidence * 100:.1f}%"
        return "0.0%"


class EmailCreateSerializer(serializers.ModelSerializer):
    """Serializer para criação de emails"""
    
    class Meta:
        model = Email
        fields = ['subject', 'content', 'sender_email', 'recipient_email', 'file_type']
        
    def validate_content(self, value):
        """Validação do conteúdo"""
        if not value or not value.strip():
            raise serializers.ValidationError("Conteúdo é obrigatório.")
        return value.strip()


class EmailSimpleSerializer(serializers.ModelSerializer):
    """Serializer simples para listagens"""
    
    content_preview = serializers.SerializerMethodField()
    
    class Meta:
        model = Email
        fields = ['id', 'subject', 'content_preview', 'sender_email', 'classification', 'confidence', 'created_at']
    
    @extend_schema_field(serializers.CharField)
    def get_content_preview(self, obj):
        """Preview do conteúdo"""
        return obj.content_preview
