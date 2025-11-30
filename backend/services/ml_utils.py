"""
ML utilities for time series forecasting
Functions for data preprocessing and feature engineering
"""
import pandas as pd
import numpy as np
from typing import List
import logging

# Import HistoricalDataPoint from forecast_schemas
try:
    from api.forecast_schemas import HistoricalDataPoint
except ImportError:
    logging.warning("Не удалось импортировать HistoricalDataPoint в ml_utils. Используется заглушка Pydantic.")
    from pydantic import BaseModel
    
    class HistoricalDataPoint(BaseModel):
        date: object 
        value: float


logger = logging.getLogger(__name__)


def convert_to_dataframe(data: List[HistoricalDataPoint], index_name: str) -> pd.DataFrame:
    """Конвертирует список Pydantic моделей в Pandas DataFrame."""
    if not data:
        return pd.DataFrame(columns=[index_name])

    # Обработка совместимости Pydantic V1 (.dict()) и V2 (.model_dump())
    if hasattr(data[0], 'model_dump'):
        data_list = [item.model_dump() for item in data]
    else:
        data_list = [item.dict() for item in data]

    df = pd.DataFrame(data_list)
    
    # Конвертируем date объекты в datetime для работы с временным рядом
    df['date'] = pd.to_datetime(df['date'])
    # Устанавливаем индекс и сортируем
    df = df.set_index('date').sort_index()
    df = df.rename(columns={'value': index_name})
    
    # Удаляем дубликаты (если есть), оставляя среднее значение
    if not df.index.is_unique:
        df = df.groupby(df.index).mean()
        
    return df


def create_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Создает временные признаки (циклические) для захвата сезонности.
    """
    df = df.copy()
    df['dayofyear'] = df.index.dayofyear
    
    # Обработка weekofyear для совместимости с разными версиями Pandas
    try:
        df['weekofyear'] = df.index.isocalendar().week.astype(int)
    except AttributeError:
        # Fallback для старых версий Pandas (deprecated)
        df['weekofyear'] = df.index.week
        
    df['month'] = df.index.month

    # Циклические признаки (Sin/Cos Transformation)
    # Используем 365.25 для учета високосных лет.
    df['dayofyear_sin'] = np.sin(2 * np.pi * df['dayofyear']/365.25)
    df['dayofyear_cos'] = np.cos(2 * np.pi * df['dayofyear']/365.25)
    return df

