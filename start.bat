@echo off
echo ========================================
echo   Interview Prep - Запуск системы
echo ========================================
echo.

REM Проверяем Docker
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker не установлен!
    echo Скачайте Docker Desktop: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

echo [1/4] Останавливаем старые контейнеры...
docker-compose down --remove-orphans 2>nul

echo [2/4] Собираем образы...
docker-compose build

echo [3/4] Запускаем сервисы...
docker-compose up -d postgres redis

echo Ждем запуска базы данных...
timeout /t 10 /nobreak >nul

echo [4/4] Запускаем остальные сервисы...
docker-compose up -d

echo.
echo ========================================
echo   Система запущена!
echo ========================================
echo.
echo   Frontend:  http://localhost:3000
echo   Backend:   http://localhost:8000
echo   n8n:       http://localhost:5678
echo   Ollama:    http://localhost:11434
echo.
echo   Первый запуск может занять 5-10 минут
echo   пока скачиваются модели Ollama и Whisper
echo.
echo   Логи: docker-compose logs -f
echo   Остановка: docker-compose down
echo ========================================

pause
