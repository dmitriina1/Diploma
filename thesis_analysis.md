# Методы и технологии решения задачи: Анализ системы InterviewHub

## Глава 2. Архитектура и технологии системы

### 2.1. Общая архитектура системы

InterviewHub — это full-stack веб-приложение для подготовки к IT-собеседованиям с автоматизированной обработкой видеоконтента. Система использует AI для извлечения вопросов из видеозаписей собеседований, создавая структурированную базу знаний с семантическим поиском и статистикой.

**Основные компоненты системы:**

1. **Backend (FastAPI)** — основной сервер с REST API
2. **Frontend (Vue 3)** — современный веб-интерфейс
3. **Whisper Service** — микросервис транскрибации
4. **PostgreSQL** — основная база данных
5. **Redis** — кэш и задачи обработки
6. **FAISS** — семантический поиск
7. **yt-dlp** — скачивание видео с платформ

### 2.2. Методы обработки видео

#### 2.2.1. Скачивание видео и аудио

Система использует библиотеку **yt-dlp** для универсального скачивания видео с различных платформ:

- **YouTube** (youtube.com, youtu.be)
- **VK.video** (vk.com/video, vkvideo.ru)
- **Rutube** (rutube.ru)
- **OK.ru** (ok.ru/video)
- **Dailymotion**
- **Vimeo**

**Методы работы с yt-dlp:**
- Использует встроенные экстракторы для каждой платформы
- Поддерживает скачивание аудио в формате MP3
- Извлекает субтитры (VTT/SRT) при наличии
- Обходит стандартные ограничения платформ
- Работает с кэшированием для повторных запросов

```python
# Пример использования yt-dlp в системе
ydl_opts = {
    'format': 'bestaudio/best',
    'outtmpl': str(self.temp_dir / f'{video_id}.%(ext)s'),
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
    'writesubtitles': True,
    'writeautomaticsub': True,
    'subtitleslangs': ['ru'],
    'subtitlesformat': 'vtt',
    'quiet': False,
    'no_warnings': False,
    'ignoreerrors': False,
    'nocheckcertificate': True,
    'socket_timeout': 60,
    'retries': 10,
    'fragment_retries': 10,
    'skip_unavailable_fragments': True,
    'http_chunk_size': 10485760,
    'concurrent_fragment_downloads': 1,
    'noprogress': False,
}
```

#### 2.2.2. Сравнение и выбор технологии транскрипции

Система использует **faster-whisper** как основную технологию транскрипции. Рассмотрим альтернативные подходы:

**1. OpenAI Whisper:**
- Преимущества: высокое качество, хорошая точность
- Недостатки: медленная обработка, требует GPU, лицензионные ограничения
- Использование: не используется напрямую

**2. faster-whisper (основной выбор):**
- Преимущества: в 4-6 раз быстрее оригинального Whisper, поддержка CPU, эффективное использование памяти
- Недостатки: требует больше ресурсов для установки
- Использование: основной метод транскрипции

**3. SpeechRecognition (Python библиотека):**
- Преимущества: простота использования
- Недостатки: ограниченные возможности, зависимость от внешних API
- Использование: не используется

**4. AssemblyAI/Voicegain API:**
- Преимущества: облачные решения, минимальная настройка
- Недостатки: стоимость, зависимость от интернета
- Использование: не используется

#### 2.2.3. Архитектура whisper-service

Сервис транскрибации построен как отдельный микросервис:

**Конфигурация:**
- Модель: large-v3-turbo (оптимальное соотношение качества и скорости)
- Устройство: автоопределение (GPU при наличии, иначе CPU)
- Тип вычислений: float16 для GPU, int8 для CPU
- Потоки: 8 для CPU режима
- Beam size: 3 для баланса скорости и качества
- VAD (Voice Activity Detection): включен для фильтрации тишины

```python
# Пример конфигурации faster-whisper
model_kwargs = {
    "model_size_or_path": "large-v3-turbo",
    "device": "cuda" if gpu_available else "cpu",
    "compute_type": "float16" if gpu_available else "int8",
    "download_root": "/root/.cache/whisper",
}
if device == "cpu":
    model_kwargs["cpu_threads"] = 8
```

**Преимущества архитектуры:**
- Изолированная обработка аудио
- Масштабируемость (per-task модель)
- Поддержка различных форматов аудио
- Встроенный VAD фильтр

