"""
Evaluation Script: Question Extraction Quality Assessment
==========================================================

Оценка качества извлечения вопросов из видеозаписей IT-собеседований.

Методология:
1. Загрузка экспертной разметки (ground truth) из JSON-файла
2. Загрузка извлечённых вопросов из API или JSON-экспорта
3. Сопоставление вопросов (fuzzy matching + semantic similarity)
4. Расчёт метрик: Precision, Recall, F1, MAE таймкодов
5. Анализ ошибок: классификация FP/FN

Запуск:
    python evaluate_extraction.py --ground-truth data/ground_truth.json
    python evaluate_extraction.py --ground-truth data/ground_truth.json --extracted data/extracted.json
    python evaluate_extraction.py --ground-truth data/ground_truth.json --api-url http://localhost:8000
"""

import json
import argparse
import sys
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import re


# ============== Data Models ==============

@dataclass
class Question:
    """Представление вопроса (экспертного или извлечённого)"""
    text: str
    topic: str = ""
    difficulty: str = ""
    timecode: Optional[str] = None
    timecode_seconds: int = 0

    def __post_init__(self):
        self.text = self.text.strip()
        if self.timecode and not self.timecode_seconds:
            self.timecode_seconds = parse_timecode(self.timecode)


@dataclass
class MatchResult:
    """Результат сопоставления двух вопросов"""
    extracted: Question
    expert: Question
    similarity_score: float
    levenshtein_distance: float
    timecode_error_seconds: int = 0
    match_method: str = ""  # "levenshtein" or "semantic"


@dataclass
class VideoEvaluation:
    """Результаты оценки для одного видео"""
    video_name: str
    duration_minutes: int = 0
    expert_questions: List[Question] = field(default_factory=list)
    extracted_questions: List[Question] = field(default_factory=list)
    true_positives: List[MatchResult] = field(default_factory=list)
    false_positives: List[Question] = field(default_factory=list)
    false_negatives: List[Question] = field(default_factory=list)

    @property
    def precision(self) -> float:
        tp = len(self.true_positives)
        fp = len(self.false_positives)
        return tp / (tp + fp) if (tp + fp) > 0 else 0.0

    @property
    def recall(self) -> float:
        tp = len(self.true_positives)
        fn = len(self.false_negatives)
        return tp / (tp + fn) if (tp + fn) > 0 else 0.0

    @property
    def f1(self) -> float:
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if (p + r) > 0 else 0.0

    @property
    def timecode_mae(self) -> float:
        """Mean Absolute Error таймкодов (секунды)"""
        errors = [m.timecode_error_seconds for m in self.true_positives
                  if m.timecode_error_seconds is not None]
        return sum(errors) / len(errors) if errors else 0.0


@dataclass
class EvaluationReport:
    """Агрегированный отчёт"""
    video_evaluations: List[VideoEvaluation] = field(default_factory=list)

    @property
    def total_expert(self) -> int:
        return sum(len(v.expert_questions) for v in self.video_evaluations)

    @property
    def total_extracted(self) -> int:
        return sum(len(v.extracted_questions) for v in self.video_evaluations)

    @property
    def total_tp(self) -> int:
        return sum(len(v.true_positives) for v in self.video_evaluations)

    @property
    def total_fp(self) -> int:
        return sum(len(v.false_positives) for v in self.video_evaluations)

    @property
    def total_fn(self) -> int:
        return sum(len(v.false_negatives) for v in self.video_evaluations)

    @property
    def macro_precision(self) -> float:
        scores = [v.precision for v in self.video_evaluations if v.expert_questions]
        return sum(scores) / len(scores) if scores else 0.0

    @property
    def macro_recall(self) -> float:
        scores = [v.recall for v in self.video_evaluations if v.expert_questions]
        return sum(scores) / len(scores) if scores else 0.0

    @property
    def macro_f1(self) -> float:
        scores = [v.f1 for v in self.video_evaluations if v.expert_questions]
        return sum(scores) / len(scores) if scores else 0.0

    @property
    def micro_precision(self) -> float:
        tp, fp = self.total_tp, self.total_fp
        return tp / (tp + fp) if (tp + fp) > 0 else 0.0

    @property
    def micro_recall(self) -> float:
        tp, fn = self.total_tp, self.total_fn
        return tp / (tp + fn) if (tp + fn) > 0 else 0.0

    @property
    def micro_f1(self) -> float:
        p, r = self.micro_precision, self.micro_recall
        return 2 * p * r / (p + r) if (p + r) > 0 else 0.0

    @property
    def avg_timecode_mae(self) -> float:
        maes = [v.timecode_mae for v in self.video_evaluations if v.true_positives]
        return sum(maes) / len(maes) if maes else 0.0


