# Проект: Interview Prep — Система извлечения вопросов для IT-собеседований из YouTube

## 📋 Обзор проекта
**Цель**: Автоматизация подготовки к IT-собеседованиям путем извлечения и анализа вопросов из YouTube видео с записями реальных интервью.

**Технологии**: Docker, FastAPI, React, PostgreSQL, Redis, Whisper, LLM (OpenRouter/Groq/Gemini), n8n, Nginx

## 🏗️ Архитектура системы

### Микросервисная архитектура
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │     Backend     │    │     n8n         │
│   (React)       │◄──►│   (FastAPI)     │◄──►│  (Workflow)     │
│   Port: 3000    │    │   Port: 8000    │    │  Port: 5678     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PostgreSQL    │    │     Redis       │    │   Whisper Pool  │
│   Port: 5432    │    │   Port: 6379    │    │   Port: 8001     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Сервисы детально

#### 1. PostgreSQL (База данных)
**Таблицы:**
- `questions`: id, question, answer, topic, difficulty, probability, approved, timecode, created_at
- `processed_videos`: id, youtube_url, video_id, title, transcript, questions_count
- `question_video`: question_id, video_id (связь многие-ко-многим)

**Инициализация:** `scripts/init-db.sql`

#### 2. Redis (Кэширование)
- Хранение статусов задач обработки
- Кэширование результатов
- TTL: 24 часа для длинных видео

#### 3. n8n (Оркестрация workflow)
**Workflow:** `n8n/workflows/youtube-questions.json`
- Автоматический импорт при запуске
- Таймауты: 1 час для транскрибации, 10 мин для извлечения вопросов
- Обработка ошибок и обновление прогресса

#### 4. Whisper Service Pool
**Масштабирование:** `docker-compose up -d --scale whisper=N`
- Реплики: 2 по умолчанию (можно до 8+)
- CPU_THREADS: рассчитывается как `16 / N`
- Модель: medium (можно изменить через WHISPER_MODEL)
- Load Balancer: Nginx с least_conn стратегией

#### 5. Backend (FastAPI)
**Ключевые эндпоинты:**
- `POST /api/process-video`: Запуск обработки видео
- `GET /api/task/{task_id}`: Статус задачи
- `GET /api/questions`: Получение вопросов для PublicSide
- `GET /api/admin/questions`: Админские вопросы
- `POST /api/admin/approve-questions`: Одобрение вопросов
- `POST /internal/save-questions`: Сохранение вопросов (n8n webhook)
- `POST /internal/update-progress`: Обновление прогресса

**LLM интеграция:**
- Провайдеры: auto, openrouter, groq, gemini, ollama
- Fallback: автоматический выбор при недоступности
- Промпты: оптимизированы для извлечения вопросов из транскрибации

#### 6. Frontend (React)
**Компоненты:**
- `AdminPanel.js`: Обработка URL, просмотр вопросов
- `PublicSide.js`: Отображение вопросов с вероятностями
- `App.js`: Основной роутер

## 🔄 Workflow обработки видео

1. **Frontend** → Отправка YouTube URL
2. **Backend** → Валидация URL, создание задачи в Redis
3. **n8n** → Запуск workflow:
   - Скачивание аудио через yt-dlp
   - Транскрибация через Whisper pool
   - Извлечение вопросов через LLM
   - Сохранение в БД через backend webhook
4. **Backend** → Обновление статусов, расчет вероятностей

## 🗄️ Схема базы данных

```sql
-- Вопросы
CREATE TABLE questions (
    id SERIAL PRIMARY KEY,
    question TEXT NOT NULL,
    answer TEXT,
    topic VARCHAR(50) DEFAULT 'General',
    difficulty VARCHAR(20) DEFAULT 'middle',
    probability FLOAT DEFAULT 0.0,
    approved BOOLEAN DEFAULT FALSE,
    timecode VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Обработанные видео
CREATE TABLE processed_videos (
    id SERIAL PRIMARY KEY,
    youtube_url TEXT UNIQUE NOT NULL,
    video_id VARCHAR(20) NOT NULL,
    title TEXT,
    transcript TEXT,
    questions_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Связь вопросов и видео (многие-ко-многим)
CREATE TABLE question_video (
    question_id INTEGER REFERENCES questions(id),
    video_id INTEGER REFERENCES processed_videos(id),
    PRIMARY KEY (question_id, video_id)
);
```

## 🎯 Текущая функциональность

### ✅ Реализовано
- Обработка YouTube видео через URL
- Скачивание аудио и субтитров (yt-dlp)
- Гибридная транскрибация (субтитры + Whisper ASR)
- Извлечение вопросов через LLM
- Дедупликация вопросов в рамках одного видео
- Базовый AdminPanel и PublicSide
- Масштабируемый Whisper pool
- Система вероятностей вопросов

### 🔄 Требуется доработать

