import requests
import logging
import time
import re

from typing import Dict, Optional, List, Tuple
from django.conf import settings
from django.core.cache import cache



# Imports condicionais para fallback local. / Conditional imports for local fallback.
try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logging.warning("Transformers não disponível para fallback local")

logger = logging.getLogger(__name__)


class HuggingFaceAPIError(Exception):
    """Exceção personalizada para erros da API Hugging Face."""
    pass


class AIClassificationService:
    """
        Serviço de IA para classificação de emails e geração de respostas / AI service for email classification and response generation.

        Integra com Hugging Face API com fallback para modelos locais / Integrates with Hugging Face API with local model fallback.
        Inclui cache, rate limiting e retry logic / Includes caching, rate limiting, and retry logic.
    """


    def __init__(self):
        """Inicializa o serviço com configurações default / Initializes the service with default settings."""


        # Configurações da API / API settings
        self.api_token = settings.AI_SETTINGS['HUGGINGFACE_API_TOKEN']
        self.api_url = settings.AI_SETTINGS['HUGGINGFACE_API_URL']
        self.timeout = settings.AI_SETTINGS['PROCESSING_TIMEOUT']
        self.retry_attempts = settings.AI_SETTINGS['AI_RETRY_ATTEMPTS']


        # Modelos / Models
        self.classification_model = settings.AI_SETTINGS['CLASSIFICATION_MODEL']
        self.response_model = settings.AI_SETTINGS['RESPONSE_GENERATION_MODEL']
        self.backup_model = settings.AI_SETTINGS['BACKUP_CLASSIFICATION_MODEL']

        self.ai_mode = settings.AI_SETTINGS['AI_MODE']
        self.use_local_models = settings.AI_SETTINGS['AI_USE_LOCAL_MODELS']  

        
        # Configurações de processamento / Processing settings
        self.confidence_threshold = settings.AI_SETTINGS['AI_CONFIDENCE_THRESHOLD']
        self.max_response_length = settings.AI_SETTINGS['MAX_RESPONSE_LENGTH']
        self.fallback_to_local = settings.AI_SETTINGS['AI_FALLBACK_TO_LOCAL']

        # Cache e rate limiting / Cache and rate limiting
        self.cache_ttl = settings.AI_SETTINGS['AI_CACHE_TTL']
        self.rate_limit = settings.AI_SETTINGS['AI_RATE_LIMIT_PER_MINUTE']

        
        # Headers da API / API headers
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
            "User-Agent": "AutoU-Email-Classifier/1.0"
        }


        # Pipeline local para fallback / Local pipeline for fallback
        self._local_classifier = None

        # Estatísticas de uso / Usage statistics
        self.stats = {
            'api_calls': 0,
            'cache_hits': 0,
            'fallback_uses': 0,
            'errors': 0
        }

        logger.info("AI Classification Service inicializado.")
        self._validate_configuration()
    

    def classify_email_text(self, email_content: str) -> Dict:
        """
            Classifica um email como produtivo ou improdutivo / Classifies an email as productive or unproductive.

            Estratégia / Strategy:
                1. Verifica o cache / Check cache
                2. Tenta chamar a API Hugging Face / Try calling Hugging Face API
                3. Fallback para modelo local se disponível / Fallback to local model if available
                4. Fallback para heurísticas simples / Fallback to simple heuristics
        """


        if not email_content or not email_content.strip():
            logger.warning("Conteúdo do email vazio ou inválido.")
            return self._get_fallback_classification("Email vazio")
        

        # Preprocessar texto / Preprocess text
        processed_text = self._preprocess_text(email_content)

        # Verificar cache / Check cache
        cache_key = self._get_cache_key('classify', processed_text)
        cached_result = cache.get(cache_key)
        
        if cached_result:
            self.stats['cache_hits'] += 1
            logger.info("Resultado de classificação obtido do cache.")
            return cached_result


        # Verificar rate limiting / Check rate limiting
        if not self._check_rate_limit():
            logger.error("Limite de taxa excedido, usando fallback.")
            return self._classify_with_fallback(processed_text)
        
        logger.info(f"Classificando email via API (length: {len(processed_text)})")


        try:
            # Tenta via API / Try via API
            result = self._classify_with_api(processed_text)

            # Cache do resultado / Cache the result
            cache.set(cache_key, result, self.cache_ttl)

            logger.info(f"Classificação API: {result['classification']} (confiança: {result['confidence']:.2f})")
            return result
        except Exception as e:
            logger.error(f"Erro na classificação via API: {e}")
            self.stats['errors'] += 1

            # Fallback para modelo local ou heurísticas / Fallback to local model or heuristics
            return self._classify_with_fallback(processed_text)
        

    def generate_response(self, email_content: str, classification: str) -> Dict:
        """
            Gera um resposta automática baseada no conteúdo do email e sua classificação / Generates an automatic response based on email content and its classification.

            Usa templates personalizados com contexto extraído do email / Uses custom templates with context extracted from the email.
        """
        logger.info(f"Gerando resposta para email classificado como {classification}")


        try:
            # Extrair contexto do email / Extract context from email
            context = self._extract_email_context(email_content)

            # Verificar cache / Check cache
            cache_key = self._get_cache_key('response', f"{classification}_{context}")
            cached_response = cache.get(cache_key)

            if cached_response:
                self.stats['cache_hints'] += 1
                logger.info("Resposta obtida do cache.")
                return cached_response
            
            # Gerar resposta / Generate response
            if settings.AI_SETTINGS['AI_MODE'] == 'online' and self.api_token:
                try:
                    response = self._generate_response_api(email_content, classification, context)
                except Exception as e:
                    logger.warning(f"API response generation falhou: {str(e)}")
                    response = self._generate_response_template(classification, context)
            else:
                response = self._generate_response_template(classification, context)
            
            # Cache da resposta / Cache the response
            cache.set(cache_key, response, self.cache_ttl)

            logger.info(f"Resposta gerada (length: {len(response['suggested_response'])})")
            return response

        except Exception as e:
            logger.error(f"❌ Erro na geração de resposta: {str(e)}")
            return self._get_fallback_response(classification)
    

    def _validate_configuration(self):
        

        if not self.api_token:
            logger.warning("HUGGINGFACE_API_TOKEN não configurado. Usando fallback local ou heurísticas.")
        
        if not self.api_url:
            logger.error("HUGGINGFACE_API_URL não configurado. A API não funcionará.")
    

        # Testar conectividade / Test connectivity
        if self.api_token:
            try:
                test_url = f"{self.api_url}/{self.classification_model}"
                response = requests.head(test_url, headers=self.headers, timeout=5)
                if response.status_code == 200:
                    logger.info("Conectividade com Hugging Face OK")
                else:
                    logger.warning(f"Modelo pode não estar disponível: {response.status_code}")
            except Exception as e:
                logger.warning(f"Não foi possível testar conectividade: {str(e)}")


    def _preprocess_text(self, text: str) -> str:


        if not text:
            return ""
        
        cleaned = text.strip()
        cleaned = re.sub(r'[\x00-\x1F\x7F-\x9F]', ' ', cleaned)
        cleaned = ' '.join(cleaned.split())

        # Truncar para limite do modelo (512 tokens ~ 400 chars) / Truncate to model limit (512 tokens ~ 400 chars
        if len(cleaned) > 400:
            cleaned = cleaned[:400] + "..."
            logger.debug("Texto truncado para limite do modelo.")
        
        return cleaned
    

    def _classify_with_api(self, text: str) -> Dict:
        """Chama a API Hugging Face para classificação / Calls Hugging Face API for classification."""


        url = f"{self.api_url}/{self.classification_model}"
        payload = {
            "inputs": text,
            "parameters": {
                "return_all_scores": True,
            }
        }

        for attempt in range(self.retry_attempts):
            try:
                logger.debug(f"Tentativa {attempt + 1} - Chamando API {self.classification_model}")
                
                response = requests.post(
                    url,
                    headers=self.headers,
                    json=payload,
                    timeout=self.timeout
                )

                self.stats['api_calls'] += 1

                if response.status_code == 200:
                    result = response.json()
                    return self._process_api_classification_result(result, text)

                elif response.status_code == 503:
                    wait_time = 2 ** attempt
                    logger.info(f"Modelo carregando, aguardando {wait_time}s antes de tentar novamente.")
                    time.sleep(wait_time)
                    continue

                else:
                    error_message = f"Erro na API: {response.status_code} - {response.text}"
                    if attempt == self.retry_attempts -1:
                        raise HuggingFaceAPIError(error_message)
                    logger.warning(f"{error_message}, tentando novamente...")

            except requests.exceptions.Timeout:
                if attempt == self.retry_attempts - 1:
                    raise HuggingFaceAPIError("Timeout na API")
                logger.warning(f"Timeout na tentativa {attempt + 1}")
                
            except requests.exceptions.RequestException as e:
                if attempt == self.retry_attempts - 1:
                    raise HuggingFaceAPIError(f"Erro de conexão: {str(e)}")
                logger.warning(f"Erro de conexão: {str(e)}")
            
        raise HuggingFaceAPIError("Todas as tentativas de API falharam")
    

    def _process_api_classification_result(self, api_result: List[Dict], original_text: str) -> Dict:
        """Processa resultado da API de classificação. / Processes classification API result."""
        
        
        if not api_result or not isinstance(api_result, list) or not api_result[0]:
            raise ValueError("Resultado da API inválido")
        
        scores = api_result[0]
        if not scores:
            raise ValueError("Scores vazios na resposta da API")
        
        # Encontrar melhor score / Find best score
        best_score = max(scores, key=lambda x: x.get('score', 0))
        
        # Mapear sentimento para nossa classificação / Map sentiment to our classification
        sentiment_mapping = {
            'POSITIVE': 'productive',
            'LABEL_2': 'productive',
            'pos': 'productive',
            'NEGATIVE': 'unproductive',
            'LABEL_0': 'unproductive', 
            'neg': 'unproductive',
            'NEUTRAL': 'unproductive',
            'LABEL_1': 'unproductive',
            'neutral': 'unproductive'
        }
        
        sentiment = best_score.get('label', 'UNKNOWN')
        confidence = best_score.get('score', 0.0)
        classification = sentiment_mapping.get(sentiment, 'unproductive')
        
        # Ajustar confiança baseada em contexto / Adjust confidence based on context
        adjusted_confidence = self._adjust_confidence_by_context(
            classification, confidence, original_text
        )
        
        return {
            'classification': classification,
            'confidence': adjusted_confidence,
            'processing_details': {
                'method': 'huggingface_api',
                'model_used': self.classification_model,
                'original_sentiment': sentiment,
                'original_confidence': confidence,
                'all_scores': scores,
                'text_length': len(original_text),
                'processed_at': time.time()
            }
        }
    

    def _classify_with_fallback(self, text: str) -> Dict:
        """Usa métodos de fallback quando API falha. / Uses fallback methods when API fails."""


        self.stats['fallback_uses'] += 1
        
        # MUDANÇA: Priorizar heurística para classificação de produtividade / CHANGE: Prioritize heuristics for productivity classification
        logger.info("Usando fallback heurístico (prioridade para produtividade).")
        heuristic_result = self._classify_with_heuristics(text)
        
        # Se heurística tem alta confiança, usar ela / If heuristic is high confidence, use it
        if heuristic_result['confidence'] >= 0.8:
            logger.info(f"✅ Heurística confiável: {heuristic_result['confidence']:.2f}")
            return heuristic_result
        
        # Senão, tentar modelo local como validação adicional / Else, try local model as additional validation
        if self.fallback_to_local and TRANSFORMERS_AVAILABLE:
            try:
                local_result = self._classify_with_local_model(text)
                
                # Combinar resultados: se heurística e modelo concordam, aumentar confiança / Combine results: if heuristic and model agree, boost confidence
                if heuristic_result['classification'] == local_result['classification']:
                    confidence = min(0.95, (heuristic_result['confidence'] + local_result['confidence']) / 2 + 0.1)
                    logger.info(f"✅ Consenso heurística + modelo local: {confidence:.2f}")
                    
                    return {
                        'classification': heuristic_result['classification'],
                        'confidence': confidence,
                        'processing_details': {
                            'method': 'consensus_fallback',
                            'heuristic_confidence': heuristic_result['confidence'],
                            'local_confidence': local_result['confidence'],
                            'consensus_boost': True,
                            'processed_at': time.time()
                        }
                    }
                else:
                    # Se discordam, priorizar heurística para produtividade / If they disagree, prioritize heuristic for productivity
                    logger.warning(f"⚠️ Discordância: heurística={heuristic_result['classification']}, modelo={local_result['classification']}")
                    return heuristic_result
                    
            except Exception as e:
                logger.warning(f"Fallback local falhou: {str(e)}")
        
        return heuristic_result

    def _classify_with_local_model(self, text: str) -> Dict:
        """Classifica usando modelo local. / Classifies using local model."""
        
        
        if not self._local_classifier:
            logger.info("Carregando modelo local...")
            self._local_classifier = pipeline(
                "sentiment-analysis",
                model=self.backup_model,
                return_all_scores=True # top_k = None
            )
        
        result = self._local_classifier(text[:512])
        
        if result and result[0]:
            scores = result[0]
            best_score = max(scores, key=lambda x: x['score'])
            
            # MAPEAMENTO MELHORADO - Considerar contexto / IMPROVED MAPPING - Consider context
            text_lower = text.lower()
            
            # Verificar indicadores de produtividade independente do sentimento / Check productivity indicators regardless of sentiment
            productive_indicators = [
                'reunião', 'meeting', 'projeto', 'project', 'deadline', 'prazo',
                'urgente', 'urgent', 'importante', 'important', 'tarefa', 'task',
                'entrega', 'delivery', 'proposta', 'proposal', 'contrato', 'contract'
            ]
            
            productive_count = sum(1 for word in productive_indicators if word in text_lower)
            
            # Se tem muitos indicadores produtivos, forçar productive independente do sentimento / If many productive indicators, force productive regardless of sentiment
            if productive_count >= 2:
                classification = 'productive'
                # Ajustar confiança baseada nos indicadores / Adjust confidence based on indicators
                confidence = min(0.95, 0.7 + (productive_count * 0.05))
                logger.info(f"🔧 Override: {productive_count} indicadores produtivos detectados")
            else:
                # Usar sentimento original apenas se não há indicadores claros / Use original sentiment only if no clear indicators
                classification = 'productive' if best_score['label'] == 'POSITIVE' else 'unproductive'
                confidence = best_score['score']
            
            return {
                'classification': classification,
                'confidence': confidence,
                'processing_details': {
                    'method': 'local_model_enhanced',
                    'model_used': self.backup_model,
                    'original_sentiment': best_score['label'],
                    'productive_indicators_found': productive_count,
                    'override_applied': productive_count >= 2,
                    'processed_at': time.time()
                }
            }
        
        raise ValueError("Modelo local retornou resultado inválido")


    def _classify_with_heuristics(self, text: str) -> Dict:
        """Classificação heurística baseada em palavras-chave. / Heuristic classification based on keywords."""
        
        
        productive_keywords = [
            # Reuniões e encontros / Meetings and gatherings
            'reunião', 'meeting', 'encontro', 'videoconferência', 'call', 'zoom', 'teams',
            # Projetos e trabalho / Projects and work
            'projeto', 'project', 'trabalho', 'work', 'tarefa', 'task', 'atividade',
            # Prazos e urgência / Deadlines and urgency
            'deadline', 'prazo', 'urgente', 'urgent', 'importante', 'important', 'asap',
            # Entregas e resultados / Deliveries and results
            'entrega', 'delivery', 'resultado', 'result', 'relatório', 'report',
            # Propostas e negócios / Proposals and business
            'proposta', 'proposal', 'contrato', 'contract', 'acordo', 'agreement',
            # Documentos e dados / Documents and data
            'documento', 'document', 'planilha', 'spreadsheet', 'apresentação',
            # Comunicação profissional / Professional communication
            'prezado', 'dear', 'cordialmente', 'regards', 'atenciosamente',
            # Ações e verbos de trabalho / Actions and work verbs
            'agendar', 'schedule', 'confirmar', 'confirm', 'revisar', 'review',
            'aprovar', 'approve', 'enviar', 'send', 'receber', 'receive'
        ]
        
        unproductive_keywords = [
            # Marketing e promoções / Marketing and promotions
            'promoção', 'promotion', 'desconto', 'discount', 'oferta', 'offer',
            'grátis', 'free', 'ganhe', 'win', 'premio', 'prize',
            # Spam típico / Typical spam
            'spam', 'clique aqui', 'click here', 'compre agora', 'buy now',
            # Marketing digital / Digital marketing
            'marketing', 'newsletter', 'publicidade', 'advertising',
            # Redes sociais / Social media
            'social', 'facebook', 'instagram', 'twitter', 'linkedin',
            # Urgência falsa / False urgency
            'limitado', 'limited', 'últimas horas', 'last hours',
            # Emojis excessivos (indicador de spam) / Excessive emojis (spam indicator)
            '🎉', '💰', '🔥', '⚡', '🎊'
        ]
        
        text_lower = text.lower()
        
        productive_matches = sum(1 for kw in productive_keywords if kw in text_lower)
        unproductive_matches = sum(1 for kw in unproductive_keywords if kw in text_lower)
        
         
        total_words = len(text_lower.split())
        productive_density = productive_matches / max(total_words, 1)
        
        if productive_matches >= 3:  # 3+ indicadores = alta produtividade / 3+ indicators = high productivity
            classification = 'productive'
            confidence = min(0.95, 0.8 + (productive_matches * 0.03))
        elif productive_matches >= 2:  # 2 indicadores = provável produtividade / 2 indicators = likely productive
            classification = 'productive'
            confidence = 0.75 + (productive_density * 0.2)
        elif productive_matches > unproductive_matches and productive_matches > 0:
            classification = 'productive'
            confidence = 0.65 + (productive_matches * 0.05)
        elif unproductive_matches > 2:  
            classification = 'unproductive'
            confidence = min(0.95, 0.7 + (unproductive_matches * 0.05))
        else:
            # Padrão: se em dúvida, considerar produtivo em contexto empresarial / Default: if in doubt, consider productive in business context
            classification = 'productive' if total_words > 20 else 'unproductive'
            confidence = 0.6
        
        return {
            'classification': classification,
            'confidence': confidence,
            'processing_details': {
                'method': 'heuristic_enhanced',
                'productive_keywords': productive_matches,
                'unproductive_keywords': unproductive_matches,
                'text_length': total_words,
                'productive_density': productive_density,
                'processed_at': time.time()
            }
        }
    

    def _adjust_confidence_by_context(self, classification: str, confidence: float, text: str) -> float:
        """Ajusta confiança baseada no contexto do email. / Adjusts confidence based on email context."""
        
        
        # Aumentar confiança para emails claramente urgentes / Increase confidence for clearly urgent emails
        if any(word in text.lower() for word in ['urgente', 'asap', 'emergency', 'deadline']):
            if classification == 'productive':
                confidence = min(0.95, confidence + 0.1)

        # Diminuir confiança para textos muito curtos / Decrease confidence for very short texts
        if len(text) < 50:
            confidence = max(0.5, confidence - 0.1)
        
        return round(confidence, 3)
    

    def _extract_email_context(self, email_content: str) -> Dict:
        """Extrai contexto do email para personalizar resposta. / Extracts email context to personalize response."""
        
        
        context = {
            'has_meeting': any(word in email_content.lower() for word in ['reunião', 'meeting', 'encontro']),
            'has_deadline': any(word in email_content.lower() for word in ['prazo', 'deadline', 'urgente']),
            'has_questions': '?' in email_content,
            'is_urgent': any(word in email_content.lower() for word in ['urgente', 'urgent', 'asap']),
            'length': len(email_content),
            'tone': 'formal' if any(word in email_content.lower() for word in ['prezado', 'cordialmente']) else 'casual'
        }
        return context
    

    def _generate_response_template(self, classification: str, context: Dict) -> Dict:
        """Gera resposta usando templates. / Generates response using templates."""
        
        
        if classification == 'productive':
            if context['has_meeting']:
                response = "Obrigado pelo email. Vou verificar minha agenda e confirmar a reunião em breve."
            elif context['has_deadline']:
                response = "Recebi sua mensagem urgente. Vou priorizar e retornar rapidamente."
            elif context['has_questions']:
                response = "Obrigado pelas perguntas. Vou analisar e enviar as respostas detalhadas em breve."
            else:
                response = "Obrigado pelo seu email. Vou analisar as informações e retornar em breve."
        else:
            response = "Obrigado pelo contato, mas no momento não posso ajudar com isso."
        
        return {
            'suggested_response': response,
            'confidence': 0.8,
            'generation_details': {
                'method': 'template_based',
                'context_used': context,
                'generated_at': time.time()
            }
        }
    

    def _generate_response_api(self, email_content: str, classification: str, context: Dict) -> Dict:
        """Gera resposta via API Hugging Face (implementação futura). / Generates response via Hugging Face API (future implementation)."""
        
        
        # Por enquanto, usar templates / For now, use templates
        return self._generate_response_template(classification, context)
    

    def _check_rate_limit(self) -> bool:
        

        current_minute = int(time.time() // 60)
        cache_key = f"ai_rate_limit_{current_minute}"
        
        current_count = cache.get(cache_key, 0)
        if current_count >= self.rate_limit:
            return False
        
        cache.set(cache_key, current_count + 1, 60)
        return True
    

    def _get_cache_key(self, operation: str, content: str) -> str:
        """Gera chave de cache baseada no conteúdo. / Generates cache key based on content."""
        
        
        import hashlib
        content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
        return f"ai_{operation}_{content_hash}"
    

    def _get_fallback_classification(self, reason: str = "Unknown error") -> Dict:
        """Classificação padrão quando tudo falha. / Default classification when all else fails."""
        
        
        return {
            'classification': 'unproductive',
            'confidence': 0.5,
            'processing_details': {
                'method': 'fallback_default',
                'reason': reason,
                'processed_at': time.time()
            }
        }
    

    def _get_fallback_response(self, classification: str) -> Dict:
        """Resposta padrão quando geração falha. / Default response when generation fails."""
        
        
        responses = {
            'productive': "Obrigado pelo seu email. Vou analisar e retornar em breve.",
            'unproductive': "Obrigado pelo contato."
        }
        
        return {
            'suggested_response': responses.get(classification, responses['unproductive']),
            'confidence': 0.5,
            'generation_details': {
                'method': 'fallback_default',
                'reason': 'Response generation failed',
                'generated_at': time.time()
            }
        }
    

    def get_stats(self) -> Dict:
        

        return {
            **self.stats,
            'cache_hit_rate': self.stats['cache_hits'] / max(1, self.stats['api_calls'] + self.stats['cache_hits']),
            'error_rate': self.stats['errors'] / max(1, self.stats['api_calls']),
            'fallback_rate': self.stats['fallback_uses'] / max(1, self.stats['api_calls'] + self.stats['fallback_uses'])
        }

# Instancia singleton do serviço / Singleton instance of the service
ai_service = AIClassificationService()