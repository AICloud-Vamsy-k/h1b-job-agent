import requests
from src.scrapers.base_scraper import BaseScraper

class AdzunaScraper(BaseScraper):
    """
    Adzuna Job Search API - FREE tier: 1000 calls/month
    Sign up: https://developer.adzuna.com/
    """
    
    def __init__(self, app_id, app_key):
        super().__init__()
        self.app_id = app_id
        self.app_key = app_key
        self.base_url = "https://api.adzuna.com/v1/api/jobs/us/search"
        
    def search_jobs(self, keywords, location, num_pages=3):
        """
        Search jobs using Adzuna API
        """
        jobs = []
        
        if not self.app_id or not self.app_key:
            print("  ⚠️  Adzuna API credentials not provided")
            return jobs
        
        results_per_page = 20
        
        for page in range(1, num_pages + 1):
            try:
                print(f"  📡 Fetching Adzuna page {page}...")
                
                url = f"{self.base_url}/{page}"
                params = {
                    'app_id': self.app_id,
                    'app_key': self.app_key,
                    'what': keywords,
                    'where': location,
                    'results_per_page': results_per_page,
                    'content-type': 'application/json'
                }
                
                response = requests.get(url, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    results = data.get('results', [])
                    
                    print(f"  ✅ Found {len(results)} jobs on page {page}")
                    
                    for job in results:
                        jobs.append({
                            'title': job.get('title', 'N/A'),
                            'company': job.get('company', {}).get('display_name', 'N/A'),
                            'location': job.get('location', {}).get('display_name', 'N/A'),
                            'description': job.get('description', ''),
                            'url': job.get('redirect_url', 'N/A'),
                            'source': 'Adzuna'
                        })
                else:
                    print(f"  ⚠️  Adzuna returned status {response.status_code}")
                    
                self.delay(1, 2)
                
            except Exception as e:
                print(f"  ❌ Error fetching Adzuna page {page}: {e}")
                continue
                
        return jobs
