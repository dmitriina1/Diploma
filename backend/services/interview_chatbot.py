"""
AI Interview Chatbot Service
Uses LLM + RAG (FAISS) to simulate technical interviews
"""
import json
from typing import List, Dict, Optional
import httpx
import asyncpg


class InterviewChatbot:
    def __init__(
        self,
        db_connect,
        db_release,
        similarity_search,
        llm_provider: str = "openrouter",
        openrouter_api_key: Optional[str] = None,
        gemini_api_key: Optional[str] = None,
    ):
        self._db_connect = db_connect
        self._db_release = db_release
        self._similarity_search = similarity_search
        self.llm_provider = llm_provider
        self.openrouter_api_key = openrouter_api_key
        self.gemini_api_key = gemini_api_key

    def _build_system_prompt(self, topic: str, difficulty: str) -> str:
        """Build system prompt for the interviewer"""
        return f"""Ты — опытный технический интервьюер в IT-компании. Твоя задача — провести собеседование по теме "{topic}" для уровня {difficulty}.

ПРАВИЛА ПОВЕДЕНИЯ:
1. Задавай вопросы последовательно, один за другим
2. Слушай ответы кандидата и задавай уточняющие вопросы
3. Если ответ неполный или неточный, помоги наводящими вопросами
4. Оценивай глубину понимания, а не только знание фактов
5. Будь дружелюбным, но профессиональным
6. После каждого ответа давай краткий feedback (хорошо/можно лучше)
7. Адаптируй сложность вопросов под уровень кандидата

СТРУКТУРА ИНТЕРВЬЮ:
- Начни с приветствия и простого вопроса для разминки
- Постепенно усложняй вопросы
- Задавай follow-up вопросы для проверки глубины знаний
- В конце дай общую оценку и рекомендации

СТИЛЬ ОБЩЕНИЯ:
- Пиши на русском языке
- Используй профессиональную терминологию
- Будь конкретным в вопросах
- Не задавай несколько вопросов сразу

Начни интервью с приветствия и первого вопроса."""

    async def _get_relevant_questions(
        self, topic: str, difficulty: str, limit: int = 5
    ) -> List[Dict]:
        """Get relevant questions from database using semantic search"""
        conn = await self._db_connect()
        try:
            # Get questions by topic and difficulty
            query = """
                SELECT id, question, answer, topic, difficulty, probability
                FROM questions
                WHERE approved = true
                AND topic ILIKE $1
                AND difficulty = $2
                ORDER BY probability DESC
                LIMIT $3
            """
            rows = await conn.fetch(query, f"%{topic}%", difficulty, limit)
            return [dict(row) for row in rows]
        finally:
            await self._db_release(conn)

    async def _call_llm(
        self, messages: List[Dict[str, str]], temperature: float = 0.7
    ) -> str:
        """Call LLM API (OpenRouter or Gemini)"""
        if self.llm_provider == "openrouter" and self.openrouter_api_key:
            return await self._call_openrouter(messages, temperature)
        elif self.llm_provider == "gemini" and self.gemini_api_key:
            return await self._call_gemini(messages, temperature)
        else:
            raise ValueError("No LLM provider configured")

    async def _call_openrouter(
        self, messages: List[Dict[str, str]], temperature: float
    ) -> str:
        """Call OpenRouter API"""
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.openrouter_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "openai/gpt-4o-mini",  # Fast and cheap
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": 500,
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    async def _call_gemini(
        self, messages: List[Dict[str, str]], temperature: float
    ) -> str:
        """Call Gemini API"""
        # Convert messages to Gemini format
        contents = []
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            contents.append({"role": role, "parts": [{"text": msg["content"]}]})

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={self.gemini_api_key}",
                headers={"Content-Type": "application/json"},
                json={
                    "contents": contents,
                    "generationConfig": {
                        "temperature": temperature,
                        "maxOutputTokens": 500,
                    },
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]

    async def start_interview(
        self, topic: str, difficulty: str, user_session: str
    ) -> Dict:
        """Start a new interview session"""
        # Get relevant questions for context
        relevant_questions = await self._get_relevant_questions(
            topic, difficulty, limit=10
        )

        # Build system prompt with context
        system_prompt = self._build_system_prompt(topic, difficulty)
        
        # Add relevant questions as context
        if relevant_questions:
            context = "\n\nПРИМЕРЫ ВОПРОСОВ ДЛЯ ВДОХНОВЕНИЯ (не задавай их дословно):\n"
            for q in relevant_questions[:5]:
                context += f"- {q['question']}\n"
            system_prompt += context

        # Initialize conversation
        messages = [{"role": "system", "content": system_prompt}]

        # Get first message from LLM
        first_message = await self._call_llm(messages)

        # Save to database
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
                json.dumps(messages + [{"role": "assistant", "content": first_message}]),
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
    ) -> Dict:
        """Send user message and get response"""
        conn = await self._db_connect()
        try:
            # Get interview session
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

            # Load messages
            messages = json.loads(row["messages"])

            # Add user message
            messages.append({"role": "user", "content": user_message})

            # Get LLM response
            assistant_message = await self._call_llm(messages)

            # Add assistant message
            messages.append({"role": "assistant", "content": assistant_message})

            # Update database
            await conn.execute(
                """
                UPDATE interview_chat_sessions
                SET messages = $1, updated_at = CURRENT_TIMESTAMP
                WHERE id = $2
                """,
                json.dumps(messages),
                interview_id,
            )

            return {
                "interview_id": interview_id,
                "message": assistant_message,
                "message_count": len([m for m in messages if m["role"] == "user"]),
            }
        finally:
            await self._db_release(conn)

    async def end_interview(self, interview_id: int, user_session: str) -> Dict:
        """End interview and get summary"""
        conn = await self._db_connect()
        try:
            # Get interview session
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

            messages = json.loads(row["messages"])

            # Ask LLM for final summary
            summary_prompt = """Подведи итоги интервью. Оцени:
1. Сильные стороны кандидата
2. Области для улучшения
3. Общую оценку (1-10)
4. Рекомендации для подготовки

Будь конструктивным и конкретным."""

            messages.append({"role": "user", "content": summary_prompt})
            summary = await self._call_llm(messages, temperature=0.3)

            # Update status
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
                "message_count": len([m for m in messages if m["role"] == "user"]) - 1,
            }
        finally:
            await self._db_release(conn)

    async def get_history(self, user_session: str, limit: int = 10) -> List[Dict]:
        """Get user's interview history"""
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
