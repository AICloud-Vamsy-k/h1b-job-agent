"""
H1B Job Finder Pipeline (RAG-Enabled)

Contains both CLI and Streamlit-compatible versions.
Includes job matching, gap analysis, and tailored resume generation.
"""

import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

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
    REPORT_RECIPIENT,
)

from src.scrapers.scraper_manager import ScraperManager
from src.filters.h1b_filter import H1BFilter
from src.rag.profile_rag import build_or_refresh_profile_index  # RAG support
from src.crews.job_match_crew import evaluate_job  # Job matching
from src.crews.resume_builder_crew import generate_tailored_resume  # Tailored resumes
from src.crews.gap_analyzer_crew import analyze_gaps_for_learning  # Gap analysis


def _resolve_date_filter(label: str):
    """Map UI label to a cutoff datetime (local now-based)."""
    now = datetime.now()
    if label == "Last 24 hours":
        return now - timedelta(hours=24)
    if label == "Last 7 days":
        return now - timedelta(days=7)
    if label == "Last 30 days":
        return now - timedelta(days=30)
    return None


def run_h1b_job_finder(generate_resumes: bool = False, match_threshold: float = 0.65):
    """
    Main function: Scrape jobs, filter for H1B, match against resume, generate reports.
    CLI version - prints to console.
    Used by: runner.py, command line execution.

    Args:
        generate_resumes: Generate tailored resumes for top matches.
        match_threshold: Minimum match score for resume generation.
    """
    print("=" * 70)
    print("🚀 H1B JOB FINDER - Real-time Job Search (RAG-Enabled)")
    print("=" * 70)

    # STEP 0: Build RAG index from uploaded resume
    print("\n[0/5] Building RAG index from your latest uploaded resume...")
    try:
        build_or_refresh_profile_index()
        print("✅ RAG index ready (full resume chunked & embedded)")
    except Exception as e:
        print(f"⚠️ RAG setup warning: {e}")
        print("💡 Upload resume via Streamlit first for best results")

    # Step 1: Scrape jobs from portals
    print(f"\n[1/5] Scraping jobs for: {JOB_KEYWORDS}")
    print(f"      Location: {JOB_LOCATION}")
    print(f"🔑 API Key loaded: {RAPIDAPI_KEY[:20]}..." if RAPIDAPI_KEY else "❌ No API key")

    scraper = ScraperManager(
        rapidapi_key=RAPIDAPI_KEY,
        adzuna_app_id=ADZUNA_APP_ID,
        adzuna_app_key=ADZUNA_APP_KEY,
    )


    # For CLI we keep a single keyword string and no date filter
    raw_jobs = scraper.scrape_all(
        JOB_KEYWORDS,
        JOB_LOCATION,
        NUM_PAGES,
        posted_after=None,
    )

    print(f"✅ Found {len(raw_jobs)} total jobs")

    if not raw_jobs:
        print("❌ No jobs found. Check your scraper configuration.")
        return

    # Step 2: Filter for H1B eligibility
    print(f"\n[2/5] Filtering for H1B-friendly jobs...")

    h1b_filter = H1BFilter(OPENAI_API_KEY)
    h1b_jobs = h1b_filter.filter_jobs(raw_jobs, use_ai=True)

    print(f"✅ Found {len(h1b_jobs)} H1B-eligible jobs")

    # STEP 3: Job matching against your resume
    print(f"\n[3/5] Matching jobs against your resume (threshold: {match_threshold})...")
    matched_jobs = []

    for i, job in enumerate(h1b_jobs, 1):
        print(f"  Matching job {i}/{len(h1b_jobs)}: {job['title'][:50]}...")

        try:
            # Get match score using RAG-enhanced job matching
            match_result = evaluate_job(job["description"])
            match_score = match_result.get("match_score", 0)

            # Add match data to job
            job["match_score"] = match_score
            job["strengths"] = match_result.get("strengths", [])
            job["gaps"] = match_result.get("gaps", [])
            job["match_summary"] = match_result.get("summary", "")

            # Keep if above threshold
            if match_score >= match_threshold:
                matched_jobs.append(job)
                print(f"    ✅ {match_score:.2f} - Good match!")
            else:
                print(f"    ❌ {match_score:.2f} - Below threshold")

        except Exception as e:
            print(f"    ⚠️ Match failed: {e}")
            job["match_score"] = 0
            h1b_jobs.append(job)

    print(f"✅ Found {len(matched_jobs)} good matches (>= {match_threshold})")

    # STEP 4: Generate tailored resumes (OPTIONAL)
    if generate_resumes and matched_jobs:
        print(f"\n[4/5] Generating tailored resumes for top {len(matched_jobs)} matches...")

        OUTPUT_DIR = project_root / "output" / "h1b_resumes"
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        for i, job in enumerate(matched_jobs, 1):
            print(f"  Generating resume {i}/{len(matched_jobs)}...")

            try:
                resume_result = generate_tailored_resume(
                    job["description"],
                    {
                        "match_score": job["match_score"],
                        "strengths": job["strengths"],
                        "gaps": job["gaps"],
                        "summary": job["match_summary"],
                    },
                )

                # Save tailored resume
                resume_filename = (
                    f"h1b_job_{i}_{job['company'].replace(' ', '_')[:20]}_"
                    f"{job['match_score']:.0%}.docx"
                )
                resume_path = OUTPUT_DIR / resume_filename

                if resume_result.get("docx_path"):
                    resume_result["docx_path"].rename(resume_path)
                    job["resume_path"] = str(resume_path)
                    print(f"    ✅ Resume saved: {resume_path.name}")
                else:
                    print("    ⚠️ No DOCX generated")

            except Exception as e:
                print(f"    ⚠️ Resume generation failed: {e}")

    # Step 5: Save to CSV
    print(f"\n[5/5] Saving results...")

    if matched_jobs:
        df = pd.DataFrame(matched_jobs)
        df["search_date"] = datetime.now().strftime("%Y-%m-%d %H:%M")

        # Save full data with match scores
        df.to_csv(JOBS_H1B_LIVE_CSV, index=False)
        print(f"✅ Full results saved to: {JOBS_H1B_LIVE_CSV}")

        # Save report (top columns)
        report_df = df[
            [
                "title",
                "company",
                "location",
                "source",
                "h1b_eligible",
                "eligibility_reason",
                "match_score",
                "url",
                "resume_path",
            ]
        ].head(20)
        report_df.to_csv(H1B_REPORT_CSV, index=False)
        print(f"✅ Report saved to: {H1B_REPORT_CSV}")

    # Step 6: Send email (optional)
    if EMAIL_USER and EMAIL_PASSWORD and REPORT_RECIPIENT:
        print(f"\nSending email report to {REPORT_RECIPIENT}...")
        try:
            from src.utils.email_sender import EmailReporter

            reporter = EmailReporter(SMTP_HOST, SMTP_PORT, EMAIL_USER, EMAIL_PASSWORD)
            reporter.send_report(matched_jobs, REPORT_RECIPIENT)
            print("✅ Email sent successfully")
        except Exception as e:
            print(f"⚠️ Email failed: {e}")
    else:
        print("\nEmail not configured (skipping)")

    # Summary
    print("\n" + "=" * 70)
    print("📊 SUMMARY")
    print("=" * 70)
    print(f"Total jobs scraped:         {len(raw_jobs):>4}")
    print(f"H1B-eligible jobs:         {len(h1b_jobs):>4}")
    print(f"Good matches (≥{match_threshold}): {len(matched_jobs):>4}")
    if len(raw_jobs) > 0:
        print(
            f"H1B exclusion rate:        "
            f"{((len(raw_jobs) - len(h1b_jobs)) / len(raw_jobs) * 100):>6.1f}%"
        )
        print(
            f"Match rate (top jobs):     "
            f"{((len(matched_jobs) / len(h1b_jobs)) * 100):>6.1f}%"
        )
    print("=" * 70)


