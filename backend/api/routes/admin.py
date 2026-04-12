import asyncpg
from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.responses import JSONResponse

from auth import require_admin
from core.config import DATABASE_URL


def _env_bool(name: str, default: bool) -> bool:
    import os

    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


router = APIRouter(tags=["Admin"])


@router.get("/api/admin/questions")
async def get_admin_questions(_admin: dict = Depends(require_admin)):
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        total_videos = await conn.fetchval("SELECT COUNT(*) FROM processed_videos") or 0
        questions = await conn.fetch(
            """
            SELECT q.id, q.question, q.answer, q.topic, q.difficulty, q.probability,
                   q.timecode, q.approved, q.source_url, q.video_title, q.created_at,
                   COALESCE(vc.cnt, 0) AS video_count
            FROM questions q
            LEFT JOIN (
                SELECT question_id, COUNT(DISTINCT video_id) AS cnt
                FROM question_video
                GROUP BY question_id
            ) vc ON vc.question_id = q.id
            ORDER BY q.probability DESC NULLS LAST, q.created_at DESC
            """
        )

        result = [
            {
                "id": q["id"],
                "question": q["question"],
                "answer": q["answer"],
                "topic": q["topic"],
                "difficulty": q["difficulty"],
                "probability": float(q["probability"]) if q["probability"] else 0.0,
                "video_count": q["video_count"],
                "timecode": q["timecode"],
                "approved": q["approved"],
                "source_url": q["source_url"],
                "video_title": q["video_title"],
                "created_at": q["created_at"].isoformat() if q["created_at"] else None,
            }
            for q in questions
        ]

        return JSONResponse(content={"questions": result, "total_videos": total_videos})
    finally:
        await conn.close()


@router.get("/api/admin/questions/{question_id}")
async def get_question_detail(question_id: int, _admin: dict = Depends(require_admin)):
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        q = await conn.fetchrow(
            """
            SELECT q.*,
                   COALESCE(array_agg(DISTINCT qt.tag) FILTER (WHERE qt.tag IS NOT NULL), '{}') AS tags,
                   COALESCE(array_agg(DISTINCT qv.video_id) FILTER (WHERE qv.video_id IS NOT NULL), '{}') AS video_ids
            FROM questions q
            LEFT JOIN question_tags qt ON qt.question_id = q.id
            LEFT JOIN question_video qv ON qv.question_id = q.id
            WHERE q.id = $1
            GROUP BY q.id
            """,
            question_id,
        )
        if not q:
            raise HTTPException(status_code=404, detail="Question not found")
        d = dict(q)
        if d.get("created_at") and hasattr(d["created_at"], "isoformat"):
            d["created_at"] = d["created_at"].isoformat()
        d["probability"] = float(d["probability"]) if d.get("probability") else 0.0
        return d
    finally:
        await conn.close()


@router.get("/api/admin/feedback")
async def get_admin_feedback(
    is_resolved: bool | None = None, _admin: dict = Depends(require_admin)
):
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        if is_resolved is None:
            rows = await conn.fetch(
                """
                SELECT id, question_id, feedback_type, rating, comment,
                       user_name, user_email, user_session, is_resolved, admin_response, created_at
                FROM feedback
                ORDER BY created_at DESC
                LIMIT 300
                """
            )
        else:
            rows = await conn.fetch(
                """
                SELECT id, question_id, feedback_type, rating, comment,
                       user_name, user_email, user_session, is_resolved, admin_response, created_at
                FROM feedback
                WHERE is_resolved = $1
                ORDER BY created_at DESC
                LIMIT 300
                """,
                is_resolved,
            )

        feedbacks = []
        for r in rows:
            d = dict(r)
            if d.get("created_at"):
                d["created_at"] = d["created_at"].isoformat()
            feedbacks.append(d)
        return {"feedbacks": feedbacks, "count": len(feedbacks)}
    finally:
        await conn.close()


@router.put("/api/admin/feedback/{feedback_id}")
async def update_feedback(
    feedback_id: int, data: dict = Body(...), _admin: dict = Depends(require_admin)
):
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        row = await conn.fetchrow(
            """
            UPDATE feedback
            SET is_resolved = COALESCE($2, is_resolved),
                admin_response = COALESCE($3, admin_response)
            WHERE id = $1
            RETURNING id, is_resolved, admin_response
            """,
            feedback_id,
            data.get("is_resolved"),
            data.get("admin_response"),
        )
        if not row:
            raise HTTPException(status_code=404, detail="Feedback not found")
        return dict(row)
    finally:
        await conn.close()


