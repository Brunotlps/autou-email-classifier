"""
Views para o app de emails
"""
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Email
from .serializers import EmailSerializer, EmailCreateSerializer, EmailSimpleSerializer
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample, OpenApiResponse
from drf_spectacular.types import OpenApiTypes

@extend_schema(tags=["📧 Emails"])
class EmailViewSet(viewsets.ModelViewSet):
    """ViewSet para operações CRUD de emails"""
    
    queryset = Email.objects.all().order_by('-created_at')
    serializer_class = EmailSerializer
    
    def get_serializer_class(self):
        """Usar serializer apropriado baseado na ação"""
        if self.action == 'create':
            return EmailCreateSerializer
        elif self.action == 'list':
            return EmailSimpleSerializer
        return EmailSerializer
    
    @extend_schema(
        summary="📋 Listar emails",
        description="Lista todos os emails com filtros opcionais",
        parameters=[
            OpenApiParameter(
                name="classification",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Filtrar por classificação",
                enum=["spam", "legitimate", "unknown", "phishing", "promotional"]
            ),
            OpenApiParameter(
                name="search",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Buscar por assunto ou conteúdo"
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    def get_queryset(self):
        """Filtros via query params"""
        queryset = self.queryset
        
        # Filtro por classificação
        classification = self.request.query_params.get('classification')
        if classification:
            queryset = queryset.filter(classification=classification)
        
        # Filtro por busca
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                models.Q(subject__icontains=search) | 
                models.Q(content__icontains=search)
            )
        
        return queryset
    
    @extend_schema(
        summary="➕ Criar email",
        description="Cria um novo email no sistema"
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    
    @extend_schema(
        summary="📊 Estatísticas de emails",
        description="Retorna estatísticas dos emails"
    )
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Estatísticas dos emails"""
        total = self.get_queryset().count()
        by_classification = {}
        
        for choice in Email.CLASSIFICATION_CHOICES:
            key = choice[0]
            count = self.get_queryset().filter(classification=key).count()
            by_classification[key] = count
        
        return Response({
            'total_emails': total,
            'by_classification': by_classification
        })
