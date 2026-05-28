# InterviewHub: инженерный контекст проекта

Дата обновления: 2026-04-19
Репозиторий: C:\Users\Lenovo\Desktop\Diploma
Статус: активная разработка (магистерская диссертация)

## 1) Что это за система

InterviewHub - full-stack платформа подготовки к IT-собеседованиям.

Ключевой сценарий:

1. Пользователь отправляет ссылку на видео собеседования.
2. Сервис скачивает аудио и субтитры (yt-dlp).
3. Whisper транскрибирует аудио.
4. LLM извлекает вопросы.
5. Вопросы сохраняются в PostgreSQL и доступны в UI.

Дополнительно:

- SM-2 тренажер (spaced repetition)
- mock-собеседования
- UGC-ответы пользователей с голосованием
- HH-аналитика навыков
- админ-панель с модерацией и генерацией ответов

## 2) Актуальная архитектура (монорепо)

Проект содержит несколько фронтенд-вариантов и общий backend:

- backend/ - FastAPI API + пайплайн обработки видео
- whisper-service/ - microservice транскрибации (faster-whisper)
- frontend-new/ - основной новый Vue UI (порт 3000)
- frontend-vue/ - legacy Vue + PrimeVue (порт 3001)
- frontend-new-v2/ - альтернативный фронт (порт 3010)
- PrimeVue/ - отдельная PrimeVue-сборка (порт 3020)
- scripts/ - SQL миграции и служебные SQL

Инфраструктура в docker-compose.yml:

- postgres (5432)
- redis (6379)
- whisper-worker (8001 -> 8000 в контейнере)
- backend (8000)
- frontend variants (3000/3001/3010/3020)
- metabase (3035)

## 3) Критические backend-файлы

- backend/main_new.py - основной FastAPI app и пайплайн (process_video_pipeline)
- backend/video_downloader.py - загрузка видео/аудио + субтитры через yt-dlp
- backend/services/whisper_orchestrator.py - оркестрация Whisper worker'ов
- backend/services/task_runtime.py - очередь задач
- backend/services/ws_manager.py - WebSocket прогресс
- backend/core/config.py - env-конфиг

Маршруты:

- backend/api/routes/processing.py - API запуска обработки видео
- backend/api/routes/public.py - публичные endpoint'ы
- backend/api/routes/admin.py - админ endpoint'ы
- backend/api/routes/auth.py - авторизация

## 4) База данных (high-level)

Основные сущности:

- questions, processed_videos, question_video, question_timecodes
- processing_tasks, uploaded_videos
- users, bookmarks, user_notes, user_answers, answer_votes
- sr_cards, mock_interviews
- professions, test_assignments
- hh_skills, hh_sync_runs

SQL-файлы:

- scripts/init-db.sql
- scripts/migration_v2.sql
- scripts/migration_v3.sql
- scripts/migration_v3_update.sql
- scripts/migration_v4_hh_sources.sql
- scripts/migration_v5_interview_chatbot.sql
- scripts/migration_v6_metabase_page_analytics.sql

## 5) Пайплайн обработки видео

Базовый флоу в backend/main_new.py -> process_video_pipeline:

1. download_video_audio(video_url, task_id)
2. whisper_orchestrator.transcribe_audio(...)
3. extract_questions_from_transcript(...)
4. deduplicate/filter + save_questions_to_db(...)
5. прогресс и статусы в Redis + WebSocket

Состояния задачи в UI:

- pending -> downloading -> downloaded -> transcribing -> transcribed -> extracting -> extracted -> saving -> completed
- при ошибке: error + текст причины

## 6) YouTube/yt-dlp runbook (ВАЖНО)

### 6.1 Симптом

Ошибка вида:

Failed to download video from youtube: ERROR: [youtube] <id>: Requested format is not available

### 6.2 Что изменено в проекте

Файл: backend/video_downloader.py

Сделано:

1. Добавлены fallback-стратегии форматов для YouTube (последовательные попытки):
   - bestaudio/best
   - best[acodec!=none][height<=720]/best[acodec!=none]/best
   - worstaudio/worst
2. Включен retry по стратегиям при yt_dlp DownloadError.
3. Улучшены таймауты и retries (socket_timeout/retries/fragment_retries).
4. Добавлен geo_bypass и более понятные пользовательские ошибки.
5. Субтитры загружаются в RU-only режиме для снижения риска 429/anti-bot ошибок при скачивании.

Результат: при недоступности preferred формата система не падает сразу, а пробует следующий формат.

### 6.3 Почему это нужно

YouTube регулярно меняет availability форматов (region, age, client-specific ограничения). Один format selector недостаточен. Для стабильности нужна стратегия с несколькими попытками.

### 6.4 Быстрая диагностика

1. Проверить версию yt-dlp в контейнере backend:
   docker compose exec backend python -c "import yt_dlp; print(yt_dlp.version.__version__)"
2. Проверить доступность видео:
   docker compose exec backend yt-dlp --skip-download https://www.youtube.com/watch?v=QI-bXKC2mvU
3. Проверить backend logs:
   docker logs -f diploma-backend
4. Если упирается в anti-bot/private/geo - повторить позже или использовать cookies.

## 7) Быстрый старт разработки

1. Запуск всех сервисов:
   docker compose up -d --build

2. Проверка health:
   - Backend: http://localhost:8000/health
   - Whisper: http://localhost:8001/health

3. UI:
   - http://localhost:3000 (frontend-new)
   - http://localhost:3001 (frontend-vue legacy)
   - http://localhost:3010 (frontend-new-v2)
   - http://localhost:3020 (PrimeVue)

4. Swagger:
   - http://localhost:8000/docs

## 8) Переменные окружения (минимум)

Файл: .env

Обязательные ключи для LLM:

- OPENROUTER_API_KEY или GEMINI_API_KEY или GROQ_API_KEY
- LLM_PROVIDER=auto|openrouter|gemini|groq

Backend:

- DATABASE_URL
- REDIS_URL
- WHISPER_BASE_URL
- JWT_SECRET_KEY
- CORS_ALLOW_ORIGINS
- AUTO_MIGRATE_DB
- YTDLP_COOKIE_FILE (optional, path to cookies.txt for restricted YouTube videos)

## 9) Известные продуктовые проблемы (UI)

Текущий список для доработки:

1. Home page: слабая информационная плотность и UX.
2. Вопросы: текст фильтров не помещается в кнопки.
3. Тренажер: артефакты обратной стороны при flip карточки.
4. Задания: нужен более удобный UI.
5. HH навыки:
   - добавить переключение источников (skills/description/title)
   - добавить фильтры-галочки по источнику

## 10) Операционные подсказки

1. Для тяжелых видео сначала проверять download-only стадию.
2. Если задача зависает на transcribing, смотреть whisper-worker logs.
3. Если падает LLM extraction, проверить LLM ключ и rate limits.
4. Для локальной отладки backend лучше запускать через docker compose (одинаковая среда).

## 11) Приоритеты ближайших улучшений

1. Роадмапы подготовки по уровням (junior/middle/senior).
2. Interview chatbot (LangChain/FAISS + RAG по базе вопросов).
3. Прогресс-дашборд и персональные метрики подготовки.
4. Расширение аналитики HH и company-specific контента.

## 12) Контрольный кейс (YouTube)

Проблемный URL:

https://www.youtube.com/watch?v=QI-bXKC2mvU

Ожидаемое поведение после фикса:

1. Загрузка не падает на первой же ошибке формата.
2. Система перебирает fallback-форматы.
3. На выходе создается mp3 и запускается следующая стадия pipeline.
