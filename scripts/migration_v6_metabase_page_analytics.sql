-- Migration v6: Metabase page analytics views (Top URL, Entry pages, Referrer -> URL)

ALTER TABLE IF EXISTS question_views ADD COLUMN IF NOT EXISTS path TEXT;
ALTER TABLE IF EXISTS question_views ADD COLUMN IF NOT EXISTS referrer TEXT;

CREATE INDEX IF NOT EXISTS idx_views_viewed_at ON question_views(viewed_at);
CREATE INDEX IF NOT EXISTS idx_views_path ON question_views(path);
CREATE INDEX IF NOT EXISTS idx_views_referrer ON question_views(referrer);

CREATE OR REPLACE VIEW analytics_top_urls_30d AS
SELECT
    COALESCE(NULLIF(path, ''), '[unknown]') AS path,
    COUNT(*)::bigint AS views,
    COUNT(DISTINCT user_session)::bigint AS unique_sessions,
    ROUND((COUNT(*) * 100.0 / NULLIF(SUM(COUNT(*)) OVER (), 0))::numeric, 2) AS views_pct
FROM question_views
WHERE question_id IS NULL
  AND viewed_at >= NOW() - INTERVAL '30 days'
GROUP BY COALESCE(NULLIF(path, ''), '[unknown]')
ORDER BY views DESC, path;

CREATE OR REPLACE VIEW analytics_entry_pages_30d AS
WITH first_hits AS (
    SELECT DISTINCT ON (user_session)
        user_session,
        viewed_at,
        COALESCE(NULLIF(path, ''), '[unknown]') AS entry_path,
        COALESCE(NULLIF(referrer, ''), 'direct') AS entry_referrer
    FROM question_views
    WHERE question_id IS NULL
      AND user_session IS NOT NULL
      AND user_session <> ''
      AND viewed_at >= NOW() - INTERVAL '30 days'
    ORDER BY user_session, viewed_at ASC, id ASC
)
SELECT
    entry_path AS path,
    entry_referrer AS referrer,
    COUNT(*)::bigint AS sessions
FROM first_hits
GROUP BY entry_path, entry_referrer
ORDER BY sessions DESC, path;

CREATE OR REPLACE VIEW analytics_referrer_to_url_30d AS
SELECT
    COALESCE(
        NULLIF(substring(referrer FROM 'https?://([^/]+)'), ''),
        NULLIF(referrer, ''),
        'direct'
    ) AS referrer_source,
    COALESCE(NULLIF(path, ''), '[unknown]') AS path,
    COUNT(*)::bigint AS visits,
    COUNT(DISTINCT user_session)::bigint AS unique_sessions
FROM question_views
WHERE question_id IS NULL
  AND viewed_at >= NOW() - INTERVAL '30 days'
GROUP BY
    COALESCE(
        NULLIF(substring(referrer FROM 'https?://([^/]+)'), ''),
        NULLIF(referrer, ''),
        'direct'
    ),
    COALESCE(NULLIF(path, ''), '[unknown]')
ORDER BY visits DESC, referrer_source, path;

COMMENT ON VIEW analytics_top_urls_30d IS 'Top URLs for last 30 days from question_views page hits';
COMMENT ON VIEW analytics_entry_pages_30d IS 'Landing pages (first page per session) for last 30 days';
COMMENT ON VIEW analytics_referrer_to_url_30d IS 'Referrer source to URL funnel for last 30 days';
