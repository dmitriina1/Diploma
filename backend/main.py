import os
import uuid
import json
import asyncio
import re
from pathlib import Path
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import httpx
import redis.asyncio as redis
import yt_dlp
import whisper

# ============== Конфигурация ==============
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://diploma:diploma123@localhost:5432/interview_prep")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "http://localhost:5678/webhook/youtube-questions")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")  # Бесплатный быстрый LLM
USE_GROQ = os.getenv("USE_GROQ", "true").lower() == "true"  # По умолчанию используем Groq
TEMP_DIR = Path("/app/temp")
TEMP_DIR.mkdir(exist_ok=True)

# ============== Глобальные объекты ==============
redis_client: Optional[redis.Redis] = None
whisper_model = None
connected_clients: Dict[str, WebSocket] = {}

# ============== Pydantic модели ==============
class YouTubeRequest(BaseModel):
    youtube_url: str
    topic: Optional[str] = "General"
    level: Optional[str] = "middle"

class ProgressUpdate(BaseModel):
    task_id: str
    progress: int
    step: str

class DownloadRequest(BaseModel):
    youtube_url: str
    task_id: str

class TranscribeRequest(BaseModel):
    audio_path: str
    task_id: str

class ExtractQuestionsRequest(BaseModel):
    transcript: str
    task_id: str
    topic: str = "General"
    level: str = "middle"

class SaveQuestionsRequest(BaseModel):
    questions: List[Dict[str, Any]]
    youtube_url: str
    video_title: str
    task_id: str

class TaskStatus(BaseModel):
    task_id: str
    status: str
    progress: int
    step: str
    result: Optional[Dict[str, Any]] = None

# ============== Lifecycle ==============
@asynccontextmanager
async def lifespan(app: FastAPI):
    global redis_client, whisper_model
    
    # Startup
    print("🚀 Starting up...")
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    
    # Загружаем Whisper модель (base - баланс скорости и качества)
    print("📦 Loading Whisper model (base)...")
    try:
        whisper_model = whisper.load_model("base")
        print("✅ Whisper model loaded!")
    except Exception as e:
        print(f"⚠️ Whisper will be loaded on first use: {e}")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down...")
    if redis_client:
        await redis_client.close()

app = FastAPI(
    title="Interview Prep API",
    description="""
## API для подготовки к IT собеседованиям

Извлечение вопросов из YouTube видео с помощью:
- **Whisper** для транскрибации аудио
- **Groq API (LLaMA 70B)** для извлечения вопросов
- **n8n** для оркестрации процессов

### Основные эндпоинты:
- `POST /api/process-video` - Запуск обработки видео
- `GET /api/status/{task_id}` - Статус задачи
- `GET /api/full-export/{task_id}` - Полный экспорт (транскрипция + вопросы)
""",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {"name": "Processing", "description": "Обработка видео"},
        {"name": "Export", "description": "Экспорт данных"},
        {"name": "Status", "description": "Статус и мониторинг"},
        {"name": "Internal", "description": "Внутренние эндпоинты для n8n"}
    ]
)

# ============== CORS ==============
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============== WebSocket Manager ==============
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        print(f"✅ Client {client_id} connected. Total: {len(self.active_connections)}")
    
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            print(f"❌ Client {client_id} disconnected. Total: {len(self.active_connections)}")
    
    async def send_progress(self, client_id: str, data: dict):
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_json(data)
            except Exception as e:
                print(f"Error sending to {client_id}: {e}")
                self.disconnect(client_id)
    
    async def broadcast_to_task(self, task_id: str, data: dict):
        # Получаем client_id для task_id из Redis
        if redis_client:
            client_id = await redis_client.get(f"task:{task_id}:client")
            if client_id:
                await self.send_progress(client_id, data)

manager = ConnectionManager()

# ============== WebSocket Endpoint ==============
@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    try:
        while True:
            # Ждём сообщения от клиента (keep-alive)
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(client_id)

