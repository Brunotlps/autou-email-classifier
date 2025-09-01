from django.views.generic import TemplateView
from django.shortcuts import render
from django.contrib import messages
from django.conf import settings
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta, datetime
import json
import logging

logger = logging.getLogger(__name__)

class HomeView(TemplateView):
    """Pagina inicial do sistema / Home page of the system."""
    template_name = 'base/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'AutoU Email Classifier',
            'description': 'Sistema de classificação de emails usando IA.',
            'version': '1.0.0',
            'features': [
                'Classificação automática de emails',
                'Dashboard interativo',
                'Histórico de classificações',
                'Upload fácil de arquivos CSV',
                'Visualização de resultados detalhados'
            ]
        })
        return context

class UploadView(TemplateView):
    """Pagina de upload de emails / Email upload page."""
    template_name = 'classifier/upload.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Upload de Email'
        context['api_endpoint'] = '/api/classifier/classifications/classify_no_db/'
        return context



class DashboardTestView(TemplateView):
    """Página de teste do dashboard sem base.html"""
    template_name = 'classifier/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            # ✅ REUTILIZAR A MESMA LÓGICA DO DASHBOARDVIEW
            stats = self._get_initial_stats()
            timeline_data = self._get_timeline_data()
            confidence_data = self._get_confidence_distribution()
            recent_emails = self._get_recent_classifications()
            
            context.update({
                'title': 'Dashboard Test',
                'description': 'Teste isolado dos gráficos sem Bootstrap.',
                'has_data': True,
                'stats': stats,
                'timeline_labels': json.dumps(timeline_data['labels']),
                'timeline_data': json.dumps(timeline_data['data']),
                'confidence_distribution': json.dumps(confidence_data),
                'recent_emails': recent_emails,
                'system_status': 'success'
            })
            
        except Exception as e:
            logger.error(f"Erro ao carregar dashboard test: {e}")
            context.update({
                'title': 'Dashboard Test',
                'description': 'Erro ao carregar dados do dashboard test.',
                'has_data': False,
                'error_message': 'Dados indisponíveis no momento.',
                'stats': {'total_emails': 0, 'productive_emails': 0, 'unproductive_emails': 0, 'neutral_emails': 0},
                'timeline_labels': json.dumps([]),
                'timeline_data': json.dumps([]),
                'confidence_distribution': json.dumps([0, 0, 0, 0, 0]),
                'recent_emails': [],
                'system_status': 'error'
            })

        return context
    
    # ✅ COPIAR TODOS OS MÉTODOS AUXILIARES DO DASHBOARDVIEW
    def _get_initial_stats(self):
        """Obter estatísticas básicas das Classifications."""
        try:
            from apps.classifier.models import Classification
            
            total_classifications = Classification.objects.filter(processing_status='completed').count()

            stats = Classification.objects.filter(processing_status='completed').aggregate(
                productive=Count('id', filter=Q(classification_result='productive')),
                unproductive=Count('id', filter=Q(classification_result='unproductive'))
            )
            
            return {
                'total_emails': total_classifications,
                'productive_emails': stats['productive'] or 0,
                'unproductive_emails': stats['unproductive'] or 0,
                'neutral_emails': 0,
            }
            
        except Exception as e:
            logger.error(f"Erro ao calcular estatísticas: {e}")
            return {
                'total_emails': 0,
                'productive_emails': 0,
                'unproductive_emails': 0,
                'neutral_emails': 0,
            }
    
    def _get_timeline_data(self):
        """Obter dados de timeline dos últimos 7 dias."""
        try:
            from apps.classifier.models import Classification
            
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=6)
            
            labels = []
            data = []
            
            for i in range(7):
                date = start_date + timedelta(days=i)
                labels.append(date.strftime('%d/%m'))
                
                count = Classification.objects.filter(
                    processing_status='completed',
                    classified_at__date=date
                ).count()
                
                data.append(count)
            
            return {
                'labels': labels,
                'data': data
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter timeline: {e}")
            return {
                'labels': [],
                'data': []
            }
    
    def _get_confidence_distribution(self):
        """Obter distribuição de confiança."""
        try:
            from apps.classifier.models import Classification
            
            distributions = [0, 0, 0, 0, 0]
            
            classifications = Classification.objects.filter(
                processing_status='completed',
                confidence_score__isnull=False
            ).values_list('confidence_score', flat=True)
            
            for confidence in classifications:
                if confidence <= 0.2:
                    distributions[0] += 1
                elif confidence <= 0.4:
                    distributions[1] += 1
                elif confidence <= 0.6:
                    distributions[2] += 1
                elif confidence <= 0.8:
                    distributions[3] += 1
                else:
                    distributions[4] += 1
            
            return distributions
            
        except Exception as e:
            logger.error(f"Erro ao obter distribuição de confiança: {e}")
            return [0, 0, 0, 0, 0]
    
    def _get_recent_classifications(self):
        """Obter classificações recentes."""
        try:
            from apps.classifier.models import Classification
            
            recent = Classification.objects.filter(
                processing_status='completed'
            ).select_related('email').order_by('-classified_at')[:5]
            
            return list(recent)
            
        except Exception as e:
            logger.error(f"Erro ao obter classificações recentes: {e}")
            return []


class DashboardView(TemplateView):
    """Pagina do dashboard / Dashboard page."""
    template_name = 'classifier/dashboard.html'
    
    def get_context_data(self, **kwargs):  # ✅ CORRIGIR: estava "se" em vez de "self, **kwargs"
        context = super().get_context_data(**kwargs)
        
        try:
            # ✅ OBTER DADOS REAIS
            stats = self._get_initial_stats()
            timeline_data = self._get_timeline_data()
            confidence_data = self._get_confidence_distribution()
            recent_emails = self._get_recent_classifications()
            
            context.update({
                'title': 'Dashboard',
                'description': 'Visualização dos dados de classificação de emails.',
                'has_data': True,
                'stats': stats,
                # ✅ DADOS REAIS EM JSON
                'timeline_labels': json.dumps(timeline_data['labels']),
                'timeline_data': json.dumps(timeline_data['data']),
                'confidence_distribution': json.dumps(confidence_data),
                'recent_emails': recent_emails,
                'ai_stats': None,
                'system_status': 'success'
            })
            
        except Exception as e:
            logger.error(f"Erro ao carregar dashboard: {e}")
            context.update({
                'title': 'Dashboard',
                'description': 'Erro ao carregar dados do dashboard.',
                'has_data': False,
                'error_message': 'Dados indisponíveis no momento.',
                'stats': {'total_emails': 0, 'productive_emails': 0, 'unproductive_emails': 0, 'neutral_emails': 0},
                # ✅ ARRAYS VAZIOS EM JSON
                'timeline_labels': json.dumps([]),
                'timeline_data': json.dumps([]),
                'confidence_distribution': json.dumps([0, 0, 0, 0, 0]),
                'recent_emails': [],
                'ai_stats': None,
                'system_status': 'error'
            })

        return context
    
    # ✅ ADICIONAR TODOS OS MÉTODOS QUE ESTÃO FALTANDO
    def _get_initial_stats(self):
        """Obter estatísticas básicas das Classifications."""
        try:
            from apps.classifier.models import Classification
            
            total_classifications = Classification.objects.filter(processing_status='completed').count()

            stats = Classification.objects.filter(processing_status='completed').aggregate(
                productive=Count('id', filter=Q(classification_result='productive')),
                unproductive=Count('id', filter=Q(classification_result='unproductive'))
            )
            
            return {
                'total_emails': total_classifications,
                'productive_emails': stats['productive'] or 0,
                'unproductive_emails': stats['unproductive'] or 0,
                'neutral_emails': 0,
            }
            
        except Exception as e:
            logger.error(f"Erro ao calcular estatísticas: {e}")
            return {
                'total_emails': 0,
                'productive_emails': 0,
                'unproductive_emails': 0,
                'neutral_emails': 0,
            }
    
    def _get_timeline_data(self):
        """Obter dados de timeline dos últimos 7 dias."""
        try:
            from apps.classifier.models import Classification
            
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=6)
            
            labels = []
            data = []
            
            for i in range(7):
                date = start_date + timedelta(days=i)
                labels.append(date.strftime('%d/%m'))
                
                count = Classification.objects.filter(
                    processing_status='completed',
                    classified_at__date=date
                ).count()
                
                data.append(count)
            
            return {
                'labels': labels,
                'data': data
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter timeline: {e}")
            return {
                'labels': [],
                'data': []
            }
    
    def _get_confidence_distribution(self):
        """Obter distribuição de confiança."""
        try:
            from apps.classifier.models import Classification
            
            distributions = [0, 0, 0, 0, 0]
            
            classifications = Classification.objects.filter(
                processing_status='completed',
                confidence_score__isnull=False
            ).values_list('confidence_score', flat=True)
            
            for confidence in classifications:
                if confidence <= 0.2:
                    distributions[0] += 1
                elif confidence <= 0.4:
                    distributions[1] += 1
                elif confidence <= 0.6:
                    distributions[2] += 1
                elif confidence <= 0.8:
                    distributions[3] += 1
                else:
                    distributions[4] += 1
            
            return distributions
            
        except Exception as e:
            logger.error(f"Erro ao obter distribuição de confiança: {e}")
            return [0, 0, 0, 0, 0]
    
    def _get_recent_classifications(self):
        """Obter classificações recentes."""
        try:
            from apps.classifier.models import Classification
            
            recent = Classification.objects.filter(
                processing_status='completed'
            ).select_related('email').order_by('-classified_at')[:5]
            
            return list(recent)
            
        except Exception as e:
            logger.error(f"Erro ao obter classificações recentes: {e}")
            return []

class ResultsView(TemplateView):
    """Pagina de resultado / Result page."""
    template_name = 'classifier/results.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Resultado da Classificação'
        context['description'] = 'Visualização dos resultado da classificação de emails.'
        context['api_endpoint'] = '/api/classifier/classifications/'
        return context

class HistoryView(TemplateView):
    """Pagina de histórico / History page."""
    template_name = 'classifier/history.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Histórico'
        context['description'] = 'Visualização do histórico de classificações de emails.'
        context['api_endpoint'] = '/api/classifier/classifications/'
        return context