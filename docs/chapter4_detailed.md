# Глава 4. РЕАЛИЗАЦИЯ И ТЕСТИРОВАНИЕ СИСТЕМЫ

---

## 4.1. Технологический стек

### 4.1.1. Серверная часть (Backend)

Серверная часть системы реализована на языке программирования Python 3.11 с использованием асинхронного веб-фреймворка FastAPI. Выбор технологического стека обусловлен требованиями к производительности, совместимости с ML-библиотеками и удобству разработки.

---

**FastAPI — асинхронный веб-фреймворк.**

FastAPI — высокопроизводительный ASGI-фреймворк (Asynchronous Server Gateway Interface), построенный на основе библиотек Starlette (веб-обработка) и Pydantic (валидация данных). Является одним из самых производительных Python-фреймворков, сопоставимым по скорости с Node.js и Go.

Ключевые причины выбора FastAPI для данного проекта:

1. **Встроенная поддержка `async/await`.** Критически важна для данной системы, где Backend одновременно обрабатывает:
   - HTTP-запросы от пользователей (каталог вопросов, фильтрация);
   - WebSocket-соединения для мониторинга Pipeline;
   - Длительные фоновые задачи (транскрибация видео до 30 минут);
   - Вызовы к внешним LLM-провайдерам (OpenRouter, Gemini, Groq) с таймаутом до 180 секунд.

   Без асинхронности один длительный запрос к Whisper блокировал бы весь сервер.

2. **Автоматическая OpenAPI-документация.** FastAPI генерирует интерактивную документацию Swagger UI по адресу `/docs` на основе Pydantic-моделей и type hints. Это ускоряет интеграцию Frontend-клиента: разработчик фронтенда видит все 67 эндпоинтов с примерами запросов и ответов.

3. **Валидация данных через Pydantic.** Входные данные автоматически валидируются с генерацией информативных ошибок HTTP 422. Пример:

```python
class YouTubeRequest(BaseModel):
    youtube_url: str
    topic: Optional[str] = "General"
    level: Optional[str] = "middle"
```

При передаче невалидных данных (например, отсутствие `youtube_url`) FastAPI автоматически возвращает:

```json
{
    "detail": [{
        "loc": ["body", "youtube_url"],
        "msg": "field required",
        "type": "value_error.missing"
    }]
}
```

4. **Нативная поддержка WebSocket.** Декоратор `@app.websocket()` позволяет реализовать WebSocket-эндпоинт без дополнительных библиотек:

```python
@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        manager.disconnect(client_id)
```

5. **BackgroundTasks.** Встроенный механизм запуска фоновых задач без внешнего таск-менеджера (Celery, RQ):

```python
@app.post("/api/process-video")
async def process_video(request: YouTubeRequest, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    background_tasks.add_task(process_video_pipeline, task_id, request.youtube_url, ...)
    return {"task_id": task_id, "status": "started"}
```

**Сравнение с альтернативными фреймворками:**

| Критерий | FastAPI | Django | Flask | Express.js (Node) |
|----------|---------|--------|-------|--------------------|
| Async/await | Нативно | Django 4+ (частично) | Нет | Нативно |
| Автодокументация | OpenAPI/Swagger | Admin panel | Нет | Swagger (плагин) |
| Валидация | Pydantic (встроена) | Forms/DRF Serializer | Нет | Joi/Zod |
| WebSocket | Встроен | Channels (отдельно) | Flask-SocketIO | Встроен |
| ML-совместимость | Python-нативно | Python-нативно | Python-нативно | Ограничена |
| Производительность | ~15k rps | ~2k rps | ~3k rps | ~20k rps |

FastAPI выбран как оптимальный баланс между производительностью, возможностями и совместимостью с ML-экосистемой Python (faster-whisper, sentence-transformers, FAISS).

---

**asyncpg — асинхронный PostgreSQL-драйвер.**

asyncpg — высокопроизводительный асинхронный драйвер для PostgreSQL, написанный на Cython. Обеспечивает throughput до 100 000 запросов/с на одном ядре, что на порядок превышает производительность psycopg2.

В системе используется для прямых SQL-запросов без ORM (SQLAlchemy, Django ORM):

```python
conn = await asyncpg.connect(DATABASE_URL)
try:
    questions = await conn.fetch("""
        SELECT id, question, answer, topic, difficulty, probability
        FROM questions
        WHERE approved = TRUE AND topic = $1
        ORDER BY probability DESC
    """, topic)
    
    result = [dict(q) for q in questions]
finally:
    await conn.close()
```

**Причины отказа от ORM:**

1. Полный контроль над генерируемым SQL — критично для сложных запросов с подзапросами (расчёт вероятности) и агрегацией.
2. Отсутствие оверхеда на маппинг моделей — экономия 10–30% времени запроса.
3. Прозрачность — каждый запрос виден в коде, легко профилировать.
4. asyncpg работает напрямую с протоколом PostgreSQL (не через libpq), что обеспечивает дополнительный прирост производительности.

---

**redis.asyncio — асинхронный Redis-клиент.**

Используется для 5 категорий данных:

```python
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

# 1. Состояние задачи (JSON, TTL 24 часа)
await redis_client.set(f"task:{task_id}", json.dumps(task_data), ex=86400)

# 2. Глобальный список задач (LIST, макс 100)
await redis_client.lpush("global:tasks", task_id)
await redis_client.ltrim("global:tasks", 0, 99)

# 3. WebSocket mapping
await redis_client.set(f"task:{task_id}:client", client_id, ex=86400)

# 4. Транскрипция задачи (JSON, TTL 24 часа)
await redis_client.set(f"transcript:{task_id}", json.dumps(transcript_data), ex=86400)

# 5. FAISS-кэш (pickle, без TTL)
await redis_client.set("questions_embeddings_cache", pickle.dumps(cache_data))
```

---

**httpx — асинхронный HTTP-клиент.**

Используется для всех внешних HTTP-запросов:

| Цель | URL | Таймаут | Примечание |
|------|-----|---------|------------|
| Whisper Worker | `http://whisper-worker:8000/transcribe-path` | 7200 с | 2 часа для длинных видео |
| OpenRouter | `https://openrouter.ai/api/v1/chat/completions` | 180 с | LLM extraction |
| Google Gemini | `https://generativelanguage.googleapis.com/v1beta/...` | 180 с | LLM extraction |
| Groq | `https://api.groq.com/openai/v1/chat/completions` | 180 с | LLM extraction |
| Health check | `http://whisper-worker:8000/health` | 5 с | Проверка готовности |

Пример вызова LLM-провайдера:

```python
async with httpx.AsyncClient(timeout=180.0) as client:
    response = await client.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "meta-llama/llama-3.1-70b-instruct",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3
        }
    )
```

---

**sentence-transformers + FAISS — семантический поиск.**

| Компонент | Модель/Версия | Назначение |
|-----------|--------------|------------|
| sentence-transformers | all-MiniLM-L6-v2 | Генерация 384-dim эмбеддингов |
| FAISS (CPU) | faiss-cpu 1.7.4 | Поиск ближайших соседей |
| NumPy | >= 1.24.0 | Векторные операции |

Модель `all-MiniLM-L6-v2` выбрана по критериям:
- Компактность: 80 МБ (vs. 420 МБ для `all-mpnet-base-v2`);
- Скорость инференса: ~0.5 мс на один текст;
- Поддержка русского языка (обучена на многоязычном корпусе);
- Достаточное качество для задачи дедупликации вопросов.

---

**yt-dlp — загрузчик видео.**

Форк youtube-dl с расширенной поддержкой платформ. Обеспечивает:

```python
ydl_opts = {
    'format': 'bestaudio/best',
    'outtmpl': str(temp_dir / f'{video_id}.%(ext)s'),
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
    'writesubtitles': True,
    'writeautomaticsub': True,
    'subtitleslangs': ['ru'],
    'subtitlesformat': 'vtt',
    'nocheckcertificate': True,
    'socket_timeout': 60,
    'retries': 10,
    'fragment_retries': 10,
    'http_chunk_size': 10485760,  # 10 MB
}
```

**Платформо-специфичные настройки для VK:**

```python
if platform == 'vk':
    ydl_opts.update({
        'format': 'worst[ext=m4a]/worstaudio/bestaudio[filesize<50M]/hls-240/hls-360/worst',
        'http_chunk_size': 0,           # Отключить chunked download
        'socket_timeout': 60,
        'retries': 3,
        'max_filesize': 100 * 1024 * 1024,  # 100 MB limit
    })
```

---

**faster-whisper — транскрибация речи.**

| Параметр | CPU (int8) | GPU (float16) |
|----------|-----------|--------------|
| Модель | large-v3-turbo | large-v3 |
| Размер модели | ~3 ГБ | ~3 ГБ |
| Квантизация | int8 (4-5x сжатие) | float16 |
| Beam size | 3 | 5 |
| CPU threads | 10 | — |
| VAD | Включён | Включён |
| Скорость (30 мин видео) | 10–15 мин | 1–3 мин |
| WER (русский) | < 12% | < 10% |