# ============== API Endpoints ==============
@app.get("/", tags=["Status"])
async def root():
    """Корневой эндпоинт"""
    return {"message": "Interview Prep API", "status": "running"}

@app.get("/health", tags=["Status"])
async def health():
    """Проверка здоровья сервиса"""
    return {"status": "healthy", "whisper_loaded": whisper_model is not None}

@app.post("/api/process-video", tags=["Processing"])
async def process_video(request: YouTubeRequest, background_tasks: BackgroundTasks):
    """
    Запуск обработки YouTube видео
    
    - **youtube_url**: Ссылка на YouTube видео
    - **topic**: Тема (например: Backend, Frontend, DevOps)
    - **level**: Уровень сложности (junior, middle, senior)
    """
    task_id = str(uuid.uuid4())
    
    # Валидация URL
    if not is_valid_youtube_url(request.youtube_url):
        raise HTTPException(status_code=400, detail="Invalid YouTube URL")
    
    # Сохраняем задачу в Redis
    task_data = {
        "task_id": task_id,
        "youtube_url": request.youtube_url,
        "topic": request.topic,
        "level": request.level,
        "status": "pending",
        "progress": 0,
        "step": "В очереди..."
    }
    await redis_client.set(f"task:{task_id}", json.dumps(task_data), ex=3600)
    
    # Запускаем обработку в фоне
    background_tasks.add_task(trigger_n8n_workflow, task_id, request)
    
    return {"task_id": task_id, "status": "started"}

@app.post("/api/process-video/{client_id}", tags=["Processing"])
async def process_video_with_client(client_id: str, request: YouTubeRequest, background_tasks: BackgroundTasks):
    """Запуск обработки с привязкой к WebSocket клиенту"""
    task_id = str(uuid.uuid4())
    
    if not is_valid_youtube_url(request.youtube_url):
        raise HTTPException(status_code=400, detail="Invalid YouTube URL")
    
    # Связываем task с client
    await redis_client.set(f"task:{task_id}:client", client_id, ex=3600)
    await redis_client.set(f"client:{client_id}:last_task", task_id, ex=3600)
    
    task_data = {
        "task_id": task_id,
        "youtube_url": request.youtube_url,
        "topic": request.topic,
        "level": request.level,
        "status": "pending",
        "progress": 0,
        "step": "В очереди..."
    }
    await redis_client.set(f"task:{task_id}", json.dumps(task_data), ex=3600)
    
    # Отправляем начальный статус через WebSocket
    await manager.send_progress(client_id, {
        "type": "progress",
        "task_id": task_id,
        "progress": 0,
        "step": "Запуск обработки..."
    })
    
    background_tasks.add_task(trigger_n8n_workflow, task_id, request)
    
    return {"task_id": task_id, "status": "started"}

@app.get("/api/task/{task_id}", tags=["Status"])
async def get_task_status(task_id: str):
    """Получение статуса задачи по task_id"""
    task_data = await redis_client.get(f"task:{task_id}")
    if not task_data:
        raise HTTPException(status_code=404, detail="Task not found")
    return json.loads(task_data)

@app.get("/api/last-result/{client_id}", tags=["Status"])
async def get_last_result(client_id: str):
    """Получение последнего результата для WebSocket клиента"""
    task_id = await redis_client.get(f"client:{client_id}:last_task")
    if not task_id:
        return {"status": "no_task"}
    
    task_data = await redis_client.get(f"task:{task_id}")
    if not task_data:
        return {"status": "no_task"}
    
    task = json.loads(task_data)
    return task

