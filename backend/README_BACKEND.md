# Backend - AgroSky Insight

## Быстрый запуск (локально)

### 1. Установите зависимости

```bash
# Windows PowerShell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Запустите сервер

```bash
python main.py
```

Сервер запустится на http://localhost:8000

### 3. Проверьте работу

Откройте в браузере:
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

## Конфигурация

По умолчанию backend работает в **MOCK режиме** (генерирует синтетические данные).

Для использования реальных данных Sentinel-2:

1. Зарегистрируйтесь на https://apps.sentinel-hub.com/
2. Создайте `config.py` на основе `config.example.py`
3. Заполните credentials

## Структура

```
backend/
├── main.py              # Точка входа FastAPI
├── api/
│   ├── routes.py        # API endpoints
│   └── schemas.py       # Pydantic models
├── services/
│   ├── geo_processor.py # NDVI расчет
│   └── sentinel_service.py # Получение данных
└── tests/               # Unit тесты
```

## Тестирование

```bash
pytest tests/ -v
```

## API Endpoints

### POST /api/v1/analyze

Анализ поля

**Request:**
```json
{
  "geometry": {
    "type": "Polygon",
    "coordinates": [[[lon, lat], ...]]
  },
  "date_range": ["2023-10-01", "2023-10-15"]
}
```

**Response:**
```json
{
  "status": "success",
  "image_url": "/results/uuid/image.png",
  "stats": {...}
}
```

Полная документация: http://localhost:8000/docs


