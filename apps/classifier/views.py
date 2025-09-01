from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view
from rest_framework.response import Response

# Imports para documentação DRF Spectacular
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample, OpenApiResponse
from drf_spectacular.types import OpenApiTypes

from django.db.models import Q
from django.utils import timezone
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Count, Q

from .models import Classification
from .serializers import ClassificationSerializer, EmailClassificationSerializer
from .services import process_classification_async
from .services import classify_email_ai, process_classification_async
from .direct_ai import classify_email_direct

from datetime import datetime, timedelta

import json
import logging

logger = logging.getLogger(__name__)


@extend_schema(tags=["📊 Classificações de Email"])
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

    queryset = Classification.objects.select_related("email").all()
    serializer_class = ClassificationSerializer

    @extend_schema(
        summary="📋 Listar classificações",
        description="Lista todas as classificações com filtros opcionais",
        parameters=[
            OpenApiParameter(
                name="status",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Filtrar por status de processamento",
                enum=["pending", "processing", "completed", "failed"]
            ),
            OpenApiParameter(
                name="category",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Filtrar por categoria de classificação",
                enum=["productive", "unproductive"]
            ),
            OpenApiParameter(
                name="search",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Buscar por termo no conteúdo do email"
            ),
            OpenApiParameter(
                name="model",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Filtrar por modelo de IA utilizado"
            ),
        ],
        responses={
            200: ClassificationSerializer(many=True),
            400: OpenApiResponse(description="Parâmetros inválidos"),
        },
        examples=[
            OpenApiExample(
                "Filtro por status",
                description="Exemplo de filtragem por status",
                parameter_only=True,
                value={"status": "completed", "category": "productive"}
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

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
        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(processing_status=status_filter)

        # Filtros por categoria de classificação / Filters by classification category
        category_filter = self.request.query_params.get("category")
        if category_filter:
            queryset = queryset.filter(classification_result=category_filter)

        # Filtros por termo de busca no conteúdo do email / Filters by search term in email content
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(Q(email__content__icontains=search) | Q(suggested_response__icontains=search))

        # Filtro por modelo de IA / Filter by AI model
        model_filter = self.request.query_params.get("model")
        if model_filter:
            queryset = queryset.filter(ai_model_used=model_filter)

        return queryset.order_by("-created_at")

    @extend_schema(
        summary="➕ Criar classificação",
        description="Cria uma nova classificação e inicia processamento assíncrono automaticamente",
        request=ClassificationSerializer,
        responses={
            201: ClassificationSerializer,
            400: OpenApiResponse(description="Dados inválidos"),
        }
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(
        summary="🔍 Buscar classificação",
        description="Retorna detalhes de uma classificação específica",
        responses={
            200: ClassificationSerializer,
            404: OpenApiResponse(description="Classificação não encontrada"),
        }
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="✏️ Atualizar classificação",
        description="Atualiza completamente uma classificação existente",
        request=ClassificationSerializer,
        responses={
            200: ClassificationSerializer,
            400: OpenApiResponse(description="Dados inválidos"),
            404: OpenApiResponse(description="Classificação não encontrada"),
        }
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(
        summary="📝 Atualizar parcialmente",
        description="Atualiza parcialmente uma classificação existente",
        request=ClassificationSerializer,
        responses={
            200: ClassificationSerializer,
            400: OpenApiResponse(description="Dados inválidos"),
            404: OpenApiResponse(description="Classificação não encontrada"),
        }
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        summary="🗑️ Deletar classificação",
        description="Remove uma classificação do sistema",
        responses={
            204: OpenApiResponse(description="Classificação removida com sucesso"),
            404: OpenApiResponse(description="Classificação não encontrada"),
        }
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    def perform_create(self, serializer):
        """
        Ao criar uma nova classificação, inicia o processamento assíncrono. / When creating a new classification, start asynchronous processing.
        """
        classification = serializer.save()

        if classification.processing_status == "pending":
            process_classification_async(classification.id)

    @extend_schema(
        summary="🔄 Reprocessar classificação",
        description="Reprocessa uma classificação existente com novo ciclo de IA",
        request=None,
        responses={
            200: OpenApiResponse(
                description="Reprocessamento iniciado com sucesso",
                examples=[
                    OpenApiExample(
                        "Sucesso",
                        value={
                            "status": "success",
                            "message": "Reprocessamento iniciado com sucesso",
                            "classification_id": 123,
                            "previous_status": "failed",
                            "current_status": "processing"
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                description="Classificação já sendo processada",
                examples=[
                    OpenApiExample(
                        "Erro - já processando",
                        value={
                            "error": "Classificação já está sendo processada",
                            "current_status": "processing"
                        }
                    )
                ]
            ),
            404: OpenApiResponse(description="Classificação não encontrada"),
            500: OpenApiResponse(description="Erro interno do servidor"),
        }
    )
    @action(detail=True, methods=["post"])
    def reprocess(self, request, pk=None):
        """
        Endpoint customizado para reprocessar uma classificação existente. / Custom endpoint to reprocess an existing classification.

        POST /api/classifier/classifications/{id}/reprocess/

        Marca a classificação como 'processing' e inicia novo processamento. / Marks the classification as 'processing' and starts new processing.
        """
        classification = self.get_object()

        if classification.processing_status == "processing":
            return Response(
                {"error": "Classificação já está sendo processada", "current_status": classification.processing_status},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Salvar status anterior para debug / Save previous status for debugging
        previous_status = classification.processing_status

        # Marcar como processando / Mark as processing
        classification.mark_as_processing()

        # Iniciar processamento / Start processing
        success = process_classification_async(classification.id)

        if success:
            return Response(
                {
                    "status": "success",
                    "message": "Reprocessamento iniciado com sucesso",
                    "classification_id": classification.id,
                    "previous_status": previous_status,
                    "current_status": "processing",
                },
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {"status": "error", "message": "Falha ao iniciar reprocessamento"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @extend_schema(
        summary="📊 Estatísticas gerais",
        description="Retorna estatísticas completas das classificações do sistema",
        responses={
            200: OpenApiResponse(
                description="Estatísticas calculadas com sucesso",
                examples=[
                    OpenApiExample(
                        "Estatísticas completas",
                        value={
                            "total_classifications": 1500,
                            "by_category": {
                                "productive": 900,
                                "unproductive": 600
                            },
                            "by_status": {
                                "pending": 10,
                                "processing": 5,
                                "completed": 1480,
                                "failed": 5
                            },
                            "completion_rate_percent": 98.67
                        }
                    )
                ]
            )
        }
    )
    @action(detail=False, methods=["get"])
    def stats(self, request):
        """
        Endpoint customizado para obter estatísticas de classificações. / Custom endpoint to get classification statistics.

        GET /api/classifier/classifications/stats/

        Retorna contagens por status e categoria. / Returns counts by status and category.
        """
        queryset = self.get_queryset()

        total = queryset.count()
        productive = queryset.filter(classification_result="productive").count()
        unproductive = queryset.filter(classification_result="unproductive").count()
        pending = queryset.filter(processing_status="pending").count()
        processing = queryset.filter(processing_status="processing").count()
        completed = queryset.filter(processing_status="completed").count()
        failed = queryset.filter(processing_status="failed").count()

        completion_rate = (completed / total * 100) if total > 0 else 0

        return Response(
            {
                "total_classifications": total,
                "by_category": {"productive": productive, "unproductive": unproductive},
                "by_status": {"pending": pending, "processing": processing, "completed": completed, "failed": failed},
                "completion_rate_percent": round(completion_rate, 2),
            },
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        summary="🤖 Classificar email com IA",
        description="Classifica um email usando IA e salva resultado no banco de dados",
        request=EmailClassificationSerializer,
        responses={
            200: OpenApiResponse(
                description="Email classificado com sucesso",
                examples=[
                    OpenApiExample(
                        "Classificação produtiva",
                        value={
                            "id": 456,
                            "category": "productive",
                            "confidence": 0.92,
                            "suggested_response": "Resposta profissional sugerida...",
                            "processing_time": 2.45,
                            "ai_enhanced": True,
                            "model_used": "cardiffnlp/twitter-roberta-base-sentiment",
                            "details": {
                                "method": "huggingface_api",
                                "original_label": "LABEL_2",
                                "processing_steps": ["preprocessing", "ai_inference", "post_processing"]
                            }
                        }
                    ),
                    OpenApiExample(
                        "Classificação não produtiva",
                        value={
                            "id": 457,
                            "category": "unproductive",
                            "confidence": 0.88,
                            "suggested_response": "Email promocional ou spam detectado",
                            "processing_time": 1.23,
                            "ai_enhanced": True,
                            "model_used": "cardiffnlp/twitter-roberta-base-sentiment"
                        }
                    )
                ]
            ),
            400: OpenApiResponse(description="Dados de entrada inválidos"),
            500: OpenApiResponse(description="Erro no processamento da IA"),
        },
        examples=[
            OpenApiExample(
                "Email de reunião",
                summary="Exemplo de email produtivo",
                description="Email sobre reunião de trabalho",
                value={
                    "subject": "Reunião urgente - deadline do projeto",
                    "content": "Precisamos agendar uma reunião para discutir o deadline do projeto X. É muito importante definirmos as próximas etapas."
                },
                request_only=True,
            ),
            OpenApiExample(
                "Email promocional",
                summary="Exemplo de email não produtivo", 
                description="Email promocional/spam",
                value={
                    "subject": "🎉 OFERTA IMPERDÍVEL! 70% OFF",
                    "content": "Aproveite nossa super promoção! Desconto de 70% em todos os produtos. Clique aqui rapidamente!"
                },
                request_only=True,
            )
        ]
    )
    @action(detail=False, methods=["post"])
    def classify(self, request):
        """Classificar email usando IA. / Classify email using AI."""
        serializer = EmailClassificationSerializer(data=request.data)

        if serializer.is_valid():
            subject = serializer.validated_data.get("subject", "")
            content = serializer.validated_data.get("content", "")

            try:
                logger.info(f"🔍 Iniciando classificação: subject='{subject}', content='{content[:50]}...'")
                # Usar nova função com IA / Use new function with AI
                result = classify_email_ai(subject, content)
                logger.info(f"✅ IA retornou: {result['category']} ({result['confidence']:.2f})")

                from apps.emails.models import Email

                email_obj, created = Email.objects.get_or_create(
                    subject=subject,
                    content=content,
                    defaults={"sender_email": "test@example.com", "received_at": timezone.now()},
                )

                # Criar registro no banco de dados / Create record in database
                logger.info("💾 Tentando salvar no banco...")
                classification = Classification.objects.create(
                    email=email_obj,
                    classification_result=result["category"],
                    confidence_score=result["confidence"],
                    suggested_response=result["suggested_response"],
                    ai_model_used=result["model_used"],
                    processing_status="completed",
                    processing_time_seconds=result["processing_time"],
                    classified_at=timezone.now(),
                )
                logger.info(f"✅ Salvo com ID: {classification.id}")

                response_data = {
                    "id": classification.id,
                    "category": result["category"],
                    "confidence": result["confidence"],
                    "suggested_response": result["suggested_response"],
                    "processing_time": result["processing_time"],
                    "ai_enhanced": True,
                    "model_used": result["model_used"],
                    "details": result["ai_details"],
                }

                return Response(response_data, status=status.HTTP_200_OK)

            except Exception as e:
                import traceback

                error_details = traceback.format_exc()
                logger.error(f"❌ Erro na classificação: {str(e)}")
                logger.error(f"📋 Stack trace: {error_details}")

                return Response(
                    {"error": f"Erro específico: {str(e)}", "details": error_details if True else None},  # Debug mode
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        logger.error(f"❌ Serializer inválido: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="⚡ Classificação assíncrona",
        description="Classificação assíncrona de email com processamento em background",
        request=EmailClassificationSerializer,
        responses={
            200: OpenApiResponse(
                description="Processamento assíncrono iniciado",
                examples=[
                    OpenApiExample(
                        "Processamento completo",
                        value={
                            "status": "completed",
                            "classification": "productive",
                            "confidence": 0.89,
                            "suggested_response": "Resposta sugerida...",
                            "ai_enhanced": True,
                            "processing_details": {
                                "method": "async_processing",
                                "queue_time": 0.5,
                                "processing_time": 3.2
                            }
                        }
                    )
                ]
            ),
            400: OpenApiResponse(description="Dados inválidos"),
        }
    )
    @action(detail=False, methods=["post"])
    def classify_async(self, request):
        """Classificação assíncrona com IA. / Asynchronous classification with AI."""
        serializer = EmailClassificationSerializer(data=request.data)

        if serializer.is_valid():
            # Processar diretamente (sem Celery por enquanto) / Process directly (without Celery for now)
            result = process_classification_async(serializer.validated_data)

            if result["success"]:
                return Response(
                    {
                        "status": "completed",
                        "classification": result["classification"],
                        "confidence": result["confidence"],
                        "suggested_response": result["suggested_response"],
                        "ai_enhanced": True,
                        "processing_details": result["processing_details"],
                    }
                )
            else:
                return Response(
                    {
                        "status": "completed_with_fallback",
                        "classification": result["classification"],
                        "confidence": result["confidence"],
                        "processing_details": result["processing_details"],
                    }
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="🧪 Teste da IA",
        description="Endpoint de teste para verificar funcionamento da IA sem salvar dados",
        request=EmailClassificationSerializer,
        responses={
            200: OpenApiResponse(
                description="Teste da IA executado com sucesso",
                examples=[
                    OpenApiExample(
                        "IA funcionando",
                        value={
                            "test_mode": True,
                            "category": "productive",
                            "confidence": 0.85,
                            "suggested_response": "Resposta de teste...",
                            "processing_time": 1.89,
                            "model_used": "cardiffnlp/twitter-roberta-base-sentiment",
                            "ai_details": {
                                "api_status": "success",
                                "model_health": "ok"
                            },
                            "message": "✅ IA funcionando perfeitamente!"
                        }
                    )
                ]
            ),
            400: OpenApiResponse(description="Content é obrigatório"),
            500: OpenApiResponse(description="Erro no teste da IA"),
        }
    )
    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def test_ai(self, request):
        """Endpoint de teste da IA sem banco de dados. / AI test endpoint without database."""
        try:
            data = request.data
            subject = data.get("subject", "")
            content = data.get("content", "")

            if not content:
                return Response({"error": "Content é obrigatório"}, status=status.HTTP_400_BAD_REQUEST)

            # Testar IA diretamente / Test AI directly
            result = classify_email_ai(subject, content)

            return Response(
                {
                    "test_mode": True,
                    "category": result["category"],
                    "confidence": result["confidence"],
                    "suggested_response": result["suggested_response"],
                    "processing_time": result["processing_time"],
                    "model_used": result["model_used"],
                    "ai_details": result.get("ai_details", {}),
                    "message": "✅ IA funcionando perfeitamente!",
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.error(f"Erro no teste IA: {str(e)}")
            return Response(
                {"test_mode": True, "error": str(e), "message": "❌ Erro no teste da IA"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @extend_schema(
        summary="🚫 Classificar sem salvar",
        description="Classifica email usando IA mas não salva resultado no banco de dados",
        request=EmailClassificationSerializer,
        responses={
            200: OpenApiResponse(
                description="Classificação realizada sem persistência",
                examples=[
                    OpenApiExample(
                        "Classificação sem salvar",
                        value={
                            "id": None,
                            "category": "productive",
                            "confidence": 0.91,
                            "suggested_response": "Email sobre trabalho...",
                            "processing_time": 2.1,
                            "ai_enhanced": True,
                            "model_used": "cardiffnlp/twitter-roberta-base-sentiment",
                            "details": {
                                "method": "ai_only"
                            },
                            "saved_to_db": False
                        }
                    )
                ]
            ),
            400: OpenApiResponse(description="Dados inválidos"),
            500: OpenApiResponse(description="Erro na IA"),
        }
    )
    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def classify_no_db(self, request):
        """Classificação sem salvar no banco de dados. / Classification without saving to database."""
        serializer = EmailClassificationSerializer(data=request.data)

        if serializer.is_valid():
            subject = serializer.validated_data.get("subject", "")
            content = serializer.validated_data.get("content", "")

            try:
                # Usar IA apenas / Use AI only
                result = classify_email_ai(subject, content)

                # Retornar resultado SEM salvar no banco / Return result WITHOUT saving to database
                response_data = {
                    "id": None,  # Sem ID pois não foi salvo / No ID since not saved
                    "category": result["category"],
                    "confidence": result["confidence"],
                    "suggested_response": result["suggested_response"],
                    "processing_time": result["processing_time"],
                    "ai_enhanced": True,
                    "model_used": result["model_used"],
                    "details": result["ai_details"],
                    "saved_to_db": False,
                }

                return Response(response_data, status=status.HTTP_200_OK)

            except Exception as e:
                return Response({"error": f"Erro na IA: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="📤 Upload e Classificar (AJAX)",
        description="Endpoint de compatibilidade para upload via AJAX",
        request=EmailClassificationSerializer,
        responses={200: ClassificationSerializer}
    )
    @action(detail=False, methods=['post'])
    def upload_ajax(self, request):
        """Endpoint de compatibilidade para upload via AJAX"""
        try:
            serializer = EmailClassificationSerializer(data=request.data)
            if serializer.is_valid():
                return self.classify(request)
            else:
                return Response(
                    {'error': 'Dados inválidos', 'details': serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            logger.error(f'Erro no upload_ajax: {str(e)}')
            return Response(
                {'error': 'Erro interno no servidor'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="📝 Formulário de Upload (GET)",
        description="Retorna formulário para upload de emails"
    )
    @action(detail=False, methods=['get'])
    def upload_ajax_form(self, request):
        """Retorna formulário para upload"""
        return Response({
            'message': 'Use POST com subject e content para classificar emails',
            'example': {
                'subject': 'Assunto do email',
                'content': 'Conteúdo do email aqui'
            }
        })



    @extend_schema(
        summary="📤 Upload AJAX Direto (FUNCIONAL)",
        description="Endpoint direto funcional baseado no ai_standalone",
        request=EmailClassificationSerializer,
        responses={200: OpenApiResponse(description="Classificação realizada")}
    )
    @action(detail=False, methods=['post'], url_path='upload-ajax-direct')
    def upload_ajax_direct(self, request):
        """Endpoint direto funcional baseado no ai_standalone"""
        try:
            data = request.data
            subject = data.get('subject', '')
            content = data.get('content', '')
            
            if not content:
                return Response({
                    'success': False,
                    'error': 'Content é obrigatório'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Usar classificação direta funcional
            result = classify_email_direct(subject, content)
            
            if result['success']:
                # Salvar no banco se a classificação foi bem-sucedida
                try:
                    from apps.emails.models import Email
                    
                    email_obj, created = Email.objects.get_or_create(
                        subject=subject,
                        content=content,
                        defaults={
                            "sender_email": "system@autoU.com",
                            "received_at": timezone.now()
                        }
                    )
                    
                    classification = Classification.objects.create(
                        email=email_obj,
                        classification_result=result['category'],
                        confidence_score=result['confidence'],
                        suggested_response=result['suggested_response'],
                        ai_model_used=result['model_version'],
                        processing_status="completed",
                        processing_time_seconds=float(result['processing_time'].replace('s', '')),
                        classified_at=timezone.now()
                    )
                    
                    return Response({
                        'success': True,
                        'id': classification.id,
                        'category': result['category'],
                        'confidence': result['confidence'],
                        'suggested_response': result['suggested_response'],
                        'processing_time': result['processing_time'],
                        'model_used': result['model_version'],
                        'message': result['message']
                    }, status=status.HTTP_200_OK)
                    
                except Exception as db_error:
                    logger.error(f'Erro ao salvar: {str(db_error)}')
                    # Retornar resultado mesmo se não conseguir salvar
                    return Response({
                        'success': True,
                        'id': None,
                        'category': result['category'],
                        'confidence': result['confidence'],
                        'suggested_response': result['suggested_response'],
                        'processing_time': result['processing_time'],
                        'model_used': result['model_version'],
                        'message': result['message'] + ' (não salvo no DB)',
                        'db_error': str(db_error)
                    }, status=status.HTTP_200_OK)
            else:
                return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            logger.error(f'Erro no upload_ajax_direct: {str(e)}')
            return Response({
                'success': False,
                'error': f'Erro interno: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# === DASHBOARD VIEWS SEPARADAS / SEPARATE DASHBOARD VIEWS ===
@extend_schema(
    tags=["📈 Dashboard"],
    summary="📊 Dados completos do dashboard",
    description="Retorna todos os dados necessários para renderizar o dashboard completo",
    responses={
        200: OpenApiResponse(
            description="Dados do dashboard carregados com sucesso",
            examples=[
                OpenApiExample(
                    "Dashboard completo",
                    value={
                        "stats": {
                            "total_emails": 1500,
                            "productive_emails": 900,
                            "unproductive_emails": 600,
                            "neutral_emails": 0
                        },
                        "timeline_labels": ["01/09", "02/09", "03/09", "04/09", "05/09"],
                        "timeline_data": [45, 52, 38, 67, 43],
                        "confidence_distribution": [12, 45, 89, 123, 67],
                        "recent_emails": [
                            {
                                "id": 123,
                                "subject": "Reunião importante",
                                "category": "productive",
                                "confidence": 0.92,
                                "created_at": "01/09/2025 14:30"
                            }
                        ],
                        "ai_stats": {
                            "cache_hit_rate": 85.5,
                            "error_rate": 2.1,
                            "fallback_rate": 12.4,
                            "api_calls": 1450,
                            "cache_hits": 1240,
                            "errors": 30,
                            "fallback_uses": 180
                        },
                        "system_status": "success",
                        "last_updated": "2025-09-01T14:30:00.000Z"
                    }
                )
            ]
        ),
        500: OpenApiResponse(description="Erro interno do servidor")
    }
)
@api_view(["GET"])
def dashboard_data_api(request):
    """
    API endpoint específico para dados do dashboard.
    Dedicated API endpoint for dashboard data.
    """
    try:
        # Funções auxiliares placeholder - implementar conforme necessário
        def _get_dashboard_stats():
            return {
                "total_emails": Classification.objects.count(),
                "productive_emails": Classification.objects.filter(classification_result="productive").count(),
                "unproductive_emails": Classification.objects.filter(classification_result="unproductive").count(),
                "neutral_emails": 0
            }

        def _get_timeline_data():
            return {
                "labels": ["01/09", "02/09", "03/09", "04/09", "05/09"],
                "data": [45, 52, 38, 67, 43]
            }

        def _get_confidence_distribution():
            return [12, 45, 89, 123, 67]

        def _get_recent_classifications():
            return Classification.objects.select_related("email").order_by("-created_at")[:10]

        def _serialize_recent_classifications(classifications):
            return [
                {
                    "id": c.id,
                    "subject": c.email.subject if c.email else "Sem assunto",
                    "category": c.classification_result,
                    "confidence": c.confidence_score,
                    "created_at": c.created_at.strftime("%d/%m/%Y %H:%M")
                }
                for c in classifications
            ]

        def _get_ai_service_stats():
            return {
                "cache_hit_rate": 85.5,
                "error_rate": 2.1,
                "fallback_rate": 12.4,
                "api_calls": 1450,
                "cache_hits": 1240,
                "errors": 30,
                "fallback_uses": 180
            }

        def _get_system_status():
            return "success"

        data = {
            "stats": _get_dashboard_stats(),
            "timeline_labels": _get_timeline_data()["labels"],
            "timeline_data": _get_timeline_data()["data"],
            "confidence_distribution": _get_confidence_distribution(),
            "recent_emails": _serialize_recent_classifications(_get_recent_classifications()),
            "ai_stats": _get_ai_service_stats(),
            "system_status": _get_system_status(),
            "last_updated": timezone.now().isoformat(),
        }

        return Response(data)

    except Exception as e:
        logger.error(f"Erro no endpoint de dados do dashboard: {e}")
        return Response({"error": "Erro interno do servidor", "message": str(e)}, status=500)


@extend_schema(
    tags=["📈 Dashboard"],
    summary="📈 Estatísticas básicas",
    description="Retorna estatísticas básicas para o dashboard",
    responses={
        200: OpenApiResponse(
            description="Estatísticas carregadas com sucesso",
            examples=[
                OpenApiExample(
                    "Estatísticas básicas",
                    value={
                        "total": 1500,
                        "productive": 900,
                        "unproductive": 600,
                        "completion_rate": 98.67
                    }
                )
            ]
        )
    }
)
@api_view(["GET"])
def dashboard_stats_api(request):
    """
    API endpoint para estatísticas básicas do dashboard.
    Basic dashboard statistics API endpoint.
    """
    try:
        total = Classification.objects.count()
        productive = Classification.objects.filter(classification_result="productive").count()
        unproductive = Classification.objects.filter(classification_result="unproductive").count()
        completed = Classification.objects.filter(processing_status="completed").count()
        
        completion_rate = (completed / total * 100) if total > 0 else 0

        data = {
            "total": total,
            "productive": productive,
            "unproductive": unproductive,
            "completion_rate": round(completion_rate, 2)
        }

        return Response(data)

    except Exception as e:
        logger.error(f"Erro no endpoint de estatísticas: {e}")
        return Response({"error": "Erro interno do servidor", "message": str(e)}, status=500)