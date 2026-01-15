FROM python:3.11-slim

WORKDIR /app

# Установка минимальных зависимостей
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    xz-utils \
    && rm -rf /var/lib/apt/lists/*

# Установка ffmpeg статического бинарника
RUN curl -L https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz -o /tmp/ffmpeg.tar.xz \
    && tar -xf /tmp/ffmpeg.tar.xz -C /tmp \
    && mv /tmp/ffmpeg-*-amd64-static/ffmpeg /usr/local/bin/ \
    && mv /tmp/ffmpeg-*-amd64-static/ffprobe /usr/local/bin/ \
    && rm -rf /tmp/ffmpeg* \
    && chmod +x /usr/local/bin/ffmpeg /usr/local/bin/ffprobe

# Установка Python зависимостей - сначала CPU PyTorch
COPY requirements.txt .
RUN pip install --no-cache-dir --timeout 600 \
    torch torchaudio --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir --timeout 300 -r requirements.txt

COPY . .

# Порт сервиса
EXPOSE 8001

# Запуск
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
