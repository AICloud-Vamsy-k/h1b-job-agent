"""
H1B Job Finder Pipeline
Contains both CLI and Streamlit-compatible versions
"""
import sys
import os
import pandas as pd
from datetime import datetime
from pathlib import Path

# Add project root to path - FIX FOR WINDOWS
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Now imports will work
from config.settings import (  # Updated from config.h1b_settings
    OPENAI_API_KEY,
    RAPIDAPI_KEY,
    ADZUNA_APP_ID,
    ADZUNA_APP_KEY,
    JOB_KEYWORDS,
    JOB_LOCATION,
    NUM_PAGES,
    JOBS_H1B_LIVE_CSV,
    H1B_REPORT_CSV,
    EMAIL_USER,
    EMAIL_PASSWORD,
    SMTP_HOST,
    SMTP_PORT,
    REPORT_RECIPIENT
)
from src.scrapers.scraper_manager import ScraperManager
from src.filters.h1b_filter import H1BFilter


def run_h1b_job_finder():
    """
    Main function: Scrape jobs, filter for H1B, save report
    CLI version - prints to console
    Used by: runner.py, command line execution
    """
    print("=" * 60)
    print("H1B JOB FINDER - Real-time Job Search")
    print("=" * 60)
    
    # Step 1: Scrape jobs from portals
    print(f"\n[1/4] Scraping jobs for: {JOB_KEYWORDS}")
    print(f"      Location: {JOB_LOCATION}")
    print(f"🔑 API Key loaded: {RAPIDAPI_KEY[:20]}..." if RAPIDAPI_KEY else "❌ No API key")
    
    scraper = ScraperManager(rapidapi_key=RAPIDAPI_KEY)
    raw_jobs = scraper.scrape_all(JOB_KEYWORDS, JOB_LOCATION, NUM_PAGES)
    
    print(f"✅ Found {len(raw_jobs)} total jobs")
    
    if not raw_jobs:
        print("❌ No jobs found. Check your scraper configuration.")
        return
    
    # Step 2: Filter for H1B eligibility
    print(f"\n[2/4] Filtering for H1B-friendly jobs...")
    
    h1b_filter = H1BFilter(OPENAI_API_KEY)
    h1b_jobs = h1b_filter.filter_jobs(raw_jobs, use_ai=True)
    
    print(f"✅ Found {len(h1b_jobs)} H1B-eligible jobs")
    
    # Step 3: Save to CSV
    print(f"\n[3/4] Saving results...")
    
    if h1b_jobs:
        df = pd.DataFrame(h1b_jobs)
        df['search_date'] = datetime.now().strftime('%Y-%m-%d %H:%M')
        
        # Save full data
        df.to_csv(JOBS_H1B_LIVE_CSV, index=False)
        print(f"✅ Saved to: {JOBS_H1B_LIVE_CSV}")
        
        # Save report (selected columns)
        report_df = df[['title', 'company', 'location', 'source', 
                        'h1b_eligible', 'eligibility_reason', 'url']]
        report_df.to_csv(H1B_REPORT_CSV, index=False)
        print(f"✅ Report saved to: {H1B_REPORT_CSV}")
    
    # Step 4: Send email (optional)
    if EMAIL_USER and EMAIL_PASSWORD and REPORT_RECIPIENT:
        print(f"\n[4/4] Sending email report to {REPORT_RECIPIENT}...")
        try:
            from src.utils.email_sender import EmailReporter
            
            reporter = EmailReporter(SMTP_HOST, SMTP_PORT, EMAIL_USER, EMAIL_PASSWORD)
            reporter.send_report(h1b_jobs, REPORT_RECIPIENT)
            print("✅ Email sent successfully")
        except Exception as e:
            print(f"⚠️  Email failed: {e}")
    else:
        print("\n[4/4] Email not configured (skipping)")
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total jobs scraped:     {len(raw_jobs)}")
    print(f"H1B-eligible jobs:      {len(h1b_jobs)}")
    if len(raw_jobs) > 0:
        print(f"Exclusion rate:         {((len(raw_jobs)-len(h1b_jobs))/len(raw_jobs)*100):.1f}%")
    print("=" * 60)


def run_h1b_job_finder_streamlit(keywords, location, num_pages=3, use_ai=True):
    """
    Streamlit-compatible version - returns results dict instead of printing
    Used by: streamlit_app.py
    
    Args:
        keywords: Job search keywords
        location: Job location  
        num_pages: Number of pages to scrape (default: 3)
        use_ai: Use AI filtering (default: True)
    
    Returns:
        dict: {
            'total_jobs': int,
            'h1b_jobs': list of dicts,
            'exclusion_rate': float
        }
    """
    from config.settings import OPENAI_API_KEY, RAPIDAPI_KEY
    from src.scrapers.scraper_manager import ScraperManager
    from src.filters.h1b_filter import H1BFilter
    
    # Step 1: Scrape jobs
    scraper = ScraperManager(rapidapi_key=RAPIDAPI_KEY)
    raw_jobs = scraper.scrape_all(keywords, location, num_pages)
    
    if not raw_jobs:
        return {
            'total_jobs': 0,
            'h1b_jobs': [],
            'exclusion_rate': 0
        }
    
    # Step 2: Filter for H1B eligibility
    h1b_filter = H1BFilter(OPENAI_API_KEY)
    h1b_jobs = h1b_filter.filter_jobs(raw_jobs, use_ai=use_ai)
    
    # Calculate exclusion rate
    exclusion_rate = ((len(raw_jobs) - len(h1b_jobs)) / len(raw_jobs) * 100) if raw_jobs else 0
    
    # Return structured results for Streamlit
    return {
        'total_jobs': len(raw_jobs),
        'h1b_jobs': h1b_jobs,
        'exclusion_rate': exclusion_rate
    }


if __name__ == "__main__":
    run_h1b_job_finder()
