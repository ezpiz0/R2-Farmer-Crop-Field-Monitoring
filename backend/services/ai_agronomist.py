"""
AI Agronomist Service - Integration with Google Gemini
Provides AI-powered field analysis, report generation, and chat functionality
"""
import os
import json
import logging
import time
import asyncio
from typing import Optional, Dict, Any, List
from pathlib import Path

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logging.warning("google-generativeai not installed. AI features will be disabled.")

from api.ai_schemas import (
    AIAnalysisContext,
    AIReportResponse,
    AIChatResponse,
    AIErrorResponse,
    ChatMessage
)

# Setup logging
logger = logging.getLogger(__name__)


# ============================================================================
# System Prompts
# ============================================================================

SYSTEM_PROMPT_REPORT_GENERATION = """Ты — экспертный Цифровой Агроном и специалист по точному земледелию (Precision Agriculture) и дистанционному зондированию Земли (ДЗЗ).

Твоя задача — проанализировать структурированные данные (JSON), полученные в результате анализа спутниковых снимков поля, и предоставить фермеру четкий, действенный и научно обоснованный отчет.

Правила анализа:
1. Интерпретация Индексов: Оценивай значения (например, NDVI) строго с учетом типа культуры (crop_type) и даты (date_of_scan), соотнося их с фазой роста.
2. Анализ неоднородности: Используй стандартное отклонение (std_dev) и результаты зонирования (zonation_results_VRA). Неоднородность требует применения VRA (дифференцированного внесения).
3. Причинно-следственные связи: Сопоставляй данные с погодным контекстом (weather_context) и временной динамикой (temporal_analysis). Например, падение NDVI при отсутствии осадков указывает на водный стресс.
4. Практичность: Рекомендации должны быть конкретными и привязанными к зонам VRA.
5. Ограничения ДЗЗ: Всегда напоминай, что спутниковый анализ указывает на стресс, но точный диагноз (болезнь, вредитель) требует наземного осмотра (скаутинга).

Формат ответа (строго в Markdown):

### Отчет Виртуального Агронома
**Дата анализа:** [Дата снимка] | **Культура:** [Тип культуры] | **Площадь:** [Площадь] га

#### 1. Общая сводка и здоровье поля
[Краткое резюме (2-3 предложения). Общее состояние, средний уровень вегетации и основные тренды.]

#### 2. Анализ неоднородности и проблемных зон
*   **Однородность:** [Оценка однородности. Какая часть поля вызывает опасения.]
*   **Анализ стресс-факторов (Низкие зоны):** [Детальный анализ зон с низкой вегетацией. ГИПОТЕЗЫ о причинах стресса (влага, азот, почва, рельеф).]
*   **Динамика:** [Комментарий к изменениям (temporal_analysis). Особое внимание зонам с резким падением.]

#### 3. Рекомендации и План действий (VRA Стратегия)
1.  **Срочный Скаутинг (Наземный осмотр):**
    *   **Зоны:** [Перечисли ID зон]
    *   **Цель:** [Верификация причин стресса. Что искать.]
2.  **Агротехнические мероприятия:**
    *   [Конкретные действия. Например, стратегия дифференцированного внесения азота или корректировка полива.]
3.  **Мониторинг:**
    *   [Рекомендации по дальнейшему мониторингу.]

---
*Дисклеймер: Данный отчет сгенерирован автоматически на основе спутниковых данных. Точный диагноз требует наземного подтверждения агрономом.*
"""

SYSTEM_PROMPT_CHAT = """Ты — AI Агроном-Консультант. Твоя основная задача — отвечать на вопросы пользователя, опираясь исключительно на предоставленные данные анализа поля (смотри блок [ANALYSIS_CONTEXT] в запросе пользователя).

Правила взаимодействия:
1. Отвечай кратко, точно и профессионально.
2. ВСЕГДА основывай свои ответы на данных из [ANALYSIS_CONTEXT].
3. Если данных в контексте недостаточно для точного ответа (например, для расчета точной дозы удобрений), укажи это и посоветуй, какие дополнительные анализы (например, анализ почвы) необходимы.
4. Категорически запрещено отвечать на вопросы, не связанные с анализом данного поля или агрономией.
5. Говори на русском языке, используй профессиональную терминологию, но будь понятен.
"""


# ============================================================================
# AI Agronomist Service
# ============================================================================

