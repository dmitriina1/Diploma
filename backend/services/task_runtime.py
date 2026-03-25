import asyncio
import json
from datetime import datetime
from typing import Awaitable, Callable, Optional


class TaskRuntime:
    def __init__(self, db_connect, db_release, redis_ttl: int):
        self._db_connect = db_connect
        self._db_release = db_release
        self.redis_ttl = redis_ttl
        self.queue: Optional[asyncio.Queue] = None
        self.worker_task: Optional[asyncio.Task] = None

    async def ensure_runtime_tables(self):
        conn = await self._db_connect()
        try:
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS processing_tasks (
                    id UUID PRIMARY KEY,
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
                """
            )
        finally:
            await self._db_release(conn)

    async def persist_task_snapshot(self, task: dict, client_id: Optional[str] = None):
        task_id = task.get("task_id")
        if not task_id:
            return

        payload = {
            "task_snapshot": task,
            "result": task.get("result"),
        }

        conn = await self._db_connect()
        try:
            await conn.execute(
                """
                INSERT INTO processing_tasks (id, youtube_url, status, progress, current_step, result, error_message, client_id)
                VALUES ($1::uuid, $2, $3, $4, $5, $6::jsonb, $7, $8)
                ON CONFLICT (id) DO UPDATE SET
                    youtube_url = EXCLUDED.youtube_url,
                    status = EXCLUDED.status,
                    progress = EXCLUDED.progress,
                    current_step = EXCLUDED.current_step,
                    result = EXCLUDED.result,
                    error_message = EXCLUDED.error_message,
                    client_id = COALESCE(EXCLUDED.client_id, processing_tasks.client_id),
                    updated_at = CURRENT_TIMESTAMP
                """,
                task_id,
                task.get("youtube_url") or task.get("video_url") or "",
                task.get("status", "pending"),
                task.get("progress", 0),
                task.get("step", ""),
                json.dumps(payload),
                task.get("error"),
                client_id or task.get("client_id"),
            )
        finally:
            await self._db_release(conn)

    async def load_task_snapshot(self, task_id: str):
        conn = await self._db_connect()
        try:
            row = await conn.fetchrow(
                """
                SELECT id::text AS id, youtube_url, status, progress, current_step, result,
                       error_message, client_id, created_at
                FROM processing_tasks
                WHERE id = $1::uuid
                """,
                task_id,
            )
            if not row:
                return None

            raw_result = row.get("result")
            payload = raw_result if isinstance(raw_result, dict) else {}
            task = payload.get("task_snapshot") if isinstance(payload, dict) else None
            if not isinstance(task, dict):
                task = {
                    "task_id": row["id"],
                    "youtube_url": row["youtube_url"],
                    "video_url": row["youtube_url"],
                    "status": row["status"],
                    "progress": row["progress"] or 0,
                    "step": row["current_step"] or "",
                    "result": payload.get("result")
                    if isinstance(payload, dict)
                    else None,
                    "error": row["error_message"],
                    "client_id": row["client_id"],
                    "created_at": row["created_at"].isoformat()
                    if row["created_at"]
                    else datetime.now().isoformat(),
                    "logs": [],
                }

            task["status"] = row["status"]
            task["progress"] = row["progress"] or task.get("progress", 0)
            task["step"] = row["current_step"] or task.get("step", "")
            if row["error_message"]:
                task["error"] = row["error_message"]
            if row["client_id"]:
                task["client_id"] = row["client_id"]
            return task
        finally:
            await self._db_release(conn)

    async def enqueue(self, job: dict):
        if self.queue is None:
            raise RuntimeError("Processing queue is not initialized")
        await self.queue.put(job)

    async def start_worker(
        self,
        video_handler: Callable[..., Awaitable[None]],
        local_handler: Callable[..., Awaitable[None]],
    ):
        self.queue = asyncio.Queue()

        async def worker_loop():
            while True:
                job = await self.queue.get()
                try:
                    if job is None:
                        self.queue.task_done()
                        break

                    kind = job.get("kind")
                    if kind == "video":
                        await video_handler(
                            job["task_id"],
                            job["video_url"],
                            job.get("topic", "General"),
                            job.get("level", "middle"),
                        )
                    elif kind == "local_video":
                        await local_handler(
                            job["task_id"],
                            job["audio_path"],
                            job.get("filename", "video.mp4"),
                            job.get("topic", "General"),
                            job.get("difficulty", "middle"),
                        )
                except Exception as e:
                    print(f"❌ Processing worker error: {e}")
                finally:
                    self.queue.task_done()

        self.worker_task = asyncio.create_task(worker_loop())

    async def stop_worker(self):
        if self.queue is not None:
            await self.queue.put(None)
        if self.worker_task is not None:
            try:
                await self.worker_task
            except Exception:
                pass
        self.worker_task = None
        self.queue = None

    async def recover_pending_tasks(self, redis_client, enqueue_video):
        conn = await self._db_connect()
        try:
            rows = await conn.fetch(
                """
                SELECT id::text AS id
                FROM processing_tasks
                WHERE status IN ('pending', 'queued', 'downloading', 'transcribing', 'extracting', 'saving', 'processing')
                ORDER BY created_at ASC
                """
            )
        finally:
            await self._db_release(conn)

        recovered = 0
        for row in rows:
            task = await self.load_task_snapshot(row["id"])
            if not task:
                continue

            task_id = task["task_id"]
            video_url = task.get("youtube_url") or task.get("video_url") or ""
            if video_url.startswith("local://"):
                task["status"] = "error"
                task["step"] = (
                    "Локальная задача не может быть восстановлена после перезапуска"
                )
                task["error"] = "Local upload cannot be resumed after restart"
                await redis_client.set(
                    f"task:{task_id}", json.dumps(task), ex=self.redis_ttl
                )
                await self.persist_task_snapshot(task)
                continue

            task["status"] = "queued"
            task["step"] = "Восстановлено после перезапуска сервера"
            task.setdefault("logs", []).append(
                {
                    "time": datetime.now().isoformat(),
                    "progress": task.get("progress", 0),
                    "status": "queued",
                    "message": "Задача восстановлена после перезапуска",
                }
            )
            await redis_client.set(
                f"task:{task_id}", json.dumps(task), ex=self.redis_ttl
            )
            await redis_client.lrem("global:tasks", 0, task_id)
            await redis_client.lpush("global:tasks", task_id)
            await redis_client.ltrim("global:tasks", 0, 99)
            await redis_client.expire("global:tasks", self.redis_ttl)
            await self.persist_task_snapshot(task)

            await enqueue_video(
                task_id,
                video_url,
                task.get("topic", "General"),
                task.get("level", "middle"),
            )
            recovered += 1

        if recovered:
            print(f"♻️ Recovered {recovered} pending tasks from database")
