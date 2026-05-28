-- Ready SQL questions for Metabase (native query editor)
-- Optional: use these directly if you need custom periods/filters.

-- 1) Top URL pages by views
-- Metabase variables: {{days}} (Number)
SELECT
    COALESCE(NULLIF(path, ''), '[unknown]') AS path,
    COUNT(*)::bigint AS views,
    COUNT(DISTINCT user_session)::bigint AS unique_sessions,
    ROUND((COUNT(*) * 100.0 / NULLIF(SUM(COUNT(*)) OVER (), 0))::numeric, 2) AS views_pct
FROM question_views
WHERE question_id IS NULL
  AND viewed_at >= NOW() - ({{days}}::int * INTERVAL '1 day')
GROUP BY COALESCE(NULLIF(path, ''), '[unknown]')
ORDER BY views DESC, path;

-- 2) Entry pages (first page in session)
-- Metabase variables: {{days}} (Number)
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
      AND viewed_at >= NOW() - ({{days}}::int * INTERVAL '1 day')
    ORDER BY user_session, viewed_at ASC, id ASC
)
SELECT
    entry_path AS path,
    entry_referrer AS referrer,
    COUNT(*)::bigint AS sessions
FROM first_hits
GROUP BY entry_path, entry_referrer
ORDER BY sessions DESC, path;

-- 3) Referrer -> URL funnel
-- Metabase variables: {{days}} (Number), optional {{source}} (Text, exact match)
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
  AND viewed_at >= NOW() - ({{days}}::int * INTERVAL '1 day')
[[AND COALESCE(
    NULLIF(substring(referrer FROM 'https?://([^/]+)'), ''),
    NULLIF(referrer, ''),
    'direct'
) = {{source}}]]
GROUP BY
    COALESCE(
        NULLIF(substring(referrer FROM 'https?://([^/]+)'), ''),
        NULLIF(referrer, ''),
        'direct'
    ),
    COALESCE(NULLIF(path, ''), '[unknown]')
ORDER BY visits DESC, referrer_source, path;
