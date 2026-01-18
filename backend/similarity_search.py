"""
Модуль для семантического поиска похожих вопросов с использованием embeddings
"""
import asyncio
import pickle
import os
from typing import List, Dict, Any
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
import redis.asyncio as redis
import asyncpg

# Конфигурация БД
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://diploma:diploma123@localhost:5432/interview_prep")

class QuestionSimilaritySearch:
    def __init__(self):
        self.model = None
        self.index = None
        self.questions_data = []
        self.redis_client = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))

    async def initialize(self):
        """Инициализация модели и индекса"""
        if self.model is None:
            print("🔄 Loading sentence transformer model...")
            self.model = SentenceTransformer('all-MiniLM-L6-v2')  # Легкая модель для русского языка
            print("✅ Model loaded")

        # Проверяем кэш в Redis
        cached_data = await self.redis_client.get("questions_embeddings_cache")
        if cached_data:
            print("🔄 Loading cached embeddings...")
            cache = pickle.loads(cached_data)
            self.index = cache['index']
            self.questions_data = cache['questions_data']
            print(f"✅ Loaded {len(self.questions_data)} cached questions")
        else:
            await self._build_index()
            await self._save_cache()

    async def _build_index(self):
        """Построение векторного индекса из всех одобренных вопросов"""
        print("🔄 Building embeddings index...")

        conn = await asyncpg.connect(DATABASE_URL)
        try:
            # Получаем все одобренные вопросы
            questions = await conn.fetch("""
                SELECT id, question, topic, difficulty, probability
                FROM questions
                WHERE approved = TRUE
            """)
        finally:
            await conn.close()

        if not questions:
            print("⚠️ No approved questions found")
            return

        # Извлекаем тексты вопросов
        question_texts = [q['question'] for q in questions]
        self.questions_data = [
            {
                'id': q['id'],
                'question': q['question'],
                'topic': q['topic'],
                'difficulty': q['difficulty'],
                'probability': q['probability']
            }
            for q in questions
        ]

        print(f"🔄 Creating embeddings for {len(question_texts)} questions...")
        # Создаем embeddings
        embeddings = self.model.encode(question_texts, show_progress_bar=True)

        # Создаем FAISS индекс
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dimension)  # Inner product для косинусного сходства

        # Нормализуем векторы для косинусного сходства
        faiss.normalize_L2(embeddings)
        self.index.add(embeddings.astype('float32'))

        print(f"✅ Index built with {len(self.questions_data)} questions")

    async def _save_cache(self):
        """Сохранение индекса в кэш"""
        if self.index and self.questions_data:
            cache_data = {
                'index': self.index,
                'questions_data': self.questions_data
            }
            await self.redis_client.set("questions_embeddings_cache", pickle.dumps(cache_data))
            print("💾 Cache saved to Redis")

    async def find_similar(self, question_text: str, question_id: int = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Найти похожие вопросы"""
        if not self.index or not self.questions_data:
            await self.initialize()
            if not self.index:
                return []

        # Создаем embedding для запроса
        query_embedding = self.model.encode([question_text])
        faiss.normalize_L2(query_embedding)

        # Ищем похожие
        scores, indices = self.index.search(query_embedding.astype('float32'), limit + 1)  # +1 на случай исключения самого себя

        similar_questions = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < len(self.questions_data):
                question_data = self.questions_data[idx]

                # Исключаем сам вопрос, если указан ID
                if question_id and question_data['id'] == question_id:
                    continue

                similar_questions.append({
                    **question_data,
                    'similarity_score': float(score)
                })

                if len(similar_questions) >= limit:
                    break

        return similar_questions

    async def invalidate_cache(self):
        """Очистка кэша при изменении вопросов"""
        await self.redis_client.delete("questions_embeddings_cache")
        self.index = None
        self.questions_data = []
        print("🗑️ Cache invalidated")

# Глобальный экземпляр
similarity_search = QuestionSimilaritySearch()

async def get_similar_questions(question_text: str, question_id: int = None, limit: int = 10) -> List[Dict[str, Any]]:
    """Удобная функция для поиска похожих вопросов"""
    if similarity_search.model is None:
        return []
    return await similarity_search.find_similar(question_text, question_id, limit)

async def initialize_similarity_search():
    """Инициализация поиска при запуске приложения"""
    await similarity_search.initialize()

async def invalidate_similarity_cache():
    """Очистка кэша при изменении вопросов"""
    await similarity_search.invalidate_cache()