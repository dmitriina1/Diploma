import os
import uuid
import json
import asyncio
import re
import random
from pathlib import Path
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import httpx
import redis.asyncio as redis
import yt_dlp

from similarity_search import get_similar_questions as search_similar_questions
from video_downloader import VideoDownloader

# ============== Конфигурация ==============
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://diploma:diploma123@localhost:5432/interview_prep")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "http://localhost:5678/webhook/youtube-questions")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
# Whisper через Nginx Load Balancer
WHISPER_SERVICE_URL = os.getenv("WHISPER_SERVICE_URL", "http://localhost:8001")
WHISPER_POOL_SIZE = int(os.getenv("WHISPER_POOL_SIZE", "2"))  # Количество Whisper реплик
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
whisper_pool: Optional["WhisperPool"] = None  # Инициализируется при старте
video_downloader: Optional[VideoDownloader] = None  # Универсальный загрузчик


# ============== WhisperPool — пул транскрибации с балансировкой ==============
class WhisperPool:
    """
    Пул Whisper сервисов с Nginx Load Balancer.
    
    Архитектура:
    - Nginx балансирует запросы между Whisper репликами (least_conn)
    - Backend делит аудио на части и отправляет параллельно
    - Результаты объединяются с учётом overlap
    
    Масштабирование:
        docker-compose up -d --scale whisper=N
    """
    
    def __init__(self, service_url: str, pool_size: int = 2):
        self.service_url = service_url.rstrip("/")
        self.pool_size = pool_size
        self.is_healthy = False
        self._lock = asyncio.Lock()
    
    async def health_check(self) -> bool:
        """Проверка доступности Whisper через Nginx"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.service_url}/health")
                self.is_healthy = response.status_code == 200
                return self.is_healthy
        except Exception as e:
            print(f"⚠️ Whisper pool health check failed: {e}")
            self.is_healthy = False
            return False
    
    async def detect_pool_size(self) -> int:
        """
        Автоматическое определение количества Whisper реплик.
        Делаем несколько запросов и смотрим на разные upstream адреса в логах Nginx.
        Fallback: используем значение из конфига.
        """
        try:
            # Пробуем определить через DNS резолвинг (Docker Compose создаёт записи для каждой реплики)
            import socket
            # whisper — имя сервиса в docker-compose
            # Docker создаёт A-записи для каждой реплики
            try:
                # Получаем все IP адреса сервиса whisper
                ips = socket.getaddrinfo("whisper", 8001, socket.AF_INET, socket.SOCK_STREAM)
                unique_ips = set(ip[4][0] for ip in ips)
                detected = len(unique_ips)
                if detected > 0:
                    print(f"🔍 Detected {detected} Whisper replicas via DNS")
                    self.pool_size = detected
                    return detected
            except socket.gaierror:
                pass
        except Exception as e:
            print(f"⚠️ Could not detect pool size: {e}")
        
        print(f"📊 Using configured pool_size: {self.pool_size}")
        return self.pool_size
    
    async def transcribe(self, audio_path: Path, language: str = "ru") -> Dict[str, Any]:
        """
        Транскрибация одного аудиофайла через Nginx → Whisper Pool.
        Nginx автоматически выбирает наименее загруженный инстанс.
        """
        async with httpx.AsyncClient(timeout=1800.0) as client:
            with open(audio_path, "rb") as audio_file:
                files = {"file": (audio_path.name, audio_file, "audio/mpeg")}
                response = await client.post(
                    f"{self.service_url}/transcribe",
                    files=files,
                    params={"language": language}
                )
        
        if response.status_code != 200:
            raise Exception(f"Whisper error: {response.text}")
        
        return response.json()
    
    async def transcribe_parallel(
        self, 
        audio_path: Path, 
        duration: float,
        task_id: str
    ) -> Dict[str, Any]:
        """
        Параллельная транскрибация: разрезаем аудио на части и отправляем
        одновременно на разные Whisper инстансы через Nginx.
        
        Args:
            audio_path: Путь к аудиофайлу
            duration: Длительность в секундах
            task_id: ID задачи для логирования
            
        Returns:
            Объединённый результат транскрибации
        """
        import subprocess
        
        num_parts = self.pool_size
        part_duration = duration / num_parts
        
        print(f"✂️ Splitting audio into {num_parts} parts of ~{part_duration:.0f}s each")
        
        # Создаём части аудио с overlap
        audio_parts = []
        for i in range(num_parts):
            start_time = max(0, i * part_duration - AUDIO_OVERLAP_SECONDS if i > 0 else 0)
            end_time = duration if i == num_parts - 1 else (i + 1) * part_duration + AUDIO_OVERLAP_SECONDS
            
            part_path = TEMP_DIR / f"{audio_path.stem}_part{i}.mp3"
            
            # FFmpeg для вырезания части
            cmd = [
                "ffmpeg", "-y", "-i", str(audio_path),
                "-ss", str(start_time),
                "-to", str(end_time),
                "-c", "copy",
                str(part_path)
            ]
            
            subprocess.run(cmd, capture_output=True, timeout=60)
            
            audio_parts.append({
                "path": part_path,
                "start_offset": start_time,
                "index": i
            })
            
            print(f"   Part {i+1}: {start_time:.1f}s - {end_time:.1f}s")
        
        # Параллельная транскрибация всех частей
        async def transcribe_part(part: Dict) -> Dict[str, Any]:
            try:
                result = await self.transcribe(part["path"])
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
        
        print(f"🚀 Starting parallel transcription ({num_parts} parts)...")
        results = await asyncio.gather(*[transcribe_part(part) for part in audio_parts])
        
        # Сортируем по индексу и объединяем
        results = sorted(results, key=lambda x: x["index"])
        
        merged_segments = []
        merged_text_parts = []
        
        for result in results:
            offset = result.get("offset", 0)
            
            for seg in result.get("segments", []):
                adjusted_seg = {
                    "start": seg["start"] + offset,
                    "end": seg["end"] + offset,
                    "text": seg["text"]
                }
                merged_segments.append(adjusted_seg)
            
            if result.get("text"):
                merged_text_parts.append(result["text"])
        
        # Удаляем дубликаты на границах overlap
        merged_segments = self._remove_overlap_duplicates(merged_segments)
        merged_segments = sorted(merged_segments, key=lambda x: x["start"])
        
        print(f"✅ Parallel transcription complete: {len(merged_segments)} segments")
        
        return {
            "text": " ".join(merged_text_parts),
            "segments": merged_segments,
            "language": "ru"
        }
    
    def _remove_overlap_duplicates(self, segments: List[Dict]) -> List[Dict]:
        """Удаление дублирующихся сегментов на границах overlap"""
        if not segments:
            return []
        
        sorted_segs = sorted(segments, key=lambda x: x["start"])
        unique = [sorted_segs[0]]
        
        for seg in sorted_segs[1:]:
            last = unique[-1]
            
            # Проверяем перекрытие
            overlap_start = max(last["start"], seg["start"])
            overlap_end = min(last["end"], seg["end"])
            overlap_duration = max(0, overlap_end - overlap_start)
            
            seg_duration = seg["end"] - seg["start"]
            
            if seg_duration > 0 and overlap_duration / seg_duration > 0.5:
                continue  # Дубликат
            
            if last["text"].strip().lower() == seg["text"].strip().lower():
                continue  # Одинаковый текст
            
            unique.append(seg)
        
        return unique


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
    global redis_client, whisper_pool, video_downloader
    
    # Startup
    print("🚀 Starting up...")
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    
    # Инициализируем универсальный загрузчик видео
    video_downloader = VideoDownloader(TEMP_DIR)
    print(f"📥 VideoDownloader initialized (supports: YouTube, VK, Rutube, OK.ru, Dailymotion, Vimeo)")
    
    # Инициализируем WhisperPool
    whisper_pool = WhisperPool(
        service_url=WHISPER_SERVICE_URL,
        pool_size=WHISPER_POOL_SIZE
    )
    print(f"📡 Whisper Pool: {WHISPER_SERVICE_URL} (initial pool_size={WHISPER_POOL_SIZE})")
    
    # Проверяем доступность и определяем реальное количество реплик
    if await whisper_pool.health_check():
        # Автоопределение количества реплик через DNS
        detected_size = await whisper_pool.detect_pool_size()
        print(f"✅ Whisper Pool is healthy! Detected {detected_size} replicas")
    else:
        print("⚠️ Whisper Pool not available yet (will retry on use)")
    
    # Инициализируем систему поиска похожих вопросов
    from similarity_search import initialize_similarity_search
    try:
        await initialize_similarity_search()
    except Exception as e:
        print(f"⚠️ Failed to initialize similarity search: {e}")
        import traceback
        traceback.print_exc()
    print("🔍 Similarity search initialized")
    
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
    global whisper_pool
    
    # Проверяем WhisperPool через Nginx и обновляем pool_size
    pool_healthy = False
    pool_size = 0
    if whisper_pool:
        pool_healthy = await whisper_pool.health_check()
        if pool_healthy:
            await whisper_pool.detect_pool_size()
        pool_size = whisper_pool.pool_size
    
    # Считаем temp файлы
    temp_files = list(TEMP_DIR.glob("*"))
    temp_size_mb = sum(f.stat().st_size for f in temp_files if f.is_file()) / (1024 * 1024)
    
    return {
        "status": "healthy",
        "whisper_pool": {
            "url": WHISPER_SERVICE_URL,
            "pool_size": pool_size,
            "is_healthy": pool_healthy
        },
        "parallel_processing": pool_size > 1,
        "temp_files_count": len(temp_files),
        "temp_size_mb": round(temp_size_mb, 2)
    }

@app.get("/favicon.ico", tags=["Status"])
async def favicon():
    """Favicon для браузера"""
    return {"message": "No favicon"}

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
        raise HTTPException(status_code=400, detail="Неподдерживаемая ссылка. Поддерживаются: YouTube, VK, Rutube, OK.ru, Dailymotion, Vimeo")
    
    # Определяем платформу
    platform = video_downloader.detect_platform(request.youtube_url) if video_downloader else 'youtube'
    
    # Сохраняем задачу в Redis
    task_data = {
        "task_id": task_id,
        "youtube_url": request.youtube_url,
        "platform": platform,
        "topic": request.topic,
        "level": request.level,
        "status": "pending",
        "progress": 0,
        "step": "В очереди..."
    }
    await redis_client.set(f"task:{task_id}", json.dumps(task_data), ex=REDIS_TTL)
    
    # Запускаем обработку в фоне
    background_tasks.add_task(trigger_n8n_workflow, task_id, request)
    
    return {"task_id": task_id, "status": "started", "platform": platform}

@app.post("/api/process-video/{client_id}", tags=["Processing"])
async def process_video_with_client(client_id: str, request: YouTubeRequest, background_tasks: BackgroundTasks):
    """Запуск обработки с привязкой к WebSocket клиенту"""
    task_id = str(uuid.uuid4())
    
    if not is_valid_youtube_url(request.youtube_url):
        raise HTTPException(status_code=400, detail="Неподдерживаемая ссылка. Поддерживаются: YouTube, VK, Rutube, OK.ru, Dailymotion, Vimeo")
    
    # Определяем платформу
    platform = video_downloader.detect_platform(request.youtube_url) if video_downloader else 'youtube'
    
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

@app.get("/api/questions", tags=["Public"])
async def get_all_questions(topic: Optional[str] = None, level: Optional[str] = None):
    """
    Получение всех одобренных вопросов с вероятностью для PublicSide
    
    - **topic**: Фильтр по теме (опционально)
    - **level**: Фильтр по уровню (опционально)
    """
    import asyncpg
    from fastapi.responses import JSONResponse
    
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        # Получить общее количество обработанных видео
        total_videos = await conn.fetchval("SELECT COUNT(*) FROM processed_videos")
        if total_videos == 0:
            return JSONResponse(content={"questions": []}, media_type="application/json; charset=utf-8")
        
        # Получить вопросы с источниками
        query = """
        SELECT 
            q.id, q.question, q.answer, q.topic, q.difficulty, q.probability, q.timecode,
            json_agg(json_build_object(
                'video_id', pv.id,
                'url', pv.youtube_url,
                'title', pv.title
            )) as sources
        FROM questions q
        LEFT JOIN question_video qv ON q.id = qv.question_id
        LEFT JOIN processed_videos pv ON qv.video_id = pv.id
        WHERE q.approved = TRUE
        """
        params = []
        if topic:
            query += " AND LOWER(q.topic) = LOWER($1)"
            params.append(topic)
        if level:
            query += " AND LOWER(q.difficulty) = LOWER($2)"
            params.append(level)
        
        query += " GROUP BY q.id, q.question, q.answer, q.topic, q.difficulty, q.probability, q.timecode"
        
        questions = await conn.fetch(query, *params)
        
        result = []
        for q in questions:
            sources_raw = q["sources"]
            if sources_raw and sources_raw != [None]:  # json_agg returns [null] for no matches
                try:
                    if isinstance(sources_raw, str):
                        sources = json.loads(sources_raw)
                    else:
                        sources = sources_raw
                    sources = [s for s in sources if s is not None]  # Filter out nulls
                except (json.JSONDecodeError, TypeError):
                    sources = []
            else:
                sources = []
            result.append({
                "id": q["id"],
                "question": q["question"],
                "answer": q["answer"],
                "topic": q["topic"],
                "difficulty": q["difficulty"],
                "probability": q["probability"],
                "timecode": q["timecode"],
                "approved": True,  # All questions are approved
                "sources": sources
            })
        
        return JSONResponse(content={"questions": result}, media_type="application/json; charset=utf-8")
    except Exception as e:
        import traceback
        print(f"Error in get_all_questions: {e}")
        traceback.print_exc()
        return JSONResponse(content={"error": str(e)}, status_code=500)
    finally:
        await conn.close()

@app.get("/api/questions/similar", tags=["Public"])
async def get_similar_questions(query: str, limit: int = 5):
    """
    Поиск похожих вопросов по тексту
    
    - **query**: Текст для поиска похожих вопросов
    - **limit**: Максимальное количество результатов (по умолчанию 5)
    """
    try:
        from similarity_search import initialize_similarity_search
        await initialize_similarity_search()  # Убедимся, что модель загружена
        similar_questions = await search_similar_questions(query, None, limit)
        return similar_questions
    except Exception as e:
        import traceback
        print(f"Error in get_similar_questions: {e}")
        traceback.print_exc()
        return {"error": str(e)}

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
    """Скачивание аудио и субтитров — универсальный загрузчик (YouTube, Rutube, VK, OK.ru и др.)"""
    import time
    global video_downloader
    
    try:
        # Определяем платформу
        platform = video_downloader.detect_platform(request.youtube_url) if video_downloader else 'youtube'
        video_id = video_downloader.extract_video_id(request.youtube_url, platform) if video_downloader else extract_video_id(request.youtube_url)
        
        audio_path = TEMP_DIR / f"{video_id}.mp3"
        
        # Используем универсальный загрузчик для всех платформ
        if video_downloader and platform != 'youtube':
            # Для не-YouTube используем VideoDownloader напрямую
            print(f"📥 Using universal downloader for {platform}...")
            result = await video_downloader.download_video_audio(request.youtube_url, video_id)
            
            title = result.get('video_title', 'Unknown')
            subtitles = result.get('subtitles', [])
            duration = result.get('duration', 0)
            
            # Конвертируем формат субтитров если нужно (VideoDownloader может вернуть строковые времена)
            converted_subs = []
            for sub in subtitles:
                start = sub.get('start', 0)
                end = sub.get('end', 0)
                # Если start/end — строки вида "00:01:23.456", конвертируем в секунды
                if isinstance(start, str):
                    start = _parse_time_str(start)
                if isinstance(end, str):
                    end = _parse_time_str(end)
                converted_subs.append({
                    'start': round(float(start), 1),
                    'end': round(float(end), 1),
                    'text': sub.get('text', '')
                })
            subtitles = converted_subs
            
            # Сохраняем platform в Redis
            await redis_client.set(f"platform:{request.task_id}", platform, ex=REDIS_TTL)
            await redis_client.set(f"video_id:{request.task_id}", video_id, ex=REDIS_TTL)
            
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
                "platform": platform,
                "has_subtitles": len(subtitles) > 0,
                "subtitles_count": len(subtitles),
                "duration": duration
            }
        
        # ===== YouTube — оригинальная логика с ретраями субтитров =====
        subtitles = []
        max_retries = 5
        retry_delay = 3

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
    Параллельная транскрибация аудио через Nginx-балансируемый Whisper Pool.
    
    Архитектура:
    1. Определить длительность аудио
    2. Разрезать на N частей (N = WHISPER_POOL_SIZE)
    3. Отправить части параллельно через Nginx (least_conn балансировка)
    4. Объединить результаты с учётом overlap
    5. Слить с YouTube субтитрами (если есть)
    """
    global whisper_pool
    import subprocess
    
    try:
        audio_path = Path(request.audio_path)
        
        # 1. Определяем длительность аудио через ffprobe
        duration = await get_audio_duration(audio_path)
        print(f"🎵 Audio duration: {duration:.1f} seconds ({duration/60:.1f} minutes)")
        
        # 2. Проверяем доступность WhisperPool и обновляем pool_size
        if not whisper_pool:
            raise HTTPException(status_code=503, detail="WhisperPool not initialized")
        
        pool_healthy = await whisper_pool.health_check()
        if not pool_healthy:
            raise HTTPException(status_code=503, detail="Whisper Pool not available")
        
        # Автоопределение количества реплик (на случай scale up/down)
        await whisper_pool.detect_pool_size()
        
        print(f"🖥️ Whisper Pool: {whisper_pool.pool_size} workers via Nginx")
        
        # 3. Транскрибация через WhisperPool
        # Параллелим если видео > MIN_CHUNK_DURATION на воркер И pool_size > 1
        min_parallel_duration = MIN_CHUNK_DURATION * whisper_pool.pool_size
        use_parallel = whisper_pool.pool_size > 1 and duration >= min_parallel_duration
        
        if use_parallel:
            print(f"⚡ Using PARALLEL transcription with {whisper_pool.pool_size} workers")
            whisper_result = await whisper_pool.transcribe_parallel(audio_path, duration, request.task_id)
        else:
            print(f"📝 Using single Whisper request (duration < {min_parallel_duration}s or single worker)")
            whisper_result = await whisper_pool.transcribe(audio_path)
        
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
                "parallel_processing": use_parallel,
                "pool_size": whisper_pool.pool_size
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
            "parallel_processing_used": use_parallel
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
    """Сохранение вопросов в БД"""
    import asyncpg
    from similarity_search import invalidate_similarity_cache
    
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        # Найти или создать видео
        video_id = await conn.fetchval("""
            INSERT INTO processed_videos (youtube_url, video_id, title, transcript, questions_count)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (youtube_url) DO UPDATE SET
                questions_count = EXCLUDED.questions_count
            RETURNING id
        """, request.youtube_url, request.youtube_url.split('v=')[-1][:11], request.video_title, "", len(request.questions))
        
        # Сохранить вопросы с дедупликацией
        question_ids = []
        for q in request.questions:
            # Проверить, существует ли уже такой вопрос из этого видео
            existing_question = await conn.fetchval("""
                SELECT q.id FROM questions q
                JOIN question_video qv ON q.id = qv.question_id
                WHERE q.question = $1 AND q.timecode = $2 AND qv.video_id = $3
                LIMIT 1
            """, q["question"], q.get("timecode", ""), video_id)
            
            if existing_question:
                # Вопрос уже существует, пропускаем
                question_ids.append(existing_question)
                continue
            
            # Вопрос новый, вставляем
            q_id = await conn.fetchval("""
                INSERT INTO questions (question, answer, topic, difficulty, source_url, video_title, timecode, approved)
                VALUES ($1, $2, $3, $4, $5, $6, $7, FALSE)
                RETURNING id
            """, q["question"], q.get("answer", ""), q.get("topic", ""), q.get("difficulty", ""), request.youtube_url, request.video_title, q.get("timecode", ""))
            question_ids.append(q_id)
            
            # Создать связь вопрос-видео
            await conn.execute("""
                INSERT INTO question_video (question_id, video_id)
                VALUES ($1, $2)
                ON CONFLICT DO NOTHING
            """, q_id, video_id)
        
        # Обновить вероятности
        await update_probabilities(conn)
        
        # Сохраняем в Redis для совместимости
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
        
        # Инвалидируем кэш поиска похожих вопросов
        await invalidate_similarity_cache()
        
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
    """Проверка валидности URL видео (YouTube, VK, Rutube, OK.ru, Dailymotion, Vimeo)"""
    global video_downloader
    if video_downloader:
        return video_downloader.is_valid_url(url)
    # Fallback — базовые паттерны
    patterns = [
        r'(https?://)?(www\.)?youtube\.com/watch\?v=[\w-]+',
        r'(https?://)?(www\.)?youtu\.be/[\w-]+',
        r'(https?://)?(www\.)?youtube\.com/shorts/[\w-]+',
        r'(https?://)?(www\.)?rutube\.ru/video/',
        r'(https?://)?(www\.)?(vk\.com|vkvideo\.ru)/video',
        r'(https?://)?(www\.)?ok\.ru/video/',
        r'(https?://)?(www\.)?dailymotion\.com/video/',
        r'(https?://)?(www\.)?vimeo\.com/\d+',
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

def _parse_time_str(time_str: str) -> float:
    """Конвертация строки времени VTT '00:01:23.456' -> секунды"""
    try:
        # Убираем лишние пробелы и атрибуты
        time_str = time_str.strip().split()[0]
        parts = time_str.split(':')
        if len(parts) == 3:
            h, m, s = parts
            return int(h) * 3600 + int(m) * 60 + float(s)
        elif len(parts) == 2:
            m, s = parts
            return int(m) * 60 + float(s)
        return float(time_str)
    except Exception:
        return 0.0

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
        
        # Нормализуем уровень сложности
        difficulty = q.get('difficulty', '').lower().strip()
        if difficulty in ['easy', 'beginner', 'новичок', 'джуниор']:
            q['difficulty'] = 'junior'
        elif difficulty in ['medium', 'intermediate', 'middle', 'средний', 'миддл']:
            q['difficulty'] = 'middle'
        elif difficulty in ['hard', 'advanced', 'expert', 'senior', 'сложный', 'сеньор']:
            q['difficulty'] = 'senior'
        else:
            # Если уровень не распознан, ставим middle по умолчанию
            q['difficulty'] = 'middle'
        
        # Проверяем только на ТОЧНЫЕ дубликаты (вся строка целиком)
        if normalized not in seen_questions:
            seen_questions.add(normalized)
            unique_questions.append(q)
    
    return unique_questions

# ============== Admin Panel Endpoints ==============

@app.get("/api/admin/questions", tags=["Admin"])
async def get_admin_questions():
    """Получить все вопросы для админа (одобренные и не одобренные)"""
    import asyncpg
    
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        questions = await conn.fetch("""
            SELECT id, question, answer, topic, difficulty, probability, timecode, approved, source_url, video_title, created_at
            FROM questions
            ORDER BY created_at DESC
        """)
        result = []
        for q in questions:
            # Получить похожие вопросы среди одобренных (без учета самого себя)
            try:
                similar = await search_similar_questions(q["question"], q["id"], limit=1000)
                # Фильтровать по порогу similarity_score > 0.7 и взять топ-5
                filtered_similar = [s for s in similar if s['similarity_score'] > 0.7]
                top_similar = sorted(filtered_similar, key=lambda x: x['similarity_score'], reverse=True)[:5]
                similar_count = len(top_similar)
            except Exception as e:
                print(f"⚠️ Failed to get similar questions for {q['id']}: {e}")
                similar_count = 0
            result.append({
                "id": q["id"],
                "question": q["question"],
                "answer": q["answer"],
                "topic": q["topic"],
                "difficulty": q["difficulty"],
                "probability": q["probability"],
                "timecode": q["timecode"],
                "approved": q["approved"],
                "source_url": q["source_url"],
                "video_title": q["video_title"],
                "created_at": q["created_at"],
                "similar_count": similar_count
            })
        
        return {"questions": result}
    finally:
        await conn.close()

@app.post("/api/admin/questions", tags=["Admin"])
async def create_question(data: dict = Body(...)):
    """Создать новый вопрос"""
    import asyncpg
    from similarity_search import invalidate_similarity_cache
    
    question = data.get("question")
    answer = data.get("answer")
    topic = data.get("topic", "General")
    difficulty = data.get("difficulty", "middle")
    timecode = data.get("timecode")
    
    if not question:
        raise HTTPException(status_code=400, detail="Question is required")
    
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        question_id = await conn.fetchval("""
            INSERT INTO questions (question, answer, topic, difficulty, timecode, approved)
            VALUES ($1, $2, $3, $4, $5, TRUE)
            RETURNING id
        """, question, answer, topic, difficulty, timecode)
        
        # Обновить вероятности
        await update_probabilities(conn)
        
        # Инвалидируем кэш поиска похожих вопросов
        await invalidate_similarity_cache()
        
        return {"id": question_id, "message": "Question created"}
    finally:
        await conn.close()

@app.delete("/api/admin/questions/{question_id}", tags=["Admin"])
async def delete_question(question_id: int):
    """Удалить вопрос"""
    import asyncpg
    from similarity_search import invalidate_similarity_cache
    
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        await conn.execute("DELETE FROM questions WHERE id = $1", question_id)
        
        # Обновить вероятности
        await update_probabilities(conn)
        
        # Инвалидируем кэш поиска похожих вопросов
        await invalidate_similarity_cache()
        
        return {"message": "Question deleted"}
    finally:
        await conn.close()

@app.post("/api/admin/approve-questions", tags=["Admin"])
async def approve_questions(data: Dict[str, List[int]]):
    """Одобрить вопросы - дедупликация через кнопку 'Похожих'"""
    question_ids = data.get("question_ids", [])
    import asyncpg
    from similarity_search import invalidate_similarity_cache

    conn = await asyncpg.connect(DATABASE_URL)
    try:
        approved_count = 0

        for question_id in question_ids:
            # Проверить, что вопрос существует и не одобрен
            question_exists = await conn.fetchval("SELECT 1 FROM questions WHERE id = $1 AND approved = FALSE", question_id)
            if question_exists:
                await conn.execute("UPDATE questions SET approved = TRUE WHERE id = $1", question_id)
                approved_count += 1

        # Обновить вероятности для всех вопросов
        await update_probabilities(conn)

        # Инвалидируем кэш поиска похожих вопросов
        await invalidate_similarity_cache()

        return {
            "message": f"Одобрено {approved_count} вопросов",
            "approved_count": approved_count
        }
    finally:
        await conn.close()

@app.get("/api/admin/similar-questions/{question_id}", tags=["Admin"])
async def get_similar_questions(question_id: int):
    """Найти похожие вопросы для замены с использованием семантического поиска"""
    import asyncpg
    from similarity_search import get_similar_questions
    from fastapi.responses import JSONResponse

    conn = await asyncpg.connect(DATABASE_URL)
    try:
        # Получить текущий вопрос
        current_question = await conn.fetchval("SELECT question FROM questions WHERE id = $1", question_id)
        if not current_question:
            raise HTTPException(status_code=404, detail="Question not found")

        # Используем семантический поиск
        similar_questions = await get_similar_questions(current_question, question_id, limit=1000)
        # Фильтровать по порогу similarity_score > 0.7 и взять топ-5
        filtered_similar = [s for s in similar_questions if s['similarity_score'] > 0.7]
        top_similar = sorted(filtered_similar, key=lambda x: x['similarity_score'], reverse=True)[:5]

        return JSONResponse(content={"similar_questions": top_similar}, media_type="application/json; charset=utf-8")
    finally:
        await conn.close()

@app.put("/api/admin/replace-question/{question_id}", tags=["Admin"])
async def replace_question(question_id: int, data: dict):
    """Заменить вопрос на похожий - перенести связи и увеличить использование"""
    import asyncpg
    from similarity_search import invalidate_similarity_cache

    new_question_id = data.get("similar_question_id")
    if not new_question_id:
        raise HTTPException(status_code=400, detail="similar_question_id required")

    conn = await asyncpg.connect(DATABASE_URL)
    try:
        # Проверить, что новый вопрос существует и одобрен
        new_question_exists = await conn.fetchval("SELECT 1 FROM questions WHERE id = $1 AND approved = TRUE", new_question_id)
        if not new_question_exists:
            raise HTTPException(status_code=404, detail="New question not found or not approved")

        # Перенести видео-связи от старого вопроса к новому
        duplicate_links = await conn.fetch("SELECT video_id FROM question_video WHERE question_id = $1", question_id)

        for link in duplicate_links:
            # Проверить, существует ли уже такая связь для нового вопроса
            existing_link = await conn.fetchval("SELECT 1 FROM question_video WHERE question_id = $1 AND video_id = $2",
                                               new_question_id, link['video_id'])
            if not existing_link:
                # Добавить связь, если её нет
                await conn.execute("INSERT INTO question_video (question_id, video_id) VALUES ($1, $2)",
                                 new_question_id, link['video_id'])

        # Удалить старые связи
        await conn.execute("DELETE FROM question_video WHERE question_id = $1", question_id)

        # Удалить старый вопрос
        await conn.execute("DELETE FROM questions WHERE id = $1", question_id)

        # Обновить вероятности для всех вопросов
        await update_probabilities(conn)

        # Инвалидируем кэш поиска похожих вопросов
        await invalidate_similarity_cache()

        return {"message": "Question replaced successfully"}
    finally:
        await conn.close()

@app.post("/api/admin/recalculate-probabilities", tags=["Admin"])
async def recalculate_probabilities():
    """Пересчитать вероятности для всех вопросов (админ функция)"""
    import asyncpg
    from similarity_search import invalidate_similarity_cache

    conn = await asyncpg.connect(DATABASE_URL)
    try:
        await update_probabilities(conn)
        await invalidate_similarity_cache()
        return {"message": "Probabilities recalculated"}
    finally:
        await conn.close()


async def update_probabilities(conn):
    """Обновить вероятности для всех вопросов - процент от общего количества видео"""
    
    # Получить общее количество обработанных видео
    total_videos = await conn.fetchval("SELECT COUNT(*) FROM processed_videos")
    
    if total_videos > 0:
        # Обновить вероятности - процент видео, где встречается вопрос (только если вопрос в 2+ видео)
        await conn.execute("""
            UPDATE questions 
            SET probability = CASE 
                WHEN (
                    SELECT COUNT(DISTINCT qv.video_id)
                    FROM question_video qv
                    WHERE qv.question_id = questions.id
                ) >= 2 THEN (
                    SELECT (COUNT(DISTINCT qv.video_id) * 100.0 / $1)
                    FROM question_video qv
                    WHERE qv.question_id = questions.id
                )
                ELSE 0.0  -- Не показывать вероятность если вопрос только в 1 видео
            END
            WHERE approved = TRUE
        """, total_videos)

async def trigger_n8n_workflow(task_id: str, request: YouTubeRequest):
    """Запуск n8n workflow"""
    print(f"🚀 Starting n8n workflow for task {task_id}")
    try:
        async with httpx.AsyncClient(timeout=1800.0) as client:  # 30 мин для длинных видео
            print(f"📡 Sending request to n8n: {N8N_WEBHOOK_URL}")
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
            if response.status_code != 200:
                print(f"n8n response body: {response.text}")
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


# ============== Все задачи (для фронтенда) ==============
@app.get("/api/all-tasks", tags=["Status"])
async def get_all_tasks():
    """Получение всех задач из Redis"""
    try:
        tasks = []
        # Сканируем все ключи задач
        cursor = 0
        while True:
            cursor, keys = await redis_client.scan(cursor, match="task:*", count=100)
            for key in keys:
                # Пропускаем служебные ключи
                if ':client' in key or ':tasks' in key:
                    continue
                task_data = await redis_client.get(key)
                if task_data:
                    try:
                        task = json.loads(task_data)
                        if 'task_id' in task:
                            tasks.append(task)
                    except json.JSONDecodeError:
                        pass
            if cursor == 0:
                break
        
        # Сортируем по времени создания (новые первые)
        tasks.sort(key=lambda t: t.get('created_at', ''), reverse=True)
        return {"tasks": tasks}
    except Exception as e:
        return {"tasks": [], "error": str(e)}


# ============== Отзыв одобрения вопросов ==============
@app.post("/api/admin/revoke-questions", tags=["Admin"])
async def revoke_questions(data: Dict[str, List[int]]):
    """Отозвать одобрение вопросов"""
    question_ids = data.get("question_ids", [])
    import asyncpg
    from similarity_search import invalidate_similarity_cache

    conn = await asyncpg.connect(DATABASE_URL)
    try:
        revoked_count = 0
        for question_id in question_ids:
            result = await conn.execute("UPDATE questions SET approved = FALSE WHERE id = $1 AND approved = TRUE", question_id)
            if result == "UPDATE 1":
                revoked_count += 1

        await update_probabilities(conn)
        await invalidate_similarity_cache()

        return {"message": f"Отозвано {revoked_count} вопросов", "revoked_count": revoked_count}
    finally:
        await conn.close()


# ============== Получение деталей вопроса ==============
@app.get("/api/questions/{question_id}", tags=["Public"])
async def get_public_question_detail(question_id: int):
    """Полная информация о вопросе для публичной части"""
    import asyncpg
    from fastapi.responses import JSONResponse

    conn = await asyncpg.connect(DATABASE_URL)
    try:
        q = await conn.fetchrow("""
            SELECT q.id, q.question, q.answer, q.topic, q.difficulty, q.probability, q.timecode,
                   q.source_url, q.video_title, q.created_at
            FROM questions q
            WHERE q.id = $1 AND q.approved = TRUE
        """, question_id)

        if not q:
            raise HTTPException(status_code=404, detail="Вопрос не найден")

        # Получаем видео-источники
        sources = await conn.fetch("""
            SELECT pv.id, pv.youtube_url as url, pv.title, pv.platform
            FROM question_video qv
            JOIN processed_videos pv ON qv.video_id = pv.id
            WHERE qv.question_id = $1
        """, question_id)

        # Получаем теги
        tags = await conn.fetch("SELECT tag FROM question_tags WHERE question_id = $1", question_id)

        # Записываем просмотр
        try:
            await conn.execute(
                "INSERT INTO question_views (question_id) VALUES ($1)", question_id
            )
        except Exception:
            pass  # Таблица может не существовать

        result = {
            "id": q["id"],
            "question": q["question"],
            "answer": q["answer"],
            "topic": q["topic"],
            "difficulty": q["difficulty"],
            "probability": q["probability"],
            "timecode": q["timecode"],
            "source_url": q["source_url"],
            "video_title": q["video_title"],
            "created_at": str(q["created_at"]) if q["created_at"] else None,
            "sources": [dict(s) for s in sources],
            "tags": [t["tag"] for t in tags]
        }

        return JSONResponse(content=result, media_type="application/json; charset=utf-8")
    finally:
        await conn.close()


# ============== Детали вопроса для админа ==============
@app.get("/api/admin/questions/{question_id}", tags=["Admin"])
async def get_admin_question_detail(question_id: int):
    """Полная информация о вопросе для админа"""
    import asyncpg
    from fastapi.responses import JSONResponse

    conn = await asyncpg.connect(DATABASE_URL)
    try:
        q = await conn.fetchrow("""
            SELECT * FROM questions WHERE id = $1
        """, question_id)

        if not q:
            raise HTTPException(status_code=404, detail="Вопрос не найден")

        sources = await conn.fetch("""
            SELECT pv.id, pv.youtube_url as url, pv.title, pv.platform
            FROM question_video qv JOIN processed_videos pv ON qv.video_id = pv.id
            WHERE qv.question_id = $1
        """, question_id)

        tags = await conn.fetch("SELECT tag FROM question_tags WHERE question_id = $1", question_id)

        # Количество просмотров
        views_count = 0
        try:
            views_count = await conn.fetchval("SELECT COUNT(*) FROM question_views WHERE question_id = $1", question_id)
        except Exception:
            pass

        # Обратная связь
        feedbacks = []
        try:
            feedbacks_raw = await conn.fetch(
                "SELECT * FROM feedback WHERE question_id = $1 ORDER BY created_at DESC LIMIT 10", question_id
            )
            feedbacks = [dict(f) for f in feedbacks_raw]
        except Exception:
            pass

        result = dict(q)
        result["sources"] = [dict(s) for s in sources]
        result["tags"] = [t["tag"] for t in tags]
        result["views_count"] = views_count
        result["feedbacks"] = feedbacks
        # Convert datetime objects to strings
        for key in result:
            if hasattr(result[key], 'isoformat'):
                result[key] = result[key].isoformat()

        return JSONResponse(content=result, media_type="application/json; charset=utf-8")
    finally:
        await conn.close()


# ============== Объединение вопросов ==============
@app.post("/api/admin/questions/merge", tags=["Admin"])
async def merge_questions(data: dict = Body(...)):
    """Объединить два вопроса (перенести связи с source_id на target_id, удалить source)"""
    import asyncpg
    from similarity_search import invalidate_similarity_cache

    source_id = data.get("source_id")
    target_id = data.get("target_id")
    if not source_id or not target_id:
        raise HTTPException(status_code=400, detail="source_id and target_id required")

    conn = await asyncpg.connect(DATABASE_URL)
    try:
        # Перенести видео-связи
        links = await conn.fetch("SELECT video_id FROM question_video WHERE question_id = $1", source_id)
        for link in links:
            await conn.execute("""
                INSERT INTO question_video (question_id, video_id) VALUES ($1, $2)
                ON CONFLICT DO NOTHING
            """, target_id, link['video_id'])

        # Удалить связи и сам исходный вопрос
        await conn.execute("DELETE FROM question_video WHERE question_id = $1", source_id)
        await conn.execute("DELETE FROM questions WHERE id = $1", source_id)

        await update_probabilities(conn)
        await invalidate_similarity_cache()

        return {"message": "Вопросы объединены", "kept_id": target_id, "deleted_id": source_id}
    finally:
        await conn.close()


# ============== Генерация ответа через LLM ==============
@app.post("/api/admin/generate-answer/{question_id}", tags=["Admin"])
async def generate_answer(question_id: int):
    """Генерация ответа на вопрос с помощью LLM"""
    import asyncpg

    conn = await asyncpg.connect(DATABASE_URL)
    try:
        q = await conn.fetchrow("SELECT id, question, topic, difficulty FROM questions WHERE id = $1", question_id)
        if not q:
            raise HTTPException(status_code=404, detail="Вопрос не найден")

        prompt = f"""Ты опытный IT-специалист, который готовит кандидатов к собеседованиям.

Дай подробный, структурированный ответ на вопрос для IT-собеседования.

Тема: {q['topic']}
Уровень: {q['difficulty']}
Вопрос: {q['question']}

Требования к ответу:
1. Ответ должен быть на русском языке
2. Начни с краткого определения (1-2 предложения)
3. Раскрой тему подробнее (2-4 абзаца)
4. Приведи пример кода, если это уместно (используй Markdown)
5. Упомяни практическое применение
6. Если есть подводные камни или edge cases, укажи их
7. Формат: Markdown

Ответ:"""

        # Генерируем ответ через LLM
        try:
            result = await call_llm_for_answer(prompt)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Ошибка LLM: {str(e)}")

        # Сохраняем ответ в БД
        await conn.execute(
            "UPDATE questions SET answer = $1, updated_at = CURRENT_TIMESTAMP WHERE id = $2",
            result, question_id
        )

        return {"answer": result, "question_id": question_id}
    finally:
        await conn.close()


async def call_llm_for_answer(prompt: str) -> str:
    """Получить текстовый ответ от LLM (не JSON)"""
    provider = LLM_PROVIDER.lower()
    if provider == "auto":
        if OPENROUTER_API_KEY:
            provider = "openrouter"
        elif GROQ_API_KEY:
            provider = "groq"
        elif GEMINI_API_KEY:
            provider = "gemini"
        else:
            provider = "ollama"

    if provider == "openrouter":
        async with httpx.AsyncClient(timeout=180.0) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "mistralai/devstral-2512:free",
                    "messages": [
                        {"role": "system", "content": "Ты опытный IT-специалист. Отвечай подробно, структурированно, на русском языке."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.4,
                    "max_tokens": 4000
                }
            )
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
    
    if provider == "groq" or (provider == "openrouter" and GROQ_API_KEY):
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [
                        {"role": "system", "content": "Ты опытный IT-специалист. Отвечай подробно, структурированно, на русском языке."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.4,
                    "max_tokens": 4000
                }
            )
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
    
    if provider == "gemini" or GEMINI_API_KEY:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}",
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"temperature": 0.4, "maxOutputTokens": 4000}
                }
            )
            if response.status_code == 200:
                return response.json()["candidates"][0]["content"]["parts"][0]["text"]
    
    raise Exception("Нет доступного LLM провайдера для генерации ответа")


