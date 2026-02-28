-- ============================================
-- v3: Новые фичи — профессии, SM-2, UGC, тестовые задания, HH навыки
-- ============================================

-- Профессии (Frontend Developer, Backend Developer, etc.)
CREATE TABLE IF NOT EXISTS professions (
    id SERIAL PRIMARY KEY,
    slug VARCHAR(100) UNIQUE NOT NULL,       -- e.g. 'frontend-developer'
    title VARCHAR(200) NOT NULL,             -- e.g. 'Frontend разработчик'
    icon VARCHAR(50) DEFAULT 'pi pi-code',
    color VARCHAR(100) DEFAULT '#667eea',
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Связь профессий и технологий (topics)
CREATE TABLE IF NOT EXISTS profession_topics (
    id SERIAL PRIMARY KEY,
    profession_id INTEGER REFERENCES professions(id) ON DELETE CASCADE,
    topic VARCHAR(100) NOT NULL,
    UNIQUE(profession_id, topic)
);

-- SM-2 Spaced Repetition (серверное хранение)
CREATE TABLE IF NOT EXISTS sr_cards (
    id SERIAL PRIMARY KEY,
    user_session VARCHAR(100) NOT NULL,
    question_id INTEGER REFERENCES questions(id) ON DELETE CASCADE,
    easiness_factor FLOAT DEFAULT 2.5,       -- EF (min 1.3)
    interval_days FLOAT DEFAULT 0,           -- Интервал в днях
    repetitions INTEGER DEFAULT 0,           -- Число успешных повторений подряд
    next_review TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_quality INTEGER DEFAULT 0,          -- 0-5 (0=забыл, 5=идеально)
    total_reviews INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_session, question_id)
);

