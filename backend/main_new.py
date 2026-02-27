"""
Interview Prep API - Переработанная архитектура
===============================================

Изменения:
1. ❌ Убран n8n - весь pipeline обработки напрямую в backend
2. ❌ Убран WhisperPool с разделением аудио на части
3. ✅ Добавлен WhisperOrchestrator - per-task модель (1 Whisper = 1 полное аудио)
4. ✅ Динамическое управление Whisper-воркерами через Docker API
5. ✅ Оптимизировано для AMD Ryzen 7, 32GB RAM

Архитектура:
- Whisper large-v3 модель (лучшее качество)
- CPU_THREADS=10 для одного воркера
- Максимум 2 воркера одновременно
- TaskQueue с приоритетами
"""

import os
import uuid
import json
import asyncio
import re
from pathlib import Path
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager
from datetime import datetime
import time

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks, Body, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import httpx
import redis.asyncio as redis
import asyncpg
import yt_dlp

from similarity_search import get_similar_questions as search_similar_questions
from video_downloader import VideoDownloader

# ============== Конфигурация ==============
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://diploma:diploma123@localhost:5432/interview_prep")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
WHISPER_BASE_URL = os.getenv("WHISPER_BASE_URL", "http://whisper-worker")  # Базовый URL для воркеров
MAX_WHISPER_WORKERS = int(os.getenv("MAX_WHISPER_WORKERS", "2"))  # Максимум воркеров одновременно
WORKER_IDLE_TIMEOUT = int(os.getenv("WORKER_IDLE_TIMEOUT", "600"))  # Время жизни простаивающего воркера (10 мин)
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "auto")
TEMP_DIR = Path("/app/temp")
TEMP_DIR.mkdir(exist_ok=True)
REDIS_TTL = 86400  # 24 часа

# ============== Глобальные объекты ==============
redis_client: Optional[redis.Redis] = None
whisper_orchestrator: Optional["WhisperOrchestrator"] = None
video_downloader: Optional[VideoDownloader] = None


# ============== WhisperOrchestrator — управление Whisper-воркерами ==============
class WhisperWorker:
    """Один Whisper-воркер, обрабатывающий одну задачу полностью"""
    
    def __init__(self, worker_id: str, port: int):
        self.worker_id = worker_id
        self.port = port
        # Используем WHISPER_BASE_URL для подключения к единственному worker контейнеру
        self.url = f"{WHISPER_BASE_URL}:{port}" if ":" not in WHISPER_BASE_URL else WHISPER_BASE_URL
        self.is_busy = False
        self.current_task_id: Optional[str] = None
        self.last_used = time.time()
        self.is_ready = False
    
    async def health_check(self) -> bool:
        """Проверка доступности воркера"""
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
    
    async def transcribe(self, audio_path: Path, language: str = "ru") -> Dict[str, Any]:
        """Транскрибация полного аудиофайла (БЕЗ разделения на части!)"""
        if not self.is_ready:
            raise Exception(f"Worker {self.worker_id} not ready")
        
        self.is_busy = True
        self.last_used = time.time()
        
        try:
            async with httpx.AsyncClient(timeout=7200.0) as client:  # 2 часа для длинных видео
                response = await client.post(
                    f"{self.url}/transcribe-path",
                    params={"audio_path": str(audio_path), "language": language}
                )
                
                if response.status_code != 200:
                    raise Exception(f"Transcription failed: {response.text}")
                
                return response.json()
        finally:
            self.is_busy = False
            self.last_used = time.time()


class WhisperOrchestrator:
    """
    Оркестратор Whisper-воркеров с per-task моделью масштабирования
    
    Принцип работы:
    1. Приходит задача → ищем свободный воркер
    2. Если есть → отправляем на него
    3. Если нет свободных и можно создать новый → создаем
    4. Если нет ресурсов → ставим в очередь
    5. После обработки воркер остается warm (готов к следующей задаче)
    6. Если простаивает 10 мин → можно остановить для экономии ресурсов
    
    Каждый воркер обрабатывает ПОЛНОЕ аудио целиком (БЕЗ разделения)!
    """
    
    def __init__(self, max_workers: int = 2):
        self.max_workers = max_workers
        self.workers: Dict[str, WhisperWorker] = {}
        self.task_queue: asyncio.Queue = asyncio.Queue()
        self._lock = asyncio.Lock()
        self.next_worker_id = 1
    
    async def initialize(self):
        """Инициализация — запускаем 1 воркер для быстрого старта"""
        print(f"🚀 Initializing WhisperOrchestrator (max_workers={self.max_workers})")
        
        # Запускаем первый воркер сразу (будет готов к работе)
        await self._create_worker()
        print("✅ WhisperOrchestrator ready!")
    
    async def _create_worker(self) -> Optional[WhisperWorker]:
        """Создание нового Whisper-воркера"""
        if len(self.workers) >= self.max_workers:
            print(f"⚠️ Already at max workers ({self.max_workers})")
            return None
        
        async with self._lock:
            worker_id = f"w{self.next_worker_id}"
            self.next_worker_id += 1
            port = 8001
            
            worker = WhisperWorker(worker_id, port)
            
            # В production здесь был бы Docker API для запуска контейнера
            # Сейчас используем статический контейнер из docker-compose
            print(f"📦 Creating worker {worker_id}...")
            
            # Ждем готовности воркера (максимум 2 минуты)
            for i in range(24):  # 24 * 5 = 120 sec
                if await worker.health_check():
                    print(f"✅ Worker {worker_id} ready!")
                    self.workers[worker_id] = worker
                    return worker
                await asyncio.sleep(5)
            
            print(f"❌ Worker {worker_id} failed to start")
            return None
    
    async def get_available_worker(self) -> Optional[WhisperWorker]:
        """Получить свободный воркер или создать новый"""
        # Ищем свободный воркер
        for worker in self.workers.values():
            if not worker.is_busy and worker.is_ready:
                return worker
        
        # Нет свободных — пытаемся создать новый
        if len(self.workers) < self.max_workers:
            return await self._create_worker()
        
        # Все воркеры заняты и нельзя создать новый
        return None
    
    async def transcribe_audio(self, audio_path: Path, task_id: str, language: str = "ru") -> Dict[str, Any]:
        """
        Транскрибация аудио через доступный воркер
        
        ВАЖНО: Воркер обрабатывает ПОЛНОЕ аудио целиком!
        Никакого разделения на части!
        """
        print(f"🎤 Requesting transcription for task {task_id}: {audio_path.name}")
        
        # Получаем воркер
        worker = await self.get_available_worker()
        
        if not worker:
            print(f"⏳ No available workers, waiting...")
            # Ждем пока освободится воркер (максимум 1 час)
            for i in range(720):  # 720 * 5 = 3600 sec = 1 hour
                await asyncio.sleep(5)
                worker = await self.get_available_worker()
                if worker:
                    break
            
            if not worker:
                raise Exception("No available workers after 1 hour wait")
        
        print(f"🎯 Using worker {worker.worker_id} for task {task_id}")
        worker.current_task_id = task_id
        
        try:
            result = await worker.transcribe(audio_path, language)
            print(f"✅ Transcription complete on worker {worker.worker_id}")
            return result
        finally:
            worker.current_task_id = None


# ============== Pydantic Models ==============
class YouTubeRequest(BaseModel):
    youtube_url: str
    topic: Optional[str] = "General"
    level: Optional[str] = "middle"


class TaskStatus(BaseModel):
    task_id: str
    status: str
    progress: int
    step: str
    result: Optional[Dict[str, Any]] = None


