"""
Script de debug para problemas no Render
"""

import os
import django
from django.conf import settings

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.render')
django.setup()

def debug_render():
    print("🔍 DEBUG RENDER - AutoU Email Classifier")
    print("=" * 50)
    
    # Verificar settings
    print(f"✅ DEBUG: {settings.DEBUG}")
    print(f"✅ SECRET_KEY: {'***' if settings.SECRET_KEY else 'NOT SET'}")
    print(f"✅ ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")
    print(f"✅ DATABASE: {settings.DATABASES['default']['ENGINE']}")
    
    # Verificar static files
    print(f"✅ STATIC_URL: {settings.STATIC_URL}")
    print(f"✅ STATIC_ROOT: {settings.STATIC_ROOT}")
    print(f"✅ STATICFILES_DIRS: {settings.STATICFILES_DIRS}")
    
    # Verificar apps
    print(f"✅ INSTALLED_APPS: {len(settings.INSTALLED_APPS)} apps")
    for app in settings.INSTALLED_APPS:
        if app.startswith('apps.'):
            print(f"   📱 {app}")
    
    # Verificar banco de dados
    from django.db import connection
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            print(f"✅ TABELAS NO BANCO: {len(tables)}")
            for table in tables:
                print(f"   📋 {table[0]}")
    except Exception as e:
        print(f"❌ ERRO NO BANCO: {e}")
    
    # Verificar modelos
    from apps.emails.models import Email
    try:
        count = Email.objects.count()
        print(f"✅ EMAILS NO BANCO: {count}")
    except Exception as e:
        print(f"❌ ERRO EMAILS: {e}")
    
    print("=" * 50)
    print("🎯 Para executar no Render Shell:")
    print("python debug_render.py")

if __name__ == "__main__":
    debug_render()
