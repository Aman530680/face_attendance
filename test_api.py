import requests
import json

def test_api():
    base_url = "http://localhost:5000"
    
    endpoints = [
        "/api/status",
        "/api/attendance/settings"
    ]
    
    for endpoint in endpoints:
        try:
            print(f"Testing {endpoint}...")
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                print(f"Response: {response.json()}")
            else:
                print(f"Error: {response.text}")
        except requests.exceptions.RequestException as e:
            print(f"Connection error: {e}")
        print("-" * 50)

if __name__ == "__main__":
    test_api()