@app.get("/api/questions", tags=["Export"])
async def get_all_questions(topic: Optional[str] = None, level: Optional[str] = None):
    """
    Получение всех вопросов с фильтрацией
    
    - **topic**: Фильтр по теме (опционально)
    - **level**: Фильтр по уровню (опционально)
    """
    questions_data = await redis_client.get("all_questions")
    if questions_data:
        questions = json.loads(questions_data)
        # Фильтрация
        if topic:
            questions = [q for q in questions if q.get("topic", "").lower() == topic.lower()]
        if level:
            questions = [q for q in questions if q.get("difficulty", "").lower() == level.lower()]
        return {"questions": questions}
    return {"questions": []}

@app.get("/api/export/{task_id}", tags=["Export"])
async def export_questions_json(task_id: str):
    """Скачать вопросы задачи в формате JSON"""
    from fastapi.responses import JSONResponse
    
    task_data = await redis_client.get(f"task:{task_id}")
    if not task_data:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = json.loads(task_data)
    result = task.get("result", {})
    
    export_data = {
        "task_id": task_id,
        "video_title": result.get("video_title", "Unknown"),
        "questions_count": result.get("questions_count", 0),
        "questions": result.get("questions", []),
        "exported_at": str(asyncio.get_event_loop().time())
    }
    
    return JSONResponse(
        content=export_data,
        headers={
            "Content-Disposition": f'attachment; filename="questions_{task_id}.json"'
        }
    )

@app.get("/api/export-all", tags=["Export"])
async def export_all_questions():
    """Скачать ВСЕ вопросы из базы в формате JSON"""
    from fastapi.responses import JSONResponse
    
    questions_data = await redis_client.get("all_questions")
    questions = json.loads(questions_data) if questions_data else []
    
    return JSONResponse(
        content={"questions": questions, "total": len(questions)},
        headers={
            "Content-Disposition": 'attachment; filename="all_questions.json"'
        }
    )

@app.get("/api/transcript/{task_id}", tags=["Export"])
async def get_transcript(task_id: str):
    """Скачать транскрипцию с таймкодами по task_id"""
    from fastapi.responses import JSONResponse
    
    transcript_data = await redis_client.get(f"transcript:{task_id}")
    if not transcript_data:
        raise HTTPException(status_code=404, detail="Transcript not found")
    
    data = json.loads(transcript_data)
    return JSONResponse(
        content=data,
        headers={
            "Content-Disposition": f'attachment; filename="transcript_{task_id}.json"'
        }
    )

@app.get("/api/full-export/{task_id}", tags=["Export"])
async def full_export(task_id: str):
    """
    Полный экспорт данных задачи:
    - Транскрипция с таймкодами
    - Все извлечённые вопросы
    - Метаданные видео
    """
    from fastapi.responses import JSONResponse
    
    # Получаем транскрипцию
    transcript_data = await redis_client.get(f"transcript:{task_id}")
    transcript = json.loads(transcript_data) if transcript_data else {}
    
    # Получаем задачу с вопросами
    task_data = await redis_client.get(f"task:{task_id}")
    task = json.loads(task_data) if task_data else {}
    
    export = {
        "task_id": task_id,
        "transcript": transcript.get("transcript", ""),
        "segments": transcript.get("segments", []),
        "transcript_length": transcript.get("length", 0),
        "video_title": task.get("result", {}).get("video_title", "Unknown"),
        "questions": task.get("result", {}).get("questions", []),
        "questions_count": task.get("result", {}).get("questions_count", 0),
        "status": task.get("status", "unknown")
    }
    
    return JSONResponse(
        content=export,
        headers={
            "Content-Disposition": f'attachment; filename="full_export_{task_id}.json"'
        }
    )

# ============== Internal Endpoints (для n8n) ==============
@app.post("/internal/update-progress")
async def update_progress(update: ProgressUpdate):
    """Обновление прогресса (вызывается из n8n)"""
    # Обновляем в Redis
    task_data = await redis_client.get(f"task:{update.task_id}")
    if task_data:
        task = json.loads(task_data)
        task["progress"] = update.progress
        task["step"] = update.step
        task["status"] = "processing" if update.progress < 100 else "completed"
        await redis_client.set(f"task:{update.task_id}", json.dumps(task), ex=3600)
    
    # Отправляем через WebSocket
    await manager.broadcast_to_task(update.task_id, {
        "type": "progress",
        "task_id": update.task_id,
        "progress": update.progress,
        "step": update.step
    })
    
    return {"status": "ok"}

