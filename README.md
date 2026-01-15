# 🎯 Interview Prep System

Система для подготовки к IT-собеседованиям на основе YouTube видео.

## 📋 Стек технологий (100% БЕСПЛАТНО)

| Компонент | Технология | Назначение |
|-----------|------------|------------|
| LLM | Ollama (llama3.2) | Извлечение вопросов |
| Speech-to-Text | Whisper (локальный) | Транскрибация аудио |
| Автоматизация | n8n | Оркестрация пайплайна |
| Backend | FastAPI + Python | API + WebSocket |
| Frontend | React | Интерфейс |
| База данных | PostgreSQL | Хранение данных |
| Очереди | Redis | Параллельная обработка |
| Контейнеризация | Docker Compose | Развёртывание |

## 🚀 Быстрый старт

### Требования
- Docker Desktop (Windows/Mac) или Docker + Docker Compose (Linux)
- 8GB RAM (минимум 4GB)
- 10GB свободного места на диске

### Запуск

**Windows:**
```bash
start.bat
```

**Linux/Mac:**
```bash
chmod +x start.sh
./start.sh
```

**Или вручную:**
```bash
docker-compose up -d
```

### Доступ
- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **n8n Dashboard:** http://localhost:5678
- **Ollama API:** http://localhost:11434

## 📁 Структура проекта

```
Diploma/
├── docker-compose.yml      # Конфигурация всех сервисов
├── start.bat              # Скрипт запуска (Windows)
├── stop.bat               # Скрипт остановки
├── README.md              # Документация
│
├── backend/               # FastAPI бэкенд
│   ├── Dockerfile
│   ├── requirements.txt
│   └── main.py           # Основной код API
│
├── frontend/              # React фронтенд
│   ├── Dockerfile
│   ├── package.json
│   ├── public/
│   │   └── index.html
│   └── src/
│       ├── index.js
│       └── App.js        # Основной компонент
│
├── n8n/
│   └── workflows/
│       └── youtube-questions.json  # Workflow для обработки
│
└── scripts/
    └── init-db.sql       # Инициализация БД
```

## 🔄 Как работает система

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Frontend  │────▶│   Backend   │────▶│    n8n      │
│   (React)   │◀────│  (FastAPI)  │◀────│  Workflow   │
└─────────────┘     └─────────────┘     └─────────────┘
      │                    │                   │
      │              WebSocket            ┌────┴────┐
      │              (прогресс)           │         │
      └──────────────────────────────────▶│  Redis  │
                                          │         │
                                          └────┬────┘
                                               │
                    ┌──────────────────────────┼──────────────────────────┐
                    │                          │                          │
              ┌─────▼─────┐             ┌──────▼──────┐            ┌──────▼──────┐
              │  yt-dlp   │             │   Whisper   │            │   Ollama    │
              │ (download)│             │ (transcribe)│            │   (LLM)     │
              └───────────┘             └─────────────┘            └─────────────┘
```

### Последовательность обработки:

1. **Пользователь** вводит YouTube URL и нажимает кнопку
2. **Frontend** отправляет запрос на Backend через REST API
3. **Backend** создаёт задачу в Redis и запускает n8n Webhook
4. **n8n Workflow** выполняет пайплайн:
   - Скачивает аудио (yt-dlp)
   - Транскрибирует (Whisper)
   - Извлекает вопросы (Ollama LLM)
   - Сохраняет результаты
5. **Backend** отправляет прогресс через **WebSocket**
6. **Frontend** отображает прогресс-бар и результаты

## ⚙️ API Endpoints

### REST API

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/` | Проверка статуса |
| GET | `/health` | Health check |
| POST | `/api/process-video` | Запуск обработки |
| POST | `/api/process-video/{client_id}` | Запуск с WebSocket |
| GET | `/api/task/{task_id}` | Статус задачи |
| GET | `/api/questions` | Список вопросов |

### WebSocket

```javascript
ws://localhost:8000/ws/{client_id}
```

Сообщения:
```json
{"type": "progress", "task_id": "...", "progress": 50, "step": "Транскрибация..."}
{"type": "result", "task_id": "...", "questions": [...], "video_title": "..."}
{"type": "error", "task_id": "...", "error": "..."}
```

## 🔧 Настройка

### Переменные окружения

**Backend:**
```env
DATABASE_URL=postgresql://diploma:diploma123@postgres:5432/interview_prep
REDIS_URL=redis://redis:6379
N8N_WEBHOOK_URL=http://n8n:5678/webhook/youtube-questions
OLLAMA_URL=http://ollama:11434
```

**Frontend:**
```env
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000
```

### Смена модели Ollama

Для более качественных результатов (требует больше RAM):

```bash
# Подключиться к контейнеру
docker exec -it diploma-ollama bash

# Скачать другую модель
ollama pull llama3:8b
ollama pull mistral
```

Затем изменить в `backend/main.py`:
```python
"model": "llama3:8b"  # вместо llama3.2:1b
```

## 📊 Параллельная обработка

Система поддерживает параллельную обработку запросов от разных клиентов:

1. Каждый клиент получает уникальный `client_id`
2. Задачи хранятся в Redis с привязкой к клиенту
3. WebSocket обеспечивает независимую доставку прогресса
4. n8n обрабатывает запросы параллельно

## 🐛 Troubleshooting

### Проблема: Долго запускается
```bash
# Проверьте загрузку модели Ollama
docker logs diploma-ollama-init
```

### Проблема: n8n workflow не работает
```bash
# Проверьте импорт
docker logs diploma-n8n-init

# Импортируйте вручную через UI: http://localhost:5678
```

### Проблема: Ошибки памяти
```bash
# Используйте меньшую модель
# В docker-compose.yml измените ollama-init:
curl -X POST http://ollama:11434/api/pull -d '{"name": "phi3:mini"}'
```

### Полный сброс
```bash
docker-compose down -v
docker-compose up -d
```

## 📚 Для диссертации

### Ключевые особенности системы:
1. **Open-source стек** — независимость от платных API
2. **Локальный деплой** — работа без интернета
3. **Масштабируемость** — параллельная обработка
4. **Real-time обновления** — WebSocket для прогресса
5. **Модульная архитектура** — легко заменить компоненты

### Сравнение с аналогами:
| Характеристика | Наша система | ChatGPT API | Другие |
|----------------|--------------|-------------|--------|
| Стоимость | Бесплатно | $0.002/1K токенов | Varies |
| Приватность | Локально | Облако | Облако |
| Кастомизация | Полная | Ограничена | Varies |

## 📝 Лицензия

MIT License — для учебных и исследовательских целей.

---

**Магистерская диссертация**  
09.04.02 Информационные системы и технологии  
2026
