import React, { useState, useEffect, useRef, useCallback } from 'react';

// Конфигурация
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
const WS_URL = process.env.REACT_APP_WS_URL || 'ws://localhost:8000';

// Генерация уникального ID клиента
const generateClientId = () => {
  let clientId = localStorage.getItem('clientId');
  if (!clientId) {
    clientId = 'client_' + Math.random().toString(36).substr(2, 9);
    localStorage.setItem('clientId', clientId);
  }
  return clientId;
};

function App() {
  const [url, setUrl] = useState('');
  const [topic, setTopic] = useState('Backend');
  const [level, setLevel] = useState('middle');
  const [isProcessing, setIsProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState('');
  const [questions, setQuestions] = useState([]);
  const [error, setError] = useState('');
  const [videoTitle, setVideoTitle] = useState('');
  const [wsConnected, setWsConnected] = useState(false);
  const [taskHistory, setTaskHistory] = useState([]);
  const [currentTaskId, setCurrentTaskId] = useState(null);
  
  const wsRef = useRef(null);
  const clientId = useRef(generateClientId());
  const reconnectTimeout = useRef(null);
  const pollInterval = useRef(null);

  // WebSocket подключение
  const connectWebSocket = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;
    
    const ws = new WebSocket(`${WS_URL}/ws/${clientId.current}`);
    
    ws.onopen = () => {
      console.log('✅ WebSocket connected');
      setWsConnected(true);
      // Keep-alive ping
      const pingInterval = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send('ping');
        }
      }, 30000);
      ws.pingInterval = pingInterval;
    };
    
    ws.onmessage = (event) => {
      if (event.data === 'pong') return;
      
      try {
        const data = JSON.parse(event.data);
        console.log('📨 WS message:', data);
        
        if (data.type === 'progress') {
          setProgress(data.progress);
          setCurrentStep(data.step);
        } else if (data.type === 'result') {
          setQuestions(data.questions || []);
          setVideoTitle(data.video_title || '');
          setIsProcessing(false);
          setProgress(100);
          setCurrentStep('Готово!');
          
          // Добавляем в историю
          setTaskHistory(prev => [{
            id: data.task_id,
            title: data.video_title,
            questionsCount: data.questions?.length || 0,
            timestamp: new Date().toLocaleString()
          }, ...prev.slice(0, 9)]);
        } else if (data.type === 'error') {
          setError(data.error);
          setIsProcessing(false);
        }
      } catch (e) {
        console.error('Parse error:', e);
      }
    };
    
    ws.onclose = () => {
      console.log('❌ WebSocket disconnected');
      setWsConnected(false);
      clearInterval(ws.pingInterval);
      
      // Переподключение через 3 секунды
      reconnectTimeout.current = setTimeout(() => {
        connectWebSocket();
      }, 3000);
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
    
    wsRef.current = ws;
  }, []);

  useEffect(() => {
    connectWebSocket();
    
    return () => {
      if (reconnectTimeout.current) {
        clearTimeout(reconnectTimeout.current);
      }
      if (pollInterval.current) {
        clearInterval(pollInterval.current);
      }
      if (wsRef.current) {
        clearInterval(wsRef.current.pingInterval);
        wsRef.current.close();
      }
    };
  }, [connectWebSocket]);

  // Отправка запроса на обработку
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!url.trim()) {
      setError('Введите URL видео');
      return;
    }
    
    setIsProcessing(true);
    setProgress(0);
    setCurrentStep('Запуск обработки...');
    setError('');
    setQuestions([]);
    setVideoTitle('');
    
    try {
      const response = await fetch(`${API_URL}/api/process-video/${clientId.current}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          youtube_url: url,
          topic: topic,
          level: level
        }),
      });
      
      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Ошибка сервера');
      }
      
      const data = await response.json();
      console.log('Task started:', data.task_id);
      setCurrentTaskId(data.task_id);
      
      // Запускаем polling для проверки статуса
      if (pollInterval.current) clearInterval(pollInterval.current);
      pollInterval.current = setInterval(async () => {
        try {
          const statusRes = await fetch(`${API_URL}/api/task/${data.task_id}`);
          if (statusRes.ok) {
            const status = await statusRes.json();
            setProgress(status.progress || 0);
            setCurrentStep(status.step || '');
            
            if (status.status === 'completed' && status.result) {
              setQuestions(status.result.questions || []);
              setVideoTitle(status.result.video_title || '');
              setIsProcessing(false);
              setProgress(100);
              setCurrentStep('Готово!');
              clearInterval(pollInterval.current);
              
              // Добавляем в историю
              setTaskHistory(prev => [{
                id: data.task_id,
                title: status.result.video_title,
                questionsCount: status.result.questions?.length || 0,
                timestamp: new Date().toLocaleString()
              }, ...prev.slice(0, 9)]);
            }
          }
        } catch (e) {
          console.error('Poll error:', e);
        }
      }, 2000);
      
    } catch (err) {
      setError(err.message);
      setIsProcessing(false);
    }
  };

  return (
    <div style={styles.container}>
      {/* Header */}
      <header style={styles.header}>
        <h1 style={styles.title}>🎯 Interview Prep</h1>
        <p style={styles.subtitle}>Извлечение вопросов для собеседований из YouTube</p>
        <div style={styles.connectionStatus}>
          <span style={{
            ...styles.statusDot,
            backgroundColor: wsConnected ? '#10b981' : '#ef4444'
          }}></span>
          {wsConnected ? 'Подключено' : 'Переподключение...'}
        </div>
      </header>

      {/* Main Form */}
      <main style={styles.main}>
        <form onSubmit={handleSubmit} style={styles.form}>
          <div style={styles.inputGroup}>
            <label style={styles.label}>YouTube URL</label>
            <input
              type="text"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://www.youtube.com/watch?v=..."
              style={styles.input}
              disabled={isProcessing}
            />
          </div>

          <div style={styles.row}>
            <div style={styles.inputGroup}>
              <label style={styles.label}>Тема</label>
              <select 
                value={topic} 
                onChange={(e) => setTopic(e.target.value)}
                style={styles.select}
                disabled={isProcessing}
              >
                <option value="Backend">Backend</option>
                <option value="Frontend">Frontend</option>
                <option value="DevOps">DevOps</option>
                <option value="Data Science">Data Science</option>
                <option value="System Design">System Design</option>
                <option value="General">Общее</option>
              </select>
            </div>

            <div style={styles.inputGroup}>
              <label style={styles.label}>Уровень</label>
              <select 
                value={level} 
                onChange={(e) => setLevel(e.target.value)}
                style={styles.select}
                disabled={isProcessing}
              >
                <option value="junior">Junior</option>
                <option value="middle">Middle</option>
                <option value="senior">Senior</option>
              </select>
            </div>
          </div>

          <button 
            type="submit" 
            style={{
              ...styles.button,
              opacity: isProcessing ? 0.7 : 1,
              cursor: isProcessing ? 'not-allowed' : 'pointer'
            }}
            disabled={isProcessing}
          >
            {isProcessing ? '⏳ Обработка...' : '🚀 Извлечь вопросы'}
          </button>
        </form>

        {/* Progress Bar */}
        {isProcessing && (
          <div style={styles.progressContainer}>
            <div style={styles.progressHeader}>
              <span style={styles.progressText}>{currentStep}</span>
              <span style={styles.progressPercent}>{progress}%</span>
            </div>
            <div style={styles.progressBar}>
              <div 
                style={{
                  ...styles.progressFill,
                  width: `${progress}%`
                }}
              ></div>
            </div>
          </div>
        )}

        {/* Error */}
        {error && (
          <div style={styles.error}>
            ❌ {error}
          </div>
        )}

        {/* Results */}
        {questions.length > 0 && (
          <div style={styles.results}>
            <h2 style={styles.resultsTitle}>
              📋 Извлечённые вопросы ({questions.length})
              {videoTitle && <span style={styles.videoTitle}> — {videoTitle}</span>}
            </h2>
            
            <div style={styles.questionsList}>
              {questions.map((q, index) => (
                <div key={index} style={styles.questionCard}>
                  <div style={styles.questionHeader}>
                    <span style={styles.questionNumber}>#{index + 1}</span>
                    <span style={{
                      ...styles.difficultyBadge,
                      backgroundColor: 
                        q.difficulty === 'junior' ? '#10b981' :
                        q.difficulty === 'middle' ? '#f59e0b' : '#ef4444'
                    }}>
                      {q.difficulty}
                    </span>
                    {q.topic && (
                      <span style={styles.topicBadge}>{q.topic}</span>
                    )}
                  </div>
                  <p style={styles.questionText}>{q.question}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Task History */}
        {taskHistory.length > 0 && (
          <div style={styles.history}>
            <h3 style={styles.historyTitle}>📜 История обработок</h3>
            {taskHistory.map((task, index) => (
              <div key={index} style={styles.historyItem}>
                <span>{task.title}</span>
                <span style={styles.historyMeta}>
                  {task.questionsCount} вопросов • {task.timestamp}
                </span>
              </div>
            ))}
          </div>
        )}
      </main>

      {/* Footer */}
      <footer style={styles.footer}>
        <p>Магистерская диссертация • 09.04.02 Информационные системы и технологии</p>
        <p style={styles.footerTech}>n8n + Ollama + Whisper + FastAPI + React</p>
      </footer>
    </div>
  );
}

// Стили
const styles = {
  container: {
    minHeight: '100vh',
    backgroundColor: '#0f172a',
    color: '#e2e8f0',
    fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
  },
  header: {
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    padding: '40px 20px',
    textAlign: 'center',
  },
  title: {
    fontSize: '2.5rem',
    fontWeight: 700,
    margin: 0,
    marginBottom: '10px',
  },
  subtitle: {
    fontSize: '1.1rem',
    opacity: 0.9,
    margin: 0,
  },
  connectionStatus: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '8px',
    marginTop: '15px',
    padding: '6px 12px',
    backgroundColor: 'rgba(255,255,255,0.1)',
    borderRadius: '20px',
    fontSize: '0.85rem',
  },
  statusDot: {
    width: '8px',
    height: '8px',
    borderRadius: '50%',
  },
  main: {
    maxWidth: '800px',
    margin: '0 auto',
    padding: '30px 20px',
  },
  form: {
    backgroundColor: '#1e293b',
    padding: '30px',
    borderRadius: '16px',
    boxShadow: '0 4px 6px rgba(0, 0, 0, 0.3)',
  },
  inputGroup: {
    marginBottom: '20px',
    flex: 1,
  },
  label: {
    display: 'block',
    marginBottom: '8px',
    fontWeight: 500,
    color: '#94a3b8',
  },
  input: {
    width: '100%',
    padding: '14px 16px',
    fontSize: '1rem',
    border: '2px solid #334155',
    borderRadius: '10px',
    backgroundColor: '#0f172a',
    color: '#e2e8f0',
    outline: 'none',
    transition: 'border-color 0.2s',
    boxSizing: 'border-box',
  },
  select: {
    width: '100%',
    padding: '14px 16px',
    fontSize: '1rem',
    border: '2px solid #334155',
    borderRadius: '10px',
    backgroundColor: '#0f172a',
    color: '#e2e8f0',
    outline: 'none',
    cursor: 'pointer',
    boxSizing: 'border-box',
  },
  row: {
    display: 'flex',
    gap: '20px',
  },
  button: {
    width: '100%',
    padding: '16px',
    fontSize: '1.1rem',
    fontWeight: 600,
    color: 'white',
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    border: 'none',
    borderRadius: '10px',
    cursor: 'pointer',
    transition: 'transform 0.2s, box-shadow 0.2s',
  },
  progressContainer: {
    marginTop: '30px',
    backgroundColor: '#1e293b',
    padding: '20px',
    borderRadius: '12px',
  },
  progressHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    marginBottom: '10px',
  },
  progressText: {
    color: '#94a3b8',
  },
  progressPercent: {
    fontWeight: 600,
    color: '#667eea',
  },
  progressBar: {
    height: '8px',
    backgroundColor: '#334155',
    borderRadius: '4px',
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    background: 'linear-gradient(90deg, #667eea, #764ba2)',
    borderRadius: '4px',
    transition: 'width 0.3s ease',
  },
  error: {
    marginTop: '20px',
    padding: '15px 20px',
    backgroundColor: 'rgba(239, 68, 68, 0.1)',
    border: '1px solid #ef4444',
    borderRadius: '10px',
    color: '#ef4444',
  },
  results: {
    marginTop: '30px',
  },
  resultsTitle: {
    fontSize: '1.3rem',
    fontWeight: 600,
    marginBottom: '20px',
  },
  videoTitle: {
    fontSize: '0.9rem',
    fontWeight: 400,
    color: '#94a3b8',
  },
  questionsList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '15px',
  },
  questionCard: {
    backgroundColor: '#1e293b',
    padding: '20px',
    borderRadius: '12px',
    border: '1px solid #334155',
  },
  questionHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    marginBottom: '12px',
  },
  questionNumber: {
    color: '#667eea',
    fontWeight: 600,
  },
  difficultyBadge: {
    padding: '4px 10px',
    borderRadius: '12px',
    fontSize: '0.75rem',
    fontWeight: 600,
    color: 'white',
    textTransform: 'uppercase',
  },
  topicBadge: {
    padding: '4px 10px',
    borderRadius: '12px',
    fontSize: '0.75rem',
    backgroundColor: '#334155',
    color: '#94a3b8',
  },
  questionText: {
    margin: 0,
    lineHeight: 1.6,
    fontSize: '1rem',
  },
  history: {
    marginTop: '40px',
    padding: '20px',
    backgroundColor: '#1e293b',
    borderRadius: '12px',
  },
  historyTitle: {
    margin: 0,
    marginBottom: '15px',
    fontSize: '1rem',
    color: '#94a3b8',
  },
  historyItem: {
    display: 'flex',
    justifyContent: 'space-between',
    padding: '10px 0',
    borderBottom: '1px solid #334155',
    fontSize: '0.9rem',
  },
  historyMeta: {
    color: '#64748b',
    fontSize: '0.8rem',
  },
  footer: {
    textAlign: 'center',
    padding: '30px 20px',
    color: '#64748b',
    fontSize: '0.9rem',
  },
  footerTech: {
    marginTop: '5px',
    fontSize: '0.8rem',
    color: '#475569',
  },
};

export default App;
