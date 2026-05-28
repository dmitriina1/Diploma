import os
from pathlib import Path
from typing import List


def _parse_origins(value: str) -> List[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def _get_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://diploma:diploma123@localhost:5432/interview_prep"
)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
WHISPER_BASE_URL = os.getenv("WHISPER_BASE_URL", "http://whisper-worker")
MAX_WHISPER_WORKERS = int(os.getenv("MAX_WHISPER_WORKERS", "2"))
WORKER_IDLE_TIMEOUT = int(os.getenv("WORKER_IDLE_TIMEOUT", "600"))
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "auto")
TEMP_DIR = Path("/app/temp")
TEMP_DIR.mkdir(exist_ok=True)
REDIS_TTL = 86400

APP_ENV = os.getenv("APP_ENV", "development").lower()
IS_PRODUCTION = APP_ENV in {"production", "prod"}
AUTO_MIGRATE_DB = (
    os.getenv("AUTO_MIGRATE_DB", "true" if not IS_PRODUCTION else "false").lower()
    == "true"
)
DB_POOL_MIN_SIZE = int(os.getenv("DB_POOL_MIN_SIZE", "2"))
DB_POOL_MAX_SIZE = int(os.getenv("DB_POOL_MAX_SIZE", "20"))

DEFAULT_CORS = "http://localhost:3000,http://localhost:3001,http://localhost:3010,http://localhost:3020"
CORS_ALLOW_ORIGINS = _parse_origins(os.getenv("CORS_ALLOW_ORIGINS", DEFAULT_CORS))

HH_SYNC_ENABLED = _get_bool("HH_SYNC_ENABLED", True)
HH_SYNC_INTERVAL_HOURS = int(os.getenv("HH_SYNC_INTERVAL_HOURS", "24"))
HH_SYNC_STARTUP_DELAY_SECONDS = int(os.getenv("HH_SYNC_STARTUP_DELAY_SECONDS", "20"))
HH_SYNC_MAX_PAGES = int(os.getenv("HH_SYNC_MAX_PAGES", "3"))
HH_SYNC_PER_PAGE = int(os.getenv("HH_SYNC_PER_PAGE", "50"))
HH_SYNC_MAX_VACANCIES_PER_PROF = int(os.getenv("HH_SYNC_MAX_VACANCIES_PER_PROF", "150"))
HH_SYNC_TOP_SKILLS = int(os.getenv("HH_SYNC_TOP_SKILLS", "30"))
HH_SYNC_HTTP_CONCURRENCY = int(os.getenv("HH_SYNC_HTTP_CONCURRENCY", "8"))
HH_SYNC_MIN_VACANCIES = int(os.getenv("HH_SYNC_MIN_VACANCIES", "15"))
