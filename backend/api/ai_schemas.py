"""
AI Agronomist Data Contracts - Pydantic Models
Structured data schemas for AI-powered field analysis and recommendations
"""
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional
from datetime import datetime


# ============================================================================
# Context Payload Models - Data sent to LLM for analysis
# ============================================================================

class FieldLocation(BaseModel):
    """Geographic location information"""
    region: str = Field(..., description="Region or area name")
    lat: float = Field(..., ge=-90, le=90, description="Latitude")
    lon: float = Field(..., ge=-180, le=180, description="Longitude")


class FieldInfo(BaseModel):
    """Basic field information"""
    name: str = Field(..., min_length=1, max_length=200, description="Field name")
    location: FieldLocation = Field(..., description="Geographic location")
    area_ha: float = Field(..., gt=0, description="Field area in hectares")
    crop_type: Optional[str] = Field(None, description="Crop type (critical for recommendations)")
    sowing_date: Optional[str] = Field(None, description="Sowing date (YYYY-MM-DD)")


class AnalysisInfo(BaseModel):
    """Analysis metadata"""
    date_of_scan: str = Field(..., description="Date of satellite scan (YYYY-MM-DD)")
    satellite: str = Field(default="Sentinel-2", description="Satellite source")


class WeatherContext(BaseModel):
    """Weather context for field analysis"""
    precipitation_last_14_days_mm: Optional[float] = Field(None, description="Precipitation in last 14 days (mm)")
    avg_temp_last_14_days_celsius: Optional[float] = Field(None, description="Average temperature (°C)")
    forecast_summary: Optional[str] = Field(None, description="Weather forecast summary")


class IndexStats(BaseModel):
    """Statistics for a vegetation index"""
    mean: float = Field(..., description="Mean value")
    std_dev: float = Field(..., description="Standard deviation (high = heterogeneous field)")
    min: Optional[float] = Field(None, description="Minimum value")
    max: Optional[float] = Field(None, description="Maximum value")


class IndicesSummary(BaseModel):
    """Summary of all calculated vegetation indices"""
    NDVI: IndexStats = Field(..., description="NDVI statistics")
    EVI: Optional[IndexStats] = Field(None, description="EVI statistics")
    PSRI: Optional[IndexStats] = Field(None, description="PSRI statistics")
    NBR: Optional[IndexStats] = Field(None, description="NBR statistics")
    NDSI: Optional[IndexStats] = Field(None, description="NDSI statistics")


class VRAZone(BaseModel):
    """Variable Rate Application (VRA) zone details"""
    id: int = Field(..., description="Zone ID")
    label: str = Field(..., description="Zone label (e.g., 'Critical stress', 'High vegetation')")
    area_ha: float = Field(..., gt=0, description="Zone area in hectares")
    percentage: float = Field(..., ge=0, le=100, description="Percentage of total field area")
    mean_NDVI: float = Field(..., ge=-1, le=1, description="Mean NDVI value in zone")


class ZonationResults(BaseModel):
    """VRA zonation results from clustering"""
    zones: List[VRAZone] = Field(..., min_length=1, max_length=10, description="Management zones (1-10, typically 3-5)")
    
    @validator('zones')
    def validate_zones(cls, v):
        if len(v) < 1:
            raise ValueError('Must have at least 1 zone')
        if len(v) > 10:
            raise ValueError('Too many zones (max 10)')
        return v


class TemporalAnalysis(BaseModel):
    """Temporal comparison with previous scans"""
    mean_NDVI_change: Optional[float] = Field(None, description="NDVI change from previous scan (negative = degradation)")
    significant_drop_area_ha: Optional[float] = Field(None, description="Area with significant NDVI drop (>15%)")


class AIAnalysisContext(BaseModel):
    """
    Complete context payload for AI Agronomist analysis
    This is the primary data structure sent to the LLM for generating reports and chat responses
    """
    field_info: FieldInfo = Field(..., description="Field metadata")
    analysis_info: AnalysisInfo = Field(..., description="Analysis metadata")
    weather_context: Optional[WeatherContext] = Field(None, description="Weather data")
    indices_summary: IndicesSummary = Field(..., description="Vegetation indices statistics")
    zonation_results_VRA: Optional[ZonationResults] = Field(None, description="VRA management zones")
    temporal_analysis: Optional[TemporalAnalysis] = Field(None, description="Temporal comparison")
    
    class Config:
        json_schema_extra = {
            "example": {
                "field_info": {
                    "name": "Поле Озимые-3",
                    "location": {
                        "region": "Калужская область",
                        "lat": 55.1,
                        "lon": 36.6
                    },
                    "area_ha": 150.5,
                    "crop_type": "Озимая пшеница",
                    "sowing_date": "2025-09-01"
                },
                "analysis_info": {
                    "date_of_scan": "2025-10-18",
                    "satellite": "Sentinel-2"
                },
                "weather_context": {
                    "precipitation_last_14_days_mm": 5.0,
                    "avg_temp_last_14_days_celsius": 10.5,
                    "forecast_summary": "Отсутствие осадков, риск засухи"
                },
                "indices_summary": {
                    "NDVI": {
                        "mean": 0.55,
                        "std_dev": 0.20,
                        "min": 0.15,
                        "max": 0.85
                    }
                },
                "zonation_results_VRA": {
                    "zones": [
                        {
                            "id": 1,
                            "label": "Критический стресс",
                            "area_ha": 20.0,
                            "percentage": 13.3,
                            "mean_NDVI": 0.25
                        },
                        {
                            "id": 2,
                            "label": "Слабая вегетация",
                            "area_ha": 35.0,
                            "percentage": 23.3,
                            "mean_NDVI": 0.45
                        },
                        {
                            "id": 3,
                            "label": "Умеренная вегетация",
                            "area_ha": 60.0,
                            "percentage": 40.0,
                            "mean_NDVI": 0.62
                        },
                        {
                            "id": 4,
                            "label": "Высокая вегетация",
                            "area_ha": 25.0,
                            "percentage": 16.6,
                            "mean_NDVI": 0.75
                        },
                        {
                            "id": 5,
                            "label": "Очень высокая вегетация",
                            "area_ha": 10.5,
                            "percentage": 7.0,
                            "mean_NDVI": 0.85
                        }
                    ]
                },
                "temporal_analysis": {
                    "mean_NDVI_change": -0.05,
                    "significant_drop_area_ha": 15.0
                }
            }
        }


