import requests
from datetime import datetime
from typing import Optional, List

from bs4 import BeautifulSoup

from src.scrapers.base_scraper import BaseScraper
from src.utils.date_parsing import parse_any_posted_date
from src.utils.job_filters import filter_by_date


class IndeedScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.base_url = "https://www.indeed.com"

    def search_jobs(
        self,
        keywords: str,
        location: str,
        num_pages: int = 3,
        posted_after: Optional[datetime] = None,
    ) -> List[dict]:
        """
        Scrape Indeed jobs.

        Returns list of dicts:
        [{title, company, location, description, url, source, posted_at, posted_at_raw}, ...]
        """
        jobs: List[dict] = []

        for page in range(num_pages):
            start = page * 10  # Indeed pagination uses 'start' parameter

            search_url = (
                f"{self.base_url}/jobs?"
                f"q={keywords.replace(' ', '+')}&"
                f"l={location.replace(' ', '+')}&"
                f"start={start}"
            )

            try:
                print(f"  📡 Fetching Indeed page {page + 1}...")
                response = requests.get(
                    search_url, headers=self.headers, timeout=10
                )

                if response.status_code != 200:
                    print(f"  ⚠️  Indeed returned status {response.status_code}")
                    continue

                soup = BeautifulSoup(response.content, "html.parser")

                # Find all job cards (Indeed's HTML structure)
                job_cards = soup.find_all("div", class_="job_seen_beacon")

                if not job_cards:
                    # Try alternative class names (Indeed changes them frequently)
                    job_cards = soup.find_all("td", class_="resultContent")

                print(
                    f"  ✅ Found {len(job_cards)} job cards on page {page + 1}"
                )

                for card in job_cards:
                    try:
                        # Title
                        title_elem = card.find("h2", class_="jobTitle")
                        if not title_elem:
                            title_elem = card.find("a", class_="jcs-JobTitle")
                        title = (
                            title_elem.get_text(strip=True)
                            if title_elem
                            else "N/A"
                        )

                        # Company
                        company_elem = card.find(
                            "span", {"data-testid": "company-name"}
                        )
                        if not company_elem:
                            company_elem = card.find(
                                "span", class_="companyName"
                            )
                        company = (
                            company_elem.get_text(strip=True)
                            if company_elem
                            else "N/A"
                        )

                        # Location
                        loc_elem = card.find(
                            "div", {"data-testid": "text-location"}
                        )
                        if not loc_elem:
                            loc_elem = card.find(
                                "div", class_="companyLocation"
                            )
                        job_location = (
                            loc_elem.get_text(strip=True)
                            if loc_elem
                            else "N/A"
                        )

                        # Job link
                        link_elem = title_elem.find("a") if title_elem else None
                        job_url = (
                            f"{self.base_url}{link_elem['href']}"
                            if link_elem and "href" in link_elem.attrs
                            else "N/A"
                        )

                        # Description snippet
                        desc_elem = card.find("div", class_="job-snippet")
                        if not desc_elem:
                            desc_elem = card.find(
                                "div", {"class": "jobCardShelfContainer"}
                            )
                        description = (
                            desc_elem.get_text(strip=True)
                            if desc_elem
                            else ""
                        )

                        # Posted date text – Indeed often puts it in a 'date' or 'date' span
                        date_elem = card.find("span", class_="date")
                        if not date_elem:
                            date_elem = card.find(
                                "span", {"data-testid": "myJobsStateDate"}
                            )
                        raw_date = (
                            date_elem.get_text(strip=True)
                            if date_elem
                            else ""
                        )
                        posted_at = parse_any_posted_date(raw_date)

                        jobs.append(
                            {
                                "title": title,
                                "company": company,
                                "location": job_location,
                                "description": description,
                                "url": job_url,
                                "source": "Indeed",
                                "posted_at": posted_at,
                                "posted_at_raw": raw_date,
                            }
                        )

                    except Exception as e:
                        print(f"  ⚠️  Error parsing job card: {e}")
                        continue

                self.delay()  # Polite delay between pages

            except Exception as e:
                print(f"  ❌ Error fetching Indeed page {page + 1}: {e}")
                continue

        # Apply shared date filter
        jobs = filter_by_date(jobs, posted_after)
        return jobs
