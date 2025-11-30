/**
 * AIAgronomistPanel Component
 * Container component for AI-powered field analysis and chat
 * 
 * Features:
 * - Generate AI agronomist reports
 * - Interactive chat with RAG context
 * - State management for loading, errors, chat history
 * - Professional UX with loading states and error handling
 */
import React, { useState, useRef, useEffect } from 'react';
import AIReportViewer from './AIReportViewer';
import aiService from '../utils/aiService';
import './AIAgronomistPanel.css';

const AIAgronomistPanel = ({ analysisContext, onClose }) => {
  // State management
  const [status, setStatus] = useState('idle'); // idle, loading, success, error
  const [error, setError] = useState(null);
  const [reportData, setReportData] = useState(null);
  const [chatHistory, setChatHistory] = useState([]);
  const [currentQuestion, setCurrentQuestion] = useState('');
  const [isChatLoading, setIsChatLoading] = useState(false);

  // Refs
  const chatContainerRef = useRef(null);
  const questionInputRef = useRef(null);

  /**
   * Auto-scroll chat to bottom when new messages arrive
   */
  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [chatHistory]);

  /**
   * Generate AI report
   */
  const handleGenerateReport = async () => {
    setStatus('loading');
    setError(null);

    try {
      const response = await aiService.generateReport(analysisContext);

      setReportData(response);
      setStatus('success');

      // Add report to chat history as first assistant message
      setChatHistory([
        {
          role: 'assistant',
          content: response.report_markdown,
          timestamp: new Date().toISOString()
        }
      ]);

      // Focus on question input after report is ready
      setTimeout(() => {
        if (questionInputRef.current) {
          questionInputRef.current.focus();
        }
      }, 500);

    } catch (err) {
      setError({
        message: err.message || 'Не удалось сгенерировать отчет',
        type: err.errorType || 'unknown'
      });
      setStatus('error');
    }
  };

  /**
   * Send chat question
   */
  const handleSendQuestion = async (e) => {
    e.preventDefault();

    const question = currentQuestion.trim();
    if (!question || isChatLoading) return;

    // Add user question to chat history
    const userMessage = {
      role: 'user',
      content: question,
      timestamp: new Date().toISOString()
    };

    setChatHistory(prev => [...prev, userMessage]);
    setCurrentQuestion('');
    setIsChatLoading(true);
    setError(null);

    try {
      const response = await aiService.sendChatMessage(
        analysisContext,
        chatHistory,
        question
      );

      // Add AI response to chat history
      const assistantMessage = {
        role: 'assistant',
        content: response.answer,
        timestamp: new Date().toISOString()
      };

      setChatHistory(prev => [...prev, assistantMessage]);

    } catch (err) {
      setError({
        message: err.message || 'Не удалось получить ответ',
        type: err.errorType || 'unknown'
      });

      // Remove user message on error (optional)
      // setChatHistory(prev => prev.slice(0, -1));
    } finally {
      setIsChatLoading(false);
    }
  };

  /**
   * Render error message
   */
  const renderError = () => {
    if (!error) return null;

    let errorIcon = '❌';
    if (error.type === 'timeout') errorIcon = '⏱️';
    if (error.type === 'quota_exceeded') errorIcon = '🚫';

    return (
      <div className="ai-error-message">
        <span className="error-icon">{errorIcon}</span>
        <div className="error-content">
          <div className="error-title">Ошибка</div>
          <div className="error-text">{error.message}</div>
          {error.type === 'timeout' && (
            <div className="error-hint">
              AI сервис перегружен. Попробуйте через несколько секунд.
            </div>
          )}
          {error.type === 'quota_exceeded' && (
            <div className="error-hint">
              Превышен лимит запросов. Обратитесь к администратору.
            </div>
          )}
        </div>
      </div>
    );
  };

  /**
   * Render loading state
   */
  const renderLoading = () => (
    <div className="ai-loading">
      <div className="loading-spinner"></div>
      <div className="loading-text">
        Генерация AI отчета...
        <span className="loading-subtext">Это может занять до 30 секунд</span>
      </div>
    </div>
  );

  /**
   * Render initial state (before report generation)
   */
  const renderInitialState = () => (
    <div className="ai-welcome">
      <div className="welcome-icon">🤖</div>
      <h2>AI Агроном</h2>
      <p className="welcome-description">
        Получите экспертный анализ состояния вашего поля на основе спутниковых данных.
        AI агроном предоставит детальный отчет и ответит на ваши вопросы.
      </p>
      <div className="welcome-features">
        <div className="feature-item">
          <span className="feature-icon">📊</span>
          <span>Детальный анализ здоровья поля</span>
        </div>
        <div className="feature-item">
          <span className="feature-icon">🎯</span>
          <span>Зонирование и VRA стратегия</span>
        </div>
        <div className="feature-item">
          <span className="feature-icon">💬</span>
          <span>Интерактивный чат-консультант</span>
        </div>
      </div>
      <button
        className="btn-primary generate-btn"
        onClick={handleGenerateReport}
      >
        <span className="btn-icon">✨</span>
        Сгенерировать AI Отчет
      </button>
    </div>
  );

  /**
   * Render chat interface
   */
  const renderChat = () => (
    <div className="ai-chat-section">
      <div className="chat-header">
        <span className="chat-title">💬 Чат с AI Агрономом</span>
        <span className="chat-subtitle">Задайте вопрос по анализу поля</span>
      </div>

      <div className="chat-container" ref={chatContainerRef}>
        {chatHistory.slice(1).map((message, index) => (
          <div
            key={index}
            className={`chat-message ${message.role === 'user' ? 'user-message' : 'assistant-message'}`}
          >
            <div className="message-avatar">
              {message.role === 'user' ? '👤' : '🤖'}
            </div>
            <div className="message-content">
              <div className="message-text">{message.content}</div>
            </div>
          </div>
        ))}

        {isChatLoading && (
          <div className="chat-message assistant-message">
            <div className="message-avatar">🤖</div>
            <div className="message-content">
              <div className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        )}
      </div>

      <form className="chat-input-form" onSubmit={handleSendQuestion}>
        <input
          ref={questionInputRef}
          type="text"
          className="chat-input"
          placeholder="Задайте вопрос по анализу поля..."
          value={currentQuestion}
          onChange={(e) => setCurrentQuestion(e.target.value)}
          disabled={isChatLoading}
        />
        <button
          type="submit"
          className="chat-send-btn"
          disabled={!currentQuestion.trim() || isChatLoading}
        >
          <span>📤</span>
        </button>
      </form>
    </div>
  );

  return (
    <div className="ai-agronomist-panel">
      <div className="panel-header">
        <h1 className="panel-title">
          <span className="title-icon">🌾</span>
          AI Агроном
        </h1>
        <button className="close-btn" onClick={onClose} title="Закрыть">
          ✕
        </button>
      </div>

      <div className="panel-content">
        {status === 'idle' && renderInitialState()}
        {status === 'loading' && renderLoading()}
        {status === 'error' && (
          <div>
            {renderError()}
            <div className="retry-section">
              <button className="btn-secondary" onClick={handleGenerateReport}>
                🔄 Попробовать снова
              </button>
            </div>
          </div>
        )}
        {status === 'success' && reportData && (
          <div className="success-content">
            <AIReportViewer
              markdown={reportData.report_markdown}
              generationTime={reportData.generation_time_seconds}
              modelUsed={reportData.model_used}
            />
            {error && renderError()}
            {renderChat()}
          </div>
        )}
      </div>
    </div>
  );
};

export default AIAgronomistPanel;

