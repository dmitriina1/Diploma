# 🎯 Interview Prep Platform

**Полнофункциональная платформа для автоматизированной подготовки к IT-собеседованиям**  
Анализирует видео с собеседованиями на русском языке и извлекает вопросы/ответы с помощью AI

---

## 📋 Полное описание

### Что это?

Автоматизированная система для создания базы знаний из видео-собеседований. Система обрабатывает видео с разных платформ, использует Whisper AI для транскрибации речи, LLM для извлечения структурированных вопросов и ответов, и предоставляет удобный интерфейс для изучения материала.

### Как это работает?

```mermaid
graph LR
    A[Видео URL] --> B[yt-dlp]
    B --> C[Аудио MP3]
    C --> D[Whisper large-v3]
    D --> E[Транскрипт текста]
    E --> F[LLM GPT-4/Gemini]
    F --> G[Структурированные Q&A]
    G --> H[PostgreSQL]
    H --> I[Vue.js UI]
```

**Детальный процесс**:

1. **Загрузка видео** (`video_downloader.py`):
   - Определение платформы (YouTube, VK, Rutube, OK, Dailymotion)
   - Скачивание русских субтитров (если есть)
   - Извлечение аудиодорожки в MP3 (192kbps)
   - Сохранение метаданных (название, длительность, thumbnail)

2. **Транскрибация** (`whisper-service/main_new.py`):
   - Загрузка модели faster-whisper large-v3 (3GB)
   - Обработка ПОЛНОГО аудио без разбиения на части
   - Распознавание на русском языке с автоопределением
   - Генерация временных меток для каждого сегмента
   - Возврат полного текста + сегментированного JSON

3. **Извлечение вопросов** (LLM в `main_new.py`):
   - Отправка транскрипта в LLM (OpenRouter/Gemini/Groq)
   - Промпт специально настроен для русскоязычных собеседований
   - Извлечение: вопрос, ответ, технология, уровень сложности
   - Валидация и очистка от дубликатов

4. **Сохранение** (PostgreSQL):
   - Запись вопросов со статусом "на модерации"
   - Связывание вопросов с исходным видео
   - Индексация для быстрого поиска
   - Embeddings для семантического поиска

5. **Модерация** (Админ-панель):
   - Просмотр всех извлеченных вопросов
   - Редактирование текста вопроса/ответа
   - Одобрение или удаление
   - Одобренные вопросы появляются на публичной стороне

### Основные возможности

#### Для администраторов:
- ✅ **Мультиплатформенная загрузка**: YouTube, VK.video, Rutube, OK.ru, Dailymotion (через yt-dlp)
- ✅ **Автоматическая обработка**: Полный pipeline без ручного вмешательства
- ✅ **Модерация вопросов**: Полный контроль над публикуемым контентом
- ✅ **Редактирование**: Исправление ошибок распознавания или LLM
- ✅ **Мониторинг задач**: Отслеживание прогресса обработки в реальном времени

#### Для пользователей:
- ✅ **Фильтрация по технологиям**: JavaScript, Python, React, Node.js и др.
- ✅ **Поиск по схожести**: Semantic search через sentence-transformers
- ✅ **Адаптивный UI**: Работает на десктопе и мобильных устройствах
- ✅ **Современный дизайн**: Glassmorphism, градиенты, плавные анимации

#### Технические:
- ✅ **Whisper large-v3**: Самая точная модель для русского языка
- ✅ **Batch processing**: До 2 параллельных обработок видео
- ✅ **Автоматические retry**: При ошибках загрузки видео (до 10 попыток)
- ✅ **SSL bypass**: Обход проблем с сертификатами YouTube
- ✅ **Pip cache**: Быстрая пересборка Docker без загрузки библиотек
- ✅ **Volume mounts**: Изменения кода без rebuild контейнеров

---

## 🏗️ Архитектура

```
┌─────────────────┐
│  Frontend Vue3  │ ← http://localhost:3000
└────────┬────────┘
         │
┌────────▼────────┐
│   Backend API   │ ← FastAPI (http://localhost:8000)
│   (FastAPI)     │
└────┬─────┬──────┘
     │     │
     │     └──────────┐
     │                │
┌────▼────┐    ┌─────▼──────┐
│PostgreSQL│    │Whisper AI  │ ← large-v3 (http://localhost:8001)
│   +DB    │    │  Worker    │
└─────────┘    └────────────┘
     │
┌────▼────┐
│  Redis  │ ← Кэш и очереди  
└─────────┘
```

### Компоненты

| Сервис | Порт | Описание |
|--------|------|----------|
| **Frontend** | 3000 | Vue 3 + Vite интерфейс |
| **Backend** | 8000 | FastAPI REST API |
| **Whisper** | 8001 | faster-whisper large-v3 |
| **PostgreSQL** | 5432 | База данных |
| **Redis** | 6379 | Кэш и очереди |

---

## 🔧 Детальное описание компонентов

### 1. Frontend (Vue 3 + Vite)

**Путь**: `frontend-vue/`  
**Технологии**: Vue 3 (Composition API), Vite, Pinia, Vue Router, Axios  
**Порт**: 3000 (dev) / 80 (production через nginx)

#### Структура проекта:
```
src/
├── views/
│   ├── Home.vue         # Публичная сторона (список вопросов)
│   ├── Admin.vue        # Панель администратора
│   ├── Questions.vue    # Все вопросы с фильтрами
│   └── QuestionDetail.vue  # Детальный просмотр вопроса
├── components/
│   ├── VideoUpload.vue      # Форма загрузки видео
│   ├── TechSelector.vue     # Фильтр по технологиям
│   ├── QuestionCard.vue     # Карточка вопроса
│   ├── QuestionApproval.vue # Модерация вопроса
│   ├── AnswerGenerator.vue  # Генерация ответов
│   └── NavBar.vue           # Навигация
├── store/
│   └── index.js         # Pinia store (состояние)
├── router/
│   └── index.js         # Vue Router конфигурация
└── api/
    └── client.js        # HTTP клиент
```

#### Ключевые файлы:

**`src/views/Admin.vue`** - Админ-панель:
```vue
<template>
  <div class="admin-panel">
    <!-- Форма загрузки видео -->
    <VideoUpload @video-submitted="refreshTasks" />
    
    <!-- Активные задачи обработки -->
    <div v-for="task in tasks" :key="task.id">
      <div class="progress-bar" :style="{width: task.progress + '%'}"></div>
      {{ task.status }} - {{ task.video_title }}
    </div>
    
    <!-- Вопросы на модерации -->
    <QuestionApproval 
      v-for="q in pendingQuestions" 
      :question="q"
      @approved="handleApprove"
      @rejected="handleReject"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import api from '@/api/client'

const tasks = ref([])
const pendingQuestions = ref([])

// Обновление задач каждые 2 секунды
let interval
onMounted(() => {
  loadPendingQuestions()
  interval = setInterval(loadTasks, 2000)
})
onUnmounted(() => clearInterval(interval))

async function loadTasks() {
  const { data } = await api.get('/api/tasks')
  tasks.value = data.filter(t => t.status !== 'completed')
}
</script>
```

**`src/store/index.js`** - Глобальное состояние:
```javascript
import { defineStore } from 'pinia'

export const useMainStore = defineStore('main', {
  state: () => ({
    selectedTechnologies: [],
    searchQuery: '',
    questions: [],
    loading: false
  }),
  
  actions: {
    async fetchQuestions(filters = {}) {
      this.loading = true
      try {
        const params = new URLSearchParams()
        if (filters.technology) params.append('technology', filters.technology)
        if (filters.status) params.append('status', filters.status)
        
        const { data } = await api.get(`/api/questions?${params}`)
        this.questions = data
      } finally {
        this.loading = false
      }
    },
    
    async searchSimilar(query) {
      const { data } = await api.post('/api/search-similar', { query, limit: 10 })
      this.questions = data
    }
  }
})
```

