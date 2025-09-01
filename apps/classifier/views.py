from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view
from rest_framework.response import Response

from django.db.models import Q 
from django.utils import timezone
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Count, Q

from .models import Classification
from .serializers import ClassificationSerializer, EmailClassificationSerializer
from .services import process_classification_async
from .services import classify_email_ai, process_classification_async

from datetime import datetime, timedelta

import json
import logging 
logger = logging.getLogger(__name__)



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
    

    @action(detail=False, methods=['post'])
    def classify(self, request):
        """Classificar email usando IA. / Classify email using AI."""
        
        
        serializer = EmailClassificationSerializer(data=request.data)
        
        if serializer.is_valid():
            subject = serializer.validated_data.get('subject', '')
            content = serializer.validated_data.get('content', '')
            
            try:
                logger.info(f"🔍 Iniciando classificação: subject='{subject}', content='{content[:50]}...'")
                # Usar nova função com IA / Use new function with AI
                result = classify_email_ai(subject, content)
                logger.info(f"✅ IA retornou: {result['category']} ({result['confidence']:.2f})")
            
                from apps.emails.models import Email
                email_obj, created = Email.objects.get_or_create(
                    subject=subject,
                    content=content,
                    defaults={
                        'sender_email': 'test@example.com',
                        'received_at': timezone.now()
                    }
                )
                
                # Criar registro no banco de dados / Create record in database
                logger.info("💾 Tentando salvar no banco...")
                classification = Classification.objects.create(
                    email=email_obj,
                    classification_result=result['category'],        
                    confidence_score=result['confidence'],           
                    suggested_response=result['suggested_response'],
                    ai_model_used=result['model_used'],
                    processing_status='completed',
                    processing_time_seconds=result['processing_time'],
                    classified_at=timezone.now()
                )
                logger.info(f"✅ Salvo com ID: {classification.id}")
                
                response_data = {
                    'id': classification.id,
                    'category': result['category'],
                    'confidence': result['confidence'],
                    'suggested_response': result['suggested_response'],
                    'processing_time': result['processing_time'],
                    'ai_enhanced': True,
                    'model_used': result['model_used'],
                    'details': result['ai_details']
                }
                
                return Response(response_data, status=status.HTTP_200_OK)
                
            except Exception as e:
                import traceback
                error_details = traceback.format_exc()
                logger.error(f"❌ Erro na classificação: {str(e)}")
                logger.error(f"📋 Stack trace: {error_details}")

                return Response({
                    'error': f'Erro específico: {str(e)}',
                    'details': error_details if True else None  # Debug mode
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        logger.error(f"❌ Serializer inválido: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def classify_async(self, request):
        """Classificação assíncrona com IA. / Asynchronous classification with AI."""
        
        
        serializer = EmailClassificationSerializer(data=request.data)
        
        if serializer.is_valid():
            # Processar diretamente (sem Celery por enquanto) / Process directly (without Celery for now)
            result = process_classification_async(serializer.validated_data)
            
            if result['success']:
                return Response({
                    'status': 'completed',
                    'classification': result['classification'],
                    'confidence': result['confidence'],
                    'suggested_response': result['suggested_response'],
                    'ai_enhanced': True,
                    'processing_details': result['processing_details']
                })
            else:
                return Response({
                    'status': 'completed_with_fallback',
                    'classification': result['classification'],
                    'confidence': result['confidence'],
                    'processing_details': result['processing_details']
                })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def test_ai(self, request):
        """Endpoint de teste da IA sem banco de dados. / AI test endpoint without database."""


        try:
            data = request.data
            subject = data.get('subject', '')
            content = data.get('content', '')

            if not content:
                return Response({
                    'error': 'Content é obrigatório'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Testar IA diretamente / Test AI directly
            result = classify_email_ai(subject, content)

            return Response({
                'test_mode': True,
                'category': result['category'],
                'confidence': result['confidence'],
                'suggested_response': result['suggested_response'],
                'processing_time': result['processing_time'],
                'model_used': result['model_used'],
                'ai_details': result.get('ai_details', {}),
                'message': '✅ IA funcionando perfeitamente!'
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Erro no teste IA: {str(e)}")
            return Response({
                'test_mode': True,
                'error': str(e),
                'message': '❌ Erro no teste da IA'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def classify_no_db(self, request):
        """Classificação sem salvar no banco de dados. / Classification without saving to database."""


        serializer = EmailClassificationSerializer(data=request.data)

        if serializer.is_valid():
            subject = serializer.validated_data.get('subject', '')
            content = serializer.validated_data.get('content', '')

            try:
                # Usar IA apenas / Use AI only
                result = classify_email_ai(subject, content)

                # Retornar resultado SEM salvar no banco / Return result WITHOUT saving to database
                response_data = {
                    'id': None,  # Sem ID pois não foi salvo / No ID since not saved
                    'category': result['category'],
                    'confidence': result['confidence'],
                    'suggested_response': result['suggested_response'],
                    'processing_time': result['processing_time'],
                    'ai_enhanced': True,
                    'model_used': result['model_used'],
                    'details': result['ai_details'],
                    'saved_to_db': False
                }

                return Response(response_data, status=status.HTTP_200_OK)

            except Exception as e:
                return Response({
                    'error': f'Erro na IA: {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# === DASHBOARD VIEWS SEPARADAS / SEPARATE DASHBOARD VIEWS ===
@api_view(['GET'])
def dashboard_data_api(request):
    """
    API endpoint específico para dados do dashboard.
    Dedicated API endpoint for dashboard data.
    """


    try:
        data = {
            'stats': _get_dashboard_stats(),
            'timeline_labels': _get_timeline_data()['labels'],
            'timeline_data': _get_timeline_data()['data'],
            'confidence_distribution': _get_confidence_distribution(),
            'recent_emails': _serialize_recent_classifications(_get_recent_classifications()),
            'ai_stats': _get_ai_service_stats(),
            'system_status': _get_system_status(),
            'last_updated': timezone.now().isoformat(),
        }
        
        return Response(data)
        
    except Exception as e:
        logger.error(f"Erro no endpoint de dados do dashboard: {e}")
        return Response({
            'error': 'Erro interno do servidor',
            'message': str(e)
        }, status=500)


@api_view(['GET'])
def dashboard_stats_api(request):
    """
    Endpoint específico só para estatísticas básicas.
    Dedicated endpoint for basic statistics only.
    """
    try:
        return Response(_get_dashboard_stats())
    except Exception as e:
        return Response({'error': str(e)}, status=500)


# === FUNÇÕES AUXILIARES / HELPER FUNCTIONS ===
def _get_dashboard_stats():
    """Calcular estatísticas básicas das classificações. / Calculate basic statistics of classifications."""
    
    
    try:
        # Apenas classificações completas / Only completed classifications
        completed_classifications = Classification.objects.filter(processing_status='completed')
        
        total_classifications = completed_classifications.count()
        
        # Contar por categoria / Count by category
        stats = completed_classifications.aggregate(
            productive=Count('id', filter=Q(classification_result='productive')),
            unproductive=Count('id', filter=Q(classification_result='unproductive'))
        )
        
        return {
            'total_emails': total_classifications,
            'productive_emails': stats['productive'] or 0,
            'unproductive_emails': stats['unproductive'] or 0,
            'neutral_emails': 0,  # Placeholder para futuras categorias / Placeholder for future categories
        }
        
    except Exception as e:
        logger.error(f"Erro ao calcular estatísticas: {e}")
        return {
            'total_emails': 0,
            'productive_emails': 0,
            'unproductive_emails': 0,
            'neutral_emails': 0,
        }


def _get_timeline_data(days=7):
    """Obter dados de timeline dos últimos N dias. / Get timeline data for the last N days."""
    
    
    try:
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days-1)
        
        # Criar lista de datas / Create list of dates
        date_list = []
        current_date = start_date
        while current_date <= end_date:
            date_list.append(current_date)
            current_date += timedelta(days=1)
        
        # Buscar contagens por data de classificação / Fetch counts by classification date
        date_counts = {}
        queryset = Classification.objects.filter(
            processing_status='completed',
            classified_at__date__gte=start_date,
            classified_at__date__lte=end_date
        ).extra(
            select={'date': 'DATE(classified_at)'}
        ).values('date').annotate(
            count=Count('id')
        )
        
        for item in queryset:
            date_counts[item['date']] = item['count']
        
        # Preparar dados para Chart.js / Prepare data for Chart.js
        labels = []
        data = []
        
        for date in date_list:
            labels.append(date.strftime('%d/%m'))
            data.append(date_counts.get(date, 0))
        
        return {
            'labels': labels,
            'data': data
        }
        
    except Exception as e:
        logger.error(f"Erro ao obter dados de timeline: {e}")
        return {
            'labels': [],
            'data': []
        }


def _get_confidence_distribution():
    """Calcular distribuição de confiança. / Calculate confidence distribution."""
    
    
    try:
        intervals = [
            (0.0, 0.2),    # 0-20%
            (0.21, 0.4),   # 21-40%
            (0.41, 0.6),   # 41-60%
            (0.61, 0.8),   # 61-80%
            (0.81, 1.0),   # 81-100%
        ]
        
        distribution = []
        
        base_queryset = Classification.objects.filter(
            processing_status='completed',
            confidence_score__isnull=False
        )
        
        for min_conf, max_conf in intervals:
            count = base_queryset.filter(
                confidence_score__gte=min_conf,
                confidence_score__lte=max_conf
            ).count()
            distribution.append(count)
        
        return distribution
        
    except Exception as e:
        logger.error(f"Erro ao calcular distribuição de confiança: {e}")
        return [0, 0, 0, 0, 0]


def _get_recent_classifications(limit=10):
    """Obter classificações recentes. / Get recent classifications."""
    
    
    try:
        return Classification.objects.filter(
            processing_status='completed'
        ).select_related('email').order_by('-classified_at')[:limit]
        
    except Exception as e:
        logger.error(f"Erro ao obter classificações recentes: {e}")
        return []


def _serialize_recent_classifications(classifications):
    """Serializar classificações para JSON. / Serialize classifications to JSON."""
    
    
    try:
        return [
            {
                'id': classification.id,
                'subject': classification.email.subject if classification.email else 'Sem assunto',
                'category': classification.classification_result or 'unknown',
                'confidence': float(classification.confidence_score) if classification.confidence_score else 0,
                'created_at': classification.classified_at.strftime('%d/%m/%Y %H:%M') if classification.classified_at else '',
                'get_category_display': classification.get_classification_result_display() if classification.classification_result else 'N/A'
            }
            for classification in classifications
        ]
    except Exception as e:
        logger.error(f"Erro ao serializar classificações: {e}")
        return []



def _get_ai_service_stats():
    """Obter estatísticas do serviço de IA. / Get AI service statistics."""
    
    
    try:
        try:
            from .ai_service import get_ai_service
            
            ai_service = get_ai_service()
            if hasattr(ai_service, 'get_stats'):
                stats = ai_service.get_stats()
                
                return {
                    'cache_hit_rate': stats.get('cache_hit_rate', 0) * 100,
                    'error_rate': stats.get('error_rate', 0) * 100,
                    'fallback_rate': stats.get('fallback_rate', 0) * 100,
                    'api_calls': stats.get('api_calls', 0),
                    'cache_hits': stats.get('cache_hits', 0),
                    'errors': stats.get('errors', 0),
                    'fallback_uses': stats.get('fallback_uses', 0),
                }
        except ImportError:
            pass
        
        return None
        
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas do AI service: {e}")
        return None


def _get_system_status():
    """Status do sistema baseado nas classificações. / System status based on classifications."""
    
    
    try:
        has_classifications = Classification.objects.filter(processing_status='completed').exists()
        
        if not has_classifications:
            return 'warning'
        
        # Taxa de erro nas últimas 24h / Error rate in the last 24 hours
        last_24h = timezone.now() - timedelta(hours=24)
        
        recent_stats = Classification.objects.filter(
            created_at__gte=last_24h
        ).aggregate(
            total=Count('id'),
            failed=Count('id', filter=Q(processing_status='failed')),
            completed=Count('id', filter=Q(processing_status='completed'))
        )
        
        if recent_stats['total'] > 0:
            error_rate = recent_stats['failed'] / recent_stats['total']
            
            if error_rate > 0.5:
                return 'error'
            
            if error_rate > 0.2:
                return 'warning'
        
        return 'success'
        
    except Exception as e:
        logger.error(f"Erro ao verificar status do sistema: {e}")
        return 'error'