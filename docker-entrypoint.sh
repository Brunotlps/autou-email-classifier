#!/bin/bash
set -e

echo "AutoU Email Classifier - Starting Application..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Wait for database (if needed)
print_status "Checking database connection..."

# Run migrations
print_status "Running database migrations..."
python manage.py migrate --noinput || true
print_success "Database migrations completed!"

# Create superuser
print_status "Setting up superuser account..."
python manage.py shell << 'PYEOF'
from django.contrib.auth import get_user_model
import os

User = get_user_model()
username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@autou.com')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'admin123')

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username, email, password)
    print(f'Superuser created: {username}/{password}')
else:
    print(f'Superuser already exists: {username}')
PYEOF

# Collect static files
print_status "Collecting static files..."
python manage.py collectstatic --noinput || true
print_success "Static files collected!"

print_success "Application initialization completed!"
print_status "Starting application with command: $@"

# Execute the main command
exec "$@"
