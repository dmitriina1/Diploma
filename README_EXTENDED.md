# ДОПОЛНИТЕЛЬНАЯ ДОКУМЕНТАЦИЯ

Этот файл содержит расширенные секции, которые нужно добавить в основной README.md перед разделом "Вклад в проект".

---

## 🚀 Production Deployment Guide

### Подготовка к продакшену

#### 1. Изменение переменных окружения

Создайте `.env.production`:

```bash
# ============== PRODUCTION SETTINGS ==============
NODE_ENV=production
DEBUG=False
LOG_LEVEL=WARNING

# Database (используйте managed PostgreSQL: AWS RDS, DigitalOcean, etc.)
DATABASE_URL=postgresql://prod_user:strong_password_here@db-host.example.com:5432/interview_prep_prod

# Секретный ключ (генерировать: openssl rand -hex 32)
SECRET_KEY=your-secret-key-change-this-in-production-abc123...

# Домен
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
CORS_ORIGINS=https://yourdomain.com

# LLM (используйте платный аккаунт с высоким rate limit)
OPENROUTER_API_KEY=sk-or-v1-production-key...

# Whisper (если возможно - используйте GPU сервер)
WHISPER_DEVICE=cuda
WHISPER_MODEL=large-v3

# Rate Limiting
RATE_LIMIT_PER_MINUTE=30  # Строже, чем в dev
RATE_LIMIT_PER_HOUR=500

# Security
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

#### 2. Docker Compose для продакшена

Создайте `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  backend:
    image: ${DOCKER_HUB_USER}/interview-backend:${VERSION}
    restart: always
    env_file:
      - .env.production
    depends_on:
      - whisper-service
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: '2.0'
      replicas: 2  # Load balancing
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
  
  whisper-service:
    image: ${DOCKER_HUB_USER}/interview-whisper:${VERSION}
    restart: always
    environment:
      - WHISPER_MODEL=large-v3
      - WHISPER_DEVICE=cuda  # Требуется NVIDIA GPU
    deploy:
      resources:
        limits:
          memory: 8G
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    runtime: nvidia
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
      interval: 60s
      timeout: 30s
      retries: 3
  
  frontend:
    image: ${DOCKER_HUB_USER}/interview-frontend:${VERSION}
    restart: always
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '1.0'
      replicas: 2
  
  nginx:
    image: nginx:alpine
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.prod.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro  # SSL сертификаты
      - frontend_static:/usr/share/nginx/html:ro
    depends_on:
      - backend
      - frontend
    deploy:
      resources:
        limits:
          memory: 256M
  
  postgres:
    image: postgres:15-alpine
    restart: always
    environment:
      POSTGRES_DB: interview_prep_prod
      POSTGRES_USER: prod_user
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}  # Из secrets
    volumes:
      - postgres_prod_data:/var/lib/postgresql/data
      - ./scripts/init-db.sql:/docker-entrypoint-initdb.d/init.sql:ro
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: '2.0'
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U prod_user"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_prod_data:
  frontend_static:

networks:
  default:
    driver: bridge
