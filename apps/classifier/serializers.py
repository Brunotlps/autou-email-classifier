"""Serializers para o app de classificação - CORRIGIDO"""

from rest_framework import serializers
from .models import Classification
from apps.emails.models import Email
from drf_spectacular.utils import extend_schema_field


class ClassificationSerializer(serializers.ModelSerializer):
    """Serializer completo para Classification - com type hints"""
    
    email_subject = serializers.CharField(source='email.subject', read_only=True)
    email_content_preview = serializers.SerializerMethodField()
    confidence_percentage = serializers.SerializerMethodField()
    processing_duration_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Classification
        fields = [
            'id', 'email', 'email_subject', 'email_content_preview',
            'classification_result', 'confidence_score', 'confidence_percentage',
            'suggested_response', 'ai_model_used', 'processing_status',
            'created_at', 'classified_at', 'processing_time_seconds',
            'processing_duration_display', 'error_message'
        ]
        read_only_fields = ['id', 'created_at', 'classified_at']
    
    @extend_schema_field(serializers.CharField)
    def get_email_content_preview(self, obj) -> str:
        """Preview do conteúdo do email"""
        if obj.email and obj.email.content:
            content = obj.email.content
            return content[:100] + "..." if len(content) > 100 else content
        return "Sem conteúdo"
    
    @extend_schema_field(serializers.CharField)
    def get_confidence_percentage(self, obj) -> str:
        """Confiança em porcentagem"""
        return obj.confidence_percentage if hasattr(obj, 'confidence_percentage') else "0.0%"
    
    @extend_schema_field(serializers.CharField)
    def get_processing_duration_display(self, obj) -> str:
        """Duração do processamento formatada"""
        return obj.processing_duration_display if hasattr(obj, 'processing_duration_display') else "N/A"


class EmailClassificationSerializer(serializers.Serializer):
    """Serializer para requests de classificação de email"""
    
    subject = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
        default="",
        help_text="Assunto do email"
    )
    
    content = serializers.CharField(
        required=True,
        allow_blank=False,
        style={'base_template': 'textarea.html', 'rows': 10},
        help_text="Conteúdo completo do email"
    )
    
    def validate_content(self, value):
        """Validação do conteúdo"""
        if not value or not value.strip():
            raise serializers.ValidationError("Conteúdo é obrigatório.")
        return value.strip()


class EmailUploadSerializer(serializers.Serializer):
    """Serializer para upload de emails via formulário"""
    
    subject = serializers.CharField(
        max_length=255,
        required=False,
        default="Email sem assunto"
    )
    content = serializers.CharField(
        style={'base_template': 'textarea.html', 'rows': 10}
    )
    
    def validate_content(self, value):
        """Validação do conteúdo"""
        if not value.strip():
            raise serializers.ValidationError("Conteúdo é obrigatório.")
        return value.strip()
    
    def create(self, validated_data):
        """Criar email a partir dos dados validados"""
        return Email.objects.create(**validated_data)


class ClassificationResultSerializer(serializers.Serializer):
    """Serializer para resultados de classificação"""
    
    email_id = serializers.IntegerField()
    classification = serializers.CharField(max_length=50)
    confidence = serializers.FloatField(min_value=0.0, max_value=1.0)
    processing_time = serializers.CharField(required=False)
    model_version = serializers.CharField(required=False)
