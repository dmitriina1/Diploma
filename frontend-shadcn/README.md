# frontend-shadcn — современный UI для InterviewHub

React + Vite + TypeScript + Tailwind CSS v4 + shadcn/ui + Aceternity-стиль анимации.

Альтернативный фронтенд для проекта [Diploma / InterviewHub](https://github.com/dmitriina1/Diploma) — платформы подготовки к IT-собеседованиям. Подключается к существующему FastAPI-бэкенду на порту `8000` (по REST API + WebSocket для прогресса) без каких-либо изменений в backend.

> Полностью совместим с существующим compose-стеком. Все варианты frontend (`frontend-new`, `frontend-vue`, `frontend-new-v2`, `PrimeVue`) продолжают работать.

## Стек

| Слой | Технология |
| --- | --- |
| UI Library | **shadcn/ui** (React + Radix UI primitives) |
| Стили | **Tailwind CSS v4** (через `@tailwindcss/vite`) |
| Цветовая модель | **OKLch** (perceptually-uniform колор-спейс) |
| Анимации | Framer Motion + кастомные Aceternity-стиль эффекты |
| State | Zustand (auth) + локальный React state |
| Routing | React Router v7 |
| HTTP | axios с JWT-интерсепторами |
| Toaster | Sonner |
| Иконки | lucide-react |

## 14 страниц (1:1 с PrimeVue)

| Маршрут | Файл | Описание |
| --- | --- | --- |
| `/` | `HomePage.tsx` | Лендинг с Aurora hero, тикером, фичами и пайплайном |
| `/login` | `LoginPage.tsx` | Вход / регистрация (JWT) |
| `/profile` | `ProfilePage.tsx` | Профиль пользователя |
| `/interview-questions` | `InterviewQuestionsPage.tsx` | Каталог вопросов с фильтрами |
| `/question/:id` | `QuestionDetailPage.tsx` | Детали вопроса + UGC-ответы + голосование |
| `/trainer` | `TrainerPage.tsx` | SM-2 тренажёр с 3D flip-картами и keyboard shortcuts |
| `/ai-interview` | `AIInterviewChatPage.tsx` | AI-собеседование (LLM-чат) |
| `/mock-interview` | `MockInterviewPage.tsx` | Mock-сессии с финальной оценкой |
| `/recordings` | `InterviewRecordingsPage.tsx` | Список обработанных видео |
| `/suggest` | `SuggestionsPage.tsx` | Предложить видео для обработки |
| `/test-assignments` | `TestAssignmentsPage.tsx` | Тестовые задания компаний |
| `/test-assignments/:id` | `TestAssignmentDetailPage.tsx` | Детали задания |
| `/hh-requirements` | `HHRequirementsPage.tsx` | HH-аналитика навыков с фильтрами по источникам |
| `/admin` | `AdminPage.tsx` | Админ-панель (6 вкладок: Stats / Questions / Suggestions / Feedback / Videos / HH) |

## Aceternity-стиль эффекты

Реализованы в `src/components/effects/`:

- `aurora-background.tsx` — анимированный gradient-aurora фон
- `spotlight.tsx` — луч прожектора
- `grid-pattern.tsx` — диагональная сетка с radial-mask
- `dot-pattern.tsx` — точечный фон
- `border-beam.tsx` — бегущий по бордеру луч
- `meteors.tsx` — падающие метеоры
- `animated-shiny-text.tsx` — переливающийся текст
- `animated-gradient.tsx` — gradient-shimmer текст

## Тёмная / светлая тема

- Реализована через CSS custom properties (`--background`, `--foreground`, `--primary`, …) в OKLch.
- Светлая, тёмная, system режимы.
- Сохранение в `localStorage`, инициализация ДО рендера для отсутствия мерцания (см. `index.html`).
- `<ThemeToggle />` в правом верхнем углу.

## Подключение к бэкенду

Все обращения идут через единый axios-инстанс (`src/api/client.ts`), который читает `VITE_API_BASE_URL`:

- В **dev**: `npm run dev` → Vite proxy перебрасывает `/api` и `/ws` на `http://localhost:8000` (см. `vite.config.ts`). Backend изменять не нужно.
- В **prod (docker)**: nginx внутри контейнера проксирует `/api` и `/ws` на `backend:8000`.

JWT хранится в `localStorage.auth_token` и автоматически добавляется к запросам в `Authorization: Bearer …`.

WebSocket для прогресса задач: `ws(s)://<host>/ws/<client_id>` (см. `getWebSocketUrl()` в `src/api/client.ts`).

## Локальная разработка

```bash
cd frontend-shadcn
npm install
# (вариант) cp .env.example .env  и поправить VITE_API_BASE_URL
npm run dev
```

Откроется на http://localhost:3030. Backend ожидается на http://localhost:8000.

## Сборка

```bash
npm run build      # production build → dist/
npm run preview    # локальный просмотр build
```

## Docker

### Production (multi-stage с nginx)

```bash
docker build -t interviewhub-frontend-shadcn .
docker run -p 3030:80 interviewhub-frontend-shadcn
```

### Dev (с hot reload)

```bash
docker build -f Dockerfile.dev -t interviewhub-frontend-shadcn-dev .
docker run -p 3030:3030 -v $(pwd):/app -v /app/node_modules interviewhub-frontend-shadcn-dev
```

### docker-compose

В корневой `docker-compose.yml` добавьте сервис:

```yaml
  frontend-shadcn:
    build: ./frontend-shadcn
    container_name: diploma-frontend-shadcn
    ports:
      - "3030:80"
    depends_on:
      - backend
    networks:
      - default
```

Затем:

```bash
docker compose up -d --build frontend-shadcn
```

UI будет доступен на http://localhost:3030.

## Структура проекта

```
src/
├── api/                  axios клиент + типизированные API модули
├── components/
│   ├── ui/               shadcn/ui компоненты (button, card, dialog, …)
│   ├── effects/          Aceternity-стиль (aurora, spotlight, beam, …)
│   └── layout/           NavBar (glassmorphism), Footer, AppLayout, ThemeToggle
├── hooks/                use-theme, и т.п.
├── lib/                  cn() и хелперы
├── pages/                14 страниц
├── store/                Zustand auth-store
├── types/                TypeScript интерфейсы для API
├── App.tsx               Роутинг
├── main.tsx              Entry point
└── index.css             Tailwind v4 + OKLch theming
```

## Roadmap

- [ ] Прогресс-дашборд (упомянут в магистерской, п. 11)
- [ ] Роадмапы junior/middle/senior
- [ ] Метрики обучения (heatmap по дням SM-2)

## Лицензия

Часть проекта `dmitriina1/Diploma` (магистерская диссертация).
