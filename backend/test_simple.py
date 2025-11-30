import requests

BASE_URL = "http://localhost:8000/api/v1"

# Very simple password
test_data = {
    "email": "simple@test.com",
    "password": "pass123"
}

print("\nTest with simple password...")
print(f"Email: {test_data['email']}")
print(f"Password: {test_data['password']}")
print(f"Password length: {len(test_data['password'])} chars")
print(f"Password bytes: {len(test_data['password'].encode('utf-8'))} bytes\n")

try:
    response = requests.post(
        f"{BASE_URL}/auth/register",
        json=test_data,
        timeout=5
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}\n")
    
except Exception as e:
    print(f"Error: {e}\n")

