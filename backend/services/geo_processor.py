"""
Geospatial data processing module
Handles NDVI calculation, cloud masking, and statistics
"""
import numpy as np
from shapely.geometry import shape, mapping

try:
    import rasterio
    from rasterio.mask import mask
    from rasterio.transform import from_bounds
    from rasterio.io import MemoryFile
    RASTERIO_AVAILABLE = True
except ImportError:
    RASTERIO_AVAILABLE = False
    print("WARNING: rasterio not available. Image processing features will be limited.")
    
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from pathlib import Path
import logging
from typing import Dict, Any, Tuple
from datetime import datetime

from api.schemas import Geometry, FieldStats

logger = logging.getLogger(__name__)


class GeoProcessor:
    """Processes geospatial data and calculates NDVI"""
    
    def __init__(self):
        """Initialize GeoProcessor"""
        # Define color maps for different indices
        self.colormaps = {
            'NDVI': LinearSegmentedColormap.from_list(
                'ndvi',
                [
                    (0.0, '#8B4513'),   # Brown for bare soil/very low
                    (0.2, '#D2691E'),   # Light brown
                    (0.3, '#FFD700'),   # Gold
                    (0.4, '#FFFF00'),   # Yellow
                    (0.5, '#ADFF2F'),   # Yellow-green
                    (0.6, '#7FFF00'),   # Light green
                    (0.7, '#00FF00'),   # Green
                    (0.8, '#228B22'),   # Forest green
                    (1.0, '#006400')    # Dark green
                ]
            ),
            'EVI': LinearSegmentedColormap.from_list(
                'evi',
                [
                    (0.0, '#8B4513'),   # Brown
                    (0.2, '#FFD700'),   # Gold
                    (0.4, '#ADFF2F'),   # Yellow-green
                    (0.6, '#00FF00'),   # Green
                    (1.0, '#006400')    # Dark green
                ]
            ),
            'PSRI': LinearSegmentedColormap.from_list(
                'psri',
                [
                    (0.0, '#00FF00'),   # Green - healthy
                    (0.5, '#FFFF00'),   # Yellow
                    (1.0, '#FF0000')    # Red - senescence
                ]
            ),
            'NBR': LinearSegmentedColormap.from_list(
                'nbr',
                [
                    (0.0, '#FF0000'),   # Red - burned
                    (0.3, '#FFFF00'),   # Yellow
                    (0.5, '#00FF00'),   # Green - healthy
                    (1.0, '#006400')    # Dark green
                ]
            ),
            'NDSI': LinearSegmentedColormap.from_list(
                'ndsi',
                [
                    (0.0, '#8B4513'),   # Brown - no snow
                    (0.3, '#FFFFFF'),   # White - snow
                    (1.0, '#E0F8FF')    # Light blue - ice
                ]
            )
        }
        
        # Backwards compatibility
        self.ndvi_colormap = self.colormaps['NDVI']
    
    def calculate_ndvi(
        self, 
        red: np.ndarray, 
        nir: np.ndarray
    ) -> np.ndarray:
        """
        Calculate NDVI from Red and NIR bands
        
        NDVI = (NIR - Red) / (NIR + Red)
        
        Args:
            red: Red band array (B04)
            nir: Near-infrared band array (B08)
            
        Returns:
            NDVI array with values between -1 and 1
        """
        # Convert to float32 for precision
        red = red.astype('float32')
        nir = nir.astype('float32')
        
        # Suppress division warnings
        np.seterr(divide='ignore', invalid='ignore')
        
        # Calculate NDVI
        numerator = nir - red
        denominator = nir + red
        
        # Handle division by zero
        ndvi = np.where(
            denominator != 0,
            numerator / denominator,
            0
        )
        
        # Clip values to valid range [-1, 1]
        ndvi = np.clip(ndvi, -1, 1)
        
        return ndvi
    
    def calculate_evi(
        self,
        red: np.ndarray,
        nir: np.ndarray,
        blue: np.ndarray
    ) -> np.ndarray:
        """
        Calculate Enhanced Vegetation Index (EVI)
        
        EVI = 2.5 * (NIR - RED) / (NIR + 6*RED - 7.5*BLUE + 1)
        
        Args:
            red: Red band array (B04)
            nir: Near-infrared band array (B08)
            blue: Blue band array (B02)
            
        Returns:
            EVI array
        """
        red = red.astype('float32')
        nir = nir.astype('float32')
        blue = blue.astype('float32')
        
        np.seterr(divide='ignore', invalid='ignore')
        
        numerator = nir - red
        denominator = nir + 6*red - 7.5*blue + 1
        
        evi = np.where(
            denominator != 0,
            2.5 * numerator / denominator,
            0
        )
        
        return np.clip(evi, -1, 1)
    
    def calculate_psri(
        self,
        red: np.ndarray,
        green: np.ndarray,
        nir: np.ndarray
    ) -> np.ndarray:
        """
        Calculate Plant Senescence Reflectance Index (PSRI)
        
        PSRI = (RED - GREEN) / NIR
        
        Args:
            red: Red band array (B04)
            green: Green band array (B03)
            nir: Near-infrared band array (B08)
            
        Returns:
            PSRI array
        """
        red = red.astype('float32')
        green = green.astype('float32')
        nir = nir.astype('float32')
        
        np.seterr(divide='ignore', invalid='ignore')
        
        psri = np.where(
            nir != 0,
            (red - green) / nir,
            0
        )
        
        return psri
    
    def calculate_nbr(
        self,
        nir: np.ndarray,
        swir2: np.ndarray
    ) -> np.ndarray:
        """
        Calculate Normalized Burn Ratio (NBR)
        
        NBR = (NIR - SWIR2) / (NIR + SWIR2)
        
        Args:
            nir: Near-infrared band array (B08)
            swir2: Short-wave infrared 2 band array (B12)
            
        Returns:
            NBR array
        """
        nir = nir.astype('float32')
        swir2 = swir2.astype('float32')
        
        np.seterr(divide='ignore', invalid='ignore')
        
        numerator = nir - swir2
        denominator = nir + swir2
        
        nbr = np.where(
            denominator != 0,
            numerator / denominator,
            0
        )
        
        return np.clip(nbr, -1, 1)
    
    def calculate_ndsi(
        self,
        green: np.ndarray,
        swir1: np.ndarray
    ) -> np.ndarray:
        """
        Calculate Normalized Difference Snow Index (NDSI)
        
        NDSI = (GREEN - SWIR1) / (GREEN + SWIR1)
        
        Args:
            green: Green band array (B03)
            swir1: Short-wave infrared 1 band array (B11)
            
        Returns:
            NDSI array
        """
        green = green.astype('float32')
        swir1 = swir1.astype('float32')
        
        np.seterr(divide='ignore', invalid='ignore')
        
        numerator = green - swir1
        denominator = green + swir1
        
        ndsi = np.where(
            denominator != 0,
            numerator / denominator,
            0
        )
        
        return np.clip(ndsi, -1, 1)
    
    def apply_cloud_mask(
        self,
        data_array: np.ndarray,
        scl: np.ndarray
    ) -> np.ndarray:
        """
        Apply cloud mask using Scene Classification Layer (SCL)
        
        SCL codes (Sentinel-2 L2A):
        - 0: No Data (mask)
        - 1: Saturated or defective (mask)
        - 2: Dark area pixels (mask)
        - 3: Cloud shadows (mask)
        - 4: Vegetation (valid)
        - 5: Not vegetated (valid)
        - 6: Water (valid)
        - 7: Unclassified (valid)
        - 8: Cloud medium probability (mask)
        - 9: Cloud high probability (mask)
        - 10: Thin cirrus (mask)
        - 11: Snow/ice (valid)
        
        Args:
            data_array: Data array to mask
            scl: Scene Classification Layer
            
        Returns:
            Masked array with NaN for clouds and invalid pixels
        """
        # Resize SCL to match data array if needed
        if scl.shape != data_array.shape:
            from scipy.ndimage import zoom
            zoom_factors = (
                data_array.shape[0] / scl.shape[0],
                data_array.shape[1] / scl.shape[1]
            )
            scl = zoom(scl, zoom_factors, order=0)  # Nearest neighbor
        
        # Create mask for invalid/cloud pixels
        # Valid SCL codes: 4 (Vegetation), 5 (Not vegetated), 6 (Water), 7 (Unclassified), 11 (Snow/ice)
        # Mask everything else: 0, 1, 2, 3, 8, 9, 10
        invalid_mask = ~np.isin(scl, [4, 5, 6, 7, 11])
        
        # Apply mask
        masked_data = data_array.copy()
        masked_data[invalid_mask] = np.nan
        
        return masked_data
    
    def calculate_statistics(
        self,
        ndvi: np.ndarray,
        geometry: Geometry,
        capture_date: str
    ) -> FieldStats:
        """
        Calculate field statistics from NDVI data
        
        Args:
            ndvi: NDVI array
            geometry: Field geometry
            capture_date: Date of satellite capture
            
        Returns:
            Field statistics
        """
        # Calculate area in hectares
        geom = shape(geometry.dict())
        # Approximate area calculation (for better precision, use projected CRS)
        area_ha = geom.area * 111320 * 111320 / 10000  # Very rough approximation
        
        # Filter out NaN values
        valid_ndvi = ndvi[~np.isnan(ndvi)]
        total_pixels = ndvi.size
        valid_pixels = valid_ndvi.size
        
        # Calculate mean NDVI
        mean_ndvi = float(np.mean(valid_ndvi)) if valid_pixels > 0 else 0.0
        
        # Calculate cloud coverage
        cloud_coverage_percent = ((total_pixels - valid_pixels) / total_pixels * 100) if total_pixels > 0 else 0.0
        valid_pixels_percent = 100.0 - cloud_coverage_percent
        
        # Calculate NDVI zones distribution
        if valid_pixels > 0:
            low_zone = np.sum(valid_ndvi < 0.3) / valid_pixels * 100
            medium_zone = np.sum((valid_ndvi >= 0.3) & (valid_ndvi < 0.6)) / valid_pixels * 100
            high_zone = np.sum(valid_ndvi >= 0.6) / valid_pixels * 100
        else:
            low_zone = medium_zone = high_zone = 0.0
        
        return FieldStats(
            area_ha=round(area_ha, 2),
            mean_ndvi=round(mean_ndvi, 3),
            capture_date=capture_date,
            cloud_coverage_percent=round(cloud_coverage_percent, 1),
            zones_percent={
                "low (<0.3)": round(low_zone, 1),
                "medium (0.3-0.6)": round(medium_zone, 1),
                "high (>0.6)": round(high_zone, 1)
            },
            valid_pixels_percent=round(valid_pixels_percent, 1)
        )
    
    def process_field(
        self,
        red_band: np.ndarray,
        nir_band: np.ndarray,
        scl_band: np.ndarray,
        geometry: Geometry,
        output_dir: Path
    ) -> Dict[str, Any]:
        """
        Process field data: calculate NDVI, apply cloud mask, calculate statistics
        
        Args:
            red_band: Red band data (B04)
            nir_band: NIR band data (B08)
            scl_band: Scene Classification Layer
            geometry: Field geometry
            output_dir: Output directory for results
            
        Returns:
            Dictionary with NDVI array, statistics, and bounds
        """
        logger.info("Calculating NDVI...")
        ndvi = self.calculate_ndvi(red_band, nir_band)
        
        logger.info("Applying cloud mask...")
        ndvi_masked = self.apply_cloud_mask(ndvi, scl_band)
        
        logger.info("Calculating statistics...")
        stats = self.calculate_statistics(
            ndvi_masked,
            geometry,
            datetime.now().strftime("%Y-%m-%d")
        )
        
        # Calculate bounds from geometry
        geom = shape(geometry.dict())
        bounds = [
            [geom.bounds[1], geom.bounds[0]],  # [minLat, minLon]
            [geom.bounds[3], geom.bounds[2]]   # [maxLat, maxLon]
        ]
        
        return {
            "ndvi": ndvi_masked,
            "stats": stats,
            "bounds": bounds
        }
    
    def generate_visualization(
        self,
        data_array: np.ndarray,
        bounds: list,
        output_dir: Path,
        filename: str = "ndvi_visualization.png",
        index_name: str = "NDVI",
        vmin: float = -1.0,
        vmax: float = 1.0
    ) -> str:
        """
        Generate vegetation index visualization as PNG image
        
        Args:
            data_array: Index data array
            bounds: Geographic bounds
            output_dir: Output directory
            filename: Output filename
            index_name: Name of the index (NDVI, EVI, etc.)
            vmin: Minimum value for colormap
            vmax: Maximum value for colormap
            
        Returns:
            Filename of generated image
        """
        output_path = output_dir / filename
        
        # Get the appropriate colormap
        base_cmap = self.colormaps.get(index_name, self.ndvi_colormap)
        cmap = base_cmap.copy()
        
        # Calculate valid pixels percentage
        valid_pixels = np.sum(~np.isnan(data_array))
        total_pixels = data_array.size
        valid_percent = 100 * valid_pixels / total_pixels if total_pixels > 0 else 0
        
        try:
            # For very low valid pixels (< 5%), show masked areas as light gray instead of transparent
            # This ensures the image frame and valid pixels are visible
            if valid_percent < 5.0:
                # Light gray for masked areas - visible but not distracting
                cmap.set_bad((0.95, 0.95, 0.95, 0.3))  # Light gray, semi-transparent
                logger.info(f"Low valid pixels ({valid_percent:.2f}%) - using light gray for masked areas")
            else:
                # Normal case - transparent for masked areas
                cmap.set_bad((0.0, 0.0, 0.0, 0.0))  # Fully transparent
        except Exception:
            pass
        
        # Create figure with higher DPI for better pixel visibility
        # Match the actual data array size
        data_height, data_width = data_array.shape
        fig_dpi = 150
        fig_width = max(10, data_width / fig_dpi)
        fig_height = max(10, data_height / fig_dpi)
        fig, ax = plt.subplots(figsize=(fig_width, fig_height), dpi=fig_dpi)
        
        # Plot index with colormap (mask invalid values)
        # Use better normalization for visualization
        from matplotlib.colors import Normalize
        
        # Filter out NaN and extreme values
        valid_data = data_array[~np.isnan(data_array)]
        if len(valid_data) > 0:
            # Use data-driven normalization for better contrast
            # Use wider percentiles for better visibility of all pixels
            data_min = np.percentile(valid_data, 1)  # 1st percentile
            data_max = np.percentile(valid_data, 99)  # 99th percentile
            # But respect the index range and ensure some margin
            vmin_used = max(vmin, data_min * 0.95)  # Slightly extend range for visibility
            vmax_used = min(vmax, data_max * 1.05)  # Slightly extend range for visibility
            # Ensure minimum range for visibility
            if vmax_used - vmin_used < 0.1:
                center = (vmin_used + vmax_used) / 2
                vmin_used = center - 0.1
                vmax_used = center + 0.1
        else:
            vmin_used = vmin
            vmax_used = vmax
        
        norm = Normalize(vmin=vmin_used, vmax=vmax_used, clip=True)
        
        # Use nearest neighbor interpolation for pixel-perfect display when zoomed
        # This ensures individual pixels are visible
        # Use imshow with extent to ensure proper georeferencing
        # Calculate extent from bounds if available
        im = ax.imshow(
            np.ma.masked_invalid(data_array),
            cmap=cmap,
            norm=norm,
            interpolation='nearest',  # Nearest for pixel-perfect display
            aspect='equal',  # Maintain aspect ratio
            origin='upper'  # Top-left origin (standard for images)
        )
        
        # Log visualization stats
        valid_for_viz = ~np.isnan(data_array)
        valid_count = np.sum(valid_for_viz)
        logger.info(f"Visualization: {valid_count}/{data_array.size} pixels valid ({100*valid_count/data_array.size:.2f}%)")
        
        # Remove axes
        ax.axis('off')
        
        # Save figure without colorbar (for map overlay)
        # CRITICAL: If image is mostly transparent, use white background for masked areas
        # instead of fully transparent - this ensures image is visible on map
        valid_pixels = np.sum(~np.isnan(data_array))
        total_pixels = data_array.size
        valid_percent = 100 * valid_pixels / total_pixels
        
        # Always use transparent to preserve alpha channel
        # Masked areas are handled via cmap.set_bad()
        facecolor = 'none'
        transparent = True
        
        plt.savefig(
            output_path,
            bbox_inches='tight',
            pad_inches=0,
            dpi=fig_dpi,
            transparent=transparent,
            facecolor=facecolor,
            edgecolor='none'
        )
        plt.close()
        
        # Log image stats for debugging
        valid_pixels = np.sum(~np.isnan(data_array))
        total_pixels = data_array.size
        logger.info(f"Visualization saved to {output_path} - Valid pixels: {valid_pixels}/{total_pixels} ({100*valid_pixels/total_pixels:.1f}%)")
        return filename



