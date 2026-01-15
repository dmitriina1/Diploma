FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей для yt-dlp и ffmpeg
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Копируем requirements
COPY requirements.txt .

# Установка Python зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код
COPY . .

# Создаём папку для временных файлов
RUN mkdir -p /app/temp

# Запуск приложения
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
