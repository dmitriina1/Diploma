"""
Whisper Service v2.0 — Оптимизировано для AMD Ryzen 7, 32GB RAM
================================================================

Изменения:
- Модель: large-v3 (лучшее качество распознавания)
- CPU threads: 10 (оптимально для R7 8 ядер / 16 потоков)
- Compute type: int8 (квантизация для экономии памяти)
- VAD фильтр: включен (пропускает тишину, ускоряет обработку)

Архитектура:
- Каждый воркер обрабатывает ПОЛНОЕ аудио (БЕЗ разделения на части!)
- Модель загружается один раз и остаётся в памяти
- Требования: ~12-14GB RAM на воркер
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import tempfile
import os
import gc
import logging
from typing import List, Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Whisper Service v2.0 (large-v3 optimized)", version="2.0.0")

# Глобальная модель - загружается один раз при старте
whisper_model = None
MODEL_NAME = os.getenv("WHISPER_MODEL", "large-v3")
CPU_THREADS = int(os.getenv("CPU_THREADS", "10"))  # Оптимально для R7


@app.on_event("startup")
async def startup_event():
    """Загрузка faster-whisper модели при старте сервиса"""
    global whisper_model
    from faster_whisper import WhisperModel
    
    logger.info(f"🚀 Starting Whisper Service v2.0...")
    logger.info(f"📦 Loading model '{MODEL_NAME}' with {CPU_THREADS} CPU threads...")
    logger.info(f"💻 Optimized for: AMD Ryzen 7, 32GB RAM")
    
    # Отключаем XET для надежной загрузки через HTTP
    os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "0"
    os.environ["HF_HUB_DISABLE_XET"] = "1"
    
    # faster-whisper с оптимизациями для CPU
    whisper_model = WhisperModel(
        MODEL_NAME,
        device="cpu",
        compute_type="int8",  # int8 квантизация — быстрее и меньше памяти
        cpu_threads=CPU_THREADS,
        download_root="/root/.cache/whisper",
        local_files_only=False
    )
    
    logger.info(f"✅ Whisper {MODEL_NAME} loaded successfully!")
    logger.info(f"   - Compute type: int8 (quantized)")
    logger.info(f"   - CPU threads: {CPU_THREADS}")
    logger.info(f"   - VAD filter: enabled")


@app.get("/health")
async def health():
    """Проверка здоровья сервиса"""
    return {
        "status": "healthy",
        "model_loaded": whisper_model is not None,
        "model_name": MODEL_NAME,
        "engine": "faster-whisper",
        "compute_type": "int8",
        "cpu_threads": CPU_THREADS,
        "architecture": "per-task (no chunking)"
    }


class TranscribeResponse(BaseModel):
    text: str
    segments: list
    language: str


@app.post("/transcribe", response_model=TranscribeResponse)
async def transcribe(file: UploadFile = File(...), language: str = "ru"):
    """
    Транскрибация аудиофайла (ПОЛНОЕ аудио, БЕЗ разделения!)
    
    - **file**: Аудиофайл (mp3, wav, m4a и др.)
    - **language**: Язык аудио (по умолчанию 'ru')
    """
    if whisper_model is None:
        raise HTTPException(status_code=503, detail="Whisper model not loaded")
    
    # Сохраняем файл во временную директорию
    suffix = os.path.splitext(file.filename)[1] if file.filename else ".mp3"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        file_size_mb = len(content) / (1024 * 1024)
        logger.info(f"🎤 Transcribing {file.filename} ({file_size_mb:.1f} MB) with {MODEL_NAME}...")
        
        # faster-whisper транскрибация с оптимизациями
        segments_generator, info = whisper_model.transcribe(
            tmp_path,
            language=language,
            task="transcribe",
            beam_size=5,  # Баланс скорость/качество
            vad_filter=True,  # Voice Activity Detection — пропускает тишину (ускоряет!)
            vad_parameters=dict(
                min_silence_duration_ms=500,  # Минимальная тишина для пропуска
                speech_pad_ms=200  # Padding вокруг речи
            ),
            condition_on_previous_text=True,  # Лучше для длинных файлов
            compression_ratio_threshold=2.4,
            log_prob_threshold=-1.0,
            no_speech_threshold=0.6
        )
        
        # Собираем сегменты из генератора
        segments = []
        full_text_parts = []
        
        for seg in segments_generator:
            segments.append({
                "start": seg.start,
                "end": seg.end,
                "text": seg.text.strip()
            })
            full_text_parts.append(seg.text.strip())
        
        full_text = " ".join(full_text_parts)
        
        logger.info(f"✅ Transcription complete: {len(segments)} segments, {len(full_text)} chars")
        logger.info(f"📊 Detected language: {info.language} (prob: {info.language_probability:.2f})")
        
        # Очистка памяти после обработки
        gc.collect()
        
        return TranscribeResponse(
            text=full_text,
            segments=segments,
            language=info.language
        )
    
    except Exception as e:
        logger.error(f"❌ Transcription error: {e}")
        gc.collect()
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        # Удаляем временный файл
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@app.post("/transcribe-path")
async def transcribe_from_path(audio_path: str, language: str = "ru"):
    """
    Транскрибация по пути к файлу (для внутреннего использования)
    
    ВАЖНО: Транскрибируется ПОЛНОЕ аудио целиком!
    Никакого разделения на части!
    
    - **audio_path**: Путь к аудиофайлу в shared volume
    - **language**: Язык аудио
    """
    if whisper_model is None:
        raise HTTPException(status_code=503, detail="Whisper model not loaded")
    
    if not os.path.exists(audio_path):
        raise HTTPException(status_code=404, detail=f"File not found: {audio_path}")
    
    try:
        file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)
        logger.info(f"🎤 Transcribing FULL audio: {audio_path} ({file_size_mb:.1f} MB)")
        logger.info(f"   Model: {MODEL_NAME}, Threads: {CPU_THREADS}")
        
        # Транскрибация ПОЛНОГО аудио
        segments_generator, info = whisper_model.transcribe(
            audio_path,
            language=language,
            task="transcribe",
            beam_size=5,
            vad_filter=True,
            vad_parameters=dict(
                min_silence_duration_ms=500,
                speech_pad_ms=200
            ),
            condition_on_previous_text=True,
            compression_ratio_threshold=2.4,
            log_prob_threshold=-1.0,
            no_speech_threshold=0.6
        )
        
        segments = []
        full_text_parts = []
        
        for seg in segments_generator:
            segments.append({
                "start": seg.start,
                "end": seg.end,
                "text": seg.text.strip()
            })
            full_text_parts.append(seg.text.strip())
        
        full_text = " ".join(full_text_parts)
        
        logger.info(f"✅ Full audio transcription complete!")
        logger.info(f"   Segments: {len(segments)}, Characters: {len(full_text)}")
        logger.info(f"   Language: {info.language} (prob: {info.language_probability:.2f})")
        
        gc.collect()
        
        return {
            "text": full_text,
            "segments": segments,
            "language": info.language
        }
    
    except Exception as e:
        logger.error(f"❌ Transcription error: {e}")
        gc.collect()
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