# ============== Массовая генерация ответов ==============
@app.post("/api/admin/generate-answers-bulk", tags=["Admin"])
async def generate_answers_bulk(data: dict = Body(...)):
    """Массовая генерация ответов для вопросов без ответов"""
    import asyncpg
    question_ids = data.get("question_ids", [])
    max_count = data.get("max_count", 10)  # Ограничение

    conn = await asyncpg.connect(DATABASE_URL)
    try:
        if not question_ids:
            # Генерируем для всех вопросов без ответов
            rows = await conn.fetch(
                "SELECT id FROM questions WHERE (answer IS NULL OR answer = '') AND approved = TRUE LIMIT $1",
                max_count
            )
            question_ids = [r["id"] for r in rows]

        generated = 0
        errors = 0
        for qid in question_ids[:max_count]:
            try:
                await generate_answer(qid)
                generated += 1
                await asyncio.sleep(1)  # Пауза между запросами
            except Exception as e:
                print(f"⚠️ Error generating answer for {qid}: {e}")
                errors += 1

        return {"generated": generated, "errors": errors, "total": len(question_ids)}
    finally:
        await conn.close()


# ============== Предложения видео ==============
@app.post("/api/suggestions", tags=["Public"])
async def create_suggestion(data: dict = Body(...)):
    """Пользователь предлагает видео для обработки"""
    import asyncpg

    url = data.get("url", "").strip()
    if not url:
        raise HTTPException(status_code=400, detail="URL обязателен")

    # Определяем платформу
    platform = video_downloader.detect_platform(url) if video_downloader else 'unknown'

    conn = await asyncpg.connect(DATABASE_URL)
    try:
        suggestion_id = await conn.fetchval("""
            INSERT INTO video_suggestions (url, platform, topic, difficulty, comment, user_name, user_email)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING id
        """, url, platform,
            data.get("topic", "General"),
            data.get("difficulty", "middle"),
            data.get("comment", ""),
            data.get("user_name", ""),
            data.get("user_email", ""))

        return {"id": suggestion_id, "message": "Спасибо! Ваше предложение отправлено на рассмотрение."}
    finally:
        await conn.close()


