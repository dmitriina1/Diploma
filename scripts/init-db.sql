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
    platform VARCHAR(50) DEFAULT 'youtube',  -- Платформа: youtube, vk, rutube, ok, etc.
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
CREATE INDEX IF NOT EXISTS idx_processed_videos_platform ON processed_videos(platform);

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

-- ============================================
-- v2: Таблицы расширенной функциональности
-- ============================================

-- Предложения видео от пользователей
CREATE TABLE IF NOT EXISTS video_suggestions (
    id SERIAL PRIMARY KEY,
    url VARCHAR(500) NOT NULL,
    platform VARCHAR(50) DEFAULT 'youtube',
    title VARCHAR(500),
    topic VARCHAR(100),
    difficulty VARCHAR(20) DEFAULT 'middle',
    comment TEXT,
    user_name VARCHAR(100),
    user_email VARCHAR(200),
    status VARCHAR(30) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'processing', 'completed')),
    admin_comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Обратная связь
CREATE TABLE IF NOT EXISTS feedback (
    id SERIAL PRIMARY KEY,
    question_id INTEGER REFERENCES questions(id) ON DELETE SET NULL,
    feedback_type VARCHAR(30) NOT NULL CHECK (feedback_type IN ('like', 'dislike', 'report', 'suggestion', 'answer_quality')),
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    comment TEXT,
    user_name VARCHAR(100),
    user_email VARCHAR(200),
    user_session VARCHAR(100),
    is_resolved BOOLEAN DEFAULT FALSE,
    admin_response TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Закладки (избранное)
CREATE TABLE IF NOT EXISTS bookmarks (
    id SERIAL PRIMARY KEY,
    question_id INTEGER REFERENCES questions(id) ON DELETE CASCADE,
    user_session VARCHAR(100) NOT NULL,
    note TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(question_id, user_session)
);

-- Теги для вопросов
CREATE TABLE IF NOT EXISTS question_tags (
    id SERIAL PRIMARY KEY,
    question_id INTEGER REFERENCES questions(id) ON DELETE CASCADE,
    tag VARCHAR(50) NOT NULL,
    UNIQUE(question_id, tag)
);

-- Результаты мок-интервью
CREATE TABLE IF NOT EXISTS mock_interviews (
    id SERIAL PRIMARY KEY,
    user_session VARCHAR(100) NOT NULL,
    topic VARCHAR(100),
    difficulty VARCHAR(20),
    total_questions INTEGER DEFAULT 0,
    correct_answers INTEGER DEFAULT 0,
    score FLOAT DEFAULT 0.0,
    duration_seconds INTEGER DEFAULT 0,
    answers JSONB DEFAULT '[]',
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Локально загруженные видео
CREATE TABLE IF NOT EXISTS uploaded_videos (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(500) NOT NULL,
    original_name VARCHAR(500),
    file_size BIGINT,
    mime_type VARCHAR(100),
    topic VARCHAR(100),
    difficulty VARCHAR(20) DEFAULT 'middle',
    status VARCHAR(30) DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'error')),
    task_id VARCHAR(100),
    uploaded_by VARCHAR(100) DEFAULT 'admin',
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Аналитика просмотров вопросов
CREATE TABLE IF NOT EXISTS question_views (
    id SERIAL PRIMARY KEY,
    question_id INTEGER REFERENCES questions(id) ON DELETE CASCADE,
    user_session VARCHAR(100),
    path TEXT,
    referrer TEXT,
    viewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Заметки пользователя к вопросам
CREATE TABLE IF NOT EXISTS user_notes (
    id SERIAL PRIMARY KEY,
    question_id INTEGER REFERENCES questions(id) ON DELETE CASCADE,
    user_session VARCHAR(100) NOT NULL,
    note TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(question_id, user_session)
);

-- Индексы v2
CREATE INDEX IF NOT EXISTS idx_suggestions_status ON video_suggestions(status);
CREATE INDEX IF NOT EXISTS idx_suggestions_platform ON video_suggestions(platform);
CREATE INDEX IF NOT EXISTS idx_feedback_type ON feedback(feedback_type);
CREATE INDEX IF NOT EXISTS idx_feedback_question ON feedback(question_id);
CREATE INDEX IF NOT EXISTS idx_feedback_resolved ON feedback(is_resolved);
CREATE INDEX IF NOT EXISTS idx_bookmarks_session ON bookmarks(user_session);
CREATE INDEX IF NOT EXISTS idx_bookmarks_question ON bookmarks(question_id);
CREATE INDEX IF NOT EXISTS idx_tags_question ON question_tags(question_id);
CREATE INDEX IF NOT EXISTS idx_tags_tag ON question_tags(tag);
CREATE INDEX IF NOT EXISTS idx_mock_session ON mock_interviews(user_session);
CREATE INDEX IF NOT EXISTS idx_uploaded_status ON uploaded_videos(status);
CREATE INDEX IF NOT EXISTS idx_views_question ON question_views(question_id);
CREATE INDEX IF NOT EXISTS idx_views_session ON question_views(user_session);
CREATE INDEX IF NOT EXISTS idx_notes_session ON user_notes(user_session);

-- Триггер для video_suggestions
DROP TRIGGER IF EXISTS update_suggestions_updated_at ON video_suggestions;
CREATE TRIGGER update_suggestions_updated_at
    BEFORE UPDATE ON video_suggestions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Триггер для user_notes
DROP TRIGGER IF EXISTS update_notes_updated_at ON user_notes;
CREATE TRIGGER update_notes_updated_at
    BEFORE UPDATE ON user_notes
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
