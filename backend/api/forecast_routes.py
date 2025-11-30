"""
API routes for ML forecasting
Endpoints for time series forecasting of vegetation indices
"""
from fastapi import APIRouter, HTTPException, status, Depends
import logging

# Import schemas and service
try:
    from api.forecast_schemas import ForecastRequest, ForecastResponse
    from services.forecast_service import ForecastService, get_forecast_service
except ImportError:
    logging.warning("Не удалось выполнить импорты в forecast_routes. Используются заглушки.")
    ForecastRequest = object
    ForecastResponse = object
    ForecastService = object
    get_forecast_service = lambda: object()


logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/indices",
    response_model=ForecastResponse,
    status_code=status.HTTP_200_OK,
    summary="Сгенерировать прогноз вегетационного индекса (ML)",
    description="""
    Принимает исторические данные временного ряда вегетационного индекса 
    и возвращает прогноз на заданный горизонт с использованием машинного обучения.
    
    **Требования:**
    - Минимум 10 исторических точек данных
    - Горизонт прогнозирования: 7-90 дней
    - Значения индексов в диапазоне 0-1
    
    **Модель:** Gradient Boosting с циклическими временными признаками для учета сезонности
    """
)
def predict_index(
    request: ForecastRequest,
    service: ForecastService = Depends(get_forecast_service)
):
    """
    Генерирует прогноз вегетационного индекса на основе исторических данных.
    
    Returns:
        ForecastResponse: Прогноз с историческими, интерполированными и прогнозными значениями
    """
    try:
        # Проверка, что зависимости были импортированы корректно (если использовались заглушки)
        if service is object() or ForecastRequest is object:
            raise ImportError("Сервис прогнозирования или схемы запроса не были импортированы корректно.")
             
        response = service.generate_forecast(request)
        logger.info(f"Successfully generated forecast for {request.index_name}")
        return response
        
    except ValueError as e:
        # Ошибки валидации данных или предобработки
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ImportError as e:
        # Ошибки, если зависимости не были корректно настроены на предыдущих шагах
        logger.error(f"Configuration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка конфигурации сервера (Импорты): {e}"
        )
    except Exception as e:
        # Непредвиденные ошибки (например, сбой модели)
        logger.exception(f"An unexpected error occurred during forecast generation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутренняя ошибка сервера при генерации прогноза."
        )