```

#### 3. NGINX конфигурация для production

Создайте `nginx/nginx.prod.conf`:

```nginx
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 2048;
    use epoll;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    
    # Logging
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';
    access_log /var/log/nginx/access.log main;
    
    # Performance
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    client_max_body_size 500M;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml text/javascript 
               application/json application/javascript application/xml+rss 
               application/rss+xml font/truetype font/opentype 
               application/vnd.ms-fontobject image/svg+xml;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=upload_limit:10m rate=2r/m;
    
    # Upstream backend
    upstream backend_servers {
        least_conn;  # Load balancing
        server backend:8000 max_fails=3 fail_timeout=30s;
    }
    
    # Redirect HTTP → HTTPS
    server {
        listen 80;
        server_name yourdomain.com www.yourdomain.com;
        
        location /.well-known/acme-challenge/ {
            root /var/www/certbot;
        }
        
        location / {
            return 301 https://$server_name$request_uri;
        }
    }
    
    # HTTPS server
    server {
        listen 443 ssl http2;
        server_name yourdomain.com www.yourdomain.com;
        
        # SSL certificates
        ssl_certificate /etc/nginx/ssl/fullchain.pem;
        ssl_certificate_key /etc/nginx/ssl/privkey.pem;
        
        # SSL configuration (Mozilla Modern)
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_prefer_server_ciphers off;
        ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
        ssl_session_timeout 1d;
        ssl_session_cache shared:SSL:50m;
        ssl_session_tickets off;
        
        # HSTS
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
        
        # Frontend (статика)
        location / {
            root /usr/share/nginx/html;
            try_files $uri $uri/ /index.html;
            
            # Cache статики
            location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
                expires 1y;
                add_header Cache-Control "public, immutable";
            }
        }
        
        # API (rate limited)
        location /api/ {
            limit_req zone=api_limit burst=20 nodelay;
            
            proxy_pass http://backend_servers/api/;
            proxy_http_version 1.1;
            
            # Headers
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Timeouts
            proxy_connect_timeout 60s;
            proxy_send_timeout 600s;
            proxy_read_timeout 600s;
            
            # Buffering
            proxy_buffering on;
            proxy_buffer_size 4k;
            proxy_buffers 8 4k;
        }
        
        # Video upload (separate rate limit)
        location /api/process-video {
            limit_req zone=upload_limit burst=2 nodelay;
            
            proxy_pass http://backend_servers/api/process-video;
            proxy_http_version 1.1;
            
            # Большие таймауты для загрузки
            proxy_connect_timeout 120s;
            proxy_send_timeout 900s;
            proxy_read_timeout 900s;
            
            client_max_body_size 500M;
        }
        
        # Health check (без логирования)
        location /health {
            access_log off;
            proxy_pass http://backend_servers/health;
        }
    }
}
```

#### 4. SSL сертификаты (Let's Encrypt)

```bash
# Установить Certbot
sudo apt-get update
sudo apt-get install certbot python3-certbot-nginx

# Получить сертификат
sudo certbot certonly --nginx \
  -d yourdomain.com \
  -d www.yourdomain.com \
  --email your-email@example.com \
  --agree-tos \
  --no-eff-email

# Автообновление (добавить в crontab)
sudo crontab -e
# Добавить строку:
0 0 * * * certbot renew --quiet --post-hook "docker-compose -f docker-compose.prod.yml restart nginx"

