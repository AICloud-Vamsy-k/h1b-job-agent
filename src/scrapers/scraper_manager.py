"""
Orchestrates all job scrapers
"""
from src.scrapers.jsearch_scraper import JSearchScraper

class ScraperManager:
    
    def __init__(self, rapidapi_key=None):
        self.jsearch = JSearchScraper(rapidapi_key) if rapidapi_key else None
        
    def scrape_all(self, keywords, location, num_pages=3):
        """
        Scrape from all available sources
        """
        all_jobs = []
        
        # Try JSearch (FREE API via RapidAPI)
        if self.jsearch:
            print(f"\n🔍 Scraping JSearch for: '{keywords}' in '{location}'")
            jsearch_jobs = self.jsearch.search_jobs(keywords, location, num_pages)
            all_jobs.extend(jsearch_jobs)
            print(f"✅ Total from JSearch: {len(jsearch_jobs)} jobs\n")
        else:
            print("⚠️  No RapidAPI key provided, skipping JSearch")
        
        print(f"📊 Combined total: {len(all_jobs)} jobs")
        return all_jobs
