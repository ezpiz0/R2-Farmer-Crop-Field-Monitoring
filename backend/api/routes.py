"""
API Routes for field analysis
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional, List
import uuid
from pathlib import Path
import logging
import numpy as np

from api.schemas import (
    AnalysisRequest, AnalysisResponse, 
    TimeSeriesRequest, TimeSeriesResponse,
    FieldCreate, FieldResponse,
    DashboardItemCreate, DashboardItemResponse,
    ZoneAnalysisRequest, ZoneAnalysisResponse
)
from api.ai_schemas import (
    AIReportRequest, AIReportResponse,
    AIChatRequest, AIChatResponse,
    AIErrorResponse
)
from services.geo_processor import GeoProcessor
from services.sentinel_service import SentinelService
from services.zone_analyzer import zone_analyzer
from services.ai_agronomist import ai_agronomist_service
from database import get_db
from database.models import User, Field, DashboardItem
from auth.utils import get_current_user

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize services
sentinel_service = SentinelService()
geo_processor = GeoProcessor()


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_field(request: AnalysisRequest):
    """
    Analyze agricultural field using Sentinel-2 data
    
    Args:
        request: Analysis request containing geometry, date range, and indices to calculate
        
    Returns:
        Analysis results with NDVI statistics and visualizations for all requested indices
    """
    try:
        logger.info(f"Starting analysis for geometry: {request.geometry.type}")
        logger.info(f"Requested indices: {request.indices}")
        
        # Generate unique ID for this analysis
        analysis_id = str(uuid.uuid4())
        results_dir = Path("results") / analysis_id
        results_dir.mkdir(parents=True, exist_ok=True)
        
        # Step 1: Fetch Sentinel-2 data
        logger.info("Fetching Sentinel-2 data...")
        sentinel_data = await sentinel_service.fetch_data(
            geometry=request.geometry,
            date_range=request.date_range
        )
        
        if not sentinel_data:
            raise HTTPException(
                status_code=404,
                detail="No suitable Sentinel-2 imagery found for the specified area and date range"
            )
        
        # Step 2: Process NDVI (always calculated)
        logger.info("Processing data and calculating NDVI...")
        analysis_result = geo_processor.process_field(
            red_band=sentinel_data["red"],
            nir_band=sentinel_data["nir"],
            scl_band=sentinel_data["scl"],
            geometry=request.geometry,
            output_dir=results_dir
        )
        
        # Step 3: Generate NDVI visualization
        logger.info("Generating NDVI visualization...")
        ndvi_filename = geo_processor.generate_visualization(
            data_array=analysis_result["ndvi"],
            bounds=analysis_result["bounds"],
            output_dir=results_dir,
            filename="ndvi_visualization.png",
            index_name="NDVI",
            vmin=-0.2,
            vmax=1.0
        )
        
        # Step 4: Calculate and visualize additional indices
        additional_indices_urls = {}
        indices_stats = {}
        
        for index_name in request.indices:
            if index_name == "NDVI":
                continue  # Already processed
            
            try:
                logger.info(f"Calculating {index_name}...")
                index_data = None
                vmin, vmax = -1.0, 1.0  # Default range
                
                if index_name == "EVI":
                    index_data = geo_processor.calculate_evi(
                        red=sentinel_data["red"],
                        nir=sentinel_data["nir"],
                        blue=sentinel_data["blue"]
                    )
                    vmin, vmax = -0.2, 1.0
                    
                elif index_name == "PSRI":
                    index_data = geo_processor.calculate_psri(
                        red=sentinel_data["red"],
                        green=sentinel_data["green"],
                        nir=sentinel_data["nir"]
                    )
                    vmin, vmax = -0.2, 0.8
                    
                elif index_name == "NBR":
                    index_data = geo_processor.calculate_nbr(
                        nir=sentinel_data["nir"],
                        swir2=sentinel_data["swir2"]
                    )
                    vmin, vmax = -1.0, 1.0
                    
                elif index_name == "NDSI":
                    index_data = geo_processor.calculate_ndsi(
                        green=sentinel_data["green"],
                        swir1=sentinel_data["swir1"]
                    )
                    vmin, vmax = -1.0, 1.0
                
                if index_data is not None:
                    # Apply cloud mask
                    index_data_masked = geo_processor.apply_cloud_mask(index_data, sentinel_data["scl"])
                    
                    # Calculate statistics
                    valid_data = index_data_masked[~np.isnan(index_data_masked)]
                    if valid_data.size > 0:
                        indices_stats[index_name] = {
                            "mean": float(np.mean(valid_data)),
                            "min": float(np.min(valid_data)),
                            "max": float(np.max(valid_data)),
                            "std_dev": float(np.std(valid_data))
                        }
                    
                    # Generate visualization
                    index_filename = geo_processor.generate_visualization(
                        data_array=index_data_masked,
                        bounds=analysis_result["bounds"],
                        output_dir=results_dir,
                        filename=f"{index_name.lower()}_visualization.png",
                        index_name=index_name,
                        vmin=vmin,
                        vmax=vmax
                    )
                    additional_indices_urls[index_name] = f"/results/{analysis_id}/{index_filename}"
                    logger.info(f"{index_name} visualization generated")
                    
            except Exception as e:
                logger.error(f"Failed to calculate {index_name}: {e}")
                # Continue with other indices
        
        # Update stats with additional indices
        if indices_stats:
            analysis_result["stats"].indices_stats = indices_stats
        
        # Step 5: Prepare response
        response = AnalysisResponse(
            status="success",
            image_url=f"/results/{analysis_id}/{ndvi_filename}",
            bounds=analysis_result["bounds"],
            stats=analysis_result["stats"],
            additional_indices=additional_indices_urls if additional_indices_urls else None
        )
        
        logger.info(f"Analysis completed successfully. Mean NDVI: {response.stats.mean_ndvi:.3f}")
        if indices_stats:
            logger.info(f"Additional indices calculated: {list(indices_stats.keys())}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )


@router.get("/status/{analysis_id}")
async def get_analysis_status(analysis_id: str):
    """
    Get status of a specific analysis
    
    Args:
        analysis_id: UUID of the analysis
        
    Returns:
        Status information
    """
    results_dir = Path("results") / analysis_id
    
    if not results_dir.exists():
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    return {
        "analysis_id": analysis_id,
        "status": "completed",
        "timestamp": datetime.now().isoformat()
    }


@router.post("/analyze/timeseries", response_model=TimeSeriesResponse)
async def analyze_timeseries(request: TimeSeriesRequest):
    """
    Analyze vegetation index time series for a field
    
    Args:
        request: Time series analysis request with geometry, date range, and index type
        
    Returns:
        Time series data with dates and index values
    """
    try:
        logger.info(f"Starting time series analysis for {request.index_type}")
        logger.info(f"Date range: {request.start_date} to {request.end_date}")
        
        dates = []
        values = []
        
        # Parse dates
        start_date = datetime.fromisoformat(request.start_date)
        end_date = datetime.fromisoformat(request.end_date)
        
        # Validate Sentinel-2 data availability (launched June 2015)
        sentinel2_start = datetime(2015, 6, 23)
        if start_date < sentinel2_start:
            raise HTTPException(
                status_code=400,
                detail=f"Sentinel-2 data is only available from 2015-06-23 onwards. Please select a start date after this."
            )
        
        # Determine interval based on date range
        days_diff = (end_date - start_date).days
        
        # Limit maximum number of data points to prevent long processing
        # Reduced to 10 points for faster response
        max_points = 10
        
        if days_diff <= 30:
            interval = max(7, days_diff // max_points)  # Every week minimum
        elif days_diff <= 90:
            interval = max(14, days_diff // max_points)  # Every 2 weeks minimum
        elif days_diff <= 180:
            interval = max(21, days_diff // max_points)  # Every 3 weeks
        else:
            interval = max(30, days_diff // max_points)  # Monthly for long ranges
        
        logger.info(f"Using interval of {interval} days for {days_diff} days range")
        
        # Iterate through dates
        current_date = start_date
        point_count = 0
        while current_date <= end_date and point_count < max_points:
            date_str = current_date.strftime('%Y-%m-%d')
            
            # Get index value for this date
            index_value = await get_field_index_for_date(
                request.geometry,
                current_date,
                request.index_type
            )
            
            if index_value is not None and not np.isnan(index_value):
                dates.append(date_str)
                values.append(float(index_value))
                logger.info(f"Date {date_str}: {request.index_type}={index_value:.3f}")
                point_count += 1
            else:
                logger.warning(f"No valid data for {date_str}")
            
            current_date += timedelta(days=interval)
        
        if not dates:
            raise HTTPException(
                status_code=404,
                detail="No valid data found for the specified date range"
            )
        
        logger.info(f"Time series analysis completed. {len(dates)} data points.")
        
        return TimeSeriesResponse(
            index_type=request.index_type,
            dates=dates,
            values=values,
            geometry=request.geometry
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Time series analysis failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Time series analysis failed: {str(e)}"
        )


async def get_field_index_for_date(
    geometry: any,
    date: datetime,
    index_type: str
) -> Optional[float]:
    """
    Get vegetation index value for a specific date
    
    Args:
        geometry: Field geometry
        date: Target date
        index_type: Index type (NDVI, EVI, etc.)
        
    Returns:
        Mean index value or None if no data
    """
    try:
        # Format date for API request
        date_str = date.strftime('%Y-%m-%d')
        
        # Try with ±7 days window first (wider window for better data availability)
        date_start = (date - timedelta(days=7)).strftime('%Y-%m-%d')
        date_end = (date + timedelta(days=7)).strftime('%Y-%m-%d')
        
        logger.info(f"Fetching Sentinel-2 data for {date_str}, window: {date_start} to {date_end}")
        
        sentinel_data = await sentinel_service.fetch_data(
            geometry=geometry,
            date_range=[date_start, date_end]
        )
        
        # If no data found, try even wider window (±15 days)
        if not sentinel_data:
            logger.warning(f"No data found for {date_str} with ±7 days window, trying ±15 days")
            date_start = (date - timedelta(days=15)).strftime('%Y-%m-%d')
            date_end = (date + timedelta(days=15)).strftime('%Y-%m-%d')
            
            sentinel_data = await sentinel_service.fetch_data(
                geometry=geometry,
                date_range=[date_start, date_end]
            )
        
        if not sentinel_data:
            logger.warning(f"No Sentinel-2 data available for {date_str} even with ±15 days window")
            return None
        
        # Calculate the requested index
        if index_type == "NDVI":
            # NDVI calculation
            index_data = geo_processor.calculate_ndvi(
                red=sentinel_data["red"],
                nir=sentinel_data["nir"]
            )
        elif index_type == "EVI":
            index_data = geo_processor.calculate_evi(
                red=sentinel_data["red"],
                nir=sentinel_data["nir"],
                blue=sentinel_data["blue"]
            )
        elif index_type == "PSRI":
            index_data = geo_processor.calculate_psri(
                red=sentinel_data["red"],
                green=sentinel_data["green"],
                nir=sentinel_data["nir"]
            )
        elif index_type == "NBR":
            index_data = geo_processor.calculate_nbr(
                nir=sentinel_data["nir"],
                swir2=sentinel_data["swir2"]
            )
        elif index_type == "NDSI":
            index_data = geo_processor.calculate_ndsi(
                green=sentinel_data["green"],
                swir1=sentinel_data["swir1"]
            )
        else:
            return None
        
        # Apply cloud mask
        index_data_masked = geo_processor.apply_cloud_mask(index_data, sentinel_data["scl"])
        
        # Calculate mean value
        valid_data = index_data_masked[~np.isnan(index_data_masked)]
        
        if valid_data.size > 0:
            return np.mean(valid_data)
        else:
            return None
            
    except Exception as e:
        logger.error(f"Failed to get index for date {date}: {e}")
        return None


# ============================================================================
# Field Management Endpoints
# ============================================================================

@router.post("/fields", response_model=FieldResponse, status_code=201)
async def create_field(
    field_data: FieldCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Save a new field for the current user
    
    Args:
        field_data: Field name and geometry
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Created field data including field ID
    """
    try:
        logger.info(f"Creating new field '{field_data.name}' for user {current_user.id}")
        
        # Create new field
        new_field = Field(
            user_id=current_user.id,
            name=field_data.name,
            geometry_geojson=field_data.geometry.dict()
        )
        
        db.add(new_field)
        db.commit()
        db.refresh(new_field)
        
        logger.info(f"Field created successfully: ID={new_field.id}")
        
        return FieldResponse(
            id=new_field.id,
            user_id=new_field.user_id,
            name=new_field.name,
            geometry_geojson=new_field.geometry_geojson,
            created_at=new_field.created_at
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create field: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create field: {str(e)}")


@router.get("/fields", response_model=List[FieldResponse])
async def get_user_fields(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all fields for the current user
    
    Args:
        current_user: Authenticated user
        db: Database session
        
    Returns:
        List of user's fields
    """
    try:
        logger.info(f"Fetching fields for user {current_user.id}")
        
        fields = db.query(Field).filter(Field.user_id == current_user.id).order_by(Field.created_at.desc()).all()
        
        logger.info(f"Found {len(fields)} fields for user {current_user.id}")
        
        return [
            FieldResponse(
                id=field.id,
                user_id=field.user_id,
                name=field.name,
                geometry_geojson=field.geometry_geojson,
                created_at=field.created_at
            )
            for field in fields
        ]
        
    except Exception as e:
        logger.error(f"Failed to fetch fields: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch fields: {str(e)}")


# ============================================================================
# Dashboard Management Endpoints
# ============================================================================

@router.post("/dashboard/items", response_model=DashboardItemResponse, status_code=201)
async def create_dashboard_item(
    item_data: DashboardItemCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add an analysis to the user's dashboard
    
    Args:
        item_data: Dashboard item configuration
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Created dashboard item with field data
    """
    try:
        logger.info(f"Creating dashboard item for user {current_user.id}")
        
        # Verify that the field belongs to the current user
        field = db.query(Field).filter(
            Field.id == item_data.field_id,
            Field.user_id == current_user.id
        ).first()
        
        if not field:
            raise HTTPException(
                status_code=404,
                detail="Field not found or does not belong to the current user"
            )
        
        # Create dashboard item
        new_item = DashboardItem(
            user_id=current_user.id,
            field_id=item_data.field_id,
            item_type=item_data.item_type,
            start_date=item_data.start_date,
            end_date=item_data.end_date,
            index_type=item_data.index_type
        )
        
        db.add(new_item)
        db.commit()
        db.refresh(new_item)
        
        logger.info(f"Dashboard item created successfully: ID={new_item.id}")
        
        return DashboardItemResponse(
            id=new_item.id,
            user_id=new_item.user_id,
            field_id=new_item.field_id,
            field_name=field.name,
            field_geometry=field.geometry_geojson,
            item_type=new_item.item_type,
            start_date=new_item.start_date,
            end_date=new_item.end_date,
            index_type=new_item.index_type,
            display_order=new_item.display_order,
            created_at=new_item.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create dashboard item: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create dashboard item: {str(e)}")


@router.get("/dashboard/items", response_model=List[DashboardItemResponse])
async def get_dashboard_items(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all dashboard items for the current user
    
    Args:
        current_user: Authenticated user
        db: Database session
        
    Returns:
        List of dashboard items with field data
    """
    try:
        logger.info(f"Fetching dashboard items for user {current_user.id}")
        
        # Query dashboard items with joined field data
        items = db.query(DashboardItem).filter(
            DashboardItem.user_id == current_user.id
        ).order_by(DashboardItem.display_order, DashboardItem.created_at.desc()).all()
        
        logger.info(f"Found {len(items)} dashboard items for user {current_user.id}")
        
        # Build response with field data
        response_items = []
        for item in items:
            field = db.query(Field).filter(Field.id == item.field_id).first()
            if field:
                response_items.append(
                    DashboardItemResponse(
                        id=item.id,
                        user_id=item.user_id,
                        field_id=item.field_id,
                        field_name=field.name,
                        field_geometry=field.geometry_geojson,
                        item_type=item.item_type,
                        start_date=item.start_date,
                        end_date=item.end_date,
                        index_type=item.index_type,
                        display_order=item.display_order,
                        created_at=item.created_at
                    )
                )
        
        return response_items
        
    except Exception as e:
        logger.error(f"Failed to fetch dashboard items: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch dashboard items: {str(e)}")


@router.delete("/dashboard/items/{item_id}", status_code=204)
async def delete_dashboard_item(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a dashboard item
    
    Args:
        item_id: Dashboard item ID
        current_user: Authenticated user
        db: Database session
    """
    try:
        logger.info(f"Deleting dashboard item {item_id} for user {current_user.id}")
        
        # Find the item and verify ownership
        item = db.query(DashboardItem).filter(
            DashboardItem.id == item_id,
            DashboardItem.user_id == current_user.id
        ).first()
        
        if not item:
            raise HTTPException(
                status_code=404,
                detail="Dashboard item not found or does not belong to the current user"
            )
        
        db.delete(item)
        db.commit()
        
        logger.info(f"Dashboard item {item_id} deleted successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete dashboard item: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete dashboard item: {str(e)}")


# ============================================================================
# Zone Analysis Endpoints
# ============================================================================

@router.post("/analyze/zones", response_model=ZoneAnalysisResponse)
async def create_management_zones(
    request: ZoneAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create management zones for a field based on NDVI clustering
    
    Args:
        request: Zone analysis request with field/geometry, NDVI data reference, and number of zones
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Zone analysis results with GeoJSON, statistics, and download links
    """
    try:
        logger.info(f"Starting zone analysis for user {current_user.id} with {request.num_zones} zones")
        
        # Determine NDVI data path
        ndvi_path = None
        
        if request.ndvi_data_url:
            # Direct path to NDVI file
            ndvi_path = request.ndvi_data_url
            logger.info(f"Using provided NDVI data: {ndvi_path}")
        elif request.analysis_id:
            # Try to find NDVI file from previous analysis
            ndvi_path = Path("results") / request.analysis_id / "ndvi.tif"
            if not ndvi_path.exists():
                raise HTTPException(
                    status_code=404,
                    detail=f"NDVI data not found for analysis_id: {request.analysis_id}"
                )
            logger.info(f"Using NDVI from analysis {request.analysis_id}")
        elif request.field_id:
            # Need to run analysis first for this field
            field = db.query(Field).filter(
                Field.id == request.field_id,
                Field.user_id == current_user.id
            ).first()
            
            if not field:
                raise HTTPException(
                    status_code=404,
                    detail="Field not found or does not belong to the current user"
                )
            
            # Create a temporary analysis to get NDVI data
            logger.info(f"Running NDVI analysis for field {request.field_id}")
            analysis_id = str(uuid.uuid4())
            results_dir = Path("results") / analysis_id
            results_dir.mkdir(parents=True, exist_ok=True)
            
            # Fetch and process data
            from datetime import date
            sentinel_data = await sentinel_service.fetch_data(
                geometry=field.geometry_geojson,
                date_range=[
                    (date.today() - timedelta(days=30)).isoformat(),
                    date.today().isoformat()
                ]
            )
            
            if not sentinel_data:
                raise HTTPException(
                    status_code=404,
                    detail="No suitable Sentinel-2 imagery found for this field"
                )
            
            analysis_result = geo_processor.process_field(
                red_band=sentinel_data["red"],
                nir_band=sentinel_data["nir"],
                scl_band=sentinel_data["scl"],
                geometry=field.geometry_geojson,
                output_dir=results_dir
            )
            
            ndvi_path = results_dir / "ndvi.tif"
        else:
            raise HTTPException(
                status_code=400,
                detail="Must provide either field_id, analysis_id, or ndvi_data_url"
            )
        
        if not ndvi_path or not Path(ndvi_path).exists():
            raise HTTPException(
                status_code=404,
                detail="NDVI data file not found"
            )
        
        # Create management zones
        logger.info(f"Creating {request.num_zones} management zones...")
        zone_result = zone_analyzer.create_management_zones(
            ndvi_path=str(ndvi_path),
            num_zones=request.num_zones,
            analysis_id=request.analysis_id
        )
        
        logger.info(f"Zone analysis completed successfully: {zone_result['num_zones']} zones created")
        
        return ZoneAnalysisResponse(**zone_result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create management zones: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create management zones: {str(e)}")


# ============================================================================
# File Download Endpoint
# ============================================================================

from fastapi.responses import FileResponse
import os

@router.get("/downloads/{file_id}")
async def download_file(
    file_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Download generated zone files (GeoJSON or Shapefile ZIP)
    
    Args:
        file_id: File identifier (e.g., zones_uuid.geojson or zones_uuid.zip)
        current_user: Authenticated user
        
    Returns:
        File for download
    """
    try:
        logger.info(f"Download request for file: {file_id}")
        
        # Construct file path
        file_path = Path("results") / file_id
        
        # Security check: ensure file exists and is within results directory
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        if not file_path.is_relative_to(Path("results").resolve()):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Determine media type
        media_type = "application/octet-stream"
        if file_id.endswith('.geojson'):
            media_type = "application/geo+json"
        elif file_id.endswith('.zip'):
            media_type = "application/zip"
        
        logger.info(f"Serving file: {file_path}")
        
        return FileResponse(
            path=str(file_path),
            media_type=media_type,
            filename=file_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download file: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to download file: {str(e)}")


# ============================================================================
# AI Agronomist Endpoints
# ============================================================================

@router.post("/analysis/ai_report", response_model=AIReportResponse)
async def generate_ai_report(
    request: AIReportRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Generate AI-powered agronomist report based on field analysis context
    
    This endpoint uses Google Gemini to analyze field data and provide:
    - Comprehensive field health assessment
    - Zone-specific recommendations
    - VRA (Variable Rate Application) strategies
    - Action plan for farmer
    
    Args:
        request: AI report request with complete analysis context
        current_user: Authenticated user
        
    Returns:
        AIReportResponse with generated Markdown report
    """
    try:
        logger.info(f"✅ AI report request received from user {current_user.id}")
        logger.info(f"Field: {request.context.field_info.name}, Area: {request.context.field_info.area_ha} ha")
        logger.info(f"NDVI stats: mean={request.context.indices_summary.NDVI.mean}, std_dev={request.context.indices_summary.NDVI.std_dev}")
        
        # Check if AI service is available
        if not ai_agronomist_service.is_available():
            raise HTTPException(
                status_code=503,
                detail="AI service temporarily unavailable. Please ensure GEMINI_API_KEY is configured."
            )
        
        # Generate report
        report_response = await ai_agronomist_service.generate_report(
            context=request.context
        )
        
        logger.info(f"AI report generated successfully in {report_response.generation_time_seconds}s")
        
        return report_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate AI report: {e}", exc_info=True)
        
        # Return structured error response
        error_type = "api_error"
        if "timeout" in str(e).lower():
            error_type = "api_timeout"
        elif "quota" in str(e).lower() or "rate" in str(e).lower():
            error_type = "quota_exceeded"
        elif "not available" in str(e).lower():
            error_type = "service_unavailable"
        
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "error_type": error_type,
                "message": "Не удалось сгенерировать AI отчет",
                "details": str(e)
            }
        )


@router.post("/analysis/ai_chat", response_model=AIChatResponse)
async def ai_chat(
    request: AIChatRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Interactive AI chat with RAG (Retrieval-Augmented Generation)
    
    This endpoint provides context-aware chat functionality where the AI assistant
    answers questions based on the original field analysis data.
    
    Args:
        request: Chat request with original context, chat history, and new question
        current_user: Authenticated user
        
    Returns:
        AIChatResponse with AI-generated answer
    """
    try:
        logger.info(f"AI chat requested by user {current_user.id}")
        logger.debug(f"Question: {request.new_question[:100]}...")
        
        # Check if AI service is available
        if not ai_agronomist_service.is_available():
            raise HTTPException(
                status_code=503,
                detail="AI service temporarily unavailable. Please ensure GEMINI_API_KEY is configured."
            )
        
        # Validate question length
        if len(request.new_question.strip()) < 3:
            raise HTTPException(
                status_code=400,
                detail="Question too short. Please provide a meaningful question."
            )
        
        # Generate chat response
        chat_response = await ai_agronomist_service.chat(
            original_context=request.original_context,
            chat_history=request.chat_history,
            new_question=request.new_question
        )
        
        logger.info(f"AI chat response generated in {chat_response.generation_time_seconds}s")
        
        return chat_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate AI chat response: {e}", exc_info=True)
        
        # Return structured error response
        error_type = "api_error"
        if "timeout" in str(e).lower():
            error_type = "api_timeout"
        elif "quota" in str(e).lower() or "rate" in str(e).lower():
            error_type = "quota_exceeded"
        elif "not available" in str(e).lower():
            error_type = "service_unavailable"
        
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "error_type": error_type,
                "message": "Не удалось получить ответ от AI ассистента",
                "details": str(e)
            }
        )


@router.get("/ai/health")
async def ai_health_check():
    """
    Check AI service availability
    
    Returns:
        Status of AI service (available/unavailable)
    """
    is_available = ai_agronomist_service.is_available()
    
    return {
        "status": "available" if is_available else "unavailable",
        "service": "Google Gemini AI",
        "model": ai_agronomist_service.model_name if is_available else None,
        "message": "AI service is ready" if is_available else "AI service not configured (missing GEMINI_API_KEY)"
    }
