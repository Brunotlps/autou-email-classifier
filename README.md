# AutoU Email Classifier

Sistema inteligente de classificação de emails e geração de respostas automáticas usando Django REST Framework e Inteligência Artificial.

## 🎯 Objetivo

Automatizar a leitura e classificação de emails corporativos, categorizando-os como "Produtivo" ou "Improdutivo" e sugerindo respostas automáticas adequadas.

## 🚀 Tecnologias

- **Backend:** Python 3.10, Django 5.2, Django REST Framework
- **IA/ML:** Hugging Face Transformers, spaCy
- **Banco de Dados:** PostgreSQL (produção), SQLite (desenvolvimento)
- **Cache:** Redis
- **Containerização:** Docker, Docker Compose
- **Documentação API:** drf-spectacular (OpenAPI 3.0)

## 📋 Funcionalidades

- [x] Upload de arquivos (.txt, .pdf)
- [x] Inserção direta de texto
- [x] Classificação automática (Produtivo/Improdutivo)
- [x] Geração de respostas automáticas
- [x] API RESTful documentada
- [x] Interface web intuitiva

## 🔧 Instalação e Execução

### Pré-requisitos
- Python 3.10+
- Docker e Docker Compose
- Git

### Setup Local
```bash
# Clone o repositório
git clone https://github.com/seu-usuario/autou-email-classifier.git
cd autou-email-classifier

### Setup com Docker
```bash
# Build e execute
docker-compose up --build

# Acesse: http://localhost:8000
```

## 📖 Documentação da API

Após executar o projeto, acesse:
- Swagger UI: http://localhost:8000/api/docs/
- ReDoc: http://localhost:8000/api/redoc/

## 🧪 Testes

```bash
# Executar todos os testes
pytest

# Com coverage
pytest --cov=apps --cov-report=html
```

## 🚀 Deploy
Instruções de deploy para produção disponíveis em docs/deploy.md.

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

---

**Desenvolvido com ❤️ para o desafio técnico da AutoU**