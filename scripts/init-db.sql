-- Включить расширение для поиска по схожести (триграммы)
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Таблица для хранения вопросов
CREATE TABLE IF NOT EXISTS questions (
    id SERIAL PRIMARY KEY,
    question TEXT NOT NULL,
    answer TEXT,
    topic VARCHAR(100),
    difficulty VARCHAR(20) CHECK (difficulty IN ('junior', 'middle', 'senior')),
    source_url VARCHAR(500),
    video_title VARCHAR(500),
    timecode VARCHAR(20),  -- Время в видео (например, "10:30")
    probability FLOAT DEFAULT 0.0,  -- Вероятность выпадения вопроса (%)
    approved BOOLEAN DEFAULT FALSE,  -- Одобрен ли вопрос админом
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица для хранения задач обработки
CREATE TABLE IF NOT EXISTS processing_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    youtube_url VARCHAR(500) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    progress INTEGER DEFAULT 0,
    current_step VARCHAR(200),
    result JSONB,
    error_message TEXT,
    client_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица для хранения обработанных видео
CREATE TABLE IF NOT EXISTS processed_videos (
    id SERIAL PRIMARY KEY,
    youtube_url VARCHAR(500) UNIQUE NOT NULL,
    video_id VARCHAR(50) NOT NULL,
    title VARCHAR(500),
    transcript TEXT,
    questions_count INTEGER DEFAULT 0,
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица для связи вопросов и видео (для расчёта вероятности)
CREATE TABLE IF NOT EXISTS question_video (
    id SERIAL PRIMARY KEY,
    question_id INTEGER REFERENCES questions(id) ON DELETE CASCADE,
    video_id INTEGER REFERENCES processed_videos(id) ON DELETE CASCADE,
    UNIQUE(question_id, video_id)
);

-- Добавить столбец timecode, если он не существует (для обратной совместимости)
ALTER TABLE questions ADD COLUMN IF NOT EXISTS timecode VARCHAR(20);

-- Индексы для быстрого поиска
CREATE INDEX IF NOT EXISTS idx_questions_topic ON questions(topic);
CREATE INDEX IF NOT EXISTS idx_questions_difficulty ON questions(difficulty);
CREATE INDEX IF NOT EXISTS idx_questions_approved ON questions(approved);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON processing_tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_client ON processing_tasks(client_id);
CREATE INDEX IF NOT EXISTS idx_question_video_question ON question_video(question_id);
CREATE INDEX IF NOT EXISTS idx_question_video_video ON question_video(video_id);

-- Функция обновления времени
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Триггеры для автообновления updated_at
DROP TRIGGER IF EXISTS update_questions_updated_at ON questions;
CREATE TRIGGER update_questions_updated_at
    BEFORE UPDATE ON questions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_tasks_updated_at ON processing_tasks;
CREATE TRIGGER update_tasks_updated_at
    BEFORE UPDATE ON processing_tasks
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
