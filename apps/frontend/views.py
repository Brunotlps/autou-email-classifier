"""
Frontend Views for AutoU Email Classifier - VERSÃO CORRIGIDA
"""

import json
import logging
import time
import os
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db import connections
from django.core.cache import cache
from django.conf import settings
from django.utils import timezone

# Import models
try:
    from apps.classifier.models import Email
except ImportError as e:
    logging.error(f"Error importing models: {e}")
    class Email:
        objects = None

# Import AI service
try:
    from apps.classifier.ai_service import get_ai_service
except ImportError as e:
    logging.error(f"Error importing AI service: {e}")
    def get_ai_service():
        return None

logger = logging.getLogger(__name__)


def home_view(request):
    """Render home page"""
    context = {
        'description': 'Sistema inteligente de classificação de emails usando IA avançada para identificar emails produtivos e improdutivos.',
        'features': [
            'Classificação automática com IA',
            'Análise de produtividade em tempo real', 
            'Interface intuitiva e responsiva',
            'Resultados precisos e confiáveis',
            'Histórico completo de classificações',
            'Dashboard com estatísticas detalhadas'
        ]
    }
    return render(request, 'base/home.html', context)


def upload_view(request):
    """Render upload page"""
    return render(request, 'classifier/upload.html')


def analyze_content_keywords(content, subject):
    """Fallback content analysis using keywords"""
    content_lower = content.lower()
    subject_lower = subject.lower()
    
    productive_keywords = [
        'reunião', 'meeting', 'projeto', 'project', 'trabalho', 'work', 
        'deadline', 'prazo', 'tarefa', 'task', 'importante', 'urgent',
        'relatório', 'report', 'apresentação', 'presentation', 'cliente',
        'client', 'contrato', 'contract', 'proposta', 'proposal'
    ]
    
    unproductive_keywords = [
        'spam', 'promoção', 'desconto', 'oferta', 'comprar', 'venda',
        'click here', 'free', 'winner', 'prize', 'congratulations',
        'viagra', 'casino', 'lottery', 'investment opportunity'
    ]
    
    productive_score = sum(1 for keyword in productive_keywords 
                         if keyword in content_lower or keyword in subject_lower)
    unproductive_score = sum(1 for keyword in unproductive_keywords 
                           if keyword in content_lower or keyword in subject_lower)
    
    if productive_score > unproductive_score:
        return 'productive'
    elif unproductive_score > productive_score:
        return 'unproductive'
    else:
        return 'neutral'


def generate_suggested_response(classification, subject):
    """Generate suggested response"""
    responses = {
        'productive': f"Obrigado pelo email sobre '{subject}'. Vou revisar e retornar em breve.",
        'unproductive': f"Email sobre '{subject}' foi classificado como não prioritário.",
        'neutral': f"Email sobre '{subject}' recebido e será analisado conforme necessário."
    }
    return responses.get(classification, 'Resposta padrão')


def fallback_classification(content, subject):
    """Fallback classification when AI service is not available"""
    classification = analyze_content_keywords(content, subject)
    return {
        'classification': classification,
        'confidence': 0.6,
        'reasoning': f'Classificação baseada em análise de palavras-chave. Email identificado como {classification}.',
        'model': 'keyword-fallback',
        'processing_time': 0.1
    }


