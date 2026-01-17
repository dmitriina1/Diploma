import React, { useState, useEffect, useRef, useCallback } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import PublicSide from './PublicSide';
import AdminPanel from './AdminPanel';
import './App.css';

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
  // Стили
  const styles = {
    minHeight: '100vh',
    backgroundColor: '#0f172a',
    color: '#e2e8f0',
    fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
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
    nav: {
      display: 'flex',
      justifyContent: 'center',
      gap: '20px',
      padding: '10px',
      background: '#f8fafc',
      borderBottom: '1px solid #e2e8f0',
    },
    navLink: {
      textDecoration: 'none',
      color: '#475569',
      fontWeight: '500',
      padding: '8px 16px',
      borderRadius: '4px',
      transition: 'background 0.2s',
    },
  };

  return (
    <Router future={{
      v7_startTransition: true,
      v7_relativeSplatPath: true
    }}>
      <Routes>
        <Route path="/" element={<MainPage />} />
        <Route path="/public" element={<PublicSide />} />
        <Route path="/admin" element={<AdminPanel />} />
      </Routes>
    </Router>
  );
}

function MainPage() {
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

  const connectWebSocket = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    console.log('🔌 Connecting to WebSocket...');
    const ws = new WebSocket(`${WS_URL}/ws/${clientId.current}`);

    ws.onopen = () => {
      console.log('✅ WebSocket connected');
      setWsConnected(true);
      // Отправка ping каждые 30 секунд для поддержания соединения
      pollInterval.current = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send('ping');
        }
      }, 30000);
    };

    ws.onmessage = (event) => {
      if (event.data === 'pong') return;

      try {
        const data = JSON.parse(event.data);
        console.log('📨 WebSocket message:', data);

        if (data.type === 'progress') {
          setProgress(data.progress || 0);
          setCurrentStep(data.step || '');
        } else if (data.type === 'complete') {
          setIsProcessing(false);
          setProgress(100);
          setCurrentStep('Обработка завершена');
          setQuestions(data.questions || []);
          setVideoTitle(data.video_title || '');
          // Добавление в историю
          setTaskHistory(prev => [{
            id: Date.now(),
            url: url,
            topic: topic,
            level: level,
            timestamp: new Date().toLocaleString(),
            status: 'completed',
            questionsCount: data.questions?.length || 0
          }, ...prev.slice(0, 9)]);
        } else if (data.type === 'error') {
          setIsProcessing(false);
          setError(data.message || 'Произошла ошибка');
          setTaskHistory(prev => [{
            id: Date.now(),
            url: url,
            topic: topic,
            level: level,
            timestamp: new Date().toLocaleString(),
            status: 'error',
            error: data.message
          }, ...prev.slice(0, 9)]);
        }
      } catch (error) {
        console.error('❌ WebSocket message parse error:', error);
      }
    };

    ws.onclose = () => {
      console.log('❌ WebSocket disconnected');
      setWsConnected(false);
      // Автопереподключение
      reconnectTimeout.current = setTimeout(() => {
        connectWebSocket();
      }, 5000);
    };

    ws.onerror = (error) => {
      console.error('❌ WebSocket error:', error);
      setWsConnected(false);
    };

    wsRef.current = ws;
  }, [url, topic, level]);

  useEffect(() => {
    connectWebSocket();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (reconnectTimeout.current) {
        clearTimeout(reconnectTimeout.current);
      }
      if (pollInterval.current) {
        clearInterval(pollInterval.current);
      }
    };
  }, [connectWebSocket]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!url.trim()) return;

    setIsProcessing(true);
    setProgress(0);
    setCurrentStep('Инициализация...');
    setError('');
    setQuestions([]);
    setVideoTitle('');

    try {
      const response = await fetch(`${API_URL}/process-url`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          url: url.trim(),
          topic,
          level,
          client_id: clientId.current
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('✅ Process started:', data);
      setCurrentTaskId(data.task_id);
    } catch (error) {
      console.error('❌ Process error:', error);
      setIsProcessing(false);
      setError(error.message);
    }
  };

  const clearHistory = () => {
    setTaskHistory([]);
  };

  return (
    <div style={styles.container}>
      {/* Header */}
      <header style={styles.header}>
        <h1 style={styles.title}>🎓 Интеллектуальная система подготовки к собеседованиям</h1>
        <p style={styles.subtitle}>Автоматическая генерация вопросов из YouTube видео</p>
        <div style={styles.connectionStatus}>
          <div style={{
            ...styles.statusDot,
            backgroundColor: wsConnected ? '#10b981' : '#ef4444'
          }}></div>
          {wsConnected ? 'Подключено' : 'Отключено'}
        </div>
      </header>

      {/* Main Content */}
      <main style={styles.main}>
        <form onSubmit={handleSubmit} style={styles.form}>
          <div style={styles.row}>
            <div style={styles.inputGroup}>
              <label style={styles.label}>YouTube URL</label>
              <input
                type="url"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="https://www.youtube.com/watch?v=..."
                required
                style={styles.input}
              />
            </div>
          </div>

          <div style={styles.row}>
            <div style={styles.inputGroup}>
              <label style={styles.label}>Тема</label>
              <select value={topic} onChange={(e) => setTopic(e.target.value)} style={styles.select}>
                <option value="Backend">Backend</option>
                <option value="Frontend">Frontend</option>
                <option value="DevOps">DevOps</option>
                <option value="Data Science">Data Science</option>
                <option value="Mobile">Mobile</option>
                <option value="Other">Другое</option>
              </select>
            </div>
            <div style={styles.inputGroup}>
              <label style={styles.label}>Уровень</label>
              <select value={level} onChange={(e) => setLevel(e.target.value)} style={styles.select}>
                <option value="junior">Junior</option>
                <option value="middle">Middle</option>
                <option value="senior">Senior</option>
              </select>
            </div>
          </div>

          <button
            type="submit"
            disabled={isProcessing}
            style={{
              ...styles.button,
              opacity: isProcessing ? 0.6 : 1,
              cursor: isProcessing ? 'not-allowed' : 'pointer'
            }}
          >
            {isProcessing ? 'Обработка...' : 'Начать обработку'}
          </button>
        </form>

        {/* Progress */}
        {isProcessing && (
          <div style={styles.progressContainer}>
            <div style={styles.progressHeader}>
              <span style={styles.progressText}>{currentStep}</span>
              <span style={styles.progressPercent}>{progress}%</span>
            </div>
            <div style={styles.progressBar}>
              <div style={styles.progressFill} style={{ width: `${progress}%` }}></div>
            </div>
          </div>
        )}

        {/* Error */}
        {error && (
          <div style={styles.error}>
            <strong>Ошибка:</strong> {error}
          </div>
        )}

        {/* Results */}
        {questions.length > 0 && (
          <div style={styles.results}>
            <h2 style={styles.resultsTitle}>
              {videoTitle && <span style={styles.videoTitle}>{videoTitle}</span>}
              Сгенерированные вопросы ({questions.length})
            </h2>
            <div style={styles.questionsList}>
              {questions.map((question, index) => (
                <div key={index} style={styles.questionCard}>
                  <div style={styles.questionHeader}>
                    <span style={styles.questionNumber}>#{index + 1}</span>
                    <span style={{
                      ...styles.difficultyBadge,
                      backgroundColor: question.level === 'junior' ? '#10b981' :
                                     question.level === 'middle' ? '#f59e0b' : '#ef4444'
                    }}>
                      {question.level}
                    </span>
                    <span style={styles.topicBadge}>{question.topic}</span>
                  </div>
                  <p style={styles.questionText}>{question.text}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* History */}
        {taskHistory.length > 0 && (
          <div style={styles.history}>
            <div style={styles.historyTitle}>
              История задач
              <button
                onClick={clearHistory}
                style={{
                  marginLeft: '10px',
                  padding: '4px 8px',
                  fontSize: '0.8rem',
                  backgroundColor: '#ef4444',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer'
                }}
              >
                Очистить
              </button>
            </div>
            {taskHistory.map((task) => (
              <div key={task.id} style={styles.historyItem}>
                <div>
                  <strong>{task.url}</strong>
                  <div style={styles.historyMeta}>
                    {task.topic} • {task.level} • {task.timestamp}
                  </div>
                </div>
                <div style={{
                  color: task.status === 'completed' ? '#10b981' :
                         task.status === 'error' ? '#ef4444' : '#64748b'
                }}>
                  {task.status === 'completed' ? `✅ ${task.questionsCount} вопросов` :
                   task.status === 'error' ? `❌ ${task.error || 'Ошибка'}` :
                   task.status}
                </div>
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

export default App;