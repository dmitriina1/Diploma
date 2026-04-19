import asyncio
from collections import Counter
from datetime import datetime
from typing import Any

import httpx

from .tech_extractor import extract_from_title, extract_from_description


HH_API_BASE = "https://api.hh.ru"


DEFAULT_PROFESSIONS = [
    "Frontend разработчик",
    "Backend разработчик",
    "Fullstack разработчик",
    "Python разработчик",
    "Java разработчик",
    "Golang разработчик",
    "PHP разработчик",
    "C# разработчик",
    "DevOps инженер",
    "QA тестировщик",
    "Data Scientist",
    "Data Analyst",
    "Системный аналитик",
    "Бизнес-аналитик",
    "Product Manager",
]


def _pick_skill_name(item: Any) -> str:
    if isinstance(item, str):
        return item.strip()
    if isinstance(item, dict):
        return str(item.get("name") or "").strip()
    return ""


async def _fetch_vacancy_key_skills(
    client: httpx.AsyncClient, vacancy_id: str
) -> list[str]:
    try:
        response = await client.get(f"{HH_API_BASE}/vacancies/{vacancy_id}")
        if response.status_code >= 400:
            return []
        data = response.json() or {}
        skills = data.get("key_skills") or []
        return [name for name in (_pick_skill_name(s) for s in skills) if name]
    except Exception:
        return []


