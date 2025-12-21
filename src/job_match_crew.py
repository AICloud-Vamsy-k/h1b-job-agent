from pathlib import Path

from crewai import Agent, Task, Crew

from .config import PROJECT_ROOT, DEFAULT_MODEL_NAME
import json
from typing import Any, Dict


def load_profile_text() -> str:
    """Load your basic profile text from data/profile_basic.md."""
    profile_path = PROJECT_ROOT / "data" / "profile_basic.md"
    if not profile_path.exists():
        raise FileNotFoundError(f"Profile file not found: {profile_path}")
    return profile_path.read_text(encoding="utf-8")


def create_job_match_crew(job_description: str) -> Crew:
    """
    Create a Crew that takes a job description and your profile,
    and explains the match.
    """
    profile_text = load_profile_text()

    job_match_agent = Agent(
        role="Job Match Analyst",
        goal=(
            "Evaluate how well the candidate fits a given job posting and "
            "explain the match clearly and honestly."
        ),
        backstory=(
            "You are an experienced technical recruiter. "
            "You compare job descriptions with the candidate profile. "
            "You never fabricate skills or experience; you only use what "
            "the candidate profile states."
        ),
        model=DEFAULT_MODEL_NAME,
    )

    combined_text = f"""
Job description:
{job_description}

Candidate profile:
{profile_text}
"""

    task = Task(
        description=(
            "Read the job description and the candidate profile below. "
            "Rate the match from 0 to 1 and identify strengths and gaps.\n\n"
            f"{combined_text}"
        ),
        expected_output=(
            "Return JSON with keys: "
            "match_score (0-1 float), strengths (list of strings), "
            "gaps (list of strings), summary (short paragraph)."
        ),
        agent=job_match_agent,
    )

    crew = Crew(
        agents=[job_match_agent],
        tasks=[task],
    )
    return crew

def evaluate_job(job_description: str) -> Dict[str, Any]:
    """Run the Job Match crew on a job description and return a dict."""
    crew: Crew = create_job_match_crew(job_description)
    crew_output = crew.kickoff()  # This is a CrewOutput object now

    # Option A: if your task already returns JSON, parse crew_output.raw
    raw_text = crew_output.raw  # final text from the crew [web:50][web:52][web:63]

    # Try to parse JSON
    try:
        data = json.loads(raw_text)
        # Expect keys: match_score, strengths, gaps, summary
        return {
            "match_score": data.get("match_score"),
            "strengths": data.get("strengths"),
            "gaps": data.get("gaps"),
            "summary": data.get("summary"),
            "raw": raw_text,
        }
    except Exception:
        # Fallback: if not JSON, just wrap as text
        return {
            "match_score": None,
            "strengths": None,
            "gaps": None,
            "summary": raw_text,
            "raw": raw_text,
        }


def run_job_match_example() -> None:
    """Small manual test for the Job Match crew."""
    print("Using model at runtime:", DEFAULT_MODEL_NAME)

    sample_job = """
Title: Senior Backend Engineer
Location: USA (Remote)
Requirements:
- 5+ years Python backend development
- Strong experience with REST APIs and microservices
- SQL databases (PostgreSQL or MySQL)
- Experience with AWS services (EC2, S3, RDS)

Nice to have:
- Docker, Kubernetes
- CI/CD pipelines
"""

    result = evaluate_job(sample_job)
    print("=== Job Match Crew Result ===")
    print(result)