@csrf_exempt
@require_http_methods(["POST"])
def upload_ajax(request):
    """Handle AJAX email classification requests"""
    try:
        data = json.loads(request.body)
        subject = data.get('subject', 'Sem assunto')
        content = data.get('content', '').strip()
        
        logger.info(f"📧 Recebendo classificação: subject='{subject}', content_length={len(content)}")
        
        if not content:
            return JsonResponse({'success': False, 'error': 'Conteúdo do email é obrigatório'})
        
        if Email.objects is None:
            return JsonResponse({'success': False, 'error': 'Modelos não disponíveis'})
        
        # Get AI classification
        ai_service = get_ai_service()
        if ai_service is None:
            result = fallback_classification(content, subject)
        else:
            result = ai_service.classify_email(content, subject)
        
        # Normalize classification
        raw_classification = result.get('classification', 'unknown').lower()
        
        if raw_classification in ['productive', 'legitimate', 'important', 'work', 'business']:
            normalized_classification = 'productive'
        elif raw_classification in ['unproductive', 'spam', 'phishing', 'junk', 'irrelevant']:
            normalized_classification = 'unproductive'
        elif raw_classification in ['neutral', 'moderate', 'uncertain']:
            normalized_classification = 'neutral'
        else:
            normalized_classification = analyze_content_keywords(content, subject)
        
        # Create email with classification
        email = Email.objects.create(
            subject=subject,
            content=content,
            sender='user@upload.com',
            classification_result=normalized_classification,
            confidence_score=result.get('confidence', 0.6),
            reasoning=result.get('reasoning', f'Email classificado como {normalized_classification}'),
            ai_model_used=result.get('model', 'huggingface-api'),
            processing_time_seconds=result.get('processing_time', 0),
            suggested_response=generate_suggested_response(normalized_classification, subject),
            processing_status='completed',
            classified_at=timezone.now()
        )
        
        logger.info(f"✅ Email criado e classificado com ID: {email.id}")
        
        # Generate response
        recommended_responses = {
            'productive': f"✅ RESPONDER COM PRIORIDADE: Este email sobre '{subject}' é importante para sua produtividade.",
            'unproductive': f"❌ IGNORAR OU DELETAR: Este email sobre '{subject}' não contribui para sua produtividade.",
            'neutral': f"⚠️ AVALIAR CONFORME NECESSÁRIO: Este email sobre '{subject}' tem importância moderada."
        }
        
        enhanced_reasoning = result.get('reasoning', '')
        if not enhanced_reasoning:
            if normalized_classification == 'productive':
                enhanced_reasoning = "Este email contém palavras-chave relacionadas a trabalho e projetos importantes."
            elif normalized_classification == 'unproductive':
                enhanced_reasoning = "Este email não apresenta características de produtividade profissional."
            else:
                enhanced_reasoning = "Este email apresenta características mistas de produtividade."
        
        response_data = {
            'success': True,
            'email_id': email.id,
            'subject': subject,
            'classification': normalized_classification,
            'classification_result': normalized_classification,
            'confidence': result.get('confidence', 0.6),
            'confidence_score': result.get('confidence', 0.6),
            'reasoning': enhanced_reasoning,
            'message': enhanced_reasoning,
            'processing_time': f"{result.get('processing_time', 0):.2f}s",
            'model_version': result.get('model', 'AI-HuggingFace'),
            'recommended_response': recommended_responses.get(normalized_classification, 'Sem recomendação disponível'),
            'timestamp': email.created_at.isoformat() if hasattr(email, 'created_at') else None
        }
        
        return JsonResponse(response_data)
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Dados JSON inválidos'})
    except Exception as e:
        logger.error(f"❌ Erro na classificação: {str(e)}")
        return JsonResponse({'success': False, 'error': f'Erro interno: {str(e)}'})


def dashboard_view(request):
    """Dashboard view with email statistics"""
    try:
        from django.db.models import Count, Q
        from datetime import timedelta
        
        if Email.objects is None:
            context = {
                'error': 'Modelos não disponíveis',
                'total_emails': 0,
                'productive_emails': 0,
                'unproductive_emails': 0,
                'neutral_emails': 0,
                'recent_activity': [],
                'classification_distribution': {'productive': 0, 'unproductive': 0, 'neutral': 0},
                'confidence_distribution': {'high': 0, 'medium': 0, 'low': 0},
            }
            return render(request, 'classifier/dashboard.html', context)
        
        # Calculate statistics
        total_emails = Email.objects.count()
        productive_emails = Email.objects.filter(classification_result='productive').count()
        unproductive_emails = Email.objects.filter(classification_result='unproductive').count()
        neutral_emails = Email.objects.filter(classification_result='neutral').count()
        
        # Recent activity (last 7 days)
        seven_days_ago = timezone.now() - timedelta(days=7)
        recent_classifications = Email.objects.filter(
            classified_at__gte=seven_days_ago,
            classification_result__isnull=False
        ).order_by('-classified_at')[:10]
        
        # Classification distribution
        classification_distribution = {
            'productive': productive_emails,
            'unproductive': unproductive_emails,
            'neutral': neutral_emails
        }
        
        # Confidence distribution
        high_confidence = Email.objects.filter(confidence_score__gte=0.8).count()
        medium_confidence = Email.objects.filter(
            confidence_score__gte=0.6, 
            confidence_score__lt=0.8
        ).count()
        low_confidence = Email.objects.filter(
            confidence_score__lt=0.6, 
            confidence_score__isnull=False
        ).count()
        
        confidence_distribution = {
            'high': high_confidence,
            'medium': medium_confidence,
            'low': low_confidence
        }
        
        # Prepare recent activity for template
        recent_activity = []
        for email in recent_classifications:
            recent_activity.append({
                'email_subject': email.subject,
                'classification_result': email.classification_result,
                'confidence_score': email.confidence_score or 0,
                'classified_at': email.classified_at or email.created_at,
                'reasoning': email.reasoning or 'Sem justificativa'
            })
        
        context = {
            'total_emails': total_emails,
            'productive_emails': productive_emails,
            'unproductive_emails': unproductive_emails,
            'neutral_emails': neutral_emails,
            'recent_activity': recent_activity,
            'classification_distribution': classification_distribution,
            'confidence_distribution': confidence_distribution,
            'total_classifications': productive_emails + unproductive_emails + neutral_emails,
            'productivity_rate': round((productive_emails / max(1, productive_emails + unproductive_emails)) * 100, 1) if (productive_emails + unproductive_emails) > 0 else 0
        }
        
        return render(request, 'classifier/dashboard.html', context)
        
    except Exception as e:
        logger.error(f"❌ Erro no dashboard: {str(e)}")
        context = {
            'error': f'Erro ao carregar dados: {str(e)}',
            'total_emails': 0,
            'productive_emails': 0,
            'unproductive_emails': 0,
            'neutral_emails': 0,
            'recent_activity': [],
            'classification_distribution': {'productive': 0, 'unproductive': 0, 'neutral': 0},
            'confidence_distribution': {'high': 0, 'medium': 0, 'low': 0},
        }
        return render(request, 'classifier/dashboard.html', context)