@app.post("/internal/download-audio")
async def download_audio(request: DownloadRequest):
    """Скачивание аудио с YouTube"""
    try:
        video_id = extract_video_id(request.youtube_url)
        audio_path = TEMP_DIR / f"{video_id}.mp3"
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': str(TEMP_DIR / f"{video_id}.%(ext)s"),
            'quiet': True,
            'no_warnings': True,
            # Обход блокировок YouTube
            'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            },
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(request.youtube_url, download=True)
            title = info.get('title', 'Unknown')
        
        return {
            "audio_path": str(audio_path),
            "title": title,
            "video_id": video_id
        }
    except Exception as e:
        print(f"Download error: {e}")
        raise HTTPException(status_code=500, detail=f"Download error: {str(e)}")

@app.post("/internal/transcribe", tags=["Internal"])
async def transcribe_audio(request: TranscribeRequest):
    """Транскрибация аудио через Whisper с таймкодами"""
    global whisper_model
    
    try:
        if whisper_model is None:
            print("📦 Loading Whisper model...")
            whisper_model = whisper.load_model("base")
        
        # Транскрибация с таймкодами
        result = whisper_model.transcribe(
            request.audio_path,
            language="ru",
            fp16=False,
            word_timestamps=True  # Включаем таймкоды
        )
        
        transcript = result["text"]
        
        # Собираем сегменты с таймкодами
        segments = []
        for seg in result.get("segments", []):
            segments.append({
                "start": seg.get("start", 0),
                "end": seg.get("end", 0),
                "text": seg.get("text", "").strip()
            })
        
        # Сохраняем транскрипцию с таймкодами в Redis
        await redis_client.set(
            f"transcript:{request.task_id}", 
            json.dumps({
                "transcript": transcript,
                "segments": segments,
                "audio_path": request.audio_path,
                "length": len(transcript)
            }),
            ex=7200  # 2 часа
        )
        
        # Удаляем временный файл
        try:
            Path(request.audio_path).unlink()
        except:
            pass
        
        return {"transcript": transcript, "segments": segments}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription error: {str(e)}")

@app.post("/internal/extract-questions", tags=["Internal"])
async def extract_questions(request: ExtractQuestionsRequest):
    """Извлечение вопросов через Groq API с таймкодами и проверкой русского языка"""
    try:
        # Получаем сегменты с таймкодами из Redis
        transcript_data = await redis_client.get(f"transcript:{request.task_id}")
        segments = []
        if transcript_data:
            data = json.loads(transcript_data)
            segments = data.get("segments", [])
        
        # Формируем текст с таймкодами для LLM
        transcript_with_times = ""
        for seg in segments:
            start_time = int(seg.get("start", 0))
            mins, secs = divmod(start_time, 60)
            transcript_with_times += f"[{mins:02d}:{secs:02d}] {seg.get('text', '')}\n"
        
        if not transcript_with_times:
            transcript_with_times = request.transcript[:20000]
        
        # Улучшенный промпт с таймкодами и проверкой русского языка
        prompt = f"""Ты эксперт по анализу собеседований и русскому языку. Твоя задача:
1. Извлечь АБСОЛЮТНО ВСЕ вопросы из транскрипции
2. Проверить и исправить орфографию/грамматику каждого вопроса
3. Указать таймкод, где задаётся вопрос

КРИТИЧЕСКИ ВАЖНЫЕ ПРАВИЛА:
1. Извлеки КАЖДЫЙ вопрос БЕЗ ИСКЛЮЧЕНИЯ — даже уточняющие и дополнительные
2. "А на Python писали?" и "А на Java?" — это ДВА РАЗНЫХ вопроса, НЕ объединяй!
3. Уточняющие вопросы — тоже отдельные вопросы
4. НЕ ОБЪЕДИНЯЙ похожие вопросы
5. НЕ ПРОПУСКАЙ вопросы, даже глупые или нерелевантные
6. Убирай имена людей (Иван, Павел и т.д.)
7. НЕ ПРИДУМЫВАЙ вопросы — только те, что есть в тексте
8. ИСПРАВЬ орфографические и грамматические ошибки в вопросах
9. Если Whisper неправильно распознал слово — исправь по контексту
10. Укажи таймкод в формате MM:SS

ФОРМАТ ОТВЕТА — JSON массив:
[
  {{
    "question": "Грамматически правильный вопрос?",
    "answer": "Краткий ответ",
    "timecode": "01:23",
    "topic": "{request.topic}",
    "difficulty": "{request.level}"
  }}
]

Тема: {request.topic}
Уровень: {request.level}

Транскрипция с таймкодами:
{transcript_with_times[:25000]}
"""
        
        if USE_GROQ and GROQ_API_KEY:
            # Используем Groq API (быстро и качественно)
            questions = await call_groq_api(prompt)
        else:
            # Fallback на Ollama
            questions = await call_ollama_api(prompt)
        
        return {"questions": questions}
    except Exception as e:
        print(f"LLM Error: {e}")
        raise HTTPException(status_code=500, detail=f"LLM error: {str(e)}")

