import os
import uuid
import json
import asyncio
import re
import random
from pathlib import Path
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import httpx
import redis.asyncio as redis
import yt_dlp

# ============== Конфигурация ==============
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://diploma:diploma123@localhost:5432/interview_prep")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "http://localhost:5678/webhook/youtube-questions")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
# Несколько Whisper инстансов для параллельной обработки
WHISPER_SERVICES = os.getenv("WHISPER_SERVICES", "http://localhost:8001,http://localhost:8002").split(",")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")  # Бесплатный быстрый LLM
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")  # Google Gemini
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")  # OpenRouter — без лимитов!
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "auto")  # auto, openrouter, groq, gemini, ollama
TEMP_DIR = Path("/app/temp")
TEMP_DIR.mkdir(exist_ok=True)

# Параметры параллельной обработки
AUDIO_OVERLAP_SECONDS = 5  # Перекрытие между частями аудио для корректного слияния
MIN_CHUNK_DURATION = 60  # Минимальная длина части в секундах (не делить короткие видео)

# TTL для Redis (24 часа для длинных видео)
REDIS_TTL = 86400  # 24 часа

# ============== Глобальные объекты ==============
redis_client: Optional[redis.Redis] = None
connected_clients: Dict[str, WebSocket] = {}

# ============== Pydantic модели ==============
class YouTubeRequest(BaseModel):
    youtube_url: str
    topic: Optional[str] = "General"
    level: Optional[str] = "middle"

class ProgressUpdate(BaseModel):
    task_id: str = ""
    progress: int = 0
    step: str = ""

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
    global redis_client
    
    # Startup
    print("🚀 Starting up...")
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    
    # Whisper теперь распределённый (несколько инстансов)
    print(f"📡 Whisper services: {WHISPER_SERVICES}")
    
    # Проверяем доступность Whisper сервисов
    available_services = []
    for service_url in WHISPER_SERVICES:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{service_url.strip()}/health")
                if response.status_code == 200:
                    available_services.append(service_url.strip())
                    print(f"✅ Whisper service {service_url} is available!")
        except Exception as e:
            print(f"⚠️ Whisper service {service_url} not available yet: {e}")
    
    if available_services:
        print(f"✅ {len(available_services)}/{len(WHISPER_SERVICES)} Whisper services ready")
    else:
        print("⚠️ No Whisper services available yet (will retry on use)")
    
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
    # Проверяем доступность Whisper сервисов
    whisper_status = {}
    for i, service_url in enumerate(WHISPER_SERVICES):
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                response = await client.get(f"{service_url.strip()}/health")
                whisper_status[f"whisper-{i+1}"] = response.status_code == 200
        except:
            whisper_status[f"whisper-{i+1}"] = False
    
    # Считаем temp файлы
    temp_files = list(TEMP_DIR.glob("*"))
    temp_size_mb = sum(f.stat().st_size for f in temp_files if f.is_file()) / (1024 * 1024)
    
    return {
        "status": "healthy",
        "whisper_services": whisper_status,
        "whisper_urls": WHISPER_SERVICES,
        "parallel_processing": len([v for v in whisper_status.values() if v]) > 1,
        "temp_files_count": len(temp_files),
        "temp_size_mb": round(temp_size_mb, 2)
    }

@app.delete("/api/cleanup-temp", tags=["Status"])
async def cleanup_all_temp():
    """Очистка всех временных файлов (для администрирования)"""
    cleaned = 0
    for f in TEMP_DIR.glob("*"):
        if f.is_file():
            try:
                f.unlink()
                cleaned += 1
            except:
                pass
    return {"cleaned_files": cleaned}

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
    await redis_client.set(f"task:{task_id}", json.dumps(task_data), ex=REDIS_TTL)
    
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
    await redis_client.set(f"task:{task_id}:client", client_id, ex=REDIS_TTL)
    await redis_client.set(f"client:{client_id}:last_task", task_id, ex=REDIS_TTL)
    
    # Добавляем в список задач клиента (для истории)
    tasks_key = f"client:{client_id}:tasks"
    await redis_client.lpush(tasks_key, task_id)
    await redis_client.ltrim(tasks_key, 0, 19)  # Храним только 20 последних
    await redis_client.expire(tasks_key, REDIS_TTL)
    
    task_data = {
        "task_id": task_id,
        "youtube_url": request.youtube_url,
        "topic": request.topic,
        "level": request.level,
        "status": "pending",
        "progress": 0,
        "step": "В очереди..."
    }
    await redis_client.set(f"task:{task_id}", json.dumps(task_data), ex=REDIS_TTL)
    
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

@app.get("/api/tasks/{client_id}", tags=["Status"])
async def get_client_tasks(client_id: str):
    """
    Получение всех задач клиента (для истории)
    Хранит до 20 последних задач
    """
    tasks_key = f"client:{client_id}:tasks"
    task_ids = await redis_client.lrange(tasks_key, 0, 19)  # Последние 20 задач
    
    tasks = []
    for task_id in task_ids:
        task_data = await redis_client.get(f"task:{task_id}")
        if task_data:
            task = json.loads(task_data)
            tasks.append({
                "task_id": task.get("task_id"),
                "status": task.get("status"),
                "progress": task.get("progress", 0),
                "step": task.get("step", ""),
                "video_title": task.get("result", {}).get("video_title", "Unknown"),
                "questions_count": task.get("result", {}).get("questions_count", 0),
                "youtube_url": task.get("youtube_url", "")
            })
    
    return {"tasks": tasks, "count": len(tasks)}

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

