#!/usr/bin/env pwsh
# Скрипт для мониторинга обработки видео

Write-Host "`n╔══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║     МОНИТОРИНГ ОБРАБОТКИ ВИДЕО (Live)       ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

Write-Host "📱 Запущен режим live-мониторинга" -ForegroundColor Green
Write-Host "   Нажмите Ctrl+C для остановки`n" -ForegroundColor Gray

$taskId = $args[0]

while ($true) {
    Clear-Host
    
    Write-Host "╔══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║     LIVE МОНИТОРИНГ - $(Get-Date -Format 'HH:mm:ss')      ║" -ForegroundColor Cyan
    Write-Host "╚══════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan
    
    # 1. Статус задачи
    Write-Host "📊 СТАТУС ЗАДАЧИ:" -ForegroundColor Yellow
    if ($taskId) {
        try {
            $task = Invoke-RestMethod -Uri "http://localhost:8000/api/task/$taskId" -TimeoutSec 2
            Write-Host "   ID: $($task.task_id)" -ForegroundColor White
            Write-Host "   Статус: " -NoNewline -ForegroundColor White
            if ($task.status -eq "completed") {
                Write-Host $task.status -ForegroundColor Green
            } elseif ($task.status -eq "failed") {
                Write-Host $task.status -ForegroundColor Red
            } else {
                Write-Host $task.status -ForegroundColor Yellow
            }
            Write-Host "   Прогресс: $($task.progress)%" -ForegroundColor Cyan
            if ($task.current_stage) {
                Write-Host "   Этап: $($task.current_stage)" -ForegroundColor Magenta
            }
            if ($task.error) {
                Write-Host "   Ошибка: $($task.error)" -ForegroundColor Red
            }
        } catch {
            Write-Host "   ❌ Не удалось получить статус" -ForegroundColor Red
        }
    } else {
        Write-Host "   Укажите task_id как параметр: .\monitor.ps1 <task_id>" -ForegroundColor Gray
    }
    
    Write-Host "`n🔧 BACKEND (последние 10 строк):" -ForegroundColor Yellow
    docker logs diploma-backend --tail 10 2>&1 | Select-Object -Last 10
    
    Write-Host "`n🤖 WHISPER (последние 5 строк):" -ForegroundColor Yellow
    docker logs diploma-whisper-worker --tail 5 2>&1 | Select-Object -Last 5
    
    Write-Host "`n💾 ИСПОЛЬЗОВАНИЕ РЕСУРСОВ:" -ForegroundColor Yellow
    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" diploma-backend diploma-whisper-worker
    
    Write-Host "`n[Обновление каждые 3 секунды. Ctrl+C для выхода]" -ForegroundColor Gray
    Start-Sleep 3
}