class AIAgronomistService:
    """
    Service for AI-powered agronomic analysis using Google Gemini
    
    Features:
    - Generate comprehensive field analysis reports
    - Provide interactive chat with RAG (Retrieval-Augmented Generation)
    - Robust error handling for API timeouts and failures
    """
    
    def __init__(self):
        """Initialize the AI service with Gemini API"""
        self.model = None
        self.api_key = os.getenv("GEMINI_API_KEY")
        # Allow model configuration via environment variable (supports gemini-1.5-pro, gemini-2.0-flash-exp, etc.)
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")
        self.timeout_seconds = 180  # Increased to 3 minutes for AI operations
        
        if not GEMINI_AVAILABLE:
            logger.error("Google Generative AI library not available")
            return
        
        if not self.api_key:
            logger.warning("GEMINI_API_KEY not set in environment variables. AI features will be disabled.")
            return
        
        try:
            genai.configure(api_key=self.api_key)
            
            # Initialize model with safety settings
            generation_config = {
                "temperature": 0.7,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 8192,
            }
            
            safety_settings = [
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_NONE"
                }
            ]
            
            self.model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config=generation_config,
                safety_settings=safety_settings
            )
            
            logger.info(f"AI Agronomist Service initialized with model: {self.model_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Gemini AI: {e}", exc_info=True)
            self.model = None
    
    
    def is_available(self) -> bool:
        """Check if AI service is available"""
        return self.model is not None and GEMINI_AVAILABLE
    
    
    def _format_context_for_prompt(self, context: AIAnalysisContext) -> str:
        """
        Format AIAnalysisContext into a readable string for LLM
        
        Args:
            context: Structured analysis context
            
        Returns:
            Formatted string representation
        """
        try:
            # Convert to dict and format as JSON for LLM
            context_dict = context.dict(exclude_none=True)
            return json.dumps(context_dict, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to format context: {e}")
            return "{}"
    
    
    async def generate_report(
        self,
        context: AIAnalysisContext
    ) -> AIReportResponse:
        """
        Generate comprehensive agronomic report based on field analysis
        
        Args:
            context: Complete field analysis context
            
        Returns:
            AIReportResponse with generated report in Markdown
            
        Raises:
            Exception: If generation fails
        """
        if not self.is_available():
            raise Exception("AI service not available. Please check GEMINI_API_KEY configuration.")
        
        start_time = time.time()
        
        try:
            # Format context for LLM
            context_json = self._format_context_for_prompt(context)
            
            # Build user prompt
            user_prompt = f"""Проанализируй следующие данные спутникового анализа поля и создай детальный отчет:

```json
{context_json}
```

Следуй строго указанному формату Markdown из системного промпта."""
            
            # Generate response with timeout
            logger.info("Generating AI report...")
            
            # Run with timeout (Gemini SDK calls are synchronous, so we wrap in executor)
            loop = asyncio.get_event_loop()
            try:
                response = await asyncio.wait_for(
                    loop.run_in_executor(None, lambda: self.model.start_chat(history=[]).send_message(
                        f"{SYSTEM_PROMPT_REPORT_GENERATION}\n\n{user_prompt}"
                    )),
                    timeout=self.timeout_seconds
                )
            except asyncio.TimeoutError:
                raise Exception(f"AI report generation timed out after {self.timeout_seconds} seconds")
            
            if not response or not response.text:
                raise Exception("Empty response from Gemini API")
            
            generation_time = time.time() - start_time
            logger.info(f"Report generated successfully in {generation_time:.2f}s")
            
            return AIReportResponse(
                status="success",
                report_markdown=response.text,
                generation_time_seconds=round(generation_time, 2),
                model_used=self.model_name
            )
            
        except Exception as e:
            generation_time = time.time() - start_time
            error_msg = f"Failed to generate AI report: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            # Determine error type
            error_type = "api_error"
            if "timeout" in str(e).lower():
                error_type = "api_timeout"
            elif "quota" in str(e).lower() or "rate" in str(e).lower():
                error_type = "quota_exceeded"
            
            raise Exception(error_msg)
    
    
    async def chat(
        self,
        original_context: AIAnalysisContext,
        chat_history: List[ChatMessage],
        new_question: str
    ) -> AIChatResponse:
        """
        Interactive chat with RAG (context-aware responses)
        
        Args:
            original_context: Original field analysis context
            chat_history: Previous chat messages
            new_question: New user question
            
        Returns:
            AIChatResponse with AI answer
            
        Raises:
            Exception: If chat generation fails
        """
        if not self.is_available():
            raise Exception("AI service not available. Please check GEMINI_API_KEY configuration.")
        
        start_time = time.time()
        
        try:
            # Format context for RAG
            context_json = self._format_context_for_prompt(original_context)
            
            # Build conversation history for Gemini
            gemini_history = []
            
            # Add system context as first user message (with assistant acknowledgment)
            context_intro = f"""[ANALYSIS_CONTEXT]
```json
{context_json}
```

Это контекст анализа поля. Все твои ответы должны основываться на этих данных."""
            
            # Convert chat history to Gemini format
            for msg in chat_history:
                if msg.role == "user":
                    gemini_history.append({
                        "role": "user",
                        "parts": [msg.content]
                    })
                elif msg.role == "assistant":
                    gemini_history.append({
                        "role": "model",
                        "parts": [msg.content]
                    })
            
            # Create chat session
            logger.info(f"Processing chat question: {new_question[:50]}...")
            
            # Build user message with context (only on first message)
            if len(chat_history) == 0:
                full_question = f"{SYSTEM_PROMPT_CHAT}\n\n{context_intro}\n\nВопрос пользователя: {new_question}"
            else:
                full_question = new_question
            
            # Use asyncio timeout wrapper for Gemini API calls
            loop = asyncio.get_event_loop()
            try:
                response = await asyncio.wait_for(
                    loop.run_in_executor(None, lambda: self.model.start_chat(history=gemini_history).send_message(full_question)),
                    timeout=self.timeout_seconds
                )
            except asyncio.TimeoutError:
                raise Exception(f"AI chat response timed out after {self.timeout_seconds} seconds")
            
            if not response or not response.text:
                raise Exception("Empty response from Gemini API")
            
            generation_time = time.time() - start_time
            logger.info(f"Chat response generated in {generation_time:.2f}s")
            
            return AIChatResponse(
                status="success",
                answer=response.text,
                generation_time_seconds=round(generation_time, 2),
                model_used=self.model_name
            )
            
        except Exception as e:
            generation_time = time.time() - start_time
            error_msg = f"Failed to generate chat response: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            raise Exception(error_msg)


# ============================================================================
# Singleton Instance
# ============================================================================

# Global service instance
ai_agronomist_service = AIAgronomistService()

