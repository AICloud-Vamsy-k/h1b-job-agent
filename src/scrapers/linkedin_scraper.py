import requests
from src.scrapers.base_scraper import BaseScraper  # ✅ Fixed import

class LinkedInScraper(BaseScraper):
    
    def __init__(self, api_key=None):
        super().__init__()
        self.api_key = api_key  # RapidAPI key for LinkedIn Job Search API
        
    def search_jobs(self, keywords, location, num_pages=3):
        """
        LinkedIn scraper using RapidAPI
        Get free API key from: https://rapidapi.com/fantastic-jobs-fantastic-jobs-default/api/linkedin-job-search-api
        """
        jobs = []
        
        if not self.api_key:
            print("  ⚠️  LinkedIn API key not provided. Skipping LinkedIn scraping.")
            print("     Get a free key from: https://rapidapi.com/")
            return jobs
            
        # Using RapidAPI LinkedIn Job Search API
        url = "https://linkedin-job-search-api.p.rapidapi.com/search"
        
        headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": "linkedin-job-search-api.p.rapidapi.com"
        }
        
        for page in range(1, num_pages + 1):
            querystring = {
                "keywords": keywords,
                "location": location,
                "page": str(page)
            }
            
            try:
                print(f"  📡 Fetching LinkedIn page {page}...")
                response = requests.get(url, headers=headers, params=querystring, timeout=15)
                
                if response.status_code != 200:
                    print(f"  ⚠️  LinkedIn API returned status {response.status_code}")
                    continue
                
                data = response.json()
                
                if 'jobs' in data:
                    print(f"  ✅ Found {len(data['jobs'])} jobs on page {page}")
                    
                    for job in data['jobs']:
                        jobs.append({
                            'title': job.get('title', 'N/A'),
                            'company': job.get('company', 'N/A'),
                            'location': job.get('location', 'N/A'),
                            'description': job.get('description', ''),
                            'url': job.get('url', 'N/A'),
                            'source': 'LinkedIn'
                        })
                else:
                    print(f"  ⚠️  No jobs found in response")
                        
                self.delay()
                
            except Exception as e:
                print(f"  ❌ Error fetching LinkedIn page {page}: {e}")
                continue
                
        return jobs
