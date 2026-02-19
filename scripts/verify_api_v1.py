import requests
import sys
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_endpoint(method, url, params=None, json_body=None, expected_status=200):
    try:
        print(f"Testing {method} {url}...")
        if method == "GET":
            response = requests.get(f"{BASE_URL}{url}", params=params)
        elif method == "POST":
            response = requests.post(f"{BASE_URL}{url}", json=json_body)
        elif method == "PUT":
            response = requests.put(f"{BASE_URL}{url}", json=json_body)
        
        if response.status_code != expected_status:
            print(f"❌ Failed: Expected {expected_status}, got {response.status_code}")
            print(response.text)
            return False
            
        try:
            data = response.json()
            if data.get("status") != "ok" and "status" in data:
                 print(f"❌ Failed: Parsed status is {data.get('status')}")
                 print(data)
                 return False
            print("✅ Passed")
            # print(json.dumps(data, indent=2))
            return True
        except:
            print("❌ Failed: Could not parse JSON")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def verify_all():
    print("--- Starting V1 API Verification ---")
    
    # 1. Health
    if not test_endpoint("GET", "/health"):
        print("Health check failed. specific server might not be running.")
        # Proceed anyway to test other headers/routes if partially up
    
    # 2. Config
    test_endpoint("GET", "/v1/config/app")
    
    # 3. Home
    test_endpoint("GET", "/v1/home/summary")
    
    # 4. Temples
    test_endpoint("GET", "/v1/temples", params={"q": "Ganesh"})
    # Assuming at least one temple exists or empty list is OK
    
    # 5. Aartis
    test_endpoint("GET", "/v1/aartis")
    
    # 6. Bhajans
    test_endpoint("GET", "/v1/bhajans")
    
    # 7. Panchang
    today = datetime.now().strftime("%Y-%m-%d")
    test_endpoint("GET", "/v1/panchang/daily", params={"date": today, "city": "Delhi"})
    
    # 8. Festivals
    test_endpoint("GET", "/v1/festivals", params={"start": today, "end": today})
    
    # 9. Muhurat
    test_endpoint("GET", "/v1/muhurat", params={"city": "Delhi"})
    
    # 10. Puja
    test_endpoint("GET", "/v1/puja/guides")
    
    # 11. Search
    test_endpoint("GET", "/v1/search/suggestions", params={"q": "Gan"})
    test_endpoint("GET", "/v1/search", params={"q": "Ganesh"})
    
    # 12. Auth (Mock)
    test_endpoint("POST", "/v1/auth/login", json_body={"provider": "google", "token": "xyz"})
    
    print("--- Verification Complete ---")

if __name__ == "__main__":
    verify_all()
