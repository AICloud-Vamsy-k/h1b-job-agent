# src/job_sources.py

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import List


DATA_DIR = Path(__file__).resolve().parents[2] / "data"

@dataclass
class JobPosting:
    id: str
    title: str
    company: str
    location: str
    url: str
    description: str
    sponsorship_score: float = 0.0  # will fill later


def load_h1b_sponsors() -> List[str]:
    """Load known H1B sponsor company names from data/h1b_sponsors.txt."""
    path = DATA_DIR / "h1b_sponsors.txt"
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    sponsors = [line.strip() for line in lines if line.strip()]
    return sponsors


def load_jobs_from_csv(path: Path | None = None) -> List[JobPosting]:
    """Load jobs from a CSV file into JobPosting objects."""
    if path is None:
        path = DATA_DIR / "jobs_sample.csv"

    jobs: List[JobPosting] = []
    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            jobs.append(
                JobPosting(
                    id=str(row.get("id", "")).strip(),
                    title=(row.get("title") or "").strip(),
                    company=(row.get("company") or "").strip(),
                    location=(row.get("location") or "").strip(),
                    url=(row.get("url") or "").strip(),
                    description=(row.get("description") or "").strip(),
                )
            )
    return jobs


def compute_sponsorship_score(job: JobPosting, sponsor_names: List[str]) -> float:
    """
    Simple heuristic:
    - If company name matches or contains any sponsor name -> high score.
    - If JD description mentions visa sponsorship keywords -> boost.
    """
    company_lower = job.company.lower()
    desc_lower = job.description.lower()

    score = 0.0

    # Company-based signal
    for sponsor in sponsor_names:
        s = sponsor.strip()
        if not s:
            continue
        s_lower = s.lower()
        if s_lower in company_lower:
            score += 0.7
            break  # one match is enough

    # Keyword-based signal
    visa_keywords = [
        "h-1b",
        "h1b",
        "visa sponsorship",
        "sponsorship available",
        "will sponsor",
        "work authorization provided",
    ]
    for kw in visa_keywords:
        if kw in desc_lower:
            score += 0.3
            break

    # Clamp to [0, 1]
    return max(0.0, min(1.0, score))


def get_candidate_jobs() -> List[JobPosting]:
    """Load jobs and compute sponsorship_score for each."""
    sponsor_names = load_h1b_sponsors()
    jobs = load_jobs_from_csv()
    for job in jobs:
        job.sponsorship_score = compute_sponsorship_score(job, sponsor_names)
    return jobs

