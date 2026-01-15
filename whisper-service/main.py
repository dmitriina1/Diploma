"""
Whisper Service — отдельный микросервис для транскрибации
Модель загружается один раз и остаётся в памяти
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import whisper
import tempfile
import os
import gc
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Whisper Service", version="1.0.0")

# Глобальная модель - загружается один раз при старте
whisper_model = None
MODEL_NAME = os.getenv("WHISPER_MODEL", "medium")


@app.on_event("startup")
async def startup_event():
    """Загрузка Whisper модели при старте сервиса"""
    global whisper_model
    logger.info(f"🚀 Starting Whisper Service...")
    logger.info(f"📦 Loading Whisper model ({MODEL_NAME})...")
    whisper_model = whisper.load_model(MODEL_NAME)
    logger.info(f"✅ Whisper model loaded!")


@app.get("/health")
async def health():
    """Проверка здоровья сервиса"""
    return {
        "status": "healthy",
        "model_loaded": whisper_model is not None,
        "model_name": MODEL_NAME
    }


class TranscribeResponse(BaseModel):
    text: str
    segments: list
    language: str


@app.post("/transcribe", response_model=TranscribeResponse)
async def transcribe(file: UploadFile = File(...), language: str = "ru"):
    """
    Транскрибация аудиофайла
    
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
        logger.info(f"🎤 Transcribing {file.filename} ({file_size_mb:.1f} MB)...")
        
        # Транскрибация с оптимизациями для длинных файлов
        result = whisper_model.transcribe(
            tmp_path,
            language=language,
            task="transcribe",
            verbose=False,
            fp16=False,  # CPU не поддерживает fp16
            condition_on_previous_text=True  # Лучше для длинных файлов
        )
        
        # Формируем сегменты
        segments = []
        for seg in result.get("segments", []):
            segments.append({
                "start": seg["start"],
                "end": seg["end"],
                "text": seg["text"].strip()
            })
        
        logger.info(f"✅ Transcription complete: {len(segments)} segments, {len(result['text'])} chars")
        
        # Очистка памяти после обработки длинных файлов
        gc.collect()
        
        return TranscribeResponse(
            text=result["text"],
            segments=segments,
            language=result.get("language", language)
        )
    
    except Exception as e:
        logger.error(f"❌ Transcription error: {e}")
        gc.collect()  # Очистка памяти даже при ошибке
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        # Удаляем временный файл
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@app.post("/transcribe-path")
async def transcribe_from_path(audio_path: str, language: str = "ru"):
    """
    Транскрибация по пути к файлу (для внутреннего использования)
    
    - **audio_path**: Путь к аудиофайлу в shared volume
    - **language**: Язык аудио
    """
    if whisper_model is None:
        raise HTTPException(status_code=503, detail="Whisper model not loaded")
    
    if not os.path.exists(audio_path):
        raise HTTPException(status_code=404, detail=f"File not found: {audio_path}")
    
    try:
        file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)
        logger.info(f"🎤 Transcribing {audio_path} ({file_size_mb:.1f} MB)...")
        
        result = whisper_model.transcribe(
            audio_path,
            language=language,
            task="transcribe",
            verbose=False,
            fp16=False,
            condition_on_previous_text=True
        )
        
        segments = []
        for seg in result.get("segments", []):
            segments.append({
                "start": seg["start"],
                "end": seg["end"],
                "text": seg["text"].strip()
            })
        
        logger.info(f"✅ Transcription complete: {len(segments)} segments, {len(result['text'])} chars")
        
        # Очистка памяти
        gc.collect()
        
        return {
            "text": result["text"],
            "segments": segments,
            "language": result.get("language", language)
        }
    
    except Exception as e:
        logger.error(f"❌ Transcription error: {e}")
        gc.collect()
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
