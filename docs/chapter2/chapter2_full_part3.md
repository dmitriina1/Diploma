## 2.6 Семантическая обработка, классификация, дедупликация и накопление статистики встречаемости вопросов

Результатом этапа извлечения вопросов (2.5) является множество Q = {q₁, ..., q_M}. При обработке множества видео неизбежно возникает дублирование: одни и те же вопросы формулируются по-разному, а LLM-классификация может быть непоследовательной. Данный раздел посвящён методам обеспечения семантической согласованности базы знаний.

### 2.6.1 Векторное представление вопросов (эмбеддинги)

Основой семантической обработки является отображение текста вопроса в векторное пространство [21]:

e: Σ* → ℝ^d

В системе используется мультиязычная модель SentenceTransformer (paraphrase-multilingual-MiniLM-L12-v2) с d = 384, обученная на параллельных корпусах более 50 языков [22]. Выбор обусловлен необходимостью корректного представления русскоязычных вопросов с английской технической терминологией.

Качество эмбеддингов оценивается косинусным сходством:

cos(e(qᵢ), e(qⱼ)) = (e(qᵢ)·e(qⱼ)) / (‖e(qᵢ)‖·‖e(qⱼ)‖)

Модель демонстрирует усреднённое косинусное сходство 0,82 на русскоязычных парафразах [22].

### 2.6.2 Семантическая дедупликация на основе FAISS

Задача дедупликации: выявить пары (qᵢ, qⱼ), являющиеся семантическими дубликатами:

(qᵢ, qⱼ) ∈ Duplicates ⇔ cos(e(qᵢ), e(qⱼ)) ≥ θ

Для эффективного поиска ближайших соседей применяется FAISS [23], обеспечивающий поиск за O(M·log M) вместо O(M²).

Алгоритм:
1. Вычисление эмбеддингов: E = {e(q₁), ..., e(q_M)}.
2. Нормализация: êᵢ = e(qᵢ)/‖e(qᵢ)‖.
3. Построение FAISS-индекса IndexFlatIP.
4. k-NN поиск для каждого qᵢ: N(qᵢ) = {(qⱼ, cos(êᵢ, êⱼ)) : j ∈ top-k}.
5. Кластеризация: cos(êᵢ, êⱼ) ≥ θ → объединение в кластер.
6. Выбор канонического вопроса в каждом кластере.

Оптимальный порог θ = 0,87 (экспериментально, раздел 3.x).

Мера информативности для выбора канонической формулировки [24]:

I(q) = (1/|w(q)|) · Σ_{w ∈ w(q)\S} idf(w)

где w(q) — множество слов вопроса, S — стоп-слово, idf(w) = log(M/df(w)). Вопрос с максимальным I(q) содержит наиболее специфичную терминологию.

Рисунок 2.6 — Алгоритм семантической дедупликации

```
Извлечённые вопросы Q = {q₁, ..., q_M}
       │
       ▼
Эмбеддинги: E = {e(q₁), ..., e(q_M)}
Модель: paraphrase-multilingual-MiniLM-L12-v2 (d=384)
       │
       ▼
Нормализация: êᵢ = e(qᵢ)/‖e(qᵢ)‖
Построение FAISS IndexFlatIP
       │
       ▼
k-NN поиск → фильтрация cos ≥ θ = 0,87
       │
       ▼
Кластеры дубликатов: C₁, C₂, ..., C_L
Выбор канонического: argmax I(q)
       │
       ▼
Дедуплицированная база: Q' = {q*₁, ..., q*_L}, L ≤ M
```

### 2.6.3 Классификация вопросов по тематическим категориям

Классификация выполняется на двух уровнях:

**Первичная LLM-классификация** (этап 2.5): F₁ ≈ 0,90, но возможна непоследовательность.

**Уточняющая k-NN классификация** на основе эмбеддингов. Пусть Q_labeled — подтверждённые администратором вопросы. Для нового вопроса:

topic(q_new) = argmax_{t∈T} Σ_{q∈N_k(q_new)∩Q_labeled^t} cos(e(q_new), e(q))

Это обеспечивает согласованность с верифицированными данными.

### 2.6.4 Оценка уровня сложности вопросов

Первичная оценка — LLM, уточняющая — эвристические признаки:

- «Алгоритмы»: базовые термины (массив, хеш-таблица) → junior; продвинутые (динамическое программирование, графы) → middle; оптимизационные (NP-полнота) → senior.
- «Системное проектирование» → middle/senior по умолчанию.
- Сравнительный анализ («разница между X и Y») → middle; проектирование с нуля → senior.

Формально: diff_corrected(q) = adjust(diff_LLM(q), features(q)).

### 2.6.5 Накопление статистики встречаемости и оценка вероятности вопросов

Для каждого вопроса q ∈ Q' определяется множество видео V(q), в которых он встречается. Итоговая вероятность:

P(q) = α₁·f₁(q) + α₂·f₂(q) + α₃·f₃(q)

где:
- f₁(q) = |V(q)|/|V| — частота встречаемости;
- f₂(q) = |Platforms(q)|/|Platforms_total| — перекрёстная валидация;
- f₃(q) = max_{v∈V(q)} exp(−λ·age(v)) — временная актуальность (λ = 0,001 день⁻¹, период полураспада ≈ 1,9 года).

