# Script para reiniciar frontends limpiamente
Write-Host "🔄 Reiniciando frontends..." -ForegroundColor Cyan

# Detener procesos existentes
Write-Host "⏹️  Deteniendo procesos..." -ForegroundColor Yellow
Get-Process -Name "node" -ErrorAction SilentlyContinue | Where-Object { $_.Path -like "*frontend*" } | Stop-Process -Force

# Limpiar caché de node_modules/.vite
Write-Host "🧹 Limpiando caché de Vite..." -ForegroundColor Yellow
Remove-Item -Path "frontend/admin/node_modules/.vite" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "frontend/advisor/node_modules/.vite" -Recurse -Force -ErrorAction SilentlyContinue

# Esperar un momento
Start-Sleep -Seconds 2

# Iniciar admin frontend
Write-Host "🚀 Iniciando Admin Frontend..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd 'frontend/admin'; npm run dev"

# Esperar un momento
Start-Sleep -Seconds 2

# Iniciar advisor frontend
Write-Host "🚀 Iniciando Advisor Frontend..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd 'frontend/advisor'; npm run dev"

Write-Host "✅ Frontends reiniciados. Recuerda hacer Ctrl+Shift+R en el navegador." -ForegroundColor Green
