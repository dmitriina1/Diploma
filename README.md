# 🎓 Interview Prep — Извлечение вопросов для собеседований из YouTube

> **Дипломный проект** — Магистратура, направление 09.04.02 «Информационные системы и технологии»

100% бесплатное решение для автоматического извлечения вопросов с IT-собеседований из YouTube видео с использованием AI.

![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-61DAFB?style=flat&logo=react&logoColor=black)
![n8n](https://img.shields.io/badge/n8n-EA4B71?style=flat&logo=n8n&logoColor=white)

---

## 📋 Содержание

- [Описание проекта](#-описание-проекта)
- [Архитектура](#-архитектура)
- [Технологический стек](#-технологический-стек)
- [Быстрый старт](#-быстрый-старт)
- [API документация](#-api-документация)
- [Структура проекта](#-структура-проекта)
- [Конфигурация](#-конфигурация)
- [Примеры использования](#-примеры-использования)
- [Формат данных](#-формат-данных)
- [Troubleshooting](#-troubleshooting)

---

## 🎯 Описание проекта

### Цель
Автоматизация подготовки к IT-собеседованиям путём извлечения вопросов из YouTube видео с записями реальных интервью.

### Что делает система:
1. **Скачивает аудио + субтитры** из YouTube видео через yt-dlp (только русские субтитры, с обходом rate limiting)
2. **Транскрибирует** аудио в текст с таймкодами (OpenAI Whisper)
3. **Сливает субтитры с Whisper** — субтитры дают точный текст, Whisper — пунктуацию
4. **Извлекает вопросы** с помощью LLM (Groq API / LLaMA 70B)
5. **Проверяет грамматику** и исправляет ошибки распознавания
6. **Сохраняет результат** в JSON с таймкодами

### Ключевые особенности:
- ✅ **100% бесплатно** — Groq API предоставляет бесплатный доступ к LLaMA 70B
- ✅ **~100% точность** — гибридная транскрипция (субтитры + Whisper)
- ✅ **Надёжные субтитры** — 15 попыток с обходом rate limiting, правильный парсинг YouTube VTT
- ✅ **Retry субтитров** — 10 попыток с интервалом 3 сек + проверка после транскрибации
- ✅ **Локальное развёртывание** — все данные остаются на вашем сервере
- ✅ **Таймкоды** — каждый вопрос привязан к моменту в видео
- ✅ **Автокоррекция** — LLM исправляет ошибки распознавания речи
- ✅ **Real-time прогресс** — WebSocket + Polling для отслеживания
- ✅ **Swagger UI** — интерактивная документация API

---

## 🏗 Архитектура

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (React)                         │
│                      http://localhost:3000                       │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP/WebSocket
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Backend (FastAPI)                           │
│                      http://localhost:8000                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │   yt-dlp    │  │   Whisper   │  │      Groq API           │  │
│  │  (download) │  │ (transcribe)│  │  (extract questions)    │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
┌──────────────────┐ ┌──────────────┐ ┌──────────────────┐
│       n8n        │ │    Redis     │ │   PostgreSQL     │
│ (orchestration)  │ │   (cache)    │ │   (storage)      │
│ localhost:5678   │ │ localhost:6379│ │ localhost:5432  │
└──────────────────┘ └──────────────┘ └──────────────────┘
```

### Процесс обработки:

```
YouTube URL → yt-dlp → Audio (MP3) + Subtitles (VTT)
                          ↓              ↓
                      Whisper      Parse VTT
                (пунктуация)    (точный текст)
                          ↓              ↓
                         ─────MERGE─────
                               ↓
              Transcript + Timecodes (~100% accuracy)
                               ↓
                         Groq API (LLM)
                               ↓
           Questions (JSON) + Answers + Timecodes
```

---

## 🛠 Технологический стек

### Backend
| Компонент | Технология | Назначение |
|-----------|------------|------------|
| API Server | **FastAPI** | REST API, WebSocket, Swagger |
| Транскрибация | **OpenAI Whisper** | Speech-to-Text (base model) |
| **YouTube Subtitles** | **yt-dlp** | Автоматические/ручные субтитры |
| **Гибридная транскрипция** | Whisper + Subtitles | ~100% точность |
| LLM | **Groq API** (LLaMA 3.3 70B) | Извлечение вопросов |
| YouTube | **yt-dlp** | Скачивание аудио |
| Оркестрация | **n8n** | Workflow automation |
| Кэш | **Redis** | Хранение задач и результатов |
| БД | **PostgreSQL** | Персистентное хранение |

### Frontend
| Компонент | Технология |
|-----------|------------|
| UI | **React 18** |
| HTTP | **Fetch API** |
| Real-time | **WebSocket + Polling** |

### Инфраструктура
| Компонент | Технология |
|-----------|------------|
| Контейнеризация | **Docker + Docker Compose** |
| Reverse Proxy | Docker network |

---

## 🚀 Быстрый старт

### Требования
- Docker Desktop (Windows/Mac) или Docker Engine (Linux)
- 8 GB RAM минимум
- 10 GB свободного места
- Интернет-соединение

### 1. Клонирование репозитория
```bash
git clone <repository-url>
cd Diploma
```

### 2. Настройка Groq API (бесплатно)
1. Зарегистрируйтесь на [console.groq.com](https://console.groq.com)
2. Создайте API ключ
3. Создайте файл `.env`:
```env
GROQ_API_KEY=gsk_ваш_ключ_здесь
```

### 3. Запуск
**Windows:**
```cmd
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

### 4. Проверка
| Сервис | URL |
|--------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| **Swagger UI** | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |
| n8n | http://localhost:5678 |

### 5. Остановка
```bash
docker-compose down
```

---

## 📚 API документация

### 🔗 Интерактивная документация
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

---

### Processing — Обработка видео

#### `POST /api/process-video`
Запуск обработки YouTube видео.

**Request:**
```json
{
  "youtube_url": "https://www.youtube.com/watch?v=VIDEO_ID",
  "topic": "Backend",
  "level": "middle"
}
```

**Response:**
```json
{
  "task_id": "4e126365-6c13-4c44-a1c4-2ebc2b273ef6",
  "status": "started"
}
```

---

### Status — Статус и мониторинг

#### `GET /health`
Проверка здоровья сервиса.

**Response:**
```json
{
  "status": "healthy",
  "whisper_loaded": true
}
```

#### `GET /api/task/{task_id}`
Получение статуса задачи.

**Response:**
```json
{
  "task_id": "uuid",
  "status": "completed",
  "progress": 100,
  "step": "Готово!",
  "result": {
    "questions": [...],
    "video_title": "Название видео",
    "questions_count": 15
  }
}
```

---

### Export — Экспорт данных

#### `GET /api/transcript/{task_id}`
Скачать транскрипцию с таймкодами.

**Response:**
```json
{
  "transcript": "Полный текст...",
  "segments": [
    {"start": 0.0, "end": 5.2, "text": "Добрый день..."},
    {"start": 5.2, "end": 10.1, "text": "..."}
  ],
  "length": 5432
}
```

#### `GET /api/export/{task_id}`
Скачать только вопросы.

#### `GET /api/full-export/{task_id}` ⭐
Скачать всё: транскрипцию (merged + Whisper + субтитры) + вопросы + метаданные.

**Response:**
```json
{
  "task_id": "uuid",
  "transcript": "Merged текст (субтитры + Whisper пунктуация)...",
  "segments": [
    {"start": 0.0, "end": 2.5, "text": "Добрый день?", "source": "merged"}
  ],
  "whisper_raw": "Оригинальный текст Whisper...",
  "whisper_segments": [...],
  "youtube_subtitles": [
    {"start": 0.0, "end": 2.5, "text": "добрый день"}
  ],
  "has_subtitles": true,
  "video_title": "Название",
  "questions": [
    {
      "question": "Что такое REST API?",
      "answer": "REST — архитектурный стиль...",
      "timecode": "01:23",
      "topic": "Backend",
      "difficulty": "middle"
    }
  ],
  "questions_count": 15,
  "status": "completed"
}
```

#### `GET /api/subtitles/{task_id}` 🆕
Скачать оригинальные YouTube субтитры.

**Response:**
```json
{
  "task_id": "uuid",
  "subtitles": [
    {"start": 0.0, "end": 2.5, "text": "добрый день"},
    {"start": 2.5, "end": 5.0, "text": "меня зовут павел"}
  ],
  "count": 150
}
```

#### `GET /api/export-all`
Скачать ВСЕ вопросы из базы.

#### `GET /api/questions?topic=Backend&level=middle`
Получить вопросы с фильтрацией.

---

### WebSocket

#### `WS /ws/{client_id}`
Real-time обновления прогресса.

**Сообщения:**
```json
{"type": "progress", "task_id": "uuid", "progress": 50, "step": "Транскрибация..."}
{"type": "result", "task_id": "uuid", "questions": [...], "video_title": "..."}
```

---

## 📁 Структура проекта

```
Diploma/
├── backend/
│   ├── main.py              # FastAPI приложение (основной файл)
│   ├── requirements.txt     # Python зависимости
│   ├── Dockerfile          # Docker образ backend
│   └── temp/               # Временные файлы (аудио)
│
├── frontend/
│   ├── src/
│   │   ├── App.js          # React компонент
│   │   └── index.js        # Entry point
│   ├── public/
│   │   └── index.html
│   ├── package.json
│   └── Dockerfile
│
├── n8n/
│   └── workflows/
│       └── youtube-questions.json  # n8n workflow (авто-импорт)
│
├── scripts/
│   └── init-db.sql         # Инициализация PostgreSQL
│
├── docker-compose.yml      # Конфигурация контейнеров
├── .env                    # Переменные окружения (создать!)
├── start.bat              # Запуск (Windows)
├── start.sh               # Запуск (Linux/Mac)
├── stop.bat               # Остановка (Windows)
└── README.md              # Документация
```

---

## ⚙️ Конфигурация

### Переменные окружения (.env)

```env
# Обязательно
GROQ_API_KEY=gsk_ваш_ключ

# Опционально (есть значения по умолчанию)
USE_GROQ=true
DATABASE_URL=postgresql://diploma:diploma123@postgres:5432/interview_prep
REDIS_URL=redis://redis:6379
N8N_WEBHOOK_URL=http://n8n:5678/webhook/youtube-questions
OLLAMA_URL=http://ollama:11434
```

### Порты

| Сервис | Порт | Описание |
|--------|------|----------|
| Frontend | 3000 | React приложение |
| Backend | 8000 | FastAPI + Swagger |
| n8n | 5678 | Workflow UI |
| PostgreSQL | 5432 | База данных |
| Redis | 6379 | Кэш |
| Ollama | 11434 | Локальный LLM (опционально) |

---

## 💡 Примеры использования

### cURL

```bash
# Запуск обработки
curl -X POST "http://localhost:8000/api/process-video" \
  -H "Content-Type: application/json" \
  -d '{"youtube_url": "https://www.youtube.com/watch?v=VIDEO_ID", "topic": "Backend", "level": "middle"}'

# Проверка статуса
curl "http://localhost:8000/api/task/{task_id}"

# Экспорт результата
curl "http://localhost:8000/api/full-export/{task_id}" -o result.json
```

### Python

```python
import requests
import time

# Запуск обработки
response = requests.post(
    "http://localhost:8000/api/process-video",
    json={
        "youtube_url": "https://www.youtube.com/watch?v=VIDEO_ID",
        "topic": "Backend",
        "level": "middle"
    }
)
task_id = response.json()["task_id"]
print(f"Task started: {task_id}")

# Ожидание завершения
while True:
    status = requests.get(f"http://localhost:8000/api/task/{task_id}").json()
    print(f"Progress: {status['progress']}% - {status['step']}")
    if status["status"] == "completed":
        break
    time.sleep(2)

# Получение результата
result = requests.get(f"http://localhost:8000/api/full-export/{task_id}").json()

print(f"\n📹 {result['video_title']}")
print(f"📝 Найдено вопросов: {result['questions_count']}\n")

for q in result["questions"]:
    print(f"[{q.get('timecode', 'N/A')}] {q['question']}")
    print(f"   ➡️ {q['answer']}\n")
```

### JavaScript / Fetch

```javascript
// Запуск обработки
const response = await fetch('http://localhost:8000/api/process-video', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    youtube_url: 'https://www.youtube.com/watch?v=VIDEO_ID',
    topic: 'Backend',
    level: 'middle'
  })
});
const { task_id } = await response.json();

// WebSocket для real-time прогресса
const ws = new WebSocket(`ws://localhost:8000/ws/${clientId}`);
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'progress') {
    console.log(`Progress: ${data.progress}% - ${data.step}`);
  } else if (data.type === 'result') {
    console.log('Questions:', data.questions);
  }
};
```

---

## 📊 Формат данных

### Вопрос (Question)

```json
{
  "question": "Что такое SOLID принципы?",
  "answer": "SOLID — это пять принципов ООП: Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, Dependency Inversion.",
  "timecode": "03:45",
  "topic": "Backend",
  "difficulty": "middle"
}
```

### Сегмент транскрипции (Segment)

```json
{
  "start": 12.5,
  "end": 15.8,
  "text": "Расскажите о вашем опыте работы"
}
```

### Полный экспорт (Full Export)

```json
{
  "task_id": "4e126365-6c13-4c44-a1c4-2ebc2b273ef6",
  "transcript": "Добрый день, меня зовут Павел...",
  "segments": [
    {"start": 0.0, "end": 2.5, "text": "Добрый день"},
    {"start": 2.5, "end": 5.0, "text": "меня зовут Павел"}
  ],
  "transcript_length": 5432,
  "video_title": "Собеседование Java Developer",
  "questions": [
    {
      "question": "На каких языках вы писали код?",
      "answer": "Основной язык — Java, также работал с Python и SQL.",
      "timecode": "01:23",
      "topic": "Backend",
      "difficulty": "middle"
    }
  ],
  "questions_count": 15,
  "status": "completed"
}
```

---

## 🔧 Troubleshooting

### Проблема: "NetworkError when attempting to fetch resource"
**Решение:** Перезапустите backend
```bash
docker-compose restart backend
```

### Проблема: YouTube субтитры не скачиваются (429 ошибка)
**Решение:** ✅ **ИСПРАВЛЕНО** Система автоматически обходит rate limiting:
- 15 попыток скачивания с задержками 10 секунд
- Ротация User-Agent (5 разных браузеров)
- Разные player clients (web, android, ios, tvhtml5)
- Geo bypass для России
- **Флаг `nooverwrites`** предотвращает повторное скачивание существующих субтитров

### Проблема: Скачиваются английские субтитры вместо русских
**Решение:** ✅ **ИСПРАВЛЕНО** Код настроен только на русские субтитры (`'subtitleslangs': ['ru']`). Парсер правильно обрабатывает YouTube VTT формат с HTML-тегами и временными метками внутри текста.

### Проблема: Субтитры скачиваются но не парсятся (0 segments)
**Решение:** ✅ **ИСПРАВЛЕНО** Улучшенный парсер VTT:
- Удаляет HTML-теги (`<c>`, `<00:00:14.120>`)
- Игнорирует дополнительные атрибуты таймкодов (`align:start position:0%`)
- Очищает временные метки внутри текста
- Поддерживает стандартный и YouTube VTT форматы

### Проблема: Whisper медленно работает
**Решение:** Используется модель `base`. Для ускорения можно использовать `tiny`, но качество будет хуже. Для лучшего качества — `medium` или `large`.

### Проблема: Groq API rate limit
**Решение:** Бесплатный план Groq — 30 запросов/минуту. Подождите минуту между запросами.

### Проблема: Контейнеры не запускаются
**Решение:**
```bash
docker-compose down -v
docker-compose up -d --build
```

### Проблема: n8n workflow не работает
**Решение:** Убедитесь, что workflow активирован (зелёный тоггл) в http://localhost:5678

### Просмотр логов
```bash
# Все сервисы
docker-compose logs -f

# Конкретный сервис
docker-compose logs -f backend
docker-compose logs -f n8n
docker-compose logs -f frontend
```

### Очистка всех данных
```bash
docker-compose down -v
docker system prune -a
```

---

## 📈 Возможные улучшения

- [ ] Поддержка других видео-платформ (VK Video, Rutube)
- [ ] Генерация тестовых вопросов с вариантами ответов
- [ ] Экспорт в Anki / Quizlet
- [ ] Поддержка английского языка
- [ ] Кластеризация похожих вопросов
- [ ] Интеграция с ChatGPT для расширенных ответов

---

## 📝 Лицензия

MIT License — свободное использование в образовательных и коммерческих целях.

---

## 👤 Автор

**Дипломный проект магистратуры**  
Направление: 09.04.02 «Информационные системы и технологии»  
Год: 2026

---

## 🙏 Благодарности

- [OpenAI Whisper](https://github.com/openai/whisper) — Speech-to-Text модель
- [Groq](https://groq.com) — Бесплатный доступ к LLaMA 70B
- [n8n](https://n8n.io) — Open-source workflow automation
- [FastAPI](https://fastapi.tiangolo.com) — Modern Python web framework
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) — YouTube downloader
- [React](https://react.dev) — UI library
