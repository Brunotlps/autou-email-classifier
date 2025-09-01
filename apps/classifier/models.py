"""
Models for AutoU Email Classifier - VERSÃO FINAL CORRIGIDA
"""

from django.db import models
from django.utils import timezone


class Email(models.Model):
    """
    Modelo unificado para emails com classificação integrada
    """
    # Campos básicos do email
    subject = models.CharField(max_length=500, default='Sem assunto')
    content = models.TextField()
    sender = models.EmailField(default='unknown@example.com')
    sender_email = models.EmailField(null=True, blank=True)  # Campo adicional para compatibilidade
    
    # Classificação integrada
    classification_result = models.CharField(
        max_length=20,
        choices=[
            ('productive', 'Produtivo'),
            ('unproductive', 'Improdutivo'),
            ('neutral', 'Neutro'),
        ],
        null=True,
        blank=True
    )
    confidence_score = models.FloatField(null=True, blank=True)
    reasoning = models.TextField(null=True, blank=True)
    
    # Metadados da classificação
    ai_model_used = models.CharField(max_length=100, default='huggingface-api')
    model_used = models.CharField(max_length=100, default='huggingface-api')
    processing_time_seconds = models.FloatField(default=0.0)
    processing_time = models.FloatField(default=0.0)
    processing_status = models.CharField(max_length=20, default='completed')
    suggested_response = models.TextField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    classified_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'emails'  # FORÇAR NOME DA TABELA
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['classification_result']),
            models.Index(fields=['created_at']),
            models.Index(fields=['confidence_score']),
        ]
    
    def __str__(self):
        return f"Email de {self.sender}: {self.subject[:50]}..."
    
    def save(self, *args, **kwargs):
        # Auto-definir classified_at quando classification_result é definido
        if self.classification_result and not self.classified_at:
            self.classified_at = timezone.now()
        
        # Sincronizar campos de compatibilidade
        if self.sender and not self.sender_email:
            self.sender_email = self.sender
        if self.sender_email and not self.sender:
            self.sender = self.sender_email
            
        super().save(*args, **kwargs)


# Alias para compatibilidade (proxy model)
class Classification(Email):
    """
    Proxy model para manter compatibilidade com código existente
    """
    class Meta:
        proxy = True
        
    @property
    def email(self):
        """Retorna self como se fosse o email relacionado"""
        return self
