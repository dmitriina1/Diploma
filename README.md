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
| **Frontend NEW** | 3000 | Vue 3 + Custom CSS (новый дизайн, без PrimeVue) |
| **Frontend OLD** | 3001 | Vue 3 + PrimeVue (legacy, для сравнения) |
| Backend | 8000 | FastAPI REST API (55+ эндпоинтов) |
| Whisper | 8001 | faster-whisper large-v3-turbo |
| PostgreSQL | 5432 | Основная БД (19 таблиц) |
| Redis | 6379 | Кэш задач и FAISS-эмбеддингов |

Оба фронтенда работают параллельно и используют один и тот же бэкенд (API на порту 8000).

---

## Возможности

**Обработка видео:** мультиплатформенная загрузка (6 платформ), автоматический pipeline, мониторинг задач в реальном времени (WebSocket), загрузка файлов

**Подготовка:** 26 IT-профессий, фильтрация по технологии/сложности, семантический поиск похожих вопросов (FAISS + sentence-transformers), тренажёр SM-2 (интервальное повторение с 3D-флипкартами), mock-собеседования

**Аналитика:** навыки из вакансий HH.ru (214 навыков, пагинация, bar chart), тестовые задания от компаний, расчёт вероятности вопроса на собеседовании, дашборд с KPI

**UGC:** пользовательские ответы с голосованием ↑↓, закладки с заметками, предложение видео (URL + загрузка файлов)

**Админ-панель:** 6 вкладок — модерация вопросов (массовые действия), предложения, обратная связь, видео, тестовые задания (CRUD), аналитика (метрики, экспорт JSON/CSV, пересчёт вероятностей)

**Аутентификация:** JWT-авторизация, роли (user/admin), профиль с GitHub-ссылкой

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

# 3. Запустить все сервисы (включая оба фронтенда)
docker-compose up -d --build

# 4. Дождаться загрузки модели Whisper (~3 ГБ при первом запуске)
docker logs -f diploma-whisper-worker
```

### Доступ

| URL | Описание |
|-----|----------|
| http://localhost:3000 | **Новый** веб-интерфейс (custom CSS) |
| http://localhost:3001 | **Старый** веб-интерфейс (PrimeVue) |
| http://localhost:3000/admin | Панель администратора (новый) |
| http://localhost:3001/admin | Панель администратора (старый) |
| http://localhost:8000/docs | Swagger API документация |
| http://localhost:3035 | Metabase (BI аналитика из PostgreSQL) |
| http://localhost:8030 | PostHog (self-hosted, профиль posthog-selfhost) |

---

## Технологический стек

**Backend:** Python 3.11, FastAPI, asyncpg, yt-dlp, sentence-transformers, FAISS  
**Frontend NEW:** Vue 3.4, Vite 5, Pinia, Vue Router 4, Axios, @vueuse/core — **без PrimeVue**, полностью кастомный CSS  
**Frontend OLD (legacy):** Vue 3, Vite, PrimeVue (lara-dark-purple), Pinia, Axios  
**AI/ML:** faster-whisper (CTranslate2), all-MiniLM-L6-v2, LLM (GPT-4o / Gemini / Llama-3.1)  
**Инфраструктура:** Docker Compose, PostgreSQL 15, Redis 7, nginx  

---

## Структура проекта

```
├── backend/            # FastAPI сервер (main_new.py — 3200+ строк)
├── frontend-new/       # НОВЫЙ Vue 3 фронтенд (12 views, кастомный CSS)
│   ├── src/
│   │   ├── api/        # HTTP-клиент (100+ методов)
│   │   ├── assets/     # global.css — дизайн-система
│   │   ├── components/ # NavBar, AppFooter
│   │   ├── router/     # 12 маршрутов с guards
│   │   ├── store/      # Pinia (auth, questions, tasks)
│   │   └── views/      # 12 страниц (Home – Admin)
│   ├── Dockerfile      # Production (multi-stage + nginx)
│   └── Dockerfile.dev  # Development (hot-reload)
├── frontend-vue/       # СТАРЫЙ Vue 3 фронтенд (PrimeVue)
├── whisper-service/    # Сервис транскрибации (faster-whisper)
├── scripts/            # SQL миграции, данные
└── docker-compose.yml  # Оркестрация всех сервисов
```

---

## Новый дизайн (frontend-new)

Полностью переписанный фронтенд **без PrimeVue** — только нативный HTML + CSS custom properties:

- **Дизайн-система:** тёмная тема (#0c0c0f), фиолетовый бренд (#7c5cfc), CSS-переменные для цветов/радиусов/теней
- **Утилитные классы:** `.btn` (primary/secondary/ghost/ok/warn/err + sm/lg/icon), `.badge` (brand/ok/warn/err/info/muted), `.card`, `.input`, `.spinner`, `.progress`
- **Компоненты:** glassmorphism NavBar с hamburger-меню, Teleport-диалоги (вместо PrimeVue Dialog), нативные `<select>` (вместо PrimeVue Dropdown), HTML-таблицы (вместо PrimeVue DataTable)
- **Тренажёр:** 3D CSS-флипкарты, keyboard shortcuts (Space/←/→), SM-2 алгоритм
- **Админка:** 6 вкладок (нативные табы), inline вся логика подкомпонентов

---

## Команды

```bash
# Запуск всех сервисов
docker-compose up -d

# Запуск только нового фронтенда (локально, без Docker)
cd frontend-new && npm install && npm run dev

# Пересборка одного сервиса
docker-compose up -d --build frontend

# Логи
docker logs -f diploma-backend
docker logs -f diploma-frontend-new
docker logs -f diploma-frontend-old

# Остановка
docker-compose down

# Проверка статуса
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Production-сборка нового фронтенда
cd frontend-new && npm run build
```

---

## Product Analytics: Metabase + PostHog

Проект поддерживает одновременное использование двух систем:

- **Metabase** для BI-аналитики по данным PostgreSQL (SQL, дашборды, отчеты)
- **PostHog** для продуктовой аналитики поведения (events, funnels, retention)

### 1) Запуск Metabase

```bash
docker compose up -d metabase
```

Открыть: `http://localhost:3035`

### 2) Подключение PostHog в PrimeVue (порт 3020)

По умолчанию PostHog отключен. Для локального запуска self-hosted PostHog используйте отдельный профиль:

```bash
docker compose --profile posthog-selfhost up -d \
	posthog-proxy posthog-web posthog-worker posthog-plugins \
	posthog-capture posthog-feature-flags \
	posthog-db posthog-redis posthog-clickhouse posthog-kafka
```

После первого запуска откройте `http://localhost:8030`, создайте пользователя и скопируйте Project API Key.

Затем задайте env перед сборкой PrimeVue:

```bash
# PowerShell
$env:VITE_POSTHOG_KEY="phc_xxx"
$env:VITE_POSTHOG_HOST="http://localhost:8030"
docker compose up -d --build primevue
```

Если переменная `VITE_POSTHOG_KEY` не задана, приложение продолжает работать только с внутренней аналитикой (без ошибок).

---

## Лицензия

MIT