@app.get("/api/suggestions", tags=["Public"])
async def get_suggestions(status: Optional[str] = None):
    """Список предложений видео (для публичной части — только одобренные)"""
    import asyncpg
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        if status:
            suggestions = await conn.fetch(
                "SELECT * FROM video_suggestions WHERE status = $1 ORDER BY created_at DESC", status)
        else:
            suggestions = await conn.fetch(
                "SELECT * FROM video_suggestions ORDER BY created_at DESC LIMIT 50")
        
        result = []
        for s in suggestions:
            row = dict(s)
            for key in row:
                if hasattr(row[key], 'isoformat'):
                    row[key] = row[key].isoformat()
            result.append(row)
        return {"suggestions": result}
    finally:
        await conn.close()


@app.get("/api/admin/suggestions", tags=["Admin"])
async def get_admin_suggestions():
    """Все предложения видео для админа"""
    import asyncpg
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        suggestions = await conn.fetch("SELECT * FROM video_suggestions ORDER BY created_at DESC")
        result = []
        for s in suggestions:
            row = dict(s)
            for key in row:
                if hasattr(row[key], 'isoformat'):
                    row[key] = row[key].isoformat()
            result.append(row)
        return {"suggestions": result}
    finally:
        await conn.close()


@app.put("/api/admin/suggestions/{suggestion_id}", tags=["Admin"])
async def update_suggestion(suggestion_id: int, data: dict = Body(...)):
    """Обновить статус предложения (approve, reject, processing)"""
    import asyncpg
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        status = data.get("status", "pending")
        admin_comment = data.get("admin_comment", "")
        await conn.execute(
            "UPDATE video_suggestions SET status = $1, admin_comment = $2 WHERE id = $3",
            status, admin_comment, suggestion_id)
        return {"message": "Предложение обновлено"}
    finally:
        await conn.close()


