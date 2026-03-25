import re
from typing import Optional

import asyncpg
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from core.config import DATABASE_URL
from similarity_search import get_similar_questions as search_similar_questions


router = APIRouter(tags=["Public"])


def is_valid_video_url(url: str) -> bool:
    patterns = [
        r"(?:youtube\.com/watch\?v=|youtu\.be/)[\w-]+",
        r"(?:vk\.com/video|vkvideo\.ru/video)[\w\-_/]+",
        r"rutube\.ru/video/[\w-]+",
        r"ok\.ru/video/[\w-]+",
    ]
    return any(re.search(p, url.lower()) for p in patterns)


@router.get("/api/questions")
async def get_all_questions(topic: Optional[str] = None, level: Optional[str] = None):
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        query = """
            SELECT id, question, answer, topic, difficulty, probability, timecode
            FROM questions
            WHERE approved = TRUE
        """
        params = []

        if topic:
            query += " AND topic = $1"
            params.append(topic)

        if level:
            idx = len(params) + 1
            query += f" AND difficulty = ${idx}"
            params.append(level)

        query += " ORDER BY probability DESC NULLS LAST, created_at DESC"
        questions = (
            await conn.fetch(query, *params) if params else await conn.fetch(query)
        )

        result = [
            {
                "id": q["id"],
                "question": q["question"],
                "answer": q["answer"],
                "topic": q["topic"],
                "difficulty": q["difficulty"],
                "probability": float(q["probability"]) if q["probability"] else 0.0,
                "timecode": q["timecode"],
            }
            for q in questions
        ]
        return JSONResponse(content={"questions": result, "total": len(result)})
    finally:
        await conn.close()


@router.get("/api/questions/{question_id}")
async def get_public_question_detail(question_id: int):
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        total_videos = await conn.fetchval("SELECT COUNT(*) FROM processed_videos") or 0

        q = await conn.fetchrow(
            """
            SELECT q.id, q.question, q.answer, q.topic, q.difficulty, q.probability,
                   q.timecode, q.source_url, q.video_title, q.created_at,
                   COALESCE(vc.cnt, 0) AS video_count
            FROM questions q
            LEFT JOIN (
                SELECT question_id, COUNT(DISTINCT video_id) AS cnt
                FROM question_video GROUP BY question_id
            ) vc ON vc.question_id = q.id
            WHERE q.id = $1 AND q.approved = TRUE
            """,
            question_id,
        )
        if not q:
            raise HTTPException(status_code=404, detail="Question not found")

        videos = await conn.fetch(
            """
            SELECT pv.id, pv.title, pv.youtube_url, pv.platform,
                   qt.timecode_start, qt.timecode_seconds
            FROM question_video qv
            JOIN processed_videos pv ON pv.id = qv.video_id
            LEFT JOIN question_timecodes qt ON qt.question_id = qv.question_id AND qt.video_id = qv.video_id
            WHERE qv.question_id = $1
            ORDER BY pv.title
            """,
            question_id,
        )

        similar = []
        try:
            similar = await search_similar_questions(q["question"], limit=5)
            similar = [s for s in similar if s.get("id") != question_id]
        except Exception as e:
            print(f"⚠️ Similar search failed: {e}")

        result = {
            "id": q["id"],
            "question": q["question"],
            "answer": q["answer"],
            "topic": q["topic"],
            "difficulty": q["difficulty"],
            "probability": float(q["probability"]) if q["probability"] else 0.0,
            "video_count": q["video_count"],
            "total_videos": total_videos,
            "timecode": q["timecode"],
            "source_url": q["source_url"],
            "video_title": q["video_title"],
            "created_at": q["created_at"].isoformat() if q["created_at"] else None,
            "videos": [
                {
                    "id": v["id"],
                    "title": v["title"],
                    "url": v["youtube_url"],
                    "platform": v["platform"] or "youtube",
                    "timecode": v["timecode_start"] or None,
                    "timecode_seconds": v["timecode_seconds"] or 0,
                }
                for v in videos
            ],
            "similar_questions": similar,
        }
        return JSONResponse(content=result)
    finally:
        await conn.close()


@router.get("/api/questions/similar")
async def get_similar_questions_api(query: str, limit: int = 5):
    try:
        similar = await search_similar_questions(query, limit=limit)
        return JSONResponse(content={"similar_questions": similar})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/suggestions")
async def create_suggestion(data: dict):
    url = (data.get("url") or "").strip()
    if not url or not is_valid_video_url(url):
        raise HTTPException(status_code=400, detail="Invalid video URL")

    conn = await asyncpg.connect(DATABASE_URL)
    try:
        row = await conn.fetchrow(
            """
            INSERT INTO video_suggestions (url, platform, title, topic, difficulty, comment, user_name, user_email, status)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, 'pending')
            RETURNING id, url, topic, difficulty, status, created_at
            """,
            url,
            data.get("platform") or "youtube",
            data.get("title"),
            data.get("topic"),
            data.get("difficulty") or "middle",
            data.get("comment"),
            data.get("user_name"),
            data.get("user_email"),
        )
        result = dict(row)
        result["created_at"] = result["created_at"].isoformat()
        return {"success": True, "suggestion": result}
    finally:
        await conn.close()


