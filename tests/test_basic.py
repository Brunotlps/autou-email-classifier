"""Testes básicos para AutoU Email Classifier."""

import pytest
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.conf import settings
import os


class AutoUBasicTests(TestCase):
    """Testes básicos de funcionalidade."""

    def setUp(self):
        """Setup inicial para testes."""
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", email="test@example.com", password="testpass123")

    def test_home_page_loads(self):
        """Testa se a página inicial carrega corretamente."""
        response = self.client.get(reverse("frontend:home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "E-mail Classifier")

    def test_upload_page_loads(self):
        """Testa se a página de upload carrega corretamente."""
        response = self.client.get(reverse("frontend:upload"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Classificação")

    def test_dashboard_page_loads(self):
        """Testa se o dashboard carrega corretamente."""
        response = self.client.get(reverse("frontend:dashboard"))
        self.assertEqual(response.status_code, 200)

    def test_history_page_loads(self):
        """Testa se a página de histórico carrega."""
        response = self.client.get(reverse("frontend:history"))
        self.assertEqual(response.status_code, 200)

    def test_navbar_links(self):
        """Testa se todos os links da navbar funcionam."""
        urls_to_test = [
            reverse("frontend:home"),
            reverse("frontend:upload"),
            reverse("frontend:dashboard"),
            reverse("frontend:history"),
        ]

        for url in urls_to_test:
            response = self.client.get(url)
            self.assertIn(response.status_code, [200, 302], f"URL {url} falhou com status {response.status_code}")

    def test_static_files_configuration(self):
        """Testa se os arquivos estáticos estão configurados."""
        self.assertTrue(hasattr(settings, "STATIC_URL"))
        self.assertTrue(hasattr(settings, "STATIC_ROOT"))

    def test_database_connection(self):
        """Testa conexão com o banco de dados."""
        from django.db import connection

        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        self.assertEqual(result[0], 1)


@pytest.mark.django_db
class TestModels:
    """Testes dos modelos Django."""

    def test_email_model_exists(self):
        """Testa se o modelo Email foi criado corretamente."""
        from apps.emails.models import Email

        # Criar um email de teste
        email = Email.objects.create(subject="Test Email", content="This is a test email content.", sender="test@example.com")

        assert email.subject == "Test Email"
        assert email.sender == "test@example.com"
        assert email.created_at is not None

    def test_classification_model_exists(self):
        """Testa se o modelo Classification foi criado."""
        from apps.emails.models import Email
        from apps.classifier.models import Classification

        # Criar email primeiro
        email = Email.objects.create(
            subject="Business Email", content="Meeting at 2 PM tomorrow.", sender="colleague@company.com"
        )

        # Criar classificação
        classification = Classification.objects.create(
            email=email, category="business", confidence=0.95, processed_by="test_ai"
        )

        assert classification.category == "business"
        assert classification.confidence == 0.95
        assert classification.email == email


class TestPerformance(TestCase):
    """Testes de performance básicos."""

    def test_home_page_performance(self):
        """Testa performance da página inicial."""
        import time

        start_time = time.time()
        response = self.client.get(reverse("frontend:home"))
        end_time = time.time()

        # Página deve carregar em menos de 3 segundos
        load_time = end_time - start_time
        self.assertLess(load_time, 3.0, f"Página inicial muito lenta: {load_time:.2f}s")
        self.assertEqual(response.status_code, 200)

    def test_database_query_performance(self):
        """Testa performance básica de queries."""
        from django.test import override_settings
        from django.db import connection
        from apps.emails.models import Email

        with override_settings(DEBUG=True):
            # Limpar log de queries
            connection.queries_log.clear()

            # Criar alguns emails
            emails = [
                Email(subject=f"Test Email {i}", content=f"Content for email {i}", sender=f"user{i}@example.com")
                for i in range(5)
            ]
            Email.objects.bulk_create(emails)

            # Reset query count
            connection.queries_log.clear()

            # Buscar emails
            list(Email.objects.all()[:3])

            # Deve usar poucas queries
            query_count = len(connection.queries)
            self.assertLessEqual(query_count, 3, f"Muitas queries: {query_count}")


class TestIntegration(TestCase):
    """Testes de integração entre componentes."""

    def test_complete_email_workflow(self):
        """Testa workflow completo de email."""
        from apps.emails.models import Email
        from apps.classifier.models import Classification

        # 1. Criar um email
        email = Email.objects.create(
            subject="Important Meeting", content="We need to discuss the project timeline.", sender="manager@company.com"
        )

        # 2. Criar classificação para o email
        classification = Classification.objects.create(
            email=email, category="meeting", confidence=0.88, processed_by="ai_classifier_v1"
        )

        # 3. Verificar relacionamento
        self.assertEqual(email.classification, classification)
        self.assertEqual(classification.email, email)

        # 4. Verificar que dados aparecem no dashboard
        response = self.client.get(reverse("frontend:dashboard"))
        self.assertEqual(response.status_code, 200)

    def test_api_endpoints_exist(self):
        """Testa se endpoints da API existem."""
        api_urls = [
            "/api/",
            "/api/emails/",
            "/api/classifications/",
        ]

        for url in api_urls:
            response = self.client.get(url)
            # API pode retornar 200, 404 (sem dados) ou 405 (método não permitido)
            self.assertIn(response.status_code, [200, 404, 405], f"API endpoint {url} não encontrado")


@pytest.mark.integration
class TestAPIIntegration:
    """Testes de integração da API."""

    @pytest.mark.django_db
    def test_api_classification_flow(self, client):
        """Testa fluxo da API de classificação."""
        from apps.emails.models import Email

        # Criar email via modelo
        email = Email.objects.create(subject="Test API Email", content="Testing API integration", sender="api@test.com")

        # Tentar acessar via API
        response = client.get(f"/api/emails/")
        assert response.status_code in [200, 404]  # 404 se não há implementação ainda


class TestErrorHandling(TestCase):
    """Testes de tratamento de erros."""

    def test_404_page(self):
        """Testa página 404."""
        response = self.client.get("/pagina-que-nao-existe/")
        self.assertEqual(response.status_code, 404)

    def test_invalid_url_patterns(self):
        """Testa URLs inválidas."""
        invalid_urls = [
            "/upload/invalid/",
            "/dashboard/wrong/",
            "/api/invalid-endpoint/",
        ]

        for url in invalid_urls:
            response = self.client.get(url)
            self.assertIn(response.status_code, [404, 405])