@app.post("/api/admin/suggestions/{suggestion_id}/process", tags=["Admin"])
async def process_suggestion(suggestion_id: int, background_tasks: BackgroundTasks):
    """Обработать предложенное видео (запустить pipeline)"""
    import asyncpg
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        suggestion = await conn.fetchrow("SELECT * FROM video_suggestions WHERE id = $1", suggestion_id)
        if not suggestion:
            raise HTTPException(status_code=404, detail="Предложение не найдено")

        # Обновляем статус
        await conn.execute("UPDATE video_suggestions SET status = 'processing' WHERE id = $1", suggestion_id)

        # Запускаем обработку
        task_id = str(uuid.uuid4())
        request = YouTubeRequest(
            youtube_url=suggestion["url"],
            topic=suggestion.get("topic", "General"),
            level=suggestion.get("difficulty", "middle")
        )

        task_data = {
            "task_id": task_id,
            "youtube_url": suggestion["url"],
            "topic": suggestion.get("topic", "General"),
            "level": suggestion.get("difficulty", "middle"),
            "status": "pending",
            "progress": 0,
            "step": "Обработка предложенного видео...",
            "suggestion_id": suggestion_id
        }
        await redis_client.set(f"task:{task_id}", json.dumps(task_data), ex=REDIS_TTL)

        background_tasks.add_task(trigger_n8n_workflow, task_id, request)

        return {"task_id": task_id, "message": "Видео отправлено на обработку"}
    finally:
        await conn.close()


