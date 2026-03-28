# InterviewHub - Платформа подготовки к IT-собеседованиям

## Обзор проекта

**InterviewHub** — это full-stack веб-приложение для подготовки к IT-собеседованиям с автоматизированной обработкой видеоконтента. Система использует AI для извлечения вопросов из видеозаписей собеседований, создавая структурированную базу знаний с семантическим поиском и статистикой.

### Ключевые возможности

- **AI-обработка видео**: Автоматическая транскрипция (Whisper), извлечение вопросов (LLM), семантическая дедупликация (FAISS)
- **База вопросов**: 26 IT-профессий, фильтры по технологиям/сложности, семантический поиск
- **SM-2 тренажер**: Spaced Repetition с 3D-флипкартами для эффективного запоминания
- **Mock-интервью**: Симуляция собеседований с таймером и скорингом
- **Аналитика HH.ru**: Автосинхронизация навыков из 214+ вакансий, статистика по профессиям
- **Тестовые задания**: База заданий от топовых компаний (Яндекс, СБЕР, VK, Т-Банк)
- **UGC**: Пользовательские ответы с голосованием, предложения видео

---

## Технологический стек

### Backend
- **Python 3.11+** / **FastAPI** (асинхронный REST API)
- **PostgreSQL 15** (основная БД, 28 таблиц)
- **Redis 7** (кэш задач, FAISS-эмбеддингов)
- **asyncpg** (асинхронный драйвер PostgreSQL)
- **yt-dlp** (загрузка видео: YouTube, VK, Rutube, OK.ru, Dailymotion, Vimeo)
- **faster-whisper** (CTranslate2) — транскрибация аудио (large-v3-turbo)
- **sentence-transformers + FAISS** (семантический поиск, all-MiniLM-L6-v2)
- **httpx** (HTTP-клиент для LLM API)

