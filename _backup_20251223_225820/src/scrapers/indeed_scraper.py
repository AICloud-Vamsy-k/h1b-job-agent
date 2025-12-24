import requests
from bs4 import BeautifulSoup
from src.scrapers.base_scraper import BaseScraper  # ✅ Fixed import

class IndeedScraper(BaseScraper):
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://www.indeed.com"
        
    def search_jobs(self, keywords, location, num_pages=3):
        """
        Scrape Indeed jobs
        Returns list of dicts: [{title, company, location, description, url, source}, ...]
        """
        jobs = []
        
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
                response = requests.get(search_url, headers=self.headers, timeout=10)
                
                if response.status_code != 200:
                    print(f"  ⚠️  Indeed returned status {response.status_code}")
                    continue
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find all job cards (Indeed's HTML structure)
                job_cards = soup.find_all('div', class_='job_seen_beacon')
                
                if not job_cards:
                    # Try alternative class names (Indeed changes them frequently)
                    job_cards = soup.find_all('td', class_='resultContent')
                
                print(f"  ✅ Found {len(job_cards)} job cards on page {page + 1}")
                
                for card in job_cards:
                    try:
                        # Extract job details (multiple attempts for different HTML structures)
                        title_elem = card.find('h2', class_='jobTitle')
                        if not title_elem:
                            title_elem = card.find('a', class_='jcs-JobTitle')
                        title = title_elem.get_text(strip=True) if title_elem else "N/A"
                        
                        company_elem = card.find('span', {'data-testid': 'company-name'})
                        if not company_elem:
                            company_elem = card.find('span', class_='companyName')
                        company = company_elem.get_text(strip=True) if company_elem else "N/A"
                        
                        loc_elem = card.find('div', {'data-testid': 'text-location'})
                        if not loc_elem:
                            loc_elem = card.find('div', class_='companyLocation')
                        job_location = loc_elem.get_text(strip=True) if loc_elem else "N/A"
                        
                        # Get job link
                        link_elem = title_elem.find('a') if title_elem else None
                        job_url = f"{self.base_url}{link_elem['href']}" if link_elem and 'href' in link_elem.attrs else "N/A"
                        
                        # Get snippet/description
                        desc_elem = card.find('div', class_='job-snippet')
                        if not desc_elem:
                            desc_elem = card.find('div', {'class': 'jobCardShelfContainer'})
                        description = desc_elem.get_text(strip=True) if desc_elem else ""
                        
                        jobs.append({
                            'title': title,
                            'company': company,
                            'location': job_location,
                            'description': description,
                            'url': job_url,
                            'source': 'Indeed'
                        })
                        
                    except Exception as e:
                        print(f"  ⚠️  Error parsing job card: {e}")
                        continue
                        
                self.delay()  # Polite delay between pages
                
            except Exception as e:
                print(f"  ❌ Error fetching Indeed page {page + 1}: {e}")
                continue
                
        return jobs
