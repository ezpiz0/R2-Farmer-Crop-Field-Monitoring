"""
Pydantic schemas for ML Forecast API
Schemas for time series forecasting of vegetation indices
"""
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional
from datetime import date
import logging

logger = logging.getLogger(__name__)


class HistoricalDataPoint(BaseModel):
    """Отдельная точка данных из истории спутниковых наблюдений."""
    date: date
    value: float = Field(..., ge=0, le=1, description="Значение индекса (0-1)")


class ForecastRequest(BaseModel):
    """Запрос на генерацию прогноза."""
    index_name: str = Field(..., description="Название индекса (например, NDVI, EVI)")
    historical_data: List[HistoricalDataPoint]
    forecast_horizon_days: int = Field(30, ge=7, le=90, description="Горизонт прогнозирования в днях (7-90)")

    @validator('historical_data')
    def check_data_sufficiency(cls, v):
        # Требуется минимум 10 наблюдений для стабильной интерполяции и обучения
        if len(v) < 10:
            raise ValueError("Недостаточно исторических данных. Требуется минимум 10 наблюдений.")
        return v

    @validator('historical_data')
    def check_dates_are_unique(cls, v):
        dates = [dp.date for dp in v]
        if len(dates) != len(set(dates)):
            # Предупреждаем и обрабатываем дубликаты на этапе предобработки.
            logger.warning("Обнаружены дубликаты дат в запросе. Данные будут агрегированы (среднее).")
        return v


class ForecastDataPoint(BaseModel):
    """Точка данных в прогнозе."""
    date: date
    value: float
    # Тип данных: Historical (реальное), Interpolated (заполнение пропуска), Forecast (прогноз)
    type: str = Field(..., description="Тип данных: Historical, Interpolated, или Forecast")


class ForecastResponse(BaseModel):
    """Ответ API с результатами прогноза."""
    index_name: str
    forecast: List[ForecastDataPoint]
    metadata: Dict[str, Optional[str]] = Field(default_factory=dict)
    
    class Config:
        json_schema_extra = {
            "example": {
                "index_name": "NDVI",
                "forecast": [
                    {
                        "date": "2025-01-01",
                        "value": 0.75,
                        "type": "Historical"
                    },
                    {
                        "date": "2025-01-15",
                        "value": 0.78,
                        "type": "Forecast"
                    }
                ],
                "metadata": {
                    "model_type": "GradientBoostingRegressor (Seasonal Features)"
                }
            }
        }