# ============================================================================
# API Request/Response Models
# ============================================================================

class AIReportRequest(BaseModel):
    """Request for generating AI agronomist report"""
    context: AIAnalysisContext = Field(..., description="Complete field analysis context")
    
    class Config:
        json_schema_extra = {
            "example": {
                "context": {
                    "field_info": {
                        "name": "Поле Озимые-3",
                        "location": {"region": "Калужская область", "lat": 55.1, "lon": 36.6},
                        "area_ha": 150.5,
                        "crop_type": "Озимая пшеница",
                        "sowing_date": "2025-09-01"
                    },
                    "analysis_info": {
                        "date_of_scan": "2025-10-18",
                        "satellite": "Sentinel-2"
                    },
                    "indices_summary": {
                        "NDVI": {"mean": 0.55, "std_dev": 0.20}
                    }
                }
            }
        }


class AIReportResponse(BaseModel):
    """Response containing AI-generated agronomist report"""
    status: str = Field(..., description="Response status")
    report_markdown: str = Field(..., description="AI-generated report in Markdown format")
    generation_time_seconds: float = Field(..., description="Time taken to generate report")
    llm_model: str = Field(..., description="LLM model identifier", alias="model_used")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "report_markdown": "### Отчет Виртуального Агронома\n...",
                "generation_time_seconds": 3.2,
                "model_used": "gemini-2.5-pro"
            }
        }
        populate_by_name = True  # Позволяет использовать и llm_model, и model_used


class ChatMessage(BaseModel):
    """Single chat message"""
    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., min_length=1, description="Message content")
    timestamp: Optional[datetime] = Field(default_factory=datetime.now, description="Message timestamp")
    
    @validator('role')
    def validate_role(cls, v):
        if v not in ['user', 'assistant']:
            raise ValueError("Role must be 'user' or 'assistant'")
        return v


class AIChatRequest(BaseModel):
    """Request for AI chat with RAG context"""
    original_context: AIAnalysisContext = Field(..., description="Original field analysis context")
    chat_history: List[ChatMessage] = Field(default_factory=list, description="Previous chat messages")
    new_question: str = Field(..., min_length=1, max_length=1000, description="New user question")
    
    class Config:
        json_schema_extra = {
            "example": {
                "original_context": {
                    "field_info": {"name": "Поле Озимые-3", "area_ha": 150.5},
                    "indices_summary": {"NDVI": {"mean": 0.55, "std_dev": 0.20}}
                },
                "chat_history": [
                    {"role": "assistant", "content": "### Отчет Виртуального Агронома\n..."}
                ],
                "new_question": "Какие зоны требуют срочного внимания?"
            }
        }


class AIChatResponse(BaseModel):
    """Response from AI chat"""
    status: str = Field(..., description="Response status")
    answer: str = Field(..., description="AI assistant answer")
    generation_time_seconds: float = Field(..., description="Time taken to generate answer")
    llm_model: str = Field(..., description="LLM model identifier", alias="model_used")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "answer": "Зоны 1 и 2 требуют срочного внимания...",
                "generation_time_seconds": 1.5,
                "model_used": "gemini-1.5-pro"
            }
        }
        populate_by_name = True  # Позволяет использовать и llm_model, и model_used


# ============================================================================
# Error Response Model
# ============================================================================

class AIErrorResponse(BaseModel):
    """Error response from AI service"""
    status: str = Field(default="error", description="Error status")
    error_type: str = Field(..., description="Error type (timeout, validation, api_error, etc.)")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[str] = Field(None, description="Additional error details")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "error",
                "error_type": "api_timeout",
                "message": "Превышено время ожидания ответа от AI сервиса",
                "details": "Gemini API timeout after 30 seconds"
            }
        }

