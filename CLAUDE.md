# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

IT interview preparation platform that processes video interviews to extract Q&A pairs. Videos are downloaded, transcribed via Whisper, and Q&A is extracted via LLM. Admins moderate content; users browse questions, use a trainer, and take mock interviews.

## Architecture

6-service Docker Compose stack:

```
Frontend (Vue 3, :3000) → Backend FastAPI (:8000) → PostgreSQL (:5432)
                                  ↓                → Redis (:6379)
                         Nginx LB (:8001)
                                  ↓
                         Whisper Service (:8000) [CPU or GPU variant]
```

**Data flow:** URL submitted → audio downloaded (yt-dlp) → transcribed (faster-whisper large-v3-turbo) → Q&A extracted (LLM via OpenRouter/Gemini/Groq/Ollama) → pending moderation → admin approves → public interface.

**Active backend entry point:** `backend/main_new.py` (2595 lines). `backend/main.py` is legacy.

**Active Whisper entry point:** `whisper-service/main_new.py`. `whisper-service/main.py` is legacy.

**Frontend:** `frontend-vue/` is the active Vue 3 app. `frontend/` is a deprecated React version, ignore it.

## Commands

### Run everything
```bash
docker-compose up -d                            # standard
docker-compose -f docker-compose.cpu.yml up -d  # CPU-optimized Whisper
docker-compose -f docker-compose.gpu.yml up -d  # GPU-optimized Whisper
docker-compose logs -f backend
docker-compose down
```

### Frontend development
```bash
cd frontend-vue
npm install
npm run dev      # Vite dev server on port 3000
npm run build
npm run preview
```

### Backend development
```bash
cd backend
pip install -r requirements.txt
uvicorn main_new:app --host 0.0.0.0 --port 8000 --reload
```

### Whisper service development
```bash
cd whisper-service
pip install -r requirements.txt
uvicorn main_new:app --host 0.0.0.0 --port 8000
```

### Database
```bash
docker-compose exec postgres psql -U diploma -d interview_prep
# Migrations: scripts/init-db.sql, scripts/migration_v2.sql, scripts/migration_add_platform.sql
```

## Key Environment Variables

Set in `.env` or directly in `docker-compose.yml`. LLM provider is auto-detected from available keys:

```
OPENROUTER_API_KEY=
GEMINI_API_KEY=
GROQ_API_KEY=
LLM_PROVIDER=auto          # or openrouter, gemini, groq, ollama
WHISPER_MODEL=large-v3-turbo
MAX_WHISPER_WORKERS=2
CPU_THREADS=10             # tune to CPU core count
```

## Code Structure

### Backend (`backend/main_new.py`)
- `WhisperWorker` / `WhisperOrchestrator` — manages up to 2 concurrent transcription tasks
- `ConnectionManager` — WebSocket connections for real-time progress
- `process_video_pipeline()` — main async pipeline (download → transcribe → extract → save)
- `extract_questions_from_transcript()` — LLM Q&A extraction
- `update_probabilities()` — calculates per-question interview likelihood %

### Frontend (`frontend-vue/src/`)
- `api/client.js` — Axios client with 30+ typed endpoints
- `views/Admin.vue` — admin panel: video upload, task monitoring, moderation
- `views/Trainer.vue` / `MockInterview.vue` — user-facing interview simulation
- `components/QuestionDetailDialog.vue` — full editor for questions (text, answer, tags, merge)
- `router/index.js` — 7 client-side routes
- `store/index.js` — Pinia global state

### Database schema (PostgreSQL)
Core tables: `questions`, `processed_videos`, `processing_tasks` (UUID + status + progress), `question_video` (M2M), `bookmarks`, `user_notes`, `feedback`, `video_suggestions`.

## Supported Video Platforms
YouTube, VK, Rutube, OK.ru, Dailymotion, Vimeo — all via yt-dlp.

## Nginx Load Balancer
`nginx/nginx.conf` balances Whisper replicas using `least_conn`. Timeouts are 30 minutes; max body 500 MB for audio.
