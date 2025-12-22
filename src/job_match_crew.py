# src/job_match_crew.py

from pathlib import Path
import json
from typing import Any, Dict

from crewai import Agent, Task, Crew

from .config import PROJECT_ROOT, DEFAULT_MODEL_NAME
from src.profile_rag import retrieve_relevant_chunks


def load_profile_text() -> str:
    """Load your basic profile text from data/profile_basic.md."""
    profile_path = PROJECT_ROOT / "data" / "profile_basic.md"
    if not profile_path.exists():
        raise FileNotFoundError(f"Profile file not found: {profile_path}")
    return profile_path.read_text(encoding="utf-8")


def create_job_match_crew(job_description: str) -> Crew:
    """
    Create a Crew that takes a job description and your profile,
    and explains the match. Now also uses RAG (relevant chunks).
    """
    profile_text = load_profile_text()

    # Get most relevant chunks from profile for this JD (RAG)
    relevant_chunks = retrieve_relevant_chunks(job_description, top_k=5)
    relevant_chunks_text = "\n\n".join(relevant_chunks)

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
----------------
{job_description}

Candidate profile (summary):
----------------------------
{profile_text}

Most relevant experience chunks for this job (retrieved via RAG):
-----------------------------------------------------------------
{relevant_chunks_text}
"""

    task = Task(
        description=(
            "Read the job description, the candidate profile, and the retrieved "
            "relevant experience chunks below. "
            "Rate the match from 0 to 1 and identify strengths and gaps.\n\n"
            f"{combined_text}\n\n"
            "Return your answer STRICTLY as JSON with keys:\n"
            "- \"match_score\" (0-1 float)\n"
            "- \"strengths\" (list of strings)\n"
            "- \"gaps\" (list of strings)\n"
            "- \"summary\" (short paragraph).\n"
            "Only output valid JSON, with double quotes and no trailing commas."
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
    crew_output = crew.kickoff()  # This is a CrewOutput object

    # Try to get raw text from crew output and parse as JSON
    try:
        raw_text = crew_output.raw
    except Exception:
        raw_text = str(crew_output)

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