class HHSkillsSyncService:
    def __init__(
        self,
        db_connect,
        db_release,
        *,
        enabled: bool,
        interval_hours: int,
        startup_delay_seconds: int,
        max_pages: int,
        per_page: int,
        max_vacancies_per_prof: int,
        top_skills: int,
        http_concurrency: int,
        min_vacancies: int,
    ):
        self._db_connect = db_connect
        self._db_release = db_release
        self.enabled = enabled
        self.interval_seconds = max(1, interval_hours) * 3600
        self.startup_delay_seconds = max(0, startup_delay_seconds)
        self.max_pages = max(1, max_pages)
        self.per_page = max(1, min(per_page, 100))
        self.max_vacancies_per_prof = max(20, max_vacancies_per_prof)
        self.top_skills = max(5, top_skills)
        self.http_concurrency = max(1, http_concurrency)
        self.min_vacancies = max(1, min_vacancies)
        self._task: asyncio.Task | None = None
        self._stop_event = asyncio.Event()

    async def ensure_tables(self):
        conn = await self._db_connect()
        try:
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS hh_sync_runs (
                    id SERIAL PRIMARY KEY,
                    started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    finished_at TIMESTAMP,
                    status VARCHAR(20) NOT NULL DEFAULT 'running',
                    details TEXT
                )
                """
            )
        finally:
            await self._db_release(conn)

    async def start(self):
        if not self.enabled:
            print("ℹ️ HH sync disabled by HH_SYNC_ENABLED=false")
            return
        if self._task and not self._task.done():
            return
        self._stop_event.clear()
        self._task = asyncio.create_task(self._runner())
        print("✅ HH sync scheduler started")

    async def stop(self):
        self._stop_event.set()
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    async def run_once(self) -> dict[str, int]:
        professions = await self._load_professions()
        started_at = datetime.utcnow()
        run_id = await self._save_run_started(started_at, len(professions))
        try:
            result = await self._sync_professions(professions)
            details = (
                f"updated_professions={result['updated_professions']};"
                f"skills_upserted={result['skills_upserted']};"
                f"vacancies_scanned={result['vacancies_scanned']}"
            )
            await self._save_run_finished(run_id, "success", details)
            print(
                "📈 HH sync done: "
                f"professions={result['updated_professions']}, "
                f"skills={result['skills_upserted']}, "
                f"vacancies={result['vacancies_scanned']}"
            )
            return result
        except Exception as e:
            await self._save_run_finished(run_id, "error", str(e)[:1800])
            raise

    async def _runner(self):
        try:
            if self.startup_delay_seconds > 0:
                try:
                    await asyncio.wait_for(
                        self._stop_event.wait(), timeout=self.startup_delay_seconds
                    )
                    return
                except asyncio.TimeoutError:
                    pass

            while not self._stop_event.is_set():
                try:
                    await self.run_once()
                except Exception as e:
                    print(f"⚠️ HH sync failed: {e}")

                try:
                    await asyncio.wait_for(
                        self._stop_event.wait(), timeout=self.interval_seconds
                    )
                except asyncio.TimeoutError:
                    continue
        except asyncio.CancelledError:
            pass

    async def _load_professions(self) -> list[str]:
        conn = await self._db_connect()
        try:
            rows = await conn.fetch(
                """
                SELECT DISTINCT profession
                FROM hh_skills
                WHERE profession IS NOT NULL AND profession <> ''
                ORDER BY profession
                """
            )
            existing_professions = [
                str(r["profession"]).strip() for r in rows if r["profession"]
            ]
        finally:
            await self._db_release(conn)

        merged = []
        seen = set()
        for profession in [*existing_professions, *DEFAULT_PROFESSIONS]:
            normalized = profession.strip()
            if not normalized:
                continue
            key = normalized.casefold()
            if key in seen:
                continue
            seen.add(key)
            merged.append(normalized)

        return merged or DEFAULT_PROFESSIONS

    async def _sync_professions(self, professions: list[str]) -> dict[str, int]:
        semaphore = asyncio.Semaphore(self.http_concurrency)

        async with httpx.AsyncClient(
            timeout=httpx.Timeout(20.0, connect=10.0),
            headers={"User-Agent": "InterviewHub-HHSync/1.0 (+local dev)"},
        ) as client:

            async def wrapped(profession: str):
                async with semaphore:
                    return await self._fetch_profession_skills(client, profession)

            per_prof_results = await asyncio.gather(
                *(wrapped(prof) for prof in professions), return_exceptions=True
            )

        rows_to_upsert: list[tuple[str, str, str, int, int, float]] = []  # Added source field
        vacancies_scanned = 0
        updated_professions = 0

        for profession, prof_result in zip(professions, per_prof_results):
            if isinstance(prof_result, BaseException):
                print(f"⚠️ HH profession sync failed [{profession}]: {prof_result}")
                continue
            if not isinstance(prof_result, dict):
                continue

            skills_counter = prof_result.get("skills_counter") or Counter()
            description_counter = prof_result.get("description_counter") or Counter()
            title_counter = prof_result.get("title_counter") or Counter()
            total_vacancies = int(prof_result.get("total_vacancies") or 0)
            vacancies_scanned += total_vacancies
            if total_vacancies < self.min_vacancies:
                continue

            updated_professions += 1
            
            # Process skills from key_skills
            top_skills = skills_counter.most_common(self.top_skills)
            for skill, count in top_skills:
                pct = round((count / total_vacancies) * 100, 2)
                rows_to_upsert.append((profession, skill, "skills", count, total_vacancies, pct))
            
            # Process techs from description
            top_desc = description_counter.most_common(self.top_skills)
            for tech, count in top_desc:
                pct = round((count / total_vacancies) * 100, 2)
                rows_to_upsert.append((profession, tech, "description", count, total_vacancies, pct))
            
            # Process techs from title
            top_title = title_counter.most_common(self.top_skills)
            for tech, count in top_title:
                pct = round((count / total_vacancies) * 100, 2)
                rows_to_upsert.append((profession, tech, "title", count, total_vacancies, pct))

        if rows_to_upsert:
            await self._upsert_rows_v2(rows_to_upsert)

        return {
            "updated_professions": updated_professions,
            "skills_upserted": len(rows_to_upsert),
            "vacancies_scanned": vacancies_scanned,
        }

    async def _fetch_profession_skills(
        self, client: httpx.AsyncClient, profession: str
    ) -> dict[str, Any]:
        skills_counter: Counter[str] = Counter()
        description_counter: Counter[str] = Counter()
        title_counter: Counter[str] = Counter()
        total_vacancies = 0

        for page in range(self.max_pages):
            if total_vacancies >= self.max_vacancies_per_prof:
                break

            params = {
                "text": profession,
                "area": 113,
                "search_field": "name",
                "per_page": self.per_page,
                "page": page,
                "only_with_salary": "false",
            }
            response = await client.get(f"{HH_API_BASE}/vacancies", params=params)
            response.raise_for_status()
            data = response.json() or {}
            items = data.get("items") or []
            if not items:
                break

            for vacancy in items:
                # Extract from key_skills
                key_skills = vacancy.get("key_skills") or []
                if not key_skills and vacancy.get("id"):
                    key_skills = await _fetch_vacancy_key_skills(
                        client, str(vacancy.get("id"))
                    )
                for raw_skill in key_skills:
                    skill_name = _pick_skill_name(raw_skill)
                    if skill_name:
                        skills_counter[skill_name] += 1

                # Extract from title
                title = vacancy.get("name") or ""
                if title:
                    title_techs = extract_from_title(title)
                    for tech in title_techs:
                        title_counter[tech] += 1

                # Extract from description (snippet)
                snippet = vacancy.get("snippet") or {}
                requirement = snippet.get("requirement") or ""
                responsibility = snippet.get("responsibility") or ""
                description_text = f"{requirement} {responsibility}"
                if description_text.strip():
                    desc_techs = extract_from_description(description_text)
                    for tech in desc_techs:
                        description_counter[tech] += 1

                total_vacancies += 1
                if total_vacancies >= self.max_vacancies_per_prof:
                    break

            pages_total = int(data.get("pages") or 0)
            if page + 1 >= pages_total:
                break

        return {
            "skills_counter": skills_counter,
            "description_counter": description_counter,
            "title_counter": title_counter,
            "total_vacancies": total_vacancies,
        }

    async def _upsert_rows(self, rows: list[tuple[str, str, int, int, float]]):
        """Legacy method for backward compatibility - inserts into hh_skills"""
        conn = await self._db_connect()
        try:
            await conn.executemany(
                """
                INSERT INTO hh_skills (profession, skill, vacancy_count, total_vacancies, percentage, updated_at)
                VALUES ($1, $2, $3, $4, $5, CURRENT_TIMESTAMP)
                ON CONFLICT (profession, skill) DO UPDATE SET
                    vacancy_count = EXCLUDED.vacancy_count,
                    total_vacancies = EXCLUDED.total_vacancies,
                    percentage = EXCLUDED.percentage,
                    updated_at = CURRENT_TIMESTAMP
                """,
                rows,
            )
        finally:
            await self._db_release(conn)

    async def _upsert_rows_v2(self, rows: list[tuple[str, str, str, int, int, float]]):
        """New method - inserts into hh_tech_mentions with source field"""
        conn = await self._db_connect()
        try:
            await conn.executemany(
                """
                INSERT INTO hh_tech_mentions (profession, technology, source, vacancy_count, total_vacancies, percentage, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, CURRENT_TIMESTAMP)
                ON CONFLICT (profession, technology, source) DO UPDATE SET
                    vacancy_count = EXCLUDED.vacancy_count,
                    total_vacancies = EXCLUDED.total_vacancies,
                    percentage = EXCLUDED.percentage,
                    updated_at = CURRENT_TIMESTAMP
                """,
                rows,
            )
        finally:
            await self._db_release(conn)

    async def _save_run_started(
        self, started_at: datetime, professions_count: int
    ) -> int:
        conn = await self._db_connect()
        try:
            row = await conn.fetchrow(
                """
                INSERT INTO hh_sync_runs (started_at, status, details)
                VALUES ($1, 'running', $2)
                RETURNING id
                """,
                started_at,
                f"professions={professions_count}",
            )
            return int(row["id"])
        finally:
            await self._db_release(conn)

    async def _save_run_finished(self, run_id: int, status: str, details: str):
        conn = await self._db_connect()
        try:
            await conn.execute(
                """
                UPDATE hh_sync_runs
                SET finished_at = CURRENT_TIMESTAMP,
                    status = $2,
                    details = $3
                WHERE id = $1
                """,
                run_id,
                status,
                details,
            )
        finally:
            await self._db_release(conn)
