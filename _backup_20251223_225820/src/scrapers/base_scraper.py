import time
import random
from abc import ABC, abstractmethod

class BaseScraper(ABC):
    """Base class for all job scrapers"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
    @abstractmethod
    def search_jobs(self, keywords, location, num_pages=3):
        """Each scraper implements its own search logic"""
        pass
        
    def delay(self, min_sec=2, max_sec=5):
        """Random delay to avoid rate limiting"""
        time.sleep(random.uniform(min_sec, max_sec))
