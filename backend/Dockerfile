FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей для yt-dlp
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

# Установка Python зависимостей с кэшированием (BuildKit)
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt && \
    pip install --upgrade yt-dlp

# Копируем код
COPY . .

# Создаём папку для временных файлов
RUN mkdir -p /app/temp

# Запуск приложения
CMD ["uvicorn", "main_new:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