def run_h1b_job_finder_streamlit(
    keywords: str,
    location: str,
    num_pages: int = 3,
    use_ai: bool = True,
    match_threshold: float = 0.65,
    date_filter: str = "Last 24 hours",
    sources: dict | None = None,
):
    """
    Streamlit-compatible version - returns results dict instead of printing.
    Used by: streamlit_app.py

    Args:
        keywords: Job search keywords (can be comma-separated for multiple roles).
        location: Job location.
        num_pages: Number of pages to scrape per keyword.
        use_ai: Use AI filtering for H1B eligibility.
        match_threshold: Minimum match score.

    Returns:
        dict: {
            'total_jobs': int,
            'h1b_jobs': list[dict],
            'matched_jobs': list[dict],
            'exclusion_rate': float,
        }
    """
    from config.settings import (
        OPENAI_API_KEY as UI_OPENAI_KEY,
        RAPIDAPI_KEY as UI_RAPID_KEY,
        ADZUNA_APP_ID,
        ADZUNA_APP_KEY,
    )

    if sources is None:
       sources = {"jsearch": True, "adzuna": True, "indeed": True}

    # Build RAG index (best-effort)
    try:
        build_or_refresh_profile_index()
    except Exception:
        pass

    posted_after = _resolve_date_filter(date_filter)

    # Step 1: Scrape jobs (supports multiple comma-separated keywords)
    scraper = ScraperManager(
        rapidapi_key=UI_RAPID_KEY,
        adzuna_app_id=ADZUNA_APP_ID,
        adzuna_app_key=ADZUNA_APP_KEY,
    )
    keyword_list = [k.strip() for k in (keywords or "").split(",") if k.strip()]

    raw_jobs: list[dict] = []
    for kw in keyword_list or [""]:
        raw_jobs.extend(
            scraper.scrape_all(
                kw,
                location,
                num_pages,
                posted_after=posted_after,
                use_jsearch=sources.get("jsearch", True),
                use_indeed=sources.get("indeed", True),
                use_adzuna=sources.get("adzuna", True),
            )
        )

    if not raw_jobs:
        return {
            "total_jobs": 0,
            "h1b_jobs": [],
            "matched_jobs": [],
            "exclusion_rate": 0.0,
        }

    # Step 2: Filter for H1B eligibility
    h1b_filter = H1BFilter(UI_OPENAI_KEY)
    h1b_jobs = h1b_filter.filter_jobs(raw_jobs, use_ai=use_ai)

    # Step 3: Job matching
    matched_jobs: list[dict] = []
    for job in h1b_jobs:
        # Allow Streamlit cancel button to stop further processing
        try:
            import streamlit as st

            if getattr(st.session_state, "cancel_run", False):
                break
        except Exception:
            pass

        try:
            match_result = evaluate_job(job["description"])
            match_score = match_result.get("match_score", 0)

            job["match_score"] = match_score
            job["strengths"] = match_result.get("strengths", [])
            job["gaps"] = match_result.get("gaps", [])

            # NEW: flatten gaps and generate per-job use-case text
            job["gap_skills"] = "; ".join(job["gaps"])
            try:
                use_case_text = analyze_gaps_for_learning(
                    job["description"], match_result
                )
            except Exception:
                use_case_text = ""
            job["gap_use_case"] = use_case_text

            if match_score >= match_threshold:
                matched_jobs.append(job)
        except Exception:
            job["match_score"] = 0

    exclusion_rate = (
        (len(raw_jobs) - len(h1b_jobs)) / len(raw_jobs) * 100 if raw_jobs else 0.0
    )

    return {
        "total_jobs": len(raw_jobs),
        "h1b_jobs": h1b_jobs,
        "matched_jobs": matched_jobs,
        "exclusion_rate": exclusion_rate,
    }


if __name__ == "__main__":
    # Test with resume generation
    run_h1b_job_finder(generate_resumes=True, match_threshold=0.65)
