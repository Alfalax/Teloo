import requests
import json

# First login
login_url = "http://localhost:8000/auth/login"
login_data = {
    "email": "admin@teloo.com",
    "password": "admin123"
}

print("=== LOGIN ===")
login_response = requests.post(login_url, json=login_data)
print(f"Login Status: {login_response.status_code}")

if login_response.status_code == 200:
    token = login_response.json()["access_token"]
    print(f"Token obtained: {token[:50]}...")
    
    # Now test solicitudes endpoint
    print("\n=== GET SOLICITUDES ===")
    url = "http://localhost:8000/v1/solicitudes"
    params = {"page": 1, "page_size": 25}
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(url, params=params, headers=headers)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        else:
            print(f"Error Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
else:
    print(f"Login failed: {login_response.text}")
