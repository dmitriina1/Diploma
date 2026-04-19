"""
AI Interview Chatbot Service.

Runs on LLM when provider keys are available and falls back to
deterministic local interview logic when they are not.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

import httpx


class InterviewChatbot:
    def __init__(
        self,
        db_connect,
        db_release,
        similarity_search,
        llm_provider: str = "auto",
        openrouter_api_key: Optional[str] = None,
        gemini_api_key: Optional[str] = None,
        groq_api_key: Optional[str] = None,
    ):
        self._db_connect = db_connect
        self._db_release = db_release
        self._similarity_search = similarity_search

        self.llm_provider = (llm_provider or "auto").strip().lower()
        self.openrouter_api_key = (openrouter_api_key or "").strip()
        self.gemini_api_key = (gemini_api_key or "").strip()
        self.groq_api_key = (groq_api_key or "").strip()

        self._provider_priority = ["openrouter", "gemini", "groq"]

    async def ensure_runtime_tables(self) -> None:
        """Create required runtime tables for interview chat if migrations were skipped."""
        conn = await self._db_connect()
        try:
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS interview_chat_sessions (
                    id SERIAL PRIMARY KEY,
                    user_session VARCHAR(255) NOT NULL,
                    topic VARCHAR(255) NOT NULL,
                    difficulty VARCHAR(20) NOT NULL,
                    messages TEXT NOT NULL,
                    status VARCHAR(20) NOT NULL DEFAULT 'active',
                    summary TEXT,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            await conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_interview_chat_user ON interview_chat_sessions(user_session)"
            )
            await conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_interview_chat_status ON interview_chat_sessions(status)"
            )
            await conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_interview_chat_created ON interview_chat_sessions(created_at DESC)"
            )
            await conn.execute(
                """
                CREATE OR REPLACE FUNCTION update_interview_chat_updated_at()
                RETURNS TRIGGER AS $$
                BEGIN
                    NEW.updated_at = CURRENT_TIMESTAMP;
                    RETURN NEW;
                END;
                $$ LANGUAGE plpgsql;
                """
            )
            await conn.execute(
                "DROP TRIGGER IF EXISTS trigger_interview_chat_updated_at ON interview_chat_sessions"
            )
            await conn.execute(
                """
                CREATE TRIGGER trigger_interview_chat_updated_at
                BEFORE UPDATE ON interview_chat_sessions
                FOR EACH ROW
                EXECUTE FUNCTION update_interview_chat_updated_at();
                """
            )
        finally:
            await self._db_release(conn)

    # --------------------------
    # Prompt and question pools
    # --------------------------
    def _build_system_prompt(self, topic: str, difficulty: str) -> str:
        return (
            "Ты — опытный технический интервьюер в IT-компании. "
            f"Проведи собеседование по теме '{topic}' для уровня {difficulty}.\n\n"
            "ПРАВИЛА:\n"
            "1) Задавай один вопрос за раз\n"
            "2) После ответа давай краткий feedback\n"
            "3) Уточняй, если ответ поверхностный\n"
            "4) Оценивай понимание, а не зубрежку\n"
            "5) Веди диалог на русском\n"
            "6) Не пиши длинные лекции\n"
            "7) Начни с приветствия и первого вопроса"
        )

    def _topic_key(self, topic: str) -> str:
        key = (topic or "").strip().lower()
        if "python" in key:
            return "python"
        if "javascript" in key or "js" in key:
            return "javascript"
        if "java" in key and "javascript" not in key:
            return "java"
        if "go" in key or "golang" in key:
            return "go"
        if "react" in key:
            return "react"
        if "vue" in key:
            return "vue"
        if "node" in key:
            return "node"
        if "system design" in key or "архитект" in key:
            return "system_design"
        if "docker" in key:
            return "docker"
        if "postgres" in key or "sql" in key:
            return "database"
        return "default"

    def _fallback_question(self, topic: str, index: int = 0) -> str:
        pools = {
            "python": [
                "Объясни разницу между list и tuple в Python и когда что использовать.",
                "Что такое GIL и как он влияет на CPU-bound задачи?",
                "Как работает async/await в Python и в каких случаях это полезно?",
            ],
            "javascript": [
                "Чем отличаются var, let и const?",
                "Что такое event loop в JavaScript?",
                "Как работает замыкание и где его удобно применять?",
            ],
            "java": [
                "В чем разница между JDK, JRE и JVM?",
                "Объясни, как работает garbage collector в Java на базовом уровне.",
                "Чем интерфейс отличается от абстрактного класса?",
            ],
            "go": [
                "Как устроены goroutine и чем они отличаются от потоков ОС?",
                "Когда использовать channel, а когда mutex?",
                "Что такое context в Go и зачем он нужен в сервисах?",
            ],
            "react": [
                "Чем отличаются state и props?",
                "Зачем нужны key в списках React-компонентов?",
                "Когда использовать useMemo и useCallback?",
            ],
            "vue": [
                "Чем отличаются computed и watch во Vue?",
                "Когда уместнее использовать Pinia, а когда локальное состояние?",
                "Как организовать переиспользуемую логику с Composition API?",
            ],
            "node": [
                "Почему Node.js хорошо подходит для I/O-bound задач?",
                "Как ты обрабатываешь ошибки в async обработчиках API?",
                "Как ограничить количество запросов к одному endpoint?",
            ],
            "system_design": [
                "Как бы ты спроектировал сокращатель ссылок (URL shortener)?",
                "Как обеспечить масштабируемость API при росте трафика?",
                "Какие компромиссы между consistency и availability ты учитываешь?",
            ],
            "docker": [
                "Чем отличается образ от контейнера?",
                "Как уменьшить размер Docker-образа для production?",
                "Какие риски безопасности есть при запуске контейнеров от root?",
            ],
            "database": [
                "В чем разница между индексом B-tree и Hash?",
                "Когда лучше выбрать транзакции с уровнем isolation выше default?",
                "Как ты ищешь причину медленного SQL-запроса?",
            ],
            "default": [
                "Расскажи о проекте, которым ты больше всего гордишься, и своей роли в нем.",
                "Как ты подходишь к отладке сложной ошибки в продакшене?",
                "Какие практики помогают тебе писать поддерживаемый код?",
            ],
        }
        bucket = pools.get(self._topic_key(topic), pools["default"])
        return bucket[index % len(bucket)]

    # --------------------------
    # Provider selection
    # --------------------------
    def _available_providers(self) -> List[str]:
        providers = []
        if self.openrouter_api_key:
            providers.append("openrouter")
        if self.gemini_api_key:
            providers.append("gemini")
        if self.groq_api_key:
            providers.append("groq")
        return providers

    def _provider_chain(self) -> List[str]:
        available = self._available_providers()
        if not available:
            return []

        if self.llm_provider and self.llm_provider != "auto":
            if self.llm_provider in available:
                ordered = [self.llm_provider]
                ordered.extend(
                    [
                        p
                        for p in self._provider_priority
                        if p in available and p != self.llm_provider
                    ]
                )
                return ordered

        return [p for p in self._provider_priority if p in available]

    # --------------------------
    # DB helpers
    # --------------------------
    async def _get_relevant_questions(
        self, topic: str, difficulty: str, limit: int = 6
    ) -> List[Dict[str, Any]]:
        conn = await self._db_connect()
        try:
            strict_rows = await conn.fetch(
                """
                SELECT id, question, answer, topic, difficulty, probability
                FROM questions
                WHERE approved = true
                  AND topic ILIKE $1
                  AND difficulty = $2
                ORDER BY probability DESC, id DESC
                LIMIT $3
                """,
                f"%{topic}%",
                difficulty,
                limit,
            )
            if strict_rows:
                return [dict(row) for row in strict_rows]

            topic_rows = await conn.fetch(
                """
                SELECT id, question, answer, topic, difficulty, probability
                FROM questions
                WHERE approved = true
                  AND topic ILIKE $1
                ORDER BY probability DESC, id DESC
                LIMIT $2
                """,
                f"%{topic}%",
                limit,
            )
            if topic_rows:
                return [dict(row) for row in topic_rows]

            generic_rows = await conn.fetch(
                """
                SELECT id, question, answer, topic, difficulty, probability
                FROM questions
                WHERE approved = true
                ORDER BY probability DESC, id DESC
                LIMIT $1
                """,
                limit,
            )
            return [dict(row) for row in generic_rows]
        finally:
            await self._db_release(conn)

    @staticmethod
    def _safe_load_messages(raw: Any) -> List[Dict[str, str]]:
        if not raw:
            return []

        try:
            parsed = json.loads(raw) if isinstance(raw, str) else raw
        except json.JSONDecodeError:
            return []

        if not isinstance(parsed, list):
            return []

        clean = []
        for item in parsed:
            if not isinstance(item, dict):
                continue
            role = str(item.get("role", "")).strip()
            content = str(item.get("content", "")).strip()
            if not role or not content:
                continue
            clean.append({"role": role, "content": content})
        return clean

    @staticmethod
    def _dump_messages(messages: List[Dict[str, str]]) -> str:
        return json.dumps(messages, ensure_ascii=False)

    # --------------------------
    # LLM callers
    # --------------------------
    @staticmethod
    def _extract_openai_message(data: Dict[str, Any]) -> str:
        choices = data.get("choices") or []
        if not choices:
            raise RuntimeError("LLM response has no choices")

        message = choices[0].get("message") or {}
        content = message.get("content", "")

        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, dict):
                    text = item.get("text") or item.get("content") or ""
                    if text:
                        parts.append(str(text))
                elif isinstance(item, str):
                    parts.append(item)
            content = "\n".join(parts)
        elif not isinstance(content, str):
            content = str(content)

        content = content.strip()
        if not content:
            raise RuntimeError("LLM response is empty")
        return content

    @staticmethod
    def _extract_gemini_message(data: Dict[str, Any]) -> str:
        candidates = data.get("candidates") or []
        if not candidates:
            raise RuntimeError("Gemini response has no candidates")

        parts = (candidates[0].get("content") or {}).get("parts") or []
        text_parts = []
        for part in parts:
            if isinstance(part, dict) and part.get("text"):
                text_parts.append(str(part["text"]))

        content = "\n".join(text_parts).strip()
        if not content:
            raise RuntimeError("Gemini response is empty")
        return content

    async def _call_openrouter(
        self, messages: List[Dict[str, str]], temperature: float
    ) -> str:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.openrouter_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "openai/gpt-4o-mini",
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": 700,
                },
            )

        if response.status_code >= 400:
            detail = response.text[:320]
            raise RuntimeError(f"OpenRouter {response.status_code}: {detail}")

        return self._extract_openai_message(response.json())

    async def _call_groq(
        self, messages: List[Dict[str, str]], temperature: float
    ) -> str:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.groq_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "llama-3.1-70b-versatile",
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": 700,
                },
            )

        if response.status_code >= 400:
            detail = response.text[:320]
            raise RuntimeError(f"Groq {response.status_code}: {detail}")

        return self._extract_openai_message(response.json())

    async def _call_gemini(
        self, messages: List[Dict[str, str]], temperature: float
    ) -> str:
        system_parts: List[str] = []
        contents: List[Dict[str, Any]] = []

        for msg in messages:
            role = (msg.get("role") or "").strip()
            text = (msg.get("content") or "").strip()
            if not text:
                continue

            if role == "system":
                system_parts.append(text)
                continue

            gem_role = "model" if role == "assistant" else "user"
            contents.append({"role": gem_role, "parts": [{"text": text}]})

        if not contents:
            contents.append(
                {
                    "role": "user",
                    "parts": [
                        {"text": "Начни техническое интервью с первого вопроса."}
                    ],
                }
            )

        payload: Dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": 700,
            },
        }
        if system_parts:
            payload["system_instruction"] = {
                "parts": [{"text": "\n\n".join(system_parts)}]
            }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                (
                    "https://generativelanguage.googleapis.com/v1beta/models/"
                    f"gemini-2.0-flash-exp:generateContent?key={self.gemini_api_key}"
                ),
                headers={"Content-Type": "application/json"},
                json=payload,
            )

        if response.status_code >= 400:
            detail = response.text[:320]
            raise RuntimeError(f"Gemini {response.status_code}: {detail}")

        return self._extract_gemini_message(response.json())

    async def _call_llm(
        self, messages: List[Dict[str, str]], temperature: float = 0.7
    ) -> str:
        providers = self._provider_chain()
        if not providers:
            raise RuntimeError("No LLM provider configured")

        errors = []
        for provider in providers:
            try:
                if provider == "openrouter":
                    return await self._call_openrouter(messages, temperature)
                if provider == "gemini":
                    return await self._call_gemini(messages, temperature)
                if provider == "groq":
                    return await self._call_groq(messages, temperature)
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{provider}: {exc}")

        raise RuntimeError("; ".join(errors) if errors else "All providers failed")

    # --------------------------
    # Local fallback mode
    # --------------------------
    def _fallback_feedback(self, user_message: str, difficulty: str) -> str:
        words = len(user_message.split())
        if words < 8:
            base = "Ответ получился коротким. Добавьте больше контекста: причины, компромиссы и практический пример."
        elif words < 20:
            base = "Неплохой ответ. Чтобы усилить его, раскройте внутренние механизмы и ограничения подхода."
        else:
            base = "Хорошо структурированный ответ. Видно понимание темы и практики применения."

        if difficulty == "senior":
            return (
                base
                + " Для senior-уровня добавьте оценку рисков, производительности и эксплуатационных trade-off."
            )
        if difficulty == "junior":
            return (
                base
                + " Для junior-уровня достаточно добавить 1 конкретный пример из практики."
            )
        return base

    def _build_fallback_opening(
        self, topic: str, difficulty: str, relevant_questions: List[Dict[str, Any]]
    ) -> str:
        first_question = (
            relevant_questions[0].get("question") if relevant_questions else None
        ) or self._fallback_question(topic, 0)
        return (
            f"Привет! Проведем интервью по теме '{topic}' ({difficulty}). "
            "Буду задавать по одному вопросу и давать короткий feedback.\n\n"
            f"Первый вопрос:\n{first_question}"
        )

    def _build_fallback_reply(
        self,
        topic: str,
        difficulty: str,
        user_message: str,
        messages: List[Dict[str, str]],
        relevant_questions: List[Dict[str, Any]],
    ) -> str:
        user_count = len([m for m in messages if m.get("role") == "user"])
        feedback = self._fallback_feedback(user_message, difficulty)

        question_pool = [
            q.get("question") for q in relevant_questions if q.get("question")
        ]
        if question_pool:
            next_question = question_pool[user_count % len(question_pool)]
        else:
            next_question = self._fallback_question(topic, user_count)

        return f"{feedback}\n\nСледующий вопрос:\n{next_question}"

    def _build_fallback_summary(
        self, messages: List[Dict[str, str]], difficulty: str
    ) -> str:
        user_answers = [
            m.get("content", "") for m in messages if m.get("role") == "user"
        ]
        if not user_answers:
            return (
                "**Сильные стороны**\n"
                "- Вы начали интервью и дошли до этапа оценки.\n\n"
                "**Что улучшить**\n"
                "- Дайте больше развернутых ответов, чтобы корректно оценить уровень.\n\n"
                "**Оценка:** 5/10\n\n"
                "**Рекомендации**\n"
                "- Пройдите еще одну сессию и отвечайте с примерами из практики."
            )

        avg_words = sum(len(a.split()) for a in user_answers) / max(
            len(user_answers), 1
        )
        score = 6
        if avg_words >= 28:
            score = 8
        elif avg_words >= 18:
            score = 7
        elif avg_words <= 8:
            score = 5

        if difficulty == "senior" and score > 7:
            score = 7
        if difficulty == "junior" and score < 6:
            score = 6

        return (
            "**Сильные стороны**\n"
            "- Ответы в целом последовательные и по теме.\n"
            "- Видно стремление объяснять, а не просто перечислять термины.\n\n"
            "**Что улучшить**\n"
            "- Добавляйте больше архитектурных trade-off и метрик (latency, throughput, reliability).\n"
            "- После каждого тезиса приводите короткий практический пример.\n\n"
            f"**Оценка:** {score}/10\n\n"
            "**Рекомендации**\n"
            "- Отработайте 10-15 типовых вопросов по вашей специализации.\n"
            "- Тренируйте структуру ответа: контекст -> решение -> ограничения -> результат."
        )

    # --------------------------
    # Public service API
    # --------------------------
    async def start_interview(
        self, topic: str, difficulty: str, user_session: str
    ) -> Dict[str, Any]:
        relevant_questions = await self._get_relevant_questions(
            topic, difficulty, limit=10
        )

        system_prompt = self._build_system_prompt(topic, difficulty)
        if relevant_questions:
            context_lines = ["\n\nПРИМЕРЫ ВОПРОСОВ ИЗ БАЗЫ (не задавай дословно):"]
            for item in relevant_questions[:5]:
                q_text = (item.get("question") or "").strip()
                if q_text:
                    context_lines.append(f"- {q_text}")
            system_prompt += "\n".join(context_lines)

        messages = [{"role": "system", "content": system_prompt}]

        try:
            first_message = await self._call_llm(messages)
        except Exception as exc:  # noqa: BLE001
            print(f"⚠️ Interview chatbot switched to local mode: {exc}")
            first_message = self._build_fallback_opening(
                topic, difficulty, relevant_questions
            )

        messages.append({"role": "assistant", "content": first_message})

        conn = await self._db_connect()
        try:
            interview_id = await conn.fetchval(
                """
                INSERT INTO interview_chat_sessions
                (user_session, topic, difficulty, messages, status, created_at)
                VALUES ($1, $2, $3, $4, 'active', CURRENT_TIMESTAMP)
                RETURNING id
                """,
                user_session,
                topic,
                difficulty,
                self._dump_messages(messages),
            )
        finally:
            await self._db_release(conn)

        return {
            "interview_id": interview_id,
            "message": first_message,
            "topic": topic,
            "difficulty": difficulty,
        }

    async def send_message(
        self, interview_id: int, user_message: str, user_session: str
    ) -> Dict[str, Any]:
        conn = await self._db_connect()
        try:
            row = await conn.fetchrow(
                """
                SELECT id, topic, difficulty, messages, status
                FROM interview_chat_sessions
                WHERE id = $1 AND user_session = $2
                """,
                interview_id,
                user_session,
            )

            if not row:
                raise ValueError("Interview session not found")
            if row["status"] != "active":
                raise ValueError("Interview session is not active")

            topic = row["topic"]
            difficulty = row["difficulty"]
            messages = self._safe_load_messages(row["messages"])
            messages.append({"role": "user", "content": user_message})

            try:
                assistant_message = await self._call_llm(messages)
            except Exception as exc:  # noqa: BLE001
                print(f"⚠️ Interview chatbot local reply mode: {exc}")
                relevant_questions = await self._get_relevant_questions(
                    topic, difficulty, limit=10
                )
                assistant_message = self._build_fallback_reply(
                    topic=topic,
                    difficulty=difficulty,
                    user_message=user_message,
                    messages=messages,
                    relevant_questions=relevant_questions,
                )

            messages.append({"role": "assistant", "content": assistant_message})

            await conn.execute(
                """
                UPDATE interview_chat_sessions
                SET messages = $1, updated_at = CURRENT_TIMESTAMP
                WHERE id = $2
                """,
                self._dump_messages(messages),
                interview_id,
            )

            return {
                "interview_id": interview_id,
                "message": assistant_message,
                "message_count": len([m for m in messages if m["role"] == "user"]),
            }
        finally:
            await self._db_release(conn)

    async def end_interview(
        self, interview_id: int, user_session: str
    ) -> Dict[str, Any]:
        conn = await self._db_connect()
        try:
            row = await conn.fetchrow(
                """
                SELECT id, topic, difficulty, messages
                FROM interview_chat_sessions
                WHERE id = $1 AND user_session = $2
                """,
                interview_id,
                user_session,
            )

            if not row:
                raise ValueError("Interview session not found")

            difficulty = row["difficulty"]
            messages = self._safe_load_messages(row["messages"])
            summary_prompt = (
                "Подведи итоги интервью.\n"
                "1) Сильные стороны\n"
                "2) Области для улучшения\n"
                "3) Оценка 1-10\n"
                "4) Практичные рекомендации\n"
                "Ответ дай на русском, кратко и структурированно."
            )

            llm_messages = messages + [{"role": "user", "content": summary_prompt}]
            try:
                summary = await self._call_llm(llm_messages, temperature=0.25)
            except Exception as exc:  # noqa: BLE001
                print(f"⚠️ Interview chatbot local summary mode: {exc}")
                summary = self._build_fallback_summary(messages, difficulty)

            await conn.execute(
                """
                UPDATE interview_chat_sessions
                SET status = 'completed',
                    summary = $1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = $2
                """,
                summary,
                interview_id,
            )

            return {
                "interview_id": interview_id,
                "summary": summary,
                "message_count": len([m for m in messages if m["role"] == "user"]),
            }
        finally:
            await self._db_release(conn)

    async def get_history(
        self, user_session: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        conn = await self._db_connect()
        try:
            rows = await conn.fetch(
                """
                SELECT id, topic, difficulty, status, summary, created_at, updated_at
                FROM interview_chat_sessions
                WHERE user_session = $1
                ORDER BY created_at DESC
                LIMIT $2
                """,
                user_session,
                limit,
            )
            return [dict(row) for row in rows]
        finally:
            await self._db_release(conn)