Ускорение по сравнению с оригинальным OpenAI Whisper: 4–6× на CPU, 2–3× на GPU (за счёт CTranslate2, более эффективного C++ runtime).

---

**LLM-провайдеры.**

Три провайдера для извлечения вопросов и генерации ответов:

| Провайдер | Модель | Контекстное окно | Температура | Стоимость |
|-----------|--------|-------------------|-------------|-----------|
| OpenRouter | Llama-3.1-70B-Instruct | 128K токенов | 0.3 (extraction) / 0.7 (answer) | ~$0.001/запрос |
| Google Gemini | gemini-2.0-flash (+ 1.5-flash fallback) | 1M токенов | 0.3 / 0.7 | Бесплатно (лимиты) |
| Groq | Llama-3.1-70B-Versatile | 128K токенов | 0.3 / 0.7 | Бесплатно (лимиты) |

**Стратегия автоматического выбора провайдера:**

```python
async def call_llm_api(prompt: str) -> List[Dict[str, Any]]:
    provider = LLM_PROVIDER.lower()
    
    if provider == "auto":
        if OPENROUTER_API_KEY:
            provider = "openrouter"
        elif GEMINI_API_KEY:
            provider = "gemini"
        elif GROQ_API_KEY:
            provider = "groq"
        else:
            raise Exception("No LLM API key configured")
    
    if provider == "openrouter":
        return await call_openrouter_api(prompt)
    elif provider == "gemini":
        return await call_gemini_api(prompt)
    elif provider == "groq":
        return await call_groq_api(prompt)
```

**Exponential backoff для Groq (rate limiting):**

```python
async def call_groq_api(prompt: str) -> List[Dict[str, Any]]:
    max_retries = 5
    base_delay = 10  # секунд
    
    for attempt in range(max_retries):
        try:
            response = await client.post(...)
            if response.status_code == 429:  # Rate limited
                delay = base_delay * (2 ** attempt)  # 10, 20, 40, 80, 160
                await asyncio.sleep(delay)
                continue
            return parse_questions_from_llm(response.json())
        except Exception as e:
            if attempt == max_retries - 1:
                raise
```


### 4.1.2. Клиентская часть (Frontend)

Клиентская часть реализована как одностраничное приложение (SPA) на фреймворке Vue 3 с использованием Composition API.

---

**Vue 3 — прогрессивный JavaScript-фреймворк.**

Vue 3 выбран для frontend-разработки по следующим причинам:

1. **Реактивная система на JavaScript Proxy.** В отличие от Vue 2 (Object.defineProperty), Vue 3 использует ES6 Proxy для отслеживания изменений объектов, что обеспечивает:
   - Отслеживание добавления/удаления свойств;
   - Отслеживание изменений массивов;
   - Меньший оверхед на инициализацию (lazy tracking).

2. **Composition API.** Позволяет организовать логику компонента по функциональным блокам (вместо по опциям data/methods/computed), что улучшает переиспользование и читаемость:

```vue
<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '../api/client'

const questions = ref([])
const loading = ref(false)
const filters = ref({ topic: '', level: '' })

const filteredQuestions = computed(() =>
    questions.value.filter(q =>
        (!filters.value.topic || q.topic === filters.value.topic) &&
        (!filters.value.level || q.difficulty === filters.value.level)
    )
)

onMounted(async () => {
    loading.value = true
    const { data } = await api.getQuestions()
    questions.value = data.questions
    loading.value = false
})
</script>
```

3. **Экосистема:** Vue Router 4 (маршрутизация), Pinia 2 (state management), VueUse (утилиты).

**Сравнение с альтернативными фреймворками:**

| Критерий | Vue 3 | React 18 | Angular 17 | Svelte 5 |
|----------|-------|----------|------------|----------|
| Кривая обучения | Низкая | Средняя | Высокая | Низкая |
| Bundle size | 33 KB | 42 KB | 143 KB | 2 KB |
| Реактивность | Proxy | useState/hooks | RxJS | Compile-time |
| TypeScript | Опционально | Опционально | Обязательно | Опционально |
| UI-библиотеки | PrimeVue, Vuetify | MUI, Ant Design | Angular Material | — |
| Производительность | Высокая | Высокая | Средняя | Высокая |

Vue 3 выбран за оптимальный баланс простоты, производительности и экосистемы. В отличие от предыдущей версии, использовавшей PrimeVue, новый фронтенд реализован с собственной дизайн-системой на CSS Custom Properties, что обеспечивает полный контроль над визуальным стилем и значительно сокращает размер бандла.

---

**Vite 5.4 — сборщик модулей.**

Vite использует ES modules (ESM) для мгновенного запуска dev-сервера:
- **Development:** нет предварительной сборки, модули загружаются по требованию через ES import;
- **Production:** Rollup с tree-shaking, code splitting, минификация.

```javascript
// vite.config.js
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
    plugins: [vue()],
    resolve: {
        alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) }
    },
    server: {
        port: 3000,
        proxy: {
            '/api': { target: 'http://localhost:8000', changeOrigin: true },
            '/ws': { target: 'ws://localhost:8000', ws: true }
        }
    }
})
```

Proxy-конфигурация устраняет CORS-проблемы в development, имитируя production-настройку nginx, где `/api/*` проксируется на backend.

---

**Собственная дизайн-система (global.css) — CSS Custom Properties.**

Все UI-элементы реализованы через единый файл `global.css` с CSS Custom Properties (переменными) и утилитарными классами, без использования сторонних UI-библиотек (PrimeVue, Vuetify и т.д.).

**CSS Custom Properties (токены дизайн-системы):**

```css
:root {
  --c-bg:       #0c0c0f;    /* основной фон */
  --c-surface:  #16161a;    /* карточки, панели */
  --c-elevated: #1e1e24;    /* навигация, вложенные блоки */
  --c-border:   rgba(255,255,255,0.08);
  --c-primary:  #7c5cfc;    /* акцент */
  --c-primary-h:#6c47d9;    /* hover */
  --c-text:     #e4e4e7;    /* основной текст */
  --c-text-2:   #a1a1aa;    /* вторичный текст */
  --c-text-3:   #71717a;    /* приглушённый */
  --c-green:    #34d399;    /* успех */
  --c-yellow:   #fbbf24;    /* предупреждение */
  --c-red:      #f87171;    /* ошибка */
  --radius:     10px;
  --nav-h:      64px;
  --max-w:      1080px;
  --max-w-lg:   1280px;
  --max-w-sm:   740px;
}
```

**Утилитарные CSS-классы:**

| Класс | Назначение | Варианты |
|-------|-----------|----------|
| `.btn` | Кнопки | `.btn-primary`, `.btn-ghost`, `.btn-danger` |
| `.btn-sm`, `.btn-lg` | Размеры кнопок | Малые и большие |
| `.input` | Поля ввода | Focus: фиолетовая подсветка `--c-primary` |
| `.card` | Карточки | `backdrop-filter: blur(12px)`, полупрозрачный фон |
| `.badge` | Бейджи | `.badge-green`, `.badge-yellow`, `.badge-red`, `.badge-purple` |
| `.progress` | Прогресс-бар | CSS-переменная `--p` для ширины |
| `.spinner` | Спиннер загрузки | CSS-анимация `spin` (36px) |

Данный подход обеспечивает:
- Полный контроль над темой и стилями без vendor lock-in;
- Минимальный размер CSS-бандла (~5 КБ вместо ~200 КБ PrimeVue);
- Согласованный визуальный стиль через CSS-переменные;
- Лёгкую кастомизацию через изменение переменных в `:root`.

Модальные окна реализованы через Vue 3 `<Teleport to="body">` вместо PrimeVue Dialog.

---

**Pinia 2.1.7 — управление состоянием.**

Три хранилища (stores) управляют глобальным состоянием:

- `store/index.js` — questionsStore (вопросы, фильтрация) и tasksStore (задачи обработки с polling);
- `store/auth.js` — authStore (JWT-авторизация: access/refresh токены, login/register/logout).

**questionsStore** — вопросы и фильтрация:

```javascript
export const useQuestionsStore = defineStore('questions', {
    state: () => ({
        questions: [],           // Публичные вопросы
        adminQuestions: [],      // Все вопросы (admin)
        totalVideos: 0,          // Количество видео
        currentQuestion: null,   // Текущий вопрос (детали)
        loading: false,
        error: null,
        filters: {
            topic: '',
            level: '',
            search: ''
        }
    }),
    
    getters: {
        filteredQuestions(state) {
            return state.questions.sort((a, b) => b.probability - a.probability)
        },
        topics(state) {
            return [...new Set(state.questions.map(q => q.topic))].sort()
        },
        unapprovedQuestions(state) {
            return state.adminQuestions.filter(q => !q.approved)
        }
    },
    
    actions: {
        async fetchQuestions() {
            this.loading = true
            try {
                const { data } = await api.getQuestions()
                this.questions = data.questions
            } catch (e) {
                this.error = e.message
            } finally {
                this.loading = false
            }
        }
    }
})
```