@router.get("/api/admin/videos")
async def get_processed_videos(_admin: dict = Depends(require_admin)):
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        rows = await conn.fetch(
            """
            SELECT
                pv.id,
                pv.title,
                pv.youtube_url,
                pv.platform,
                pv.processed_at,
                GREATEST(COALESCE(pv.questions_count, 0), COALESCE(qc.question_count, 0)) AS questions_count,
                GREATEST(COALESCE(pv.questions_count, 0), COALESCE(qc.question_count, 0)) AS question_count,
                GREATEST(COALESCE(pv.questions_count, 0), COALESCE(qc.question_count, 0)) AS linked_questions
            FROM processed_videos pv
            LEFT JOIN (
                SELECT video_id, COUNT(*) AS question_count
                FROM question_video
                GROUP BY video_id
            ) qc ON qc.video_id = pv.id
            ORDER BY pv.processed_at DESC NULLS LAST, pv.id DESC
            LIMIT 300
            """
        )
        videos = []
        for row in rows:
            d = dict(row)
            if d.get("processed_at") and hasattr(d["processed_at"], "isoformat"):
                d["processed_at"] = d["processed_at"].isoformat()
            # Keep backward-compatible timestamp key used by UI cards.
            d["created_at"] = d.get("processed_at")
            videos.append(d)
        return {"videos": videos, "count": len(videos)}
    finally:
        await conn.close()


@router.get("/api/admin/videos/{video_id}/questions")
async def get_video_questions(video_id: int, _admin: dict = Depends(require_admin)):
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        rows = await conn.fetch(
            """
            SELECT q.id, q.question, q.answer, q.topic, q.difficulty, q.timecode
            FROM question_video qv
            JOIN questions q ON q.id = qv.question_id
            WHERE qv.video_id = $1
            ORDER BY q.id
            """,
            video_id,
        )
        return {"questions": [dict(r) for r in rows], "count": len(rows)}
    finally:
        await conn.close()


@router.delete("/api/admin/videos/{video_id}")
async def delete_processed_video(video_id: int, _admin: dict = Depends(require_admin)):
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        await conn.execute("DELETE FROM question_video WHERE video_id = $1", video_id)
        deleted = await conn.execute(
            "DELETE FROM processed_videos WHERE id = $1", video_id
        )
        if deleted.endswith("0"):
            raise HTTPException(status_code=404, detail="Video not found")
        return {"ok": True}
    finally:
        await conn.close()


@router.patch("/api/admin/videos/{video_id}")
async def update_video(
    video_id: int, data: dict = Body(...), _admin: dict = Depends(require_admin)
):
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        row = await conn.fetchrow(
            """
            UPDATE processed_videos
            SET title = COALESCE($2, title),
                youtube_url = COALESCE($3, youtube_url),
                platform = COALESCE($4, platform)
            WHERE id = $1
            RETURNING id, title, youtube_url, platform
            """,
            video_id,
            data.get("title"),
            data.get("youtube_url"),
            data.get("platform"),
        )
        if not row:
            raise HTTPException(status_code=404, detail="Video not found")
        return dict(row)
    finally:
        await conn.close()


@router.get("/api/admin/stats")
async def get_admin_stats(_admin: dict = Depends(require_admin)):
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        total_questions = await conn.fetchval("SELECT COUNT(*) FROM questions") or 0
        approved_questions = (
            await conn.fetchval("SELECT COUNT(*) FROM questions WHERE approved = TRUE")
            or 0
        )
        total_videos = await conn.fetchval("SELECT COUNT(*) FROM processed_videos") or 0
        total_suggestions = (
            await conn.fetchval("SELECT COUNT(*) FROM video_suggestions") or 0
        )
        open_feedback = (
            await conn.fetchval(
                "SELECT COUNT(*) FROM feedback WHERE is_resolved = FALSE"
            )
            or 0
        )
        return {
            "total_questions": total_questions,
            "approved_questions": approved_questions,
            "total_videos": total_videos,
            "total_suggestions": total_suggestions,
            "open_feedback": open_feedback,
        }
    finally:
        await conn.close()


