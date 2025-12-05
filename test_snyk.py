"""Test Snyk and Serper APIs."""
from dotenv import load_dotenv
load_dotenv()

from config import config
import requests

print("=" * 60)
print("Testing Snyk API")
print("=" * 60)

if config.SNYK_TOKEN:
    print(f"SNYK_TOKEN: {config.SNYK_TOKEN[:10]}...")
    
    # Test with Flask package
    url = "https://api.snyk.io/v1/test/pip/flask"
    headers = {
        "Authorization": f"token {config.SNYK_TOKEN}",
        "Content-Type": "application/json"
    }
    
    response = requests.get(url, headers=headers, timeout=15)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"OK: {data.get('ok')}")
        issues = data.get("issues", {}).get("vulnerabilities", [])
        print(f"Vulnerabilities: {len(issues)}")
        for issue in issues[:3]:
            print(f"  - {issue.get('severity')}: {issue.get('title', '')[:50]}")
    else:
        print(f"Error: {response.text[:200]}")
else:
    print("SNYK_TOKEN not set")

print("\n" + "=" * 60)
print("Testing Serper API")
print("=" * 60)

if config.SERPER_API_KEY:
    print(f"SERPER_API_KEY: {config.SERPER_API_KEY[:10]}...")
    
    response = requests.post(
        "https://google.serper.dev/search",
        json={"q": "Flask vulnerability CVE", "num": 3},
        headers={"X-API-KEY": config.SERPER_API_KEY},
        timeout=10
    )
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        results = response.json().get("organic", [])
        print(f"Results: {len(results)}")
        for r in results[:3]:
            print(f"  - {r.get('title', '')[:50]}")
    else:
        print(f"Error: {response.text[:100]}")
else:
    print("SERPER_API_KEY not set")
