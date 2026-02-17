#!/usr/bin/env pwsh
# Быстрые команды для мониторинга

Write-Host "`n╔══════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║     📋 КОМАНДЫ ДЛЯ МОНИТОРИНГА ОБРАБОТКИ     ║" -ForegroundColor Green
Write-Host "╚══════════════════════════════════════════════════════════╝`n" -ForegroundColor Green

Write-Host "1️⃣  Смотреть логи Backend (LIVE):" -ForegroundColor Cyan
Write-Host "   docker logs diploma-backend -f" -ForegroundColor White
Write-Host "`n2️⃣  Смотреть логи Whisper Worker (LIVE):" -ForegroundColor Cyan
Write-Host "   docker logs diploma-whisper-worker -f" -ForegroundColor White
Write-Host "`n3️⃣  Последние 50 строк Backend:" -ForegroundColor Cyan
Write-Host "   docker logs diploma-backend --tail 50" -ForegroundColor White
Write-Host "`n4️⃣  Статус задачи через API:" -ForegroundColor Cyan
Write-Host "   Invoke-RestMethod -Uri 'http://localhost:8000/api/task/<task_id>'" -ForegroundColor White
Write-Host "`n5️⃣  Использование ресурсов:" -ForegroundColor Cyan
Write-Host "   docker stats diploma-backend diploma-whisper-worker" -ForegroundColor White
Write-Host "`n6️⃣  Live мониторинг (автообновление):" -ForegroundColor Cyan
Write-Host "   .\monitor.ps1 <task_id>" -ForegroundColor White
Write-Host "`n7️⃣  Проверить что Whisper занят:" -ForegroundColor Cyan
Write-Host "   docker exec diploma-backend python -c 'import httpx, asyncio; asyncio.run(httpx.get(`"http://whisper-worker:8000/health`"))'" -ForegroundColor White
Write-Host "`n8️⃣  Открыть Swagger API:" -ForegroundColor Cyan
Write-Host "   http://localhost:8000/docs" -ForegroundColor White
Write-Host "`n" -ForegroundColor White
Write-Host "💡 ТИП: Используйте " -NoNewline -ForegroundColor Yellow
Write-Host "docker logs -f" -NoNewline -ForegroundColor White
Write-Host " для просмотра логов в реальном времени!" -ForegroundColor Yellow
Write-Host "   (Ctrl+C для выхода)`n" -ForegroundColor Gray
