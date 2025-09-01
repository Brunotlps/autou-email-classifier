"""Modelos para gerenciamento de emails."""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Email(models.Model):
    """Modelo para armazenar emails enviados pelos usuários."""

    CLASSIFICATION_CHOICES = [
        ('spam', 'Spam'),
        ('legitimate', 'Legítimo'),
        ('unknown', 'Desconhecido'),
        ('phishing', 'Phishing'),
        ('promotional', 'Promocional'),
    ]
    
    FILE_TYPE_CHOICES = [
        ('text', 'Texto'),
        ('txt', 'Arquivo de Texto'),
        ('pdf', 'Arquivo PDF'),
    ]
    
    # Dados básicos do email
    content = models.TextField(
        verbose_name="Conteúdo do Email",
        help_text="Texto completo do email enviado pelo usuário."
    )
    
    subject = models.CharField(
        max_length=255,
        verbose_name="Assunto",
        help_text="Assunto do email.",
        blank=True,
        default="Email sem assunto"
    )
    
    # ✅ CORRIGIDO: Campos de email padronizados
    sender_email = models.EmailField(
        verbose_name="Email do Remetente",
        help_text="Email do remetente.",
        blank=True,
        null=True
    )
    
    recipient_email = models.EmailField(
        verbose_name="Email do Destinatário", 
        help_text="Email do destinatário.",
        blank=True,
        null=True
    )
    
    # Campo sender mantido para compatibilidade
    sender = models.EmailField(
        verbose_name="Remetente (Legacy)",
        help_text="Email do remetente (campo legado).",
        blank=True,
        null=True
    )
    
    # Informações do arquivo
    file_type = models.CharField(
        max_length=10,
        choices=FILE_TYPE_CHOICES,
        default='text',
        verbose_name="Tipo de Arquivo"
    )
    
    original_filename = models.CharField(
        max_length=255,
        verbose_name="Nome do Arquivo Original",
        blank=True,
        null=True
    )
    
    # CLASSIFICAÇÃO LEGADA (mantida para compatibilidade)
    classification = models.CharField(
        max_length=50,
        choices=CLASSIFICATION_CHOICES,
        default='unknown',
        verbose_name="Classificação Legada",
        help_text="Resultado da classificação por IA (campo legado)."
    )
    
    confidence = models.FloatField(
        default=0.0,
        verbose_name="Confiança",
        help_text="Nível de confiança da classificação (0.0 a 1.0)."
    )
    
    model_version = models.CharField(
        max_length=50,
        verbose_name="Versão do Modelo",
        help_text="Versão do modelo de IA usado.",
        blank=True,
        default="v1.0"
    )

    # Relacionamentos
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="emails_sent",
        verbose_name="Usuário"
    )
    
    # Timestamps
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data de Upload"
    )
    
    # ✅ CORRIGIDO: Campo para compatibilidade
    received_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Data de Recebimento",
        default=timezone.now
    )
    
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name="Data de Criação"
    )
    
    processed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Data de Processamento"
    )
    
    class Meta:
        verbose_name = "Email"
        verbose_name_plural = "Emails"
        ordering = ['-created_at']
    
    def __str__(self):
        sender = self.sender_email or self.sender or 'Anônimo'
        return f"Email de {sender}: {self.subject[:50]}..."
    
    @property
    def content_preview(self):
        """Preview do conteúdo para admin"""
        if self.content:
            return self.content[:100] + "..." if len(self.content) > 100 else self.content
        return "Sem conteúdo"
    
    def save(self, *args, **kwargs):
        if self.classification != 'unknown' and not self.processed_at:
            self.processed_at = timezone.now()
        super().save(*args, **kwargs)