# ============== Обратная связь ==============
@app.post("/api/feedback", tags=["Public"])
async def create_feedback(data: dict = Body(...)):
    """Оставить обратную связь"""
    import asyncpg
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        feedback_id = await conn.fetchval("""
            INSERT INTO feedback (question_id, feedback_type, rating, comment, user_name, user_email, user_session)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING id
        """,
            data.get("question_id"),
            data.get("feedback_type", "suggestion"),
            data.get("rating"),
            data.get("comment", ""),
            data.get("user_name", ""),
            data.get("user_email", ""),
            data.get("user_session", ""))

        return {"id": feedback_id, "message": "Спасибо за обратную связь!"}
    finally:
        await conn.close()


@app.get("/api/admin/feedback", tags=["Admin"])
async def get_admin_feedback(is_resolved: Optional[bool] = None):
    """Вся обратная связь для админа"""
    import asyncpg
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        if is_resolved is not None:
            feedbacks = await conn.fetch(
                "SELECT f.*, q.question as question_text FROM feedback f LEFT JOIN questions q ON f.question_id = q.id WHERE f.is_resolved = $1 ORDER BY f.created_at DESC",
                is_resolved)
        else:
            feedbacks = await conn.fetch(
                "SELECT f.*, q.question as question_text FROM feedback f LEFT JOIN questions q ON f.question_id = q.id ORDER BY f.created_at DESC LIMIT 100")

        result = []
        for f in feedbacks:
            row = dict(f)
            for key in row:
                if hasattr(row[key], 'isoformat'):
                    row[key] = row[key].isoformat()
            result.append(row)
        return {"feedbacks": result}
    finally:
        await conn.close()


