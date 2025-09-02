FROM python:3.11-slim

# Instalar dependências do sistema necessárias
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Definir diretório de trabalho
WORKDIR /app

# Copiar requirements primeiro (para cache do Docker)
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo o projeto
COPY . .

# Criar diretórios necessários
RUN mkdir -p staticfiles logs media

# Coletar arquivos estáticos
RUN python manage.py collectstatic --noinput --settings=core.settings.docker

# Expor porta
EXPOSE 8000

# Comando para iniciar a aplicação
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000", "--settings=core.settings.docker"]