@app.get("/api/subtitles/{task_id}", tags=["Export"])
async def get_subtitles(task_id: str):
    """Скачать оригинальные YouTube субтитры по task_id"""
    from fastapi.responses import JSONResponse
    
    subtitles_data = await redis_client.get(f"subtitles:{task_id}")
    if not subtitles_data:
        raise HTTPException(status_code=404, detail="Subtitles not found (video may not have subtitles)")
    
    subtitles = json.loads(subtitles_data)
    return JSONResponse(
        content={
            "task_id": task_id,
            "subtitles": subtitles,
            "count": len(subtitles)
        },
        headers={
            "Content-Disposition": f'attachment; filename="subtitles_{task_id}.json"'
        }
    )

@app.get("/api/full-export/{task_id}", tags=["Export"])
async def full_export(task_id: str):
    """
    Полный экспорт данных задачи:
    - Транскрипция (merged, Whisper, YouTube subtitles)
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
        # Финальная merged транскрипция
        "transcript": transcript.get("transcript", ""),
        "segments": transcript.get("segments", []),
        "transcript_length": transcript.get("length", 0),
        # Whisper raw (для сравнения)
        "whisper_raw": transcript.get("whisper_raw", ""),
        "whisper_segments": transcript.get("whisper_segments", []),
        # YouTube субтитры (для сравнения)
        "youtube_subtitles": transcript.get("youtube_subtitles", []),
        "has_subtitles": transcript.get("has_subtitles", False),
        # Вопросы и метаданные
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
        await redis_client.set(f"task:{update.task_id}", json.dumps(task), ex=REDIS_TTL)
    
    # Отправляем через WebSocket
    await manager.broadcast_to_task(update.task_id, {
        "type": "progress",
        "task_id": update.task_id,
        "progress": update.progress,
        "step": update.step
    })
    
    return {"status": "ok"}

@app.post("/internal/download-audio", tags=["Internal"])
async def download_audio(request: DownloadRequest):
    """Скачивание аудио и субтитров с YouTube"""
    import time
    
    try:
        video_id = extract_video_id(request.youtube_url)
        audio_path = TEMP_DIR / f"{video_id}.mp3"
        
        # Пробуем скачать субтитры (5 попыток, 3 сек между ними) — оптимизировано
        subtitles = []
        max_retries = 5
        retry_delay = 3  # Быстрее, но достаточно для YouTube

        # Ротация User-Agent для обхода блокировки
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15'
        ]

        subs_opts = {
            'skip_download': True,
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': ['ru'],  # ТОЛЬКО русские субтитры
            'subtitlesformat': 'vtt',
            'outtmpl': str(TEMP_DIR / f"{video_id}"),
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': True,
            'extractor_retries': 5,  # Уменьшим для скорости
            'retries': 5,
            'sleep_interval': 2,
            'sleep_interval_subtitles': 3,
            'nooverwrites': True,  # НЕ перезаписывать существующие файлы
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            },
        }
        
        def check_subtitle_files():
            """Проверяет наличие файлов субтитров в temp"""
            sub_file = TEMP_DIR / f"{video_id}.ru.vtt"
            if sub_file.exists():
                print(f"📄 File exists: {sub_file}, size: {sub_file.stat().st_size} bytes")
                subs = parse_vtt_subtitles(sub_file)
                print(f"📝 Parsed {len(subs)} segments")
                if subs:
                    print(f"✅ Found ru subtitles: {len(subs)} segments")
                    return subs
                else:
                    print("⚠️ File exists but no valid segments parsed")
            else:
                print(f"❌ File not found: {sub_file}")
            return []
        
        for attempt in range(max_retries):
            # Проверяем файл ПЕРЕД скачиванием
            subtitles = check_subtitle_files()
            if subtitles:
                print(f"✅ Subtitles already exist from previous attempt")
                break

            try:
                print(f"📥 Downloading subtitles (attempt {attempt + 1}/{max_retries})...")
                with yt_dlp.YoutubeDL(subs_opts) as ydl:
                    ydl.download([request.youtube_url])
                
                # Небольшая задержка чтобы файл успел записаться
                time.sleep(1)
                
            except Exception as e:
                print(f"⚠️ Subtitles attempt {attempt + 1} failed: {e}")

            # Проверяем файлы ПОСЛЕ каждой попытки (даже если была ошибка)
            subtitles = check_subtitle_files()
            if subtitles:
                break

            # Ждём перед следующей попыткой
            if attempt < max_retries - 1:
                print(f"⏳ Waiting {retry_delay}s before retry...")
                time.sleep(retry_delay)
        
        if not subtitles:
            print("⚠️ No subtitles after all retries, will check again after transcription")
        
        # Скачиваем аудио
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
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(request.youtube_url, download=True)
            title = info.get('title', 'Unknown')
        
        # Сохраняем video_id в Redis для повторной попытки после транскрибации
        await redis_client.set(f"video_id:{request.task_id}", video_id, ex=REDIS_TTL)
        
        # Сохраняем субтитры в Redis (если есть)
        if subtitles:
            await redis_client.set(
                f"subtitles:{request.task_id}",
                json.dumps(subtitles),
                ex=REDIS_TTL
            )
        
        return {
            "audio_path": str(audio_path),
            "title": title,
            "video_id": video_id,
            "has_subtitles": len(subtitles) > 0,
            "subtitles_count": len(subtitles)
        }
    except Exception as e:
        error_msg = f"Download error: {str(e)}"
        print(f"❌ {error_msg}")
        
        # Обновляем статус задачи — ошибка скачивания
        task_data = await redis_client.get(f"task:{request.task_id}")
        if task_data:
            task = json.loads(task_data)
            task["status"] = "error"
            task["error"] = error_msg
            await redis_client.set(f"task:{request.task_id}", json.dumps(task), ex=REDIS_TTL)
        
        # Отправляем ошибку клиенту через WebSocket
        await manager.broadcast_to_task(request.task_id, {
            "type": "error",
            "task_id": request.task_id,
            "error": error_msg
        })
        
        raise HTTPException(status_code=500, detail=error_msg)

@app.post("/internal/transcribe", tags=["Internal"])
async def transcribe_audio(request: TranscribeRequest):
    """
    Параллельная транскрибация аудио через несколько Whisper инстансов.
    
    Архитектура:
    1. Определить длительность аудио
    2. Разрезать на N частей (N = кол-во Whisper инстансов)
    3. Отправить части параллельно на разные инстансы
    4. Объединить результаты с учётом overlap
    5. Слить с YouTube субтитрами (если есть)
    """
    import subprocess
    
    try:
        audio_path = Path(request.audio_path)
        
        # 1. Определяем длительность аудио через ffprobe
        duration = await get_audio_duration(audio_path)
        print(f"🎵 Audio duration: {duration:.1f} seconds ({duration/60:.1f} minutes)")
        
        # 2. Определяем доступные Whisper сервисы
        available_services = await get_available_whisper_services()
        num_services = len(available_services)
        
        if num_services == 0:
            raise HTTPException(status_code=503, detail="No Whisper services available")
        
        print(f"🖥️ Available Whisper services: {num_services}")
        
        # 3. Решаем: параллельно или последовательно
        # Параллелим только если видео > 2 минут на сервис И есть несколько сервисов
        min_parallel_duration = MIN_CHUNK_DURATION * num_services
        
        if duration < min_parallel_duration or num_services == 1:
            # Короткое видео или один сервис — обычная обработка
            print(f"📝 Using single Whisper instance (duration < {min_parallel_duration}s or single service)")
            whisper_result = await transcribe_single(audio_path, available_services[0])
        else:
            # Длинное видео — параллельная обработка
            print(f"⚡ Using PARALLEL transcription with {num_services} Whisper instances")
            whisper_result = await transcribe_parallel(audio_path, duration, available_services, request.task_id)
        
        whisper_transcript = whisper_result["text"]
        whisper_segments = whisper_result.get("segments", [])
        
        # 4. Получаем субтитры YouTube из Redis (если есть)
        subtitles_data = await redis_client.get(f"subtitles:{request.task_id}")
        youtube_subtitles = json.loads(subtitles_data) if subtitles_data else []
        
        # Проверяем файл субтитров (могли загрузиться позже)
        if not youtube_subtitles:
            video_id = await redis_client.get(f"video_id:{request.task_id}")
            if video_id:
                video_id = video_id.decode() if isinstance(video_id, bytes) else video_id
                print(f"🔍 Checking for late-loaded subtitles for {video_id}...")
                sub_file = TEMP_DIR / f"{video_id}.ru.vtt"
                if sub_file.exists():
                    youtube_subtitles = parse_vtt_subtitles(sub_file)
                    if youtube_subtitles:
                        print(f"✅ Found late-loaded ru subtitles: {len(youtube_subtitles)} segments")
                        await redis_client.set(
                            f"subtitles:{request.task_id}",
                            json.dumps(youtube_subtitles),
                            ex=REDIS_TTL
                        )
        
        # 5. Слияние: субтитры (точный текст) + Whisper (пунктуация)
        if youtube_subtitles:
            print(f"🔀 Merging {len(youtube_subtitles)} subtitles with Whisper...")
            merged_segments = merge_subtitles_with_whisper(youtube_subtitles, whisper_segments)
            merged_transcript = " ".join([s["text"] for s in merged_segments])
        else:
            print("⚠️ No subtitles available, using Whisper only")
            merged_segments = whisper_segments
            merged_transcript = whisper_transcript
        
        # 6. Сохраняем все версии в Redis
        await redis_client.set(
            f"transcript:{request.task_id}", 
            json.dumps({
                "transcript": merged_transcript,
                "segments": merged_segments,
                "whisper_raw": whisper_transcript,
                "whisper_segments": whisper_segments,
                "youtube_subtitles": youtube_subtitles,
                "has_subtitles": len(youtube_subtitles) > 0,
                "length": len(merged_transcript),
                "parallel_processing": num_services > 1 and duration >= min_parallel_duration
            }),
            ex=REDIS_TTL
        )
        
        # Удаляем временные файлы
        video_id = await redis_client.get(f"video_id:{request.task_id}")
        if video_id:
            video_id = video_id.decode() if isinstance(video_id, bytes) else video_id
            cleanup_temp_files(video_id)
        
        # Обновляем статус задачи
        task_data = await redis_client.get(f"task:{request.task_id}")
        if task_data:
            task = json.loads(task_data)
            task["progress"] = 60
            task["stage"] = "Транскрипция завершена"
            await redis_client.set(f"task:{request.task_id}", json.dumps(task), ex=REDIS_TTL)
        
        return {
            "transcript": merged_transcript,
            "segments": merged_segments,
            "has_subtitles": len(youtube_subtitles) > 0,
            "parallel_processing_used": num_services > 1 and duration >= min_parallel_duration
        }
        
    except httpx.TimeoutException as e:
        error_msg = f"Whisper service timeout: видео слишком длинное ({e})"
        print(f"❌ Transcription timeout: {e}")
        await update_task_error(request.task_id, error_msg)
        raise HTTPException(status_code=504, detail=error_msg)
        
    except Exception as e:
        error_msg = f"Transcription error: {str(e)}"
        print(f"❌ {error_msg}")
        await update_task_error(request.task_id, error_msg)
        raise HTTPException(status_code=500, detail=error_msg)


async def get_audio_duration(audio_path: Path) -> float:
    """Получить длительность аудио через ffprobe"""
    import subprocess
    
    try:
        result = subprocess.run([
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(audio_path)
        ], capture_output=True, text=True, timeout=30)
        
        return float(result.stdout.strip())
    except Exception as e:
        print(f"⚠️ ffprobe error: {e}, estimating duration from file size")
        # Fallback: оценка по размеру файла (MP3 192kbps ≈ 24KB/сек)
        file_size = audio_path.stat().st_size
        return file_size / (24 * 1024)


async def get_available_whisper_services() -> List[str]:
    """Получить список доступных Whisper сервисов"""
    available = []
    
    for service_url in WHISPER_SERVICES:
        service_url = service_url.strip()
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{service_url}/health")
                if response.status_code == 200:
                    available.append(service_url)
        except:
            print(f"⚠️ Whisper service {service_url} not available")
    
    return available


async def transcribe_single(audio_path: Path, service_url: str) -> Dict[str, Any]:
    """Транскрибация через один Whisper сервис"""
    async with httpx.AsyncClient(timeout=1800.0) as client:
        with open(audio_path, "rb") as audio_file:
            files = {"file": (audio_path.name, audio_file, "audio/mpeg")}
            response = await client.post(
                f"{service_url}/transcribe",
                files=files,
                params={"language": "ru"}
            )
    
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail=f"Whisper error: {response.text}")
    
    return response.json()


async def transcribe_parallel(
    audio_path: Path, 
    duration: float, 
    services: List[str],
    task_id: str
) -> Dict[str, Any]:
    """
    Параллельная транскрибация: разрезаем аудио на части и обрабатываем одновременно.
    
    Используем overlap для корректного слияния на границах.
    """
    import subprocess
    
    num_parts = len(services)
    part_duration = duration / num_parts
    
    print(f"✂️ Splitting audio into {num_parts} parts of ~{part_duration:.0f}s each")
    
    # Создаём части аудио с overlap
    audio_parts = []
    for i in range(num_parts):
        start_time = max(0, i * part_duration - AUDIO_OVERLAP_SECONDS if i > 0 else 0)
        # Для последней части — до конца
        if i == num_parts - 1:
            end_time = duration
        else:
            end_time = (i + 1) * part_duration + AUDIO_OVERLAP_SECONDS
        
        part_path = TEMP_DIR / f"{audio_path.stem}_part{i}.mp3"
        
        # FFmpeg команда для вырезания части
        cmd = [
            "ffmpeg", "-y", "-i", str(audio_path),
            "-ss", str(start_time),
            "-to", str(end_time),
            "-c", "copy",  # Быстрое копирование без перекодирования
            str(part_path)
        ]
        
        subprocess.run(cmd, capture_output=True, timeout=60)
        
        audio_parts.append({
            "path": part_path,
            "start_offset": start_time,
            "service": services[i],
            "index": i
        })
        
        print(f"   Part {i+1}: {start_time:.1f}s - {end_time:.1f}s → {services[i]}")
    
    # Отправляем все части параллельно
    async def transcribe_part(part: Dict) -> Dict[str, Any]:
        """Транскрибация одной части"""
        try:
            async with httpx.AsyncClient(timeout=1800.0) as client:
                with open(part["path"], "rb") as audio_file:
                    files = {"file": (part["path"].name, audio_file, "audio/mpeg")}
                    response = await client.post(
                        f"{part['service']}/transcribe",
                        files=files,
                        params={"language": "ru"}
                    )
            
            if response.status_code != 200:
                print(f"⚠️ Part {part['index']} failed: {response.text}")
                return {"text": "", "segments": [], "index": part["index"], "offset": part["start_offset"]}
            
            result = response.json()
            result["index"] = part["index"]
            result["offset"] = part["start_offset"]
            return result
            
        except Exception as e:
            print(f"⚠️ Part {part['index']} error: {e}")
            return {"text": "", "segments": [], "index": part["index"], "offset": part["start_offset"]}
        finally:
            # Удаляем временный файл части
            if part["path"].exists():
                part["path"].unlink()
    
    # Запускаем все транскрибации параллельно
    print(f"🚀 Starting parallel transcription...")
    results = await asyncio.gather(*[transcribe_part(part) for part in audio_parts])
    
    # Сортируем по индексу
    results = sorted(results, key=lambda x: x["index"])
    
    # Объединяем результаты с учётом offset
    merged_segments = []
    merged_text_parts = []
    
    for result in results:
        offset = result.get("offset", 0)
        
        for seg in result.get("segments", []):
            # Корректируем таймкоды с учётом offset
            adjusted_seg = {
                "start": seg["start"] + offset,
                "end": seg["end"] + offset,
                "text": seg["text"]
            }
            merged_segments.append(adjusted_seg)
        
        if result.get("text"):
            merged_text_parts.append(result["text"])
    
    # Удаляем дубликаты на границах (overlap)
    merged_segments = remove_overlap_duplicates(merged_segments)
    
    # Сортируем по времени
    merged_segments = sorted(merged_segments, key=lambda x: x["start"])
    
    full_text = " ".join(merged_text_parts)
    
    print(f"✅ Parallel transcription complete: {len(merged_segments)} segments")
    
    return {
        "text": full_text,
        "segments": merged_segments,
        "language": "ru"
    }


def remove_overlap_duplicates(segments: List[Dict]) -> List[Dict]:
    """Удаление дублирующихся сегментов на границах overlap"""
    if not segments:
        return []
    
    # Сортируем по времени начала
    sorted_segs = sorted(segments, key=lambda x: x["start"])
    
    unique = [sorted_segs[0]]
    
    for seg in sorted_segs[1:]:
        last = unique[-1]
        
        # Если сегменты сильно пересекаются (>50% по времени) — это дубликат
        overlap_start = max(last["start"], seg["start"])
        overlap_end = min(last["end"], seg["end"])
        overlap_duration = max(0, overlap_end - overlap_start)
        
        seg_duration = seg["end"] - seg["start"]
        
        if seg_duration > 0 and overlap_duration / seg_duration > 0.5:
            # Дубликат — пропускаем
            continue
        
        # Если тексты почти идентичны — дубликат
        if last["text"].strip().lower() == seg["text"].strip().lower():
            continue
        
        unique.append(seg)
    
    return unique


async def update_task_error(task_id: str, error_msg: str):
    """Обновить статус задачи с ошибкой"""
    task_data = await redis_client.get(f"task:{task_id}")
    if task_data:
        task = json.loads(task_data)
        task["status"] = "error"
        task["error"] = error_msg
        await redis_client.set(f"task:{task_id}", json.dumps(task), ex=REDIS_TTL)
    
    await manager.broadcast_to_task(task_id, {
        "type": "error",
        "task_id": task_id,
        "error": error_msg
    })

def merge_subtitles_with_whisper(subtitles: List[Dict], whisper_segments: List[Dict]) -> List[Dict]:
    """
    Слияние YouTube субтитров с Whisper:
    - Субтитры дают точный текст (без ошибок распознавания)
    - Whisper даёт пунктуацию (вопросительные знаки)
    """
    merged = []
    
    for sub in subtitles:
        sub_start = sub["start"]
        sub_end = sub["end"]
        sub_text = sub["text"]
        
        # Ищем соответствующий сегмент Whisper для получения пунктуации
        best_whisper = None
        best_overlap = 0
        
        for wseg in whisper_segments:
            w_start = wseg["start"]
            w_end = wseg["end"]
            
            # Вычисляем перекрытие по времени
            overlap_start = max(sub_start, w_start)
            overlap_end = min(sub_end, w_end)
            overlap = max(0, overlap_end - overlap_start)
            
            if overlap > best_overlap:
                best_overlap = overlap
                best_whisper = wseg
        
        # Определяем пунктуацию из Whisper
        final_text = sub_text
        if best_whisper:
            whisper_text = best_whisper["text"]
            # Если Whisper заканчивает на "?", добавляем к субтитрам
            if whisper_text.strip().endswith("?"):
                if not final_text.strip().endswith("?"):
                    final_text = final_text.rstrip() + "?"
            # Проверяем вопросительные слова и добавляем "?"
            question_words = ["как", "что", "почему", "зачем", "где", "когда", "кто", "какой", "какая", "какие", "сколько"]
            lower_text = final_text.lower()
            if any(lower_text.startswith(qw) for qw in question_words) and not final_text.endswith("?"):
                # Проверяем, есть ли "?" в Whisper для этого времени
                for wseg in whisper_segments:
                    if abs(wseg["start"] - sub_start) < 3 and "?" in wseg["text"]:
                        final_text = final_text.rstrip() + "?"
                        break
        
        merged.append({
            "start": sub_start,
            "end": sub_end,
            "text": final_text,
            "source": "merged"
        })
    
    return merged

@app.post("/internal/extract-questions", tags=["Internal"])
async def extract_questions(request: ExtractQuestionsRequest):
    """Извлечение вопросов через Groq API с таймкодами — обрабатывает чанками для полноты"""
    try:
        # Получаем сегменты с таймкодами из Redis
        transcript_data = await redis_client.get(f"transcript:{request.task_id}")
        segments = []
        if transcript_data:
            data = json.loads(transcript_data)
            segments = data.get("segments", [])
        
        # Формируем текст с таймкодами для LLM — каждый сегмент на отдельной строке
        all_lines = []
        for seg in segments:
            start_time = seg.get("start", 0)
            mins = int(start_time // 60)
            secs = int(start_time % 60)
            text = seg.get('text', '').strip()
            if text:
                all_lines.append(f"[{mins:02d}:{secs:02d}] {text}")
        
        transcript_with_times = "\n".join(all_lines)
        
        print(f"📝 Transcript size: {len(transcript_with_times)} chars, {len(all_lines)} lines")
        
        if not transcript_with_times:
            transcript_with_times = request.transcript[:20000]
        
        # === CHUNKING для длинных транскриптов ===
        # Разбиваем на чанки по ~5000 символов для лучшего извлечения
        CHUNK_SIZE = 5000  # Уменьшено для повышения точности
        
        all_questions = []
        
        if len(transcript_with_times) <= CHUNK_SIZE:
            # Короткий транскрипт — один вызов
            chunks = [transcript_with_times]
        else:
            # Длинный транскрипт — разбиваем по строкам
            lines = all_lines
            chunks = []
            current_chunk = []
            current_size = 0
            
            for line in lines:
                line_size = len(line) + 1  # +1 для \n
                if current_size + line_size > CHUNK_SIZE and current_chunk:
                    chunks.append("\n".join(current_chunk))
                    current_chunk = [line]
                    current_size = line_size
                else:
                    current_chunk.append(line)
                    current_size += line_size
            
            if current_chunk:
                chunks.append("\n".join(current_chunk))
            
            print(f"📦 Transcript split into {len(chunks)} chunks for complete extraction")
        
        # Обрабатываем каждый чанк
        for i, chunk in enumerate(chunks):
            print(f"🔍 Processing chunk {i+1}/{len(chunks)} ({len(chunk)} chars)...")
            
            prompt = f"""Ты эксперт по анализу IT-собеседований. Твоя задача — извлечь ВОПРОСЫ ИНТЕРВЬЮЕРА из транскрипции.