**Vite конфигурация** (`vite.config.js`):
```javascript
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig({
  plugins: [vue()],
  
  server: {
    host: '0.0.0.0',
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://backend:8000',
        changeOrigin: true
      }
    }
  },
  
  build: {
    outDir: 'dist',
    rollupOptions: {
      output: {
        manualChunks: {
          'vendor': ['vue', 'vue-router', 'pinia', 'axios']
        }
      }
    }
  },
  
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src')
    }
  }
})
```

**Стилизация** (Glassmorphism):
```css
.question-card {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  padding: 24px;
  transition: transform 0.3s ease;
}

.question-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.2);
}
```

---

### 2. Backend (FastAPI)

**Путь**: `backend/`  
**Технологии**: FastAPI, asyncio, httpx, asyncpg, yt-dlp  
**Порт**: 8000

#### Основные модули:

##### `main_new.py` - Core API (800+ строк)

**Классы**:

```python
class TaskManager:
    """Управление задачами обработки видео"""
    
    MAX_CONCURRENT_TASKS = 2  # Не более 2 одновременно
    
    def __init__(self):
        self.semaphore = asyncio.Semaphore(self.MAX_CONCURRENT_TASKS)
        self.tasks = {}  # task_id -> TaskInfo
        
    async def process_with_limit(self, video_url: str, task_id: str):
        """Обработка с ограничением по количеству"""
        async with self.semaphore:  # Блокируется, если уже 2 задачи
            try:
                await self.process_video(video_url, task_id)
            except Exception as e:
                self.tasks[task_id].status = 'failed'
                self.tasks[task_id].error = str(e)
                logger.error(f"Task {task_id} failed: {e}")
```

```python
class WhisperWorker:
    """Клиент для whisper-service"""
    
    def __init__(self, base_url: str = "http://whisper-service:8001"):
        self.client = httpx.AsyncClient(timeout=600.0)  # 10 минут
        self.base_url = base_url
        
    async def transcribe(self, audio_path: Path, language: str = "ru"):
        """Отправка аудио на транскрипцию"""
        response = await self.client.get(
            f"{self.base_url}/transcribe-path",
            params={
                "audio_path": str(audio_path),
                "language": language
            }
        )
        
        if response.status_code != 200:
            raise Exception(f"Whisper failed: {response.text}")
            
        data = response.json()
        return {
            "text": data["text"],           # Полный текст
            "segments": data["segments"],   # Сегменты с временем
            "language": data["language"]    # Определенный язык
        }
```

```python
class LLMProcessor:
    """Извлечение вопросов через LLM"""
    
    PROVIDERS = {
        "openrouter": {
            "url": "https://openrouter.ai/api/v1/chat/completions",
            "key_env": "OPENROUTER_API_KEY",
            "model": "openai/gpt-4-turbo"
        },
        "gemini": {
            "url": "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent",
            "key_env": "GEMINI_API_KEY"
        },
        "groq": {
            "url": "https://api.groq.com/openai/v1/chat/completions",
            "key_env": "GROQ_API_KEY",
            "model": "llama-3.1-70b-versatile"
        }
    }
    
    EXTRACTION_PROMPT = """
    Ты - AI помощник для анализа технических собеседований.
    Из данного транскрипта извлеки ВСЕ вопросы и ответы.
    
    ФОРМАТ (обязательно JSON массив):
    [
      {
        "question": "Что такое замыкание в JavaScript?",
        "answer": "Замыкание - это функция вместе с окружением...",
        "technology": "JavaScript",
        "complexity": "middle"
      }
    ]
    
    ПРАВИЛА:
    1. Только технические вопросы (код, архитектура, алгоритмы)
    2. Пропускай вопросы о зарплате, компании
    3. Complexity: junior/middle/senior
    4. Technology: JavaScript, Python, React, SQL и т.д.
    5. Ответ - полный, но сжатый (2-4 предложения)
    
    ТРАНСКРИПТ:
    {transcript}
    """
    
    async def extract_questions(self, transcript: str) -> list[dict]:
        """Извлечение через LLM"""
        provider = self._select_provider()
        prompt = self.EXTRACTION_PROMPT.format(transcript=transcript)
        
        response = await self._call_llm(provider, prompt)
        questions = self._parse_response(response)
        
        return self._validate_questions(questions)
```

**API Endpoints**:

```python
@app.post("/api/process-video")
async def process_video(request: VideoProcessRequest):
    """
    Запуск обработки видео
    
    Body:
    {
        "video_url": "https://www.youtube.com/watch?v=...",
        "language": "ru"  # optional
    }
    
    Response:
    {
        "task_id": "uuid-task-id",
        "status": "processing",
        "message": "Video processing started"
    }
    """
    task_id = str(uuid.uuid4())
    
    # Запуск в фоне
    asyncio.create_task(
        task_manager.process_with_limit(request.video_url, task_id)
    )
    
    return {"task_id": task_id, "status": "processing"}


@app.get("/api/tasks")
async def get_tasks():
    """
    Получить список всех задач
    
    Response:
    [
        {
            "task_id": "...",
            "status": "processing",  # processing/completed/failed
            "progress": 45,           # 0-100
            "video_title": "Mock interview...",
            "created_at": "2026-02-18T10:30:00",
            "error": null
        }
    ]
    """
    return list(task_manager.tasks.values())


@app.get("/api/questions")
async def get_questions(
    technology: str | None = None,
    status: str = "approved",      # pending/approved/rejected
    limit: int = 50,
    offset: int = 0
):
    """
    Получить список вопросов с фильтрами
    
    Query params:
    - technology: фильтр по технологии
    - status: pending/approved/rejected
    - limit: количество (default 50)
    - offset: пагинация (default 0)
    
    Response:
    [
        {
            "id": 123,
            "question_text": "Что такое hoisting?",
            "answer_text": "Hoisting - это...",
            "technology": "JavaScript",
            "complexity": "junior",
            "status": "approved",
            "video_title": "JS Interview",
            "youtube_url": "https://...",
            "created_at": "2026-02-18T10:00:00"
        }
    ]
    """
    query = """
        SELECT q.*, v.title as video_title, v.youtube_url
        FROM questions q
        JOIN processed_videos v ON q.video_id = v.id
        WHERE q.status = $1
    """
    params = [status]
    
    if technology:
        query += " AND q.technology = $2"
        params.append(technology)
        
    query += " ORDER BY q.created_at DESC LIMIT $3 OFFSET $4"
    params.extend([limit, offset])
    
    rows = await db.fetch(query, *params)
    return [dict(row) for row in rows]


@app.patch("/api/questions/{question_id}/approve")
async def approve_question(question_id: int):
    """
    Одобрить вопрос (изменить статус на approved)
    
    Response:
    {"status": "approved", "id": 123}
    """
    await db.execute(
        "UPDATE questions SET status = 'approved', approved_at = NOW() WHERE id = $1",
        question_id
    )
    return {"status": "approved", "id": question_id}


@app.post("/api/search-similar")
async def search_similar(request: SearchRequest):
    """
    Семантический поиск похожих вопросов
    
    Body:
    {
        "query": "как работает useState",
        "limit": 10
    }
    
    Response:
    [
        {
            "id": 456,
            "question_text": "Как работает хук useState?",
            "answer_text": "useState - это React хук для...",
            "similarity": 0.87,  # 0-1 (similarity score)
            "technology": "React"
        }
    ]
    """
    # Создать embedding для запроса
    query_embedding = model.encode(request.query)
    
    # Поиск через pgvector
    results = await db.fetch("""
        SELECT 
            q.*,
            1 - (q.question_embedding <=> $1::vector) as similarity
        FROM questions q
        WHERE q.status = 'approved'
        ORDER BY q.question_embedding <=> $1::vector
        LIMIT $2
    """, query_embedding.tolist(), request.limit)
    
    return [dict(r) for r in results]


@app.get("/api/technologies")
async def get_technologies():
    """
    Получить список всех технологий с количеством вопросов
    
    Response:
    [
        {"name": "JavaScript", "count": 145},
        {"name": "Python", "count": 89},
        {"name": "React", "count": 67}
    ]
    """
    rows = await db.fetch("""
        SELECT 
            technology as name,
            COUNT(*)::int as count
        FROM questions
        WHERE status = 'approved'
        GROUP BY technology
        ORDER BY count DESC
    """)
    return [dict(row) for row in rows]
```

