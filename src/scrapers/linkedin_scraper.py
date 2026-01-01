import requests
from datetime import datetime
from typing import Optional, List

from src.scrapers.base_scraper import BaseScraper
from src.utils.date_parsing import parse_any_posted_date
from src.utils.job_filters import filter_by_date


class LinkedInScraper(BaseScraper):
    """
    LinkedIn scraper using RapidAPI:
    https://rapidapi.com/fantastic-jobs-fantastic-jobs-default/api/linkedin-job-search-api
    """

    def __init__(self, api_key: Optional[str] = None):
        super().__init__()
        self.api_key = api_key  # RapidAPI key for LinkedIn Job Search API

    def search_jobs(
        self,
        keywords: str,
        location: str,
        num_pages: int = 3,
        posted_after: Optional[datetime] = None,
    ) -> List[dict]:
        """
        Search LinkedIn jobs via RapidAPI.

        Returns list of dicts:
        [{title, company, location, description, url, source, posted_at, posted_at_raw}, ...]
        """
        jobs: List[dict] = []

        if not self.api_key:
            print("  ⚠️  LinkedIn API key not provided. Skipping LinkedIn scraping.")
            print("     Get a free key from: https://rapidapi.com/")
            return jobs

        url = "https://linkedin-job-search-api.p.rapidapi.com/search"

        headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": "linkedin-job-search-api.p.rapidapi.com",
        }

        for page in range(1, num_pages + 1):
            querystring = {
                "keywords": keywords,
                "location": location,
                "page": str(page),
            }

            try:
                print(f"  📡 Fetching LinkedIn page {page}...")
                response = requests.get(
                    url, headers=headers, params=querystring, timeout=15
                )

                if response.status_code != 200:
                    print(
                        f"  ⚠️  LinkedIn API returned status {response.status_code}"
                    )
                    continue

                data = response.json()

                jobs_list = data.get("jobs") or data.get("data") or []
                if jobs_list:
                    print(f"  ✅ Found {len(jobs_list)} jobs on page {page}")

                    for job in jobs_list:
                        # Different LinkedIn wrappers use slightly different keys for date
                        raw_date = (
                            job.get("postedAt")
                            or job.get("listedAt")
                            or job.get("time_ago")
                            or ""
                        )
                        posted_at = parse_any_posted_date(raw_date)

                        jobs.append(
                            {
                                "title": job.get("title", "N/A"),
                                "company": job.get("company", "N/A"),
                                "location": job.get("location", "N/A"),
                                "description": job.get("description", ""),
                                "url": job.get("url", "N/A"),
                                "source": "LinkedIn",
                                "posted_at": posted_at,
                                "posted_at_raw": raw_date,
                            }
                        )
                else:
                    print("  ⚠️  No jobs found in LinkedIn response")

                self.delay()

            except Exception as e:
                print(f"  ❌ Error fetching LinkedIn page {page}: {e}")
                continue

        # Apply shared date filter
        jobs = filter_by_date(jobs, posted_after)
        return jobs
