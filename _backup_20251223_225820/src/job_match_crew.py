# src/job_match_crew.py

from pathlib import Path
import json
from typing import Any, Dict

from crewai import Agent, Task, Crew, LLM

from . import config  # ensures config.py runs and prints
from .config import PROJECT_ROOT, DEFAULT_MODEL_NAME
from src.profile_rag import retrieve_relevant_chunks
from src.profile_summary import get_or_build_profile_summary


def create_job_match_crew(job_description: str) -> Crew:
    """
    Create a Crew that takes a job description and your resume-based profile,
    and explains the match. Uses:
    - Profile summary derived from the current resume.
    - RAG resume chunks from Chroma.
    """
    # High-level summary from resume
    profile_summary = get_or_build_profile_summary()

    # Most relevant resume chunks for this JD (RAG)
    #relevant_chunks = retrieve_relevant_chunks(
    #    query="profile and experience relevant to this job description: " + job_description,
    #    top_k=5,
    #)
    #relevant_chunks_text = "\n\n".join(relevant_chunks) if relevant_chunks else "(no relevant chunks found)"

    # Most relevant resume chunks for this JD (RAG)
    # TEMP: disable RAG completely to avoid Chroma/index issues
    relevant_chunks = []
    relevant_chunks_text = "(RAG disabled for debugging)"

    # Explicit OpenAI LLM so CrewAI knows which provider to use
    openai_llm = LLM(
        model=DEFAULT_MODEL_NAME,
        provider="openai",
        # Uses OPENAI_API_KEY from environment
    )

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
            "the candidate resume states or what is present in the retrieved context."
        ),
        llm=openai_llm,
    )

    combined_text = f"""
Job description:
----------------
{job_description}

Candidate profile (summary from resume):
---------------------------------------
{profile_summary or "(no profile summary available; resume may not be set yet)"}

Most relevant experience chunks for this job (retrieved via RAG from resume):
-----------------------------------------------------------------------------
{relevant_chunks_text}
"""

    task = Task(
        description=(
            "Read the job description, the candidate profile summary, and the "
            "retrieved relevant experience chunks below. "
            "Rate the match from 0 to 1 and identify strengths and gaps.\n\n"
            f"{combined_text}\n\n"
            "Return your answer STRICTLY as JSON with keys:\n"
            '- "match_score" (0-1 float)\n'
            '- "strengths" (list of strings)\n'
            '- "gaps" (list of strings)\n'
            '- "summary" (short paragraph).\n'
            "Only output valid JSON, with double quotes and no trailing commas."
        ),
        expected_output=(
            "Return JSON with keys: match_score (0-1 float), strengths "
            "(list of strings), gaps (list of strings), summary (short paragraph)."
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
    import time

    crew: Crew = create_job_match_crew(job_description)
    print("Starting Job Match crew...")
    start = time.time()
    crew_output = crew.kickoff()  # CrewOutput object
    end = time.time()
    print(f"Job Match crew finished in {end - start:.2f} seconds.")

    # Try to get raw text from crew output and parse as JSON
    try:
        raw_text = crew_output.raw
    except Exception:
        raw_text = str(crew_output)

    print("Raw job match output:\n", raw_text)  # <--- add this

    try:
        data = json.loads(raw_text)
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