@app.put("/api/admin/feedback/{feedback_id}", tags=["Admin"])
async def resolve_feedback(feedback_id: int, data: dict = Body(...)):
    """Разрешить/ответить на обратную связь"""
    import asyncpg
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        await conn.execute(
            "UPDATE feedback SET is_resolved = $1, admin_response = $2 WHERE id = $3",
            data.get("is_resolved", True),
            data.get("admin_response", ""),
            feedback_id)
        return {"message": "Обратная связь обновлена"}
    finally:
        await conn.close()


# ============== Закладки (избранное) ==============
@app.post("/api/bookmarks", tags=["Public"])
async def toggle_bookmark(data: dict = Body(...)):
    """Добавить/удалить вопрос из закладок"""
    import asyncpg
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        question_id = data.get("question_id")
        user_session = data.get("user_session", "")
        if not question_id or not user_session:
            raise HTTPException(status_code=400, detail="question_id и user_session обязательны")

        # Проверяем, есть ли уже закладка
        existing = await conn.fetchval(
            "SELECT id FROM bookmarks WHERE question_id = $1 AND user_session = $2",
            question_id, user_session)

        if existing:
            # Удаляем
            await conn.execute("DELETE FROM bookmarks WHERE id = $1", existing)
            return {"bookmarked": False, "message": "Закладка удалена"}
        else:
            # Добавляем
            await conn.execute(
                "INSERT INTO bookmarks (question_id, user_session, note) VALUES ($1, $2, $3)",
                question_id, user_session, data.get("note", ""))
            return {"bookmarked": True, "message": "Добавлено в закладки"}
    finally:
        await conn.close()


@app.get("/api/bookmarks/{user_session}", tags=["Public"])
async def get_bookmarks(user_session: str):
    """Получить закладки пользователя"""
    import asyncpg
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        bookmarks = await conn.fetch("""
            SELECT b.id, b.note, b.created_at,
                   q.id as question_id, q.question, q.answer, q.topic, q.difficulty, q.probability
            FROM bookmarks b
            JOIN questions q ON b.question_id = q.id
            WHERE b.user_session = $1
            ORDER BY b.created_at DESC
        """, user_session)

        result = []
        for b in bookmarks:
            row = dict(b)
            for key in row:
                if hasattr(row[key], 'isoformat'):
                    row[key] = row[key].isoformat()
            result.append(row)
        return {"bookmarks": result}
    finally:
        await conn.close()


# ============== Заметки пользователя ==============
@app.put("/api/notes/{question_id}", tags=["Public"])
async def save_note(question_id: int, data: dict = Body(...)):
    """Сохранить заметку пользователя к вопросу"""
    import asyncpg
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        user_session = data.get("user_session", "")
        note = data.get("note", "")
        if not user_session:
            raise HTTPException(status_code=400, detail="user_session обязателен")

        await conn.execute("""
            INSERT INTO user_notes (question_id, user_session, note)
            VALUES ($1, $2, $3)
            ON CONFLICT (question_id, user_session) DO UPDATE SET note = $3, updated_at = CURRENT_TIMESTAMP
        """, question_id, user_session, note)
        return {"message": "Заметка сохранена"}
    finally:
        await conn.close()


@app.get("/api/notes/{user_session}", tags=["Public"])
async def get_notes(user_session: str):
    """Получить все заметки пользователя"""
    import asyncpg
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        notes = await conn.fetch("""
            SELECT n.*, q.question, q.topic
            FROM user_notes n
            JOIN questions q ON n.question_id = q.id
            WHERE n.user_session = $1
            ORDER BY n.updated_at DESC
        """, user_session)
        result = []
        for n in notes:
            row = dict(n)
            for key in row:
                if hasattr(row[key], 'isoformat'):
                    row[key] = row[key].isoformat()
            result.append(row)
        return {"notes": result}
    finally:
        await conn.close()


# ============== Мок-интервью ==============
@app.post("/api/mock-interview/start", tags=["Public"])
async def start_mock_interview(data: dict = Body(...)):
    """Начать мок-интервью — получить случайные вопросы"""
    import asyncpg
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        topic = data.get("topic", "")
        difficulty = data.get("difficulty", "")
        count = min(data.get("count", 10), 30)
        user_session = data.get("user_session", "")

        query = "SELECT id, question, answer, topic, difficulty, probability FROM questions WHERE approved = TRUE"
        params = []
        param_count = 0

        if topic:
            param_count += 1
            query += f" AND LOWER(topic) = LOWER(${param_count})"
            params.append(topic)
        if difficulty:
            param_count += 1
            query += f" AND LOWER(difficulty) = LOWER(${param_count})"
            params.append(difficulty)

        query += " ORDER BY RANDOM()"
        param_count += 1
        query += f" LIMIT ${param_count}"
        params.append(count)

        questions = await conn.fetch(query, *params)
        questions_list = [dict(q) for q in questions]

        # Создаём запись интервью
        interview_id = await conn.fetchval("""
            INSERT INTO mock_interviews (user_session, topic, difficulty, total_questions)
            VALUES ($1, $2, $3, $4)
            RETURNING id
        """, user_session, topic, difficulty, len(questions_list))

        return {
            "interview_id": interview_id,
            "questions": questions_list,
            "total": len(questions_list)
        }
    finally:
        await conn.close()


