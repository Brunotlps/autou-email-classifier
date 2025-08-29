""" Serviços para classificações dos emails / Email classifications services """


import time
from typing import Dict, Any
from .models import Classification



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
        'reunião', 'projeto', 'deadline', 'importante', 'urgente',
        'meeting', 'project', 'urgent', 'important', 'deadline',
        'prazo', 'tarefa', 'entrega', 'proposta', 'contrato',
        'documento', 'relatório', 'report', 'task', 'delivery',
        'document', 'proposal', 'contract', 'follow-up'
    ]


    # Análise simpole baseada em palavras-chave / Simple keyword-based analysis
    content_lower = email_content.lower()
    productive_matches = sum(1 for keyword in productive_keywords if keyword in content_lower)


    # Determinar classificação baseada em matches / Determine classification based on matches
    if productive_matches >= 2:
        category = 'productive'
        confidence = min(0.85 + (productive_matches * 0.03), 0.95)
        response = f'Email produtivo identificado ({productive_matches} indicadores). Recomendo responder em breve.'
    elif productive_matches == 1:
        category = 'productive'
        confidence = 0.65 + (len(content_lower) / 1000 * 0.1)  # Confiança baseada no tamanho
        response = 'Email pode ser produtivo. Revisar conteúdo para confirmar prioridade.'
    else:
        category = 'unproductive'
        confidence = 0.72
        response = 'Email não parece prioritário com base nos indicadores analisados.'
    
    # Calcular tempo de processamento / Calculate processing time
    processing_time = time.time() - start_time

    return {
        'category': category,
        'confidence': round(confidence, 3),
        'response': response,
        'model_used': 'basic-keyword-classifier-v1.0',
        'processing_time': processing_time,
        'keywords_found': productive_matches
    }


def process_classification_async(classification_id: int) -> bool:
    """
        Processa a classificação de email de forma assíncrona. / Processes email classification asynchronously.

        Args:
            classification_id (int): ID da classificação a ser processada / ID of the classification to be processed
        Returns:
            bool: Indica se o processamento foi bem-sucedido / Indicates if processing was successful
    """

    try:
        classification = Classification.objects.get(id=classification_id)

        classification.mark_as_processing()

        # Simulação de processamento assíncrono / Simulating asynchronous processing
        if classification.email:
            result = classify_email_basic(classification.email.content)

            # Marcar classificação como concluída / Mark classification as completed
            classification.mark_as_completed(
                classification_result=result['category'],
                confidence_score=result['confidence'],
                suggested_response=result['response'],
                ai_model_used=result['model_used'],
                processing_time=result['processing_time']
            )
            
            return True
        else:
            classification.mark_as_failed("Email não encontrado para classificação.")
            return False
    
    except Classification.DoesNotExist:
        # Log de erro / Log error
        print(f"Classificação com ID {classification_id} não encontrada.")
        return False
    except Exception as e:
        # Log de erro / Log error
        print(f"Erro ao processar classificação ID {classification_id}: {str(e)}")
        classification.mark_as_failed(f"Erro no processamento: {str(e)}")
        return False
