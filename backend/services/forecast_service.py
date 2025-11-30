"""
ML Forecast Service
Service for time series forecasting of vegetation indices using Gradient Boosting
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
import logging

# Import schemas and utilities
try:
    from api.forecast_schemas import ForecastRequest, ForecastResponse, ForecastDataPoint
    from services.ml_utils import convert_to_dataframe, create_features
except ImportError:
    logging.warning("Не удалось выполнить импорты в ForecastService. Используются заглушки.")
    # Определяем заглушки, чтобы избежать ошибок импорта
    ForecastRequest = object
    ForecastResponse = object
    ForecastDataPoint = object
    convert_to_dataframe = lambda x, y: pd.DataFrame()
    create_features = lambda x: pd.DataFrame()


logger = logging.getLogger(__name__)


class ForecastService:
    """Сервис для прогнозирования временных рядов вегетационных индексов."""
    
    def __init__(self):
        # Признаки, используемые моделью
        self.FEATURES = ['dayofyear_sin', 'dayofyear_cos', 'weekofyear', 'month']
        # Параметры модели (оптимизированы для баланса скорости и точности)
        self.MODEL_PARAMS = {
            'n_estimators': 400,
            'learning_rate': 0.05,
            'max_depth': 5,
            'random_state': 42
        }

    def _initialize_model(self):
        """Инициализирует модель Gradient Boosting."""
        return GradientBoostingRegressor(**self.MODEL_PARAMS)

    def _preprocess_and_label(self, df_raw: pd.DataFrame, index_name: str) -> pd.DataFrame:
        """
        Интерполирует временной ряд и маркирует точки как Historical или Interpolated.
        """
        # Ресемплинг до ежедневной частоты
        df_daily = df_raw[[index_name]].resample('D').mean()

        # Маркировка типа данных
        df_daily['Type'] = np.where(df_daily[index_name].notna(), 'Historical', 'Interpolated')
            
        # Полиномиальная интерполяция (order=2) с отказоустойчивостью.
        try:
            # Проверяем, достаточно ли уникальных точек (> order+1) для полиномиальной интерполяции
            if len(df_daily[index_name].dropna()) > 3:
                df_interpolated = df_daily[index_name].interpolate(method='polynomial', order=2)
            else:
                raise ValueError("Недостаточно данных для полиномиальной интерполяции.")
        except Exception as e:
            logger.warning(f"Polynomial interpolation failed ({e}). Falling back to linear interpolation.")
            df_interpolated = df_daily[index_name].interpolate(method='linear')
        
        # Заполнение оставшихся NaN на краях (если интерполяция не покрыла начало/конец)
        df_interpolated = df_interpolated.ffill().bfill()

        # Объединяем интерполированные значения и метки типа
        df_processed = pd.DataFrame({
            index_name: df_interpolated,
            'Type': df_daily['Type']
        })

        # Ограничиваем значения в валидном диапазоне (0-1)
        df_processed[index_name] = df_processed[index_name].clip(lower=0, upper=1)

        return df_processed

    def generate_forecast(self, request: ForecastRequest) -> ForecastResponse:
        """
        Основная функция для генерации прогноза.
        """
        logger.info(f"Generating forecast for {request.index_name}. Horizon: {request.forecast_horizon_days} days.")
        
        index_name = request.index_name

        # 1. Подготовка данных
        try:
            df_raw = convert_to_dataframe(request.historical_data, index_name)
            df_processed = self._preprocess_and_label(df_raw, index_name)
            df_featured = create_features(df_processed)
        except Exception as e:
            logger.error(f"Data preprocessing failed: {e}")
            # Выбрасываем ValueError для обработки на уровне API (HTTP 400)
            raise ValueError(f"Ошибка предобработки данных: {e}")

        X_train = df_featured[self.FEATURES]
        y_train = df_featured[index_name]

        # 2. Обучение модели
        model = self._initialize_model()
        model.fit(X_train, y_train)

        # 3. Создание DataFrame для будущих дат
        last_date = df_processed.index.max()
        future_dates = pd.date_range(
            start=last_date + pd.Timedelta(days=1),
            periods=request.forecast_horizon_days,
            freq='D'
        )
        
        df_future = pd.DataFrame(index=future_dates)
        df_future_featured = create_features(df_future)
        X_future = df_future_featured[self.FEATURES]

        # 4. Прогнозирование
        predictions = model.predict(X_future)
        
        # 5. Объединение результатов
        df_future_results = pd.DataFrame({index_name: predictions}, index=future_dates)
        df_future_results['Type'] = 'Forecast'
        
        df_combined = pd.concat([
            df_processed[[index_name, 'Type']],
            df_future_results
        ])
        
        # Финальное ограничение диапазона
        df_combined[index_name] = df_combined[index_name].clip(lower=0, upper=1)

        # 6. Конвертация в формат ответа API
        # Проверка корректности импортов перед использованием (если использовались заглушки)
        if ForecastDataPoint is object or ForecastResponse is object:
            raise ImportError("Схемы данных (ForecastDataPoint/Response) не были импортированы корректно.")

        forecast_points = []
        for index, row in df_combined.iterrows():
            forecast_points.append(
                ForecastDataPoint(
                    date=index.date(),  # Конвертируем обратно в date объект
                    value=round(row[index_name], 4),  # Округление до 4 знаков
                    type=row['Type']
                )
            )

        return ForecastResponse(
            index_name=index_name,
            forecast=forecast_points,
            metadata={"model_type": "GradientBoostingRegressor (Seasonal Features)"}
        )


# Функция для Dependency Injection в FastAPI
def get_forecast_service() -> ForecastService:
    """Возвращает экземпляр ForecastService для использования в FastAPI."""
    return ForecastService()

