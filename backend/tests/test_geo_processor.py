"""
Unit tests for GeoProcessor
"""
import pytest
import numpy as np
from services.geo_processor import GeoProcessor


class TestGeoProcessor:
    """Test cases for GeoProcessor class"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.processor = GeoProcessor()
    
    def test_calculate_ndvi_normal(self):
        """Test NDVI calculation with normal values"""
        # Create test data
        red = np.array([[100, 200], [300, 400]], dtype='float32')
        nir = np.array([[400, 500], [600, 700]], dtype='float32')
        
        # Calculate NDVI
        ndvi = self.processor.calculate_ndvi(red, nir)
        
        # Check shape
        assert ndvi.shape == red.shape
        
        # Check values are in valid range [-1, 1]
        assert np.all(ndvi >= -1)
        assert np.all(ndvi <= 1)
        
        # Check specific calculation
        expected_00 = (400 - 100) / (400 + 100)  # 0.6
        assert np.isclose(ndvi[0, 0], expected_00)
    
    def test_calculate_ndvi_zero_division(self):
        """Test NDVI calculation handles zero division"""
        # Both bands zero
        red = np.array([[0, 100], [0, 0]], dtype='float32')
        nir = np.array([[0, 200], [0, 0]], dtype='float32')
        
        ndvi = self.processor.calculate_ndvi(red, nir)
        
        # Should not raise error
        assert ndvi.shape == red.shape
        
        # Zero division should result in 0
        assert ndvi[0, 0] == 0
        assert ndvi[1, 1] == 0
    
    def test_apply_cloud_mask(self):
        """Test cloud masking functionality"""
        # Create test data
        data = np.ones((10, 10), dtype='float32')
        scl = np.ones((10, 10), dtype='uint8') * 4  # All vegetation
        
        # Add clouds
        scl[2:4, 2:4] = 8  # Cloud medium probability
        scl[6:8, 6:8] = 9  # Cloud high probability
        
        # Apply mask
        masked = self.processor.apply_cloud_mask(data, scl)
        
        # Check that cloud pixels are NaN
        assert np.isnan(masked[2, 2])
        assert np.isnan(masked[3, 3])
        assert np.isnan(masked[6, 6])
        assert np.isnan(masked[7, 7])
        
        # Check that non-cloud pixels are unchanged
        assert masked[0, 0] == 1
        assert masked[9, 9] == 1
    
    def test_apply_cloud_mask_with_shadows(self):
        """Test cloud masking includes shadow detection"""
        data = np.ones((10, 10), dtype='float32')
        scl = np.ones((10, 10), dtype='uint8') * 4
        
        # Add shadows
        scl[1:3, 1:3] = 3  # Cloud shadow
        
        masked = self.processor.apply_cloud_mask(data, scl)
        
        # Shadows should be masked
        assert np.isnan(masked[1, 1])
        assert np.isnan(masked[2, 2])
    
    def test_ndvi_range_clipping(self):
        """Test NDVI values are clipped to [-1, 1]"""
        # Extreme values
        red = np.array([[1, 1000]], dtype='float32')
        nir = np.array([[10000, 1]], dtype='float32')
        
        ndvi = self.processor.calculate_ndvi(red, nir)
        
        # All values should be in valid range
        assert np.all(ndvi >= -1)
        assert np.all(ndvi <= 1)


class TestNDVIFormula:
    """Test NDVI formula correctness"""
    
    def test_healthy_vegetation(self):
        """Test NDVI for typical healthy vegetation"""
        processor = GeoProcessor()
        
        # Healthy vegetation: high NIR, low Red
        red = np.array([[800]], dtype='float32')
        nir = np.array([[4000]], dtype='float32')
        
        ndvi = processor.calculate_ndvi(red, nir)
        
        # Should be high positive value (> 0.6)
        assert ndvi[0, 0] > 0.6
    
    def test_bare_soil(self):
        """Test NDVI for bare soil"""
        processor = GeoProcessor()
        
        # Bare soil: similar NIR and Red
        red = np.array([[2000]], dtype='float32')
        nir = np.array([[2500]], dtype='float32')
        
        ndvi = processor.calculate_ndvi(red, nir)
        
        # Should be low value (< 0.3)
        assert ndvi[0, 0] < 0.3
    
    def test_water(self):
        """Test NDVI for water bodies"""
        processor = GeoProcessor()
        
        # Water: higher Red than NIR
        red = np.array([[1000]], dtype='float32')
        nir = np.array([[200]], dtype='float32')
        
        ndvi = processor.calculate_ndvi(red, nir)
        
        # Should be negative
        assert ndvi[0, 0] < 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])


