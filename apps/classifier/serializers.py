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