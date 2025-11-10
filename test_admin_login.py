import requests
import json

# Test admin login
url = "http://localhost:8000/auth/login"
credentials = {
    "email": "admin@teloo.com",
    "password": "admin123"
}

print("Testing admin login...")
print(f"URL: {url}")
print(f"Credentials: {json.dumps(credentials, indent=2)}")

try:
    response = requests.post(url, json=credentials)
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        data = response.json()
        print("\n✅ Login successful!")
        print(f"User: {data['user']['nombre']}")
        print(f"Role: {data['user']['rol']}")
        print(f"Token: {data['access_token'][:50]}...")
    else:
        print("\n❌ Login failed!")
        
except Exception as e:
    print(f"\n❌ Error: {e}")