@app.post("/api/mock-interview/{interview_id}/submit", tags=["Public"])
async def submit_mock_interview(interview_id: int, data: dict = Body(...)):
    """Завершить мок-интервью с результатами"""
    import asyncpg
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        answers = data.get("answers", [])
        duration = data.get("duration_seconds", 0)
        correct = sum(1 for a in answers if a.get("is_correct", False))
        total = len(answers)
        score = (correct / total * 100) if total > 0 else 0

        await conn.execute("""
            UPDATE mock_interviews
            SET correct_answers = $1, score = $2, duration_seconds = $3, answers = $4::jsonb, completed_at = CURRENT_TIMESTAMP
            WHERE id = $5
        """, correct, score, duration, json.dumps(answers), interview_id)

        return {"score": round(score, 1), "correct": correct, "total": total, "duration": duration}
    finally:
        await conn.close()


@app.get("/api/mock-interview/history/{user_session}", tags=["Public"])
async def get_mock_interview_history(user_session: str):
    """История мок-интервью пользователя"""
    import asyncpg
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        interviews = await conn.fetch("""
            SELECT id, topic, difficulty, total_questions, correct_answers, score, duration_seconds, completed_at, created_at
            FROM mock_interviews
            WHERE user_session = $1
            ORDER BY created_at DESC
            LIMIT 20
        """, user_session)
        result = []
        for i in interviews:
            row = dict(i)
            for key in row:
                if hasattr(row[key], 'isoformat'):
                    row[key] = row[key].isoformat()
            result.append(row)
        return {"interviews": result}
    finally:
        await conn.close()


# ============== Загрузка локального видео ==============
@app.post("/api/admin/upload-video", tags=["Admin"])
async def upload_local_video(background_tasks: BackgroundTasks):
    """Загрузить видео с локального ПК (multipart form)"""
    from fastapi import UploadFile, File, Form
    raise HTTPException(status_code=501, detail="Use /api/admin/upload-video-file endpoint with multipart/form-data")


@app.post("/api/admin/upload-video-file", tags=["Admin"])
async def upload_video_file(
    background_tasks: BackgroundTasks,
    file: bytes = Body(...),
    filename: str = "video.mp4",
    topic: str = "General",
    difficulty: str = "middle"
):
    """Загрузить видео файл для обработки"""
    import asyncpg

    task_id = str(uuid.uuid4())
    video_id = task_id[:16]

    # Сохраняем файл
    video_path = TEMP_DIR / f"{video_id}.mp4"
    with open(video_path, "wb") as f:
        f.write(file)

    file_size = len(file)
    print(f"📁 Uploaded video: {filename} ({file_size / 1024 / 1024:.1f} MB)")

    # Конвертируем в mp3
    import subprocess
    audio_path = TEMP_DIR / f"{video_id}.mp3"

    try:
        subprocess.run([
            "ffmpeg", "-y", "-i", str(video_path),
            "-vn", "-acodec", "libmp3lame", "-q:a", "2",
            str(audio_path)
        ], capture_output=True, timeout=300)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка конвертации: {str(e)}")
    finally:
        # Удаляем оригинальное видео для экономии места
        if video_path.exists():
            video_path.unlink()

    # Сохраняем в БД
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        await conn.execute("""
            INSERT INTO uploaded_videos (filename, original_name, file_size, topic, difficulty, task_id, status)
            VALUES ($1, $2, $3, $4, $5, $6, 'processing')
        """, f"{video_id}.mp3", filename, file_size, topic, difficulty, task_id)
    finally:
        await conn.close()

    # Сохраняем задачу
    task_data = {
        "task_id": task_id,
        "youtube_url": f"local://{filename}",
        "topic": topic,
        "level": difficulty,
        "status": "pending",
        "progress": 0,
        "step": "Загружено, начинаем обработку...",
        "is_local_upload": True,
        "filename": filename
    }
    await redis_client.set(f"task:{task_id}", json.dumps(task_data), ex=REDIS_TTL)
    await redis_client.set(f"video_id:{task_id}", video_id, ex=REDIS_TTL)

    # Запускаем транскрибацию напрямую (без yt-dlp)
    background_tasks.add_task(process_local_video, task_id, str(audio_path), filename, topic, difficulty)

    return {"task_id": task_id, "message": "Файл загружен, обработка начата"}


async def process_local_video(task_id: str, audio_path: str, filename: str, topic: str, difficulty: str):
    """Обработка локально загруженного видео"""
    try:
        # Обновляем статус
        task_data = json.loads(await redis_client.get(f"task:{task_id}") or "{}")
        task_data["status"] = "transcribing"
        task_data["progress"] = 20
        task_data["step"] = "Транскрибация аудио..."
        await redis_client.set(f"task:{task_id}", json.dumps(task_data), ex=REDIS_TTL)

        # Транскрибация
        request = TranscribeRequest(audio_path=audio_path, task_id=task_id)
        transcribe_result = await transcribe_audio(request)

        # Обновляем статус
        task_data["status"] = "extracting"
        task_data["progress"] = 60
        task_data["step"] = "Извлечение вопросов..."
        await redis_client.set(f"task:{task_id}", json.dumps(task_data), ex=REDIS_TTL)

        # Извлечение вопросов
        extract_request = ExtractQuestionsRequest(
            transcript=transcribe_result.get("transcript", ""),
            task_id=task_id,
            topic=topic,
            level=difficulty
        )
        extract_result = await extract_questions(extract_request)
        questions = extract_result.get("questions", [])

        # Сохранение вопросов
        save_request = SaveQuestionsRequest(
            questions=questions,
            youtube_url=f"local://{filename}",
            video_title=filename,
            task_id=task_id
        )
        await save_questions(save_request)

        # Обновляем статус
        task_data["status"] = "completed"
        task_data["progress"] = 100
        task_data["step"] = f"Готово! Извлечено {len(questions)} вопросов"
        task_data["result"] = {
            "questions": questions,
            "video_title": filename,
            "questions_count": len(questions)
        }
        await redis_client.set(f"task:{task_id}", json.dumps(task_data), ex=REDIS_TTL)

    except Exception as e:
        print(f"❌ Local video processing error: {e}")
        task_data = json.loads(await redis_client.get(f"task:{task_id}") or "{}")
        task_data["status"] = "error"
        task_data["error"] = str(e)
        await redis_client.set(f"task:{task_id}", json.dumps(task_data), ex=REDIS_TTL)


# ============== Теги вопросов ==============
@app.post("/api/admin/questions/{question_id}/tags", tags=["Admin"])
async def add_question_tag(question_id: int, data: dict = Body(...)):
    """Добавить тег к вопросу"""
    import asyncpg
    tag = data.get("tag", "").strip().lower()
    if not tag:
        raise HTTPException(status_code=400, detail="Тег обязателен")

    conn = await asyncpg.connect(DATABASE_URL)
    try:
        await conn.execute(
            "INSERT INTO question_tags (question_id, tag) VALUES ($1, $2) ON CONFLICT DO NOTHING",
            question_id, tag)
        return {"message": f"Тег '{tag}' добавлен"}
    finally:
        await conn.close()


@app.delete("/api/admin/questions/{question_id}/tags/{tag}", tags=["Admin"])
async def remove_question_tag(question_id: int, tag: str):
    """Удалить тег у вопроса"""
    import asyncpg
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        await conn.execute("DELETE FROM question_tags WHERE question_id = $1 AND tag = $2", question_id, tag)
        return {"message": f"Тег '{tag}' удалён"}
    finally:
        await conn.close()


@app.get("/api/tags", tags=["Public"])
async def get_all_tags():
    """Все используемые теги"""
    import asyncpg
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        tags = await conn.fetch("""
            SELECT tag, COUNT(*) as count
            FROM question_tags
            GROUP BY tag
            ORDER BY count DESC
        """)
        return {"tags": [{"tag": t["tag"], "count": t["count"]} for t in tags]}
    finally:
        await conn.close()


