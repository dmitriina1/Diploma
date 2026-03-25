import json

from fastapi import APIRouter, HTTPException


router = APIRouter(tags=["Status"])

_state = {
    "redis_client": None,
    "load_task_snapshot": None,
    "db_connect": None,
    "db_release": None,
    "redis_ttl": 86400,
}


def configure_status_routes(
    redis_client, load_task_snapshot, db_connect, db_release, redis_ttl: int
):
    _state["redis_client"] = redis_client
    _state["load_task_snapshot"] = load_task_snapshot
    _state["db_connect"] = db_connect
    _state["db_release"] = db_release
    _state["redis_ttl"] = redis_ttl


def _get_redis():
    if _state["redis_client"] is None:
        raise HTTPException(status_code=503, detail="Redis is not initialized")
    return _state["redis_client"]


@router.get("/api/task/{task_id}")
async def get_task_status(task_id: str):
    redis_client = _get_redis()
    task_data = await redis_client.get(f"task:{task_id}")
    if not task_data:
        restored = await _state["load_task_snapshot"](task_id)
        if not restored:
            raise HTTPException(status_code=404, detail="Task not found")
        await redis_client.set(
            f"task:{task_id}", json.dumps(restored), ex=_state["redis_ttl"]
        )
        return restored
    return json.loads(task_data)


@router.get("/api/last-result/{client_id}")
async def get_last_result(client_id: str):
    redis_client = _get_redis()
    task_id = await redis_client.get(f"client:{client_id}:last_task")
    if not task_id:
        raise HTTPException(status_code=404, detail="No tasks for this client")

    task_data = await redis_client.get(f"task:{task_id}")
    if not task_data:
        restored = await _state["load_task_snapshot"](task_id)
        if not restored:
            raise HTTPException(status_code=404, detail="Task not found")
        await redis_client.set(
            f"task:{task_id}", json.dumps(restored), ex=_state["redis_ttl"]
        )
        return restored
    return json.loads(task_data)


@router.get("/api/tasks/{client_id}")
async def get_client_tasks(client_id: str):
    redis_client = _get_redis()
    tasks_key = f"client:{client_id}:tasks"
    task_ids = await redis_client.lrange(tasks_key, 0, 19)

    tasks = []
    for task_id in task_ids:
        task_data = await redis_client.get(f"task:{task_id}")
        if task_data:
            task = json.loads(task_data)
            tasks.append(
                {
                    "task_id": task_id,
                    "status": task.get("status"),
                    "progress": task.get("progress"),
                    "video_title": task.get("result", {}).get(
                        "video_title", "Processing..."
                    ),
                }
            )
        else:
            restored = await _state["load_task_snapshot"](task_id)
            if restored:
                await redis_client.set(
                    f"task:{task_id}", json.dumps(restored), ex=_state["redis_ttl"]
                )
                tasks.append(
                    {
                        "task_id": task_id,
                        "status": restored.get("status"),
                        "progress": restored.get("progress"),
                        "video_title": restored.get("result", {}).get(
                            "video_title", "Processing..."
                        ),
                    }
                )

    return {"tasks": tasks, "count": len(tasks)}


@router.get("/api/all-tasks")
async def get_all_tasks():
    redis_client = _get_redis()
    task_ids = await redis_client.lrange("global:tasks", 0, 99)
    if task_ids:
        seen = set()
        unique_ids = []
        for task_id in task_ids:
            if task_id in seen:
                continue
            seen.add(task_id)
            unique_ids.append(task_id)
        task_ids = unique_ids

    if not task_ids:
        conn = await _state["db_connect"]()
        try:
            db_ids = await conn.fetch(
                "SELECT id::text AS id FROM processing_tasks ORDER BY created_at DESC LIMIT 100"
            )
            task_ids = [row["id"] for row in db_ids]
        finally:
            await _state["db_release"](conn)

    tasks = []
    for task_id in task_ids:
        task_data = await redis_client.get(f"task:{task_id}")
        if task_data:
            task = json.loads(task_data)
            tasks.append(
                {
                    "task_id": task_id,
                    "video_url": task.get("video_url") or task.get("youtube_url", ""),
                    "status": task.get("status", "unknown"),
                    "progress": task.get("progress", 0),
                    "step": task.get("step", ""),
                    "logs": task.get("logs", []),
                    "created_at": task.get("created_at"),
                    "result": task.get("result"),
                    "error": task.get("error"),
                }
            )
        else:
            restored = await _state["load_task_snapshot"](task_id)
            if restored:
                await redis_client.set(
                    f"task:{task_id}", json.dumps(restored), ex=_state["redis_ttl"]
                )
                tasks.append(
                    {
                        "task_id": task_id,
                        "video_url": restored.get("video_url")
                        or restored.get("youtube_url", ""),
                        "status": restored.get("status", "unknown"),
                        "progress": restored.get("progress", 0),
                        "step": restored.get("step", ""),
                        "logs": restored.get("logs", []),
                        "created_at": restored.get("created_at"),
                        "result": restored.get("result"),
                        "error": restored.get("error"),
                    }
                )

    return {"tasks": tasks, "count": len(tasks)}
