import time
import random
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional


class BaseScraper(ABC):
    """Base class for all job scrapers"""

    def __init__(self):
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }

    @abstractmethod
    def search_jobs(
        self,
        keywords: str,
        location: str,
        num_pages: int = 3,
        posted_after: Optional[datetime] = None,
    ):
        """Each scraper implements its own search logic"""
        raise NotImplementedError

    def delay(self, min_sec: float = 2, max_sec: float = 5):
        """Random delay to avoid rate limiting"""
        time.sleep(random.uniform(min_sec, max_sec))
