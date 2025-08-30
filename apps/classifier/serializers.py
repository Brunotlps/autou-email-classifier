"""
    Serializers para as classes de classificação de email. / Serializers for email classification classes.
    Conversão entre instâncias de modelos e representações JSON. / Conversion between model instances and JSON representations.
"""

from rest_framework import serializers
from .models import Classification
from apps.emails.models import Email


class ClassificationSerializer(serializers.ModelSerializer):


    # Campos calculados / Computed fields
    confidence_percentage = serializers.ReadOnlyField()
    processing_duration_display = serializers.ReadOnlyField()
    is_completed = serializers.ReadOnlyField()
    is_pending = serializers.ReadOnlyField()


    email_content_preview = serializers.CharField(
        source='email.content_preview',
        read_only=True
    )


    email_file_type = serializers.CharField(
        source='email.file_type',
        read_only=True
    )

    
    class Meta:


        model = Classification
        fields = [
            'id',
            'email',
            'email_content_preview',     
            'email_file_type',           
            'classification_result',
            'confidence_score',
            'confidence_percentage',
            'suggested_response',
            'processing_status',
            'processing_duration_display',
            'is_completed',
            'is_pending',
            'ai_model_used',
            'created_at',
            'classified_at'
        ]
        read_only_fields = [
            'id',
            'created_at',
            'classified_at',
            'classification_result',
            'confidence_score',
            'suggested_response',
            'ai_model_used'
        ]


class EmailClassificationSerializer(serializers.Serializer):
    """
    Serializer para classificação de emails via API. / Serializer for email classification via API.
    Usado nos endpoints /classify/ e /classify_async/ Used in the /classify/ and /classify_async/ endpoints.
    """
    
    subject = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
        help_text="Assunto do email"
    )
    
    content = serializers.CharField(
        max_length=10000,
        required=True,
        allow_blank=False,
        help_text="Conteúdo do email para classificação"
    )
    
    def validate_content(self, value):
        """Validação customizada do conteúdo."""
        if len(value.strip()) < 10:
            raise serializers.ValidationError(
                "Conteúdo deve ter pelo menos 10 caracteres"
            )
        return value.strip()
    
    def validate(self, data):
        """Validação geral dos dados."""
        subject = data.get('subject', '').strip()
        content = data.get('content', '').strip()
        
        # Verificar se há conteúdo suficiente para análise / Check for sufficient content for analysis
        total_text = f"{subject} {content}".strip()
        if len(total_text) < 15:
            raise serializers.ValidationError(
                "Conteúdo total (assunto + texto) muito curto para análise"
            )
        
        return data