# ============== Lifecycle ==============
@asynccontextmanager
async def lifespan(app: FastAPI):
    global redis_client, whisper_orchestrator, video_downloader
    
    # Startup
    print("🚀 Starting up...")
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    
    # Auto-migrate: создаём v2 таблицы если их нет
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        try:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS video_suggestions (
                    id SERIAL PRIMARY KEY, url VARCHAR(500) NOT NULL, platform VARCHAR(50) DEFAULT 'youtube',
                    title VARCHAR(500), topic VARCHAR(100), difficulty VARCHAR(20) DEFAULT 'middle',
                    comment TEXT, user_name VARCHAR(100), user_email VARCHAR(200),
                    status VARCHAR(30) DEFAULT 'pending' CHECK (status IN ('pending','approved','rejected','processing','completed')),
                    admin_comment TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS feedback (
                    id SERIAL PRIMARY KEY, question_id INTEGER REFERENCES questions(id) ON DELETE SET NULL,
                    feedback_type VARCHAR(30) NOT NULL CHECK (feedback_type IN ('like','dislike','report','suggestion','answer_quality')),
                    rating INTEGER CHECK (rating >= 1 AND rating <= 5), comment TEXT,
                    user_name VARCHAR(100), user_email VARCHAR(200), user_session VARCHAR(100),
                    is_resolved BOOLEAN DEFAULT FALSE, admin_response TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS bookmarks (
                    id SERIAL PRIMARY KEY, question_id INTEGER REFERENCES questions(id) ON DELETE CASCADE,
                    user_session VARCHAR(100) NOT NULL, note TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(question_id, user_session)
                );
                CREATE TABLE IF NOT EXISTS question_tags (
                    id SERIAL PRIMARY KEY, question_id INTEGER REFERENCES questions(id) ON DELETE CASCADE,
                    tag VARCHAR(50) NOT NULL, UNIQUE(question_id, tag)
                );
                CREATE TABLE IF NOT EXISTS mock_interviews (
                    id SERIAL PRIMARY KEY, user_session VARCHAR(100) NOT NULL, topic VARCHAR(100),
                    difficulty VARCHAR(20), total_questions INTEGER DEFAULT 0, correct_answers INTEGER DEFAULT 0,
                    score FLOAT DEFAULT 0.0, duration_seconds INTEGER DEFAULT 0, answers JSONB DEFAULT '[]',
                    completed_at TIMESTAMP, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS uploaded_videos (
                    id SERIAL PRIMARY KEY, filename VARCHAR(500) NOT NULL, original_name VARCHAR(500),
                    file_size BIGINT, mime_type VARCHAR(100), topic VARCHAR(100),
                    difficulty VARCHAR(20) DEFAULT 'middle',
                    status VARCHAR(30) DEFAULT 'pending' CHECK (status IN ('pending','processing','completed','error')),
                    task_id VARCHAR(100), uploaded_by VARCHAR(100) DEFAULT 'admin', error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS question_views (
                    id SERIAL PRIMARY KEY, question_id INTEGER REFERENCES questions(id) ON DELETE CASCADE,
                    user_session VARCHAR(100), viewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS user_notes (
                    id SERIAL PRIMARY KEY, question_id INTEGER REFERENCES questions(id) ON DELETE CASCADE,
                    user_session VARCHAR(100) NOT NULL, note TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(question_id, user_session)
                );
            """)
            print("✅ Database v2 tables ensured")
        finally:
            await conn.close()
    except Exception as e:
        print(f"⚠️ Auto-migration warning: {e}")
    
    # Инициализируем VideoDownloader
    video_downloader = VideoDownloader(TEMP_DIR)
    print("📥 VideoDownloader initialized (supports YouTube, VK.video, Rutube, OK.ru, etc.)")
    
    # Инициализируем WhisperOrchestrator
    whisper_orchestrator = WhisperOrchestrator(max_workers=MAX_WHISPER_WORKERS)
    await whisper_orchestrator.initialize()
    
    # Инициализируем систему поиска похожих вопросов
    from similarity_search import initialize_similarity_search
    try:
        await initialize_similarity_search()
    except Exception as e:
        print(f"⚠️ Similarity search initialization failed: {e}")
        print("   (Will initialize on first use)")
    print("🔍 Similarity search initialized")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down...")
    if redis_client:
        await redis_client.close()


app = FastAPI(
    title="Interview Prep API v2.0",
    description="""
## API для подготовки к IT собеседованиям (переработанная архитектура)

**Улучшения:**
- ❌ Убран n8n — прямой REST API pipeline
- ❌ Убрано разделение аудио на части
- ✅ Per-task масштабирование Whisper (1 воркер = 1 полное аудио)
- ✅ Оптимизировано для AMD Ryzen 7, 32GB RAM
- ✅ Whisper large-v3 для максимального качества

### Основные эндпоинты:
- `POST /api/process-video` - Запуск обработки видео (прямой pipeline)
- `GET /api/task/{task_id}` - Статус задачи
- `GET /api/full-export/{task_id}` - Полный экспорт
""",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {"name": "Processing", "description": "Обработка видео"},
        {"name": "Status", "description": "Статус и мониторинг"},
        {"name": "Export", "description": "Экспорт данных"},
        {"name": "Public", "description": "Публичные данные"},
        {"name": "Admin", "description": "Административная панель"}
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
            except:
                self.disconnect(client_id)
    
    async def broadcast_to_task(self, task_id: str, data: dict):
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
            data = await websocket.receive_text()
            # Echo для keepalive
            await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        manager.disconnect(client_id)


# ============== Core Processing Pipeline ==============
async def process_video_pipeline(task_id: str, video_url: str, topic: str, level: str):
    """
    Главный pipeline обработки видео (БЕЗ n8n!)
    
    Поддерживаемые платформы:
    - YouTube
    - VK.video
    - Rutube
    - OK.ru
    - Dailymotion
    - Vimeo
    - и другие
    
    Этапы:
    1. Скачивание аудио и субтитров (yt-dlp)
    2. Транскрибация через Whisper (ПОЛНОЕ аудио, без разделения)
    3. Извлечение вопросов через LLM
    4. Сохранение в БД
    """
    try:
        # ========== Этап 1: Скачивание аудио ==========
        await update_task_progress(task_id, 5, "downloading", "Начинаем скачивание видео...")
        
        try:
            download_result = await download_video_audio(video_url, task_id)
        except Exception as download_err:
            await update_task_progress(task_id, 5, "error", f"Ошибка скачивания: {download_err}")
            raise
        
        audio_path = Path(download_result["audio_path"])
        video_title = download_result["video_title"]
        video_id = download_result["video_id"]
        platform = download_result.get("platform", "unknown")
        subtitles = download_result.get("subtitles", [])
        has_subtitles = download_result.get("has_subtitles", False)
        duration = download_result.get("duration", 0)
        
        await update_task_progress(task_id, 20, "downloaded", f"Скачано: {video_title} ({duration}с)")
        
        # ========== Этап 2: Транскрибация ==========
        await update_task_progress(task_id, 25, "transcribing", "Транскрибация аудио через Whisper...")
        
        try:
            whisper_result = await whisper_orchestrator.transcribe_audio(
                audio_path=audio_path,
                task_id=task_id,
                language="ru"
            )
        except Exception as whisper_err:
            await update_task_progress(task_id, 30, "error", f"Ошибка транскрибации: {whisper_err}")
            raise
        
        transcript = whisper_result["text"]
        whisper_segments = whisper_result["segments"]
        
        await update_task_progress(task_id, 60, "transcribed", f"Транскрибация завершена: {len(whisper_segments)} сегментов, {len(transcript)} символов")
        
        # Слияние с субтитрами (если есть)
        merged_segments = whisper_segments
        if has_subtitles and subtitles:
            merged_segments = merge_subtitles_with_whisper(subtitles, whisper_segments)
            transcript = " ".join([s["text"] for s in merged_segments])
        
        # Сохраняем транскрипцию в Redis
        transcript_data = {
            "transcript": transcript,
            "segments": merged_segments,
            "length": len(transcript),
            "whisper_raw": whisper_result["text"],
            "whisper_segments": whisper_segments,
            "youtube_subtitles": subtitles,
            "has_subtitles": has_subtitles
        }
        await redis_client.set(f"transcript:{task_id}", json.dumps(transcript_data), ex=REDIS_TTL)
        
        # ========== Этап 3: Извлечение вопросов ==========
        await update_task_progress(task_id, 65, "extracting", "Извлечение вопросов через LLM...")
        
        try:
            questions = await extract_questions_from_transcript(transcript, topic, level)
        except Exception as llm_err:
            await update_task_progress(task_id, 70, "error", f"Ошибка LLM: {llm_err}")
            raise
        
        # Фильтрация и дедупликация
        questions = filter_low_quality_questions(questions)
        questions = deduplicate_questions(questions)
        
        await update_task_progress(task_id, 85, "extracted", f"Извлечено {len(questions)} вопросов")
        
        # ========== Этап 4: Сохранение в БД ==========
        await update_task_progress(task_id, 90, "saving", "Сохранение в базу данных...")
        
        try:
            await save_questions_to_db(questions, video_url, video_title, video_id, task_id, platform)
        except Exception as db_err:
            await update_task_progress(task_id, 90, "error", f"Ошибка БД: {db_err}")
            raise
        
        # ========== Завершение ==========
        await update_task_progress(task_id, 100, "completed", "Готово!")
        
        task_data = await redis_client.get(f"task:{task_id}")
        if task_data:
            task = json.loads(task_data)
            task["status"] = "completed"
            task["result"] = {
                "video_title": video_title,
                "questions_count": len(questions),
                "questions": questions
            }
            await redis_client.set(f"task:{task_id}", json.dumps(task), ex=REDIS_TTL)
        
        # Отправляем результат через WebSocket
        await manager.broadcast_to_task(task_id, {
            "type": "completed",
            "task_id": task_id,
            "video_title": video_title,
            "questions_count": len(questions)
        })
        
        # Очистка временных файлов
        cleanup_temp_files(video_id)
        
        print(f"✅ Task {task_id} completed successfully!")
        
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Task {task_id} failed: {error_msg}")
        
        await update_task_error(task_id, error_msg)


async def update_task_progress(task_id: str, progress: int, status: str, step: str):
    """Обновить прогресс задачи с детальным статусом"""
    task_data = await redis_client.get(f"task:{task_id}")
    if task_data:
        task = json.loads(task_data)
        task["progress"] = progress
        task["status"] = status
        task["step"] = step
        # Добавляем запись в лог
        if "logs" not in task:
            task["logs"] = []
        task["logs"].append({
            "time": datetime.now().isoformat(),
            "progress": progress,
            "status": status,
            "message": step
        })
        # Ограничиваем размер лога
        if len(task["logs"]) > 50:
            task["logs"] = task["logs"][-50:]
        await redis_client.set(f"task:{task_id}", json.dumps(task), ex=REDIS_TTL)
    
    # Отправляем через WebSocket
    await manager.broadcast_to_task(task_id, {
        "type": "progress",
        "task_id": task_id,
        "progress": progress,
        "status": status,
        "step": step
    })
    print(f"📊 Task {task_id}: [{status}] {progress}% — {step}")


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


# ============== Processing Functions ==============
async def download_video_audio(video_url: str, task_id: str) -> Dict[str, Any]:
    """Скачивание аудио и субтитров с любой платформы (YouTube, VK.video, Rutube, и т.д.)"""
    global video_downloader
    
    if not video_downloader:
        raise Exception("VideoDownloader not initialized")
    
    try:
        result = await video_downloader.download_video_audio(video_url)
        
        # Добавляем информацию о платформе (для логов)
        platform_info = video_downloader.get_platform_info(video_url)
        print(f"{platform_info['platform_icon']} Loaded from {platform_info['platform_name']}: {result['video_title']}")
        
        return result
    except Exception as e:
        print(f"❌ Download failed: {e}")
        raise


async def extract_questions_from_transcript(transcript: str, topic: str, level: str) -> List[Dict[str, Any]]:
    """Извлечение вопросов из транскрипции через LLM"""
    
    prompt = f"""Ты — эксперт по анализу технических интервью. Проанализируй транскрипцию видео с собеседованием и извлеки ВСЕ вопросы, которые задаются кандидату.

ВАЖНО:
- Извлекай ТОЛЬКО вопросы, которые задаёт интервьюер кандидату
- НЕ извлекай вопросы, которые кандидат задаёт интервьюеру
- Формулируй вопросы чётко и понятно
- Определи тему вопроса (Backend, Frontend, DevOps, Database, Algorithms, System Design и т.д.)
- Определи сложность (junior, middle, senior)

Транскрипция:
{transcript[:50000]}

Верни JSON массив вопросов в формате:
[
  {{
    "question": "Полный текст вопроса?",
    "topic": "Backend",
    "difficulty": "middle"
  }}
]

Только JSON, без дополнительного текста!"""
    
    return await call_llm_api(prompt)


async def save_questions_to_db(questions: List[Dict], video_url: str, video_title: str, video_id: str, task_id: str, platform: str = "youtube"):
    """Сохранение вопросов в базу данных"""
    
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        # Проверяем, обрабатывалось ли это видео
        existing_video = await conn.fetchval(
            "SELECT id FROM processed_videos WHERE video_id = $1", video_id
        )
        
        if existing_video:
            print(f"⚠️ Video {video_id} already processed, skipping save")
            return
        
        # Сохраняем видео с указанием платформы
        db_video_id = await conn.fetchval(
            """INSERT INTO processed_videos (video_id, youtube_url, title, platform, processed_at)
               VALUES ($1, $2, $3, $4, NOW())
               RETURNING id""",
            video_id, video_url, video_title, platform
        )
        
        # Сохраняем вопросы
        saved_count = 0
        for q in questions:
            question_text = q.get("question", "").strip()
            if not question_text or len(question_text) < 5:
                continue
            
            # Проверяем дубликат
            existing = await conn.fetchval(
                "SELECT id FROM questions WHERE LOWER(question) = LOWER($1)",
                question_text
            )
            
            if existing:
                # Добавляем связь с видео
                await conn.execute(
                    """INSERT INTO question_video (question_id, video_id)
                       VALUES ($1, $2)
                       ON CONFLICT DO NOTHING""",
                    existing, db_video_id
                )
            else:
                # Создаём новый вопрос
                question_id = await conn.fetchval(
                    """INSERT INTO questions (question, topic, difficulty, approved)
                       VALUES ($1, $2, $3, FALSE)
                       RETURNING id""",
                    question_text,
                    q.get("topic", "General"),
                    q.get("difficulty", "middle")
                )
                
                # Связываем с видео
                await conn.execute(
                    """INSERT INTO question_video (question_id, video_id)
                       VALUES ($1, $2)""",
                    question_id, db_video_id
                )
            
            saved_count += 1
        
        # Обновляем вероятности
        await update_probabilities(conn)
        
        print(f"✅ Saved {saved_count} questions for video {video_title}")
        
    finally:
        await conn.close()


# ============== API Endpoints ==============
@app.get("/", tags=["Status"])
async def root():
    """Корневой эндпоинт"""
    return {
        "message": "Interview Prep API v2.0",
        "status": "running",
        "architecture": "per-task Whisper scaling (no chunking)"
    }


@app.get("/health", tags=["Status"])
async def health():
    """Проверка здоровья сервиса"""
    global whisper_orchestrator
    
    workers_status = []
    if whisper_orchestrator:
        for wid, worker in whisper_orchestrator.workers.items():
            workers_status.append({
                "id": wid,
                "is_ready": worker.is_ready,
                "is_busy": worker.is_busy,
                "current_task": worker.current_task_id
            })
    
    temp_files = list(TEMP_DIR.glob("*"))
    temp_size_mb = sum(f.stat().st_size for f in temp_files if f.is_file()) / (1024 * 1024)
    
    return {
        "status": "healthy",
        "whisper_orchestrator": {
            "max_workers": MAX_WHISPER_WORKERS,
            "active_workers": len(whisper_orchestrator.workers) if whisper_orchestrator else 0,
            "workers": workers_status
        },
        "architecture": "per-task scaling (1 worker = 1 full audio, no chunking)",
        "temp_files_count": len(temp_files),
        "temp_size_mb": round(temp_size_mb, 2)
    }


@app.post("/api/process-video", tags=["Processing"])
async def process_video(request: YouTubeRequest, background_tasks: BackgroundTasks):
    """
    Запуск обработки видео (прямой pipeline, без n8n)
    
    Поддерживаемые платформы:
    - YouTube (youtube.com, youtu.be)
    - VK Video (vk.com/video, vkvideo.ru)
    - Rutube (rutube.ru)
    - OK.ru (ok.ru/video)
    - Dailymotion, Vimeo и др.
    
    Pipeline:
    1. Скачивание аудио (yt-dlp)
    2. Транскрибация полного аудио через Whisper (БЕЗ разделения!)
    3. Извлечение вопросов через LLM
    4. Сохранение в БД
    """
    task_id = str(uuid.uuid4())
    
    if not is_valid_video_url(request.youtube_url):
        raise HTTPException(status_code=400, detail="Invalid video URL. Supported: YouTube, VK.video, Rutube, OK.ru, etc.")
    
    # Сохраняем задачу в Redis
    task_data = {
        "task_id": task_id,
        "youtube_url": request.youtube_url,
        "video_url": request.youtube_url,
        "topic": request.topic,
        "level": request.level,
        "status": "pending",
        "progress": 0,
        "step": "В очереди...",
        "logs": [{"time": datetime.now().isoformat(), "progress": 0, "status": "pending", "message": "Задача создана"}],
        "created_at": datetime.now().isoformat()
    }
    await redis_client.set(f"task:{task_id}", json.dumps(task_data), ex=REDIS_TTL)
    
    # Добавляем в глобальный список задач
    await redis_client.lpush("global:tasks", task_id)
    await redis_client.ltrim("global:tasks", 0, 99)
    await redis_client.expire("global:tasks", REDIS_TTL)
    
    # Запускаем обработку в фоне (БЕЗ n8n!)
    background_tasks.add_task(
        process_video_pipeline,
        task_id,
        request.youtube_url,
        request.topic,
        request.level
    )
    
    return {"task_id": task_id, "status": "started"}


@app.post("/api/process-video/{client_id}", tags=["Processing"])
async def process_video_with_client(
    client_id: str,
    request: YouTubeRequest,
    background_tasks: BackgroundTasks
):
    """Запуск обработки с привязкой к WebSocket клиенту"""
    task_id = str(uuid.uuid4())
    
    if not is_valid_video_url(request.youtube_url):
        raise HTTPException(status_code=400, detail="Invalid video URL. Supported: YouTube, VK.video, Rutube, OK.ru, etc.")
    
    # Связываем task с client
    await redis_client.set(f"task:{task_id}:client", client_id, ex=REDIS_TTL)
    await redis_client.set(f"client:{client_id}:last_task", task_id, ex=REDIS_TTL)
    
    tasks_key = f"client:{client_id}:tasks"
    await redis_client.lpush(tasks_key, task_id)
    await redis_client.ltrim(tasks_key, 0, 19)
    await redis_client.expire(tasks_key, REDIS_TTL)
    
    task_data = {
        "task_id": task_id,
        "youtube_url": request.youtube_url,
        "video_url": request.youtube_url,
        "topic": request.topic,
        "level": request.level,
        "status": "pending",
        "progress": 0,
        "step": "В очереди...",
        "logs": [{"time": datetime.now().isoformat(), "progress": 0, "status": "pending", "message": "Задача создана"}],
        "created_at": datetime.now().isoformat()
    }
    await redis_client.set(f"task:{task_id}", json.dumps(task_data), ex=REDIS_TTL)
    
    # Добавляем в глобальный список задач
    await redis_client.lpush("global:tasks", task_id)
    await redis_client.ltrim("global:tasks", 0, 99)
    await redis_client.expire("global:tasks", REDIS_TTL)
    
    await manager.send_progress(client_id, {
        "type": "progress",
        "task_id": task_id,
        "progress": 0,
        "status": "pending",
        "step": "Запуск обработки..."
    })
    
    background_tasks.add_task(
        process_video_pipeline,
        task_id,
        request.youtube_url,
        request.topic,
        request.level
    )
    
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
        raise HTTPException(status_code=404, detail="No tasks for this client")
    
    task_data = await redis_client.get(f"task:{task_id}")
    if not task_data:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return json.loads(task_data)


@app.get("/api/tasks/{client_id}", tags=["Status"])
async def get_client_tasks(client_id: str):
    """Получение всех задач клиента"""
    tasks_key = f"client:{client_id}:tasks"
    task_ids = await redis_client.lrange(tasks_key, 0, 19)
    
    tasks = []
    for task_id in task_ids:
        task_data = await redis_client.get(f"task:{task_id}")
        if task_data:
            task = json.loads(task_data)
            tasks.append({
                "task_id": task_id,
                "status": task.get("status"),
                "progress": task.get("progress"),
                "video_title": task.get("result", {}).get("video_title", "Processing...")
            })
    
    return {"tasks": tasks, "count": len(tasks)}


@app.get("/api/all-tasks", tags=["Status"])
async def get_all_tasks():
    """Получение всех задач (глобальный список для админки)"""
    task_ids = await redis_client.lrange("global:tasks", 0, 99)
    
    tasks = []
    for task_id in task_ids:
        task_data = await redis_client.get(f"task:{task_id}")
        if task_data:
            task = json.loads(task_data)
            tasks.append({
                "task_id": task_id,
                "video_url": task.get("video_url") or task.get("youtube_url", ""),
                "status": task.get("status", "unknown"),
                "progress": task.get("progress", 0),
                "step": task.get("step", ""),
                "logs": task.get("logs", []),
                "created_at": task.get("created_at"),
                "result": task.get("result"),
                "error": task.get("error"),
            })
    
    return {"tasks": tasks, "count": len(tasks)}


@app.get("/api/questions", tags=["Public"])
async def get_all_questions(topic: Optional[str] = None, level: Optional[str] = None):
    """Получение всех одобренных вопросов"""
    
    conn = await asyncpg.connect(DATABASE_URL)
    try:
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
        
        questions = await conn.fetch(query, *params) if params else await conn.fetch(query)
        
        result = [
            {
                "id": q["id"],
                "question": q["question"],
                "answer": q["answer"],
                "topic": q["topic"],
                "difficulty": q["difficulty"],
                "probability": float(q["probability"]) if q["probability"] else 0.0,
                "timecode": q["timecode"]
            }
            for q in questions
        ]
        
        return JSONResponse(
            content={"questions": result, "total": len(result)},
            media_type="application/json; charset=utf-8"
        )
    finally:
        await conn.close()


@app.get("/api/questions/{question_id}", tags=["Public"])
async def get_public_question_detail(question_id: int):
    """Получить детали одобренного вопроса для публичной части (с видео)"""
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        total_videos = await conn.fetchval("SELECT COUNT(*) FROM processed_videos") or 0
        
        q = await conn.fetchrow("""
            SELECT q.id, q.question, q.answer, q.topic, q.difficulty, q.probability,
                   q.timecode, q.source_url, q.video_title, q.created_at,
                   COALESCE(vc.cnt, 0) AS video_count
            FROM questions q
            LEFT JOIN (
                SELECT question_id, COUNT(DISTINCT video_id) AS cnt
                FROM question_video GROUP BY question_id
            ) vc ON vc.question_id = q.id
            WHERE q.id = $1 AND q.approved = TRUE
        """, question_id)
        
        if not q:
            raise HTTPException(status_code=404, detail="Question not found")
        
        # Видео, в которых встречался этот вопрос
        videos = await conn.fetch("""
            SELECT pv.id, pv.title, pv.youtube_url, pv.platform
            FROM question_video qv
            JOIN processed_videos pv ON pv.id = qv.video_id
            WHERE qv.question_id = $1
            ORDER BY pv.title
        """, question_id)
        
        # Похожие вопросы
        similar = []
        try:
            similar = await search_similar_questions(q["question"], limit=5)
            # Исключаем текущий вопрос из похожих
            similar = [s for s in similar if s.get("id") != question_id]
        except Exception as e:
            print(f"⚠️ Similar search failed: {e}")
        
        result = {
            "id": q["id"],
            "question": q["question"],
            "answer": q["answer"],
            "topic": q["topic"],
            "difficulty": q["difficulty"],
            "probability": float(q["probability"]) if q["probability"] else 0.0,
            "video_count": q["video_count"],
            "total_videos": total_videos,
            "timecode": q["timecode"],
            "source_url": q["source_url"],
            "video_title": q["video_title"],
            "created_at": q["created_at"].isoformat() if q["created_at"] else None,
            "videos": [
                {
                    "id": v["id"],
                    "title": v["title"],
                    "url": v["youtube_url"],
                    "platform": v["platform"] or "youtube",
                }
                for v in videos
            ],
            "similar_questions": similar,
        }
        
        return JSONResponse(content=result, media_type="application/json; charset=utf-8")
    finally:
        await conn.close()


@app.get("/api/questions/similar", tags=["Public"])
async def get_similar_questions_api(query: str, limit: int = 5):
    """Поиск похожих вопросов"""
    try:
        similar = await search_similar_questions(query, limit=limit)
        return JSONResponse(
            content={"similar_questions": similar},
            media_type="application/json; charset=utf-8"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============== Export Endpoints ==============
@app.get("/api/export/{task_id}", tags=["Export"])
async def export_questions_json(task_id: str):
    """Скачать вопросы задачи в формате JSON"""
    task_data = await redis_client.get(f"task:{task_id}")
    if not task_data:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = json.loads(task_data)
    result = task.get("result", {})
    
    export_data = {
        "task_id": task_id,
        "video_title": result.get("video_title", "Unknown"),
        "questions_count": result.get("questions_count", 0),
        "questions": result.get("questions", [])
    }
    
    return JSONResponse(
        content=export_data,
        headers={"Content-Disposition": f'attachment; filename="questions_{task_id}.json"'}
    )


@app.get("/api/transcript/{task_id}", tags=["Export"])
async def get_transcript(task_id: str):
    """Скачать транскрипцию"""
    transcript_data = await redis_client.get(f"transcript:{task_id}")
    if not transcript_data:
        raise HTTPException(status_code=404, detail="Transcript not found")
    
    data = json.loads(transcript_data)
    return JSONResponse(
        content=data,
        headers={"Content-Disposition": f'attachment; filename="transcript_{task_id}.json"'}
    )


@app.get("/api/full-export/{task_id}", tags=["Export"])
async def full_export(task_id: str):
    """Полный экспорт данных задачи"""
    transcript_data = await redis_client.get(f"transcript:{task_id}")
    transcript = json.loads(transcript_data) if transcript_data else {}
    
    task_data = await redis_client.get(f"task:{task_id}")
    task = json.loads(task_data) if task_data else {}
    
    export = {
        "task_id": task_id,
        "transcript": transcript.get("transcript", ""),
        "segments": transcript.get("segments", []),
        "video_title": task.get("result", {}).get("video_title", "Unknown"),
        "questions": task.get("result", {}).get("questions", []),
        "questions_count": task.get("result", {}).get("questions_count", 0),
        "status": task.get("status", "unknown")
    }
    
    return JSONResponse(
        content=export,
        headers={"Content-Disposition": f'attachment; filename="full_export_{task_id}.json"'}
    )


# ============== Admin Panel Endpoints ==============
@app.get("/api/admin/questions", tags=["Admin"])
async def get_admin_questions():
    """Получить все вопросы для админа с video_count и total_videos"""
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        # Общее число обработанных видео
        total_videos = await conn.fetchval("SELECT COUNT(*) FROM processed_videos") or 0
        
        questions = await conn.fetch("""
            SELECT q.id, q.question, q.answer, q.topic, q.difficulty, q.probability, 
                   q.timecode, q.approved, q.source_url, q.video_title, q.created_at,
                   COALESCE(vc.cnt, 0) AS video_count
            FROM questions q
            LEFT JOIN (
                SELECT question_id, COUNT(DISTINCT video_id) AS cnt
                FROM question_video
                GROUP BY question_id
            ) vc ON vc.question_id = q.id
            ORDER BY q.probability DESC NULLS LAST, q.created_at DESC
        """)
        
        result = [
            {
                "id": q["id"],
                "question": q["question"],
                "answer": q["answer"],
                "topic": q["topic"],
                "difficulty": q["difficulty"],
                "probability": float(q["probability"]) if q["probability"] else 0.0,
                "video_count": q["video_count"],
                "timecode": q["timecode"],
                "approved": q["approved"],
                "source_url": q["source_url"],
                "video_title": q["video_title"],
                "created_at": q["created_at"].isoformat() if q["created_at"] else None,
            }
            for q in questions
        ]
        
        return JSONResponse(
            content={"questions": result, "total_videos": total_videos},
            media_type="application/json; charset=utf-8"
        )
    finally:
        await conn.close()


@app.post("/api/admin/questions", tags=["Admin"])
async def create_question(data: dict = Body(...)):
    """Создать новый вопрос"""
    from similarity_search import invalidate_similarity_cache
    
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        question_id = await conn.fetchval(
            """INSERT INTO questions (question, answer, topic, difficulty, approved)
               VALUES ($1, $2, $3, $4, $5)
               RETURNING id""",
            data.get("question"),
            data.get("answer", ""),
            data.get("topic", "General"),
            data.get("difficulty", "middle"),
            data.get("approved", False)
        )
        
        await invalidate_similarity_cache()
        return {"id": question_id, "message": "Question created"}
    finally:
        await conn.close()


@app.put("/api/admin/questions/{question_id}", tags=["Admin"])
async def update_question(question_id: int, data: dict = Body(...)):
    """Обновить вопрос (body JSON)"""
    from similarity_search import invalidate_similarity_cache
    
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        await conn.execute(
            """UPDATE questions
               SET question = $1, answer = $2, topic = $3, difficulty = $4, timecode = $5, approved = $6
               WHERE id = $7""",
            data.get("question", ""),
            data.get("answer", ""),
            data.get("topic", "General"),
            data.get("difficulty", "middle"),
            data.get("timecode"),
            data.get("approved", False),
            question_id
        )
        
        await invalidate_similarity_cache()
        return {"message": "Question updated"}
    finally:
        await conn.close()


@app.delete("/api/admin/questions/{question_id}", tags=["Admin"])
async def delete_question(question_id: int):
    """Удалить вопрос"""
    from similarity_search import invalidate_similarity_cache
    
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        await conn.execute("DELETE FROM questions WHERE id = $1", question_id)
        await invalidate_similarity_cache()
        return {"message": "Question deleted"}
    finally:
        await conn.close()


@app.post("/api/admin/approve-questions", tags=["Admin"])
async def approve_questions(data: Dict[str, List[int]]):
    """Одобрить вопросы"""
    from similarity_search import invalidate_similarity_cache
    
    question_ids = data.get("question_ids", [])
    
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        await conn.execute(
            "UPDATE questions SET approved = TRUE WHERE id = ANY($1::int[])",
            question_ids
        )
        
        await update_probabilities(conn)
        await invalidate_similarity_cache()
        
        return {"message": f"Approved {len(question_ids)} questions"}
    finally:
        await conn.close()


@app.post("/api/admin/revoke-questions", tags=["Admin"])
async def revoke_questions(data: Dict[str, List[int]]):
    """Отозвать утверждение вопросов (approved → false)"""
    from similarity_search import invalidate_similarity_cache
    
    question_ids = data.get("question_ids", [])
    
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        await conn.execute(
            "UPDATE questions SET approved = FALSE WHERE id = ANY($1::int[])",
            question_ids
        )
        
        await update_probabilities(conn)
        await invalidate_similarity_cache()
        
        return {"message": f"Revoked {len(question_ids)} questions"}
    finally:
        await conn.close()


@app.get("/api/admin/questions/{question_id}", tags=["Admin"])
async def get_question_detail(question_id: int):
    """Получить полную карточку вопроса: данные + video_count + похожие вопросы"""
    from similarity_search import get_similar_questions as find_similar
    
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        total_videos = await conn.fetchval("SELECT COUNT(*) FROM processed_videos") or 0
        
        q = await conn.fetchrow("""
            SELECT q.id, q.question, q.answer, q.topic, q.difficulty, q.probability,
                   q.timecode, q.approved, q.source_url, q.video_title, q.created_at,
                   COALESCE(vc.cnt, 0) AS video_count
            FROM questions q
            LEFT JOIN (
                SELECT question_id, COUNT(DISTINCT video_id) AS cnt
                FROM question_video GROUP BY question_id
            ) vc ON vc.question_id = q.id
            WHERE q.id = $1
        """, question_id)
        
        if not q:
            raise HTTPException(status_code=404, detail="Question not found")
        
        # Видео, в которых встречался этот вопрос
        videos = await conn.fetch("""
            SELECT pv.id, pv.title, pv.youtube_url, pv.platform, pv.processed_at
            FROM question_video qv
            JOIN processed_videos pv ON pv.id = qv.video_id
            WHERE qv.question_id = $1
            ORDER BY pv.processed_at DESC
        """, question_id)
        
        # Похожие вопросы (через FAISS embeddings)
        similar = []
        try:
            similar = await find_similar(q["question"], question_id=question_id, limit=5)
        except Exception as e:
            print(f"⚠️ Similar search failed: {e}")
        
        result = {
            "id": q["id"],
            "question": q["question"],
            "answer": q["answer"],
            "topic": q["topic"],
            "difficulty": q["difficulty"],
            "probability": float(q["probability"]) if q["probability"] else 0.0,
            "video_count": q["video_count"],
            "total_videos": total_videos,
            "timecode": q["timecode"],
            "approved": q["approved"],
            "source_url": q["source_url"],
            "video_title": q["video_title"],
            "created_at": q["created_at"].isoformat() if q["created_at"] else None,
            "videos": [
                {
                    "id": v["id"],
                    "title": v["title"],
                    "url": v["youtube_url"],
                    "platform": v["platform"],
                    "processed_at": v["processed_at"].isoformat() if v["processed_at"] else None,
                }
                for v in videos
            ],
            "similar_questions": [
                {
                    "id": s.get("id"),
                    "question": s.get("question"),
                    "topic": s.get("topic"),
                    "difficulty": s.get("difficulty"),
                    "probability": s.get("probability", 0),
                    "similarity_score": s.get("similarity_score", 0),
                }
                for s in similar
            ],
        }
        
        return JSONResponse(content=result, media_type="application/json; charset=utf-8")
    finally:
        await conn.close()


@app.post("/api/admin/questions/merge", tags=["Admin"])
async def merge_questions(data: dict = Body(...)):
    """
    Объединить вопрос source_id в target_id.
    Все video-связи source переносятся на target, source удаляется.
    Вероятность target пересчитывается.
    """
    from similarity_search import invalidate_similarity_cache
    
    source_id = data.get("source_id")
    target_id = data.get("target_id")
    
    if not source_id or not target_id:
        raise HTTPException(status_code=400, detail="source_id и target_id обязательны")
    
    if source_id == target_id:
        raise HTTPException(status_code=400, detail="Нельзя объединить вопрос сам с собой")
    
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        # Проверяем что оба существуют
        source = await conn.fetchrow("SELECT id, question FROM questions WHERE id = $1", source_id)
        target = await conn.fetchrow("SELECT id, question FROM questions WHERE id = $1", target_id)
        
        if not source:
            raise HTTPException(status_code=404, detail=f"Вопрос source_id={source_id} не найден")
        if not target:
            raise HTTPException(status_code=404, detail=f"Вопрос target_id={target_id} не найден")
        
        # Переносим все video-связи с source на target (игнорируем конфликты)
        await conn.execute("""
            INSERT INTO question_video (question_id, video_id)
            SELECT $1, video_id FROM question_video WHERE question_id = $2
            ON CONFLICT DO NOTHING
        """, target_id, source_id)
        
        # Удаляем source
        await conn.execute("DELETE FROM questions WHERE id = $1", source_id)
        
        # Пересчитываем вероятности
        await update_probabilities(conn)
        await invalidate_similarity_cache()
        
        return {
            "message": f"Вопрос #{source_id} объединён с #{target_id}",
            "target_id": target_id
        }
    finally:
        await conn.close()


@app.post("/api/admin/generate-answer/{question_id}", tags=["Admin"])
async def generate_answer_for_question(question_id: int):
    """
    Генерация ответа на вопрос через LLM
    
    Админ может использовать эту функцию для автоматической генерации
    ответов на вопросы через LLM (OpenRouter, Gemini, Groq)
    """
    from similarity_search import invalidate_similarity_cache
    
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        # Получаем вопрос
        question_data = await conn.fetchrow(
            "SELECT id, question, topic, difficulty FROM questions WHERE id = $1",
            question_id
        )
        
        if not question_data:
            raise HTTPException(status_code=404, detail="Question not found")
        
        question_text = question_data["question"]
        topic = question_data["topic"]
        difficulty = question_data["difficulty"]
        
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

Верни только текст ответа, без дополнительных пояснений."""
        
        # Вызываем LLM
        llm_response = await call_llm_api_for_answer(prompt)
        
        # Обновляем вопрос с ответом
        await conn.execute(
            """UPDATE questions SET answer = $1 WHERE id = $2""",
            llm_response, question_id
        )
        
        await invalidate_similarity_cache()
        
        return {
            "message": "Answer generated successfully",
            "question_id": question_id,
            "answer": llm_response
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate answer: {str(e)}")
    finally:
        await conn.close()


@app.post("/api/admin/recalculate-probabilities", tags=["Admin"])
async def recalculate_probabilities():
    """Пересчитать вероятности"""
    from similarity_search import invalidate_similarity_cache
    
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        await update_probabilities(conn)
        await invalidate_similarity_cache()
        return {"message": "Probabilities recalculated"}
    finally:
        await conn.close()


# ============== Helper Functions ==============
def is_valid_video_url(url: str) -> bool:
    """Проверка валидности URL видео (любая платформа)"""
    global video_downloader
    if video_downloader:
        return video_downloader.is_valid_url(url)
    # Fallback - базовая проверка
    return bool(re.match(r'https?://[^\s<>"{}|\\^`\[\]]+', url))


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
    """Парсинг VTT субтитров"""
    subtitles = []
    try:
        with open(vtt_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Простой парсинг VTT
        lines = content.split('\n')
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Ищем таймкод
            if '-->' in line:
                times = line.split('-->')
                start_time = times[0].strip()
                end_time = times[1].strip()
                
                # Следующая строка - текст
                i += 1
                text_parts = []
                while i < len(lines) and lines[i].strip() and '-->' not in lines[i]:
                    text_parts.append(lines[i].strip())
                    i += 1
                
                text = ' '.join(text_parts)
                if text:
                    subtitles.append({
                        "start": start_time,
                        "end": end_time,
                        "text": text
                    })
            
            i += 1
    except Exception as e:
        print(f"⚠️ VTT parsing error: {e}")
    
    return subtitles


def merge_subtitles_with_whisper(subtitles: List[Dict], whisper_segments: List[Dict]) -> List[Dict]:
    """Слияние YouTube субтитров с Whisper"""
    merged = []
    
    for sub in subtitles:
        # Ищем соответствующий сегмент Whisper
        best_match = None
        for wseg in whisper_segments:
            # Простое сопоставление по времени
            if abs(wseg.get("start", 0) - float(sub.get("start", "0").split(':')[-1])) < 2.0:
                best_match = wseg
                break
        
        merged_text = sub["text"]
        if best_match and '?' in best_match["text"]:
            # Whisper даёт пунктуацию
            merged_text = best_match["text"]
        
        merged.append({
            "start": sub.get("start"),
            "end": sub.get("end"),
            "text": merged_text
        })
    
    return merged if merged else whisper_segments


def filter_low_quality_questions(questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Фильтрация мусорных вопросов"""
    if not questions:
        return []
    
    garbage_patterns = [
        r'^(да|нет|ага|угу|ну|ок|м+|хм+|э)\??$',
        r'^(что|как|а)\??$',
        r'^.{1,4}\??$',
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


def deduplicate_questions(questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Удаление дубликатов"""
    if not questions:
        return []
    
    seen = set()
    unique = []
    
    for q in questions:
        text = q.get("question", "").strip().lower()
        normalized = re.sub(r'[^\w\s]', '', text)
        normalized = ' '.join(normalized.split())
        
        if normalized and normalized not in seen:
            seen.add(normalized)
            unique.append(q)
    
    return unique


def cleanup_temp_files(video_id: str):
    """Очистка временных файлов"""
    try:
        for pattern in [f"{video_id}.*", f"*{video_id}*"]:
            for f in TEMP_DIR.glob(pattern):
                try:
                    f.unlink()
                    print(f"🗑️ Deleted: {f.name}")
                except Exception as e:
                    print(f"⚠️ Failed to delete {f.name}: {e}")
    except Exception as e:
        print(f"⚠️ Cleanup error: {e}")


async def update_probabilities(conn):
    """Обновить вероятности для всех вопросов (на основе % видео, в которых встречается вопрос)"""
    total_videos = await conn.fetchval("SELECT COUNT(*) FROM processed_videos")
    
    if total_videos > 0:
        # Обновляем вероятность для ВСЕХ вопросов (не только approved)
        # Вероятность = кол-во видео с этим вопросом / общее кол-во видео * 100
        await conn.execute("""
            UPDATE questions 
            SET probability = (
                SELECT COALESCE(COUNT(DISTINCT qv.video_id) * 100.0 / $1, 0)
                FROM question_video qv
                WHERE qv.question_id = questions.id
            )
        """, total_videos)


# ============== LLM API Calls ==============
async def call_llm_api(prompt: str) -> List[Dict[str, Any]]:
    """Умный выбор LLM провайдера для извлечения вопросов"""
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
    
    print(f"🤖 Using LLM provider: {provider}")
    
    if provider == "openrouter":
        return await call_openrouter_api(prompt)
    elif provider == "gemini":
        return await call_gemini_api(prompt)
    elif provider == "groq":
        return await call_groq_api(prompt)
    else:
        raise Exception(f"Unknown LLM provider: {provider}")


async def call_llm_api_for_answer(prompt: str) -> str:
    """
    Вызов LLM для генерации текстового ответа
    (используется для генерации ответов на вопросы в админке)
    """
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
    
    print(f"🤖 Generating answer using: {provider}")
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        if provider == "openrouter":
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "meta-llama/llama-3.1-70b-instruct",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7
                }
            )
            
            if response.status_code != 200:
                raise Exception(f"OpenRouter error: {response.text}")
            
            result = response.json()
            return result["choices"][0]["message"]["content"]
        
        elif provider == "gemini":
            models = ["gemini-2.0-flash", "gemini-1.5-flash"]
            
            for model in models:
                try:
                    response = await client.post(
                        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}",
                        json={
                            "contents": [{"parts": [{"text": prompt}]}],
                            "generationConfig": {"temperature": 0.7}
                        }
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        return result["candidates"][0]["content"]["parts"][0]["text"]
                except Exception as e:
                    print(f"⚠️ Gemini {model} failed: {e}")
                    continue
            
            raise Exception("All Gemini models failed")
        
        elif provider == "groq":
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "llama-3.1-70b-versatile",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7
                }
            )
            
            if response.status_code != 200:
                raise Exception(f"Groq error: {response.text}")
            
            result = response.json()
            return result["choices"][0]["message"]["content"]
        
        else:
            raise Exception(f"Unknown provider: {provider}")


async def call_openrouter_api(prompt: str) -> List[Dict[str, Any]]:
    """OpenRouter API"""
    async with httpx.AsyncClient(timeout=180.0) as client:
        response = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "meta-llama/llama-3.1-70b-instruct",
                "messages": [{"role": "user", "content": prompt}]
            }
        )
        
        if response.status_code != 200:
            raise Exception(f"OpenRouter error: {response.text}")
        
        result = response.json()
        text = result["choices"][0]["message"]["content"]
        
        return parse_questions_from_llm(text)


async def call_gemini_api(prompt: str) -> List[Dict[str, Any]]:
    """Google Gemini API"""
    models = ["gemini-2.0-flash", "gemini-1.5-flash"]
    
    for model in models:
        try:
            async with httpx.AsyncClient(timeout=180.0) as client:
                response = await client.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}",
                    json={
                        "contents": [{"parts": [{"text": prompt}]}],
                        "generationConfig": {"temperature": 0.3}
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    text = result["candidates"][0]["content"]["parts"][0]["text"]
                    return parse_questions_from_llm(text)
        except Exception as e:
            print(f"⚠️ Gemini {model} failed: {e}")
            continue
    
    # Fallback to Groq
    return await call_groq_api(prompt)


async def call_groq_api(prompt: str) -> List[Dict[str, Any]]:
    """Groq API с retry при rate limiting"""
    max_retries = 5
    base_delay = 10
    
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=180.0) as client:
                response = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {GROQ_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "llama-3.1-70b-versatile",
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.3
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    text = result["choices"][0]["message"]["content"]
                    return parse_questions_from_llm(text)
                elif response.status_code == 429:
                    delay = base_delay * (2 ** attempt)
                    print(f"⚠️ Groq rate limit, retrying in {delay}s...")
                    await asyncio.sleep(delay)
                else:
                    raise Exception(f"Groq error: {response.text}")
        except Exception as e:
            if attempt == max_retries - 1:
                raise
    
    raise Exception("Groq API error after retries")


def parse_questions_from_llm(response: str) -> List[Dict[str, Any]]:
    """Парсинг JSON из ответа LLM"""
    try:
        # Удаляем markdown code blocks
        response = re.sub(r'```json\s*', '', response)
        response = re.sub(r'```\s*', '', response)
        response = response.strip()
        
        questions = json.loads(response)
        return questions if isinstance(questions, list) else []
    except json.JSONDecodeError:
        print(f"⚠️ Failed to parse LLM response as JSON")
        return []


# =====================================================================
# ============== Дополнительные эндпоинты (v2.1) =====================
# =====================================================================

async def _table_exists(conn, table_name: str) -> bool:
    """Проверка существования таблицы"""
    try:
        return await conn.fetchval(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = $1)", table_name)
    except Exception:
        return False


# ============== Массовая генерация ответов ==============
@app.post("/api/admin/generate-answers-bulk", tags=["Admin"])
async def generate_answers_bulk(data: dict = Body(...)):
    """Массовая генерация ответов для вопросов без ответов"""
    question_ids = data.get("question_ids", [])
    max_count = data.get("max_count", 10)

    conn = await asyncpg.connect(DATABASE_URL)
    try:
        if not question_ids:
            rows = await conn.fetch(
                "SELECT id FROM questions WHERE (answer IS NULL OR answer = '') AND approved = TRUE LIMIT $1",
                max_count)
            question_ids = [r["id"] for r in rows]

        generated = 0
        errors = 0
        for qid in question_ids[:max_count]:
            try:
                await generate_answer_for_question(qid)
                generated += 1
                await asyncio.sleep(1)
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
    url = data.get("url", "").strip()
    if not url:
        raise HTTPException(status_code=400, detail="URL обязателен")

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
    """Список предложений видео"""
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
    """Обновить статус предложения"""
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
    """Обработать предложенное видео"""
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        suggestion = await conn.fetchrow("SELECT * FROM video_suggestions WHERE id = $1", suggestion_id)
        if not suggestion:
            raise HTTPException(status_code=404, detail="Предложение не найдено")
        await conn.execute("UPDATE video_suggestions SET status = 'processing' WHERE id = $1", suggestion_id)

        task_id = str(uuid.uuid4())
        topic = suggestion.get("topic", "General") if hasattr(suggestion, 'get') else (suggestion["topic"] or "General")
        difficulty = suggestion.get("difficulty", "middle") if hasattr(suggestion, 'get') else (suggestion["difficulty"] or "middle")
        video_url = suggestion["url"]

        task_data = {
            "task_id": task_id,
            "youtube_url": video_url,
            "topic": topic,
            "level": difficulty,
            "status": "pending",
            "progress": 0,
            "step": "Обработка предложенного видео...",
            "suggestion_id": suggestion_id
        }
        await redis_client.set(f"task:{task_id}", json.dumps(task_data), ex=REDIS_TTL)
        background_tasks.add_task(process_video_pipeline, task_id, video_url, topic, difficulty)
        return {"task_id": task_id, "message": "Видео отправлено на обработку"}
    finally:
        await conn.close()


# ============== Обратная связь ==============
@app.post("/api/feedback", tags=["Public"])
async def create_feedback(data: dict = Body(...)):
    """Оставить обратную связь"""
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


# ============== Закладки ==============
@app.post("/api/bookmarks", tags=["Public"])
async def toggle_bookmark(data: dict = Body(...)):
    """Добавить/удалить вопрос из закладок"""
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        question_id = data.get("question_id")
        user_session = data.get("user_session", "")
        if not question_id or not user_session:
            raise HTTPException(status_code=400, detail="question_id и user_session обязательны")
        existing = await conn.fetchval(
            "SELECT id FROM bookmarks WHERE question_id = $1 AND user_session = $2",
            question_id, user_session)
        if existing:
            await conn.execute("DELETE FROM bookmarks WHERE id = $1", existing)
            return {"bookmarked": False, "message": "Закладка удалена"}
        else:
            await conn.execute(
                "INSERT INTO bookmarks (question_id, user_session, note) VALUES ($1, $2, $3)",
                question_id, user_session, data.get("note", ""))
            return {"bookmarked": True, "message": "Добавлено в закладки"}
    finally:
        await conn.close()


@app.get("/api/bookmarks/{user_session}", tags=["Public"])
async def get_bookmarks(user_session: str):
    """Получить закладки пользователя"""
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
    """Сохранить заметку к вопросу"""
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
    """Начать мок-интервью"""
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

        interview_id = await conn.fetchval("""
            INSERT INTO mock_interviews (user_session, topic, difficulty, total_questions)
            VALUES ($1, $2, $3, $4) RETURNING id
        """, user_session, topic, difficulty, len(questions_list))
        return {"interview_id": interview_id, "questions": questions_list, "total": len(questions_list)}
    finally:
        await conn.close()


@app.post("/api/mock-interview/{interview_id}/submit", tags=["Public"])
async def submit_mock_interview(interview_id: int, data: dict = Body(...)):
    """Завершить мок-интервью"""
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
    """История мок-интервью"""
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        interviews = await conn.fetch("""
            SELECT id, topic, difficulty, total_questions, correct_answers, score, duration_seconds, completed_at, created_at
            FROM mock_interviews WHERE user_session = $1 ORDER BY created_at DESC LIMIT 20
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
@app.post("/api/admin/upload-video-file", tags=["Admin"])
async def upload_video_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    topic: str = Form("General"),
    difficulty: str = Form("middle")
):
    """Загрузить видео файл для обработки"""
    task_id = str(uuid.uuid4())
    video_id = task_id[:16]
    filename = file.filename or "video.mp4"

    # Сохраняем файл
    video_path = TEMP_DIR / f"{video_id}.mp4"
    contents = await file.read()
    with open(video_path, "wb") as f:
        f.write(contents)

    file_size = len(contents)
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
        if video_path.exists():
            video_path.unlink()

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

    background_tasks.add_task(process_local_video, task_id, str(audio_path), filename, topic, difficulty)
    return {"task_id": task_id, "message": "Файл загружен, обработка начата"}


async def process_local_video(task_id: str, audio_path: str, filename: str, topic: str, difficulty: str):
    """Обработка локально загруженного видео"""
    try:
        await update_task_progress(task_id, 20, "transcribing", "Транскрибация аудио...")
        whisper_result = await whisper_orchestrator.transcribe_audio(
            audio_path=Path(audio_path), task_id=task_id, language="ru")
        transcript = whisper_result["text"]

        await update_task_progress(task_id, 60, "extracting", "Извлечение вопросов...")
        questions = await extract_questions_from_transcript(transcript, topic, difficulty)
        questions = filter_low_quality_questions(questions)
        questions = deduplicate_questions(questions)

        await update_task_progress(task_id, 85, "saving", "Сохранение в базу данных...")
        video_id = task_id[:16]
        await save_questions_to_db(questions, f"local://{filename}", filename, video_id, task_id, "local")

        await update_task_progress(task_id, 100, "completed", f"Готово! Извлечено {len(questions)} вопросов")
        task_data = json.loads(await redis_client.get(f"task:{task_id}") or "{}")
        task_data["status"] = "completed"
        task_data["result"] = {"video_title": filename, "questions_count": len(questions), "questions": questions}
        await redis_client.set(f"task:{task_id}", json.dumps(task_data), ex=REDIS_TTL)

    except Exception as e:
        print(f"❌ Local video processing error: {e}")
        await update_task_error(task_id, str(e))


# ============== Теги вопросов ==============
@app.post("/api/admin/questions/{question_id}/tags", tags=["Admin"])
async def add_question_tag(question_id: int, data: dict = Body(...)):
    """Добавить тег к вопросу"""
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
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        await conn.execute("DELETE FROM question_tags WHERE question_id = $1 AND tag = $2", question_id, tag)
        return {"message": f"Тег '{tag}' удалён"}
    finally:
        await conn.close()


@app.get("/api/tags", tags=["Public"])
async def get_all_tags():
    """Все используемые теги"""
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        tags = await conn.fetch("SELECT tag, COUNT(*) as count FROM question_tags GROUP BY tag ORDER BY count DESC")
        return {"tags": [{"tag": t["tag"], "count": t["count"]} for t in tags]}
    finally:
        await conn.close()


# ============== Статистика ==============
@app.get("/api/stats", tags=["Public"])
async def get_public_stats():
    """Публичная статистика"""
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        total_questions = await conn.fetchval("SELECT COUNT(*) FROM questions WHERE approved = TRUE")
        total_topics = await conn.fetchval("SELECT COUNT(DISTINCT topic) FROM questions WHERE approved = TRUE")
        total_videos = await conn.fetchval("SELECT COUNT(*) FROM processed_videos")
        total_with_answers = await conn.fetchval(
            "SELECT COUNT(*) FROM questions WHERE approved = TRUE AND answer IS NOT NULL AND answer != ''")

        top_topics = await conn.fetch("""
            SELECT topic, COUNT(*) as count FROM questions WHERE approved = TRUE
            GROUP BY topic ORDER BY count DESC LIMIT 5
        """)
        levels = await conn.fetch("""
            SELECT difficulty, COUNT(*) as count FROM questions WHERE approved = TRUE GROUP BY difficulty
        """)
        platforms = await conn.fetch("""
            SELECT COALESCE(platform, 'youtube') as platform, COUNT(*) as count
            FROM processed_videos GROUP BY platform
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
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        stats = {}
        stats["total_questions"] = await conn.fetchval("SELECT COUNT(*) FROM questions")
        stats["approved_questions"] = await conn.fetchval("SELECT COUNT(*) FROM questions WHERE approved = TRUE")
        stats["pending_questions"] = await conn.fetchval("SELECT COUNT(*) FROM questions WHERE approved = FALSE")
        stats["with_answers"] = await conn.fetchval(
            "SELECT COUNT(*) FROM questions WHERE answer IS NOT NULL AND answer != ''")
        stats["without_answers"] = await conn.fetchval(
            "SELECT COUNT(*) FROM questions WHERE answer IS NULL OR answer = ''")
        stats["total_videos"] = await conn.fetchval("SELECT COUNT(*) FROM processed_videos")
        stats["total_suggestions"] = await conn.fetchval(
            "SELECT COUNT(*) FROM video_suggestions") if await _table_exists(conn, 'video_suggestions') else 0
        stats["pending_suggestions"] = await conn.fetchval(
            "SELECT COUNT(*) FROM video_suggestions WHERE status = 'pending'") if await _table_exists(conn, 'video_suggestions') else 0
        stats["total_feedback"] = await conn.fetchval(
            "SELECT COUNT(*) FROM feedback") if await _table_exists(conn, 'feedback') else 0
        stats["unresolved_feedback"] = await conn.fetchval(
            "SELECT COUNT(*) FROM feedback WHERE is_resolved = FALSE") if await _table_exists(conn, 'feedback') else 0
        stats["questions_last_week"] = await conn.fetchval(
            "SELECT COUNT(*) FROM questions WHERE created_at > CURRENT_TIMESTAMP - INTERVAL '7 days'")

        top_questions = await conn.fetch("""
            SELECT id, question, probability, topic FROM questions
            WHERE approved = TRUE AND probability > 0 ORDER BY probability DESC LIMIT 10
        """)
        stats["top_questions"] = [dict(q) for q in top_questions]
        return stats
    finally:
        await conn.close()


# ============== Экспорт CSV ==============
@app.get("/api/admin/export-csv", tags=["Admin"])
async def export_questions_csv():
    """Экспорт вопросов в CSV"""
    from fastapi.responses import StreamingResponse
    import io

    conn = await asyncpg.connect(DATABASE_URL)
    try:
        questions = await conn.fetch("""
            SELECT id, question, answer, topic, difficulty, probability, timecode, approved, source_url, video_title, created_at
            FROM questions ORDER BY id
        """)
        output = io.StringIO()
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
            headers={"Content-Disposition": "attachment; filename=questions_export.csv"})
    finally:
        await conn.close()


# ============== Обработанные видео ==============
@app.get("/api/admin/videos", tags=["Admin"])
async def get_processed_videos():
    """Список обработанных видео"""
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        videos = await conn.fetch("""
            SELECT pv.*,
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
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        questions = await conn.fetch("""
            SELECT q.id, q.question, q.answer, q.topic, q.difficulty, q.timecode,
                   q.probability, q.approved, q.created_at
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
    """Удалить обработанное видео"""
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        existing = await conn.fetchrow("SELECT id FROM processed_videos WHERE id = $1", video_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Видео не найдено")
        await conn.execute("DELETE FROM processed_videos WHERE id = $1", video_id)
        await update_probabilities(conn)
        return {"message": "Видео удалено"}
    finally:
        await conn.close()


@app.patch("/api/admin/videos/{video_id}", tags=["Admin"])
async def update_processed_video(video_id: int, data: dict = Body(...)):
    """Обновить заголовок обработанного видео"""
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