# ============== Utility Functions ==============

def parse_timecode(tc: str) -> int:
    """Парсинг таймкода вида MM:SS или HH:MM:SS в секунды"""
    if not tc:
        return 0
    try:
        parts = str(tc).split(':')
        parts = [int(p) for p in parts]
        if len(parts) == 3:
            return parts[0] * 3600 + parts[1] * 60 + parts[2]
        elif len(parts) == 2:
            return parts[0] * 60 + parts[1]
        return int(tc)
    except (ValueError, TypeError):
        return 0


def normalize_text(text: str) -> str:
    """Нормализация текста для сравнения"""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s]', '', text)  # Удаление пунктуации
    text = re.sub(r'\s+', ' ', text)     # Нормализация пробелов
    return text


def levenshtein_distance(s1: str, s2: str) -> int:
    """Расстояние Левенштейна"""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)

    prev_row = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        curr_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = prev_row[j + 1] + 1
            deletions = curr_row[j] + 1
            substitutions = prev_row[j] + (c1 != c2)
            curr_row.append(min(insertions, deletions, substitutions))
        prev_row = curr_row

    return prev_row[-1]


def normalized_levenshtein(s1: str, s2: str) -> float:
    """Нормализованное расстояние Левенштейна (0 = идентичны, 1 = полностью различны)"""
    if not s1 and not s2:
        return 0.0
    dist = levenshtein_distance(s1, s2)
    max_len = max(len(s1), len(s2))
    return dist / max_len if max_len > 0 else 0.0


# ============== Semantic Similarity (optional) ==============

_embedding_model = None


def get_embedding_model():
    """Ленивая загрузка модели sentence-transformers"""
    global _embedding_model
    if _embedding_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            print("✅ Loaded sentence-transformers model (all-MiniLM-L6-v2)")
        except ImportError:
            print("⚠️ sentence-transformers not installed. Using Levenshtein only.")
            print("   Install: pip install sentence-transformers")
            return None
    return _embedding_model


def cosine_similarity(v1, v2) -> float:
    """Косинусное сходство двух векторов"""
    import numpy as np
    dot = np.dot(v1, v2)
    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)
    return float(dot / (norm1 * norm2)) if (norm1 * norm2) > 0 else 0.0


def compute_semantic_similarity(text1: str, text2: str) -> float:
    """Семантическое сходство через sentence-transformers"""
    model = get_embedding_model()
    if model is None:
        return 0.0

    embeddings = model.encode([text1, text2])
    return cosine_similarity(embeddings[0], embeddings[1])


# ============== Matching Algorithm ==============

