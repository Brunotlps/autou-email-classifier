from django.db import models
from django.contrib.auth.models import User


class Email(models.Model):
    """
        Model para armazenar emails enviados pelos usuários. / Model to store emails sent by users.
    """


    # Choices para tipos de arquivo. / Choices for file types.
    FILE_TYPE_CHOICES = [
        ('text', 'Texto'),
        ('txt', 'Arquivo de Texto'),
        ('pdf', 'Arquivo PDF'),
    ]
    

    content = models.TextField(
        verbose_name="Conteúdo do Email",
        help_text="Texto completo do email enviado pelo usuário."
    )


    file_type = models.CharField(
        max_length=10,
        choices=FILE_TYPE_CHOICES,
        default='text',
        verbose_name="Tipo de Arquivo",
        help_text="Formato do arquivo associado ao email."
    )


    original_filename = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Nome do Arquivo Original",
        help_text="Nome do arquivo original (se enviado via upload)."
    )


    # Campos de auditoria. / Audit fields.
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data de Upload",
        help_text="Data e hora em que o email foi enviado."
    )


    processed_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Data de Processamento",
        help_text="Data e hora em que o email foi processado."
    )

    # Para futuras funcionalidades. / For future features.
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='emails_sent',
        verbose_name="Usuário",
        help_text="Usuário que enviou o email."
    )


    class Meta:
        """
            Metadados do modelo Email. / Metadata for the Email model.
        """
        

        verbose_name = "Email"
        verbose_name_plural = "Emails"
        ordering = ['-uploaded_at'] 
     

    def __str__(self):
        """
            Representação em string do modelo Email. / String representation of the Email model.
        """


        return f"Email {self.id} - {self.file_type} - {self.uploaded_at.strftime('%d/%m/%Y %H:%M')}"


    @property
    def is_processed(self):
        """
            Verifica se o email foi processado. / Checks if the email has been processed.
        """


        return self.processed_at is not None
    

    @property
    def content_preview(self):
        """
            Retorna uma prévia do conteúdo do email (primeiros 100 caracteres). / Returns a preview of the email content (first 100 characters).
        """


        return self.content[:100] + "..." if len(self.content) > 100 else self.content