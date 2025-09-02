FROM python:3.11-slim

# Variáveis de ambiente
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

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
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY . .

# Criar diretórios necessários
RUN mkdir -p staticfiles media logs

# ⚠️ REMOVER collectstatic do Dockerfile - será feito no build command
# RUN python manage.py collectstatic --noinput --settings=core.settings.render

# Expor porta
EXPOSE 8000

# Comando padrão (Render sobrescreve isso)
CMD ["gunicorn", "core.wsgi:application", "--host", "0.0.0.0", "--port", "8000"]
