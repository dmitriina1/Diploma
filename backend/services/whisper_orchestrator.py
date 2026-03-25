import asyncio
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional

import httpx


WHISPER_BASE_URL = os.getenv("WHISPER_BASE_URL", "http://whisper-worker")


class WhisperWorker:
    """Один Whisper-воркер, обрабатывающий одну задачу полностью"""

    def __init__(self, worker_id: str, port: int):
        self.worker_id = worker_id
        self.port = port
        self.url = (
            f"{WHISPER_BASE_URL}:{port}"
            if ":" not in WHISPER_BASE_URL
            else WHISPER_BASE_URL
        )
        self.is_busy = False
        self.current_task_id: Optional[str] = None
        self.last_used = time.time()
        self.is_ready = False

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.url}/health")
                if response.status_code == 200:
                    self.is_ready = True
                    return True
        except Exception:
            pass
        self.is_ready = False
        return False

    async def transcribe(
        self, audio_path: Path, language: str = "ru"
    ) -> Dict[str, Any]:
        if not self.is_ready:
            raise Exception(f"Worker {self.worker_id} not ready")

        self.is_busy = True
        self.last_used = time.time()

        try:
            async with httpx.AsyncClient(timeout=7200.0) as client:
                response = await client.post(
                    f"{self.url}/transcribe-path",
                    params={"audio_path": str(audio_path), "language": language},
                )

                if response.status_code != 200:
                    raise Exception(f"Transcription failed: {response.text}")

                return response.json()
        finally:
            self.is_busy = False
            self.last_used = time.time()


class WhisperOrchestrator:
    def __init__(self, max_workers: int = 2):
        self.max_workers = max_workers
        self.workers: Dict[str, WhisperWorker] = {}
        self.task_queue: asyncio.Queue = asyncio.Queue()
        self._lock = asyncio.Lock()
        self.next_worker_id = 1

    async def initialize(self):
        print(f"🚀 Initializing WhisperOrchestrator (max_workers={self.max_workers})")
        asyncio.create_task(self._create_worker())
        print("✅ WhisperOrchestrator ready (worker warmup in background)")

    async def _create_worker(self) -> Optional[WhisperWorker]:
        if len(self.workers) >= self.max_workers:
            print(f"⚠️ Already at max workers ({self.max_workers})")
            return None

        async with self._lock:
            worker_id = f"w{self.next_worker_id}"
            self.next_worker_id += 1
            port = 8001
            worker = WhisperWorker(worker_id, port)

            print(f"📦 Creating worker {worker_id}...")

            for _ in range(24):
                if await worker.health_check():
                    print(f"✅ Worker {worker_id} ready!")
                    self.workers[worker_id] = worker
                    return worker
                await asyncio.sleep(5)

            print(f"❌ Worker {worker_id} failed to start")
            return None

    async def get_available_worker(self) -> Optional[WhisperWorker]:
        for worker in self.workers.values():
            if not worker.is_busy and worker.is_ready:
                return worker

        if len(self.workers) < self.max_workers:
            return await self._create_worker()

        return None

    async def transcribe_audio(
        self, audio_path: Path, task_id: str, language: str = "ru"
    ) -> Dict[str, Any]:
        print(f"🎤 Requesting transcription for task {task_id}: {audio_path.name}")

        worker = await self.get_available_worker()
        if not worker:
            print("⏳ No available workers, waiting...")
            for _ in range(720):
                await asyncio.sleep(5)
                worker = await self.get_available_worker()
                if worker:
                    break

            if not worker:
                raise Exception("No available workers after 1 hour wait")

        print(f"🎯 Using worker {worker.worker_id} for task {task_id}")
        worker.current_task_id = task_id

        try:
            result = await worker.transcribe(audio_path, language)
            print(f"✅ Transcription complete on worker {worker.worker_id}")
            return result
        finally:
            worker.current_task_id = None