def match_questions(
    extracted: List[Question],
    expert: List[Question],
    levenshtein_threshold: float = 0.4,
    semantic_threshold: float = 0.75,
    use_semantic: bool = True
) -> Tuple[List[MatchResult], List[Question], List[Question]]:
    """
    Сопоставление извлечённых вопросов с экспертной разметкой.

    Алгоритм (жадный, greedy matching):
    1. Для каждой пары (extracted, expert) вычислить score
    2. Отсортировать пары по убыванию score
    3. Жадно назначить пары (каждый вопрос используется только один раз)

    Returns:
        (true_positives, false_positives, false_negatives)
    """
    if not extracted or not expert:
        return [], list(extracted), list(expert)

    # Вычисляем матрицу scores
    scores = []
    for i, eq in enumerate(extracted):
        for j, gq in enumerate(expert):
            norm_ext = normalize_text(eq.text)
            norm_exp = normalize_text(gq.text)

            # Нормализованное расстояние Левенштейна
            lev_dist = normalized_levenshtein(norm_ext, norm_exp)
            lev_match = lev_dist <= levenshtein_threshold

            # Семантическое сходство (если доступно)
            sem_score = 0.0
            sem_match = False
            if use_semantic:
                sem_score = compute_semantic_similarity(eq.text, gq.text)
                sem_match = sem_score >= semantic_threshold

            if lev_match or sem_match:
                # Комбинированный score: приоритет семантику, но учитываем оба
                combined_score = max(
                    (1 - lev_dist) if lev_match else 0,
                    sem_score if sem_match else 0
                )
                method = "semantic" if (sem_match and sem_score > (1 - lev_dist)) else "levenshtein"
                scores.append((i, j, combined_score, lev_dist, sem_score, method))

    # Сортируем по убыванию score
    scores.sort(key=lambda x: x[2], reverse=True)

    # Жадное сопоставление
    matched_extracted = set()
    matched_expert = set()
    true_positives = []

    for i, j, score, lev_dist, sem_score, method in scores:
        if i in matched_extracted or j in matched_expert:
            continue

        eq = extracted[i]
        gq = expert[j]

        timecode_error = abs(eq.timecode_seconds - gq.timecode_seconds)

        match = MatchResult(
            extracted=eq,
            expert=gq,
            similarity_score=score,
            levenshtein_distance=lev_dist,
            timecode_error_seconds=timecode_error,
            match_method=method
        )
        true_positives.append(match)
        matched_extracted.add(i)
        matched_expert.add(j)

    # False Positives: извлечённые, не сопоставленные
    false_positives = [extracted[i] for i in range(len(extracted))
                       if i not in matched_extracted]

    # False Negatives: экспертные, не сопоставленные
    false_negatives = [expert[j] for j in range(len(expert))
                       if j not in matched_expert]

    return true_positives, false_positives, false_negatives


# ============== Data Loading ==============

def load_ground_truth(filepath: str) -> List[Dict]:
    """
    Загрузка экспертной разметки из JSON.

    Ожидаемый формат:
    {
        "videos": [
            {
                "name": "Python собеседование",
                "url": "https://youtube.com/watch?v=...",
                "duration_minutes": 35,
                "questions": [
                    {
                        "question": "Что такое GIL в Python?",
                        "topic": "Python",
                        "difficulty": "middle",
                        "timecode": "05:23"
                    },
                    ...
                ]
            },
            ...
        ]
    }
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    return data.get("videos", [])


def load_extracted_questions(filepath: str) -> Dict[str, List[Dict]]:
    """
    Загрузка извлечённых вопросов.

    Ожидаемый формат:
    {
        "videos": {
            "Video Name": [
                {
                    "question": "...",
                    "topic": "...",
                    "difficulty": "...",
                    "timecode": "..."
                },
                ...
            ]
        }
    }
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    return data.get("videos", {})


async def load_extracted_from_api(api_url: str, video_ids: List[int]) -> Dict[str, List[Dict]]:
    """Загрузка извлечённых вопросов из API"""
    import httpx

    result = {}
    async with httpx.AsyncClient(timeout=30.0) as client:
        for vid in video_ids:
            resp = await client.get(f"{api_url}/api/admin/videos/{vid}/questions")
            if resp.status_code == 200:
                data = resp.json()
                result[f"video_{vid}"] = data.get("questions", [])

    return result


# ============== Main Evaluation ==============

def evaluate(
    ground_truth_path: str,
    extracted_path: Optional[str] = None,
    use_semantic: bool = True,
    levenshtein_threshold: float = 0.4,
    semantic_threshold: float = 0.75,
    verbose: bool = True
) -> EvaluationReport:
    """
    Основная функция оценки качества.

    Args:
        ground_truth_path: Путь к JSON-файлу экспертной разметки
        extracted_path: Путь к JSON-файлу извлечённых вопросов (опционально)
        use_semantic: Использовать ли семантическое сходство
        levenshtein_threshold: Порог расстояния Левенштейна (0-1, меньше = строже)
        semantic_threshold: Порог косинусного сходства (0-1, больше = строже)
        verbose: Подробный вывод

    Returns:
        EvaluationReport с результатами оценки
    """
    # Загрузка данных
    gt_videos = load_ground_truth(ground_truth_path)

    if extracted_path:
        extracted_data = load_extracted_questions(extracted_path)
    else:
        extracted_data = {}

    report = EvaluationReport()

    for gt_video in gt_videos:
        video_name = gt_video["name"]
        duration = gt_video.get("duration_minutes", 0)

        # Экспертные вопросы
        expert_questions = [
            Question(
                text=q["question"],
                topic=q.get("topic", ""),
                difficulty=q.get("difficulty", ""),
                timecode=q.get("timecode")
            )
            for q in gt_video.get("questions", [])
        ]

        # Извлечённые вопросы
        extracted_raw = extracted_data.get(video_name, [])
        extracted_questions = [
            Question(
                text=q.get("question", ""),
                topic=q.get("topic", ""),
                difficulty=q.get("difficulty", ""),
                timecode=q.get("timecode")
            )
            for q in extracted_raw
        ]

        # Сопоставление
        tp, fp, fn = match_questions(
            extracted_questions,
            expert_questions,
            levenshtein_threshold=levenshtein_threshold,
            semantic_threshold=semantic_threshold,
            use_semantic=use_semantic
        )

        evaluation = VideoEvaluation(
            video_name=video_name,
            duration_minutes=duration,
            expert_questions=expert_questions,
            extracted_questions=extracted_questions,
            true_positives=tp,
            false_positives=fp,
            false_negatives=fn
        )

        report.video_evaluations.append(evaluation)

    if verbose:
        print_report(report)

    return report


