/**
 * AI Agronomist Service - Frontend API Client
 * Handles communication with AI endpoints for report generation and chat functionality
 */
import api from './api';

/**
 * AI Service class for interacting with AI Agronomist endpoints
 */
class AIService {
  /**
   * Generate AI agronomist report based on field analysis context
   * 
   * @param {Object} context - AIAnalysisContext object with field data
   * @returns {Promise<Object>} AIReportResponse with generated Markdown report
   * @throws {Error} If request fails or timeout occurs
   */
  async generateReport(context) {
    try {
      const response = await api.post('/api/v1/analysis/ai_report', {
        context: context
      }, {
        timeout: 180000 // 180 seconds (3 minutes) timeout for AI generation
      });
      
      return response.data;
    } catch (error) {
      this._handleError(error, 'Failed to generate AI report');
    }
  }

  /**
   * Send chat message to AI assistant with RAG context
   * 
   * @param {Object} originalContext - Original field analysis context
   * @param {Array} chatHistory - Array of previous chat messages
   * @param {string} newQuestion - New user question
   * @returns {Promise<Object>} AIChatResponse with AI answer
   * @throws {Error} If request fails or timeout occurs
   */
  async sendChatMessage(originalContext, chatHistory, newQuestion) {
    try {
      const response = await api.post('/api/v1/analysis/ai_chat', {
        original_context: originalContext,
        chat_history: chatHistory,
        new_question: newQuestion
      }, {
        timeout: 180000 // 180 seconds (3 minutes) timeout for chat
      });
      
      return response.data;
    } catch (error) {
      this._handleError(error, 'Failed to get AI chat response');
    }
  }

  /**
   * Check AI service health and availability
   * 
   * @returns {Promise<Object>} AI service status
   */
  async checkHealth() {
    try {
      const response = await api.get('/api/v1/ai/health');
      return response.data;
    } catch (error) {
      console.error('AI health check failed:', error);
      return {
        status: 'unavailable',
        message: 'Could not connect to AI service'
      };
    }
  }

  /**
   * Handle API errors and throw user-friendly messages
   * 
   * @private
   * @param {Error} error - Axios error object
   * @param {string} defaultMessage - Default error message
   * @throws {Error} User-friendly error with structured data
   */
  _handleError(error, defaultMessage) {
    console.error('AI Service Error:', error);

    // Extract error details from response
    if (error.response) {
      const status = error.response.status;
      const data = error.response.data;

      // Structured error response from backend
      if (data && data.detail && typeof data.detail === 'object') {
        const errorObj = new Error(data.detail.message || defaultMessage);
        errorObj.errorType = data.detail.error_type;
        errorObj.details = data.detail.details;
        errorObj.statusCode = status;
        throw errorObj;
      }

      // Simple error response
      if (data && data.detail) {
        const errorObj = new Error(data.detail);
        errorObj.statusCode = status;
        throw errorObj;
      }

      // Status-based error messages
      if (status === 401) {
        throw new Error('Требуется авторизация. Пожалуйста, войдите в систему.');
      } else if (status === 403) {
        throw new Error('Доступ запрещен.');
      } else if (status === 503) {
        throw new Error('AI сервис временно недоступен. Проверьте конфигурацию GEMINI_API_KEY.');
      } else if (status >= 500) {
        throw new Error('Ошибка сервера. Пожалуйста, попробуйте позже.');
      }
    }

    // Network or timeout errors
    if (error.code === 'ECONNABORTED') {
      const errorObj = new Error('Превышено время ожидания ответа от AI сервиса. Попробуйте снова.');
      errorObj.errorType = 'timeout';
      throw errorObj;
    }

    if (!error.response) {
      throw new Error('Не удалось подключиться к серверу. Проверьте интернет-соединение.');
    }

    // Generic error
    throw new Error(error.message || defaultMessage);
  }

  /**
   * Generate ML forecast for vegetation index time series
   * 
   * @param {Array} historicalData - Array of {date, value} objects
   * @param {string} indexName - Index name (NDVI, EVI, etc.)
   * @param {number} forecastHorizonDays - Forecast horizon (7-90 days)
   * @returns {Promise<Object>} Forecast response with historical, interpolated and forecast data
   * @throws {Error} If request fails
   */
  async forecastTimeSeries(historicalData, indexName, forecastHorizonDays = 30) {
    try {
      const response = await api.post('/api/v1/forecast/indices', {
        index_name: indexName,
        historical_data: historicalData,
        forecast_horizon_days: forecastHorizonDays
      }, {
        timeout: 60000 // 60 seconds timeout for ML training and prediction
      });
      
      return response.data;
    } catch (error) {
      this._handleError(error, 'Failed to generate forecast');
    }
  }

  /**
   * Build AIAnalysisContext from application state
   * Helper method to construct context payload from various data sources
   * 
   * @param {Object} params - Object containing field info, stats, zones, etc.
   * @returns {Object} AIAnalysisContext object
   */
  buildAnalysisContext({
    fieldName,
    fieldLocation,
    fieldAreaHa,
    cropType = null,
    sowingDate = null,
    dateOfScan,
    satellite = 'Sentinel-2',
    weatherContext = null,
    ndviStats,
    additionalIndicesStats = null,
    zones = null,
    temporalAnalysis = null
  }) {
    const context = {
      field_info: {
        name: fieldName,
        location: fieldLocation || { region: 'Не указано', lat: 0, lon: 0 },
        area_ha: fieldAreaHa,
        crop_type: cropType,
        sowing_date: sowingDate
      },
      analysis_info: {
        date_of_scan: dateOfScan,
        satellite: satellite
      },
      indices_summary: {
        NDVI: {
          mean: ndviStats.mean,
          std_dev: ndviStats.std || ndviStats.std_dev || 0,
          min: ndviStats.min,
          max: ndviStats.max
        }
      }
    };

    // Add optional weather context
    if (weatherContext) {
      context.weather_context = weatherContext;
    }

    // Add additional indices if available
    if (additionalIndicesStats) {
      Object.keys(additionalIndicesStats).forEach(indexName => {
        if (indexName !== 'NDVI' && additionalIndicesStats[indexName]) {
          context.indices_summary[indexName] = additionalIndicesStats[indexName];
        }
      });
    }

    // Add VRA zones if available
    if (zones && zones.length > 0) {
      context.zonation_results_VRA = {
        zones: zones.map(zone => ({
          id: zone.id || zone.zone_id,
          label: zone.label || zone.zone_label || `Зона ${zone.id}`,
          area_ha: zone.area_ha,
          percentage: zone.percentage,
          mean_NDVI: zone.mean_ndvi || zone.mean_NDVI
        }))
      };
    }

    // Add temporal analysis if available
    if (temporalAnalysis) {
      context.temporal_analysis = temporalAnalysis;
    }

    return context;
  }
}

// Export singleton instance
const aiService = new AIService();
export default aiService;

