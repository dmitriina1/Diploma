import React, { useState, useEffect } from 'react';

const API_URL = process.env.REACT_APP_API_URL || '';

function PublicSide() {
  const [questions, setQuestions] = useState([]);
  const [filteredQuestions, setFilteredQuestions] = useState([]);
  const [topicFilter, setTopicFilter] = useState('');
  const [levelFilter, setLevelFilter] = useState('');
  const [probabilitySort, setProbabilitySort] = useState('desc'); // desc, asc
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchQuestions();
  }, []);

  useEffect(() => {
    filterAndSortQuestions();
  }, [questions, topicFilter, levelFilter, probabilitySort, searchQuery]);

  const fetchQuestions = async () => {
    try {
      const response = await fetch(`${API_URL}/api/questions`);
      const data = await response.json();
      setQuestions(data.questions || []);
    } catch (error) {
      console.error('Error fetching questions:', error);
    } finally {
      setLoading(false);
    }
  };

  const filterAndSortQuestions = () => {
    let filtered = questions.filter(q => q.approved); // Только одобренные

    // Текстовый поиск
    if (searchQuery) {
      filtered = filtered.filter(q =>
        q.question?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        q.answer?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        q.topic?.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    // Фильтр по теме
    if (topicFilter) {
      filtered = filtered.filter(q => q.topic === topicFilter);
    }

    // Фильтр по уровню
    if (levelFilter) {
      filtered = filtered.filter(q => q.difficulty === levelFilter);
    }

    // Сортировка по вероятности
    filtered.sort((a, b) => {
      const aProb = a.probability || 0;
      const bProb = b.probability || 0;
      return probabilitySort === 'desc' ? bProb - aProb : aProb - bProb;
    });

    setFilteredQuestions(filtered);
  };

  const getYouTubeTimestampUrl = (url, timecode) => {
    if (!url || !timecode) return url;
    const videoId = url.split('v=')[1]?.split('&')[0];
    if (!videoId) return url;

    // Преобразовать timecode в секунды (например, "01:23" -> 83)
    const parts = timecode.split(':');
    const seconds = parts.length === 2 ?
      parseInt(parts[0]) * 60 + parseInt(parts[1]) :
      parseInt(parts[0]);

    return `https://www.youtube.com/watch?v=${videoId}&t=${seconds}`;
  };

  const getUniqueTopics = () => {
    const topics = [...new Set(questions.map(q => q.topic).filter(Boolean))];
    return topics.sort();
  };

  const getProbabilityColor = (probability) => {
    if (probability >= 80) return 'high';
    if (probability >= 50) return 'medium';
    return 'low';
  };

  if (loading) {
    return <div className="loading">Загрузка вопросов...</div>;
  }

  return (
    <div className="public-side">
      <h1>База вопросов для IT-собеседований</h1>
      <p className="subtitle">Найдите вопросы, которые могут встретиться на вашем собеседовании</p>

      {/* Фильтры и поиск */}
      <div className="filters">
        <div className="search-box">
          <input
            type="text"
            placeholder="Поиск по вопросам, ответам или темам..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>

        <div className="filter-controls">
          <select value={topicFilter} onChange={(e) => setTopicFilter(e.target.value)}>
            <option value="">Все темы</option>
            {getUniqueTopics().map(topic => (
              <option key={topic} value={topic}>{topic}</option>
            ))}
          </select>

          <select value={levelFilter} onChange={(e) => setLevelFilter(e.target.value)}>
            <option value="">Все уровни</option>
            <option value="junior">Junior</option>
            <option value="middle">Middle</option>
            <option value="senior">Senior</option>
          </select>

          <select value={probabilitySort} onChange={(e) => setProbabilitySort(e.target.value)}>
            <option value="desc">По убыванию вероятности</option>
            <option value="asc">По возрастанию вероятности</option>
          </select>
        </div>
      </div>

      {/* Статистика */}
      <div className="stats">
        <span>Найдено вопросов: {filteredQuestions.length}</span>
        <span>Всего в базе: {questions.filter(q => q.approved).length}</span>
      </div>

      {/* Список вопросов */}
      <div className="questions-list">
        {filteredQuestions.map(question => (
          <div key={question.id} className="question-card">
            <div className="question-header">
              <h3 className="question-text">{question.question}</h3>
              <div className={`probability-badge ${getProbabilityColor(question.probability)}`}>
                {question.probability?.toFixed(1)}%
              </div>
            </div>

            {question.answer && (
              <div className="answer">
                <strong>Ответ:</strong> {question.answer}
              </div>
            )}

            <div className="question-meta">
              <span className="topic">Тема: {question.topic}</span>
              <span className="difficulty">Уровень: {question.difficulty}</span>
              {question.sources && question.sources.length > 0 && (
                <div className="sources">
                  <strong>Источники:</strong>
                  {question.sources.map((source, index) => (
                    <a
                      key={index}
                      href={getYouTubeTimestampUrl(source.url, source.timecode)}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="source-link"
                    >
                      {source.title} ({source.timecode})
                    </a>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}

        {filteredQuestions.length === 0 && (
          <div className="no-results">
            <p>По вашему запросу ничего не найдено.</p>
            <p>Попробуйте изменить фильтры или поисковый запрос.</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default PublicSide;