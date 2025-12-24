import requests
from src.scrapers.base_scraper import BaseScraper

class JSearchScraper(BaseScraper):
    """
    JSearch API via RapidAPI - FREE tier: 1000 calls/month
    Get key: https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch
    """
    
    def __init__(self, rapidapi_key):
        super().__init__()
        self.rapidapi_key = rapidapi_key
        
    def search_jobs(self, keywords, location, num_pages=3):
        """
        Search jobs using JSearch API
        """
        jobs = []
        
        if not self.rapidapi_key:
            print("  ⚠️  RapidAPI key not provided for JSearch")
            return jobs
        
        url = "https://jsearch.p.rapidapi.com/search"
        headers = {
            "X-RapidAPI-Key": self.rapidapi_key,
            "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
        }
        
        for page in range(1, num_pages + 1):
            try:
                print(f"  📡 Fetching JSearch page {page}...")
                
                querystring = {
                    "query": f"{keywords} in {location}",
                    "page": str(page),
                    "num_pages": "1"
                }
                
                response = requests.get(url, headers=headers, params=querystring, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    results = data.get('data', [])
                    
                    print(f"  ✅ Found {len(results)} jobs on page {page}")
                    
                    for job in results:
                        jobs.append({
                            'title': job.get('job_title', 'N/A'),
                            'company': job.get('employer_name', 'N/A'),
                            'location': f"{job.get('job_city', 'N/A')}, {job.get('job_state', '')}",
                            'description': job.get('job_description', ''),
                            'url': job.get('job_apply_link', 'N/A'),
                            'source': 'JSearch'
                        })
                else:
                    print(f"  ⚠️  JSearch returned status {response.status_code}")
                    print(f"  Response: {response.text[:200]}")
                    
                self.delay(1, 2)
                
            except Exception as e:
                print(f"  ❌ Error fetching JSearch page {page}: {e}")
                continue
                
        return jobs