### Frontend
- **Vue 3.4** + **Vite 5** + **Pinia** (state management)
- **Кастомный CSS** (471 строка, без UI-библиотек)
- **Axios** (HTTP-клиент)
- **Glassmorphism UI** (тёмная тема #0c0c0f, бренд #1f8a70)

### AI/ML
- **Whisper large-v3-turbo** (транскрибация речи)
- **all-MiniLM-L6-v2** (эмбеддинги для семантического поиска)
- **LLM провайдеры**: OpenRouter (GPT-4o, Llama-3.1-70b) / Gemini 2.0 Flash / Groq

### Инфраструктура
- **Docker Compose** (6 сервисов: postgres, redis, whisper, backend, frontend-new, frontend-vue)
- **WebSocket** (real-time обновления задач)
- **JWT-авторизация** (bcrypt)

---

## Архитектура

### Структура директорий

```
Diploma/
├── backend/                    # FastAPI сервер (1.1 MB, 19 Python файлов)
│   ├── main_new.py            # Главный файл (3817 строк, 55+ endpoints)
│   ├── api/routes/            # Модульные роуты
│   │   ├── auth.py            # JWT-авторизация
│   │   ├── admin.py           # Админка (CRUD, модерация, генерация ответов)
│   │   ├── public.py          # Публичные API (вопросы, поиск, закладки)
│   │   ├── processing.py      # Обработка видео
│   │   └── status.py          # Статусы задач
│   ├── core/
│   │   ├── config.py          # Конфигурация
│   │   └── db.py              # Пул соединений PostgreSQL
│   ├── services/
│   │   ├── whisper_orchestrator.py  # Управление Whisper-воркерами
│   │   ├── task_runtime.py          # Очередь задач
│   │   ├── ws_manager.py            # WebSocket менеджер
│   │   └── hh_sync.py               # Синхронизация с HH.ru API
│   ├── auth.py                # JWT + bcrypt (374 строки)
│   ├── video_downloader.py    # Универсальный загрузчик (351 строка)
│   ├── similarity_search.py   # FAISS семантический поиск (154 строки)
│   └── requirements.txt       # 23 зависимости
│
├── frontend-new/              # Новый фронтенд (45 MB, 32 файла)
│   ├── src/
│   │   ├── views/             # 13 страниц
│   │   │   ├── Home.vue       # Главная (177 строк)
│   │   │   ├── InterviewQuestions.vue  # Каталог вопросов (257 строк)
│   │   │   ├── QuestionDetail.vue      # Детали вопроса
│   │   │   ├── Trainer.vue             # SM-2 тренажёр (467 строк)
│   │   │   ├── MockInterview.vue       # Mock-собеседование
│   │   │   ├── InterviewRecordings.vue # Записи видео
│   │   │   ├── TestAssignments.vue     # Тестовые задания (139 строк)
│   │   │   ├── HHRequirements.vue      # HH-аналитика (193 строки)
│   │   │   ├── Suggestions.vue         # Предложить видео
│   │   │   ├── Profile.vue             # Профиль пользователя
│   │   │   ├── Admin.vue               # Админ-панель (647 строк)
│   │   │   └── Login.vue               # Авторизация
│   │   ├── components/
│   │   │   ├── NavBar.vue     # Навигация с glassmorphism
│   │   │   ├── AppFooter.vue  # Футер
│   │   │   ├── BrandIcon.vue  # SVG иконки
│   │   │   ├── StatePanel.vue # Пустые состояния
│   │   │   └── LineChart.vue  # График
│   │   ├── api/               # HTTP-клиент (100+ методов)
│   │   ├── store/             # Pinia stores
│   │   ├── router/            # 13 маршрутов + guards
│   │   ├── assets/global.css  # Дизайн-система (471 строка)
│   │   └── main.js            # Entry point
│   ├── package.json           # Vue 3.4, Vite 5, Pinia, Axios
│   ├── Dockerfile             # Production (multi-stage + nginx)
│   └── Dockerfile.dev         # Development (hot-reload)
│
├── whisper-service/           # Микросервис транскрибации (25 KB)
│   ├── main.py                # FastAPI + faster-whisper (266 строк)
│   ├── Dockerfile.cpu         # CPU-версия (int8)
│   ├── Dockerfile.gpu         # GPU-версия (float16)
│   └── requirements.txt       # faster-whisper, ctranslate2
│
├── scripts/                   # SQL миграции
│   ├── init-db.sql            # Базовая схема (221 строка)
│   ├── migration_v2.sql       # v2 фичи
│   └── migration_v3.sql       # v3 фичи (262 строки)
│
├── docker-compose.yml         # Оркестрация (183 строки, 6 сервисов)
└── README.md                  # Документация (167 строк)
```

---

## База данных (PostgreSQL)

### Основные таблицы (28 таблиц)

**Вопросы и контент:**
- `questions` — вопросы с собеседований (question, answer, topic, difficulty, probability, approved, timecode, source_url)
- `processed_videos` — обработанные видео (video_id, youtube_url, title, platform, transcript, questions_count)
- `question_video` — связь вопросов и видео (M2M)
- `question_timecodes` — таймкоды по видео
- `question_tags` — теги вопросов

**Обработка:**
- `processing_tasks` — задачи обработки видео (UUID, youtube_url, status, progress, current_step, result JSONB, error_message, client_id)
- `uploaded_videos` — локально загруженные файлы

**Пользовательский контент:**
- `video_suggestions` — предложения от пользователей (url, platform, topic, difficulty, comment, status, admin_comment)
- `feedback` — обратная связь (question_id, feedback_type, rating, comment, is_resolved)
- `bookmarks` — закладки пользователей (question_id, user_session, note)
- `user_notes` — заметки к вопросам
- `user_answers` — UGC-ответы пользователей (question_id, user_session, answer_text, votes, is_selected)
- `answer_votes` — голоса за ответы (up/down)

**Тренажер и mock:**
- `sr_cards` — SM-2 Spaced Repetition (user_session, question_id, easiness_factor, interval_days, repetitions, next_review, last_quality)
- `mock_interviews` — результаты mock-интервью (user_session, topic, difficulty, total_questions, correct_answers, score, answers JSONB, duration_seconds)

**Профессии и навыки:**
- `professions` — IT-профессии (26 штук: slug, title, icon, color, sort_order)
- `profession_topics` — связь профессий и технологий
- `test_assignments` — тестовые задания (title, description, company, profession, difficulty, skills, link, source)
- `hh_skills` — навыки из HH.ru (profession, skill, vacancy_count, total_vacancies, percentage)
- `hh_sync_runs` — логи синхронизации HH

**Авторизация:**
- `users` — пользователи (username, password_hash, display_name, role: user/admin, github_url)

**Аналитика:**
- `question_views` — аналитика просмотров

**Индексы:** 40+ индексов для оптимизации запросов  
**Триггеры:** 8 триггеров для auto-update `updated_at`

---

## API Endpoints (55+)

### Авторизация (`/api/auth`)
- `POST /register` — регистрация
- `POST /login` — вход (JWT)
- `GET /me` — текущий пользователь
- `PUT /profile` — обновление профиля

### Обработка видео (`/api`)
- `POST /process-video` — запуск обработки
- `POST /process-video/{client_id}` — с WebSocket
- `GET /task/{task_id}` — статус задачи
- `GET /tasks` — все задачи
- `GET /full-export/{task_id}` — экспорт результата

### Публичные (`/api`)
- `GET /questions` — список вопросов (фильтры: topic, level)
- `GET /questions/{id}` — детали вопроса
- `GET /questions/similar` — семантический поиск
- `GET /professions` — список профессий
- `GET /professions/{slug}/questions` — вопросы по профессии
- `POST /bookmarks` — добавить закладку
- `GET /bookmarks/{session}` — закладки пользователя
- `PUT /notes/{question_id}` — сохранить заметку
- `POST /feedback` — отправить feedback
- `GET /user-answers/{question_id}` — UGC-ответы
- `POST /user-answers/{question_id}` — добавить ответ
- `POST /user-answers/{answer_id}/vote` — голосовать
- `GET /test-assignments` — тестовые задания
- `GET /hh-skills` — навыки HH.ru
- `GET /hh-skills/professions` — профессии HH

### Админ-панель (`/api/admin`)
- `GET /questions` — все вопросы (с неодобренными)
- `POST /questions` — создать вопрос
- `PUT /questions/{id}` — обновить
- `DELETE /questions/{id}` — удалить
- `POST /approve-questions` — одобрить (массово)
- `POST /revoke-questions` — отозвать
- `POST /questions/merge` — объединить дубликаты
- `POST /generate-answer/{id}` — сгенерировать ответ (LLM)
- `POST /generate-answers-bulk` — массовая генерация
- `POST /recalculate-probabilities` — пересчёт вероятностей
- `GET /suggestions` — предложения видео
- `PUT /suggestions/{id}` — обновить статус
- `POST /suggestions/{id}/process` — обработать видео
- `GET /feedback` — обратная связь
- `POST /upload-video-file` — загрузить файл
- `POST /questions/{id}/tags` — добавить тег
- `GET /export-csv` — экспорт CSV
- `POST /test-assignments` — CRUD заданий
- `POST /hh-skills` — запустить синхронизацию HH

### Тренажер (`/api/trainer`)
- `POST /sm2-review` — отметить карточку (SM-2)
- `GET /sm2-cards/{session}` — карточки для повторения
- `DELETE /sm2-reset/{session}` — сбросить прогресс

### Mock-интервью (`/api/mock-interview`)
- `POST /start` — начать mock-интервью
- `POST /{id}/submit` — отправить результат
- `GET /history/{session}` — история попыток

### Статус
- `GET /` — главная страница API
- `GET /health` — health check
- `WS /ws/{client_id}` — WebSocket для real-time обновлений

---

## Основные фичи

### 1. AI Pipeline обработки видео (4 этапа)

**Мультиплатформенность:** YouTube, VK.video, Rutube, OK.ru, Dailymotion, Vimeo

**Pipeline:**
1. **Загрузка аудио** (yt-dlp) + субтитры
2. **Транскрибация** (Whisper large-v3-turbo, VAD-фильтр)
3. **Извлечение вопросов** (LLM: GPT-4o/Gemini/Llama-3.1)
4. **Сохранение в БД** с дедупликацией

**Real-time мониторинг:** WebSocket + polling, прогресс-бар, логи

### 2. Каталог вопросов

- **Фильтры:** 26 профессий, технология, сложность (junior/middle/senior)
- **Сортировка:** по вероятности, дате, алфавиту
- **Семантический поиск:** FAISS + all-MiniLM-L6-v2
- **Вероятность вопроса:** % на основе частоты в видео
- **Детали вопроса:**
  - Ответ (AI-генерация или ручной)
  - Похожие вопросы (top-5 по косинусному сходству)
  - Видео-источники с таймкодами
  - UGC-ответы с голосованием ↑↓
  - Закладки + заметки

### 3. SM-2 Тренажер (Spaced Repetition)

**Алгоритм SuperMemo 2:**
- Easiness Factor (1.3–2.5)
- Интервалы: 1 день → 6 дней → 16 дней → ...
- Качество ответа (0-5): 0=забыл, 5=идеально

**UI:**
- 3D CSS-флипкарты: вопрос → ответ (клик/пробел)
- Keyboard shortcuts: Space (flip), ← (повтор), → (знаю)
- Статистика: новые, на повтор, выучено
- Фильтры: тема, сложность, количество карточек

### 4. Mock-собеседование

- **Симуляция интервью:** случайные вопросы по теме/сложности
- **Таймер:** ограничение времени на ответ
- **Скоринг:** % правильных ответов
- **История попыток:** дата, тема, результат

### 5. Аналитика рынка труда (HH.ru)

- **Автосинхронизация:** каждые 24 часа
- **214+ навыков** по 15 профессиям
- **Bar chart:** % вакансий с навыком
- **Категории:**
  - Must-have (>50%)
  - Nice-to-have (20-50%)
  - Дополнительно (<20%)
- **Пагинация:** 30 навыков на страницу

### 6. Тестовые задания

- **База заданий:** от Яндекс, СБЕР, VK, Т-Банк, Wildberries, МТС, Авито, Ozon
- **Фильтры:** профессия, сложность, поиск
- **Детали:** описание, компания, навыки, ссылка

### 7. UGC (User-Generated Content)

- **Пользовательские ответы:** текст + автор
- **Голосование:** ↑↓ (один голос на пользователя)
- **Лучший ответ:** админ может отметить
- **Предложение видео:** URL + загрузка файла (до 500 MB)

### 8. Админ-панель (6 вкладок)

1. **Вопросы:** таблица с фильтрами, массовые действия, inline редактирование, генерация ответов (LLM), объединение дубликатов
2. **Предложения:** модерация URL от пользователей, запуск обработки
3. **Feedback:** просмотр отзывов, отметка "решено"
4. **Видео:** список обработанных видео, загрузка локальных файлов
5. **Тестовые задания:** CRUD
6. **Аналитика:** KPI, экспорт JSON/CSV, пересчёт вероятностей

---

## Дизайн-система (frontend-new)

### CSS Custom Properties (471 строка)

**Цвета:**
- Фон: `#0c0c0f` (тёмная тема)
- Бренд: `#1f8a70` (основной цвет)
- Акценты: `#ff6b6b` (ошибки), `#4ecdc4` (успех)

**Компоненты:**
- `.btn` — кнопки (primary, secondary, ghost)
- `.badge` — бейджи (junior, middle, senior)
- `.card` — карточки с glassmorphism
- `.input` — поля ввода
- `.spinner` — загрузчики

**Эффекты:**
- Glassmorphism (backdrop-filter: blur)
- Анимации: stagger, fade, slide
- 3D-трансформации (флипкарты)

---

## Архитектурные особенности

### Backend

- **Асинхронность:** asyncio, asyncpg, httpx
- **Per-task Whisper:** 1 воркер = 1 полное аудио (не chunking)
- **Пул соединений:** 2-20 коннектов к PostgreSQL
- **Redis TTL:** 24 часа для кэша
- **WebSocket broadcast:** real-time обновления для всех клиентов
- **LLM fallback:** автовыбор провайдера (OpenRouter → Gemini → Groq)
- **Дедупликация:** проверка LOWER(question) перед вставкой
- **Миграции:** SQL-скрипты (init + v2 + v3)

### Frontend

- **Без UI-библиотек:** полностью кастомный CSS (471 строка)
- **CSS custom properties:** тёмная тема, цвета, радиусы, тени
- **Composition API:** Vue 3 `<script setup>`
- **Pinia stores:** questionsStore, tasksStore, authStore
- **Route guards:** requiresAuth, requiresAdmin
- **WebSocket + polling:** гибридный подход для надёжности
- **Lazy loading:** динамический импорт компонентов
- **Teleport:** модальные окна вне DOM-дерева

### DevOps

- **Docker Compose:** 6 сервисов (postgres, redis, whisper, backend, frontend-new, frontend-vue)
- **Health checks:** для всех сервисов
- **Volumes:** postgres_data, redis_data, whisper_cache, shared_temp
- **Networks:** diploma-network (bridge)
- **Multi-stage builds:** production Dockerfile (nginx)
- **Hot-reload:** Dockerfile.dev для разработки

---

## Контекст диссертации

### Цель работы

Разработка информационной системы интеллектуального анализа видеоконтента для автоматизированного извлечения и структурирования вопросов из записей IT-собеседований.

### Проблематика

1. **Фрагментация знаний:** вопросы разбросаны по тысячам видео без структурированного доступа
2. **Низкая плотность информации:** 1-2 вопроса в час просмотра
3. **Отсутствие статистики:** невозможность приоритизации подготовки по частоте встречаемости
4. **Устаревание материалов:** книги и курсы не успевают за изменениями в индустрии

### Решение

**AI-конвейер:**
1. Автоматическая транскрипция (Whisper)
2. Извлечение вопросов (LLM с промптами)
3. Семантическая дедупликация (FAISS)
4. Структурированная база знаний с метаданными

**Результат:** масштабируемая система для агрегации и анализа видеоконтента с real-time обновлениями и персонализированной статистикой.

---

## Статистика проекта

- **Backend:** 19 Python файлов, 3817 строк в main_new.py, 55+ endpoints
- **Frontend:** 32 файла (Vue + JS), 13 страниц, 100+ API методов
- **База данных:** 28 таблиц, 40+ индексов, 8 триггеров
- **Сервисы:** 6 Docker-контейнеров
- **Поддержка платформ:** YouTube, VK, Rutube, OK.ru, Dailymotion, Vimeo
- **LLM провайдеры:** OpenRouter, Gemini, Groq
- **AI модели:** Whisper large-v3-turbo, all-MiniLM-L6-v2, GPT-4o/Llama-3.1/Gemini

---

## Запуск проекта

### Development

```bash
docker-compose up -d
```

Сервисы:
- Backend: http://localhost:8000
- Frontend: http://localhost:5173
- PostgreSQL: localhost:5432
- Redis: localhost:6379
- Whisper: http://localhost:8001

### Production

```bash
docker-compose -f docker-compose.yml up -d
```

Frontend собирается с nginx для production.

---

## Известные проблемы UI (требуют исправления)

1. **Home page:** небольшая, неинтересная, неудобная
2. **Вопросы:** текст в фильтрах не помещается полностью в кнопку
3. **Тренажер:** при перевороте карточки виден перевернутый вопрос с уровнями (обратная сторона карточки)
4. **Задания:** требуется улучшение UI
5. **Навыки:** 
   - Большинство навыков в Nice-to-have (20–50%)
   - Статистика берется только по навыкам в вакансиях
   - Нужно добавить переключение графиков: по навыкам / по описанию / по заголовку
   - Нужны фильтры-галочки для источника технологий (описание/навыки/заголовок)

---

## Планируемые улучшения

### Новые фичи

1. **Роадмапы подготовки:** персональные планы по уровню (junior/middle/senior)
2. **Чат-бот для вопросов:** LLM на базе LangChain/FAISS для симуляции интервью или разбора тем (алгоритмы, system design) вместо mock
3. **Трекинг прогресса:** дашборд с метриками (решено задач, пройдено mock, % готовности к компаниям) и лидерборды
4. **Интеграция с платформами:** экспорт в LeetCode/HackerRank, импорт результатов для адаптации плана

### Улучшения существующих фич

1. **Навыки и задания:**
   - Расширить парсинг HH на ATS-совместимость резюме
   - Behavioral вопросы (STAR-метод)
   - Company-specific вопросы (Яндекс, Сбер)

2. **Профиль:**
   - Генерация резюме/LinkedIn-оптимизация с AI
   - Портфолио с GitHub-интеграцией
   - Советы по soft skills

---

## Контакты и ссылки

- **Репозиторий:** C:\Users\Lenovo\Desktop\Diploma
- **Дата:** 2026-03-28
- **Статус:** В разработке (магистерская диссертация)