=== ПРАВИЛА ИЗВЛЕЧЕНИЯ ===

✅ ИЗВЛЕКАЙ (вопросы интервьюера):
- Технические вопросы: "Что такое REST API?", "Как работает HashMap?"
- Вопросы про опыт: "Расскажите о вашем опыте работы?", "Какие проекты вы делали?"
- Уточняющие вопросы: "А как именно это работает?", "Можете подробнее объяснить?"
- Проверочные вопросы: "А почему вы выбрали такой подход?", "Какие альтернативы знаете?"

❌ НЕ ИЗВЛЕКАЙ (ответы кандидата и мусор):
- Ответы кандидата на вопросы (даже если заканчиваются на "?")
- Односложные междометия: "Да?", "Ага?", "Угу?", "М?"
- Риторические вопросы в ответах: "ну типа как бы да?"
- Переспросы кандидата: "Вы имеете в виду...?"

=== ПРИМЕРЫ (Few-shot) ===

ПРИМЕР 1 — Извлечь:
Транскрипция: "[01:23] Расскажите что вы знаете про микросервисную архитектуру?"
Ответ: [{{"question": "Что вы знаете про микросервисную архитектуру?", "timecode": "01:23", "topic": "{request.topic}", "difficulty": "{request.level}", "answer": "Микросервисы — архитектурный стиль, где приложение состоит из независимых сервисов"}}]