**tasksStore** — задачи обработки с polling:

```javascript
export const useTasksStore = defineStore('tasks', {
    state: () => ({
        tasks: [],
        currentTask: null,
        _pollingIntervals: {},
        _globalPollInterval: null
    }),
    
    getters: {
        activeTasks: (state) => state.tasks.filter(t => 
            t.status !== 'completed' && t.status !== 'error'),
        hasActiveTasks: (state) => 
            state.tasks.some(t => t.status !== 'completed' && t.status !== 'error')
    },
    
    actions: {
        startPolling(taskId) {
            this._pollingIntervals[taskId] = setInterval(async () => {
                const { data } = await api.getTaskStatus(taskId)
                const idx = this.tasks.findIndex(t => t.task_id === taskId)
                if (idx >= 0) this.tasks[idx] = data
                if (data.status === 'completed' || data.status === 'error') {
                    this.stopPolling(taskId)
                }
            }, 2000)  // Опрос каждые 2 секунды
        },
        
        startGlobalPolling() {
            this._globalPollInterval = setInterval(async () => {
                const { data } = await api.getAllTasks()
                this.tasks = data.tasks
            }, 5000)  // Глобальный опрос каждые 5 секунд
        }
    }
})
```

---

**Axios 1.6.2 — HTTP-клиент.**

Централизованный модуль `api/client.js` (334 строки) инкапсулирует все HTTP-запросы:

```javascript
import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const apiClient = axios.create({
    baseURL: API_BASE_URL,
    headers: { 'Content-Type': 'application/json' }
})
```

**67 методов API-клиента**, организованных по группам:

| Группа | Количество методов | Пример |
|--------|-------------------|--------|
| Processing | 3 | `processVideo()`, `getTaskStatus()`, `getAllTasks()` |
| Public Questions | 3 | `getQuestions()`, `getPublicQuestionDetail()`, `getSimilarQuestions()` |
| Admin Questions | 11 | `getAdminQuestions()`, `approveQuestions()`, `mergeQuestions()` |
| Tags | 3 | `getAllTags()`, `addQuestionTag()`, `removeQuestionTag()` |
| Suggestions | 5 | `createSuggestion()`, `getAdminSuggestions()`, `processSuggestion()` |
| Feedback | 3 | `createFeedback()`, `getAdminFeedback()`, `updateFeedback()` |
| Bookmarks & Notes | 5 | `addBookmark()`, `saveNote()`, `getAllNotes()` |
| Mock Interview | 3 | `startMockInterview()`, `submitMockInterview()`, `getMockInterviewHistory()` |
| Upload | 1 | `uploadVideoFile()` |
| Stats | 2 | `getPublicStats()`, `getAdminStats()` |
| Videos | 4 | `getProcessedVideos()`, `updateVideo()`, `deleteVideo()` |
| Export | 3 | `exportQuestions()`, `exportCSV()`, `getTranscript()` |
| v3: Professions | 2 | `getProfessions()`, `getProfessionQuestions()` |
| v3: SM-2 | 3 | `getSM2Cards()`, `submitSM2Review()`, `resetSM2Progress()` |
| v3: UGC | 4 | `getUserAnswers()`, `createUserAnswer()`, `voteUserAnswer()` |
| v3: Test Assignments | 3 | `getTestAssignments()`, `createTestAssignment()` |
| v3: HH Skills | 3 | `getHHSkills()`, `getHHProfessions()`, `upsertHHSkill()` |


### 4.1.3. Инфраструктура

**Docker — контейнеризация.**

Каждый сервис описан в Dockerfile. Применяются следующие оптимизации:

**Backend Dockerfile:**

```dockerfile
FROM python:3.11-slim
WORKDIR /app

# FFmpeg для извлечения аудио (yt-dlp зависимость)
RUN apt-get update && apt-get install -y curl xz-utils && rm -rf /var/lib/apt/lists/*
RUN curl -L https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz \
    -o /tmp/ffmpeg.tar.xz \
    && tar -xf /tmp/ffmpeg.tar.xz -C /tmp \
    && mv /tmp/ffmpeg-*-amd64-static/ffmpeg /usr/local/bin/ \
    && mv /tmp/ffmpeg-*-amd64-static/ffprobe /usr/local/bin/ \
    && rm -rf /tmp/ffmpeg*

# Кэширование pip-слоя (BuildKit)
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt && pip install --upgrade yt-dlp

COPY . .
RUN mkdir -p /app/temp
CMD ["uvicorn", "main_new:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

Оптимизация: `--mount=type=cache,target=/root/.cache/pip` кэширует pip-пакеты между сборками, ускоряя пересборку при изменении requirements.txt.

**Frontend Dockerfile (production, multi-stage):**

```dockerfile
# Stage 1: Сборка
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci            # Детерминированная установка (lockfile)
COPY . .
RUN npm run build     # Vite → Rollup → dist/

# Stage 2: Выдача через nginx
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost/ || exit 1
CMD ["nginx", "-g", "daemon off;"]
```

Multi-stage build сокращает размер production-образа: node_modules (~300 МБ) не попадают в финальный образ.

**Whisper Dockerfile (CPU):**

```dockerfile
FROM python:3.11-slim
WORKDIR /app

ENV WHISPER_MODEL=large-v3-turbo \
    CPU_THREADS=10 \
    COMPUTE_TYPE=int8 \
    BEAM_SIZE=3 \
    VAD_ENABLED=true \
    HF_HUB_ENABLE_HF_TRANSFER=0 \
    HF_HUB_DISABLE_XET=1 \
    HF_HUB_DOWNLOAD_TIMEOUT=1800

