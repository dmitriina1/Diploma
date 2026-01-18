import React, { useState, useEffect } from 'react';

const API_URL = process.env.REACT_APP_API_URL || '';

function AdminPanel() {
  const [questions, setQuestions] = useState([]);
  const [url, setUrl] = useState('');
  const [topic, setTopic] = useState('General');
  const [level, setLevel] = useState('middle');
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentTaskId, setCurrentTaskId] = useState(null);
  const [processingStatus, setProcessingStatus] = useState(null);
  const [showSimilar, setShowSimilar] = useState(null);
  const [similarQuestions, setSimilarQuestions] = useState([]);
  const [editingQuestion, setEditingQuestion] = useState(null);
  const [newQuestion, setNewQuestion] = useState({ question: '', answer: '', topic: 'General', difficulty: 'middle' });
  const [similarNewQuestions, setSimilarNewQuestions] = useState([]);
  const [showSimilarNewQuestions, setShowSimilarNewQuestions] = useState(false);
  const [activeTab, setActiveTab] = useState('unapproved');

  useEffect(() => {
    fetchQuestions();
  }, []);

  const fetchQuestions = async () => {
    try {
      const response = await fetch(`${API_URL}/api/admin/questions`);
      const data = await response.json();
      setQuestions(data.questions || []);
    } catch (error) {
      console.error('Error fetching questions:', error);
    }
  };

  const handleProcessVideo = async () => {
    if (!url.trim()) return;

    setIsProcessing(true);
    setProcessingStatus({ progress: 0, step: 'Начинаем обработку...' });

    try {
      const response = await fetch(`${API_URL}/api/process-video`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ youtube_url: url, topic, level })
      });

      const data = await response.json();
      if (data.task_id) {
        setCurrentTaskId(data.task_id);
        pollTask(data.task_id);
      }
    } catch (error) {
      console.error('Error processing video:', error);
      setIsProcessing(false);
      setProcessingStatus(null);
    }
  };

  const pollTask = async (taskId) => {
    try {
      const response = await fetch(`${API_URL}/api/task/${taskId}`);
      const data = await response.json();

      setProcessingStatus({
        progress: data.progress || 0,
        step: data.step || 'Обработка...'
      });

      if (data.status === 'completed') {
        setIsProcessing(false);
        setCurrentTaskId(null);
        setProcessingStatus(null);
        fetchQuestions(); // Обновить список вопросов
      } else if (data.status === 'error') {
        setIsProcessing(false);
        setCurrentTaskId(null);
        setProcessingStatus({ progress: 0, step: `Ошибка: ${data.error || 'Неизвестная ошибка'}` });
      } else {
        // Продолжить polling
        setTimeout(() => pollTask(taskId), 2000);
      }
    } catch (error) {
      console.error('Error polling task:', error);
      setTimeout(() => pollTask(taskId), 2000);
    }
  };

  const handleApproveQuestions = async (questionIds) => {
    try {
      const response = await fetch(`${API_URL}/api/admin/approve-questions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question_ids: questionIds })
      });

      if (response.ok) {
        fetchQuestions(); // Обновить список
      }
    } catch (error) {
      console.error('Error approving questions:', error);
    }
  };

  const handleShowSimilar = async (questionId) => {
    try {
      const response = await fetch(`${API_URL}/api/admin/similar-questions/${questionId}`);
      const data = await response.json();
      setSimilarQuestions(data.similar_questions || []);
      setShowSimilar(questionId);
    } catch (error) {
      console.error('Error fetching similar questions:', error);
    }
  };

  const handleReplaceQuestion = async (questionId, similarQuestionId) => {
    try {
      const response = await fetch(`${API_URL}/api/admin/replace-question/${questionId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ similar_question_id: similarQuestionId })
      });

      if (response.ok) {
        setShowSimilar(null);
        fetchQuestions(); // Обновить список - вопрос исчезнет
      }
    } catch (error) {
      console.error('Error replacing question:', error);
    }
  };

  const handleEditQuestion = async (questionId, updatedData) => {
    try {
      const response = await fetch(`${API_URL}/api/admin/questions/${questionId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updatedData)
      });

      if (response.ok) {
        setEditingQuestion(null);
        fetchQuestions();
      }
    } catch (error) {
      console.error('Error updating question:', error);
    }
  };

  const handleDeleteQuestion = async (questionId) => {
    if (!confirm('Вы уверены, что хотите удалить этот вопрос?')) return;

    try {
      const response = await fetch(`${API_URL}/api/admin/questions/${questionId}`, {
        method: 'DELETE'
      });

      if (response.ok) {
        fetchQuestions();
      }
    } catch (error) {
      console.error('Error deleting question:', error);
    }
  };

  const handleCreateQuestion = async () => {
    try {
      const response = await fetch(`${API_URL}/api/admin/questions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newQuestion)
      });

      if (response.ok) {
        setNewQuestion({ question: '', answer: '', topic: 'General', difficulty: 'middle' });
        setSimilarNewQuestions([]);
        setShowSimilarNewQuestions(false);
        fetchQuestions();
      }
    } catch (error) {
      console.error('Error creating question:', error);
    }
  };

  const checkSimilarQuestions = async () => {
    if (!newQuestion.question.trim()) return;
    
    try {
      const response = await fetch(`${API_URL}/api/questions/similar?query=${encodeURIComponent(newQuestion.question)}&limit=5`);
      if (response.ok) {
        const data = await response.json();
        setSimilarNewQuestions(data);
        setShowSimilarNewQuestions(data.length > 0);
      }
    } catch (error) {
      console.error('Error checking similar questions:', error);
    }
  };

  const getUnapprovedQuestions = () => {
    return questions.filter(q => !q.approved);
  };

  const getApprovedQuestions = () => {
    return questions.filter(q => q.approved);
  };

  return (
    <div className="admin-panel">
      <h1>Панель администратора</h1>

      {/* Форма обработки видео */}
      <div className="video-processing">
        <h2>Обработка YouTube видео</h2>
        <div className="form-group">
          <input
            type="text"
            placeholder="YouTube URL"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            disabled={isProcessing}
          />
          <select value={topic} onChange={(e) => setTopic(e.target.value)} disabled={isProcessing}>
            <option value="General">Общее</option>
            <option value="Backend">Backend</option>
            <option value="Frontend">Frontend</option>
            <option value="DevOps">DevOps</option>
          </select>
          <select value={level} onChange={(e) => setLevel(e.target.value)} disabled={isProcessing}>
            <option value="junior">Junior</option>
            <option value="middle">Middle</option>
            <option value="senior">Senior</option>
          </select>
          <button onClick={handleProcessVideo} disabled={isProcessing}>
            {isProcessing ? 'Обработка...' : 'Обработать видео'}
          </button>
        </div>

        {processingStatus && (
          <div className="processing-status">
            <div className="progress-bar">
              <div className="progress-fill" style={{ width: `${processingStatus.progress}%` }}></div>
            </div>
            <p>{processingStatus.step}</p>
          </div>
        )}
      </div>

      {/* Создание нового вопроса */}
      <div className="create-question">
        <h2>Создать новый вопрос</h2>
        <div className="form-group">
          <input
            type="text"
            placeholder="Вопрос"
            value={newQuestion.question}
            onChange={(e) => {
              setNewQuestion({...newQuestion, question: e.target.value});
              // Очищаем похожие вопросы при изменении текста
              if (showSimilarNewQuestions) {
                setShowSimilarNewQuestions(false);
                setSimilarNewQuestions([]);
              }
            }}
          />
          <input
            type="text"
            placeholder="Ответ"
            value={newQuestion.answer}
            onChange={(e) => setNewQuestion({...newQuestion, answer: e.target.value})}
          />
          <select value={newQuestion.topic} onChange={(e) => setNewQuestion({...newQuestion, topic: e.target.value})}>
            <option value="General">Общее</option>
            <option value="Backend">Backend</option>
            <option value="Frontend">Frontend</option>
            <option value="DevOps">DevOps</option>
          </select>
          <select value={newQuestion.difficulty} onChange={(e) => setNewQuestion({...newQuestion, difficulty: e.target.value})}>
            <option value="junior">Junior</option>
            <option value="middle">Middle</option>
            <option value="senior">Senior</option>
          </select>
          
          {/* Предупреждение о похожих вопросах */}
          {showSimilarNewQuestions && (
            <div className="similar-warning">
              <p>⚠️ Найдено {similarNewQuestions.length} похожих вопросов. Если вы уверены, что хотите создать новый вопрос, нажмите "Создать".</p>
              <button 
                type="button" 
                onClick={() => setShowSimilarNewQuestions(!showSimilarNewQuestions)}
                className="show-similar-btn"
              >
                {showSimilarNewQuestions ? 'Скрыть похожие' : 'Показать похожие'}
              </button>
            </div>
          )}
          
          {/* Список похожих вопросов */}
          {showSimilarNewQuestions && similarNewQuestions.length > 0 && (
            <div className="similar-questions-list">
              <h4>Похожие вопросы:</h4>
              {similarNewQuestions.map((q, index) => (
                <div key={index} className="similar-question-item">
                  <strong>{q.question}</strong>
                  <p>{q.answer}</p>
                  <small>Тема: {q.topic} | Сложность: {q.difficulty}</small>
                </div>
              ))}
            </div>
          )}
          
          <div className="button-group">
            <button type="button" onClick={checkSimilarQuestions} className="check-similar-btn">
              Проверить похожие
            </button>
            <button onClick={handleCreateQuestion} disabled={!newQuestion.question.trim()}>
              Создать
            </button>
          </div>
        </div>
      </div>

      {/* Неодобренные вопросы */}
      {getUnapprovedQuestions().length > 0 && (
        <div className="unapproved-questions">
          <h2>Неодобренные вопросы ({getUnapprovedQuestions().length})</h2>
          <button
            onClick={() => handleApproveQuestions(getUnapprovedQuestions().map(q => q.id))}
            className="approve-all-btn"
          >
            Одобрить все ({getUnapprovedQuestions().length})
          </button>

          <div className="questions-list">
            {getUnapprovedQuestions().map(question => (
              <div key={question.id} className="question-item unapproved">
                <div className="question-content">
                  <h3>{question.question}</h3>
                  <p className="answer">{question.answer}</p>
                  <div className="question-meta">
                    <span>Тема: {question.topic}</span>
                    <span>Сложность: {question.difficulty}</span>
                    <span>Источник: {question.video_title}</span>
                    {question.similar_count > 0 && (
                      <button
                        onClick={() => handleShowSimilar(question.id)}
                        className="similar-btn"
                      >
                        Похожих: {question.similar_count}
                      </button>
                    )}
                  </div>
                </div>
                <div className="question-actions">
                  <button onClick={() => handleApproveQuestions([question.id])}>Одобрить</button>
                  <button onClick={() => setEditingQuestion(question)}>Редактировать</button>
                  <button onClick={() => handleDeleteQuestion(question.id)} className="delete-btn">Удалить</button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Одобренные вопросы */}
      <div className="approved-questions">
        <h2>Одобренные вопросы ({getApprovedQuestions().length})</h2>
        <div className="questions-list">
          {getApprovedQuestions().map(question => (
            <div key={question.id} className="question-item approved">
              <div className="question-content">
                <h3>{question.question}</h3>
                <p className="answer">{question.answer}</p>
                <div className="question-meta">
                  <span>Тема: {question.topic}</span>
                  <span>Сложность: {question.difficulty}</span>
                  <span>Вероятность: {question.probability?.toFixed(1)}%</span>
                  <span>Источник: {question.video_title}</span>
                </div>
              </div>
              <div className="question-actions">
                <button onClick={() => setEditingQuestion(question)}>Редактировать</button>
                <button onClick={() => handleDeleteQuestion(question.id)} className="delete-btn">Удалить</button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Модальное окно редактирования */}
      {editingQuestion && (
        <div className="modal">
          <div className="modal-content">
            <h2>Редактировать вопрос</h2>
            <input
              type="text"
              value={editingQuestion.question}
              onChange={(e) => setEditingQuestion({...editingQuestion, question: e.target.value})}
            />
            <textarea
              value={editingQuestion.answer || ''}
              onChange={(e) => setEditingQuestion({...editingQuestion, answer: e.target.value})}
              placeholder="Ответ"
            />
            <select
              value={editingQuestion.topic}
              onChange={(e) => setEditingQuestion({...editingQuestion, topic: e.target.value})}
            >
              <option value="General">Общее</option>
              <option value="Backend">Backend</option>
              <option value="Frontend">Frontend</option>
              <option value="DevOps">DevOps</option>
            </select>
            <select
              value={editingQuestion.difficulty}
              onChange={(e) => setEditingQuestion({...editingQuestion, difficulty: e.target.value})}
            >
              <option value="junior">Junior</option>
              <option value="middle">Middle</option>
              <option value="senior">Senior</option>
            </select>
            <div className="modal-actions">
              <button onClick={() => handleEditQuestion(editingQuestion.id, editingQuestion)}>Сохранить</button>
              <button onClick={() => setEditingQuestion(null)}>Отмена</button>
            </div>
          </div>
        </div>
      )}

      {/* Модальное окно похожих вопросов */}
      {showSimilar && (
        <div className="modal">
          <div className="modal-content">
            <h2>Похожие вопросы</h2>
            <div className="similar-questions-list">
              {similarQuestions.map(similar => (
                <div key={similar.id} className="similar-question">
                  <h3>{similar.question}</h3>
                  <p>Тема: {similar.topic} | Сложность: {similar.difficulty} | Вероятность: {similar.probability?.toFixed(1)}%</p>
                  <button onClick={() => handleReplaceQuestion(showSimilar, similar.id)}>
                    Заменить на этот вопрос
                  </button>
                </div>
              ))}
            </div>
            <div className="modal-actions">
              <button onClick={() => setShowSimilar(null)}>Закрыть</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default AdminPanel;