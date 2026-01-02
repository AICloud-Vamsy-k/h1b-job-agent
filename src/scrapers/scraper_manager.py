"""
Orchestrates all job scrapers
"""

from datetime import datetime
from typing import Optional, List

from src.scrapers.jsearch_scraper import JSearchScraper
from src.scrapers.indeed_scraper import IndeedScraper
from src.scrapers.adzuna_scraper import AdzunaScraper


class ScraperManager:
    def __init__(
        self,
        rapidapi_key: Optional[str] = None,
        adzuna_app_id: Optional[str] = None,
        adzuna_app_key: Optional[str] = None,
    ):
        # JSearch via RapidAPI
        self.jsearch = JSearchScraper(rapidapi_key) if rapidapi_key else None
        # Indeed HTML scraper (no key needed)
        self.indeed = IndeedScraper()
        # Adzuna API
        self.adzuna = (
            AdzunaScraper(adzuna_app_id, adzuna_app_key)
            if adzuna_app_id and adzuna_app_key
            else None
        )

    def scrape_all(
        self,
        keywords: str,
        location: str,
        num_pages: int = 3,
        posted_after: Optional[datetime] = None,
        use_jsearch: bool = True,
        use_indeed: bool = True,
        use_adzuna: bool = True,
    ) -> List[dict]:
        """
        Scrape from all available sources.
        """
        all_jobs: List[dict] = []

        # JSearch
        if self.jsearch and use_jsearch:
            print(f"\n🔍 Scraping JSearch for: '{keywords}' in '{location}'")
            jsearch_jobs = self.jsearch.search_jobs(
                keywords, location, num_pages, posted_after=posted_after
            )
            all_jobs.extend(jsearch_jobs)
            print(f"✅ Total from JSearch: {len(jsearch_jobs)} jobs\n")
        elif not self.jsearch:
            print("⚠️ No RapidAPI key provided, skipping JSearch")

        # Indeed
        if self.indeed and use_indeed:
            print(f"\n🔍 Scraping Indeed for: '{keywords}' in '{location}'")
            indeed_jobs = self.indeed.search_jobs(
                keywords, location, num_pages, posted_after=posted_after
            )
            all_jobs.extend(indeed_jobs)
            print(f"✅ Total from Indeed: {len(indeed_jobs)} jobs\n")

        # Adzuna
        if self.adzuna and use_adzuna:
            print(f"\n🔍 Scraping Adzuna for: '{keywords}' in '{location}'")
            adzuna_jobs = self.adzuna.search_jobs(
                keywords, location, num_pages, posted_after=posted_after
            )
            all_jobs.extend(adzuna_jobs)
            print(f"✅ Total from Adzuna: {len(adzuna_jobs)} jobs\n")

        print(f"📊 Combined total: {len(all_jobs)} jobs")
        return all_jobs
