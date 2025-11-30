"""
Конфигурация вегетационных индексов
Описания и настройки для каждого индекса
"""

VEGETATION_INDICES = {
    "NDVI": {
        "name": "NDVI - Normalized Difference Vegetation Index",
        "description": "Нормализованный разностный вегетационный индекс",
        "formula": "(NIR - RED) / (NIR + RED)",
        "interpretation": {
            "< 0.2": "Почва, вода, бесплодные территории",
            "0.2-0.4": "Низкая растительность, стресс",
            "0.4-0.6": "Средняя растительность",
            "> 0.6": "Здоровая, густая растительность"
        },
        "colormap": [
            (0.0, '#8B4513'),   # Brown
            (0.2, '#D2691E'),
            (0.3, '#FFD700'),
            (0.4, '#FFFF00'),
            (0.5, '#ADFF2F'),
            (0.6, '#7FFF00'),
            (0.7, '#00FF00'),
            (0.8, '#228B22'),
            (1.0, '#006400')    # Dark green
        ],
        "range": (-1, 1)
    },
    "EVI": {
        "name": "EVI - Enhanced Vegetation Index",
        "description": "Улучшенный вегетационный индекс",
        "formula": "2.5 * (NIR - RED) / (NIR + 6*RED - 7.5*BLUE + 1)",
        "interpretation": {
            "< 0.2": "Низкая вегетация",
            "0.2-0.4": "Средняя вегетация",
            "> 0.4": "Высокая вегетация, улучшенная чувствительность"
        },
        "colormap": [
            (0.0, '#8B4513'),
            (0.2, '#FFD700'),
            (0.4, '#ADFF2F'),
            (0.6, '#00FF00'),
            (1.0, '#006400')
        ],
        "range": (-1, 1),
        "note": "Более чувствителен к густой растительности, чем NDVI"
    },
    "PSRI": {
        "name": "PSRI - Plant Senescence Reflectance Index",
        "description": "Индекс старения растений",
        "formula": "(RED - GREEN) / NIR",
        "interpretation": {
            "Низкие значения": "Здоровая зеленая растительность",
            "Высокие значения": "Старение, стресс растений"
        },
        "colormap": [
            (0.0, '#00FF00'),   # Green - healthy
            (0.5, '#FFFF00'),   # Yellow
            (1.0, '#FF0000')    # Red - senescence
        ],
        "range": (-0.2, 0.8),
        "note": "Используется для определения созревания и стресса"
    },
    "NBR": {
        "name": "NBR - Normalized Burn Ratio",
        "description": "Нормализованный индекс гари",
        "formula": "(NIR - SWIR2) / (NIR + SWIR2)",
        "interpretation": {
            "Высокие значения (> 0.1)": "Здоровая растительность",
            "Около 0": "Недавние ожоги",
            "Низкие значения (< 0)": "Сильные повреждения от огня"
        },
        "colormap": [
            (0.0, '#FF0000'),   # Red - burned
            (0.3, '#FFFF00'),
            (0.5, '#00FF00'),   # Green - healthy
            (1.0, '#006400')
        ],
        "range": (-1, 1),
        "note": "Для мониторинга пожаров и восстановления"
    },
    "NDSI": {
        "name": "NDSI - Normalized Difference Snow Index",
        "description": "Нормализованный снежный индекс",
        "formula": "(GREEN - SWIR1) / (GREEN + SWIR1)",
        "interpretation": {
            "> 0.4": "Снег и лед",
            "0.0-0.4": "Возможное присутствие снега",
            "< 0.0": "Отсутствие снега"
        },
        "colormap": [
            (0.0, '#8B4513'),   # Brown - no snow
            (0.3, '#FFFFFF'),   # White - snow
            (1.0, '#E0F8FF')    # Light blue - ice
        ],
        "range": (-1, 1),
        "note": "Для обнаружения снега и льда"
    }
}


def get_index_info(index_name: str) -> dict:
    """Получить информацию об индексе"""
    return VEGETATION_INDICES.get(index_name, {})


def get_all_indices_names() -> list:
    """Получить список всех доступных индексов"""
    return list(VEGETATION_INDICES.keys())

