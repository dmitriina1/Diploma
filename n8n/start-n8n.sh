#!/bin/sh

# Запуск n8n в фоне
n8n start &
N8N_PID=$!

# Ждём пока n8n запустится
echo "⏳ Waiting for n8n to start..."
sleep 15

# Импортируем и активируем workflow
echo "📦 Importing workflow..."
n8n import:workflow --input=/home/node/workflows/youtube-questions.json --activate 2>/dev/null || true
echo "✅ Workflow imported!"

# Ждём завершения n8n
wait $N8N_PID
