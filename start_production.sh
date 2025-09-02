#!/bin/bash

echo "🚀 INICIANDO AUTOU EMAIL CLASSIFIER EM PRODUÇÃO"

# Cores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }

# Verificar se está no ambiente virtual
if [[ "$VIRTUAL_ENV" == "" ]]; then
    print_warning "⚠️ Ativando ambiente virtual..."
    source venv/bin/activate || {
        print_error "❌ Ambiente virtual não encontrado. Execute: python -m venv venv"
        exit 1
    }
fi

# Criar diretório de logs
print_status "📁 Criando diretório de logs..."
mkdir -p logs

# Variáveis de ambiente para produção
export DJANGO_SETTINGS_MODULE=core.settings.production
export PYTHONPATH="."

# Executar migrações
print_status "🗄️ Executando migrações..."
python manage.py migrate --noinput

# Coletar arquivos estáticos
print_status "📦 Coletando arquivos estáticos..."
python manage.py collectstatic --noinput

# Verificar configuração
print_status "🔍 Verificando configuração Django..."
python manage.py check --deploy

# Iniciar Gunicorn
print_status "🚀 Iniciando Gunicorn..."
print_success "✅ Servidor rodando em: http://localhost:8000"
print_success "📊 Logs de acesso: logs/gunicorn_access.log"
print_success "🐛 Logs de erro: logs/gunicorn_error.log"
print_warning "⚠️ Para parar: Ctrl+C ou kill -TERM \$(cat logs/gunicorn.pid)"

exec gunicorn core.wsgi:application \
    --config gunicorn_config.py \
    --env DJANGO_SETTINGS_MODULE=core.settings.production
