-- ============================================
-- Migration v2: Расширение функциональности
-- ============================================
-- Новые таблицы: предложения видео, обратная связь, закладки, теги, аналитика

-- 1. Таблица предложений видео от пользователей
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

-- 2. Таблица обратной связи
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

-- 3. Таблица закладок (избранное)
CREATE TABLE IF NOT EXISTS bookmarks (
    id SERIAL PRIMARY KEY,
    question_id INTEGER REFERENCES questions(id) ON DELETE CASCADE,
    user_session VARCHAR(100) NOT NULL,
    note TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(question_id, user_session)
);

-- 4. Таблица тегов для вопросов
CREATE TABLE IF NOT EXISTS question_tags (
    id SERIAL PRIMARY KEY,
    question_id INTEGER REFERENCES questions(id) ON DELETE CASCADE,
    tag VARCHAR(50) NOT NULL,
    UNIQUE(question_id, tag)
);

-- 5. Таблица результатов мок-интервью
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

-- 6. Таблица локально загруженных видео
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

-- 7. Таблица аналитики просмотров вопросов
CREATE TABLE IF NOT EXISTS question_views (
    id SERIAL PRIMARY KEY,
    question_id INTEGER REFERENCES questions(id) ON DELETE CASCADE,
    user_session VARCHAR(100),
    path TEXT,
    referrer TEXT,
    viewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE question_views ADD COLUMN IF NOT EXISTS path TEXT;
ALTER TABLE question_views ADD COLUMN IF NOT EXISTS referrer TEXT;

-- 8. Таблица заметок пользователя к вопросам
CREATE TABLE IF NOT EXISTS user_notes (
    id SERIAL PRIMARY KEY,
    question_id INTEGER REFERENCES questions(id) ON DELETE CASCADE,
    user_session VARCHAR(100) NOT NULL,
    note TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(question_id, user_session)
);

-- Индексы
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

-- Триггеры обновления updated_at
DROP TRIGGER IF EXISTS update_suggestions_updated_at ON video_suggestions;
CREATE TRIGGER update_suggestions_updated_at
    BEFORE UPDATE ON video_suggestions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_notes_updated_at ON user_notes;
CREATE TRIGGER update_notes_updated_at
    BEFORE UPDATE ON user_notes
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Добавить столбец platform в processed_videos если его нет
ALTER TABLE processed_videos ADD COLUMN IF NOT EXISTS platform VARCHAR(50) DEFAULT 'youtube';
-- Добавить столбец thumbnail
ALTER TABLE processed_videos ADD COLUMN IF NOT EXISTS thumbnail VARCHAR(500);
-- Добавить столбец duration
ALTER TABLE processed_videos ADD COLUMN IF NOT EXISTS duration INTEGER DEFAULT 0;
