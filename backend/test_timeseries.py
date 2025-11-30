"""
Тестовый скрипт для проверки анализа временных рядов
"""
import asyncio
import sys
from datetime import datetime
from services.sentinel_service import SentinelService
from api.schemas import Geometry

# Тестовая геометрия (небольшое поле в Молдове)
test_geometry = Geometry(
    type="Polygon",
    coordinates=[[
        [28.8, 47.0],
        [28.81, 47.0],
        [28.81, 47.01],
        [28.8, 47.01],
        [28.8, 47.0]
    ]]
)

async def test_single_date():
    """Тест получения данных за одну дату"""
    print("\n" + "="*60)
    print("TEST: Getting Sentinel-2 data for single date")
    print("="*60)
    
    sentinel = SentinelService()
    
    # Проверяем, что credentials настроены
    if sentinel.use_mock:
        print("❌ ОШИБКА: Sentinel Hub credentials не настроены!")
        print("   Настройте SENTINEL_CLIENT_ID и SENTINEL_CLIENT_SECRET в config.py")
        return False
    
    print(f"✅ Credentials найдены")
    print(f"   Client ID: {sentinel.client_id[:20]}...")
    
    # Тестируем загрузку данных за последний месяц
    date_range = ["2025-09-01", "2025-09-15"]
    
    print(f"\n📅 Запрос данных за период: {date_range[0]} - {date_range[1]}")
    print("⏳ Загрузка... (это может занять 10-30 секунд)")
    
    try:
        data = await sentinel.fetch_data(test_geometry, date_range)
        
        if data:
            print("\n✅ ДАННЫЕ ПОЛУЧЕНЫ УСПЕШНО!")
            print(f"   Каналы: {list(data.keys())}")
            print(f"   Размер изображения: {data['red'].shape}")
            print(f"   Тип данных: {data['red'].dtype}")
            print(f"   Диапазон NIR: {data['nir'].min():.3f} - {data['nir'].max():.3f}")
            print(f"   Диапазон Red: {data['red'].min():.3f} - {data['red'].max():.3f}")
            
            # Вычислим простой NDVI
            import numpy as np
            nir = data['nir']
            red = data['red']
            
            # Избегаем деления на ноль
            denominator = nir + red
            ndvi = np.where(
                denominator != 0,
                (nir - red) / denominator,
                0
            )
            
            # Применяем маску облаков (SCL)
            scl = data['scl']
            invalid_mask = np.isin(scl, [0, 1, 2, 3, 8, 9, 10])
            ndvi[invalid_mask] = np.nan
            
            valid_ndvi = ndvi[~np.isnan(ndvi)]
            
            if len(valid_ndvi) > 0:
                print(f"\n📊 NDVI статистика:")
                print(f"   Среднее: {np.mean(valid_ndvi):.3f}")
                print(f"   Мин: {np.min(valid_ndvi):.3f}")
                print(f"   Макс: {np.max(valid_ndvi):.3f}")
                print(f"   Валидных пикселей: {len(valid_ndvi)} из {ndvi.size}")
            else:
                print("\n⚠️ ВНИМАНИЕ: Нет валидных пикселей (возможно, вся область покрыта облаками)")
                print("   Попробуйте другой период или область")
            
            return True
        else:
            print("\n❌ НЕТ ДАННЫХ для указанного периода")
            print("   Возможные причины:")
            print("   - Высокая облачность")
            print("   - Нет снимков для этой области")
            print("   Попробуйте:")
            print("   - Расширить диапазон дат")
            print("   - Выбрать летний период (июнь-август)")
            return False
            
    except Exception as e:
        print(f"\n❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Главная функция"""
    print("\n" + "="*60)
    print(" "*15 + "TEST SENTINEL-2 API")
    print("="*60)
    
    success = await test_single_date()
    
    print("\n" + "="*60)
    if success:
        print("✅ ТЕСТ ПРОЙДЕН! Анализ динамики должен работать.")
        print("\n📖 Следующие шаги:")
        print("   1. Откройте http://localhost:3000")
        print("   2. Войдите в систему")
        print("   3. Выберите поле на карте")
        print("   4. Нажмите '📊 Открыть анализ динамики'")
        print("   5. Выберите период: сентябрь-октябрь 2025")
        print("   6. Выберите индексы: NDVI + EVI")
        print("   7. Нажмите 'Анализировать динамику'")
    else:
        print("❌ ТЕСТ НЕ ПРОЙДЕН. Проверьте:")
        print("   1. Настроены ли credentials в config.py")
        print("   2. Запущен ли backend сервер")
        print("   3. Установлен ли rasterio (python -c 'import rasterio')")
        print("   4. Есть ли доступ к интернету")
    print("="*60 + "\n")

if __name__ == "__main__":
    asyncio.run(main())