@router.get("/api/admin/analytics")
async def get_admin_analytics(days: int = 30, _admin: dict = Depends(require_admin)):
    days = int(days or 30)
    if days not in {7, 30, 90}:
        raise HTTPException(status_code=400, detail="days must be one of: 7, 30, 90")

    conn = await asyncpg.connect(DATABASE_URL)
    try:
        key_goal_events = ["open_question", "start_trainer", "submit_mock"]

        def _safe_pct(numerator: float, denominator: float) -> float:
            if not denominator:
                return 0.0
            return round((numerator / denominator) * 100.0, 1)

        by_topic = await conn.fetch(
            """
            SELECT topic, COUNT(*) AS count
            FROM questions
            GROUP BY topic
            ORDER BY count DESC
            """
        )
        by_difficulty = await conn.fetch(
            """
            SELECT difficulty, COUNT(*) AS count
            FROM questions
            GROUP BY difficulty
            ORDER BY count DESC
            """
        )

        user_totals = await conn.fetchrow(
            """
            SELECT
              COUNT(*) AS total,
              COUNT(*) FILTER (WHERE role = 'admin') AS admins,
              COUNT(*) FILTER (WHERE role <> 'admin') AS regular,
                            COUNT(*) FILTER (WHERE created_at >= NOW() - ($1::int * INTERVAL '1 day')) AS registered_period,
                            COUNT(*) FILTER (WHERE last_login IS NOT NULL AND last_login >= NOW() - ($1::int * INTERVAL '1 day')) AS active_period
            FROM users
            """,
            days,
        )

        registrations_period = await conn.fetch(
            """
            SELECT TO_CHAR(created_at::date, 'YYYY-MM-DD') AS day, COUNT(*) AS count
            FROM users
            WHERE created_at >= NOW() - ($1::int * INTERVAL '1 day')
            GROUP BY created_at::date
            ORDER BY created_at::date
            """,
            days,
        )

        logins_period = await conn.fetch(
            """
            SELECT TO_CHAR(last_login::date, 'YYYY-MM-DD') AS day, COUNT(*) AS count
            FROM users
            WHERE last_login IS NOT NULL AND last_login >= NOW() - ($1::int * INTERVAL '1 day')
            GROUP BY last_login::date
            ORDER BY last_login::date
            """,
            days,
        )

        sessions = await conn.fetchrow(
            """
            SELECT
              COUNT(*) AS total_views,
                            COUNT(*) FILTER (WHERE question_id IS NULL) AS page_views,
                            COUNT(*) FILTER (WHERE question_id IS NOT NULL) AS question_views,
              COUNT(DISTINCT user_session) AS unique_sessions,
              COUNT(DISTINCT user_session) FILTER (
                WHERE user_session IS NOT NULL AND user_session IN (SELECT username FROM users)
              ) AS authorized_sessions,
              COUNT(DISTINCT user_session) FILTER (
                WHERE user_session IS NULL OR user_session NOT IN (SELECT username FROM users)
              ) AS anonymous_sessions
            FROM question_views
            """
        )

        daily_views = await conn.fetch(
            """
            SELECT TO_CHAR(viewed_at::date, 'YYYY-MM-DD') AS day, COUNT(*) AS count
            FROM question_views
            WHERE viewed_at >= NOW() - ($1::int * INTERVAL '1 day')
            GROUP BY viewed_at::date
            ORDER BY viewed_at::date
            """,
            days,
        )

        question_daily_views = await conn.fetch(
            """
            SELECT TO_CHAR(viewed_at::date, 'YYYY-MM-DD') AS day, COUNT(*) AS count
            FROM question_views
            WHERE question_id IS NOT NULL AND viewed_at >= NOW() - ($1::int * INTERVAL '1 day')
            GROUP BY viewed_at::date
            ORDER BY viewed_at::date
            """,
            days,
        )

        page_daily_views = await conn.fetch(
            """
            SELECT TO_CHAR(viewed_at::date, 'YYYY-MM-DD') AS day, COUNT(*) AS count
            FROM question_views
            WHERE question_id IS NULL AND viewed_at >= NOW() - ($1::int * INTERVAL '1 day')
            GROUP BY viewed_at::date
            ORDER BY viewed_at::date
            """,
            days,
        )

        trainer = await conn.fetchrow(
            """
            SELECT
              COUNT(DISTINCT user_session) AS unique_users,
              COALESCE(SUM(total_reviews), 0) AS total_reviews
            FROM sr_cards
            """
        )

        community = await conn.fetchrow(
            """
            SELECT
              (SELECT COUNT(*) FROM user_answers) AS total_answers,
              (SELECT COUNT(DISTINCT user_session) FROM answer_votes) AS active_voters
            """
        )

        test_assignments_total = await conn.fetchval(
            "SELECT COUNT(*) FROM test_assignments"
        )

        videos = await conn.fetchrow(
            """
            SELECT
              COUNT(*) AS total,
              COALESCE(ROUND(AVG(questions_count)::numeric, 1), 0) AS avg_questions
            FROM processed_videos
            """
        )

        analytics_events_exists = await conn.fetchval(
            "SELECT to_regclass('public.analytics_events') IS NOT NULL"
        )
        goal_events_totals = []
        goal_events_daily = []
        goal_funnel = {
            "open_question": 0,
            "start_trainer": 0,
            "submit_mock": 0,
            "open_question_sessions": 0,
            "start_trainer_sessions": 0,
            "submit_mock_sessions": 0,
            "start_from_open_pct": 0.0,
            "submit_from_start_pct": 0.0,
            "submit_from_open_pct": 0.0,
        }

        if analytics_events_exists:
            goal_events_totals_raw = await conn.fetch(
                """
                SELECT
                  event_name,
                  COUNT(*)::int AS count,
                  COUNT(DISTINCT user_session)::int AS unique_sessions
                FROM analytics_events
                WHERE created_at >= NOW() - ($1::int * INTERVAL '1 day')
                GROUP BY event_name
                ORDER BY count DESC, event_name
                """,
                days,
            )
            totals_map = {
                str(row["event_name"]): {
                    "event_name": str(row["event_name"]),
                    "count": int(row["count"] or 0),
                    "unique_sessions": int(row["unique_sessions"] or 0),
                }
                for row in goal_events_totals_raw
            }

            for event_name in key_goal_events:
                goal_events_totals.append(
                    totals_map.get(
                        event_name,
                        {
                            "event_name": event_name,
                            "count": 0,
                            "unique_sessions": 0,
                        },
                    )
                )

            # Keep non-key custom events available for diagnostics and future UI toggles.
            for event_name, event_row in totals_map.items():
                if event_name not in key_goal_events:
                    goal_events_totals.append(event_row)

            goal_events_daily_rows = await conn.fetch(
                """
                SELECT
                  TO_CHAR(created_at::date, 'YYYY-MM-DD') AS day,
                  event_name,
                  COUNT(*)::int AS count
                FROM analytics_events
                WHERE created_at >= NOW() - ($1::int * INTERVAL '1 day')
                GROUP BY created_at::date, event_name
                ORDER BY created_at::date, event_name
                """,
                days,
            )
            goal_events_daily = [
                {
                    "day": str(row["day"]),
                    "event_name": str(row["event_name"]),
                    "count": int(row["count"] or 0),
                }
                for row in goal_events_daily_rows
            ]

            open_row = totals_map.get("open_question", {"count": 0, "unique_sessions": 0})
            start_row = totals_map.get("start_trainer", {"count": 0, "unique_sessions": 0})
            submit_row = totals_map.get("submit_mock", {"count": 0, "unique_sessions": 0})

            open_count = int(open_row.get("count", 0) or 0)
            start_count = int(start_row.get("count", 0) or 0)
            submit_count = int(submit_row.get("count", 0) or 0)

            goal_funnel = {
                "open_question": open_count,
                "start_trainer": start_count,
                "submit_mock": submit_count,
                "open_question_sessions": int(open_row.get("unique_sessions", 0) or 0),
                "start_trainer_sessions": int(start_row.get("unique_sessions", 0) or 0),
                "submit_mock_sessions": int(submit_row.get("unique_sessions", 0) or 0),
                "start_from_open_pct": _safe_pct(start_count, open_count),
                "submit_from_start_pct": _safe_pct(submit_count, start_count),
                "submit_from_open_pct": _safe_pct(submit_count, open_count),
            }
        else:
            goal_events_totals = [
                {"event_name": event_name, "count": 0, "unique_sessions": 0}
                for event_name in key_goal_events
            ]

        users = dict(user_totals) if user_totals else {}
        users["registered_30d"] = users.get("registered_period", 0)
        users["active_30d"] = users.get("active_period", 0)
        videos_data = dict(videos) if videos else {"total": 0, "avg_questions": 0}

        return {
            "topics": [{"topic": r["topic"], "count": r["count"]} for r in by_topic],
            "difficulties": [
                {"difficulty": r["difficulty"], "count": r["count"]}
                for r in by_difficulty
            ],
            "users": users,
            "days": days,
            "registrations_30d": [dict(r) for r in registrations_period],
            "logins_30d": [dict(r) for r in logins_period],
            "sessions": dict(sessions) if sessions else {},
            "views_30d": [dict(r) for r in daily_views],
            "question_views_30d": [dict(r) for r in question_daily_views],
            "page_views_30d": [dict(r) for r in page_daily_views],
            "trainer": dict(trainer) if trainer else {"unique_users": 0, "total_reviews": 0},
            "community": dict(community) if community else {"total_answers": 0, "active_voters": 0},
            "test_assignments": {"total": int(test_assignments_total or 0)},
            "videos": {
                "total": int(videos_data.get("total", 0)),
                "avg_questions": float(videos_data.get("avg_questions", 0) or 0),
            },
            "goal_events": {
                "totals": goal_events_totals,
                "daily": goal_events_daily,
                "funnel": goal_funnel,
            },
        }
    finally:
        await conn.close()


@router.post("/api/admin/hh-sync/run")
async def run_hh_sync_now(_admin: dict = Depends(require_admin)):
    if not _env_bool("HH_SYNC_ALLOW_MANUAL", True):
        raise HTTPException(status_code=403, detail="Manual HH sync is disabled")

    import main_new

    svc = getattr(main_new, "hh_sync_service", None)
    if svc is None:
        raise HTTPException(
            status_code=503, detail="HH sync service is not initialized"
        )

    result = await svc.run_once()
    return {"ok": True, **result}
