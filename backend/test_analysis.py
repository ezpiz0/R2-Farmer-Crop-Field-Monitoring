"""
Test analysis endpoint to verify shape import fix
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

# First, login with existing user
print("\n" + "="*50)
print("TEST ANALIZA POLYA")
print("="*50 + "\n")

# Login
print("1. Vhod v sistemu...")
try:
    login_response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": "testuser124411@test.com", "password": "testpassword123"},
        timeout=5
    )
    
    if login_response.status_code == 200:
        token = login_response.json()["access_token"]
        print("OK Vhod uspeshen!")
        print(f"   Token: {token[:30]}...\n")
    else:
        print(f"OSHIBKA: {login_response.status_code}")
        print(f"   {login_response.text}\n")
        exit(1)
        
except Exception as e:
    print(f"OSHIBKA: {e}\n")
    exit(1)

# Test analysis with simple polygon
print("2. Test analiza polya...")

test_geometry = {
    "type": "Polygon",
    "coordinates": [[
        [30.5, 50.5],
        [30.6, 50.5],
        [30.6, 50.6],
        [30.5, 50.6],
        [30.5, 50.5]
    ]]
}

headers = {"Authorization": f"Bearer {token}"}

try:
    analysis_response = requests.post(
        f"{BASE_URL}/analyze",
        json={
            "geometry": test_geometry,
            "start_date": "2024-01-01",
            "end_date": "2024-01-31",
            "index_type": "NDVI"
        },
        headers=headers,
        timeout=30
    )
    
    print(f"Status: {analysis_response.status_code}")
    
    if analysis_response.status_code == 200:
        result = analysis_response.json()
        print("\nOK Analiz zavershyon uspeshno!")
        print(f"   Statistics: {result.get('statistics', {})}")
        print(f"   Image URL: {result.get('ndvi_image_url', 'N/A')}")
        print("\nOSHIBKA 'shape is not defined' ISPRAVLENA!\n")
    else:
        print(f"\nOSHIBKA: {analysis_response.text}\n")
        
except Exception as e:
    print(f"\nOSHIBKA pri analize: {e}\n")

print("="*50)
print("Test zavershen")
print("="*50 + "\n")

