"""Test Serper API directly."""
from dotenv import load_dotenv
load_dotenv()

from config import config
import requests

print(f"SERPER_API_KEY: {config.SERPER_API_KEY[:10] if config.SERPER_API_KEY else 'NOT SET'}...")

query = "Flask vulnerability CVE"
response = requests.post(
    "https://google.serper.dev/search",
    json={"q": query, "num": 5},
    headers={"X-API-KEY": config.SERPER_API_KEY, "Content-Type": "application/json"},
    timeout=15
)

print(f"Status: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    results = data.get("organic", [])
    print(f"Results: {len(results)}")
    for r in results[:5]:
        print(f"\n  Title: {r.get('title', '')[:60]}")
        print(f"  URL: {r.get('link', '')[:80]}")
else:
    print(f"Error: {response.text[:200]}")
