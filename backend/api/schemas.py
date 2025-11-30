"""
Pydantic schemas for API request/response validation
"""
from pydantic import BaseModel, Field, validator
from typing import List, Tuple, Dict, Optional
from datetime import date, datetime


class Geometry(BaseModel):
    """GeoJSON geometry (Polygon)"""
    type: str = Field(..., description="Geometry type (must be 'Polygon')")
    coordinates: List[List[List[float]]] = Field(..., description="Polygon coordinates [[[lon, lat], ...]]")
    
    @validator('type')
    def validate_type(cls, v):
        if v != 'Polygon':
            raise ValueError('Only Polygon geometry is supported')
        return v
    
    @validator('coordinates')
    def validate_coordinates(cls, v):
        if not v or not v[0] or len(v[0]) < 3:
            raise ValueError('Polygon must have at least 3 points')
        return v


class AnalysisRequest(BaseModel):
    """Request for field analysis"""
    geometry: Geometry = Field(..., description="Field boundary as GeoJSON Polygon")
    date_range: List[str] = Field(
        default_factory=lambda: [
            (date.today().replace(day=1).isoformat()),
            date.today().isoformat()
        ],
        description="Date range for imagery [start_date, end_date] in YYYY-MM-DD format"
    )
    indices: List[str] = Field(
        default=["NDVI"],
        description="Vegetation indices to calculate. NDVI is always included. Options: NDVI, EVI, PSRI, NBR, NDSI"
    )
    
    @validator('date_range')
    def validate_date_range(cls, v):
        if len(v) != 2:
            raise ValueError('date_range must contain exactly 2 dates')
        return v
    
    @validator('indices')
    def validate_indices(cls, v):
        valid_indices = {'NDVI', 'EVI', 'PSRI', 'NBR', 'NDSI'}
        # NDVI всегда включен
        if 'NDVI' not in v:
            v = ['NDVI'] + v
        # Проверяем валидность
        for idx in v:
            if idx not in valid_indices:
                raise ValueError(f'Invalid index: {idx}. Valid options: {valid_indices}')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [37.6173, 55.7558],
                            [37.6273, 55.7558],
                            [37.6273, 55.7458],
                            [37.6173, 55.7458],
                            [37.6173, 55.7558]
                        ]
                    ]
                },
                "date_range": ["2023-10-01", "2023-10-15"]
            }
        }


class FieldStats(BaseModel):
    """Statistics for analyzed field"""
    area_ha: float = Field(..., description="Field area in hectares")
    mean_ndvi: float = Field(..., description="Mean NDVI value")
    capture_date: str = Field(..., description="Date of satellite capture")
    cloud_coverage_percent: float = Field(..., description="Percentage of cloud coverage")
    zones_percent: Dict[str, float] = Field(
        ..., 
        description="Distribution of NDVI zones"
    )
    valid_pixels_percent: float = Field(..., description="Percentage of valid (non-cloudy) pixels")
    indices_stats: Optional[Dict[str, Dict[str, float]]] = Field(
        default=None,
        description="Statistics for additional indices (mean, min, max)"
    )


class AnalysisResponse(BaseModel):
    """Response from field analysis"""
    status: str = Field(..., description="Analysis status")
    image_url: str = Field(..., description="URL to NDVI visualization image")
    bounds: List[List[float]] = Field(..., description="Bounds of the analyzed area [[minLat, minLon], [maxLat, maxLon]]")
    stats: FieldStats = Field(..., description="Field statistics")
    additional_indices: Optional[Dict[str, str]] = Field(
        default=None,
        description="URLs to additional indices visualizations"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "image_url": "/results/uuid-here/ndvi_visualization.png",
                "bounds": [[55.7458, 37.6173], [55.7558, 37.6273]],
                "stats": {
                    "area_ha": 120.5,
                    "mean_ndvi": 0.65,
                    "capture_date": "2023-10-14",
                    "cloud_coverage_percent": 5.2,
                    "zones_percent": {
                        "low (<0.3)": 10.0,
                        "medium (0.3-0.6)": 30.0,
                        "high (>0.6)": 60.0
                    },
                    "valid_pixels_percent": 94.8
                }
            }
        }


class TimeSeriesRequest(BaseModel):
    """Request for time series analysis"""
    geometry: Geometry = Field(..., description="Field boundary as GeoJSON Polygon")
    start_date: str = Field(..., description="Start date in YYYY-MM-DD format")
    end_date: str = Field(..., description="End date in YYYY-MM-DD format")
    index_type: str = Field(default="NDVI", description="Vegetation index type (NDVI, EVI, PSRI, NBR, NDSI)")
    
    @validator('index_type')
    def validate_index_type(cls, v):
        valid_indices = {'NDVI', 'EVI', 'PSRI', 'NBR', 'NDSI'}
        if v not in valid_indices:
            raise ValueError(f'Invalid index type: {v}. Valid options: {valid_indices}')
        return v
    
    @validator('end_date')
    def validate_dates(cls, v, values):
        if 'start_date' in values:
            start = datetime.fromisoformat(values['start_date'])
            end = datetime.fromisoformat(v)
            if end < start:
                raise ValueError('end_date must be after start_date')
        return v