@router.get("/api/suggestions")
async def get_suggestions(status: Optional[str] = None):
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        if status:
            rows = await conn.fetch(
                """
                SELECT id, url, platform, title, topic, difficulty, status, created_at
                FROM video_suggestions WHERE status = $1
                ORDER BY created_at DESC
                """,
                status,
            )
        else:
            rows = await conn.fetch(
                """
                SELECT id, url, platform, title, topic, difficulty, status, created_at
                FROM video_suggestions
                ORDER BY created_at DESC
                LIMIT 200
                """
            )
        suggestions = []
        for r in rows:
            d = dict(r)
            if d.get("created_at"):
                d["created_at"] = d["created_at"].isoformat()
            suggestions.append(d)
        return {"suggestions": suggestions, "count": len(suggestions)}
    finally:
        await conn.close()


@router.get("/api/tags")
async def get_tags():
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        tags = await conn.fetch("SELECT DISTINCT tag FROM question_tags ORDER BY tag")
        return {"tags": [r["tag"] for r in tags]}
    finally:
        await conn.close()


@router.get("/api/stats")
async def get_stats():
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        total_questions = (
            await conn.fetchval("SELECT COUNT(*) FROM questions WHERE approved = TRUE")
            or 0
        )
        total_videos = await conn.fetchval("SELECT COUNT(*) FROM processed_videos") or 0
        topics = await conn.fetch(
            """
            SELECT topic, COUNT(*) as count
            FROM questions
            WHERE approved = TRUE
            GROUP BY topic
            ORDER BY count DESC
            """
        )
        return {
            "total_questions": total_questions,
            "total_videos": total_videos,
            "topics": [{"topic": t["topic"], "count": t["count"]} for t in topics],
        }
    finally:
        await conn.close()


@router.get("/api/recordings")
async def get_recordings():
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        rows = await conn.fetch(
            """
            SELECT id, title, youtube_url, platform
            FROM processed_videos
            ORDER BY id DESC
            LIMIT 200
            """
        )
        recordings = []
        for row in rows:
            d = dict(row)
            d["url"] = d.pop("youtube_url")
            d["created_at"] = None
            recordings.append(d)
        return {"recordings": recordings, "count": len(recordings)}
    finally:
        await conn.close()


@router.get("/api/professions")
async def get_professions():
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        rows = await conn.fetch(
            """
            SELECT id, slug, title, icon, color, sort_order
            FROM professions
            ORDER BY sort_order, title
            """
        )
        topics = await conn.fetch(
            """
            SELECT p.slug, pt.topic
            FROM profession_topics pt
            JOIN professions p ON p.id = pt.profession_id
            ORDER BY p.slug, pt.topic
            """
        )
        by_slug = {}
        for t in topics:
            by_slug.setdefault(t["slug"], []).append(t["topic"])

        professions = []
        for r in rows:
            d = dict(r)
            d["topics"] = by_slug.get(r["slug"], [])
            professions.append(d)
        return {"professions": professions, "count": len(professions)}
    finally:
        await conn.close()


@router.get("/api/professions/{slug}/questions")
async def get_profession_questions(
    slug: str, topic: Optional[str] = None, limit: int = 100
):
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        prof = await conn.fetchrow(
            "SELECT id, slug, title FROM professions WHERE slug = $1", slug
        )
        if not prof:
            raise HTTPException(status_code=404, detail="Profession not found")

        topics_rows = await conn.fetch(
            "SELECT topic FROM profession_topics WHERE profession_id = $1 ORDER BY topic",
            prof["id"],
        )
        topics = [r["topic"] for r in topics_rows]
        if not topics:
            return {"profession": dict(prof), "questions": [], "count": 0}

        if topic and topic not in topics:
            return {"profession": dict(prof), "questions": [], "count": 0}

        if topic:
            rows = await conn.fetch(
                """
                SELECT id, question, answer, topic, difficulty, probability, timecode
                FROM questions
                WHERE approved = TRUE AND topic = $1
                ORDER BY probability DESC NULLS LAST, created_at DESC
                LIMIT $2
                """,
                topic,
                limit,
            )
        else:
            rows = await conn.fetch(
                """
                SELECT id, question, answer, topic, difficulty, probability, timecode
                FROM questions
                WHERE approved = TRUE AND topic = ANY($1::text[])
                ORDER BY probability DESC NULLS LAST, created_at DESC
                LIMIT $2
                """,
                topics,
                limit,
            )

        questions = []
        for q in rows:
            questions.append(
                {
                    "id": q["id"],
                    "question": q["question"],
                    "answer": q["answer"],
                    "topic": q["topic"],
                    "difficulty": q["difficulty"],
                    "probability": float(q["probability"]) if q["probability"] else 0.0,
                    "timecode": q["timecode"],
                }
            )

        return {
            "profession": dict(prof),
            "available_topics": topics,
            "selected_topic": topic,
            "questions": questions,
            "count": len(questions),
        }
    finally:
        await conn.close()
