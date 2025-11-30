#!/usr/bin/env python3
"""
Тестовый скрипт для проверки Sentinel Hub API
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

# ВАЖНО: Загрузить credentials ДО импорта SentinelService
try:
    from config import SENTINEL_CLIENT_ID, SENTINEL_CLIENT_SECRET
    if SENTINEL_CLIENT_ID:
        os.environ['SENTINEL_CLIENT_ID'] = SENTINEL_CLIENT_ID
    if SENTINEL_CLIENT_SECRET:
        os.environ['SENTINEL_CLIENT_SECRET'] = SENTINEL_CLIENT_SECRET
    print(f"Loaded credentials from config.py: ID={SENTINEL_CLIENT_ID[:20]}..." if SENTINEL_CLIENT_ID else "No credentials")
except Exception as e:
    print(f"Failed to load config.py: {e}")

import asyncio
from services.sentinel_service import SentinelService
from api.schemas import Geometry

async def test_sentinel():
    print("=" * 60)
    print("ТЕСТ SENTINEL HUB API")
    print("=" * 60)
    
    # Инициализируем сервис
    service = SentinelService()
    
    print(f"\n1. Proverka credentials:")
    if service.client_id:
        print(f"   Client ID: {service.client_id[:20]}...")
    else:
        print("   ERROR: Client ID ne nayden")
    print(f"   MOCK rezhim: {'DA' if service.use_mock else 'NET'}")
    
    if service.use_mock:
        print("\nERROR: Sistema v MOCK rezhime!")
        print("   Prover'te backend/config.py")
        return
    
    print("\n2. Тестовый запрос к Sentinel Hub API")
    print("   Область: Обнинск (тестовое поле)")
    
    # Тестовая геометрия (маленький полигон в Обнинске)
    test_geometry = Geometry(
        type="Polygon",
        coordinates=[[
            [36.6, 55.1],
            [36.61, 55.1],
            [36.61, 55.11],
            [36.6, 55.11],
            [36.6, 55.1]
        ]]
    )
    
    # Тестовые даты (август 2024)
    date_range = ["2024-08-01", "2024-08-15"]
    
    print(f"   Даты: {date_range[0]} - {date_range[1]}")
    print("\n   Отправка запроса...")
    
    try:
        data = await service.fetch_data(test_geometry, date_range)
        
        if data:
            print("\nUSPEH! Dannye polucheny:")
            for band_name, band_data in data.items():
                print(f"   - {band_name}: shape={band_data.shape}, dtype={band_data.dtype}")
        else:
            print("\nOSHIBKA: Dannye ne polucheny (vernulsya None)")
            
    except Exception as e:
        print(f"\nOSHIBKA: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    asyncio.run(test_sentinel())

