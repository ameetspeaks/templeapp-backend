import os
import sys
import httpx

HF_BACKEND_URL = os.getenv("HF_BACKEND_URL", "").strip()
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "").strip()

def require_env():
    if not HF_BACKEND_URL or not ADMIN_API_KEY:
        print("Missing HF_BACKEND_URL or ADMIN_API_KEY")
        sys.exit(1)

def panchang_generate_range(year: int, city: str):
    url = f"{HF_BACKEND_URL}/panchang/generate-range"
    payload = {"start_date": f"{year}-01-01", "end_date": f"{year}-12-31", "city": city}
    with httpx.Client(timeout=60.0) as client:
        r = client.post(url, json=payload, headers={"X-API-Key": ADMIN_API_KEY, "Content-Type": "application/json"})
        print("Panchang generate-range:", r.status_code, r.text)

def muhurat_calculate_year(year: int, city: str, muhurat_type: str):
    url = f"{HF_BACKEND_URL}/muhurat/calculate"
    with httpx.Client(timeout=60.0) as client:
        for month in range(1, 13):
            payload = {"muhurat_type": muhurat_type, "month": month, "year": year, "city": city}
            r = client.post(url, json=payload, headers={"X-API-Key": ADMIN_API_KEY, "Content-Type": "application/json"})
            print(f"Muhurat calculate {month}/{year}:", r.status_code, r.text)

def main():
    require_env()
    year = 2026
    city = "Delhi"
    muhurat_type = "Vivah"
    panchang_generate_range(year, city)
    muhurat_calculate_year(year, city, muhurat_type)

if __name__ == "__main__":
    main()