def results_view(request):
    """Results view"""
    context = {'api_endpoint': '/api/classifications/'}
    return render(request, 'classifier/results.html', context)


@csrf_exempt
def api_classifications(request):
    """API endpoint for classifications data"""
    try:
        from django.core.paginator import Paginator
        from django.db.models import Q
        
        if Email.objects is None:
            return JsonResponse({
                'results': [],
                'count': 0,
                'current_page': 1,
                'total_pages': 1,
                'error': 'Modelos não disponíveis'
            })
        
        # Filter parameters
        classification_filter = request.GET.get('classification_result', '')
        search_query = request.GET.get('search', '')
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 10))
        
        # Build query
        queryset = Email.objects.filter(classification_result__isnull=False).order_by('-classified_at')
        
        if classification_filter:
            queryset = queryset.filter(classification_result=classification_filter)
        
        if search_query:
            queryset = queryset.filter(
                Q(subject__icontains=search_query) |
                Q(content__icontains=search_query) |
                Q(reasoning__icontains=search_query)
            )
        
        # Pagination
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)
        
        # Serialize data
        results = []
        for email in page_obj:
            results.append({
                'id': email.id,
                'classification_result': email.classification_result,
                'confidence_score': email.confidence_score or 0,
                'reasoning': email.reasoning,
                'classified_at': email.classified_at.isoformat() if email.classified_at else email.created_at.isoformat(),
                'email': {
                    'id': email.id,
                    'subject': email.subject,
                    'content': email.content,
                    'sender': email.sender
                }
            })
        
        return JsonResponse({
            'results': results,
            'count': paginator.count,
            'current_page': page,
            'total_pages': paginator.num_pages,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous()
        })
        
    except Exception as e:
        logger.error(f"❌ Erro na API de classificações: {str(e)}")
        return JsonResponse({
            'results': [],
            'count': 0,
            'current_page': 1,
            'total_pages': 1,
            'error': str(e)
        })


def health_check(request):
    """Health check endpoint"""
    status = {'status': 'healthy', 'timestamp': time.time(), 'checks': {}}
    
    try:
        db_conn = connections['default']
        db_conn.cursor()
        status['checks']['database'] = 'healthy'
    except Exception as e:
        status['checks']['database'] = f'unhealthy: {str(e)}'
        status['status'] = 'unhealthy'
    
    try:
        cache.set('health_check', 'test', 30)
        cache.get('health_check')
        status['checks']['cache'] = 'healthy'
    except Exception as e:
        status['checks']['cache'] = f'unhealthy: {str(e)}'
        status['status'] = 'unhealthy'
    
    try:
        ai_service = get_ai_service()
        status['checks']['ai_service'] = 'healthy' if ai_service else 'unavailable (using fallback)'
    except Exception as e:
        status['checks']['ai_service'] = f'unhealthy: {str(e)}'
    
    response_status = 200 if status['status'] == 'healthy' else 503
    return JsonResponse(status, status=response_status)


def readiness_check(request):
    """Readiness probe"""
    return JsonResponse({'status': 'ready'})


def liveness_check(request):
    """Liveness probe"""
    return JsonResponse({'status': 'alive'})