# ============== Статистика (расширенная) ==============
@app.get("/api/stats", tags=["Public"])
async def get_public_stats():
    """Публичная статистика для дашборда"""
    import asyncpg
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        total_questions = await conn.fetchval("SELECT COUNT(*) FROM questions WHERE approved = TRUE")
        total_topics = await conn.fetchval("SELECT COUNT(DISTINCT topic) FROM questions WHERE approved = TRUE")
        total_videos = await conn.fetchval("SELECT COUNT(*) FROM processed_videos")
        total_with_answers = await conn.fetchval("SELECT COUNT(*) FROM questions WHERE approved = TRUE AND answer IS NOT NULL AND answer != ''")

        # Топ-5 тем
        top_topics = await conn.fetch("""
            SELECT topic, COUNT(*) as count
            FROM questions WHERE approved = TRUE
            GROUP BY topic ORDER BY count DESC LIMIT 5
        """)

        # Распределение по уровням
        levels = await conn.fetch("""
            SELECT difficulty, COUNT(*) as count
            FROM questions WHERE approved = TRUE
            GROUP BY difficulty
        """)

        # Платформы видео
        platforms = await conn.fetch("""
            SELECT COALESCE(platform, 'youtube') as platform, COUNT(*) as count
            FROM processed_videos
            GROUP BY platform
        """)

        return {
            "total_questions": total_questions,
            "total_topics": total_topics,
            "total_videos": total_videos,
            "total_with_answers": total_with_answers,
            "top_topics": [{"topic": t["topic"], "count": t["count"]} for t in top_topics],
            "difficulty_distribution": [{"difficulty": l["difficulty"], "count": l["count"]} for l in levels],
            "platform_distribution": [{"platform": p["platform"], "count": p["count"]} for p in platforms]
        }
    finally:
        await conn.close()


@app.get("/api/admin/stats", tags=["Admin"])
async def get_admin_stats():
    """Расширенная статистика для админа"""
    import asyncpg
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        stats = {}
        stats["total_questions"] = await conn.fetchval("SELECT COUNT(*) FROM questions")
        stats["approved_questions"] = await conn.fetchval("SELECT COUNT(*) FROM questions WHERE approved = TRUE")
        stats["pending_questions"] = await conn.fetchval("SELECT COUNT(*) FROM questions WHERE approved = FALSE")
        stats["with_answers"] = await conn.fetchval("SELECT COUNT(*) FROM questions WHERE answer IS NOT NULL AND answer != ''")
        stats["without_answers"] = await conn.fetchval("SELECT COUNT(*) FROM questions WHERE answer IS NULL OR answer = ''")
        stats["total_videos"] = await conn.fetchval("SELECT COUNT(*) FROM processed_videos")
        stats["total_suggestions"] = await conn.fetchval("SELECT COUNT(*) FROM video_suggestions") if await _table_exists(conn, 'video_suggestions') else 0
        stats["pending_suggestions"] = await conn.fetchval("SELECT COUNT(*) FROM video_suggestions WHERE status = 'pending'") if await _table_exists(conn, 'video_suggestions') else 0
        stats["total_feedback"] = await conn.fetchval("SELECT COUNT(*) FROM feedback") if await _table_exists(conn, 'feedback') else 0
        stats["unresolved_feedback"] = await conn.fetchval("SELECT COUNT(*) FROM feedback WHERE is_resolved = FALSE") if await _table_exists(conn, 'feedback') else 0

        # Вопросы за последние 7 дней
        stats["questions_last_week"] = await conn.fetchval(
            "SELECT COUNT(*) FROM questions WHERE created_at > CURRENT_TIMESTAMP - INTERVAL '7 days'")

        # Топ вопросы по вероятности
        top_questions = await conn.fetch("""
            SELECT id, question, probability, topic FROM questions
            WHERE approved = TRUE AND probability > 0
            ORDER BY probability DESC LIMIT 10
        """)
        stats["top_questions"] = [dict(q) for q in top_questions]

        return stats
    finally:
        await conn.close()


async def _table_exists(conn, table_name: str) -> bool:
    """Проверка существования таблицы"""
    try:
        result = await conn.fetchval(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = $1)",
            table_name)
        return result
    except Exception:
        return False


# ============== Экспорт CSV ==============
@app.get("/api/admin/export-csv", tags=["Admin"])
async def export_questions_csv():
    """Экспорт вопросов в CSV"""
    import asyncpg
    from fastapi.responses import StreamingResponse
    import io

    conn = await asyncpg.connect(DATABASE_URL)
    try:
        questions = await conn.fetch("""
            SELECT id, question, answer, topic, difficulty, probability, timecode, approved, source_url, video_title, created_at
            FROM questions ORDER BY id
        """)

        output = io.StringIO()
        # BOM для корректного отображения в Excel
        output.write('\ufeff')
        output.write("ID,Вопрос,Ответ,Тема,Уровень,Вероятность,Таймкод,Одобрен,Источник,Видео,Дата\n")

        for q in questions:
            row = [
                str(q["id"]),
                f'"{(q["question"] or "").replace(chr(34), chr(34)+chr(34))}"',
                f'"{(q["answer"] or "").replace(chr(34), chr(34)+chr(34))}"',
                q["topic"] or "",
                q["difficulty"] or "",
                str(round(q["probability"] or 0, 2)),
                q["timecode"] or "",
                "Да" if q["approved"] else "Нет",
                q["source_url"] or "",
                f'"{(q["video_title"] or "").replace(chr(34), chr(34)+chr(34))}"',
                str(q["created_at"]) if q["created_at"] else ""
            ]
            output.write(",".join(row) + "\n")

        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": "attachment; filename=questions_export.csv"}
        )
    finally:
        await conn.close()


# ============== Обработанные видео ==============
@app.get("/api/admin/videos", tags=["Admin"])
async def get_processed_videos():
    """Список обработанных видео"""
    import asyncpg
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        videos = await conn.fetch("""
            SELECT pv.*, 
                   (SELECT COUNT(*) FROM question_video qv WHERE qv.video_id = pv.id) as linked_questions,
                   (SELECT COUNT(*) FROM question_video qv WHERE qv.video_id = pv.id) as question_count
            FROM processed_videos pv
            ORDER BY pv.processed_at DESC
        """)
        result = []
        for v in videos:
            row = dict(v)
            for key in row:
                if hasattr(row[key], 'isoformat'):
                    row[key] = row[key].isoformat()
            result.append(row)
        return {"videos": result}
    finally:
        await conn.close()


@app.get("/api/admin/videos/{video_id}/questions", tags=["Admin"])
async def get_video_questions(video_id: int):
    """Вопросы, извлечённые из конкретного видео"""
    import asyncpg
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        questions = await conn.fetch("""
            SELECT q.id, q.question, q.answer, q.topic, q.difficulty, q.timecode,
                   q.probability, q.is_approved as approved, q.created_at
            FROM questions q
            JOIN question_video qv ON qv.question_id = q.id
            WHERE qv.video_id = $1
            ORDER BY q.timecode, q.id
        """, video_id)
        result = []
        for q in questions:
            row = dict(q)
            for key in row:
                if hasattr(row[key], 'isoformat'):
                    row[key] = row[key].isoformat()
            result.append(row)
        return {"questions": result}
    finally:
        await conn.close()


@app.delete("/api/admin/videos/{video_id}", tags=["Admin"])
async def delete_processed_video(video_id: int):
    """Удалить обработанное видео (связи question_video удалятся каскадно)"""
    import asyncpg
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        existing = await conn.fetchrow("SELECT id FROM processed_videos WHERE id = $1", video_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Видео не найдено")
        await conn.execute("DELETE FROM processed_videos WHERE id = $1", video_id)
        # Пересчитать вероятности после удаления видео
        await update_probabilities(conn)
        return {"message": "Видео удалено"}
    finally:
        await conn.close()


@app.patch("/api/admin/videos/{video_id}", tags=["Admin"])
async def update_processed_video(video_id: int, data: dict = Body(...)):
    """Обновить заголовок обработанного видео"""
    import asyncpg
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        existing = await conn.fetchrow("SELECT id FROM processed_videos WHERE id = $1", video_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Видео не найдено")
        if "title" in data:
            await conn.execute("UPDATE processed_videos SET title = $1 WHERE id = $2", data["title"], video_id)
        return {"message": "Видео обновлено"}
    finally:
        await conn.close()


# ============== Обновление вопроса (Body вместо query params) ==============
@app.put("/api/admin/questions/{question_id}", tags=["Admin"])
async def update_question_v2(question_id: int, data: dict = Body(...)):
    """Обновить вопрос (принимает JSON body)"""
    import asyncpg
    from similarity_search import invalidate_similarity_cache

    conn = await asyncpg.connect(DATABASE_URL)
    try:
        # Получаем текущий вопрос
        existing = await conn.fetchrow("SELECT * FROM questions WHERE id = $1", question_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Вопрос не найден")

        # Обновляем только переданные поля
        question_text = data.get("question", existing["question"])
        answer = data.get("answer", existing["answer"])
        topic = data.get("topic", existing["topic"])
        difficulty = data.get("difficulty", existing["difficulty"])
        timecode = data.get("timecode", existing["timecode"])

        await conn.execute("""
            UPDATE questions
            SET question = $1, answer = $2, topic = $3, difficulty = $4, timecode = $5, updated_at = CURRENT_TIMESTAMP
            WHERE id = $6
        """, question_text, answer, topic, difficulty, timecode, question_id)

        await update_probabilities(conn)
        await invalidate_similarity_cache()

        return {"message": "Вопрос обновлён"}
    finally:
        await conn.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
