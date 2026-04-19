"""
Модуль для семантического поиска похожих вопросов с использованием embeddings
"""
import pickle
import os
import re
from difflib import SequenceMatcher
from typing import List, Dict, Any, Optional, Set
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
        self.questions_by_id = {}
        self.redis_client = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))
        # v2 cache keeps embeddings for all questions (approved + unapproved)
        self.cache_key = "questions_embeddings_cache_v2_all_questions"
        # Minimal bilingual stop-list for specificity estimation.
        self.stop_words: Set[str] = {
            "и", "в", "во", "не", "что", "он", "на", "я", "с", "со", "как", "а", "то", "все",
            "она", "так", "его", "но", "да", "ты", "к", "у", "же", "вы", "за", "бы", "по", "только",
            "ее", "мне", "было", "вот", "от", "меня", "еще", "нет", "о", "из", "ему", "теперь", "когда",
            "даже", "ну", "ли", "если", "уже", "или", "ни", "быть", "был", "него", "до", "вас", "нибудь",
            "опять", "уж", "вам", "ведь", "там", "потом", "себя", "ничего", "ей", "может", "они", "тут",
            "где", "есть", "надо", "ней", "для", "мы", "тебя", "их", "чем", "была", "сам", "чтоб", "без",
            "будто", "чего", "раз", "тоже", "себе", "под", "будет", "ж", "тогда", "кто", "этот", "того",
            "потому", "этого", "какой", "совсем", "ним", "здесь", "этом", "один", "almost", "and", "the",
            "is", "are", "to", "for", "of", "on", "in", "a", "an", "with", "at", "by", "from", "or",
            "be", "as", "that", "this", "it", "you", "your", "we", "they", "their", "our", "was", "were",
        }

    @staticmethod
    def _normalize_text(text: str) -> str:
        normalized = (text or "").lower().strip()
        normalized = re.sub(r"[^\w\s]", " ", normalized)
        normalized = re.sub(r"\s+", " ", normalized)
        return normalized

    def _tokenize(self, text: str) -> List[str]:
        return [t for t in self._normalize_text(text).split() if t]

    @staticmethod
    def _jaccard(tokens_a: List[str], tokens_b: List[str]) -> float:
        if not tokens_a or not tokens_b:
            return 0.0
        a = set(tokens_a)
        b = set(tokens_b)
        inter = len(a & b)
        union = len(a | b)
        if union == 0:
            return 0.0
        return inter / union

    @staticmethod
    def _sequence_ratio(a: str, b: str) -> float:
        if not a or not b:
            return 0.0
        return SequenceMatcher(None, a, b).ratio()

    @staticmethod
    def _length_ratio(a: str, b: str) -> float:
        la, lb = len(a), len(b)
        if la == 0 or lb == 0:
            return 0.0
        return min(la, lb) / max(la, lb)

    def _specificity(self, tokens: List[str]) -> float:
        if not tokens:
            return 0.0
        informative = [t for t in tokens if t not in self.stop_words and len(t) > 2]
        if not informative:
            return 0.2
        unique_ratio = len(set(informative)) / len(informative)
        density = len(informative) / len(tokens)
        return max(0.0, min(1.0, 0.6 * unique_ratio + 0.4 * density))

    @staticmethod
    def _metadata_alignment(source: Dict[str, Any], candidate: Dict[str, Any]) -> float:
        if not source:
            return 0.0
        topic_match = 1.0 if source.get("topic") and source.get("topic") == candidate.get("topic") else 0.0
        difficulty_match = 1.0 if source.get("difficulty") and source.get("difficulty") == candidate.get("difficulty") else 0.0
        return 0.7 * topic_match + 0.3 * difficulty_match

    @staticmethod
    def _bound_01(value: float) -> float:
        return max(0.0, min(1.0, float(value)))

    async def initialize(self):
        """Инициализация модели и индекса"""
        if self.model is None:
            print("🔄 Loading sentence transformer model...")
            self.model = SentenceTransformer('all-MiniLM-L6-v2')  # Легкая модель для русского языка
            print("✅ Model loaded")

        # Проверяем кэш в Redis
        cached_data = await self.redis_client.get(self.cache_key)
        if cached_data:
            print("🔄 Loading cached embeddings...")
            cache = pickle.loads(cached_data)
            self.index = cache['index']
            self.questions_data = cache['questions_data']
            # Safety check for old/incompatible cache shape
            if self.questions_data and 'approved' not in self.questions_data[0]:
                print("⚠️ Outdated similarity cache detected, rebuilding...")
                self.index = None
                self.questions_data = []
                await self._build_index()
                await self._save_cache()
                return
            self.questions_by_id = {q["id"]: q for q in self.questions_data}
            print(f"✅ Loaded {len(self.questions_data)} cached questions")
        else:
            await self._build_index()
            await self._save_cache()

    async def _build_index(self):
        """Построение векторного индекса по всем вопросам"""
        print("🔄 Building embeddings index...")

        conn = await asyncpg.connect(DATABASE_URL)
        try:
            # Получаем все вопросы (для админ-модерации дубликатов тоже)
            questions = await conn.fetch("""
                SELECT id, question, topic, difficulty, probability, approved
                FROM questions
                WHERE question IS NOT NULL AND BTRIM(question) != ''
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
                'probability': q['probability'],
                'approved': bool(q['approved'])
            }
            for q in questions
        ]
        self.questions_by_id = {q["id"]: q for q in self.questions_data}

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
            await self.redis_client.set(self.cache_key, pickle.dumps(cache_data))
            print("💾 Cache saved to Redis")

    async def find_similar(
        self,
        question_text: str,
        question_id: int = None,
        limit: int = 10,
        include_unapproved: bool = False,
        min_score: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """
        Найти похожие вопросы через адаптивный гибридный скоринг.

        Идея: объединяем семантику (embeddings), лексическую близость, токенное
        пересечение и метаданные (topic/difficulty) с динамическим порогом.
        """
        if not self.index or not self.questions_data:
            await self.initialize()
            if not self.index:
                return []

        if not question_text or not question_text.strip():
            return []

        limit = max(1, min(int(limit or 10), 20))

        # Создаем embedding для запроса
        query_embedding = self.model.encode([question_text])
        faiss.normalize_L2(query_embedding)
        query_norm = self._normalize_text(question_text)
        query_tokens = self._tokenize(query_norm)
        query_specificity = self._specificity(query_tokens)
        source_question = self.questions_by_id.get(question_id) if question_id else None

        # Ищем похожие: берем расширенный пул кандидатов, затем фильтруем
        search_k = min(len(self.questions_data), max(limit * 8, 60))
        scores, indices = self.index.search(query_embedding.astype('float32'), search_k)

        candidates = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < len(self.questions_data):
                question_data = self.questions_data[idx]

                # Исключаем сам вопрос, если указан ID
                if question_id and question_data['id'] == question_id:
                    continue

                # Для публичных сценариев скрываем неутвержденные вопросы
                if not include_unapproved and not question_data.get('approved', False):
                    continue

                candidate_text = question_data.get("question", "")
                candidate_norm = self._normalize_text(candidate_text)
                candidate_tokens = self._tokenize(candidate_norm)

                semantic_score = self._bound_01(float(score))
                lexical_score = self._sequence_ratio(query_norm, candidate_norm)
                token_overlap = self._jaccard(query_tokens, candidate_tokens)
                meta_score = self._metadata_alignment(source_question, question_data)
                length_consistency = self._length_ratio(query_norm, candidate_norm)

                # Adaptive Hybrid Similarity (AHS): multi-signal fusion.
                hybrid_score = (
                    0.60 * semantic_score
                    + 0.20 * lexical_score
                    + 0.12 * token_overlap
                    + 0.08 * meta_score
                ) * (0.85 + 0.15 * length_consistency)

                is_hard_duplicate = (
                    (lexical_score >= 0.93 and semantic_score >= 0.65)
                    or (token_overlap >= 0.85 and semantic_score >= 0.60)
                )

                candidates.append({
                    **question_data,
                    'similarity_score': float(hybrid_score),
                    'semantic_score': float(semantic_score),
                    'lexical_score': float(lexical_score),
                    'token_overlap': float(token_overlap),
                    'meta_score': float(meta_score),
                    'length_consistency': float(length_consistency),
                    'is_hard_duplicate': bool(is_hard_duplicate),
                })

        if not candidates:
            return []

        candidates.sort(key=lambda x: x["similarity_score"], reverse=True)

        base_threshold = 0.60 if include_unapproved else 0.64
        specificity_adjustment = max(0.0, 0.55 - query_specificity) * 0.12
        adaptive_threshold = base_threshold + specificity_adjustment
        if min_score is not None:
            adaptive_threshold = max(adaptive_threshold, self._bound_01(min_score))
        adaptive_threshold = max(0.45, min(0.85, adaptive_threshold))

        filtered = [
            c
            for c in candidates
            if c["is_hard_duplicate"] or c["similarity_score"] >= adaptive_threshold
        ]

        if not filtered:
            # Return empty list rather than low-quality noise.
            return []

        # Confidence-tail pruning: remove weak tail even if above threshold.
        best_score = filtered[0]["similarity_score"]
        tail_floor = max(adaptive_threshold, best_score - 0.18)
        filtered = [
            c for c in filtered if c["is_hard_duplicate"] or c["similarity_score"] >= tail_floor
        ]

        return filtered[:limit]

    async def invalidate_cache(self):
        """Очистка кэша при изменении вопросов"""
        await self.redis_client.delete(self.cache_key)
        self.index = None
        self.questions_data = []
        print("🗑️ Cache invalidated")

# Глобальный экземпляр
similarity_search = QuestionSimilaritySearch()

async def get_similar_questions(
    question_text: str,
    question_id: int = None,
    limit: int = 10,
    include_unapproved: bool = False,
    min_score: Optional[float] = None,
) -> List[Dict[str, Any]]:
    """Удобная функция для поиска похожих вопросов"""
    return await similarity_search.find_similar(
        question_text,
        question_id,
        limit,
        include_unapproved=include_unapproved,
        min_score=min_score,
    )

async def initialize_similarity_search():
    """Инициализация поиска при запуске приложения"""
    await similarity_search.initialize()

async def invalidate_similarity_cache():
    """Очистка кэша при изменении вопросов"""
    await similarity_search.invalidate_cache()