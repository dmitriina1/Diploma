#!/bin/bash

# Entrypoint для Whisper сервиса
# Автоматически определяет количество инстансов и рассчитывает CPU_THREADS

set -e

echo "🚀 Starting Whisper Service entrypoint..."

# Ждём 10 секунд, чтобы все инстансы запустились и зарегистрировались в DNS
sleep 10

# Определяем количество Whisper инстансов через DNS
COUNT=$(python3 -c "
import socket
try:
    ips = socket.getaddrinfo('whisper', 8001, socket.AF_INET, socket.SOCK_STREAM)
    unique_ips = set(ip[4][0] for ip in ips)
    print(len(unique_ips))
except Exception as e:
    print(f'Error detecting pool size: {e}')
    print(1)
")

# Рассчитываем CPU_THREADS: 16 потоков / количество инстансов
CPU_THREADS=$((16 / COUNT))
if [ $CPU_THREADS -lt 1 ]; then
    CPU_THREADS=1
fi

echo "🔍 Detected $COUNT Whisper instances"
echo "📊 Calculated CPU_THREADS = 16 / $COUNT = $CPU_THREADS threads per instance"

# Устанавливаем переменную окружения
export CPU_THREADS=$CPU_THREADS

# Запускаем приложение
echo "🎯 Starting uvicorn with $CPU_THREADS CPU threads..."
exec uvicorn main:app --host 0.0.0.0 --port 8000