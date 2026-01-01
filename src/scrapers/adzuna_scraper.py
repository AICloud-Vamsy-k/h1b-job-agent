import requests
from datetime import datetime
from typing import Optional, List

from src.scrapers.base_scraper import BaseScraper
from src.utils.date_parsing import parse_any_posted_date
from src.utils.job_filters import filter_by_date


class AdzunaScraper(BaseScraper):
    """
    Adzuna Job Search API - FREE tier.
    Sign up: https://developer.adzuna.com/
    """

    def __init__(self, app_id: str, app_key: str):
        super().__init__()
        self.app_id = app_id
        self.app_key = app_key
        self.base_url = "https://api.adzuna.com/v1/api/jobs/us/search"

    def search_jobs(
        self,
        keywords: str,
        location: str,
        num_pages: int = 3,
        posted_after: Optional[datetime] = None,
    ) -> List[dict]:
        """
        Search jobs using Adzuna API.

        Returns a list of dicts with keys:
        - title, company, location, description, url, source
        - posted_at (naive UTC datetime or None)
        - posted_at_raw (original string from API)
        """
        jobs: List[dict] = []

        if not self.app_id or not self.app_key:
            print("  ⚠️  Adzuna API credentials not provided")
            return jobs

        results_per_page = 20

        for page in range(1, num_pages + 1):
            try:
                print(f"  📡 Fetching Adzuna page {page}...")

                url = f"{self.base_url}/{page}"
                params = {
                    "app_id": self.app_id,
                    "app_key": self.app_key,
                    "what": keywords,
                    "where": location,
                    "results_per_page": results_per_page,
                    "content-type": "application/json",
                }

                response = requests.get(url, params=params, timeout=10)

                if response.status_code == 200:
                    data = response.json()
                    results = data.get("results", [])

                    print(f"  ✅ Found {len(results)} jobs on page {page}")

                    for job in results:
                        # Adzuna usually returns ISO date/time in "created"
                        raw_date = job.get("created") or ""
                        posted_at = parse_any_posted_date(raw_date)

                        jobs.append(
                            {
                                "title": job.get("title", "N/A"),
                                "company": job.get("company", {}).get(
                                    "display_name", "N/A"
                                ),
                                "location": job.get("location", {}).get(
                                    "display_name", "N/A"
                                ),
                                "description": job.get("description", ""),
                                "url": job.get("redirect_url", "N/A"),
                                "source": "Adzuna",
                                "posted_at": posted_at,
                                "posted_at_raw": raw_date,
                            }
                        )
                else:
                    print(f"  ⚠️  Adzuna returned status {response.status_code}")
                    print(f"  Response: {response.text[:200]}")

                self.delay(1, 2)

            except Exception as e:
                print(f"  ❌ Error fetching Adzuna page {page}: {e}")
                continue

        # Apply shared date filter
        jobs = filter_by_date(jobs, posted_after)
        return jobs
