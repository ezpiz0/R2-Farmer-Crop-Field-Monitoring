/**
 * AI Agronomist Data Contracts - TypeScript Interfaces
 * Type definitions for AI-powered field analysis and recommendations
 * 
 * These interfaces mirror the Pydantic models in backend/api/ai_schemas.py
 */

// ============================================================================
// Context Payload Interfaces - Data sent to LLM for analysis
// ============================================================================

export interface FieldLocation {
  region: string;
  lat: number;
  lon: number;
}

export interface FieldInfo {
  name: string;
  location: FieldLocation;
  area_ha: number;
  crop_type?: string | null;
  sowing_date?: string | null;
}

export interface AnalysisInfo {
  date_of_scan: string;
  satellite: string;
}

export interface WeatherContext {
  precipitation_last_14_days_mm?: number | null;
  avg_temp_last_14_days_celsius?: number | null;
  forecast_summary?: string | null;
}

export interface IndexStats {
  mean: number;
  std_dev: number;
  min?: number | null;
  max?: number | null;
}

export interface IndicesSummary {
  NDVI: IndexStats;
  EVI?: IndexStats | null;
  PSRI?: IndexStats | null;
  NBR?: IndexStats | null;
  NDSI?: IndexStats | null;
}

export interface VRAZone {
  id: number;
  label: string;
  area_ha: number;
  percentage: number;
  mean_NDVI: number;
}

export interface ZonationResults {
  zones: VRAZone[];
}

export interface TemporalAnalysis {
  mean_NDVI_change?: number | null;
  significant_drop_area_ha?: number | null;
}

export interface AIAnalysisContext {
  field_info: FieldInfo;
  analysis_info: AnalysisInfo;
  weather_context?: WeatherContext | null;
  indices_summary: IndicesSummary;
  zonation_results_VRA?: ZonationResults | null;
  temporal_analysis?: TemporalAnalysis | null;
}

// ============================================================================
// API Request/Response Interfaces
// ============================================================================

export interface AIReportRequest {
  context: AIAnalysisContext;
}

export interface AIReportResponse {
  status: string;
  report_markdown: string;
  generation_time_seconds: number;
  model_used: string;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
}

export interface AIChatRequest {
  original_context: AIAnalysisContext;
  chat_history: ChatMessage[];
  new_question: string;
}

export interface AIChatResponse {
  status: string;
  answer: string;
  generation_time_seconds: number;
  model_used: string;
}

export interface AIErrorResponse {
  status: string;
  error_type: string;
  message: string;
  details?: string | null;
}

// ============================================================================
// Helper Types
// ============================================================================

export type AIStatus = 'idle' | 'loading' | 'success' | 'error';

export interface AIState {
  status: AIStatus;
  error: AIErrorResponse | null;
  reportMarkdown: string | null;
  chatHistory: ChatMessage[];
  isGeneratingReport: boolean;
  isChatLoading: boolean;
}

