"""
Sentinel Hub API integration service
Fetches Sentinel-2 data
"""
import os
import numpy as np
from typing import Dict, Optional, List
import logging
from datetime import datetime, timedelta
import requests
from shapely.geometry import shape
import base64
import json

from api.schemas import Geometry

logger = logging.getLogger(__name__)


class SentinelService:
    """
    Service for fetching Sentinel-2 data
    
    This implementation provides two modes:
    1. Real API mode using Sentinel Hub (requires API credentials)
    2. Mock mode for testing without credentials
    """
    
    def __init__(self):
        """Initialize Sentinel Hub service"""
        self.client_id = os.getenv("SENTINEL_CLIENT_ID")
        self.client_secret = os.getenv("SENTINEL_CLIENT_SECRET")
        self.instance_id = os.getenv("SENTINEL_INSTANCE_ID")
        
        # Use mock mode if credentials are not provided
        self.use_mock = not all([self.client_id, self.client_secret])
        
        if self.use_mock:
            logger.warning(
                "Sentinel Hub credentials not found. Using MOCK mode. "
                "Set SENTINEL_CLIENT_ID and SENTINEL_CLIENT_SECRET environment variables for real data."
            )
        else:
            logger.info("Sentinel Hub credentials found. Using REAL API mode.")
            self.api_url = "https://services.sentinel-hub.com"
            self.access_token = None
    
    def _get_access_token(self) -> str:
        """
        Get OAuth2 access token from Sentinel Hub
        
        Returns:
            Access token
        """
        if self.access_token:
            return self.access_token
        
        url = f"{self.api_url}/oauth/token"
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        
        response = requests.post(url, data=data)
        response.raise_for_status()
        
        self.access_token = response.json()["access_token"]
        return self.access_token
    
    def _fetch_real_data(
        self,
        geometry: Geometry,
        date_range: List[str]
    ) -> Optional[Dict[str, np.ndarray]]:
        """
        Fetch real Sentinel-2 data from Sentinel Hub API
        
        Args:
            geometry: Field geometry
            date_range: Date range [start, end]
            
        Returns:
            Dictionary with band data or None
        """
        try:
            token = self._get_access_token()
            
            # Prepare request
            geom = shape(geometry.dict())
            bbox = geom.bounds  # [minx, miny, maxx, maxy]
            
            # Evalscript: stack 7 bands into one multi-band GeoTIFF  
            evalscript = """
            //VERSION=3
            function setup() {
              return {
                input: [{
                  bands: ["B02", "B03", "B04", "B08", "B11", "B12", "SCL"],
                  units: "DN"
                }],
                output: { bands: 7, sampleType: "FLOAT32" }
              };
            }
            function evaluatePixel(s) {
              const scale = 10000.0;
              return [
                s.B02/scale,
                s.B03/scale,
                s.B04/scale,
                s.B08/scale,
                s.B11/scale,
                s.B12/scale,
                s.SCL
              ];
            }
            """
            
            request_payload = {
                "input": {
                    "bounds": {
                        "geometry": geometry.dict(),
                        "properties": {"crs": "http://www.opengis.net/def/crs/EPSG/0/4326", "clipToGeometry": True}
                    },
                    "data": [{
                        "type": "sentinel-2-l2a",
                        "dataFilter": {
                            "timeRange": {
                                "from": f"{date_range[0]}T00:00:00Z",
                                "to": f"{date_range[1]}T23:59:59Z"
                            },
                            "maxCloudCoverage": 80,  # Increased to 80% for better data availability
                            "mosaickingOrder": "leastCC"  # Changed to leastCC (least cloud coverage)
                        },
                        "processing": {
                            "upsampling": "NEAREST",
                            "downsampling": "NEAREST"
                        }
                    }]
                },
                "output": {
                  "width": 1024,  # Increased resolution for better pixel visibility
                  "height": 1024,
                  "responses": [
                    {"identifier": "default", "format": {"type": "image/tiff"}}
                  ]
                },
                "evalscript": evalscript
            }
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            url = f"{self.api_url}/api/v1/process"
            def _perform_request(payload):
                resp = requests.post(url, json=payload, headers=headers, timeout=60)
                
                # Log response details
                logger.info(f"API Response: status={resp.status_code}, content-type={resp.headers.get('content-type')}, size={len(resp.content)} bytes")
                
                # Check if response is JSON (error message)
                content_type = resp.headers.get('content-type', '')
                if 'json' in content_type.lower():
                    try:
                        error_data = resp.json()
                        logger.error(f"Sentinel Hub API returned JSON error: {error_data}")
                        raise ValueError(f"API error: {error_data.get('error', {}).get('message', str(error_data))}")
                    except (ValueError, KeyError) as json_err:
                        if resp.status_code >= 400:
                            raise ValueError(f"API returned error status {resp.status_code}: {resp.text[:200]}")
                
                resp.raise_for_status()
                
                # Try to use rasterio if available, otherwise use PIL/numpy
                try:
                    from rasterio.io import MemoryFile as _MemoryFile
                    with _MemoryFile(resp.content) as memfile:
                        with memfile.open() as dataset:
                            b02 = dataset.read(1)
                            b03 = dataset.read(2)
                            b04 = dataset.read(3)
                            b08 = dataset.read(4)
                            b11 = dataset.read(5)
                            b12 = dataset.read(6)
                            scl = dataset.read(7)
                    return b02, b03, b04, b08, b11, b12, scl
                except (ImportError, Exception) as e:
                    # Rasterio not available or failed, try PIL
                    logger.warning(f"Rasterio failed ({type(e).__name__}), trying PIL for TIFF reading")
                    from PIL import Image, TiffImagePlugin
                    from io import BytesIO
                    
                    try:
                        # Open TIFF with PIL
                        img = Image.open(BytesIO(resp.content))
                        
                        # Check if it's a multi-page TIFF (each band is a page)
                        bands = []
                        page_count = getattr(img, 'n_frames', 1)
                        
                        if page_count >= 7:
                            # Multi-page TIFF - each band is a separate page
                            logger.info(f"Reading {page_count}-page TIFF")
                            for i in range(7):
                                img.seek(i)
                                band_array = np.array(img, dtype=np.float32)
                                bands.append(band_array)
                        else:
                            # Single page with all bands - need to extract them
                            logger.info("Reading single-page multi-band TIFF")
                            img_array = np.array(img, dtype=np.float32)
                            
                            # Check if it's (height, width, 7) or (7, height, width)
                            if len(img_array.shape) == 3:
                                if img_array.shape[2] == 7:
                                    # (H, W, 7) - split along last axis
                                    for i in range(7):
                                        bands.append(img_array[:, :, i])
                                elif img_array.shape[0] == 7:
                                    # (7, H, W) - already separated
                                    for i in range(7):
                                        bands.append(img_array[i, :, :])
                                else:
                                    raise ValueError(f"Unexpected TIFF shape: {img_array.shape}")
                            else:
                                raise ValueError(f"Expected 3D array, got shape: {img_array.shape}")
                        
                        b02, b03, b04, b08, b11, b12, scl = bands
                        logger.info(f"Successfully read bands with shapes: B02={b02.shape}, SCL={scl.shape}")
                        return b02, b03, b04, b08, b11, b12, scl
                        
                    except Exception as pil_error:
                        logger.error(f"PIL TIFF reading failed: {pil_error}", exc_info=True)
                        raise ValueError(f"Failed to read TIFF data: {pil_error}")

            b02, b03, b04, b08, b11, b12, scl = _perform_request(request_payload)

            # SCL diagnostics
            # Valid SCL codes for Sentinel-2 L2A: 4 (Vegetation), 5 (Not vegetated), 6 (Water), 7 (Unclassified), 11 (Snow/ice)
            unique, counts = np.unique(scl, return_counts=True)
            hist = dict(zip(unique.astype(int).tolist(), counts.astype(int).tolist()))
            valid = np.isin(scl, [4, 5, 6, 7, 11])
            valid_fraction = float(valid.sum()) / float(scl.size) if scl.size else 0.0
            logger.info(f"Date range {date_range[0]} to {date_range[1]}: SCL histogram: {hist}; valid_fraction={valid_fraction:.3f}")

            # Retry if very few valid pixels (lowered threshold from 0.01 to 0.001)
            if valid_fraction < 0.001:
                import copy
                retry_payload = copy.deepcopy(request_payload)
                # Already using leastCC and 80% cloud, just expand time window
                # expand window back by 30 days
                start_dt = datetime.fromisoformat(date_range[0]) - timedelta(days=30)
                retry_payload["input"]["data"][0]["dataFilter"]["timeRange"]["from"] = f"{start_dt.date().isoformat()}T00:00:00Z"
                retry_payload["input"]["data"][0]["dataFilter"]["maxCloudCoverage"] = 95  # Almost any data
                logger.warning(f"Very low valid pixel fraction ({valid_fraction:.4f}), retrying with expanded window (-30 days) and 95% cloud coverage")
                try:
                    b02, b03, b04, b08, b11, b12, scl = _perform_request(retry_payload)
                    unique, counts = np.unique(scl, return_counts=True)
                    hist = dict(zip(unique.astype(int).tolist(), counts.astype(int).tolist()))
                    valid = np.isin(scl, [4, 5, 6, 7, 11])
                    valid_fraction = float(valid.sum()) / float(scl.size) if scl.size else 0.0
                    logger.info(f"Retry result: SCL histogram: {hist}; valid_fraction={valid_fraction:.3f}")
                except Exception as retry_err:
                    logger.error(f"Retry failed: {retry_err}")
                    # Continue with original data even if retry fails

            return {
                "blue": b02.astype("float32"),
                "green": b03.astype("float32"),
                "red": b04.astype("float32"),
                "nir": b08.astype("float32"),
                "swir1": b11.astype("float32"),
                "swir2": b12.astype("float32"),
                "scl": scl.astype("uint8")
            }
            
        except Exception as e:
            logger.error(f"Failed to fetch real Sentinel-2 data for date range {date_range[0]} to {date_range[1]}: {e}", exc_info=True)
            # Return None to trigger retry in calling function
            return None
    
    def _generate_mock_data(
        self,
        geometry: Geometry,
        date_range: Optional[List[str]] = None
    ) -> Dict[str, np.ndarray]:
        """
        Generate mock Sentinel-2 data for testing
        
        Creates realistic-looking agricultural field data with:
        - Variable NDVI patterns based on season
        - Some cloud coverage
        - Realistic value ranges
        
        Args:
            geometry: Field geometry (used for size estimation)
            date_range: Date range (used for seasonal variation)
            
        Returns:
            Dictionary with mock band data
        """
        logger.info("Generating mock Sentinel-2 data...")
        
        # Fixed size for demo
        size = (512, 512)
        
        # Calculate seasonal factor based on date
        seasonal_factor = 1.0
        if date_range and len(date_range) > 0:
            try:
                # Use the start date for season calculation
                date_str = date_range[0].split('T')[0]  # Remove time part if present
                date_obj = datetime.fromisoformat(date_str)
                
                # Calculate day of year (1-365)
                day_of_year = date_obj.timetuple().tm_yday
                
                # Seasonal variation for Northern Hemisphere agriculture
                # Spring (Mar-May, days 60-150): growing season, NDVI increases
                # Summer (Jun-Aug, days 150-240): peak vegetation, high NDVI
                # Autumn (Sep-Nov, days 240-330): harvest, NDVI decreases
                # Winter (Dec-Feb, days 330-60): dormant, low NDVI
                
                # Create sinusoidal pattern with peak in summer
                # Peak around day 200 (mid-July), minimum around day 20 (mid-January)
                seasonal_factor = 0.5 + 0.5 * np.sin((day_of_year - 80) * 2 * np.pi / 365)
                
                # Add some random variation
                seasonal_factor += np.random.uniform(-0.1, 0.1)
                seasonal_factor = np.clip(seasonal_factor, 0.2, 1.0)
                
                logger.info(f"Date: {date_str}, Day of year: {day_of_year}, Seasonal factor: {seasonal_factor:.3f}")
                
            except Exception as e:
                logger.warning(f"Failed to parse date for seasonal variation: {e}")
                seasonal_factor = 0.7  # Default to moderate vegetation
        
        # Generate realistic Red and NIR bands
        # Simulate agricultural field with varying vegetation
        # Use date-based seed for reproducibility but variation across dates
        if date_range and len(date_range) > 0:
            seed = hash(date_range[0]) % (2**32)
        else:
            seed = 42
        np.random.seed(seed)
        
        # Base reflectance values (scaled to 0-10000 as Sentinel-2 DN values)
        # Healthy vegetation: Red ~500-1000, NIR ~3000-5000
        # Bare soil: Red ~1500-2500, NIR ~2000-3000
        
        # Create spatial pattern
        y, x = np.ogrid[0:size[0], 0:size[1]]
        
        # Create zones with different vegetation health
        pattern = np.sin(x / 50) * np.cos(y / 50) + np.random.randn(*size) * 0.3
        pattern = (pattern - pattern.min()) / (pattern.max() - pattern.min())
        
        # Apply seasonal factor to vegetation patterns
        # Higher seasonal_factor = more vegetation (summer)
        # Lower seasonal_factor = less vegetation (winter)
        
        # Generate NIR band (higher for healthy vegetation, scales with season)
        nir_base = 1000 + pattern * 2000  # Base NIR pattern
        nir = nir_base * seasonal_factor + np.random.randn(*size) * 200
        nir = np.clip(nir, 500, 8000).astype(np.uint16)
        
        # Generate Red band (lower for healthy vegetation due to chlorophyll absorption)
        # Inverse relationship with season - less red absorption in winter
        red_base = 2500 - pattern * 1500  # Base red pattern
        red = red_base * (1.5 - seasonal_factor * 0.5) + np.random.randn(*size) * 150
        red = np.clip(red, 300, 4000).astype(np.uint16)
        
        # Generate Blue band (B02) - similar to red but slightly different
        blue_base = 2200 - pattern * 1200
        blue = blue_base * (1.4 - seasonal_factor * 0.4) + np.random.randn(*size) * 130
        blue = np.clip(blue, 250, 3500).astype(np.uint16)
        
        # Generate Green band (B03) - between blue and red
        green_base = 2300 - pattern * 1300
        green = green_base * (1.4 - seasonal_factor * 0.4) + np.random.randn(*size) * 140
        green = np.clip(green, 280, 3600).astype(np.uint16)
        
        # Generate SWIR1 band (B11) - sensitive to moisture, varies with season
        swir1_base = 2000 - pattern * 1000
        swir1 = swir1_base * (1.3 - seasonal_factor * 0.3) + np.random.randn(*size) * 200
        swir1 = np.clip(swir1, 500, 5000).astype(np.uint16)
        
        # Generate SWIR2 band (B12) - similar to SWIR1
        swir2_base = 1800 - pattern * 900
        swir2 = swir2_base * (1.3 - seasonal_factor * 0.3) + np.random.randn(*size) * 190
        swir2 = np.clip(swir2, 450, 4800).astype(np.uint16)
        
        # Generate SCL (Scene Classification Layer)
        scl = np.ones(size, dtype=np.uint8) * 4  # 4 = Vegetation
        
        # Add some clouds (code 8 and 9)
        cloud_mask = np.random.rand(*size) < 0.05  # 5% cloud coverage
        scl[cloud_mask] = np.random.choice([8, 9], size=np.sum(cloud_mask))
        
        # Add some cloud shadows (code 3)
        shadow_mask = np.random.rand(*size) < 0.02  # 2% shadow coverage
        scl[shadow_mask] = 3
        
        logger.info(f"Generated mock data: Blue={blue.shape}, Green={green.shape}, Red={red.shape}, NIR={nir.shape}, SWIR1={swir1.shape}, SWIR2={swir2.shape}, SCL={scl.shape}")
        
        return {
            "blue": blue,
            "green": green,
            "red": red,
            "nir": nir,
            "swir1": swir1,
            "swir2": swir2,
            "scl": scl
        }
    
    async def fetch_data(
        self,
        geometry: Geometry,
        date_range: List[str]
    ) -> Optional[Dict[str, np.ndarray]]:
        """
        Fetch Sentinel-2 data (REAL ONLY - NO MOCK)
        
        Args:
            geometry: Field geometry
            date_range: Date range for imagery
            
        Returns:
            Dictionary with band data (red, nir, scl) or None if not found
        """
        logger.info(f"Fetching REAL Sentinel-2 data for date range: {date_range}")
        
        # ONLY use real API - NO MOCK DATA
        if self.use_mock:
            logger.error("Sentinel Hub credentials not configured. MOCK mode is disabled. Please configure credentials.")
            raise ValueError("Sentinel Hub credentials required. Please configure SENTINEL_CLIENT_ID and SENTINEL_CLIENT_SECRET in backend/config.py")
        
        # Fetch real data
        real_data = self._fetch_real_data(geometry, date_range)
        if not real_data:
            logger.error("Failed to fetch real Sentinel-2 data")
            raise ValueError("No Sentinel-2 data available for the specified area and date range")
        
        return real_data



