import json
import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from api.deps import get_handler, get_resource
from core.config import REDIS_TTL


router = APIRouter(tags=["Processing"])


class YouTubeRequest(BaseModel):
    youtube_url: str
    topic: Optional[str] = "General"
    level: Optional[str] = "middle"


@router.post("/api/process-video")
async def process_video(request: YouTubeRequest):
    is_valid_video_url = get_handler("is_valid_video_url")
    persist_task_snapshot = get_handler("persist_task_snapshot")
    queue_processing_job = get_handler("queue_processing_job")

    redis_client = get_resource("redis_client")

    task_id = str(uuid.uuid4())
    if not is_valid_video_url(request.youtube_url):
        raise HTTPException(
            status_code=400,
            detail="Invalid video URL. Supported: YouTube, VK.video, Rutube, OK.ru, etc.",
        )

    task_data = {
        "task_id": task_id,
        "youtube_url": request.youtube_url,
        "video_url": request.youtube_url,
        "topic": request.topic,
        "level": request.level,
        "status": "pending",
        "progress": 0,
        "step": "Инициализация...",
        "created_at": __import__("datetime").datetime.now().isoformat(),
        "logs": [
            {
                "time": __import__("datetime").datetime.now().isoformat(),
                "progress": 0,
                "status": "pending",
                "message": "Задача создана",
            }
        ],
    }
    await redis_client.set(f"task:{task_id}", json.dumps(task_data), ex=REDIS_TTL)
    await persist_task_snapshot(task_data)

    await redis_client.lpush("global:tasks", task_id)
    await redis_client.ltrim("global:tasks", 0, 99)
    await redis_client.expire("global:tasks", REDIS_TTL)

    await queue_processing_job(
        {
            "kind": "video",
            "task_id": task_id,
            "video_url": request.youtube_url,
            "topic": request.topic,
            "level": request.level,
        }
    )

    return {"task_id": task_id, "status": "started"}


@router.post("/api/process-video/{client_id}")
async def process_video_with_client(client_id: str, request: YouTubeRequest):
    is_valid_video_url = get_handler("is_valid_video_url")
    persist_task_snapshot = get_handler("persist_task_snapshot")
    queue_processing_job = get_handler("queue_processing_job")
    redis_client = get_resource("redis_client")

    task_id = str(uuid.uuid4())
    if not is_valid_video_url(request.youtube_url):
        raise HTTPException(
            status_code=400,
            detail="Invalid video URL. Supported: YouTube, VK.video, Rutube, OK.ru, etc.",
        )

    task_data = {
        "task_id": task_id,
        "youtube_url": request.youtube_url,
        "video_url": request.youtube_url,
        "topic": request.topic,
        "level": request.level,
        "status": "pending",
        "progress": 0,
        "step": "Инициализация...",
        "created_at": __import__("datetime").datetime.now().isoformat(),
        "client_id": client_id,
    }
    await redis_client.set(f"task:{task_id}", json.dumps(task_data), ex=REDIS_TTL)
    await persist_task_snapshot(task_data, client_id=client_id)

    await redis_client.set(f"task:{task_id}:client", client_id, ex=REDIS_TTL)
    await redis_client.set(f"client:{client_id}:last_task", task_id, ex=REDIS_TTL)
    await redis_client.lpush(f"client:{client_id}:tasks", task_id)
    await redis_client.ltrim(f"client:{client_id}:tasks", 0, 49)
    await redis_client.expire(f"client:{client_id}:tasks", REDIS_TTL)

    await redis_client.lpush("global:tasks", task_id)
    await redis_client.ltrim("global:tasks", 0, 99)
    await redis_client.expire("global:tasks", REDIS_TTL)

    await queue_processing_job(
        {
            "kind": "video",
            "task_id": task_id,
            "video_url": request.youtube_url,
            "topic": request.topic,
            "level": request.level,
        }
    )

    return {"task_id": task_id, "status": "started", "client_id": client_id}


@router.get("/api/export/{task_id}")
async def export_questions_json(task_id: str):
    redis_client = get_resource("redis_client")
    task_data = await redis_client.get(f"task:{task_id}")
    if not task_data:
        raise HTTPException(status_code=404, detail="Task not found")

    task = json.loads(task_data)
    result = task.get("result", {})
    export_data = {
        "task_id": task_id,
        "video_title": result.get("video_title", "Unknown"),
        "questions_count": result.get("questions_count", 0),
        "questions": result.get("questions", []),
    }
    return JSONResponse(
        content=export_data,
        headers={
            "Content-Disposition": f'attachment; filename="questions_{task_id}.json"'
        },
    )


@router.get("/api/transcript/{task_id}")
async def get_transcript(task_id: str):
    redis_client = get_resource("redis_client")
    transcript_data = await redis_client.get(f"transcript:{task_id}")
    if not transcript_data:
        raise HTTPException(status_code=404, detail="Transcript not found")
    data = json.loads(transcript_data)
    return JSONResponse(
        content=data,
        headers={
            "Content-Disposition": f'attachment; filename="transcript_{task_id}.json"'
        },
    )


@router.get("/api/full-export/{task_id}")
async def full_export(task_id: str):
    redis_client = get_resource("redis_client")
    transcript_data = await redis_client.get(f"transcript:{task_id}")
    transcript = json.loads(transcript_data) if transcript_data else {}
    task_data = await redis_client.get(f"task:{task_id}")
    task = json.loads(task_data) if task_data else {}

    export = {
        "task_id": task_id,
        "transcript": transcript.get("transcript", ""),
        "segments": transcript.get("segments", []),
        "video_title": task.get("result", {}).get("video_title", "Unknown"),
        "questions": task.get("result", {}).get("questions", []),
        "questions_count": task.get("result", {}).get("questions_count", 0),
        "status": task.get("status", "unknown"),
    }
    return JSONResponse(
        content=export,
        headers={
            "Content-Disposition": f'attachment; filename="full_export_{task_id}.json"'
        },
    )
