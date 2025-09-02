#!/usr/bin/env bash
# Build script for Render.com

# Exit on error
set -o errexit

echo "🚀 Iniciando build para Render..."

# Install Python dependencies
echo "📦 Instalando dependências..."
pip install --upgrade pip
pip install -r requirements.txt

# Create directories
echo "📁 Criando diretórios..."
mkdir -p staticfiles media logs static templates

# Collect static files
echo "📦 Coletando arquivos estáticos..."
python manage.py collectstatic --noinput --settings=core.settings.render

# Run migrations (opcional - pode ser feito no primeiro deploy)
echo "🗄️ Executando migrações..."
python manage.py migrate --settings=core.settings.render || echo "⚠️ Falha nas migrações (normal no primeiro build)"

echo "✅ Build concluído com sucesso!"
