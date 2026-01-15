FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей включая ffmpeg для yt-dlp
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    xz-utils \
    && rm -rf /var/lib/apt/lists/*

# Установка статического ffmpeg
RUN curl -L https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz -o /tmp/ffmpeg.tar.xz \
    && tar -xf /tmp/ffmpeg.tar.xz -C /tmp \
    && mv /tmp/ffmpeg-*-amd64-static/ffmpeg /usr/local/bin/ \
    && mv /tmp/ffmpeg-*-amd64-static/ffprobe /usr/local/bin/ \
    && rm -rf /tmp/ffmpeg*

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
