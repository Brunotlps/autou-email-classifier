#!/bin/bash
echo "🎨 TESTANDO CSS MINIMALISTA..."

# Fazer backup dos arquivos originais
echo "📦 Criando backup dos CSS originais..."
cp static/css/main.css static/css/main_original.css.backup
cp static/css/dashboard.css static/css/dashboard_original.css.backup
cp static/css/upload.css static/css/upload_original.css.backup

# Aplicar versões minimalistas
echo "✨ Aplicando versões minimalistas..."
cp static/css/main_minimal.css static/css/main.css
cp static/css/dashboard_minimal.css static/css/dashboard.css
cp static/css/upload_minimal.css static/css/upload.css

echo "✅ CSS MINIMALISTA APLICADO!"
echo ""
echo "🧪 Para testar:"
echo "   1. Acesse: http://localhost:8000/"
echo "   2. Teste upload: http://localhost:8000/upload/"
echo "   3. Verifique dashboard: http://localhost:8000/dashboard/"
echo ""
echo "📋 Para reverter se não gostar:"
echo "   ./revert_css.sh"
echo ""
echo "📋 Para manter se gostar:"
echo "   rm static/css/*_original.css.backup"
echo "   rm static/css/*_minimal.css"
