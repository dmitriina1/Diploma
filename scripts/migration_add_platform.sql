-- Миграция БД для добавления поддержки разных видеоплатформ
-- Запустить после первого запуска проекта

-- Добавить столбец platform (если он не существует)
ALTER TABLE processed_videos 
ADD COLUMN IF NOT EXISTS platform VARCHAR(50) DEFAULT 'youtube';

-- Обновить существующие записи
UPDATE processed_videos 
SET platform = CASE
    WHEN url LIKE '%youtube.com%' OR url LIKE '%youtu.be%' THEN 'youtube'
    WHEN url LIKE '%vk.com%' OR url LIKE '%vkvideo.ru%' THEN 'vk'
    WHEN url LIKE '%rutube.ru%' THEN 'rutube'
    WHEN url LIKE '%ok.ru%' THEN 'ok'
    ELSE 'unknown'
END
WHERE platform IS NULL OR platform = 'youtube';

-- Добавить индекс
CREATE INDEX IF NOT EXISTS idx_processed_videos_platform ON processed_videos(platform);

-- Проверка
SELECT platform, COUNT(*) as count 
FROM processed_videos 
GROUP BY platform;