### 2.3. Извлечение вопросов и субтитров

#### 2.3.1. Извлечение субтитров

Система извлекает субтитры через yt-dlp в формате VTT и парсит их:

```python
def _parse_vtt_subtitles(self, vtt_path: Path) -> List[Dict[str, Any]]:
    """Парсинг VTT субтитров"""
    subtitles = []
    with open(vtt_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        # Ищем таймкод
        if '-->' in line:
            times = line.split('-->')
            start_time = times[0].strip()
            end_time = times[1].strip() if len(times) > 1 else start_time
            
            # Следующая строка - текст
            i += 1
            text_parts = []
            
            while i < len(lines) and lines[i].strip() and '-->' not in lines[i]:
                text_parts.append(lines[i].strip())
                i += 1
            
            text = ' '.join(text_parts)
            if text:
                subtitles.append({
                    'start': start_time,
                    'end': end_time,
                    'text': text
                })
        i += 1
    
    return subtitles
```

#### 2.3.2. Слияние Whisper и субтитров

Система объединяет результаты Whisper транскрипции и субтитров:

```python
def merge_subtitles_with_whisper(subtitles: List[Dict], whisper_segments: List[Dict]) -> List[Dict]:
    """Слияние YouTube субтитров с Whisper"""
    merged = []
    for sub in subtitles:
        # Ищем соответствующий сегмент Whisper
        best_match = None
        for wseg in whisper_segments:
            # Простое сопоставление по времени
            if abs(wseg.get("start", 0) - float(sub.get("start", "0").split(":")[-1])) < 2.0:
                best_match = wseg
                break
        
        merged_text = sub["text"]
        if best_match and "?" in best_match["text"]:
            # Whisper даёт пунктуацию
            merged_text = best_match["text"]
        
        merged.append({
            "start": sub.get("start"), 
            "end": sub.get("end"), 
            "text": merged_text
        })
    
    return merged if merged else whisper_segments
```

### 2.4. Извлечение вопросов через LLM

#### 2.4.1. Метод работы с LLM

Система использует большие языковые модели для извлечения вопросов из транскрипций:

**Поддерживаемые провайдеры:**
- OpenRouter (Llama-3.1-70b)
- Google Gemini (2.0-flash, 1.5-flash)
- Groq (Llama-3.1-70b-versatile)

**Промпт для извлечения вопросов:**
```
Ты — эксперт по анализу технических интервью. Проанализируй транскрипцию видео с собеседованием и извлеки ВСЕ вопросы, которые задаются кандидату.

ВАЖНО:
- Извлекай ТОЛЬКО вопросы, которые задаёт интервьюер кандидату
- НЕ извлекай вопросы, которые кандидат задаёт интервьюеру
- Формулируй вопросы чётко и понятно
- Определи тему вопроса (Backend, Frontend, DevOps, Database, Algorithms, System Design и т.д.)
- Определи сложность (junior, middle, senior)
- Если в транскрипции есть метки времени, укажи таймкод начала вопроса в формате MM:SS или HH:MM:SS

Верни JSON массив вопросов в формате:
[
  {
    "question": "Полный текст вопроса?",
    "topic": "Backend",
    "difficulty": "middle",
    "timecode": "12:34"
  }
]
```

**Алгоритм извлечения:**
1. Подготовка транскрипции (ограничение длины до 50000 символов)
2. Формирование промпта для LLM
3. Вызов LLM API (с fallback между провайдерами)
4. Парсинг JSON результата
5. Фильтрация низкокачественных вопросов
6. Удаление дубликатов

#### 2.4.2. Фильтрация и дедупликация

