"""
Classificação direta inspirada no ai_standalone - FUNCIONAL
"""
import json
import time
import requests
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def classify_email_direct(subject, content):
    """
    Classificação direta inspirada no ai_standalone que funciona
    """
    try:
        # Combinar texto como no ai_standalone
        text = f"{subject} {content}".strip()
        
        if not text:
            return {
                "success": False,
                "error": "Texto vazio"
            }
        
        # Obter configurações IA
        ai_settings = getattr(settings, 'AI_SETTINGS', {})
        token = ai_settings.get('HUGGINGFACE_API_TOKEN')
        model = ai_settings.get('CLASSIFICATION_MODEL', 'cardiffnlp/twitter-roberta-base-sentiment')
        
        start_time = time.time()
        
        if token and len(token) > 10:
            # Tentar IA real
            try:
                result = classify_with_huggingface_direct(text, token, model)
                processing_time = round(time.time() - start_time, 2)
                
                return {
                    "success": True,
                    "text": text[:100] + "..." if len(text) > 100 else text,
                    "classification": result['classification'],
                    "confidence": result['confidence'],
                    "model_version": "ai-huggingface_api",
                    "processing_time": f"{processing_time}s",
                    "message": "Email classificado com IA real!",
                    "category": result['classification'],
                    "suggested_response": generate_response_for_category(result['classification'])
                }
                
            except Exception as e:
                logger.warning(f"⚠️ Erro IA real: {e}")
                # Fallback para heurística
                pass
        
        # Fallback heurístico (sempre funciona)
        result = classify_heuristic_direct(text)
        processing_time = round(time.time() - start_time, 2)
        
        return {
            "success": True,
            "text": text[:100] + "..." if len(text) > 100 else text,
            "classification": result['classification'],
            "confidence": result['confidence'],
            "model_version": "heuristic-fallback",
            "processing_time": f"{processing_time}s",
            "message": "Email classificado com heurística (IA indisponível)",
            "category": result['classification'],
            "suggested_response": generate_response_for_category(result['classification'])
        }
        
    except Exception as e:
        logger.error(f"Erro na classificação direta: {str(e)}")
        return {
            "success": False,
            "error": f"Erro interno: {str(e)}"
        }


def classify_with_huggingface_direct(text, token, model):
    """
    Classificação com Hugging Face API (cópia do ai_standalone)
    """
    url = f"https://api-inference.huggingface.co/models/{model}"
    headers = {"Authorization": f"Bearer {token}"}
    
    payload = {"inputs": text}
    
    response = requests.post(url, headers=headers, json=payload, timeout=10)
    
    if response.status_code == 200:
        result = response.json()
        
        if isinstance(result, list) and len(result) > 0:
            scores = result[0]
            
            # Mapear sentimentos para produtividade (mesmo que ai_standalone)
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
                heuristic = classify_heuristic_direct(text)
                classification = heuristic['classification']
                confidence = min(confidence, 0.6)  # Reduzir confiança para neutros
            
            return {
                'classification': classification,
                'confidence': round(confidence, 3)
            }
    
    raise Exception(f"API error: {response.status_code}")


def classify_heuristic_direct(text):
    """
    Classificação heurística (cópia exata do ai_standalone)
    """
    text_lower = text.lower()
    
    # Palavras-chave produtivas (mesmo que ai_standalone)
    productive_keywords = [
        'reunião', 'projeto', 'deadline', 'urgente', 'importante', 'trabalho',
        'tarefa', 'entrega', 'apresentação', 'cliente', 'contrato', 'proposta',
        'desenvolvimento', 'bug', 'sistema', 'produção', 'deploy', 'meeting',
        'project', 'urgent', 'important', 'work', 'task', 'delivery', 'client',
        'contract', 'proposal', 'development', 'production', 'critical'
    ]
    
    # Palavras-chave não produtivas (mesmo que ai_standalone)
    unproductive_keywords = [
        'promoção', 'desconto', 'grátis', 'ganhe', 'oferta', 'clique',
        'compre', 'venda', 'marketing', 'spam', 'promocional', 'publicidade',
        'social', 'pessoal', 'fim de semana', 'férias', 'festa', 'birthday',
        'promotion', 'discount', 'free', 'buy', 'sale', 'marketing', 'spam',
        'advertisement', 'social', 'personal', 'weekend', 'vacation', 'party'
    ]
    
    # Contar ocorrências (mesmo algoritmo que ai_standalone)
    productive_count = sum(1 for keyword in productive_keywords if keyword in text_lower)
    unproductive_count = sum(1 for keyword in unproductive_keywords if keyword in text_lower)
    
    # Determinar classificação (mesma lógica que ai_standalone)
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


def generate_response_for_category(category):
    """
    Gerar resposta sugerida baseada na categoria
    """
    responses = {
        'productive': 'Obrigado pelo seu email profissional. Vou analisar e retornar em breve.',
        'unproductive': 'Obrigado pelo contato, mas este email não parece ser prioritário no momento.'
    }
    return responses.get(category, responses['unproductive'])