##### `video_downloader.py` - Загрузчик видео

**Платформы**:
- YouTube (`youtube.com`, `youtu.be`)
- VK Video (`vk.com/video`)
- Rutube (`rutube.ru`)
- Odnoklassniki (`ok.ru`)
- Dailymotion (`dailymotion.com`)

**Конфигурация yt-dlp**:
```python
ydl_opts = {
    # Аудио формат
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',  # 192 kbps
    }],
    'outtmpl': str(output_path),
    
    # Субтитры (только русские - избегаем HTTP 429)
    'writesubtitles': True,
    'writeautomaticsub': True,
    'subtitleslangs': ['ru'],  # ТОЛЬКО РУССКИЙ
    
    # SSL обход (фикс для YouTube)
    'nocheckcertificate': True,
    'socket_timeout': 60,  # Увеличенный таймаут
    
    # Retry логика
    'retries': 10,              # Повторы при ошибках
    'fragment_retries': 10,     # Повторы для фрагментов
    'http_chunk_size': 10485760,  # 10MB чанки
    
    # Прочее
    'ignoreerrors': False,
    'noplaylist': True,         # Не скачивать плейлисты
    'quiet': False,
    'no_warnings': False,
}
```

**Возвращаемые данные**:
```python
{
    'title': str,          # Название видео
    'platform': str,       # youtube, vk, rutube и т.д.
    'duration': int,       # Секунды
    'audio_path': Path,    # Путь к .mp3 файлу
    'thumbnail': str,      # URL превьюшки
    'video_id': str        # ID на платформе
}
```

##### `similarity_search.py` - Семантический поиск

**Модель**: `sentence-transformers/paraphrase-multilingual-mpnet-base-v2`
- **Размер**: ~420MB
- **Языки**: 50+ (включая русский)
- **Embedding размер**: 768 измерений
- **Метрика**: Cosine similarity

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')

def create_embedding(text: str) -> list[float]:
    """Создать embedding для текста"""
    embedding = model.encode(text, normalize_embeddings=True)
    return embedding.tolist()  # [0.234, -0.156, ...] (768 чисел)

def search_similar(query: str, limit: int = 10):
    """Поиск похожих вопросов"""
    query_emb = create_embedding(query)
    
    # Поиск через pgvector (cosine distance)
    results = db.query("""
        SELECT 
            *,
            1 - (question_embedding <=> $1::vector) as similarity
        FROM questions
        WHERE status = 'approved'
        ORDER BY question_embedding <=> $1::vector
        LIMIT $2
    """, query_emb, limit)
    
    return results
```

---

### 3. Whisper Service (faster-whisper)

**Путь**: `whisper-service/`  
**Технологии**: FastAPI, faster-whisper, CTranslate2  
**Порт**: 8001

**Модель**: `large-v3` (2.87GB)

**Преимущества faster-whisper**:
- В **4x быстрее** оригинального OpenAI Whisper
- Использует **CTranslate2** (оптимизированный inference)
- Поддержка CPU и GPU (CUDA)
- **Меньше памяти** (~3GB вместо ~6GB)

**Файл `main_new.py`**:

```python
from faster_whisper import WhisperModel
from fastapi import FastAPI, HTTPException
from pathlib import Path

app = FastAPI(title="Whisper Transcription Service")

# Загрузка модели при старте
model = WhisperModel(
    "large-v3",
    device="cpu",              # или "cuda" для GPU
    compute_type="int8",       # Квантизация (int8/float16/float32)
    download_root="/app/models",  # Кэш моделей
    num_workers=4              # Потоки для CPU
)

@app.get("/transcribe-path")
async def transcribe_file(audio_path: str, language: str = "ru"):
    """
    Транскрибировать аудио файл
    
    Query params:
    - audio_path: полный путь к .mp3/.wav файлу
    - language: код языка (ru, en, auto)
    
    Response:
    {
        "text": "Полный транскрипт...",
        "segments": [
            {
                "start": 0.0,
                "end": 5.2,
                "text": "Привет, сегодня..."
            }
        ],
        "language": "ru"
    }
    """
    if not Path(audio_path).exists():
        raise HTTPException(404, f"File not found: {audio_path}")
    
    # Параметры транскрипции
    segments, info = model.transcribe(
        audio_path,
        language=language if language != "auto" else None,
        beam_size=5,           # Точность (1-10)
        vad_filter=True,       # Voice Activity Detection
        vad_parameters=dict(
            min_silence_duration_ms=500  # Минимальная пауза
        ),
        condition_on_previous_text=True  # Контекст из предыдущих сегментов
    )
    
    # Собрать результаты
    segments_list = []
    full_text = []
    
    for segment in segments:
        segments_list.append({
            "start": segment.start,
            "end": segment.end,
            "text": segment.text.strip()
        })
        full_text.append(segment.text.strip())
    
    return {
        "text": " ".join(full_text),
        "segments": segments_list,
        "language": info.language,
        "duration": info.duration
    }

@app.get("/health")
async def health():
    """Health check"""
    return {"status": "ok", "model": "large-v3"}
```

**Производительность**:

| CPU (8 cores) | GPU (NVIDIA RTX 3060) |
|---------------|----------------------|
| ~0.3x realtime | ~3x realtime |
| 10 min audio = 30 min | 10 min = 3 min |

**Требования**:
- CPU: 8+ cores рекомендуется
- RAM: 4GB минимум (8GB рекомендуется)
- Диск: 4GB (модель + кэш)
- GPU (опционально): NVIDIA с CUDA 11.x+

---

### 4. PostgreSQL + pgvector

**Версия**: PostgreSQL 15.3  
**Расширение**: pgvector 0.5.0  
**Порт**: 5432

**Схема БД**:

```sql
-- Расширение для vector embeddings
CREATE EXTENSION IF NOT EXISTS vector;

-- Таблица обработанных видео
CREATE TABLE processed_videos (
    id SERIAL PRIMARY KEY,
    video_id VARCHAR(255) UNIQUE NOT NULL,  -- ID с платформы (youtube_id)
    youtube_url TEXT NOT NULL,               -- Исходный URL
    title TEXT,                              -- Название
    platform VARCHAR(50),                    -- youtube/vk/rutube/ok
    duration INTEGER,                        -- Длительность в секундах
    thumbnail_url TEXT,                      -- URL превью
    processed_at TIMESTAMP DEFAULT NOW()
);

-- Таблица вопросов
CREATE TABLE questions (
    id SERIAL PRIMARY KEY,
    video_id INTEGER REFERENCES processed_videos(id) ON DELETE CASCADE,
    
    -- Текст
    question_text TEXT NOT NULL,
    answer_text TEXT,
    
    -- Метаданные
    technology VARCHAR(100),                 -- JavaScript, Python и т.д.
    complexity VARCHAR(20),                  -- junior/middle/senior
    
    -- Модерация
    status VARCHAR(20) DEFAULT 'pending',    -- pending/approved/rejected
    created_at TIMESTAMP DEFAULT NOW(),
    approved_at TIMESTAMP,
    
    -- Vector embedding для семантического поиска
    question_embedding vector(768),          -- 768-мерный вектор
    
    -- Индексы
    CONSTRAINT valid_status CHECK (status IN ('pending', 'approved', 'rejected')),
    CONSTRAINT valid_complexity CHECK (complexity IN ('junior', 'middle', 'senior'))
);

-- Индексы для быстрого поиска
CREATE INDEX idx_questions_status ON questions(status);
CREATE INDEX idx_questions_technology ON questions(technology);
CREATE INDEX idx_questions_video_id ON questions(video_id);
CREATE INDEX idx_questions_created_at ON questions(created_at DESC);