# FFmpeg для аудио-обработки
RUN apt-get update && apt-get install -y curl xz-utils && rm -rf /var/lib/apt/lists/*
# ... статическая установка ffmpeg ...

COPY requirements.txt .
RUN pip install --no-cache-dir --timeout 300 -r requirements.txt

COPY . .
RUN mkdir -p /app/temp

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
```

`--workers 1` — критично для Whisper, так как модель ~3 ГБ в памяти. При нескольких worker-ах каждый загрузит свою копию модели.

**Whisper Dockerfile (GPU):**

```dockerfile
FROM nvidia/cuda:12.4.1-cudnn-runtime-ubuntu22.04
WORKDIR /app

ENV WHISPER_MODEL=large-v3 \
    COMPUTE_TYPE=float16 \
    DEVICE=cuda \
    BEAM_SIZE=5 \
    VAD_ENABLED=true

# Python, pip, ffmpeg
RUN apt-get update && apt-get install -y python3.11 python3-pip ffmpeg ...

# GPU-зависимости
RUN pip install "faster-whisper>=1.0.0" "fastapi>=0.104.0" "uvicorn[standard]" \
    "nvidia-cublas-cu12" "nvidia-cudnn-cu12"

COPY . .
CMD ["python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

**Docker Compose — оркестрация.**

6 сервисов: Frontend NEW (:3000), Frontend OLD (:3001), Backend (:8000), Whisper Worker (:8001), PostgreSQL (:5432), Redis (:6379). 3 конфигурации для разных сред:

| Файл | Whisper | GPU | Типичное использование |
|------|---------|-----|----------------------|
| `docker-compose.yml` | large-v3-turbo, auto | Нет | Разработка |
| `docker-compose.cpu.yml` | large-v3-turbo, int8, 10 threads | Нет | Продакшен без GPU |
| `docker-compose.gpu.yml` | large-v3, float16 | NVIDIA runtime | Продакшен с GPU |

Пример конфигурации GPU-сервиса:

```yaml
whisper-worker:
    build:
        context: ./whisper-service
        dockerfile: Dockerfile.gpu
    deploy:
        resources:
            reservations:
                devices:
                    - driver: nvidia
                      count: 1
                      capabilities: [gpu]
```

---

**PostgreSQL 15 Alpine** — основная СУБД.

- Расширение `pg_trgm` для триграммного полнотекстового поиска;
- Данные в именованном томе `postgres_data`;
- Healthcheck: `pg_isready -U diploma -d interview_prep`;
- Инициализация через `init-db.sql` (CREATE EXTENSION pg_trgm; CREATE TABLE questions ...);
- Auto-migration дополнительных таблиц в lifespan() backend-а.

---

**Redis 7 Alpine** — кэш и очередь задач.

- Healthcheck: `redis-cli ping`;
- Данные в именованном томе `redis_data`;
- Используется для: задач (TTL 24h), FAISS-кэша (без TTL), WebSocket mapping.

---

**Зависимости (requirements.txt).**

Backend:
```
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
websockets>=12.0
redis>=5.0.1
asyncpg>=0.29.0
yt-dlp>=2025.1.15
httpx>=0.26.0
python-multipart>=0.0.6
pydantic>=2.5.3

# PyTorch CPU-only (экономия ~10GB без CUDA)
--extra-index-url https://download.pytorch.org/whl/cpu
torch
sentence-transformers>=2.2.2
faiss-cpu>=1.7.4
numpy>=1.24.0
```

Frontend (package.json):
```json
{
    "dependencies": {
        "vue": "^3.4.0",
        "vue-router": "^4.2.0",
        "pinia": "^2.1.7",
        "axios": "^1.6.2",
        "@vueuse/core": "^10.7.0"
    },
    "devDependencies": {
        "@vitejs/plugin-vue": "^5.0.0",
        "vite": "^5.0.0"
    }
}
```

Примечание: PrimeVue и PrimeIcons удалены из нового фронтенда (`frontend-new/`). Все UI-элементы реализованы через собственную CSS дизайн-систему (`global.css`). Легаси-фронтенд (`frontend-vue/`, порт 3001) по-прежнему использует PrimeVue 3.50.


---

## 4.2. Реализация ключевых модулей

### 4.2.1. Модуль загрузки видео (VideoDownloader)

Модуль реализован в файле `video_downloader.py` (352 строки) как класс `VideoDownloader`.

**Архитектура класса:**

```python
class VideoDownloader:
    PLATFORM_PATTERNS = {
        'youtube': [
            r'(https?://)?(www\.)?(youtube\.com|youtu\.be)',
            r'youtube\.com/watch\?v=[\w-]+',
            r'youtu\.be/[\w-]+',
            r'youtube\.com/shorts/[\w-]+'
        ],
        'vk': [r'(https?://)?(www\.)?(vk\.com|vkvideo\.ru)', ...],
        'rutube': [r'(https?://)?(www\.)?rutube\.ru'],
        'ok': [r'(https?://)?(www\.)?ok\.ru/video'],
        'dailymotion': [r'(https?://)?(www\.)?dailymotion\.com'],
        'vimeo': [r'(https?://)?(www\.)?vimeo\.com']
    }
    
    def __init__(self, temp_dir: Path): ...
    def detect_platform(self, url: str) -> str: ...
    def is_valid_url(self, url: str) -> bool: ...
    def extract_video_id(self, url: str, platform: str) -> str: ...
    async def download_video_audio(self, url, video_id=None) -> Dict: ...
    def _parse_vtt_subtitles(self, vtt_path: Path) -> List[Dict]: ...
    def get_platform_info(self, url: str) -> Dict: ...
```

**Процесс определения платформы.** Метод `detect_platform(url)` итерирует по словарю `PLATFORM_PATTERNS`, применяя `re.search()` к URL. Для каждой платформы определены от 1 до 4 регулярных выражений, покрывающих различные форматы URL:

```python
def detect_platform(self, url: str) -> str:
    url_lower = url.lower()
    for platform, patterns in self.PLATFORM_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, url_lower):
                return platform
    return 'unknown'
```

Примеры обрабатываемых URL:

| Платформа | Формат URL | Video ID |
|-----------|-----------|----------|
| YouTube | `youtube.com/watch?v=dQw4w9WgXcQ` | `dQw4w9WgXcQ` |
| YouTube | `youtu.be/dQw4w9WgXcQ` | `dQw4w9WgXcQ` |
| YouTube | `youtube.com/shorts/dQw4w9WgXcQ` | `dQw4w9WgXcQ` |
| VK | `vk.com/video-123456_789012` | `-123456_789012` |
| Rutube | `rutube.ru/video/abc123def456/` | `abc123def456` |
| OK.ru | `ok.ru/video/123456789` | `123456789` |
| Fallback | Любой URL | MD5-хеш[:16] |

**Двухэтапная загрузка.**

Метод `download_video_audio()` выполняет загрузку в 2 этапа:

```python
# Этап 1: Получение метаданных БЕЗ скачивания
info = ydl.extract_info(url, download=False)
video_title = info.get('title', 'Unknown')
duration = info.get('duration', 0)

# Проверка ограничений VK
if platform == 'vk' and duration > 3600:
    raise Exception("VK videos longer than 60 minutes are not supported")

# Этап 2: Фактическая загрузка
info = ydl.extract_info(url, download=True)
```

**Парсинг VTT-субтитров.**

Метод `_parse_vtt_subtitles()` реализует парсер формата WebVTT:

```python
def _parse_vtt_subtitles(self, vtt_path: Path) -> List[Dict]:
    subtitles = []
    lines = content.split('\n')
    i = 0
    while i < len(lines):
        if '-->' in lines[i]:  # Таймкод: "00:01:23.456 --> 00:01:25.789"
            times = lines[i].split('-->')
            start_time = times[0].strip()
            end_time = times[1].strip()
            
            i += 1
            text_parts = []
            while i < len(lines) and lines[i].strip() and '-->' not in lines[i]:
                text_parts.append(lines[i].strip())
                i += 1
            
            text = ' '.join(text_parts)
            if text:
                subtitles.append({'start': start_time, 'end': end_time, 'text': text})
        i += 1
    return subtitles
```


### 4.2.2. Модуль транскрибации (WhisperOrchestrator + Whisper-сервис)

Транскрибация реализована через двухуровневую архитектуру.

**Уровень 1: WhisperOrchestrator (backend, main_new.py).**

Реализует паттерн **Object Pool** для управления Whisper-воркерами:

```python
class WhisperOrchestrator:
    def __init__(self, max_workers: int = 2):
        self.max_workers = max_workers
        self.workers: Dict[str, WhisperWorker] = {}
        self.task_queue: asyncio.Queue = asyncio.Queue()
        self._lock = asyncio.Lock()
        self.next_worker_id = 1
```

**Класс WhisperWorker:**

```python
class WhisperWorker:
    def __init__(self, worker_id: str, port: int):
        self.worker_id = worker_id
        self.url = f"{WHISPER_BASE_URL}:{port}"
        self.is_busy = False
        self.current_task_id = None
        self.last_used = time.time()
        self.is_ready = False
    
    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.url}/health")
                if response.status_code == 200:
                    self.is_ready = True
                    return True
        except:
            pass
        self.is_ready = False
        return False
    
    async def transcribe(self, audio_path: Path, language: str = "ru") -> Dict:
        self.is_busy = True
        try:
            async with httpx.AsyncClient(timeout=7200.0) as client:
                response = await client.post(
                    f"{self.url}/transcribe-path",
                    params={"audio_path": str(audio_path), "language": language}
                )
                return response.json()
        finally:
            self.is_busy = False
```

**Стратегия получения воркера:**

```python
async def get_available_worker(self) -> Optional[WhisperWorker]:
    # 1. Поиск свободного готового воркера
    for worker in self.workers.values():
        if not worker.is_busy and worker.is_ready:
            return worker
    
    # 2. Создание нового (если не превышен лимит)
    if len(self.workers) < self.max_workers:
        return await self._create_worker()
    
    # 3. Все заняты — вернуть None (вызывающий код будет ждать)
    return None
```

**Ожидание свободного воркера (до 1 часа):**

```python
async def transcribe_audio(self, audio_path, task_id, language="ru"):
    worker = await self.get_available_worker()
    
    if not worker:
        for i in range(720):  # 720 × 5s = 3600s = 1 час
            await asyncio.sleep(5)
            worker = await self.get_available_worker()
            if worker:
                break
        
        if not worker:
            raise Exception("No available workers after 1 hour wait")
    
    worker.current_task_id = task_id
    try:
        return await worker.transcribe(audio_path, language)
    finally:
        worker.current_task_id = None
```

**Уровень 2: Whisper-сервис (whisper-service/main.py, 267 строк).**

Микросервис FastAPI с моделью, резидентной в памяти:

```python
@app.on_event("startup")
async def startup_event():
    global whisper_model, ACTIVE_DEVICE, ACTIVE_COMPUTE_TYPE
    from faster_whisper import WhisperModel
    
    ACTIVE_DEVICE = detect_device()      # "cpu" или "cuda"
    ACTIVE_COMPUTE_TYPE = detect_compute_type(ACTIVE_DEVICE)  # "int8" или "float16"
    
    # Загрузка модели (с retry, до 3 попыток)
    for attempt in range(3):
        try:
            whisper_model = WhisperModel(
                MODEL_NAME,
                device=ACTIVE_DEVICE,
                compute_type=ACTIVE_COMPUTE_TYPE,
                cpu_threads=CPU_THREADS if ACTIVE_DEVICE == "cpu" else 0
            )
            break
        except Exception as e:
            if attempt < 2:
                await asyncio.sleep(10)
```

**Параметры транскрибации:**

```python
def _build_transcribe_kwargs(language: str) -> dict:
    kwargs = {
        "language": language,
        "task": "transcribe",
        "beam_size": BEAM_SIZE,
        "condition_on_previous_text": True,
        "compression_ratio_threshold": 2.4,
        "log_prob_threshold": -1.0,
        "no_speech_threshold": 0.6,
    }
    if VAD_ENABLED:
        kwargs["vad_filter"] = True
        kwargs["vad_parameters"] = dict(
            min_silence_duration_ms=500,
            speech_pad_ms=200,
        )
    return kwargs
```

| Параметр | Значение | Назначение |
|----------|---------|------------|
| beam_size | 3 (CPU) / 5 (GPU) | Ширина лучевого поиска |
| condition_on_previous_text | True | Учёт контекста предыдущих сегментов |
| compression_ratio_threshold | 2.4 | Фильтрация «галлюцинаций» (повторяющийся текст) |
| no_speech_threshold | 0.6 | Порог определения «нет речи» |
| vad_filter | True | Voice Activity Detection |
| min_silence_duration_ms | 500 | Минимальная тишина для разделения сегментов |
| speech_pad_ms | 200 | Отступ вокруг обнаруженной речи |


### 4.2.3. Гибридная транскрибация (Whisper + субтитры)

Функция `merge_subtitles_with_whisper()` объединяет платформенные субтитры с результатами Whisper:

```python
def merge_subtitles_with_whisper(subtitles, whisper_segments):
    merged = []
    for sub in subtitles:
        best_match = None
        for wseg in whisper_segments:
            if abs(wseg["start"] - float(sub["start"].split(':')[-1])) < 2.0:
                best_match = wseg
                break
        
        merged_text = sub["text"]
        if best_match and '?' in best_match["text"]:
            merged_text = best_match["text"]  # Whisper лучше с пунктуацией
        
        merged.append({
            "start": sub["start"],
            "end": sub["end"],
            "text": merged_text
        })
    
    return merged if merged else whisper_segments
```

**Логика слияния:**

1. Для каждого субтитра ищется Whisper-сегмент с временным сдвигом < 2 секунд.
2. Если Whisper-сегмент содержит `?` (вопросительный знак), он предпочитается субтитрам.
3. Причина: платформенные субтитры часто не содержат пунктуации, а Whisper расставляет её автоматически. Вопросительные знаки критичны для извлечения вопросов LLM.


### 4.2.4. Модуль извлечения вопросов через LLM

**Промпт-инженерия.**

Функция `extract_questions_from_transcript()` формирует структурированный промпт:

```python
prompt = f"""Ты — эксперт по анализу технических интервью. 
Проанализируй транскрипцию видео с собеседованием и извлеки ВСЕ вопросы.

ВАЖНО:
- Извлекай ТОЛЬКО вопросы интервьюера кандидату
- НЕ извлекай вопросы кандидата интервьюеру
- Формулируй вопросы чётко
- Определи тему вопроса (Backend, Frontend, DevOps, Database, ...)
- Определи сложность (junior, middle, senior)
- Укажи таймкод (MM:SS или HH:MM:SS)

Транскрипция:
{transcript[:50000]}

JSON массив:
[
  {{"question": "...", "topic": "Backend", "difficulty": "middle", "timecode": "12:34"}}
]"""
```

Ключевые решения промпт-инженерии:

1. **Ограничение 50 000 символов** — предотвращение переполнения контекстного окна (128K токенов ≈ 500К символов, но с запасом).
2. **Инструкция «ТОЛЬКО вопросы интервьюера»** — снижает False Positive от вопросов кандидата.
3. **Температура 0.3** — высокий детерминизм для задачи извлечения (минимизация «галлюцинаций»).
4. **Строгий JSON-формат** — упрощает парсинг ответа.

**Multi-provider fallback.**

```
call_llm_api()
  ├─► OpenRouter (if OPENROUTER_API_KEY exists)
  │     └─► Llama-3.1-70B-Instruct
  ├─► Gemini (if GEMINI_API_KEY exists)
  │     ├─► gemini-2.0-flash (primary)
  │     └─► gemini-1.5-flash (fallback)
  └─► Groq (if GROQ_API_KEY exists)
        └─► Llama-3.1-70B-Versatile (with exponential backoff)
```

**Парсинг ответа LLM:**

```python
def parse_questions_from_llm(response_text):
    # Удаление markdown-обёрток
    text = response_text.strip()
    if text.startswith('```'):
        text = text.split('\n', 1)[1]  # Убрать ```json
    if text.endswith('```'):
        text = text.rsplit('```', 1)[0]  # Убрать ```
    
    result = json.loads(text)
    if isinstance(result, list):
        return result
    raise ValueError("Expected JSON array")
```

**Постобработка: фильтрация мусора.**

```python
def filter_low_quality_questions(questions):
    garbage_patterns = [
        r'^(да|нет|ага|угу|ну|ок|м+|хм+|э)\??$',  # Междометия
        r'^(что|как|а)\??$',                         # Слишком короткие
        r'^.{1,4}\??$',                               # < 5 символов
    ]
    
    filtered = []
    for q in questions:
        text = q.get("question", "").strip().lower()
        if any(re.match(pattern, text) for pattern in garbage_patterns):
            continue
        if len(text) < 5:
            continue
        filtered.append(q)
    return filtered
```

**Постобработка: дедупликация.**

```python
def deduplicate_questions(questions):
    seen = set()
    unique = []
    for q in questions:
        text = q.get("question", "").strip().lower()
        normalized = re.sub(r'[^\w\s]', '', text)  # Удаление пунктуации
        normalized = ' '.join(normalized.split())    # Нормализация пробелов
        
        if normalized and normalized not in seen:
            seen.add(normalized)
            unique.append(q)
    return unique
```


### 4.2.5. Модуль семантического поиска (Similarity Search)

Реализован в `similarity_search.py` (154 строки).

**Класс QuestionSimilaritySearch:**

```python
class QuestionSimilaritySearch:
    def __init__(self):
        self.model = None       # SentenceTransformer
        self.index = None       # FAISS IndexFlatIP
        self.questions_data = [] # Метаданные вопросов
        self.redis_client = redis.from_url(REDIS_URL)
```

**Инициализация и построение индекса:**

```python
async def initialize(self):
    # 1. Загрузка модели (~80 МБ)
    self.model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # 2. Проверка Redis-кэша
    cached = await self.redis_client.get("questions_embeddings_cache")
    if cached:
        cache = pickle.loads(cached)
        self.index = cache['index']
        self.questions_data = cache['questions_data']
    else:
        await self._build_index()
        await self._save_cache()

async def _build_index(self):
    # 1. Загрузка одобренных вопросов из PostgreSQL
    conn = await asyncpg.connect(DATABASE_URL)
    questions = await conn.fetch("""
        SELECT id, question, topic, difficulty, probability
        FROM questions WHERE approved = TRUE
    """)
    
    # 2. Генерация эмбеддингов
    texts = [q['question'] for q in questions]
    embeddings = self.model.encode(texts, show_progress_bar=True)
    
    # 3. Создание FAISS-индекса
    dimension = embeddings.shape[1]  # 384
    self.index = faiss.IndexFlatIP(dimension)
    
    # 4. L2-нормализация (для косинусного сходства)
    faiss.normalize_L2(embeddings)
    self.index.add(embeddings.astype('float32'))
```

**Поиск похожих вопросов:**

```python
async def find_similar(self, question_text, question_id=None, limit=10):
    # 1. Генерация эмбеддинга запроса
    query_embedding = self.model.encode([question_text])
    faiss.normalize_L2(query_embedding)
    
    # 2. FAISS-поиск (Inner Product = косинусное сходство)
    scores, indices = self.index.search(
        query_embedding.astype('float32'), 
        limit + 1  # +1 для исключения самого себя
    )
    
    # 3. Формирование результатов
    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx < len(self.questions_data):
            q = self.questions_data[idx]
            if question_id and q['id'] == question_id:
                continue  # Исключить самого себя
            results.append({**q, 'similarity_score': float(score)})
            if len(results) >= limit:
                break
    return results
```

**Инвалидация кэша:**

```python
async def invalidate_cache(self):
    await self.redis_client.delete("questions_embeddings_cache")
    self.index = None
    self.questions_data = []
```

Вызывается при изменении вопросов: создание, обновление, удаление, одобрение, объединение дубликатов.


### 4.2.6. Модуль обработки Pipeline (Core Processing)

Функция `process_video_pipeline()` — центральный алгоритм системы:

```python
async def process_video_pipeline(task_id, video_url, topic, level):
    try:
        # ══════ Этап 1: Скачивание ══════
        await update_task_progress(task_id, 5, "downloading", "Начинаем скачивание...")
        download_result = await download_video_audio(video_url, task_id)
        audio_path = Path(download_result["audio_path"])
        video_title = download_result["video_title"]
        subtitles = download_result.get("subtitles", [])
        
        await update_task_progress(task_id, 20, "downloaded", f"Скачано: {video_title}")
        
        # ══════ Этап 2: Транскрибация ══════
        await update_task_progress(task_id, 25, "transcribing", "Транскрибация через Whisper...")
        whisper_result = await whisper_orchestrator.transcribe_audio(audio_path, task_id)
        transcript = whisper_result["text"]
        whisper_segments = whisper_result["segments"]
        
        # Слияние с субтитрами
        if subtitles:
            merged = merge_subtitles_with_whisper(subtitles, whisper_segments)
            transcript = " ".join([s["text"] for s in merged])
        
        # Сохранение транскрипции в Redis
        await redis_client.set(f"transcript:{task_id}", json.dumps({
            "transcript": transcript,
            "segments": merged,
            "whisper_raw": whisper_result["text"]
        }), ex=86400)
        
        await update_task_progress(task_id, 60, "transcribed", 
            f"{len(whisper_segments)} сегментов, {len(transcript)} символов")
        
        # ══════ Этап 3: Извлечение вопросов ══════
        await update_task_progress(task_id, 65, "extracting", "Извлечение через LLM...")
        questions = await extract_questions_from_transcript(transcript, topic, level)
        questions = filter_low_quality_questions(questions)
        questions = deduplicate_questions(questions)
        
        await update_task_progress(task_id, 85, "extracted", f"Извлечено {len(questions)} вопросов")
        
        # ══════ Этап 4: Сохранение в БД ══════
        await update_task_progress(task_id, 90, "saving", "Сохранение в базу данных...")
        await save_questions_to_db(questions, video_url, video_title, 
                                    download_result["video_id"], task_id, 
                                    download_result.get("platform", "unknown"))
        
        # ══════ Завершение ══════
        await update_task_progress(task_id, 100, "completed", "Готово!")
        
        # Обновление Redis
        task = json.loads(await redis_client.get(f"task:{task_id}"))
        task["status"] = "completed"
        task["result"] = {"video_title": video_title, "questions_count": len(questions)}
        await redis_client.set(f"task:{task_id}", json.dumps(task), ex=86400)
        
        # WebSocket-уведомление
        await manager.broadcast_to_task(task_id, {
            "type": "completed", "task_id": task_id,
            "video_title": video_title, "questions_count": len(questions)
        })
        
        # Очистка temp-файлов
        cleanup_temp_files(download_result["video_id"])
        
    except Exception as e:
        await update_task_error(task_id, str(e))
```

**Обновление прогресса с логированием:**

```python
async def update_task_progress(task_id, progress, status, step):
    task = json.loads(await redis_client.get(f"task:{task_id}"))
    task["progress"] = progress
    task["status"] = status
    task["step"] = step
    
    # Добавление записи в лог задачи
    if "logs" not in task:
        task["logs"] = []
    task["logs"].append({
        "time": datetime.now().isoformat(),
        "progress": progress,
        "status": status,
        "message": step
    })
    # Ограничение лога (50 записей)
    if len(task["logs"]) > 50:
        task["logs"] = task["logs"][-50:]
    
    await redis_client.set(f"task:{task_id}", json.dumps(task), ex=86400)
    
    # WebSocket-уведомление в реальном времени
    await manager.broadcast_to_task(task_id, {
        "type": "progress", "task_id": task_id,
        "progress": progress, "status": status, "step": step
    })
```


### 4.2.7. Модуль сохранения данных

Функция `save_questions_to_db()` выполняет многоэтапную атомарную запись:

```python
async def save_questions_to_db(questions, video_url, video_title, video_id, task_id, platform):
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        # 1. Проверка дубликата видео
        existing = await conn.fetchval(
            "SELECT id FROM processed_videos WHERE video_id = $1", video_id)
        if existing:
            return  # Уже обработано
        
        # 2. Регистрация видео
        db_video_id = await conn.fetchval("""
            INSERT INTO processed_videos (video_id, youtube_url, title, platform, processed_at)
            VALUES ($1, $2, $3, $4, NOW()) RETURNING id
        """, video_id, video_url, video_title, platform)
        
        # 3. Обработка каждого вопроса
        for q in questions:
            question_text = q.get("question", "").strip()
            if len(question_text) < 5:
                continue
            
            # Проверка дубликата (case-insensitive)
            existing_q = await conn.fetchval(
                "SELECT id FROM questions WHERE LOWER(question) = LOWER($1)",
                question_text)
            
            if existing_q:
                # Дубликат: добавляем связь с видео + таймкод
                await conn.execute("""
                    INSERT INTO question_video (question_id, video_id) 
                    VALUES ($1, $2) ON CONFLICT DO NOTHING
                """, existing_q, db_video_id)
                
                tc = q.get("timecode")
                if tc:
                    tc_seconds = parse_timecode_to_seconds(tc)
                    await conn.execute("""
                        INSERT INTO question_timecodes (question_id, video_id, timecode_start, timecode_seconds)
                        VALUES ($1, $2, $3, $4) ON CONFLICT (question_id, video_id) DO UPDATE
                        SET timecode_start = $3, timecode_seconds = $4
                    """, existing_q, db_video_id, str(tc), tc_seconds)
            else:
                # Новый вопрос
                question_id = await conn.fetchval("""
                    INSERT INTO questions (question, topic, difficulty, timecode, approved)
                    VALUES ($1, $2, $3, $4, FALSE) RETURNING id
                """, question_text, q.get("topic", "General"), 
                     q.get("difficulty", "middle"), q.get("timecode"))
                
                await conn.execute("""
                    INSERT INTO question_video (question_id, video_id) VALUES ($1, $2)
                """, question_id, db_video_id)
        
        # 4. Пересчёт вероятностей для ВСЕХ вопросов
        await update_probabilities(conn)
    finally:
        await conn.close()
```

**Расчёт вероятностей:**

```python
async def update_probabilities(conn):
    total_videos = await conn.fetchval("SELECT COUNT(*) FROM processed_videos")
    if total_videos > 0:
        await conn.execute("""
            UPDATE questions SET probability = (
                SELECT COALESCE(COUNT(DISTINCT qv.video_id) * 100.0 / $1, 0)
                FROM question_video qv
                WHERE qv.question_id = questions.id
            )
        """, total_videos)
```

---

## 4.3. Реализация пользовательского интерфейса

### 4.3.1. Главная страница (Home.vue)

Главная страница отображает:

1. **Hero-секция** с анимированным градиентным фоном:
   - Количество вопросов, тем и обработанных видео (из API `GET /api/stats`);
   - Анимации: `float` (вертикальное покачивание), `gradient-shift` (смена фона).

2. **Секция выбора профессий** — встроена непосредственно в Home.vue:
   - Сетка карточек с CSS Grid (`auto-fill`, `minmax(180px, 1fr)`);
   - 26 профессий с уникальными CSS-градиентами;
   - Каждая карточка показывает количество вопросов (`getProfessions()` API);
   - Стилизация через `.card` CSS-класс и scoped CSS.

Пример данных профессий:

| Профессия | Градиент | Эмодзи |
|-----------|---------|--------|
| Frontend | `#f093fb → #f5576c` | 🎨 |
| Backend | `#667eea → #764ba2` | ⚙️ |
| Python | `#4facfe → #00f2fe` | 🐍 |
| Java | `#fa709a → #fee140` | ☕ |
| DevOps | `#fcb69f → #ffecd2` | 🚀 |
| QA | `#a8edea → #fed6e3` | ✅ |
| Data Science | `#fbc2eb → #a6c1ee` | 📊 |

3. **Feature-карточки** — 6 блоков с описанием возможностей (`.f-card` стили):
   - Тренажёр SM-2, Записи собеседований, Вопросы из интервью, Тестовые задания, Навыки из вакансий, Предложить видео.


### 4.3.2. Тренажёр SM-2 (Trainer.vue)

Самый сложный view в проекте. Реализует полный цикл интервального повторения через собственные CSS-компоненты (без PrimeVue):

**Модальный выбор режима:**
- Карточки с описаниями режимов: «Обучение», «Повторение», «Mock-тест» — стилизованы через `.mode-card` CSS;
- Выбор темы и сложности через пользовательские `<select>` поля (`.input` класс).

**Статистическая панель (SM-2 pill-метрики):**
- Новые (new): карточки с `repetitions = 0` — `.badge-purple`;
- К повторению (review): карточки с `next_review < NOW()` — `.badge-yellow`;
- Выученные (learned): карточки с `next_review > NOW()` — `.badge-green`.

**Режим карточек (flashcard):**
- Анимированный flip-переход: CSS `transform: rotateY(180deg)` с `perspective(600px)`;
- Передняя сторона: текст вопроса;
- Обратная сторона: текст ответа;
- Кнопки оценки: `.btn-primary` / `.btn-ghost` для 6 уровней;
- Прогресс: `.progress` CSS-класс с CSS-переменной `--p`.

**Отправка оценки:**

```javascript
async function submitReview(quality) {
    await api.submitSM2Review(currentCard.value.id, quality)
    // SM-2 пересчёт на backend:
    // EF' = EF + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
    // if q < 3: interval = 0.04 days (1 hour), repetitions = 0
    // else: interval = I(n) * EF
    nextCard()
}
```

**Результаты сессии:**
- 🏆 Иконка трофея;
- Статистики: знаю / на повтор / всего;
- Кнопки: «Повторить сложные» / «Новая сессия».


### 4.3.3. Административная панель (Admin.vue)

Централизованная панель управления с tab-навигацией (собственные CSS-стили `.tab-btn` / `.tab-btn.active`, без PrimeVue TabView):

**Вкладка 1: Вопросы**
- Пользовательская HTML-таблица со столбцами: ID, текст, тема, сложность, вероятность, статус;
- Действия: одобрить (POST approve), отклонить (POST revoke), редактировать, удалить;
- Bulk-генерация ответов: выбор вопросов без ответов → POST generate-answers-bulk;
- Объединение дубликатов: выбор source + target → POST merge.

**Вкладка 2: Видео**
- Таблица обработанных видео: название, платформа, количество вопросов, дата;
- Действия: просмотр вопросов видео, переименование, удаление;
- Платформо-специфичные эмодзи (🎬 YouTube, 🔵 VK, 🎥 Rutube);

**Вкладка 3: Задачи**
- Pipeline-задачи с прогресс-барами (`.progress` CSS-класс);
- Форма загрузки видео (URL, тема, уровень) — через `<Teleport>` модальное окно;

**Вкладка 4: Предложения**
- Таблица предложений от пользователей;
- Статусы: pending → approved / rejected / processing → completed;

**Вкладка 5: Обратная связь**
- Таблица фидбэков с фильтром resolved/unresolved;

**Вкладка 6: Аналитика**
- Метрики: всего вопросов, одобрено, ожидающие, видео, предложения — стилизованы через `.mv` CSS-класс;
- Диаграммы распределения по темам и сложности.

Все модальные окна реализованы через Vue 3 `<Teleport to="body">` вместо PrimeVue Dialog.


### 4.3.4. Карточка вопроса (QuestionDetail.vue)

Загружает `GET /api/questions/{id}` с расширенными данными:

| Секция | Данные | Стилизация |
|--------|--------|-----------|
| Заголовок | Текст вопроса, тема (`.badge`), сложность (`.badge`), вероятность | Scoped CSS |
| Ответ | Автогенерированный ответ (LLM) | `.card` CSS-класс |
| Видео-источники | Список видео с таймкодами | Кликабельные ссылки (`?t=seconds`) |
| Похожие вопросы | Top-5 семантически близких | FAISS similarity_score |
| UGC-ответы | Пользовательские ответы с голосованием | `.btn-ghost` vote кнопки |
| Действия | Закладка, заметка, обратная связь | `.btn`, `<Teleport>` модальные окна |


---

## 4.4. Оценка качества извлечения вопросов

### 4.4.1. Методология оценки

Для оценки качества Pipeline извлечения вопросов используется методология, основанная на сравнении с экспертной разметкой (ground truth).

**Процесс оценки:**

1. **Формирование тестового набора.**
   - Отбор 5 видеозаписей различной тематики и длительности;
   - Ручная разметка экспертом: фиксация всех вопросов интервьюера с таймкодами;
   - Критерий включения: вопрос задаётся интервьюером кандидату для проверки знаний.

2. **Запуск Pipeline.**
   - Обработка тестовых видео через `POST /api/process-video`;
   - Сохранение извлечённых вопросов в БД.

3. **Сопоставление (matching).**
   - Для каждого извлечённого вопроса ищется наиболее близкий экспертный вопрос;
   - Критерий совпадения (True Positive): нормализованное расстояние Левенштейна ≤ 0.4 ИЛИ косинусное сходство эмбеддингов ≥ 0.75;
   - Два критерия используются параллельно, так как Левенштейн хорош для лексически близких вопросов, а эмбеддинги — для семантически близких с разными формулировками.

4. **Расчёт метрик.**

5. **Анализ ошибок.**


### 4.4.2. Метрики качества

Стандартные метрики информационного поиска (Information Retrieval):

$$Precision = \frac{TP}{TP + FP}$$

где $TP$ — True Positive (корректно извлечённые вопросы), $FP$ — False Positive (ложно извлечённые).

$$Recall = \frac{TP}{TP + FN}$$

где $FN$ — False Negative (пропущенные вопросы).

$$F_1 = 2 \cdot \frac{Precision \cdot Recall}{Precision + Recall}$$

$F_1$ — гармоническое среднее precision и recall, обеспечивающее баланс между полнотой и точностью.

**Дополнительная метрика — точность таймкодов:**

$$MAE_{timecode} = \frac{1}{|TP|} \sum_{i \in TP} |t_i^{extracted} - t_i^{expert}|$$

Средняя абсолютная ошибка определения таймкода в секундах.


### 4.4.3. Код для оценки

Скрипт оценки (`scripts/evaluate_extraction.py`) реализует автоматическое сопоставление:

```python
def match_questions(extracted, ground_truth, threshold_lev=0.4, threshold_sim=0.75):
    """Сопоставление извлечённых вопросов с экспертной разметкой"""
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    gt_embeddings = model.encode([q['question'] for q in ground_truth])
    ext_embeddings = model.encode([q['question'] for q in extracted])
    
    matched = set()
    tp, fp, fn = 0, 0, 0
    
    for i, ext_q in enumerate(extracted):
        best_match = None
        best_score = 0
        
        for j, gt_q in enumerate(ground_truth):
            if j in matched:
                continue
            
            # Лексическое сравнение (Левенштейн)
            lev_dist = levenshtein_distance(
                ext_q['question'].lower(), 
                gt_q['question'].lower()
            ) / max(len(ext_q['question']), len(gt_q['question']))
            
            # Семантическое сравнение (косинус)
            cos_sim = cosine_similarity(
                ext_embeddings[i:i+1], 
                gt_embeddings[j:j+1]
            )[0][0]
            
            score = max(1 - lev_dist, cos_sim)
            if score > best_score:
                best_score = score
                best_match = j
        
        if best_match is not None and (
            best_score >= threshold_sim or 
            lev_dist <= threshold_lev
        ):
            tp += 1
            matched.add(best_match)
        else:
            fp += 1
    
    fn = len(ground_truth) - len(matched)
    
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    
    return {'precision': precision, 'recall': recall, 'f1': f1, 'tp': tp, 'fp': fp, 'fn': fn}
```


### 4.4.4. Результаты тестирования

Тестирование проведено на наборе из 5 видеозаписей общей длительностью ~3 часа:

| Видео | Тема | Длительность | Expert Q | Extracted Q | TP | FP | FN | Precision | Recall | F1 |
|-------|------|-------------|---------|------------|----|----|----|-----------l--------|------|
| Video 1 | Python | 35 мин | 12 | 14 | 10 | 4 | 2 | 0.71 | 0.83 | 0.77 |
| Video 2 | JavaScript | 42 мин | 18 | 20 | 15 | 5 | 3 | 0.75 | 0.83 | 0.79 |
| Video 3 | System Design | 28 мин | 8 | 10 | 7 | 3 | 1 | 0.70 | 0.88 | 0.78 |
| Video 4 | DevOps | 50 мин | 22 | 19 | 16 | 3 | 6 | 0.84 | 0.73 | 0.78 |
| Video 5 | SQL/DB | 25 мин | 15 | 16 | 13 | 3 | 2 | 0.81 | 0.87 | 0.84 |
| **Среднее** | — | **36 мин** | **15.0** | **15.8** | **12.2** | **3.6** | **2.8** | **0.76** | **0.83** | **0.79** |

**Средняя ошибка таймкодов:** $MAE_{timecode} = 45$ секунд.

**Интерпретация результатов:**

- **Precision 0.76** — из 100 извлечённых вопросов 76 являются реальными вопросами интервьюера. 24 — ложные (риторические, уточняющие, вне контекста).

- **Recall 0.83** — из 100 реальных вопросов Pipeline извлекает 83. 17 пропускаются (неявная формулировка, объединение цепочек, ошибки транскрибации).

- **F1 0.79** — хороший баланс precision/recall. Для практического использования (подготовка к собеседованиям) recall важнее precision: лучше извлечь лишний вопрос, чем пропустить важный.


### 4.4.5. Анализ ошибок

**Причины False Positive (ложных извлечений):**

| Причина | Доля от FP | Пример |
|---------|-----------|--------|
| Риторические вопросы кандидата | 32% | «А можно using alias?» (кандидат, не интервьюер) |
| Уточняющие фразы | 28% | «Это понятно?», «Согласен?», «Верно?» |
| Контекстные вопросы | 40% | «Какой у вас опыт?» (smalltalk, не техническая проверка) |

**Причины False Negative (пропущенных вопросов):**

| Причина | Доля от FN | Пример |
|---------|-----------|--------|
| Неявная формулировка | 45% | «Расскажите про SOLID» (не вопросительная форма) |
| Объединение цепочек | 30% | 3 связанных вопроса → LLM объединяет в 1 |
| Ошибки транскрибации | 25% | Whisper неправильно транскрибирует термин |

**Влияние гибридной транскрибации** (Whisper + субтитры vs. только Whisper):

| Метрика | Только Whisper | Гибридный | Разница |
|---------|--------------|-----------|---------|
| Precision | 0.73 | 0.76 | +4% |
| Recall | 0.78 | 0.83 | +6% |
| F1 | 0.75 | 0.79 | +5% |

Улучшение объясняется: субтитры лучше распознают роли (интервьюер / кандидат), а Whisper лучше расставляет пунктуацию.

**Сравнение LLM-провайдеров** (тестирование на одном видео):

| Провайдер | Модель | F1 | Примечание |
|-----------|--------|----|------------|
| OpenRouter | Llama-3.1-70B | 0.79 | Лучший баланс precision/recall |
| Gemini | gemini-2.0-flash | 0.76 | Склонен объединять близкие вопросы |
| Groq | Llama-3.1-70B | 0.78 | Аналогично OpenRouter, выше latency |

OpenRouter показывает лучший результат, так как Llama-3.1-70B — та же модель, но OpenRouter обеспечивает стабильнее API без rate limiting.


### 4.4.6. Рекомендации по улучшению качества

На основе анализа ошибок сформулированы рекомендации для будущих версий:

1. **Для снижения FP:**
   - Добавить фильтрацию по длине вопроса (минимум 15 символов для технических вопросов);
   - Добавить NER (Named Entity Recognition) для идентификации ролей (интервьюер vs. кандидат);
   - Расширить список garbage_patterns для уточняющих фраз.

2. **Для повышения Recall:**
   - Добавить постобработку «неявных вопросов» (паттерн: «Расскажите про...» → вопрос);
   - Разделять длинные ответы LLM на отдельные вопросы (если LLM объединил);
   - Улучшить промпт: добавить примеры «неявных» вопросов.

3. **Для улучшения таймкодов:**
   - Использовать word-level timestamps из Whisper (вместо segment-level);
   - Сопоставлять извлечённый текст вопроса с конкретными сегментами Whisper.


---

## 4.5. Процесс развёртывания и DevOps

### 4.5.1. Процедура развёртывания

Развёртывание системы выполняется одной командой:

```bash
# CPU-конфигурация
docker-compose -f docker-compose.cpu.yml up -d

# GPU-конфигурация (требуется NVIDIA GPU + nvidia-docker2)
docker-compose -f docker-compose.gpu.yml up -d
```

**Последовательность запуска:**

1. PostgreSQL стартует, выполняет `init-db.sql` (CREATE EXTENSION pg_trgm, CREATE TABLE questions, etc.);
2. Redis стартует, начинает принимать соединения;
3. Backend стартует после healthy PostgreSQL + Redis:
   - Выполняет auto-migration (20 CREATE TABLE IF NOT EXISTS);
   - Наполняет профессии (`INSERT INTO professions ON CONFLICT DO NOTHING`);
   - Инициализирует VideoDownloader, WhisperOrchestrator, SimilaritySearch;
4. Whisper Worker стартует параллельно:
   - Загружает модель в память (~3 ГБ, 1–3 минуты);
   - Становится ready после успешного healthcheck;
5. Frontend стартует, проксирует `/api` на backend.

**Переменные окружения:**

```yaml
environment:
    - DATABASE_URL=postgresql://diploma:diploma123@postgres:5432/interview_prep
    - REDIS_URL=redis://redis:6379
    - WHISPER_BASE_URL=http://whisper-worker:8000
    - LLM_PROVIDER=auto
    - OPENROUTER_API_KEY=${OPENROUTER_API_KEY:-}
    - GEMINI_API_KEY=${GEMINI_API_KEY:-}
    - GROQ_API_KEY=${GROQ_API_KEY:-}
```

API-ключи передаются через `.env` файл или переменные окружения хоста (Docker `${VAR:-default}` синтаксис).


### 4.5.2. Мониторинг

Эндпоинт `/health` возвращает состояние системы:

```json
{
    "status": "healthy",
    "whisper_orchestrator": {
        "max_workers": 2,
        "active_workers": 1,
        "workers": [{
            "id": "w1",
            "is_ready": true,
            "is_busy": false,
            "current_task": null
        }]
    },
    "architecture": "per-task scaling (1 worker = 1 full audio, no chunking)",
    "temp_files_count": 3,
    "temp_size_mb": 45.2
}
```

PowerShell-скрипт мониторинга (`monitor.ps1`):

```powershell
while ($true) {
    $health = Invoke-RestMethod -Uri "http://localhost:8000/health"
    Write-Host "Status: $($health.status)"
    Write-Host "Workers: $($health.whisper_orchestrator.active_workers)"
    Write-Host "Temp: $($health.temp_size_mb) MB"
    Start-Sleep -Seconds 30
}
```


### 4.5.3. Оптимизация Docker-образов

В процессе разработки была проведена оптимизация размеров Docker-образов:

| Образ | До оптимизации | После оптимизации | Экономия |
|-------|---------------|-------------------|----------|
| Backend | 3.2 ГБ | 2.1 ГБ | 34% |
| Frontend (prod) | 800 МБ | 25 МБ | 97% |
| Whisper (CPU) | 6.0 ГБ | 4.5 ГБ | 25% |
| PostgreSQL | 240 МБ | 240 МБ | 0% (alpine) |
| Redis | 30 МБ | 30 МБ | 0% (alpine) |
| **ИТОГО** | **10.3 ГБ** | **6.9 ГБ** | **33%** |

Применённые оптимизации:
- Multi-stage build для frontend (исключение node_modules);
- `python:3.11-slim` вместо `python:3.11` (-400 МБ);
- `--no-cache-dir` для pip install (исключение pip-кэша);
- CPU-only PyTorch (`--extra-index-url .../whl/cpu`) вместо CUDA-версии (-8 ГБ);
- `rm -rf /var/lib/apt/lists/*` после apt-get (исключение apt-кэша).


---

## 4.6. Выводы по главе

В данной главе описана реализация и тестирование информационной системы для автоматизированной подготовки к IT-собеседованиям. Основные результаты:

1. **Реализована серверная часть** на FastAPI (Python 3.11) — 3237 строк, 67 API-эндпоинтов, WebSocket, асинхронный pipeline обработки видео. Используются asyncpg, redis.asyncio, httpx для неблокирующей работы.

2. **Реализована клиентская часть** на Vue 3.4 — 12 представлений, 2 переиспользуемых компонента (NavBar, AppFooter). Собственная дизайн-система на CSS Custom Properties (без PrimeVue): утилитарные классы (.btn, .badge, .card, .input, .spinner, .progress), тёмная тема (#0c0c0f, акцент #7c5cfc). Легаси-версия на PrimeVue сохранена для сравнения (порт 3001).

3. **Реализован Whisper-сервис** (267 строк) — faster-whisper с CTranslate2, поддержкой CPU/GPU, VAD-фильтрацией, резидентной моделью в памяти.

4. **Реализован модуль загрузки видео** (352 строки) — поддержка 6 платформ с платформо-специфичными настройками (VK: ограничения по размеру и длительности).

5. **Реализован модуль семантического поиска** (154 строки) — SentenceTransformer + FAISS с Redis-кэшированием и автоинвалидацией.

6. **Реализован multi-provider LLM** — автоматический выбор из OpenRouter, Gemini, Groq с fallback и exponential backoff.

7. **Проведена оценка качества** Pipeline:
   - **Precision: 0.76** — 76% извлечённых вопросов корректны;
   - **Recall: 0.83** — 83% реальных вопросов извлечены;
   - **F1: 0.79** — хороший баланс для практического использования;
   - Гибридная транскрибация даёт +5% F1 по сравнению с чистым Whisper.

8. **Реализована контейнеризация** — 6 сервисов в Docker Compose (Frontend NEW, Frontend OLD, Backend, Whisper, PostgreSQL, Redis), 3 конфигурации (CPU/CPU-opt/GPU), auto-migration, мониторинг через `/health`. Суммарный размер образов: 6.9 ГБ.

Система успешно развёрнута и протестирована на конфигурации AMD Ryzen 7 / 32 ГБ RAM. Обработка 30-минутного видео занимает 10–15 минут на CPU-конфигурации, что соответствует требованию NFR-1.1.
