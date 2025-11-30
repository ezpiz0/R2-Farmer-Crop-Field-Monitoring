"""
Zone Analyzer Service
Handles field zoning based on NDVI clustering using K-Means algorithm
"""
import numpy as np
try:
    import rasterio
    from rasterio.features import shapes
    HAS_RASTERIO = True
except ImportError:
    HAS_RASTERIO = False
    print("WARNING: rasterio not available. Zone analysis features will be limited.")

from sklearn.cluster import KMeans
try:
    import geopandas as gpd
    HAS_GEOPANDAS = True
except ImportError:
    HAS_GEOPANDAS = False
    
from shapely.geometry import shape, mapping
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import json
import uuid

logger = logging.getLogger(__name__)


class ZoneAnalyzer:
    """
    Analyzes NDVI data and creates management zones using K-Means clustering
    """
    
    def __init__(self, results_dir: str = "results"):
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(exist_ok=True)
    
    def create_management_zones(
        self,
        ndvi_path: str,
        num_zones: int = 4,
        analysis_id: Optional[str] = None
    ) -> Dict:
        """
        Create management zones from NDVI raster data
        
        Args:
            ndvi_path: Path to NDVI GeoTIFF file
            num_zones: Number of zones to create (3-5 recommended)
            analysis_id: Optional analysis ID for tracking
            
        Returns:
            Dictionary with zone data, statistics, and file paths
        """
        try:
            logger.info(f"Starting zone creation with {num_zones} zones")
            
            # Step 1: Load NDVI data
            with rasterio.open(ndvi_path) as src:
                ndvi_data = src.read(1)
                profile = src.profile
                transform = src.transform
                crs = src.crs
            
            # Step 2: Prepare data for clustering
            valid_mask = ~np.isnan(ndvi_data) & (ndvi_data >= -1) & (ndvi_data <= 1)
            valid_ndvi = ndvi_data[valid_mask]
            
            if len(valid_ndvi) < num_zones:
                raise ValueError(f"Not enough valid pixels for {num_zones} zones")
            
            logger.info(f"Found {len(valid_ndvi)} valid NDVI pixels")
            
            # Step 3: K-Means clustering
            kmeans = KMeans(
                n_clusters=num_zones,
                random_state=42,
                n_init=10,
                max_iter=300
            )
            
            # Reshape for sklearn (expects 2D array)
            ndvi_reshaped = valid_ndvi.reshape(-1, 1)
            cluster_labels = kmeans.fit_predict(ndvi_reshaped)
            
            # Step 4: Sort clusters by NDVI values (ascending)
            # So Zone 1 = lowest NDVI, Zone N = highest NDVI
            cluster_centers = kmeans.cluster_centers_.flatten()
            sorted_indices = np.argsort(cluster_centers)
            
            # Create mapping from old labels to new sorted labels
            label_mapping = {old_label: new_label + 1 
                           for new_label, old_label in enumerate(sorted_indices)}
            
            # Apply mapping to cluster labels
            sorted_labels = np.array([label_mapping[label] for label in cluster_labels])
            
            # Step 5: Create zone raster
            zone_raster = np.full_like(ndvi_data, fill_value=-9999, dtype=np.int16)
            zone_raster[valid_mask] = sorted_labels
            
            # Step 6: Vectorize zones
            logger.info("Vectorizing zones...")
            features = []
            zone_stats = {}
            
            for zone_id in range(1, num_zones + 1):
                zone_mask = (zone_raster == zone_id).astype(np.uint8)
                
                # Calculate zone statistics
                zone_ndvi_values = ndvi_data[zone_raster == zone_id]
                if len(zone_ndvi_values) > 0:
                    zone_stats[zone_id] = {
                        'mean_ndvi': float(np.mean(zone_ndvi_values)),
                        'min_ndvi': float(np.min(zone_ndvi_values)),
                        'max_ndvi': float(np.max(zone_ndvi_values)),
                        'std_ndvi': float(np.std(zone_ndvi_values)),
                        'pixel_count': int(len(zone_ndvi_values))
                    }
                
                # Extract shapes for this zone
                zone_shapes = list(shapes(
                    zone_mask,
                    mask=zone_mask > 0,
                    transform=transform
                ))
                
                for geom, value in zone_shapes:
                    if value == 1:  # Only process zone pixels
                        features.append({
                            'type': 'Feature',
                            'properties': {
                                'zone_id': zone_id,
                                'mean_ndvi': zone_stats[zone_id]['mean_ndvi'],
                                'pixel_count': zone_stats[zone_id]['pixel_count'],
                                'zone_label': self._get_zone_label(zone_id, num_zones)
                            },
                            'geometry': geom
                        })
            
            logger.info(f"Created {len(features)} zone polygons")
            
            # Step 7: Create GeoDataFrame
            gdf = gpd.GeoDataFrame.from_features(features, crs=crs)
            
            # Dissolve polygons by zone_id to merge adjacent polygons
            logger.info("Dissolving adjacent polygons...")
            gdf_dissolved = gdf.dissolve(
                by='zone_id',
                aggfunc={
                    'mean_ndvi': 'first',
                    'pixel_count': 'sum',
                    'zone_label': 'first'
                }
            ).reset_index()
            
            # Step 8: Save to files
            unique_id = analysis_id or str(uuid.uuid4())
            geojson_path = self.results_dir / f"zones_{unique_id}.geojson"
            shapefile_path = self.results_dir / f"zones_{unique_id}"
            shapefile_zip = self.results_dir / f"zones_{unique_id}.zip"
            
            # Save GeoJSON
            gdf_dissolved.to_file(geojson_path, driver='GeoJSON')
            logger.info(f"Saved GeoJSON to {geojson_path}")
            
            # Save Shapefile (creates multiple files, need to zip them)
            gdf_dissolved.to_file(str(shapefile_path), driver='ESRI Shapefile')
            logger.info(f"Saved Shapefile to {shapefile_path}")
            
            # Zip shapefile components
            self._zip_shapefile(shapefile_path, shapefile_zip)
            
            # Step 9: Create GeoJSON for response
            zone_geojson = json.loads(gdf_dissolved.to_json())
            
            return {
                'status': 'success',
                'message': f'Field divided into {num_zones} management zones',
                'num_zones': num_zones,
                'zone_geojson': zone_geojson,
                'zone_statistics': zone_stats,
                'download_links': {
                    'geojson': f'/api/v1/downloads/zones_{unique_id}.geojson',
                    'shapefile': f'/api/v1/downloads/zones_{unique_id}.zip'
                },
                'file_paths': {
                    'geojson': str(geojson_path),
                    'shapefile_zip': str(shapefile_zip)
                }
            }
            
        except Exception as e:
            logger.error(f"Error creating management zones: {str(e)}", exc_info=True)
            raise
    
    def _get_zone_label(self, zone_id: int, num_zones: int) -> str:
        """
        Get descriptive label for zone based on its ID
        Zone 1 = lowest NDVI (weakest vegetation)
        Zone N = highest NDVI (strongest vegetation)
        """
        labels_3 = {1: "Слабая", 2: "Средняя", 3: "Сильная"}
        labels_4 = {1: "Очень слабая", 2: "Слабая", 3: "Средняя", 4: "Сильная"}
        labels_5 = {1: "Очень слабая", 2: "Слабая", 3: "Средняя", 4: "Сильная", 5: "Очень сильная"}
        
        if num_zones == 3:
            return labels_3.get(zone_id, f"Zone {zone_id}")
        elif num_zones == 4:
            return labels_4.get(zone_id, f"Zone {zone_id}")
        elif num_zones == 5:
            return labels_5.get(zone_id, f"Zone {zone_id}")
        else:
            return f"Zone {zone_id}"
    
    def _zip_shapefile(self, shapefile_path: Path, zip_path: Path):
        """
        Zip all shapefile components (.shp, .shx, .dbf, .prj, etc.)
        """
        import zipfile
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Find all files with the same base name
            for file in shapefile_path.parent.glob(f"{shapefile_path.name}.*"):
                zipf.write(file, file.name)
        
        logger.info(f"Created shapefile ZIP: {zip_path}")


# Singleton instance
zone_analyzer = ZoneAnalyzer()

