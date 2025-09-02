#!/bin/bash

echo "🚀 DEPLOY PRODUÇÃO - AUTOU EMAIL CLASSIFIER"

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

# Verificar se .env existe
if [ ! -f ".env" ]; then
    print_warning "Criando arquivo .env..."
    cat > .env << 'ENVEOF'
SECRET_KEY=django-insecure-change-this-in-production-$(openssl rand -hex 32)
DB_PASSWORD=secure_db_password_$(openssl rand -hex 16)
REDIS_PASSWORD=secure_redis_password_$(openssl rand -hex 16)
ENVEOF
    print_success "✅ Arquivo .env criado. EDITE AS SENHAS!"
fi

# Carregar variáveis
set -a
source .env
set +a

# Verificar Docker
if ! docker info >/dev/null 2>&1; then
    print_error "Docker não está rodando"
    exit 1
fi

# Parar containers existentes
print_status "Parando containers existentes..."
docker compose -f docker-compose.production.yml down

# Build das imagens
print_status "Construindo imagens de produção..."
docker compose -f docker-compose.production.yml build --no-cache

# Iniciar banco e Redis primeiro
print_status "Iniciando banco de dados e Redis..."
docker compose -f docker-compose.production.yml up -d db redis

# Aguardar banco ficar pronto
print_status "Aguardando banco de dados..."
sleep 20

# Executar migrações
print_status "Executando migrações..."
docker compose -f docker-compose.production.yml run --rm web python manage.py migrate

# Coletar estáticos
print_status "Coletando arquivos estáticos..."
docker compose -f docker-compose.production.yml run --rm web python manage.py collectstatic --noinput

# Criar superuser se não existir
print_status "Verificando superuser..."
docker compose -f docker-compose.production.yml run --rm web python manage.py shell << 'PYEOF'
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@autou.com', 'admin123')
    print('✅ Superuser criado: admin/admin123')
else:
    print('✅ Superuser já existe')
PYEOF

# Iniciar todos os serviços
print_status "Iniciando todos os serviços..."
docker compose -f docker-compose.production.yml up -d

# Aguardar inicialização
print_status "Aguardando inicialização completa..."
sleep 30

# Verificar saúde dos serviços
print_status "Verificando saúde dos serviços..."
docker compose -f docker-compose.production.yml ps

# Testar aplicação
print_status "Testando aplicação..."
for i in {1..10}; do
    if curl -f http://localhost/ >/dev/null 2>&1; then
        print_success "✅ APLICAÇÃO FUNCIONANDO!"
        break
    else
        if [ $i -eq 10 ]; then
            print_error "❌ Aplicação não respondeu"
            docker compose -f docker-compose.production.yml logs web
            exit 1
        fi
        print_warning "Tentativa $i/10..."
        sleep 5
    fi
done

echo ""
print_success "🎉 DEPLOY DE PRODUÇÃO CONCLUÍDO!"
echo ""
print_success "🌐 APLICAÇÃO DISPONÍVEL:"
echo "   🏠 Frontend: http://localhost/"
echo "   🔧 Admin:    http://localhost/admin/ (admin/admin123)"
echo "   📖 API:      http://localhost/api/docs/"
echo ""
print_success "📊 MONITORAMENTO:"
echo "   docker compose -f docker-compose.production.yml logs -f web"
echo "   docker compose -f docker-compose.production.yml ps"
echo "   docker compose -f docker-compose.production.yml exec web python manage.py shell"
echo ""
print_warning "⚠️ LEMBRE-SE:"
echo "   - Editar senhas no arquivo .env"
echo "   - Configurar domínio em ALLOWED_HOSTS"
echo "   - Configurar SSL/HTTPS para produção"