# Скопировать сертификаты в проект
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ssl/
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ssl/
sudo chmod 644 ssl/*.pem
```

#### 5. Deploy на сервер

**Вариант А: Manual Deploy**

```bash
# На локальной машине - собрать и запушить образы
docker-compose -f docker-compose.prod.yml build
docker tag interview-backend:latest yourdockerhub/interview-backend:v1.0.0
docker tag interview-frontend:latest yourdockerhub/interview-frontend:v1.0.0
docker tag interview-whisper:latest yourdockerhub/interview-whisper:v1.0.0
docker push yourdockerhub/interview-backend:v1.0.0
docker push yourdockerhub/interview-frontend:v1.0.0
docker push yourdockerhub/interview-whisper:v1.0.0

# На сервере - подтянуть и запустить
ssh user@your-server.com
cd /var/www/interview-prep
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
docker-compose -f docker-compose.prod.yml logs -f
```

**Вариант Б: GitHub Actions CI/CD**

Создайте `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Production

on:
  push:
    branches: [ main ]
    tags: [ 'v*' ]

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2
      
      - name: Login to DockerHub
        uses: docker/login-action@v2
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}
      
      - name: Build and push Backend
        uses: docker/build-push-action@v4
        with:
          context: ./backend
          push: true
          tags: ${{ secrets.DOCKERHUB_USERNAME }}/interview-backend:${{ github.ref_name }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
      
      - name: Build and push Frontend
        uses: docker/build-push-action@v4
        with:
          context: ./frontend-vue
          push: true
          tags: ${{ secrets.DOCKERHUB_USERNAME }}/interview-frontend:${{ github.ref_name }}
      
      - name: Build and push Whisper
        uses: docker/build-push-action@v4
        with:
          context: ./whisper-service
          push: true
          tags: ${{ secrets.DOCKERHUB_USERNAME }}/interview-whisper:${{ github.ref_name }}
      
      - name: Deploy to server
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: ${{ secrets.SERVER_USER }}
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          script: |
            cd /var/www/interview-prep
            export VERSION=${{ github.ref_name }}
            docker-compose -f docker-compose.prod.yml pull
            docker-compose -f docker-compose.prod.yml up -d
            docker-compose -f docker-compose.prod.yml exec -T backend python migrate.py
```

#### 6. Мониторинг (Prometheus + Grafana)

Добавьте в `docker-compose.prod.yml`:

```yaml
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
    ports:
      - "9090:9090"
  
  grafana:
    image: grafana/grafana:latest
    volumes:
      - grafana_data:/var/lib/grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin123
    ports:
      - "3001:3000"
    depends_on:
      - prometheus

volumes:
  prometheus_data:
  grafana_data:
```

`monitoring/prometheus.yml`:

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'backend'
    static_configs:
      - targets: ['backend:8000']
  
  - job_name: 'whisper'
    static_configs:
      - targets: ['whisper-service:8001']
  
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres_exporter:9187']
```

#### 7. Backup стратегия

**Автоматический backup PostgreSQL**:

```bash
#!/bin/bash
# backup-db.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/postgres"
CONTAINER_NAME="postgres"
DB_NAME="interview_prep_prod"

# Создать backup
docker exec $CONTAINER_NAME pg_dump -U prod_user $DB_NAME | gzip > "$BACKUP_DIR/backup_$DATE.sql.gz"

# Удалить старые бэкапы (>7 дней)
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +7 -delete

# Загрузить в S3 (опционально)
aws s3 cp "$BACKUP_DIR/backup_$DATE.sql.gz" s3://your-bucket/backups/
```

**Добавить в crontab**:
```bash
0 2 * * * /path/to/backup-db.sh
```

---

## ❓ FAQ (Часто задаваемые вопросы)

### Общие вопросы

**Q: Можно ли использовать проект без LLM API ключа?**  
A: Нет, LLM критически необходим для извлечения вопросов из транскрипта. Используйте **Gemini** или **Groq** — оба бесплатные.

**Q: Сколько стоит запустить в production?**  
A: Минимальная конфигурация:
- VPS с GPU: $50-100/месяц (vast.ai, RunPod)
- Без GPU: $20-40/месяц (DigitalOcean, Hetzner)
- LLM API: $0.01-0.05 за видео (Gemini бесплатный)
- Домен: $10-15/год

**Q: Какая скорость обработки видео?**  
A: На CPU: ~0.3x realtime (10 мин видео = 30 мин обработки)  
На GPU: ~3x realtime (10 мин = 3 мин обработки)

**Q: Можно ли обрабатывать видео на других языках?**  
A: Да! Whisper поддерживает 50+ языков. Измените в `.env`:
```bash
WHISPER_LANGUAGE=en  # английский
WHISPER_LANGUAGE=auto  # автоопределение
```

---

### Технические вопросы

**Q: Почему Whisper large-v3 а не base/small?**  
A: Для русского языка large-v3 даёт значительно лучшее качество. Сравнение:
- `tiny`: 60-70% точность (много ошибок)
- `base`: 75-80% точность
- `small`: 85-90% точность
- `medium`: 90-93% точность
- `large-v3`: 95-98% точность ✅

**Q: Можно ли использовать оригинальный Whisper вместо faster-whisper?**  
A: Можно, но faster-whisper в 4x быстрее и потребляет меньше памяти при той же точности.

 **Q: Почему PostgreSQL а не MongoDB?**  
A:  
1. pgvector для embeddings (отлично работает для semantic search)
2. ACID транзакции (важно для модерации)
3. Сложные JOIN запросы (вопросы + видео + статистика)
4. Бесплатные managed solutions (AWS RDS, DigitalOcean)

**Q: Что делать если YouTube блокирует IP (HTTP 429)?**  
A: 3 решения:
1. Скачивать только русские субтитры (`subtitleslangs: ['ru']`) ✅ уже исправлено
2. Использовать VPN/proxy
3. Делать паузы между обработкой (15-20 минут)

**Q: Можно ли добавить поддержку Twitch/TikTok?**  
A: yt-dlp поддерживает 1000+ сайтов. Для Twitch/TikTok работает из коробки:
```python
# Просто передать URL
video_url = "https://www.twitch.tv/videos/1234567890"
video_url = "https://www.tiktok.com/@username/video/1234567890"
```

---

### Производительность

**Q: Почему Whisper использует 100% CPU?**  
A: Это нормально во время транскрипции! Whisper — вычислительно тяжёлая модель.

**Q: Как ускорить обработку?**  
A: 4 способа:
1. **GPU** (в 10x быстрее) - лучший вариант
2. Меньшая модель (`medium` вместо `large-v3`) - 3x быстрее
3. Увеличить `CPU_THREADS` в docker-compose.yml
4. Несколько параллельных workers (`MAX_CONCURRENT_TASKS=4`)

**Q: Сколько RAM нужно?**  
A: Минимум 8GB, рекомендуется 16GB:
- Whisper large-v3: ~3GB
- PostgreSQL: ~2GB
- Backend: ~2GB
- Frontend + nginx: ~1GB
- Резерв: ~2GB

**Q: Можно ли запустить на Raspberry Pi?**  
A: Нет, Whisper large-v3 слишком тяжёлая модель для ARM процессоров. Минимум нужен x86 CPU с 8+ ядрами.

---

### Deployment

**Q: Как deploy на AWS/GCP/Azure?**  
A: Используйте managed Kubernetes (EKS/GKE/AKS) или Container services (ECS/Cloud Run/Container Instances):

**AWS ECS**:
```bash
# 1. Создать ECR репозитории
aws ecr create-repository --repository-name interview-backend
aws ecr create-repository --repository-name interview-frontend
aws ecr create-repository --repository-name interview-whisper

# 2. Push образы
docker tag interview-backend:latest 123456.dkr.ecr.us-east-1.amazonaws.com/interview-backend:latest
docker push 123456.dkr.ecr.us-east-1.amazonaws.com/interview-backend:latest

# 3. Создать ECS task definition и service
aws ecs create-service --cli-input-json file://ecs-service.json
```

**Google Cloud Run** (самый простой):
```bash
# Deploy backend
gcloud run deploy interview-backend \
  --image gcr.io/your-project/interview-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 4Gi \
  --cpu 2

# Deploy frontend
gcloud run deploy interview-frontend \
  --image gcr.io/your-project/interview-frontend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

**Q: Нужен ли Kubernetes?**  
A: Для маленького проекта (<1000 пользователей) — НЕТ. Docker Compose достаточно.  
Kubernetes имеет смысл при:
- 1000+ одновременных пользователей
- Multi-region deployment
- Auto-scaling по нагрузке

---

### Безопасность

**Q: Как защитить админ-панель?**  
A: Добавить JWT authentication:

```python
# backend/auth.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

security = HTTPBearer()

def verify_admin(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        if payload.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Not authorized")
        return payload
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

# Использование в endpoints:
@app.post("/api/process-video")
async def process_video(video_url: str, admin = Depends(verify_admin)):
    # Только для админов
    ...
```

**Q: Как защититься от DDOS?**  
A: 3 уровня защиты:
1. **CloudFlare** (бесплатный plan) - автоматическая защита
2. **Rate limiting в nginx** (уже настроен в prod конфиге)
3. **Fail2Ban** на сервере

**Q: Где хранить API ключи в production?**  
A: НЕ в .env файле! Используйте:
- **AWS Secrets Manager**
- **Google Cloud Secret Manager**
- **HashiCorp Vault**
- **Environment variables** в Docker/Kubernetes

---

### Кастомизация

**Q: Как изменить дизайн фронтенда?**  
A: Все стили в `frontend-vue/src/App.css` и компонентах. Используется CSS variables:

```css
/* Изменить цветовую схему */
:root {
  --primary-color: #667eea;  /* Синий → ваш цвет */
  --secondary-color: #764ba2;
  --background: #0f172a;
  --card-bg: rgba(255, 255, 255, 0.1);
}
```

**Q: Как добавить новое поле в вопросы (например, "video_timestamp")?**  
A: 3 шага:

1. **Миграция БД**:
```sql
-- scripts/migration_add_timestamp.sql
ALTER TABLE questions ADD COLUMN video_timestamp INTEGER;
CREATE INDEX idx_timestamp ON questions(video_timestamp);
```

2. **Backend обновление**:
```python
# backend/main_new.py
async def save_question(..., timestamp: int = None):
    await db.execute("""
        INSERT INTO questions (..., video_timestamp)
        VALUES (..., $10)
    """, ..., timestamp)
