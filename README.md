# 🎯 Interview Prep Platform

**Платформа для автоматизированной подготовки к IT-собеседованиям.**  
Анализирует видео с собеседованиями на русском языке, извлекает вопросы и ответы с помощью AI.

---

## Как это работает

```
Видео URL → yt-dlp → Аудио → Whisper large-v3 → Транскрипт → LLM → Вопросы → PostgreSQL → Vue.js UI
```

1. Загрузка видео с YouTube / VK / Rutube / OK.ru / Dailymotion / Vimeo  
2. Транскрибация речи моделью faster-whisper large-v3-turbo  
3. Извлечение вопросов и ответов через LLM (OpenRouter / Gemini / Groq)  
4. Модерация, хранение и отображение через веб-интерфейс  

---

## Архитектура

| Сервис | Порт | Описание |
|--------|------|----------|
| Frontend | 3000 | Vue 3 + PrimeVue |
| Backend | 8000 | FastAPI REST API (55 эндпоинтов) |
| Whisper | 8001 | faster-whisper large-v3-turbo |
| PostgreSQL | 5432 | Основная БД (19 таблиц) |
| Redis | 6379 | Кэш задач и FAISS-эмбеддингов |

---

## Возможности

**Обработка видео:** мультиплатформенная загрузка, автоматический pipeline, мониторинг задач в реальном времени (WebSocket)

**Подготовка:** 26 IT-профессий, фильтрация по технологии/сложности, семантический поиск похожих вопросов (FAISS + sentence-transformers), тренажёр SM-2 (интервальное повторение), mock-собеседования

**Аналитика:** навыки из вакансий HH.ru (214 навыков, пагинация), тестовые задания от компаний, расчёт вероятности вопроса на собеседовании

**UGC:** пользовательские ответы с голосованием, закладки, заметки, предложение видео

**Админ-панель:** модерация вопросов, генерация ответов через LLM, управление видео, статистика, экспорт (JSON/CSV)

---

## Быстрый старт

### Требования

- Docker + Docker Compose  
- 8+ GB RAM (Whisper large-v3-turbo)  
- API-ключ одного из LLM-провайдеров (OpenRouter / Gemini / Groq)

### Запуск

```bash
# 1. Клонировать
git clone <repo-url>
cd Diploma

# 2. Настроить LLM-ключи (любой один из трёх)
#    В docker-compose.yml → backend → environment:
#    - OPENROUTER_API_KEY=sk-or-...
#    - GEMINI_API_KEY=AI...
#    - GROQ_API_KEY=gsk_...

# 3. Запустить
docker-compose up -d --build

# 4. Дождаться загрузки модели Whisper (~3 ГБ при первом запуске)
docker logs -f diploma-whisper-worker
```

### Доступ

| URL | Описание |
|-----|----------|
| http://localhost:3000 | Веб-интерфейс |
| http://localhost:3000/admin | Панель администратора |
| http://localhost:8000/docs | Swagger API документация |

---

## Технологический стек

**Backend:** Python 3.11, FastAPI, asyncpg, yt-dlp, sentence-transformers, FAISS  
**Frontend:** Vue 3, Vite, PrimeVue (lara-dark-purple), Pinia, Axios  
**AI/ML:** faster-whisper (CTranslate2), all-MiniLM-L6-v2, LLM (GPT-4 / Gemini / Llama-3.1)  
**Инфраструктура:** Docker Compose, PostgreSQL 15, Redis 7, nginx  

---

## Структура проекта

```
├── backend/          # FastAPI сервер (main_new.py — 3200+ строк)
├── frontend-vue/     # Vue 3 приложение (9 views, 12 components)
├── whisper-service/  # Сервис транскрибации (faster-whisper)
├── scripts/          # SQL миграции
├── nginx/            # Конфигурация nginx
└── docker-compose.yml
```

---

## Команды

```bash
# Запуск
docker-compose up -d

# Пересборка одного сервиса
docker-compose up -d --build backend

# Логи
docker logs -f diploma-backend

# Остановка
docker-compose down

# Проверка статуса
docker ps --format "table {{.Names}}\t{{.Status}}"
```

---

## Лицензия

MIT