Весовые коэффициенты: α₁ = 0,5, α₂ = 0,3, α₃ = 0,2. P(q) нормализуется к [0, 100%].

Рисунок 2.7 — Модель накопления статистики

```
Обработанные видео V = {v₁, ..., v_K}
  v₁(YouTube)  v₂(Rutube)  ...  v_K(YouTube)
       │             │                  │
       ▼             ▼                  ▼
q*₁ → V = {v₁,v₃,v₇}       P = 47%
q*₂ → V = {v₂}              P = 8%
q*₃ → V = {v₁,v₂,v₅,v₈,v₁₂} P = 89%
```

### 2.6.6 Интегральная схема семантической обработки

Рисунок 2.8 — Интегральная схема

```
Извлечённые вопросы Q (из 2.5)
       │
  ┌────┼────┐
  ▼    ▼    ▼
Эмбед.  Класс.  Сложн.
e→ℝ³⁸⁴ topic∈T diff∈D
  │                │     │
  ▼                │     │
FAISS-индекс       │     │
+ k-NN + θ=0,87   │     │
  │                │     │
  ▼                ▼     ▼
Дедуплицированная база Q'
q*ⱼ = (text, topic, diff, embeddings, sources)
       │
       ▼
Статистика: P(q) = α₁f₁ + α₂f₂ + α₃f₃
       │
       ▼
База знаний: {q*ⱼ, topic, diff, P(q), sources, tc}
→ UI: каталог, фильтрация, SM-2 тренажёр
```

Реализованный комплекс обеспечивает: дедупликацию с точностью ≥90% на основе FAISS; согласованную классификацию; статистически обоснованную оценку вероятности встречаемости. Данные методы формируют базу знаний, удовлетворяющую требованиям главы 1.

---

# Список литературы

[7] Appelt D.E., Israel D.J. Introduction to information extraction technology // IJCAI Tutorial. — 1999.

[8] Сёрл Дж. Р. Косвенные речевые акты // Новое в зарубежной лингвистике. — М.: Прогресс, 1985. — Вып. 17. — С. 195–222.

[9] Шардин Д.В., Гринёв А.В. Автоматическая диаризация говорящих: обзор методов // Информационные технологии и вычислительные системы. — 2023. — Т. 29, № 2. — С. 3–20.

[10] Manning C.D., Raghavan P., Schütze H. Introduction to Information Retrieval. — Cambridge University Press, 2008.

[11] Zhang Y., Clark S. A shift-reduce framework for sentence-level discourse parsing // Proc. ACL. — 2015. — P. 105–115.

[12] Lafferty J., McCallum A., Pereira F.C.N. Conditional random fields // Proc. ICML. — 2001. — P. 282–289.

[13] Vaswani A. et al. Attention is all you need // NeurIPS. — 2017. — P. 5998–6008.

[14] Devlin J. et al. BERT: Pre-training of deep bidirectional transformers // Proc. NAACL-HLT. — 2019. — P. 4171–4186.

[15] Sun C. et al. A comparative study on LSTM and Transformer for sentence classification // Proc. RepL4NLP. — 2020. — P. 42–49.

[16] Brown T.B. et al. Language models are few-shot learners // NeurIPS. — 2020. — P. 1877–1901.

[17] Liu P. et al. Pre-train, prompt, and predict: A systematic survey of prompting methods // ACM Computing Surveys. — 2023. — Vol. 55, No. 9. — P. 1–35.

[18] Wang Z. et al. RolePrompt: Exploring the role of LLMs in information extraction // Proc. EMNLP. — 2024. — P. 2841–2856.

[19] Bai Y. et al. Constitutional AI: Harmlessness from AI feedback // arXiv:2212.08073. — 2022.

[20] Joulin A., Mikolov T. Inferring algorithmic patterns with stack-augmented recurrent nets // NeurIPS. — 2015. — P. 190–198.

[21] Mikolov T. et al. Distributed representations of words and phrases // NeurIPS. — 2013. — P. 3111–3119.

[22] Reimers N., Gurevych I. Sentence-BERT: Sentence embeddings using Siamese BERT-networks // Proc. EMNLP. — 2019. — P. 3982–3992.

[23] Johnson J., Douze M., Jégou H. Billion-scale similarity search with GPUs // IEEE Trans. Big Data. — 2021. — Vol. 7, No. 3. — P. 535–547.

[24] Robertson S.E., Walker S. Some simple effective approximations to the 2-Poisson model // Proc. SIGIR. — 1994. — P. 232–241.

[25] Boll S.F. Suppression of acoustic noise in speech using spectral subtraction // IEEE Trans. ASSP. — 1979. — Vol. 27, No. 2. — P. 113–120.

[26] EBU Recommendation R128: Loudness normalisation and permitted maximum level of audio signals // European Broadcasting Union. — 2020.

[27] Silero VAD: pre-trained enterprise-grade Voice Activity Detector // GitHub. — 2024.

[28] Linder K., Nakhimova D. Closed captions and subtitles in online learning // J. Educational Technology Systems. — 2022. — Vol. 50, No. 3. — P. 289–305.

[29] Fiscus J.G. A post-processing system to yield reduced word error rates: ROVER // Proc. IEEE ASRU. — 1997. — P. 347–354.