-- UGC ответы пользователей
CREATE TABLE IF NOT EXISTS user_answers (
    id SERIAL PRIMARY KEY,
    question_id INTEGER REFERENCES questions(id) ON DELETE CASCADE,
    user_session VARCHAR(100) NOT NULL,
    user_name VARCHAR(100) DEFAULT 'Аноним',
    answer_text TEXT NOT NULL,
    votes INTEGER DEFAULT 0,
    is_selected BOOLEAN DEFAULT FALSE,       -- Выбран как лучший ответ
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Голоса за UGC ответы
CREATE TABLE IF NOT EXISTS answer_votes (
    id SERIAL PRIMARY KEY,
    answer_id INTEGER REFERENCES user_answers(id) ON DELETE CASCADE,
    user_session VARCHAR(100) NOT NULL,
    vote_type VARCHAR(10) NOT NULL CHECK (vote_type IN ('up', 'down')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(answer_id, user_session)
);

-- Тестовые задания от компаний
CREATE TABLE IF NOT EXISTS test_assignments (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    company VARCHAR(200),
    profession VARCHAR(200),
    difficulty VARCHAR(20) DEFAULT 'middle' CHECK (difficulty IN ('junior', 'middle', 'senior')),
    skills TEXT,                              -- Навыки через запятую
    link VARCHAR(500),                        -- Ссылка на задание
    source VARCHAR(200),                      -- Откуда взято
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- HH навыки/требования
CREATE TABLE IF NOT EXISTS hh_skills (
    id SERIAL PRIMARY KEY,
    profession VARCHAR(200) NOT NULL,
    skill VARCHAR(200) NOT NULL,
    vacancy_count INTEGER DEFAULT 0,          -- В скольких вакансиях встречается
    total_vacancies INTEGER DEFAULT 0,        -- Всего вакансий просканировано
    percentage FLOAT DEFAULT 0.0,             -- % вакансий с этим навыком
    source VARCHAR(50) DEFAULT 'hh.ru',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(profession, skill)
);

-- Таймкоды вопросов по видео (вместо одного timecode в questions)
CREATE TABLE IF NOT EXISTS question_timecodes (
    id SERIAL PRIMARY KEY,
    question_id INTEGER REFERENCES questions(id) ON DELETE CASCADE,
    video_id INTEGER REFERENCES processed_videos(id) ON DELETE CASCADE,
    timecode_start VARCHAR(20),              -- "10:30"
    timecode_seconds INTEGER DEFAULT 0,      -- В секундах для удобства
    UNIQUE(question_id, video_id)
);

-- Индексы v3
CREATE INDEX IF NOT EXISTS idx_profession_topics_prof ON profession_topics(profession_id);
CREATE INDEX IF NOT EXISTS idx_profession_topics_topic ON profession_topics(topic);
CREATE INDEX IF NOT EXISTS idx_sr_cards_session ON sr_cards(user_session);
CREATE INDEX IF NOT EXISTS idx_sr_cards_question ON sr_cards(question_id);
CREATE INDEX IF NOT EXISTS idx_sr_cards_next_review ON sr_cards(next_review);
CREATE INDEX IF NOT EXISTS idx_user_answers_question ON user_answers(question_id);
CREATE INDEX IF NOT EXISTS idx_user_answers_session ON user_answers(user_session);
CREATE INDEX IF NOT EXISTS idx_answer_votes_answer ON answer_votes(answer_id);
CREATE INDEX IF NOT EXISTS idx_test_assignments_prof ON test_assignments(profession);
CREATE INDEX IF NOT EXISTS idx_test_assignments_diff ON test_assignments(difficulty);
CREATE INDEX IF NOT EXISTS idx_hh_skills_prof ON hh_skills(profession);
CREATE INDEX IF NOT EXISTS idx_question_timecodes_q ON question_timecodes(question_id);
CREATE INDEX IF NOT EXISTS idx_question_timecodes_v ON question_timecodes(video_id);

-- Наполнение профессий
INSERT INTO professions (slug, title, icon, color, sort_order) VALUES
    ('frontend-developer', 'Frontend разработчик', 'pi pi-palette', '#f093fb', 1),
    ('backend-developer', 'Backend разработчик', 'pi pi-server', '#667eea', 2),
    ('python-developer', 'Python разработчик', 'pi pi-code', '#4facfe', 3),
    ('java-developer', 'Java разработчик', 'pi pi-code', '#fa709a', 4),
    ('fullstack-developer', 'Fullstack разработчик', 'pi pi-th-large', '#43e97b', 5),
    ('devops', 'DevOps инженер', 'pi pi-cloud', '#fcb69f', 6),
    ('qa-engineer', 'QA инженер', 'pi pi-check-circle', '#a8edea', 7),
    ('data-scientist', 'Data Scientist', 'pi pi-chart-bar', '#fbc2eb', 8),
    ('mobile-developer', 'Mobile разработчик', 'pi pi-mobile', '#84fab0', 9),
    ('golang-developer', 'Golang разработчик', 'pi pi-code', '#ffecd2', 10)
ON CONFLICT (slug) DO NOTHING;

-- Связь профессий с технологиями (topics)
INSERT INTO profession_topics (profession_id, topic) VALUES
    ((SELECT id FROM professions WHERE slug='frontend-developer'), 'Frontend'),
    ((SELECT id FROM professions WHERE slug='frontend-developer'), 'JavaScript'),
    ((SELECT id FROM professions WHERE slug='frontend-developer'), 'React'),
    ((SELECT id FROM professions WHERE slug='frontend-developer'), 'CSS'),
    ((SELECT id FROM professions WHERE slug='frontend-developer'), 'HTML'),
    ((SELECT id FROM professions WHERE slug='backend-developer'), 'Backend'),
    ((SELECT id FROM professions WHERE slug='backend-developer'), 'Database'),
    ((SELECT id FROM professions WHERE slug='backend-developer'), 'System Design'),
    ((SELECT id FROM professions WHERE slug='backend-developer'), 'API'),
    ((SELECT id FROM professions WHERE slug='python-developer'), 'Python'),
    ((SELECT id FROM professions WHERE slug='python-developer'), 'Backend'),
    ((SELECT id FROM professions WHERE slug='python-developer'), 'Django'),
    ((SELECT id FROM professions WHERE slug='python-developer'), 'Flask'),
    ((SELECT id FROM professions WHERE slug='java-developer'), 'Java'),
    ((SELECT id FROM professions WHERE slug='java-developer'), 'Spring'),
    ((SELECT id FROM professions WHERE slug='java-developer'), 'Backend'),
    ((SELECT id FROM professions WHERE slug='fullstack-developer'), 'Frontend'),
    ((SELECT id FROM professions WHERE slug='fullstack-developer'), 'Backend'),
    ((SELECT id FROM professions WHERE slug='fullstack-developer'), 'JavaScript'),
    ((SELECT id FROM professions WHERE slug='fullstack-developer'), 'Database'),
    ((SELECT id FROM professions WHERE slug='devops'), 'DevOps'),
    ((SELECT id FROM professions WHERE slug='devops'), 'Docker'),
    ((SELECT id FROM professions WHERE slug='devops'), 'Kubernetes'),
    ((SELECT id FROM professions WHERE slug='devops'), 'CI/CD'),
    ((SELECT id FROM professions WHERE slug='qa-engineer'), 'QA'),
    ((SELECT id FROM professions WHERE slug='qa-engineer'), 'Testing'),
    ((SELECT id FROM professions WHERE slug='data-scientist'), 'Data Science'),
    ((SELECT id FROM professions WHERE slug='data-scientist'), 'Python'),
    ((SELECT id FROM professions WHERE slug='data-scientist'), 'Algorithms'),
    ((SELECT id FROM professions WHERE slug='mobile-developer'), 'Mobile'),
    ((SELECT id FROM professions WHERE slug='mobile-developer'), 'iOS'),
    ((SELECT id FROM professions WHERE slug='mobile-developer'), 'Android'),
    ((SELECT id FROM professions WHERE slug='golang-developer'), 'Go'),
    ((SELECT id FROM professions WHERE slug='golang-developer'), 'Backend')
ON CONFLICT DO NOTHING;

-- Наполнение демо тестовых заданий
INSERT INTO test_assignments (title, description, company, profession, difficulty, skills) VALUES
    ('Создать To-Do приложение на React', 'Реализовать список задач с фильтрацией, CRUD операциями и сохранением в localStorage', 'Яндекс', 'Frontend разработчик', 'junior', 'React,JavaScript,CSS'),
    ('REST API на Spring Boot', 'Разработать REST API для управления пользователями с JWT авторизацией', 'СБЕР', 'Java разработчик', 'middle', 'Java,Spring Boot,PostgreSQL,JWT'),
    ('Микросервисная архитектура', 'Спроектировать и реализовать систему из 3 микросервисов с API Gateway', 'VK', 'Backend разработчик', 'senior', 'Docker,Kubernetes,gRPC,PostgreSQL'),
    ('Telegram бот на Python', 'Бот для трекинга привычек с напоминаниями и статистикой', 'Т-Банк', 'Python разработчик', 'junior', 'Python,aiogram,SQLite'),
    ('CI/CD пайплайн', 'Настроить полный CI/CD пайплайн для Node.js приложения с тестами и деплоем', 'Wildberries', 'DevOps инженер', 'middle', 'GitLab CI,Docker,Nginx,Ansible'),
    ('Нагрузочное тестирование API', 'Разработать план и провести нагрузочное тестирование REST API', 'МТС', 'QA инженер', 'middle', 'JMeter,Gatling,Python,SQL'),
    ('Мобильное приложение прогноза погоды', 'Реализовать приложение с использованием OpenWeather API', 'Авито', 'Mobile разработчик', 'junior', 'Flutter,Dart,REST API'),
    ('ETL пайплайн для Data Lake', 'Сборка данных из 3-х источников, обработка и загрузка в аналитический склад', 'Ozon', 'Data Scientist', 'senior', 'Python,Apache Spark,SQL,Airflow')
ON CONFLICT DO NOTHING;

-- Наполнение демо HH навыков
INSERT INTO hh_skills (profession, skill, vacancy_count, total_vacancies, percentage) VALUES
    ('Frontend разработчик', 'JavaScript', 850, 1000, 85.0),
    ('Frontend разработчик', 'React', 620, 1000, 62.0),
    ('Frontend разработчик', 'TypeScript', 580, 1000, 58.0),
    ('Frontend разработчик', 'HTML/CSS', 540, 1000, 54.0),
    ('Frontend разработчик', 'Vue.js', 320, 1000, 32.0),
    ('Frontend разработчик', 'Git', 480, 1000, 48.0),
    ('Frontend разработчик', 'REST API', 410, 1000, 41.0),
    ('Frontend разработчик', 'Webpack/Vite', 350, 1000, 35.0),
    ('Frontend разработчик', 'Redux/MobX', 280, 1000, 28.0),
    ('Frontend разработчик', 'Next.js', 220, 1000, 22.0),
    ('Frontend разработчик', 'Node.js', 190, 1000, 19.0),
    ('Frontend разработчик', 'Docker', 150, 1000, 15.0),
    ('Frontend разработчик', 'GraphQL', 120, 1000, 12.0),
    ('Frontend разработчик', 'Jest', 110, 1000, 11.0),
    ('Frontend разработчик', 'Angular', 180, 1000, 18.0),
    ('Backend разработчик', 'SQL', 780, 1000, 78.0),
    ('Backend разработчик', 'PostgreSQL', 650, 1000, 65.0),
    ('Backend разработчик', 'Docker', 580, 1000, 58.0),
    ('Backend разработчик', 'Git', 540, 1000, 54.0),
    ('Backend разработчик', 'REST API', 520, 1000, 52.0),
    ('Backend разработчик', 'Linux', 480, 1000, 48.0),
    ('Backend разработчик', 'Redis', 350, 1000, 35.0),
    ('Backend разработчик', 'Kafka', 280, 1000, 28.0),
    ('Backend разработчик', 'Kubernetes', 250, 1000, 25.0),
    ('Backend разработчик', 'CI/CD', 320, 1000, 32.0),
    ('Backend разработчик', 'MongoDB', 180, 1000, 18.0),
    ('Backend разработчик', 'RabbitMQ', 160, 1000, 16.0),
    ('Python разработчик', 'Python', 950, 1000, 95.0),
    ('Python разработчик', 'Django', 420, 1000, 42.0),
    ('Python разработчик', 'FastAPI', 350, 1000, 35.0),
    ('Python разработчик', 'PostgreSQL', 580, 1000, 58.0),
    ('Python разработчик', 'Docker', 480, 1000, 48.0),
    ('Python разработчик', 'SQL', 620, 1000, 62.0),
    ('Python разработчик', 'Git', 520, 1000, 52.0),
    ('Python разработчик', 'REST API', 480, 1000, 48.0),
    ('Python разработчик', 'Redis', 280, 1000, 28.0),
    ('Python разработчик', 'Celery', 220, 1000, 22.0),
    ('Python разработчик', 'Flask', 250, 1000, 25.0),
    ('Python разработчик', 'asyncio', 190, 1000, 19.0),
    ('Java разработчик', 'Java', 920, 1000, 92.0),
    ('Java разработчик', 'Spring', 750, 1000, 75.0),
    ('Java разработчик', 'SQL', 680, 1000, 68.0),
    ('Java разработчик', 'PostgreSQL', 520, 1000, 52.0),
    ('Java разработчик', 'Docker', 450, 1000, 45.0),
    ('Java разработчик', 'Hibernate', 380, 1000, 38.0),
    ('Java разработчик', 'Kafka', 350, 1000, 35.0),
    ('Java разработчик', 'Git', 480, 1000, 48.0),
    ('Java разработчик', 'Maven/Gradle', 420, 1000, 42.0),
    ('Java разработчик', 'Microservices', 320, 1000, 32.0),
    ('DevOps инженер', 'Docker', 880, 1000, 88.0),
    ('DevOps инженер', 'Kubernetes', 720, 1000, 72.0),
    ('DevOps инженер', 'Linux', 780, 1000, 78.0),
    ('DevOps инженер', 'CI/CD', 680, 1000, 68.0),
    ('DevOps инженер', 'Terraform', 420, 1000, 42.0),
    ('DevOps инженер', 'Ansible', 380, 1000, 38.0),
    ('DevOps инженер', 'Git', 520, 1000, 52.0),
    ('DevOps инженер', 'Python', 350, 1000, 35.0),
    ('DevOps инженер', 'Bash', 450, 1000, 45.0),
    ('DevOps инженер', 'AWS/GCP', 320, 1000, 32.0),
    ('QA инженер', 'SQL', 520, 1000, 52.0),
    ('QA инженер', 'Selenium', 380, 1000, 38.0),
    ('QA инженер', 'Postman', 450, 1000, 45.0),
    ('QA инженер', 'Python', 320, 1000, 32.0),
    ('QA инженер', 'Git', 350, 1000, 35.0),
    ('QA инженер', 'REST API', 420, 1000, 42.0),
    ('QA инженер', 'Java', 250, 1000, 25.0),
    ('QA инженер', 'Docker', 180, 1000, 18.0),
    ('QA инженер', 'JMeter', 150, 1000, 15.0)
ON CONFLICT (profession, skill) DO UPDATE SET
    vacancy_count = EXCLUDED.vacancy_count,
    total_vacancies = EXCLUDED.total_vacancies,
    percentage = EXCLUDED.percentage,
    updated_at = CURRENT_TIMESTAMP;

-- Триггеры для новых таблиц
DROP TRIGGER IF EXISTS update_sr_cards_updated_at ON sr_cards;
CREATE TRIGGER update_sr_cards_updated_at
    BEFORE UPDATE ON sr_cards FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_user_answers_updated_at ON user_answers;
CREATE TRIGGER update_user_answers_updated_at
    BEFORE UPDATE ON user_answers FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