```

3. **Frontend отображение**:
```vue
<!-- frontend-vue/src/components/QuestionCard.vue -->
<div v-if="question.video_timestamp">
  ⏱️ Timestamp: {{ formatTime(question.video_timestamp) }}
</div>
```

**Q: Как добавить экспорт в Anki?**  
A: Создать новый endpoint:

```python
@app.get("/api/export/anki")
async def export_anki(technology: str | None = None):
    questions = await db.fetch("""
        SELECT question_text as front, answer_text as back
        FROM questions
        WHERE status = 'approved'
        AND ($1::text IS NULL OR technology = $1)
    """, technology)
    
    # Генерация Anki deck (формат .apkg)
    import genanki
    deck = genanki.Deck(2059400110, f"Interview Questions - {technology}")
    
    model = genanki.Model(...)  # Определить модель карточки
    
    for q in questions:
        note = genanki.Note(
            model=model,
            fields=[q['front'], q['back']]
        )
        deck.add_note(note)
    
    deck.write_to_file(f'/tmp/deck_{technology}.apkg')
    return FileResponse(f'/tmp/deck_{technology}.apkg')
```

---

### Troubleshooting Advanced

**Q: Backend зависает на больших видео (>2 часа)**  
A: Увеличить таймауты:

```python
# backend/main_new.py
whisper_client = httpx.AsyncClient(
    timeout=3600.0  # 1 час вместо 10 минут
)