-- HNSW индекс для векторного поиска (быстрее IVFFlat)
CREATE INDEX idx_question_embedding ON questions 
USING hnsw (question_embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
```

**Примеры запросов**:

```sql
-- 1. Получить все одобренные вопросы по JavaScript
SELECT 
    q.id,
    q.question_text,
    q.answer_text,
    q.complexity,
    v.title as video_title,
    v.youtube_url,
    v.duration
FROM questions q
JOIN processed_videos v ON q.video_id = v.id
WHERE q.status = 'approved' 
  AND q.technology = 'JavaScript'
ORDER BY q.created_at DESC
LIMIT 50;

-- 2. Семантический поиск (найти вопросы про "useState")
-- embedding - это массив из 768 чисел, полученный от sentence-transformers
SELECT 
    q.question_text,
    q.answer_text,
    q.technology,
    1 - (q.question_embedding <=> $1::vector) as similarity
FROM questions q
WHERE q.status = 'approved'
  AND 1 - (q.question_embedding <=> $1::vector) > 0.7  -- Порог схожести
ORDER BY q.question_embedding <=> $1::vector
LIMIT 10;

-- 3. Статистика по технологиям
SELECT 
    technology,
    COUNT(*) as total,
    COUNT(*) FILTER (WHERE status = 'approved') as approved,
    COUNT(*) FILTER (WHERE status = 'pending') as pending,
    COUNT(*) FILTER (WHERE complexity = 'junior') as junior_count,
    COUNT(*) FILTER (WHERE complexity = 'middle') as middle_count,
    COUNT(*) FILTER (WHERE complexity = 'senior') as senior_count
FROM questions
GROUP BY technology
ORDER BY total DESC;

-- 4. Последние обработанные видео
SELECT 
    v.*,
    COUNT(q.id) as questions_count,
    COUNT(q.id) FILTER (WHERE q.status = 'approved') as approved_count
FROM processed_videos v
LEFT JOIN questions q ON v.id = q.video_id
GROUP BY v.id
ORDER BY v.processed_at DESC
LIMIT 20;

-- 5. Найти дубликаты вопросов (схожесть > 0.95)
SELECT DISTINCT ON (q1.id)
    q1.id as question1_id,
    q1.question_text as question1,
    q2.id as question2_id,
    q2.question_text as question2,
    1 - (q1.question_embedding <=> q2.question_embedding) as similarity
FROM questions q1
CROSS JOIN questions q2
WHERE q1.id < q2.id
  AND 1 - (q1.question_embedding <=> q2.question_embedding) > 0.95
ORDER BY q1.id, similarity DESC;
```

**Инициализация БД** (`scripts/init-db.sql`):
```sql
-- Создание БД
CREATE DATABASE interview_prep;

\c interview_prep

-- Расширения
CREATE EXTENSION IF NOT EXISTS vector;

-- Таблицы (см. выше)
...

-- Начальные данные (опционально)
INSERT INTO processed_videos (video_id, youtube_url, title, platform, duration)
VALUES 
('example123', 'https://youtube.com/watch?v=example123', 'Test Interview', 'youtube', 600);
```

---

### 5. NGINX (Reverse Proxy)

**Конфигурация**: `nginx/nginx.conf`  
**Порт**: 80 (или 443 для HTTPS)

```nginx
worker_processes auto;

events {
    worker_connections 1024;
}

http {
    include mime.types;
    default_type application/octet-stream;
    
    # Логи
    access_log /var/log/nginx/access.log;
    error_log /var/log/nginx/error.log;
    
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    
    # Сжатие
    gzip on;
    gzip_vary on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;
    
    upstream backend {
        server backend:8000;
    }
    
    server {
        listen 80;
        server_name localhost;
        
        # Увеличенный размер для загрузки видео
        client_max_body_size 500M;
        client_body_buffer_size 128k;
        
        # Таймауты для длительных запросов
        proxy_connect_timeout 600s;
        proxy_send_timeout 600s;
        proxy_read_timeout 600s;
        send_timeout 600s;
        
        # Фронтенд (статика)
        location / {
            root /usr/share/nginx/html;
            try_files $uri $uri/ /index.html;
            
            # Кэширование статики
            location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
                expires 1y;
                add_header Cache-Control "public, immutable";
            }
        }
        
        # API (проксирование на backend)
        location /api/ {
            proxy_pass http://backend/api/;
            proxy_http_version 1.1;
            
            # Заголовки
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # CORS
            add_header Access-Control-Allow-Origin *;
            add_header Access-Control-Allow-Methods "GET, POST, PATCH, PUT, DELETE, OPTIONS";
            add_header Access-Control-Allow-Headers "Content-Type, Authorization";
            
            # Preflight
            if ($request_method = OPTIONS) {
                return 204;
            }
        }
        
       # Health check
        location /health {
            access_log off;
            return 200 "OK\n";
            add_header Content-Type text/plain;
        }
    }
}
```

**Особенности**:
- Раздача статики из `/usr/share/nginx/html` (Vue build)
- Проксирование `/api/*` на FastAPI
- Увеличенные таймауты (10 минут) для длительных запросов
- CORS headers для локальной разработки
- Кэширование статических файлов (1 год)
- Gzip сжатие для текстовых файлов

---

### 6. LLM провайдеры

Система поддерживает 3 LLM провайдера (выбирается автоматически по наличию API ключа):

#### OpenRouter (рекомендуется)
- **Модели**: GPT-4 Turbo, Claude 3 Opus, Gemini Pro, Llama 3
- **URL**: `https://openrouter.ai/api/v1/chat/completions`
- **API Key**: `OPENROUTER_API_KEY` в .env
- **Стоимость**: $0.01-0.10 за запрос (зависит от модели)
- **Преимущества**: Доступ ко всем топ-моделям через один API

**Пример запроса**:
```python
response = await httpx.post(
    "https://openrouter.ai/api/v1/chat/completions",
    headers={
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "http://localhost",
        "X-Title": "Interview Prep"
    },
    json={
        "model": "openai/gpt-4-turbo",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 4000
    }
)
```

#### Google Gemini
- **Модель**: `gemini-1.5-pro`
- **URL**: `https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent`
- **API Key**: `GEMINI_API_KEY` в .env
- **Преимущество**: Огромный контекст (2M токенов), бесплатный tier
- **Ограничения**: 60 requests/min (бесплатно)

**Пример запроса**:
```python
response = await httpx.post(
    f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent?key={api_key}",
    json={
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 4000
        }
    }
)
```

#### Groq
- **Модели**: Llama 3.1 (70B/405B), Mixtral
- **URL**: `https://api.groq.com/openai/v1/chat/completions`
- **API Key**: `GROQ_API_KEY` в .env
- **Преимущество**: Очень быстрый (~500 tokens/sec), бесплатный
- **Ограничения**: 30 requests/min, меньшая точность чем GPT-4

**Пример запроса**:
```python
response = await httpx.post(
    "https://api.groq.com/openai/v1/chat/completions",
    headers={"Authorization": f"Bearer {api_key}"},
    json={
        "model": "llama-3.1-70b-versatile",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }
)
```

**Промпт для извлечения вопросов**:
```python
EXTRACTION_PROMPT = """
Ты - AI ассистент для анализа технических собеседований.
Из данного транскрипта видео извлеки ВСЕ вопросы и ответы.

ОБЯЗАТЕЛЬНЫЙ ФОРМАТ ОТВЕТА (только JSON массив):
[
  {
    "question": "Что такое замыкание в JavaScript?",
    "answer": "Замыкание - это функция вместе с лексическим окружением. Позволяет функции получать доступ к переменным из внешней области видимости даже после её завершения.",
    "technology": "JavaScript",
    "complexity": "middle"
  },
  {
    "question": "Как работает async/await?",
    "answer": "Async/await - синтаксический сахар над Promise. Async функция всегда возвращает Promise, await приостанавливает выполнение до разрешения Promise.",
    "technology": "JavaScript",
    "complexity": "middle"
  }
]

СТРОГИЕ ПРАВИЛА:
1. Извлекай ТОЛЬКО технические вопросы про код, архитектуру, алгоритмы
2. НЕ извлекай вопросы про зарплату, компанию, личные вопросы
3. Complexity выставляй по сложности ответа:
   - junior: базовые концепции (что такое переменная, цикл)
   - middle: продвинутые концепции (замыкания, промисы, ООП)
   - senior: архитектура, оптимизация, сложные паттерны
4. Technology - точное название: JavaScript, Python, React, Node.js, SQL, Docker и т.д.
5. Ответ должен быть полным, но сжатым (2-4 предложения)
6. Если в транскрипте нет технических вопросов - верни пустой массив []
7. НЕ придумывай вопросы - только из транскрипта

ТРАНСКРИПТ:
{transcript}

ВАЖНО: Ответь ТОЛЬКО JSON массивом, без дополнительного текста!
"""
```

**Логика выбора провайдера**:
```python
def _select_provider(self):
    """Выбор провайдера по наличию API ключа"""
    if os.getenv("OPENROUTER_API_KEY"):
        return "openrouter"
    elif os.getenv("GEMINI_API_KEY"):
        return "gemini"
    elif os.getenv("GROQ_API_KEY"):
        return "groq"
    else:
        raise ValueError("No LLM API key found. Set OPENROUTER_API_KEY, GEMINI_API_KEY или GROQ_API_KEY")
```

---

## 🚀 Быстрый старт

### Требования системы

| Компонент | Минимум | Рекомендуется |
|-----------|---------|---------------|
| **RAM** | 8 GB | 16 GB+ |
| **CPU** | 4 cores | 8+ cores |
| **Диск** | 15 GB | 25 GB |
| **Docker** | 20.10+ | Latest |
| **Docker Compose** | 2.0+ | Latest |
| **OS** | Windows 10/Linux/macOS | Windows 11/Ubuntu 22.04 |

**Почему такие требования?**:
- Whisper модель `large-v3`: ~3GB RAM + 2GB диск
- PostgreSQL + pgvector: ~2GB RAM
- Backend + Frontend: ~2GB RAM
- Временные файлы (аудио, видео): ~5-10GB

### Запуск за 5 минут

#### 1. Клонирование репозитория
```bash
git clone <repo-url>
cd Diploma
```

#### 2. Создание `.env` файла

Создайте файл `.env` в корне проекта:

```bash
# ============== ОБЯЗАТЕЛЬНЫЕ ==============
# База данных PostgreSQL
DATABASE_URL=postgresql://diploma:diploma123@postgres:5432/interview_prep

# ============== ОПЦИОНАЛЬНЫЕ ==============
# LLM провайдер (выберите ОДИН из трёх)

# Вариант 1: OpenRouter (рекомендуется)
# Поддерживает GPT-4, Claude, Gemini
# Регистрация: https://openrouter.ai
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxx

# Вариант 2: Google Gemini (бесплатный)
# Получить: https://makersuite.google.com/app/apikey
# GEMINI_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXX

# Вариант 3: Groq (быстрый, бесплатный)
# Получить: https://console.groq.com
# GROQ_API_KEY=gsk_XXXXXXXXXXXXXXXXXXXXXXXXXX

# ============== ДОПОЛНИТЕЛЬНЫЕ ==============
# Whisper настройки
WHISPER_MODEL=large-v3        # tiny, base, small, medium, large-v3
WHISPER_DEVICE=cpu            # cpu или cuda (для NVIDIA GPU)
WHISPER_COMPUTE_TYPE=int8     # int8 (быстрее) или float16 (точнее)

# Backend настройки
MAX_CONCURRENT_TASKS=2        # Макс. параллельных обработок видео
LOG_LEVEL=INFO                # DEBUG, INFO, WARNING, ERROR

# CORS (для локальной разработки)
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000
```

**Где получить API ключи?**:

| Провайдер | Регистрация | Бесплатный tier | Преимущества |
|-----------|-------------|-----------------|--------------|
| **OpenRouter** | [openrouter.ai](https://openrouter.ai) | $5 credits | Все топ-модели (GPT-4, Claude, Gemini) |
| **Gemini** | [makersuite.google.com](https://makersuite.google.com/app/apikey) | ✅ 60 req/min | Огромный контекст (2M tokens) |
| **Groq** | [console.groq.com](https://console.groq.com) | ✅ 30 req/min | Очень быстрый (~500 tok/sec) |

**Можно ли без LLM?** Нет, LLM критически необходим для извлечения вопросов из транскрипта. Выберите **Gemini** или **Groq** — оба бесплатные и работают хорошо.

#### 3. Запуск всех сервисов

```bash
# Запуск в фоновом режиме
docker-compose up -d

# Или с логами в консоли (для отладки)
docker-compose up
```

**Что происходит**:
1. Скачивание Docker образов (~5-10 минут при первом запуске)
2. Запуск PostgreSQL и инициализация БД
3. Запуск Backend FastAPI
4. Скачивание Whisper модели large-v3 (~3GB, 5-7 минут)
5. Запуск Frontend (Vue.js build)

#### 4. Проверка статуса сервисов

**Проверить все контейнеры**:
```bash
docker-compose ps
```

Должен быть вывод:
```
NAME               STATUS        PORTS
backend            Up            0.0.0.0:8000->8000/tcp
frontend           Up            0.0.0.0:3000->3000/tcp
postgres           Up            5432/tcp
whisper-service    Up            0.0.0.0:8001->8001/tcp
```

**Проверить логи Whisper** (самая долгая загрузка):
```bash
docker logs whisper-service -f
```

Ожидаемый вывод при успешном запуске:
```
INFO:     Loading Whisper model 'large-v3'...
INFO:     Model loaded successfully (2.87 GB)
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8001
```

**Проверить Backend**:
```bash
docker logs backend -f
```

Должно быть:
```
INFO:     Connected to database
INFO:     Whisper service: http://whisper-service:8001
INFO:     Using LLM provider: openrouter (или gemini/groq)
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

#### 5. Открытие в браузере

После успешного запуска откройте:

| URL | Описание |
|-----|----------|
| [http://localhost:3000](http://localhost:3000) | **Главная** - Публичная сторона с вопросами |
| [http://localhost:3000/admin](http://localhost:3000/admin) | **Админ-панель** - Загрузка видео, модерация |
| [http://localhost:8000/docs](http://localhost:8000/docs) | **API Docs** - Swagger UI документация |
| [http://localhost:8000/redoc](http://localhost:8000/redoc) | **ReDoc** - Альтернативная документация |

**Первый запуск**:
На публичной стороне будет пусто — нужно сначала загрузить и обработать видео через админ-панель! ⬇️

---

## 📖 Использование

### Workflow: От видео до вопросов

```
┌──────────────┐
│ 1. Админ     │  Вставляет ссылку на видео
│   загружает  │  (YouTube/VK/Rutube)
└───────┬──────┘
        │
        ▼
┌──────────────┐
│ 2. Система   │  Скачивает видео, извлекает MP3 
│   обрабатывает│  (2-5 минут)
└───────┬──────┘
        │
        ▼
┌──────────────┐
│ 3. Whisper   │  Транскрибирует аудио → текст
│   распознаёт │  (0.3x времени видео, ~10 мин для 30-мин видео)
└───────┬──────┘
        │
        ▼
┌──────────────┐
│ 4. LLM       │  Извлекает вопросы и ответы
│   парсит     │  (1-2 минуты)
└───────┬──────┘
        │
        ▼
┌──────────────┐
│ 5. База      │  Сохраняет со статусом "pending"
│   сохраняет  │
└───────┬──────┘
        │
        ▼
┌──────────────┐
│ 6. Админ     │  Проверяет и одобряет вопросы
│   модерирует │
└───────┬──────┘
        │
        ▼
┌──────────────┐
│ 7. Публично  │  Вопросы доступны на главной странице
│   доступно   │
└──────────────┘
```

### 1. Загрузка и обработка видео (Админ)

#### Шаг 1: Откройте админ-панель
```
http://localhost:3000/admin
```

#### Шаг 2: Вставьте ссылку на видео

Поддерживаемые платформы:
- ✅ **YouTube**: `https://www.youtube.com/watch?v=VIDEO_ID`
- ✅ **YouTube Short**: `https://youtu.be/VIDEO_ID`
- ✅ **VK Video**: `https://vk.com/video-12345_67890`
- ✅ **Rutube**: `https://rutube.ru/video/xxxxxx/`
- ✅ **OK.ru**: `https://ok.ru/video/12345`
- ✅ **Dailymotion**: `https://www.dailymotion.com/video/xxxxx`

**Пример видео для теста**:
```
https://www.youtube.com/watch?v=QI-bXKC2mvU
(Mock-собеседование JavaScript Junior)
```

#### Шаг 3: Нажмите "Обработать видео"

Появится карточка задачи с прогрессом:

```
┌─────────────────────────────────────────┐
│ 🎬 Mock Interview JavaScript Junior     │
│ ▓▓▓▓▓▓▓▓▓░░░░░░░░░░░░░░ 45%            │
│ 📝 Статус: Транскрибация Whisper...     │
│ ⏱️  Время: 5 мин 23 сек                 │
└─────────────────────────────────────────┘
```

**Этапы обработки**:
1. **Скачивание видео** (0-10%): Загрузка через yt-dlp
2. **Извлечение аудио** (10-20%): Конвертация в MP3
3. **Транскрибация** (20-80%): Whisper распознает речь
4. **LLM парсинг** (80-95%): Извлечение вопросов
5. **Сохранение** (95-100%): Запись в PostgreSQL

**Возможные ошибки**:
- ❌ **"HTTP 429 Too Many Requests"**: YouTube временно заблокировал IP. Подождите 10-15 минут.
- ❌ **"SSL handshake timeout"**: Проблема с сетью. Система автоматически повторит (до 10 раз).
- ❌ **"Whisper service unavailable"**: Whisper контейнер еще загружается. Проверьте `docker logs whisper-service`.
- ❌ **"LLM API key invalid"**: Проверьте правильность API ключа в `.env`.

#### Шаг 4: Дождитесь завершения

**Время обработки** (примерно):

| Длина видео | Скачивание | Whisper | LLM | Итого |
|-------------|------------|---------|-----|-------|
| 10 минут    | 1-2 мин    | 30 мин  | 1 мин | ~32 минуты |
| 30 минут    | 2-5 мин    | 90 мин  | 2 мин | ~97 минут |
| 60 минут    | 5-10 мин   | 180 мин | 3 мин | ~198 минут |

**Оптимизация**:
- **GPU вместо CPU**: Whisper на NVIDIA GPU работает в ~10x быстрее (10 мин вместо 30 мин для 10-мин видео)
- **Smaller модель**: `medium` вместо `large-v3` даёт 2x ускорение, но ниже точность для русского

**Статус завершения**:
```
┌─────────────────────────────────────────┐
│ ✅ Mock Interview JavaScript Junior     │
│ ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ 100%          │
│ 📝 Статус: Завершено                    │
│ 📊 Извлечено: 15 вопросов               │
│ ⏱️  Время обработки: 32 мин 18 сек      │
└─────────────────────────────────────────┘
```

### 2. Модерация вопросов (Админ)

После обработки все вопросы **автоматически** появляются в админ-панели со статусом **"На модерации"**.

#### Интерфейс модерации:

```
┌────────────────────────────────────────────────┐
│ 🎯 Вопрос #1              [JavaScript] [Middle]│
│                                                 │
│ Что такое замыкание в JavaScript?              │
│                                                 │
│ 💬 Ответ:                                       │
│ Замыкание - это функция вместе с лексическим   │
│ окружением. Позволяет получать доступ к        │
│ переменным из внешней области видимости даже   │
│ после завершения выполнения внешней функции.   │
│                                                 │
│ 🎬 Видео: Mock Interview JavaScript Junior     │
│ 🔗 https://youtube.com/watch?v=QI-bXKC2mvU     │
│                                                 │
│ [✅ Одобрить]  [✏️ Редактировать]  [❌ Удалить]│
└────────────────────────────────────────────────┘
```

**Действия**:
- **✅ Одобрить**: Вопрос переходит в статус `approved` и становится видимым на публичной стороне
- **✏️ Редактировать**: Исправить текст вопроса/ответа (если LLM ошибся)
- **❌ Удалить**: Перевести в статус `rejected` (не удалять из БД, просто скрыть)

**Зачем нужна модерация?**:
1. **LLM может ошибаться**: Извлечь не вопрос, а комментарий
2. **Качество ответов**: Иногда ответ слишком длинный или неполный
3. **Дубликаты**: Один вопрос может повториться в видео
4. **Нетехнические вопросы**: "Какая у вас зарплата?" нужно удалить

**Bulk действия**:
```bash
# Одобрить все вопросы по JavaScript из видео
curl -X POST http://localhost:8000/api/questions/bulk-approve \
  -H "Content-Type: application/json" \
  -d '{"video_id": 123, "technology": "JavaScript"}'
```

### 3. Публичная сторона (Пользователи)

#### Главная страница
```
http://localhost:3000
```

**Интерфейс**:
```
┌─────────────────────────────────────────────────┐
│  🔍 [Поиск по вопросам...]         [🔎 Умный поиск]│
│                                                  │
│  Технологии:                                    │
│  [JavaScript:45] [Python:32] [React:28]         │
│  [Node.js:19] [SQL:15] [Docker:12]              │
└─────────────────────────────────────────────────┘

┌────────────── Вопросы ──────────────────────────┐
│                                                  │
│  🎯 Что такое hoisting в JavaScript?  [Junior]  │
│  💬 Hoisting - это механизм поднятия...         │
│  🎬 Из видео: "JavaScript Interview 2024"       │
│  ───────────────────────────────────────────    │
│                                                  │
│  🎯 Как работает async/await?         [Middle]  │
│  💬 Async/await - синтаксический сахар...       │
│  🎬 Из видео: "Advanced JS Concepts"            │
│  ───────────────────────────────────────────    │
│                                                  │
│  [Загрузить еще 10...]                          │
└─────────────────────────────────────────────────┘
```

#### Фильтрация по технологиям

Клик на `[JavaScript:45]`:
- Показывает только вопросы по JavaScript
- URL обновляется: `?technology=JavaScript`
- Можно выбрать несколько: `?technology=JavaScript,React`

#### Умный поиск (Semantic Search)

**Обычный поиск** (по тексту):
```
"замыкание" → находит только вопросы со словом "замыкание"
```

**Умный поиск** (по смыслу):
```
"closure" → находит "замыкание в JavaScript"
"как хранить состояние" → находит "useState", "Redux", "Vuex"
"асинхронность" → находит "Promise", "async/await", "callback"
```

**Как работает**:
1. Ваш запрос → embedding (768 чисел)
2. PostgreSQL pgvector ищет похожие embeddings
3. Возвращает топ-10 самых похожих вопросов

**Пример API запроса**:
```bash
curl -X POST http://localhost:8000/api/search-similar \
  -H "Content-Type: application/json" \
  -d '{"query": "как работает useState", "limit": 10}'
```

**Ответ**:
```json
[
  {
    "id": 456,
    "question_text": "Как работает хук useState в React?",
    "answer_text": "useState - это React хук для управления...",
    "similarity": 0.87,    // 87% схожести
    "technology": "React",
    "complexity": "middle"
  },
  {
    "id": 123,
    "question_text": "Что такое React Hooks?",
    "similarity": 0.72,
    "technology": "React"
  }
]
```

#### Детальный просмотр вопроса

Клик на вопрос → открывается детальная страница:

```
┌──────────────────────────────────────────────┐
│ ← Назад к списку                             │
│                                              │
│ 🎯 Что такое замыкание в JavaScript?        │
│                                              │
│ 📚 Технология: JavaScript                   │
│ 📊 Сложность: Middle                        │
│                                              │
│ ──────────────────────────────────────────  │
│                                              │
│ 💬 Подробный ответ:                         │
│                                              │
│ Замыкание (closure) - это функция вместе    │
│ с её лексическим окружением. Когда функция  │
│ создаётся, она "запоминает" все переменные  │
│ из области видимости, в которой была        │
│ создана. Это позволяет функции получать     │
│ доступ к переменным даже после завершения   │
│ выполнения внешней функции.                 │
│                                              │
│ Пример:                                      │
│ ```javascript                                │
│ function outer() {                           │
│   let count = 0;                             │
│   return function inner() {                  │
│     count++;                                 │
│     return count;                            │
│   }                                          │
│ }                                            │
│ const counter = outer();                     │
│ counter(); // 1                              │
│ counter(); // 2                              │
│ ```                                          │
│                                              │
│ ──────────────────────────────────────────  │
│                                              │
│ 🎬 Источник:                                │
│ Mock Interview JavaScript Junior             │
│ 🔗 https://youtube.com/watch?v=QI-bXKC2mvU  │
│ ⏱️  Обработано: 18 февраля 2026, 10:30     │
│                                              │
│ ──────────────────────────────────────────  │
│                                              │
│ 🔗 Похожие вопросы:                         │
│ • Что такое scope в JavaScript?             │
│ • Как работает hoisting?                    │
│ • В чём разница между var, let, const?      │
└──────────────────────────────────────────────┘
```

---

## ⚙️ Конфигурация

### Переменные окружения (полный список)

Создайте файл `.env` в корне проекта:

```bash
# ============================================================
#  БАЗА ДАННЫХ (ОБЯЗАТЕЛЬНО)
# ============================================================
DATABASE_URL=postgresql://diploma:diploma123@postgres:5432/interview_prep
# Формат: postgresql://user:password@host:port/database

# ============================================================
#  LLM ПРОВАЙДЕРЫ (ВЫБЕРИТЕ ОДИН)
# ============================================================

# OpenRouter (рекомендуется) - Доступ ко всем топ-моделям
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxx
OPENROUTER_MODEL=openai/gpt-4-turbo  # или anthropic/claude-3-opus

# Google Gemini (бесплатный, большой контекст)
# GEMINI_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXX

# Groq (быстрый, бесплатный)
# GROQ_API_KEY=gsk_XXXXXXXXXXXXXXXXXXXXXXXXXX
# GROQ_MODEL=llama-3.1-70b-versatile  # или mixtral-8x7b-32768

# Автоопределение провайдера (auto выберет первый доступный)
LLM_PROVIDER=auto

# ============================================================
#  WHISPER SERVICE
# ============================================================
WHISPER_BASE_URL=http://whisper-service:8001
WHISPER_MODEL=large-v3    # tiny, base, small, medium, large-v3
WHISPER_DEVICE=cpu        # cpu или cuda (требуется NVIDIA GPU)
WHISPER_COMPUTE_TYPE=int8 # int8 (быстро), float16 (точно), float32

# Опции транскрипции
WHISPER_LANGUAGE=ru            # Язык по умолчанию (ru, en, auto)
WHISPER_BEAM_SIZE=5            # Точность поиска (1-10, больше = точнее but медленнее)
WHISPER_VAD_FILTER=true        # Voice Activity Detection (фильтр тишины)
WHISPER_MIN_SILENCE_MS=500     # Минимальная пауза между сегментами

# ============================================================
#  BACKEND НАСТРОЙКИ
# ============================================================
MAX_CONCURRENT_TASKS=2         # Макс. параллельных обработок видео
TASK_TIMEOUT=3600              # Таймаут обработки одного видео (сек)

# Логирование
LOG_LEVEL=INFO                 # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FORMAT=%(asctime)s - %(name)s - %(levelname)s - %(message)s

# CORS (для локальной разработки)
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000

# ============================================================
#  VIDEO DOWNLOADER (yt-dlp)
# ============================================================
YT_DLP_SOCKET_TIMEOUT=60       # Таймаут соединения (сек)
YT_DLP_RETRIES=10              # Количество повторов при ошибках
YT_DLP_FRAGMENT_RETRIES=10     # Повторы для фрагментов видео
YT_DLP_HTTP_CHUNK_SIZE=10485760  # Размер чанка (10MB)
YT_DLP_SUBTITLE_LANGS=ru       # Языки субтитров (через запятую: ru,en)

# Audio extraction
AUDIO_FORMAT=mp3               # mp3, wav, m4a
AUDIO_QUALITY=192              # Bitrate (kbps): 128, 192, 320

# ============================================================
#  SEMANTIC SEARCH
# ============================================================
EMBEDDING_MODEL=paraphrase-multilingual-mpnet-base-v2  # sentence-transformers модель
EMBEDDING_DIMENSION=768        # Размерность векторов
SIMILARITY_THRESHOLD=0.7       # Минимальная схожесть для поиска (0-1)

# ============================================================
#  POSTGRESQL
# ============================================================
POSTGRES_USER=diploma
POSTGRES_PASSWORD=diploma123
POSTGRES_DB=interview_prep
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

# Пул соединений
DB_POOL_MIN_SIZE=5
DB_POOL_MAX_SIZE=20
DB_CONNECTION_TIMEOUT=10       # Таймаут подключения (сек)

# ============================================================
#  PRODUCTION (для deployment)
# ============================================================
# HTTPS
# SSL_CERT_PATH=/etc/ssl/certs/cert.pem
# SSL_KEY_PATH=/etc/ssl/private/key.pem

# Security
# SECRET_KEY=your-secret-key-here-change-in-production
# ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Rate limiting
# RATE_LIMIT_PER_MINUTE=60
# RATE_LIMIT_PER_HOUR=1000
```

### Настройка Docker Compose

**Основной файл**: `docker-compose.yml`

**Изменить порты**:
```yaml
services:
  frontend:
    ports:
      - "3000:3000"  # Изменить на "8080:3000" чтобы открывать на :8080
  
  backend:
    ports:
      - "8000:8000"  # Изменить на "5000:8000" для :5000
```

**Включить GPU для Whisper**:
```yaml
whisper-service:
  environment:
    - WHISPER_DEVICE=cuda      # Включить GPU
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 1
            capabilities: [gpu]
```

**Изменить модель Whisper**:
```yaml
whisper-service:
  environment:
    - WHISPER_MODEL=medium     # Быстрее, но менее точно
    # или
    - WHISPER_MODEL=large-v3   # Медленно, но максимально точно
```

| Модель | Размер | Точность (русский) | Скорость (CPU) | Рекомендация |
|--------|--------|-------------------|----------------|--------------|
| tiny | 75 MB | ⭐⭐ | 8x | Только для тестов |
| base | 142 MB | ⭐⭐⭐ | 5x | Быстрые прототипы |
| small | 466 MB | ⭐⭐⭐⭐ | 2x | Баланс |
| medium | 1.5 GB | ⭐⭐⭐⭐⭐ | 1x | Хорошее качество |
| large-v3 | 2.9 GB | ⭐⭐⭐⭐⭐ | 0.3x | **Продакшн** |

**Volumes (постоянное хранение)**:
```yaml
services:
  postgres:
    volumes:
      - postgres_data:/var/lib/postgresql/data  # БД сохранится при перезапуске
  
  whisper-service:
    volumes:
      - whisper_models:/app/models              # Модель не будет загружаться заново

volumes:
  postgres_data:
  whisper_models:
```

### Настройка LLM промпта

Файл: `backend/main_new.py`, класс `LLMProcessor`

**Текущий промпт**:
```python
EXTRACTION_PROMPT = """
Ты - AI ассистент для анализа технических собеседований.
Из данного транскрипта видео извлеки ВСЕ вопросы и ответы.

[... см. выше в разделе "LLM провайдеры" ...]
"""
```

**Кастомизация промпта**:

```python
# Добавить фильтрацию по уровню (только senior вопросы)
EXTRACTION_PROMPT = """
...СТРОГИЕ ПРАВИЛА:
...
8. Извлекай ТОЛЬКО вопросы уровня senior (архитектура, оптимизация, масштабирование)
...
"""

# Добавить больше технологий
# В промпте упомянуть:
# Technology - точное название: JavaScript, TypeScript, Python, Go, Rust, 
# React, Vue, Angular, Node.js, Django, FastAPI, SQL, PostgreSQL, MongoDB, 
# Docker, Kubernetes, AWS, GCP, CI/CD, GraphQL, gRPC и т.д.

# Изменить формат ответа (добавить примеры кода)
[
  {
    "question": "Что такое hoisting?",
    "answer": "Hoisting...",
    "code_example": "function test() { console.log(x); var x = 10; }",
    "technology": "JavaScript",
    "complexity": "junior"
  }
]
```

### Мониторинг и логи

**Просмотр логов всех сервисов**:
```bash
docker-compose logs -f

# Только backend
docker-compose logs -f backend

# Только whisper
docker-compose logs -f whisper-service

# Последние 100 строк
docker-compose logs --tail=100 backend
```

**Ресурсы контейнеров**:
```bash
docker stats
```

Вывод:
```
CONTAINER       CPU %     MEM USAGE / LIMIT     NET I/O
backend         5.2%      450MB / 2GB           1.2MB / 800KB
whisper-service 85.3%     3.1GB / 8GB           5MB / 2MB
postgres        2.1%      250MB / 1GB           500KB / 300KB
frontend        0.5%      100MB / 512MB         100KB / 50KB
```

**Whisper использует много CPU?** — Это нормально при транскрибации. Если CPU 100% постоянно, то либо:
1. Очередь задач слишком большая → уменьшить `MAX_CONCURRENT_TASKS`
2. Нужен GPU → добавить NVIDIA GPU и изменить `WHISPER_DEVICE=cuda`

**Backend падает с OOM (Out of Memory)?**:
```bash
# Увеличить лимит памяти
docker-compose.yml:
  backend:
    deploy:
      resources:
        limits:
          memory: 4G  # Было 2G, стало 4G
```

---

**processed_videos** - Обработанные видео:
```sql
id, video_id, youtube_url, platform, 
title, transcript, questions_count, processed_at
```

**processing_tasks** - Задачи обработки:
```sql
id, youtube_url, status, progress, 
current_step, result, error_message, client_id
```

### Миграции

Схема автоматически применяется при первом запуске. Для изменения схемы отредактируйте `scripts/init-db.sql` и пересоздайте БД:

```bash
docker-compose down -v
docker-compose up -d
```

---

## 🔧 Troubleshooting

### Whisper долго загружается

Модель large-v3 весит ~3 GB. При первом запуске она скачивается из HuggingFace. Проверьте логи:
```bash
docker logs diploma-whisper-worker -f
```

### Ошибка при скачивании видео

**SSLTimeout**: Увеличьте `socket_timeout` в `backend/video_downloader.py`  
**HTTP 429**: YouTube блокирует запросы — подождите 10-15 минут

### Недостаточно памяти

Whisper large-v3 требует ~8 GB RAM. Если памяти мало, измените модель на `medium` или `small`:

```yaml
# docker-compose.yml
whisper-worker:
  environment:
    - MODEL_SIZE=medium  # вместо large-v3
```

### Порты заняты

Если порты 3000, 8000, 8001 заняты, измените в `docker-compose.yml`:

```yaml
frontend:
  ports:
    - "3001:3000"  # Внешний:Внутренний

backend:
  ports:
    - "8001:8000"
```

---

## 🎨 Дизайн и UI

### Технологии фронтенда

- **Vue 3** - Composition API
- **Vite** - Быстрая сборка
- **Vuex** - State management
- **Vue Router** - Маршрутизация
- **Axios** - HTTP клиент

### Анимации

- Glassmorphism эффекты
- Gradient анимации
- Hover эффекты с glow
- Плавные переходы между страницами

---

## 📝 API Endpoints

### Публичные

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/api/questions` | Получить одобренные вопросы |
| POST | `/api/search` | Семантический поиск вопросов |
| GET | `/health` | Проверка здоровья системы |

### Админ

| Метод | Endpoint | Описание |
|-------|----------|----------|
| POST | `/api/process-video` | Запустить обработку видео |
| GET | `/api/admin/questions` | Все вопросы (включая неодобренные) |
| PUT | `/api/questions/{id}` | Обновить вопрос |
| DELETE | `/api/questions/{id}` | Удалить вопрос |
| GET | `/api/task/{task_id}` | Статус обработки видео |

### Whisper

| Метод | Endpoint | Описание |
|-------|----------|----------|
| POST | `/transcribe-path` | Транскрибировать аудиофайл |
| GET | `/health` | Проверка модели |

---

## 🔐 Безопасность

### Текущая версия (разработка)

- ❌ Нет аутентификации
- ❌ Нет авторизации
- ❌ API полностью открыт

### Для продакшена

Добавьте:
1. JWT токены для API
2. OAuth2 для админ-панели
3. Rate limiting
4. CORS настройки
5. HTTPS сертификаты
6. Environment secrets вместо .env

---

## 📈 Производительность

### Рекомендуемые ресурсы

| Компонент | CPU | RAM | Диск |
|-----------|-----|-----|------|
| Whisper | 8-10 потоков | 8 GB | 5 GB |
| Backend | 2 ядра | 2 GB | 1 GB |
| Frontend | 1 ядро | 512 MB | 500 MB |
| PostgreSQL | 2 ядра | 2 GB | 10 GB |
| Redis | 1 ядро | 512 MB | 1 GB |
| **Итого** | **4-6 ядер** | **16 GB** | **20 GB** |

### Оптимизации

- **Pip cache** в Dockerfile - библиотеки не скачиваются повторно
- **Volume mounts** - изменения кода без пересборки
- **Retries** в yt-dlp - автоповторы при ошибках загрузки
- **Embeddings кэш** - быстрый семантический поиск

---

## 🚢 Deployment

### Docker Hub

```bash
# Build images
docker-compose build

# Tag
docker tag diploma-backend:latest username/interview-backend:latest
docker tag diploma-frontend:latest username/interview-frontend:latest
docker tag diploma-whisper:latest username/interview-whisper:latest

# Push
docker push username/interview-backend:latest
docker push username/interview-frontend:latest
docker push username/interview-whisper:latest
```

### Production docker-compose

```yaml
version: '3.8'

services:
  backend:
    image: username/interview-backend:latest
    restart: always
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/prod_db
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis
      
  # ... остальные сервисы
```

---

## 📦 Технологический стек

### Backend
- **FastAPI** - Веб-фреймворк
- **asyncpg** - Async PostgreSQL драйвер
- **redis-py** - Redis клиент
- **yt-dlp** - Загрузка видео
- **httpx** - HTTP клиент
- **sentence-transformers** - Embeddings для поиска

### AI/ML
- **faster-whisper** - Транскрипция (Whisper large-v3)
- **OpenRouter/Gemini/Groq** - LLM для извлечения вопросов

### Frontend
- **Vue 3** - UI фреймворк
- **Vite** - Build tool
- **Vuex** - State management
- **Axios** - HTTP клиент

### Инфраструктура
- **Docker** - Контейнеризация
- **Docker Compose** - Оркестрация
- **PostgreSQL 15** - База данных
- **Redis 7** - Кэш и очереди
- **Nginx** - Reverse proxy (опционально)

---

## 🤝 Вклад в проект

### Roadmap

- [ ] Аутентификация и авторизация
- [ ] Поддержка GPU для Whisper
- [ ] Экспорт вопросов в Anki
- [ ] Telegram бот для практики
- [ ] Статистика прогресса пользователя
- [ ] Темная/светлая тема
- [ ] Мобильное приложение

### Как внести вклад

1. Fork репозитория
2. Создайте ветку: `git checkout -b feature/amazing-feature`
3. Commit изменений: `git commit -m 'Add amazing feature'`
4. Push в ветку: `git push origin feature/amazing-feature`
5. Откройте Pull Request

---

## 📄 Лицензия

MIT License - используйте свободно для любых целей.

---

## 📞 Поддержка

Возникли проблемы? 

1. Проверьте [Troubleshooting](#-troubleshooting)
2. Посмотрите логи: `docker-compose logs`
3. Откройте Issue на GitHub

---

## 🎓 Использованные ресурсы

- [faster-whisper](https://github.com/guillaumekln/faster-whisper) - Whisper оптимизация
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - Загрузка видео
- [FastAPI](https://fastapi.tiangolo.com/) - Backend фреймворк
- [Vue 3](https://vuejs.org/) - Frontend фреймворк

---

**Made with ❤️ for Russian IT community**
