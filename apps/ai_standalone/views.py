"""
Views standalone para IA - sem dependência de outros apps
"""
import json
import time
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings

@csrf_exempt
@require_http_methods(["POST"])
def classify_text_direct(request):
    """
    Endpoint direto para classificação de IA
    """
    try:
        # Parse JSON
        data = json.loads(request.body)
        subject = data.get('subject', '')
        content = data.get('content', '')
        
        # Combinar texto
        text = f"{subject} {content}".strip()
        
        if not text:
            return JsonResponse({
                "success": False,
                "error": "Texto vazio"
            }, status=400)
        
        # Obter configurações IA
        ai_settings = getattr(settings, 'AI_SETTINGS', {})
        token = ai_settings.get('HUGGINGFACE_API_TOKEN')
        model = ai_settings.get('CLASSIFICATION_MODEL', 'cardiffnlp/twitter-roberta-base-sentiment-latest')
        
        start_time = time.time()
        
        if token:
            # Tentar IA real
            try:
                result = classify_with_huggingface(text, token, model)
                processing_time = round(time.time() - start_time, 2)
                
                return JsonResponse({
                    "success": True,
                    "text": text[:100] + "..." if len(text) > 100 else text,
                    "classification": result['classification'],
                    "confidence": result['confidence'],
                    "model_version": "ai-huggingface_api",
                    "processing_time": f"{processing_time}s",
                    "message": "Email classificado com IA real!"
                })
                
            except Exception as e:
                print(f"⚠️ Erro IA real: {e}")
                # Fallback para heurística
                pass
        
        # Fallback heurístico
        result = classify_heuristic(text)
        processing_time = round(time.time() - start_time, 2)
        
        return JsonResponse({
            "success": True,
            "text": text[:100] + "..." if len(text) > 100 else text,
            "classification": result['classification'],
            "confidence": result['confidence'],
            "model_version": "heuristic-fallback",
            "processing_time": f"{processing_time}s",
            "message": "Email classificado com heurística (IA indisponível)"
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            "success": False,
            "error": "JSON inválido"
        }, status=400)
    except Exception as e:
        return JsonResponse({
            "success": False,
            "error": f"Erro interno: {str(e)}"
        }, status=500)


def classify_with_huggingface(text, token, model):
    """
    Classificação com Hugging Face API
    """
    url = f"https://api-inference.huggingface.co/models/{model}"
    headers = {"Authorization": f"Bearer {token}"}
    
    payload = {"inputs": text}
    
    response = requests.post(url, headers=headers, json=payload, timeout=10)
    
    if response.status_code == 200:
        result = response.json()
        
        if isinstance(result, list) and len(result) > 0:
            scores = result[0]
            
            # Mapear sentimentos para produtividade
            productive_keywords = ['positive', 'joy', 'optimism', 'trust', 'anticipation']
            unproductive_keywords = ['negative', 'sadness', 'anger', 'fear', 'disgust']
            
            max_score = max(scores, key=lambda x: x['score'])
            label = max_score['label'].lower()
            confidence = max_score['score']
            
            # Determinar classificação
            if any(keyword in label for keyword in productive_keywords):
                classification = 'productive'
            elif any(keyword in label for keyword in unproductive_keywords):
                classification = 'unproductive'
            else:
                # Se neutra, usar heurística do texto
                heuristic = classify_heuristic(text)
                classification = heuristic['classification']
                confidence = min(confidence, 0.6)  # Reduzir confiança para neutros
            
            return {
                'classification': classification,
                'confidence': round(confidence, 3)
            }
    
    raise Exception(f"API error: {response.status_code}")


def classify_heuristic(text):
    """
    Classificação heurística simples
    """
    text_lower = text.lower()
    
    # Palavras-chave produtivas
    productive_keywords = [
        'reunião', 'projeto', 'deadline', 'urgente', 'importante', 'trabalho',
        'tarefa', 'entrega', 'apresentação', 'cliente', 'contrato', 'proposta',
        'desenvolvimento', 'bug', 'sistema', 'produção', 'deploy', 'meeting',
        'project', 'urgent', 'important', 'work', 'task', 'delivery', 'client',
        'contract', 'proposal', 'development', 'production', 'critical'
    ]
    
    # Palavras-chave não produtivas
    unproductive_keywords = [
        'promoção', 'desconto', 'grátis', 'ganhe', 'oferta', 'clique',
        'compre', 'venda', 'marketing', 'spam', 'promocional', 'publicidade',
        'social', 'pessoal', 'fim de semana', 'férias', 'festa', 'birthday',
        'promotion', 'discount', 'free', 'buy', 'sale', 'marketing', 'spam',
        'advertisement', 'social', 'personal', 'weekend', 'vacation', 'party'
    ]
    
    # Contar ocorrências
    productive_count = sum(1 for keyword in productive_keywords if keyword in text_lower)
    unproductive_count = sum(1 for keyword in unproductive_keywords if keyword in text_lower)
    
    # Determinar classificação
    if productive_count > unproductive_count:
        confidence = min(0.8, 0.5 + (productive_count * 0.1))
        return {'classification': 'productive', 'confidence': confidence}
    elif unproductive_count > productive_count:
        confidence = min(0.8, 0.5 + (unproductive_count * 0.1))
        return {'classification': 'unproductive', 'confidence': confidence}
    else:
        # Neutro - classificar baseado no comprimento e estrutura
        if len(text) > 50 and any(char in text for char in ['.', '!', '?']):
            return {'classification': 'productive', 'confidence': 0.6}
        else:
            return {'classification': 'unproductive', 'confidence': 0.6}


def health_check(request):
    """
    Health check endpoint
    """
    ai_settings = getattr(settings, 'AI_SETTINGS', {})
    token_configured = bool(ai_settings.get('HUGGINGFACE_API_TOKEN'))
    
    return JsonResponse({
        "status": "ok",
        "message": "IA Endpoint funcionando!",
        "ai_configured": token_configured,
        "model": ai_settings.get('CLASSIFICATION_MODEL', 'N/A'),
        "settings_count": len(ai_settings)
    })