class TimeSeriesResponse(BaseModel):
    """Response for time series analysis"""
    index_type: str = Field(..., description="Vegetation index type")
    dates: List[str] = Field(..., description="List of dates")
    values: List[float] = Field(..., description="Index values for each date")
    geometry: Geometry = Field(..., description="Analyzed geometry")
    
    class Config:
        json_schema_extra = {
            "example": {
                "index_type": "NDVI",
                "dates": ["2024-10-01", "2024-10-05", "2024-10-10", "2024-10-15"],
                "values": [0.65, 0.68, 0.72, 0.70],
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [37.6173, 55.7558],
                            [37.6273, 55.7558],
                            [37.6273, 55.7458],
                            [37.6173, 55.7458],
                            [37.6173, 55.7558]
                        ]
                    ]
                }
            }
        }


# ============================================================================
# Field and Dashboard Schemas
# ============================================================================

class FieldCreate(BaseModel):
    """Request schema for creating a new field"""
    name: str = Field(..., min_length=1, max_length=200, description="Field name")
    geometry: Geometry = Field(..., description="Field boundary as GeoJSON Polygon")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Мое первое поле",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [37.6173, 55.7558],
                            [37.6273, 55.7558],
                            [37.6273, 55.7458],
                            [37.6173, 55.7458],
                            [37.6173, 55.7558]
                        ]
                    ]
                }
            }
        }


class FieldResponse(BaseModel):
    """Response schema for field data"""
    id: int
    user_id: int
    name: str
    geometry_geojson: Dict
    created_at: datetime
    
    class Config:
        from_attributes = True


class DashboardItemCreate(BaseModel):
    """Request schema for creating a dashboard item"""
    field_id: int = Field(..., description="ID of the saved field")
    item_type: str = Field(
        ..., 
        description="Widget type: time_series_chart, latest_ndvi_map, field_stats"
    )
    start_date: Optional[str] = Field(None, description="Start date for time series (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="End date for time series (YYYY-MM-DD)")
    index_type: Optional[str] = Field(None, description="Vegetation index type (NDVI, EVI, etc.)")
    
    @validator('item_type')
    def validate_item_type(cls, v):
        valid_types = {'time_series_chart', 'latest_ndvi_map', 'field_stats'}
        if v not in valid_types:
            raise ValueError(f'Invalid item_type. Valid options: {valid_types}')
        return v
    
    @validator('index_type')
    def validate_index_type(cls, v):
        if v is None:
            return v
        valid_indices = {'NDVI', 'EVI', 'PSRI', 'NBR', 'NDSI'}
        if v not in valid_indices:
            raise ValueError(f'Invalid index type. Valid options: {valid_indices}')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "field_id": 1,
                "item_type": "time_series_chart",
                "start_date": "2024-01-01",
                "end_date": "2024-03-31",
                "index_type": "NDVI"
            }
        }


class DashboardItemResponse(BaseModel):
    """Response schema for dashboard item with field data"""
    id: int
    user_id: int
    field_id: int
    field_name: str
    field_geometry: Dict
    item_type: str
    start_date: Optional[str]
    end_date: Optional[str]
    index_type: Optional[str]
    display_order: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# Zone Analysis Schemas
# ============================================================================

class ZoneAnalysisRequest(BaseModel):
    """Request schema for creating management zones"""
    field_id: Optional[int] = Field(None, description="ID of saved field (if using saved field)")
    geometry: Optional[Geometry] = Field(None, description="Field boundary (if not using saved field)")
    analysis_id: Optional[str] = Field(None, description="ID of previous NDVI analysis")
    ndvi_data_url: Optional[str] = Field(None, description="Path to NDVI GeoTIFF file")
    num_zones: int = Field(4, ge=3, le=5, description="Number of management zones (3-5)")
    
    @validator('num_zones')
    def validate_num_zones(cls, v):
        if v < 3 or v > 5:
            raise ValueError('num_zones must be between 3 and 5')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "field_id": 1,
                "analysis_id": "uuid-of-previous-analysis",
                "num_zones": 4
            }
        }


class ZoneStatistics(BaseModel):
    """Statistics for a single zone"""
    mean_ndvi: float = Field(..., description="Mean NDVI value in zone")
    min_ndvi: float = Field(..., description="Minimum NDVI value")
    max_ndvi: float = Field(..., description="Maximum NDVI value")
    std_ndvi: float = Field(..., description="Standard deviation of NDVI")
    pixel_count: int = Field(..., description="Number of pixels in zone")


class ZoneAnalysisResponse(BaseModel):
    """Response schema for zone analysis"""
    status: str = Field(..., description="Analysis status")
    message: str = Field(..., description="Status message")
    num_zones: int = Field(..., description="Number of zones created")
    zone_geojson: Dict = Field(..., description="GeoJSON FeatureCollection of zones")
    zone_statistics: Dict[int, ZoneStatistics] = Field(..., description="Statistics for each zone")
    download_links: Dict[str, str] = Field(..., description="Download links for zone files")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "message": "Field divided into 4 management zones",
                "num_zones": 4,
                "zone_geojson": {
                    "type": "FeatureCollection",
                    "features": [
                        {
                            "type": "Feature",
                            "properties": {
                                "zone_id": 1,
                                "mean_ndvi": 0.25,
                                "zone_label": "Очень слабая"
                            },
                            "geometry": {"type": "Polygon", "coordinates": []}
                        }
                    ]
                },
                "zone_statistics": {
                    "1": {
                        "mean_ndvi": 0.25,
                        "min_ndvi": 0.1,
                        "max_ndvi": 0.35,
                        "std_ndvi": 0.05,
                        "pixel_count": 1500
                    }
                },
                "download_links": {
                    "geojson": "/api/v1/downloads/zones_uuid.geojson",
                    "shapefile": "/api/v1/downloads/zones_uuid.zip"
                }
            }
        }