ПРИМЕР 2 — Извлечь:
Транскрипция: "[05:45] А какие паттерны проектирования вы использовали на практике?"
Ответ: [{{"question": "Какие паттерны проектирования вы использовали на практике?", "timecode": "05:45", "topic": "{request.topic}", "difficulty": "{request.level}", "answer": "Singleton, Factory, Observer, Strategy — основные GoF паттерны"}}]

ПРИМЕР 3 — НЕ извлекать (это ответ кандидата):
Транскрипция: "[02:30] Ну это когда у нас есть отдельные сервисы которые общаются через API?"
Ответ: [] (это ответ кандидата, не вопрос интервьюера)

ПРИМЕР 4 — НЕ извлекать (междометие):
Транскрипция: "[03:00] Угу?"
Ответ: [] (односложное междометие)

=== ФОРМАТ ОТВЕТА ===
Верни ТОЛЬКО валидный JSON массив. Никакого текста до или после.

[{{"question": "Текст вопроса?", "answer": "Краткий ответ (1-2 предложения)", "timecode": "MM:SS", "topic": "{request.topic}", "difficulty": "{request.level}"}}]

=== ТРАНСКРИПЦИЯ (часть {i+1}/{len(chunks)}) ===
{chunk}

JSON:"""
            
            # Выбор LLM провайдера: Gemini (рекомендуется) > Groq > Ollama
            chunk_questions = await call_llm_api(prompt)
            
            all_questions.extend(chunk_questions)
            print(f"   ✅ Extracted {len(chunk_questions)} questions from chunk {i+1}")
            
            # Задержка между чанками (Gemini: не нужна, Groq: 3 сек)
            if i < len(chunks) - 1 and not GEMINI_API_KEY:
                await asyncio.sleep(2)  # Только для Groq
        
        # Подсчитаем общее количество вопросительных знаков
        total_question_marks = transcript_with_times.count('?')
        
        # Убираем дубликаты (могут появиться на границах чанков)
        # Убираем дубликаты и фильтруем некачественные вопросы
        unique_questions = deduplicate_questions(all_questions)
        filtered_questions = filter_low_quality_questions(unique_questions)
        
        print(f"📊 Extracted: {len(all_questions)} raw → {len(unique_questions)} unique → {len(filtered_questions)} quality")
        
        return {"questions": filtered_questions}
    except Exception as e:
        error_msg = f"LLM Error: {str(e)}"
        print(f"❌ {error_msg}")
        
        # Обновляем статус задачи — ошибка извлечения вопросов
        task_data = await redis_client.get(f"task:{request.task_id}")
        if task_data:
            task = json.loads(task_data)
            task["status"] = "error"
            task["error"] = error_msg
            await redis_client.set(f"task:{request.task_id}", json.dumps(task), ex=REDIS_TTL)
        
        # Отправляем ошибку клиенту через WebSocket
        await manager.broadcast_to_task(request.task_id, {
            "type": "error",
            "task_id": request.task_id,
            "error": error_msg
        })
        
        raise HTTPException(status_code=500, detail=error_msg)

async def call_llm_api(prompt: str) -> List[Dict[str, Any]]:
    """Умный выбор LLM провайдера: OpenRouter (без лимитов) > Groq > Gemini > Ollama"""
    provider = LLM_PROVIDER.lower()
    
    # Auto-select лучший доступный провайдер
    # OpenRouter приоритетнее — практически без лимитов!
    if provider == "auto":
        if OPENROUTER_API_KEY:
            provider = "openrouter"
        elif GROQ_API_KEY:
            provider = "groq"
        elif GEMINI_API_KEY:
            provider = "gemini"
        else:
            provider = "ollama"
    
    print(f"🤖 Using LLM provider: {provider}")
    
    if provider == "openrouter":
        return await call_openrouter_api(prompt)
    elif provider == "gemini":
        return await call_gemini_api(prompt)
    elif provider == "groq":
        return await call_groq_api(prompt)
    else:
        return await call_ollama_api(prompt)


async def call_openrouter_api(prompt: str) -> List[Dict[str, Any]]:
    """OpenRouter API — бесплатные модели без лимитов для длинных видео!"""
    async with httpx.AsyncClient(timeout=180.0) as client:
        response = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://interview-prep.local",
                "X-Title": "Interview Prep"
            },
            json={
                "model": "mistralai/devstral-2512:free",  # Mistral Devstral — быстрый и бесплатный!
                "messages": [
                    {"role": "system", "content": "Ты эксперт по анализу IT-собеседований. Извлекай только осмысленные технические вопросы и вопросы про опыт. Игнорируй междометия и переспросы. Отвечай ТОЛЬКО валидным JSON массивом."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3,
                "max_tokens": 8000
            }
        )
        
        if response.status_code != 200:
            print(f"OpenRouter error: {response.status_code} - {response.text}")
            # Fallback на Groq если OpenRouter не работает
            if GROQ_API_KEY:
                print("⚠️ OpenRouter failed, falling back to Groq...")
                return await call_groq_api(prompt)
            raise Exception(f"OpenRouter API error: {response.status_code}")
        
        result = response.json()
        llm_response = result["choices"][0]["message"]["content"]
        return parse_questions_from_llm(llm_response)


async def call_gemini_api(prompt: str) -> List[Dict[str, Any]]:
    """Вызов Google Gemini API — огромные лимиты (1M токенов/мин)!"""
    # Пробуем разные модели Gemini
    models = ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-flash-latest"]
    
    for model in models:
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}",
                    headers={"Content-Type": "application/json"},
                    json={
                        "contents": [{
                            "parts": [{
                                "text": f"Ты эксперт по анализу IT-собеседований. Извлекай только осмысленные технические вопросы и вопросы про опыт. Игнорируй междометия и переспросы. Отвечай ТОЛЬКО валидным JSON массивом.\n\n{prompt}"
                            }]
                        }],
                        "generationConfig": {
                            "temperature": 0.3,
                            "maxOutputTokens": 8000
                        }
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    llm_response = result["candidates"][0]["content"]["parts"][0]["text"]
                    print(f"✅ Gemini model {model} works!")
                    return parse_questions_from_llm(llm_response)
                elif response.status_code == 404:
                    print(f"⚠️ Gemini model {model} not found, trying next...")
                    continue
                else:
                    print(f"Gemini error: {response.status_code} - {response.text}")
                    raise Exception(f"Gemini API error: {response.status_code}")
        except httpx.TimeoutException:
            print(f"⚠️ Gemini model {model} timeout, trying next...")
            continue
    
    # Все модели не сработали — fallback на Groq
    print("⚠️ All Gemini models failed, falling back to Groq...")
    return await call_groq_api(prompt)


async def call_groq_api(prompt: str) -> List[Dict[str, Any]]:
    """Вызов Groq API для быстрой генерации — с retry при rate limiting (429)"""
    max_retries = 5
    base_delay = 10  # Начальная задержка 10 секунд
    
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {GROQ_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "llama-3.3-70b-versatile",  # Мощная модель, бесплатно
                        "messages": [
                            {"role": "system", "content": "Ты эксперт по анализу IT-собеседований. Извлекай только осмысленные технические вопросы и вопросы про опыт. Игнорируй междометия и переспросы. Отвечай ТОЛЬКО валидным JSON массивом."},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.3,
                        "max_tokens": 8000
                    }
                )
                
                if response.status_code == 429:
                    # Rate limiting — ждём и повторяем
                    delay = base_delay * (2 ** attempt)  # Exponential backoff: 10, 20, 40, 80, 160 сек
                    print(f"⏳ Groq rate limit (429). Retry {attempt + 1}/{max_retries} after {delay}s...")
                    await asyncio.sleep(delay)
                    continue
                
                if response.status_code != 200:
                    print(f"Groq error: {response.status_code} - {response.text}")
                    raise Exception(f"Groq API error: {response.status_code}")
                
                result = response.json()
                llm_response = result["choices"][0]["message"]["content"]
                return parse_questions_from_llm(llm_response)
                
        except httpx.TimeoutException:
            print(f"⏳ Groq timeout. Retry {attempt + 1}/{max_retries}...")
            await asyncio.sleep(base_delay)
            continue
    
    # Все попытки исчерпаны
    raise Exception("Groq API error: 429 (rate limit exceeded after retries)")

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
            await redis_client.set(f"task:{request.task_id}", json.dumps(task), ex=REDIS_TTL)
        
        # Отправляем результат через WebSocket
        await manager.broadcast_to_task(request.task_id, {
            "type": "result",
            "task_id": request.task_id,
            "questions": request.questions,
            "video_title": request.video_title
        })
        
        return {"status": "saved", "count": len(request.questions)}
    except Exception as e:
        error_msg = f"Save error: {str(e)}"
        print(f"❌ {error_msg}")
        
        # Обновляем статус задачи — ошибка сохранения
        task_data = await redis_client.get(f"task:{request.task_id}")
        if task_data:
            task = json.loads(task_data)
            task["status"] = "error"
            task["error"] = error_msg
            await redis_client.set(f"task:{request.task_id}", json.dumps(task), ex=REDIS_TTL)
        
        # Отправляем ошибку клиенту через WebSocket
        await manager.broadcast_to_task(request.task_id, {
            "type": "error",
            "task_id": request.task_id,
            "error": error_msg
        })
        
        raise HTTPException(status_code=500, detail=error_msg)

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

def parse_vtt_subtitles(vtt_path: Path) -> List[Dict[str, Any]]:
    """Парсинг VTT субтитров в список сегментов с таймкодами"""
    subtitles = []
    try:
        with open(vtt_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Паттерн для VTT таймкодов: 00:00:01.000 --> 00:00:04.000 (игнорируем дополнительные атрибуты)
        pattern = r'(\d{2}:\d{2}:\d{2}\.\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}\.\d{3})(?:\s+[^\n]*)?\s*\n(.*?)(?=\n\n|\n\d{2}:\d{2}|\Z)'
        matches = re.findall(pattern, content, re.DOTALL)
        
        for start_str, end_str, text in matches:
            # Конвертируем время в секунды
            start_parts = start_str.split(':')
            start_secs = int(start_parts[0]) * 3600 + int(start_parts[1]) * 60 + float(start_parts[2])
            
            end_parts = end_str.split(':')
            end_secs = int(end_parts[0]) * 3600 + int(end_parts[1]) * 60 + float(end_parts[2])
            
            # Очищаем текст от тегов и лишних пробелов
            # Удаляем HTML-теги, временные метки внутри текста и цветовые теги
            clean_text = re.sub(r'<[^>]+>', '', text)  # HTML теги
            clean_text = re.sub(r'\d{2}:\d{2}:\d{2}\.\d{3}', '', clean_text)  # Временные метки внутри текста
            clean_text = re.sub(r'\s+', ' ', clean_text).strip()
            
            if clean_text and clean_text not in ['', '[Music]', '[Музыка]']:
                subtitles.append({
                    "start": round(start_secs, 1),
                    "end": round(end_secs, 1),
                    "text": clean_text
                })
        
        # Объединяем соседние сегменты с одинаковым текстом
        merged = []
        for sub in subtitles:
            if merged and merged[-1]["text"] == sub["text"]:
                merged[-1]["end"] = sub["end"]
            else:
                merged.append(sub)
        
        return merged
    except Exception as e:
        print(f"VTT parse error: {e}")
        return []

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

def cleanup_temp_files(video_id: str):
    """Очистка временных файлов после обработки"""
    try:
        patterns = [
            TEMP_DIR / f"{video_id}.mp3",
            TEMP_DIR / f"{video_id}.ru.vtt",
            TEMP_DIR / f"{video_id}.en.vtt",
        ]
        for file_path in patterns:
            if file_path.exists():
                file_path.unlink()
                print(f"🧹 Cleaned up: {file_path.name}")
    except Exception as e:
        print(f"⚠️ Cleanup error: {e}")

def filter_low_quality_questions(questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Фильтрация только явного мусора (односложные междометия)"""
    if not questions:
        return []
    
    # Только явный мусор — односложные междометия без контекста
    garbage_patterns = [
        r'^(да|нет|ага|угу|ну|ок|м+|хм+|э)\??$',  # Односложные междометия
        r'^(что|как|а)\??$',  # Одиночные слова-переспросы
        r'^.{1,4}\??$',  # Очень короткие (до 4 символов)
    ]
    
    filtered = []
    removed_count = 0
    
    for q in questions:
        question_text = q.get('question', '').strip()
        question_lower = question_text.lower()
        
        # Проверяем только на явный мусор
        is_garbage = False
        for pattern in garbage_patterns:
            if re.match(pattern, question_lower):
                is_garbage = True
                break
        
        if is_garbage:
            removed_count += 1
            continue
        
        # Вопрос прошёл фильтрацию
        filtered.append(q)
    
    if removed_count > 0:
        print(f"🗑️ Filtered out {removed_count} garbage questions")
    
    return filtered

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
        
        # Слишком короткий вопрос (минимум 5 символов)
        if len(question_text) < 5:
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
        async with httpx.AsyncClient(timeout=1800.0) as client:  # 30 мин для длинных видео
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
            await redis_client.set(f"task:{task_id}", json.dumps(task), ex=REDIS_TTL)
        
        # Отправляем ошибку клиенту
        await manager.broadcast_to_task(task_id, {
            "type": "error",
            "task_id": task_id,
            "error": str(e)
        })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
