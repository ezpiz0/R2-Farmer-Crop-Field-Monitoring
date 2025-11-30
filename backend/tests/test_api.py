"""
Integration tests for API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


class TestHealthEndpoints:
    """Test health check endpoints"""
    
    def test_root(self):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"
        assert "version" in data
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestAnalyzeEndpoint:
    """Test /api/v1/analyze endpoint"""
    
    def test_analyze_valid_request(self):
        """Test analysis with valid geometry"""
        payload = {
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [37.6173, 55.7558],
                    [37.6273, 55.7558],
                    [37.6273, 55.7458],
                    [37.6173, 55.7458],
                    [37.6173, 55.7558]
                ]]
            },
            "date_range": ["2023-10-01", "2023-10-15"]
        }
        
        response = client.post("/api/v1/analyze", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert "image_url" in data
        assert "stats" in data
        assert "bounds" in data
        
        # Check stats structure
        stats = data["stats"]
        assert "area_ha" in stats
        assert "mean_ndvi" in stats
        assert "zones_percent" in stats
        assert "cloud_coverage_percent" in stats
    
    def test_analyze_invalid_geometry_type(self):
        """Test analysis with invalid geometry type"""
        payload = {
            "geometry": {
                "type": "Point",  # Should be Polygon
                "coordinates": [37.6173, 55.7558]
            },
            "date_range": ["2023-10-01", "2023-10-15"]
        }
        
        response = client.post("/api/v1/analyze", json=payload)
        assert response.status_code == 422  # Validation error
    
    def test_analyze_missing_geometry(self):
        """Test analysis without geometry"""
        payload = {
            "date_range": ["2023-10-01", "2023-10-15"]
        }
        
        response = client.post("/api/v1/analyze", json=payload)
        assert response.status_code == 422
    
    def test_analyze_invalid_coordinates(self):
        """Test analysis with too few coordinates"""
        payload = {
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [37.6173, 55.7558],
                    [37.6273, 55.7558]
                    # Less than 3 points
                ]]
            },
            "date_range": ["2023-10-01", "2023-10-15"]
        }
        
        response = client.post("/api/v1/analyze", json=payload)
        assert response.status_code == 422
    
    def test_analyze_with_default_dates(self):
        """Test analysis uses default dates if not provided"""
        payload = {
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [37.6173, 55.7558],
                    [37.6273, 55.7558],
                    [37.6273, 55.7458],
                    [37.6173, 55.7458],
                    [37.6173, 55.7558]
                ]]
            }
            # No date_range - should use defaults
        }
        
        response = client.post("/api/v1/analyze", json=payload)
        assert response.status_code == 200


class TestResponseValidation:
    """Test response data validation"""
    
    def test_ndvi_in_valid_range(self):
        """Test that returned NDVI is in valid range"""
        payload = {
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [37.6173, 55.7558],
                    [37.6273, 55.7558],
                    [37.6273, 55.7458],
                    [37.6173, 55.7458],
                    [37.6173, 55.7558]
                ]]
            },
            "date_range": ["2023-10-01", "2023-10-15"]
        }
        
        response = client.post("/api/v1/analyze", json=payload)
        data = response.json()
        
        mean_ndvi = data["stats"]["mean_ndvi"]
        assert -1 <= mean_ndvi <= 1
    
    def test_zones_sum_to_100(self):
        """Test that zone percentages sum to approximately 100%"""
        payload = {
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [37.6173, 55.7558],
                    [37.6273, 55.7558],
                    [37.6273, 55.7458],
                    [37.6173, 55.7458],
                    [37.6173, 55.7558]
                ]]
            },
            "date_range": ["2023-10-01", "2023-10-15"]
        }
        
        response = client.post("/api/v1/analyze", json=payload)
        data = response.json()
        
        zones = data["stats"]["zones_percent"]
        total = sum(zones.values())
        
        # Should sum to approximately 100 (allowing for rounding)
        assert 99 <= total <= 101


if __name__ == '__main__':
    pytest.main([__file__, '-v'])


