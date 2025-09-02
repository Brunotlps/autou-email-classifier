FROM python:3.11-slim

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Definir diretório de trabalho
WORKDIR /app

# Copiar e instalar dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Instalar dj-database-url para Render
RUN pip install dj-database-url psycopg2-binary

# Copiar código da aplicação
COPY . .

# Criar diretórios necessários
RUN mkdir -p staticfiles media logs

# Coletar arquivos estáticos
RUN python manage.py collectstatic --noinput --settings=core.settings.render

# Expor porta (Render usa PORT environment variable)
EXPOSE $PORT

# Comando para iniciar aplicação
CMD gunicorn core.wsgi:application --host 0.0.0.0 --port $PORT --workers 3
