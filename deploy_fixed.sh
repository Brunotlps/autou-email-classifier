#!/bin/bash

echo "🚀 DEPLOY DOCKER CORRIGIDO - AUTOU EMAIL CLASSIFIER"

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Verificar Docker
print_status "Verificando Docker..."
if ! docker info >/dev/null 2>&1; then
    print_error "Docker não está rodando. Iniciando..."
    sudo systemctl start docker
    sleep 5
fi

# Usar Docker Compose v2 syntax
COMPOSE_CMD="docker-compose"
if command -v docker compose &> /dev/null; then
    COMPOSE_CMD="docker compose"
fi

print_status "Usando comando: $COMPOSE_CMD"

# Parar containers
print_status "Parando containers..."
$COMPOSE_CMD down 2>/dev/null || true

# Build apenas se necessário
print_status "Construindo imagem..."
$COMPOSE_CMD build web

# Iniciar em background
print_status "Iniciando containers..."
$COMPOSE_CMD up -d

# Aguardar e verificar
print_status "Aguardando inicialização..."
sleep 10

# Verificar logs
print_status "Verificando logs..."
$COMPOSE_CMD logs web

# Verificar se está rodando
print_status "Verificando containers..."
$COMPOSE_CMD ps

# Testar aplicação
print_status "Testando aplicação..."
for i in {1..5}; do
    if curl -f http://localhost:8000/ >/dev/null 2>&1; then
        print_success "✅ APLICAÇÃO FUNCIONANDO!"
        break
    else
        print_warning "Tentativa $i/5..."
        sleep 3
    fi
done

echo ""
print_success "🎉 DEPLOY CONCLUÍDO!"
echo ""
echo "🌐 URLs:"
echo "   http://localhost:8000/"
echo "   http://localhost:8000/dashboard/"
echo ""
echo "📋 Comandos úteis:"
echo "   $COMPOSE_CMD logs -f web    # Ver logs"
echo "   $COMPOSE_CMD down           # Parar"
echo "   $COMPOSE_CMD restart web    # Reiniciar"
