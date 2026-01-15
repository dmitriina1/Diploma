#!/bin/sh

# Ждём запуска n8n
echo "⏳ Waiting for n8n to start..."
sleep 10

# Импортируем workflow
echo "📦 Importing workflow..."
n8n import:workflow --input=/home/node/workflows/youtube-questions.json

# Активируем workflow (получаем ID и активируем)
echo "🔄 Activating workflow..."
n8n update:workflow --id=1 --active=true 2>/dev/null || echo "Workflow activation will be done manually"

echo "✅ n8n initialization complete!"
