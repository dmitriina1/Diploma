# Переход на новую архитектуру v2.0

## ✅ Что изменилось

### 1. **Убран n8n**
- ❌ Удален контейнер n8n и все зависимости
- ✅ Весь pipeline обработки теперь напрямую в backend
- ✅ Упрощенная архитектура — меньше точек отказа

### 2. **Убрано разделение аудио на части**
- ❌ Удален WhisperPool с разделением аудио
- ✅ WhisperOrchestrator — каждый воркер обрабатывает ПОЛНОЕ аудио
- ✅ Лучшее качество транскрипции (нет потерь на стыках)

### 3. **Per-Task масштабирование**
- ✅ 1 Whisper воркер = 1 полная задача
- ✅ Если приходит еще задача → поднимается еще воркер
- ✅ Правильная модель масштабирования

### 4. **Оптимизация для AMD Ryzen 7, 32GB RAM**
- ✅ Whisper **large-v3** (лучшее качество)
- ✅ CPU_THREADS=10 (оптимально для R7)
- ✅ Максимум 2 воркера одновременно (28GB total)

---

## 🚀 Установка новой версии

### Шаг 1: Бэкап текущей версии (опционально)

```bash
# Создайте бэкап
cp docker-compose.yml docker-compose.old.yml
cp backend/main.py backend/main.old.py
cp whisper-service/main.py whisper-service/main.old.py
```

### Шаг 2: Замените файлы новыми версиями

```bash
# Docker Compose
mv docker-compose.new.yml docker-compose.yml

# Backend
mv backend/main_new.py backend/main.py

# Whisper Service
mv whisper-service/main_new.py whisper-service/main.py
mv whisper-service/Dockerfile.new whisper-service/Dockerfile
```

### Шаг 3: Удалите старые контейнеры

```bash
# Остановите и удалите все старые контейнеры
docker-compose down

# Опционально: удалите неиспользуемые volumes (ВНИМАНИЕ: удалит данные!)
# docker volume prune
```

### Шаг 4: Запустите новую версию

```bash
# Пересоберите образы
docker-compose build --no-cache

# Запустите контейнеры
docker-compose up -d

# Проверьте логи
docker-compose logs -f backend
docker-compose logs -f whisper-worker
```

---

## 📊 Проверка работоспособности

### 1. Проверьте health эндпоинты

```bash
# Backend
curl http://localhost:8000/health

# Whisper Worker
curl http://localhost:8001/health
```

### 2. Проверьте документацию API

Откройте в браузере: http://localhost:8000/docs

### 3. Отправьте тестовую задачу

```bash
curl -X POST http://localhost:8000/api/process-video \
  -H "Content-Type: application/json" \
  -d '{
    "youtube_url": "https://www.youtube.com/watch?v=XXXXX",
    "topic": "Backend",
    "level": "middle"
  }'
```

---

## 🔧 Настройки для вашей машины

### Для Lenovo Xiaoxin Pro 16 (R7, 32GB):

По умолчанию уже оптимизировано:
- `WHISPER_MODEL=large-v3` (лучшее качество)
- `CPU_THREADS=10` (оптимально)
- `MAX_WHISPER_WORKERS=2` (можно обрабатывать 2 видео одновременно)

### Если нужно изменить:

Отредактируйте `docker-compose.yml`:

```yaml
whisper-worker:
  environment:
    - WHISPER_MODEL=large-v3  # Модель: medium, large-v2, large-v3
    - CPU_THREADS=10          # Потоки: 8-12 для R7

backend:
  environment:
    - MAX_WHISPER_WORKERS=2   # Макс. воркеров: 1-2 для 32GB RAM
```

---

## 🆘 Troubleshooting

### Whisper воркер не запускается

```bash
# Проверьте логи
docker-compose logs whisper-worker

# Возможные причины:
# 1. Не хватает памяти → уменьшите CPU_THREADS или используйте medium модель
# 2. Не загружена модель → проверьте интернет соединение
```

### Backend не может подключиться к Whisper

```bash
# Проверьте что whisper-worker запущен
docker-compose ps

# Проверьте сеть
docker network inspect diploma_diploma-network
```

### Медленная транскрипция

```bash
# Увеличьте CPU_THREADS (не больше 12 для R7)
# Или используйте модель поменьше (medium вместо large-v3)
```

---

## 📈 Сравнение производительности

| Метрика | Старая версия | Новая версия |
|---------|--------------|--------------|
| **Качество транскрипции** | ⭐⭐⭐ (потери на стыках) | ⭐⭐⭐⭐⭐ (полное аудио) |
| **Скорость** | Быстрее на длинных видео | Оптимальная |
| **Использование RAM** | Меньше | Больше (~14GB на воркер) |
| **Сложность архитектуры** | Высокая (n8n + nginx + chunking) | Низкая (прямой pipeline) |
| **Надежность** | Средняя | Высокая |
| **Масштабируемость** | По частям аудио | По задачам ✅ |

---

## 🎯 Преимущества новой архитектуры

1. **Лучшее качество** — Whisper видит весь контекст аудио
2. **Проще код** — нет логики разрезания/склеивания
3. **Меньше багов** — меньше движущихся частей
4. **Честное масштабирование** — 1 воркер = 1 задача
5. **Убран n8n** — на одну зависимость меньше

---

## 🔄 Откат на старую версию

Если что-то пошло не так:

```bash
# Остановите контейнеры
docker-compose down

# Верните старые файлы
mv docker-compose.old.yml docker-compose.yml
mv backend/main.old.py backend/main.py
mv whisper-service/main.old.py whisper-service/main.py

# Запустите старую версию
docker-compose up -d
```

---

## 📞 Поддержка

Если возникли проблемы — проверьте логи:

```bash
# Все логи
docker-compose logs -f

# Только backend
docker-compose logs -f backend

# Только whisper
docker-compose logs -f whisper-worker
```