**Фильтрация мусорных вопросов:**
```python
def filter_low_quality_questions(questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Фильтрация мусорных вопросов"""
    if not questions:
        return []
    
    garbage_patterns = [
        r"^(да|нет|ага|угу|ну|ок|м+|хм+|э)\??$",
        r"^(что|как|а)\??$",
        r"^.{1,4}\??$",
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

**Удаление дубликатов:**
```python
def deduplicate_questions(questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Удаление дубликатов"""
    if not questions:
        return []
    
    seen = set()
    unique = []
    
    for q in questions:
        text = q.get("question", "").strip().lower()
        normalized = re.sub(r"[^\w\s]", "", text)
        normalized = " ".join(normalized.split())
        
        if normalized and normalized not in seen:
            seen.add(normalized)
            unique.append(q)
    
    return unique
```

## Глава 3. Реализация функций системы

### 3.1. Поиск вопросов по технологии/теме с фильтрацией

#### 3.1.1. Структура хранения данных

**Таблица questions:**
- id: уникальный идентификатор
- question: текст вопроса
- answer: текст ответа (AI-генерация или ручной)
- topic: тема/технология (Backend, Frontend, DevOps и т.д.)
- difficulty: сложность (junior, middle, senior)
- probability: вероятность встречи на собеседовании (%)
- approved: одобрен администратором
- timecode: время в видео для воспроизведения
- created_at: дата создания

**Пример фильтрации на бэкенде:**
```python
@app.get("/api/questions")
async def get_all_questions(topic: Optional[str] = None, level: Optional[str] = None):
    """Получение всех одобренных вопросов"""
    query = """
        SELECT id, question, answer, topic, difficulty, probability, timecode
        FROM questions
        WHERE approved = TRUE
    """
    params = []

    if topic:
        query += " AND topic = $1"
        params.append(topic)

    if level:
        idx = len(params) + 1
        query += f" AND difficulty = ${idx}"
        params.append(level)

    query += " ORDER BY probability DESC NULLS LAST, created_at DESC"
```

**Фильтрация на фронтенде:**
```javascript
const filteredQuestions = computed(() => {
  let r = questions.value.filter(q => {
    if (selectedTopic.value && q.topic !== selectedTopic.value) return false
    if (selectedDifficulty.value && q.difficulty !== selectedDifficulty.value) return false
    if (search.value && !q.question.toLowerCase().includes(search.value.toLowerCase())) return false
    return true
  })
  if (sortBy.value === 'probability') r.sort((a, b) => (b.probability||0) - (a.probability||0))
  else if (sortBy.value === 'date') r.sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
  else if (sortBy.value === 'alpha') r.sort((a, b) => a.question.localeCompare(b.question, 'ru'))
  return r
})
```

#### 3.1.2. Сортировка по различным критериям

Система поддерживает несколько типов сортировки:
- **По вероятности** (probability DESC) — наиболее часто встречающиеся
- **По дате** (created_at DESC) — самые последние
- **По алфавиту** (question ASC) — по тексту вопроса
- **По сложности** — сгруппированные по уровням

### 3.2. Формирование списка с ссылками на ресурсы

#### 3.2.1. Связь вопросов с видео

Система использует схему отношения "многие ко многим" через таблицу `question_video`:

```sql
CREATE TABLE question_video (
    question_id INTEGER REFERENCES questions(id),
    video_id INTEGER REFERENCES processed_videos(id),
    PRIMARY KEY (question_id, video_id)
);

CREATE TABLE question_timecodes (
    question_id INTEGER REFERENCES questions(id),
    video_id INTEGER REFERENCES processed_videos(id),
    timecode_start VARCHAR(10),
    timecode_seconds INTEGER,
    PRIMARY KEY (question_id, video_id)
);
```

**Получение видео по вопросу:**
```python
@app.get("/api/questions/{question_id}")
async def get_public_question_detail(question_id: int):
    # Видео, в которых встречался этот вопрос (с таймкодами)
    videos = await conn.fetch(
        """
        SELECT pv.id, pv.title, pv.youtube_url, pv.platform,
               qt.timecode_start, qt.timecode_seconds
        FROM question_video qv
        JOIN processed_videos pv ON pv.id = qv.video_id
        LEFT JOIN question_timecodes qt ON qt.question_id = qv.question_id AND qt.video_id = qv.video_id
        WHERE qv.question_id = $1
        ORDER BY pv.title
        """,
        question_id,
    )
```

**Формирование списка на фронтенде:**
```javascript
// В компоненте детализации вопроса
<div v-if="question.videos && question.videos.length" class="video-links">
  <h3>Видео-источники:</h3>
  <div v-for="video in question.videos" :key="video.id" class="video-link">
    <a :href="video.url" target="_blank">{{ video.title }}</a>
    <span v-if="video.timecode">⏱ {{ video.timecode }}</span>
  </div>
</div>
```

### 3.3. Просмотр видеофрагментов по таймкоду

#### 3.3.1. Обработка и хранение таймкодов

Система сохраняет таймкоды при обработке видео:

```python
def parse_timecode_to_seconds(tc):
    """Parse timecode string like '12:34' or '1:02:03' to seconds"""
    if not tc:
        return 0
    try:
        parts = str(tc).split(":")
        parts = [int(p) for p in parts]
        if len(parts) == 3:
            return parts[0] * 3600 + parts[1] * 60 + parts[2]
        elif len(parts) == 2:
            return parts[0] * 60 + parts[1]
        return int(tc)
    except (ValueError, TypeError):
        return 0

# При сохранении используем оба формата
tc = q.get("timecode")
if tc:
    tc_seconds = parse_timecode_to_seconds(tc)
    await conn.execute(
        """INSERT INTO question_timecodes (question_id, video_id, timecode_start, timecode_seconds)
           VALUES ($1, $2, $3, $4) ON CONFLICT (question_id, video_id) DO NOTHING""",
        question_id,
        db_video_id,
        str(tc),
        tc_seconds,
    )
```

#### 3.3.2. Воспроизведение видео по таймкоду

На фронтенде системы реализована возможность перехода к конкретному моменту в видео:

```javascript
// В компоненте детализации вопроса
<a 
  v-for="video in question.videos" 
  :key="video.id" 
  :href="`${video.url}${video.timecode_seconds ? '?t=' + video.timecode_seconds : ''}`" 
  target="_blank"
  class="timecoded-link"
>
  {{ video.title }} 
  <span v-if="video.timecode" class="timecode-badge">⏱ {{ video.timecode }}</span>
</a>
```

### 3.4. Статистика частоты вопросов

#### 3.4.1. Алгоритм расчета вероятности

Система автоматически рассчитывает вероятность встречи вопроса на собеседовании:

```python
async def update_probabilities(conn):
    """Обновить вероятности для всех вопросов (на основе % видео, в которых встречается вопрос)"""
    total_videos = await conn.fetchval("SELECT COUNT(*) FROM processed_videos")
    
    if total_videos > 0:
        # Обновляем вероятность для ВСЕХ вопросов (не только approved)
        # Вероятность = кол-во видео с этим вопросом / общее кол-во видео * 100
        await conn.execute(
            """
            UPDATE questions 
            SET probability = (
                SELECT COALESCE(COUNT(DISTINCT qv.video_id) * 100.0 / $1, 0)
                FROM question_video qv
                WHERE qv.question_id = questions.id
            )
            """,
            total_videos,
        )
```

#### 3.4.2. Отображение статистики

Веб-интерфейс показывает вероятность как процент:

```javascript
// В списке вопросов
<span class="q-prob">{{ (q.probability||0).toFixed(0) }}%</span>

// В детализации вопроса
<span v-if="question.probability" class="meta-prob">{{ question.probability.toFixed(0) }}% вероятность</span>
```

### 3.5. Сохранение вопросов в избранное с заметками

#### 3.5.1. Система закладок

Система использует таблицу `bookmarks` для хранения избранных вопросов:

```sql
CREATE TABLE bookmarks (
    id SERIAL PRIMARY KEY,
    question_id INTEGER REFERENCES questions(id),
    user_session VARCHAR(255),
    note TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(question_id, user_session)
);
```

**Реализация на бэкенде:**
```python
@app.post("/api/bookmarks")
async def toggle_bookmark(data: dict = Body(...)):
    """Добавить/удалить вопрос из закладок"""
    question_id = data.get("question_id")
    user_session = data.get("user_session", "")
    note = data.get("note", "")
    
    if not question_id or not user_session:
        raise HTTPException(
            status_code=400, detail="question_id и user_session обязательны"
        )
    
    existing = await conn.fetchval(
        "SELECT id FROM bookmarks WHERE question_id = $1 AND user_session = $2",
        question_id,
        user_session,
    )
    
    if existing:
        await conn.execute("DELETE FROM bookmarks WHERE id = $1", existing)
        return {"bookmarked": False, "message": "Закладка удалена"}
    else:
        await conn.execute(
            "INSERT INTO bookmarks (question_id, user_session, note) VALUES ($1, $2, $3)",
            question_id,
            user_session,
            note,
        )
        return {"bookmarked": True, "message": "Добавлено в закладки"}

@app.put("/api/notes/{question_id}")
async def save_note(question_id: int, data: dict = Body(...)):
    """Сохранить заметку к вопросу"""
    user_session = data.get("user_session", "")
    note = data.get("note", "")
    if not user_session:
        raise HTTPException(status_code=400, detail="user_session обязателен")
    
    await conn.execute(
        """
        INSERT INTO user_notes (question_id, user_session, note)
        VALUES ($1, $2, $3)
        ON CONFLICT (question_id, user_session) DO UPDATE SET note = $3, updated_at = CURRENT_TIMESTAMP
        """,
        question_id,
        user_session,
        note,
    )
    return {"message": "Заметка сохранена"}
```

#### 3.5.2. Реализация на фронтенде

```javascript
// В компоненте вопроса
<button class="btn btn-secondary btn-sm" @click="toggleBookmark">
  <svg width="16" height="16" viewBox="0 0 24 24" :fill="isBookmarked ? 'currentColor' : 'none'" stroke="currentColor" stroke-width="2">
    <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/>
  </svg>
  {{ isBookmarked ? 'В закладках' : 'Сохранить' }}
</button>

// Поле для заметки
<section class="section">
  <h2>Моя заметка</h2>
  <textarea v-model="note" class="input" rows="3" placeholder="Ваши короткие заметки по вопросу"></textarea>
  <button class="btn btn-secondary btn-sm" @click="saveNote">Сохранить заметку</button>
</section>
```

### 3.6. Архитектура обработки видео

#### 3.6.1. Структура pipeline обработки

**Полный процесс обработки видео:**

1. **Скачивание аудио и субтитров (yt-dlp)** - 5-20%
2. **Транскрибация через Whisper** - 25-60% (самый длительный этап)  
3. **Извлечение вопросов через LLM** - 65-85%
4. **Сохранение в базу данных** - 90-100%

```python
async def process_video_pipeline(task_id: str, video_url: str, topic: str, level: str):
    """
    Главный pipeline обработки видео.
    Поддерживаемые платформы: YouTube, VK.video, Rutube, OK.ru, Dailymotion, Vimeo
    """
    # ========== Этап 1: Скачивание аудио ==========
    await update_task_progress(
        task_id, 5, "downloading", "Начинаем скачивание видео..."
    )
    
    try:
        download_result = await download_video_audio(video_url, task_id)
    except Exception as download_err:
        await update_task_progress(
            task_id, 5, "error", f"Ошибка скачивания: {download_err}"
        )
        raise

    # ========== Этап 2: Транскрибация ==========
    await update_task_progress(
        task_id, 25, "transcribing", "Транскрибация аудио через Whisper..."
    )
    
    try:
        whisper_result = await whisper_orchestrator.transcribe_audio(
            audio_path=audio_path, task_id=task_id, language="ru"
        )
    except Exception as whisper_err:
        await update_task_progress(
            task_id, 30, "error", f"Ошибка транскрибации: {whisper_err}"
        )
        raise

    # ========== Этап 3: Извлечение вопросов ==========
    await update_task_progress(
        task_id, 65, "extracting", "Извлечение вопросов через LLM..."
    )

    # ========== Этап 4: Сохранение в БД ==========
    await update_task_progress(task_id, 90, "saving", "Сохранение в базу данных...")
```

#### 3.6.2. Масштабирование и оркестрация

**WhisperOrchestrator** реализует per-task масштабирование:

```python
class WhisperOrchestrator:
    def __init__(self, max_workers: int = 2):
        self.max_workers = max_workers
        self.workers: Dict[str, WhisperWorker] = {}
        
    async def transcribe_audio(self, audio_path: Path, task_id: str, language: str = "ru"):
        worker = await self.get_available_worker()
        # Каждый воркер обрабатывает одно аудио полностью
        return await worker.transcribe(audio_path, language)
```

#### 3.6.3. Мониторинг и WebSocket

Система обеспечивает реальное обновление прогресса через WebSocket:

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

# Обновление прогресса через WebSocket
async def broadcast_to_task(task_id: str, data: dict):
    if redis_client:
        client_id = await redis_client.get(f"task:{task_id}:client")
        if client_id:
            await manager.send_progress(client_id, data)
```

### 3.7. Семантический поиск похожих вопросов

#### 3.7.1. Использование FAISS и Sentence Transformers

Система использует библиотеки FAISS и Sentence Transformers для семантического поиска:

```python
class QuestionSimilaritySearch:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')  # Легкая модель для русского языка
        self.index = None
        self.questions_data = []

    async def _build_index(self):
        # Получаем все одобренные вопросы
        questions = await conn.fetch("""
            SELECT id, question, topic, difficulty, probability
            FROM questions
            WHERE approved = TRUE
        """)
        
        # Создаем embeddings
        question_texts = [q['question'] for q in questions]
        embeddings = self.model.encode(question_texts, show_progress_bar=True)
        
        # Создаем FAISS индекс
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dimension)  # Inner product для косинусного сходства
        
        # Нормализуем векторы для косинусного сходства
        faiss.normalize_L2(embeddings)
        self.index.add(embeddings.astype('float32'))

    async def find_similar(self, question_text: str, question_id: int = None, limit: int = 10):
        # Создаем embedding для запроса
        query_embedding = self.model.encode([question_text])
        faiss.normalize_L2(query_embedding)
        
        # Ищем похожие
        scores, indices = self.index.search(query_embedding.astype('float32'), limit + 1)
```

#### 3.7.2. Кэширование и производительность

Система использует Redis для кэширования embeddings:

```python
async def _save_cache(self):
    """Сохранение индекса в кэш"""
    if self.index and self.questions_data:
        cache_data = {
            'index': self.index,
            'questions_data': self.questions_data
        }
        await self.redis_client.set("questions_embeddings_cache", pickle.dumps(cache_data))
```

### 3.8. Алгоритм интервального повторения SM-2

#### 3.8.1. Реализация SM-2 на бэкенде

Система использует алгоритм SuperMemo 2 для эффективного запоминания:

```python
@app.post("/api/trainer/sm2-review")
async def sm2_review(data: dict = Body(...)):
    """
    Записать результат повторения по SM-2.
    quality: 0-5 (0=забыл, 1=повтор, 3=сложно вспомнил, 5=идеально)
    """
    quality = max(0, min(5, quality))
    
    # Получаем текущую карточку или создаём
    card = await conn.fetchrow(
        "SELECT * FROM sr_cards WHERE user_session = $1 AND question_id = $2",
        user_session, question_id
    )
    
    if card:
        ef = card["easiness_factor"]
        interval = card["interval_days"]
        reps = card["repetitions"]
    else:
        ef = 2.5  # начальный фактор простоты
        interval = 0.0
        reps = 0

    # SM-2 алгоритм
    ef = ef + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    ef = max(1.3, ef)  # минимальный фактор простоты

    if quality >= 3:
        if reps == 0:
            interval = 1.0  # первый повтор через 1 день
        elif reps == 1:
            interval = 6.0  # второй повтор через 6 дней
        else:
            interval = interval * ef  # последующие интервалы
        reps += 1
    else:
        reps = 0
        interval = 0.04  # ~1 час (в днях) - вернуть на повтор

    next_review = datetime.now() + timedelta(days=interval)

    await conn.execute(
        """
        INSERT INTO sr_cards (user_session, question_id, easiness_factor, interval_days, repetitions,
                              next_review, last_quality, total_reviews)
        VALUES ($1, $2, $3, $4, $5, $6, $7, 1)
        ON CONFLICT (user_session, question_id) DO UPDATE SET
            easiness_factor = $3, interval_days = $4, repetitions = $5,
            next_review = $6, last_quality = $7,
            total_reviews = sr_cards.total_reviews + 1,
            updated_at = CURRENT_TIMESTAMP
        """,
        user_session, question_id, round(ef, 2), round(interval, 2), reps, next_review, quality
    )
```

#### 3.8.2. 3D флипкарты на фронтенде

Карточки реализованы с 3D-эффектом переворота:

```css
.fc-scene {
  width: 100%;
  max-width: 720px;
  min-height: 360px;
  perspective: 1000px;
  cursor: pointer;
}

.fc-card {
  width: 100%;
  min-height: 360px;
  position: relative;
  transform-style: preserve-3d;
  transition: transform .5s var(--ease);
}

.fc-card.flipped { transform: rotateY(180deg); }

.fc-face {
  position: absolute;
  inset: 0;
  backface-visibility: hidden;
  background: var(--c-surface);
  border: 1px solid var(--c-border);
  border-radius: var(--r-lg);
  padding: 2rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.fc-front { }
.fc-back { transform: rotateY(180deg); }
```

### 3.9. Модерация и управление контентом

#### 3.9.1. Админ-панель

Система включает админ-панель с шестью вкладками:
1. **Вопросы** - таблица с фильтрами, массовые действия
2. **Предложения** - модерация URL от пользователей  
3. **Feedback** - просмотр отзывов
4. **Видео** - список обработанных видео
5. **Тестовые задания** - CRUD
6. **Аналитика** - KPI, экспорт JSON/CSV

#### 3.9.2. Генерация ответов через LLM

Администратор может автоматически генерировать ответы на вопросы:

```python
@app.post("/api/admin/generate-answer/{question_id}")
async def generate_answer_for_question(question_id: int):
    # Получаем вопрос
    question_data = await conn.fetchrow(
        "SELECT id, question, topic, difficulty FROM questions WHERE id = $1", question_id
    )
    
    # Генерируем ответ через LLM
    prompt = f"""Ты — эксперт в области IT и программирования. Дай развёрнутый, но лаконичный ответ на вопрос технического собеседования.
    
    Вопрос: {question_text}
    Тема: {topic}
    Уровень: {difficulty}
    
    Требования к ответу:
    - Ответь кратко, но полно (2-4 абзаца)
    - Приведи примеры, если уместно
    - Используй простой и понятный язык
    - Структурируй ответ логично
    """
    
    llm_response = await call_llm_api_for_answer(prompt)
    
    # Сохраняем ответ
    await conn.execute(
        """UPDATE questions SET answer = $1 WHERE id = $2""", llm_response, question_id
    )
```

### 3.10. Технологии и инфраструктура

#### 3.10.1. Технологический стек

**Backend:**
- **Python 3.11+** / **FastAPI** (асинхронный REST API)
- **PostgreSQL 15** (основная БД)
- **Redis 7** (кэш задач, FAISS-эмбеддингов)
- **asyncpg** (асинхронный драйвер PostgreSQL)
- **yt-dlp** (загрузка видео)
- **faster-whisper** (CTranslate2) — транскрибация аудио
- **sentence-transformers + FAISS** (семантический поиск)
- **httpx** (HTTP-клиент для LLM API)

**Frontend:**
- **Vue 3.4** + **Vite 5** + **Pinia** (state management)
- **Кастомный CSS** (471 строка, без UI-библиотек)
- **Axios** (HTTP-клиент)

**AI/ML:**
- **Whisper large-v3-turbo** (транскрибация речи)
- **all-MiniLM-L6-v2** (эмбеддинги для семантического поиска)
- **LLM провайдеры**: OpenRouter (GPT-4o, Llama-3.1-70b) / Gemini 2.0 Flash / Groq

**Инфраструктура:**
- **Docker Compose** (6 сервисов)
- **WebSocket** (real-time обновления задач)
- **JWT-авторизация** (bcrypt)

#### 3.10.2. Сравнение технологий

| Технология | Преимущества | Недостатки | Обоснование выбора |
|------------|--------------|------------|-------------------|
| **faster-whisper** | 4-6x быстрее оригинального Whisper, поддержка CPU | Требует больше ресурсов для установки | Оптимальная производительность для персонального использования |
| **yt-dlp** | Поддержка 100+ платформ, активное развитие | Зависимость от изменений на целевых сайтах | Единственный надежный инструмент для мультисайтовой загрузки |
| **FAISS** | Быстрый семантический поиск, эффективное использование памяти | Требует предварительного обучения | Лучшее решение для поиска по схожести |
| **Sentence Transformers** | Поддержка русского языка, легковесность | Не так мощно как OpenAI embeddings | Умеренный баланс качества и производительности |
| **Vue 3** | Современный реактивный фреймворк, хорошая экосистема | Кривая обучения для новичков | Лучший выбор для SPA с комплексным UI |

### Заключение

InterviewHub представляет собой комплексную систему для автоматизированной обработки видеоконтента собеседований с применением современных технологий AI и машинного обучения. Система эффективно решает все поставленные задачи:

1. ✅ **Поиск вопросов** по технологии/теме с фильтрацией по уровню сложности
2. ✅ **Формирование списка** с ссылками на ресурсы и таймкодами  
3. ✅ **Просмотр видеофрагментов** по таймкоду
4. ✅ **Статистика частоты** вопросов для приоритезации подготовки
5. ✅ **Сохранение в избранное** с возможностью добавления заметок

Архитектура системы позволяет масштабироваться и адаптироваться к новым требованиям, а использование современных API и библиотек обеспечивает высокую производительность и точность обработки.