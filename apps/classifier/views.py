from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from django.db.models import Q 

from .models import Classification
from .serializers import ClassificationSerializer
from .services import process_classification_async



class ClassificationViewSet(viewsets.ModelViewSet):
    """
        ViewSet para operações CRUD de classificações de email. / ViewSet for CRUD operations on email classifications.
    
        Endpoints disponíveis: / Available endpoints:
        - GET    /api/classifier/classifications/     → Listar todas / List all
        - POST   /api/classifier/classifications/     → Criar nova / Create new
        - GET    /api/classifier/classifications/{id}/ → Buscar por ID / Retrieve by ID
        - PUT    /api/classifier/classifications/{id}/ → Atualizar completa / Update fully
        - PATCH  /api/classifier/classifications/{id}/ → Atualizar parcial / Update partially
        - DELETE /api/classifier/classifications/{id}/ → Deletar / Delete

        Ações customizadas:
        - POST   /api/classifier/classifications/{id}/reprocess/ → Reprocessar / Reprocess
        - GET    /api/classifier/classifications/stats/         → Estatísticas / Statistics
    """


    queryset = Classification.objects.select_related('email').all()
    serializer_class = ClassificationSerializer


    def get_queryset(self):
        """
            Filtragem avançada via query params. / Advanced filtering via query params.

            Ex:
                - /api/classifier/classifications/?status=pending
                - /api/classifier/classifications/?category=productive
                - /api/classifier/classifications/?search=reunião

        """


        queryset = self.queryset

        # Filtros por status de processamento / Filters by processing status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(processing_status=status_filter)

        
        # Filtros por categoria de classificação / Filters by classification category
        category_filter = self.request.query_params.get('category')
        if category_filter:
            queryset = queryset.filter(classification_result=category_filter)


        # Filtros por termo de busca no conteúdo do email / Filters by search term in email content
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(email__content__icontains=search) |
                Q(suggested_response__icontains=search)
            )

        
        # Filtro por modelo de IA / Filter by AI model
        model_filter = self.request.query_params.get('model')
        if model_filter:
            queryset = queryset.filter(ai_model_used=model_filter)
        
        return queryset.order_by('-created_at')
    

    def perform_create(self, serializer):
        """
            Ao criar uma nova classificação, inicia o processamento assíncrono. / When creating a new classification, start asynchronous processing.
        """


        classification = serializer.save()

        if classification.processing_status == 'pending':
            process_classification_async(classification.id)
        


    @action(detail=True, methods=['post'])
    def reprocess(self, request, pk=None):
        """
            Endpoint customizado para reprocessar uma classificação existente. / Custom endpoint to reprocess an existing classification.
            
            POST /api/classifier/classifications/{id}/reprocess/
        
            Marca a classificação como 'processing' e inicia novo processamento. / Marks the classification as 'processing' and starts new processing.
        """


        classification = self.get_object()


        if classification.processing_status == 'processing':
            return Response({
                'error': 'Classificação já está sendo processada',
                'current_status': classification.processing_status
            }, status=status.HTTP_400_BAD_REQUEST)

        # Salvar status anterior para debug / Save previous status for debugging
        previous_status = classification.processing_status

        # Marcar como processando / Mark as processing
        classification.mark_as_processing()

        # Iniciar processamento / Start processing
        success = process_classification_async(classification.id)
        

        if success:
            return Response({
                'status': 'success',
                'message': 'Reprocessamento iniciado com sucesso',
                'classification_id': classification.id,
                'previous_status': previous_status,
                'current_status': 'processing'
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'status': 'error',
                'message': 'Falha ao iniciar reprocessamento'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
            Endpoint customizado para obter estatísticas de classificações. / Custom endpoint to get classification statistics.

            GET /api/classifier/classifications/stats/

            Retorna contagens por status e categoria. / Returns counts by status and category.
        """


        queryset = self.get_queryset()

        
        total = queryset.count()
        productive = queryset.filter(classification_result='productive').count()
        unproductive = queryset.filter(classification_result='unproductive').count()
        pending = queryset.filter(processing_status='pending').count()
        processing = queryset.filter(processing_status='processing').count()
        completed = queryset.filter(processing_status='completed').count()
        failed = queryset.filter(processing_status='failed').count()


        completion_rate = (completed / total * 100) if total > 0 else 0

        return Response({
            'total_classifications': total,
            'by_category': {
                'productive': productive,
                'unproductive': unproductive
            },
            'by_status': {
                'pending': pending,
                'processing': processing,
                'completed': completed,
                'failed': failed
            },
            'completion_rate_percent': round(completion_rate, 2)
        }, status=status.HTTP_200_OK)
    


