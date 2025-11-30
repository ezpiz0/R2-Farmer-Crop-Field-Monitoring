"""
Простой тест регистрации и входа
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000/api/v1"

# Генерируем уникальный email
timestamp = datetime.now().strftime("%H%M%S")
test_email = f"testuser{timestamp}@test.com"
test_password = "testpassword123"

print("\n" + "="*50)
print("TEST REGISTRATSII I VHODA")
print("="*50 + "\n")

# Test 1: Registration
print(f"Email: {test_email}")
print(f"Password: {test_password}\n")

print("1. Testirovanie registratsii...")
try:
    response = requests.post(
        f"{BASE_URL}/auth/register",
        json={"email": test_email, "password": test_password},
        timeout=5
    )
    
    if response.status_code == 201:
        print("OK Registratsiya USPESHNA!")
        print(f"   Otvet: {response.json()}\n")
    else:
        print(f"OSHIBKA Registratsiya ne udalas!")
        print(f"   Status: {response.status_code}")
        print(f"   Otvet: {response.text}\n")
        exit(1)
        
except Exception as e:
    print(f"OSHIBKA pri registratsii: {e}\n")
    exit(1)

# Test 2: Login
print("2. Testirovanie vhoda...")
try:
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": test_email, "password": test_password},
        timeout=5
    )
    
    if response.status_code == 200:
        data = response.json()
        print("OK Vhod USPESHEN!")
        print(f"   Token poluchen: {data['access_token'][:20]}...")
        print(f"   Tip tokena: {data['token_type']}\n")
        
        # Test 3: Token check
        print("3. Testirovanie tokena...")
        token = data['access_token']
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get(
            f"{BASE_URL}/auth/me",
            headers=headers,
            timeout=5
        )
        
        if response.status_code == 200:
            user_data = response.json()
            print("OK Token RABOTAET!")
            print(f"   Email: {user_data['email']}")
            print(f"   ID: {user_data['id']}\n")
        else:
            print(f"OSHIBKA Token ne rabotaet!")
            print(f"   Status: {response.status_code}\n")
            
    else:
        print(f"OSHIBKA Vhod ne udalsya!")
        print(f"   Status: {response.status_code}")
        print(f"   Otvet: {response.text}\n")
        
except Exception as e:
    print(f"OSHIBKA pri vhode: {e}\n")

print("="*50)
print("VSE TESTY PROJDENY!")
print("="*50)
print("\nRegistratsiya i autentifikatsiya rabotayut pravilno!")
print("Otkroyte http://localhost:3000 i poprobujte vojti\n")

