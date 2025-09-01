"""Serviços para classificações dos emails / Email classifications services"""

import time
from typing import Dict, Any
from .models import Classification
import logging

logger = logging.getLogger(__name__)


def classify_email_basic(email_content: str) -> Dict[str, Any]:
    """
    Classificação básica de email baseada em palavras-chave. / Basic email classification based on keywords.

    Args:
        email_content (str): Conteúdo do email / Email content
    Returns:
        Dict[str, Any]: Resultado da classificação / Classification result
    """

    # Simulação do tempo de processamento / Simulating processing time
    start_time = time.time()

    productive_keywords = [
        "reunião",
        "projeto",
        "deadline",
        "importante",
        "urgente",
        "meeting",
        "project",
        "urgent",
        "important",
        "deadline",
        "prazo",
        "tarefa",
        "entrega",
        "proposta",
        "contrato",
        "documento",
        "relatório",
        "report",
        "task",
        "delivery",
        "document",
        "proposal",
        "contract",
        "follow-up",
    ]

    # Análise simpole baseada em palavras-chave / Simple keyword-based analysis
    content_lower = email_content.lower()
    productive_matches = sum(1 for keyword in productive_keywords if keyword in content_lower)

    # Determinar classificação baseada em matches / Determine classification based on matches
    if productive_matches >= 2:
        category = "productive"
        confidence = min(0.85 + (productive_matches * 0.03), 0.95)
        response = f"Email produtivo identificado ({productive_matches} indicadores). Recomendo responder em breve."
    elif productive_matches == 1:
        category = "productive"
        confidence = 0.65 + (len(content_lower) / 1000 * 0.1)  # Confiança baseada no tamanho
        response = "Email pode ser produtivo. Revisar conteúdo para confirmar prioridade."
    else:
        category = "unproductive"
        confidence = 0.72
        response = "Email não parece prioritário com base nos indicadores analisados."

    # Calcular tempo de processamento / Calculate processing time
    processing_time = time.time() - start_time

    return {
        "category": category,
        "confidence": round(confidence, 3),
        "response": response,
        "model_used": "basic-keyword-classifier-v1.0",
        "processing_time": processing_time,
        "keywords_found": productive_matches,
    }


def process_classification_async(email_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Processamento assíncrono com IA integrada. / Asynchronous processing with integrated AI.

    Args:
        email_data (Dict): Dados do email / Email data
    Returns:
        Dict: Resultado do processamento / Processing result
    """

    try:
        subject = email_data.get("subject", "")
        content = email_data.get("content", "")

        # Usar IA por padrão, fallback para básico se falhar / Use AI by default, fallback to basic if it fails
        result = classify_email_ai(subject, content)

        return {
            "success": True,
            "classification": result["category"],
            "confidence": result["confidence"],
            "suggested_response": result["suggested_response"],
            "processing_details": {
                "method": "ai_enhanced",
                "processing_time": result["processing_time"],
                "model_used": result["model_used"],
                "ai_details": result["ai_details"],
            },
        }

    except Exception as e:
        logger.error(f"Erro no processamento assíncrono: {str(e)}")
        # Fallback completo / Full fallback
        basic_result = classify_email_basic(subject, content)
        return {
            "success": False,
            "classification": basic_result["category"],
            "confidence": basic_result["confidence"],
            "suggested_response": basic_result.get("suggested_response", ""),
            "processing_details": {"method": "basic_fallback", "error": str(e)},
        }


def classify_email_ai(subject: str, content: str) -> Dict[str, Any]:
    """
    Classificação avançada de email usando IA. / Advanced email classification using AI.

    Args:
        subject (str): Assunto do email / Email subject
        content (str): Conteúdo do email / Email content
    Returns:
        Dict[str, Any]: Resultado da classificação com IA / AI classification result
    """
    from .ai_service import ai_service
    import time

    start_time = time.time()

    # Combinar subject + content para análise completa / Combine subject + content for full analysis
    full_text = f"{subject}\n\n{content}" if subject else content

    try:
        # Obter classificação IA / Get AI classification
        ai_result = ai_service.classify_email_text(full_text)

        # Gerar resposta automática /  Generate automatic response
        response_result = ai_service.generate_response(full_text, ai_result["classification"])

        processing_time = time.time() - start_time

        # Combinar resultados no formato esperado pela API / Combine results in expected API format
        return {
            "category": ai_result["classification"],
            "confidence": ai_result["confidence"],
            "suggested_response": response_result["suggested_response"],
            "response_confidence": response_result["confidence"],
            "processing_time": round(processing_time, 3),
            "model_used": f"ai-{ai_result['processing_details']['method']}",
            "ai_details": {
                "classification_method": ai_result["processing_details"]["method"],
                "model_used": ai_result["processing_details"].get("model_used", "heuristic"),
                "context_detected": response_result["generation_details"]["context_used"],
                "keywords_found": ai_result["processing_details"].get("productive_keywords", 0),
                "confidence_boost": ai_result["processing_details"].get("consensus_boost", False),
                "processed_at": ai_result["processing_details"]["processed_at"],
            },
        }

    except Exception as e:
        logger.error(f"Erro na classificação AI: {str(e)}")
        # Fallback para classificação básica / Fallback to basic classification
        return classify_email_basic(subject, content)