#### 1. PublicSide (Расширенный)
**Текущий статус:** Базовая реализация
**Требуется:**
- Полный список всех одобренных вопросов
- Фильтры по теме, сложности, вероятности
- Отображение вероятности (%) для каждого вопроса
- Поиск по вопросам

#### 2. AdminPanel (Полная переработка)
**Текущий статус:** Базовая отправка URL
**Требуется:**
- Отправка YouTube URL и получение списка вопросов
- CRUD операции: добавление/редактирование/удаление вопросов
- Одобрение вопросов (все сразу / по отдельности)
- Система похожих вопросов:
  - Рядом с каждым вопросом: цифра похожих вопросов из БД
  - При клике: модальное окно с похожими вопросами
  - Возможность замены текущего вопроса на похожий
- Интеграция с LLM для семантического поиска похожих вопросов

#### 3. Система вероятностей
**Формула:** `вероятность = (количество видео с вопросом / общее количество видео) * 100%`
**Текущий статус:** Базовая реализация
**Требуется:**
- Точная калькуляция через таблицу `question_video`
- Обновление при одобрении/отклонении вопросов
- Кэширование расчетов

## 🔧 Ключевые технические решения

### Дедупликация вопросов
```python
# Проверка дубликатов в рамках одного видео
existing_question = await conn.fetchval("""
    SELECT q.id FROM questions q
    JOIN question_video qv ON q.id = qv.question_id
    WHERE q.question = $1 AND q.timecode = $2 AND qv.video_id = $3
    LIMIT 1
""", q["question"], q.get("timecode", ""), video_id)
```

### Расчет вероятностей
```python
# Обновление вероятностей после изменений
async def update_probabilities(conn):
    await conn.execute("""
        UPDATE questions
        SET probability = (
            SELECT (COUNT(DISTINCT qv.video_id) * 100.0 / (SELECT COUNT(*) FROM processed_videos))
            FROM question_video qv
            WHERE qv.question_id = questions.id
        )
        WHERE approved = TRUE
    """)
```

### Поиск похожих вопросов
**Требуется реализовать:**
- Семантический поиск через embeddings (OpenAI, HuggingFace)
- Или использование pg_trgm для текстового поиска
- Или интеграция с LLM для оценки похожести

## 📁 Структура файлов

```
diploma/
├── docker-compose.yml          # Оркестрация сервисов
├── project_context.md          # Этот файл
├── README.md                   # Документация
├── backend/
│   ├── main.py                 # FastAPI приложение
│   ├── requirements.txt        # Python зависимости
│   └── Dockerfile             # Контейнер backend
├── frontend/
│   ├── package.json           # Node зависимости
│   ├── Dockerfile             # Контейнер frontend
│   └── src/
│       ├── App.js             # Основной компонент
│       ├── AdminPanel.js      # Панель администратора
│       └── PublicSide.js      # Публичная страница
├── whisper-service/
│   ├── main.py                # Whisper API
│   ├── entrypoint.sh          # Скрипт запуска
│   └── Dockerfile             # Контейнер Whisper
├── n8n/
│   └── workflows/
│       └── youtube-questions.json  # Workflow обработки
├── nginx/
│   └── nginx.conf             # Load balancer config
└── scripts/
    └── init-db.sql            # Инициализация БД
```

## 🚀 План реализации новых требований

### Фаза 1: Обновление базы данных
- Добавить таблицу `question_video`
- Обновить схему `questions` (approved, probability)
- Миграция существующих данных

### Фаза 2: Backend доработки
- Реализовать CRUD для вопросов
- Добавить эндпоинты для AdminPanel
- Реализовать поиск похожих вопросов
- Улучшить систему вероятностей

### Фаза 3: Frontend переработка
- Полная переработка AdminPanel
- Улучшение PublicSide
- Добавление модальных окон для похожих вопросов

### Фаза 4: Тестирование и оптимизация
- Интеграционное тестирование
- Оптимизация производительности
- Документация новых функций

## 🔐 Переменные окружения

```bash
# База данных
DATABASE_URL=postgresql://diploma:diploma123@postgres:5432/interview_prep
REDIS_URL=redis://redis:6379

# Сервисы
N8N_WEBHOOK_URL=http://n8n:5678/webhook/youtube-questions
WHISPER_SERVICE_URL=http://nginx-whisper:8001
WHISPER_POOL_SIZE=2

# LLM провайдеры
LLM_PROVIDER=auto
OPENROUTER_API_KEY=your_key
GROQ_API_KEY=your_key
GEMINI_API_KEY=your_key

# Whisper
WHISPER_MODEL=medium
```

## 📊 Мониторинг и метрики

- Healthchecks для всех сервисов
- Логи обработки видео
- Статистика использования LLM
- Производительность Whisper pool

---

**Последнее обновление:** 17 января 2026
**Версия проекта:** 2.0 (с дедупликацией и вероятностями)</content>
<parameter name="filePath">c:\Users\Lenovo\Desktop\Diploma\project_context.md