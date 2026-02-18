"""
Whisper Service — Универсальный микросервис для транскрибации
==============================================================
Использует faster-whisper (CTranslate2) — в 4-6x быстрее OpenAI Whisper!
Поддерживает CPU (int8) и NVIDIA GPU (float16/int8_float16).
Модель загружается один раз и остаётся в памяти.

Environment Variables:
  WHISPER_MODEL    — модель (large-v3, large-v3-turbo, medium, small)
  DEVICE           — устройство (cpu | cuda | auto)
  COMPUTE_TYPE     — тип вычислений (int8, float16, int8_float16, float32, auto)
  CPU_THREADS      — потоки CPU (только для CPU mode)
  BEAM_SIZE        — beam size для декодирования (1-10, меньше = быстрее)
  VAD_ENABLED      — VAD фильтр (true/false, пропускает тишину)
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import tempfile
import os
import gc
import time
import logging
from typing import List, Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Whisper Service (faster-whisper)", version="3.0.0")

# ============== Конфигурация ==============
whisper_model = None
MODEL_NAME = os.getenv("WHISPER_MODEL", "large-v3-turbo")
DEVICE = os.getenv("DEVICE", "auto")
COMPUTE_TYPE = os.getenv("COMPUTE_TYPE", "auto")
CPU_THREADS = int(os.getenv("CPU_THREADS", "8"))
BEAM_SIZE = int(os.getenv("BEAM_SIZE", "3"))
VAD_ENABLED = os.getenv("VAD_ENABLED", "true").lower() == "true"

ACTIVE_DEVICE = None
ACTIVE_COMPUTE_TYPE = None


def detect_device() -> str:
    """Автоопределение устройства"""
    if DEVICE != "auto":
        return DEVICE
    try:
        import ctranslate2
        if "cuda" in ctranslate2.get_supported_compute_types("cuda"):
            logger.info("🎮 NVIDIA GPU detected — using CUDA")
            return "cuda"
    except Exception:
        pass
    logger.info("💻 No GPU found — using CPU")
    return "cpu"


def detect_compute_type(device: str) -> str:
    """Автоопределение типа вычислений"""
    if COMPUTE_TYPE != "auto":
        return COMPUTE_TYPE
    return "float16" if device == "cuda" else "int8"


@app.on_event("startup")
async def startup_event():
    """Загрузка faster-whisper модели при старте"""
    global whisper_model, ACTIVE_DEVICE, ACTIVE_COMPUTE_TYPE
    from faster_whisper import WhisperModel

    ACTIVE_DEVICE = detect_device()
    ACTIVE_COMPUTE_TYPE = detect_compute_type(ACTIVE_DEVICE)

    logger.info("🚀 Starting Whisper Service v3.0...")
    logger.info(f"📦 Model: {MODEL_NAME}")
    logger.info(f"💻 Device: {ACTIVE_DEVICE}")
    logger.info(f"⚡ Compute type: {ACTIVE_COMPUTE_TYPE}")
    if ACTIVE_DEVICE == "cpu":
        logger.info(f"🧵 CPU threads: {CPU_THREADS}")
    logger.info(f"🔍 Beam size: {BEAM_SIZE}")
    logger.info(f"🎤 VAD filter: {'enabled' if VAD_ENABLED else 'disabled'}")

    os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "0"
    os.environ["HF_HUB_DISABLE_XET"] = "1"
    os.environ["HF_HUB_DOWNLOAD_TIMEOUT"] = "1800"

    model_kwargs = {
        "model_size_or_path": MODEL_NAME,
        "device": ACTIVE_DEVICE,
        "compute_type": ACTIVE_COMPUTE_TYPE,
        "download_root": "/root/.cache/whisper",
    }
    if ACTIVE_DEVICE == "cpu":
        model_kwargs["cpu_threads"] = CPU_THREADS

    # Сначала пробуем из кэша (без интернета), потом с ретраями
    cache_path = f"/root/.cache/whisper/models--*{MODEL_NAME}*"
    import glob
    has_cache = len(glob.glob(cache_path.replace("*", "*"))) > 0

    if has_cache:
        logger.info("📦 Модель найдена в кэше — загрузка без интернета")
        model_kwargs["local_files_only"] = True
        try:
            whisper_model = WhisperModel(**model_kwargs)
            logger.info(f"✅ Whisper {MODEL_NAME} loaded from cache on {ACTIVE_DEVICE} ({ACTIVE_COMPUTE_TYPE})!")
            return
        except Exception as e:
            logger.warning(f"⚠️ Не удалось загрузить из кэша: {e}, пробуем скачать...")
            model_kwargs["local_files_only"] = False

    # Загрузка с ретраями
    MAX_RETRIES = 3
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info(f"⬇️ Скачивание модели {MODEL_NAME}... (попытка {attempt}/{MAX_RETRIES})")
            model_kwargs["local_files_only"] = False
            whisper_model = WhisperModel(**model_kwargs)
            logger.info(f"✅ Whisper {MODEL_NAME} loaded on {ACTIVE_DEVICE} ({ACTIVE_COMPUTE_TYPE})!")
            return
        except Exception as e:
            logger.error(f"❌ Попытка {attempt}/{MAX_RETRIES} не удалась: {e}")
            if attempt < MAX_RETRIES:
                wait = 10 * attempt
                logger.info(f"⏳ Ждём {wait} сек перед повтором...")
                import asyncio
                await asyncio.sleep(wait)
            else:
                logger.critical(f"💀 Не удалось загрузить модель после {MAX_RETRIES} попыток!")
                raise RuntimeError(f"Failed to load whisper model after {MAX_RETRIES} attempts: {e}")


@app.get("/health")
async def health():
    """Проверка здоровья сервиса"""
    return {
        "status": "healthy",
        "model_loaded": whisper_model is not None,
        "model_name": MODEL_NAME,
        "engine": "faster-whisper",
        "device": ACTIVE_DEVICE or "unknown",
        "compute_type": ACTIVE_COMPUTE_TYPE or "unknown",
        "cpu_threads": CPU_THREADS if (ACTIVE_DEVICE or "cpu") == "cpu" else None,
        "beam_size": BEAM_SIZE,
        "vad_enabled": VAD_ENABLED,
    }


class TranscribeResponse(BaseModel):
    text: str
    segments: list
    language: str


def _build_transcribe_kwargs(language: str) -> dict:
    """Собрать оптимальные параметры транскрибации"""
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


def _collect_segments(segments_generator):
    """Собрать сегменты из генератора faster-whisper"""
    segments = []
    full_text_parts = []
    for seg in segments_generator:
        segments.append({
            "start": seg.start,
            "end": seg.end,
            "text": seg.text.strip(),
        })
        full_text_parts.append(seg.text.strip())
    return segments, " ".join(full_text_parts)


@app.post("/transcribe", response_model=TranscribeResponse)
async def transcribe(file: UploadFile = File(...), language: str = "ru"):
    """
    Транскрибация аудиофайла.

    - **file**: Аудиофайл (mp3, wav, m4a и др.)
    - **language**: Язык аудио (по умолчанию 'ru')
    """
    if whisper_model is None:
        raise HTTPException(status_code=503, detail="Whisper model not loaded")

    suffix = os.path.splitext(file.filename)[1] if file.filename else ".mp3"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        file_size_mb = len(content) / (1024 * 1024)
        logger.info(f"🎤 Transcribing {file.filename} ({file_size_mb:.1f} MB)...")

        t0 = time.time()
        seg_gen, info = whisper_model.transcribe(tmp_path, **_build_transcribe_kwargs(language))
        segments, full_text = _collect_segments(seg_gen)
        elapsed = time.time() - t0

        logger.info(f"✅ Done in {elapsed:.1f}s — {len(segments)} segments, {len(full_text)} chars")
        logger.info(f"📊 Language: {info.language} (prob: {info.language_probability:.2f})")
        gc.collect()

        return TranscribeResponse(text=full_text, segments=segments, language=info.language)
    except Exception as e:
        logger.error(f"❌ Transcription error: {e}")
        gc.collect()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@app.post("/transcribe-path")
async def transcribe_from_path(audio_path: str, language: str = "ru"):
    """
    Транскрибация по пути к файлу (для shared volume).

    - **audio_path**: Путь к аудиофайлу
    - **language**: Язык аудио
    """
    if whisper_model is None:
        raise HTTPException(status_code=503, detail="Whisper model not loaded")

    if not os.path.exists(audio_path):
        raise HTTPException(status_code=404, detail=f"File not found: {audio_path}")

    try:
        file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)
        logger.info(f"🎤 Transcribing {audio_path} ({file_size_mb:.1f} MB)...")

        t0 = time.time()
        seg_gen, info = whisper_model.transcribe(audio_path, **_build_transcribe_kwargs(language))
        segments, full_text = _collect_segments(seg_gen)
        elapsed = time.time() - t0

        logger.info(f"✅ Done in {elapsed:.1f}s — {len(segments)} segments, {len(full_text)} chars")
        gc.collect()

        return {"text": full_text, "segments": segments, "language": info.language}
    except Exception as e:
        logger.error(f"❌ Transcription error: {e}")
        gc.collect()
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
