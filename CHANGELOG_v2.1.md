# Changelog v2.1 — Система вероятностей и карточка вопроса

## Дата: 18 февраля 2026

---

## 🎯 Основные изменения

### 1. Карточка вопроса (Admin Panel)

**Новый компонент:** `QuestionDetailDialog.vue`

При клике на строку в таблице "Управление вопросами" открывается полноэкранный диалог с:

- **Редактированием** — вопрос, ответ, технология, сложность, таймкод
- **Генерацией/перегенерацией ответа** через LLM
- **Вероятностью на собеседовании** — прогресс-бар с формулой:
  ```
  Вероятность = (кол-во видео с вопросом / всего видео) × 100%
  ```
- **Списком видео**, в которых встречался вопрос
- **Похожими вопросами** с возможностью объединения

### 2. Объединение (Merge) вопросов

При нажатии "Объединить" на похожем вопросе:

1. Появляется диалог подтверждения
2. Все видео-связи переносятся с текущего вопроса на целевой
3. Текущий вопрос удаляется
4. Вероятность целевого вопроса пересчитывается
5. Открывается карточка целевого вопроса

**Endpoint:** `POST /api/admin/questions/merge`
```json
{
  "source_id": 123,
  "target_id": 456
}
```

### 3. Вероятность в публичной части

Теперь вероятность отображается **всегда** (даже если 0%):
- На карточках вопросов в списке
- На странице детального просмотра вопроса

### 4. Видео в публичной части

На странице детального просмотра вопроса добавлен блок:
> **Видео, в которых встречался вопрос** (X из Y)

Каждое видео — кликабельная ссылка с названием и платформой.

**Новый публичный endpoint:** `GET /api/questions/{id}`

---

## 📁 Изменённые файлы

### Backend (`backend/main_new.py`)
- `update_probabilities()` — исправлен расчёт для ВСЕХ вопросов (не только approved)
- `GET /api/admin/questions` — добавлены `video_count` и `total_videos`
- `GET /api/admin/questions/{id}` — детали вопроса с видео и похожими
- `POST /api/admin/questions/merge` — объединение вопросов
- `GET /api/questions/{id}` — **НОВЫЙ** публичный endpoint

### Frontend

| Файл | Изменения |
|------|-----------|
| `components/QuestionDetailDialog.vue` | **НОВЫЙ** — карточка вопроса для админки |
| `components/QuestionApproval.vue` | Убран инлайн-редактор, добавлен клик на строку, колонка "Вероятность" |
| `components/QuestionCard.vue` | Вероятность показывается всегда (не только > 0) |
| `views/QuestionDetail.vue` | Добавлен блок "Видео", загрузка через новый endpoint |
| `api/client.js` | Добавлены `getPublicQuestionDetail()`, `mergeQuestions()` |
| `store/index.js` | Добавлены `totalVideos`, `mergeQuestions` action |

---

## 🔧 Формула расчёта вероятности

```sql
UPDATE questions 
SET probability = (
    SELECT COALESCE(COUNT(DISTINCT qv.video_id) * 100.0 / total_videos, 0)
    FROM question_video qv
    WHERE qv.question_id = questions.id
)
```

**Пример:**
- Вопрос встречался в 3 видео из 10 → `30%`
- Вопрос встречался в 1 видео из 1 → `100%`

После объединения: если вопрос А был в 2 видео, вопрос Б в 1 видео → после merge в целевом будет 3 видео.

---

## 🗄️ Структура базы данных

### Таблица `question_video` (many-to-many)
```sql
CREATE TABLE question_video (
    question_id INTEGER REFERENCES questions(id) ON DELETE CASCADE,
    video_id INTEGER REFERENCES processed_videos(id) ON DELETE CASCADE,
    PRIMARY KEY (question_id, video_id)
);
```

### Связи
```
questions ←→ question_video ←→ processed_videos
```

---

## 🚀 Как пересчитать вероятности вручную

Если вероятности показывают 0%, выполните SQL:

```sql
UPDATE questions 
SET probability = (
    SELECT COALESCE(COUNT(DISTINCT qv.video_id) * 100.0 / 
           (SELECT COUNT(*) FROM processed_videos), 0)
    FROM question_video qv
    WHERE qv.question_id = questions.id
);
```

Или через docker:
```bash
docker-compose exec postgres psql -U diploma -d interview_prep -c "UPDATE questions SET probability = (SELECT COALESCE(COUNT(DISTINCT qv.video_id) * 100.0 / (SELECT COUNT(*) FROM processed_videos), 0) FROM question_video qv WHERE qv.question_id = questions.id);"
```

---

## 📊 UI/UX улучшения

### Админ-панель
- Клик на строку → открывает карточку (не inline-редактирование)
- Кнопки действий (✓/↩/🗑) не триггерят открытие карточки
- Колонка "Вероятность" сортируемая

### Публичная часть
- Вероятность с иконкой 📊 и tooltip "Вероятность на собеседовании"
- Список видео с ссылками и платформами
- Похожие вопросы кликабельны

---

## ⚠️ Breaking Changes

Нет breaking changes. Все новые функции дополняют существующий API.

---

## 🔄 Миграция

Миграция не требуется — все таблицы уже существуют.

Если таблица `question_video` отсутствует:
```sql
CREATE TABLE IF NOT EXISTS question_video (
    question_id INTEGER REFERENCES questions(id) ON DELETE CASCADE,
    video_id INTEGER REFERENCES processed_videos(id) ON DELETE CASCADE,
    PRIMARY KEY (question_id, video_id)
);
```
