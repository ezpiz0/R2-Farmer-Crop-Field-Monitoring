"""
Test image generation and display
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

print("\n" + "="*50)
print("TEST GENERATSII IZOBRAZHENIYA NDVI")
print("="*50 + "\n")

# Login
print("1. Vhod...")
try:
    login_response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": "testuser124411@test.com", "password": "testpassword123"},
        timeout=5
    )
    
    if login_response.status_code != 200:
        print(f"OSHIBKA vhoda: {login_response.status_code}")
        exit(1)
        
    token = login_response.json()["access_token"]
    print(f"OK Token poluchен\n")
    
except Exception as e:
    print(f"OSHIBKA: {e}\n")
    exit(1)

# Test analysis
print("2. Zapros analiza...")

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
    
    print(f"Status: {analysis_response.status_code}\n")
    
    if analysis_response.status_code == 200:
        result = analysis_response.json()
        print("=== OTVET OT SERVERA ===\n")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        print("\n=== ANALIZ OTVETA ===\n")
        
        if result.get('image_url'):
            image_url = result['image_url']
            print(f"OK image_url: {image_url}")
            
            # Check if image exists
            full_url = f"http://localhost:8000{image_url}"
            print(f"Proverka dostupnosti: {full_url}")
            
            img_response = requests.get(full_url, timeout=5)
            if img_response.status_code == 200:
                print(f"OK Izobrazhenie dostupno! Razmer: {len(img_response.content)} bytes")
            else:
                print(f"OSHIBKA Izobrazhenie nedostupno: {img_response.status_code}")
        else:
            print("OSHIBKA image_url otsutstvuet v otvete!")
            
        if result.get('stats'):
            print(f"\nStatistika:")
            print(f"  mean_ndvi: {result['stats'].get('mean_ndvi', 'N/A')}")
            print(f"  valid_pixels: {result['stats'].get('valid_pixels_count', 'N/A')}")
        else:
            print("\nOSHIBKA Statistika otsutstvuet!")
            
    else:
        print(f"OSHIBKA: {analysis_response.text}")
        
except Exception as e:
    print(f"OSHIBKA: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*50)
print("Test zavershen")
print("="*50 + "\n")