# ============== Reporting ==============

def print_report(report: EvaluationReport):
    """Вывод детализированного отчёта"""
    print("=" * 80)
    print("ОТЧЁТ ОБ ОЦЕНКЕ КАЧЕСТВА ИЗВЛЕЧЕНИЯ ВОПРОСОВ")
    print("=" * 80)
    print()

    # Таблица по видео
    print(f"{'Видео':<35} {'Длит.':<7} {'Эксп.':<7} {'Извл.':<7} "
          f"{'TP':<5} {'FP':<5} {'FN':<5} {'Prec.':<7} {'Rec.':<7} {'F1':<7}")
    print("-" * 95)

    for v in report.video_evaluations:
        print(f"{v.video_name[:34]:<35} {v.duration_minutes:<7} "
              f"{len(v.expert_questions):<7} {len(v.extracted_questions):<7} "
              f"{len(v.true_positives):<5} {len(v.false_positives):<5} "
              f"{len(v.false_negatives):<5} "
              f"{v.precision:<7.2f} {v.recall:<7.2f} {v.f1:<7.2f}")

    print("-" * 95)
    print(f"{'ИТОГО':<35} {'':7} "
          f"{report.total_expert:<7} {report.total_extracted:<7} "
          f"{report.total_tp:<5} {report.total_fp:<5} {report.total_fn:<5} "
          f"{'':7} {'':7} {'':7}")
    print()

    # Агрегированные метрики
    print("АГРЕГИРОВАННЫЕ МЕТРИКИ:")
    print(f"  Micro Precision: {report.micro_precision:.4f}")
    print(f"  Micro Recall:    {report.micro_recall:.4f}")
    print(f"  Micro F1:        {report.micro_f1:.4f}")
    print()
    print(f"  Macro Precision: {report.macro_precision:.4f}")
    print(f"  Macro Recall:    {report.macro_recall:.4f}")
    print(f"  Macro F1:        {report.macro_f1:.4f}")
    print()
    print(f"  Средняя ошибка таймкодов (MAE): {report.avg_timecode_mae:.1f} сек")
    print()

    # Детализация ошибок
    print("АНАЛИЗ ОШИБОК:")
    print()

    all_fp = []
    all_fn = []
    for v in report.video_evaluations:
        all_fp.extend([(v.video_name, q) for q in v.false_positives])
        all_fn.extend([(v.video_name, q) for q in v.false_negatives])

    if all_fp:
        print(f"  False Positives ({len(all_fp)} шт.) — ложно извлечённые:")
        for video_name, q in all_fp[:10]:
            print(f"    [{video_name}] \"{q.text[:80]}...\"" if len(q.text) > 80
                  else f"    [{video_name}] \"{q.text}\"")
        if len(all_fp) > 10:
            print(f"    ... и ещё {len(all_fp) - 10}")
        print()

    if all_fn:
        print(f"  False Negatives ({len(all_fn)} шт.) — пропущенные:")
        for video_name, q in all_fn[:10]:
            print(f"    [{video_name}] \"{q.text[:80]}...\"" if len(q.text) > 80
                  else f"    [{video_name}] \"{q.text}\"")
        if len(all_fn) > 10:
            print(f"    ... и ещё {len(all_fn) - 10}")
        print()

    # Сопоставленные пары (TP)
    print("  Успешные сопоставления (TP, первые 5):")
    all_tp = []
    for v in report.video_evaluations:
        all_tp.extend(v.true_positives)

    for match in all_tp[:5]:
        print(f"    Извлечено : \"{match.extracted.text[:70]}\"")
        print(f"    Эксперт   : \"{match.expert.text[:70]}\"")
        print(f"    Score={match.similarity_score:.3f}, "
              f"Method={match.match_method}, "
              f"TC error={match.timecode_error_seconds}s")
        print()


