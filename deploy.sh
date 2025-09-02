#!/bin/bash

echo "🚀 AUTOU EMAIL CLASSIFIER - DEPLOY DOCKER SIMPLES"

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

# Verificar se Docker está funcionando
print_status "Verificando Docker..."
if ! docker info >/dev/null 2>&1; then
    print_error "Docker não está rodando. Inicie o Docker primeiro."
    exit 1
fi

# Verificar arquivos necessários
print_status "Verificando arquivos necessários..."
required_files=("Dockerfile" "docker-compose.yml" "requirements.txt" "manage.py" "core/settings/docker.py")

for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        print_error "Arquivo não encontrado: $file"
        exit 1
    fi
done

print_success "Todos os arquivos necessários encontrados!"

# Parar containers existentes
print_status "Parando containers existentes..."
docker compose down 2>/dev/null || true

# Build da aplicação
print_status "Construindo imagem Docker..."
docker compose build --no-cache

# Verificar se build foi bem-sucedido
if [ $? -ne 0 ]; then
    print_error "Falha no build da imagem Docker"
    exit 1
fi

print_success "Imagem construída com sucesso!"

# Iniciar containers
print_status "Iniciando containers..."
docker compose up -d

# Aguardar inicialização
print_status "Aguardando inicialização (30s)..."
sleep 30

# Executar migrações
print_status "Executando migrações..."
docker compose exec web python manage.py migrate --settings=core.settings.docker

# Criar superuser (opcional)
print_status "Criando superuser (admin/admin)..."
docker compose exec web python manage.py shell --settings=core.settings.docker << 'PYEOF'
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@autou.com', 'admin')
    print("✅ Superuser criado: admin/admin")
else:
    print("✅ Superuser já existe")
PYEOF

# Verificar se container está rodando
print_status "Verificando status do container..."
if docker compose ps | grep -q "Up"; then
    print_success "Container está rodando!"
else
    print_error "Container não está rodando. Verificando logs..."
    docker compose logs web
    exit 1
fi

# Testar aplicação
print_status "Testando aplicação..."
for i in {1..10}; do
    if curl -f http://localhost:8000/ >/dev/null 2>&1; then
        print_success "✅ APLICAÇÃO FUNCIONANDO!"
        break
    else
        if [ $i -eq 10 ]; then
            print_error "❌ Aplicação não respondeu após 10 tentativas"
            print_status "Logs da aplicação:"
            docker compose logs web
            exit 1
        fi
        print_warning "Tentativa $i/10..."
        sleep 5
    fi
done

echo ""
print_success "🎉 DEPLOY CONCLUÍDO COM SUCESSO!"
echo ""
echo "🌐 APLICAÇÃO DISPONÍVEL EM:"
echo "   🏠 Home:        http://localhost:8000/"
echo "   📊 Dashboard:   http://localhost:8000/dashboard/"
echo "   📤 Upload:      http://localhost:8000/upload/"
echo "   🔧 Admin:       http://localhost:8000/admin/ (admin/admin)"
echo "   📖 API Docs:    http://localhost:8000/api/docs/"
echo ""
echo "📋 COMANDOS ÚTEIS:"
echo "   docker compose logs -f web        # Ver logs em tempo real"
echo "   docker compose exec web bash      # Entrar no container"
echo "   docker compose down               # Parar aplicação"
echo "   docker compose up -d              # Iniciar aplicação"
echo ""
echo "🎯 TESTE RÁPIDO:"
echo "   curl http://localhost:8000/"