async def call_groq_api(prompt: str) -> List[Dict[str, Any]]:
    """Вызов Groq API для быстрой генерации"""
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.3-70b-versatile",  # Мощная модель, бесплатно
                "messages": [
                    {"role": "system", "content": "Ты эксперт по IT-собеседованиям. Отвечай только JSON."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3,
                "max_tokens": 4000
            }
        )
        
        if response.status_code != 200:
            print(f"Groq error: {response.status_code} - {response.text}")
            raise Exception(f"Groq API error: {response.status_code}")
        
        result = response.json()
        llm_response = result["choices"][0]["message"]["content"]
        return parse_questions_from_llm(llm_response)

async def call_ollama_api(prompt: str) -> List[Dict[str, Any]]:
    """Fallback на локальный Ollama"""
    async with httpx.AsyncClient(timeout=300.0) as client:
        response = await client.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": "llama3.2:1b",
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "num_predict": 4000
                }
            }
        )
        
        if response.status_code != 200:
            raise Exception("Ollama error")
        
        result = response.json()
        llm_response = result.get("response", "[]")
        return parse_questions_from_llm(llm_response)

@app.post("/internal/save-questions")
async def save_questions(request: SaveQuestionsRequest):
    """Сохранение вопросов"""
    try:
        # Добавляем метаданные к вопросам
        for q in request.questions:
            q["source_url"] = request.youtube_url
            q["video_title"] = request.video_title
        
        # Сохраняем в Redis (для демо)
        existing = await redis_client.get("all_questions")
        all_questions = json.loads(existing) if existing else []
        all_questions.extend(request.questions)
        await redis_client.set("all_questions", json.dumps(all_questions))
        
        # Обновляем результат задачи
        task_data = await redis_client.get(f"task:{request.task_id}")
        if task_data:
            task = json.loads(task_data)
            task["result"] = {
                "questions": request.questions,
                "video_title": request.video_title,
                "questions_count": len(request.questions)
            }
            task["status"] = "completed"
            await redis_client.set(f"task:{request.task_id}", json.dumps(task), ex=3600)
        
        # Отправляем результат через WebSocket
        await manager.broadcast_to_task(request.task_id, {
            "type": "result",
            "task_id": request.task_id,
            "questions": request.questions,
            "video_title": request.video_title
        })
        
        return {"status": "saved", "count": len(request.questions)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Save error: {str(e)}")

# ============== Helper Functions ==============
def is_valid_youtube_url(url: str) -> bool:
    """Проверка валидности YouTube URL"""
    patterns = [
        r'(https?://)?(www\.)?youtube\.com/watch\?v=[\w-]+',
        r'(https?://)?(www\.)?youtu\.be/[\w-]+',
        r'(https?://)?(www\.)?youtube\.com/shorts/[\w-]+'
    ]
    return any(re.match(pattern, url) for pattern in patterns)

def extract_video_id(url: str) -> str:
    """Извлечение ID видео из URL"""
    patterns = [
        r'(?:v=|/)([a-zA-Z0-9_-]{11})',
        r'youtu\.be/([a-zA-Z0-9_-]{11})',
        r'shorts/([a-zA-Z0-9_-]{11})'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return str(uuid.uuid4())[:11]

def parse_questions_from_llm(response: str) -> List[Dict[str, Any]]:
    """Парсинг JSON из ответа LLM с дедупликацией"""
    try:
        # Пробуем найти JSON в ответе
        json_match = re.search(r'\[[\s\S]*\]', response)
        if json_match:
            questions = json.loads(json_match.group())
            # Применяем очистку и дедупликацию
            return deduplicate_questions(questions)
        return []
    except json.JSONDecodeError:
        # Если JSON невалидный, возвращаем пустой список
        return []

def deduplicate_questions(questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Удаление дубликатов вопросов"""
    if not questions:
        return []
    
    # Список имён для очистки из вопросов
    common_names = ['иван', 'анна', 'сергей', 'алексей', 'дмитрий', 'михаил', 
                    'андрей', 'александр', 'елена', 'мария', 'ольга', 'наталья',
                    'владимир', 'артём', 'павел', 'николай', 'евгений', 'кирилл']
    
    seen_questions = set()
    unique_questions = []
    
    for q in questions:
        if not isinstance(q, dict) or 'question' not in q:
            continue
            
        question_text = q.get('question', '').strip()
        if not question_text:
            continue
        
        question_lower = question_text.lower()
        
        # Убираем имена из начала вопроса
        first_word = question_lower.split()[0] if question_lower.split() else ''
        if first_word.rstrip(',') in common_names:
            # Убираем имя из начала
            question_text = re.sub(r'^[\w]+,?\s*', '', question_text, count=1)
            q['question'] = question_text
            question_lower = question_text.lower()
        
        # Слишком короткий вопрос
        if len(question_text) < 8:
            continue
        
        # Нормализуем для проверки ТОЧНЫХ дубликатов
        normalized = re.sub(r'[^\w\s]', '', question_lower)
        normalized = ' '.join(normalized.split())  # Убираем лишние пробелы
        
        # Проверяем только на ТОЧНЫЕ дубликаты (вся строка целиком)
        if normalized not in seen_questions:
            seen_questions.add(normalized)
            unique_questions.append(q)
    
    return unique_questions

async def trigger_n8n_workflow(task_id: str, request: YouTubeRequest):
    """Запуск n8n workflow"""
    try:
        async with httpx.AsyncClient(timeout=600.0) as client:
            response = await client.post(
                N8N_WEBHOOK_URL,
                json={
                    "task_id": task_id,
                    "youtube_url": request.youtube_url,
                    "topic": request.topic,
                    "level": request.level
                }
            )
            print(f"n8n response: {response.status_code}")
    except Exception as e:
        print(f"n8n error: {e}")
        # Обновляем статус ошибки
        task_data = await redis_client.get(f"task:{task_id}")
        if task_data:
            task = json.loads(task_data)
            task["status"] = "error"
            task["error"] = str(e)
            await redis_client.set(f"task:{task_id}", json.dumps(task), ex=3600)
        
        # Отправляем ошибку клиенту
        await manager.broadcast_to_task(task_id, {
            "type": "error",
            "task_id": task_id,
            "error": str(e)
        })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