def save_report_json(report: EvaluationReport, output_path: str):
    """Сохранение отчёта в JSON"""
    data = {
        "summary": {
            "total_videos": len(report.video_evaluations),
            "total_expert_questions": report.total_expert,
            "total_extracted_questions": report.total_extracted,
            "total_true_positives": report.total_tp,
            "total_false_positives": report.total_fp,
            "total_false_negatives": report.total_fn,
            "micro_precision": round(report.micro_precision, 4),
            "micro_recall": round(report.micro_recall, 4),
            "micro_f1": round(report.micro_f1, 4),
            "macro_precision": round(report.macro_precision, 4),
            "macro_recall": round(report.macro_recall, 4),
            "macro_f1": round(report.macro_f1, 4),
            "avg_timecode_mae_seconds": round(report.avg_timecode_mae, 1)
        },
        "videos": [
            {
                "name": v.video_name,
                "duration_minutes": v.duration_minutes,
                "expert_count": len(v.expert_questions),
                "extracted_count": len(v.extracted_questions),
                "tp": len(v.true_positives),
                "fp": len(v.false_positives),
                "fn": len(v.false_negatives),
                "precision": round(v.precision, 4),
                "recall": round(v.recall, 4),
                "f1": round(v.f1, 4),
                "timecode_mae": round(v.timecode_mae, 1),
                "false_positives": [q.text for q in v.false_positives],
                "false_negatives": [q.text for q in v.false_negatives],
                "matches": [
                    {
                        "extracted": m.extracted.text,
                        "expert": m.expert.text,
                        "score": round(m.similarity_score, 4),
                        "method": m.match_method,
                        "timecode_error_s": m.timecode_error_seconds
                    }
                    for m in v.true_positives
                ]
            }
            for v in report.video_evaluations
        ]
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n📄 Отчёт сохранён: {output_path}")


# ============== CLI ==============

def main():
    parser = argparse.ArgumentParser(
        description="Оценка качества извлечения вопросов из видеозаписей IT-собеседований"
    )
    parser.add_argument(
        "--ground-truth", "-g",
        required=True,
        help="Путь к JSON-файлу экспертной разметки"
    )
    parser.add_argument(
        "--extracted", "-e",
        help="Путь к JSON-файлу извлечённых вопросов"
    )
    parser.add_argument(
        "--output", "-o",
        default="evaluation_report.json",
        help="Путь для сохранения JSON-отчёта (default: evaluation_report.json)"
    )
    parser.add_argument(
        "--no-semantic",
        action="store_true",
        help="Отключить семантическое сравнение (только Левенштейн)"
    )
    parser.add_argument(
        "--levenshtein-threshold",
        type=float,
        default=0.4,
        help="Порог расстояния Левенштейна (default: 0.4)"
    )
    parser.add_argument(
        "--semantic-threshold",
        type=float,
        default=0.75,
        help="Порог косинусного сходства (default: 0.75)"
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Минимальный вывод"
    )

    args = parser.parse_args()

    if not Path(args.ground_truth).exists():
        print(f"❌ Файл не найден: {args.ground_truth}")
        sys.exit(1)

    if args.extracted and not Path(args.extracted).exists():
        print(f"❌ Файл не найден: {args.extracted}")
        sys.exit(1)

    report = evaluate(
        ground_truth_path=args.ground_truth,
        extracted_path=args.extracted,
        use_semantic=not args.no_semantic,
        levenshtein_threshold=args.levenshtein_threshold,
        semantic_threshold=args.semantic_threshold,
        verbose=not args.quiet
    )

    save_report_json(report, args.output)


if __name__ == "__main__":
    main()
