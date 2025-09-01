#!/bin/bash
echo "🔄 REVERTENDO PARA CSS ORIGINAL..."

# Restaurar backups
cp static/css/main_original.css.backup static/css/main.css
cp static/css/dashboard_original.css.backup static/css/dashboard.css
cp static/css/upload_original.css.backup static/css/upload.css

echo "✅ CSS ORIGINAL RESTAURADO!"

# Limpar backups e experimentais
rm static/css/*_original.css.backup
rm static/css/*_minimal.css

echo "🧹 Arquivos temporários removidos"