# docker-compose.yml
backend:
  environment:
    - TASK_TIMEOUT=7200  # 2 часа
```

**Q: PostgreSQL падает с "too many connections"**  
A: Увеличить connection pool:

```python
# backend/main_new.py
pool = await asyncpg.create_pool(
    DATABASE_URL,
    min_size=5,
    max_size=50  # Было 20
)
```

**Q: Whisper выдаёт gibberish (бессмыслица) на некоторых видео**  
A: 2 причины:
1. **Плохое качество аудио** → фильтровать видео с низким bitrate
2. **Неправильный язык** → использовать `language='auto'` вместо `ru`

**Q: LLM извлекает слишком мало вопросов**  
A: Проблема в промпте. Улучшить:

```python
EXTRACTION_PROMPT = """
...
ВАЖНО: Извлеки ВСЕ вопросы, даже короткие или простые.
НЕ ПРОПУСКАЙ вопросы, которые кажутся очевидными.
Минимум: извлеки хотя бы 10-15 вопросов из часового видео.
...
"""
```

**Q: Frontend не обновляется после деплоя новой версии**  
A: Проблема с кэшированием. Решения:

1. **Добавить версию в build**:
```javascript
// vite.config.js
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        entryFileNames: `assets/[name]-[hash]-${Date.now()}.js`,
        chunkFileNames: `assets/[name]-[hash]-${Date.now()}.js`,
      }
    }
  }
})
```

2. **Service Worker cache busting**:
```javascript
// frontend-vue/public/service-worker.js
const CACHE_VERSION = 'v1.0.1';  // Увеличивать при деплое
```

3. **nginx cache headers**:
```nginx
location /index.html {
    add_header Cache-Control "no-cache, must-revalidate";
}
```

---

## 📊 Performance Tuning

### Database Optimization

**1. Explain Analyze для медленных запросов**:

```sql
-- Найти медленные запросы
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;

-- Analyze конкретный запрос
EXPLAIN (ANALYZE, BUFFERS) 
SELECT * FROM questions 
WHERE technology = 'JavaScript' AND status = 'approved';
```

**2. Индексы для частых запросов**:

```sql
-- Composite index для фильтров
CREATE INDEX idx_questions_tech_status ON questions(technology, status);

-- Partial index (только approved)
CREATE INDEX idx_approved_questions ON questions(technology) 
WHERE status = 'approved';

-- GIN index для full-text search
CREATE INDEX idx_question_text_search ON questions 
USING GIN(to_tsvector('russian', question_text));
```

**3. Connection Pooling**:

```python
# backend/main_new.py
import asyncpg

async def init_db_pool():
    return await asyncpg.create_pool(
        DATABASE_URL,
        min_size=10,
        max_size=50,
        max_queries=50000,
        max_inactive_connection_lifetime=300
    )

pool = await init_db_pool()

# Использование
async with pool.acquire() as connection:
    await connection.fetch("SELECT * FROM questions")
