from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Classification(models.Model):
    """
        Model para armazenar resultados de classificação de emails / Model to store email classification results
    """


    # Categoria da classificação / Classification category
    CATEGORY_CHOICES = [
        ('productive', 'Produtivo'),
        ('unproductive', 'Não Produtivo'),
    ]


    # Status da classificação / Classification status
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('processing', 'Processando'),
        ('completed', 'Concluído'),
        ('failed', 'Falhou'),
    ]


    # Relacionamento de um para um com Email / One-to-one relationship with Email
    email = models.OneToOneField(
        'emails.Email', # String reference para evitar importações circulares / String reference to avoid circular imports
        on_delete=models.CASCADE,
        related_name='classification',
        verbose_name='Email',
        help_text='Email associado a esta classificação.',
        blank=True,
        null=True,
    )


    classification_result = models.CharField(
        max_length=15,
        choices=CATEGORY_CHOICES,
        blank=True,
        null=True,
        verbose_name="Categoria",
        help_text="Categoria atribuída ao email após classificação: Produtivo ou  Improdutivo."
    )


    # Pontuação de confiança da IA / AI confidence score
    confidence_score = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        blank=True,
        null=True,
        verbose_name="Pontuação de Confiança",
        help_text="Valor entre 0.0 e 1.0 indicando a confiança da IA"
    )


    # Resposta sugerida pela IA / Suggested response by AI
    suggested_response = models.TextField(
        blank=True,
        null=True,
        verbose_name="Resposta Sugerida",
        help_text="Resposta automática gerada pela IA"
    )


    # Modelo de IA utilizado / AI model used
    ai_model_used = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Modelo de IA",
        help_text="Nome ou versão do modelo de IA utilizado para a classificação."
    )


    # Status do processamento / Processing status
    processing_status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Status',
        help_text='Status atual do processamento da classificação.'
    )


    # Campos de auditoria / Audit fields
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data de Criação",
        help_text="Data e hora em que a classificação foi criada."
    )


    classified_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Data de Classificação",
        help_text="Data e hora em que a classificação foi concluída."
    )


    # Campos para debugging / Fields for debugging
    processing_time_seconds = models.FloatField(
        blank=True,
        null=True,
        verbose_name="Tempo de Processamento (seg)",
        help_text="Tempo que levou para processar em segundos"
    )

    
    error_message = models.TextField(
        blank=True,
        null=True,
        verbose_name="Mensagem de Erro",
        help_text="Mensagem de erro se o processamento falhar"
    )


    class Meta:
        """
            Metadados do modelo Classification / Metadata for the Classification model
        """
        
        
        verbose_name = "Classificação"
        verbose_name_plural = "Classificações"
        ordering = ['-created_at']

        indexes = [
            models.Index(fields=['classification_result']),
            models.Index(fields=['processing_status']),
            models.Index(fields=['created_at']),
        ]
    

    def __str__(self):
        """
            Representação string do objeto Classification / String representation of the Classification object
        """


        if self.email:
            email_preview = self.email.content_preview
        else:
            email_preview = f"Classificação #{self.id}"
            
        classification_display = self.get_classification_result_display() if self.classification_result else "Não classificado"
        return f"Classificação {self.id} - {classification_display} - {email_preview}"


    @property
    def is_completed(self):
        """
            Verifica se a classificação foi concluída / Checks if the classification is completed
        """


        return self.processing_status == 'completed'


    @property
    def is_pending(self):
        """
            Verifica se a classificação está pendente / Checks if the classification is pending
        """


        return self.processing_status == 'pending'
    

    @property
    def confidence_percentage(self):
        """
            Retorna a pontuação de confiança como porcentagem / Returns confidence score as a percentage
        """


        if self.confidence_score is not None:
            return round(self.confidence_score * 100, 2)
        return None


    @property
    def processing_duration_display(self):
        """
            Retorna o tempo de processamento em um formato legível / Returns processing time in a human-readable format
        """


        if self.processing_time_seconds is not None:
            if self.processing_time_seconds < 1:
                return f"{round(self.processing_time_seconds * 1000)}ms"
            else:
                return f"{round(self.processing_time_seconds, 2)}s"
        return "N/A"


    def mark_as_completed(self, classification_result, confidence_score, suggested_response, ai_model_used, processing_time=None):
        """
            Marca a classificação como concluída e define a data de classificação / Marks the classification as completed and sets the classified_at date
        """


        from django.utils import timezone
        self.processing_status = 'completed'
        self.classification_result = classification_result
        self.confidence_score = confidence_score
        self.suggested_response = suggested_response
        self.ai_model_used = ai_model_used
        self.classified_at = timezone.now()
        
        if processing_time:
            self.processing_time_seconds = processing_time
            
        self.save()
        
        # Atualizar o email associado
        if self.email:
            self.email.processed_at = self.classified_at
            self.email.save(update_fields=['processed_at'])
    

    def mark_as_processing(self):
        """
            Marca a classificação como em processamento / Marks the classification as processing
        """


        self.processing_status = 'processing'
        self.save(update_fields=['processing_status'])


    def mark_as_failed(self, error_message):
        """
            Marca a classificação como falhada e define a mensagem de erro / Marks the classification as failed and sets the error message
        """


        self.processing_status = 'failed'
        self.error_message = error_message
        self.save(update_fields=['processing_status', 'error_message'])


    def get_classification_result_display(self):
        """Retorna display name da classificação. / Returns display name of the classification."""
        
        
        display_map = {
            'productive': 'Produtivo',
            'unproductive': 'Não Produtivo'
        }
        return display_map.get(self.classification_result, 'Desconhecido')
    
   