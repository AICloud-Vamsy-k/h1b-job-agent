"""
Test JSearch API connection
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")

print(f"API Key loaded: {RAPIDAPI_KEY[:20]}..." if RAPIDAPI_KEY else "❌ No API key found")

if RAPIDAPI_KEY:
    # Test JSearch API
    url = "https://jsearch.p.rapidapi.com/search"
    
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
    }
    
    querystring = {
        "query": "Python developer in New York",
        "page": "1",
        "num_pages": "1"
    }
    
    print("\n🔍 Testing JSearch API connection...")
    
    try:
        response = requests.get(url, headers=headers, params=querystring, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ SUCCESS! Found {len(data.get('data', []))} jobs")
            print(f"\nFirst job title: {data['data'][0]['job_title'] if data.get('data') else 'N/A'}")
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")
else:
    print("\n⚠️  Add RAPIDAPI_KEY to your .env file")