```

### Caching Strategy

**1. Redis для кэширования API responses**:

```python
import redis.asyncio as redis
import json

redis_client = redis.from_url("redis://redis:6379")

async def get_questions_cached(technology: str):
    cache_key = f"questions:{technology}"
    
    # Проверить кэш
    cached = await redis_client.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # Запрос к БД
    questions = await db.fetch(...)
    
    # Сохранить в кэш (TTL 5 минут)
    await redis_client.setex(
        cache_key,
        300,
        json.dumps(questions)
    )
    
    return questions
```

**2. Cache invalidation при обновлении**:

```python
@app.patch("/api/questions/{id}/approve")
async def approve_question(id: int):
    # Одобрить вопрос
    await db.execute(...)
    
    # Инвалидировать кэш
    technology = await db.fetchval("SELECT technology FROM questions WHERE id = $1", id)
    await redis_client.delete(f"questions:{technology}")
    await redis_client.delete("questions:all")
    
    return {"status": "approved"}
```

### Frontend Optimization

**1. Code splitting**:

```javascript
// frontend-vue/src/router/index.js
const routes = [
  {
    path: '/admin',
    component: () => import(/* webpackChunkName: "admin" */ '../views/Admin.vue')
  },
  {
    path: '/questions/:id',
    component: () => import(/* webpackChunkName: "detail" */ '../views/QuestionDetail.vue')
  }
]
```

**2. Lazy loading images**:

```vue
<template>
  <img 
    v-lazy="question.video_thumbnail" 
    alt="Video thumbnail"
    @error="handleImageError"
  />
</template>

<script setup>
import { directive as vLazy } from 'vue3-lazy'
</script>
```

**3. Virtual scrolling для длинных списков**:

```vue
<template>
  <RecycleScroller
    :items="questions"
    :item-size="200"
    key-field="id"
  >
    <template #default="{ item }">
      <QuestionCard :question="item" />
    </template>
  </RecycleScroller>
</template>

<script setup>
import { RecycleScroller } from 'vue-virtual-scroller'
import 'vue-virtual-scroller/dist/vue-virtual-scroller.css'
</script>
```

---

## 🔍 Monitoring & Analytics

### Application Metrics

**1. Prometheus metrics в FastAPI**:

```python
# backend/main_new.py
from prometheus_client import Counter, Histogram, Gauge, make_asgi_app
import time

# Metrics
videos_processed = Counter('videos_processed_total', 'Total videos processed')
questions_extracted = Counter('questions_extracted_total', 'Total questions extracted')
processing_time = Histogram('video_processing_seconds', 'Video processing time')
active_tasks = Gauge('active_processing_tasks', 'Number of active tasks')

@app.post("/api/process-video")
async def process_video(video_url: str):
    start_time = time.time()
    active_tasks.inc()
    
    try:
        # Process video...
        result = await process_video_pipeline(video_url)
        
        videos_processed.inc()
        questions_extracted.inc(result['questions_count'])
        
        return result
    finally:
        processing_time.observe(time.time() - start_time)
        active_tasks.dec()

# Expose metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)
```

**2. Grafana dashboards**:

Создайте `monitoring/grafana-dashboard.json`:

```json
{
  "dashboard": {
    "title": "Interview Prep Platform",
    "panels": [
      {
        "title": "Videos Processed",
        "targets": [
          {
            "expr": "rate(videos_processed_total[5m])"
          }
        ]
      },
      {
        "title": "Processing Time (p95)",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, video_processing_seconds_bucket)"
          }
        ]
      },
      {
        "title": "Active Tasks",
        "targets": [
          {
            "expr": "active_processing_tasks"
          }
        ]
      }
    ]
  }
}
```

### Error Tracking (Sentry)

```python
# backend/main_new.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn="https://your-sentry-dsn@sentry.io/project-id",
    integrations=[FastApiIntegration()],
    traces_sample_rate=0.1,  # 10% запросов
    environment="production"
)

# Автоматически ловит все ошибки
@app.post("/api/process-video")
async def process_video(video_url: str):
    try:
        # ...
    except Exception as e:
        sentry_sdk.capture_exception(e)
        raise
```

---

Эти секции нужно добавить в основной README.md перед разделом "Вклад в проект".
