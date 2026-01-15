#!/bin/bash
echo "========================================"
echo "  Interview Prep - Запуск системы"
echo "========================================"
echo

# Проверяем Docker
if ! command -v docker &> /dev/null; then
    echo "[ERROR] Docker не установлен!"
    exit 1
fi

echo "[1/4] Останавливаем старые контейнеры..."
docker-compose down --remove-orphans 2>/dev/null

echo "[2/4] Собираем образы..."
docker-compose build

echo "[3/4] Запускаем базовые сервисы..."
docker-compose up -d postgres redis
echo "Ждем запуска базы данных..."
sleep 10

echo "[4/4] Запускаем остальные сервисы..."
docker-compose up -d

echo
echo "========================================"
echo "  Система запущена!"
echo "========================================"
echo
echo "  Frontend:  http://localhost:3000"
echo "  Backend:   http://localhost:8000"
echo "  n8n:       http://localhost:5678"
echo "  Ollama:    http://localhost:11434"
echo
echo "  Логи: docker-compose logs -f"
echo "  Остановка: docker-compose down"
echo "========================================"
